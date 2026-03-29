# Spring Boot Implementation Instructions - Alert Summary Enrichment System

## Purpose

This document provides implementation rules and coding guidance for building the Spring Boot application after the architecture/design has been finalized.

The AI assistant should use this document to generate a clean, production-grade Spring Boot application skeleton and implementation.

Do not ignore the design decisions produced from the architecture phase.
Implementation must follow the chosen design.

---

## Technology Baseline

- Java 21
- Spring Boot 3.x
- Maven
- Redis
- REST APIs
- Virtual threads
- Structured logging
- Logback + logstash encoder for JSON console logging
- Externalized configuration

---

## High-Level Implementation Goals

Build a Spring Boot application that:

1. receives Actimize RCM events,
2. acknowledges requests immediately,
3. processes events asynchronously,
4. delays ITEM_CREATED / ITEM_UPDATED processing for ~30-40 seconds,
5. runs 7-8 queries to prepare alert data,
6. stores alert data in Redis with 2-day TTL,
7. stores `refetchFlag=true` when partial query failures happen,
8. on OWNER_AUTO_ASSIGNED, fetches cache and optionally refetches,
9. calls external summary-generation application,
10. supports clean observability and error handling,
11. supports environment-specific logging behavior.

---

## Coding Principles

### General Java Principles
1. Use Java 21 features where they improve clarity and correctness.
2. Prefer records for immutable DTOs where appropriate.
3. Prefer enums for event types, processing states, and statuses.
4. Keep methods small and focused.
5. Follow single responsibility principle.
6. Avoid overly large service classes.
7. Use composition over inheritance.
8. Prefer immutable data where practical.
9. Use meaningful names; avoid vague utility classes.
10. Model outcomes explicitly instead of relying on ambiguous nulls and loosely typed maps.

### Spring Boot Principles
1. Use constructor injection everywhere possible.
2. Externalize all configurable values.
3. Keep controllers thin.
4. Put business logic in service layer.
5. Separate domain, orchestration, infrastructure, and API layers.
6. Use `@ConfigurationProperties` instead of scattered `@Value` where possible.
7. Use `@Async` only where it adds clear value and is supported by configured executor strategy.
8. Centralize exception handling where applicable.
9. Keep external client logic isolated behind interfaces/adapters.
10. Prefer explicit configuration over magic defaults.
11. Keep environment-specific behavior driven by Spring profiles and configuration rather than hardcoded conditional logic.

---

## Suggested Package Structure

Use a package structure similar to this:

- `controller`
- `api`
- `domain`
- `domain.model`
- `domain.event`
- `service`
- `service.orchestration`
- `service.query`
- `service.cache`
- `service.delay`
- `service.summary`
- `client`
- `config`
- `logging`
- `metrics`
- `exception`
- `util`

The exact structure can vary, but responsibilities must stay clean.

---

## Domain Modeling Guidelines

Model the following concepts explicitly:

### Events
- Actimize event type
- event payload
- alert key / alert id / cwi id
- timestamps
- correlation id / request id if available

### Cache Model
Redis cache entry should likely contain:
- alertKey
- structured alert data
- refetchFlag
- lastUpdatedTime
- sourceEventType
- processing status
- optional version / sequence number
- optional summary status

### Processing States
Use explicit state modeling where useful, for example:
- RECEIVED
- DELAYED
- QUERYING
- PARTIAL_SUCCESS
- SUCCESS
- FAILED
- SUMMARY_REQUESTED
- SUMMARY_COMPLETED
- SUMMARY_FAILED

---

## API / Controller Guidelines

### Event Ingestion API
Implement endpoint(s) to receive Actimize events.

Requirements:
1. validate request payload,
2. identify event type,
3. generate or propagate correlation ID,
4. log receipt of request,
5. immediately return acknowledgment,
6. dispatch background processing asynchronously.

The controller must not contain query logic, cache logic, or delay logic.

---

## Async Processing Guidelines

1. Use asynchronous dispatch so event API returns immediately.
2. Use a dedicated async executor configuration.
3. Prefer a virtual-thread-backed executor where appropriate.
4. Clearly separate:
   - request acknowledgment thread
   - background orchestration
   - delayed processing
   - query execution
5. Do not mix unrelated async mechanisms without reason.
6. Ensure logging context is propagated across async boundaries.

The generated code should explain where `@Async` is used and why.

---

## Virtual Thread Guidelines

Use virtual threads thoughtfully.

Recommended usage areas:
- background event processing
- worker execution
- blocking I/O tasks such as DB calls or downstream HTTP calls

The code should:
1. configure virtual-thread-based executors cleanly,
2. avoid unnecessary fixed thread pools for blocking workflows,
3. still consider DB connection limits and downstream capacity,
4. document why virtual threads help here,
5. not assume virtual threads eliminate the need for concurrency control.

Important:
Virtual threads do not remove the need for controlling DB concurrency.
Implementation should still consider limiting concurrent DB work if necessary.

---

## Delay Queue Requirements

The requirements mention a Java delay queue.

Implementation instructions:
1. Provide a delay-processing abstraction, not just raw queue code in controller.
2. Use a dedicated component such as:
   - `DelayedEventScheduler`
   - `DelayedEventWorker`
   - `DelayedEventItem`
3. Delay should be configurable via properties.
4. Explain limitations if the delay queue is purely in-memory:
   - lost tasks on restart,
   - poor multi-pod coordination,
   - duplicate scheduling risks.

If design chooses a different production-grade alternative, implement according to final design, but still discuss the delay queue requirement and why the chosen approach is better.

---

## Query Orchestration Guidelines

For the 7-8 queries:
1. Encapsulate each query in its own service/component where practical.
2. Create a coordinator/orchestrator to run them together.
3. Use structured result objects rather than raw maps.
4. Handle partial failure explicitly.
5. Return a result object that includes:
   - query data,
   - failed query list,
   - overall status,
   - refetch flag decision.
6. Capture execution timing per query.
7. Log query name, status, and duration in a consistent structured format.
8. Avoid logging full payloads when not needed; log identifiers and summary metadata instead.

The implementation should not bury partial-failure logic deep in random classes.

---

## Cache Guidelines

Redis handling should be encapsulated in a dedicated cache service.

Requirements:
1. store cache entries with TTL = 2 days,
2. read cache by alert key,
3. update cache safely,
4. include refetch flag,
5. include metadata useful for debugging,
6. consider versioning or stale-write prevention if required by design,
7. capture timing for cache read/write operations,
8. log cache hits, misses, updates, and failures with useful identifiers.

Do not scatter Redis operations across many classes.

---

## Summary Generation Client Guidelines

The call to summary-generation application should:
1. be isolated in a dedicated client/adapter,
2. have request/response DTOs,
3. include timeout handling,
4. include retry strategy if appropriate,
5. log outbound requests safely,
6. avoid leaking infrastructure concerns into orchestration logic,
7. capture API execution time,
8. record success/failure and downstream status in logs.

---

## Logging Requirements

### Environment-Specific Logging Behavior

Logging must behave differently by environment:

- **local**:
  - plain text console logging
  - optimized for developer readability
  - concise but still include identifiers needed for debugging

- **dev**, **it**, **uat**, **prod**:
  - JSON logs to console
  - compatible with logstash-style structured logging
  - suitable for ingestion by centralized observability/logging platforms

This should be implemented through profile-specific Logback configuration rather than ad hoc if/else code in Java.

### Logging Framework Expectations

Use:
- SLF4J facade
- Logback
- logstash-logback-encoder for JSON logging in non-local environments

The implementation should separate:
- local developer-friendly console appender
- structured JSON console appender for higher environments

### Structured Logging Expectations

For JSON logs, include useful fields such as:

- timestamp
- level
- logger
- thread
- application name
- active profile / environment
- correlation id
- trace id / span id if available
- event type
- alert key / alert id / cwi id
- processing state
- operation name
- external system
- outcome
- exception class
- exception message
- execution time in milliseconds

Exact field names can vary, but they must be consistent and intentional.

### Timing / Duration Logging

Execution durations must be captured and emitted as structured fields for important operations:

- inbound event handling
- query execution
- Redis read/write
- downstream summary API call
- orchestration-level processing

Recommended approach:
- implement a reusable timing helper, interceptor, or aspect
- expose duration as numeric fields, not embedded only inside message strings

Examples:
- `executionTimeMs`
- `queryExecutionTimeMs`
- `redisExecutionTimeMs`
- `apiExecutionTimeMs`

### MDC / Context Propagation

The implementation should use MDC or an equivalent approach to carry context such as:
- correlation id
- alert id / alert key
- cwi id
- event type

Because the app uses async processing and virtual threads, the implementation must explicitly address context propagation across thread boundaries.
Do not assume MDC magically flows everywhere without design support.

### Sensitive Data Logging Rules

Do not log:
- full raw alert payloads unless explicitly needed and safe
- secrets
- tokens
- credentials
- raw personal/sensitive financial data unless masked and justified

Prefer logging:
- keys
- identifiers
- counts
- statuses
- timings
- summarized state transitions

### Logging Best Practices to Build In

The implementation should naturally follow these practices:
1. Keep messages action-oriented and useful.
2. Log state transitions clearly.
3. Avoid excessive duplicate logs for the same event.
4. Use `INFO` for important lifecycle events.
5. Use `DEBUG` for verbose diagnostics.
6. Use `WARN` for recoverable anomalies.
7. Use `ERROR` for failed operations requiring attention.
8. Ensure exceptions are logged with stack traces only where they provide value.
9. Avoid high-cardinality noisy fields unless necessary.
10. Ensure logs remain readable even in high-volume async workflows.

---

## Error Handling Guidelines

Implementation must clearly handle:
- invalid event payload
- unsupported event type
- missing cache data
- partial query failure
- Redis failure
- downstream summary service failure
- duplicate event scenarios
- retryable vs non-retryable failures

Prefer explicit result modeling over exception-driven chaos.

Also:
- log failures with enough structured detail to diagnose them,
- distinguish business failure from infrastructure failure,
- avoid swallowing exceptions silently in async flows.

---

## Configuration Guidelines

Externalize properties using `@ConfigurationProperties`.

Examples of configurable values:
- delay duration
- Redis TTL
- async executor settings
- summary service URL
- query timeout settings
- retry counts / retry delays
- logging flags
- concurrency limits
- environment-specific logging settings if needed

Do not hardcode operational values.

---

## Logging Configuration Guidelines

Use profile-aware Logback configuration.

The implementation should include guidance or skeleton for:
- `logback-spring.xml`
- Spring profile based appenders
- plain text console appender for `local`
- JSON console appender for `dev|it|uat|prod`

The logging configuration should support:
1. environment name as a field,
2. application name as a field,
3. MDC fields in output,
4. exception stack traces,
5. consistent timestamp format,
6. thread name output,
7. numeric execution-time fields when available.

Do not bury logging config in application code when it belongs in Logback configuration.

---

## Logging Instrumentation Guidance

For timing and structured fields, prefer a reusable instrumentation mechanism rather than manually duplicating stopwatch logic everywhere.

Possible implementation patterns include:
- aspect for timed methods
- helper utility
- decorator/wrapper around external clients
- query executor abstraction that measures time

The final implementation should choose one clean pattern and apply it consistently.

Instrumentation should be easy to extend for:
- query timing
- API timing
- cache timing
- orchestration timing

---

## Observability Guidelines

Use structured logging alongside metrics.

Each important log should include, where available:
- event type
- alert key / alert id
- cwi id
- correlation id
- processing state
- elapsed time
- failure reason

Add metrics where useful:
- events received by type
- delayed items queued
- delayed items processed
- query success/failure counts
- cache hits/misses
- summary request success/failure
- processing latency

If tracing is applicable, include hooks for trace propagation/correlation.

---

## Testing Guidelines

The generated project should include guidance or examples for:

1. unit tests for orchestration logic
2. unit tests for partial-failure handling
3. unit tests for cache update rules
4. tests for event-type routing
5. tests for delay logic abstraction
6. integration tests for Redis interactions
7. client tests for summary-generation API
8. tests for logging-related instrumentation where practical
9. tests for MDC/context propagation in async flows where practical

The AI should generate code in a way that remains testable:
- avoid static utility-heavy design
- prefer interfaces where mocking is useful
- keep orchestration logic isolated

---

## Style Expectations for Generated Code

The AI should generate code that is:

- production-oriented
- readable
- layered
- strongly typed
- not over-engineered
- not pseudo-enterprise boilerplate for everything
- not dependent on field injection
- not dependent on giant god classes

Where possible:
- show records for DTOs,
- show enums for event types/status,
- show configuration properties class,
- show executor configuration,
- show service interfaces and implementations only when useful,
- show a clear orchestration flow,
- show a clean logging approach rather than scattered ad hoc statements.

---

## Implementation Output Expected from AI

When generating the Spring Boot implementation, provide the output in phases:

### Phase 1
Project structure and main classes

### Phase 2
Domain models and DTOs

### Phase 3
Configuration classes
- async config
- virtual thread executor config
- properties config
- logging-aware configuration decisions

### Phase 4
Controller and event dispatch flow

### Phase 5
Delay scheduling components

### Phase 6
Query orchestration components

### Phase 7
Redis cache service

### Phase 8
Summary-generation client

### Phase 9
Error handling / observability / logging support

### Phase 10
Test examples

### Phase 11
Profile-aware `logback-spring.xml` example

---

## Explicit Instruction to AI

Do not produce a giant blob of code immediately.

First generate:
1. package structure,
2. class responsibilities,
3. key interfaces/classes,
4. configuration approach,
5. logging strategy approach.

Then incrementally generate code.

Whenever there is a conflict between:
- simplistic implementation
- and production-grade maintainable implementation,

choose the production-grade maintainable implementation.

Also explain:
- where virtual threads are truly helpful,
- where `@Async` is sufficient,
- where both should be combined,
- where concurrency should still be controlled despite virtual threads,
- how MDC/logging context is propagated across async processing,
- and how timing fields are produced consistently in logs.

Be careful not to create:
- race conditions,
- stale cache writes,
- hidden thread leaks,
- unbounded queue growth,
- inconsistent logging,
- missing async context propagation,
- or hardcoded operational configuration.
