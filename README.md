# ZAR Onchain Market Making — Research & Prototype

This repository supports my **Lava VC Task #2** response, researching a **ZAR ↔ USD AMM** with a focus on:

- Liquidity Value Risk (LVR)  
- Avoiding imbalanced trade flow subsidies  
- Addressing a **high yield-bearing, reserve-backed ZAR stablecoin** in South Africa’s high-interest-rate economy (8–10%)  

It contains:

- **Methodology** for ZAR ↔ USD market design, minimizing subsidies via dynamic fees.  
- **LVR & Fees Simulator** (`code/sim`) to estimate LP PnL = fees − LVR − opportunity costs.  
- **Planned Strategy Scaffolding** (`code/mm`, `code/solidity`) for a concentrated-liquidity market maker with range management, oracle-bounded pricing, inventory caps, hedging stubs, and optional dynamic fee hooks (to be implemented).  

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


### 3) Current Functionality

``` code/sim/run_pipeline.py ```

- Fetches 90 days of USDC/ZAR data (2160 hourly candles, May 24, 2025 → August 22, 2025) from CryptoCompare.

- Saves to data/usdc_zar.csv with columns: timestamp, open, high, low, close, volume, volume_zar.

- Generates profiling report (data/usdc_zar_profile.html).

``` code/sim/amm_simulations.py ```
**Simulates:**

- LVR: 13,193.92 ZAR (low due to USDC stability).

- Impermanent Loss: Mean -0.003% (negligible).

- Fees: 9,308,905.91 ZAR (dynamic 0.3–0.5%, needs volume validation).

- Opportunity Cost: 28,333.15 ZAR (8% interest rate).

Results saved to data/usdc_zar_simulations.csv.

### 4) Safety & Secrets

- Never commit real API keys. Use .env (example provided).

- This repository is for demonstration only.

### 5) License
**MIT**