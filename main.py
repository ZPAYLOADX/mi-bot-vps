import os
import threading
import subprocess
import string
import random
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import mercadopago

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# CONFIGURACIÓN DE ROLES DE ADMINISTRACIÓN
ADMIN_ID = int(os.getenv("ADMIN_ID", "8096590049")) # ID del Administrador Principal (Tú)
SUBADMIN_IDS = [int(x) for x in os.getenv("SUBADMIN_IDS", "").split(",") if x.strip().isdigit()]

MP_ACCESS_TOKEN = os.getenv("MERCADO_PAGO_TOKEN", "APP_USR-7873838b-66bc-44da-9818-fc975319280c")
DOMAIN_OR_IP = os.getenv("DOMAIN_OR_IP", "http://18.228.59.234:5000")

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

# Mapeo de Planes (Incluyendo Demo)
PLANES_INFO = {
    "demo_7h": {"title": "Demo VPS 7 Horas (1 Conexión)", "price": 120, "days": 0.29, "limite": 1},
    "7dias": {"title": "Plan 7 Días (1 Conexión)", "price": 1222, "days": 7, "limite": 1},
    "7dias_2user": {"title": "Plan 7 Días (2 Conexiones)", "price": 2444, "days": 7, "limite": 2},
    "14dias": {"title": "Plan 14 Días (1 Conexión)", "price": 2333, "days": 14, "limite": 1},
    "30dias": {"title": "Plan 30 Días (1 Conexión)", "price": 3200, "days": 30, "limite": 1}
}

def is_admin(user_id):
    return user_id == ADMIN_ID

def is_subadmin(user_id):
    return user_id in SUBADMIN_IDS or is_admin(user_id)

# Generador de credenciales SSH
def generar_credenciales_ssh(user_id, dias, limite):
    username = f"usr_{user_id}_{random.randint(100, 999)}"
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    try:
        subprocess.run(["sudo", "useradd", "-M", "-s", "/bin/false", username], check=True)
        subprocess.run(["sudo", "chpasswd"], input=f"{username}:{password}".encode(), check=True)
        return username, password
    except Exception as e:
        print(f"Error al crear usuario SSH: {e}")
        return username, password

def crear_preference_mp(plan_key, user_id):
    plan = PLANES_INFO.get(plan_key)
    if not plan:
        return None

    preference_data = {
        "items": [
            {
                "title": plan["title"],
                "quantity": 1,
                "unit_price": float(plan["price"]),
                "currency_id": "ARS"
            }
        ],
        "external_reference": f"{user_id}:{plan_key}",
        "notification_url": f"{DOMAIN_OR_IP}/mercado_pago"
    }

    preference_response = sdk.preference().create(preference_data)
    return preference_response["response"].get("init_point")

# ==========================================
# MENÚS INTERACTIVOS
# ==========================================
def get_main_menu(user_id):
    markup = InlineKeyboardMarkup()
    if is_admin(user_id):
        markup.add(InlineKeyboardButton("👑 Panel Principal Admin", callback_data="admin_panel"))
        markup.add(InlineKeyboardButton("👥 Listar Clientes", callback_data="list_clients"))
        markup.add(InlineKeyboardButton("🔑 Generar Acceso SSH Directo", callback_data="gen_ssh_menu"))
    elif is_subadmin(user_id):
        markup.add(InlineKeyboardButton("🛡️ Panel Subadmin (Verificaciones)", callback_data="subadmin_panel"))
        markup.add(InlineKeyboardButton("🔑 Generar Acceso SSH Directo", callback_data="gen_ssh_menu"))
    else:
        markup.add(InlineKeyboardButton("💳 Comprar Acceso / Demo VPS", callback_data="buy_vps"))
        markup.add(InlineKeyboardButton("📋 Mis Suscripciones", callback_data="my_subs"))
        markup.add(InlineKeyboardButton("❓ Soporte Técnico", callback_data="support"))
    return markup

def get_plans_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🧪 Demo 7 Horas (1 Conexión) - $120 ARS", callback_data="plan_demo_7h"))
    markup.add(InlineKeyboardButton("⚡ 7 Días (1 Conexión) - $1222 ARS", callback_data="plan_7dias"))
    markup.add(InlineKeyboardButton("⚡ 7 Días (2 Conexiones) - $2444 ARS", callback_data="plan_7dias_2user"))
    markup.add(InlineKeyboardButton("🚀 14 Días (1 Conexión) - $2333 ARS", callback_data="plan_14dias"))
    markup.add(InlineKeyboardButton("👑 30 Días (1 Conexión) - $3200 ARS", callback_data="plan_30dias"))
    markup.add(InlineKeyboardButton("⬅️ Volver al Menú", callback_data="main_menu"))
    return markup

def get_manual_gen_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🧪 Generar Demo 7 Horas", callback_data="manual_gen_demo_7h"))
    markup.add(InlineKeyboardButton("⚡ Generar 7 Días", callback_data="manual_gen_7dias"))
    markup.add(InlineKeyboardButton("⚡ Generar 7 Días (2 Conexiones)", callback_data="manual_gen_7dias_2user"))
    markup.add(InlineKeyboardButton("🚀 Generar 14 Días", callback_data="manual_gen_14dias"))
    markup.add(InlineKeyboardButton("👑 Generar 30 Días", callback_data="manual_gen_30dias"))
    markup.add(InlineKeyboardButton("⬅️ Volver al Menú", callback_data="main_menu"))
    return markup

def get_payment_methods_menu(plan_key):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⚡ Mercado Pago (Automático 🤖)", callback_data=f"pay_mp_{plan_key}"))
    markup.add(InlineKeyboardButton("🌐 Binance Pay / PayPal (Manual 📩)", callback_data=f"pay_crypto_{plan_key}"))
    markup.add(InlineKeyboardButton("🏛️ Transferencia Bancaria (Manual 📩)", callback_data=f"pay_bank_{plan_key}"))
    markup.add(InlineKeyboardButton("⬅️ Volver a Planes", callback_data="buy_vps"))
    return markup

# ==========================================
# HANDLERS DEL BOT
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        text = "👑 **Panel de Administrador Principal**\nControl total de la plataforma activo."
    elif is_subadmin(user_id):
        text = "🛡️ **Panel de Subadministrador**\nGestión de accesos y verificación de pagos habilitada."
    else:
        text = "👋 **Bienvenido al Servicio VPS**\nSelecciona una opción para comenzar:"
    bot.send_message(message.chat.id, text, reply_markup=get_main_menu(user_id), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if call.data == "main_menu":
        bot.answer_callback_query(call.id)
        bot.edit_message_text("👋 **Menú Principal**\nSelecciona una opción:", chat_id, call.message.message_id, reply_markup=get_main_menu(user_id), parse_mode="Markdown")

    elif call.data == "buy_vps":
        bot.answer_callback_query(call.id)
        text_planes = (
            "🛒 **Planes VPS y Demos Disponibles**\n\n"
            "⚠️ **Aviso de Seguridad:**\n"
            "Todos los planes corresponden a **1 conexión por usuario** (excepto el plan de 2 conexiones).\n"
            "❌ *Si se detectan más conexiones de las permitidas, la cuenta será suspendida de manera automática.*\n\n"
            "Selecciona el plan o demo que deseas adquirir:"
        )
        bot.edit_message_text(text_planes, chat_id, call.message.message_id, reply_markup=get_plans_menu(), parse_mode="Markdown")

    elif call.data.startswith("plan_"):
        plan_key = call.data.replace("plan_", "")
        plan_info = PLANES_INFO.get(plan_key, {}).get("title", "Plan VPS")
        bot.answer_callback_query(call.id)
        bot.edit_message_text(f"💳 **Método de Pago**\nHas elegido: **{plan_info}**.\n\nSelecciona cómo deseas abonar:", chat_id, call.message.message_id, reply_markup=get_payment_methods_menu(plan_key), parse_mode="Markdown")

    elif call.data.startswith("pay_"):
        parts = call.data.split("_")
        method = parts[1]
        plan_key = "_".join(parts[2:])
        bot.answer_callback_query(call.id)

        markup = InlineKeyboardMarkup()

        if method == "mp":
            init_point = crear_preference_mp(plan_key, user_id)
            if init_point:
                text = (
                    "⚡ **Pago Automático vía Mercado Pago**\n\n"
                    "1. Haz clic en el botón de abajo para abonar.\n"
                    "2. Una vez confirmado el pago de $120 ARS, se activará tu acceso.\n"
                    "3. **Tus credenciales SSH llegarán automáticamente a este chat.**"
                )
                markup.add(InlineKeyboardButton("👉 Pagar con Mercado Pago", url=init_point))
            else:
                text = "❌ Error al generar el enlace de Mercado Pago."
        else:
            text = (
                "🌐 **Verificación Manual (Binance / PayPal / Transferencia)**\n\n"
                "1. Efectúa el pago al medio correspondiente.\n"
                "2. Envía el comprobante al **Administrador** o **Subadmin**.\n"
                "3. Tu cuenta será dada de alta de inmediato mediante el panel de generación."
            )
            markup.add(InlineKeyboardButton("📩 Contactar Soporte", callback_data="support"))

        markup.add(InlineKeyboardButton("⬅️ Volver", callback_data=f"plan_{plan_key}"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "gen_ssh_menu":
        bot.answer_callback_query(call.id)
        if not is_subadmin(user_id):
            bot.send_message(chat_id, "❌ No tienes permisos para esta opción.")
            return
        bot.edit_message_text("🔑 **Generación Manual de Cuentas SSH**\nSelecciona la duración o demo que deseas otorgar:", chat_id, call.message.message_id, reply_markup=get_manual_gen_menu(), parse_mode="Markdown")

    elif call.data.startswith("manual_gen_"):
        bot.answer_callback_query(call.id)
        if not is_subadmin(user_id):
            return
        
        plan_key = call.data.replace("manual_gen_", "")
        plan = PLANES_INFO.get(plan_key)
        
        if plan:
            user_ssh, pass_ssh = generar_credenciales_ssh(user_id, plan["days"], plan["limite"])
            duracion_txt = "7 Horas" if plan_key == "demo_7h" else f"{plan['days']} días"
            msg = (
                f"✅ **Acceso Creado Exitosamente**\n\n"
                f"📦 **Plan:** {plan['title']}\n"
                f"👤 **Usuario SSH:** `{user_ssh}`\n"
                f"🔑 **Contraseña:** `{pass_ssh}`\n"
                f"⌛ **Duración:** {duracion_txt}\n"
                f"📱 **Límite:** {plan['limite']} conexión(es)\n\n"
                "Copie y reenvíe estas credenciales al cliente."
            )
            bot.send_message(chat_id, msg, parse_mode="Markdown")

    elif call.data == "support":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "📩 **Soporte Técnico**\nContacta con la administración para enviar tu comprobante de pago o solicitar asistencia.")

    elif call.data == "my_subs":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "📋 **Tus Suscripciones**\nActualmente no posees cuentas SSH activas.")

# ==========================================
# WEBHOOK DE MERCADO PAGO
# ==========================================
@app.route('/', methods=['GET'])
def index():
    return "Servidor VPS Activo", 200

@app.route('/mercado_pago', methods=['POST'])
def mercado_pago_webhook():
    data = request.args
    topic = data.get("type") or data.get("topic")

    if topic == "payment":
        payment_id = data.get("data.id") or data.get("id")
        if payment_id:
            payment_info = sdk.payment().get(payment_id)["response"]
            if payment_info.get("status") == "approved":
                ext_ref = payment_info.get("external_reference")
                if ext_ref and ":" in ext_ref:
                    user_id_str, plan_key = ext_ref.split(":")
                    user_id = int(user_id_str)
                    plan = PLANES_INFO.get(plan_key)

                    if plan:
                        user_ssh, pass_ssh = generar_credenciales_ssh(user_id, plan["days"], plan["limite"])
                        duracion_txt = "7 Horas" if plan_key == "demo_7h" else f"{plan['days']} Días"
                        msg = (
                            "✅ **¡Pago Confirmado Automáticamente!**\n\n"
                            f"📦 **Servicio:** {plan['title']}\n"
                            f"👤 **Usuario SSH:** `{user_ssh}`\n"
                            f"🔑 **Contraseña:** `{pass_ssh}`\n"
                            f"⌛ **Duración:** {duracion_txt}\n"
                            f"📱 **Límite de Conexiones:** {plan['limite']}\n\n"
                            "⚠️ *No excedas el límite de dispositivos para evitar la suspensión.*"
                        )
                        bot.send_message(user_id, msg, parse_mode="Markdown")

    return jsonify({"status": "ok"}), 200

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
