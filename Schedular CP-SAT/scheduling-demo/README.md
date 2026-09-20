# Scheduling Demo — Interview-Ready CP-SAT Scheduler

Simplified replica of the Smart Scheduler's core logic.

## Files

| File | Purpose |
|------|---------|
| `models.py` | Data classes: Task, Crew, AvailabilityWindow, ScheduledTask, ScheduleResult |
| `mapper.py` | Task-crew eligibility: capability match + availability overlap |
| `solver.py` | CP-SAT model: variables, constraints, objective, solution extraction |
| `api.py` | FastAPI layer: request/response models + POST endpoint |
| `main.py` | Sample problem + pretty-printed output (runs without the API) |

---

## How to read this code (chronological order)

Read the files in this order. Each step builds on the previous one.

### Step 1: `models.py` — understand the data

Start here. These are plain dataclasses — no logic, just structure.

```
Task
├── task_id        unique name ("T1")
├── duration       how long the job takes in minutes (60)
├── priority       1 = most important, higher = less important
├── required_capabilities   what skills are needed (["electrical"])
└── due_by         optional deadline in absolute minutes from midnight

Crew
├── crew_id        unique name ("C1")
├── capabilities   what skills this crew has (["electrical", "plumbing"])
└── availability   list of time windows they can work
                   each window = { start: 480, end: 1020 }  (08:00–17:00)
```

Time is tracked as **absolute minutes from midnight**: `480 = 08:00`, `720 = 12:00`, `1020 = 17:00`. This avoids datetime complexity — the real scheduler does this too (minutes from base_date across multi-day horizons).

Two output models: `ScheduledTask` (task + crew + start/end) and `ScheduleResult` (list of scheduled + list of unscheduled task IDs).

### Step 2: `mapper.py` — which crews can do which tasks?

Before solving, we filter down which crews are even eligible for each task. Two checks:

1. **Capability match** — every capability the task requires must be in the crew's capability list. A task needing `["electrical"]` won't be assigned to a crew with only `["plumbing"]`.

2. **Availability overlap** — at least one of the crew's time windows must be long enough to fit the task's duration. A 120-minute task can't go to a crew with only a 60-minute window.

Output: a dict like `{"T1": ["C1", "C3"], "T2": ["C2", "C3"], ...}`. This becomes the set of boolean variables the solver creates — it only creates `assign[T1, C1]` and `assign[T1, C3]`, not `assign[T1, C2]`. This is called **sparse assignment** and keeps the model small.

### Step 3: `solver.py` — the CP-SAT core (read top to bottom)

This is the heart. It has 6 clearly labeled sections:

**Section 1 — Mapping** (line ~23): Calls `generate_task_crew_mappings()` from step 2.

**Section 2 — Decision variables** (line ~30): For each task, creates:
- `start_var[t]` — IntVar in range `[0, horizon - duration]`. The solver picks the start time.
- `end_var[t]` — IntVar linked by `end = start + duration`.
- `assign_var[t, c]` — BoolVar for each eligible crew. Solver picks 0 or 1.
- `scheduled_var[t]` — BoolVar. 1 if any crew is assigned, 0 if the task is skipped.
- `interval_var[t, c]` — **Optional** IntervalVar. Only "exists" when `assign[t,c] == 1`. This is what makes `AddNoOverlap` work — it ignores intervals for crews the task isn't assigned to.

The linking logic: `scheduled == 1` iff exactly one `assign[t, c] == 1`. If no crew is eligible, `scheduled` is forced to 0.

**Section 3 — Constraints** (line ~65):

- **3a. Crew availability**: If task T is assigned to crew C, then T's `[start, end]` must fall inside at least one of C's availability windows. Uses `only_enforce_if` — the constraint only activates when the assignment bool is true.

- **3b. No overlap**: For each crew, collect all optional intervals assigned to that crew and call `model.add_no_overlap(...)`. The solver guarantees no two tasks on the same crew overlap in time. This is a single built-in constraint — OR-Tools handles the combinatorics.

- **3c. Due dates**: If a task has `due_by`, then `end <= due_by` — but only enforced when `scheduled == 1`. If the solver can't meet the deadline, it may choose to leave the task unscheduled rather than violate the constraint.

**Section 4 — Objective** (line ~100): `Maximize Σ (weight × scheduled[t])`. Weight = `10,000,000 // priority`. P1 = 10M, P2 = 5M, P3 = 3.3M. The solver will sacrifice lower-priority tasks to fit higher-priority ones.

**Section 5 — Solve** (line ~107): `solver.solve(model)` with a timeout. Returns OPTIMAL, FEASIBLE, or INFEASIBLE.

**Section 6 — Extract results** (line ~112): Loop through tasks. If `scheduled == 1`, find which crew's assign var is 1, read start/end values. Otherwise add to unscheduled list.

### Step 4: `api.py` — how requests flow in and out

The FastAPI layer mirrors the real scheduler's REST API:

1. Client sends `POST /v1/schedules` with JSON body containing tasks and crews
2. Pydantic validates and deserializes (camelCase aliases match the real API contract)
3. Convert request models → internal dataclasses
4. Call `solve()` from step 3
5. Convert result → response JSON with human-readable time displays
6. Return to client

### Step 5: `main.py` — see it all in action

Creates 5 tasks and 3 crews with various capabilities and availability, calls the solver, prints the resulting schedule. Run this to verify everything works.

---

## How it works (the 4-step pattern)

```
Input (tasks + crews)
  │
  ▼
1. MAPPING    — which crews CAN do which tasks? (capabilities + availability)
  │
  ▼
2. VARIABLES  — for each task: start_time, end_time, assigned_crew (bool per eligible crew)
  │
  ▼
3. CONSTRAINTS
   ├─ crew availability: task must fit inside a crew's work window
   ├─ no overlap: two tasks on the same crew cannot overlap in time
   └─ due dates: task must finish before its deadline
  │
  ▼
4. OBJECTIVE  — maximise Σ (priority_weight × scheduled)
  │
  ▼
Output: which crew does what, when
```

---

## API usage

### Start the server

```bash
pip install ortools fastapi uvicorn
uvicorn api:app --reload --port 8080
```

### Sample request

```bash
curl -X POST http://localhost:8080/v1/schedules \
  -H "Content-Type: application/json" \
  -d '{
  "tasks": [
    {
      "taskId": "T1",
      "estimatedDuration": 60,
      "priority": 1,
      "requiredCapabilities": ["electrical"]
    },
    {
      "taskId": "T2",
      "estimatedDuration": 90,
      "priority": 2,
      "requiredCapabilities": ["plumbing"]
    },
    {
      "taskId": "T3",
      "estimatedDuration": 45,
      "priority": 1,
      "requiredCapabilities": ["electrical"]
    },
    {
      "taskId": "T4",
      "estimatedDuration": 120,
      "priority": 3,
      "requiredCapabilities": ["plumbing", "electrical"]
    },
    {
      "taskId": "T5",
      "estimatedDuration": 30,
      "priority": 2,
      "requiredCapabilities": ["electrical"],
      "dueBy": 720
    }
  ],
  "crews": [
    {
      "crewId": "C1",
      "capabilities": ["electrical"],
      "availability": [{"start": 480, "end": 1020}]
    },
    {
      "crewId": "C2",
      "capabilities": ["plumbing"],
      "availability": [{"start": 540, "end": 900}]
    },
    {
      "crewId": "C3",
      "capabilities": ["electrical", "plumbing"],
      "availability": [
        {"start": 480, "end": 720},
        {"start": 780, "end": 1020}
      ]
    }
  ]
}'
```

### Sample response

```json
{
  "scheduled": [
    {
      "taskId": "T5",
      "crewId": "C1",
      "start": 480,
      "end": 510,
      "startDisplay": "08:00",
      "endDisplay": "08:30"
    },
    {
      "taskId": "T1",
      "crewId": "C3",
      "start": 480,
      "end": 540,
      "startDisplay": "08:00",
      "endDisplay": "09:00"
    },
    {
      "taskId": "T3",
      "crewId": "C1",
      "start": 510,
      "end": 555,
      "startDisplay": "08:30",
      "endDisplay": "09:15"
    },
    {
      "taskId": "T2",
      "crewId": "C2",
      "start": 540,
      "end": 630,
      "startDisplay": "09:00",
      "endDisplay": "10:30"
    },
    {
      "taskId": "T4",
      "crewId": "C3",
      "start": 540,
      "end": 660,
      "startDisplay": "09:00",
      "endDisplay": "11:00"
    }
  ],
  "unscheduled": [],
  "totalTasks": 5,
  "totalScheduled": 5
}
```

### What the real scheduler adds on top

| This demo | Real Smart Scheduler |
|-----------|---------------------|
| Single day, minutes from midnight | Multi-day (up to 14 days), minutes from base_date |
| Inline solve | Async: API → DB → Airflow DAG → engine pod |
| Hard due dates only | Hard + soft constraints with breach penalties |
| No travel | ESRI travel matrix + depot travel + route reorder |
| Single solve pass | Multi-day decomposition + greedy backfill |
| No locked tasks | Locked tasks pinned to specific crew + time |

---

## Key concepts to explain in an interview

1. **CP-SAT** = Constraint Programming with SAT (boolean satisfiability). You define variables, constraints, and an objective — the solver finds the best feasible assignment.

2. **Decision variables**: `start[t]` (IntVar), `assign[t,c]` (BoolVar), `scheduled[t]` (BoolVar). The solver picks values for these.

3. **Optional intervals**: `IntervalVar` that only "exists" when `assign[t,c] == 1`. This lets `AddNoOverlap` ignore tasks not assigned to that crew.

4. **Priority weighting**: `weight = 10_000_000 // priority`. P1 tasks are worth 10M, P2 worth 5M — the solver will drop a P3 before a P1.

5. **`only_enforce_if`**: conditional constraints — "this rule only applies when this bool is true". Used everywhere to tie constraints to assignment decisions.

6. **Sparse assignment**: We don't create a variable for every (task, crew) pair — only for eligible ones. This keeps the model small and solvable fast.

## Run it (no API)

```bash
pip install ortools
python main.py
```
