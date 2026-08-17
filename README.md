# ⚡ Devstudio VPN & AutoPay Bot

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-brightgreen?style=for-the-badge&logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/Telegram_Bot-v20%2B-blue?style=for-the-badge&logo=telegram" alt="Telegram Bot">
  <img src="https://img.shields.io/badge/Mercado_Pago-SDK-yellow?style=for-the-badge&logo=mercadopago" alt="Mercado Pago">
  <img src="https://img.shields.io/badge/Status-Active-neon?style=for-the-badge" alt="Status">
</p>

Sistema automatizado de venta y gestión de usuarios SSH/VPN para Telegram. Integrado con **Mercado Pago (cobros automáticos)**, métodos manuales (**Binance Pay / PayPal**), selección de múltiples regiones (**USA, Brasil, Argentina**) y aprovisionamiento remoto multi-servidor mediante **Paramiko**.

---

## 🛠️ Características Principales

* 🤖 **Pagos Automáticos:** Generación de preferencia e integración Webhook con Mercado Pago para entrega instantánea de credenciales.
* 🌐 **Despliegue Multi-Región:** Creación remota de usuarios SSH via Paramiko en servidores de 🇺🇸 EE.UU., 🇧🇷 Brasil y 🇦🇷 Argentina.
* 📱 **Cotización Flexible:** Configuración dinámica de precios según el número de conexiones simultáneas (1 a 5).
* 💳 **Métodos Internacionales:** Instrucciones integradas para Binance Pay ID y enlaces directos de PayPal.me.
* 👑 **Panel de Administración:** Comando exclusivo `/alta` para activar clientes manualmente por ID de Telegram.
* 📲 **Acceso Directo:** Enlace de descarga integrado para la aplicación oficial del cliente.

---

## 📂 Estructura del Proyecto

```text
├── main.py           # Script principal del Bot de Telegram y Webhook Flask
├── install.sh        # Instalador automatizado con soporte para entorno virtual (venv)
├── .gitignore        # Archivo para excluir credenciales y carpetas del entorno
└── README.md         # Documentación oficial del proyecto