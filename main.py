import threading
from flask import Flask, request, jsonify

# ... (Todo tu código de comandos del bot y funciones de Mercado Pago se mantiene arriba) ...

# ==========================================
# EJECUCIÓN PARALELA (FLASK + POLLING)
# ==========================================
def run_flask():
    # Ejecuta Flask en segundo plano para escuchar los Webhooks de Mercado Pago
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    print("[+] Iniciando servidor Flask para pagos en segundo plano...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("[+] Iniciando Bot de Telegram en modo Polling directo...")
    # Elimina cualquier webhook viejo antes de arrancar para evitar conflictos
    bot.remove_webhook()
    
    # Inicia la escucha continua de mensajes en Telegram
    bot.infinity_polling(skip_pending=True)
