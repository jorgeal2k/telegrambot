import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Función para manejar el comando /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("¡Hola! Soy tu bot desplegado en Render.")

# Función para manejar los mensajes de texto
async def echo(update: Update, context: CallbackContext):
    await update.message.reply_text(update.message.text)

# Configurar el bot
def main():
    app = Application.builder().token(TOKEN).build()

    # Agregar manejadores de comandos y mensajes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("El bot está funcionando en Render...")
    app.run_polling()

if __name__ == "__main__":
    main()
