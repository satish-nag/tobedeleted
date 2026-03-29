# Alert Summary Enrichment System - Requirements and Design Prompt

## Goal

Design a Spring Boot backend application that processes Actimize RCM events and prepares alert data for AI-based analyst summaries.

The purpose of the system is:
- when an analyst works on an alert in Actimize RCM,
- show alert summary + AI narrations,
- so the analyst can analyze the alert faster.

This document is intended for architecture/design reasoning.
The AI assistant should use this document to:
1. understand the requirements,
2. propose multiple design options,
3. compare trade-offs,
4. recommend the best production-grade design.

---

## Business Context

Actimize RCM emits events related to alert lifecycle and analyst assignment.

We want to build a backend system that:
- reacts to alert events,
- collects alert-related data from database queries,
- stores prepared data in Redis cache,
- and when the analyst gets assigned, triggers summary generation through another application.

There are 2 backend applications involved:

1. **This Spring Boot application**
   - receives Actimize events,
   - fetches and prepares alert data,
   - stores/retrieves alert data from Redis,
   - invokes summary-generation application.

2. **Summary-generation application**
   - receives structured alert data,
   - generates alert summary and AI narration for analysts.

---

## Events Received from Actimize RCM

The Spring Boot application receives these events:

### 1. ITEM_CREATED
Triggered whenever a new alert is created.

### 2. ITEM_UPDATED
Triggered whenever an existing alert is updated.

### 3. OWNER_AUTO_ASSIGNED
Triggered whenever a CWI is assigned to an analyst.
This is the point where summary generation should happen.

---

## Functional Requirements

### FR-1: Handle ITEM_CREATED and ITEM_UPDATED
When `ITEM_CREATED` or `ITEM_UPDATED` is received:
1. the request should return immediately,
2. actual processing should happen asynchronously in background,
3. data is not immediately available in database,
4. so processing must wait for **30-40 seconds** before executing queries,
5. after delay, run **7-8 database queries**,
6. map results into a specific structured alert-data model,
7. store the structured alert data in Redis cache,
8. cache TTL should be **2 days**.

### FR-2: Partial failure handling
If one or more of the 7-8 queries fail:
- store whatever data is available,
- set `refetchFlag=true` in the same Redis cache entry,
- so the system knows data may need to be refreshed later.

### FR-3: Handle OWNER_AUTO_ASSIGNED
When `OWNER_AUTO_ASSIGNED` is received:
1. fetch alert data from Redis using alert key,
2. if cache entry is missing OR `refetchFlag=true`,
   then run the full 7-8 queries again,
3. map query results into structured alert-data model,
4. update cache,
5. call summary-generation application with the structured alert data.

### FR-4: Summary generation timing
Summary generation should happen only when analyst assignment occurs (`OWNER_AUTO_ASSIGNED`).

### FR-5: Delay mechanism
For `ITEM_CREATED` and `ITEM_UPDATED`, data is not ready immediately in DB.
The system must:
- wait for about 30-40 seconds,
- use a Java delay queue,
- worker threads should pick items only after delay expires.

### FR-6: Asynchronous processing
All event-processing APIs must be asynchronous in nature:
- HTTP/API response should be returned immediately,
- actual work should continue in background.

---

## Logging and Observability Requirements

### LOG-1: Environment-specific console logging
The application must support different console log formats by environment:

- **local**: plain text human-readable console logs
- **dev**: JSON logs to console
- **it**: JSON logs to console
- **uat**: JSON logs to console
- **prod**: JSON logs to console

The JSON logging format should be suitable for log aggregation/parsing using logstash-compatible structured logs.

### LOG-2: Structured logging
For non-local environments, logs should be printed in structured JSON format and include relevant fields where available, such as:

- timestamp
- log level
- logger name
- thread name
- environment
- application name
- correlation id
- trace id / span id if available
- event type
- alert key / alert id / cwi id
- request id
- processing state
- downstream system name
- outcome / status
- error type / error message
- execution time fields

### LOG-3: Execution timing
The system must capture and log execution time for important operations, especially:

- individual database queries
- external API calls
- event processing orchestration
- cache reads/writes
- summary-generation call

Execution duration should be logged as explicit JSON keys, for example:
- `executionTimeMs`
- `queryExecutionTimeMs`
- `apiExecutionTimeMs`
- `redisExecutionTimeMs`

The design may choose exact field names, but they must be consistent.

### LOG-4: Correlation
Logs should support tracing a request or event end-to-end across async/background processing.
The design must consider propagation of:
- correlation id
- request id
- alert identifiers
- trace metadata where applicable

### LOG-5: Sensitive-data safety
Logs must not expose sensitive data unnecessarily.
The design should call out what should be masked, excluded, or carefully controlled in logs.

### LOG-6: Async and background processing visibility
Because processing happens asynchronously, logs must clearly distinguish:
- request accepted
- delayed/scheduled
- worker started
- query execution
- cache updated
- summary requested
- completion/failure

### LOG-7: Environment-aware operational usability
Plain-text logs in local should be optimized for developer readability.
JSON logs in higher environments should be optimized for observability systems and machine parsing.

---

## Technical Requirements

## Java Requirements
1. Use **Java 21**
2. Use **virtual threads**
3. Use Java best practices
4. Use modern Java features wherever applicable

## Spring Boot Requirements
1. Use Spring Boot asynchronous processing (`@Async`) where applicable
2. Externalize properties
3. Prefer constructor injection
4. Follow Spring Boot best practices

---

## Assumptions

1. Redis is available and can store alert-data payloads for 2 days.
2. Event payload contains enough identifiers to uniquely locate alert/CWI.
3. Multiple events for same alert may arrive close together.
4. Multiple application instances/pods may be running concurrently.
5. Duplicate events are possible.
6. Summary-generation application is an external downstream service.
7. Query execution may partially fail.
8. We want production-grade design, not only happy-path design.
9. The application may run in multiple Kubernetes pods.
10. In-memory delay queues are not automatically shared across pods.

---

## Important Non-Functional Concerns

The design must explicitly address the following:

### NFR-1: Concurrency
- Multiple events for same alert can arrive concurrently
- `ITEM_UPDATED` and `OWNER_AUTO_ASSIGNED` may overlap
- avoid stale cache updates
- avoid duplicate summary generation if possible

### NFR-2: Idempotency
- duplicate event delivery should not corrupt state
- repeated processing for same event should be safe

### NFR-3: Scalability
- system should support multiple alerts/events in parallel
- should work across multiple pods/instances

### NFR-4: Reliability
- temporary DB/query failures should not break overall flow
- partial data handling should be safe
- retries should be considered where appropriate

### NFR-5: Observability
Design should include:
- structured logging,
- correlation IDs / request IDs / alert IDs,
- metrics,
- error handling,
- tracing considerations,
- execution-time logging for important operations.

### NFR-6: Performance
- event receiver should respond quickly
- background processing should be efficient
- virtual threads should be used appropriately
- database and Redis load should be controlled

### NFR-7: Operability
- logs should be useful for debugging production incidents
- async flows should be diagnosable
- failures should be distinguishable as retryable vs non-retryable
- environment-specific behavior should remain easy to operate

---

## Data / Cache Requirements

The Redis entry should contain something like:

- alertKey
- alertData (structured data built from 7-8 query responses)
- refetchFlag
- lastUpdatedTime
- sourceEventType
- optional version or sequence info
- optional summaryGenerationStatus

The design should consider whether versioning is needed to avoid stale updates.

---

## Required Design Questions for AI

When responding, the AI must do the following:

### 1. Propose at least 3 design options
For example:
- Option A: In-memory delay queue + async workers + Redis cache
- Option B: Persistent delayed job model / scheduler-based approach
- Option C: Event-state orchestration with Redis coordination

The AI may propose different options if better.

### 2. Compare the options
For each option, evaluate:
- simplicity
- reliability
- scalability
- failure handling
- multi-pod suitability
- complexity
- operational risk

### 3. Identify hidden edge cases
The AI should explicitly reason about:
- duplicate events
- overlapping events for same alert
- alert updated while delayed task is waiting
- OWNER_AUTO_ASSIGNED before cache is ready
- partial query failures
- stale cache overwrite
- downstream summary call failure
- app restart while delayed items are in memory
- limitations of in-memory delay queue in multi-pod deployment
- loss of logging context across async boundaries
- high-cardinality logging risk
- accidental sensitive-data logging

### 4. Recommend one final design
The final design should be production-grade and clearly justified.

### 5. Provide component-level architecture
The AI should identify major components such as:
- event controller
- event dispatcher
- delay queue manager
- worker processor
- query orchestration service
- cache service
- summary orchestration service
- retry / error handling strategy
- observability hooks
- logging/timing support components

### 6. Provide sequence flows
The AI should explain step-by-step flow for:
- ITEM_CREATED
- ITEM_UPDATED
- OWNER_AUTO_ASSIGNED

### 7. Explain concurrency strategy
The AI should recommend how to handle:
- same alert updated multiple times,
- deduplication,
- stale writes,
- per-alert locking or versioning if needed,
- multi-pod coordination strategy.

### 8. Recommend best use of virtual threads and @Async
The AI should clarify:
- where virtual threads help,
- whether `@Async` should delegate to virtual-thread-based executor,
- whether delay queue workers should use virtual threads,
- how to avoid unnecessary thread-pool bottlenecks.

### 9. Recommend a logging strategy
The AI should explain:
- how to implement plain text in local and JSON in non-local environments,
- how to keep logging consistent across async boundaries,
- how to capture execution timings cleanly,
- how to avoid duplicate or noisy logs,
- what should and should not be logged.

---

## Output Format Expected from AI

The AI should respond in the following structure:

1. Executive summary
2. Restatement of requirements
3. Design options
4. Comparison table
5. Hidden edge cases / failure modes
6. Recommended design
7. Component diagram in text form
8. Sequence flow for each event
9. Concurrency and idempotency strategy
10. Cache design
11. Retry / refetch strategy
12. Logging and observability strategy
13. Virtual thread and @Async usage
14. Risks and mitigations
15. Final recommendation

---

## Explicit Instruction to AI

Do not jump directly to code.

First perform deep system-design reasoning.
Challenge the requirements where needed.
Call out risks, missing assumptions, and trade-offs.
Prefer production-grade design over simplistic demo-only design.

Be especially careful about:
- multi-pod deployments,
- in-memory delay queue limitations,
- stale data overwrites,
- duplicate event handling,
- partial failures,
- cache consistency,
- summary generation correctness,
- logging context propagation across async boundaries,
- and production-safe structured logging.
