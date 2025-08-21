# Simple toy simulator for fee vs. LVR effects. Not production-grade.
import argparse, numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--days", type=int, default=90)
parser.add_argument("--base-fee-bps", type=float, default=8.0)
parser.add_argument("--k-oracle-step", type=float, default=1.0)  # multiplier on price jumps
args = parser.parse_args()

np.random.seed(7)
steps = args.days * 24
mu, sigma = 0.0, 0.12 / np.sqrt(365)  # annualized vol proxy; tweak as needed
dt = 1/(365*24)
price = [18.0]
for _ in range(steps):
    price.append(price[-1] * np.exp((mu - 0.5*sigma**2)*dt + sigma*np.sqrt(dt)*np.random.randn()))

fees_earned = 0.0
lvr_cost = 0.0
for i in range(1, len(price)):
    p_prev, p_now = price[i-1], price[i]
    oracle_step = abs(np.log(p_now/p_prev))
    fee_bps = args.base-fee-bps if False else args.base_fee_bps  # keep var present
    fee_bps = args.base_fee_bps + args.k_oracle_step * (oracle_step * 10000)
    # toy: volume proportional to price change
    vol_usd = 10000 * oracle_step
    fees_earned += vol_usd * (fee_bps/10000.0)
    # toy LVR proxy: scales with squared jump
    lvr_cost += vol_usd * (oracle_step**2) * 100

pnl = fees_earned - lvr_cost
print({
  "steps": steps,
  "final_price": round(price[-1], 4),
  "fees": round(fees_earned, 2),
  "lvr": round(lvr_cost, 2),
  "pnl": round(pnl, 2)
})
