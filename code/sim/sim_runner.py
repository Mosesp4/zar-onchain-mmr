# sim_runner.py
# Usage: python sim_runner.py --csv usdc_zar_cryptocompare_90d.csv --initial-zar 1000000 --initial-usdc 60000
import argparse
import pandas as pd
from amms import UniswapV2Pool, UniswapV3SingleLP, Curve2Pool

def load_price_series(csv_path):
    df = pd.read_csv(csv_path, parse_dates=['timestamp'])
    # Expect column 'close' with price = ZAR per USDC
    if 'close' in df.columns:
        df = df[['timestamp', 'close']].rename(columns={'close': 'price'})
    elif 'price' in df.columns:
        df = df[['timestamp', 'price']]
    else:
        raise ValueError("CSV must contain 'close' or 'price' column")
    df = df.sort_values('timestamp').reset_index(drop=True)
    return df

def simulate_v2(df, initial_zar, initial_usdc, fee_bps=30):
    # seed pool so price = initial_price and reserves = initial_zar, initial_usdc
    init_price = df.loc[0,'price']
    pool = UniswapV2Pool(initial_zar, initial_usdc, fee_bps=fee_bps)
    # We'll track LP owning 100% of pool for simplicity (compare to HODL baseline)
    records = []
    for idx, row in df.iterrows():
        target_price = float(row['price'])
        # arbitrage to target price
        dx, dy, fee = pool.swap_to_price(target_price)
        # LP value
        lp_zar, lp_usdc = pool.lp_value(1.0)
        # convert LP to ZAR value (approx)
        lp_value_zar = lp_zar + lp_usdc * target_price
        records.append({
            'timestamp': row['timestamp'],
            'price': target_price,
            'pool_price': pool.price(),
            'fee_zar': fee,
            'lp_zar': lp_zar,
            'lp_usdc': lp_usdc,
            'lp_value_zar': lp_value_zar
        })
    return pd.DataFrame(records)

def simulate_v3(df, lower, upper, provided_zar, provided_usdc, fee_bps=30):
    lp = UniswapV3SingleLP(lower, upper, provided_zar, provided_usdc, fee_bps=fee_bps)
    records = []
    for idx, row in df.iterrows():
        target_price = float(row['price'])
        fee = lp.apply_swap(target_price, pool_fee_bps=fee_bps)
        zar_amt, usdc_amt = lp.value(target_price)
        lp_value = zar_amt + usdc_amt * target_price
        records.append({
            'timestamp': row['timestamp'],
            'price': target_price,
            'fee_zar': fee,
            'lp_zar': zar_amt,
            'lp_usdc': usdc_amt,
            'lp_value_zar': lp_value
        })
    return pd.DataFrame(records)

def simulate_curve(df, initial_zar, initial_usdc, A=200, fee_bps=4):
    pool = Curve2Pool(initial_zar, initial_usdc, A=A, fee_bps=fee_bps)
    records = []
    for idx, row in df.iterrows():
        target_price = float(row['price'])
        dx, dy, fee = pool.swap_to_price(target_price)
        value_zar = pool.x + pool.y * target_price
        records.append({
            'timestamp': row['timestamp'],
            'price': target_price,
            'pool_price': pool.price(),
            'fee_zar': fee,
            'pool_zar': pool.x,
            'pool_usdc': pool.y,
            'pool_value_zar': value_zar
        })
    return pd.DataFrame(records)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', required=True)
    parser.add_argument('--initial-zar', type=float, default=1_000_000)
    parser.add_argument('--initial-usdc', type=float, default=60_000)
    args = parser.parse_args()

    df = load_price_series(args.csv)
    print("Loaded", df.shape, "rows")

    print("Running Uniswap v2 sim...")
    df_v2 = simulate_v2(df, args.initial_zar, args.initial_usdc, fee_bps=30)
    df_v2.to_csv('sim_v2_results.csv', index=False)

    print("Running Uniswap v3 sim (example band around initial price ±10%)...")
    p0 = df.loc[0,'price']
    lower = p0 * 0.9
    upper = p0 * 1.1
    df_v3 = simulate_v3(df, lower, upper, provided_zar=args.initial_zar, provided_usdc=args.initial_usdc/p0, fee_bps=30)
    df_v3.to_csv('sim_v3_results.csv', index=False)

    print("Running Curve-like sim...")
    df_curve = simulate_curve(df, args.initial_zar, args.initial_usdc, A=200, fee_bps=4)
    df_curve.to_csv('sim_curve_results.csv', index=False)

    print("Done. Results saved: sim_v2_results.csv, sim_v3_results.csv, sim_curve_results.csv")

if __name__ == '__main__':
    main()
