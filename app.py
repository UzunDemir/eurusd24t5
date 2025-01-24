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

    fig.add_trace(go.Bar(
        x=data['timestamp'],
        y=data['buy_volume'],
        name='Buy Volume',
        marker_color='green',
        opacity=0.7
    ))

    fig.add_trace(go.Bar(
        x=data['timestamp'],
        y=data['sell_volume'],
        name='Sell Volume',
        marker_color='red',
        opacity=0.7
    ))

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

    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['RSI'],
        mode='lines',
        name='RSI',
        line=dict(color='blue'),
        yaxis='y2'
    ))

    fig.update_layout(
        title=f'{symbol} 5m Candlestick Chart with Volume, SMA, EMA, RSI',
        xaxis_title='Time',
        yaxis_title='Price (USDT)',
        template='plotly_dark',
        height=800,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        yaxis=dict(
            title='Price (USDT)',
            side='right'
        ),
        yaxis2=dict(
            title='RSI',
            overlaying='y',
            side='left',
            range=[0, 100]
        )
    )

    return fig

# Streamlit UI
st.title("24H Price Chart")
st.write("Streaming live data from Binance for EUR/USDT...")

# Fetch and display data
data, last_price, max_price, min_price = fetch_data()
if data is not None:
    st.metric("Последняя цена (USDT)", f"{last_price:.2f}")
    fig = create_plot(data, last_price, max_price, min_price)
    st.plotly_chart(fig, use_container_width=True)
