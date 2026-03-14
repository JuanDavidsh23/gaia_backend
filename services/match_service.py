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
    # Obtiene una lista de perfiles que el usuario aun no ha evaluado
    # 1. Obtener los IDs de los usuarios con los que YA interactué (para excluirlos)
    interacted_users = db.query(Interaction.user_to_id).filter(
        Interaction.user_from_id == current_user_id
    ).all()
    # interacted_users retorna una lista de tuplas: [(2,), (3,)]
    interacted_ids = [u[0] for u in interacted_users]
    
    # Excluimos también al propio usuario
    interacted_ids.append(current_user_id)

    # 2. Buscar usuarios que NO estén en esa lista de excluidos
    # (En un proyecto real, aquí también filtrarías por rol, ubicación, o skills)
    potential_matches = db.query(User).filter(
        User.user_id.notin_(interacted_ids)
    ).limit(20).all() # Traemos máximo 20 tarjetas por ahora

    result = []
    
    # 3. Formatear la respuesta con las habilidades de cada uno
    for p_user in potential_matches:
        from models.users_skills import UserSkill, IntentEnum
        from models.skill import Skill
        
        # Habilidades que quiere enseñar
        teach_skills = db.query(Skill.name).join(UserSkill).filter(
            UserSkill.user_id == p_user.user_id,
            UserSkill.intent == IntentEnum.teach
        ).all()
        
        # Habilidades que quiere aprender
        learn_skills = db.query(Skill.name).join(UserSkill).filter(
            UserSkill.user_id == p_user.user_id,
            UserSkill.intent == IntentEnum.learn
        ).all()

        result.append({
            "user_id": p_user.user_id,
            "first_name": p_user.first_name,
            "last_name": p_user.last_name,
            "bio": p_user.bio,
            "avatar_url": p_user.avatar_url,
            "skills_to_teach": [s[0] for s in teach_skills],
            "skills_to_learn": [s[0] for s in learn_skills]
        })

    return {"users": result}

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
            "bio": other_user.bio
        })
    
    return {"matches": result}
