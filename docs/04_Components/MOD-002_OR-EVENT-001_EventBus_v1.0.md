# MOD-002 — OR-EVENT-001 Event Bus v1.0

## Purpose
Provide deterministic in-process publish/subscribe communication between ORION components.

## Scope
- topic-based subscription
- registration-order dispatch
- duplicate subscription rejection
- unsubscribe
- subscriber-count inspection
- subscriber failure isolation with returned failures

## Non-goals
This version does not provide persistence, multiprocessing, distributed delivery,
retries, queues, or external messaging.

## Acceptance criteria
1. Matching subscribers receive events.
2. Delivery order is deterministic.
3. Duplicate subscriptions are rejected.
4. Unsubscribe removes delivery.
5. Invalid subscriptions are rejected.
6. One subscriber failure does not stop later subscribers.
7. Automated unit tests pass.
