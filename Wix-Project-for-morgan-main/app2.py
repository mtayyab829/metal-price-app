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
    chrome_options.add_argument("--no-sandbox")  # Essential for cloud
    chrome_options.add_argument("--disable-dev-shm-usage")  # Essential for cloud
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    
    # Set path to chromedriver based on environment
    if os.path.exists("/app/.apt/usr/bin/chromedriver"):  # Streamlit Cloud path
        service = Service("/app/.apt/usr/bin/chromedriver")
    else:
        service = Service()  # Local development
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_metal_prices():
    """Scrape metal prices with robust error handling"""
    driver = setup_driver()
    try:
        url = "https://www.metalsdaily.com/live-prices/pgms/"
        driver.get(url)
        
        # Wait for table to load
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

# Rest of your original code remains exactly the same...
# [Include all your existing Streamlit UI code from the original file]
# [From the def get_metal_data() function through to the end of the file]
