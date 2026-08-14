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
