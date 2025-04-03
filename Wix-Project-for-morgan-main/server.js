const express = require("express");
const puppeteer = require("puppeteer");
const axios = require("axios");
const path = require("path");
const app = express();

const PORT = process.env.PORT || 3000; // Use dynamic Vercel port or fallback to 3000

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static("public"));

// Function to scrape metal prices
async function getMetalPrices() {
    const browser = await puppeteer.launch({ headless: "new" });
    const page = await browser.newPage();
    await page.goto("https://www.metalsdaily.com/live-prices/pgms/");

    const metalPrices = await page.evaluate(() => {
        const rows = document.querySelectorAll("table tr");
        let prices = {};

        rows.forEach(row => {
            const cols = row.querySelectorAll("td");
            if (cols.length > 2) {
                let metal = cols[0].innerText.trim();
                let askPrice = cols[2].innerText.trim().replace(/,/g, "");
                if (metal.includes("USD/OZ")) {
                    metal = metal.replace("USD/OZ", "").trim();
                    prices[metal] = parseFloat(askPrice) / 28; // Convert to per gram
                }
            }
        });
        return prices;
    });

    await browser.close();
    return metalPrices;
}

// Function to get historical metal data from Yahoo Finance
async function getMetalData(symbol) {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?range=1y&interval=1d`;
    try {
        const response = await axios.get(url);
        const data = response.data.chart.result[0];
        return {
            dates: data.timestamp.map(ts => new Date(ts * 1000).toISOString().split("T")[0]),
            prices: data.indicators.quote[0].close
        };
    } catch (error) {
        console.error("Error fetching data:", error);
        return { dates: [], prices: [] };
    }
}

app.get("/", async (req, res) => {
    let metalPrices = await getMetalPrices();
    let goldData = await getMetalData("GC=F");
    let silverData = await getMetalData("SI=F");

    metalPrices["Gold"] = metalPrices["Gold"] || goldData.prices.slice(-1)[0] / 28;
    metalPrices["Silver"] = metalPrices["Silver"] || silverData.prices.slice(-1)[0] / 28;

    res.render("index", { metalPrices, goldData, silverData });
});

// Export for Vercel serverless
module.exports = app;

