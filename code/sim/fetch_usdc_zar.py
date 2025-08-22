# fetch_usdc_zar.py
import requests
import pandas as pd
import time
from datetime import datetime, timezone
import matplotlib.pyplot as plt


# Constants
API_URL = "https://min-api.cryptocompare.com/data/v2/histohour"
SYMBOL = "USDC"
CURRENCY = "ZAR"
LIMIT = 2000  # max candles per request


def fetch_with_retries(url, params, max_retries=5, backoff_factor=2):
    """
    Fetch data from API with retry + exponential backoff.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            wait_time = backoff_factor ** attempt
            print(f"⚠️ Error: {e}, retrying in {wait_time}s...")
            time.sleep(wait_time)
    raise Exception("❌ Max retries reached. Failed to fetch data.")


def fetch_usdc_zar(hours=2000):
    """
    Fetch historical USDC/ZAR data from CryptoCompare.
    - hours: number of hours back to fetch (max 2000 per request)
    """
    params = {
        "fsym": SYMBOL,
        "tsym": CURRENCY,
        "limit": min(hours, LIMIT - 1),  # 2000 candles max
        "toTs": int(datetime.now(timezone.utc).timestamp())  # timezone aware
    }

    data = fetch_with_retries(API_URL, params)
    if "Data" not in data or "Data" not in data["Data"]:
        raise ValueError("Invalid response format")

    df = pd.DataFrame(data["Data"]["Data"])
    if df.empty:
        raise ValueError("No data returned from API")

    # Convert UNIX timestamp to datetime (UTC)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df.set_index("time", inplace=True)

    # Keep only relevant columns
    df = df[["open", "high", "low", "close", "volumefrom", "volumeto"]]
    df.rename(columns={"volumefrom": "volume_usdc", "volumeto": "volume_zar"}, inplace=True)

    return df


def save_to_csv(df, filename="usdc_zar_history.csv"):
    df.to_csv(filename)
    print(f"💾 Saved historical USDC/ZAR data: {df.shape}")


def plot_data(df):
    """
    Plot closing price and ZAR trading volume.
    """
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot closing price (line)
    ax1.set_xlabel("Time (UTC)")
    ax1.set_ylabel("Price (ZAR)", color="blue")
    ax1.plot(df.index, df["close"], color="blue", label="USDC/ZAR Price")
    ax1.tick_params(axis="y", labelcolor="blue")

    # Plot volume (bar chart)
    ax2 = ax1.twinx()
    ax2.set_ylabel("Volume (ZAR)", color="gray")
    ax2.bar(df.index, df["volume_zar"], color="gray", alpha=0.3, label="Volume (ZAR)")
    ax2.tick_params(axis="y", labelcolor="gray")

    fig.tight_layout()
    plt.title("USDC/ZAR Historical Price & Volume")
    plt.show()


if __name__ == "__main__":
    try:
        df = fetch_usdc_zar(hours=2000)
        save_to_csv(df)
        plot_data(df)
    except Exception as e:
        print(f"❌ Failed: {e}")
