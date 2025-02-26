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

# Configurar sistema de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("telegram_bot")

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializar cliente de OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Variables de configuración centralizadas
CONFIG = {
    "resumen_intervalo_horas": 6,
    "limpieza_intervalo_horas": 24,
    "max_mensajes_por_grupo": 5000,  # Limitar para evitar problemas de memoria
    "modelo_ai": "gpt-4o",
    "max_tokens_resumen": 800
}

# Estructura de datos para almacenar mensajes por grupo
group_messages = defaultdict(list)
# Estructura para controlar qué grupos reciben resúmenes automáticos (por defecto activado=True)
auto_summary_enabled = defaultdict(lambda: True)

# Variable global para almacenar tiempo de inicio
START_TIME = time.time()

# Lista de administradores del bot
ADMIN_USER_IDS = [702356304]  # Reemplazar con IDs reales

# Función para manejar el comando /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("¡Hola! Soy tu bot que puede resumir mensajes de las últimas 6 horas usando IA. Usa /resumen para obtener un resumen inteligente. Para desactivar los resúmenes automáticos usa /stop.")

# Función para manejar el comando /stop (desactivar resúmenes)
async def stop_summaries(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    auto_summary_enabled[chat_id] = False
    await update.message.reply_text("✅ Los resúmenes automáticos han sido desactivados para este grupo. Puedes reactivarlos con /activar_resumenes")

# Función para manejar el comando /activar_resumenes (reactivar resúmenes)
async def enable_summaries(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    auto_summary_enabled[chat_id] = True
    await update.message.reply_text("✅ Los resúmenes automáticos han sido reactivados para este grupo.")

# Función para manejar el comando /help (mostrar comandos disponibles)
async def help_command(update: Update, context: CallbackContext):
    help_text = "🤖 *COMANDOS DISPONIBLES* 🤖\n\n"
    help_text += "• `/start` - Inicia el bot y muestra mensaje de bienvenida\n"
    help_text += "• `/help` - Muestra esta lista de comandos disponibles\n"
    help_text += "• `/resumen` - Genera manualmente un resumen de los mensajes de las últimas 6 horas\n"
    help_text += "• `/stop` - Desactiva los resúmenes automáticos para este grupo\n"
    help_text += "• `/activar_resumenes` - Reactiva los resúmenes automáticos para este grupo\n\n"
    help_text += "• `/status` - Muestra estadísticas y estado actual del bot\n"
    help_text += "ℹ️ El bot genera resúmenes automáticos cada 6 horas si está activada esta opción.\n"
    help_text += "ℹ️ Los mensajes se almacenan temporalmente solo para generar los resúmenes y se eliminan después de 24 horas."
    
    # Enviar mensaje con formato Markdown
    await update.message.reply_text(help_text, parse_mode="Markdown")

# Función para manejar el comando /status
async def status_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Verificar si el usuario es administrador
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("⛔ No tienes permiso para usar este comando.")
        return
    
    # Calcular tiempo de ejecución
    uptime_seconds = int(time.time() - START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    
    # Obtener información de memoria
    process = psutil.Process(os.getpid())
    memory_usage = process.memory_info().rss / 1024 / 1024  # En MB
    
    # Recopilar estadísticas
    total_groups = len(group_messages)
    total_messages = sum(len(messages) for messages in group_messages.values())
    
    # Recopilar estado de resúmenes por grupo
    groups_with_auto = sum(1 for chat_id in group_messages if auto_summary_enabled[chat_id])
    groups_without_auto = total_groups - groups_with_auto
    
    # Crear mensaje de estado
    status_text = "📊 *ESTADO DEL SERVICIO* 📊\n\n"
    status_text += f"⏱️ *Tiempo activo:* {uptime_str}\n"
    status_text += f"👥 *Grupos monitorizados:* {total_groups}\n"
    status_text += f"💬 *Total de mensajes almacenados:* {total_messages}\n\n"
    status_text += f"🔄 *Resúmenes automáticos:*\n"
    status_text += f"  ✅ Grupos con resúmenes automáticos: {groups_with_auto}\n"
    status_text += f"  ❌ Grupos sin resúmenes automáticos: {groups_without_auto}\n\n"
    
    # Próximo resumen automático
    next_job = None
    for job in context.job_queue.jobs():
        if job.callback.__name__ == 'auto_summary':
            next_job = job
            break
    
    if next_job:
        next_run = next_job.next_t.replace(microsecond=0)
        status_text += f"⏰ *Próximo resumen automático:* {next_run}\n\n"
    
    status_text += f"🖥️ *Uso de memoria:* {memory_usage:.2f} MB\n"
    status_text += f"🤖 *Modelo de IA:* {CONFIG['modelo_ai']}"
    
    # Enviar mensaje con formato Markdown
    await update.message.reply_text(status_text, parse_mode="Markdown")

# Función para capturar y almacenar mensajes
async def store_message(update: Update, context: CallbackContext):
    # Verificar si el mensaje viene de un grupo
    if update.effective_chat.type in ["group", "supergroup"]:
        chat_id = update.effective_chat.id
        user = update.effective_user.first_name
        text = update.message.text
        timestamp = datetime.datetime.now()
        
        # Guardar el mensaje con su timestamp y usuario
        message_data = {
            "user": user,
            "text": text,
            "time": timestamp
        }
        group_messages[chat_id].append(message_data)
        
        # Limitar el tamaño de la cola de mensajes por grupo
        if len(group_messages[chat_id]) > CONFIG["max_mensajes_por_grupo"]:
            # Eliminar los mensajes más antiguos
            excess = len(group_messages[chat_id]) - CONFIG["max_mensajes_por_grupo"]
            group_messages[chat_id] = group_messages[chat_id][excess:]
    else:
        # Si no es un grupo, simplemente hacer eco como en la versión original
        await update.message.reply_text(update.message.text)

# Optimizar el uso de tokens en resúmenes largos
async def generate_optimized_summary(messages, model=CONFIG["modelo_ai"]):
    # Si hay muchos mensajes, agruparlos por usuario o período
    if len(messages) > 200:  # Umbral arbitrario donde podríamos empezar a preocuparnos por tokens
        # Crear resumen de alto nivel
        summary_by_hour = {}
        for msg in messages:
            hour = msg["time"].strftime("%H:00")
            if hour not in summary_by_hour:
                summary_by_hour[hour] = {"users": set(), "msg_count": 0, "sample": []}
            
            summary_by_hour[hour]["users"].add(msg["user"])
            summary_by_hour[hour]["msg_count"] += 1
            if len(summary_by_hour[hour]["sample"]) < 5:  # Solo guardar algunos mensajes de muestra
                summary_by_hour[hour]["sample"].append(msg)
        
        # Crear texto optimizado para enviar a la API
        conversation_text = "Resumen por horas:\n\n"
        for hour, data in sorted(summary_by_hour.items()):
            conversation_text += f"[{hour}] {data['msg_count']} mensajes de {', '.join(data['users'])}\n"
            conversation_text += "Ejemplos:\n"
            for sample in data["sample"]:
                conversation_text += f"- {sample['user']}: {sample['text'][:50]}...\n"
            conversation_text += "\n"
    else:
        # Procesamiento normal para conversaciones más cortas
        conversation_text = ""
        for msg in messages:
            formatted_time = msg["time"].strftime("%H:%M:%S")
            conversation_text += f"[{formatted_time}] {msg["user"]}: {msg["text"]}\n"
    
    # Resto del código para generar el resumen con OpenAI...

# Función para generar un resumen con OpenAI
async def generate_summary(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    
    # Verificar si tenemos mensajes para este grupo
    if (chat_id not in group_messages or not group_messages[chat_id]):
        await update.message.reply_text("No hay mensajes para resumir en este grupo.")
        return
    
    # Calcular el límite de tiempo (6 horas atrás)
    time_threshold = datetime.datetime.now() - datetime.timedelta(hours=6)
    
    # Filtrar mensajes de las últimas 6 horas
    recent_messages = [msg for msg in group_messages[chat_id] if msg["time"] >= time_threshold]
    
    if not recent_messages:
        await update.message.reply_text("No hay mensajes en las últimas 6 horas.")
        return
    
    # Informar que estamos generando el resumen
    processing_message = await update.message.reply_text("Generando resumen con IA... Esto puede tomar unos segundos.")
    
    try:
        # Preparar los mensajes en un formato legible
        conversation_text = ""
        for msg in recent_messages:
            formatted_time = msg["time"].strftime("%H:%M:%S")
            conversation_text += f"[{formatted_time}] {msg["user"]}: {msg["text"]}\n"
        
        # Generar resumen con OpenAI
        response = client.chat.completions.create(
            model=CONFIG["modelo_ai"],  # Puedes cambiar al modelo que prefieras
            messages=[
                {"role": "system", "content": "Eres un asistente que resume conversaciones de grupos **en TELEGRAM**. Genera un resumen completo de la siguiente conversación de hasta 800 palabras, identificando los temas principales, participantes **clave** y conclusiones importantes. El resumen debe estar en español y ser fácil de leer. Debes usar un estilo informal. Debes usar un formato de lista ordenada. Haz uso de emoticonos y emojis típicos de un mensaje de Telegram."},
                {"role": "user", "content": f"Resume la siguiente conversación de las últimas 6 horas:\n\n{conversation_text}"}
            ],
            max_tokens=800
        )
        
        # Obtener el resumen generado
        ai_summary = response.choices[0].message.content
        
        # Añadir estadísticas básicas
        total_messages = len(recent_messages)
        users = set(msg["user"] for msg in recent_messages)
        
        summary_text = f"📊 *RESUMEN DE LAS ÚLTIMAS 6 HORAS*\n\n"
        summary_text += f"• Total de mensajes: {total_messages}\n"
        summary_text += f"• Participantes: {', '.join(users)}\n\n"
        summary_text += f"📝 *RESUMEN GENERADO POR IA. LLM: {CONFIG['modelo_ai']}*\n\n{ai_summary}\n"
        
        # Editar el mensaje de "generando resumen" con el resultado final
        await processing_message.edit_text(summary_text)
        
    except Exception as e:
        await processing_message.edit_text(f"Error al generar el resumen: {str(e)}")

# Función para limpiar mensajes antiguos (más de 24 horas)
async def clean_old_messages(context: CallbackContext):
    time_threshold = datetime.datetime.now() - datetime.timedelta(hours=24)
    
    for chat_id in group_messages:
        group_messages[chat_id] = [msg for msg in group_messages[chat_id] if msg["time"] >= time_threshold]

# Función para generar resúmenes automáticos
async def auto_summary(context: CallbackContext):
    for chat_id in group_messages:
        # Verificar si los resúmenes automáticos están activados para este grupo
        if not auto_summary_enabled[chat_id]:
            continue
            
        # Calcular el límite de tiempo (6 horas atrás)
        time_threshold = datetime.datetime.now() - datetime.timedelta(hours=6)
        
        # Filtrar mensajes de las últimas 6 horas
        recent_messages = [msg for msg in group_messages[chat_id] if msg["time"] >= time_threshold]
        
        if not recent_messages:
            continue
        
        # Preparar los mensajes en un formato legible
        conversation_text = ""
        for msg in recent_messages:
            formatted_time = msg["time"].strftime("%H:%M:%S")
            conversation_text += f"[{formatted_time}] {msg["user"]}: {msg["text"]}\n"
        
        try:
            # Generar resumen con OpenAI
            response = client.chat.completions.create(
                model=CONFIG["modelo_ai"],  # Puedes cambiar al modelo que prefieras
                messages=[
                    {"role": "system", "content": "Eres un asistente que resume conversaciones de grupos. Genera un resumen conciso pero completo de la siguiente conversación, identificando los temas principales, participantes clave y conclusiones importantes. El resumen debe estar en español y ser fácil de leer. Debes usar un estilo humorístico e informal."},
                    {"role": "user", "content": f"Resume la siguiente conversación de las últimas 6 horas:\n\n{conversation_text}"}
                ],
                max_tokens=800
            )
            
            # Obtener el resumen generado
            ai_summary = response.choices[0].message.content
            
            # Añadir estadísticas básicas
            total_messages = len(recent_messages)
            users = set(msg["user"] for msg in recent_messages)
            
            summary_text = f"📊 *RESUMEN DE LAS ÚLTIMAS 6 HORAS*\n\n"
            summary_text += f"• Total de mensajes: {total_messages}\n"
            summary_text += f"• Participantes: {', '.join(users)}\n\n"
            summary_text += f"📝 *RESUMEN GENERADO POR IA. LLM: {CONFIG['modelo_ai']}*\n\n{ai_summary}\n"
            
            # Enviar el resumen al grupo
            await context.bot.send_message(chat_id=chat_id, text=summary_text)
            
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"Error al generar el resumen: {str(e)}")

# Implementar almacenamiento persistente
import json
import os

# Funciones para guardar y cargar datos
def save_data():
    data = {
        "messages": {str(k): v for k, v in group_messages.items()},
        "auto_summary": {str(k): v for k, v in auto_summary_enabled.items()}
    }
    with open("bot_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, default=str)

def load_data():
    if os.path.exists("bot_data.json"):
        with open("bot_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            # Convertir las claves de string a enteros para los IDs de chat
            for chat_id_str, messages in data.get("messages", {}).items():
                for msg in messages:
                    msg["time"] = datetime.datetime.fromisoformat(msg["time"])
                group_messages[int(chat_id_str)] = messages
            for chat_id_str, enabled in data.get("auto_summary", {}).items():
                auto_summary_enabled[int(chat_id_str)] = enabled

# Añadir al main() para guardar datos cada cierto tiempo
async def save_data_job(context: CallbackContext):
    save_data()
    logger.info("Datos guardados correctamente")

# Función para manejar errores mejorada
async def error_handler(update: Update, context: CallbackContext) -> None:
    """Gestiona los errores de la aplicación."""
    error = context.error
    
    # Errores específicos comunes
    if isinstance(error, telegram.error.NetworkError):
        print(f"Error de red: {error}")
    elif isinstance(error, telegram.error.TelegramError):
        print(f"Error de la API de Telegram: {error}")
    elif isinstance(error, openai.APIError):
        print(f"Error de la API de OpenAI: {error}")
    else:
        print(f"Error no identificado: {error}")
    
    # Registro del error completo
    import traceback
    traceback.print_exc()

# Configurar el bot
def main():
    app = Application.builder().token(TOKEN).build()

    # Cargar datos persistentes
    load_data()

    # Agregar manejadores de comandos y mensajes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))  # Añadir el nuevo comando status
    app.add_handler(CommandHandler("resumen", generate_summary))
    app.add_handler(CommandHandler("stop", stop_summaries))
    app.add_handler(CommandHandler("activar_resumenes", enable_summaries))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, store_message))
    
    # Programar tareas periódicas
    job_queue = app.job_queue
    
    # Tarea 1: Limpiar mensajes antiguos cada 6 horas
    job_queue.run_repeating(clean_old_messages, interval=21600, first=10)
    
    # Tarea 2: Generar resúmenes automáticos cada 6 horas
    job_queue.run_repeating(auto_summary, interval=21600, first=21600)

    # Tarea 3: Guardar datos cada 30 minutos
    job_queue.run_repeating(save_data_job, interval=1800, first=300)  # Guardar cada 30 minutos

    logger.info("El bot está iniciando...")
    # En Railway, utilizaremos polling ya que es más sencillo y funciona bien
    app.run_polling()

if __name__ == "__main__":
    main()

