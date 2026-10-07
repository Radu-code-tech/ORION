# MOD-007 — OR-MEM-001
# Market Memory — Design

**Project:** ORION
**Module:** MOD-007
**Component:** OR-MEM-001
**Version:** v1.0
**Status:** DESIGN — APPROVED FOR IMPLEMENTATION
**Specification baseline:** 2fea3ea
**Lifecycle:** SPECIFICATION → DESIGN → IMPLEMENTATION → TEST → VALIDATION → MERGE → PUSH

---

# 1. Design Objective

This document defines the implementation design for OR-MEM-001 Market Memory v1.0.

The Design implements the frozen MOD-007 Specification without redefining Evidence semantics owned by OR-EVIDENCE-001.

Market Memory provides deterministic historical-context semantics over validated immutable Evidence.

The central design rule is:

> EvidenceStore owns Evidence storage semantics. MarketMemory owns historical-memory semantics.

OR-MEM-001 shall compose existing Evidence infrastructure rather than duplicate Evidence identity, validation, canonicalization or base query behavior.

---

# 2. Architectural Position

The v1.0 runtime flow is:

    producer
       |
       v
    EvidenceEngine
       |
       +----> EvidenceStore
       |
       +----> EventBus: evidence.created
                        |
                        v
                   MarketMemory
                        |
                        v
                   EvidenceStore
                 (memory-owned private store)

MarketMemory owns a private EvidenceStore dedicated exclusively to Market Memory membership.

The internal EvidenceStore is not supplied through the public MarketMemory constructor in v1.0.

The authoritative EvidenceEngine store and the MarketMemory store are distinct storage instances with distinct responsibilities.

Evidence enters Market Memory only through the MarketMemory acceptance contract defined by this Design.

External code shall not receive direct mutable access to the internal MarketMemory EvidenceStore.

This preserves composition with OR-EVIDENCE-001 while preventing external storage mutation from bypassing Market Memory membership semantics.

---

# 3. Responsibility Boundary

OR-EVIDENCE-001 remains authoritative for:

- Evidence construction;
- Evidence validation;
- Evidence immutability;
- canonical serialization;
- evidence_id;
- base Evidence storage behavior;
- duplicate rejection at EvidenceStore level;
- deterministic Evidence query ordering.

OR-MEM-001 is authoritative for:

- Evidence membership in Market Memory;
- idempotent Evidence replay;
- memory-oriented identity lookup;
- membership testing;
- deterministic historical queries;
- bounded recent-history retrieval;
- EventBus ingestion of validated Evidence;
- memory lifecycle operations explicitly exposed by v1.0.

MarketMemory shall not reconstruct, recalculate, correct or reinterpret Evidence.

---

# 4. Public Package

The component shall use:

    src/memory/
    ├── __init__.py
    ├── exceptions.py
    └── market_memory.py

No public MemoryRecord model shall exist in v1.0.

No separate store.py shall be introduced unless implementation evidence demonstrates that EvidenceStore composition cannot satisfy the approved Design.

---

# 5. Primary Class

The primary public class is MarketMemory.

Public constructor:

    MarketMemory(
        *,
        event_bus: EventBus | None = None,
    )

MarketMemory creates and exclusively owns its internal EvidenceStore.

EvidenceStore is deliberately not a public constructor dependency in v1.0.

If event_bus is supplied, it must be an EventBus.

An invalid event_bus dependency raises InvalidMemoryDependency.

Invalid constructor dependencies fail explicitly.

Construction shall not read wall-clock time.

---

# 6. Storage Composition

MarketMemory uses composition, not inheritance.

Each MarketMemory instance creates exactly one private EvidenceStore for its membership state.

The internal EvidenceStore remains an implementation detail and shall not be exposed through a public mutable property.

MarketMemory delegates Evidence-owned storage and base-query behavior to that store where doing so preserves the Market Memory contract.

MarketMemory shall not implement a second Evidence canonicalizer, validator, identity generator or general-purpose Evidence storage engine.

No external mutation path may establish or remove Market Memory membership except through explicit MarketMemory lifecycle operations defined by this Design.

---

# 7. Membership Identity

Evidence.evidence_id is the sole identity of Evidence membership in Market Memory v1.0.

No memory_id is introduced.

MarketMemory shall not recalculate, replace or reinterpret evidence_id.

The first successful acceptance of an evidence_id establishes membership.

Retrieval, membership testing, replay detection and deterministic timestamp tie-breaking use evidence_id.

Membership identity shall not depend on Python object identity, memory address, ingestion order, wall-clock time or process-specific state.

---

# 8. Evidence Acceptance API

The public acceptance operation is:

    remember(evidence: Evidence) -> bool

Behavior:

- return True when evidence establishes new Market Memory membership;
- return False when the evidence_id is already a member;
- never create a second membership for the same evidence_id;
- never replace the first accepted Evidence object during replay;
- never modify the accepted Evidence;
- never change canonical ordering as a result of replay.

For new membership, MarketMemory delegates storage to its private EvidenceStore.

The operation is synchronous in v1.0.

---

# 9. Replay and Metadata

Replay identity is determined exclusively by Evidence.evidence_id.

Because OR-EVIDENCE-001 excludes metadata from evidence_id, two valid Evidence objects may carry the same evidence_id while differing in metadata.

Such an input is an idempotent replay for Market Memory v1.0.

MarketMemory preserves the first accepted immutable Evidence object and does not replace it with a later object carrying the same evidence_id.

Metadata differences shall not create a second membership, a new identity or a silent replacement.

Replay shall not alter count, ordering, historical-query results or stored semantic state.

---

# 10. Invalid Input

remember() accepts only validated Evidence instances.

MarketMemory shall not coerce arbitrary objects into Evidence.

A non-Evidence input raises InvalidMemoryEvidence.

Invalid dependency types supplied to the constructor raise InvalidMemoryDependency.

Evidence-owned validation rules remain the responsibility of OR-EVIDENCE-001 and shall not be duplicated by MarketMemory.

---

# 11. Retrieval API

MarketMemory exposes non-strict and strict retrieval.

Public operations:

    get(evidence_id: str) -> Evidence | None

    require(evidence_id: str) -> Evidence

get() returns the stored Evidence when membership exists.

get() returns None when a valid evidence_id is not present.

require() returns the stored Evidence when membership exists.

require() raises MemoryEvidenceNotFound when a valid evidence_id is not present.

Both operations return the first accepted immutable Evidence object.

Both operations validate evidence_id before lookup.

---

# 12. Membership API

MarketMemory exposes:

    contains(evidence_id: str) -> bool

contains() returns True only when the validated evidence_id is currently a member of Market Memory.

contains() returns False for a valid but absent evidence_id.

contains() validates evidence_id before lookup.

All public APIs accepting evidence_id use the same identity-validation rule.

A supplied evidence_id must be a non-empty string.

Whitespace-only evidence_id values are invalid.

MarketMemory shall not normalize, trim, recalculate or otherwise transform evidence_id.

Invalid identity input raises InvalidMemoryIdentity.

---

# 13. Query API

The public historical query operation is:

    query(
        *,
        evidence_id: str | None = None,
        source: str | None = None,
        type: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> tuple[Evidence, ...]

All supplied filters are conjunctive.

The result is an immutable tuple.

Results use canonical ascending order:

    (Evidence.timestamp, evidence_id)

Query results are independent of ingestion order.

Query shall not mutate stored Evidence or Market Memory state.

---

# 14. Query Delegation

MarketMemory delegates the following filters to EvidenceStore.query():

- source;
- type;
- symbol;
- timeframe;
- start;
- end.

MarketMemory shall not duplicate EvidenceStore timestamp-boundary implementation or base filtering behavior.

Because EvidenceStore.query() does not expose evidence_id as a filter in MOD-006 v1.0, MarketMemory applies the optional evidence_id filter to the deterministic result returned by EvidenceStore.query().

Applying evidence_id shall preserve canonical ordering.

MarketMemory shall not perform a second full sort after EvidenceStore.query().

---

# 15. Query Parameter Semantics

Text filters use the exact semantics provided by EvidenceStore.query().

MarketMemory shall not introduce aliases, case conversion, trimming or inference for source, type, symbol or timeframe query filters.

Timestamp filtering uses Evidence.timestamp.

Timestamp ranges are half-open:

    [start, end)

start is inclusive.

end is exclusive.

When both boundaries are supplied:

    start < end

is required.

start >= end is invalid.

Omitted start means no lower bound.

Omitted end means no upper bound.

EvidenceStore / OR-EVIDENCE-001 timestamp validation remains authoritative, including timezone-awareness and UTC normalization.

Its timestamp-validation exceptions may propagate unchanged through MarketMemory.

When evidence_id is supplied to query(), it uses the same InvalidMemoryIdentity validation rule as get(), require() and contains().

query() validates the MarketMemory-owned evidence_id parameter before delegating source, type, symbol, timeframe and timestamp filtering to EvidenceStore. Therefore, if evidence_id and a delegated timestamp boundary are both invalid, InvalidMemoryIdentity has deterministic failure precedence.

---

# 16. Historical Recent API

MarketMemory exposes:

    recent(
        limit: int,
        *,
        evidence_id: str | None = None,
        source: str | None = None,
        type: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> tuple[Evidence, ...]

recent() validates limit before executing query semantics. Therefore, an invalid limit has deterministic failure precedence over invalid query-filter inputs.

After limit validation succeeds, recent() applies the same conjunctive filtering semantics as query().

The most recent N records are the final N records of that canonically ordered filtered result.

The returned records remain in canonical ascending order.

recent() shall not reverse the result.

recent() shall not use ingestion order.

recent() shall not use wall-clock time.

---

# 17. Limit Validation

limit must be an exact int greater than zero.

bool is explicitly rejected even though bool is a Python subclass of int.

Zero is invalid.

Negative values are invalid.

Non-integer values are invalid.

Invalid limit input raises InvalidMemoryLimit.

v1.0 defines no implicit default limit.

v1.0 defines no hidden maximum limit.

If limit exceeds the number of matching records, recent() returns all matching records in canonical ascending order.

---

# 18. EventBus Integration

If an EventBus is supplied at construction, MarketMemory subscribes to the existing:

    evidence.created

topic defined by OR-EVIDENCE-001.

MarketMemory shall use the existing EVIDENCE_CREATED_TOPIC constant rather than duplicate the topic string in production logic.

The subscriber handler passes Event.payload to remember().

Direct remember() ingestion and EventBus ingestion therefore share the same membership semantics.

MarketMemory does not require EventBus for direct operation.

EventBus transport semantics remain owned by OR-EVENT-001.

---

# 19. Event Validation

MarketMemory does not redefine Event validation owned by OR-EVENT-001.

For an evidence.created event received by the MarketMemory subscriber, Event.payload must satisfy the remember() Evidence contract.

An invalid payload therefore raises InvalidMemoryEvidence from the subscriber path.

MarketMemory shall not silently suppress that failure.

Under existing EventBus semantics, subscriber exceptions are isolated and returned by EventBus.publish().

A MarketMemory subscriber failure shall not rewrite EventBus failure-isolation behavior.

No invalid event payload shall establish Market Memory membership.

---

# 20. Event Replay

Repeated delivery of an evidence.created event carrying an already-member evidence_id is an idempotent replay.

The repeated event shall not create a second membership.

The repeated event shall not replace the first accepted Evidence object.

The repeated event shall not change count, canonical ordering or query results.

The EventBus ingestion path shall therefore preserve the same True-for-new and False-for-replay semantics internally as direct remember().

Event replay shall not be treated as an EvidenceStore DuplicateEvidence failure during normal single-threaded v1.0 operation.

---

# 21. Market Memory Lifecycle Events

OR-MEM-001 v1.0 publishes no Market Memory lifecycle events.

No memory.created, memory.replayed, memory.cleared or equivalent topic is introduced in v1.0.

Membership outcomes are observable through public API return values and retrieval state.

A future lifecycle-event contract requires an explicit versioned specification change.

This avoids creating transport semantics that are not required by the v1.0 Specification.

---

# 22. Subscription Lifecycle

When constructed with an EventBus, MarketMemory subscribes exactly once to EVIDENCE_CREATED_TOPIC.

MarketMemory retains the exact subscriber-handler reference used for registration.

MarketMemory exposes:

    close() -> None

close() unsubscribes the MarketMemory handler when subscribed.

close() is idempotent.

Calling close() more than once shall not fail.

When no EventBus was supplied, close() is a no-op.

close() does not clear Market Memory.

After successful close(), future evidence.created publications shall not be ingested by that MarketMemory instance.

close() affects only EventBus subscription lifecycle. It does not place MarketMemory into a closed semantic state. Direct public operations, including remember(), get(), require(), contains(), query(), recent(), count() and clear(), remain usable after close().

v1.0 does not claim thread-safe concurrent close, publish or mutation semantics.

---

# 23. Count

MarketMemory exposes:

    count() -> int

count() returns the number of unique evidence_id memberships currently stored.

Idempotent replay does not increase count.

count() delegates to the private EvidenceStore count semantics.

count() does not depend on wall-clock time.

---

# 24. Clear

MarketMemory exposes:

    clear() -> None

clear() explicitly removes all current Market Memory memberships.

clear() delegates storage clearing to the private EvidenceStore.

clear() does not unsubscribe from EventBus.

After clear(), count() returns zero.

After clear(), previously stored evidence_id values are absent from get(), require(), contains(), query() and recent() results.

A later Evidence with a previously cleared evidence_id may establish membership again.

clear() is an explicit caller action and is not automatic retention or eviction.

---

# 25. Retention

OR-MEM-001 v1.0 uses unlimited in-memory retention for the lifetime of the MarketMemory store unless clear() is explicitly invoked.

There is no automatic TTL.

There is no age-based eviction.

There is no count-based eviction.

There is no wall-clock-driven eviction.

There is no background retention process.

There is no hidden capacity limit.

Bounded automatic retention is outside v1.0 and requires a future versioned specification.

---

# 26. Exception Hierarchy

OR-MEM-001 defines:

    class MarketMemoryError(Exception):
        ...

    class InvalidMemoryDependency(MarketMemoryError, TypeError):
        ...

    class InvalidMemoryEvidence(MarketMemoryError, TypeError):
        ...

    class InvalidMemoryIdentity(MarketMemoryError, TypeError, ValueError):
        ...

    class InvalidMemoryLimit(MarketMemoryError, TypeError, ValueError):
        ...

    class MemoryEvidenceNotFound(MarketMemoryError, LookupError):
        ...

Market Memory exceptions represent Market Memory contract failures only.

Existing OR-EVIDENCE-001 exceptions may propagate when failure belongs to Evidence-owned semantics.

In particular, EvidenceStore timestamp-boundary validation exceptions are not wrapped merely to create a Market Memory-specific type.

No broad catch-and-rewrite exception layer shall hide the originating contract owner.

---

# 27. DuplicateEvidence Handling

EvidenceStore rejects duplicate evidence_id insertion with DuplicateEvidence.

MarketMemory has different public replay semantics: an already-member evidence_id is an idempotent replay.

Therefore remember() checks membership before attempting EvidenceStore.add().

During normal single-threaded v1.0 operation, replay shall return False without calling EvidenceStore.add() for the duplicate.

MarketMemory shall not use exception handling as the normal replay-control path.

No silent replacement is permitted.

v1.0 does not claim atomic check-and-add behavior under concurrent mutation and does not claim thread-safe mutation semantics.

Unexpected DuplicateEvidence outside the documented single-threaded replay path shall not be silently converted into successful new membership.

---

# 28. Determinism

For identical validated Evidence inputs, identical Market Memory state, identical configuration and identical query parameters, OR-MEM-001 shall produce identical semantic results.

Deterministic state and results shall not depend on:

- wall-clock time;
- local timezone;
- Python object identity;
- memory addresses;
- dictionary insertion order;
- Evidence ingestion order;
- process-specific hash randomization;
- nondeterministic serialization.

Canonical historical ordering remains:

    (Evidence.timestamp, evidence_id)

No datetime.now() or equivalent wall-clock read shall participate in membership identity, ordering, query semantics or reproducible state.

Operational diagnostics may record processing time only if such data does not become semantic Market Memory state.

---

# 29. Immutability

MarketMemory stores validated immutable Evidence.

MarketMemory shall not mutate Evidence fields, metadata, canonical bytes or evidence_id.

Public multi-record retrieval APIs return tuples.

MarketMemory shall not expose its internal EvidenceStore or its internal storage dictionary as mutable public state.

Replay preserves the first accepted immutable Evidence object.

Query and recent operations shall not mutate Market Memory state.

No public MemoryRecord wrapper is introduced to create a second mutable representation.

---

# 30. Complexity Targets

The v1.0 design targets the following expected complexity under the current in-memory EvidenceStore implementation:

- remember() new membership: expected O(1);
- remember() replay detection: expected O(1);
- get(): expected O(1);
- require(): expected O(1);
- contains(): expected O(1);
- count(): expected O(1);
- clear(): O(n);
- query(): O(n log n) worst case because EvidenceStore returns canonically sorted matches;
- recent(): O(n log n) worst case through query semantics.

MarketMemory shall not add a second full sort after EvidenceStore.query().

The v1.0 implementation shall prefer semantic correctness and deterministic behavior over premature indexing complexity.

These are design targets, not a claim of real-time latency guarantees.

Observability requirements that do not affect these semantics are defined by the following section.

---

# 31. Observability

OR-MEM-001 v1.0 requires observable semantic outcomes without introducing a mandatory logging framework.

The following outcomes are directly observable through the public API:

- new membership through remember() returning True;
- idempotent replay through remember() returning False;
- current membership through contains();
- current membership count through count();
- stored Evidence through get() and require();
- deterministic historical state through query() and recent();
- missing strict retrieval through MemoryEvidenceNotFound;
- invalid Market Memory inputs through typed exceptions;
- EventBus subscriber failures through existing EventBus.publish() exception reporting.

No mandatory logger dependency is introduced in v1.0.

Operational logging may be added without changing semantic state, identity, ordering or query results.

Logs shall not become a hidden source of Market Memory truth.

---

# 32. Configuration

OR-MEM-001 v1.0 requires no dedicated configuration file.

There are no retention-duration settings.

There are no capacity settings.

There are no ordering-mode settings.

There are no replay-policy settings.

There are no configurable identity rules.

The only optional runtime integration dependency is EventBus supplied through the MarketMemory constructor.

Future configuration shall require an explicit contract when it can affect semantic behavior.

---

# 33. Public Exports

The src.memory package shall publicly export:

    MarketMemory
    MarketMemoryError
    InvalidMemoryDependency
    InvalidMemoryEvidence
    InvalidMemoryIdentity
    InvalidMemoryLimit
    MemoryEvidenceNotFound

Evidence shall continue to be imported from src.evidence.

Event and EventBus shall continue to be imported from src.event.

OR-MEM-001 shall not re-export Evidence as if it were owned by the memory package.

No MemoryRecord is exported.

Internal handler functions and the private EvidenceStore shall not be public package exports.

---

# 34. Test Architecture

MOD-007 shall be implemented test-first.

The primary unit-test file is:

    tests/unit/test_market_memory.py

The unit suite shall cover at minimum:

- construction without EventBus;
- construction with valid EventBus;
- invalid EventBus dependency raising InvalidMemoryDependency;
- new Evidence acceptance;
- replay returning False;
- replay preserving first accepted Evidence;
- replay with differing metadata but identical evidence_id;
- rejection of non-Evidence input;
- get() present;
- get() absent;
- require() present;
- require() absent;
- contains() present and absent;
- invalid evidence_id across all public identity-taking APIs;
- count();
- clear();
- clear followed by re-acceptance;
- conjunctive query filters;
- evidence_id query filtering;
- canonical query ordering;
- insertion-order independence;
- start-inclusive timestamp boundary;
- end-exclusive timestamp boundary;
- invalid timestamp ranges;
- timezone-aware timestamp requirements through EvidenceStore semantics;
- recent() after filtering;
- recent() canonical ascending return order;
- recent() limit larger than result count;
- invalid zero limit;
- invalid negative limit;
- invalid non-integer limit;
- bool limit rejection;
- immutable tuple results;
- no automatic eviction;
- no wall-clock-dependent semantic behavior;
- EventBus subscription;
- EventBus Evidence ingestion;
- EventBus replay;
- invalid EventBus payload failure visibility;
- close() unsubscribe behavior;
- close() idempotence;
- close() without EventBus;
- clear() without unsubscribe.

The test suite shall verify behavior, not implementation trivia, except where the Design explicitly freezes an architectural boundary.

---

# 35. Integration Tests

The primary integration-test file is:

    tests/integration/test_market_memory_integration.py

Integration tests shall exercise the real component chain:

    Evidence
       |
       v
    EvidenceEngine.submit()
       |
       +----> EvidenceStore commit
       |
       +----> evidence.created
                    |
                    v
                EventBus
                    |
                    v
               MarketMemory

The integration suite shall prove:

- valid Evidence submitted through EvidenceEngine reaches MarketMemory;
- the exact Evidence identity is preserved;
- the accepted Evidence remains traceable to evidence_id;
- repeated delivery is idempotent;
- MarketMemory historical ordering remains deterministic;
- EventBus subscriber failure isolation remains unchanged;
- EvidenceEngine store-first / publish-second semantics remain unchanged;
- MarketMemory does not roll back the authoritative EvidenceStore;
- MarketMemory does not redefine EventBus transport semantics.

Integration tests shall use actual MOD-006 and EventBus public APIs rather than duplicate test doubles where real components are practical.

---

# 36. Backward Compatibility

MOD-007 v1.0 is additive.

Existing public behavior of OR-EVIDENCE-001 and OR-EVENT-001 shall remain unchanged.

No existing Evidence canonical representation shall change.

No existing evidence_id calculation shall change.

No existing EvidenceStore duplicate behavior shall change.

No existing EvidenceStore query semantics shall change.

No existing EvidenceEngine store-first / publish-second behavior shall change.

No existing EventBus subscription, ordering or failure-isolation behavior shall change.

All pre-MOD-007 tests must remain green.

A required modification to existing production behavior is a stop-and-review condition, not an implicit implementation detail.

---

# 37. Source Change Boundary

Expected production additions are:

    src/memory/__init__.py
    src/memory/exceptions.py
    src/memory/market_memory.py

Expected test additions are:

    tests/unit/test_market_memory.py
    tests/integration/test_market_memory_integration.py

No existing production source file is expected to require modification for MOD-007 v1.0.

In particular, implementation shall not modify:

    src/evidence/evidence.py
    src/evidence/store.py
    src/evidence/engine.py
    src/event/event_bus.py

If implementation appears to require changing an existing production component, work shall stop and the Design shall be reviewed before that change is made.

Documentation changes required by normal module completion remain permitted.

---

# 38. Implementation Sequence

Implementation shall proceed in the following controlled order:

1. add Market Memory exception hierarchy and tests;
2. add MarketMemory construction and private EvidenceStore ownership;
3. implement remember() and replay tests;
4. implement identity validation;
5. implement get(), require() and contains();
6. implement query() delegation and evidence_id filtering;
7. implement recent() and limit validation;
8. implement count() and clear();
9. implement EventBus subscription and ingestion;
10. implement close() and subscription lifecycle;
11. complete unit-test edge cases;
12. add real-component integration tests;
13. run MOD-007 focused tests;
14. run the complete repository regression suite;
15. perform Specification-to-Design-to-code compliance audit;
16. review Git diff and source-change boundary;
17. obtain owner acceptance before merge.

No implementation step may redefine a frozen semantic rule merely to simplify code.

---

# 39. Design Definition of Done

The MOD-007 Design is complete only when all of the following are true:

- every frozen Specification semantic decision is represented;
- Evidence remains the atomic semantic unit;
- evidence_id remains the sole membership identity;
- no memory_id exists;
- no public MemoryRecord exists;
- MarketMemory owns a private EvidenceStore;
- EvidenceStore is not publicly injectable in v1.0;
- remember() new/replay behavior is explicit;
- metadata replay behavior is explicit;
- identity validation is consistent across public identity-taking APIs;
- query semantics are conjunctive and deterministic;
- timestamp ranges remain [start, end);
- recent N semantics are explicit;
- EventBus integration uses EVIDENCE_CREATED_TOPIC;
- no new Market Memory lifecycle events are introduced;
- close() semantics are explicit;
- clear() semantics are explicit;
- unlimited v1.0 retention is explicit;
- InvalidMemoryDependency explicitly owns invalid constructor dependency failures;
- exception ownership is explicit;
- no thread-safety claim is made;
- determinism and immutability requirements are explicit;
- complexity targets are explicit;
- observability requirements are explicit;
- public exports are explicit;
- unit and integration test boundaries are explicit;
- backward compatibility is explicit;
- source-change boundaries are explicit;
- implementation order is explicit;
- the Specification remains unchanged;
- the complete pre-existing regression suite remains a mandatory gate.

Only after Design review and approval may implementation begin.

---

# 40. Final Design Principle

OR-MEM-001 adds memory semantics; it does not duplicate Evidence infrastructure.

Evidence remains the immutable statement of what ORION observed.

MarketMemory determines what validated Evidence ORION currently remembers and how that history is retrieved deterministically.

The implementation should remain smaller and simpler than the semantic contract it enforces.

MarketMemory remembers Evidence.

It does not reinterpret what that Evidence means.

---
