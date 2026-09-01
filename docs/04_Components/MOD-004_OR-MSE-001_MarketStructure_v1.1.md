# MOD-004 — OR-MSE-001 Market Structure v1.1

## 1. Module Identity

- Module ID: MOD-004
- Component ID: OR-MSE-001
- Component Name: Market Structure Engine
- Version: v1.1
- Status: Hardened
- Layer: ORION Analysis
- Previous Version: v1.0
- Compatibility Target: MOD-005+
- Hardening Scope: validation, deterministic classification, failure safety

---

## 2. Purpose

OR-MSE-001 provides a deterministic first-pass Market Structure Engine
for ORION.

The component analyzes an ordered sequence of market bars and classifies
the observed structure as:

- BULLISH
- BEARISH
- RANGE
- INSUFFICIENT_DATA

The engine is intentionally limited to structural classification.

It does not generate trading signals, calculate risk, execute orders,
predict future prices, or perform machine learning.

---

## 3. Responsibilities

OR-MSE-001 is responsible for:

- validating the minimum bar configuration;
- validating bar structure input;
- validating high and low values;
- rejecting non-finite price values;
- rejecting inconsistent high/low relationships;
- detecting higher-high progression;
- detecting higher-low progression;
- detecting lower-high progression;
- detecting lower-low progression;
- classifying bullish structure;
- classifying bearish structure;
- classifying mixed progression as RANGE;
- reporting insufficient input data;
- maintaining deterministic behavior.

---

## 4. Non-Responsibilities

The Market Structure Engine MUST NOT:

- generate BUY signals;
- generate SELL signals;
- generate NO TRADE decisions;
- calculate indicators;
- calculate position size;
- calculate account risk;
- manage stop-loss;
- manage take-profit;
- execute orders;
- connect to brokers;
- connect to exchanges;
- acquire live market data;
- perform sentiment analysis;
- perform prediction;
- perform machine learning;
- modify strategy parameters;
- perform portfolio management;
- persist market data.

These responsibilities belong to other ORION components.

---

## 5. Design Principles

### 5.1 Determinism

Given the same ordered sequence of valid bars and the same analyzer
configuration, the engine MUST return the same StructureResult.

No random state or external state is used.

---

### 5.2 Minimum Data Requirement

The analyzer requires a configurable minimum number of bars.

The default is:

```text
minimum_bars = 3