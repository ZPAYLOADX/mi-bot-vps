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
NC='\033[0m' # No Color
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

# 1. Entrada Interactiva
echo -e "${CYAN}┌──(${WHITE}root🌐vps-server${CYAN})-[${WHITE}~${CYAN}]${NC}"
read -p "└─$ Ingresa tu IP o DOMINIO de la VPS: " DOMINIO_IP

if [ -z "$DOMINIO_IP" ]; then
    echo -e "${RED}[!] Error: No ingresaste una IP o Dominio válido.${NC}"
    exit 1
fi

echo -e "\n${CYAN}[i] Iniciando la secuencia de despliegue en:${NC} ${GREEN}${DOMINIO_IP}${NC}"
sleep 1

# 2. Actualización de paquetes
print_step "Actualizando el sistema e instalando dependencias base..."
sudo apt update -y > /dev/null 2>&1
sudo apt install -y python3 python3-pip git nano curl > /dev/null 2>&1
loading_bar 2

# 3. Instalación de librerías Python
print_step "Instalando módulos de Python (Flask, MercadoPago, Requests)..."
pip install -r requirements.txt > /dev/null 2>&1
loading_bar 2

# 4. Configuración de Entorno (.env)
print_step "Inyectando variables de entorno cifradas (.env)..."
cat <<EOF > .env
PORT=5000
TELEGRAM_BOT_TOKEN=8385538827:AAHuS3-mcHEKuDJbqDqc0hPKhsu_OjHBuHw
TELEGRAM_CHAT_ID=8096590049
MP_ACCESS_TOKEN=APP_USR-7873838b-66bc-44da-9818-fc975319280c
BINANCE_ID=108562138
PAYPAL_LINK=https://www.paypal.me/Graciasxtudonacio
EOF
loading_bar 1

# 5. Registro Webhook Telegram
print_step "Enlazando Webhook con Servidores de Telegram..."
RESPONSE=$(curl -s -F "url=https://${DOMINIO_IP}/telegram_webhook" https://api.telegram.org/bot8385538827:AAHuS3-mcHEKuDJbqDqc0hPKhsu_OjHBuHw/setWebhook)
loading_bar 1.5

# 6. Servicio Systemd
print_step "Compilando servicio en segundo plano (systemd)..."
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
echo -e " ${GREEN}✔ SISTEMA INSTALADO Y OPERATIVO CON ÉXITO${NC}"
echo -e "${CYAN}--------------------------------------------------${NC}"
echo -e " ${WHITE}• Servicio:${NC}   ${GREEN}bot-vps.service (RUNNING)${NC}"
echo -e " ${WHITE}• Webhook:${NC}    ${CYAN}https://${DOMINIO_IP}/telegram_webhook${NC}"
echo -e " ${WHITE}• Monitoreo:${NC}  ${YELLOW}sudo systemctl status bot-vps${NC}"
echo -e "${CYAN}--------------------------------------------------${NC}\n"
