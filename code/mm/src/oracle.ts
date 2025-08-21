// Oracle adapter stubs — replace with real Chainlink/Pyth/CEX composites.
type Cfg = { rpcUrl: string; poolAddress: string };

export async function getOracleStep(_cfg: Cfg): Promise<number> {
  // Return abs(log p_t / p_{t-1})) — here, random placeholder for demo.
  return Math.abs(Math.log(1 + (Math.random() - 0.5) * 0.01));
}

export async function getCurrentTick(_cfg: Cfg): Promise<number> {
  // Placeholder for on-chain read using viem/ethers.
  return Math.floor((Math.random() - 0.5) * 2000);
}
