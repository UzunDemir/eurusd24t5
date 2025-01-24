import streamlit as st
import requests

# Функция для получения данных EUR/USD с CoinGecko
def fetch_data_coingecko():
    url = "https://api.coingecko.com/api/v3/exchange_rates"  # API для валютных курсов
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверяем на ошибки HTTP
        data = response.json()
        rates = data['rates']
        eur_to_usd = rates['usd']['value'] / rates['eur']['value']  # EUR/USD курс
        return eur_to_usd
    except requests.RequestException as e:
        st.error(f"Ошибка при получении данных: {e}")
        return None

# Заголовок приложения
st.title("Мониторинг EUR/USD")
st.write("Данные о валютной паре EUR/USD с использованием CoinGecko API.")

# Кнопка для обновления данных
if st.button("Обновить курс"):
    eur_to_usd = fetch_data_coingecko()

    if eur_to_usd:
        # Отображаем текущий курс
        st.subheader("Текущий курс EUR/USD")
        st.metric(label="EUR/USD", value=f"{eur_to_usd:.4f}")
    else:
        st.error("Не удалось получить данные. Проверьте подключение к интернету или доступность API.")

# Примечание
st.info("Данные предоставлены API CoinGecko. Информация обновляется в реальном времени.")
