import psutil
import os
import time
import functools
from datetime import datetime, timedelta
from telegram import ChatMemberAdministrator, ChatMemberOwner

# Decorador para verificar si el usuario es administrador
def admin_only(func):
    @functools.wraps(func)
    async def wrapper(self, update, context):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # Si es un chat privado, permitir (opcional)
        if update.effective_chat.type == "private":
            return await func(self, update, context)
        
        # Verificar si es administrador
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        
        if isinstance(chat_member.status, str):
            is_admin = chat_member.status in ["administrator", "creator"]
        else:
            is_admin = isinstance(chat_member, (ChatMemberAdministrator, ChatMemberOwner))
        
        if not is_admin:
            await update.message.reply_text("⚠️ Lo siento, solo los administradores del grupo pueden usar este comando.")
            return
        
        # Si es admin, ejecutar la función original
        return await func(self, update, context)
    return wrapper


class CommandHandlers:
    """Manejadores para los comandos del bot"""
    
    def __init__(self, bot_state, ai_service, config):
        self.bot_state = bot_state
        self.ai_service = ai_service
        self.config = config
    
    # Este comando lo dejamos accesible a todos
    async def start(self, update, context):
        await update.message.reply_text("¡Hola! Soy tu bot que puede resumir mensajes de las últimas 6 horas usando IA. Usa /resumen para obtener un resumen inteligente.")
    
    # Este comando también puede estar disponible para todos
    async def help_command(self, update, context):
        help_text = "🤖 *COMANDOS DISPONIBLES* 🤖\n\n"
        help_text += "• `/start` - Inicia el bot y muestra mensaje de bienvenida\n"
        help_text += "• `/help` - Muestra esta lista de comandos disponibles\n"
        help_text += "• `/resumen` - Genera manualmente un resumen de los mensajes (solo admins)\n"
        help_text += "• `/stop` - Desactiva los resúmenes automáticos (solo admins)\n"
        help_text += "• `/activar_resumenes` - Reactiva los resúmenes automáticos (solo admins)\n\n"
        help_text += "• `/status` - Muestra estadísticas y estado actual del bot (solo admins)\n"
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    @admin_only
    async def generate_summary(self, update, context):
        """Genera un resumen de la conversación reciente"""
        chat_id = update.effective_chat.id
        
        # Verificar si hay mensajes para resumir
        if chat_id not in self.bot_state.group_messages or not self.bot_state.group_messages[chat_id]:
            await update.message.reply_text("No hay mensajes para resumir en este chat.")
            return
            
        # Obtener mensajes recientes (últimas 6 horas)
        hours = self.config["resumen_intervalo_horas"]
        time_threshold = datetime.now() - timedelta(hours=hours)
        recent_messages = [msg for msg in self.bot_state.group_messages[chat_id] 
                          if msg["time"] >= time_threshold]
        
        if not recent_messages:
            await update.message.reply_text(f"No hay mensajes de las últimas {hours} horas para resumir.")
            return
            
        # Formatear los mensajes para la API de OpenAI
        conversation_text = ""
        for msg in recent_messages:
            conversation_text += f"{msg['user']}: {msg['text']}\n"
            
        # Generar resumen
        await update.message.reply_text("Generando resumen... ⏳")
        summary = self.ai_service.generate_summary(conversation_text)
        
        # Enviar resumen
        await update.message.reply_text(f"📝 *Resumen de las últimas {hours} horas:*\n\n{summary}", parse_mode="Markdown")
    
    @admin_only
    async def stop_summaries(self, update, context):
        chat_id = update.effective_chat.id
        self.bot_state.auto_summary_enabled[chat_id] = False
        await update.message.reply_text("✅ Los resúmenes automáticos han sido desactivados para este grupo. Puedes reactivarlos con /activar_resumenes")
    
    @admin_only
    async def enable_summaries(self, update, context):
        chat_id = update.effective_chat.id
        self.bot_state.auto_summary_enabled[chat_id] = True
        await update.message.reply_text("✅ Los resúmenes automáticos han sido reactivados para este grupo.")
    
    @admin_only
    async def status_command(self, update, context):
        """Muestra información sobre el estado del bot"""
        chat_id = update.effective_chat.id
        
        # Información general
        uptime_seconds = time.time() - self.bot_state.start_time
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Uso de memoria
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 / 1024  # En MB
        
        # Información de mensajes
        total_messages = sum(len(msgs) for msgs in self.bot_state.group_messages.values())
        group_count = len(self.bot_state.group_messages)
        
        # Resúmenes automáticos
        auto_summary_status = "Activados" if chat_id in self.bot_state.auto_summary_enabled and self.bot_state.auto_summary_enabled[chat_id] else "Desactivados"
        
        status_text = f"📊 *ESTADO DEL BOT* 📊\n\n"
        status_text += f"⏱️ *Tiempo activo:* {int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s\n"
        status_text += f"💾 *Uso de memoria:* {memory_usage:.2f} MB\n"
        status_text += f"📝 *Mensajes totales:* {total_messages}\n"
        status_text += f"👥 *Grupos atendidos:* {group_count}\n"
        status_text += f"🔄 *Resúmenes automáticos:* {auto_summary_status}\n"
        
        await update.message.reply_text(status_text, parse_mode="Markdown")