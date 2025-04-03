import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Function to scrape metal prices using Selenium
def get_metal_prices():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    url = "https://www.metalsdaily.com/live-prices/pgms/"
    driver.get(url)
    
    rows = driver.find_elements("xpath", "//table//tr")
    metal_prices = {}

    for row in rows:
        cols = row.find_elements("tag name", "td")
        if len(cols) > 2:
            metal = cols[0].text.strip()
            ask_price = cols[2].text.strip()  # Ask price is in column index 2
            
            if "USD/OZ" in metal:
                metal_name = metal.replace("USD/OZ", "").strip()
                try:
                    metal_prices[metal_name] = float(ask_price.replace(',', '')) / 28  # Convert to per gram
                except ValueError:
                    pass  # Skip if conversion fails
        
        elif len(cols) > 1:
            metal = cols[0].text.strip()
            price = cols[1].text.strip()
            if "USD/OZ" in metal:
                metal_name = metal.replace("USD/OZ", "").strip()
                try:
                    metal_prices[metal_name] = float(price.replace(',', '')) / 28  # Convert to per gram
                except ValueError:
                    pass  # Skip if conversion fails

    driver.quit()
    return metal_prices

# Fetch historical data for metals from Yahoo Finance
def get_metal_data(ticker):
    data = yf.Ticker(ticker).history(period="1y")
    data.index = pd.to_datetime(data.index)
    return data

# Streamlit UI
st.title("Metal Price Dashboard")

# st.image("logo.jpg", use_column_width=True)

# Scrape real-time metal prices
with st.spinner("Fetching live metal prices..."):
    metal_prices = get_metal_prices()
    
# Historical Data Fallback (Gold & Silver from Yahoo Finance)
gold_data = get_metal_data("GC=F")
silver_data = get_metal_data("SI=F")

gold_price = metal_prices.get("Gold", gold_data['Close'].iloc[-1] / 28)  # Use scraped price or fallback
silver_price = metal_prices.get("Silver", silver_data['Close'].iloc[-1] / 28)

metal_prices["GOLD"] = gold_price
metal_prices["SILVER"] = silver_price

# Display real-time prices
st.subheader("Current Prices per Gram (Live)")
for metal, price in metal_prices.items():
    st.metric(label=f"{metal} Price", value=f"${price:.2f}")

# User Input for Jewelry Value Calculation
st.subheader("Jewelry Value Calculator")
metal_choice = st.selectbox("Select Metal", list(metal_prices.keys()))
weight = st.number_input("Enter weight in grams", min_value=0.0, value=0.0, step=0.1)

if metal_choice and weight > 0:
    jewelry_value = metal_prices[metal_choice] * weight
    st.subheader(f"Estimated Jewelry Value: ${jewelry_value:.2f}")

# Plot Price Charts
def plot_line_chart(data, title):
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data['Close'], label="Close Price")
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.grid(True)
    plt.legend()

    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    st.image(buf)

st.subheader("Gold & Silver Price Charts")
plot_line_chart(gold_data, "Gold Price Chart")
plot_line_chart(silver_data, "Silver Price Chart")
st.subheader("Powered by Gilbert Systems 📊")
