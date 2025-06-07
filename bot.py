import os, time, requests, numpy as np, pandas as pd
import telebot
from datetime import datetime

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
PAIR = os.getenv("PAIR", "EUR/USD")
INTERVAL = os.getenv("INTERVAL", "1min")

bot = telebot.TeleBot(BOT_TOKEN)

def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed>=0].sum()/period
    down = -seed[seed<0].sum()/period
    rs = up/down if down!=0 else 0
    rsi = [100 - 100/(1+rs)]
    for delta in deltas[period:]:
        up = (up*(period-1) + max(delta,0))/period
        down = (down*(period-1) + max(-delta,0))/period
        rs = up/down if down!=0 else 0
        rsi.append(100 - 100/(1+rs))
    return rsi

def calculate_macd(series):
    ema12 = series.ewm(span=12).mean()
    ema26 = series.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    return macd.iloc[-1], signal.iloc[-1]

def get_market_data():
    url = f'https://api.twelvedata.com/time_series?symbol={PAIR.replace("/","")}&interval={INTERVAL}&apikey={API_KEY}&outputsize=100'
    resp = requests.get(url).json()
    return [float(v['close']) for v in resp['values']][::-1]

def send_signal(action):
    now = datetime.now().strftime("%I:%M %p")
    text = f"📊 Signal: {PAIR}\n🕐 Timeframe: {INTERVAL}\n{'🟢' if action=='UP' else '🔴'} Action: {action}\n⏰ Entry Time: {now}"
    bot.send_message(chat_id=CHAT_ID, text=text)

def job():
    prices = get_market_data()
    rsi = calculate_rsi(prices)[-1]
    ser = pd.Series(prices)
    macd, sig = calculate_macd(ser)
    ma20 = ser.rolling(20).mean().iloc[-1]
    if rsi<30 and macd>sig and prices[-1]>ma20:
        send_signal("UP")
    elif rsi>70 and macd<sig and prices[-1]<ma20:
        send_signal("DOWN")

while True:
    try:
        job()
    except Exception as e:
        print(e)
    time.sleep(60)
