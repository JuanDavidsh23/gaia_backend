from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.user import User
from models.interaction import Interaction, ActionEnum
from models.match import Match
from models.chat_room import ChatRoom
from schemas.match import InteractionRequest

def create_interaction(db: Session, data: InteractionRequest, user_from_id: int):
    # Registra un Like o Pass. Si es un Like mutuo, crea un Match y su sala de chat
    # 1. Validar que los usuarios existen
    user_from = db.query(User).filter(User.user_id == user_from_id).first()
    user_to = db.query(User).filter(User.user_id == data.user_to_id).first()
    
    if not user_from or not user_to:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    if user_from_id == data.user_to_id:
        raise HTTPException(status_code=400, detail="No puedes darte like a ti mismo")

    # 2. Revisar si la interacción ya existe (evitar doble like)
    existing_interaction = db.query(Interaction).filter(
        Interaction.user_from_id == user_from_id,
        Interaction.user_to_id == data.user_to_id
    ).first()

    if existing_interaction:
        raise HTTPException(status_code=400, detail="Ya interactuaste con este usuario")

    # 3. Guardar la interacción (Like o Pass)
    new_interaction = Interaction(
        user_from_id=user_from_id,
        user_to_id=data.user_to_id,
        actions=data.action
    )
    db.add(new_interaction)
    
    # 4. LÓGICA DE MATCH: Solo revisar si fue un "like"
    is_match = False
    if data.action == ActionEnum.like:
        # Preguntar a la DB: ¿Acaso el usuario_to ya le había dado like a usuario_from antes?
        mutual_like = db.query(Interaction).filter(
            Interaction.user_from_id == data.user_to_id,
            Interaction.user_to_id == user_from_id,
            Interaction.actions == ActionEnum.like
        ).first()

        if mutual_like:
            is_match = True
            
            # Ordenar IDs para cumplir tu CheckConstraint('user1_id < user2_id')
            user1_id = min(user_from_id, data.user_to_id)
            user2_id = max(user_from_id, data.user_to_id)
            
            # Crear el Match en la tabla matches
            new_match = Match(user1_id=user1_id, user2_id=user2_id)
            db.add(new_match)
            db.flush()  # Para obtener el match_id generado
            
            # ¡CREAR LA SALA DE CHAT automáticamente!
            new_chat_room = ChatRoom(match_id=new_match.match_id)
            db.add(new_chat_room)

    db.commit()

    if is_match:
        return {
            "msg": "¡It's a Match!", 
            "match_created": True,
            "room_id": new_chat_room.room_id
        }
    return {"msg": "Interacción guardada", "match_created": False}

def get_user_feed(db: Session, current_user_id: int):
    from models.users_skills import UserSkill, IntentEnum
    from models.skill import Skill

    # 1. IDs de usuarios ya swipeados (para excluirlos)
    excluded_ids = [u[0] for u in db.query(Interaction.user_to_id).filter(
        Interaction.user_from_id == current_user_id
    ).all()]
    excluded_ids.append(current_user_id)

    # 2. Mis skills (qué quiero aprender y qué enseño) — 2 queries
    my_learn = set(s[0] for s in db.query(UserSkill.skill_id).filter(
        UserSkill.user_id == current_user_id,
        UserSkill.intent == IntentEnum.learn
    ).all())

    my_teach = set(s[0] for s in db.query(UserSkill.skill_id).filter(
        UserSkill.user_id == current_user_id,
        UserSkill.intent == IntentEnum.teach
    ).all())

    # 3. Usuarios disponibles — 1 query (limitamos a 50 candidatos antes de filtrar)
    available_users = db.query(User).filter(
        User.user_id.notin_(excluded_ids)
    ).order_by(User.datetime_created_at.desc()).limit(50).all()

    available_ids = [u.user_id for u in available_users]

    # 4. UNA sola query para TODOS sus skills con nombres — eliminamos N+1
    all_skills = db.query(
        UserSkill.user_id,
        UserSkill.skill_id,
        UserSkill.intent,
        Skill.name
    ).join(Skill, UserSkill.skill_id == Skill.skill_id).filter(
        UserSkill.user_id.in_(available_ids)
    ).all()

    # 5. Organizar en memoria (sin tocar la BD de nuevo)
    user_teach_ids = {}    # user_id -> set de skill_ids que enseña
    user_learn_ids = {}    # user_id -> set de skill_ids que aprende
    user_teach_names = {}  # user_id -> lista de nombres que enseña
    user_learn_names = {}  # user_id -> lista de nombres que aprende

    for uid, sid, intent, name in all_skills:
        if intent == IntentEnum.teach:
            user_teach_ids.setdefault(uid, set()).add(sid)
            user_teach_names.setdefault(uid, []).append(name)
        else:
            user_learn_ids.setdefault(uid, set()).add(sid)
            user_learn_names.setdefault(uid, []).append(name)

    compatible_users = []
    other_users = []

    for p_user in available_users:
        uid = p_user.user_id
        their_teach = user_teach_ids.get(uid, set())
        their_learn = user_learn_ids.get(uid, set())

        is_compatible = (
            bool(my_learn & their_teach) or
            bool(my_teach & their_learn)
        )

        user_data = {
            "user_id": uid,
            "first_name": p_user.first_name,
            "last_name": p_user.last_name,
            "bio": p_user.bio,
            "avatar_url": p_user.avatar_url,
            "skills_to_teach": user_teach_names.get(uid, []),
            "skills_to_learn": user_learn_names.get(uid, []),
        }

        if is_compatible:
            compatible_users.append(user_data)
        else:
            other_users.append(user_data)

    # Compatibles primero, el resto como fallback. Máximo 30 tarjetas.
    return {"users": (compatible_users + other_users)[:30]}

def get_user_matches(db: Session, user_id: int):
    # Devuelve todos los matches exitosos de un usuario y los IDs de chat correspondientes
    from sqlalchemy import or_
    
    # Buscar todos los matches donde este usuario sea user1 o user2
    matches = db.query(Match).filter(
        or_(
            Match.user1_id == user_id,
            Match.user2_id == user_id
        )
    ).all()
    
    result = []
    
    for match in matches:
        # Determinar quién es la OTRA persona
        if match.user1_id == user_id:
            other_user = db.query(User).filter(User.user_id == match.user2_id).first()
        else:
            other_user = db.query(User).filter(User.user_id == match.user1_id).first()
        
        # Buscar la sala de chat asociada a este match
        chat_room = db.query(ChatRoom).filter(ChatRoom.match_id == match.match_id).first()
        
        result.append({
            "match_id": match.match_id,
            "room_id": chat_room.room_id if chat_room else None,
            "user_id": other_user.user_id,
            "first_name": other_user.first_name,
            "last_name": other_user.last_name,
            "avatar_url": other_user.avatar_url,
            "bio": other_user.bio,
            "is_completed": match.is_completed
        })
    
    return {"matches": result}

def finish_match_session(db: Session, match_id: int):
    """
    Finaliza un match (sesión de aprendizaje completada).
    Otorga puntos a ambos usuarios por haber terminado el intercambio
    y marca el match como 'is_completed = True' para evitar repeticiones.
    """
    match = db.query(Match).filter(Match.match_id == match_id).first()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match no encontrado.")
        
    if match.is_completed:
        raise HTTPException(status_code=400, detail="Este match ya fue finalizado y los puntos ya se otorgaron.")
        
    # Obtener usuarios correspondientes
    user1 = db.query(User).filter(User.user_id == match.user1_id).first()
    user2 = db.query(User).filter(User.user_id == match.user2_id).first()
    
    # -------------------------------------------------------------
    # CONFIGURACIÓN DE PUNTOS: Otorgamos 50 puntos por match completado
    # -------------------------------------------------------------
    POINTS_REWARD = 50
    user1.points += POINTS_REWARD
    user2.points += POINTS_REWARD
    
    # Bloquear para que no se sumen puntos de nuevo
    match.is_completed = True
    
    db.commit()
    
    return {
        "msg": "Match finalizado con éxito.",
        "puntos_otorgados": POINTS_REWARD,
        "user1": {"user_id": user1.user_id, "nuevos_puntos": user1.points},
        "user2": {"user_id": user2.user_id, "nuevos_puntos": user2.points}
    }
