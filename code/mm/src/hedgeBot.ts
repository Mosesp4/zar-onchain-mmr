// Hedging stub — where you'd wire CEX RFQ / perps to cap inventory risk.
export async function maybeHedge(inventoryUsd: number, capPercent: number) {
  if (Math.abs(inventoryUsd) > capPercent / 100) {
    // Place hedge order (RFQ / perp) — omitted here.
    return { hedged: true };
  }
  return { hedged: false };
}
