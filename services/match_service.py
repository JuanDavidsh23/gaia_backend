from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.user import User
from models.interaction import Interaction, ActionEnum
from models.match import Match
from models.chat_room import ChatRoom
from schemas.match import InteractionRequest

def create_interaction(db: Session, data: InteractionRequest):
    # Registra un Like o Pass. Si es un Like mutuo, crea un Match y su sala de chat
    # 1. Validar que los usuarios existen
    user_from = db.query(User).filter(User.user_id == data.user_from_id).first()
    user_to = db.query(User).filter(User.user_id == data.user_to_id).first()
    
    if not user_from or not user_to:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    if user_from.user_id == user_to.user_id:
        raise HTTPException(status_code=400, detail="No puedes darte like a ti mismo")

    # 2. Revisar si la interacción ya existe (evitar doble like)
    existing_interaction = db.query(Interaction).filter(
        Interaction.user_from_id == data.user_from_id,
        Interaction.user_to_id == data.user_to_id
    ).first()

    if existing_interaction:
        raise HTTPException(status_code=400, detail="Ya interactuaste con este usuario")

    # 3. Guardar la interacción (Like o Pass)
    new_interaction = Interaction(
        user_from_id=data.user_from_id,
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
            Interaction.user_to_id == data.user_from_id,
            Interaction.actions == ActionEnum.like
        ).first()

        if mutual_like:
            is_match = True
            
            # Ordenar IDs para cumplir tu CheckConstraint('user1_id < user2_id')
            user1_id = min(data.user_from_id, data.user_to_id)
            user2_id = max(data.user_from_id, data.user_to_id)
            
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
    
    # 1. Obtener los IDs de usuarios ya swipeados (para excluirlos)
    interacted_users = db.query(Interaction.user_to_id).filter(
        Interaction.user_from_id == current_user_id
    ).all()
    excluded_ids = [u[0] for u in interacted_users]
    excluded_ids.append(current_user_id)  # Excluirme a mí mismo

    # 2. Obtener MIS skills (qué quiero aprender y qué enseño)
    my_learn = [s[0] for s in db.query(UserSkill.skill_id).filter(
        UserSkill.user_id == current_user_id,
        UserSkill.intent == IntentEnum.learn
    ).all()]
    
    my_teach = [s[0] for s in db.query(UserSkill.skill_id).filter(
        UserSkill.user_id == current_user_id,
        UserSkill.intent == IntentEnum.teach
    ).all()]

    # 3. Buscar TODOS los usuarios disponibles (no swipeados, no soy yo)
    all_available = db.query(User).filter(
        User.user_id.notin_(excluded_ids)
    ).order_by(User.datetime_created_at.desc()).all()

    compatible_users = []
    other_users = []

    for p_user in all_available:
        # Skills de este usuario
        their_teach = [s[0] for s in db.query(UserSkill.skill_id).filter(
            UserSkill.user_id == p_user.user_id,
            UserSkill.intent == IntentEnum.teach
        ).all()]
        
        their_learn = [s[0] for s in db.query(UserSkill.skill_id).filter(
            UserSkill.user_id == p_user.user_id,
            UserSkill.intent == IntentEnum.learn
        ).all()]

        # ¿Es compatible? (lo que yo quiero aprender, él enseña, o viceversa)
        is_compatible = (
            bool(set(my_learn) & set(their_teach)) or
            bool(set(my_teach) & set(their_learn))
        )

        # Nombres de skills para la respuesta
        teach_names = [s[0] for s in db.query(Skill.name).join(UserSkill).filter(
            UserSkill.user_id == p_user.user_id,
            UserSkill.intent == IntentEnum.teach
        ).all()]
        
        learn_names = [s[0] for s in db.query(Skill.name).join(UserSkill).filter(
            UserSkill.user_id == p_user.user_id,
            UserSkill.intent == IntentEnum.learn
        ).all()]

        user_data = {
            "user_id": p_user.user_id,
            "first_name": p_user.first_name,
            "last_name": p_user.last_name,
            "bio": p_user.bio,
            "avatar_url": p_user.avatar_url,
            "skills_to_teach": teach_names,
            "skills_to_learn": learn_names
        }

        if is_compatible:
            compatible_users.append(user_data)
        else:
            other_users.append(user_data)

    # 4. PRIORIZAR compatibles primero, luego los demás (fallback)
    result = compatible_users + other_users

    # Limitar a 30 tarjetas máximo
    return {"users": result[:30]}

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
