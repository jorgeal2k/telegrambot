from datetime import datetime

class MessageHandlers:
    """Manejadores para los mensajes del bot"""
    
    def __init__(self, bot_state, config):
        self.bot_state = bot_state
        self.config = config
    
    async def store_message(self, update, context):
        """Almacena un mensaje en el historial del grupo"""
        message = update.message
        chat_id = message.chat_id
        user = message.from_user.first_name
        text = message.text
        
        # Almacenar el mensaje en el estado del bot
        self.bot_state.group_messages[chat_id].append({
            "user": user,
            "text": text,
            "time": datetime.now()
        })
        
        # Limitar la cantidad de mensajes almacenados
        max_msgs = self.config["max_mensajes_por_grupo"]
        if len(self.bot_state.group_messages[chat_id]) > max_msgs:
            excess = len(self.bot_state.group_messages[chat_id]) - max_msgs
            self.bot_state.group_messages[chat_id] = self.bot_state.group_messages[chat_id][excess:]