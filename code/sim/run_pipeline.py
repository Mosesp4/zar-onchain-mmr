import os
import pandas as pd
import subprocess
from pathlib import Path
import ydata_profiling
import sys
import requests
from datetime import datetime, timedelta
import time
import pytz

DATA_DIR = Path("../data")
RAW_DATA_FILE = DATA_DIR / "usdc_zar.csv"
PROFILE_REPORT_FILE = DATA_DIR / "usdc_zar_profile.html"

def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        print(f"📦 Installing missing package: {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Ensure dependencies exist
for pkg in ["requests", "pandas", "ydata_profiling", "pytz"]:
    install_and_import(pkg)

def fetch_usdc_zar_cryptocompare(days=90, timeframe="hour"):
    """
    Fetch historical USDC/ZAR OHLCV data from CryptoCompare with pagination.
    """
    print("📡 Fetching USDC/ZAR data from CryptoCompare...")
    base_url = "https://min-api.cryptocompare.com/data/v2/histohour"
    limit = 2000  # Max candles per request
    target_hours = days * 24
    all_candles = []
    to_ts = int(datetime.now(pytz.UTC).timestamp())

    while len(all_candles) < target_hours:
        params = {
            "fsym": "USDC",
            "tsym": "ZAR",
            "limit": limit,
            "toTs": to_ts
        }
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data["Response"] != "Success" or not data["Data"]["Data"]:
                print("No more data available or error fetching USDC/ZAR.")
                break

            candles = data["Data"]["Data"]
            if not candles:
                break

            all_candles.extend(candles)
            to_ts = candles[0]["time"] - 1
            print(f"Fetched {len(candles)} candles, earliest timestamp: {datetime.fromtimestamp(candles[0]['time'], tz=pytz.UTC)}")
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching USDC/ZAR: {e}")
            break

    if not all_candles:
        print("No data fetched from CryptoCompare.")
        return None

    df = pd.DataFrame(all_candles, columns=["time", "open", "high", "low", "close", "volumefrom"])
    df["timestamp"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df["volume_zar"] = df["volumefrom"] * df["close"]  # Calculate volume in ZAR
    df = df[["timestamp", "open", "high", "low", "close", "volumefrom", "volume_zar"]]
    df = df.rename(columns={"volumefrom": "volume"})
    df = df.sort_values("timestamp")
    end_time = datetime.now(pytz.UTC)
    start_time = end_time - timedelta(days=days)
    df = df[df["timestamp"] >= start_time]

    # Save to CSV
    DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(RAW_DATA_FILE, index=False)
    print(f"Saved USDC/ZAR data to {RAW_DATA_FILE}: {df.shape}")
    return df

def generate_profile():
    """
    Generate profiling report (HTML) for the fetched data using minimal mode.
    """
    if not RAW_DATA_FILE.exists():
        raise FileNotFoundError(f"{RAW_DATA_FILE} not found. Ensure data fetching succeeded.")

    print("📊 Generating profiling report (minimal mode)...")
    df = pd.read_csv(RAW_DATA_FILE)
    profile = ydata_profiling.ProfileReport(
        df,
        title="USDC/ZAR Data Profiling Report",
        minimal=True  # Use minimal mode to reduce memory usage
    )
    profile.to_file(PROFILE_REPORT_FILE)
    print(f"✅ Profiling report saved: {PROFILE_REPORT_FILE}")

def run_pipeline():
    """
    Orchestrates the pipeline: fetch data → profile data
    """
    df = fetch_usdc_zar_cryptocompare(days=90, timeframe="hour")
    if df is not None:
        generate_profile()
        print("🚀 Pipeline run completed successfully!")
    else:
        print("❌ Pipeline failed: No data fetched.")

if __name__ == "__main__":
    run_pipeline()