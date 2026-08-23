# main.py
import os
import random
import string
import secrets
import asyncio
import json
import logging
from datetime import datetime, timedelta

import httpx
import asyncssh
import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

# --------------------------------------------------
# 1. CARGA DE VARIABLES DE ENTORNO
# --------------------------------------------------
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
MERCADO_PAGO_TOKEN = os.getenv("MERCADO_PAGO_TOKEN")
DOMAIN_OR_IP = os.getenv("DOMAIN_OR_IP")
APP_DOWNLOAD_URL = os.getenv("APP_DOWNLOAD_URL")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME")
BINANCE_ID = os.getenv("BINANCE_ID")
PAYPAL_URL = os.getenv("PAYPAL_URL")

# --------------------------------------------------
# 2. CONFIGURACIÓN DE LOGGING
# --------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# --------------------------------------------------
# 3. MODELOS Y DATOS ESTÁTICOS
# --------------------------------------------------
class Region(BaseModel):
    nombre: str
    ip: str
    port: int
    user: str
    password: str

SERVIDORES_REGION = {
    "us": Region(
        nombre="🇺🇸 Estados Unidos",
        ip="78.13.49.7",
        port=22,
        user="root",
        password="master99@@",
    ),
    "br": Region(
        nombre="🇧🇷 Brasil",
        ip="18.228.59.234",
        port=22,
        user="root",
        password="master9900@@",
    ),
    "ar": Region(
        nombre="🇦🇷 Argentina",
        ip="147.78.123.152",
        port=22,
        user="root",
        password="lQw3LqCAEaJWVyMlbOWx",
    ),
}

PLANES_BASE = {
    "demo_7h": {"name": "🧪 Demo VPS (7 Horas)", "base_price": 120, "days": 0.29},
    "7dias": {"name": "⚡ Plan 7 Días", "base_price": 1222, "days": 7},
    "14dias": {"name": "🚀 Plan 14 Días", "base_price": 2333, "days": 14},
    "30dias": {"name": "👑 Plan 30 Días", "base_price": 3200, "days": 30},
}

# --------------------------------------------------
# 4. CLIENTE ASINCRÓNICO DE MERCADOPAGO
# --------------------------------------------------
http_client = httpx.AsyncClient(base_url="https://api.mercadopago.com")

async def crear_preference_mp(plan_key: str, conexiones: int, region_code: str, user_id: int) -> str | None:
    plan = PLANES_BASE.get(plan_key)
    if not plan:
        return None

    price = plan["base_price"] * conexiones
    region = SERVIDORES_REGION[region_code]
    payload = {
        "items": [
            {
                "title": f"{plan['name']} - {region.nombre} ({conexiones} Conexión/es)",
                "quantity": 1,
                "unit_price": price,
                "currency_id": "ARS",
            }
        ],
        "external_reference": f"{user_id}:{plan_key}:{conexiones}:{region_code}",
        "notification_url": f"{DOMAIN_OR_IP}/mercado_pago",
    }

    headers = {"Authorization": f"Bearer {MERCADO_PAGO_TOKEN}"}
    r = await http_client.post("/checkout/preferences", headers=headers, json=payload)
    if r.status_code != 201:
        logger.error(f"MP preference failed: {r.text}")
        return None

    return r.json()["init_point"]  # url de pago

# --------------------------------------------------
# 5. CREACIÓN DE USUARIO SSH ASÍNCONO
# --------------------------------------------------
async def crear_usuario_ssh_remoto(region_code: str, user_id: int, conexiones: int) -> tuple[str, str, str]:
    """Crea un usuario sin shell en el VPS y devuelve usuario, password y nombre de región."""
    region: Region = SERVIDORES_REGION[region_code]
    username = f"usr_{user_id}_{secrets.randbelow(900)+100}"
    password = secrets.token_urlsafe(8)

    # Usamos asyncssh para no bloquear el event‑loop
    try:
        async with asyncssh.connect(
            host=region.ip,
            port=region.port,
            username=region.user,
            password=region.password,
            known_hosts=None,
        ) as conn:
            await conn.run(f"sudo useradd -M -s /bin/false {username}")
            await conn.run(f"echo '{username}:{password}' | sudo chpasswd")
        logger.info(f"Usuario {username} creado en {region.nombre}")
    except Exception as e:
        logger.exception(f"Error al crear usuario remoto: {e}")
        # fallback a subprocess en caso de fallo
        import subprocess
        subprocess.run(
            ["sudo", "useradd", "-M", "-s", "/bin/false", username],
            check=True,
        )
        subprocess.run(
            ["sudo", "chpasswd"],
            input=f"{username}:{password}".encode(),
            check=True,
        )

    return username, password, region.nombre

# --------------------------------------------------
# 6. BOT DE TELEGRAM (python‑telegram‑bot v20)
# --------------------------------------------------
def get_main_menu(user_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🛒 Comprar VPS / Solicitar Demo", callback_data="buy_vps")],
        [InlineKeyboardButton("📲 Descargar Aplicación VPN", url=APP_DOWNLOAD_URL)],
        [InlineKeyboardButton("❓ Soporte Técnico Directo", url=f"https://t.me/{SUPPORT_USERNAME}")],
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("👑 Panel de Administración", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

# (Las demás funciones de menú se mantienen igual, solo cambia el retorno de la marca)

# --------------------------------------------------
# 7. HANDLERS ASÍNCONOS
# --------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    welcome_text = (
        "👋 **Bienvenido a Servidores VPS High Speed**\n\n"
        "Conexiones SSH de alto rendimiento y baja latencia.\n"
        "📲 Descarga nuestra App oficial para conectarte.\n"
        "📩 Atención & Soporte Oficial: @{SUPPORT_USERNAME}\n\n"
        "Selecciona una opción del menú:"
    )
    await update.message.reply_text(
        welcome_text, reply_markup=get_main_menu(user_id), parse_mode="Markdown"
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # … (el resto del switch‑case permanece igual, con la única diferencia de usar
    # `await query.edit_message_text(...)` y no hacer `asyncio.run_coroutine_threadsafe`)

    if data.startswith("pay_mp_"):
        _, _, plan_key, conns, region_code = data.split("_")
        conns = int(conns)
        init_point = await crear_preference_mp(plan_key, conns, region_code, user_id)

        if init_point:
            buttons = [
                [InlineKeyboardButton("👉 Pagar con Mercado Pago", url=init_point)],
                [InlineKeyboardButton("⬅️ Volver", callback_data=f"checkout_{plan_key}_{conns}_{region_code}")],
            ]
            text = (
                "⚡ **Pago Automático vía Mercado Pago**\n\n"
                "1. Presiona el botón de abajo para abonar.\n"
                "2. Tras acreditarse, el bot te entregará tus credenciales SSH de forma automática aquí en segundos."
            )
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        else:
            await query.edit_message_text(
                "❌ Error al conectar con Mercado Pago. Intenta nuevamente.", reply_markup=get_main_menu(user_id)
            )

    # … (los demás casos se dejan igual)

async def alta_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    try:
        target_id = int(context.args[0])
        dias = int(context.args[1])
        conexiones = int(context.args[2])
        region_code = context.args[3].lower() if len(context.args) > 3 else "us"

        ssh_user, ssh_pass, region_name = await crear_usuario_ssh_remoto(region_code, target_id, conexiones)

        msg_cliente = (
            f"✅ **¡Tu servicio VPS ha sido activado!**\n\n"
            f"🌐 **Ubicación:** {region_name}\n"
            f"👤 **Usuario SSH:** `{ssh_user}`\n"
            f"🔑 **Contraseña:** `{ssh_pass}`\n"
            f"⌛ **Duración:** {dias} días\n"
            f"📱 **Conexiones Permitidas:** {conexiones}\n\n"
            f"📲 **Descarga la app para conectarte:** {APP_DOWNLOAD_URL}\n"
            f"💬 Soporte Oficial: @{SUPPORT_USERNAME}"
        )

        await context.bot.send_message(chat_id=target_id, text=msg_cliente, parse_mode="Markdown")
        await update.message.reply_text(
            f"✅ Usuario {target_id} activado en {region_name}.\nSSH: `{ssh_user}`", parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception(e)
        await update.message.reply_text(
            "❌ **Sintaxis incorrecta.** Uso: `/alta <id_telegram> <dias> <conexiones> <region_code>` (ej: `/alta 123456789 30 2 us`)",
            parse_mode="Markdown",
        )

# --------------------------------------------------
# 8. WEBHOOK ASÍNCONO CON FASTAPI
# --------------------------------------------------
app_fastapi = FastAPI()

class MercadoPagoWebhook(BaseModel):
    type: str
    data: dict

@app_fastapi.post("/mercado_pago")
async def mercado_pago_webhook(payload: MercadoPagoWebhook, background_tasks: BackgroundTasks):
    if payload.type != "payment":
        return JSONResponse(content={"status": "ignored"}, status_code=200)

    payment_info = payload.data
    if payment_info.get("status") != "approved":
        return JSONResponse(content={"status": "not approved"}, status_code=200)

    ext_ref = payment_info.get("external_reference", "")
    if not ext_ref:
        return JSONResponse(content={"status": "no ext_ref"}, status_code=200)

    try:
        user_id, plan_key, conexiones, region_code = ext_ref.split(":")
        user_id = int(user_id)
        conexiones = int(conexiones)
        region_code = region_code or "us"
    except ValueError:
        return JSONResponse(content={"status": "bad ref"}, status_code=200)

    plan = PLANES_BASE.get(plan_key)
    if not plan:
        return JSONResponse(content={"status": "bad plan"}, status_code=200)

    # Se crea el usuario en background (no bloquea la respuesta)
    background_tasks.add_task(
        send_user_and_admin_messages,
        user_id=user_id,
        plan=plan,
        conexiones=conexiones,
        region_code=region_code,
    )
    return JSONResponse(content={"status": "ok"}, status_code=200)

async def send_user_and_admin_messages(user_id: int, plan: dict, conexiones: int, region_code: str):
    ssh_user, ssh_pass, region_name = await crear_usuario_ssh_remoto(region_code, user_id, conexiones)

    msg_cliente = (
        f"✅ **¡Pago Confirmado Automáticamente!**\n\n"
        f"📦 **Servicio:** {plan['name']}\n"
        f"🌐 **Ubicación:** {region_name}\n"
        f"👤 **Usuario SSH:** `{ssh_user}`\n"
        f"🔑 **Contraseña:** `{ssh_pass}`\n"
        f"📱 **Conexiones:** {conexiones}\n\n"
        f"📲 **Descarga la app:** {APP_DOWNLOAD_URL}\n"
        f"💬 Soporte: @{SUPPORT_USERNAME}"
    )

    msg_admin = (
        f"💰 **Nueva venta confirmada**\n\n"
        f"👤 **Cliente ID:** `{user_id}`\n"
        f"📦 **Plan:** {plan['name']}\n"
        f"🌐 **Servidor:** {region_name}\n"
        f"📱 **Conexiones:** {conexiones}\n"
        f"🔑 **SSH Creado:** `{ssh_user}`"
    )

    # Enviamos los mensajes con el bot ya creado
    await telegram_app.bot.send_message(chat_id=user_id, text=msg_cliente, parse_mode="Markdown")
    await telegram_app.bot.send_message(chat_id=ADMIN_ID, text=msg_admin, parse_mode="Markdown")

# --------------------------------------------------
# 9. INICIALIZACIÓN
# --------------------------------------------------
async def start_bot_and_server():
    # 1️⃣ Crea la aplicación de telegram
    global telegram_app
    telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CommandHandler("alta", alta_manual))
    telegram_app.add_handler(CallbackQueryHandler(callback_handler))

    # 2️⃣ Inicia el bot en un thread separado (evita que el servidor FastAPI se bloquee)
    bot_task = asyncio.create_task(telegram_app.run_polling(drop_pending_updates=True))

    # 3️⃣ Inicia el servidor FastAPI
    uvicorn_config = uvicorn.Config(app_fastapi, host="0.0.0.0", port=5000, log_level="info")
    server = uvicorn.Server(uvicorn_config)
    server_task = asyncio.create_task(server.serve())

    await asyncio.gather(bot_task, server_task)

if __name__ == "__main__":
    asyncio.run(start_bot_and_server())
