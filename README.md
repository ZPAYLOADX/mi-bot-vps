# 🚀 VPS AutoPay & SSH Manager Bot

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask_3.0-000000.svg?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot_API-26A5E4.svg?style=flat-square&logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![Mercado Pago] 
(https://img.shields.io/badge/Payments-Mercado_Pago-009EE3.svg?style=flat-square&logo=mercadopago&logoColor=white)](https://www.mercadopago.com.ar/developers)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

Sistema automatizado de gestión, venta y provisión instantánea de cuentas **SSH** con límites de concurrencia en servidores Linux (Ubuntu/Debian). Integrado nativamente con **Mercado Pago (Checkout Pro)**, **Binance Pay** y **PayPal**.
## 📋 Características Principales

- **⚡ Automatización Completa (Mercado Pago):** Aprobado el pago, el sistema crea el usuario en Linux y le entrega las credenciales al cliente por Telegram en segundos via Webhook.
- **🛡️ Verificación Manual Admin (`/crear`):** Permite al administrador verificar pagos de Binance Pay o PayPal y emitir credenciales con un solo comando.
- **🔒 Control de Concurrencia:** Configuración automática de límites de sesiones simultáneas (`maxlogins`) en `/etc/security/limits.conf`.
- **📅 Expiración Automática:** Asignación de fechas límite de uso (`useradd -e YYYY-MM-DD`).
- **🔐 Seguridad Reforzada:** No expone IPs ni puertos del servidor en la interfaz del cliente (ideal para clientes con aplicaciones dedicadas).

---

## ⚙️ Arquitectura de Funcionamiento

```
                 +-----------------------+
                 |    Cliente Telegram   |
                 +-----------+-----------+
                             |
                   Selecciona Plan / Pago
                             |
            +----------------+----------------+
            |                                 |
   [ Mercado Pago ]                  [ Binance / PayPal ]
            |                                 |
    Pago Automático                   Verificación Manual
            |                                 |
     Webhook /webhook                 Admin: /crear ID Días Conex
            |                                 |
            +----------------+----------------+
                             |
                     +-------v-------+
                     | VPS Manager   |
                     |  (Flask App)  |
                     +-------+-------+
                             |
                  useradd + limits.conf
                             |
                     +-------v-------+
                     |  Entrega de   |
                     | Credenciales  |
                     +---------------+
```

---

## 🛠️ Requisitos Previos

- **Servidor Linux** (Ubuntu 20.04/22.04 o Debian 11/12) con acceso Root.
- **Python 3.9+** y `pip`.
- Dominio o Subdominio apuntando a la IP de la VPS con certificado **SSL/HTTPS** (necesario para Webhooks de Telegram y Mercado Pago).

---

## 📦 Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone https://github.com/ZPAYLOADX/mi-bot-vps.git
cd mi-bot-vps
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno (`.env`)

Crea un archivo `.env` en la raíz del proyecto basándote en el ejemplo:

```bash
cp .env.example .env
nano .env
```

Edita los parámetros con tus credenciales reales:

```env
# Servidor
PORT=5000

# Bot de Telegram
TELEGRAM_BOT_TOKEN=PEGA AQUI TI TOKEN 
TELEGRAM_CHAT_ID= PEGA AQUI TU ID DE TELEGRAM

# Credenciales de Pago
MP_ACCESS_TOKEN=APP_USR-XXXXXXXXX REZPLAZA EL CÓDIGO 
BINANCE_ID=108562138
PAYPAL_LINK=https://www.paypal.me/TU ENLACE DE PAYPAL 
```

---

## 🚀 Ejecución y Despliegue

### Modo Desarrollo / Prueba
```bash
python3 main.py
```

### Vinculación del Webhook de Telegram
Para recibir los comandos administrativos (como `/crear`), registra tu URL pública en la API de Telegram:

```bash
curl -F "url=https://TU_DOMINIO.COM/telegram_webhook" https://api.telegram.org/bot<TU_BOT_TOKEN>/setWebhook
```

---

## 🛠️ Comandos Administrativos

| Comando | Formato | Descripción |
| :--- | :--- | :--- |
| `/crear` | `/crear <chat_id> <dias> <conexiones>` | Crea manualmente una cuenta SSH y notifica al cliente. |

**Ejemplo de uso:**
```text
/crear 8096590049 30 2
```

---

## 📩 Formato de Credenciales Entregadas

El cliente recibe una notificación limpia y directa:

```text
✅ ¡PAGO CONFIRMADO CON ÉXITO!

💻 Tus Credenciales SSH:
• Usuario: usr4829
• Contraseña: x8K2pM9v
• Duración: 30 días
• Límite de Conexiones: 1

⚠️ Guarda tus datos en un lugar seguro.
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia **MIT**. Consulta el archivo `LICENSE` para más información.
