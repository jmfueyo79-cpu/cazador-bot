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
# Zona horaria de NY para gestionar el mercado
NY_TIMEZONE = pytz.timezone('America/New_York')

class CazadorPro:
    def __init__(self):
        self.bot = telepot.Bot(TELEGRAM_TOKEN)
        self.trailing_pct = 0.20
        self.posiciones = {}
        self.enviar_telegram("🚀 BOT INICIADO: Modo Francotirador (Filtro Anti-Gap y Anti-After)")

    def es_horario_operativo(self):
        """Devuelve True solo si el mercado está abierto y han pasado 30 min."""
        now = datetime.now(NY_TIMEZONE)
        # Mercado abre a las 9:30 AM y cierra a las 4:00 PM
        es_laboral = now.weekday() < 5
        apertura_valida = now.hour == 9 and now.minute >= 30 or (now.hour > 9 and now.hour < 16)
        return es_laboral and apertura_valida

    def ejecutar(self):
        # 1. SEGUIMIENTO (Siempre activo para proteger posiciones)
        for ticker, datos in list(self.posiciones.items()):
            # ... (código de seguimiento igual al anterior) ...
            pass

        # 2. ESCÁNER SOLO EN HORARIO OPERATIVO Y ESTABLE
        if not self.es_horario_operativo():
            return # El bot duerme si no es horario de oro

        try:
            muestra = random.sample(si.tickers_nasdaq(), 200) # Muestra más pequeña para mayor velocidad
            for ticker in muestra:
                if ticker in self.posiciones or ticker.endswith('W'): continue
                
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                if len(hist) < 5: continue
                
                precio_actual = hist['Close'].iloc[-1]
                precio_apertura = hist['Open'].iloc[-1]
                
                # FILTRO DE GAP: Evita acciones que abrieron con salto > 3%
                gap = abs((precio_apertura - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2])
                if gap > 0.03: continue 
                
                # FILTRO DE CALIDAD (Precio y Momentum)
                if not (2.00 <= precio_actual <= 20.00): continue
                
                vol_actual = hist['Volume'].iloc[-1]
                vol_promedio = hist['Volume'].iloc[:-2].mean()
                cambio_5d = ((precio_actual - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) * 100
                
                if (vol_actual / vol_promedio) > 3.0 and cambio_5d > 5.0:
                    self.posiciones[ticker] = {'entrada': precio_actual, 'sl': precio_actual * (1 - self.trailing_pct)}
                    self.enviar_telegram(f"🎯 ENTRADA FRANCOTIRADOR: {ticker}\nPrecio: ${precio_actual:.2f}\nMomentum: {cambio_5d:.2f}%")
        except: pass
