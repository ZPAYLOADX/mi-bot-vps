import os
import secrets
import string
import datetime
import subprocess
import requests
import mercadopago
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINANCE_ID = os.getenv("BINANCE_ID")
PAYPAL_LINK = os.getenv("PAYPAL_LINK")
PORT = int(os.getenv("PORT", 5000))

app = Flask(__name__)
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

# Precios base (Días -> Precio ARS)
PRECIOS_BASE = {
    7: 1222.0,
    14: 2333.0,
    30: 3200.0
}

def generar_password(longitud=8):
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

def crear_usuario_vps(usuario, password, dias, conexiones):
    try:
        fecha_exp = (datetime.date.today() + datetime.timedelta(days=dias)).strftime('%Y-%m-%d')
        
        # Crear usuario sin shell de acceso
        cmd_user = f"useradd -M -s /bin/false -e {fecha_exp} {usuario}"
        subprocess.run(cmd_user, shell=True, check=True)

        # Asignar contraseña
        cmd_pass = f"echo '{usuario}:{password}' | chpasswd"
        subprocess.run(cmd_pass, shell=True, check=True)

        # Asignar límite de conexiones simultáneas
        regla_limite = f"\n{usuario} hard maxlogins {conexiones}\n"
        with open("/etc/security/limits.conf", "a") as f:
            f.write(regla_limite)

        return True
    except Exception as e:
        print(f"Error al crear usuario en VPS: {e}")
        return False

def enviar_mensaje_telegram(chat_id, texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error enviando mensaje a Telegram: {e}")

@app.route("/generar_pago", methods=["POST"])
def generar_pago():
    datos = request.json
    chat_id = datos.get("chat_id")
    dias = int(datos.get("dias"))
    conexiones = int(datos.get("conexiones", 1))

    precio_unidad = PRECIOS_BASE.get(dias, 1222.0)
    precio_total = precio_unidad * conexiones
    ref_datos = f"{chat_id}|{dias}|{conexiones}"

    preference_data = {
        "items": [
            {
                "title": f"Cuenta SSH ({dias} Dias / {conexiones} Conexiones)",
                "quantity": 1,
                "unit_price": float(precio_total),
                "currency_id": "ARS"
            }
        ],
        "external_reference": ref_datos,
        "auto_return": "approved"
    }

    resultado = sdk.preference().create(preference_data)
    url_pago = resultado["response"]["init_point"]

    return jsonify({"url": url_pago, "total": precio_total}), 200

# Webhook Mercado Pago (Automático)
@app.route("/webhook", methods=["POST"])
def recibir_webhook():
    datos = request.args
    topic = datos.get("topic") or datos.get("type")

    if topic == "payment":
        payment_id = datos.get("id") or request.json.get("data", {}).get("id")

        if payment_id:
            payment_info = sdk.payment().get(payment_id)
            if payment_info["response"]["status"] == "approved":
                
                ref = payment_info["response"]["external_reference"]
                chat_id, dias_str, conexiones_str = ref.split("|")
                dias = int(dias_str)
                conexiones = int(conexiones_str)

                usuario_ssh = f"usr{secrets.randbelow(8999) + 1000}"
                password_ssh = generar_password()

                creado = crear_usuario_vps(usuario_ssh, password_ssh, dias, conexiones)

                if creado:
                    mensaje = (
                        f"✅ *¡PAGO CONFIRMADO CON ÉXITO!*\n\n"
                        f"💻 *Tus Credenciales SSH:*\n"
                        f"• *Usuario:* `{usuario_ssh}`\n"
                        f"• *Contraseña:* `{password_ssh}`\n"
                        f"• *Duración:* `{dias} días`\n"
                        f"• *Límite de Conexiones:* `{conexiones}`\n\n"
                        f"⚠️ _Guarda tus datos en un lugar seguro._"
                    )
                    enviar_mensaje_telegram(chat_id, mensaje)

    return jsonify({"status": "ok"}), 200

# Webhook Telegram (Manual con /crear)
@app.route("/telegram_webhook", methods=["POST"])
def recibir_telegram():
    update = request.json
    if "message" in update and "text" in update["message"]:
        msg = update["message"]
        sender_id = str(msg["from"]["id"])
        texto = msg["text"].strip()

        if texto.startswith("/crear"):
            if sender_id != str(TELEGRAM_CHAT_ID):
                enviar_mensaje_telegram(sender_id, "❌ *Acceso denegado.* No tienes permisos de administrador.")
                return jsonify({"status": "forbidden"}), 403

            partes = texto.split()
            if len(partes) != 4:
                enviar_mensaje_telegram(
                    sender_id,
                    "⚠️ *Uso del comando:*\n`/crear <chat_id> <dias> <conexiones>`"
                )
                return jsonify({"status": "bad_request"}), 400

            try:
                cliente_chat_id = partes[1]
                dias = int(partes[2])
                conexiones = int(partes[3])

                usuario_ssh = f"usr{secrets.randbelow(8999) + 1000}"
                password_ssh = generar_password()

                creado = crear_usuario_vps(usuario_ssh, password_ssh, dias, conexiones)

                if creado:
                    enviar_mensaje_telegram(
                        sender_id,
                        f"✅ *Cuenta Creada*\n\n"
                        f"• *Cliente:* `{cliente_chat_id}`\n"
                        f"• *Usuario:* `{usuario_ssh}`\n"
                        f"• *Contraseña:* `{password_ssh}`\n"
                        f"• *Días:* `{dias}`\n"
                        f"• *Conexiones:* `{conexiones}`"
                    )

                    mensaje_cliente = (
                        f"✅ *¡PAGO VERIFICADO Y CONFIRMADO!*\n\n"
                        f"💻 *Tus Credenciales SSH:*\n"
                        f"• *Usuario:* `{usuario_ssh}`\n"
                        f"• *Contraseña:* `{password_ssh}`\n"
                        f"• *Duración:* `{dias} días`\n"
                        f"• *Límite de Conexiones:* `{conexiones}`\n\n"
                        f"⚠️ _Guarda tus datos en un lugar seguro._"
                    )
                    enviar_mensaje_telegram(cliente_chat_id, mensaje_cliente)
                else:
                    enviar_mensaje_telegram(sender_id, "❌ *Error al crear el usuario en Linux.*")

            except ValueError:
                enviar_mensaje_telegram(sender_id, "❌ *Error:* Formato de números inválido.")

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
