from collections import defaultdict
import time
from datetime import datetime

class BotState:
    """Clase para manejar el estado global del bot"""
    
    def __init__(self):
        # Estructura de datos para almacenar mensajes por grupo
        self.group_messages = defaultdict(list)
        # Estructura para controlar resúmenes automáticos
        self.auto_summary_enabled = defaultdict(lambda: True)
        # Tiempo de inicio
        self.start_time = time.time()
    
    def add_message(self, chat_id, user, text, max_messages):
        """Añade un mensaje al historial del grupo"""
        message_data = {
            "user": user,
            "text": text,
            "time": datetime.now()
        }
        self.group_messages[chat_id].append(message_data)
        
        # Limitar el tamaño de la cola de mensajes
        if len(self.group_messages[chat_id]) > max_messages:
            excess = len(self.group_messages[chat_id]) - max_messages
            self.group_messages[chat_id] = self.group_messages[chat_id][excess:]
    
    def get_recent_messages(self, chat_id, hours):
        """Obtiene mensajes recientes de un grupo"""
        from datetime import timedelta
        time_threshold = datetime.now() - timedelta(hours=hours)
        return [msg for msg in self.group_messages[chat_id] 
                if msg["time"] >= time_threshold]