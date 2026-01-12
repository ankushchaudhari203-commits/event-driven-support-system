> **Note:**  
> This system currently runs as a single FastAPI service with a local database.  
> The architecture is intentionally designed to evolve into a distributed setup
> (e.g., message queues, external services) without changing core business logic.


(https://github.com/ankushchaudhari203-commits/event-driven-support-system/blob/main/app/diagrams/event-driven-architecture.jpg)

## ⚡ Event-Driven Design

This system is built using an **event-driven architecture**, where **events are the source of truth** instead of direct state mutations.

Instead of directly updating a ticket, the system processes **events** such as:

- `MESSAGE_RECEIVED`
- `RESOLVE`

Each event:
- is uniquely identified (`event_id`)
- is processed **exactly once**
- drives a **deterministic state transition**

### 🔁 Why event-driven?
Event-driven systems are resilient to:
- retries
- duplicate messages
- partial failures
- concurrent processing

This project intentionally focuses on these real-world failure scenarios.

### 🧠 How it works (high-level)
1. An event is received by the API
2. A transaction is started
3. Global idempotency is checked (duplicate delivery protection)
4. The related ticket is locked (concurrency safety)
5. Per-ticket idempotency is validated
6. A state transition is applied using a state machine
7. State history is recorded (audit trail)
8. The transaction is committed atomically

If any step fails, the entire operation is rolled back safely.

### 🧱 State Machine
Tickets follow a strict state machine:



OPEN → PROCESSING → RESOLVED

Invalid transitions are rejected to maintain system correctness.

### 🧪 Reliability Guarantees
- **Transactional safety** (no partial writes)
- **Concurrency control** (race-condition safe)
- **Idempotency** (duplicate-safe processing)
- **Auditability** (full event history per ticket)

This mirrors how production-grade backend systems are designed.
