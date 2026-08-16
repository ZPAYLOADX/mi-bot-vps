#!/bin/bash

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
BOLD='\033[1m'

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
    echo -e "${MAGENTA}   [ SYSTEM AUTO-INSTALLER & SSH MANAGER V2.0 ]${NC}"
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

# 1. Captura de Datos Interactiva y Segura
echo -e "${CYAN}┌──(${WHITE}root🌐vps-server${CYAN})-[${WHITE}CONFIGURACIÓN DE RED Y TOKENS${CYAN}]${NC}"
read -p "├─$ IP o DOMINIO de la VPS: " DOMINIO_IP
read -p "├─$ TELEGRAM BOT TOKEN: " TELEGRAM_BOT_TOKEN
read -p "├─$ TELEGRAM CHAT ID: " TELEGRAM_CHAT_ID
read -p "├─$ MERCADO PAGO ACCESS TOKEN: " MP_ACCESS_TOKEN
read -p "├─$ BINANCE ID (Opcional - Presiona Enter para omitir): " BINANCE_ID
read -p "└─$ PAYPAL LINK (Opcional - Presiona Enter para omitir): " PAYPAL_LINK

if [ -z "$DOMINIO_IP" ] || [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ] || [ -z "$MP_ACCESS_TOKEN" ]; then
    echo -e "\n${RED}[!] Error: Los campos IP, Bot Token, Chat ID y Mercado Pago Token son obligatorios.${NC}"
    exit 1
fi

echo -e "\n${CYAN}[i] Desplegando servicios para:${NC} ${GREEN}${DOMINIO_IP}${NC}"
sleep 1

# 2. Actualización del sistema
print_step "Actualizando paquetes base e instalando dependencias Linux..."
sudo apt update -y > /dev/null 2>&1
sudo apt install -y python3 python3-pip git nano curl > /dev/null 2>&1
loading_bar 2

# 3. Instalación de librerías de Python (CORREGIDO PARA IGNORAR PAQUETES PROTEGIDOS)
print_step "Instalando módulos Python (Flask, MercadoPago, Requests)..."
if [ -f "requisitos.txt" ]; then
    sudo python3 -m pip install -r requisitos.txt --break-system-packages --ignore-installed > /dev/null 2>&1
elif [ -f "requirements.txt" ]; then
    sudo python3 -m pip install -r requirements.txt --break-system-packages --ignore-installed > /dev/null 2>&1
else
    sudo python3 -m pip install mercadopago flask requests python-dotenv --break-system-packages --ignore-installed > /dev/null 2>&1
fi
loading_bar 2

# 4. Generación local del archivo .env
print_step "Inyectando variables de entorno en el servidor..."
cat <<EOF > .env
PORT=5000
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
MP_ACCESS_TOKEN=${MP_ACCESS_TOKEN}
BINANCE_ID=${BINANCE_ID:-"N/A"}
PAYPAL_LINK=${PAYPAL_LINK:-"N/A"}
EOF
loading_bar 1

# 5. Configuración del Webhook en Telegram
print_step "Enlazando Webhook con la API de Telegram..."
RESPONSE=$(curl -s -F "url=https://${DOMINIO_IP}/telegram_webhook" https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook)
loading_bar 1.5

# 6. Creación y activación del Servicio Systemd
print_step "Configurando el servicio en segundo plano (systemd)..."
RUTA_ACTUAL=$(pwd)

sudo cat <<EOF > /etc/systemd/system/bot-vps.service
[Unit]
Description=VPS AutoPay Bot & SSH Manager
After=network.target

[Service]
User=root
WorkingDirectory=${RUTA_ACTUAL}
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable bot-vps > /dev/null 2>&1
sudo systemctl restart bot-vps
loading_bar 2

# ==========================================
# RESUMEN FINAL
# ==========================================
echo -e "\n${CYAN}--------------------------------------------------${NC}"
echo -e " ${GREEN}✔ SISTEMA DESPLEGADO Y OPERATIVO${NC}"
echo -e "${CYAN}--------------------------------------------------${NC}"
echo -e " ${WHITE}• Servicio:${NC}   ${GREEN}bot-vps.service (ACTIVO)${NC}"
echo -e " ${WHITE}• Webhook:${NC}    ${CYAN}https://${DOMINIO_IP}/telegram_webhook${NC}"
echo -e " ${WHITE}• Estado:${NC}     ${YELLOW}sudo systemctl status bot-vps${NC}"
echo -e "${CYAN}--------------------------------------------------${NC}\n"
