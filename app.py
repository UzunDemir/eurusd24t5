import streamlit as st
import plotly.graph_objects as go
import ccxt
import pandas as pd
import datetime
import time

# Инициализация Binance
exchange = ccxt.binance()
symbol = 'EUR/USDT'

# Функция для получения данных
def fetch_data():
    # Получаем текущую дату и время
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Получаем данные за последние 24 часа
    ohlcv = exchange.fetch_ohlcv(
        symbol, 
        timeframe='5m', 
        since=exchange.parse8601((datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat())
    )

    # Преобразуем данные в DataFrame
    data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')

    # Извлекаем максимальную и минимальную цену
    max_price = max(ohlcv, key=lambda x: x[2])
    min_price = min(ohlcv, key=lambda x: x[3])
    ticker = exchange.fetch_ticker(symbol)
    last_price = ticker['last']

    # Добавляем объемы покупок и продаж
    data['buy_volume'] = data.apply(lambda row: row['volume'] if row['close'] > row['open'] else 0, axis=1)
    data['sell_volume'] = data.apply(lambda row: row['volume'] if row['close'] <= row['open'] else 0, axis=1)

    # Добавление скользящих средних
    data['SMA_50'] = data['close'].rolling(window=50).mean()
    data['EMA_50'] = data['close'].ewm(span=50, adjust=False).mean()

    # Добавление RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    return data, current_time, last_price, max_price, min_price

# Функция для создания графика
def create_plot(data, current_time, last_price, max_price, min_price):
    # Создаем график
    fig = go.Figure()

    # Свечи
    fig.add_trace(go.Candlestick(
        x=data['timestamp'],
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Candlesticks'
    ))

    # Линии для максимума, минимума и последней цены
    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=[max_price[2]] * len(data),
        mode='lines',
        name=f'Max Price ({max_price[2]})',
        line=dict(color='green', dash='dash')
    ))

    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=[min_price[3]] * len(data),
        mode='lines',
        name=f'Min Price ({min_price[3]})',
        line=dict(color='red', dash='dash')
    ))

    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=[last_price] * len(data),
        mode='lines',
        name=f'Last Price ({last_price})',
        line=dict(color='blue')
    ))

    # Объемы покупок (зеленые столбцы)
    fig.add_trace(go.Bar(
        x=data['timestamp'],
        y=data['buy_volume'],
        name='Buy Volume',
        marker_color='green',
        yaxis='y2',
        opacity=0.7
    ))

    # Объемы продаж (красные столбцы)
    fig.add_trace(go.Bar(
        x=data['timestamp'],
        y=data['sell_volume'],
        name='Sell Volume',
        marker_color='red',
        yaxis='y2',
        opacity=0.7
    ))

    # Добавление скользящих средних (SMA, EMA)
    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['SMA_50'],
        mode='lines',
        name='SMA 50',
        line=dict(color='orange')
    ))

    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['EMA_50'],
        mode='lines',
        name='EMA 50',
        line=dict(color='purple')
    ))

    # Добавление RSI на том же графике
    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['RSI'],
        mode='lines',
        name='RSI',
        line=dict(color='blue'),
        yaxis='y3'
    ))

    # Настройки оформления
    fig.update_layout(
        title=f'{symbol} 5m Candlestick Chart with Volume, SMA, EMA, RSI',
        xaxis_title='Time',
        yaxis_title='Price (USDT)',
        template='plotly_dark',
        height=800,
        xaxis_rangeslider_visible=False,
        yaxis=dict(
            title='Price (USDT)',
            side='right'
        ),
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='left',
            showgrid=False
        ),
        yaxis3=dict(
            title='RSI',
            overlaying='y',
            side='right',
            position=0.15,
            showgrid=False,
            zeroline=True
        )
    )

    return fig

# Streamlit UI
st.set_page_config(layout="wide", page_title="Cryptocurrency Chart")

st.title("Cryptocurrency 24H Candlestick Chart")
st.write("Symbol: ", symbol)

# Обновление данных
if st.button("Refresh Data"):
    with st.spinner("Fetching new data..."):
        data, current_time, last_price, max_price, min_price = fetch_data()
        st.write(f"Data last updated at: {current_time}")
        fig = create_plot(data, current_time, last_price, max_price, min_price)
        st.plotly_chart(fig, use_container_width=True)
