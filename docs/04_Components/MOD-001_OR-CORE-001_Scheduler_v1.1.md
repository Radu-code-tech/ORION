# MOD-001 — OR-CORE-001 Scheduler v1.1

## 1. Module Identity

- Module ID: MOD-001
- Component ID: OR-CORE-001
- Component Name: Scheduler
- Version: v1.1
- Status: Hardened
- Layer: ORION Core
- Previous Version: v1.0
- Hardening Scope: MOD-001 → MOD-001 v1.1
- Compatibility Target: MOD-002+
  
---

## 2. Purpose

OR-CORE-001 provides deterministic scheduling of internal ORION jobs.

The Scheduler coordinates registered jobs and executes them when their
configured execution time is reached.

The component is intentionally small and infrastructure-oriented.

It contains no market logic, trading logic, risk logic, execution logic,
signal generation, decision logic, or learning logic.

---

## 3. Responsibilities

OR-CORE-001 is responsible for:

- registering internal jobs;
- validating job definitions;
- preventing duplicate job registration;
- starting and stopping scheduler execution;
- determining when registered jobs are due;
- executing due jobs once per scheduler cycle;
- preserving deterministic job execution order;
- rescheduling successfully executed jobs;
- propagating handler failures;
- avoiding successful rescheduling after a failed handler execution;
- supporting deterministic testing through an injectable clock.

---

## 4. Non-Responsibilities

The Scheduler MUST NOT:

- generate BUY signals;
- generate SELL signals;
- generate NO TRADE decisions;
- calculate trading indicators;
- analyze market structure;
- calculate position size;
- calculate risk exposure;
- manage stop-loss or take-profit levels;
- place or cancel orders;
- connect to brokers or exchanges;
- fetch market data;
- generate market sentiment;
- perform portfolio management;
- perform machine learning;
- modify trading strategy parameters.

These responsibilities belong to other ORION components.

---

## 5. Design Principles

OR-CORE-001 follows these principles:

### 5.1 Determinism

Given the same clock state, registered jobs, intervals, and handlers,
the Scheduler must produce the same execution behavior.

### 5.2 Dependency Isolation

The Scheduler does not depend on market-data providers, brokers,
exchanges, trading APIs, or external services.

### 5.3 Injectable Time Source

The Scheduler accepts an injectable Clock implementation.

This allows deterministic unit testing without waiting for real time.

### 5.4 Non-Blocking Operation

`tick()` does not sleep and does not own the operating-system scheduling loop.

A higher-level ORION runtime is responsible for calling `tick()` at the
desired cadence.

### 5.5 Minimal Core

The Scheduler must remain a small infrastructure component.

Trading intelligence must not be introduced into OR-CORE-001.

---

## 6. Public Contract

### 6.1 Clock

The Scheduler accepts an object implementing:

```text
now() -> datetime