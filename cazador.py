import os
import threading
import time
import yfinance as yf
import random
from flask import Flask
import telepot
from yahoo_fin import stock_info as si
from datetime import datetime
import pytz

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = "8620604654:AAEsvDlxfzCpICHtTyMg0HYApvKXwzJ9Xys"
TELEGRAM_CHAT_ID = "2047038250"
NY_TIMEZONE = pytz.timezone('America/New_York')

# --- SERVIDOR ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot Francotirador Activo"

class CazadorPro:
    def __init__(self):
        self.bot = telepot.Bot(TELEGRAM_TOKEN)
        self.trailing_pct = 0.20
        self.posiciones = {}
        # Llamada al método definido dentro de la clase
        self.enviar_telegram("🎯 BOT LISTO: Modo Francotirador Activo (Horario NY)")

    def enviar_telegram(self, msg):
        try:
            self.bot.sendMessage(TELEGRAM_CHAT_ID, msg)
        except Exception as e:
            print(f"Error enviando telegram: {e}")

    def es_horario_operativo(self):
        now = datetime.now(NY_TIMEZONE)
        es_laboral = now.weekday() < 5
        apertura_valida = (now.hour == 9 and now.minute >= 59) or (now.hour >= 10 and now.hour < 16)
        return es_laboral and apertura_valida

    def ejecutar(self):
        # 1. SEGUIMIENTO
        for ticker, datos in list(self.posiciones.items()):
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                if hist.empty: continue
                precio_actual = hist['Close'].iloc[-1]
                
                beneficio = ((precio_actual - datos['entrada']) / datos['entrada']) * 100
                nuevo_sl = precio_actual * (1 - self.trailing_pct)
                
                if precio_actual <= datos['sl']:
                    self.enviar_telegram(f"🛑 STOP OUT: {ticker}\nBeneficio Final: {beneficio:.2f}%")
                    del self.posiciones[ticker]
                elif nuevo_sl > datos['sl']:
                    datos['sl'] = nuevo_sl
                    self.enviar_telegram(f"📈 SEGUIMIENTO: {ticker}\nPrecio: ${precio_actual:.2f}\nBeneficio: {beneficio:.2f}%\nNuevo SL: ${datos['sl']:.2f}")
            except: continue

        # 2. ESCÁNER
        if not self.es_horario_operativo(): return

        try:
            muestra = random.sample(si.tickers_nasdaq(), 200)
            for ticker in muestra:
                if ticker in self.posiciones or ticker.endswith('W'): continue
                
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                if len(hist) < 5: continue
                
                precio_actual = hist['Close'].iloc[-1]
                precio_apertura = hist['Open'].iloc[-1]
                
                if abs((precio_apertura - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) > 0.03: continue
                if not (2.00 <= precio_actual <= 20.00): continue
                
                vol_actual = hist['Volume'].iloc[-1]
                vol_promedio = hist['Volume'].iloc[:-2].mean()
                cambio_5d = ((precio_actual - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) * 100
                
                if (vol_actual / vol_promedio) > 3.0 and cambio_5d > 5.0:
                    self.posiciones[ticker] = {'entrada': precio_actual, 'sl': precio_actual * (1 - self.trailing_pct)}
                    self.enviar_telegram(f"🎯 ENTRADA FRANCOTIRADOR: {ticker}\nPrecio: ${precio_actual:.2f}\nMomentum 5d: {cambio_5d:.2f}%")
        except: pass

if __name__ == "__main__":
    # Arrancar Flask en un hilo
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))), daemon=True).start()
    
    cazador = CazadorPro()
    while True:
        cazador.ejecutar()
        time.sleep(300)
                    
