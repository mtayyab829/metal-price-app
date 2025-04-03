import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure matplotlib for headless environment
plt.switch_backend('Agg')

def setup_driver():
    """Configure ChromeDriver for Streamlit Cloud"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    
    # Set path to chromedriver
    if os.path.exists("/app/.apt/usr/bin/chromedriver"):
        service = Service("/app/.apt/usr/bin/chromedriver")
    else:
        service = Service()
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_metal_prices():
    """Scrape metal prices with robust error handling"""
    driver = setup_driver()
    try:
        url = "https://www.metalsdaily.com/live-prices/pgms/"
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        rows = driver.find_elements(By.TAG_NAME, "tr")
        metal_prices = {}

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) > 2:
                metal = cols[0].text.strip()
                ask_price = cols[2].text.strip()
                
                if "USD/OZ" in metal:
                    metal_name = metal.replace("USD/OZ", "").strip()
                    try:
                        metal_prices[metal_name] = float(ask_price.replace(',', '')) / 28
                    except ValueError:
                        continue
        
        return metal_prices
    except Exception as e:
        st.warning(f"Couldn't fetch live prices: {str(e)}")
        return {}
    finally:
        driver.quit()

def get_metal_data(ticker):
    """Get historical data with error handling"""
    try:
        data = yf.Ticker(ticker).history(period="1y")
        data.index = pd.to_datetime(data.index)
        return data
    except Exception as e:
        st.warning(f"Couldn't fetch {ticker} data: {str(e)}")
        return pd.DataFrame()

# Streamlit UI
st.title("Metal Price Dashboard")

# Fetch data
with st.spinner("Fetching metal prices..."):
    metal_prices = get_metal_prices()
    gold_data = get_metal_data("GC=F")
    silver_data = get_metal_data("SI=F")

# Process prices
gold_price = metal_prices.get("Gold", gold_data['Close'].iloc[-1] / 28 if not gold_data.empty else 0)
silver_price = metal_prices.get("Silver", silver_data['Close'].iloc[-1] / 28 if not silver_data.empty else 0)

# Display current prices
st.subheader("Current Prices per Gram (Live)")
if metal_prices:
    col1, col2 = st.columns(2)
    for i, (metal, price) in enumerate(metal_prices.items()):
        if i % 2 == 0:
            with col1:
                st.metric(label=metal, value=f"${price:.2f}")
        else:
            with col2:
                st.metric(label=metal, value=f"${price:.2f}")
else:
    st.warning("Using fallback pricing data")
    st.metric(label="Gold", value=f"${gold_price:.2f}")
    st.metric(label="Silver", value=f"${silver_price:.2f}")

# Jewelry calculator
st.subheader("Jewelry Value Calculator")
metal_choice = st.selectbox("Select Metal", list(metal_prices.keys()) if metal_prices else ["Gold", "Silver"])
weight = st.number_input("Enter weight in grams", min_value=0.0, value=1.0, step=0.1)

if metal_choice and weight > 0:
    price = metal_prices.get(metal_choice, gold_price if metal_choice == "Gold" else silver_price)
    jewelry_value = price * weight
    st.success(f"Estimated {metal_choice} Jewelry Value: ${jewelry_value:.2f}")

# Plot charts
def plot_chart(data, title):
    if data.empty:
        st.warning(f"No data available for {title}")
        return
        
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(data.index, data['Close'])
    ax.set_title(title)
    ax.grid(True)
    st.pyplot(fig)

st.subheader("Gold & Silver Price Charts")
plot_chart(gold_data, "Gold Price History")
plot_chart(silver_data, "Silver Price History")

st.subheader("Powered by Gilbert Systems 📊")
