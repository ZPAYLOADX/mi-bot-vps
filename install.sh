#!/bin/bash

# ==========================================
# VERIFICACIÓN DE PERMISOS ROOT
# ==========================================
if [ "$EUID" -ne 0 ]; then
    echo -e "\033[1;31m[!] Este script debe ejecutarse como root o con sudo.\033[0m"
    exit 1
fi

# ==========================================
# DEFINICIÓN DE COLORES Y ESTILOS (NEON)
# ==========================================
CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
MAGENTA='\033[1;35m'
RED='\033[1;31m'
WHITE='\033[1;37m'
NC='\033[0m'

# ==========================================
# FUNCIONES DE ANIMACIÓN Y PROGRESO
# ==========================================
banner() {
    clear
    echo -e "${CYAN}"
    echo "  ██╗   ██╗██████╗ ███████╗    ██████╗ ██████╗ ████████╗"
    echo "  ██║   ██║██╔══██╗██╔════╝    ██╔══██╗██╔══██╗╚══██╔══╝"
    echo "  ██║   ██║██████╔╝███████╗    ██████╔╝██║  ██║   ██║   "
    echo "  ╚██╗ ██╔╝██╔═══╝ ╚════██║    ██╔══██╗██║  ██║   ██║   "
    echo "   ╚████╔╝ ██║     ███████║    ██████╔╝██████╔╝   ██║   "
    echo "    ╚═══╝  ╚═╝     ╚══════╝    ╚═════╝ ╚═════╝    ╚═╝   "
    echo -e "${MAGENTA}   [ SYSTEM AUTO-INSTALLER & SSH MANAGER V2.5 ]${NC}"
    echo -e "${CYAN}--------------------------------------------------${NC}"
    echo ""
}

loading_bar() {
    local duration=$1
    local steps=20
    local delay=$(python3 -c "print($duration / $steps)" 2>/dev/null || echo "0.1")
    
    echo -ne "  ${YELLOW}[${NC}"
    for ((i=0; i<steps; i++)); do
        echo -ne "${GREEN}█${NC}"
        sleep $delay
    done
    echo -e "${YELLOW}]${NC} ${GREEN}100% - OK${NC}"
}

print_step() {
    echo -e "\n${MAGENTA}▶ [SYSTEM CORE]${NC} ${WHITE}${1}${NC}"
}

# ==========================================
# INICIO DE INSTALACIÓN
# ==========================================
banner

# 1. Captura de Datos Interactiva
echo -e "${CYAN}┌──(${WHITE}root🌐vps-server${CYAN})-[${WHITE}CONFIGURACIÓN DE RED Y TOKENS${CYAN}]${NC}"
read -p "├─$ IP o DOMINIO de la VPS: " DOMINIO_IP
read -p "├─$ TELEGRAM BOT TOKEN: " TELEGRAM_BOT_TOKEN
read -p "├─$ TELEGRAM CHAT ID (Admin): " TELEGRAM_CHAT_ID
read -p "├─$ MERCADO PAGO ACCESS TOKEN: " MP_ACCESS_TOKEN
read -p "├─$ BINANCE ID (Opcional - Enter para omitir): " BINANCE_ID
read -p "└─$ PAYPAL LINK (Opcional - Enter para omitir): " PAYPAL_LINK

# Normalización del Dominio/IP (elimina prefijos http:// o https:// si se ingresan)
DOMINIO_IP=$(echo "$DOMINIO_IP" | sed -e 's|^[^/]*//||' -e 's|/.*$||')

if [ -z "$DOMINIO_IP" ] || [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ] || [ -z "$MP_ACCESS_TOKEN" ]; then
    echo -e "\n${RED}[!] Error: IP/Dominio, Bot Token, Chat ID y Mercado Pago Token son obligatorios.${NC}"
    exit 1
fi

echo -e "\n${CYAN}[i] Desplegando servicios para:${NC} ${GREEN}${DOMINIO_IP}${NC}"
sleep 1

# 2. Actualización del sistema y paquetes requeridos
print_step "Actualizando paquetes e instalando dependencias de C, OpenSSL y Python..."
apt update -y > /dev/null 2>&1
apt install -y python3 python3-pip python3-venv build-essential libssl-dev libffi-dev git nano curl > /dev/null 2>&1
loading_bar 2

# 3. Creación e instalación de módulos Python en un entorno virtual (venv)
print_step "Creando entorno virtual e instalando módulos (Paramiko, Flask, MercadoPago, etc.)..."
RUTA_ACTUAL=$(pwd)

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1

if [ -f "requisitos.txt" ]; then
    pip install -r requisitos.txt > /dev/null 2>&1
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt > /dev/null 2>&1
else
    pip install mercadopago flask requests python-dotenv paramiko python-telegram-bot > /dev/null 2>&1
fi
loading_bar 2.5

# 4. Generación del archivo .env
print_step "Generando y protegiendo variables de entorno (.env)..."
cat <<EOF > .env
PORT=5000
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
MP_ACCESS_TOKEN=${MP_ACCESS_TOKEN}
BINANCE_ID=${BINANCE_ID:-"N/A"}
PAYPAL_LINK=${PAYPAL_LINK:-"N/A"}
EOF
chmod 600 .env
loading_bar 1

# 5. Enlace del Webhook con la API de Telegram
print_step "Enlazando Webhook con la API de Telegram..."
RESPONSE=$(curl -s -F "url=https://${DOMINIO_IP}/telegram_webhook" https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook)
loading_bar 1.5

# 6. Verificación de existencia de main.py y creación del servicio Systemd
print_step "Configurando el servicio en segundo plano (systemd)..."

if [ ! -f "main.py" ]; then
    echo -e "${YELLOW}[!] Advertencia: No se encontró 'main.py' en la ruta actual (${RUTA_ACTUAL}). Asegúrate de colocar tu script antes de iniciar el servicio.${NC}"
fi

cat <<EOF > /etc/systemd/system/bot-vps.service
[Unit]
Description=VPS AutoPay Bot & SSH Manager
After=network.target

[Service]
User=root
WorkingDirectory=${RUTA_ACTUAL}
ExecStart=${RUTA_ACTUAL}/venv/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable bot-vps > /dev/null 2>&1
systemctl restart bot-vps
loading_bar 2

# ==========================================
# RESUMEN FINAL
# ==========================================
echo -e "\n${CYAN}--------------------------------------------------${NC}"
echo -e " ${GREEN}✔ SISTEMA DESPLEGADO Y OPERATIVO${NC}"
echo -e "${CYAN}--------------------------------------------------${NC}"
echo -e " ${WHITE}• Servicio:${NC}   ${GREEN}bot-vps.service (ACTIVO)${NC}"
echo -e " ${WHITE}• Entorno:${NC}    ${CYAN}${RUTA_ACTUAL}/venv${NC}"
echo -e " ${WHITE}• Webhook:${NC}    ${CYAN}https://${DOMINIO_IP}/telegram_webhook${NC}"
echo -e " ${WHITE}• Estado:${NC}     ${YELLOW}sudo systemctl status bot-vps${NC}"
echo -e " ${WHITE}• Logs:${NC}       ${YELLOW}sudo journalctl -u bot-vps -f${NC}"
echo -e "${CYAN}--------------------------------------------------${NC}\n"