import streamlit as st
import platform
import os
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# Check and install dependencies if needed
try:
    import yfinance
    import pandas
    import matplotlib
    from selenium import webdriver
except ImportError as e:
    st.warning(f"Installing missing dependencies: {e}")
    subprocess.check_call(["pip", "install", "yfinance", "pandas", "matplotlib", "selenium", "webdriver-manager"])
    import yfinance as yf
    import pandas as pd
    import matplotlib.pyplot as plt
    from selenium import webdriver

# Configure Selenium for Streamlit Cloud
def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Set up ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Function to scrape metal prices with improved error handling
def get_metal_prices():
    driver = None
    try:
        driver = setup_selenium()
        url = "https://www.metalsdaily.com/live-prices/pgms/"
        driver.get(url)
        
        # Wait for table to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        
        rows = driver.find_elements(By.XPATH, "//table//tr")
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
        st.warning(f"Couldn't scrape live prices: {str(e)}")
        return {}
    finally:
        if driver:
            driver.quit()

# Fetch historical data with error handling
def get_metal_data(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1y")
        data.index = pd.to_datetime(data.index)
        return data
    except Exception as e:
        st.warning(f"Couldn't fetch {ticker} data: {str(e)}")
        return pd.DataFrame()

# Streamlit UI
st.title("Metal Price Dashboard")

# Main app logic
try:
    with st.spinner("Fetching data..."):
        metal_prices = get_metal_prices()
        gold_data = get_metal_data("GC=F")
        silver_data = get_metal_data("SI=F")

    # Display prices
    st.subheader("Current Prices per Gram")
    if metal_prices:
        col1, col2 = st.columns(2)
        for i, (metal, price) in enumerate(metal_prices.items()):
            if i % 2 == 0:
                with col1:
                    st.metric(label=f"{metal}", value=f"${price:.2f}")
            else:
                with col2:
                    st.metric(label=f"{metal}", value=f"${price:.2f}")
    else:
        st.warning("Using Yahoo Finance fallback data")
        if not gold_data.empty:
            gold_price = gold_data['Close'].iloc[-1] / 28
            st.metric(label="Gold", value=f"${gold_price:.2f}")
        if not silver_data.empty:
            silver_price = silver_data['Close'].iloc[-1] / 28
            st.metric(label="Silver", value=f"${silver_price:.2f}")

    # Plot charts with improved error handling
    def plot_chart(data, title):
        if data.empty:
            st.warning(f"No data available for {title}")
            return
            
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(data.index, data['Close'])
        ax.set_title(title)
        ax.grid(True)
        st.pyplot(fig)

    st.subheader("Historical Prices")
    plot_chart(gold_data, "Gold Price History")
    plot_chart(silver_data, "Silver Price History")

    # Jewelry calculator
    st.subheader("Jewelry Value Calculator")
    metals = list(metal_prices.keys()) if metal_prices else ["Gold", "Silver"]
    metal_choice = st.selectbox("Select Metal", metals)
    weight = st.number_input("Enter weight in grams", min_value=0.0, value=1.0, step=0.1)

    if metal_choice and weight > 0:
        if metal_prices:
            price = metal_prices[metal_choice]
        elif metal_choice == "Gold" and not gold_data.empty:
            price = gold_data['Close'].iloc[-1] / 28
        elif metal_choice == "Silver" and not silver_data.empty:
            price = silver_data['Close'].iloc[-1] / 28
        else:
            price = 0
            
        jewelry_value = price * weight
        st.success(f"Estimated {metal_choice} Jewelry Value: ${jewelry_value:.2f}")

except Exception as e:
    st.error(f"Application error: {str(e)}")
finally:
    st.subheader("Powered by Gilbert Systems 📊")
