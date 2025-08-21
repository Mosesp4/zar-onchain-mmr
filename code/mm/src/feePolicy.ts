// Simple LVR-aware fee policy: base + k * step_in_bps
export function getFeeBpsFromOracleStep(baseBps: number, k: number, step: number) {
  return baseBps + k * (step * 10000);
}
