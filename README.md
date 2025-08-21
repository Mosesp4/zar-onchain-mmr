# ZAR Onchain Market Making — Research & Prototype

This repo supports my LAVA task #2 response. It contains:
- **Methodology** for ZAR↔USD market design without subsidizing imbalanced flows.
- **LVR & Fees Simulator** (`code/sim`) to estimate LP PnL = fees − LVR − gas − hedging.
- **Strategy Scaffolding** (`code/mm`) for a concentrated-liquidity market maker with:
  - range management,
  - oracle-bounded pricing,
  - inventory caps + hedging stubs,
  - optional dynamic fee policy (if protocol supports hooks).

> ⚠️ This is research scaffolding for discussion only. Do **not** use in production.

## Quickstart

### 1) Python simulator
```bash
cd code/sim
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python backtest.py --days 120 --base-fee-bps 8 --k-oracle-step 1.5
```

### 2) TypeScript strategy scaffold
```bash
cd code/mm
npm i
cp src/config.example.json src/config.json  # Windows PowerShell: copy src\config.example.json src\config.json
npm run build
npm start  # dry-run: logs range updates + hypothetical hedges
```

### 3) Docker (optional, one command to run sim)
```bash
cd infra
docker compose up --build
```

## Structure
```
zar-onchain-mm/
├─ README.md
├─ docs/
│  ├─ approach.md
│  ├─ sources.md
│  └─ open-problems.md
├─ code/
│  ├─ sim/
│  │  ├─ backtest.py
│  │  └─ requirements.txt
│  ├─ mm/
│  │  ├─ package.json
│  │  ├─ tsconfig.json
│  │  └─ src/
│  │     ├─ config.example.json
│  │     ├─ rangeManager.ts
│  │     ├─ feePolicy.ts
│  │     ├─ oracle.ts
│  │     ├─ hedgeBot.ts
│  │     └─ utils.ts
│  └─ solidity/
│     └─ LvrAwareFeeHook.sol
├─ infra/
│  ├─ Dockerfile
│  └─ docker-compose.yml
├─ .env.example
├─ .gitignore
└─ .github/
   └─ workflows/
      └─ ci.yml
```

## Safety & secrets
- Never commit real API keys. Use `.env` (example provided).
- RPC endpoints in `config.json` should be non-sensitive or test RPCs.
- This repository is for demonstration only.

## License
MIT
