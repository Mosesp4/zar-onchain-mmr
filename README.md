# ZAR Onchain Market Making - Research & Prototype

This repository supports my **Lava VC Task (Question 2)** response, researching a **ZAR ↔ USD AMM** with a focus on:

- Liquidity Value Risk (LVR)  
- Avoiding imbalanced trade flow subsidies  
- Addressing a **high yield-bearing, reserve-backed ZAR stablecoin** in South Africa’s high-interest-rate economy (8–10%)  

It contains:

- **Methodology** for ZAR ↔ USD market design, minimizing subsidies via dynamic fees.  
- **LVR & Fees Simulator** (`code/sim`) to estimate LP PnL = fees − LVR − opportunity costs.    

⚠️ **This is research scaffolding for discussion only. Do not use in production.**

---

## 🚀 Quickstart

### 1) Python Simulator
Run data fetching and AMM simulations:

```bash
cd code/sim
python -m venv .venv && .venv\Scripts\activate  # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

# Fetch USDC/ZAR data and generate profiling report
python run_pipeline.py  

# Run simulations: LVR, impermanent loss, fees, opportunity costs
python amm_simulations.py  

```

### 2) Structure
```bash
zar-onchain-mm-research/
├─ README.md
├─ docs/
│  ├─ approach.md
│  ├─ sources.md
│  └─ open-problems.md
├─ code/
│  ├─ sim/
│  │  ├─ run_pipeline.py
│  │  ├─ amm_simulations.py
      ├─ backtest.py
      ├─ calculate_lvr.py
      ├─ fetch_usdc_zar.py
      ├─ profile_report.py
      ├─ amms.py
│  │  └─ requirements.txt
│  ├─ data/
│  │  ├─ usdc_zar.csv
│  │  ├─ usdc_zar_profile.html
│  │  ├─ usdc_zar_simulations.csv
├─ .gitignore
└─ .github/
   └─ workflows/
      └─ ci.yml
```

### 3) Current Functionality

``` code/sim/run_pipeline.py ```

- Fetches 90 days of USDC/ZAR data (2160 hourly candles, May 24, 2025 → August 22, 2025) from CryptoCompare.
- Saves to data/usdc_zar.csv with columns: timestamp, open, high, low, close, volume, volume_zar.
- Generates profiling report (data/usdc_zar_profile.html).
  
``` code/sim/amm_simulations.py ```<br />
 **Simulates:**

- LVR: 13,193.92 ZAR (low due to USDC stability).
- Impermanent Loss: Mean -0.003% (negligible).
- Fees: 9,308,905.91 ZAR (dynamic 0.3–0.5%, needs volume validation).
- Opportunity Cost: 28,333.15 ZAR (8% interest rate).
  
Results saved to data/usdc_zar_simulations.csv.

``` code/sim/fetch_usdc_zar.py ```
  - Fetches ZAR/USD and USDC/ZAR market data from APIs (e.g., Binance, FX providers).  
  - Normalizes the data into a structured format (CSV/Parquet).  
  - Can be scheduled to run periodically for live updates.

``` code/sim/profile_report.py ``` 
  - Generates automated exploratory data profiling reports using `ydata-profiling`.  
  - Provides statistics, distributions, correlations, and anomaly checks on fetched datasets.  
  - Useful for quickly understanding market data quality and potential biases.  


``` code/sim/backtest.py ```
- Runs simple backtests on ZAR <> USDC swap strategies.  
- Helps simulate how different AMM pricing models would perform historically.  
- Outputs performance metrics such as PnL, slippage, and arbitrage opportunities.  

``` code/sim/calculate_lvr.py ```
  - Implements calculations of Loss Versus Rebalancing (LVR).  
  - Compares AMM strategy performance against an ideal arbitrage-free benchmark.  
  - Useful for understanding the costs of market making in volatile or imbalanced ZAR flows.

### 4) Open Source Code to Learn From / Fork
 - Hummingbot: https://github.com/hummingbot/hummingbot (8k+ ⭐, hedging bots).
 - Uniswap V3 Core: https://github.com/Uniswap/v3-core (5k+ ⭐, concentrated liquidity).
 - Balancer V2: https://github.com/balancer-labs/balancer-v2-monorepo (1k+ ⭐, weighted/yield pools).
 - Curve Finance: https://github.com/curvefi/curve-contract (1.5k+ ⭐, stablecoin AMMs).
 - Awesome-AMM: https://github.com/0xperp/awesome-amm (curated list).

### 5) Safety & Secrets

- Never commit real API keys. Use .env (example provided).

- This repository is for demonstration only.

### 6) License
MIT License
