# Engineering Decisions

## 1. SQLite for the initial submission
- **Context:** The deadline is short and local setup should be reliable.
- **Options:** PostgreSQL with Docker Compose, or SQLite.
- **Choice:** SQLite for the initial demo to avoid a separate database service.
- **Trade-off:** Setup is simpler, but PostgreSQL-specific concurrency and scaling behavior is not demonstrated. PostgreSQL should be used before treating this as production-ready.

## 2. Team-scoped server authorization
- **Context:** Users must not access another team's work by changing frontend requests.
- **Options:** Hide controls in the UI only, or check access on the API.
- **Choice:** API endpoints verify the user's team before reading or changing an item.
- **Trade-off:** Checks add backend code, but the permission boundary does not depend on the browser.

## 3. Version-based stale-update protection
- **Context:** A user may edit an item after another user has already changed it.
- **Options:** Last write wins, or require the submitted version to match.
- **Choice:** Updates include a version; mismatches return HTTP 409.
- **Trade-off:** The user may need to reload and retry, but silent overwrites are avoided.

## 4. Idempotency key for create requests
- **Context:** A double-click or network retry could create duplicate work items.
- **Options:** Accept every request, or remember request keys.
- **Choice:** The API stores an optional Idempotency-Key and returns the existing item for repeats.
- **Trade-off:** Keys need a retention policy in production; this demo keeps them indefinitely.

## 5. Explicit workflow transitions
- **Context:** Arbitrary status changes can skip required review.
- **Options:** Allow any status, or define permitted transitions on the server.
- **Choice:** A transition map validates status changes, and only Leads/Admins can approve Awaiting Approval → Resolved.
- **Trade-off:** Adding a status requires updating the transition map and tests.

## Next improvements
Move to PostgreSQL and Docker Compose; use password hashing and signed tokens; add true atomic claim tests against PostgreSQL; use cursor pagination and database indexes tuned to query patterns; add an outbox worker with retries; add stronger role-per-action tests and deployment configuration.
