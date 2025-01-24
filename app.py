import streamlit as st
import plotly.graph_objects as go
import ccxt
import pandas as pd
import datetime

# Инициализация Binance
exchange = ccxt.binance()
symbol = 'EUR/USDT'

# Кэширование данных
@st.cache_data(ttl=300)
def fetch_data():
    try:
        ohlcv = exchange.fetch_ohlcv(
            symbol, 
            timeframe='5m', 
            since=exchange.parse8601((datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat())
        )

        data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')

        max_price = max(ohlcv, key=lambda x: x[2])
        min_price = min(ohlcv, key=lambda x: x[3])
        ticker = exchange.fetch_ticker(symbol)
        last_price = ticker['last']

        data['buy_volume'] = data.apply(lambda row: row['volume'] if row['close'] > row['open'] else 0, axis=1)
        data['sell_volume'] = data.apply(lambda row: row['volume'] if row['close'] <= row['open'] else 0, axis=1)

        data['SMA_50'] = data['close'].rolling(window=50).mean()
        data['EMA_50'] = data['close'].ewm(span=50, adjust=False).mean()

        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        return data, last_price, max_price, min_price
    except Exception as e:
        st.error(f"Ошибка при получении данных: {e}")
        return None, None, None, None

# Функция для создания графика
def create_plot(data, last_price, max_price, min_price):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data['timestamp'],
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Candlesticks'
    ))

    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=[max_price[2]] * len(data),
        mode='lines',
        name=f'Max Price ({max_price[2]})',
        line=dict(color='green', dash='dash')
    ))

    fig.add_trace(go.Scatter(
        x=data['timestamp'],
       
