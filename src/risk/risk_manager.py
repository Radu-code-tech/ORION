from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RiskLimits:
    max_risk_per_trade_pct: float = 0.5
    max_daily_loss_pct: float = 2.0
    max_concurrent_positions: int = 3
    min_stop_distance: float = 1e-8
    allow_zero_daily_pnl: bool = True


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str
    risk_amount: float = 0.0
    quantity: float = 0.0


class RiskManager:
    def __init__(self, limits: Optional[RiskLimits] = None) -> None:
        self.limits = limits or RiskLimits()
        self._validate_limits()

    def _validate_limits(self) -> None:
        self._finite_positive(
            "max_risk_per_trade_pct",
            self.limits.max_risk_per_trade_pct,
        )
        self._finite_positive(
            "max_daily_loss_pct",
            self.limits.max_daily_loss_pct,
        )
        if not isinstance(self.limits.max_concurrent_positions, int):
            raise ValueError("max_concurrent_positions must be an integer")
        if isinstance(self.limits.max_concurrent_positions, bool):
            raise ValueError("max_concurrent_positions must be an integer")
        if self.limits.max_concurrent_positions < 0:
            raise ValueError("max_concurrent_positions must be non-negative")
        self._finite_positive(
            "min_stop_distance",
            self.limits.min_stop_distance,
        )
        if not isinstance(self.limits.allow_zero_daily_pnl, bool):
            raise ValueError("allow_zero_daily_pnl must be a boolean")

    def position_size(
        self,
        equity: float,
        risk_pct: float,
        stop_distance: float,
        point_value: float = 1.0,
    ) -> float:
        self._positive("equity", equity)
        self._positive("risk_pct", risk_pct)
        self._positive("stop_distance", stop_distance)
        self._positive("point_value", point_value)

        if risk_pct > self.limits.max_risk_per_trade_pct:
            raise ValueError("risk_pct exceeds configured maximum")

        if stop_distance < self.limits.min_stop_distance:
            raise ValueError("stop_distance is below configured minimum")

        risk_amount = equity * risk_pct / 100.0
        return risk_amount / (stop_distance * point_value)

    def evaluate(
        self,
        equity: float,
        risk_pct: float,
        stop_distance: float,
        point_value: float = 1.0,
        daily_pnl: float = 0.0,
        open_positions: int = 0,
    ) -> RiskDecision:
        try:
            self._positive("equity", equity)
            self._positive("risk_pct", risk_pct)
            self._positive("stop_distance", stop_distance)
            self._positive("point_value", point_value)
            self._finite("daily_pnl", daily_pnl)

            if not isinstance(open_positions, int):
                raise ValueError("open_positions must be an integer")
            if isinstance(open_positions, bool):
                raise ValueError("open_positions must be an integer")

            if risk_pct > self.limits.max_risk_per_trade_pct:
                return RiskDecision(False, "risk_pct_exceeds_limit")

            if stop_distance < self.limits.min_stop_distance:
                return RiskDecision(False, "stop_distance_below_minimum")

            if open_positions < 0:
                return RiskDecision(False, "invalid_open_positions")

            if open_positions >= self.limits.max_concurrent_positions:
                return RiskDecision(False, "max_concurrent_positions_reached")

            if daily_pnl < 0:
                daily_loss_pct = abs(daily_pnl) / equity * 100.0
                if daily_loss_pct >= self.limits.max_daily_loss_pct:
                    return RiskDecision(False, "max_daily_loss_reached")

            risk_amount = equity * risk_pct / 100.0
            quantity = risk_amount / (stop_distance * point_value)

            return RiskDecision(True, "approved", risk_amount, quantity)

        except ValueError as exc:
            return RiskDecision(False, str(exc))

    @staticmethod
    def _finite(name: str, value: float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a finite number")
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")

    @staticmethod
    def _finite_positive(name: str, value: float) -> None:
        RiskManager._finite(name, value)
        if value <= 0:
            raise ValueError(f"{name} must be positive")

    @staticmethod
    def _positive(name: str, value: float) -> None:
        RiskManager._finite_positive(name, value)
