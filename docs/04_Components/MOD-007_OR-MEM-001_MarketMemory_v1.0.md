# MOD-007 — OR-MEM-001
# Market Memory

**Project:** ORION
**Module:** MOD-007
**Component:** OR-MEM-001
**Version:** v1.0
**Status:** SPECIFICATION — APPROVED FOR DESIGN
**Lifecycle:** SPECIFICATION → DESIGN → IMPLEMENTATION → TEST → VALIDATION → MERGE → PUSH

---

# 1. Purpose

OR-MEM-001 provides ORION with deterministic, traceable and queryable memory of validated market Evidence across time.

The component exists so that downstream ORION components can reason over relevant historical context without mutating Evidence, duplicating Evidence semantics, or depending on undocumented process state.

Core principle:

> Evidence records what was observed. Market Memory preserves what ORION can deterministically remember about those observations across time.

Market Memory shall provide historical context.

Market Memory shall not provide trading conviction.

---

# 2. Responsibility

OR-MEM-001 is responsible for:

1. Accepting validated Evidence produced by OR-EVIDENCE-001.
2. Preserving traceability from memory entries to their originating Evidence.
3. Organizing accepted Evidence into deterministic temporal memory.
4. Supporting deterministic retrieval of historical market context.
5. Supporting bounded temporal queries.
6. Supporting filtering by relevant Evidence and market-context attributes.
7. Preserving immutable historical records after acceptance.
8. Detecting and handling replayed or duplicate Evidence deterministically.
9. Preserving deterministic ordering independent of ingestion order.
10. Maintaining explicit retention semantics.
11. Exposing observable memory operations.
12. Integrating with ORION infrastructure without changing Evidence semantics.
13. Failing explicitly when memory input or query constraints are invalid.
14. Remaining reproducible for identical accepted inputs and configuration.

---

# 3. Non-Responsibilities

OR-MEM-001 shall not:

- generate BUY signals;
- generate SELL signals;
- generate NO TRADE decisions;
- determine trade direction;
- calculate position size;
- define stop loss;
- define take profit;
- execute orders;
- manage portfolio risk;
- determine expected profitability;
- optimize strategies;
- perform autonomous learning;
- train predictive models;
- modify Evidence;
- redefine Evidence identity;
- infer missing Evidence fields;
- silently correct invalid Evidence;
- assign subjective confidence to Evidence;
- determine whether Evidence is bullish or bearish unless that semantic value already exists explicitly in the Evidence;
- replace OR-EVIDENCE-001 storage;
- replace EventBus;
- replace future Decision, Risk, Alpha or Learning components.

Market Memory is historical infrastructure, not a trading strategy.

---

# 4. Architectural Boundary

OR-MEM-001 sits downstream of OR-EVIDENCE-001.

The intended dependency direction is:

Market observations / ORION components
→ OR-EVIDENCE-001
→ validated immutable Evidence
→ OR-MEM-001
→ downstream analytical components

OR-MEM-001 may consume Evidence directly through an explicit API and/or through an approved EventBus integration.

OR-MEM-001 shall not require modification of Evidence objects.

OR-MEM-001 shall not change the semantic meaning of Evidence.

The Evidence subsystem remains the authority for Evidence validity and Evidence identity.

The Market Memory subsystem remains the authority for temporal memory organization and memory retrieval semantics.

---

# 5. Input Contract

The primary input to OR-MEM-001 shall be a valid immutable Evidence object produced according to OR-EVIDENCE-001.

Market Memory shall not accept arbitrary unvalidated market payloads as substitutes for Evidence.

At minimum, Market Memory may rely on the following Evidence properties:

- evidence_id;
- timestamp;
- source;
- type;
- value;
- symbol;
- timeframe;
- metadata.

The exact subset copied, referenced, indexed or materialized by Market Memory shall be defined during Design.

The originating `evidence_id` shall remain traceable.

---

# 6. Memory Representation

For v1.0, validated Evidence is the atomic semantic unit stored by Market Memory.

OR-MEM-001 shall not create a second domain object that duplicates the semantic fields already owned by Evidence.

Market Memory may maintain internal indexes or storage structures required for efficient retrieval, but those structures are implementation details and shall not redefine Evidence.

The stored semantic content shall remain the validated immutable Evidence object.

Market Memory shall preserve access to all Evidence fields without copying them into a competing public memory-record schema.

A separate public `MemoryRecord` entity is not required in v1.0.

A future version may introduce a distinct memory entity only if that entity represents semantics that cannot be represented as Evidence membership alone.

Such a change requires an explicit versioned specification and shall not be introduced silently during implementation.

---

# 7. Memory Identity

For v1.0, `evidence_id` is the identity of Evidence membership in Market Memory.

No separate `memory_id` shall be generated for ordinary Evidence membership.

Therefore:

- first acceptance of an `evidence_id` establishes membership;
- retrieval by identity uses `evidence_id`;
- duplicate/replay detection uses `evidence_id`;
- deterministic tie-breaking uses `evidence_id`;
- traceability remains directly connected to OR-EVIDENCE-001.

Market Memory shall not recalculate, replace or reinterpret `evidence_id`.

Identity shall not depend on:

- Python object identity;
- memory address;
- process-specific state;
- non-deterministic serialization;
- ingestion order;
- wall-clock processing time.

If a future Market Memory concept requires identity beyond `evidence_id`, that change requires an explicit versioned specification.

---
# 8. Immutability

Accepted historical memory records shall be immutable.

OR-MEM-001 shall not expose mutable internal storage through its public API.

A query or retrieval operation shall not permit callers to mutate historical memory state indirectly.

If internal indexing structures are mutable implementation details, they shall not change the semantic content of already accepted memory records.

---

# 9. Temporal Semantics

Market Memory is explicitly temporal.

Every accepted record shall preserve the originating Evidence timestamp.

For v1.0, the semantic time of Market Memory is the originating `Evidence.timestamp`.

`Evidence.timestamp` represents event time for Market Memory ordering, querying and historical-window semantics.

Ingestion time is not part of the semantic Market Memory state in v1.0.

OR-MEM-001 shall not generate an internal wall-clock timestamp such as `datetime.now()` as part of memory identity, ordering, query semantics or reproducible state.

Operational logging may record processing time, but such telemetry shall not alter Market Memory semantics.

Given the same accepted Evidence set and configuration, reconstruction at a different wall-clock time shall produce the same semantic memory state.

---

# 10. Temporal Ordering

Memory queries shall return deterministic ordering.

Ordering shall not depend on insertion order.

The canonical v1.0 ordering shall be ascending by:

1. `Evidence.timestamp`;
2. `evidence_id` as deterministic tie-breaker.

Ordering shall therefore be independent of ingestion order.

For v1.0, "most recent N" means the final N records from this canonical ordering after all query filters have been applied.

The returned result shall preserve canonical ascending order unless a future version explicitly introduces another documented ordering mode.

Identical memory content queried from identical memory state shall produce identical ordering.

---

# 11. Replay and Duplicate Semantics

OR-MEM-001 shall behave deterministically when the same Evidence is received more than once.

For v1.0, `evidence_id` is the identity of Evidence membership in Market Memory.

The first acceptance of an `evidence_id` adds that Evidence to Market Memory.

Repeated delivery of the same valid Evidence is an idempotent replay:

- it shall not create a second historical record;
- it shall not change canonical ordering;
- it shall not change query results;
- it shall not change semantic memory state.

Replay handling shall be observable and testable.

A separate `memory_id` shall not be introduced in v1.0 unless Design demonstrates a distinct memory entity that cannot be represented by Evidence membership.

Conflicting content claiming an already-known identity shall fail explicitly rather than silently replacing historical state.

---

# 12. Storage

The initial implementation may use in-memory storage.

Storage semantics shall support:

- insertion;
- retrieval;
- deterministic query;
- duplicate/replay handling;
- count or equivalent observability;
- explicit clearing where permitted;
- future replacement by persistent storage without changing the semantic contract.

Storage implementation details shall not leak into downstream business logic.

No silent replacement of historical records is permitted.

---

# 13. Retrieval

OR-MEM-001 shall support retrieval of known memory records using deterministic identifiers or traceable Evidence identity.

Retrieval shall have explicit semantics for missing records.

The Design shall define:

- standard retrieval behavior;
- strict retrieval behavior, if required;
- expected missing-record result or typed error.

Retrieval shall return immutable historical content.

---

# 14. Query

OR-MEM-001 shall support deterministic historical queries.

The initial query model shall support relevant combinations of:

- symbol;
- timeframe;
- source;
- Evidence type;
- Evidence identity;
- timestamp range.

All supplied filters shall be conjunctive unless explicitly defined otherwise.

Timestamp ranges use half-open interval semantics `[start, end)`:

- `start` is inclusive;
- `end` is exclusive;
- `start` and `end`, when supplied, shall be valid timezone-aware timestamps;
- `start < end` is required when both boundaries are supplied;
- `start >= end` is invalid and shall fail explicitly;
- an omitted `start` means no lower temporal bound;
- an omitted `end` means no upper temporal bound.

Timestamp filtering is applied to `Evidence.timestamp`.

These boundary semantics are frozen for v1.0 and shall be tested explicitly.

Queries shall never return internal mutable storage structures.

---

# 15. Historical Windows

Market Memory shall support bounded historical context.

A historical window represents a deterministic subset of memory constrained by time and/or an explicit record limit.

The Design shall define supported window semantics, including where applicable:

- start/end time;
- most recent N records;
- symbol/timeframe-scoped history;
- source/type-scoped history.

Window behavior shall be deterministic.

No hidden adaptive windowing is permitted in v1.0.

---

# 16. Retention

Retention policy shall be explicit.

For v1.0, the in-memory Market Memory store uses unlimited retention for the lifetime of the store.

OR-MEM-001 v1.0 shall not automatically evict accepted historical records because of age, count or wall-clock time.

Historical state may be removed only through an explicit lifecycle operation defined by the public API, such as `clear`, where such an operation is approved by Design.

Automatic bounded retention and eviction are deferred to a future version and are outside the v1.0 semantic contract.

Market Memory shall never silently discard historical records.

---

# 17. Determinism

For identical:

- accepted Evidence;
- configuration;
- memory state;
- query parameters;

OR-MEM-001 shall produce identical semantic results.

Determinism applies to:

- memory identity;
- duplicate handling;
- temporal ordering;
- retrieval;
- query;
- historical windows;
- retention behavior when enabled.

Wall-clock time shall not influence deterministic results unless explicitly supplied as an input defined by the contract.

---

# 18. EventBus Integration

OR-MEM-001 may integrate with OR-EVENT-001 EventBus.

EventBus owns transport.

Market Memory owns memory semantics.

If Market Memory subscribes to Evidence events:

1. only valid Evidence payloads shall be accepted;
2. EventBus delivery shall not redefine Evidence validity;
3. replayed events shall follow Market Memory duplicate/replay semantics;
4. subscriber failures shall follow existing EventBus behavior;
5. Market Memory shall not modify EventBus semantics.

The exact topic subscriptions and any Market Memory publication topics are deferred to Design.

---

# 19. Error Handling

OR-MEM-001 shall expose explicit and deterministic failure semantics.

Error conditions include, where applicable:

- invalid memory input;
- non-Evidence input;
- invalid timestamp constraint;
- invalid query range;
- invalid query limit;
- duplicate/replayed Evidence according to the selected policy;
- conflicting memory identity;
- missing memory record during strict retrieval;
- invalid retention configuration;
- unsupported operation.

Errors shall:

- identify the violated rule;
- fail explicitly;
- never silently corrupt memory;
- never silently mutate Evidence;
- never silently discard historical state.

Typed exceptions shall be defined during Design for semantically identifiable failures.

---

# 20. Evidence Integrity

Market Memory shall preserve Evidence integrity.

OR-MEM-001 shall not:

- modify `evidence_id`;
- modify Evidence timestamp;
- modify Evidence value;
- modify Evidence source/type;
- modify symbol/timeframe;
- mutate Evidence metadata;
- fabricate missing Evidence;
- reinterpret Evidence identity.

Any memory-specific metadata introduced by OR-MEM-001 shall remain logically separate from Evidence identity.

---

# 21. Testing Requirements

Development shall follow TDD.

Tests shall verify behavior rather than implementation accidents.

At minimum, testing shall cover:

### Input

- valid Evidence acceptance;
- invalid input rejection;
- Evidence integrity preservation.

### Memory

- immutable accepted records;
- deterministic memory identity;
- traceability to Evidence.

### Replay

- repeated identical Evidence;
- duplicate/replay policy;
- no ambiguous duplicate state.

### Retrieval

- existing record;
- missing record;
- strict retrieval if implemented.

### Query

- symbol filter;
- timeframe filter;
- source filter;
- Evidence type filter;
- Evidence identity filter;
- timestamp boundaries;
- conjunctive filters.

### Ordering

- deterministic temporal ordering;
- insertion-order independence;
- deterministic tie-breaking.

### Windows

- bounded time windows;
- bounded record-count windows if supported;
- deterministic results.

### Retention

- configured retention behavior if enabled;
- deterministic eviction if enabled;
- no silent eviction.

### EventBus

- valid Evidence event ingestion if integration is enabled;
- invalid payload rejection;
- replay behavior;
- subscriber-failure behavior consistent with OR-EVENT-001.

### Regression

- all existing ORION tests shall remain green.

---

# 22. Performance Requirements

Market Memory is infrastructure on a latency-sensitive decision path.

The initial implementation shall prioritize correctness and determinism over premature optimization.

Operations shall avoid unnecessary full-memory copying where practical.

Query and retrieval complexity shall remain measurable.

The Design shall identify expected complexity for:

- insertion;
- direct retrieval;
- temporal query;
- filtered query;
- historical-window retrieval.

Performance optimization shall not weaken determinism, immutability or traceability.

---

# 23. Observability

OR-MEM-001 shall provide sufficient observability to diagnose memory behavior.

Relevant operations may include:

- Evidence accepted into memory;
- replay/duplicate detected;
- memory record retrieved;
- query executed;
- retention/eviction executed;
- EventBus ingestion attempted;
- EventBus ingestion rejected.

Logs shall contain sufficient context to diagnose failures without exposing unnecessary payload contents.

Logging shall not alter deterministic behavior.

---

# 24. Security and Integrity

Market Memory shall treat historical state as integrity-sensitive.

The component shall:

- reject malformed inputs;
- prevent silent record replacement;
- prevent caller mutation of accepted historical state;
- preserve Evidence traceability;
- avoid execution of data contained in Evidence;
- avoid unsafe dynamic deserialization.

Memory data is data, never executable instructions.

---

# 25. Configuration

Configuration may include:

- component enabled state;
- EventBus subscription enabled state;
- retention policy;
- maximum record count;
- query limits;
- observability level.

Configuration values affecting semantic behavior shall be validated before use.

Invalid configuration shall fail explicitly.

Defaults shall be documented during Design.

---

# 26. Dependencies

OR-MEM-001 may depend on:

- OR-EVIDENCE-001 Evidence;
- OR-EVENT-001 EventBus where integration is enabled;
- Python standard library;
- ORION configuration and logging infrastructure where applicable.

OR-MEM-001 shall not depend on:

- Decision Engine;
- execution components;
- strategy-specific logic;
- broker APIs;
- portfolio state;
- future Learning Engine.

Dependencies shall preserve one-way architectural flow.

---

# 27. Backward Compatibility

MOD-007 shall not change the public semantic contract of:

- OR-CORE-001 Scheduler;
- OR-EVENT-001 EventBus;
- OR-DATA-001 MarketData;
- OR-MSE-001 MarketStructure;
- OR-RISK-001 RiskManager;
- OR-EVIDENCE-001 Evidence.

If integration requires changes to an existing public contract, that change shall be handled explicitly as a separate versioned design decision.

---

# 28. Definition of Done

MOD-007 v1.0 is complete only when:

1. Specification is approved.
2. Design is approved.
3. Public interfaces are documented.
4. Memory identity semantics are explicit.
5. Temporal semantics are explicit.
6. Replay/duplicate semantics are explicit.
7. Retention semantics are explicit.
8. Error semantics are explicit.
9. Implementation follows approved Design.
10. Unit tests pass.
11. Integration tests pass where applicable.
12. Full ORION regression suite passes.
13. Results are deterministic.
14. Evidence remains immutable and traceable.
15. No existing module contract is silently changed.
16. Logs and errors are sufficiently explainable.
17. Repository diff is reviewed.
18. Working tree is clean after commit.
19. Owner acceptance is obtained.
20. Approved changes are merged and pushed to Repository Master.

---

# 29. Validation Principle

Market Memory shall be judged by whether it preserves reliable historical context, not by whether it increases trade frequency.

A correct Market Memory may return:

- no matching history;
- limited history;
- repeated historical patterns without interpretation.

Absence of memory is valid information.

Market Memory shall never fabricate context merely to satisfy downstream consumers.

---

# 30. Design Items Explicitly Deferred

The following implementation and interface decisions remain intentionally deferred to Design:

1. Exact internal storage/index structures.
2. Exact public class and method names.
3. Exact query API signature.
4. Exact query parameter validation and normalization rules.
5. Exact historical-window API signature.
6. Validation rules for record-count limits.
7. EventBus topic subscription mechanism.
8. Whether Market Memory publishes lifecycle events.
9. Typed exception hierarchy.
10. Missing-record behavior and strict retrieval API.
11. Logging API and structured log fields.
12. Complexity targets for insertion, retrieval and query.
13. Configuration defaults that do not contradict this Specification.
14. Public package exports.
15. Exact behavior and return value of explicit `clear`, if exposed.

The following semantic decisions are NOT deferred and are frozen by this Specification for v1.0:

- validated Evidence is the atomic semantic unit of Market Memory;
- `evidence_id` is the identity of Evidence membership;
- no separate `memory_id` is generated for ordinary membership;
- `Evidence.timestamp` is the semantic event time;
- timestamp ranges use `[start, end)` semantics with `start < end` when both boundaries are supplied;
- ingestion time is not part of semantic memory state;
- canonical ordering is ascending `(Evidence.timestamp, evidence_id)`;
- replay of identical valid Evidence is idempotent;
- "most recent N" is evaluated after filtering against canonical ordering;
- v1.0 in-memory retention is unlimited for the lifetime of the store;
- automatic eviction is outside the v1.0 contract.

No deferred item may be silently decided during implementation in a way that contradicts the frozen semantic decisions above.

---
# 31. Success Criteria

MOD-007 succeeds when ORION can deterministically answer questions of the form:

- What validated Evidence do we remember for this market context?
- What Evidence existed before a defined point in time?
- What is the ordered history for a symbol/timeframe?
- Has this Evidence already been incorporated into memory?
- What bounded historical context is available to a downstream component?

The answers shall be:

- deterministic;
- traceable;
- immutable;
- reproducible;
- independent of accidental ingestion order.

Success does not require trading decisions.

---

# 32. Final Principle

OR-MEM-001 exists to give ORION reliable historical context without giving historical context authority it does not possess.

> Evidence establishes facts. Memory preserves context. Decision logic decides what that context means.
