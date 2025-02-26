import os
from dotenv import load_dotenv
from bot import TelegramBot

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    # Configuración centralizada
    config = {
        "BOT_TOKEN": os.getenv("BOT_TOKEN"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "resumen_intervalo_horas": 6,
        "limpieza_intervalo_horas": 24,
        "max_mensajes_por_grupo": 5000,
        "modelo_ai": "gpt-4o",
        "max_tokens_resumen": 800,
        "ADMIN_USER_IDS": [702356304]
    }
    
    # Iniciar el bot
    bot = TelegramBot(config)
    bot.run()

if __name__ == "__main__":
    main()