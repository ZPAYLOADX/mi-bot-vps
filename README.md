import weasyprint
from weasyprint import HTML

# Direct generation of README.md text content
readme_content = """# 🚀 VPS AutoPay & SSH Manager Bot

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask_3.0-000000.svg?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot_API-26A5E4.svg?style=flat-square&logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![Mercado Pago](https://img.shields.io/badge/Payments-Mercado_Pago-009EE3.svg?style=flat-square&logo=mercadopago&logoColor=white)](https://www.mercadopago.com.ar/developers)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

Sistema automatizado de gestión, venta y provisión instantánea de cuentas **SSH** con límites de concurrencia en servidores Linux (Ubuntu/Debian). Integrado nativamente con **Mercado Pago (Checkout Pro)**, **Binance Pay** y **PayPal**.

---

## 📋 Características Principales

- **⚡ Automatización Completa (Mercado Pago):** Aprobado el pago, el sistema crea el usuario en Linux y le entrega las credenciales al cliente por Telegram en segundos via Webhook.
- **🛡️ Verificación Manual Admin (`/crear`):** Permite al administrador verificar pagos de Binance Pay o PayPal y emitir credenciales con un solo comando.
- **🔒 Control de Concurrencia:** Configuración automática de límites de sesiones simultáneas (`maxlogins`) en `/etc/security/limits.conf`.
- **📅 Expiración Automática:** Asignación de fechas límite de uso (`useradd -e YYYY-MM-DD`).
- **🔐 Seguridad Reforzada:** No expone IPs ni puertos del servidor en la interfaz del cliente (ideal para clientes con aplicaciones dedicadas).

---

## ⚙️ Arquitectura de Funcionamiento
