import json
import os
import datetime

class StorageService:
    """Maneja la persistencia de datos del bot"""
    
    @staticmethod
    def save_data(bot_state):
        """Guarda el estado del bot en un archivo JSON"""
        data = {
            "messages": {str(k): v for k, v in bot_state.group_messages.items()},
            "auto_summary": {str(k): v for k, v in bot_state.auto_summary_enabled.items()}
        }
        with open("bot_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, default=str)
    
    @staticmethod
    def load_data(bot_state):
        """Carga el estado del bot desde un archivo JSON"""
        if os.path.exists("bot_data.json"):
            with open("bot_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convertir claves y formatos
                for chat_id_str, messages in data.get("messages", {}).items():
                    for msg in messages:
                        msg["time"] = datetime.datetime.fromisoformat(msg["time"])
                    bot_state.group_messages[int(chat_id_str)] = messages
                    
                for chat_id_str, enabled in data.get("auto_summary", {}).items():
                    bot_state.auto_summary_enabled[int(chat_id_str)] = enabled