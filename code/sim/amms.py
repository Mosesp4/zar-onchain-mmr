# amms.py
# Core AMM math for simulation: Uniswap V2, Uniswap V3 (single LP), Curve-like stableswap.
# Not production code. Designed for clarity, robustness, and extensibility.

from math import sqrt
import numpy as np
from typing import Tuple, Optional

class AMMError(Exception):
    """Custom exception for AMM-related errors."""
    pass

class UniswapV2Pool:
    """Uniswap V2 constant product AMM pool (x * y = k)."""
    def __init__(self, reserve0: float, reserve1: float, fee_bps: float = 30, token0: str = "Token0", token1: str = "Token1"):
        """
        Initialize a Uniswap V2 pool.

        Args:
            reserve0 (float): Reserve of token0 (base asset, e.g., ZAR).
            reserve1 (float): Reserve of token1 (quote asset, e.g., USDC).
            fee_bps (float): Fee in basis points (e.g., 30 = 0.3%).
            token0 (str): Name of base token (default: "Token0").
            token1 (str): Name of quote token (default: "Token1").

        Raises:
            AMMError: If reserves or fee are invalid.
        """
        if reserve0 <= 0 or reserve1 <= 0:
            raise AMMError("Reserves must be positive")
        if fee_bps < 0:
            raise AMMError("Fee cannot be negative")
        self.reserve0 = float(reserve0)
        self.reserve1 = float(reserve1)
        self.k = self.reserve0 * self.reserve1
        self.fee = fee_bps / 10000.0
        self.pair = (token0, token1)
        self.cumulative_fees = 0.0  # Track fees in token0 terms

    def price(self) -> float:
        """Return price as token0 per token1 (reserve0 / reserve1)."""
        if self.reserve1 == 0:
            raise AMMError("Cannot compute price: reserve1 is zero")
        return self.reserve0 / self.reserve1

    def swap_to_price(self, target_price: float) -> Tuple[float, float, float]:
        """
        Simulate a swap to move pool price to target_price.

        Args:
            target_price (float): Desired price (token0 per token1).

        Returns:
            Tuple[float, float, float]: (d0, d1, fee_collected)
                - d0: Amount of token0 added (positive) or removed (negative).
                - d1: Amount of token1 removed (positive) or added (negative).
                - fee_collected: Fees collected in token0 terms.

        Raises:
            AMMError: If target_price is invalid.
        """
        if target_price <= 0:
            raise AMMError("Target price must be positive")
        current_price = self.price()
        if abs(current_price - target_price) < 1e-12:
            return 0.0, 0.0, 0.0

        x_new = sqrt(self.k * target_price)
        dx_effective = x_new - self.reserve0
        if abs(dx_effective) < 1e-12:
            return 0.0, 0.0, 0.0
        gross_dx = dx_effective / (1 - self.fee)
        y_new = self.k / x_new
        dy = self.reserve1 - y_new
        fee_collected = abs(gross_dx) * self.fee

        self.reserve0 += gross_dx
        self.reserve1 -= dy
        self.k = self.reserve0 * self.reserve1
        self.cumulative_fees += fee_collected
        return gross_dx, dy, fee_collected

    def lp_value(self, lp_share_ratio: float) -> Tuple[float, float]:
        """
        Calculate LP's share value in tokens.

        Args:
            lp_share_ratio (float): Fraction of pool owned (0 to 1).

        Returns:
            Tuple[float, float]: (amount_token0, amount_token1).

        Raises:
            AMMError: If lp_share_ratio is invalid.
        """
        if not 0 <= lp_share_ratio <= 1:
            raise AMMError("lp_share_ratio must be between 0 and 1")
        return self.reserve0 * lp_share_ratio, self.reserve1 * lp_share_ratio

    def add_liquidity(self, amount0: float, amount1: float) -> None:
        """
        Add liquidity to the pool, updating reserves.

        Args:
            amount0 (float): Amount of token0 to add.
            amount1 (float): Amount of token1 to add.

        Raises:
            AMMError: If amounts are invalid or violate constant product.
        """
        if amount0 <= 0 or amount1 <= 0:
            raise AMMError("Liquidity amounts must be positive")
        expected_ratio = self.reserve0 / self.reserve1 if self.reserve1 > 0 else amount0 / amount1
        if abs((amount0 / amount1) - expected_ratio) > 1e-6:
            raise AMMError("Liquidity amounts must match pool ratio")
        self.reserve0 += amount0
        self.reserve1 += amount1
        self.k = self.reserve0 * self.reserve1

class UniswapV3SingleLP:
    """Simplified Uniswap V3-style concentrated liquidity for a single LP."""
    def __init__(self, lower_price: float, upper_price: float, provided_token0: float, provided_token1: float, fee_bps: float = 30, token0: str = "Token0", token1: str = "Token1"):
        """
        Initialize a Uniswap V3 LP position.

        Args:
            lower_price (float): Lower price bound (token0 per token1).
            upper_price (float): Upper price bound (token0 per token1).
            provided_token0 (float): Amount of token0 provided.
            provided_token1 (float): Amount of token1 provided.
            fee_bps (float): Fee in basis points (e.g., 30 = 0.3%).
            token0 (str): Name of base token.
            token1 (str): Name of quote token.

        Raises:
            AMMError: If price bounds or amounts are invalid.
        """
        if lower_price <= 0 or upper_price <= lower_price:
            raise AMMError("Invalid price range: lower_price must be positive and less than upper_price")
        if provided_token0 < 0 or provided_token1 < 0:
            raise AMMError("Provided amounts cannot be negative")
        self.lower = float(lower_price)
        self.upper = float(upper_price)
        self.fee = fee_bps / 10000.0
        self.pair = (token0, token1)
        self.price = (self.lower + self.upper) / 2.0
        self.token0 = float(provided_token0)
        self.token1 = float(provided_token1)
        self.L = self._estimate_liquidity_from_assets(self.price)
        self.cumulative_fees = 0.0  # Track fees in token0 terms
        self._sqrt_lower = self._sqrtp(self.lower)  # Cache sqrt values
        self._sqrt_upper = self._sqrtp(self.upper)

    def _sqrtp(self, p: float) -> float:
        """Calculate square root of price."""
        if p < 0:
            raise AMMError("Price cannot be negative")
        return sqrt(p)

    def _estimate_liquidity_from_assets(self, p: float) -> float:
        """
        Estimate liquidity (L) from provided assets at price p.

        Args:
            p (float): Current price (token0 per token1).

        Returns:
            float: Liquidity parameter L.
        """
        sqrtP = self._sqrtp(p)
        denom = sqrtP * (1 / self._sqrt_lower - 1 / self._sqrt_upper) if self._sqrt_lower > 0 else 1.0
        denom = max(denom, 1e-12)  # Avoid division by zero
        L_from_token1 = self.token1 / denom
        L_from_token0 = (self.token0 / p) / denom
        return max(min(L_from_token1, L_from_token0), 0.0)

    def in_range(self, p: float) -> bool:
        """Check if price is within LP range."""
        return self.lower <= p <= self.upper

    def value(self, current_price: float) -> Tuple[float, float]:
        """
        Calculate LP's position value at current_price.

        Args:
            current_price (float): Current pool price (token0 per token1).

        Returns:
            Tuple[float, float]: (amount_token0, amount_token1).

        Raises:
            AMMError: If current_price is invalid.
        """
        if current_price <= 0:
            raise AMMError("Current price must be positive")
        sqrtP = self._sqrtp(current_price)
        if self.in_range(current_price):
            try:
                amount_token1 = self.L * (sqrtP - self._sqrt_lower) / (sqrtP * self._sqrt_lower)
                amount_token0 = self.L * (self._sqrt_upper - sqrtP)
            except ZeroDivisionError:
                amount_token0, amount_token1 = 0.0, 0.0
        elif current_price < self.lower:
            amount_token0 = self.token0 + self.token1 * current_price
            amount_token1 = 0.0
        else:
            amount_token0 = 0.0
            amount_token1 = self.token1 + self.token0 / current_price
        return amount_token0, amount_token1

    def apply_swap(self, target_price: float, trade_volume_token1: Optional[float] = None) -> float:
        """
        Simulate a swap and update price, returning fees.

        Args:
            target_price (float): Desired price (token0 per token1).
            trade_volume_token1 (float, optional): Trade volume in token1. If None, estimate from position change.

        Returns:
            float: Fees collected in token0 terms.

        Raises:
            AMMError: If target_price is invalid.
        """
        if target_price <= 0:
            raise AMMError("Target price must be positive")
        prev_token0, prev_token1 = self.value(self.price)
        self.price = target_price
        new_token0, new_token1 = self.value(target_price)
        vol_token1 = trade_volume_token1 or abs(new_token1 - prev_token1)
        fee = vol_token1 * self.fee * target_price
        self.cumulative_fees += fee
        return fee

class Curve2Pool:
    """Curve-like stableswap pool for two assets."""
    def __init__(self, reserve0: float, reserve1: float, A: float = 200, fee_bps: float = 4, token0: str = "Token0", token1: str = "Token1"):
        """
        Initialize a Curve-like stableswap pool.

        Args:
            reserve0 (float): Reserve of token0 (e.g., ZAR).
            reserve1 (float): Reserve of token1 (e.g., USDC).
            A (float): Amplification parameter (higher = closer to constant sum).
            fee_bps (float): Fee in basis points (e.g., 4 = 0.04%).
            token0 (str): Name of base token.
            token1 (str): Name of quote token.

        Raises:
            AMMError: If reserves, A, or fee are invalid.
        """
        if reserve0 <= 0 or reserve1 <= 0:
            raise AMMError("Reserves must be positive")
        if A <= 0:
            raise AMMError("Amplification parameter A must be positive")
        if fee_bps < 0:
            raise AMMError("Fee cannot be negative")
        self.reserve0 = float(reserve0)
        self.reserve1 = float(reserve1)
        self.A = float(A)
        self.fee = fee_bps / 10000.0
        self.pair = (token0, token1)
        self.cumulative_fees = 0.0

    def D(self, x: float = None, y: float = None) -> float:
        """
        Calculate Curve invariant D using Newton-Raphson solver.

        Args:
            x (float, optional): Reserve of token0. Defaults to current reserve0.
            y (float, optional): Reserve of token1. Defaults to current reserve1.

        Returns:
            float: Invariant D.
        """
        x = x if x is not None else self.reserve0
        y = y if y is not None else self.reserve1
        if x <= 0 or y <= 0:
            return 0.0
        # Initial guess: D ≈ x + y
        D = x + y
        Ann = self.A * 4  # For 2 tokens
        for _ in range(32):  # Newton-Raphson iterations
            D_prev = D
            D2 = D * D
            D3 = D2 * D
            S = x + y
            P = x * y
            D = (D3 * S + Ann * P * D) / (D2 * (S + Ann - 1) + 4 * Ann * P)
            if abs(D - D_prev) < 1e-10:
                break
        return D

    def price(self) -> float:
        """Approximate price as token0 per token1."""
        if self.reserve1 == 0:
            raise AMMError("Cannot compute price: reserve1 is zero")
        return self.reserve0 / self.reserve1

    def swap_to_price(self, target_price: float) -> Tuple[float, float, float]:
        """
        Simulate a swap to move pool price to target_price.

        Args:
            target_price (float): Desired price (token0 per token1).

        Returns:
            Tuple[float, float, float]: (d0, d1, fee_collected).

        Raises:
            AMMError: If target_price is invalid.
        """
        if target_price <= 0:
            raise AMMError("Target price must be positive")
        D = self.D()
        x_new = (D / 2) * (1 / target_price + 1)
        y_new = D - x_new
        dx_effective = x_new - self.reserve0
        if abs(dx_effective) < 1e-12:
            return 0.0, 0.0, 0.0
        gross_dx = dx_effective / (1 - self.fee)
        dy = self.reserve1 - y_new
        fee_collected = abs(gross_dx) * self.fee
        self.reserve0 += gross_dx
        self.reserve1 -= dy
        self.cumulative_fees += fee_collected
        return gross_dx, dy, fee_collected

    def lp_value(self, lp_share_ratio: float) -> Tuple[float, float]:
        """
        Calculate LP's share value in tokens.

        Args:
            lp_share_ratio (float): Fraction of pool owned (0 to 1).

        Returns:
            Tuple[float, float]: (amount_token0, amount_token1).
        """
        if not 0 <= lp_share_ratio <= 1:
            raise AMMError("lp_share_ratio must be between 0 and 1")
        return self.reserve0 * lp_share_ratio, self.reserve1 * lp_share_ratio