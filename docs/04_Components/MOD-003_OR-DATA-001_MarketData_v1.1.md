# MOD-003 — OR-DATA-001 Market Data v1.1

## 1. Module Identity

- Module ID: MOD-003
- Component ID: OR-DATA-001
- Component Name: Market Data
- Version: v1.1
- Status: Hardened
- Layer: ORION Data
- Previous Version: v1.0
- Hardening Scope: MOD-003 → MOD-003 v1.1
- Compatibility Target: MOD-004+

---

## 2. Purpose

OR-DATA-001 provides deterministic, validated in-memory market-data
storage for downstream ORION components.

The component stores OHLCV market bars identified by symbol,
timeframe, and timestamp.

The component is infrastructure-oriented.

It does not calculate indicators, analyze market structure,
generate trading signals, calculate risk, execute orders,
connect to brokers or exchanges, or perform machine learning.

---

## 3. Responsibilities

OR-DATA-001 is responsible for:

- defining immutable market bars;
- validating market-bar identity fields;
- validating OHLCV values;
- rejecting invalid numeric values;
- rejecting negative volume;
- storing validated market bars in memory;
- preventing duplicate market bars;
- supporting batch insertion;
- returning bars in chronological order;
- returning the latest available bar;
- counting stored bars;
- supporting symbol and timeframe filtering;
- providing deterministic behavior for downstream components.

---

## 4. Non-Responsibilities

OR-DATA-001 MUST NOT:

- connect to brokers;
- connect to exchanges;
- fetch live market data;
- place orders;
- cancel orders;
- generate BUY signals;
- generate SELL signals;
- generate NO TRADE decisions;
- analyze market structure;
- calculate trading indicators;
- calculate position size;
- calculate risk exposure;
- manage stop-loss or take-profit levels;
- generate market sentiment;
- perform portfolio management;
- perform machine learning;
- modify trading strategy parameters;
- persist data to external databases;
- perform distributed data synchronization;
- perform automatic timeframe resampling.

These responsibilities belong to other ORION components.

---

## 5. Design Principles

### 5.1 Determinism

Given the same set of valid market bars and the same query,
OR-DATA-001 must return the same result.

Bars are returned in ascending timestamp order.

---

### 5.2 Strict Validation

Market bars MUST be validated before being stored.

Validation includes:

- non-empty symbol;
- non-empty timeframe;
- valid datetime timestamp;
- finite OHLC values;
- coherent OHLC relationships;
- non-negative volume.

Invalid records MUST be rejected.

---

### 5.3 Immutable Market Bars

MarketBar instances are immutable.

The data structure is frozen to prevent accidental modification
after insertion.

This protects the integrity of stored market data.

---

### 5.4 Unique Market-Bar Identity

A market bar is uniquely identified by:

```text
(symbol, timeframe, timestamp)