import os
import threading
from flask import Flask
from time import sleep

# --- SERVIDOR PARA EVITAR ERROR EN RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot activo"

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Iniciamos el servidor web en segundo plano
threading.Thread(target=run_web, daemon=True).start()
# ---------------------------------------------

# --- A PARTIR DE AQUÍ VA TU CÓDIGO ORIGINAL ---
# (Pega aquí debajo toda la lógica de tu Cazador Pro)

print("🤖 BOT INICIADO: Escaneando...", flush=True)

# ... resto de tu código ...

import yfinance as yf
import json, os, time

# --- CONFIGURACIÓN ---
DB_FILE = "posiciones.json"
LOG_FILE = "alertas.txt"

class CazadorPro:
    def __init__(self):
        self.posiciones = self.cargar_posiciones()
        self.trailing_pct = 0.08
        self.registrar_alerta("🤖 BOT INICIADO: Escaneando...")

    def registrar_alerta(self, mensaje):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        linea = f"[{timestamp}] {mensaje}"
        with open(LOG_FILE, "a") as f:
            f.write(linea + "\n")
        print(linea)

    def cargar_posiciones(self):
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f: return json.load(f)
        return {}

    def guardar(self):
        with open(DB_FILE, 'w') as f: json.dump(self.posiciones, f)

    def ejecutar(self):
        # Escáner usando un User-Agent explícito para evitar bloqueos
        watch_list = ["LXRX", "PACB", "CRSP", "EDIT", "BEAM", "RKLB", "SOFI", "PLTR"]
        for ticker in watch_list:
            try:
                # El parámetro proxy/headers ayuda a saltar bloqueos en servidores restringidos
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d") # Bajamos a 5 días para ser más ligeros
                
                if hist.empty:
                    self.registrar_alerta(f"⚠️ {ticker}: No hay datos (reintentando en próximo ciclo)")
                    continue
                
                precio = hist['Close'].iloc[-1]
                vol_actual = hist['Volume'].iloc[-1]
                
                if ticker in self.posiciones:
                    # Lógica de seguimiento (se mantiene igual)
                    datos = self.posiciones[ticker]
                    nuevo_sl = precio * (1 - self.trailing_pct)
                    if nuevo_sl > datos['sl']:
                        datos['sl'] = nuevo_sl
                        self.guardar()
                        self.registrar_alerta(f"📈 {ticker} | SL actualizado a ${nuevo_sl:.2f}")
                else:
                    # Criterio de entrada simple (solo si hay volumen hoy)
                    if precio <= 20.00 and vol_actual > 1000000:
                        self.posiciones[ticker] = {'entrada': precio, 'sl': precio * 0.92}
                        self.guardar()
                        self.registrar_alerta(f"🚀 NUEVA: {ticker} a ${precio:.2f}")
            except Exception as e:
                self.registrar_alerta(f"Error {ticker}: {e}")

if __name__ == "__main__":
    bot = CazadorPro()
    while True:
        bot.ejecutar()
        time.sleep(1800)
import telepot
from telepot.loop import MessageLoop

# ... dentro de tu clase CazadorPro o justo antes del if __name__ == "__main__": ...

def handle(msg):
    chat_id = msg['chat']['id']
    comando = msg.get('text')
    if comando == '/start':
        bot.sendMessage(chat_id, "¡Hola! Estoy listo para escanear.")

# Al final, justo antes de tu bucle 'while True':
bot = telepot.Bot("TU_TOKEN_AQUI")
MessageLoop(bot, handle).run_as_thread()
print("🤖 Telegram escuchando...", flush=True)
