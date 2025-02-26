from openai import OpenAI

class AIService:
    """Maneja la interacción con la API de OpenAI"""
    
    def __init__(self, api_key, model="gpt-4o", max_tokens=800):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
    
    def generate_summary(self, conversation_text):
        """Genera un resumen de la conversación usando OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un asistente que resume conversaciones de grupos **en TELEGRAM**. Genera un resumen completo de la siguiente conversación de hasta 800 palabras, identificando los temas principales, participantes **clave** y conclusiones importantes. El resumen debe estar en español y ser fácil de leer. Debes usar un estilo informal. Debes usar un formato de lista ordenada. Haz uso de emoticonos y emojis típicos de un mensaje de Telegram."},
                    {"role": "user", "content": f"Resume la siguiente conversación de las últimas 6 horas:\n\n{conversation_text}"}
                ],
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error al generar el resumen: {str(e)}"