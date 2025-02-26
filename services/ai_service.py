import os
from dotenv import load_dotenv
from openai import OpenAI

class AIService:
    """Maneja la interacción con la API de OpenAI"""
    
    load_dotenv()
    SYS_MESSAGE = os.getenv("SYS_MESSAGE")
    
    def __init__(self, api_key, model="gpt-4o-mini", max_tokens=800):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
    
    def generate_summary(self, conversation_text):
        """Genera un resumen de la conversación usando OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYS_MESSAGE},
                    {"role": "user", "content": f"Resume la siguiente conversación:\n\n{conversation_text}"}
                ],
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error al generar el resumen: {str(e)}"