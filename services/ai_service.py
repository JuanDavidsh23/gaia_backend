from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv() # Cargar variables de entorno

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Función para interactuar con la IA
def ask_ai(message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": message}
        ]
    )

    return response.choices[0].message.content