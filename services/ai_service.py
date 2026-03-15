from openai import OpenAI
import os
import random
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Función original para el endpoint /ai
def ask_ai(message: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": message}]
    )
    return response.choices[0].message.content


# Función para moderar el chat y opinar ocasionalmente
def moderate_and_comment(message: str, recent_messages: list[dict]) -> str | None:
    """
    Revisa si el mensaje tiene groserías (siempre advierte) y con 25% de
    probabilidad opina sobre la conversación. Retorna None si decide no hablar.
    """
    should_comment = random.random() < 0.25

    # Construir contexto de los últimos mensajes
    context = "\n".join(
        [f"Usuario {m['user_id']}: {m['message']}" for m in recent_messages[-5:]]
    ) or "(inicio de conversación)"

    prompt = f"""Eres un asistente de aprendizaje amigable en una plataforma donde dos personas intercambian habilidades.

Conversación reciente:
{context}

Nuevo mensaje: "{message}"

Instrucciones:
1. Si el mensaje tiene groserías o lenguaje irrespetuoso → da una advertencia amable. Esto es obligatorio.
2. {"Puedes opinar brevemente sobre el tema que discuten (máximo 1-2 oraciones cortas). Solo si agrega valor." if should_comment else "No hagas comentarios adicionales hoy."}

Si no hay groserías y no tienes nada útil que aportar, responde exactamente la palabra: SILENCIO
Si sí respondes, escribe directamente el mensaje sin prefijos como 'Asistente:' ni 'IA:'."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )

    result = response.choices[0].message.content.strip()
    return None if result == "SILENCIO" else result