import os
import threading
import time
import json
import yfinance as yf
import random
from flask import Flask
import telepot
from yahoo_fin import stock_info as si

TELEGRAM_TOKEN = "8620604654:AAEsvDlxfzCpICHtTyMg0HYApvKXwzJ9Xys"
TELEGRAM_CHAT_ID = "2047038250"
DB_FILE = "posiciones.json"

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Activo"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000))), daemon=True).start()

class CazadorPro:
    def __init__(self):
        self.bot = telepot.Bot(TELEGRAM_TOKEN)
        self.trailing_pct = 0.08 
        self.enviar_telegram("🤖 BOT REINICIADO Y LISTO")

    def enviar_telegram(self, msg):
        try: self.bot.sendMessage(TELEGRAM_CHAT_ID, msg)
        except: pass

    def cargar(self):
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f: return json.load(f)
        return {}

    def guardar(self, data):
        with open(DB_FILE, 'w') as f: json.dump(data, f)

    def ejecutar(self):
        posiciones = self.cargar()
        
        # 1. SEGUIMIENTO
        for ticker, datos in list(posiciones.items()):
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                if hist.empty: continue
                precio_actual = hist['Close'].iloc[-1]
                
                # Cálculos
                beneficio = ((precio_actual - datos['entrada']) / datos['entrada']) * 100
                nuevo_sl = precio_actual * (1 - self.trailing_pct)
                
                # Check Stop Loss
                if precio_actual <= datos['sl']:
                    self.enviar_telegram(f"🛑 STOP OUT: {ticker}\nEntrada: ${datos['entrada']:.2f}\nSalida: ${precio_actual:.2f}\nBeneficio Final: {beneficio:.2f}%")
                    del posiciones[ticker]
                else:
                    # Ajuste dinámico de Stop Loss
                    if nuevo_sl > datos['sl']:
                        datos['sl'] = nuevo_sl
                        self.enviar_telegram(f"📈 SEGUIMIENTO: {ticker}\nPrecio Actual: ${precio_actual:.2f}\nBeneficio: {beneficio:.2f}%\nNuevo SL Dinámico: ${datos['sl']:.2f}")
                    else:
                        # Solo enviamos update si el beneficio es relevante
                        print(f"{ticker} estable, beneficio: {beneficio:.2f}%")
            except: continue
        self.guardar(posiciones)

        # 2. ESCÁNER
        try:
            muestra = random.sample(si.tickers_nasdaq(), 50)
            for ticker in muestra:
                if ticker in posiciones: continue
                stock = yf.Ticker(ticker)
                hist = stock.history(period="30d")
                if len(hist) < 30: continue
                
                precio = hist['Close'].iloc[-1]
                vol_actual = hist['Volume'].iloc[-1]
                vol_promedio = hist['Volume'].iloc[:-1].mean()
                
                if precio <= 20.00 and (vol_actual / vol_promedio) > 3.0:
                    posiciones[ticker] = {'entrada': precio, 'sl': precio * (1 - self.trailing_pct)}
                    self.guardar(posiciones)
                    self.enviar_telegram(f"🚀 NUEVA ENTRADA: {ticker}\nPrecio Entrada: ${precio:.2f}\nStop Loss Inicial: ${posiciones[ticker]['sl']:.2f}")
        except: pass

if __name__ == "__main__":
    cazador = CazadorPro()
    while True:
        cazador.ejecutar()
        time.sleep(1800)
