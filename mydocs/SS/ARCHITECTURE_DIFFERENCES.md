# Architecture Differences: Current Codebase vs Target Architecture

This document identifies the gaps between the **current codebase** and the **target architecture** described in `docs/ARCHITECTURE.md`. Each difference includes a plain-language impact explanation and concrete examples.

---

## How the API and Engine Work Together Today

Before diving into the differences, here's how the two current services relate to each other.

### The Restaurant Analogy

Think of the system as a restaurant:

- **API** (`scheduling-api`, port 8000) = **The Front Desk / Receptionist**
  - This is what the outside world talks to. Clients (like a Brightly web app) send requests HERE.
  - It validates the request — "Is this a properly formatted order?"
  - It does NOT do any actual scheduling work itself.

- **Engine** (`scheduling-engine`, port 8001) = **The Back Kitchen / The Chef**
  - This is where the actual math happens (OR-Tools solver, constraint programming).
  - The outside world never talks to this directly.
  - It only knows how to take tasks + crews and produce an optimized schedule.

### How They're Connected

They're connected via **HTTP calls**. The API calls the Engine over the network, like a receptionist phoning the kitchen.

The glue is in `scheduling-api/src/app/services/engine_client.py` — an HTTP client (`EngineClient`) inside the API that makes calls to `http://localhost:8001` (configured as `ENGINE_BASE_URL`). It uses `httpx.AsyncClient` with timeouts, retries, and a circuit breaker pattern.

### Step-by-Step Request Flow

```
1. CLIENT sends POST /api/v1/schedules to API (:8000)
         |
         v
2. API validates the request (Pydantic model checks)
         |
         v
3. API's EngineClient makes HTTP POST to Engine (:8001)
   at "/api/scheduler/schedule" with the full payload
         |
         v
4. ENGINE receives it, returns 202 + scheduleId immediately
   (starts solving in a background thread)
         |
         v
5. CLIENT polls API:  GET /api/v1/schedules/{id}/status
         |
         v
6. API's EngineClient makes HTTP GET to Engine
   at "/api/scheduler/status/{id}"
         |
         v
7. ENGINE returns current status (PENDING, PROCESSING, COMPLETED, FAILED)
         |
         v
8. When status is COMPLETED, client fetches result via:
   GET /api/v1/schedules/{id}/result  ->  API  ->  Engine  ->  back to client
```

**In short:** The API is a middleman. It never does scheduling — it validates requests, forwards them to the Engine via HTTP, and relays the responses back to the client. The Engine does all the heavy lifting (mapping tasks to crews, building the constraint model, running the OR-Tools solver).

### Why This Design Is Problematic

Every single client action results in **two HTTP hops** — the client calls the API, and the API turns around and calls the Engine. The API adds almost no value in the middle; it's like calling a receptionist who puts you on hold to phone the chef every single time.

The two-service HTTP pattern was likely built anticipating the target architecture (where the API and Engine would be separately deployable units). But the implementation stopped halfway: they're separate services, yet still tightly coupled via synchronous HTTP calls. This gives the **complexity** of two services without the **benefits** (independent scaling, failure isolation).

**There are two cleaner alternatives:**

1. **Single service (simplest):** Merge the API into the Engine — one service handles validation, solving, and status. The Engine already has all the endpoints. Eliminates the redundant middleman entirely.

2. **Database-connected services (what ARCHITECTURE.md describes):** Keep them separate but communicate via the database, NOT HTTP. The `request/status` service writes the payload to RDS and triggers the Engine. The Engine reads input from the database and writes results to it. The `request/status` service reads status/results from the database. **The API and Engine never talk to each other directly.** This matters when you need multiple engine instances, auto-scaling, or failure recovery.

```
Option A — Single service (simplest):

  Client  -->  Engine (one service)
               - Validates request
               - Solves schedule
               - Returns status/results directly

Option B — Database as connector (ARCHITECTURE.md target):

  Client  -->  request/status service
                  |
                  |  writes payload to DATABASE
                  |  kicks off Engine as ECS task
                  |
               Database (RDS)
                  |
                  |  Engine reads input from DB
                  |  Engine writes result to DB
                  |
  Client  -->  request/status service
                  |  reads status/result from DATABASE
                  |  (never calls Engine over HTTP)
```

The current two-service-over-HTTP approach is the **worst of both worlds**: the operational complexity of two services with none of the decoupling benefits.

### Key Files

| File | Role |
|------|------|
| `scheduling-api/src/app/services/engine_client.py` | HTTP client that connects API to Engine (the "phone line") |
| `scheduling-api/src/app/api/v1/endpoints/scheduling.py` | API endpoints that receive client requests and call EngineClient |
| `scheduling-api/src/app/services/scheduling_service.py` | Service layer that orchestrates the API-side logic |
| `scheduling-engine/src/app/api/endpoints/scheduler.py` | Engine endpoints that receive requests from the API |

---

## Difference 1: Service Decomposition — 2 Services vs 3 Microservices

### What's Different

| Aspect | Current Codebase | Target Architecture (ARCHITECTURE.md) |
|--------|-----------------|--------------------------------------|
| Services | 2 services: `scheduling-api` (gateway) + `scheduling-engine` (does everything) | 3 microservices: `request/status` (job management) + `scheduling/engine` (solver only) + `monitor` (health & retries) |
| Engine role | Receives HTTP requests, tracks status, runs solver, logs audit events, returns results | Only reads input from database, runs solver, writes output to database |
| Monitor | Does not exist | Background service that watches for stalled/failed jobs and retries them |

### Impact in Plain Terms

Think of the current system like a **single restaurant worker** who takes orders, cooks food, serves tables, AND cleans up. If that worker gets overwhelmed cooking a complex dish, nobody is taking new orders or checking on tables. The target architecture splits this into a **host** (takes orders, tracks table status), a **chef** (only cooks), and a **manager** (watches for problems and fixes them). Each person focuses on one job and can be replaced independently.

### Examples

**Example 1 — Engine overload:**
Currently, the engine (in `scheduling-engine/src/app/api/endpoints/scheduler.py`) handles request intake AND solving. If the solver is running a heavy 6000-task optimization, the same process is also responsible for responding to status-check requests. Under the target architecture, status checks go to the separate `request/status` service, so they respond instantly regardless of solver load.

**Example 2 — Missing monitor service:**
If the engine crashes mid-solve (e.g., out of memory), the current system has no way to detect this — the job stays in "PROCESSING" forever. Under the target architecture, the `monitor` service polls the database, notices the job has been "in progress" for too long, checks ECS task health, and automatically retries with exponential backoff.

### Key Files Affected
- `scheduling-engine/src/app/api/endpoints/scheduler.py` — currently handles both request intake and scheduling
- `scheduling-api/src/app/services/scheduling_service.py` — would need to become the `request/status` service
- **New service needed:** `monitor/` — entirely new codebase

---

## Difference 2: State Management — In-Memory Dictionaries vs Database-Backed

### What's Different

| Aspect | Current Codebase | Target Architecture |
|--------|-----------------|---------------------|
| Primary state store | Python dictionaries in `StatusTrackerService` (`job_status_tracker = {}`, `job_results = {}`) | Amazon RDS (PostgreSQL) |
| Persistence | Lost on restart/crash | Survives restarts, shared across instances |
| Multi-instance support | No — each instance has its own in-memory state | Yes — all instances read/write the same database |

### Impact in Plain Terms

Imagine writing important notes on a **whiteboard** (in-memory) vs in a **shared Google Doc** (database). If someone erases the whiteboard (server restarts), everything is gone. If you have two whiteboards in different rooms (two engine instances), they can't see each other's notes. A shared Google Doc solves both problems — everyone reads the same data, and it survives if someone's computer crashes.

### Examples

**Example 1 — Server restart loses all jobs:**
In the current code (`scheduling-engine/src/app/services/status_tracker.py`, line 33-34), state is stored as:
```python
job_status_tracker = {}  # Lost on restart
job_results = {}         # Lost on restart
```
If the engine pod restarts while 5 jobs are processing, all 5 jobs vanish — clients polling for status get 404 errors with no way to recover. Under the target architecture, all state is in RDS, so after restart the engine can resume where it left off.

**Example 2 — Cannot scale horizontally:**
If you run 2 engine instances to handle more load, Instance A processes Job #1 and stores the result in its local `job_results` dict. When the client polls for Job #1's result, the load balancer might route the request to Instance B, which has no knowledge of Job #1. Under the target architecture, both instances read/write to the same RDS database, so any instance can serve any status request.

### Key Files Affected
- `scheduling-engine/src/app/services/status_tracker.py` — lines 33-34: in-memory dicts must be replaced with DB operations
- `scheduling-engine/src/app/models/audit_models.py` — `ScheduleStatusTracker` model needs `request_payload` and `response_payload` columns

---

## Difference 3: Database Schema — Missing Critical Columns

### What's Different

The `schedule_status_tracker` table in the current code is missing columns required by the architecture:

| Column | In Architecture.md | In Current Code | Purpose |
|--------|-------------------|-----------------|---------|
| `request_id` | Yes (VARCHAR 50) | **Missing** | Client-provided correlation ID |
| `scheduling_engine_task_id` | Yes (VARCHAR 50) | **Missing** | ECS task ID for monitoring |
| `request_payload` | Yes (JSONB) | **Missing** | Full input payload stored in DB |
| `response_payload` | Yes (JSONB) | **Missing** | Full output payload stored in DB |

The current code has extra columns (`client_name`, `total_tasks`, `total_crews`, etc.) that aren't in the architecture.

### Impact in Plain Terms

Think of a **package tracking system**. The current database is like a tracking page that only shows "In Transit" or "Delivered" — but doesn't store what's actually in the package or the delivery receipt. The target architecture stores everything: the original order (`request_payload`), the delivery details (`response_payload`), the truck ID (`scheduling_engine_task_id`), and the customer's order number (`request_id`). Without these fields, you can't recover from failures, debug issues, or let multiple services coordinate.

### Examples

**Example 1 — No `request_payload` column:**
In the target architecture, the engine reads its input from `schedule_status_tracker.request_payload` in the database. Currently this column doesn't exist, so the engine can only receive input via HTTP POST body. If the engine crashes mid-processing, the input is lost and cannot be re-read from the database for a retry. Adding this column enables the monitor service to retry failed jobs by simply spawning a new engine task that reads the same payload.

**Example 2 — No `scheduling_engine_task_id` column:**
When the `request/status` service kicks off an ECS task, it needs to store the ECS task ID so the `monitor` service can check whether that task is still running or has crashed. Without this column, there's no way to correlate a database job record with its running container — making monitoring and retry impossible.

### Key Files Affected
- `scheduling-engine/src/app/models/audit_models.py` — `ScheduleStatusTracker` class (line 13-60)
- Database migration scripts (need to be created)

---

## Difference 4: Data Flow — HTTP-Based vs Database-Driven

### What's Different

| Step | Current Flow | Target Flow |
|------|-------------|-------------|
| Client submits | API Gateway receives request, forwards full payload via HTTP POST to engine | `request/status` stores payload in RDS, kicks off ECS task |
| Engine receives input | From HTTP request body | From database (`request_payload` column) |
| Engine writes results | To in-memory dict (`job_results`) | To database (`response_payload` column) |
| Client polls status | API polls engine via HTTP GET | `request/status` reads directly from RDS |

### Impact in Plain Terms

Currently the system works like a **phone call** — the API calls the engine directly, hands it the work, and waits. If the call drops (engine crashes), everything is lost. The target architecture works like an **email system** — the API writes the job to a shared mailbox (database), and the engine picks it up from there. If the engine crashes, the email is still in the mailbox and another engine can pick it up.

### Examples

**Example 1 — Current: Direct HTTP payload transfer:**
In `scheduling-engine/src/app/api/endpoints/scheduler.py` (line 470), the engine receives the full scheduling request directly:
```python
async def create_schedule(request: ScheduleRequest, background_tasks: BackgroundTasks):
```
If this request contains 6000 tasks and the engine crashes after receiving it but before completing, the entire payload is lost. Under the target architecture, the `request/status` service first writes the payload to RDS, then triggers the engine. The payload survives any engine failure.

**Example 2 — Status polling chain:**
Currently, when a client checks job status: `Client -> API (:8000) -> HTTP GET -> Engine (:8001) -> in-memory dict -> response chain back`. If the engine is under heavy solver load, even this simple status check is slow because it shares the same process. Under the target architecture: `Client -> request/status -> SQL query to RDS -> immediate response`. The status check never touches the engine at all.

### Key Files Affected
- `scheduling-engine/src/app/api/endpoints/scheduler.py` — `create_schedule` endpoint needs restructuring
- `scheduling-api/src/app/services/engine_client.py` — HTTP client would be replaced by DB write + ECS task trigger

---

## Difference 5: Redis Dependency — Present vs Removed

### What's Different

| Aspect | Current Codebase | Target Architecture |
|--------|-----------------|---------------------|
| Redis usage | Used for audit event storage (configurable) | Not mentioned — all storage is RDS |
| Configuration | 17+ Redis config settings in `config.py` (host, port, SSL, TTL, etc.) | No Redis config |
| Startup/shutdown | Redis connection managed in `main.py` lifespan | No Redis lifecycle management |

### Impact in Plain Terms

Think of Redis like a **secondary notebook** that the system keeps alongside its main filing cabinet (PostgreSQL). Having two places to store things means two things to maintain, two things that can break, and confusion about which one has the latest data. The target architecture simplifies this to just one: the main filing cabinet (RDS). Fewer moving parts means fewer things that can go wrong.

### Examples

**Example 1 — Extra operational overhead:**
Currently, deploying the engine requires setting up both PostgreSQL AND Redis (see `scheduling-engine/src/app/core/config.py`, lines 62-78: `REDIS_HOST`, `REDIS_PORT`, `REDIS_SSL`, etc.). If Redis goes down, the audit service silently fails. Under the target architecture, there's only one data store (RDS) to provision, monitor, and maintain.

**Example 2 — Data inconsistency risk:**
When audit events are written to Redis (with 30-day TTL) and status is tracked in PostgreSQL, there's a window where one store has data the other doesn't. For example, Redis audit entries expire after 30 days, but the PostgreSQL `schedule_audit_log` entries persist forever. A debugging investigation that spans more than 30 days would find incomplete audit trails in Redis. Consolidating to RDS eliminates this inconsistency.

### Key Files Affected
- `scheduling-engine/src/app/core/config.py` — lines 62-78: Redis settings to remove
- `scheduling-engine/src/app/main.py` — lines 18, 78-80: Redis import and shutdown
- `scheduling-engine/src/app/core/redis_client.py` — entire file to remove

---

## Difference 6: Authentication & Authorization — None vs Multi-Layer Security

### What's Different

| Aspect | Current Codebase | Target Architecture |
|--------|-----------------|---------------------|
| Authentication | None — open access | AWS Lambda Authorizer with JWT tokens / API keys |
| Authorization | None | Role-Based Access Control (RBAC) |
| CORS | `allow_origins=["*"]` (accept everything) | Configured per-environment |
| Network security | None | VPC isolation, security groups, WAF |

### Impact in Plain Terms

The current system is like a **building with no locks** — anyone who knows the address can walk in and submit scheduling requests or read other people's results. The target architecture adds a **security guard** (Lambda Authorizer) who checks your ID card (JWT token) at the door, a **receptionist** who makes sure you only access areas you're authorized for (RBAC), and **security cameras + alarm system** (WAF) that detect break-in attempts.

### Examples

**Example 1 — Open CORS allows any website to call the API:**
In `scheduling-engine/src/app/main.py` (lines 92-98):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For POC only, restrict in production
)
```
Any website in the world can make requests to this API. A malicious script on a random webpage could submit thousands of scheduling requests, overloading the system. The target architecture's Lambda Authorizer would reject all requests without a valid JWT token.

**Example 2 — No RBAC means anyone can see anyone's results:**
Currently, any client that knows a `schedule_id` can call `GET /api/scheduler/result/{schedule_id}` and retrieve the full scheduling output — including task locations, crew assignments, and due dates. There's no check whether the requesting client owns that schedule. Under the target architecture, RBAC ensures Client A can only access Client A's schedules.

### Key Files Affected
- `scheduling-engine/src/app/main.py` — CORS configuration
- `scheduling-api/src/app/main.py` — add auth middleware
- **New:** AWS Lambda Authorizer function, IAM roles, WAF rules

---

## Difference 7: Container Orchestration — Docker Only vs Full ECS

### What's Different

| Aspect | Current Codebase | Target Architecture |
|--------|-----------------|---------------------|
| Deployment | Dockerfile exists, manual `docker run` | Amazon ECS with auto-scaling |
| Scaling | Manual — run more containers yourself | Automatic — ECS scales engine instances based on demand |
| Image management | Local builds | Amazon ECR with vulnerability scanning and versioning |
| Idle behavior | Always running (consuming resources) | Scales to 0 when no jobs (saves cost) |

### Impact in Plain Terms

The current setup is like owning a **single delivery truck** that you drive yourself. If demand spikes (50 scheduling requests at once), your one truck can't handle it. If there's no demand, the truck sits in the parking lot burning insurance costs. The target architecture is like using a **delivery fleet service** (ECS) — they automatically add trucks when demand spikes and remove them when it's quiet, and you only pay for what you use.

### Examples

**Example 1 — Cannot handle 50 concurrent requests:**
The architecture requires support for 50 concurrent scheduling requests. The current engine is a single FastAPI process using `BackgroundTasks`. Processing 50 concurrent 6000-task schedules in one process would exhaust memory and CPU. With ECS, each request can spin up its own container, running 50 solvers in parallel on separate resources.

**Example 2 — Paying for idle time:**
If the scheduling system receives requests only during business hours (8 AM to 6 PM), the current always-running engine wastes resources during the 14 hours of idle time. ECS with scale-to-zero means the engine containers shut down when there are no jobs, and new ones spin up within seconds when a request arrives — reducing cloud costs by up to 60%.

### Key Files Affected
- `scheduling-engine/Dockerfile` — may need adjustments for ECS task definition
- **New:** ECS task definitions, auto-scaling policies, ECR repository setup

---

## Difference 8: Job Monitoring & Retry — None vs Dedicated Monitor Service

### What's Different

| Aspect | Current Codebase | Target Architecture |
|--------|-----------------|---------------------|
| Failure detection | None — failed jobs stay in "PROCESSING" state forever | `monitor` service polls DB for stalled jobs |
| Retry mechanism | None | Automatic retry with exponential backoff |
| Alerting | None | Alerts for prolonged failures via CloudWatch |

### Impact in Plain Terms

Imagine sending a package through a courier service that has **no tracking or customer support**. If the package gets lost, you'd never know until you wonder why it hasn't arrived. The current system works this way — if a scheduling job fails silently, nobody notices. The target architecture adds a **dedicated tracking team** (monitor service) that constantly watches all packages, notices if one gets stuck, and automatically re-sends it.

### Examples

**Example 1 — Silent solver crash:**
The OR-Tools solver can crash on malformed inputs or memory exhaustion. In the current code, the `_execute_scheduling_background` function (in `scheduler.py`) catches exceptions and writes to the status tracker — but only if the Python process is still alive. If the entire container crashes (OOM kill, hardware failure), the job remains in `PROCESSING` status forever. The monitor service would detect this: "Job X has been IN_PROGRESS for 2 hours (threshold: 1 hour), ECS task is STOPPED — triggering retry #1."

**Example 2 — Transient database failures:**
If the database has a brief outage during result writing, the solver completes successfully but the result is lost. Currently, there's no retry — the client sees "PROCESSING" indefinitely. The monitor would detect this pattern, re-trigger the engine task, and the second attempt would write results successfully.

### Key Files Affected
- **New service:** `monitor/` — polling logic, retry logic, alerting
- `scheduling-engine/src/app/models/audit_models.py` — `scheduling_engine_task_id` column needed for ECS task health checks

---

## Difference 9: Data Retention — None vs Automated Cleanup

### What's Different

| Aspect | Current Codebase | Target Architecture |
|--------|-----------------|---------------------|
| Old data cleanup | None — database grows indefinitely | EventBridge triggers monthly Lambda to delete records older than 90 days |
| In-memory cleanup | `clear_completed_jobs()` exists but must be called manually | Not needed — no in-memory state |
| Redis TTL | 30-day TTL on Redis audit events | N/A — Redis removed |

### Impact in Plain Terms

It's like never cleaning your **email inbox**. After years, you have millions of emails, searches become slow, storage fills up, and your email client starts lagging. The current database has no cleanup mechanism — after months of operation with hundreds of schedules per day, the `schedule_status_tracker` and `schedule_audit_log` tables grow unbounded, slowing down queries and increasing storage costs. The target architecture automatically shreds old documents every month.

### Examples

**Example 1 — Database bloat:**
Each scheduling request stores the full input payload (potentially thousands of tasks with GPS coordinates) and full output payload in the database. At 100 requests per day, each averaging 1 MB of payload data, the database grows by ~3 GB per month. After a year, that's 36 GB of data — most of it historical and never queried. The monthly Lambda cleanup removes records older than 90 days, keeping the database lean (~9 GB max).

**Example 2 — Query performance degradation:**
The `StatusTrackerService.get_status()` method queries `schedule_status_tracker` by `schedule_id`. As the table grows to millions of rows, even indexed queries slow down. The `schedule_audit_log` table grows even faster (multiple audit entries per schedule). Automated retention keeps table sizes bounded, maintaining consistent query performance.

### Key Files Affected
- **New:** AWS EventBridge rule + Lambda function for cleanup
- `scheduling-engine/src/app/services/status_tracker.py` — `clear_completed_jobs()` can be removed once automated retention exists

---

## Difference 10: Environment Variable & Configuration Mismatch (Pre-existing Bug)

### What's Different

The engine's `config.py` defines database settings with one naming convention, but `main.py` uses a different one:

| Setting | `config.py` uses | `main.py` uses |
|---------|-----------------|----------------|
| Database host | `DATABASE_HOST` | `DB_HOST` |
| Database port | `DATABASE_PORT` | `DB_PORT` |
| Database name | `DATABASE_NAME` | `DB_NAME` |
| Database user | `DATABASE_USER` | `DB_USER` |
| Database password | `DATABASE_PASSWORD` | `DB_PASSWORD` |

### Impact in Plain Terms

Imagine two coworkers trying to coordinate a meeting. One writes the room number on a sticky note labeled "MEETING_ROOM", the other looks for a sticky note labeled "ROOM_NUMBER". They're both trying to do the same thing, but using different names means they never find each other's notes. In the code, `config.py` and `main.py` define the same database connection but use different environment variable names — so you have to set BOTH `DATABASE_HOST` AND `DB_HOST` for the system to work properly, which is confusing and error-prone.

### Examples

**Example 1 — Deployment confusion:**
A DevOps engineer reads `config.py` and sets `DATABASE_HOST=prod-db.amazonaws.com` in the environment. The app starts, the `Settings` class loads correctly, but the `asyncpg.create_pool()` in `main.py` reads `DB_HOST` (which is empty), and the database connection fails. The error message says "connection refused" with no hint that the variable name is wrong.

**Example 2 — Audit service works but pool doesn't:**
The `SmartSchedulingAuditService` uses SQLAlchemy with `DATABASE_URL` from `config.py`, which works. But the `asyncpg` pool in `main.py` uses `DB_HOST`/`DB_PORT`/etc., which may not be set. Result: audit logging to the database works fine, but the connection pool that `StatusTrackerService` falls back to doesn't — creating inconsistent behavior that's hard to debug.

### Key Files Affected
- `scheduling-engine/src/app/core/config.py` — lines 48-60
- `scheduling-engine/src/app/main.py` — lines 37-45

---

## Priority Summary

| Priority | Difference | Effort | Risk if Not Addressed |
|----------|-----------|--------|----------------------|
| **P0** | #2 In-memory to RDS state management | Medium | Cannot scale, data loss on restart |
| **P0** | #3 Missing database columns | Low | Blocks service decomposition and monitoring |
| **P0** | #10 Config variable mismatch (bug) | Low | Silent failures in production |
| **P1** | #1 Service decomposition (3 services) | High | Engine overload, no failure recovery |
| **P1** | #4 Data flow (DB-driven) | High | Required for service decomposition |
| **P1** | #8 Monitor service | Medium | No failure detection or retry |
| **P1** | #5 Redis removal | Low | Operational complexity, data inconsistency |
| **P2** | #6 Authentication & authorization | Medium | Security vulnerability |
| **P2** | #7 ECS container orchestration | High | Cannot auto-scale, cost inefficiency |
| **P2** | #9 Data retention | Low | Database bloat over time |
