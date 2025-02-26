import psutil
import os
import time

class CommandHandlers:
    """Manejadores para los comandos del bot"""
    
    def __init__(self, bot_state, ai_service, config):
        self.bot_state = bot_state
        self.ai_service = ai_service
        self.config = config
        self.admin_user_ids = config["ADMIN_USER_IDS"]
    
    async def start(self, update, context):
        await update.message.reply_text("¡Hola! Soy tu bot que puede resumir mensajes de las últimas 6 horas usando IA. Usa /resumen para obtener un resumen inteligente. Para desactivar los resúmenes automáticos usa /stop.")
    
    async def help_command(self, update, context):
        help_text = "🤖 *COMANDOS DISPONIBLES* 🤖\n\n"
        help_text += "• `/start` - Inicia el bot y muestra mensaje de bienvenida\n"
        help_text += "• `/help` - Muestra esta lista de comandos disponibles\n"
        help_text += "• `/resumen` - Genera manualmente un resumen de los mensajes\n"
        help_text += "• `/stop` - Desactiva los resúmenes automáticos\n"
        help_text += "• `/activar_resumenes` - Reactiva los resúmenes automáticos\n\n"
        help_text += "• `/status` - Muestra estadísticas y estado actual del bot\n"
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def stop_summaries(self, update, context):
        chat_id = update.effective_chat.id
        self.bot_state.auto_summary_enabled[chat_id] = False
        await update.message.reply_text("✅ Los resúmenes automáticos han sido desactivados para este grupo. Puedes reactivarlos con /activar_resumenes")
    
    async def enable_summaries(self, update, context):
        chat_id = update.effective_chat.id
        self.bot_state.auto_summary_enabled[chat_id] = True
        await update.message.reply_text("✅ Los resúmenes automáticos han sido reactivados para este grupo.")
    
    # Otros manejadores de comandos...