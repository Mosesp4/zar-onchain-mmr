import pandas as pd
import numpy as np

def calculate_lvr(df, k=1000000):
    """Calculate Liquidity Value Risk (LVR) for USDC/ZAR AMM pool."""
    df['price_change'] = df['close'].diff()
    df['lvr'] = np.abs(df['price_change']) * np.sqrt(k / df['close'])
    print("Total LVR (ZAR):", df['lvr'].sum())
    print(df[['timestamp', 'close', 'price_change', 'lvr']].head())
    return df

def calculate_impermanent_loss(df):
    """Calculate impermanent loss for USDC/ZAR AMM pool."""
    initial_price = df['close'].iloc[0]
    df['impermanent_loss'] = 2 * np.sqrt(df['close'] / initial_price) / (1 + df['close'] / initial_price) - 1
    print("Impermanent Loss Summary:")
    print(df['impermanent_loss'].describe())
    print(df[['timestamp', 'close', 'impermanent_loss']].head())
    return df

def calculate_fees(df):
    """Calculate dynamic fees based on volatility."""
    df['volatility'] = df['close'].pct_change().rolling(window=24).std()
    df['dynamic_fee'] = np.where(df['volatility'] > df['volatility'].mean(), 0.005, 0.003)  # 0.5% or 0.3%
    df['fee_income_zar'] = df['volume_zar'] * df['dynamic_fee']
    print("Total Fee Income (ZAR):", df['fee_income_zar'].sum())
    print(df[['timestamp', 'volume_zar', 'volatility', 'dynamic_fee', 'fee_income_zar']].head())
    return df

def calculate_opportunity_cost(df, interest_rate=0.08):
    """Calculate opportunity cost in high interest rate environment."""
    df['opportunity_cost_zar'] = df['volume_zar'] * (interest_rate / 365 / 24)
    print("Total Opportunity Cost (ZAR):", df['opportunity_cost_zar'].sum())
    print(df[['timestamp', 'volume_zar', 'opportunity_cost_zar']].head())
    return df

if __name__ == "__main__":
    df = pd.read_csv('../data/usdc_zar.csv')
    df = calculate_lvr(df)
    df = calculate_impermanent_loss(df)
    df = calculate_fees(df)
    df = calculate_opportunity_cost(df)
    df.to_csv('../data/usdc_zar_simulations.csv', index=False)
    print("Saved simulation results to ../data/usdc_zar_simulations.csv")