import os
import datetime
from collections import defaultdict
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from openai import OpenAI

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODELO = "gpt-4o"  # Modelo de OpenAI a utilizar

# Inicializar cliente de OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Estructura de datos para almacenar mensajes por grupo
group_messages = defaultdict(list)
# Estructura para controlar qué grupos reciben resúmenes automáticos (por defecto activado=True)
auto_summary_enabled = defaultdict(lambda: True)

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
    else:
        # Si no es un grupo, simplemente hacer eco como en la versión original
        await update.message.reply_text(update.message.text)

# Función para generar un resumen con OpenAI
async def generate_summary(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    
    # Verificar si tenemos mensajes para este grupo
    if chat_id not in group_messages or not group_messages[chat_id]:
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
            conversation_text += f"[{formatted_time}] {msg['user']}: {msg['text']}\n"
        
        # Generar resumen con OpenAI
        response = client.chat.completions.create(
            model=MODELO,  # Puedes cambiar al modelo que prefieras
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
        
        summary_text = f"📊 RESUMEN DE LAS ÚLTIMAS 6 HORAS*\n\n"
        summary_text += f"• Total de mensajes: {total_messages}\n"
        summary_text += f"• Participantes: {', '.join(users)}\n\n"
        summary_text += f"📝 RESUMEN GENERADO POR IA. LLM: {MODELO}:\n\n{ai_summary}\n"
        
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
            conversation_text += f"[{formatted_time}] {msg['user']}: {msg['text']}\n"
        
        try:
            # Generar resumen con OpenAI
            response = client.chat.completions.create(
                model=MODELO,  # Puedes cambiar al modelo que prefieras
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
            
            summary_text = f"📊 **RESUMEN DE LAS ÚLTIMAS 6 HORAS**\n\n"
            summary_text += f"• Total de mensajes: {total_messages}\n"
            summary_text += f"• Participantes: {', '.join(users)}\n\n"
            summary_text += f"📝 **RESUMEN GENERADO POR IA**:\n\n{ai_summary}\n"
            
            # Enviar el resumen al grupo
            await context.bot.send_message(chat_id=chat_id, text=summary_text)
            
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"Error al generar el resumen: {str(e)}")

# Configurar el bot
def main():
    app = Application.builder().token(TOKEN).build()

    # Agregar manejadores de comandos y mensajes
    app.add_handler(CommandHandler("start", start))
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

    print("El bot está funcionando en Render...")
    app.run_polling()

if __name__ == "__main__":
    main()

