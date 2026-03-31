# Python FastAPI Implementation Prompt - JWT Token Caching and Structured JSON Logging

## Purpose

I have an existing Python application built using **FastAPI** and other supporting Python libraries.

I want help designing and implementing **two requirements** in a production-grade way:

1. **JWT token retrieval, in-memory caching, expiry tracking, and asynchronous refresh**
2. **Structured JSON logging with minimal changes to the existing codebase**

The implementation should be practical, maintainable, and should avoid unnecessary refactoring of unrelated code.

---

## Technology Context

- Language: **Python**
- Framework: **FastAPI**
- Existing app already has:
  - text-based logging
  - tracing implementation
- Existing app likely has:
  - API calls
  - Redis calls
  - DB calls
  - LLM calls
- I want to preserve the current behavior as much as possible and only change what is necessary for these requirements.

---

# Requirement 1: JWT Token Implementation

## Goal

Implement JWT token acquisition and caching inside each pod/process memory.

This JWT token is used for downstream API calls.

---

## Functional Requirements

### JWT-1: Token Retrieval
- Implement JWT token retrieval logic.
- Add a **clear placeholder section** in the code where I can later provide:
  - token endpoint details
  - request payload details
  - headers
  - authentication details
  - response parsing details
  - any other endpoint-specific configuration

Do not hardcode unknown details.
Instead, leave well-marked extension points / TODO placeholders.

### JWT-2: In-Memory Cache Per Pod
- Cache the token in each pod's memory.
- Each pod can maintain its own in-memory token cache.
- No distributed cache is required for the token unless strongly justified.
- The cache should store:
  - access token
  - token expiry timestamp
  - issued time or acquisition time if needed
  - total token lifetime if needed

### JWT-3: Expiry Tracking
- Keep track of token expiry.
- Detect how much token lifetime remains.
- If the remaining lifetime is less than **10% of the total token validity period**, token refresh should be triggered.

Example:
- if total token lifetime is 100 minutes,
- when only 10 minutes remain,
- start refresh flow.

### JWT-4: Asynchronous Refresh
- Token refresh must happen **asynchronously**.
- The purpose is:
  - do not block active request-processing threads
  - continue using current valid token while refresh happens in background
  - replace the cached token once refreshed successfully

### JWT-5: Non-Blocking Behavior
- If a request comes while token still exists and is valid:
  - return/use existing token immediately
- If token is nearing expiry (<10% remaining):
  - trigger asynchronous refresh
  - continue serving requests using current token until new one is available
- If token is fully expired and no valid token is available:
  - the implementation should define the safest fallback behavior
  - example: synchronous refresh only when absolutely necessary

### JWT-6: Concurrency / Thread-Safety
- Multiple concurrent requests may try to access the token.
- Avoid duplicate refresh storms.
- Ensure thread-safe / coroutine-safe access to the in-memory token state.
- Only one refresh should happen at a time per pod if possible.

### JWT-7: Failure Handling
- Handle token refresh failures gracefully.
- If refresh fails but current token is still valid, continue using current token.
- If token is expired and refresh fails, clearly define behavior and error propagation.
- Log refresh failures properly.

---

## Design Expectations for JWT Implementation

When designing JWT token handling, consider the following:

1. thread-safety / async-safety
2. race condition avoidance
3. refresh de-duplication
4. minimal performance overhead
5. suitability for FastAPI async execution model
6. clean separation of concerns
7. easy testability

The design should identify whether to use:
- singleton service
- async lock
- background task
- refresh state flag
- atomic replacement of token object
- any other better mechanism

---

## JWT Output Expected

Provide:

1. recommended design
2. key classes / modules
3. token cache data model
4. token manager flow
5. concurrency strategy
6. refresh strategy
7. fallback behavior when token is expired
8. code skeleton
9. example implementation with placeholder sections clearly marked
10. test strategy

---

# Requirement 2: Structured Logging with JSON Output

## Goal

The application currently uses **text-based logging** and already has tracing implemented.

I need to implement **JSON-based structured logging** with **minimal changes to the existing code**, while preserving current logging information as much as possible.

---

## Functional Requirements

### LOG-1: Replace / Extend Current Logging to JSON
- Implement structured logging in JSON format.
- Keep the solution compatible with existing logging/tracing setup as much as possible.
- Avoid unnecessary large-scale refactoring.

### LOG-2: Minimal Code Changes
- Make all reasonable effort to avoid changing a lot of business logic.
- Prefer changes that are localized to:
  - logging configuration
  - logging utilities
  - decorators
  - middleware
  - instrumentation helpers

### LOG-3: Preserve Existing Logging Information
- Existing logging information should be preserved as much as possible.
- Do not remove useful fields already being logged.
- Existing message content should remain usable.
- The structured logging should enrich current logs rather than destroy them.

### LOG-4: Use Decorators Where Possible
- Logging is a cross-cutting concern.
- Use decorators where practical for reusable timing/logging instrumentation.
- If middleware or other patterns are better in some places, explain why.
- Use the cleanest combination of:
  - decorators
  - middleware
  - helper utilities
  - context variables
  - logging processor/formatter

### LOG-5: Execution Time as JSON Field
Capture and log execution time for important calls as structured JSON keys, including but not limited to:

- inbound API request duration
- Redis action duration
- DB call duration
- external API call duration
- LLM call duration
- any other significant operation

Examples of fields:
- `executionTimeMs`
- `apiExecutionTimeMs`
- `redisExecutionTimeMs`
- `dbExecutionTimeMs`
- `llmExecutionTimeMs`

Exact names can be improved if consistency is maintained.

### LOG-6: Important Business / Context Fields
Include relevant contextual parameters as JSON keys where available, such as:

- `cwiId`
- `alertId`
- correlation id
- request id
- trace id / span id
- operation name
- downstream system
- status
- outcome
- exception type
- error message

The exact field list can be refined, but important identifiers should be preserved.

### LOG-7: Preserve Tracing Compatibility
- Existing tracing implementation must continue to work.
- Trace IDs / span IDs should remain available in logs where possible.
- The new structured logging should integrate well with tracing context.

### LOG-8: Avoid Excessive Logging Noise
- The solution should avoid duplicate or noisy logs.
- Timing and structured context should be added in a clean and reusable way.

---

## Design Expectations for Logging

The implementation should consider and recommend the best approach for:

1. structured logging library choice
2. minimal code-change migration strategy
3. decorator-based timing/logging
4. FastAPI middleware for request-level logging
5. context propagation using `contextvars` if useful
6. trace/log correlation
7. reusable log enrichment
8. exception logging
9. preserving existing message structure
10. safe logging practices for sensitive data

---

## Logging Best-Practice Instructions

Please incorporate relevant best practices naturally into the solution, not just by repeating this list literally.

Examples of best practices to consider:

- keep business code free from repetitive logging boilerplate
- centralize structured log formatting
- use middleware for request lifecycle logging
- use decorators for operation-level timing
- prefer reusable helpers over copy-paste timing code
- preserve backward compatibility where practical
- avoid logging secrets/tokens/raw sensitive payloads
- make logs machine-parseable and human-usable
- ensure logs still work in async code paths
- clearly distinguish info / warning / error cases
- avoid breaking current tracing correlation

---

## Logging Output Expected

Provide:

1. recommended logging design
2. library recommendations
3. migration approach with minimal code changes
4. middleware vs decorator responsibilities
5. example structured log schema
6. example implementation
7. how to preserve existing logging content
8. how to include trace/correlation fields
9. how to add timing fields consistently
10. test strategy

---

# Combined Design Constraints

The final solution for both JWT and logging should:

1. be production-grade
2. fit well into an existing FastAPI codebase
3. minimize intrusive code changes
4. be easy to extend later
5. be testable
6. work correctly in async/concurrent execution
7. avoid unnecessary over-engineering

---

# Explicit Instructions to AI

When responding:

1. Do **not** jump directly into a giant blob of code.
2. First explain the design for both requirements.
3. Clearly identify:
   - modules/files to create or modify
   - where placeholders should be added
   - what can remain unchanged
4. Prefer maintainable, incremental integration into an existing codebase.
5. For JWT, focus heavily on:
   - concurrency control
   - non-blocking refresh
   - token replacement safety
   - refresh de-duplication
6. For structured logging, focus heavily on:
   - minimal code changes
   - preserving existing log information
   - decorator + middleware based implementation
   - timing fields as structured JSON keys
   - tracing compatibility
7. Then provide phased implementation:
   - Phase 1: design and file/module layout
   - Phase 2: JWT token manager skeleton
   - Phase 3: structured logging skeleton
   - Phase 4: middleware/decorators
   - Phase 5: integration examples
   - Phase 6: tests

---

# Preferred Response Structure

The response should be structured as:

1. Executive summary
2. JWT design
3. JWT concurrency and refresh strategy
4. JWT code skeleton
5. Structured logging design
6. Logging migration strategy with minimal code changes
7. Middleware and decorator strategy
8. Example JSON log fields/schema
9. Phased implementation plan
10. Risks / edge cases
11. Test strategy

---

# Placeholder Instruction for JWT Endpoint Details

Wherever endpoint-specific JWT details are needed, add a clearly marked section like:

- `TODO: Add token URL here`
- `TODO: Add auth request payload here`
- `TODO: Add headers here`
- `TODO: Add response parsing logic here`

Do not invent these details unless explicitly necessary for the example.

---

# Important Notes

- Preserve current code behavior as much as possible.
- Do not force a large rewrite.
- Prefer elegant wrappers/adapters around existing code.
- Keep the solution realistic for a production Python/FastAPI application.
