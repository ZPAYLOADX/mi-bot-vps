import os
import threading
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8096590049")) 

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# ==========================================
# MENÚS INTERACTIVOS
# ==========================================
def get_main_menu(user_id):
    markup = InlineKeyboardMarkup()
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("🛠️ Panel Admin", callback_data="admin_panel"))
        markup.add(InlineKeyboardButton("👥 Listar Clientes", callback_data="list_clients"))
        markup.add(InlineKeyboardButton("🔑 Generar Acceso SSH Directo", callback_data="gen_ssh"))
    else:
        markup.add(InlineKeyboardButton("💳 Comprar Acceso VPS", callback_data="buy_vps"))
        markup.add(InlineKeyboardButton("📋 Mis Suscripciones", callback_data="my_subs"))
        markup.add(InlineKeyboardButton("❓ Soporte Técnico", callback_data="support"))
    return markup

def get_plans_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⚡ 7 Días (1 Conexión) - $1222", callback_data="plan_7dias"))
    markup.add(InlineKeyboardButton("⚡ 7 Días (2 Conexiones) - $2444", callback_data="plan_7dias_2user"))
    markup.add(InlineKeyboardButton("🚀 14 Días (1 Conexión) - $2333", callback_data="plan_14dias"))
    markup.add(InlineKeyboardButton("👑 30 Días (1 Conexión) - $3200", callback_data="plan_30dias"))
    markup.add(InlineKeyboardButton("⬅️ Volver al Menú", callback_data="main_menu"))
    return markup

def get_payment_methods_menu(plan_key):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🇦🇷 Mercado Pago", callback_data=f"pay_mp_{plan_key}"))
    markup.add(InlineKeyboardButton("🌐 Binance Pay / USDT", callback_data=f"pay_crypto_{plan_key}"))
    markup.add(InlineKeyboardButton("🏛️ Transferencia Bancaria", callback_data=f"pay_bank_{plan_key}"))
    markup.add(InlineKeyboardButton("⬅️ Volver a Planes", callback_data="buy_vps"))
    return markup

# ==========================================
# BOT COMANDOS Y CALLBACKS
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        text = "👑 **Panel de Administrador**\nGestión de servidor y clientes activa."
    else:
        text = "👋 **Bienvenido al Servicio VPS**\nSelecciona una opción para comenzar:"
    bot.send_message(message.chat.id, text, reply_markup=get_main_menu(user_id), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if call.data == "main_menu":
        bot.answer_callback_query(call.id)
        bot.edit_message_text("👋 **Bienvenido al Servicio VPS**\nSelecciona una opción:", chat_id, call.message.message_id, reply_markup=get_main_menu(user_id), parse_mode="Markdown")

    elif call.data == "buy_vps":
        bot.answer_callback_query(call.id)
        text_planes = (
            "🛒 **Planes VPS Disponibles**\n\n"
            "⚠️ **Aviso de Seguridad:**\n"
            "Todos los planes corresponden a **1 conexión por usuario** (a excepción del plan especificado para 2 conexiones).\n"
            "❌ *Si se detectan más conexiones de las permitidas, la cuenta será suspendida de manera automática sin derecho a reclamo.*\n\n"
            "Selecciona el plan que deseas adquirir:"
        )
        bot.edit_message_text(text_planes, chat_id, call.message.message_id, reply_markup=get_plans_menu(), parse_mode="Markdown")

    elif call.data.startswith("plan_"):
        plan_key = call.data.replace("plan_", "")
        
        # Mapeo de precios y nombres
        detalles = {
            "7dias": "7 Días (1 Conexión) por $1222",
            "7dias_2user": "7 Días (2 Conexiones) por $2444",
            "14dias": "14 Días (1 Conexión) por $2333",
            "30dias": "30 Días (1 Conexión) por $3200"
        }
        
        plan_info = detalles.get(plan_key, "Plan VPS")
        bot.answer_callback_query(call.id)
        bot.edit_message_text(f"💳 **Método de Pago**\nHas elegido el **Plan {plan_info}**.\n\nSelecciona cómo deseas abonar:", chat_id, call.message.message_id, reply_markup=get_payment_methods_menu(plan_key), parse_mode="Markdown")

    elif call.data.startswith("pay_"):
        parts = call.data.split("_")
        method = parts[1]
        plan_key = "_".join(parts[2:])
        bot.answer_callback_query(call.id)

        if method == "mp":
            text = f"🇦🇷 **Pago vía Mercado Pago**\n\nRealiza el pago correspondiente a tu plan seleccionado. Al confirmarse, el bot generará tus credenciales automáticamente."
        elif method == "crypto":
            text = f"🌐 **Pago vía Binance / Crypto (USDT)**\n\nEnvía el equivalente en USDT y presiona solicitar verificación."
        else:
            text = f"🏛️ **Transferencia Bancaria**\n\nEfectúa la transferencia a los datos indicados y envía el comprobante al soporte."

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅️ Volver", callback_data=f"plan_{plan_key}"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "support":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "📩 **Soporte Técnico**\nContacta directamente al administrador si posees dudas o inconvenientes con tu servicio.")

    elif call.data == "my_subs":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "📋 **Tus Suscripciones**\nActualmente no posees cuentas SSH activas.")

# ==========================================
# RUTAS DE FLASK
# ==========================================
@app.route('/', methods=['GET'])
def index():
    return "Servidor VPS Activo", 200

@app.route('/mercado_pago', methods=['POST'])
def mercado_pago_webhook():
    return jsonify({"status": "ok"}), 200

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
