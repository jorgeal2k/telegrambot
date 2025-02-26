from openai import OpenAI

class AIService:
    """Maneja la interacción con la API de OpenAI"""
    
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
                    {"role": "system", "content": "Eres un asistente que resume conversaciones de grupos de Telegram. Genera un resumen completo de la siguiente conversación con un máximo de 800 palabras, identificando los participantes clave, los temas principales en forma de listada numerada y conclusiones importantes. Usa un estilo informal. Usa muchos emojis típicos de un post de **TELEGRAM** en la introducción, en los elementos de la lista y en las conclusiones. Usa '*' para resaltar los elementos importantes del texto."},
                    {"role": "user", "content": f"Resume la siguiente conversación:\n\n{conversation_text}"}
                ],
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error al generar el resumen: {str(e)}"