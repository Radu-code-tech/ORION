import pytest
from risk.risk_manager import RiskLimits, RiskManager

def test_position_size_uses_equity_risk_and_stop_distance():
    assert RiskManager().position_size(10000, 0.5, 10, 1) == pytest.approx(5.0)

def test_trade_is_approved_within_limits():
    d = RiskManager().evaluate(10000, 0.5, 10)
    assert d.allowed and d.reason == "approved"
    assert d.risk_amount == pytest.approx(50.0)

def test_risk_above_limit_is_rejected():
    d = RiskManager().evaluate(10000, 0.6, 10)
    assert not d.allowed and d.reason == "risk_pct_exceeds_limit"

def test_daily_loss_limit_is_rejected():
    d = RiskManager().evaluate(10000, 0.5, 10, daily_pnl=-200)
    assert not d.allowed and d.reason == "max_daily_loss_reached"

def test_concurrent_position_limit_is_rejected():
    d = RiskManager().evaluate(10000, 0.5, 10, open_positions=3)
    assert not d.allowed and d.reason == "max_concurrent_positions_reached"

def test_invalid_stop_distance_is_rejected():
    assert not RiskManager().evaluate(10000, 0.5, 0).allowed

def test_invalid_equity_is_rejected():
    assert not RiskManager().evaluate(0, 0.5, 10).allowed

def test_custom_limits_are_respected():
    m = RiskManager(RiskLimits(max_risk_per_trade_pct=1.0,
                               max_daily_loss_pct=3.0,
                               max_concurrent_positions=1))
    assert m.evaluate(10000, 1.0, 10, daily_pnl=-250).allowed

def test_limits_reject_invalid_configuration():
    with pytest.raises(ValueError):
        RiskManager(RiskLimits(max_risk_per_trade_pct=0))


def test_nan_equity_is_rejected():
    d = RiskManager().evaluate(float("nan"), 0.5, 10)
    assert not d.allowed

def test_infinite_equity_is_rejected():
    d = RiskManager().evaluate(float("inf"), 0.5, 10)
    assert not d.allowed

def test_nan_risk_pct_is_rejected():
    d = RiskManager().evaluate(10000, float("nan"), 10)
    assert not d.allowed

def test_infinite_risk_pct_is_rejected():
    d = RiskManager().evaluate(10000, float("inf"), 10)
    assert not d.allowed

def test_nan_stop_distance_is_rejected():
    d = RiskManager().evaluate(10000, 0.5, float("nan"))
    assert not d.allowed

def test_infinite_stop_distance_is_rejected():
    d = RiskManager().evaluate(10000, 0.5, float("inf"))
    assert not d.allowed

def test_nan_point_value_is_rejected():
    d = RiskManager().evaluate(10000, 0.5, 10, float("nan"))
    assert not d.allowed

def test_infinite_point_value_is_rejected():
    d = RiskManager().evaluate(10000, 0.5, 10, float("inf"))
    assert not d.allowed

def test_nan_daily_pnl_is_rejected():
    d = RiskManager().evaluate(10000, 0.5, 10, daily_pnl=float("nan"))
    assert not d.allowed

def test_infinite_daily_pnl_is_rejected():
    d = RiskManager().evaluate(10000, 0.5, 10, daily_pnl=float("inf"))
    assert not d.allowed

def test_negative_open_positions_are_rejected():
    d = RiskManager().evaluate(10000, 0.5, 10, open_positions=-1)
    assert not d.allowed

def test_daily_loss_exact_boundary_is_rejected():
    d = RiskManager().evaluate(10000, 0.5, 10, daily_pnl=-200)
    assert not d.allowed
    assert d.reason == "max_daily_loss_reached"

def test_position_size_rejects_nan_equity():
    with pytest.raises(ValueError):
        RiskManager().position_size(float("nan"), 0.5, 10)

def test_position_size_rejects_infinite_equity():
    with pytest.raises(ValueError):
        RiskManager().position_size(float("inf"), 0.5, 10)

def test_position_size_rejects_nan_stop_distance():
    with pytest.raises(ValueError):
        RiskManager().position_size(10000, 0.5, float("nan"))

def test_position_size_rejects_infinite_stop_distance():
    with pytest.raises(ValueError):
        RiskManager().position_size(10000, 0.5, float("inf"))
