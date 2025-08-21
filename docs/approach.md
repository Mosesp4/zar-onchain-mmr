# Approach (High-Level)

**Goal:** Bootstrap a sustainable ZAR↔USD market on-chain without subsidizing imbalanced flows.

1. **Market Mapping:** Inventory ZAR venues (CEX orderbooks, OTC desks, on-chain pools) and stablecoin options.
2. **Design Choice:** Prefer concentrated-liquidity AMM with **dynamic, oracle-aware fees** and **inventory caps**.
3. **Oracle-Bounded Quotes:** Use reputable FX oracles or a composite oracle from multiple venues; add circuit breakers.
4. **Inventory & Hedging:** Cap exposure per side; hedge imbalances off-chain (or with perps) when thresholds are hit.
5. **Fee Policy:** Increase fees on high oracle steps (price jumps) to mitigate LVR/toxic flow.
6. **Measurement:** Track Fees, LVR proxy, Gas, Hedging PnL → net LP PnL; iterate parameters.
7. **Compliance Ops:** Keep hedging and issuance within regulatory perimeter; segregate entities if required.

This file complements the email submission to LAVA.
