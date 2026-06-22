# Area 6 — Parallelism & Scale (CPU)

Area 5 was about work that **waits** (I/O-bound). This area is about work that
**computes** — number-crunching that pins a CPU core at 100%. The tools are different
(processes, not threads), the constraints are different (the GIL), and the recurring
question is: how do you use all your cores, and when does adding more stop helping?

---

<a id="contents"></a>
## Contents

- [6.1 — "Is this I/O-bound or CPU-bound?" → the decision that changes everything](#6.1)
- [6.2 — "I have 8 cores but my CPU job uses only one" → multiprocessing](#6.2)
- [6.3 — "I added threads to my math loop and it got no faster (or slower)" → the GIL](#6.3)
- [6.4 — "I want multi-core parallelism with the same API as my thread pool" → ProcessPoolExecutor](#6.4)
- [6.5 — "pool.map on 50 million rows ate all my RAM before doing any work" → imap & lazy streaming](#6.5)
- [6.6 — "Parallelising made it SLOWER" → serialization (pickle) cost between processes](#6.6)
- [6.7 — "8 workers but barely faster — they spend all their time on dispatch" → chunksize](#6.7)
- [6.8 — "Every worker copied the same 4 GB array and I ran out of RAM" → shared memory](#6.8)
- [6.9 — "One slow task blocks me from seeing any results until it's done" → as_completed & ordering](#6.9)
- [6.10 — "One bad row crashed the whole 10-hour parallel job" → isolating worker failures](#6.10)
- [6.11 — "Each task reloads the 500 MB model from disk" → per-worker initializer](#6.11)
- [6.12 — "My data doesn't fit on one machine, even with all cores busy" → Dask/Spark](#6.12)

---


<a id="6.1"></a>
## 6.1 — "Is this I/O-bound or CPU-bound?" → the decision that changes everything

### The situation

You have two slow jobs and you want to speed both up:

- **Job A:** fetch 5,000 records from an API (Area 5's example) — 40 minutes, CPU at 2%.
- **Job B:** compute a similarity score between every pair of 5,000 feature vectors —
  40 minutes, **one CPU core pinned at 100%**, the rest idle.

You reach for the same fix on both — say, threads — and Job A speeds up 20×, but Job B
barely changes. Why does the *identical* concurrency tool help one and not the other?

### What's really going on

The two jobs are bottlenecked on completely different resources, and that single
distinction decides which tool works:

- **I/O-bound** (Job A): time is spent **waiting** on something external (network,
  disk, DB). The CPU is idle. Fix = **concurrency** that overlaps the waiting —
  **threads or async** (Area 5). A thread *releases the GIL while it waits*, so others
  run.
- **CPU-bound** (Job B): time is spent **computing** — the CPU is the bottleneck, pinned
  at 100% on one core. Fix = **parallelism** that uses **more cores** —
  **multiprocessing** (6.2). Threads do *not* help, because of the GIL (6.3).

> The **GIL** (Global Interpreter Lock, 6.3) is a lock inside CPython that lets only
> **one thread execute Python bytecode at a time**. So multiple threads can't crunch
> numbers in parallel — they take turns on one core. For *waiting* (I/O) that's fine
> (a waiting thread holds no lock); for *computing* it means threads give no speed-up.

The realisation: **diagnose bound-type first, because it dictates the tool.** Using
threads on CPU-bound work (or processes on I/O-bound work) is the single most common
concurrency mistake — you pick a tool that *cannot* fix your actual bottleneck.

### The move

Before writing any concurrency code, classify the job:

1. **Watch CPU during a normal run.** One core at ~100% → CPU-bound. All cores near
   idle while it's slow → I/O-bound.
2. **Ask what each second is spent on.** "Waiting for a reply/disk" → I/O-bound.
   "Doing arithmetic / transforming data" → CPU-bound.

Then pick: **I/O-bound → threads/async (Area 5). CPU-bound → multiprocessing (6.2).**

### Why it works

The classification works because the GIL makes the two cases behave oppositely under
threads. An I/O-bound thread spends its time *blocked on a system call*, during which it
**releases the GIL**, so other threads run — threads genuinely overlap waiting. A
CPU-bound thread is *executing Python bytecode*, which **holds the GIL**, so other
threads can't run Python simultaneously — they serialise onto one core and you get no
speed-up (sometimes a slowdown from lock contention). Separate **processes** each have
their *own* interpreter and *own* GIL, so they truly run on different cores in
parallel — which is why CPU-bound work needs processes, not threads.

### The code, every line explained

```python
import time, threading, multiprocessing

# --- A CPU-bound function (pure computation, holds the GIL) --------------
def heavy(n):
    total = 0
    for i in range(n):          # tight arithmetic loop = CPU-bound; pins one core
        total += i * i
    return total

# --- Threads do NOT speed up CPU-bound work (GIL) -----------------------
def run_threads():
    threads = [threading.Thread(target=heavy, args=(10_000_000,)) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    # 4 threads, but they TAKE TURNS on one core (GIL) -> ~same time as running
    # the 4 calls one after another. No parallel speed-up.

# --- Processes DO speed it up (each has its own GIL, own core) ----------
def run_processes():
    with multiprocessing.Pool(4) as pool:        # 4 separate OS processes
        results = pool.map(heavy, [10_000_000] * 4)
    # 4 processes run on 4 cores SIMULTANEOUSLY -> ~4x faster (6.2).

# --- The diagnosis table -------------------------------------------------
# symptom while running          bound type     right tool
# -------------------------------------------------------------------------
# slow, CPU ~idle, waiting       I/O-bound      threads / async (Area 5)
# slow, ONE core at 100%         CPU-bound      multiprocessing (6.2)
# slow, ALL cores at 100%        CPU-bound,     better algorithm (6.x) or
#                                already maxed   more machines (6.12)
```

### Impact

- **Picks the tool that can actually work.** Threads on CPU-bound work waste effort for
  zero gain; this diagnosis prevents that classic dead end.
- **Sets the speed-up ceiling.** CPU-bound parallelism is capped at your core count
  (4 cores → ~4×); I/O-bound concurrency is capped by the remote service, not cores.
  Knowing which tells you what's achievable before you code.

### Pros & cons / when NOT to

- **This is diagnosis, not code** — pure upside; the cost is *skipping* it and
  optimising the wrong axis.
- **Mixed jobs exist:** fetch (I/O) then transform (CPU). Profile (Area 2, 2.1) to see
  which dominates; you may thread the fetch stage and multiprocess the transform stage
  (a pipeline, 5.7).
- **"More cores" has limits:** if all cores are already at 100%, parallelism is tapped
  out — you need a better algorithm (6.13) or more machines (6.12), not more processes.

### Where this shows up

- **Real work — data pipelines:** the fetch stage is I/O-bound (threads), the
  parse/transform/featurise stage is CPU-bound (processes) — different fixes per stage.
- **Real work — ML preprocessing:** tokenising/encoding millions of rows or computing
  features is CPU-bound; use processes or vectorise (6.10).
- **Real work — the "why didn't threads help?" surprise:** the moment most engineers
  first meet the GIL is trying to thread a CPU-heavy loop and seeing no speed-up.
- **Pattern mapping (secondary):** no DSA analogue; it's the foundational systems
  decision that determines whether Area 5 (concurrency) or Area 6 (parallelism) applies.
[↑ Back to top](#contents)

---

<a id="6.2"></a>
## 6.2 — "I have 8 cores but my CPU job uses only one" → multiprocessing

### The situation

You confirmed (6.1) your job is CPU-bound: resizing and feature-extracting 100,000
images, one core pinned at 100% for 30 minutes while the other 7 cores sit idle.

```python
features = []
for path in image_paths:               # 100,000 images
    features.append(extract_features(load_image(path)))   # pure CPU, ~18 ms each, ONE core
```

You're paying for an 8-core machine but using 1/8th of it. You want the work spread
across all 8 cores so it finishes in roughly an eighth of the time.

### What's really going on

Python threads can't run CPU work in parallel because of the GIL (6.1/6.3) — only one
thread executes Python bytecode at a time. The way to use multiple cores is multiple
**processes**: each process is a *separate* Python interpreter with its **own GIL** and
its own memory, scheduled by the OS onto a different core. Run 8 worker processes and 8
chunks of the work genuinely compute at the same instant.

> A **process** is an independent running program with its own memory space and its own
> Python interpreter (and GIL). Unlike threads (which share memory within one
> interpreter), processes are isolated — which is exactly what lets them run Python in
> true parallel, but also means data must be **copied** between them (6.6).

The standard tools are `multiprocessing.Pool` and the friendlier
`concurrent.futures.ProcessPoolExecutor` (6.4) — same API shape as the thread pool you
already know (5.2), so "use all cores" is often a one-word change from threads to
processes.

### The move

Spread the work across a pool of worker processes, one per core:

```python
from multiprocessing import Pool

def process_one(path):
    return extract_features(load_image(path))   # the CPU work for ONE item

if __name__ == "__main__":                       # REQUIRED guard (see why below)
    with Pool() as pool:                          # default: one worker per CPU core
        features = pool.map(process_one, image_paths)
```

### Why it works

`Pool()` starts N worker processes (N = your core count by default). `pool.map` splits
`image_paths` into chunks, sends a chunk to each worker, and each worker — being a
separate interpreter with its own GIL on its own core — runs `process_one` on its chunk
**at the same time** as the others. Eight cores doing 1/8th of the work each finishes in
roughly 1/8th the wall-clock time (minus overhead, 6.6). The results are gathered back
and returned in input order, just like the built-in `map`.

The `if __name__ == "__main__":` guard is **mandatory** on Windows/macOS (which start
workers by *spawning* a fresh Python that re-imports your module): without it, each new
worker would re-run your top-level code and recursively spawn more processes — a
fork bomb. The guard ensures the launch code runs only in the main process.

### The code, every line explained

```python
from multiprocessing import Pool
import os

def process_one(path):                    # work for ONE item; must be at MODULE level
    img = load_image(path)                # (so workers can import/pickle it — see 6.6)
    return extract_features(img)          # pure CPU work

if __name__ == "__main__":                # guard: launch code runs ONLY in main process
    paths = list_image_paths()

    with Pool(processes=os.cpu_count()) as pool:   # one worker per core (default if omitted)
        # map: split paths across workers, run in parallel, results in INPUT order
        features = pool.map(process_one, paths)
        # for huge inputs, imap/imap_unordered stream results lazily (6.5) instead of
        # building the whole result list at once.

    save(features)
# Pool is shut down + workers joined on leaving the `with` block.

# --- chunksize: hand each worker a batch, not one item at a time --------
with Pool() as pool:
    features = pool.map(process_one, paths, chunksize=100)
    # chunksize=100: send 100 paths per task instead of 1, cutting per-task overhead
    # (dispatch + pickling). Big win when each item is quick. (Full treatment in 6.7.)

# --- ProcessPoolExecutor: the concurrent.futures equivalent (6.4) -------
from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor() as pool:       # same shape as ThreadPoolExecutor (5.2)
    features = list(pool.map(process_one, paths))
# Switching threads<->processes is often just the class name — but the constraints
# (pickling, no shared memory) differ; see 6.6.
```

### Impact

- **Near-linear speed-up to your core count:** an 8-core machine finishes CPU-bound work
  in roughly 1/8th the time — the 30-minute job becomes ~4 minutes (minus overhead).
- **Uses hardware you're already paying for:** turns a 1/8th-utilised machine into a
  fully-utilised one.
- **Familiar API:** `pool.map` mirrors built-in `map` and the thread pool, so adoption
  is small.

### Pros & cons / when NOT to

**Reach for multiprocessing when:** the work is **CPU-bound** (6.1) and splittable into
independent chunks — featurising, parsing, transforming, simulating, scoring.

**Watch out / when NOT to:**
- **Not for I/O-bound work** — processes have higher overhead than threads and give no
  extra benefit when the bottleneck is waiting; use threads/async (Area 5) there.
- **Data is copied to/from workers** (via pickling, 6.6), not shared. Passing huge
  objects per task can cost more than the computation saved — chunk well (6.7) and avoid
  shipping giant arguments (use shared memory, 6.8, or have workers load their own data).
- **Everything must be picklable** — the function and its arguments are serialised to
  reach the worker. Lambdas, local/nested functions, and open file handles aren't
  picklable; define worker functions at module level (6.6).
- **The `__main__` guard is mandatory** on spawn platforms — omit it and you get
  recursive process spawning.
- **Startup cost is real** — spawning processes takes time; not worth it for a small or
  quick job. Reuse a pool rather than recreating it (and load models once per worker,
  6.11).

### Where this shows up

- **Real work — bulk preprocessing/featurisation:** image resize, text tokenise/encode,
  feature extraction over large datasets before training — the canonical "use all cores"
  job.
- **Real work — parallel scoring/inference on CPU:** running a CPU model over millions of
  rows, split across workers (pairs with batch inference, Area 8).
- **Real work — simulations & numeric sweeps:** independent runs (parameter grids, Monte
  Carlo) farmed out across cores.
- **Pattern mapping (secondary):** the "split into independent chunks, compute in
  parallel, combine" shape is **map-reduce** / divide-and-conquer; the same decomposition
  underlies parallel sorts and many "embarrassingly parallel" problems.
[↑ Back to top](#contents)

---

<a id="6.3"></a>
## 6.3 — "I added threads to my math loop and it got no faster (or slower)" → the GIL

### The situation

You have a CPU-heavy function and you "parallelise" it with threads, expecting your
4-core machine to make it ~4× faster:

```python
import threading
def crunch(n):
    total = 0
    for i in range(n):          # pure arithmetic — CPU-bound
        total += i * i
    return total

threads = [threading.Thread(target=crunch, args=(50_000_000,)) for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
# Expected: ~4x faster than one call. Reality: SAME as running them one-by-one
# (sometimes slightly SLOWER). The 4 cores are not all busy.
```

Four threads, four cores, and yet no speed-up. The same code with *processes* (6.2)
would be ~4× faster. What's stopping the threads?

### What's really going on

CPython has a **GIL — Global Interpreter Lock**: a single lock that a thread must hold
to execute Python bytecode, and **only one thread can hold it at a time**. So even with
4 threads on 4 cores, only **one** is running Python code at any instant — the others
wait for the lock. Your threads take turns on effectively one core, so total compute
time doesn't drop (and lock hand-off overhead can make it slightly worse).

> The **GIL** exists because CPython's memory management (reference counting, Area 2)
> isn't thread-safe without it — the lock makes the interpreter simple and fast for
> single-threaded code, at the cost of blocking multi-core *Python* execution.

The crucial nuance — **why threads still help I/O (Area 5)**: a thread **releases the
GIL while it's blocked waiting** on I/O (a network/disk system call) or while running
certain C extensions. So:

- **I/O-bound threads:** mostly waiting → GIL released → others run → real concurrency. ✅
- **CPU-bound threads:** always executing bytecode → GIL held → others can't run → no
  parallelism. ❌

That single fact explains the whole threads-vs-processes split.

### The move

Don't fight the GIL — route around it based on bound-type:

- **CPU-bound** → use **processes** (6.2/6.4): each has its own GIL, true multi-core.
- **I/O-bound** → **threads/async** are fine (Area 5): the GIL is released during waits.
- **Heavy numeric CPU work** → use **libraries that release the GIL** (NumPy, pandas,
  PyTorch do their heavy loops in C/with the GIL released) — then even threads can
  parallelise *that* part (6.10).

### Why it works

Processes sidestep the GIL entirely because each process has its *own* interpreter and
*own* GIL — there's no shared lock to contend for, so N processes compute on N cores
simultaneously. NumPy-style libraries sidestep it differently: their inner loops run in
compiled C code that **explicitly releases the GIL** while crunching, so the heavy work
isn't bottlenecked by it (and vectorising, 6.10, often beats parallelism anyway). And
the reason you don't need to "fix" the GIL for I/O is that the blocking system call
releases it automatically — the waiting threads aren't holding it.

### The code, every line explained

```python
# --- CPU-bound: threads give NO speed-up (GIL) --------------------------
import threading, multiprocessing, time

def crunch(n):
    return sum(i * i for i in range(n))   # holds the GIL the whole time

# 4 THREADS: take turns on one core -> ~same as serial
ts = [threading.Thread(target=crunch, args=(50_000_000,)) for _ in range(4)]
[t.start() for t in ts]; [t.join() for t in ts]      # no parallel gain

# 4 PROCESSES: own GIL each -> ~4x faster on 4 cores
with multiprocessing.Pool(4) as pool:
    pool.map(crunch, [50_000_000] * 4)                # true parallelism (6.2)

# --- I/O-bound: threads DO help (GIL released while waiting) ------------
import requests
def fetch(url):
    return requests.get(url, timeout=10)  # while waiting on the network, GIL is RELEASED
# 50 threads here genuinely overlap (Area 5) — the GIL is not held during the wait.

# --- NumPy releases the GIL during heavy C loops ------------------------
import numpy as np
def heavy_numpy(a):
    return np.fft.fft(a)                   # the FFT runs in C with the GIL released,
                                           # so threads CAN parallelise multiple such calls
# This is why "CPU-bound" isn't always "must use processes": if the hot loop is in a
# GIL-releasing C library, threads (or just vectorising, 6.10) may suffice.

# --- Note: the GIL is a CPython implementation detail -------------------
# Jython/IronPython have no GIL; PyPy has one too. Python 3.13+ ships an EXPERIMENTAL
# "free-threaded" (no-GIL) build — but for mainstream CPython today, plan around the GIL.
```

### Impact

- **Explains the #1 concurrency surprise:** "why didn't threads speed up my computation?"
  — and points you straight to processes or vectorisation.
- **Saves wasted effort:** you stop trying to thread CPU work and reach for the tool that
  actually uses multiple cores.
- **Clarifies library behaviour:** knowing NumPy/PyTorch release the GIL explains why
  vectorised code (6.10) is fast without you managing processes.

### Pros & cons / when NOT to

This is a *mental model*, not a technique — the practical takeaways:

- **Don't use threads to parallelise pure-Python CPU loops** — they can't, by design.
  Use processes (6.2) or vectorise (6.10).
- **Don't avoid threads for I/O out of GIL fear** — the GIL is released during I/O
  waits, so threads are the right, lightweight tool there (Area 5).
- **Processes cost more** than threads (memory, startup, data copying, 6.6) — the GIL
  workaround isn't free; only pay it for genuinely CPU-bound work.
- **Don't rely on no-GIL builds yet** — free-threaded CPython exists but is experimental;
  write for the GIL on mainstream Python today.

### Where this shows up

- **Real work — the universal first lesson:** every Python engineer eventually threads a
  CPU loop, sees no speed-up, and learns the GIL — better to know it upfront.
- **Real work — choosing preprocessing strategy:** deciding between processes
  (multiprocessing, 6.2) and vectorisation (NumPy/pandas, 6.10) for heavy data transforms
  hinges on the GIL.
- **Real work — mixed servers:** an async/threaded web server stays responsive on I/O but
  must offload CPU work to a process pool (5.5) precisely because of the GIL.
- **Pattern mapping (secondary):** no DSA analogue; it's the core interpreter constraint
  behind every threads-vs-processes decision in Areas 5–6.
[↑ Back to top](#contents)

---

<a id="6.4"></a>
## 6.4 — "I want multi-core parallelism with the same API as my thread pool" → ProcessPoolExecutor

### The situation

You already use `ThreadPoolExecutor` for I/O (5.2) and like its clean API —
`submit`, `map`, `as_completed`, futures. Now you have CPU-bound work (6.1) that needs
*processes* (6.2), and you'd rather not learn a different interface (`multiprocessing`'s
`Pool`, `Manager`, etc.) for it.

```python
# You know this shape from threads (5.2):
with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(fetch, urls))
# ...is there a process version with the SAME shape for CPU work?
```

### What's really going on

`concurrent.futures` provides **two interchangeable executors** with an *identical* API:
`ThreadPoolExecutor` (threads, for I/O) and `ProcessPoolExecutor` (processes, for CPU).
They share the same `submit` / `map` / `as_completed` / `Future` interface, so switching
from "overlap I/O" to "use all cores" is often a **one-line class swap** — the surrounding
code stays the same.

`ProcessPoolExecutor` is the friendlier face of multiprocessing (6.2): it manages a pool
of worker processes, dispatches tasks, handles result collection and error propagation,
and integrates with the `Future` abstraction (a handle to a result that will exist
later, 5.2). For most CPU-parallel jobs it's the recommended entry point — you reach for
raw `multiprocessing` only when you need its lower-level features (custom shared memory,
6.8; specific start methods).

> Same `concurrent.futures` API, different worker type: **ThreadPoolExecutor** = threads
> (share memory, limited by GIL → I/O work); **ProcessPoolExecutor** = processes
> (isolated memory, own GIL each → CPU work). Pick by bound-type (6.1).

### The move

Swap `ThreadPoolExecutor` for `ProcessPoolExecutor` — same calls:

```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=8) as pool:   # processes, not threads
    results = list(pool.map(process_one, items))   # runs across 8 cores in parallel
```

### Why it works

`ProcessPoolExecutor` starts a pool of worker *processes* and exposes the same
`submit`/`map`/`as_completed` interface as the thread version. Because each worker is a
separate interpreter with its own GIL (6.3), `pool.map` genuinely runs `process_one` on
different cores at once — true parallelism for CPU work. The `Future` objects, result
ordering, exception propagation, and `with`-block shutdown all behave like the thread
pool you know, so your orchestration code is unchanged; only the *kind* of worker
differs.

### The code, every line explained

```python
from concurrent.futures import ProcessPoolExecutor, as_completed

def process_one(item):                    # MODULE-LEVEL function (must be picklable, 6.6)
    return extract_features(item)

if __name__ == "__main__":                # guard required on spawn platforms (6.2)
    # --- map: results in INPUT order ------------------------------------
    with ProcessPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(process_one, items, chunksize=50))
        #                                            └ batch items per task (6.7)
        # Identical to ThreadPoolExecutor.map — but runs on 8 cores in parallel.

    # --- submit + as_completed: handle results AS they finish + isolate errors
    with ProcessPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(process_one, it): it for it in items}
        for fut in as_completed(futures):          # yields each future when done (6.9)
            item = futures[fut]
            try:
                save(fut.result())                 # .result() re-raises worker exceptions
            except Exception as e:
                log.warning("item %r failed in worker: %s", item, e)   # (6.10 isolation)

# --- The one-line thread<->process swap ---------------------------------
# I/O-bound (waiting):   from concurrent.futures import ThreadPoolExecutor
# CPU-bound (computing): from concurrent.futures import ProcessPoolExecutor
# The body (pool.map / submit / as_completed) is otherwise the SAME.

# --- mixing: a process pool can be the executor behind asyncio (5.5) ----
# loop.run_in_executor(ProcessPoolExecutor(), heavy_cpu, data)  # offload CPU from async
```

### Impact

- **Minimal learning curve:** if you know the thread pool (5.2), you already know this —
  reuse the same patterns for multi-core CPU work.
- **True parallelism with managed plumbing:** get multi-core speed-up without hand-rolling
  `multiprocessing` worker/queue code; errors and results are handled for you.
- **Easy to switch axes:** prototype with threads, discover it's CPU-bound, change one
  import — and you get core-scaling.

### Pros & cons / when NOT to

**Reach for ProcessPoolExecutor when:** CPU-bound work (6.1), and you want the clean
`concurrent.futures` API rather than raw `multiprocessing`.

**Watch out / when NOT to:**
- **Same process constraints as 6.2 apply:** functions/args must be picklable (6.6), data
  is copied to workers (avoid huge arguments; use shared memory, 6.8), the `__main__`
  guard is required, and startup has a cost.
- **Don't use it for I/O-bound work** — process overhead with no benefit; use
  `ThreadPoolExecutor` (5.2).
- **Reach for raw `multiprocessing` only when you need its extras** — custom start
  methods, `Manager` shared objects, fine-grained control. For "run this function across
  cores," the executor is simpler.
- **Tune `max_workers` to cores, not higher** — for pure CPU work, more processes than
  cores just adds context-switching and memory; `os.cpu_count()` is the natural ceiling.

### Where this shows up

- **Real work — CPU preprocessing at scale:** the recommended entry point for
  parallelising featurisation, parsing, or transforms across cores in a data/ML pipeline.
- **Real work — offloading CPU from an async/threaded server:** passing a
  `ProcessPoolExecutor` to `loop.run_in_executor` (5.5) so heavy work doesn't block the
  event loop.
- **Real work — quick prototype-to-parallel:** start single-threaded, wrap the hot
  function in a process pool when you confirm it's CPU-bound — small, low-risk change.
- **Pattern mapping (secondary):** same map-reduce/divide-and-conquer decomposition as
  6.2; the executor is just the ergonomic wrapper around it.
[↑ Back to top](#contents)

---

<a id="6.5"></a>
## 6.5 — "pool.map on 50 million rows ate all my RAM before doing any work" → imap & lazy streaming

### The situation

You parallelise a transform over 50 million records with `pool.map` — and the process
crashes with an out-of-memory error *before* results even start coming back:

```python
with Pool(8) as pool:
    results = pool.map(transform, fifty_million_records)   # OOM!
    write(results)
```

Two things blew up memory: `pool.map` first **pulls the entire input** (`fifty_million_
records`) into a list to dispatch it, and it **collects every result into one giant
list** before returning. You're holding 50M inputs *and* 50M outputs in RAM at once,
even though you only want to write each result to disk and move on.

### What's really going on

`Pool.map` (and `executor.map(...)` wrapped in `list(...)`) is **eager on both ends**: it
materialises the full input and the full output list. For a few thousand items that's
fine; for tens of millions it's a memory bomb.

The fix is a **lazy** variant that streams: feed inputs from a generator (1.2) and
receive results **one at a time as workers finish them**, writing each out immediately so
neither the full input nor the full output is ever in memory. `multiprocessing.Pool`
offers `imap` / `imap_unordered`; `ProcessPoolExecutor.map` is *already* lazy in its
iterator if you don't wrap it in `list()`.

> **`imap`** is the lazy cousin of `map`: it returns an **iterator** that yields results
> as they're computed, pulling inputs on demand rather than all up front. **`imap_
> unordered`** is the same but yields results **in whatever order they finish** (fastest
> first) — even cheaper when you don't need input order.

### The move

Use `imap`/`imap_unordered` with a generator input, and consume results one at a time:

```python
with Pool(8) as pool:
    for result in pool.imap_unordered(transform, record_stream(), chunksize=200):
        write(result)                     # handle each as it arrives; nothing piles up
```

### Why it works

`imap_unordered` pulls inputs from `record_stream()` **lazily** (only as workers are
ready for more) instead of building a 50M-item list, and hands you each result the
moment a worker finishes it — so you `write` it and discard it. At any instant memory
holds only the in-flight chunks plus one result, regardless of total size. `unordered`
adds a small extra win: a worker that finishes early doesn't have to wait for slower
ones to preserve input order, so results flow as fast as they're produced. `chunksize`
(6.7) batches dispatch so per-task overhead stays low even at 50M items.

### The code, every line explained

```python
from multiprocessing import Pool

def record_stream():                      # a GENERATOR (1.2): yields one record at a time
    with open("huge.jsonl") as f:         # never loads the whole file
        for line in f:
            yield parse(line)

def transform(record):                    # module-level, picklable (6.6); pure CPU work
    return featurise(record)

if __name__ == "__main__":
    with Pool(8) as pool:
        # imap_unordered: lazy input + results as they finish (fastest first)
        for result in pool.imap_unordered(transform, record_stream(), chunksize=200):
            write(result)                 # stream each result out; O(1)-ish memory
        # imap (ORDERED) if you must preserve input order:
        # for result in pool.imap(transform, record_stream(), chunksize=200): ...

# --- ProcessPoolExecutor.map is ALREADY lazy if you don't list() it -----
from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor(8) as pool:
    for result in pool.map(transform, record_stream(), chunksize=200):
        write(result)                     # iterating without list() streams results
    # results = list(pool.map(...))       # <- THIS is what re-introduces the OOM

# --- ordered vs unordered: what you trade -------------------------------
# imap            -> results in INPUT order (may buffer a fast result while waiting
#                    for an earlier-but-slower one to finish — slight memory/latency cost)
# imap_unordered  -> results in COMPLETION order (lowest latency/memory; use when you
#                    don't care about order, e.g. writing to a DB keyed by id)
```

### Impact

- **Flat memory on unbounded input:** processes 50M (or 50B) records in roughly constant
  memory instead of OOMing — the parallel analogue of streaming (1.2 / Area 2).
- **Results start flowing immediately:** you write outputs as they're produced rather
  than after the entire job — better latency and resumability (Area 7).
- **`unordered` maximises throughput:** no head-of-line blocking waiting for a slow early
  item.

### Pros & cons / when NOT to

**Reach for imap/lazy map when:** the input is large/streaming and you want results
incrementally — basically any big-data parallel transform.

**Watch out / when NOT to:**
- **`list(pool.map(...))` re-creates the OOM** — the laziness is lost the moment you
  materialise. Iterate the result, don't collect it (unless it's small).
- **`imap_unordered` loses input order** — only use it when order doesn't matter, or
  attach an id to each result so you can re-associate it.
- **Still subject to per-task overhead** — pair with `chunksize` (6.7) so dispatching 50M
  tiny tasks doesn't dominate; and avoid shipping huge per-item arguments (6.6/6.8).
- **For small inputs, plain `map` is simpler** — laziness is overhead you don't need
  under a few thousand items.

### Where this shows up

- **Real work — large-corpus preprocessing:** featurising/tokenising tens of millions of
  rows across cores while streaming results to disk or a DB — the standard big-data CPU
  job (pairs with 1.2 generators, 6.2 pool).
- **Real work — ETL transforms:** reading a huge file lazily, transforming in parallel,
  writing out incrementally — constant memory end to end.
- **Real work — parallel inference over a stream:** scoring records as they arrive,
  emitting predictions as completed (`imap_unordered` keyed by id).
- **Pattern mapping (secondary):** combines streaming/lazy evaluation (1.2) with parallel
  map (6.2) — a lazy parallel map-reduce over an unbounded sequence.
[↑ Back to top](#contents)

---

<a id="6.6"></a>
## 6.6 — "Parallelising made it SLOWER" → serialization (pickle) cost between processes

### The situation

You parallelise a transform across 8 cores (6.2), expecting ~8× — but it runs *slower*
than the single-process version:

```python
big_df = load_dataframe()                 # a 2 GB DataFrame in memory
def score(row_index):
    return model_score(big_df, row_index) # each task uses the big DataFrame

with Pool(8) as pool:
    results = pool.map(score, range(len(big_df)))   # SLOWER than a plain loop!
```

The compute per row is tiny, but each task somehow drags. Profiling shows the workers
spend most of their time *not* computing — they're busy receiving data.

### What's really going on

Processes don't share memory (6.2) — so to send a task to a worker, Python must
**serialise** the function and its arguments, ship the bytes to the worker process, and
**deserialise** them there. In Python this serialisation is called **pickling**.

> **Pickling** = converting a Python object into a byte stream (`pickle` module) so it
> can be sent to another process (or saved to disk), then **unpickling** it back into an
> object on the other side. Every argument you pass to a worker, and every result it
> returns, is pickled and unpickled.

Here's the trap: `score` takes `big_df` implicitly via closure-style usage, and the way
it's written, that **2 GB DataFrame gets pickled and copied to a worker on every
task** — millions of times. The copying cost dwarfs the trivial per-row computation, so
parallelism *loses*. The rule: **the data moved to/from workers must be small relative
to the work done on it**, or serialization overhead eats the gains.

This is the **granularity** problem: parallelism only pays when each task does enough
work to justify the fixed cost of shipping its data.

### The move

Minimise what crosses the process boundary: send small arguments, do more work per task,
and let workers load big shared data **once** instead of receiving it per task:

```python
# Instead of passing the 2 GB df per task, give each worker a CHUNK of actual data
# and enough work to amortise the transfer:
with Pool(8) as pool:
    results = pool.map(score_chunk, chunks_of_rows, chunksize=1)  # each task = many rows
```

### Why it works

The cost that killed the naive version was pickling `big_df` per task. The fixes attack
that directly:

1. **Send small, send once.** Pass only the data a task actually needs (a chunk of rows),
   not a giant object referenced incidentally. Smaller pickles = less transfer.
2. **Do more per task** (coarse granularity). If each task processes 10,000 rows instead
   of 1, the fixed pickling cost is paid once per 10,000 rows, not per row — so compute
   dominates transfer again.
3. **Load big read-only data inside the worker once** (via an initializer, 6.11, or
   shared memory, 6.8) so it isn't shipped per task at all.

When the data moved is small relative to the compute, the ~8× parallel speed-up returns.

### The code, every line explained

```python
from multiprocessing import Pool

# --- WRONG: ships a huge object per task --------------------------------
def score(args):
    big_df, idx = args                    # big_df pickled+copied EVERY task -> disaster
    return model_score(big_df, idx)
# pool.map(score, [(big_df, i) for i in range(n)])   # millions of 2 GB copies

# --- BETTER 1: load the big data ONCE per worker (initializer, 6.11) ----
_DF = None
def init_worker():
    global _DF
    _DF = load_dataframe()                # runs ONCE when each worker starts, not per task
def score_idx(idx):
    return model_score(_DF, idx)          # uses the worker's own copy; only `idx` is pickled
with Pool(8, initializer=init_worker) as pool:
    results = pool.map(score_idx, range(n), chunksize=1000)
    # now only small integers cross the boundary; the big df is loaded per worker once.

# --- BETTER 2: coarse tasks — each task does a whole chunk --------------
def score_chunk(rows):                    # `rows` = a list of actual row data (small-ish)
    return [model_score_row(r) for r in rows]   # lots of work per task amortises transfer
with Pool(8) as pool:
    results = pool.map(score_chunk, batched_rows)   # few large tasks, not millions of tiny

# --- Measure what you're shipping ---------------------------------------
import pickle
print(len(pickle.dumps(my_arg)))          # how many BYTES this argument costs per task
# If that number is large and per-task compute is small, parallelism will lose.

# --- Things that DON'T pickle (common errors) ---------------------------
# lambdas, nested/local functions, open file handles, DB connections, some closures.
# -> define worker functions at MODULE level; open resources INSIDE the worker (6.11).
```

### Impact

- **Restores the speed-up:** cutting per-task data transfer turns "slower than serial"
  back into the expected near-linear multi-core gain.
- **Lower memory pressure:** not copying a 2 GB object N times avoids both the time cost
  and the memory spikes of many simultaneous copies.
- **Predictable scaling:** once transfer is small relative to compute, adding cores helps
  proportionally (until the next ceiling, 6.13).

### Pros & cons / when NOT to

**Mind serialization whenever you use processes (6.2/6.4)** — it's not optional
knowledge; it's why naive multiprocessing often disappoints.

**Watch out / guidelines:**
- **Keep arguments and results small.** Ship ids/paths/chunks, not whole datasets. Have
  workers load big data themselves (6.11) or use shared memory (6.8).
- **Make tasks coarse enough.** Millions of tiny tasks pay pickling+dispatch overhead
  millions of times — use `chunksize` (6.7) or chunk the data yourself.
- **Everything crossing the boundary must be picklable** — module-level functions, no
  lambdas/handles. Open connections and load models *inside* the worker.
- **If data is huge AND shared read-only**, copying per worker (even once) may still be
  too much — use `multiprocessing.shared_memory` or memory-mapped arrays (6.8).
- **If transfer can't be made small relative to compute, parallelism may not be worth
  it** — consider vectorising instead (6.10) or a different tool (6.12).

### Where this shows up

- **Real work — the "multiprocessing made it slower" debugging session:** almost always
  traced to a large object pickled per task; the fix is one of the three above.
- **Real work — parallel scoring with a big model/lookup:** load the model once per
  worker (6.11) instead of pickling it into every task.
- **Real work — DataFrame parallelism:** why naive `Pool` over pandas rows often loses,
  and why chunking or vectorising (6.10) wins.
- **Pattern mapping (secondary):** no DSA analogue; it's the parallel-computing principle
  that communication cost must stay small relative to computation — the same idea behind
  chunking (6.7) and data locality in distributed systems (6.12).
[↑ Back to top](#contents)

---

<a id="6.7"></a>
## 6.7 — "8 workers but barely faster — they spend all their time on dispatch" → chunksize

### The situation

You parallelise a *cheap* per-item operation over 10 million items across 8 workers, and
get nowhere near 8×:

```python
def square(x):
    return x * x                          # ~microseconds of actual work

with Pool(8) as pool:
    results = pool.map(square, range(10_000_000))   # default chunksize -> sluggish
```

Each `square` is trivially fast, but you're dispatching **10 million separate tasks** to
the pool. The overhead of handing each tiny task to a worker (pickling the item, putting
it on the queue, the worker pulling it, pickling the result back) **dwarfs** the
microsecond of squaring — so the workers spend their time on bookkeeping, not work.

### What's really going on

Every task dispatched to a worker has fixed **overhead**: serialise the argument (6.6),
enqueue it, the worker dequeues and deserialises, computes, then serialises the result
back. When the work per item is large, this overhead is negligible. When the work per
item is tiny, the overhead **dominates** — and 10 million dispatches of overhead is
enormous.

The fix is **chunksize**: send items to workers in **batches** instead of one at a time.
With `chunksize=10_000`, the pool hands each worker 10,000 items per dispatch, so the
per-task overhead is paid once per 10,000 items rather than once per item — a ~10,000×
reduction in dispatch overhead.

> **chunksize** = how many items are bundled into a single task sent to a worker. Bigger
> chunks = less per-task overhead, but coarser load balancing (a worker that gets a slow
> chunk holds it). It's the **granularity** dial: balance "overhead per task" against
> "even distribution of work."

### The move

Pass a `chunksize` sized so each chunk does meaningful work:

```python
with Pool(8) as pool:
    results = pool.map(square, range(10_000_000), chunksize=50_000)
```

### Why it works

With `chunksize=50_000`, the 10M items become ~200 tasks instead of 10M. The fixed
dispatch+pickle overhead is now paid ~200 times, so it's negligible against the actual
computation — workers spend their time squaring, not bookkeeping. The result is the
near-8× you expected. The trade-off is load balancing: chunks are handed out as units, so
if one chunk happens to be much slower, the worker holding it can become a straggler
while others idle — which is why you don't just set chunksize to "total ÷ workers" and
forget it.

### The code, every line explained

```python
from multiprocessing import Pool

def square(x):
    return x * x                          # tiny work -> overhead-sensitive

if __name__ == "__main__":
    data = range(10_000_000)

    # --- default chunksize: 10M tiny dispatches -> overhead-bound -------
    with Pool(8) as pool:
        pool.map(square, data)            # slow: dispatch cost >> compute cost

    # --- tuned chunksize: ~200 chunks -> compute-bound, near 8x ---------
    with Pool(8) as pool:
        pool.map(square, data, chunksize=50_000)   # overhead paid 200x, not 10M times

# --- rule of thumb for chunksize ----------------------------------------
# Start around:  chunksize ≈ total_items / (workers * 4)
#   - the "* 4" gives several chunks PER worker, so faster workers can pick up more
#     chunks (load balancing) instead of all work being split into exactly N huge pieces.
# Then adjust:
#   - work per item TINY  -> bigger chunks (overhead dominates; favour fewer dispatches)
#   - work per item HEAVY or UNEVEN -> smaller chunks (better balancing; overhead is moot)

# --- executor.map takes chunksize too (6.4) -----------------------------
from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor(8) as pool:
    list(pool.map(square, data, chunksize=50_000))   # same dial in the futures API

# --- uneven workloads: smaller chunks avoid stragglers ------------------
# If some items take 1ms and others 10s, huge chunks risk one worker getting all the
# slow items. Smaller chunks (or imap_unordered, 6.5) spread the heavy ones out.
```

### Impact

- **Removes dispatch overhead:** turns an overhead-bound job (workers idle, shuffling
  tiny tasks) back into a compute-bound one that scales with cores.
- **Often the difference between "no speed-up" and "near-linear":** for cheap per-item
  work, chunksize is *the* lever — bigger effect than adding workers.
- **Tunable for fairness:** smaller chunks rebalance uneven workloads; larger chunks
  minimise overhead. You choose based on the work profile.

### Pros & cons / when NOT to

**Tune chunksize when:** you parallelise many items (especially cheap ones) with
`Pool.map`/`executor.map` and aren't getting the expected speed-up.

**Watch out / when NOT to:**
- **Too-large chunks hurt load balancing.** If chunks are huge and work is uneven, one
  worker becomes a straggler holding a slow chunk while others finish and idle. Aim for
  several chunks per worker, not one giant chunk each.
- **Too-small chunks bring back overhead** — the original problem. The sweet spot makes
  each chunk's compute comfortably exceed its dispatch cost.
- **`imap` default chunksize is 1** — explicitly set it for `imap`/`imap_unordered`
  (6.5) on large inputs, or you get the per-item overhead again.
- **Heavy per-item work needs little tuning** — if each item already takes seconds,
  dispatch overhead is irrelevant and chunksize barely matters; don't over-think it.
- **It interacts with serialization (6.6)** — bigger chunks mean bigger pickles per
  dispatch; ensure a chunk's data still transfers cheaply.

### Where this shows up

- **Real work — parallelising cheap transforms:** squaring/normalising/parsing millions
  of small items where, without chunksize, dispatch overhead negates the parallelism.
- **Real work — tuning a slow `Pool.map`:** the first knob to try when multiprocessing
  "isn't faster" and the data transfer (6.6) is already small.
- **Real work — uneven workloads:** choosing smaller chunks (or `imap_unordered`, 6.5)
  when item costs vary a lot, to avoid one worker getting stuck with the slow ones.
- **Pattern mapping (secondary):** no DSA analogue; it's the granularity/overhead-vs-
  balance trade-off central to all parallel computing (and the same instinct as batching
  API calls, 5.14).
[↑ Back to top](#contents)

---

<a id="6.8"></a>
## 6.8 — "Every worker copied the same 4 GB array and I ran out of RAM" → shared memory

### The situation

All 8 workers need the *same* large read-only array — say a 4 GB embedding matrix they
look vectors up in:

```python
embeddings = np.load("embeddings.npy")    # 4 GB, read-only, needed by every worker

def lookup(query_ids):
    return [nearest(embeddings, qid) for qid in query_ids]

with Pool(8) as pool:
    results = pool.map(lookup, query_chunks)   # 8 workers x 4 GB = 32 GB -> OOM!
```

Each worker process gets its **own copy** of the 4 GB array (6.6) — 8 copies = 32 GB,
and your machine has 16 GB. Even though every worker only *reads* it and they'd happily
share one copy, multiprocessing duplicates it per process.

### What's really going on

Processes have isolated memory (6.2), so by default a large object is **copied into each
worker**. For read-only data that's pure waste: N identical copies of something nobody
modifies. The fix is **shared memory** — one copy in a memory region that all processes
**map into their address space and read directly**, without duplication.

> **Shared memory** = a block of RAM that multiple processes can access as if it were
> their own, so a single 4 GB array is stored *once* and all 8 workers read the same
> bytes. Python exposes this via `multiprocessing.shared_memory` (and NumPy can wrap a
> shared buffer as an array); memory-mapped files (`np.memmap`, `mmap`) achieve the same
> for on-disk data.

Two practical routes:

- **`fork` start method (Linux default):** child processes share the parent's memory
  **copy-on-write** — read-only data created *before* forking isn't actually copied
  until written. Often the simplest "share a big read-only object" answer on Linux.
- **Explicit shared memory / memmap:** portable across platforms (needed on
  Windows/macOS spawn), and the right tool for arrays you want all workers to read (or a
  memory-mapped file too big for RAM).

### The move

Store the big array once and have workers attach to it instead of receiving a copy —
via copy-on-write fork, a memory-mapped file, or `shared_memory`:

```python
# Simplest portable route for a big read-only array: memory-map it from disk.
import numpy as np
embeddings = np.load("embeddings.npy", mmap_mode="r")   # mapped, not loaded into RAM
```

### Why it works

`mmap_mode="r"` makes NumPy **memory-map** the file: the array's data lives on disk and
the OS pages just the parts you actually touch into RAM, **shared** across all processes
that map the same file. So 8 workers reading the 4 GB matrix share the OS page cache —
one effective copy, not eight. With the `fork` start method, the same sharing happens for
in-memory objects: children inherit the parent's pages copy-on-write, so a read-only
array built before forking is never duplicated. Either way, the per-worker 4 GB copy
disappears, and the 32 GB OOM with it.

### The code, every line explained

```python
import numpy as np
from multiprocessing import Pool

# --- Route 1: memory-mapped file (portable, great for big read-only arrays) ---
EMB = np.load("embeddings.npy", mmap_mode="r")   # "r" = read-only map; data stays on disk
def lookup(query_ids):
    return [nearest(EMB, qid) for qid in query_ids]   # workers read shared pages, no copy
# Each worker opens the same memmap; the OS shares the underlying pages across processes.

# --- Route 2: fork + module-level global (Linux): copy-on-write ---------
BIG = np.load("embeddings.npy")          # loaded ONCE in the parent, before the Pool
def lookup2(query_ids):
    return [nearest(BIG, qid) for qid in query_ids]   # children inherit BIG via fork (CoW)
if __name__ == "__main__":
    with Pool(8) as pool:                # on Linux (fork), workers share BIG read-only;
        pool.map(lookup2, query_chunks)  # it is NOT copied unless a worker writes to it

# --- Route 3: explicit shared_memory (portable, for arrays you build) ---
from multiprocessing import shared_memory
def make_shared(arr):
    shm = shared_memory.SharedMemory(create=True, size=arr.nbytes)   # one shared block
    buf = np.ndarray(arr.shape, dtype=arr.dtype, buffer=shm.buf)
    buf[:] = arr[:]                      # copy data into shared memory ONCE
    return shm                           # pass shm.name to workers; they attach by name
# Workers: shm = SharedMemory(name=...); arr = np.ndarray(shape, dtype, buffer=shm.buf)
# IMPORTANT: call shm.close() in workers and shm.unlink() ONCE at the end to free it,
# or you leak a shared-memory segment that outlives the program.

# --- The trap this avoids -----------------------------------------------
# Passing `embeddings` as a task argument (pool.map(lookup, [(embeddings, q) for ...]))
# pickles+copies the 4 GB per task (6.6) -> catastrophic. Share it instead.
```

### Impact

- **One copy, not N:** the 4 GB array is stored once and read by all workers, so memory
  stays ~4 GB instead of 32 GB — the difference between OOM and running.
- **Enables bigger-than-RAM data:** memory-mapping lets workers read a dataset larger
  than physical RAM, the OS paging in only what's touched.
- **Faster startup:** no time spent copying gigabytes into each worker before work
  begins.

### Pros & cons / when NOT to

**Reach for shared memory/memmap when:** many workers need the **same large read-only**
data (embedding tables, lookup matrices, models, reference datasets).

**Watch out / when NOT to:**
- **Read-only is the easy case; shared *writable* memory needs synchronisation.** If
  workers write to shared memory, you get race conditions (Area 7) and must add locks —
  usually better to have workers return results and combine them (6.9) than to share
  mutable state.
- **`fork` copy-on-write is Linux-only** and silently copies a page the moment any
  worker writes to it; on Windows/macOS (spawn) you need explicit shared_memory/memmap.
- **Explicit `shared_memory` must be cleaned up** — `close()` in workers and `unlink()`
  once, or you leak OS segments that persist after the program exits.
- **Don't bother for small data** — the machinery is only worth it for objects big enough
  that per-worker copies hurt. For small read-only data, copying (or an initializer,
  6.11) is simpler.
- **memmap reads hit disk on first touch** — random access over a huge memmapped file can
  be slow if the working set doesn't fit in page cache; fine for mostly-cached or
  sequential access.

### Where this shows up

- **Real work — vector search / RAG:** all workers querying one large embedding matrix —
  memory-map it so 8 workers share 4 GB instead of needing 32 GB (Area 9).
- **Real work — shared model/lookup tables:** a big read-only model or feature table used
  by every parallel scorer (pairs with load-once initializer, 6.11).
- **Real work — bigger-than-RAM datasets:** memory-mapping a large array/Parquet so
  parallel workers process data that doesn't fit in memory.
- **Pattern mapping (secondary):** no DSA analogue; it's the data-locality/avoid-copying
  principle (6.6) realised in memory — share the read-only working set instead of
  duplicating it.
[↑ Back to top](#contents)

---

<a id="6.9"></a>
## 6.9 — "One slow task blocks me from seeing any results until it's done" → as_completed & ordering

### The situation

You submit 1,000 parallel tasks where durations vary wildly — most finish in 1 second,
a few take 5 minutes. With `map`, you can't touch *any* result until you iterate to it
in order, and you'd like to handle the 1-second results immediately rather than waiting:

```python
with ProcessPoolExecutor(8) as pool:
    results = list(pool.map(process, tasks))   # blocks until ALL 1,000 done; ordered
    for r in results:
        save(r)                                # nothing saved until the slowest finishes
```

If task #3 takes 5 minutes, `map`'s ordered iterator makes you wait for #3 before
handling #4, #5, … even though they finished minutes ago. And if the job crashes at
minute 4, you've saved *nothing*.

### What's really going on

`map` returns results in **input order**, which means a slow early task creates
**head-of-line blocking** — finished later results pile up waiting their turn. When you
care about *throughput* and *incremental progress* rather than order, you want results
**as they complete**, regardless of input position.

`concurrent.futures.as_completed` does exactly that: given a set of futures (handles to
pending results, 5.2), it yields each one **the moment it finishes**, fastest first. You
process each result immediately — saving progress, freeing memory, and isolating any
per-task error (6.10) — without waiting for stragglers.

> **Ordered (`map`)** vs **completion-order (`as_completed`)**: `map` is convenient when
> you need outputs aligned to inputs; `as_completed` is better when you want results ASAP
> and order doesn't matter. To keep track of *which* input a result belongs to under
> `as_completed`, map each future back to its input via a dict.

### The move

Submit tasks to get futures, then iterate `as_completed` to handle each result the moment
it lands:

```python
from concurrent.futures import ProcessPoolExecutor, as_completed

with ProcessPoolExecutor(8) as pool:
    future_to_task = {pool.submit(process, t): t for t in tasks}
    for fut in as_completed(future_to_task):     # yields fastest-finishing first
        save(fut.result())                       # handle immediately, don't wait for slow ones
```

### Why it works

`pool.submit(process, t)` schedules a task and returns a **future** immediately (it
doesn't block). `as_completed(futures)` watches the whole set and yields each future the
instant it's done — so the 1-second results are saved within a second, while the
5-minute straggler is still running. No head-of-line blocking: completion order, not
input order. The `future_to_task` dict lets you recover which input produced each result
(needed because completion order ≠ input order), and wrapping `fut.result()` in
`try/except` isolates a single task's failure (6.10) instead of losing the batch.

### The code, every line explained

```python
from concurrent.futures import ProcessPoolExecutor, as_completed

# --- as_completed: results as they finish, with input tracking ----------
with ProcessPoolExecutor(8) as pool:
    # submit returns a Future now; map it back to its input so we know what finished
    future_to_task = {pool.submit(process, t): t for t in tasks}
    for fut in as_completed(future_to_task):     # fastest-first, NOT input order
        task = future_to_task[fut]               # recover which input this was
        try:
            result = fut.result()                # get value, or RE-RAISE the worker's error
            save(task, result)                   # incremental progress: save now
        except Exception as e:
            log.warning("task %r failed: %s", task, e)   # isolate one failure (6.10)

# --- when you DO want input order: map (or sort afterwards) -------------
with ProcessPoolExecutor(8) as pool:
    for result in pool.map(process, tasks):      # ordered; simplest when alignment matters
        save(result)
# or, with as_completed, collect into a dict and reorder at the end:
#   out = {}; ... out[task_index] = result ...; ordered = [out[i] for i in range(len(tasks))]

# --- add a per-future timeout (don't wait forever on a wedged task) -----
for fut in as_completed(future_to_task, timeout=600):   # raises TimeoutError after 600s
    ...                                          # (bounds total wait; pairs with 5.8)

# --- map vs as_completed, summarised ------------------------------------
# pool.map(fn, items)      -> results in INPUT order; blocks per-item in that order
# submit + as_completed    -> results in COMPLETION order; handle ASAP, isolate errors,
#                             save progress incrementally (best for uneven / long jobs)
```

### Impact

- **Incremental progress:** results are handled and persisted as they finish, so a crash
  at minute 4 hasn't lost the 900 tasks that already completed (pairs with checkpointing,
  Area 7).
- **No head-of-line blocking:** fast tasks aren't held hostage by a slow early one —
  better throughput and lower peak memory (results don't pile up waiting their turn).
- **Per-task error isolation:** one failing task is logged and skipped instead of
  aborting the whole batch.

### Pros & cons / when NOT to

**Reach for `as_completed` when:** task durations are uneven, you want results/progress
ASAP, or you need to isolate per-task failures.

**Watch out / when NOT to:**
- **Completion order ≠ input order.** If you need outputs aligned to inputs, either use
  `map`, or track indices with the future→input dict and reorder at the end.
- **`.result()` re-raises the worker's exception** — always wrap it in `try/except` under
  `as_completed`, or one bad task aborts your loop (defeating the isolation benefit).
- **For uniform, short tasks where order matters, `map` is simpler** — don't add
  submit/as_completed machinery you don't need.
- **Add a `timeout=`** if a task can wedge — otherwise `as_completed` waits indefinitely
  for a stuck future (process pools can't always cancel running work; bound it).
- **Holding all futures for a massive task count uses memory** — for tens of millions,
  prefer streaming with `imap_unordered` (6.5) over submitting everything at once.

### Where this shows up

- **Real work — uneven batch jobs:** processing files/records of very different sizes,
  saving each result as it lands rather than waiting for the biggest.
- **Real work — long parallel jobs with checkpoints:** writing each completed result
  immediately so a mid-run failure is resumable (Area 7, 7.6/7.10).
- **Real work — fan-out with per-item error handling:** scoring/calling where some items
  fail — log and skip them while keeping every success (6.10).
- **Pattern mapping (secondary):** `as_completed` is a completion-order merge of parallel
  results — conceptually like draining a priority/ready queue as items become available
  (the same "process whatever's ready next" idea as the async event loop, 5.4).
[↑ Back to top](#contents)

---

<a id="6.10"></a>
## 6.10 — "One bad row crashed the whole 10-hour parallel job" → isolating worker failures

### The situation

A parallel job processes 1 million records over 10 hours. At hour 9, record #847,213 —
a malformed one — raises an exception in a worker, and:

```python
with ProcessPoolExecutor(8) as pool:
    results = list(pool.map(process, records))   # ONE record raises -> the whole map dies
```

`pool.map` re-raises the first worker exception, so the entire job aborts. Nine hours of
work on the other 847,212 records is lost because of a single bad input. Worse, some
errors (a segfault, an out-of-memory kill in a worker) can take down a worker *process*
itself, leaving the pool broken.

### What's really going on

In a long parallel job over messy real-world data, **some items will fail** — bad
encoding, a null where you expected a number, an oversized input. The default behaviour
(`map` re-raises and aborts) treats one failure as fatal to the whole batch, which is
exactly wrong for a 10-hour job: you want to **isolate** the failure — record it, skip
it, keep the other 999,999 results.

There are two layers of failure to handle:

- **Task-level exceptions** (the common case): the worker function raises a normal Python
  exception on a bad input. Catch it per-task so it doesn't propagate.
- **Worker-process death** (rarer, nastier): a segfault, OOM-kill, or `sys.exit` in a
  worker kills the *process*. With `ProcessPoolExecutor` this raises
  `BrokenProcessPool` and can poison the whole pool — you need to guard against the kinds
  of work that can crash a process, or run risky items in a way you can restart.

The realisation: **partial failure is normal at scale; design for "skip and record,"
not "all-or-nothing."** (This connects directly to partial-failure handling in Area 7,
7.9.)

### The move

Catch exceptions **inside the worker** (return a result-or-error marker), or use
`submit` + `as_completed` and wrap `.result()` — so one failure is recorded, not fatal:

```python
def process_safe(record):
    try:
        return ("ok", transform(record))
    except Exception as e:
        return ("error", repr(e))         # failure becomes a value, not a crash
```

### Why it works

If the worker function never lets an exception escape — it catches it and **returns** a
tagged result — then `pool.map` only ever sees normal return values, so nothing
propagates and the batch can't be aborted by one bad item. You then split the returns
into successes and failures afterwards. (The alternative, `submit` + `as_completed` with
a `try/except` around `fut.result()`, achieves the same isolation at the call site, 6.9.)
Either way, the 999,999 good records are kept and the bad one is logged for inspection —
turning a fatal crash into a line in an errors report.

### The code, every line explained

```python
from concurrent.futures import ProcessPoolExecutor, as_completed

# --- Approach 1: catch INSIDE the worker, return a tagged result --------
def process_safe(record):
    try:
        return ("ok", transform(record))      # success: tagged with "ok"
    except Exception as e:
        return ("error", record["id"], repr(e))   # failure: tagged, carries the id+reason
# No exception ever escapes, so map can't be aborted by a bad item.

if __name__ == "__main__":
    with ProcessPoolExecutor(8) as pool:
        results = list(pool.map(process_safe, records, chunksize=500))

    ok      = [r[1] for r in results if r[0] == "ok"]       # the 999,999 good ones
    errors  = [r for r in results if r[0] == "error"]       # the failures, with reasons
    log.warning("%d/%d records failed", len(errors), len(results))
    write_error_report(errors)                              # inspect/reprocess later

# --- Approach 2: isolate at the CALL SITE with as_completed (6.9) -------
with ProcessPoolExecutor(8) as pool:
    futs = {pool.submit(transform, r): r for r in records}
    for fut in as_completed(futs):
        rec = futs[fut]
        try:
            save(fut.result())                 # .result() re-raises the worker's exception
        except Exception as e:
            record_failure(rec, e)             # log + skip; the batch continues

# --- Worker-process DEATH (segfault / OOM-kill) -------------------------
from concurrent.futures.process import BrokenProcessPool
try:
    with ProcessPoolExecutor(8) as pool:
        list(pool.map(risky, records))
except BrokenProcessPool:
    # a worker process died (not a normal exception) -> the whole pool is unusable.
    # You can't catch this PER-TASK; mitigate by: validating inputs first, capping
    # memory per item, running truly-risky items in a separate restartable process,
    # or using maxtasksperchild (below) so a leaky/crashy worker is recycled.
    log.error("pool broke; restarting with smaller/validated batch")

# --- maxtasksperchild: recycle workers to contain leaks/instability -----
from multiprocessing import Pool
with Pool(8, maxtasksperchild=1000) as pool:   # each worker is replaced after 1000 tasks
    pool.map(process_safe, records)            # bounds damage from slow leaks / bad state
```

### Impact

- **No total loss from one bad item:** a 10-hour job survives malformed inputs — you keep
  every good result and get a report of the failures.
- **Actionable errors:** failures carry their id and reason, so you can inspect, fix, and
  reprocess just the bad ones (pairs with skip-done manifests, Area 7).
- **Resilience to leaks/instability:** `maxtasksperchild` recycles workers so a slow
  memory leak or accumulated bad state can't degrade the whole run.

### Pros & cons / when NOT to

**Reach for failure isolation when:** processing large/messy datasets in parallel, where
some items are expected to fail and the batch must not.

**Watch out / when NOT to:**
- **Don't swallow errors silently** — record id + reason and surface a failure count.
  "Skip and forget" hides data-quality problems; "skip and report" (Area 7) is the goal.
- **Catch specific exceptions where you can.** A blanket `except Exception` in the worker
  is acceptable for isolation, but log the type/message so genuine bugs aren't masked as
  "just another bad row."
- **Process death (`BrokenProcessPool`) can't be caught per-task** — it kills the pool.
  Guard against it by validating inputs, bounding per-item memory, and using
  `maxtasksperchild`; truly crash-prone work needs a restartable subprocess.
- **If *most* items fail, isolation hides a systemic bug** — a 40% failure rate isn't
  "bad rows," it's a broken assumption; investigate rather than logging a million errors.

### Where this shows up

- **Real work — large messy-data pipelines:** featurising/parsing millions of
  real-world records where a fraction are malformed — keep the good, report the bad.
- **Real work — parallel inference/scoring:** isolating items the model chokes on so one
  bad input doesn't kill a batch run.
- **Real work — long jobs that must be resumable:** isolation + per-item failure records
  feed the skip-done/resume machinery (Area 7, 7.7/7.10).
- **Pattern mapping (secondary):** no DSA analogue; it's the fault-isolation principle —
  contain failures at the smallest unit so they don't cascade — shared with circuit
  breakers (5.10) and partial-failure handling (7.9).
[↑ Back to top](#contents)

---

<a id="6.11"></a>
## 6.11 — "Each task reloads the 500 MB model from disk" → per-worker initializer

### The situation

You score 1 million records in parallel with a model that takes 3 seconds to load from
disk:

```python
def score(record):
    model = load_model("model.pkl")       # 500 MB, ~3 seconds to load — EVERY call!
    return model.predict(record)

with ProcessPoolExecutor(8) as pool:
    results = list(pool.map(score, records))   # loads the model 1,000,000 times
```

The model is loaded **inside** `score`, so it's reloaded on every single record — 1
million × 3 seconds of pure loading, dwarfing the actual prediction time. The model is
identical every time; it should be loaded **once per worker** and reused for all the
records that worker handles.

### What's really going on

Expensive **per-worker setup** — loading a model, opening a DB connection, compiling a
regex, initialising a client — should happen **once when the worker starts**, then be
**reused** across all tasks that worker processes. Putting it inside the task function
repeats it per task; passing it as an argument pickles+copies it per task (6.6). Neither
is right.

The fix is the pool's **initializer**: a function run **once per worker process at
startup** that sets up shared, reusable state (stored in a module-level global the task
function reads). With 8 workers, the model loads 8 times total (once each), not 1
million times.

> **initializer** = a function passed to `Pool(initializer=...)` /
> `ProcessPoolExecutor(initializer=...)` that each worker runs **once** before handling
> any tasks. Use it to load models, open connections, or build any costly per-worker
> resource, stored in a global the task function then reuses. These are sometimes called
> **warm workers** — set up once, kept hot across many tasks.

### The move

Load the costly resource in an `initializer` that runs once per worker; the task function
reuses it via a module-level global:

```python
_MODEL = None
def init():
    global _MODEL
    _MODEL = load_model("model.pkl")      # runs ONCE per worker at startup

def score(record):
    return _MODEL.predict(record)         # reuses the already-loaded model

with ProcessPoolExecutor(8, initializer=init) as pool:
    results = list(pool.map(score, records, chunksize=500))
```

### Why it works

When the pool starts a worker process, it calls `init()` **once**, which loads the model
and stashes it in the worker's `_MODEL` global. Every task that worker subsequently runs
calls `score`, which simply reads that already-loaded global — no reloading, no pickling
the model per task. Across 8 workers the 3-second load happens 8 times (24 seconds
total) instead of 1 million times. Because the global lives in the worker's own memory,
it's also not shipped across the process boundary (6.6) — only the small `record` and
result are.

### The code, every line explained

```python
from concurrent.futures import ProcessPoolExecutor

_MODEL = None                             # module-level global, per worker process

def init():
    global _MODEL
    _MODEL = load_model("model.pkl")      # the expensive setup — runs ONCE per worker
    # also a good place to: open a DB connection, build a client/session (5.18),
    # compile regexes (Area 4), set seeds (Area 8) — anything costly + reusable.

def score(record):
    return _MODEL.predict(record)         # reuse the worker's loaded model; no reload

if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=8, initializer=init) as pool:
        results = list(pool.map(score, records, chunksize=500))
        # model loaded 8 times total (once per worker), not 1,000,000 times.

# --- multiprocessing.Pool: same idea, with initargs ---------------------
from multiprocessing import Pool
def init_with_args(model_path):           # initializer can take args via initargs
    global _MODEL
    _MODEL = load_model(model_path)
with Pool(8, initializer=init_with_args, initargs=("model.pkl",)) as pool:
    pool.map(score, records, chunksize=500)

# --- combine with maxtasksperchild carefully ----------------------------
# maxtasksperchild (6.10) recycles workers to contain leaks — but each NEW worker
# re-runs init() (reloads the model). If init is very expensive, a low recycle count
# re-pays that cost often; balance leak-control against re-init cost.

# --- the anti-patterns --------------------------------------------------
# def score(r): model = load_model(...); ...   # WRONG: reloads per task
# pool.map(score, [(model, r) for r in records]) # WRONG: pickles model per task (6.6)
```

### Impact

- **Eliminates repeated setup cost:** the 3-second load is paid 8 times, not a million —
  the job becomes prediction-bound instead of loading-bound.
- **Avoids per-task data transfer:** the model lives in the worker, so it isn't pickled
  into every task (6.6) — saving both time and memory.
- **Clean separation:** setup logic (initializer) is distinct from per-item logic (task
  function), which is easier to read and maintain.

### Pros & cons / when NOT to

**Reach for an initializer when:** workers need an expensive, reusable resource — a
loaded model, a DB/HTTP connection or session (5.18), a compiled regex, a warm client.

**Watch out / when NOT to:**
- **The resource lives in a module-level global** by necessity — acceptable here (it's
  per-worker, set once), but document it; globals are otherwise a smell (Area 10).
- **Each worker holds its own copy** — 8 workers × a 500 MB model = 4 GB. If that's too
  much and the resource is read-only, consider shared memory / memmap (6.8) instead of a
  per-worker copy.
- **`maxtasksperchild` re-runs the initializer** on each recycled worker — if init is
  very expensive, frequent recycling (6.10) re-pays it; tune the two together.
- **Don't put per-*task* state in the initializer** — only things that are the same for
  every task that worker handles. Anything that varies per item belongs in the task
  function.

### Where this shows up

- **Real work — parallel ML inference:** loading the model once per worker, then scoring
  millions of rows — the canonical use; without it, model loading dominates runtime
  (pairs with batch inference, Area 8, 8.10).
- **Real work — DB/API fan-out workers:** opening one connection/session per worker in
  the initializer and reusing it across tasks (connection reuse, 5.18).
- **Real work — heavy preprocessing:** compiling regexes or loading reference data /
  tokenisers once per worker before processing a stream of inputs.
- **Pattern mapping (secondary):** no DSA analogue; it's the "amortise expensive setup by
  reuse" principle (same as session pooling, 5.18, and warm caches) applied to worker
  lifecycle.
[↑ Back to top](#contents)

---

<a id="6.12"></a>
## 6.12 — "My data doesn't fit on one machine, even with all cores busy" → Dask/Spark

### The situation

You've done everything in this area: multiprocessing across all 8 cores (6.2), good
chunksize (6.7), shared memory (6.8). But the dataset is **500 GB** — it doesn't fit in
your machine's 64 GB RAM, and even streaming it through one machine's 8 cores would take
days:

```python
df = pd.read_parquet("500gb_dataset/")    # MemoryError — won't fit on one box
# multiprocessing helps with CORES, but you've run out of MEMORY and single-machine throughput
```

Multiprocessing scales you to one machine's cores. When the **data or compute exceeds a
single machine**, you need a *different* class of tool: a **distributed** framework that
spreads work across **many machines** (a cluster).

### What's really going on

There's a ceiling multiprocessing can't cross: it parallelises across the cores of **one
machine**, bounded by that machine's RAM and CPU. Past that, you need **distributed
computing** — a framework that partitions data and computation across a **cluster** of
machines, handling the hard parts (splitting data, scheduling tasks on nodes, moving
intermediate results, recovering from a node dying) for you.

> **Distributed framework** = software that runs your computation across many machines
> as if they were one. **Dask** (Python-native; mimics pandas/NumPy APIs) and **Apache
> Spark** (JVM-based, with PySpark for Python) are the common choices. They use
> **partitioning** (split the dataset into pieces spread across nodes), **lazy
> execution** (build a plan, then run it optimised), and **fault tolerance** (re-run a
> failed partition on another node).

The realisation: **know the ceiling and step up deliberately.** Don't reach for Spark for
a 2 GB file multiprocessing handles fine (huge complexity for nothing); but don't try to
force a 500 GB join through `multiprocessing.Pool` either. The skill is recognising
*which tier* your problem is in.

### The move

Match the tool to the scale; reach for a distributed framework only when you exceed one
machine:

```python
# Dask: pandas-like API, but partitioned across cores/machines, lazy + out-of-core
import dask.dataframe as dd
df = dd.read_parquet("500gb_dataset/")          # lazy: nothing loaded yet
result = df.groupby("customer").amount.sum()    # builds a plan across partitions
result.compute()                                # NOW it runs, partition by partition
```

### Why it works

Dask/Spark never load the whole 500 GB at once. They split it into **partitions** (say,
thousands of ~128 MB pieces), and each machine/core processes a few partitions at a time
— so the working memory is one partition, not the whole dataset (out-of-core, like
streaming in 1.2 but distributed). Operations are **lazy**: `groupby(...).sum()` records
*what* to do, and `.compute()` triggers an optimised execution that streams partitions
through the cluster and combines partial results (a distributed map-reduce). If a node
dies mid-job, the framework re-runs just its partitions elsewhere — fault tolerance you'd
have to hand-build with raw multiprocessing.

### The code, every line explained

```python
# --- Dask: closest to "pandas that scales" -----------------------------
import dask.dataframe as dd
df = dd.read_parquet("s3://bucket/500gb/")      # lazy handle; reads partitions on demand
big = df[df.amount > 100]                        # lazy; no data moved yet
agg = big.groupby("region").amount.mean()        # still lazy — just a plan
out = agg.compute()                              # executes across all cores/cluster nodes,
                                                 # streaming partitions -> small result
# Same idea for arrays: dask.array mimics NumPy over chunks too big for RAM.

# --- PySpark: the JVM-based heavyweight, common in data engineering -----
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("job").getOrCreate()
sdf = spark.read.parquet("s3://bucket/500gb/")   # distributed DataFrame across the cluster
(sdf.filter(sdf.amount > 100)
    .groupBy("region").avg("amount")
    .write.parquet("s3://bucket/out/"))          # lazy plan; runs on the cluster on write
# PySpark shines for very large ETL, runs on YARN/Kubernetes/Databricks clusters.

# --- The decision ladder: pick the SMALLEST tool that fits --------------
# fits in RAM, 1 core enough        -> plain pandas / a loop
# fits in RAM, CPU-bound            -> multiprocessing / ProcessPoolExecutor (6.2/6.4)
# bigger than RAM, ONE machine      -> chunked/streaming (1.2, 6.5) OR Dask (out-of-core)
# bigger than ONE machine           -> Dask distributed / Spark (a cluster)
# huge + heavy SQL-style ETL        -> Spark, or a data warehouse (BigQuery/Snowflake)

# --- don't over-reach ---------------------------------------------------
# Spark on a 2 GB file: you pay cluster setup, JVM overhead, and serialization for work
# a single pandas/multiprocessing run finishes faster. Distribution is NOT free.
```

### Impact

- **Breaks the single-machine ceiling:** processes datasets far larger than any one
  machine's RAM by spreading them across a cluster.
- **Out-of-core on one machine too:** even without a cluster, Dask streams partitions so
  a 500 GB file runs on a 64 GB box (one partition in memory at a time).
- **Fault tolerance & scheduling for free:** node failures, data partitioning, and task
  scheduling are handled by the framework, not hand-rolled.

### Pros & cons / when NOT to

**Reach for Dask/Spark when:** data exceeds one machine's RAM *and* can't be cheaply
streamed/chunked through it, or compute needs more than one machine's cores.

**Watch out / when NOT to:**
- **Distribution is expensive — don't use it below its tier.** Cluster setup, JVM/network
  overhead, and serialization mean Spark/Dask are often *slower* than pandas +
  multiprocessing for data that fits one machine. Exhaust single-machine options
  (streaming 1.2/6.5, multiprocessing 6.2) first.
- **Debugging is harder** — lazy execution and distributed stack traces are tougher than
  local code; errors surface at `.compute()`/action time, far from where you wrote them.
- **Not everything parallelises well** — operations needing global shuffles (big joins,
  sorts across partitions) move lots of data between nodes and can be slow/costly.
- **Prefer the simplest fit:** sometimes a database/warehouse (BigQuery, Snowflake) or a
  columnar tool (DuckDB, Polars) handles "big-ish on one machine" far more simply than a
  cluster. Pick the smallest tool that clears the bar.

### Where this shows up

- **Real work — large-scale ETL/feature engineering:** Spark/Dask jobs over terabytes of
  logs or events to build training datasets — standard data-engineering territory.
- **Real work — out-of-core analytics:** Dask to run pandas-style analysis on a dataset
  bigger than laptop RAM without a cluster.
- **Real work — distributed ML preprocessing:** partitioning a massive corpus across a
  cluster to featurise/embed it when one machine would take days (Area 9 at scale).
- **Pattern mapping (secondary):** the partition-process-combine model is **distributed
  map-reduce** — the same divide-and-conquer decomposition as 6.2, scaled from cores to
  machines, with fault tolerance added.

[↑ Back to top](#contents)

