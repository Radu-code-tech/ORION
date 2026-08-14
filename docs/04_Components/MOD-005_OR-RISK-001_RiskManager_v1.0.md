# MOD-005 — OR-RISK-001 RiskManager v1.0

## Purpose
OR-RISK-001 is the ORION pre-trade risk-control component. It converts account/equity and stop-loss information into a deterministic risk decision and position size.

## Responsibilities
- enforce maximum risk per trade;
- enforce maximum daily loss;
- enforce maximum concurrent positions;
- calculate monetary risk budget;
- calculate position quantity from stop distance and point value.

## Non-responsibilities
The module does not generate trading signals, analyze market structure, place orders, connect to a broker, or maintain live account state.

## Safety principle
A missing or invalid risk input results in rejection rather than an implicit default.

## Position sizing
risk_amount = equity × risk_pct / 100
quantity = risk_amount / (stop_distance × point_value)

The caller is responsible for applying instrument-specific lot/contract constraints after this calculation.

## Acceptance criteria
A trade is allowed only when all configured limits are satisfied.
