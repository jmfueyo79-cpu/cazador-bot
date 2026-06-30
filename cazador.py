import os
import threading
import time
import json
import yfinance as yf
from flask import Flask
import telepot

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = "8620604654:AAEsvDlxfzCpICHtTyMg0HYApvKXwzJ9Xys"
TELEGRAM_CHAT_ID = "2047038250"
DB_FILE = "posiciones.json"

# --- SERVIDOR WEB (Mantiene el servicio vivo en Render) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot de Trading Activo"

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Iniciamos el servidor web en un hilo separado
threading.Thread(target=run_web, daemon=True).start()

# --- LÓGICA DEL CAZADOR ---
class CazadorPro:
    def __init__(self):
        self.bot = telepot.Bot(TELEGRAM_TOKEN)
        self.posiciones = self.cargar_posiciones()
        self.trailing_pct = 0.08
        self.enviar_telegram("🤖 BOT INICIADO: Escaneando mercado...")

    def enviar_telegram(self, mensaje):
        try:
            print(f"Enviando: {mensaje}")
            self.bot.sendMessage(TELEGRAM_CHAT_ID, mensaje)
        except Exception as e:
            print(f"Error enviando a Telegram: {e}")

    def cargar_posiciones(self):
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f: return json.load(f)
        return {}

    def guardar(self):
        with open(DB_FILE, 'w') as f: json.dump(self.posiciones, f)

    def ejecutar(self):
        # 1. SEGUIMIENTO
        for ticker, datos in list(self.posiciones.items()):
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                if hist.empty: continue
                precio = hist['Close'].iloc[-1]
                profit_pct = ((precio - datos['entrada']) / datos['entrada']) * 100
                nuevo_sl = precio * (1 - self.trailing_pct)
                
                if precio <= datos['sl']:
                    self.enviar_telegram(f"🛑 STOP OUT: {ticker} a ${precio:.2f}. Profit: {profit_pct:.2f}%")
                    del self.posiciones[ticker]
                    self.guardar()
                elif nuevo_sl > datos['sl']:
                    datos['sl'] = nuevo_sl
                    self.guardar()
                    self.enviar_telegram(f"📈 SEGUIMIENTO: {ticker} | Profit: {profit_pct:.2f}% | SL: ${nuevo_sl:.2f}")
            except Exception as e:
                print(f"Error {ticker}: {e}")

        # 2. ESCÁNER
        watch_list = ["LXRX", "PACB", "CRSP", "EDIT", "BEAM", "RKLB", "SOFI", "PLTR"]
        for ticker in watch_list:
            if ticker in self.posiciones: continue
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="30d")
                if len(hist) < 30: continue
                precio = hist['Close'].iloc[-1]
                vol_actual = hist['Volume'].iloc[-1]
                vol_promedio = hist['Volume'].iloc[:-1].mean()
                if precio <= 20.00 and (vol_actual / vol_promedio) > 2.0:
                    self.posiciones[ticker] = {'entrada': precio, 'sl': precio * 0.92}
                    self.guardar()
                    self.enviar_telegram(f"🚀 NUEVA: {ticker} detectada a ${precio:.2f}")
            except Exception as e:
                print(f"Error escaneando {ticker}: {e}")

if __name__ == "__main__":
    cazador = CazadorPro()
    while True:
        cazador.ejecutar()
        time.sleep(1800) # Espera 30 minutos

