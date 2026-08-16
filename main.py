import os
import threading
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Reemplaza este número por tu ID real de Telegram
ADMIN_ID = int(os.getenv("ADMIN_ID", "8096590049"))

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# ==========================================
# FUNCIONES DE MENÚS
# ==========================================
def get_main_menu(user_id):
    markup = InlineKeyboardMarkup()
    
    if user_id == ADMIN_ID:
        # Menú exclusivo para el Administrador
        markup.add(InlineKeyboardButton("🛠️ Panel Admin", callback_data="admin_panel"))
        markup.add(InlineKeyboardButton("👥 Listar Clientes", callback_data="list_clients"))
        markup.add(InlineKeyboardButton("🔑 Generar Acceso SSH", callback_data="gen_ssh"))
    else:
        # Menú para Clientes
        markup.add(InlineKeyboardButton("💳 Comprar Acceso VPS", callback_data="buy_vps"))
        markup.add(InlineKeyboardButton("📋 Mis Suscripciones", callback_data="my_subs"))
        markup.add(InlineKeyboardButton("❓ Soporte", callback_data="support"))
        
    return markup

# ==========================================
# COMANDOS DEL BOT
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        text = "👑 **Bienvenido Administrador**\nTienes acceso total al panel de control."
    else:
        text = "👋 **Bienvenido al Servicio VPS**\nSelecciona una opción del menú:"
        
    bot.send_message(message.chat.id, text, reply_markup=get_main_menu(user_id), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id
    
    if call.data == "admin_panel":
        bot.answer_callback_query(call.id, "Cargando panel de administración...")
        bot.send_message(call.message.chat.id, "⚙️ **Panel de Administración VPS**\nAquí puedes gestionar usuarios y servidores.")
    elif call.data == "buy_vps":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🛒 **Planes VPS Disponibles**\nSelecciona el plan que deseas adquirir.")
    else:
        bot.answer_callback_query(call.id, "Opción en desarrollo.")

# ==========================================
# RUTAS DE FLASK
# ==========================================
@app.route('/', methods=['GET'])
def index():
    return "Servidor VPS activo", 200

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
