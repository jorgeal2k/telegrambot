import os
from dotenv import load_dotenv
from bot import TelegramBot
import logging

def main():
    # Cargar variables de entorno
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Configuración centralizada
    config = {
        "resumen_intervalo_horas": 6,
        "limpieza_intervalo_horas": 24,
        "max_mensajes_por_grupo": 5000,
        "modelo_ai": "gpt-4o-mini",
        "max_tokens_resumen": 800,
        "BOT_TOKEN": TOKEN,
        "OPENAI_API_KEY": OPENAI_API_KEY
    }
    
    # Iniciar el bot
    bot = TelegramBot(config)
    bot.run()

if __name__ == "__main__":
    main()