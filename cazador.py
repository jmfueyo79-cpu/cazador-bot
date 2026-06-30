import os
import threading
import time
import json
import yfinance as yf
import random
from flask import Flask
import telepot
from yahoo_fin import stock_info as si

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = "8620604654:AAEsvDlxfzCpICHtTyMg0HYApvKXwzJ9Xys"
TELEGRAM_CHAT_ID = "2047038250"
DB_FILE = "posiciones.json"

# --- SERVIDOR WEB (Obligatorio para mantener vivo el bot) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot de Trading Activo"

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# --- LÓGICA DEL CAZADOR ---
class CazadorPro:
    def __init__(self):
        self.bot = telepot.Bot(TELEGRAM_TOKEN)
        self.posiciones = self.cargar_posiciones()
        self.trailing_pct = 0.08
        self.enviar_telegram("🤖 BOT INICIADO: Escaneando NASDAQ...")

    def enviar_telegram(self, mensaje):
        try:
            print(f"Telegram: {mensaje}", flush=True)
            self.bot.sendMessage(TELEGRAM_CHAT_ID, mensaje)
        except Exception as e:
            print(f"Error enviando a Telegram: {e}", flush=True)

    def cargar_posiciones(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r') as f: return json.load(f)
            except: return {}
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
                nuevo_sl = precio * (1 - self.trailing_pct)
                
                if precio <= datos['sl']:
                    self.enviar_telegram(f"🛑 STOP OUT: {ticker} a ${precio:.2f}")
                    del self.posiciones[ticker]
                    self.guardar()
                elif nuevo_sl > datos['sl']:
                    datos['sl'] = nuevo_sl
                    self.guardar()
                    self.enviar_telegram(f"📈 SEGUIMIENTO: {ticker} | SL ajustado: ${nuevo_sl:.2f}")
            except: continue

        # 2. ESCÁNER INTELIGENTE (Muestra aleatoria del NASDAQ)
        try:
            tickers_nasdaq = si.tickers_nasdaq()
            muestra = random.sample(tickers_nasdaq, 50) # Escanea 50 al azar cada vez
            
            for ticker in muestra:
                if ticker in self.posiciones: continue
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="30d")
                    if len(hist) < 30: continue
                    
                    precio = hist['Close'].iloc[-1]
                    vol_actual = hist['Volume'].iloc[-1]
                    vol_promedio = hist['Volume'].iloc[:-1].mean()
                    
                    if vol_promedio > 0 and precio <= 20.00 and (vol_actual / vol_promedio) > 3.0:
                        self.posiciones[ticker] = {'entrada': precio, 'sl': precio * 0.90}
                        self.guardar()
                        self.enviar_telegram(f"🚀 ¡OPORTUNIDAD NASDAQ! {ticker} a ${precio:.2f} (RVOL > 3)")
                except: continue
        except Exception as e:
            print(f"Error en escáner: {e}", flush=True)

if __name__ == "__main__":
    cazador = CazadorPro()
    while True:
        cazador.ejecutar()
        time.sleep(1800)
