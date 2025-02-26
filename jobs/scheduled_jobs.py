from datetime import datetime, timedelta

class ScheduledJobs:
    """Maneja las tareas programadas del bot"""
    
    def __init__(self, bot_state, ai_service, config):
        self.bot_state = bot_state
        self.ai_service = ai_service
        self.config = config
    
    async def clean_old_messages(self, context):
        """Elimina mensajes antiguos para liberar memoria"""
        hours = self.config["limpieza_intervalo_horas"]
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        for chat_id in list(self.bot_state.group_messages.keys()):
            self.bot_state.group_messages[chat_id] = [
                msg for msg in self.bot_state.group_messages[chat_id]
                if msg["time"] >= time_threshold
            ]
    
    async def auto_summary(self, context):
        """Genera resúmenes automáticos en los grupos"""
        bot = context.bot
        hours = self.config["resumen_intervalo_horas"]
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        for chat_id in list(self.bot_state.group_messages.keys()):
            # Verificar si los resúmenes automáticos están habilitados
            if not self.bot_state.auto_summary_enabled.get(chat_id, True):
                continue
                
            # Obtener mensajes recientes
            recent_messages = [
                msg for msg in self.bot_state.group_messages[chat_id]
                if msg["time"] >= time_threshold
            ]
            
            if recent_messages:
                # Formatear los mensajes para la API de OpenAI
                conversation_text = ""
                for msg in recent_messages:
                    conversation_text += f"{msg['user']}: {msg['text']}\n"
                
                # Generar y enviar resumen
                try:
                    summary = self.ai_service.generate_summary(conversation_text)
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"📝 *Resumen automático de las últimas {hours} horas:*\n\n{summary}",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Error al enviar resumen automático: {e}")
    
    async def save_data(self, context):
        """Guarda los datos del bot periódicamente"""
        try:
            from services.storage_service import StorageService
            StorageService.save_data(self.bot_state)
        except Exception as e:
            print(f"Error al guardar datos: {e}")