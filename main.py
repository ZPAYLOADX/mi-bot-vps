import os
import threading
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import telebot

# Cargar variables de entorno del archivo .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Declaración explícita de Flask y Telegram Bot
app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# ==========================================
# RUTAS DE FLASK (MERCADO PAGO / WEBHOOKS)
# ==========================================
@app.route('/', methods=['GET'])
def index():
    return "Servidor VPS activo y escuchando", 200

@app.route('/mercado_pago', methods=['POST'])
def mercado_pago_webhook():
    # Lógica de notificación de pagos
    data = request.get_json()
    return jsonify({"status": "ok"}), 200

# ==========================================
# COMANDOS DEL BOT DE TELEGRAM
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Hola! El bot de VPS está activo y listo.")

# ==========================================
# EJECUCIÓN EN PARALELO
# ==========================================
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    print("[+] Iniciando servidor Flask para pagos en segundo plano...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("[+] Iniciando Bot de Telegram en modo Polling directo...")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
