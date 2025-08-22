# amms.py
# Core AMM math for sim: Uniswap v2, Uniswap v3 (banded single LP), Curve-like stableswap.
# Not production code. Clear, commented, easy to extend.

from math import sqrt

# ------- Uniswap v2 (constant product) -------
class UniswapV2Pool:
    def __init__(self, reserve_x: float, reserve_y: float, fee_bps: float = 30):
        """
        reserve_x: base asset (e.g., ZAR)
        reserve_y: quote asset (e.g., USDC expressed in USD? depends on your CSV; we'll assume close = ZAR per USDC)
        fee_bps: fee in basis points (e.g., 30 = 0.30%)
        """
        self.x = float(reserve_x)
        self.y = float(reserve_y)
        self.k = self.x * self.y
        self.fee = fee_bps / 10000.0

    def price(self):
        # price quoted as ZAR per USDC = x / y
        return self.x / self.y

    def swap_to_price(self, target_price):
        """
        Simulate arbitrage that moves pool price to target_price by swapping.
        Return (dx, dy, fee_collected) where dx is ZAR into pool (positive if ZAR added),
        dy is USDC out (positive if USDC removed). fee_collected measured in ZAR-equivalent (we will convert).
        """
        p = self.price()
        if abs(p - target_price) < 1e-12:
            return 0.0, 0.0, 0.0

        # Want x_new / y_new = target_price and x_new * y_new = k'
        # After swap (ZAR in -> USDC out), reserves change.
        # Solve for new reserves under constant product: x' = x + dx*(1 - fee), y' = k / x'
        # We need price = x'/y' = target_price -> x' / (k / x') = x'^2 / k = target_price -> x' = sqrt(k * target_price)
        x_new = sqrt(self.k * target_price)
        # dx_effective = x_new - x
        dx_effective = x_new - self.x
        if dx_effective == 0:
            return 0.0, 0.0, 0.0
        # But dx_effective = dx * (1 - fee) so gross dx = dx_effective / (1 - fee)
        gross_dx = dx_effective / (1 - self.fee)
        # compute y_new and dy out
        y_new = self.k / x_new
        dy = self.y - y_new
        # fee collected in ZAR terms = gross_dx * fee
        fee_collected = gross_dx * self.fee
        # apply changes
        self.x += gross_dx
        self.y -= dy
        self.k = self.x * self.y
        return gross_dx, dy, fee_collected

    def lp_value(self, lp_share_ratio):
        """
        Given an LP owning fraction lp_share_ratio of the pool,
        return value in (ZAR, USDC) of that share based on current reserves.
        """
        return self.x * lp_share_ratio, self.y * lp_share_ratio

# ------- Uniswap v3-style concentrated liquidity (single LP in band) -------
class UniswapV3SingleLP:
    def __init__(self, lower_price, upper_price, provided_zar, provided_usdc, fee_bps=30):
        """
        A simplified model: LP provides liquidity across [lower_price, upper_price].
        We'll represent liquidity L in Uniswap v3 math approx form by converting price to sqrtP and using
        the relations used in v3. This is a simplified, illustrative model.
        """
        self.lower = float(lower_price)
        self.upper = float(upper_price)
        self.fee = fee_bps / 10000.0
        # initialize a pool-level "virtual" pool for swaps; but LP accounting will be based on price ranges
        # We'll set initial pool price at midpoint of band if possible.
        self.price = (self.lower + self.upper) / 2.0
        # Liquidity provided is derived from provided assets at current price.
        # For simplicity, compute liquidity as min of what either asset supports at midpoint
        mid = self.price
        # compute how much LP provides in LP terms: treat like concentrated liquidity formula
        # rough approach: assume symmetric provision at mid-price: compute USD-equivalent
        self.zar = float(provided_zar)
        self.usdc = float(provided_usdc)
        self.L = self._estimate_liquidity_from_assets(mid)

    def _sqrtp(self, p):
        return p**0.5

    def _estimate_liquidity_from_assets(self, p):
        # Rough mapping: L = amount_usdc / (sqrtP * (1 - sqrt_lower/sqrt_upper))  (not exact)
        sqrtP = self._sqrtp(p)
        sqrtL = self._sqrtp(self.lower)
        sqrtU = self._sqrtp(self.upper)
        # Use whichever asset is limiting
        # Usdc-limited L estimate
        denom = sqrtP * (1 / sqrtL - 1 / sqrtU) if (sqrtL>0 and sqrtU>0) else 1.0
        if denom == 0:
            denom = 1.0
        L_from_usdc = self.usdc / denom if denom!=0 else 0.0
        # Zar-limited L estimate (convert zar to usdc units by price)
        zar_in_usdc = self.zar / p
        L_from_zar = zar_in_usdc / denom if denom!=0 else 0.0
        L = min(L_from_usdc, L_from_zar)
        return max(L, 0.0)

    def in_range(self, p):
        return (p >= self.lower) and (p <= self.upper)

    def value(self, current_price):
        """
        Return the LP's amounts (zar, usdc) at current_price.
        If out of range, liquidity fully in one asset.
        We provide a simplified conversion using v3 formulas approximated.
        """
        p = current_price
        sqrtP = p**0.5
        sqrtLower = self.lower**0.5
        sqrtUpper = self.upper**0.5
        if self.in_range(p):
            # approximate amounts
            # amount_usdc = L * (sqrtP - sqrtLower) / (sqrtP * sqrtLower)
            # amount_zar = L * (sqrtUpper - sqrtP)
            try:
                amount_usdc = self.L * (sqrtP - sqrtLower) / (sqrtP * sqrtLower)
                amount_zar = self.L * (sqrtUpper - sqrtP)
            except Exception:
                amount_usdc = 0.0
                amount_zar = 0.0
        elif p < self.lower:
            # entirely in ZAR
            amount_usdc = 0.0
            amount_zar = self.zar + self.usdc * p  # rough
        else:
            # p > upper -> entirely in USDC
            amount_usdc = self.usdc + self.zar / p
            amount_zar = 0.0
        return amount_zar, amount_usdc

    def apply_swap(self, target_price, pool_fee_bps=30):
        """
        For our simplified sim, we won't model the entire pool shape, only LP holdings change as price moves.
        We return fee collected approximated by volume * fee.
        """
        # Calculate current holdings at previous self.price
        prev_zar, prev_usdc = self.value(self.price)
        # New holdings at target price
        new_zar, new_usdc = self.value(target_price)
        # Fee estimation: assume arb trade volume = abs(change in USDC holding)
        vol_usdc = abs(new_usdc - prev_usdc)
        fee = vol_usdc * (pool_fee_bps / 10000.0) * target_price  # convert to ZAR based on price
        # update internal price to target (LP passive)
        self.price = target_price
        return fee

# ------- Curve-like stableswap (2-asset) simplified -------
class Curve2Pool:
    def __init__(self, reserve_x, reserve_y, A=200, fee_bps=4):
        """
        reserve_x: ZAR
        reserve_y: USDC (units)
        A: amplification parameter (higher => behaves more like constant sum)
        fee_bps: fee basis points (default 0.04% typical for stable pools, adjust)
        """
        self.x = float(reserve_x)
        self.y = float(reserve_y)
        self.A = float(A)
        self.fee = fee_bps / 10000.0

    def D(self, x, y):
        # Simplified stable-swap D for 2-assets (iterative solution omitted for brevity)
        # Use approximate D = x + y (if A large). For moderate A, this is a simplification.
        return x + y

    def price(self):
        # approximate price ZAR per USDC
        return self.x / self.y

    def swap_to_price(self, target_price):
        """
        Similar to v2: we find change required to move pool price to target_price with swap.
        We'll do a simple x' = sqrt(k * target_price) approach for conservative estimate.
        """
        k = self.x * self.y
        x_new = sqrt(k * target_price)
        dx_effective = x_new - self.x
        if dx_effective == 0:
            return 0.0, 0.0, 0.0
        gross_dx = dx_effective / (1 - self.fee)
        y_new = k / x_new
        dy = self.y - y_new
        fee_collected = gross_dx * self.fee
        self.x += gross_dx
        self.y -= dy
        return gross_dx, dy, fee_collected
