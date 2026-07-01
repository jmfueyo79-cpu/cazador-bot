import os
import threading
import time
import yfinance as yf
import random
from flask import Flask
import telepot
from yahoo_fin import stock_info as si

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = "8620604654:AAEsvDlxfzCpICHtTyMg0HYApvKXwzJ9Xys"
TELEGRAM_CHAT_ID = "2047038250"

# --- SERVIDOR PARA MANTENER EL BOT VIVO ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot Cazador de Momentum Activo"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000))), daemon=True).start()

class CazadorPro:
    def __init__(self):
        self.bot = telepot.Bot(TELEGRAM_TOKEN)
        self.trailing_pct = 0.20  # Mayor holgura para evitar cierres prematuros
        self.posiciones = {}
        self.enviar_telegram("🚀 BOT INICIADO: Cazador de Alta Probabilidad (Filtro Momentum 5%)")

    def enviar_telegram(self, msg):
        try: self.bot.sendMessage(TELEGRAM_CHAT_ID, msg)
        except: pass

    def ejecutar(self):
        # 1. SEGUIMIENTO (Trailing Stop Dinámico)
        for ticker, datos in list(self.posiciones.items()):
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                if hist.empty: continue
                precio_actual = hist['Close'].iloc[-1]
                
                beneficio = ((precio_actual - datos['entrada']) / datos['entrada']) * 100
                nuevo_sl = precio_actual * (1 - self.trailing_pct)
                
                if precio_actual <= datos['sl']:
                    self.enviar_telegram(f"🛑 STOP OUT: {ticker}\nEntrada: ${datos['entrada']:.2f}\nSalida: ${precio_actual:.2f}\nBeneficio Final: {beneficio:.2f}%")
                    del self.posiciones[ticker]
                elif nuevo_sl > datos['sl']:
                    datos['sl'] = nuevo_sl
                    self.enviar_telegram(f"📈 SEGUIMIENTO: {ticker}\nPrecio: ${precio_actual:.2f}\nBeneficio: {beneficio:.2f}%\nNuevo SL: ${datos['sl']:.2f}")
            except: continue

        # 2. ESCÁNER DE ALTA PROBABILIDAD
        try:
            # Seleccionamos 500 del NASDAQ para tener una muestra robusta
            muestra = random.sample(si.tickers_nasdaq(), 500)
            for ticker in muestra:
                if ticker in self.posiciones: continue
                
                stock = yf.Ticker(ticker)
                hist = stock.history(period="30d")
                if len(hist) < 20: continue
                
                precio = hist['Close'].iloc[-1]
                vol_actual = hist['Volume'].iloc[-1]
                vol_promedio = hist['Volume'].iloc[:-1].mean()
                cambio_5d = ((precio - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) * 100
                
                # CRITERIOS DE ALTA PROBABILIDAD:
                # 1. Precio <= 20$ (rango especulativo ideal)
                # 2. RVOL > 3.0 (inyección de capital institucional)
                # 3. Momentum > 5% (tendencia fuerte confirmada)
                if (precio <= 20.00 and 
                    (vol_actual / vol_promedio) > 3.0 and 
                    cambio_5d > 5.0):
                    
                    self.posiciones[ticker] = {'entrada': precio, 'sl': precio * (1 - self.trailing_pct)}
                    self.enviar_telegram(f"🔥 NUEVA LÍDER (Alta Probabilidad): {ticker}\nPrecio: ${precio:.2f}\nMomentum 5d: {cambio_5d:.2f}%\nSL Inicial: ${self.posiciones[ticker]['sl']:.2f}")
        except: pass

if __name__ == "__main__":
    cazador = CazadorPro()
    while True:
        cazador.ejecutar()
        # Escaneo cada 30 minutos
        time.sleep(1800)
                
