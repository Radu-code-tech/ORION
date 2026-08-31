# MOD-002 — OR-EVENT-001 Event Bus v1.1

## 1. Module Identity

- Module ID: MOD-002
- Component ID: OR-EVENT-001
- Component Name: Event Bus
- Version: v1.1
- Status: Hardened
- Layer: ORION Communication
- Previous Version: v1.0
- Hardening Scope: MOD-002 → MOD-002 v1.1
- Compatibility Target: MOD-003+

---

## 2. Purpose

OR-EVENT-001 provides deterministic in-process publish/subscribe
communication between ORION components.

The Event Bus provides a small, synchronous communication mechanism
through which ORION components can publish events and register handlers
for specific topics.

The component is infrastructure-oriented.

It does not interpret market information, generate trading decisions,
calculate risk, execute orders, or perform learning.

---

## 3. Responsibilities

OR-EVENT-001 is responsible for:

- defining immutable ORION events;
- validating event topics;
- registering event subscribers;
- validating subscriber definitions;
- preventing duplicate subscriptions;
- removing registered subscribers;
- reporting subscriber counts;
- publishing events synchronously;
- dispatching subscribers in registration order;
- isolating subscriber failures;
- collecting subscriber exceptions;
- preserving deterministic dispatch behavior;
- using a subscriber snapshot during dispatch.

---

## 4. Non-Responsibilities

The Event Bus MUST NOT:

- generate BUY signals;
- generate SELL signals;
- generate NO TRADE decisions;
- analyze market structure;
- calculate indicators;
- calculate position size;
- calculate risk exposure;
- manage stop-loss or take-profit levels;
- place orders;
- cancel orders;
- connect to brokers or exchanges;
- fetch market data;
- generate market sentiment;
- perform portfolio management;
- perform machine learning;
- modify strategy parameters;
- persist events;
- provide distributed messaging;
- provide multiprocessing;
- provide retry queues;
- provide external message delivery.

These responsibilities belong to other ORION components.

---

## 5. Design Principles

### 5.1 Determinism

Given the same event and subscriber registration state,
the Event Bus must produce the same dispatch behavior.

Subscribers are always invoked in registration order.

---

### 5.2 Synchronous Dispatch

Event publication is synchronous.

`publish()` invokes registered handlers directly and does not create
background threads, asynchronous queues, or external tasks.

---

### 5.3 Failure Isolation

A subscriber failure MUST NOT prevent later subscribers from receiving
the same event.

Exceptions raised by subscribers are collected and returned by `publish()`.

---

### 5.4 Subscriber Snapshot

At the beginning of a publish operation, the current subscriber list
for the event topic is copied.

Changes to subscriptions performed by handlers during dispatch therefore
do not change the subscriber set of the current dispatch cycle.

New subscriptions become effective for subsequent publications.

---

### 5.5 Immutable Events

`Event` instances are immutable.

The dataclass is frozen to prevent accidental mutation of event identity,
topic, payload reference, or event identifier fields.

---

### 5.6 Minimal Communication Layer

The Event Bus must remain a small infrastructure component.

It must not accumulate business logic or trading intelligence.

---

## 6. Public Contract

### 6.1 Event

The public event structure is:

```text
Event(
    topic: str,
    payload: Any = None,
    event_id: str | None = None
)