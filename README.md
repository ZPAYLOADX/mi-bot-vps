# Auto SSH Manager & Mercado Pago Bot

Sistema automatizado en Python para venta y aprovisionamiento instantáneo de cuentas SSH en Linux mediante pagos recibidos en Mercado Pago.

## Características
- Integración por Webhook con Mercado Pago.
- Creación automática de usuarios Linux con fecha de caducidad.
- Control estricto de límite de sesiones simultáneas mediante PAM (`limits.conf`).
- Entrega directa de credenciales vía Telegram.

## Instalación
1. Clonar repositorio: `git clone https://github.com/tu-usuario/tu-repositorio.git`
2. Instalar dependencias: `pip install -r requirements.txt`
3. Copiar archivo de entorno: `cp .env.example .env` (y completar con tus tokens)
4. Ejecutar: `python3 main.py`
