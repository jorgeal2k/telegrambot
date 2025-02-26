import os
import datetime
from collections import defaultdict
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from openai import OpenAI
import psutil
import time
import logging
import json

from models.bot_state import BotState
from services.ai_service import AIService
from services.storage_service import StorageService
from handlers.command_handlers import CommandHandlers
from handlers.message_handlers import MessageHandlers
from jobs.scheduled_jobs import ScheduledJobs

class TelegramBot:
    """Clase principal que gestiona el bot de Telegram"""
    
    def __init__(self, config):
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
        )
        self.logger = logging.getLogger("telegram_bot")
        self.config = config
        
        # Inicializar estado y servicios
        self.bot_state = BotState()
        self.ai_service = AIService(
            api_key=config["OPENAI_API_KEY"], 
            model=config["modelo_ai"],
            max_tokens=config["max_tokens_resumen"]
        )
        
        # Cargar datos persistentes
        StorageService.load_data(self.bot_state)
        
        # Inicializar manejadores
        self.command_handlers = CommandHandlers(self.bot_state, self.ai_service, config)
        self.message_handlers = MessageHandlers(self.bot_state, config)
        self.jobs = ScheduledJobs(self.bot_state, self.ai_service, config)
        
        # Inicializar la aplicación
        self.app = Application.builder().token(config["BOT_TOKEN"]).build()
        
    def setup(self):
        """Configura los manejadores y tareas programadas"""
        # Configurar manejadores de comandos
        self.app.add_handler(CommandHandler("start", self.command_handlers.start))
        self.app.add_handler(CommandHandler("help", self.command_handlers.help_command))
        self.app.add_handler(CommandHandler("resumen", self.command_handlers.generate_summary))
        self.app.add_handler(CommandHandler("stop", self.command_handlers.stop_summaries))
        self.app.add_handler(CommandHandler("activar_resumenes", self.command_handlers.enable_summaries))
        self.app.add_handler(CommandHandler("status", self.command_handlers.status_command))
        
        # Configurar manejador de mensajes
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handlers.store_message))
        
        # Configurar tareas programadas
        job_queue = self.app.job_queue
        job_queue.run_repeating(self.jobs.clean_old_messages, interval=21600, first=10)
        job_queue.run_repeating(self.jobs.auto_summary, interval=21600, first=21600)
        job_queue.run_repeating(self.jobs.save_data, interval=1800, first=300)
        
    def run(self):
        """Inicia el bot"""
        self.logger.info("El bot está iniciando...")
        self.setup()
        self.app.run_polling()

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Variables de configuración centralizadas
CONFIG = {
    "resumen_intervalo_horas": 6,
    "limpieza_intervalo_horas": 24,
    "max_mensajes_por_grupo": 5000,  # Limitar para evitar problemas de memoria
    "modelo_ai": "gpt-4o",
    "max_tokens_resumen": 800,
    "BOT_TOKEN": TOKEN,
    "OPENAI_API_KEY": OPENAI_API_KEY
}

if __name__ == "__main__":
    bot = TelegramBot(CONFIG)
    bot.run()

