import os
import random
import string
import subprocess
import logging
from flask import Flask, request, jsonify
import threading
import paramiko
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)
import mercadopago

# ==========================================
# CONFIGURACIÓN GENERAL Y CREDENCIALES
# ==========================================
TELEGRAM_BOT_TOKEN = "8385538827:AAHuS3-mcHEKuDJbqDqc0hPKhsu_OjHBuHw"
ADMIN_ID = 8096590049  # Cambia por tu ID numérico de Telegram si difiere
SUBADMIN_IDS = []

MERCADO_PAGO_TOKEN = "APP_USR-7603040831612231-081604-a3bf932e40bc0add1c6a00ea941552df-453483723"
DOMAIN_OR_IP = "http://18.228.59.234:5000"

BINANCE_ID = "108562138"
PAYPAL_URL = "https://www.paypal.me/Graciasxtudonacio"
SUPPORT_USERNAME = "@Devstudio_MP"
APP_DOWNLOAD_URL = "https://bit.ly/VPNMXAR"

# ==========================================
# CONFIGURACIÓN DE SERVIDORES Y REGIONES
# ==========================================
# Modifica estas IPs y credenciales SSH de acceso remoto según corresponda
SERVIDORES_REGION = {
    "us": {
        "nombre": "🇺🇸 Estados Unidos",
        "ip": "78.13.49.7",
        "port": 22,
        "user": "root",
        "password": "master99@@"
    },
    "br": {
        "nombre": "🇧🇷 Brasil",
        "ip": "18.228.59.234",
        "port": 22,
        "user": "root",
        "password": "master9900@@"
    },
    "ar": {
        "nombre": "🇦🇷 Argentina",
        "ip": "147.78.123.152",
        "port": 22,
        "user": "root",
        "password": "lQw3LqCAEaJWVyMlbOWx"
    }
}

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialización SDK Mercado Pago y Flask
sdk = mercadopago.SDK(MERCADO_PAGO_TOKEN)
app = Flask(__name__)

# Precios base en ARS por 1 conexión
PLANES_BASE = {
    "demo_7h": {"name": "🧪 Demo VPS (7 Horas)", "base_price": 120, "days": 0.29},
    "7dias": {"name": "⚡ Plan 7 Días", "base_price": 1222, "days": 7},
    "14dias": {"name": "🚀 Plan 14 Días", "base_price": 2333, "days": 14},
    "30dias": {"name": "👑 Plan 30 Días", "base_price": 3200, "days": 30}
}

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID or user_id in SUBADMIN_IDS

# Generador y Administrador SSH Remoto vía Paramiko
def crear_usuario_ssh_remoto(region_code: str, user_id: int, conexiones: int):
    username = f"usr_{user_id}_{random.randint(100, 999)}"
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    server_info = SERVIDORES_REGION.get(region_code, SERVIDORES_REGION["us"])
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Conexión SSH al servidor específico
        ssh.connect(
            hostname=server_info["ip"],
            port=server_info["port"],
            username=server_info["user"],
            password=server_info["password"],
            timeout=10
        )
        
        cmd_useradd = f"sudo useradd -M -s /bin/false {username}"
        cmd_chpasswd = f"echo '{username}:{password}' | sudo chpasswd"
        
        ssh.exec_command(cmd_useradd)
        ssh.exec_command(cmd_chpasswd)
        ssh.close()
        logger.info(f"Usuario {username} creado exitosamente en {server_info['nombre']} ({server_info['ip']})")
    except Exception as e:
        logger.error(f"Error creando usuario remoto en {server_info['ip']}: {e}")
        # Fallback local en caso de error de conexión remota
        try:
            subprocess.run(["sudo", "useradd", "-M", "-s", "/bin/false", username], check=True)
            subprocess.run(["sudo", "chpasswd"], input=f"{username}:{password}".encode(), check=True)
        except Exception as local_err:
            logger.error(f"Error local en useradd: {local_err}")

    return username, password, server_info["nombre"]

def crear_preference_mp(plan_key: str, conexiones: int, region_code: str, user_id: int):
    plan = PLANES_BASE.get(plan_key)
    if not plan:
        return None
        
    precio_total = float(plan["base_price"] * conexiones)
    region_info = SERVIDORES_REGION.get(region_code, SERVIDORES_REGION["us"])
    
    preference_data = {
        "items": [
            {
                "title": f"{plan['name']} - {region_info['nombre']} ({conexiones} Conexión/es)",
                "quantity": 1,
                "unit_price": precio_total,
                "currency_id": "ARS"
            }
        ],
        "external_reference": f"{user_id}:{plan_key}:{conexiones}:{region_code}",
        "notification_url": f"{DOMAIN_OR_IP}/mercado_pago"
    }

    response = sdk.preference().create(preference_data)
    return response.get("response", {}).get("init_point")

# ==========================================
# TECLADOS E INTERFAZ DE TELEGRAM
# ==========================================
def get_main_menu(user_id: int):
    buttons = [
        [InlineKeyboardButton("🛒 Comprar VPS / Solicitar Demo", callback_data="buy_vps")],
        [InlineKeyboardButton("📲 Descargar Aplicación VPN", url=APP_DOWNLOAD_URL)],
        [InlineKeyboardButton("❓ Soporte Técnico Directo", url=f"https://t.me/{SUPPORT_USERNAME.replace('@','')}")],
    ]
    if is_admin(user_id):
        buttons.append([InlineKeyboardButton("👑 Panel de Administración", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

def get_plans_menu():
    buttons = [
        [InlineKeyboardButton("🧪 Demo 7 Horas ($120 ARS/conn)", callback_data="sel_demo_7h")],
        [InlineKeyboardButton("⚡ Plan 7 Días ($1222 ARS/conn)", callback_data="sel_7dias")],
        [InlineKeyboardButton("🚀 Plan 14 Días ($2333 ARS/conn)", callback_data="sel_14dias")],
        [InlineKeyboardButton("👑 Plan 30 Días ($3200 ARS/conn)", callback_data="sel_30dias")],
        [InlineKeyboardButton("⬅️ Volver al Menú", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_connections_menu(plan_key: str):
    buttons = []
    plan = PLANES_BASE[plan_key]
    for c in range(1, 6):
        precio = plan['base_price'] * c
        buttons.append([InlineKeyboardButton(f"📱 {c} Conexión(es) - ${precio} ARS", callback_data=f"region_{plan_key}_{c}")])
    buttons.append([InlineKeyboardButton("⬅️ Seleccionar otro plan", callback_data="buy_vps")])
    return InlineKeyboardMarkup(buttons)

def get_region_menu(plan_key: str, conexiones: int):
    buttons = [
        [InlineKeyboardButton("🇺🇸 Estados Unidos", callback_data=f"checkout_{plan_key}_{conexiones}_us")],
        [InlineKeyboardButton("🇧🇷 Brasil", callback_data=f"checkout_{plan_key}_{conexiones}_br")],
        [InlineKeyboardButton("🇦🇷 Argentina", callback_data=f"checkout_{plan_key}_{conexiones}_ar")],
        [InlineKeyboardButton("⬅️ Volver a conexiones", callback_data=f"sel_{plan_key}")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_payment_methods_menu(plan_key: str, conexiones: int, region_code: str):
    buttons = [
        [InlineKeyboardButton("⚡ Mercado Pago (Automático 🤖)", callback_data=f"pay_mp_{plan_key}_{conexiones}_{region_code}")],
        [InlineKeyboardButton("🌐 Binance Pay / PayPal (Manual 📩)", callback_data=f"pay_crypto_{plan_key}_{conexiones}_{region_code}")],
        [InlineKeyboardButton("⬅️ Volver", callback_data=f"region_{plan_key}_{conexiones}")]
    ]
    return InlineKeyboardMarkup(buttons)

# ==========================================
# HANDLERS Y MENSAJES
# ==========================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    welcome_text = (
        f"👋 **Bienvenido a Servidores VPS High Speed**\n\n"
        f"Conexiones SSH de alto rendimiento y baja latencia.\n"
        f"📲 Descarga nuestra App oficial para conectarte.\n"
        f"📩 Atención & Soporte Oficial: {SUPPORT_USERNAME}\n\n"
        f"Selecciona una opción del menú:"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_menu(user_id), parse_mode="Markdown")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    await query.answer()

    if data == "main_menu":
        await query.edit_message_text("👋 **Menú Principal**\nSelecciona una opción:", reply_markup=get_main_menu(user_id), parse_mode="Markdown")

    elif data == "buy_vps":
        text = "🛒 **Selecciona la duración de tu suscripción o demo:**"
        await query.edit_message_text(text, reply_markup=get_plans_menu(), parse_mode="Markdown")

    elif data.startswith("sel_"):
        plan_key = data.replace("sel_", "")
        plan = PLANES_BASE[plan_key]
        text = f"📱 **Elige cuántas conexiones simultáneas necesitas para:**\n*{plan['name']}*"
        await query.edit_message_text(text, reply_markup=get_connections_menu(plan_key), parse_mode="Markdown")

    elif data.startswith("region_"):
        _, plan_key, conexiones = data.split("_")
        conexiones = int(conexiones)
        text = "🌐 **Selecciona la ubicación/región para tu servidor VPS:**"
        await query.edit_message_text(text, reply_markup=get_region_menu(plan_key, conexiones), parse_mode="Markdown")

    elif data.startswith("checkout_"):
        _, plan_key, conexiones, region_code = data.split("_")
        conexiones = int(conexiones)
        plan = PLANES_BASE[plan_key]
        region_info = SERVIDORES_REGION.get(region_code, SERVIDORES_REGION["us"])
        precio_total = plan['base_price'] * conexiones
        text = (
            f"📋 **Resumen del Pedido**\n\n"
            f"📦 **Servicio:** {plan['name']}\n"
            f"🌐 **Ubicación:** {region_info['nombre']}\n"
            f"📱 **Conexiones:** {conexiones}\n"
            f"💰 **Total a Pagar:** ${precio_total} ARS\n\n"
            f"Selecciona tu método de pago preferido:"
        )
        await query.edit_message_text(text, reply_markup=get_payment_methods_menu(plan_key, conexiones, region_code), parse_mode="Markdown")

    elif data.startswith("pay_mp_"):
        _, _, plan_key, conexiones, region_code = data.split("_")
        conexiones = int(conexiones)
        init_point = crear_preference_mp(plan_key, conexiones, region_code, user_id)
        
        if init_point:
            buttons = [[InlineKeyboardButton("👉 Pagar con Mercado Pago", url=init_point)], [InlineKeyboardButton("⬅️ Volver", callback_data=f"checkout_{plan_key}_{conexiones}_{region_code}")]]
            text = (
                "⚡ **Pago Automático vía Mercado Pago**\n\n"
                "1. Presiona el botón de abajo para abonar.\n"
                "2. Tras acreditarse, **el bot te entregará tus credenciales SSH de forma automática aquí en segundos.**"
            )
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        else:
            await query.edit_message_text("❌ Error al conectar con Mercado Pago. Intenta nuevamente.", reply_markup=get_main_menu(user_id))

    elif data.startswith("pay_crypto_"):
        _, _, plan_key, conexiones, region_code = data.split("_")
        plan = PLANES_BASE[plan_key]
        region_info = SERVIDORES_REGION.get(region_code, SERVIDORES_REGION["us"])
        precio_total = plan['base_price'] * int(conexiones)
        
        text = (
            "🌐 **Instrucciones para Pago Internacional / Cripto**\n\n"
            f"🌐 **Servidor:** {region_info['nombre']}\n"
            f"🟡 **Binance Pay ID:** `{BINANCE_ID}`\n"
            f"💙 **PayPal:** [Clic para Pagar vía PayPal]({PAYPAL_URL})\n\n"
            f"📌 **Monto a Confirmar:** equivalente a ${precio_total} ARS\n\n"
            f"✅ **Pasos siguientes:**\n"
            f"1. Realiza el pago por el monto seleccionado.\n"
            f"2. Envía la captura/comprobante a soporte: {SUPPORT_USERNAME}\n"
            f"3. Incluye tu ID de Telegram y Región en el mensaje: `{user_id}` ({region_code.upper()})"
        )
        buttons = [[InlineKeyboardButton("📩 Enviar Comprobante", url=f"https://t.me/{SUPPORT_USERNAME.replace('@','')}")], [InlineKeyboardButton("⬅️ Volver al Menú", callback_data="main_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown", disable_web_page_preview=True)

    elif data == "admin_panel":
        if not is_admin(user_id):
            return
        text = (
            "👑 **Panel del Administrador**\n\n"
            "Para activar a un usuario manualmente que pagó por Binance/PayPal/Transferencia, usa el comando:\n"
            "`/alta <id_telegram> <dias> <conexiones> <region_code>`\n\n"
            "**Regiones disponibles:** `us`, `br`, `ar`\n"
            "**Ejemplo:** `/alta 123456789 30 2 us`"
        )
        await query.edit_message_text(text, reply_markup=get_main_menu(user_id), parse_mode="Markdown")

# Comando de Alta Manual por Admin
async def alta_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    try:
        target_id = int(context.args[0])
        dias = float(context.args[1])
        conexiones = int(context.args[2])
        region_code = context.args[3].lower() if len(context.args) > 3 else "us"

        ssh_usr, ssh_pwd, region_nombre = crear_usuario_ssh_remoto(region_code, target_id, conexiones)
        
        msg_cliente = (
            f"✅ **¡Tu servicio VPS ha sido activado!**\n\n"
            f"🌐 **Ubicación:** {region_nombre}\n"
            f"👤 **Usuario SSH:** `{ssh_usr}`\n"
            f"🔑 **Contraseña:** `{ssh_pwd}`\n"
            f"⌛ **Duración:** {dias} días\n"
            f"📱 **Conexiones Permitidas:** {conexiones}\n\n"
            f"📲 **Descarga la app para conectarte:** {APP_DOWNLOAD_URL}\n"
            f"💬 Soporte Oficial: {SUPPORT_USERNAME}"
        )
        
        await context.bot.send_message(chat_id=target_id, text=msg_cliente, parse_mode="Markdown")
        await update.message.reply_text(f"✅ Usuario {target_id} activado exitosamente en {region_nombre}:\nSSH: `{ssh_usr}`", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text("❌ **Sintaxis incorrecta.** Uso: `/alta <id_telegram> <dias> <conexiones> <region_code>` (ej: `/alta 123456789 30 2 us`)")

# ==========================================
# WEBHOOK SERVIDOR FLASK (Mercado Pago)
# ==========================================
@app.route('/mercado_pago', methods=['POST'])
def mercado_pago_webhook():
    data = request.args
    topic = data.get("type") or data.get("topic")

    if topic == "payment":
        payment_id = data.get("data.id") or data.get("id")
        if payment_id:
            payment_info = sdk.payment().get(payment_id).get("response", {})
            if payment_info.get("status") == "approved":
                ext_ref = payment_info.get("external_reference", "")
                if ":" in ext_ref:
                    parts = ext_ref.split(":")
                    user_id = int(parts[0])
                    plan_key = parts[1]
                    conexiones = int(parts[2])
                    region_code = parts[3] if len(parts) > 3 else "us"
                    
                    plan = PLANES_BASE.get(plan_key)

                    if plan:
                        ssh_usr, ssh_pwd, region_nombre = crear_usuario_ssh_remoto(region_code, user_id, conexiones)
                        
                        msg_cliente = (
                            f"✅ **¡Pago Confirmado Automáticamente!**\n\n"
                            f"📦 **Servicio:** {plan['name']}\n"
                            f"🌐 **Ubicación:** {region_nombre}\n"
                            f"👤 **Usuario SSH:** `{ssh_usr}`\n"
                            f"🔑 **Contraseña:** `{ssh_pwd}`\n"
                            f"📱 **Conexiones:** {conexiones}\n\n"
                            f"📲 **Descarga la app para conectarte:** {APP_DOWNLOAD_URL}\n"
                            f"💬 Soporte Técnico: {SUPPORT_USERNAME}"
                        )
                        
                        # Notificación al Admin
                        msg_admin = (
                            f"💰 **¡NUEVA VENTA CONFIRMADA!**\n\n"
                            f"👤 **Cliente ID:** `{user_id}`\n"
                            f"📦 **Plan:** {plan['name']}\n"
                            f"🌐 **Servidor:** {region_nombre}\n"
                            f"📱 **Conexiones:** {conexiones}\n"
                            f"🔑 **SSH Creado:** `{ssh_usr}`"
                        )

                        # Envío asíncrono con `python-telegram-bot`
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        bot_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
                        loop.run_until_complete(bot_app.bot.send_message(chat_id=user_id, text=msg_cliente, parse_mode="Markdown"))
                        loop.run_until_complete(bot_app.bot.send_message(chat_id=ADMIN_ID, text=msg_admin, parse_mode="Markdown"))

    return jsonify({"status": "ok"}), 200

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# ==========================================
# INICIALIZACIÓN DEL BOT
# ==========================================
def main():
    threading.Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("alta", alta_manual))
    application.add_handler(CallbackQueryHandler(callback_handler))

    logger.info("Bot en marcha con éxito...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()