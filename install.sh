#!/usr/bin/env bash
# ==============================================================
#  VPS AutoPay Bot Installer  –  Versión 2.6 (2024‑06)
#  • Automatiza la instalación de dependencias
#  • Crea un entorno virtual
#  • Configura el webhook de MercadoPago
#  • Instala y habilita un servicio systemd
# ==============================================================
set -euo pipefail
IFS=$'\n\t'

# ---------- 1.1  Colores  ----------
CYAN='\033[1;36m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'
MAGENTA='\033[1;35m'; RED='\033[1;31m'; WHITE='\033[1;37m'; NC='\033[0m'

log()  { echo -e "${CYAN}➜ $1${NC}"; }
err()  { echo -e "${RED}[!] $1${NC}"; }
info() { echo -e "${WHITE}$1${NC}"; }

# ---------- 1.2  Validar root ----------
if [[ $EUID -ne 0 ]]; then
    err "Este script debe ejecutarse como root o con sudo."
    exit 1
fi

# ---------- 1.3  Banner ----------
banner() {
    clear
    echo -e "${CYAN}"
    echo "  ██╗   ██╗██████╗ ███████╗    ██████╗ ██████╗ ████████╗"
    echo "  ██║   ██║██╔══██╗██╔════╝    ██╔══██╗██╔══██╗╚══██╔══╝"
    echo "  ██║   ██║██████╔╝███████╗    ██████╔╝██║  ██║   ██║   "
    echo "  ╚██╗ ██╔╝██╔═══╝ ╚════██║    ██╔══██╗██║  ██║   ██║   "
    echo "   ╚████╔╝ ██║     ███████║    ██████╔╝██████╔╝   ██║   "
    echo "    ╚═══╝  ╚═╝     ╚══════╝    ╚═════╝ ╚═════╝    ╚═╝   "
    echo -e "${MAGENTA}   [ SYSTEM AUTO-INSTALLER & SSH MANAGER V2.6 ]${NC}"
    echo -e "${CYAN}--------------------------------------------------${NC}"
}

banner
echo -e "${WHITE}🛠️  Iniciando instalación...${NC}\n"

# ---------- 1.4  Entrada interactiva ----------
read -rp "${CYAN}┌──(${WHITE}root🌐vps-server${CYAN})-[${WHITE}CONFIGURACIÓN DE RED Y TOKENS${CYAN}]${NC} " DOMAIN_OR_IP
read -rp "${CYAN}├─${WHITE} TELEGRAM BOT TOKEN: " TELEGRAM_BOT_TOKEN
read -rp "${CYAN}├─${WHITE} TELEGRAM CHAT ID (Admin): " TELEGRAM_CHAT_ID
read -rp "${CYAN}├─${WHITE} MERCADO PAGO ACCESS TOKEN: " MP_ACCESS_TOKEN
read -rp "${CYAN}├─${WHITE} BINANCE ID (Opcional – Enter para omitir): " BINANCE_ID
read -rp "${CYAN}└─${WHITE} PAYPAL LINK (Opcional – Enter para omitir): " PAYPAL_LINK

# Normalizar dominio/IP (quitar http:// / https:// y path)
DOMAIN_OR_IP=$(echo "$DOMAIN_OR_IP" | sed -e 's|^[^/]*//||' -e 's|/.*$||')

# Validar campos obligatorios
if [[ -z $DOMAIN_OR_IP || -z $TELEGRAM_BOT_TOKEN || -z $TELEGRAM_CHAT_ID || -z $MP_ACCESS_TOKEN ]]; then
    err "Error: IP/Dominio, Bot Token, Chat ID y Mercado Pago Token son obligatorios."
    exit 1
fi

# ---------- 1.5  Actualizar y instalar paquetes base ----------
log "Actualizando repositorios y instalando dependencias básicas..."
apt-get update -y > /dev/null 2>&1
apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv git curl build-essential libssl-dev libffi-dev > /dev/null 2>&1

# ---------- 1.6  Crear entorno virtual ----------
VENV_DIR="/opt/vpsbot/venv"
if [[ ! -d $VENV_DIR ]]; then
    log "Creando entorno virtual en $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi
# Activar (solo para este script)
source "$VENV_DIR/bin/activate"

# ---------- 1.7  Instalar dependencias Python ----------
log "Instalando dependencias Python (paramiko, telegram, mercadopago, flask, python-dotenv)..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r <(cat <<EOF
paramiko
python-telegram-bot==20.7
mercadopago
flask
python-dotenv
EOF
) > /dev/null 2>&1

# ---------- 1.8  Crear archivo .env ----------
log "Generando archivo de variables de entorno (/etc/bot-vps/.env)..."
mkdir -p /etc/bot-vps
cat > /etc/bot-vps/.env <<EOF
PORT=5000
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
MP_ACCESS_TOKEN=${MP_ACCESS_TOKEN}
BINANCE_ID=${BINANCE_ID:-"N/A"}
PAYPAL_LINK=${PAYPAL_LINK:-"N/A"}
EOF
chmod 600 /etc/bot-vps/.env

# ---------- 1.9  Configurar webhook (MercadoPago endpoint) ----------
log "Enlazando webhook con la API de Telegram…"
WEBHOOK_URL="https://${DOMAIN_OR_IP}/mercado_pago"
TOKEN="$TELEGRAM_BOT_TOKEN"
curl -s -F "url=$WEBHOOK_URL" "https://api.telegram.org/bot$TOKEN/setWebhook" > /dev/null

# ---------- 1.10  Crear servicio systemd ----------
log "Creando servicio systemd (bot-vps.service)..."
cat > /etc/systemd/system/bot-vps.service <<EOF
[Unit]
Description=VPS AutoPay Bot & SSH Manager
After=network.target

[Service]
User=root
WorkingDirectory=${PWD}
EnvironmentFile=/etc/bot-vps/.env
ExecStart=${VENV_DIR}/bin/python3 main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now bot-vps
log "Servicio habilitado y arrancado."

# ---------- 1.11  Resumen ----------
echo -e "\n${CYAN}--------------------------------------------------${NC}"
echo -e " ${GREEN}✔ SISTEMA DESPLEGADO Y OPERATIVO${NC}"
echo -e " ${CYAN}--------------------------------------------------${NC}"
echo -e " ${WHITE}• Servicio:${NC}   ${GREEN}bot-vps.service${NC}"
echo -e " ${WHITE}• Webhook:${NC}    ${CYAN}https://${DOMAIN_OR_IP}/mercado_pago${NC}"
echo -e " ${WHITE}• Estado:${NC}     ${YELLOW}sudo systemctl status bot-vps${NC}"
echo -e " ${WHITE}• Logs:${NC}       ${YELLOW}sudo journalctl -u bot-vps -f${NC}"
echo -e " ${CYAN}--------------------------------------------------${NC}\n"

# ---------- 1.12  Fin ----------
log "Instalación completa. ¡Listo para usar!"
