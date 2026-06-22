# Area 5 — APIs, I/O & Concurrency

Scenarios about the moment your program stops doing its own work and **waits on
something else** — an API, a database, a disk, another service. The recurring theme
of this area: *waiting is not working*, and most of the craft here is about not
letting your program sit idle, while also not overwhelming the thing you're talking
to.

---

<a id="contents"></a>
## Contents

- [5.1 — "My program spends its life waiting" → recognising I/O-bound work](#5.1)
- [5.2 — "Call thousands of endpoints without waiting one-by-one" → ThreadPoolExecutor](#5.2)
- [5.3 — "Sync vs async — what's the actual difference?" → blocking vs non-blocking](#5.3)
- [5.4 — "I need tens of thousands of concurrent calls without tens of thousands of threads" → asyncio & the event loop](#5.4)
- [5.5 — "I'm in async code but the library I need is blocking" → to_thread & run_in_executor](#5.5)
- [5.6 — "While I wait on the API, I could be preparing the next request" → producer/consumer](#5.6)
- [5.7 — "My job has three stages and each has a different bottleneck" → multi-stage pipelines](#5.7)
- [5.8 — "One hung request froze my whole job overnight" → timeouts as a hard requirement](#5.8)
- [5.9 — "The API fails 1% of the time and my whole job dies" → retry with backoff + jitter](#5.9)
- [5.10 — "A dead dependency made every request wait 10s and time out" → circuit breaker](#5.10)
- [5.11 — "The API keeps returning 429 and rejecting my requests" → client-side rate limiting](#5.11)
- [5.12 — "I need many tasks running, but not ALL at once" → semaphore (concurrency cap)](#5.12)
- [5.13 — "The API only returns 100 results but there are 50,000" → pagination](#5.13)
- [5.14 — "I'm making one API call per item when the API accepts many" → batching](#5.14)
- [5.15 — "The API accepts my job but the result isn't ready yet" → polling](#5.15)
- [5.16 — "My polling either hammers the API or reacts too slowly" → adaptive intervals & deadlines](#5.16)
- [5.17 — "Polling thousands of jobs wastes most of its calls" → webhooks vs polling](#5.17)
- [5.18 — "Every request re-opens a fresh connection and it's slow" → session reuse & pooling](#5.18)
- [5.19 — "I have to wait for the whole 2 GB response before I can use any of it" → streaming](#5.19)
- [5.20 — "My API bill was huge and I have no idea which job caused it" → usage & cost accounting](#5.20)

---


<a id="5.1"></a>
## 5.1 — "My program spends its life waiting" → recognising I/O-bound work

### The situation

You wrote a script that calls an API for each of 5,000 customers to fetch their
latest balance, then writes each result to a database. It's *correct* — but it takes
**40 minutes**. You check your CPU usage while it runs and it's sitting at **2%**.
The machine is almost completely idle, yet the job crawls. Adding a faster CPU
wouldn't help. What's going on?

### What's really going on

Your program is **I/O-bound**. "I/O" means **Input/Output** — any time your code
talks to something *outside* its own memory: a network call, a disk read, a database
query. "I/O-bound" means the total time is dominated by **waiting for those external
things**, not by your CPU doing calculations.

Here's the key mechanic. When you make a network call like `requests.get(url)`, your
program **blocks** — it stops and does nothing — until the response comes back.
"Blocking" means the line of code does not return control to you until it's
finished. A single API round-trip might take 400 milliseconds, but of that, maybe 1
millisecond is your CPU doing work and **399 ms is pure waiting** for the network and
the remote server.

Do that 5,000 times **one after another** (this is called doing them
**sequentially** or **serially** — each one starts only after the previous finishes)
and you get: `5,000 × 400 ms = 2,000,000 ms = ~33 minutes` of mostly *waiting*. The
CPU is at 2% because it genuinely has nothing to do — it's standing in line.

This is the opposite of **CPU-bound** work (Area 6), where the CPU is pinned at 100%
crunching numbers. The two need completely different fixes, so **diagnosing which one
you have is the most important first step** — it decides everything that follows.

### The move

First, just **recognise and confirm** the diagnosis — that's the whole point of this
scenario. The *fix* (running calls concurrently) is 5.2 onward; here you learn to
correctly label the problem so you pick the right fix.

Two quick checks to confirm I/O-bound:

1. **Watch CPU usage while it runs.** Low CPU (single-digit %) + slow = I/O-bound.
   High CPU (one core near 100%) + slow = CPU-bound.
2. **Ask: "what is each second actually spent on?"** If the honest answer is
   "waiting for a reply," it's I/O-bound.

The strategic insight: **I/O-bound work can overlap.** While call #1 is waiting for
its 399 ms reply, your program could already have fired calls #2, #3, … #100. The
waiting happens *in parallel* even on a single CPU core, because waiting doesn't need
the CPU. That overlap is the entire source of the speed-up in the next scenarios.

### Why it works (the intuition you'll reuse all of Area 5)

Think of each API call as **posting a letter and waiting for a reply**. Sequential
processing is posting one letter, then sitting by the letterbox doing nothing for days
until the reply comes, *then* posting the next. Obviously you should post all 5,000
letters first, then handle replies as they arrive. The replies still each take their
own time, but the **waiting overlaps**, so total wall-clock time collapses from
"sum of all waits" toward "the single longest wait."

That is why I/O-bound jobs can often go **10–100× faster** with concurrency, while
the CPU never works any harder — you're just removing idle time, not adding compute.

### Impact

- **Naming it correctly saves you from the wrong fix.** People reach for
  `multiprocessing` (more CPU cores) on I/O-bound work and get almost no speed-up,
  because the bottleneck was never the CPU. Diagnosing "I/O-bound" points you at
  concurrency (threads/async), which is the right lever.
- **Sets a realistic ceiling.** Best case, concurrency takes you from "sum of waits"
  to "longest single wait" — so you can estimate the win *before* coding it.

### Pros & cons / when NOT to

- This scenario is **diagnosis, not a code change** — there's no downside to doing
  it; skipping it is what costs you (you optimise the wrong thing).
- **Caveat:** a job can be *mixed* — e.g. fetch data (I/O-bound) then transform it
  heavily (CPU-bound). Profile to see which dominates (2.1); you may need both a
  concurrency fix *and* a parallelism fix on different stages.

### Where this shows up

- **Real work — bulk API sync:** "fetch X for every customer/order/user," the most
  common slow script in any data team. Almost always I/O-bound.
- **Real work — scraping / crawling:** thousands of page fetches, dominated by
  network wait.
- **Real work — DB-heavy batch jobs:** many small queries in a loop; the program
  waits on the database, not the CPU.
- **Pattern mapping (secondary):** no direct LeetCode analogue — this is a systems/
  ops skill. The closest interview context is system-design rounds, where "is this
  I/O-bound or CPU-bound?" is a question you're *expected* to ask out loud.
[↑ Back to top](#contents)

---

<a id="5.2"></a>
## 5.2 — "Call thousands of endpoints without waiting one-by-one" → ThreadPoolExecutor

### The situation

You confirmed (5.1) that your 5,000-customer fetch is I/O-bound — 33 minutes, CPU at
2%. The serial loop looks like this:

```python
import requests

results = []
for customer_id in customer_ids:              # 5,000 ids
    resp = requests.get(f"https://api/customers/{customer_id}")  # ~400 ms each, BLOCKS
    results.append(resp.json())               # next call can't start until this returns
```

Each `requests.get` blocks for ~400 ms, and the next iteration only begins once the
previous one finishes. You want to have, say, 50 of these requests **in flight at the
same time** so the waiting overlaps — but you don't want to hand-manage threads,
locks, or a results list shared across them.

### What's really going on

The fix for I/O-bound work is **concurrency**: have many requests waiting at once so
their idle time overlaps (5.1). The lowest-effort, highest-value tool for this in
Python is a **thread pool**.

> A **thread** is an independent line of execution inside your program; multiple
> threads can be "running" at once, and crucially, while one thread is *blocked
> waiting* on a network reply, another thread can proceed. A **thread pool** is a
> fixed set of reusable worker threads that pick tasks off a queue — so you create,
> say, 50 threads once and feed 5,000 tasks through them, rather than spawning 5,000
> threads.

You might have heard threads "don't work in Python because of the GIL" (covered in
6.3). That's true for *CPU-bound* work — but **I/O-bound work is exactly where Python
threads shine**, because a thread *releases* the GIL while it waits on I/O, letting
other threads run. So for "call lots of slow endpoints," threads are the right tool,
not a compromise.

`concurrent.futures.ThreadPoolExecutor` is the standard-library wrapper that manages
the pool, the task queue, and result collection for you — no manual thread or lock
code.

### The move

Create a `ThreadPoolExecutor` with a worker count, and use `.map` (results in input
order) or `submit` + `as_completed` (results as they finish):

```python
from concurrent.futures import ThreadPoolExecutor

def fetch(customer_id):
    return requests.get(f"https://api/customers/{customer_id}").json()

with ThreadPoolExecutor(max_workers=50) as pool:   # 50 requests in flight at once
    results = list(pool.map(fetch, customer_ids))  # overlaps all the waiting
```

### Why it works

The pool keeps `max_workers` threads alive. Each thread pulls a `customer_id`, calls
`fetch`, and **while it's blocked waiting** for that ~400 ms reply, Python hands the
GIL to another thread which fires *its* request. So instead of 5,000 waits stacked
end-to-end, you have 50 waits overlapping at any instant. The wall-clock time drops
from `5000 × 400 ms` to roughly `(5000 / 50) × 400 ms` = **~40 seconds** instead of
33 minutes — a ~50× win, bounded by your worker count.

`pool.map(fetch, ids)` mirrors the built-in `map`: it applies `fetch` to each id and
returns results **in the same order as the input**, hiding all the thread mechanics.
The `with` block (Area 1, 1.3) guarantees the pool is shut down and all threads joined
when you leave it, even on error.

### The code, every line explained

```python
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch(customer_id):                          # the work ONE task does
    resp = requests.get(f"https://api/customers/{customer_id}", timeout=10)
    resp.raise_for_status()                      # turn HTTP 4xx/5xx into an exception
    return resp.json()

# --- Simplest: .map, results in INPUT order ------------------------------
with ThreadPoolExecutor(max_workers=50) as pool: # pool of 50 reusable threads
    results = list(pool.map(fetch, customer_ids))
    #               │        │     └ the iterable of inputs
    #               │        └ the function to apply to each
    #               └ returns results in the SAME order as customer_ids
# pool is cleanly shut down here (with-block); threads joined.

# --- submit + as_completed: handle results AS THEY FINISH ----------------
with ThreadPoolExecutor(max_workers=50) as pool:
    # submit() schedules one call and returns a Future — a handle to a result
    # that may not exist yet ("I promise to have this value later").
    future_to_id = {pool.submit(fetch, cid): cid for cid in customer_ids}
    for future in as_completed(future_to_id):    # yields each future the moment it's done
        cid = future_to_id[future]               # look up which id this future was for
        try:
            data = future.result()               # get the return value (or re-raise its error)
            save(cid, data)
        except Exception as e:                   # ONE task failing doesn't kill the rest
            log.warning("customer %s failed: %s", cid, e)
# as_completed lets you process/stream results without waiting for the slowest
# one to finish first — and isolate per-task failures (more in 6.10).

# --- Choosing max_workers (rule of thumb for I/O-bound) ------------------
# I/O-bound: workers can far exceed CPU cores (the threads mostly WAIT), so 20-200
# is typical — limited by the SERVER's tolerance and your rate limit (5.11), not CPU.
# Too many: you hammer the API (429s) or exhaust connections. Start ~20-50, tune.
```

### Impact

- **Speed:** I/O-bound jobs drop from "sum of all waits" to roughly "sum ÷ workers" —
  commonly 20–100× faster, the single biggest win for bulk API/DB scripts.
- **Low effort:** a 3-line change (`with ThreadPoolExecutor... pool.map`) wraps an
  existing function; no thread, lock, or queue code to write or get wrong.
- **Robustness:** `submit` + `as_completed` + per-future `try/except` lets you keep
  every successful result even when some tasks fail.

### Pros & cons / when NOT to

**Reach for ThreadPoolExecutor when:** the work is **I/O-bound** — HTTP calls, DB
queries, file reads, S3/blob downloads — and you want concurrency with minimal code.

**Watch out / when NOT to:**
- **Not for CPU-bound work.** Threads share one Python interpreter; the GIL (6.3) lets
  only one run Python bytecode at a time. For number-crunching you get *no* speed-up —
  use `ProcessPoolExecutor` / multiprocessing (Area 6) instead.
- **Shared mutable state needs care.** If multiple threads update the same list/dict/
  counter, you can get **race conditions** (Area 7). Prefer returning results (as
  shown) over threads mutating shared state; if you must share, use a lock (1.3) or a
  thread-safe `queue.Queue` (5.7).
- **Don't set `max_workers` huge.** 5,000 workers won't make it 5,000× faster — you'll
  exhaust sockets/memory and trigger server rate limits (5.11). Concurrency must be
  *capped* (5.12) and paired with retries (5.9).
- **`requests.Session` per thread / connection reuse** matters at scale — see 5.18.
- **`.map` re-raises the first exception and stops**; if you need per-item failure
  isolation, use `submit` + `as_completed` with a `try/except` as above.

### Where this shows up

- **Real work — bulk enrichment:** fetching a field for every customer/order/document
  from an API or DB — the canonical "make the slow nightly script finish in a minute".
- **Real work — embedding/inference fan-out:** sending many texts to an embedding or
  model-serving endpoint concurrently (pair with batching, 5.14, and rate limits,
  5.11).
- **Real work — downloading many files:** pulling thousands of objects from blob
  storage in parallel before a training run.
- **Pattern mapping (secondary):** no direct algorithm analogue; it's the practical
  realisation of the "overlap the waiting" insight from 5.1, and the foundation the
  rest of Area 5 (timeouts, retries, rate limits) builds on.
[↑ Back to top](#contents)

---

<a id="5.3"></a>
## 5.3 — "Sync vs async — what's the actual difference?" → blocking vs non-blocking

### The situation

You keep seeing two styles of code for the same job and don't know *why* you'd pick
one. The familiar **synchronous** style:

```python
import requests
def get_user(uid):
    return requests.get(f"https://api/users/{uid}").json()   # blocks here
```

and a **asynchronous** style with strange keywords:

```python
import httpx
async def get_user(uid):                                     # note: async def
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api/users/{uid}")     # note: await
        return r.json()
```

You've also been told threads (5.2) already solve I/O concurrency — so what is `async`
/ `await` even *for*, and when does it beat a thread pool?

### What's really going on

The difference is **how a single thread behaves while waiting**.

- **Synchronous / blocking:** when you call `requests.get(...)`, the thread **stops
  dead** until the reply arrives. To do many at once you need many threads (one parked
  per in-flight call) — that's what 5.2 does.
- **Asynchronous / non-blocking:** `await client.get(...)` tells Python *"I'm about to
  wait; while I do, go run other work on this same thread."* One thread juggles
  thousands of in-flight calls by switching to another task each time the current one
  hits an `await` and starts waiting.

> **`async def`** defines a **coroutine** — a function that can *pause itself* at
> `await` points and be resumed later (similar to how a generator pauses at `yield`,
> Area 1 1.2). **`await`** means "pause here until this finishes, and let other
> coroutines run meanwhile." An **event loop** (5.4) is the scheduler that runs many
> coroutines on one thread, switching between them at each `await`.

The key mental model: **threads achieve concurrency with many workers each blocking;
async achieves it with one worker that never blocks — it switches tasks instead.**
Both overlap the waiting; they just pay for it differently.

### The move

Choose based on scale and ecosystem, not fashion:

- **Thread pool (5.2)** — when you have a *moderate* number of I/O tasks (tens to a
  few thousand) and want to reuse ordinary blocking libraries (`requests`, a DB
  driver) with minimal code change. **Default choice for most scripts.**
- **Async (`asyncio`, 5.4)** — when you need *very high* concurrency (tens of
  thousands of simultaneous connections), or you're already in an async framework
  (FastAPI, aiohttp), where blocking would stall everything.

### Why it works

A blocked thread still costs real memory (each thread needs its own stack, ~MBs) and
the OS must context-switch between them — so "one thread per in-flight call" stops
scaling somewhere in the low thousands. Async keeps all that state as lightweight
coroutine objects on **one** thread, so 10,000 idle-waiting connections cost kilobytes,
not gigabytes. That's why async wins at extreme connection counts.

But async has a catch that defines when *not* to use it: the single thread must
**never block**. One accidental synchronous call (a plain `requests.get`, a heavy CPU
computation) freezes *every* coroutine, because they all share that one thread. Threads
don't have this trap — one blocked thread doesn't stop the others.

### The code, every line explained

```python
# --- Synchronous: the thread blocks at each call ------------------------
import requests
def get_user(uid):
    return requests.get(f"https://api/users/{uid}").json()  # thread parks here ~400ms

for uid in uids:            # strictly one at a time unless you add threads (5.2)
    print(get_user(uid))

# --- Asynchronous: one thread juggles many calls ------------------------
import asyncio, httpx

async def get_user(client, uid):          # async def -> a coroutine
    r = await client.get(f"https://api/users/{uid}")   # await: pause, let others run
    return r.json()

async def main(uids):
    async with httpx.AsyncClient() as client:          # async-capable HTTP client
        tasks = [get_user(client, uid) for uid in uids] # create many coroutines...
        return await asyncio.gather(*tasks)             # ...run them CONCURRENTLY on 1 thread
        # gather schedules all tasks; each yields control at its await, so while one
        # waits on the network, another's request is sent. (More in 5.4.)

results = asyncio.run(main(uids))          # asyncio.run starts the event loop, runs main

# --- The fatal async mistake: a BLOCKING call inside async --------------
async def bad(uid):
    return requests.get(...).json()        # WRONG: requests BLOCKS the whole event loop
    # every other coroutine is frozen for those 400ms. Use an async client, OR push
    # the blocking call to a thread with asyncio.to_thread (5.5).
```

### Impact

- **Right-tool clarity:** you stop cargo-culting async into scripts where a thread
  pool is simpler, and you stop forcing threads where 50,000 connections need async.
- **Scale ceiling:** async raises the practical concurrency ceiling from ~thousands
  (threads) to tens/hundreds of thousands (coroutines) on one machine.
- **Latency under load:** in a server, non-blocking handlers keep serving other
  requests while one waits on a DB/API — higher throughput per core.

### Pros & cons / when NOT to

**Use threads (5.2) when:** moderate concurrency, existing blocking libraries, you
want the least code. This is the pragmatic default.

**Use async when:** extreme connection counts, an already-async stack, or long-lived
connections (websockets, streaming).

**Watch out:**
- **Async is "all or nothing".** It only helps if the whole call chain is async; one
  blocking call (sync HTTP, CPU work, `time.sleep`) stalls everything. Use
  `await asyncio.sleep`, async libraries, and `asyncio.to_thread` (5.5) for unavoidable
  blocking bits.
- **Async has a learning/debugging cost** — coloured functions (5.5), trickier
  tracebacks. Don't pay it for a one-off batch script a thread pool handles fine.
- **Neither helps CPU-bound work** — that's Area 6 (multiprocessing).

### Where this shows up

- **Real work — high-fanout API clients:** scraping or syncing tens of thousands of
  endpoints where a thread-per-call would exhaust memory → async.
- **Real work — async web services:** FastAPI/aiohttp handlers that call a DB and other
  services; making them `async` keeps the server responsive under load.
- **Real work — moderate batch scripts:** the nightly "fetch 5,000 records" job —
  a thread pool (5.2) is the simpler, correct pick; async would be over-engineering.
- **Pattern mapping (secondary):** the coroutine pause/resume model is the same
  cooperative-scheduling idea as generators (1.2); no direct DSA analogue.
[↑ Back to top](#contents)

---

<a id="5.4"></a>
## 5.4 — "I need tens of thousands of concurrent calls without tens of thousands of threads" → asyncio & the event loop

### The situation

You need to check the health of 50,000 URLs as fast as possible. A thread pool (5.2)
with 50,000 workers is out — each thread costs ~MBs of stack, so that's tens of GB of
memory plus crippling OS context-switching. Even 500 threads only gives you 500
concurrent checks. You decided async is the right tool (5.3); now you actually have to
write it, and you're staring at `async`, `await`, `gather`, "event loop" and unsure
how they fit together.

### What's really going on

`asyncio` is Python's built-in framework for running thousands of coroutines on a
**single thread**, coordinated by an **event loop**.

> The **event loop** is a scheduler that holds a list of ready-to-run coroutines. It
> runs one until that coroutine hits an `await` on something slow (a network reply);
> at that point the coroutine *yields control* back to the loop, which immediately
> runs the next ready coroutine. When the slow thing finishes, the loop wakes the
> original coroutine where it paused. One thread, thousands of tasks, switching at
> every `await`.

Because each paused coroutine is just a small object (not an OS thread), 50,000 of
them cost megabytes, not tens of gigabytes. The event loop is **cooperative**: tasks
voluntarily give up control at `await` points. Nothing is pre-empted — which is the
power (cheap, no locks needed for single-threaded state) and the danger (one task that
never awaits, e.g. a CPU loop or blocking call, hogs the loop and freezes all others).

The building blocks you need: `asyncio.run` (start the loop), `async def` (define a
coroutine), `await` (pause on something async), and `asyncio.gather` /
`asyncio.as_completed` (run many coroutines concurrently and collect results).

### The move

Define async work, fan it out with `gather`, and bound it with a semaphore (5.12):

```python
import asyncio, httpx

async def check(client, url, sem):
    async with sem:                                  # cap concurrency (don't open 50k at once)
        r = await client.get(url, timeout=10)
        return url, r.status_code

async def main(urls):
    sem = asyncio.Semaphore(200)                     # at most 200 in flight at a time
    async with httpx.AsyncClient() as client:
        tasks = [check(client, u, sem) for u in urls]
        return await asyncio.gather(*tasks)

results = asyncio.run(main(urls))
```

### Why it works

`asyncio.run(main(...))` creates the event loop and runs `main` until done.
`asyncio.gather(*tasks)` hands all the coroutines to the loop at once; each runs until
its `await client.get(...)`, then yields, letting the loop start the next — so hundreds
of requests are genuinely in flight on one thread. As each reply arrives, the loop
resumes that coroutine to finish it. `gather` returns all results once every task
completes, **in the order of the inputs**.

The `asyncio.Semaphore(200)` (5.12) is essential at this scale: without it `gather`
would try to open all 50,000 connections instantly and you'd exhaust file descriptors
or get rate-limited. `async with sem` lets only 200 coroutines past at a time; the rest
wait their turn — at an `await`, so they cost nothing while waiting.

### The code, every line explained

```python
import asyncio, httpx

async def check(client, url, sem):
    async with sem:                          # acquire a slot; auto-released on exit (1.3)
        try:
            r = await client.get(url, timeout=10)   # pause here; loop runs others
            return url, r.status_code               # resumed when the reply lands
        except Exception as e:
            return url, f"error: {e}"               # isolate failures per task

async def main(urls):
    sem = asyncio.Semaphore(200)             # concurrency cap: 200 simultaneous requests
    async with httpx.AsyncClient() as client:# one shared client = reused connections (5.18)
        tasks = [check(client, u, sem) for u in urls]   # 50,000 coroutine objects (cheap!)
        return await asyncio.gather(*tasks)  # run all concurrently; results in input order

results = asyncio.run(main(urls))            # start event loop, run to completion, stop it

# --- Stream results as they finish (instead of waiting for all) ----------
async def main_streaming(urls):
    sem = asyncio.Semaphore(200)
    async with httpx.AsyncClient() as client:
        tasks = [asyncio.create_task(check(client, u, sem)) for u in urls]
        for coro in asyncio.as_completed(tasks):   # yields each task as it completes
            url, status = await coro               # process the fastest-finishing first
            handle(url, status)

# --- gather with return_exceptions: don't let one failure cancel all -----
results = await asyncio.gather(*tasks, return_exceptions=True)
# Without this, the first exception propagates and cancels the gather. With it,
# exceptions come back as result values you can filter — like per-task isolation.

# --- NEVER block the loop -------------------------------------------------
# await asyncio.sleep(1)   # CORRECT: non-blocking pause, loop runs others
# time.sleep(1)            # WRONG: freezes the ENTIRE loop for 1 second
```

### Impact

- **Extreme concurrency, tiny memory:** 50,000 in-flight checks on one thread in
  megabytes — impossible with one-thread-per-call.
- **Throughput:** for huge fan-out, async typically beats a thread pool because it
  isn't capped by thread/memory limits and avoids OS context-switch overhead.
- **Composability:** `gather`, `as_completed`, semaphores, timeouts all compose into
  clean high-concurrency pipelines.

### Pros & cons / when NOT to

**Reach for asyncio when:** you need very high I/O concurrency, long-lived connections
(websockets/streaming), or you're in an async framework already.

**Watch out / when NOT to:**
- **One blocking call freezes everything.** No `requests`, no `time.sleep`, no heavy
  CPU in a coroutine — use async libraries, `asyncio.sleep`, and `asyncio.to_thread`
  (5.5) for unavoidable blocking work.
- **Always cap concurrency** with a `Semaphore` (5.12) and set per-request `timeout`s
  (5.8) — unbounded `gather` over 50k tasks will exhaust sockets or trip rate limits
  (5.11).
- **`gather` cancels all on the first exception** unless you pass
  `return_exceptions=True` — easy way to lose 49,999 good results to one bad URL.
- **Don't adopt async for a small job** a thread pool handles in 5 lines (5.2/5.3) —
  the complexity isn't free.

### Where this shows up

- **Real work — mass health checks / crawling:** probing tens of thousands of URLs,
  endpoints, or hosts as fast as the network and rate limits allow.
- **Real work — async API gateways/services:** a FastAPI service fanning out to many
  downstream services per request without blocking its worker.
- **Real work — high-throughput LLM/embedding pipelines:** issuing thousands of
  concurrent model calls bounded by a semaphore tuned to your rate limit (5.11/5.12).
- **Pattern mapping (secondary):** the event loop is a cooperative scheduler over a
  ready-queue — conceptually a queue-driven traversal; the same "bounded in-flight set"
  idea recurs in producer/consumer (5.6) and worker pools (Area 7).
[↑ Back to top](#contents)

---

<a id="5.5"></a>
## 5.5 — "I'm in async code but the library I need is blocking" → to_thread & run_in_executor

### The situation

Your service is async (5.4), but you must call something that only has a **blocking**
API — a legacy DB driver, an SDK with no async version, or a CPU-ish parse:

```python
async def handle(request):
    user = await db.fetch(request.id)        # fine — async
    pdf = generate_pdf(user)                 # BLOCKING: a sync library, ~2 seconds
    return pdf
```

That `generate_pdf` is synchronous. The instant it runs, it **freezes the entire event
loop** for 2 seconds — every other concurrent request your service is handling stalls,
because they all share the one thread (5.3/5.4). Your async server's throughput
collapses whenever this code path is hit.

### What's really going on

The async event loop's golden rule is **never block the loop thread**. A blocking call
doesn't `await`, so it never yields control — the scheduler can't switch to other
coroutines, and they're all stuck behind it.

The fix is to **move the blocking work off the loop thread onto a separate thread (or
process)**, then `await` its completion. That way the loop only sees a normal awaitable
— it parks the current coroutine and keeps serving everyone else, while the blocking
work runs elsewhere.

> This is the practical face of the **"function colour" problem**: in Python, `async`
> functions and normal functions are different "colours" — you can `await` an async
> function from async code, but calling a *blocking* function from async code is the
> dangerous mismatch. `asyncio.to_thread` is the bridge that lets async code safely
> call blocking ("sync-coloured") functions without freezing the loop.

The standard bridge is **`asyncio.to_thread(func, *args)`** (Python 3.9+), or the
lower-level **`loop.run_in_executor(executor, func, *args)`**.

### The move

Wrap the blocking call in `await asyncio.to_thread(...)`:

```python
async def handle(request):
    user = await db.fetch(request.id)
    pdf = await asyncio.to_thread(generate_pdf, user)   # run blocking work off-loop
    return pdf
```

### Why it works

`asyncio.to_thread(generate_pdf, user)` hands the blocking function to a background
thread pool and returns an **awaitable**. When you `await` it, the current coroutine
parks (like any `await`), so the event loop is free to run other requests. The blocking
2-second `generate_pdf` now ties up a *worker thread*, not the loop — and because that
thread is blocked on I/O or releases the GIL during the heavy bit, the loop keeps
serving everyone else. When `generate_pdf` returns, the loop resumes your coroutine
with its result.

For **CPU-bound** blocking work (pure number-crunching that holds the GIL), a thread
won't give real parallelism (6.3) — there you pass a `ProcessPoolExecutor` to
`run_in_executor` so it runs in a separate *process* (Area 6).

### The code, every line explained

```python
import asyncio

# --- to_thread: the simple bridge (3.9+) --------------------------------
async def handle(request):
    user = await db.fetch(request.id)                 # async call: fine
    pdf = await asyncio.to_thread(generate_pdf, user) # blocking call: off-loaded to a thread
    #           │                 │            └ args passed straight to generate_pdf
    #           │                 └ the blocking function (do NOT call it — pass it)
    #           └ returns an awaitable; await parks the coroutine, frees the loop
    return pdf

# --- run_in_executor: the explicit form, choose your pool ---------------
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

async def handle_cpu(data):
    loop = asyncio.get_running_loop()                 # the current event loop
    # For CPU-bound work, use a PROCESS pool so it truly runs in parallel (Area 6):
    with ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, heavy_compute, data)
        #                                   │     │            └ arg
        #                                   │     └ the blocking/CPU function
        #                                   └ None = default thread pool; or pass your own
    return result

# --- The reverse direction: call ASYNC code from SYNC code --------------
# If you're in normal sync code and need to run a coroutine once:
result = asyncio.run(some_coroutine(x))   # starts a loop, runs it, returns result
# But you can't call asyncio.run if a loop is ALREADY running (e.g. inside async) —
# that raises RuntimeError. Within async, just `await` the coroutine directly.

# --- The mistake to avoid -----------------------------------------------
async def bad(user):
    return generate_pdf(user)             # WRONG: blocks the loop for 2s, stalls all
                                          # other requests. Must wrap in to_thread.
```

### Impact

- **Keeps the loop responsive:** one slow blocking call no longer freezes every other
  concurrent request — throughput under load is preserved.
- **Incremental adoption:** lets an async service use blocking libraries it can't
  replace yet, instead of rewriting everything at once.
- **Right pool for the job:** thread pool for blocking I/O, process pool for CPU work —
  both reachable through the same `run_in_executor` door.

### Pros & cons / when NOT to

**Reach for `to_thread`/`run_in_executor` when:** async code must call a blocking
function (legacy SDK, sync DB driver, file/CPU work) you can't make async.

**Watch out / when NOT to:**
- **Threads don't parallelise CPU work** (GIL, 6.3). If `func` is pure CPU, use a
  `ProcessPoolExecutor`, not `to_thread`, or you'll just move the freeze to a thread
  that still can't run in parallel.
- **Off-loaded work still consumes a worker thread** — fire thousands of `to_thread`
  calls and you exhaust the default thread pool. Bound it (its own executor with a set
  size) and pair with a semaphore (5.12).
- **Prefer a native async library when one exists.** `to_thread` is a bridge, not a
  goal — an async DB driver/HTTP client (5.4) is cleaner than wrapping the blocking one
  on every call.
- **Don't `asyncio.run` inside a running loop** — it errors. Use `await` directly when
  already in async code.

### Where this shows up

- **Real work — async web service + legacy dependency:** a FastAPI handler that must
  call a synchronous DB driver, file encoder, or vendor SDK without stalling the server.
- **Real work — mixed pipelines:** an async fetch stage (5.4) feeding a blocking
  parse/transform that you push to a thread (I/O-ish) or process (CPU) pool.
- **Real work — calling sync ML libraries from async serving:** wrapping a blocking
  `model.predict(...)` so the async request handler stays responsive (CPU-heavy →
  process pool / dedicated inference workers).
- **Pattern mapping (secondary):** no DSA analogue; it's the practical glue between the
  two concurrency models (5.2 threads, 5.4 async) and resolves the function-colour
  mismatch in real codebases.
[↑ Back to top](#contents)

---

<a id="5.6"></a>
## 5.6 — "While I wait on the API, I could be preparing the next request" → producer/consumer

### The situation

Your pipeline alternates between two kinds of work: it **reads/prepares** a record
(CPU/disk), then **sends** it to a slow API (network wait), in a single loop:

```python
for row in read_big_file("data.csv"):        # step A: parse a row (~5 ms, local)
    payload = transform(row)                  # step B: build the request (~5 ms, local)
    send_to_api(payload)                      # step C: POST it (~400 ms, network WAIT)
```

While step C waits 400 ms for the API, steps A and B for the *next* row sit idle —
they could be running *during* that wait. Right now the local work and the network
wait happen strictly one after another, so each iteration costs `5 + 5 + 400 ms` and
the CPU does nothing for 98% of it.

### What's really going on

You have two stages with very different bottlenecks — a **fast local producer**
(read+transform) and a **slow network consumer** (send) — chained so each waits for the
other. The realisation: these stages are *independent per item*, so they can run **at
the same time** on different threads. While the consumer is blocked sending row N, the
producer can already be reading and transforming rows N+1, N+2…

This is the **producer/consumer pattern**: one (or more) threads *produce* work items
and put them on a shared **queue**; one (or more) threads *consume* items off that
queue. The queue is the buffer between them that lets each run at its own pace.

> A **queue** here is a thread-safe FIFO (first-in-first-out) buffer:
> `queue.Queue`. "Thread-safe" means multiple threads can `put` and `get` from it
> concurrently without corrupting it or needing your own locks — the queue handles the
> synchronisation internally. It also *blocks* a consumer that calls `get()` on an
> empty queue (it waits for an item) and can block a producer when the queue is full
> (natural backpressure, 5.x / Area 7).

This is exactly the "overlap the wait with useful work" idea you described: one worker
prepares data while another talks to the API.

### The move

Put a `queue.Queue` between a producer thread (reads+transforms) and consumer threads
(send), using a sentinel value to signal "no more work":

```python
import queue, threading

q = queue.Queue(maxsize=1000)          # bounded buffer between the stages
```

### Why it works

The producer and consumers run on separate threads, so the OS/Python interpreter runs
them concurrently — and because the consumer is **I/O-bound** (blocked waiting on the
API, releasing the GIL, 6.3), the producer's CPU work genuinely proceeds during that
wait. The queue decouples their speeds: the producer races ahead and fills the buffer;
the consumers drain it as fast as the API allows. Total time stops being
`sum(prepare + send)` and becomes roughly `max(total_prepare_time, total_send_time)` —
dominated by whichever stage is slower (here, the network), with the faster stage's
cost hidden underneath it.

The **bounded** queue (`maxsize`) is what stops the fast producer from reading the
entire 10 GB file into memory when the slow consumer can't keep up: once the buffer is
full, `q.put()` blocks until a consumer frees a slot — automatic **backpressure**.

### The code, every line explained

```python
import queue, threading

q = queue.Queue(maxsize=1000)          # holds at most 1000 pending items (backpressure)
DONE = object()                        # a unique SENTINEL marking "no more items"
                                       # (a private object — can't collide with real data)

def producer(path):
    for row in read_big_file(path):    # read + transform: the FAST local stage
        q.put(transform(row))          # blocks if the queue is full (consumer behind)
    q.put(DONE)                        # signal the consumer that the stream has ended

def consumer():
    while True:
        item = q.get()                 # blocks until an item is available
        if item is DONE:               # saw the end-of-stream marker?
            q.put(DONE)                 # put it back so OTHER consumers also stop
            q.task_done()
            break
        try:
            send_to_api(item)          # the SLOW network stage (overlaps producer)
        finally:
            q.task_done()              # mark this item handled (pairs with q.join())

# --- wire it up: 1 producer, several consumers --------------------------
prod = threading.Thread(target=producer, args=("data.csv",))
cons = [threading.Thread(target=consumer) for _ in range(8)]   # 8 senders in parallel
prod.start(); [c.start() for c in cons]
prod.join();  [c.join() for c in cons]     # wait for everything to finish

# NOTE: with multiple consumers, the simplest robust shutdown is to put ONE DONE per
# consumer (or the "put it back" trick above). For most jobs, ThreadPoolExecutor (5.2)
# is simpler — reach for an explicit queue when stages have DIFFERENT speeds/worker
# counts, or when producing and consuming are genuinely different kinds of work.
```

### Impact

- **Wall-clock:** the local prepare time disappears under the network wait — the job
  runs in roughly the time of its slowest stage, not the sum of both.
- **Bounded memory:** the `maxsize` queue means you never load the whole input; you
  buffer at most N items regardless of file size (works on streams bigger than RAM).
- **Independent tuning:** you can scale the slow stage (more consumer threads) without
  touching the producer — match worker counts to where the bottleneck is.

### Pros & cons / when NOT to

**Reach for producer/consumer when:** stages have *different* throughputs or are
*different kinds* of work (read vs send, decode vs upload), and you want them to overlap
with a buffer between them.

**Watch out / when NOT to:**
- **For "just run this function over many items concurrently," use `ThreadPoolExecutor`
  (5.2)** — it *is* a producer/consumer internally, with far less code. Hand-rolling a
  queue is worth it only when stages differ or you need a custom topology.
- **Shutdown is the tricky part.** Forgetting to signal completion leaves consumers
  blocked on `q.get()` forever (a hang). Use a sentinel (as above) or
  `q.join()` + daemon threads; get this right or the program never exits.
- **Use a *bounded* queue.** An unbounded `Queue()` lets a fast producer fill memory if
  consumers stall — set `maxsize` for backpressure (Area 7).
- **Don't share other mutable state between the threads** beyond the queue without a
  lock (1.3) — the queue is safe, your global dict is not (races, Area 7).

### Where this shows up

- **Real work — ETL with a slow sink:** parse/transform local rows fast, write to a
  slow API/DB; the producer prepares while consumers write.
- **Real work — download→process pipelines:** one thread downloads files, several
  threads decode/parse them — overlap network with CPU.
- **Real work — log/event shipping:** application threads (producers) drop events on a
  queue; a background sender thread batches and ships them, so request handlers never
  block on the network.
- **Pattern mapping (secondary):** the bounded-buffer/queue handoff is a classic
  concurrency pattern; the FIFO queue itself is the same structure used in BFS
  (Area 11), here coordinating threads instead of graph nodes.
[↑ Back to top](#contents)

---

<a id="5.7"></a>
## 5.7 — "My job has three stages and each has a different bottleneck" → multi-stage pipelines

### The situation

Building on 5.6, your job now has **three** sequential stages with very different
speeds, processing 100,000 documents:

```
stage 1: download doc      (~300 ms, network)   <- I/O-bound
stage 2: extract text      (~50 ms, CPU)         <- CPU-ish
stage 3: upload embedding  (~400 ms, network)    <- I/O-bound
```

A single loop does all three per item, so each document costs `300 + 50 + 400 =
750 ms`, and the three stages constantly idle while waiting for each other. Worse, the
*right number of workers differs per stage*: the two network stages need lots of
concurrency, the CPU stage needs only a few. One thread pool can't express that.

### What's really going on

This is a **pipeline**: stages chained by queues, where each stage is its own pool of
workers sized to *its* bottleneck. It generalises producer/consumer (5.6) to N stages —
each stage consumes from the queue before it and produces to the queue after it.

The realisation: stages with different bottlenecks should have **independent worker
counts**, and the queues between them absorb the speed mismatches. The slow network
stages get many workers (they mostly wait); the CPU stage gets few (more wouldn't help
under the GIL, 6.3). Each item flows stage1 → queue → stage2 → queue → stage3, and all
three stages run *simultaneously* on different items — like a factory assembly line
where every station is busy on a different unit at once.

The throughput of the whole pipeline becomes the throughput of its **slowest stage**
(the bottleneck), not the sum — so you scale workers on that one stage to widen it.

### The move

Give each stage its own thread pool sized to its bottleneck, connected by bounded
queues:

```python
download_pool = ThreadPoolExecutor(max_workers=40)   # network: many workers
extract_pool  = ThreadPoolExecutor(max_workers=4)    # CPU: few workers (GIL)
upload_pool   = ThreadPoolExecutor(max_workers=40)   # network: many workers
```

### Why it works

Each stage runs in parallel on different items, and each is sized to its own
constraint. The network stages get 40 workers because they spend their time *waiting*
(threads release the GIL during I/O, so 40 can wait at once); the CPU stage gets only 4
because the GIL (6.3) means extra threads wouldn't compute faster — more would just add
overhead. The bounded queues between stages let a fast stage run ahead a little, then
apply backpressure (block) when the next stage falls behind, keeping memory flat. The
pipeline fills up and then all three stages stay continuously busy, so end-to-end
throughput equals that of the single slowest stage instead of the sum of all three.

### The code, every line explained

```python
import queue, threading
from concurrent.futures import ThreadPoolExecutor

q1 = queue.Queue(maxsize=200)          # between download and extract
q2 = queue.Queue(maxsize=200)          # between extract and upload
DONE = object()                        # end-of-stream sentinel (5.6)

def stage_download(doc_ids):
    with ThreadPoolExecutor(max_workers=40) as pool:        # 40 concurrent downloads
        # map keeps it simple; each finished download is pushed to the next queue
        for raw in pool.map(download, doc_ids):
            q1.put(raw)                # blocks if extract stage is behind (backpressure)
    q1.put(DONE)                       # signal stage 2 that downloads are finished

def stage_extract():
    with ThreadPoolExecutor(max_workers=4) as pool:         # only 4 — CPU-bound (GIL)
        while True:
            raw = q1.get()
            if raw is DONE:
                q2.put(DONE); break    # propagate the sentinel downstream
            # submit returns a Future; chain its result onto q2 when ready
            fut = pool.submit(extract_text, raw)
            q2.put(fut.result())       # (simple/sequential per item; see note below)

def stage_upload():
    with ThreadPoolExecutor(max_workers=40) as pool:        # 40 concurrent uploads
        futures = []
        while True:
            text = q2.get()
            if text is DONE: break
            futures.append(pool.submit(upload_embedding, text))
        for f in futures: f.result()   # surface any upload errors

# run the three stages as concurrent threads
threads = [threading.Thread(target=stage_download, args=(doc_ids,)),
           threading.Thread(target=stage_extract),
           threading.Thread(target=stage_upload)]
for t in threads: t.start()
for t in threads: t.join()
# NOTE: this is the readable shape. For production, libraries/frameworks (e.g. a task
# queue, Ray, or asyncio pipelines) handle the plumbing; hand-roll only for clarity or
# simple cases. The KEY idea is per-stage worker counts + bounded queues between them.
```

### Impact

- **Throughput = slowest stage, not the sum:** the 750 ms/item serial cost collapses
  toward the bottleneck stage's per-item time, often a multi-× speed-up.
- **Targeted scaling:** widen only the bottleneck (more workers on the slow network
  stage) instead of uniformly — efficient use of threads.
- **Bounded memory:** queues with `maxsize` keep at most a few hundred in-flight items
  regardless of the 100,000 total.

### Pros & cons / when NOT to

**Reach for a multi-stage pipeline when:** the job has *distinct stages with different
bottlenecks* (network vs CPU vs disk) and one global pool can't size them
independently.

**Watch out / when NOT to:**
- **Complexity jumps** — multiple pools, queues, and sentinels mean more shutdown/error
  edge cases. For a single kind of work, one `ThreadPoolExecutor` (5.2) is far simpler;
  don't build a pipeline you don't need.
- **The CPU stage is the real ceiling.** If extract-text is genuinely CPU-heavy, threads
  won't parallelise it (GIL, 6.3) — move *that stage* to a `ProcessPoolExecutor` or
  separate processes (Area 6), keeping the network stages on threads.
- **Shutdown/error propagation across stages is fiddly** — a failure in stage 2 must not
  leave stage 1 blocked on a full queue. Bound queues, propagate sentinels, and consider
  a real framework for anything long-lived.
- **Don't over-parallelise network stages** — 40 workers × a rate-limited API = 429s
  (5.11); cap to what the service allows (5.12).

### Where this shows up

- **Real work — RAG/embedding ingestion:** download docs → extract/clean text → embed &
  upsert to a vector store, each stage sized differently — a very common ML data
  pipeline.
- **Real work — media/ETL processing:** fetch → decode/transform → store, where decode
  is CPU and fetch/store are I/O.
- **Real work — streaming enrichment:** read from a source → call enrichment APIs →
  write to a sink, with the slow API stage given the most workers.
- **Pattern mapping (secondary):** the assembly-line/pipeline model; the per-stage queues
  are FIFOs (BFS-style structure, Area 11) used here for cross-stage coordination and
  backpressure.
[↑ Back to top](#contents)

---

<a id="5.8"></a>
## 5.8 — "One hung request froze my whole job overnight" → timeouts as a hard requirement

### The situation

Your nightly job calls an API for 10,000 records. It usually finishes in minutes. One
morning you find it **still running after 9 hours** — stuck on a single request:

```python
resp = requests.get(url)        # NO timeout -> can wait FOREVER
```

The remote server accepted the connection but never sent a response (it hung, or a
network device silently dropped the return path). With no timeout, `requests.get`
waits **indefinitely** — the whole job is frozen on record #3,847, and every record
after it never runs.

### What's really going on

By default, many network calls have **no timeout** — they'll wait forever for a reply
that may never come. A network call has several phases that can each stall: the
**connect** (establishing the TCP connection) and the **read** (waiting for response
bytes after connecting). A server that's overloaded, a dropped packet on the return
path, or a load balancer that holds the connection open can all leave you blocked with
no error and no progress.

The realisation: **a call with no timeout is a latent hang.** In production, "wait
forever" is never the behaviour you want — you'd rather the call *fail fast* after a
bounded time so you can retry it (5.9), skip it, or log it, and keep the job moving. A
timeout converts an invisible infinite hang into a normal, catchable error.

> A **timeout** is a maximum time you'll wait before the call gives up and raises an
> exception (e.g. `requests.exceptions.Timeout`). It's not "how long the work should
> take" — it's "the point past which something is clearly wrong."

### The move

**Always pass an explicit timeout** to every network call, and catch the timeout error:

```python
resp = requests.get(url, timeout=(3.05, 10))   # (connect timeout, read timeout) in seconds
```

### Why it works

The timeout tells the underlying socket: if no connection is established within the
connect budget, or no data arrives within the read budget, **stop waiting and raise**.
That turns an unbounded hang into a `Timeout` exception you can handle like any other
failure — retry it, skip it, or record it — so one bad request can no longer halt the
remaining 6,000. Setting connect and read separately lets you fail fast on an
unreachable host (short connect) while still allowing a slow-but-working endpoint enough
time to respond (longer read).

### The code, every line explained

```python
import requests
from requests.exceptions import Timeout, RequestException

# --- requests: timeout is a tuple (connect, read) or a single number ----
try:
    resp = requests.get(url, timeout=(3.05, 10))
    #                            │      └ READ: max seconds to wait for response data
    #                            └ CONNECT: max seconds to establish the connection
    #   (the odd 3.05 is a common convention — slightly over a multiple of 3s, which
    #    aligns with how TCP connection retries are timed; any small value is fine.)
    resp.raise_for_status()                   # 4xx/5xx -> HTTPError
    data = resp.json()
except Timeout:
    log.warning("timed out on %s — will retry/skip", url)   # bounded failure, not a hang
    data = None
except RequestException as e:                 # any other network/HTTP error
    log.warning("request failed on %s: %s", url, e)
    data = None

# --- A single number applies to BOTH phases -----------------------------
requests.get(url, timeout=10)                 # 10s for connect AND 10s for read

# --- httpx (async, 5.4) has the same idea -------------------------------
# await client.get(url, timeout=10.0)         # raises httpx.TimeoutException

# --- Timeout on YOUR OWN concurrent tasks (ThreadPoolExecutor, 5.2) -----
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
with ThreadPoolExecutor(max_workers=20) as pool:
    fut = pool.submit(slow_function, arg)
    try:
        result = fut.result(timeout=30)       # wait at most 30s for THIS task's result
    except FuturesTimeout:
        result = None                          # NOTE: the worker thread keeps running —
        # a future's timeout stops YOU waiting, it doesn't kill the underlying work.
        # Only a real cancellable operation (or a separate process) can be truly stopped.

# --- The anti-pattern --------------------------------------------------
resp = requests.get(url)                       # NO timeout -> potential infinite hang.
# Lint rule / code-review check: every network call MUST pass timeout=.
```

### Impact

- **No more silent hangs:** a stuck endpoint fails in seconds instead of freezing the
  whole job indefinitely — the difference between "ran overnight doing nothing" and
  "skipped 3 bad records, finished on time."
- **Composability:** a bounded failure can be *retried* (5.9), routed to a fallback
  (5.10), or logged — none of which is possible while you're hung forever.
- **Predictable worst case:** with timeouts you can compute a job's maximum runtime;
  without them it's unbounded.

### Pros & cons / when NOT to

**Reach for timeouts:** on **every** network/external call, always. There is essentially
no case where "wait forever" is the right default in production code.

**Watch out / when NOT to:**
- **Too short a timeout causes false failures** — a legitimately slow but healthy
  endpoint gets killed and retried needlessly, adding load. Set the read timeout above
  the endpoint's realistic p99 latency, not its average.
- **A future's `.result(timeout=)` doesn't cancel the work** — it only stops *you*
  waiting; the thread keeps running in the background. To truly abort, you need a
  cancellable operation or a separate process you can terminate (Area 6).
- **Timeouts must be paired with retries** (5.9) — failing fast is only useful if
  something then handles the failure. A timeout that just crashes the job isn't much
  better than a hang.
- **`time.sleep`/CPU loops can't be timed out** by socket timeouts — those are for I/O;
  bounding CPU work needs a different mechanism (process + kill, Area 6).

### Where this shows up

- **Real work — every API/DB client:** the universal first hardening step on any
  outbound call; most production incidents involving "stuck" jobs trace back to a
  missing timeout.
- **Real work — bulk jobs (5.2):** combined with a thread pool, a per-call timeout keeps
  one bad endpoint from stalling the entire batch.
- **Real work — model/LLM calls:** long-running inference endpoints need a read timeout
  generous enough for real latency but bounded so a wedged request doesn't hang a worker
  (Area 9).
- **Pattern mapping (secondary):** no DSA analogue; it's a reliability primitive that
  underpins retries (5.9), circuit breakers (5.10), and bounded worst-case runtime.
[↑ Back to top](#contents)

---

<a id="5.9"></a>
## 5.9 — "The API fails 1% of the time and my whole job dies" → retry with backoff + jitter

### The situation

Your job calls a service 10,000 times. The service is *mostly* reliable, but ~1% of
calls fail transiently — a brief network blip, a momentary `503 Service Unavailable`,
a timeout (5.8). With no retry, those ~100 failures either crash the job or leave 100
records unprocessed:

```python
resp = requests.get(url, timeout=10)   # 1 in 100 raises -> a record lost or job dead
```

Your first instinct is a simple retry loop — try again immediately, a few times. But
retrying *immediately* often makes things **worse**: if the service is briefly
overloaded, hammering it again instantly (and from all your concurrent workers at once)
piles on more load exactly when it's struggling.

### What's really going on

Many failures are **transient** — they succeed if you simply try again a moment later.
The right response isn't "give up" or "retry instantly forever"; it's **retry a bounded
number of times, waiting longer between each attempt**. Two refinements make it safe:

- **Exponential backoff:** double the wait after each failure (e.g. 1s, 2s, 4s, 8s).
  This gives a struggling service increasing room to recover instead of a constant
  barrage. "Exponential" = the delay grows by a multiplier each time.
- **Jitter:** add a small *random* amount to each wait. Without it, if 50 workers all
  failed at the same instant, they'd all retry at *exactly* 1s, 2s, 4s — synchronised
  spikes that re-overload the service (the **thundering herd** problem). Random jitter
  spreads the retries out.

And one correctness rule: **only retry safe-to-repeat operations.** Retrying a GET is
fine; blindly retrying a "charge card" POST could double-charge unless it's idempotent
(Area 7, 7.4).

### The move

Retry transient failures with exponentially-growing, jittered delays and a cap on
attempts. Use a library (`tenacity`) or a small decorator:

```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

@retry(stop=stop_after_attempt(5),
       wait=wait_exponential_jitter(initial=1, max=30))
def fetch(url):
    return requests.get(url, timeout=10).json()
```

### Why it works

The decorator wraps `fetch`: on an exception it waits, then calls it again, up to 5
attempts. The wait grows exponentially (≈1s, 2s, 4s, 8s, 16s, capped at 30s) so a
struggling service gets progressively more breathing room, and the jitter randomises
each delay so your many workers don't retry in lockstep. After the final attempt it
re-raises, so a *persistent* failure still surfaces (you don't retry forever). Most
transient blips are absorbed by attempt 2 or 3, turning a 1% failure rate into a
near-zero one without you writing loop/sleep bookkeeping.

### The code, every line explained

```python
# --- With tenacity (the standard library for this) ----------------------
from tenacity import (retry, stop_after_attempt,
                      wait_exponential_jitter, retry_if_exception_type)
from requests.exceptions import RequestException

@retry(
    stop=stop_after_attempt(5),                    # give up after 5 tries (don't loop forever)
    wait=wait_exponential_jitter(initial=1, max=30),# 1s,2s,4s... + random jitter, capped 30s
    retry=retry_if_exception_type(RequestException),# ONLY retry network errors, not bugs
    reraise=True,                                   # re-raise the real error after the last try
)
def fetch(url):
    resp = requests.get(url, timeout=10)            # timeout (5.8) so a hang counts as a failure
    resp.raise_for_status()                         # 5xx -> raises -> triggers a retry
    return resp.json()

# --- Hand-rolled version (no dependency), to see the mechanism ----------
import time, random
def fetch_manual(url, attempts=5):
    for i in range(attempts):
        try:
            r = requests.get(url, timeout=10); r.raise_for_status()
            return r.json()
        except RequestException as e:
            if i == attempts - 1:                   # last attempt -> stop retrying
                raise
            delay = min(2 ** i, 30)                 # exponential: 1,2,4,8,16 capped at 30
            delay += random.uniform(0, delay * 0.1) # jitter: +0–10% random spread
            time.sleep(delay)                       # wait before the next attempt

# --- Be selective about WHAT you retry ----------------------------------
# Retry: timeouts, connection errors, 429 (5.11), 502/503/504 (transient server).
# DON'T retry: 400/401/403/404 — these are PERMANENT (bad request/auth/not found);
# retrying just wastes time and load. A 4xx won't fix itself on attempt 2.

# --- requests built-in retry for the HTTP layer (urllib3 Retry) ---------
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
session = requests.Session()
retries = Retry(total=5, backoff_factor=1,          # urllib3's own backoff
                status_forcelist=[429, 502, 503, 504])  # which statuses to retry
session.mount("https://", HTTPAdapter(max_retries=retries))
# session.get(url) now retries those statuses automatically (pairs with sessions, 5.18).
```

### Impact

- **Resilience:** transient 1% failures get absorbed automatically — the job completes
  with all records processed instead of dying or dropping ~100.
- **Protects the dependency:** backoff + jitter avoid the thundering-herd retry storm
  that turns a brief wobble into a full outage.
- **Bounded, not infinite:** a capped attempt count means a genuinely-down service fails
  cleanly (and can trip a circuit breaker, 5.10) rather than retrying forever.

### Pros & cons / when NOT to

**Reach for retry+backoff when:** calling any network service that can fail
transiently — APIs, DBs, queues, blob storage. Effectively all production I/O.

**Watch out / when NOT to:**
- **Only retry idempotent operations.** Reads are safe; writes/POSTs that aren't
  idempotent can duplicate effects (double-charge, double-insert). Make the operation
  idempotent first (Area 7, 7.4) — e.g. an idempotency key — *then* retry.
- **Don't retry permanent errors.** 400/401/403/404 won't succeed on retry; filter to
  transient errors (timeouts, 429, 5xx) or you waste time and add load.
- **Always cap attempts and total time.** Unbounded retries hide a real outage and can
  wedge a worker. Combine with a circuit breaker (5.10) so you stop hammering a service
  that's clearly down.
- **Backoff interacts with your own timeouts/SLAs** — 5 attempts with 30s waits can mean
  a single item takes minutes. Make sure that's acceptable for the job's deadline.
- **Jitter is not optional at scale** — without it, concurrent workers synchronise their
  retries into damaging spikes.

### Where this shows up

- **Real work — every bulk API/DB job:** the standard partner to timeouts (5.8) for
  making "fetch N things" reliable against flaky networks and services.
- **Real work — cloud SDKs:** S3/GCS/Azure and most cloud clients retry with backoff
  internally for exactly this reason; you replicate it for your own HTTP calls.
- **Real work — LLM/embedding APIs:** these return 429/503 under load constantly;
  backoff+jitter (plus rate limiting, 5.11) is essential to get a large batch through.
- **Pattern mapping (secondary):** no DSA analogue; it's a core reliability pattern that
  composes with timeouts (5.8), rate limiting (5.11), and circuit breakers (5.10).
[↑ Back to top](#contents)

---

<a id="5.10"></a>
## 5.10 — "A dead dependency made every request wait 10s and time out" → circuit breaker

### The situation

One downstream service your code depends on goes **fully down**. Every call now waits
the full 10-second timeout (5.8), then retries 5 times with backoff (5.9) — so each
request to *your* code takes ~a minute before finally failing. With retries hammering a
service that's definitely dead, you're wasting time, exhausting your worker threads
(all stuck waiting), and piling load onto a service that can't recover while you keep
hitting it.

```python
data = fetch_with_retry(url)   # service is DOWN: 5 retries × 10s each = ~50s wasted, every call
```

Timeouts and retries are correct for *transient* failures — but when a dependency is
*persistently* down, retrying every single request is exactly the wrong move.

### What's really going on

Retries assume the failure is temporary. When a service is genuinely down, you need the
opposite behaviour: **stop calling it for a while, fail instantly, and check back
periodically.** This is the **circuit breaker** pattern, named after an electrical
breaker that "trips" to stop current when there's a fault.

A circuit breaker tracks recent failures and has three states:

- **Closed** (normal): calls flow through. If failures exceed a threshold, it *trips*.
- **Open** (tripped): calls **fail immediately** without even attempting the call — no
  10s wait, no load on the dead service. After a cooldown, it moves to half-open.
- **Half-open** (testing): lets *one* trial call through. If it succeeds, close the
  breaker (service recovered); if it fails, re-open and wait again.

The realisation: **fail fast when you already know it's broken.** Instead of every
request discovering the outage the slow way, the breaker remembers and short-circuits,
so your system stays responsive and the dead service gets breathing room to recover.
Often you pair this with a **fallback** — a cached value, a default, or a degraded
response — so the user gets *something* instead of an error.

### The move

Wrap the call in a circuit breaker (library `pybreaker`, or a small class), and supply
a fallback for when it's open:

```python
import pybreaker
breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30)  # trip after 5 fails; retry after 30s

def get_price(sku):
    try:
        return breaker.call(lambda: requests.get(url, timeout=10).json())
    except pybreaker.CircuitBreakerError:
        return cached_price(sku)        # fallback: serve stale data instead of failing
```

### Why it works

The breaker counts consecutive failures. Once it hits `fail_max`, it **opens**: for the
next `reset_timeout` seconds, `breaker.call(...)` raises `CircuitBreakerError`
*immediately* without touching the network — so each request fails in microseconds
instead of 50 seconds, your worker threads aren't tied up waiting, and the dead service
receives no traffic. After the cooldown it allows one trial call (half-open); success
closes it and normal flow resumes. The `except` gives you a place to return a fallback,
so callers degrade gracefully rather than erroring out.

### The code, every line explained

```python
import pybreaker, requests

breaker = pybreaker.CircuitBreaker(
    fail_max=5,            # trip to OPEN after 5 consecutive failures
    reset_timeout=30,      # stay open 30s, then allow ONE trial call (half-open)
)

def get_price(sku):
    try:
        # breaker.call runs the function ONLY if the circuit is closed/half-open.
        # If open, it raises CircuitBreakerError without calling at all.
        return breaker.call(lambda: _fetch_price(sku))
    except pybreaker.CircuitBreakerError:
        # circuit is OPEN — fail fast, serve a fallback instead of waiting/erroring
        return cached_price(sku)          # stale-but-available > nothing
    except requests.RequestException:
        return cached_price(sku)          # a real call failed (and was counted by the breaker)

def _fetch_price(sku):
    r = requests.get(f"https://pricing/{sku}", timeout=10)   # timeout still essential (5.8)
    r.raise_for_status()
    return r.json()

# --- The state machine, conceptually -----------------------------------
# CLOSED  --(failures >= fail_max)-->  OPEN
# OPEN    --(reset_timeout elapsed)-->  HALF-OPEN
# HALF-OPEN --(trial succeeds)-->  CLOSED   |   --(trial fails)-->  OPEN

# --- Layering with retries (5.9): retry transient, breaker for sustained -
# A common stack: retries handle the occasional blip; the breaker catches the case
# where retries KEEP failing (service down) and stops the retry storm entirely.
# Order matters: the breaker should see the OUTCOME of the (already-retried) call,
# so a burst of transient blips doesn't trip it, but a real outage does.
```

### Impact

- **Fast failure during outages:** requests fail in microseconds instead of tens of
  seconds, so your service stays responsive even when a dependency is down.
- **Protects both sides:** your worker threads aren't all stuck waiting, and the failing
  service gets a traffic pause to recover instead of a relentless retry storm.
- **Graceful degradation:** with a fallback, users get cached/default results rather
  than a hard error — partial functionality beats none.

### Pros & cons / when NOT to

**Reach for a circuit breaker when:** you depend on a remote service that can go
*persistently* down, especially in a long-running service or one serving live traffic,
and you want to fail fast + degrade rather than hang.

**Watch out / when NOT to:**
- **Overkill for a one-shot batch script.** If you run a job once and a dependency is
  down, capped retries (5.9) that then abort are simpler. Circuit breakers earn their
  keep in *long-running* services making *repeated* calls.
- **State scope:** an in-process breaker only protects one process. With many
  workers/replicas, each has its own breaker (often fine), or you need shared state for
  a global view — more complexity.
- **Tuning matters:** too-sensitive (`fail_max` low) trips on normal blips; too-slow to
  trip leaves you hanging. Set thresholds from real failure/latency data.
- **A fallback must be genuinely safe** — serving stale cached data is fine for a price
  display, dangerous for a balance check. Decide per use case whether degraded data is
  acceptable.

### Where this shows up

- **Real work — microservices:** the standard pattern for service-to-service calls so
  one failing service doesn't cascade into a system-wide outage (a "cascading failure").
- **Real work — serving with optional enrichment:** if a recommendation/enrichment
  service is down, the breaker opens and you serve the page without that feature instead
  of timing out.
- **Real work — ML inference with a fallback model:** if the primary model endpoint is
  down, fail fast and fall back to a cached prediction or a simpler local model
  (Area 9).
- **Pattern mapping (secondary):** no DSA analogue; it's a state-machine reliability
  pattern that completes the timeout (5.8) → retry (5.9) → breaker progression for
  handling failure at increasing severity.
[↑ Back to top](#contents)

---

<a id="5.11"></a>
## 5.11 — "The API keeps returning 429 and rejecting my requests" → client-side rate limiting

### The situation

You parallelised your calls with a thread pool (5.2) — and now the API rejects a flood
of them with **HTTP 429 Too Many Requests**:

```python
# 50 workers firing as fast as they can:
with ThreadPoolExecutor(max_workers=50) as pool:
    results = list(pool.map(fetch, ids))   # API returns 429 on most of them!
```

The service's docs say "limit: 10 requests per second." Your 50 workers are sending
far more than that, so the server throttles you — and naive retries (5.9) just resend
the rejected requests, making the storm worse. You need to *not exceed the limit in the
first place*.

### What's really going on

Most APIs enforce a **rate limit** — a maximum request rate (e.g. 10 requests/second,
or 1,000/minute). Exceed it and you get 429s, and persistent abuse can get your key
throttled or banned. The fix is **client-side rate limiting**: *you* pace your own
requests so you stay under the limit, rather than relying on the server to reject the
excess.

The standard mechanism is a **token bucket**: imagine a bucket that refills with
"tokens" at a fixed rate (10 tokens/second for a 10 rps limit). Each request must take
one token before it's sent; if the bucket is empty, the request waits until a token
refills. This naturally caps your *average* rate at the refill rate while allowing
short **bursts** up to the bucket's capacity (handy when work arrives unevenly).

> Distinguish this from **concurrency limiting** (5.12, a semaphore): concurrency caps
> *how many run at once*; rate limiting caps *how many start per unit time*. A slow API
> might allow 100 concurrent connections but only 10 new requests/second — you often
> need both controls together.

### The move

Put a rate limiter in front of every call so requests are paced to the allowed rate.
Use a library (`pyrate-limiter`, `ratelimit`) or a small token-bucket limiter:

```python
from pyrate_limiter import Limiter, RequestRate, Duration
limiter = Limiter(RequestRate(10, Duration.SECOND))   # 10 requests per second

def fetch(url):
    with limiter.ratelimit("api", delay=True):        # waits if no token available
        return requests.get(url, timeout=10).json()
```

### Why it works

The limiter hands out at most 10 tokens per second. Each `fetch` must acquire one before
sending; when they're used up, further calls **block until the next token refills** —
so no matter how many of your 50 workers are ready, requests *leave* at ≤10/second and
the server never sees more than it allows. The 429s stop because you no longer exceed
the limit. Because it caps the *outgoing rate* rather than rejecting, every request
still gets sent — just spread out in time.

### The code, every line explained

```python
# --- With a library (recommended) ---------------------------------------
from pyrate_limiter import Limiter, RequestRate, Duration
limiter = Limiter(RequestRate(10, Duration.SECOND))   # the bucket: 10 tokens/sec

def fetch(url):
    with limiter.ratelimit("api", delay=True):
        #                    │      └ delay=True: WAIT for a token (vs raise if False)
        #                    └ a name -> separate buckets for separate APIs/keys
        return requests.get(url, timeout=10).json()
# Even with 50 pool workers (5.2), calls now leave at <=10/sec. No more 429s.

# --- Minimal hand-rolled token bucket (to see the mechanism) ------------
import time, threading
class RateLimiter:
    def __init__(self, rate_per_sec, burst):
        self.rate = rate_per_sec
        self.tokens = burst              # start full so an initial burst is allowed
        self.capacity = burst
        self.updated = time.monotonic()  # monotonic clock: immune to system-clock changes
        self.lock = threading.Lock()     # protect shared token state across threads (1.3)
    def acquire(self):
        with self.lock:
            now = time.monotonic()
            # refill tokens for the time elapsed since last check, capped at capacity
            self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
            self.updated = now
            if self.tokens < 1:                       # bucket empty -> must wait
                wait = (1 - self.tokens) / self.rate  # time until one token refills
                time.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1                       # spend one token, proceed

limiter = RateLimiter(rate_per_sec=10, burst=10)
def fetch(url):
    limiter.acquire()                                 # paces every call to <=10/sec
    return requests.get(url, timeout=10).json()

# --- ALSO honour the server's own signal: Retry-After -------------------
# When you DO get a 429, the response often includes a `Retry-After: <seconds>` header.
# Respect it instead of guessing — wait exactly that long before retrying (5.9):
#   wait = int(resp.headers.get("Retry-After", 1)); time.sleep(wait)
```

### Impact

- **Stops 429s at the source:** you stay under the limit, so requests succeed instead of
  being rejected and retried — fewer wasted calls, faster overall completion.
- **Protects your API access:** sustained limit-busting can get keys throttled or
  banned; pacing keeps you a well-behaved client.
- **Smooth, predictable load:** the downstream service sees a steady rate, and your job's
  throughput becomes calculable (≈ rate × duration).

### Pros & cons / when NOT to

**Reach for client-side rate limiting when:** an API publishes a rate limit, you make
many calls, or you're parallelising (5.2/5.4) and risk exceeding it.

**Watch out / when NOT to:**
- **Distributed clients need shared state.** An in-process limiter only paces *one*
  process. With many workers/replicas hitting the same API, each enforcing 10/sec means
  the *total* is N×10 — you need a shared limiter (e.g. Redis-backed) for a global cap.
- **Match the limiter to the *real* limit dimension** — per-second, per-minute,
  per-token, or per-endpoint. Limiting per-second when the cap is per-minute can still
  burst over a minute window.
- **Combine with retries AND backoff (5.9).** Rate limiting prevents most 429s, but you
  should still handle the occasional one by honouring `Retry-After`.
- **Often pair with concurrency limiting (5.12).** Rate (starts/sec) and concurrency
  (in-flight count) are different knobs; a service may constrain both.

### Where this shows up

- **Real work — third-party APIs:** payment, geocoding, enrichment, and SaaS APIs almost
  all publish rate limits; a client limiter is mandatory for bulk use.
- **Real work — LLM/embedding providers:** these enforce strict requests-per-minute and
  tokens-per-minute limits; pacing (plus batching, 5.14) is how you push a large job
  through without a wall of 429s (Area 9).
- **Real work — scraping/crawling:** politely rate-limiting per domain to avoid
  overloading sites and getting your crawler blocked.
- **Pattern mapping (secondary):** the token bucket is a small, classic algorithm
  (constant-rate refill + capacity cap); the same "leaky/token bucket" idea appears in
  system-design interviews on designing a rate limiter.
[↑ Back to top](#contents)

---

<a id="5.12"></a>
## 5.12 — "I need many tasks running, but not ALL at once" → semaphore (concurrency cap)

### The situation

You have 50,000 async tasks (5.4) or a big batch of downloads, and firing them all
simultaneously breaks things — too many open connections, exhausted file descriptors,
or you overwhelm a service that allows only ~100 concurrent connections:

```python
tasks = [fetch(url) for url in urls]    # 50,000 coroutines
await asyncio.gather(*tasks)            # tries to open 50,000 connections AT ONCE -> crash
```

You don't want 50,000 in flight, and you don't want 1 at a time — you want a fixed
ceiling, say 100 concurrent, with the rest waiting their turn.

### What's really going on

You need to cap **concurrency** — the number of tasks *in flight simultaneously* —
distinct from rate limiting (5.11, which caps *starts per unit time*). The tool is a
**semaphore**: a counter that permits up to N holders at once.

> A **semaphore** holds N "permits." A task must *acquire* a permit before proceeding
> and *release* it when done. If all N are taken, the next acquirer **blocks/waits**
> until someone releases. Set N=100 and at most 100 tasks run the protected section at
> any instant; the 101st waits for one to finish. (A semaphore with N=1 is essentially
> a lock — 1.3.)

The realisation: a semaphore is a **gate that admits N at a time**. It bounds resource
use (connections, memory, sockets) and protects downstream services from your full
parallelism, while still keeping N tasks busy at all times — far better utilisation
than one-at-a-time, without the blow-up of all-at-once.

### The move

Guard the work with a semaphore sized to your concurrency ceiling:

```python
sem = asyncio.Semaphore(100)            # at most 100 in flight at once

async def fetch(url):
    async with sem:                     # acquire a permit; auto-release on exit (1.3)
        return await client.get(url)
```

### Why it works

`async with sem` acquires one of the 100 permits before the request and releases it
when the block exits. While 100 tasks hold permits, the 101st `async with sem` *pauses
at an await* (costing nothing — it's not a busy-wait) until one finishes and frees a
permit. So `gather` over 50,000 tasks no longer opens 50,000 connections — it keeps
exactly 100 active, feeding the next as each completes. You get full pipelining at a
safe, fixed resource level. (For threads, `threading.Semaphore` works the same way with
a `with` block.)

### The code, every line explained

```python
import asyncio, httpx

# --- async semaphore: cap in-flight coroutines --------------------------
sem = asyncio.Semaphore(100)            # the counter: 100 permits

async def fetch(client, url):
    async with sem:                     # waits here if 100 are already running
        r = await client.get(url, timeout=10)   # only <=100 of these run concurrently
        return r.status_code            # permit released as the `with` block exits

async def main(urls):
    async with httpx.AsyncClient() as client:
        tasks = [fetch(client, u) for u in urls]   # 50,000 coroutines created (cheap)
        return await asyncio.gather(*tasks)        # but only 100 ACTIVE at any moment

# --- thread version: threading.Semaphore + ThreadPoolExecutor -----------
import threading
from concurrent.futures import ThreadPoolExecutor
sem = threading.Semaphore(100)
def fetch_sync(url):
    with sem:                           # blocks the thread if 100 permits are taken
        return requests.get(url, timeout=10).status_code
# Note: with a ThreadPoolExecutor, max_workers ALREADY caps concurrency to the pool
# size — a separate semaphore is mainly needed when several pools/sources share one
# downstream limit, or to cap a subset of tasks tighter than the pool.

# --- rate limit (5.11) AND concurrency cap (5.12) together --------------
sem = asyncio.Semaphore(100)            # at most 100 connections open at once
# limiter = ... 10/sec ...              # AND no more than 10 NEW requests per second
async def fetch(client, url):
    async with sem:                     # concurrency gate
        async with limiter.ratelimit("api", delay=True):   # rate gate
            return await client.get(url, timeout=10)
# These solve DIFFERENT problems: sem bounds simultaneous connections (memory/sockets),
# limiter bounds request rate (429s). Real high-throughput clients use both.
```

### Impact

- **No resource blow-up:** caps open connections/sockets/memory at a known ceiling, so
  50,000 tasks run safely instead of crashing on "too many open files".
- **Protects the dependency:** the downstream service never sees more than N concurrent
  connections from you — respects documented connection limits.
- **Full utilisation:** keeps exactly N tasks busy at all times — much faster than
  serial, without the instability of unbounded parallelism.

### Pros & cons / when NOT to

**Reach for a semaphore when:** you fan out many tasks (especially with `asyncio.gather`,
5.4) and must bound how many run *simultaneously* — connection caps, memory limits,
politeness to a service.

**Watch out / when NOT to:**
- **Concurrency ≠ rate.** A semaphore caps simultaneous tasks but not how fast you start
  them; you may still exceed a per-second limit and need a rate limiter too (5.11).
- **With `ThreadPoolExecutor`, `max_workers` is already a concurrency cap** — don't add a
  redundant semaphore unless multiple pools share one downstream limit.
- **Always release the permit** — use `with`/`async with` so an exception can't leak a
  permit (a leaked permit permanently shrinks your effective concurrency, eventually
  deadlocking). Never acquire/release by hand without try/finally.
- **Sizing is empirical:** too low underuses capacity; too high reintroduces the
  blow-up. Tune N to the downstream's connection limit and your memory budget.

### Where this shows up

- **Real work — high-fanout async clients:** the mandatory companion to
  `asyncio.gather` (5.4) over thousands of tasks — bounds connections so the job doesn't
  exhaust sockets.
- **Real work — bounded downloads/uploads:** capping concurrent transfers to blob
  storage or a database to a level it tolerates.
- **Real work — LLM/embedding fan-out:** limiting simultaneous in-flight model calls
  (provider connection caps) while a separate limiter handles requests/min (Area 9).
- **Pattern mapping (secondary):** the semaphore is a classic concurrency primitive; the
  "admit at most K at once" idea appears in system design (connection pools, bounded
  worker pools) and is the synchronisation cousin of the bounded queue (5.6).
[↑ Back to top](#contents)

---

<a id="5.13"></a>
## 5.13 — "The API only returns 100 results but there are 50,000" → pagination

### The situation

You call an endpoint to "get all orders" and get back only the first 100, plus some
metadata hinting there's more:

```python
resp = requests.get("https://api/orders").json()
# {
#   "results": [ ...100 orders... ],
#   "next": "https://api/orders?cursor=eyJpZCI6MTAwfQ"   # a pointer to the next page
# }
len(resp["results"])    # 100  -- but you know there are ~50,000 orders!
```

You only got page one. To collect everything you must keep requesting "the next page"
until there are no more — but you don't want to hard-code "500 pages" or copy-paste the
request 500 times.

### What's really going on

APIs **paginate** large result sets — they return results in fixed-size **pages**
rather than all at once, because sending 50,000 records in one response would be slow,
memory-heavy, and fragile. Your job is to **follow the pages** until exhausted.

There are two common pagination styles, and recognising which one you're dealing with
decides your loop:

- **Offset/page-number:** you ask for `?page=1`, `?page=2`, … or `?offset=0&limit=100`,
  `?offset=100&limit=100`. Simple, but can skip/duplicate rows if data changes between
  requests, and gets slow on deep pages.
- **Cursor/token-based:** each response gives a `next` cursor/token (an opaque pointer
  to "where you left off"); you pass it to get the following page, stopping when it's
  absent/null. More robust to concurrent changes — the modern default.

The realisation: pagination is a **"keep fetching until there's no next" loop**, and the
cleanest way to expose it is a **generator** (1.2) that `yield`s items page by page — so
the caller iterates "all results" without ever holding all 50,000 in memory.

### The move

Wrap the page-following loop in a generator that yields one item at a time:

```python
def all_orders():
    url = "https://api/orders"
    while url:                                # keep going while there's a next page
        page = requests.get(url, timeout=10).json()
        yield from page["results"]            # hand out this page's items one by one
        url = page.get("next")                # advance to next page (None -> loop ends)
```

### Why it works

The generator follows the chain: fetch a page, `yield` its items, then move `url` to the
page's `next` pointer. When `next` is absent (`None`), the `while url:` condition becomes
falsy (1.17) and the loop ends — naturally stopping at the last page. Because it's a
generator (1.2), the caller pulls items lazily: only **one page** is held in memory at a
time, and the caller can start processing page one's results while later pages haven't
been fetched yet. `yield from` is shorthand for "yield each item of this iterable", so
the caller sees a flat stream of orders, not a stream of pages.

### The code, every line explained

```python
import requests

# --- Cursor/token pagination (modern, robust) ---------------------------
def all_orders():
    url = "https://api/orders"
    while url:                                # loop until there's no 'next' URL
        resp = requests.get(url, timeout=10)  # timeout (5.8) on every page
        resp.raise_for_status()
        page = resp.json()
        yield from page["results"]            # emit each order in this page
        url = page.get("next")                # the API gives the next page's URL, or None
# Caller treats it as one big stream, holds only ONE page at a time:
for order in all_orders():                    # lazy: fetches pages as you consume
    process(order)

# --- Offset/page-number pagination --------------------------------------
def all_orders_offset(page_size=100):
    offset = 0
    while True:
        resp = requests.get("https://api/orders",
                            params={"offset": offset, "limit": page_size},
                            timeout=10).json()
        results = resp["results"]
        if not results:                       # empty page -> we've passed the end
            break
        yield from results
        offset += page_size                   # advance by one page
        # (some APIs give a total count; you can stop when offset >= total instead)

# --- Token style where the cursor is a separate field -------------------
def all_items():
    cursor = None
    while True:
        params = {"cursor": cursor} if cursor else {}
        page = requests.get("https://api/items", params=params, timeout=10).json()
        yield from page["items"]
        cursor = page.get("next_cursor")
        if not cursor:                         # no more pages
            break

# --- Don't forget: pagination calls are SEQUENTIAL by nature ------------
# Each page's cursor depends on the previous response, so you can't fetch cursor
# pages in parallel (5.2). Offset pagination CAN be parallelised (you know the
# offsets up front) IF the data is stable — but beware shifting rows.
```

### Impact

- **Completeness:** you actually retrieve all 50,000 records instead of silently
  processing only the first 100 — a subtle, dangerous bug if missed.
- **Bounded memory:** the generator holds one page at a time, so "get everything" works
  regardless of total size (ties to 1.2, streaming).
- **Clean interface:** callers write `for order in all_orders():` and never deal with
  cursors/offsets — the pagination is encapsulated.

### Pros & cons / when NOT to

**Reach for a pagination generator when:** an API returns results in pages
(`next`/`cursor`/`offset`) and you need more than the first page.

**Watch out / when NOT to:**
- **Cursor pages are inherently sequential** — each depends on the previous response's
  token, so you can't parallelise them. Offset pages *can* be fetched in parallel (you
  know the offsets up front), but only if the underlying data is stable; otherwise you
  risk skipped/duplicated rows.
- **Offset pagination drifts under writes.** If rows are inserted/deleted while you
  page, offset-based paging can skip or repeat records. Prefer cursor-based when the
  data is changing.
- **Always set a timeout per page (5.8) and handle partial failure** — a 500-page pull
  that dies on page 312 should be resumable (Area 7) or at least not lose the first 311
  pages' work.
- **Respect rate limits (5.11)** — 500 sequential page calls can still trip a
  per-second limit; pace them.

### Where this shows up

- **Real work — "export everything" jobs:** pulling all orders/users/events from a SaaS
  or internal API for analysis or migration — the canonical pagination task.
- **Real work — search/listing endpoints:** results that come back in pages of 20–100,
  iterated to gather the full set.
- **Real work — cloud resource listing:** `list_objects`/`list_instances` APIs paginate
  via continuation tokens; SDK paginators implement exactly this generator pattern.
- **Pattern mapping (secondary):** following `next` pointers until null is literally
  **linked-list traversal** (Area 11) — each page is a node holding data plus a pointer
  to the next; the loop ends at the null link.
[↑ Back to top](#contents)

---

<a id="5.14"></a>
## 5.14 — "I'm making one API call per item when the API accepts many" → batching

### The situation

You need embeddings for 100,000 text snippets. You call the embedding API once per
snippet:

```python
vectors = []
for text in snippets:                         # 100,000 iterations
    v = embed_api(texts=[text])               # one network round-trip PER snippet
    vectors.append(v)
```

Each call has ~300 ms of fixed **overhead** — connection, TLS handshake, request
parsing, queueing — regardless of payload. So 100,000 calls = 100,000 × 300 ms of
overhead ≈ **8 hours**, almost all of it *per-call tax*, not actual work. But the API
docs say its `/embed` endpoint accepts **up to 512 texts per request**.

### What's really going on

Each network request carries fixed **per-call overhead** that you pay whether you send 1
item or 500. Sending one item per call means you pay that tax 100,000 times. When the
API supports **batch** requests — many items in one call — you can amortise the overhead
across the whole batch: 100,000 items in batches of 512 is just ~196 calls, paying the
overhead ~196 times instead of 100,000.

The realisation: **group items into batches and send each batch in one request.** This
is the API-call cousin of `itertools.batched` (1.12) — chunk the work, then one call per
chunk. It's often the single biggest speed-up for "call an API for every row" jobs, and
it usually costs less too (many APIs bill or rate-limit per *request*, not per item).

> This pairs naturally with the other Area 5 tools: batch first to cut the number of
> calls, then run the batches concurrently (5.2) under a rate limit (5.11) — batching
> reduces the call count, concurrency overlaps the remaining calls' waits.

### The move

Group items into batches (respecting the API's max) and send one request per batch:

```python
from itertools import batched           # 1.12 (Python 3.12+)

vectors = []
for chunk in batched(snippets, 512):     # up to 512 texts per request
    vectors.extend(embed_api(texts=list(chunk)))   # ONE call returns 512 vectors
```

### Why it works

Each `embed_api(texts=[...512...])` call pays the ~300 ms overhead **once** but returns
512 results, so the per-item overhead drops by ~512×. 100,000 items become ~196 requests
instead of 100,000 — the overhead-dominated 8-hour job collapses to minutes. The API does
the 512 embeddings server-side in one go (often itself batched on a GPU, Area 9), which
is far more efficient than 512 separate request/response cycles. `batched` (1.12) handles
the chunking, including the final short batch, with no off-by-one bookkeeping.

### The code, every line explained

```python
from itertools import batched           # groups an iterable into tuples of size n (1.12)

# --- Basic batching: one request per chunk ------------------------------
def embed_all(snippets, batch_size=512):
    vectors = []
    for chunk in batched(snippets, batch_size):   # e.g. (t0..t511), (t512..t1023), ...
        batch = list(chunk)                        # the API wants a list
        result = embed_api(texts=batch, timeout=30)# ONE call -> len(batch) vectors back
        vectors.extend(result)                     # flatten results into one list
    return vectors
# 100,000 items / 512 = ~196 calls instead of 100,000. Overhead paid ~196 times.

# --- Batching + concurrency (5.2): send batches in parallel -------------
from concurrent.futures import ThreadPoolExecutor
def embed_all_fast(snippets, batch_size=512, workers=8):
    chunks = [list(c) for c in batched(snippets, batch_size)]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        # map preserves order, so results line up with the input chunks
        results = pool.map(lambda b: embed_api(texts=b, timeout=30), chunks)
        return [v for batch_result in results for v in batch_result]  # flatten
# Now ~196 calls also overlap their network waits -> minutes, not hours.
# (Add a rate limiter (5.11) if the API caps requests/min.)

# --- Keeping results aligned with inputs --------------------------------
# Most batch APIs return vectors in the SAME ORDER as the input texts, so
# flattening preserves alignment. VERIFY this in the API docs — if a batch API
# returns results keyed by an id instead, map them back by id, don't assume order.

# --- Choosing batch_size -------------------------------------------------
# Bounded by: the API's documented max per request (hard limit), the payload SIZE
# limit (bytes — long texts may force smaller batches than the count limit), and
# latency (huge batches take longer per call and fail more expensively on error).
# Start at the API's max or a few hundred; shrink if you hit payload-size errors.
```

### Impact

- **Massive speed-up on overhead-bound jobs:** cutting 100,000 calls to ~196 turns
  hours into minutes — usually the biggest single win for "API per row" workloads.
- **Lower cost & rate-limit pressure:** APIs that bill or limit per *request* reward
  batching directly; fewer requests = lower bill and fewer 429s (5.11).
- **Server-side efficiency:** one batch of 512 lets the service process them together
  (e.g. a single GPU forward pass for embeddings), far cheaper than 512 separate cycles.

### Pros & cons / when NOT to

**Reach for batching when:** the API accepts multiple items per request and you have
many items — embeddings, bulk inserts, bulk lookups, batch inference.

**Watch out / when NOT to:**
- **Respect the API's max batch size AND payload-size limit.** Exceeding the count or
  byte limit causes errors; very long texts may force a smaller batch than the item-count
  cap allows.
- **Partial-batch failure is harder.** If one item in a batch is malformed, some APIs
  reject the *whole* batch. You then need to retry the batch, or split-and-retry to
  isolate the bad item (Area 7, 7.9) — more complex than per-item error handling.
- **Verify result ordering/keying.** Don't assume results come back in input order —
  confirm in the docs; if the API returns ids, map results back by id.
- **Bigger batches = higher latency per call and costlier retries.** A failed 512-item
  call wastes more than a failed 50-item call. Balance batch size against retry cost and
  responsiveness.
- **Not all endpoints batch** — if the API is strictly one-item, batching isn't an
  option; fall back to concurrency (5.2) to hide the overhead instead.

### Where this shows up

- **Real work — embeddings at scale:** embedding APIs (and local models) are designed
  for batches; batching is the standard way to embed a large corpus economically
  (Area 9, RAG ingestion).
- **Real work — bulk database/index writes:** `INSERT ... VALUES (...), (...), (...)` or
  a vector store's batch-upsert — one round-trip per N rows instead of per row.
- **Real work — batch inference:** sending many samples to a model-serving endpoint in
  one request so the server runs them as a single forward pass (Area 8, 8.10).
- **Pattern mapping (secondary):** the chunk-then-process shape is `itertools.batched`
  (1.12); the "amortise fixed cost over a batch" idea also underlies buffered I/O
  (Area 2) and bulk DB operations.
[↑ Back to top](#contents)

---

<a id="5.15"></a>
## 5.15 — "The API accepts my job but the result isn't ready yet" → polling

### The situation

You submit a long-running job — say, a bulk export or a video transcription — and the
API doesn't return the result. It returns a **job id** and status `"pending"`:

```python
resp = requests.post("https://api/exports", json={...}).json()
# {"job_id": "exp_123", "status": "pending"}   <- no result yet!
```

The actual export takes 2–10 minutes server-side. The result will be ready *later*, at
a separate "check status" endpoint. You need to wait for it — but you can't just block,
and you don't know exactly when it'll finish.

### What's really going on

This is an **asynchronous job** on the *server's* side (different from Python's asyncio):
the work is too slow to finish within one request, so the API uses a **submit-then-poll**
pattern. You submit (get a job id), then repeatedly **poll** a status endpoint —
"is it done yet?" — until the status becomes `"completed"` (or `"failed"`), then fetch
the result.

> **Polling** = repeatedly asking "are you done?" at intervals until the answer is yes.
> It's the client-side way to wait for something whose completion time you don't control
> and can't be notified about directly.

The realisation: you need a **wait loop** — check status, if not done sleep a bit, check
again — with three must-haves that 5.16 expands on: a **sensible interval** (don't ask
every 10 ms — that's hammering), and a **deadline/max attempts** (don't poll forever if
the job is stuck). The naive version (tight loop, no timeout) either DOS-es the API or
hangs your program indefinitely.

### The move

Submit, then loop: check status, sleep between checks, stop on a terminal state or a
deadline:

```python
import time
job = requests.post("https://api/exports", json=payload, timeout=10).json()
job_id = job["job_id"]

while True:
    status = requests.get(f"https://api/exports/{job_id}", timeout=10).json()
    if status["status"] in ("completed", "failed"):
        break
    time.sleep(5)                         # wait before asking again
```

### Why it works

You can't get the result in the first response, so you hold the job id and ask the
status endpoint periodically. The `sleep(5)` between checks means you ask ~once every 5
seconds instead of thousands of times a second — enough to notice completion promptly
without flooding the API. The loop exits on any **terminal** status (`completed` or
`failed`) — you must check for *failure* too, or a failed job loops forever. Adding a
deadline (below) guarantees the loop can't hang indefinitely if the job gets stuck in
`pending`.

### The code, every line explained

```python
import time, requests

def run_export(payload, poll_every=5, deadline_s=600):
    # --- submit: get a job handle, not a result --------------------------
    job = requests.post("https://api/exports", json=payload, timeout=10).json()
    job_id = job["job_id"]

    # --- poll until terminal status or deadline --------------------------
    start = time.monotonic()              # monotonic clock: unaffected by clock changes
    while True:
        status = requests.get(f"https://api/exports/{job_id}", timeout=10).json()
        state = status["status"]

        if state == "completed":
            return status["result_url"]   # success -> fetch/return the result
        if state == "failed":             # MUST handle failure, or loop forever
            raise RuntimeError(f"export {job_id} failed: {status.get('error')}")

        if time.monotonic() - start > deadline_s:   # give up after deadline (e.g. 10 min)
            raise TimeoutError(f"export {job_id} not done after {deadline_s}s")

        time.sleep(poll_every)            # wait before the next status check

# --- the anti-patterns to avoid -----------------------------------------
# while status != "completed":           # BUG 1: no failed/terminal check -> infinite
#     ...                                #         loop if the job FAILS
#     # no sleep                         # BUG 2: tight loop -> thousands of calls/sec,
#                                        #         you DOS the API and may get 429'd
#     # no deadline                      # BUG 3: hangs forever if job stuck "pending"

# --- terminal vs non-terminal states ------------------------------------
# Non-terminal (keep polling): "pending", "queued", "running", "processing"
# Terminal (stop):             "completed"/"succeeded" | "failed"/"cancelled"/"timeout"
# Check the API docs for the EXACT state names; missing a terminal state = a hang.
```

### Impact

- **Correctly retrieves async results:** you actually get the export instead of acting on
  a `"pending"` placeholder or giving up too early.
- **Polite to the API:** spacing checks (and backing off, 5.16) avoids hammering the
  status endpoint into rate limits.
- **Bounded wait:** the deadline guarantees your program won't hang forever on a stuck
  job — it fails cleanly and you can retry or alert.

### Pros & cons / when NOT to

**Reach for polling when:** an API returns a job id + status for long-running work
(exports, transcoding, async LLM jobs, report generation) and there's no push
notification.

**Watch out / when NOT to:**
- **Always check for terminal *failure* states**, not just success — the #1 polling bug
  is looping forever because the job `failed` and you only tested for `completed`.
- **Always sleep between checks and set a deadline.** A tight no-sleep loop DOS-es the
  API (and burns CPU); no deadline means an infinite hang. Both are mandatory.
- **Fixed short intervals are wasteful** for jobs that take minutes — use increasing
  intervals / backoff and honour any `Retry-After` the API gives (5.16).
- **Prefer webhooks if offered (5.17).** Polling is the fallback when the server *can't*
  notify you; if it can push a callback, that's more efficient than asking repeatedly.
- **Each poll needs its own timeout (5.8)** — a status check can hang just like any call.

### Where this shows up

- **Real work — bulk exports / report jobs:** "request export → poll → download" is the
  standard flow for analytics, data-warehouse, and SaaS export APIs.
- **Real work — media/ML processing:** transcription, image/video generation, and async
  LLM batch jobs return a job id and require polling for completion (Area 9).
- **Real work — cloud operations:** "create cluster / run query / provision resource"
  operations return an operation handle you poll until done.
- **Pattern mapping (secondary):** no DSA analogue; it's a client-side wait pattern that
  pairs with timeouts (5.8) and backoff (5.16), and is the alternative to event-driven
  webhooks (5.17).
[↑ Back to top](#contents)

---

<a id="5.16"></a>
## 5.16 — "My polling either hammers the API or reacts too slowly" → adaptive intervals & deadlines

### The situation

Your polling loop (5.15) uses a fixed `sleep(5)`. Two problems show up depending on the
job:

- For a job that finishes in **2 seconds**, polling every 5s means you wait up to 5s to
  notice — sluggish.
- For a job that takes **8 minutes**, polling every 5s means ~96 status calls, most of
  them pointless — wasteful and possibly rate-limited (5.11).

And you're polling 500 jobs at once, all on the same fixed schedule, so they spike the
status endpoint in synchronised bursts.

```python
while not done:
    check_status()
    time.sleep(5)        # too slow for fast jobs, too chatty for slow ones
```

### What's really going on

A single fixed interval can't be right for jobs of unknown, varying duration. The fix is
the same shape as retry backoff (5.9): **start checking frequently, then back off** as
the job clearly isn't finishing soon — poll fast early (catch quick jobs promptly), slow
down later (don't spam during a long job). Add **jitter** so 500 concurrent pollers don't
synchronise into bursts, and a hard **deadline** so a stuck job can't poll forever.

> **Adaptive/backoff polling:** the interval grows after each check (e.g. 1s, 2s, 4s,
> 8s… capped at, say, 30s), instead of staying constant. **Jitter** randomises each
> sleep slightly to de-synchronise many pollers. A **deadline** (max total wait) bounds
> the loop.

Even better, if the API returns a `Retry-After` header or an `estimated_completion`
hint, **honour it** — the server knows roughly when to check back better than your guess.

### The move

Grow the poll interval with a cap, add jitter, and enforce a deadline:

```python
delay = 1
while time.monotonic() - start < deadline:
    if check_done(): return result
    time.sleep(delay + random.uniform(0, delay * 0.1))   # jittered wait
    delay = min(delay * 2, 30)                            # back off, capped at 30s
raise TimeoutError(...)
```

### Why it works

Early checks are close together (1s, 2s) so a quick job is noticed almost immediately;
as the job drags on, the interval doubles toward a 30s cap, so a long job costs ~log(n)
checks instead of one every 5s. Jitter spreads many pollers' checks across the timeline
so the status endpoint sees a steady trickle, not synchronised spikes. The deadline
guarantees termination — a job stuck in `pending` raises `TimeoutError` rather than
polling indefinitely. Honouring `Retry-After` replaces guesswork with the server's own
guidance.

### The code, every line explained

```python
import time, random, requests

def wait_for_job(job_id, deadline_s=600, max_interval=30):
    start = time.monotonic()
    delay = 1.0                                  # start fast: first re-check after ~1s
    while True:
        resp = requests.get(f"https://api/jobs/{job_id}", timeout=10)
        status = resp.json()
        state = status["status"]

        if state == "completed":
            return status["result"]
        if state in ("failed", "cancelled"):     # terminal failure states (5.15)
            raise RuntimeError(f"job {job_id}: {state}")

        if time.monotonic() - start > deadline_s:        # hard ceiling on total wait
            raise TimeoutError(f"job {job_id} not done in {deadline_s}s")

        # --- honour the server's hint if present, else use our backoff ----
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            sleep_for = float(retry_after)       # server told us when to check back
        else:
            sleep_for = delay + random.uniform(0, delay * 0.1)   # backoff + jitter
            delay = min(delay * 2, max_interval)  # double the interval, capped

        time.sleep(sleep_for)

# --- interval growth, illustrated ---------------------------------------
# checks at ~1s, 2s, 4s, 8s, 16s, 30s, 30s, 30s, ...  (capped)
# A 2s job: caught by the 2nd check. An 8-min job: ~20 checks, not ~96.

# --- de-synchronising many concurrent pollers ---------------------------
# Without jitter, 500 jobs started together would all poll at EXACTLY 1s,2s,4s...,
# hitting the status endpoint in tight bursts (mini self-inflicted load spikes /
# possible 429s, 5.11). The random jitter smears those checks across time.
```

### Impact

- **Responsive AND efficient:** fast jobs are caught within a second or two; long jobs
  cost a handful of checks instead of dozens — best of both.
- **Gentle on the API:** backoff + jitter + honouring `Retry-After` keep the status
  endpoint from being hammered, avoiding self-inflicted rate limits.
- **Guaranteed termination:** the deadline means the loop always ends — success,
  failure, or timeout — never an infinite hang.

### Pros & cons / when NOT to

**Reach for adaptive polling when:** you poll (5.15) jobs of unknown/variable duration,
or you poll many jobs concurrently.

**Watch out / when NOT to:**
- **Cap the interval.** Unbounded doubling means a job that finishes just after a 256s
  sleep isn't noticed for over four minutes. A 15–30s cap keeps latency reasonable.
- **Honour `Retry-After`/hints over your own backoff** when the server provides them —
  guessing against the server's own estimate is worse.
- **Jitter is essential at scale** — same thundering-herd reasoning as retries (5.9);
  fixed schedules synchronise pollers into bursts.
- **If checks are very frequent and many, prefer webhooks (5.17)** — adaptive polling is
  still polling; a push notification removes the wasted checks entirely.
- **Deadline must match the job's realistic worst case** — too short and you abandon
  jobs that would have finished; too long and a stuck job ties up a worker.

### Where this shows up

- **Real work — long async jobs:** exports, transcoding, training/inference jobs, report
  generation — anywhere you submit-and-poll (5.15) and durations vary widely.
- **Real work — orchestration:** waiting for a deploy, a cloud operation, or a data
  pipeline step to reach a terminal state before proceeding.
- **Real work — CI/monitoring loops:** checking a build or run status with backoff so a
  10-minute build isn't polled every second.
- **Pattern mapping (secondary):** shares its growth-with-cap-and-jitter structure with
  retry backoff (5.9); both are "wait smarter over time" loops bounded by a deadline.
[↑ Back to top](#contents)

---

<a id="5.17"></a>
## 5.17 — "Polling thousands of jobs wastes most of its calls" → webhooks vs polling

### The situation

You're polling (5.15/5.16) the status of 5,000 background jobs. Most checks return
"still pending" — you make tens of thousands of status calls, and the vast majority are
wasted (the answer hasn't changed). Even with backoff, there's an inherent inefficiency:
you're *asking* repeatedly when nothing's happened, and there's always a delay between
"job actually finished" and "my next poll notices."

```python
# 5,000 jobs, polled until done — the great majority of calls return "pending"
for job in jobs:
    wait_for_job(job.id)     # lots of calls, most of them "nothing changed yet"
```

### What's really going on

Polling is **pull-based**: *you* repeatedly ask "done yet?" The alternative is
**push-based**: the server tells *you* the moment something happens, so you make zero
wasted calls and learn instantly. The push mechanism over HTTP is a **webhook**.

> A **webhook** is a URL *you* host that the *other* service calls (an HTTP POST) when an
> event occurs — "job exp_123 completed", "payment received". Instead of you polling
> their API, they call your endpoint with the event data. It inverts the direction: the
> server is now the client, your app is the receiver.

The realisation: **if the provider can notify you, let it — don't poll.** Webhooks
eliminate the wasted "still pending" checks and remove polling latency (you hear about
completion immediately). The cost is that you must run an **always-on HTTP endpoint** to
receive the calls, and handle their realities: verifying they're genuine, responding
fast, and coping with duplicates/retries. There's also a middle option —
**long-polling** — when you can't host an endpoint.

### The move

Register a webhook URL with the provider and expose an endpoint that receives, verifies,
and quickly acknowledges events:

```python
@app.post("/webhooks/jobs")               # the URL you registered with the provider
def on_job_event(request):
    verify_signature(request)             # 1. confirm it's really from the provider
    enqueue(request.json())               # 2. hand off to a queue, don't process inline
    return Response(status=200)           # 3. acknowledge FAST so they don't retry
```

### Why it works

Once registered, the provider POSTs to your URL the instant a job finishes — so you make
**zero** status calls and learn immediately, with no polling latency. The three steps
matter: **verify** (the URL is public, so anyone could POST fake events — check the
provider's HMAC signature), **enqueue then return** (do the real work asynchronously via
a queue/worker, Area 7 — webhook senders expect a fast 2xx and will *retry* if you're
slow or error), and **idempotent handling** (because of those retries, the same event
can arrive twice — dedupe by event id, 7.4). Long-polling is the fallback when you can't
host an endpoint: you make one request that the server *holds open* until the event
happens (or a timeout), then immediately re-request — far fewer calls than tight polling.

### The code, every line explained

```python
# --- Webhook receiver (FastAPI-style) -----------------------------------
import hmac, hashlib
from fastapi import FastAPI, Request, Response, HTTPException
app = FastAPI()

WEBHOOK_SECRET = b"..."                    # shared secret from the provider's dashboard

def verify(body: bytes, signature: str):
    # recompute the HMAC of the raw body and compare to the header the provider sent
    expected = hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):   # constant-time compare (anti-timing)
        raise HTTPException(status_code=401, detail="bad signature")

@app.post("/webhooks/jobs")
async def on_job_event(request: Request):
    body = await request.body()                        # RAW bytes (needed for signature)
    verify(body, request.headers.get("X-Signature", ""))  # reject forged calls
    event = await request.json()

    if already_processed(event["id"]):                 # idempotency: senders RETRY (7.4)
        return Response(status_code=200)               # ack duplicate, do nothing
    enqueue_for_processing(event)                      # hand off; DON'T do slow work here
    return Response(status_code=200)                   # ack within ~seconds or they retry

# --- Long-polling: the middle ground when you can't host an endpoint ----
# You make a request the server holds OPEN until the event or a timeout:
def long_poll(job_id):
    while True:
        # the server doesn't reply until status changes OR ~30s pass (note big timeout)
        r = requests.get(f"https://api/jobs/{job_id}/wait", timeout=35)
        data = r.json()
        if data["status"] in ("completed", "failed"):
            return data
        # else: timed out server-side with no change -> immediately re-request
# Far fewer calls than tight polling, no endpoint to host — but ties up a connection.

# --- Decision summary ---------------------------------------------------
# Webhook:      provider supports it AND you can host an endpoint -> best (0 wasted calls)
# Long-poll:    provider supports it, you CAN'T host an endpoint   -> good middle ground
# Poll (5.16):  neither -> fall back to adaptive polling with backoff
```

### Impact

- **Eliminates wasted calls & latency:** no "still pending" checks; you're notified the
  instant the event happens — both cheaper and faster than polling.
- **Scales to many jobs:** 5,000 jobs cost 5,000 inbound notifications total, versus tens
  of thousands of outbound poll calls.
- **Event-driven architecture:** webhooks let you react to external events (payments,
  uploads, job completion) as they occur, the basis of integrations between services.

### Pros & cons / when NOT to

**Reach for webhooks when:** the provider supports them and you can host a reachable,
always-on HTTPS endpoint — the efficient default for "notify me when X happens".

**Watch out / when NOT to:**
- **You must run and secure a public endpoint.** That's real infrastructure — not viable
  for a one-off script on your laptop (there, poll, 5.16, or use long-polling). Tools
  like ngrok help in dev, but production needs a hosted service.
- **Always verify signatures.** A public URL means anyone can POST fake events; an
  unverified webhook is a security hole. Use the provider's HMAC scheme + constant-time
  compare.
- **Handle duplicates and retries.** Webhook senders retry on any non-2xx or slow
  response, so the same event arrives more than once — process **idempotently** by event
  id (7.4), and **acknowledge fast** (enqueue, don't do slow work inline).
- **Webhooks can be missed** (your endpoint was down). Robust systems pair webhooks with
  an occasional **reconciliation poll** as a safety net — don't assume every event
  always arrives.

### Where this shows up

- **Real work — payment & SaaS integrations:** Stripe, GitHub, Slack, etc. all push
  events via webhooks (payment succeeded, PR opened) instead of making you poll.
- **Real work — async job completion:** providers that run long jobs offer a "callback
  URL" so they notify you on completion rather than you polling (5.15).
- **Real work — event-driven pipelines:** "file uploaded → webhook → kick off ingestion"
  wiring in data/ML platforms.
- **Pattern mapping (secondary):** no DSA analogue; it's the push-vs-pull architectural
  choice — the inverse of polling (5.15/5.16), trading client-side loops for a
  server-hosted receiver.
[↑ Back to top](#contents)

---

<a id="5.18"></a>
## 5.18 — "Every request re-opens a fresh connection and it's slow" → session reuse & pooling

### The situation

You make thousands of requests to the same API, each as a standalone call:

```python
for url in urls:                          # all to https://api.example.com/...
    requests.get(url, timeout=10)         # each call opens a BRAND-NEW connection
```

Each `requests.get(...)` (the module-level function) sets up a **new TCP connection and
a new TLS handshake** from scratch, every time. For an HTTPS endpoint that handshake is
several network round-trips of pure setup — often 100–300 ms — *before* your actual
request is even sent. Across thousands of calls to the *same host*, you pay that setup
cost over and over for connections you immediately throw away.

### What's really going on

Opening a connection is expensive: TCP's handshake plus TLS's certificate exchange and
key negotiation can cost more than the request itself. But these connections are
**reusable** — HTTP **keep-alive** lets one connection serve many requests to the same
host. The waste comes from creating and discarding a connection per call instead of
keeping a few open and reusing them.

The fix is a **session** with a **connection pool**:

> A **`requests.Session`** keeps a pool of open connections (a **connection pool**) and
> **reuses** them across requests to the same host. The first call to a host pays the
> handshake; subsequent calls **reuse** that warm connection, skipping the setup
> entirely. The session also persists cookies, default headers, and auth across calls.

The realisation: **create the client once, reuse it for all calls.** This is the network
equivalent of not re-opening a file on every line — amortise the expensive setup.

### The move

Create one `Session` (or async client) and reuse it for every request to the host:

```python
import requests
session = requests.Session()              # one pooled, reusable client

for url in urls:
    session.get(url, timeout=10)          # reuses warm connections to the same host
```

### Why it works

The session maintains a pool of open keep-alive connections. The *first* request to
`api.example.com` performs the TCP+TLS handshake and keeps the socket open; every later
request to the same host **borrows that already-established connection** from the pool,
so it skips the 100–300 ms setup and starts sending immediately. Across thousands of
calls you pay the handshake a handful of times (pool size) instead of thousands — often
a large chunk of total runtime for many-small-request workloads. The session also
carries cookies/headers/auth so you don't re-attach them per call.

### The code, every line explained

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- One session, reused (the core win) ---------------------------------
session = requests.Session()              # holds the connection pool + shared config
session.headers.update({"Authorization": "Bearer ..."})   # set auth ONCE, not per call

for url in urls:
    resp = session.get(url, timeout=10)   # 1st call to a host: handshake; rest: reused
    ...
session.close()                           # release pooled connections when done
# Better: use it as a context manager so close() is guaranteed (1.3):
with requests.Session() as s:
    for url in urls:
        s.get(url, timeout=10)

# --- Tune the pool size for concurrency (5.2) ---------------------------
adapter = HTTPAdapter(
    pool_connections=20,   # number of DISTINCT hosts to keep pools for
    pool_maxsize=50,       # max connections kept open PER host (match your thread count)
    max_retries=Retry(total=3, backoff_factor=1,           # retry at the HTTP layer (5.9)
                      status_forcelist=[429, 502, 503, 504]),
)
session.mount("https://", adapter)        # apply to all https requests
session.mount("http://", adapter)
# If you run 50 threads (5.2) but pool_maxsize=10, threads will CONTEND for 10
# connections -> serialised. Match pool_maxsize to your worker count.

# --- Async equivalent: reuse ONE AsyncClient (5.4) ----------------------
import httpx
async def main(urls):
    async with httpx.AsyncClient() as client:   # ONE client, pooled, reused
        return await asyncio.gather(*(client.get(u, timeout=10) for u in urls))
# Creating a new AsyncClient per request would defeat pooling — same mistake as
# calling requests.get() in a loop.

# --- The anti-pattern ---------------------------------------------------
for url in urls:
    requests.get(url)            # module-level get() = new Session + pool EACH call,
                                 # thrown away immediately -> handshake every time.
```

### Impact

- **Speed:** skipping the per-call TCP+TLS handshake can cut a large fraction of runtime
  for many-small-requests-to-one-host workloads — frequently a 2–5× improvement.
- **Lower resource churn:** fewer sockets opened/closed means less load on your machine,
  the network, and the server (which also pays to set up each connection).
- **Cleaner config:** auth, headers, and retry policy live on the session, set once
  rather than repeated (and forgotten) on every call.

### Pros & cons / when NOT to

**Reach for a session/pool when:** you make more than a couple of requests to the same
host(s) — essentially every real client. With a thread pool (5.2) or async (5.4), a
shared pooled client is mandatory for good throughput.

**Watch out / when NOT to:**
- **Size the pool to your concurrency.** 50 threads sharing a 10-connection pool
  serialise on connections, silently capping your parallelism. Set `pool_maxsize` ≥
  worker count.
- **`requests.Session` thread-safety is limited.** It's generally fine to share a
  Session across threads for simple GET/POST, but for heavy concurrency prefer one
  session per thread, or use `httpx`/async which is designed for it. When in doubt,
  per-worker sessions are safest.
- **Long-lived sessions can hold stale connections** — a server or load balancer may
  drop idle keep-alives; the retry adapter handles the occasional reset.
- **For a single one-off request**, the bare `requests.get` is fine — pooling only pays
  off across multiple calls.

### Where this shows up

- **Real work — any bulk API client:** the standard pairing with thread pools (5.2) /
  async (5.4) — a shared pooled client is what makes high-concurrency clients actually
  fast.
- **Real work — database connection pools:** the exact same principle for DBs —
  SQLAlchemy/psycopg pools reuse expensive DB connections instead of reconnecting per
  query (a frequent cause of "why is every query slow?").
- **Real work — LLM/embedding clients:** reusing one client across thousands of calls so
  you're not re-handshaking on every request (Area 9).
- **Pattern mapping (secondary):** no DSA analogue; it's the "amortise expensive setup by
  reuse" principle — the same idea as object pools, buffered I/O (Area 2), and warm
  workers (Area 6).
[↑ Back to top](#contents)

---

<a id="5.19"></a>
## 5.19 — "I have to wait for the whole 2 GB response before I can use any of it" → streaming

### The situation

Two related pains. First, downloading a large file with a normal request loads the
**entire** body into memory before you can touch it:

```python
resp = requests.get("https://data/dump.csv")   # 2 GB file
data = resp.content                             # the WHOLE 2 GB is now in RAM -> may OOM
open("dump.csv", "wb").write(data)
```

Second, with an LLM/chat API the full answer takes 20 seconds to generate, and a normal
call makes the user stare at a blank screen for all 20 seconds before *anything* appears
— even though the model produces the answer word by word.

### What's really going on

By default an HTTP client **buffers the whole response** — it waits until every byte has
arrived, holds it all in memory, then hands it to you. That's wrong for two cases:
**large bodies** (you don't have RAM for all of it) and **incrementally-produced bodies**
(you want each piece as it's generated, not at the end).

The fix is **streaming**: process the response **as it arrives**, in pieces, without
buffering the whole thing. Two flavours:

- **Streamed download:** read a large body in fixed-size **chunks** and write each to
  disk immediately — constant memory regardless of file size (the network cousin of
  generators/chunked file reading, 1.2 / Area 2).
- **Server-Sent Events (SSE) / token streaming:** the server sends a sequence of small
  events as it produces them (e.g. one LLM token per event); you handle each the instant
  it lands, so output appears progressively.

> **Streaming** = consuming a response incrementally as bytes/events arrive, instead of
> waiting for and holding the complete body. Enabled with `stream=True` in `requests`,
> or an SSE/streaming client for event streams.

### The move

Open the response in streaming mode and iterate over chunks/events:

```python
with requests.get(url, stream=True, timeout=30) as resp:   # don't buffer the body
    with open("dump.csv", "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):    # 8 KB at a time
            f.write(chunk)                                  # constant memory
```

### Why it works

`stream=True` tells `requests` *not* to download the body up front — it fetches the
headers and leaves the body to be pulled on demand. `iter_content(chunk_size=8192)` then
yields the body 8 KB at a time, and you write each chunk straight to disk before
fetching the next — so at any instant only 8 KB is in memory, whether the file is 2 MB or
2 TB. For token streaming, the server flushes each event as it's produced and your loop
receives it immediately, so you can display/forward each token in real time instead of
waiting for the full completion. The `with` blocks ensure both the response and file are
closed even on error (1.3).

### The code, every line explained

```python
import requests

# --- Streamed download: constant memory for any file size ---------------
with requests.get(url, stream=True, timeout=30) as resp:   # stream=True -> lazy body
    resp.raise_for_status()
    with open("dump.csv", "wb") as f:                       # "wb" = write bytes
        for chunk in resp.iter_content(chunk_size=8192):    # pull 8 KB per iteration
            f.write(chunk)                                  # only 8 KB in RAM at a time
# Without stream=True, resp.content would load the ENTIRE 2 GB into memory first.

# --- Stream line-delimited data (e.g. a huge JSONL export) --------------
import json
with requests.get(url, stream=True, timeout=30) as resp:
    for line in resp.iter_lines():        # yields one line at a time as they arrive
        if line:                          # iter_lines can yield empty keep-alive lines
            record = json.loads(line)     # process each record without buffering all
            handle(record)

# --- SSE / token streaming from an LLM-style endpoint -------------------
with requests.post(url, json=payload, stream=True, timeout=60) as resp:
    for line in resp.iter_lines():
        if not line:
            continue
        text = line.decode("utf-8")
        if text.startswith("data: "):     # SSE frames are prefixed with "data: "
            chunk = text[len("data: "):]  # strip the prefix to get the payload
            if chunk == "[DONE]":         # many APIs send a sentinel to mark the end
                break
            token = json.loads(chunk)     # one token/delta of the answer
            print(token["text"], end="", flush=True)   # show it IMMEDIATELY (flush!)
# The user sees the answer build up word-by-word instead of a 20s blank wait.

# --- The anti-pattern ---------------------------------------------------
data = requests.get(big_url).content      # buffers the whole body -> OOM on large files
answer = requests.post(llm_url, json=p).json()["text"]   # waits for the FULL answer
```

### Impact

- **Bounded memory:** a 2 GB (or 2 TB) download runs in a few KB of memory instead of
  loading the whole body — the difference between OOM and "just works".
- **Perceived latency:** token streaming shows output as it's generated; the user sees
  progress in ~100 ms instead of staring at a blank screen for 20 seconds.
- **Pipelining:** you can start processing/forwarding early bytes while later ones are
  still arriving (overlaps with downstream work).

### Pros & cons / when NOT to

**Reach for streaming when:** the response is **large** (don't buffer it) or
**incrementally produced** (LLM tokens, live event feeds, log tails) and you want each
piece as it arrives.

**Watch out / when NOT to:**
- **Small responses don't need it.** For a few KB of JSON, plain `.json()`/`.content` is
  simpler; streaming adds complexity for no gain.
- **Set a timeout (5.8), and know it bounds inactivity, not total time.** A stream that
  trickles forever needs its own overall deadline; a stalled stream should time out.
- **Streaming holds the connection open** for the whole transfer — at high concurrency
  that ties up connections/pool slots (5.18) longer than quick requests; size pools
  accordingly.
- **Always consume or close the stream** (use the `with` block). A half-read streamed
  response leaks a connection back-pressure-style until closed.
- **Errors can occur mid-stream** — you may have already processed/written half the data
  when it fails. For downloads, write to a temp file and rename on success (atomic
  writes, Area 7) so a partial file isn't mistaken for complete.

### Where this shows up

- **Real work — large dataset/model downloads:** pulling multi-GB data dumps or model
  weights to disk in constant memory before a training run.
- **Real work — LLM chat UIs:** token-by-token streaming is what makes assistants feel
  responsive; the same SSE pattern powers live dashboards and log streaming (Area 9).
- **Real work — big exports:** streaming a huge JSONL/CSV export through a transform and
  into a database without ever holding it all in memory (pairs with generators, 1.2).
- **Pattern mapping (secondary):** streaming is the network form of lazy/iterative
  processing (generators, 1.2; chunked I/O, Area 2) — consume-as-you-go rather than
  load-then-process.
[↑ Back to top](#contents)

---

<a id="5.20"></a>
## 5.20 — "My API bill was huge and I have no idea which job caused it" → usage & cost accounting

### The situation

You run many jobs against a paid API (say an LLM provider billed per token). At
month-end the bill is large and surprising, and you can't answer basic questions: which
job spent the most? How many calls did the nightly pipeline make? Was a retry loop (5.9)
silently re-spending? Your code just makes calls and discards the usage info the API
returns:

```python
resp = llm_api(prompt=p)        # response INCLUDES usage info...
answer = resp["text"]           # ...but you only read the text and throw the rest away
# resp["usage"] -> {"input_tokens": 1820, "output_tokens": 240}  -- ignored!
```

### What's really going on

Every paid API call has a **cost**, and most responses report the **usage** that drives
it (tokens, units, credits) right there in the response. If you don't **record** that
usage, cost is invisible until the bill arrives — too late to catch a runaway loop, a
prompt that ballooned, or one job dominating spend.

The realisation: **measure cost as you go.** Capture the usage field from each response,
attribute it to a job/feature/user, accumulate it, and optionally enforce a **budget**
(stop or alert when a threshold is crossed). This turns an opaque monthly surprise into
a live, per-job number you can see, attribute, and cap.

> **Usage accounting** = recording the cost-driving units (tokens/calls/bytes) of each
> request, tagged with context (which job/user), so total and per-segment spend is
> known in real time rather than discovered on the invoice. A **budget guard** stops or
> warns when accumulated cost crosses a limit.

### The move

Wrap the API call so it records usage per call (tagged with context) and accumulates a
running cost; optionally enforce a budget:

```python
def tracked_call(prompt, *, job, tracker):
    resp = llm_api(prompt=prompt)
    u = resp["usage"]
    tracker.add(job, u["input_tokens"], u["output_tokens"])   # record before returning
    return resp["text"]
```

### Why it works

The usage data you need is already in every response — you simply stop discarding it. By
recording `(input_tokens, output_tokens)` tagged with a job name on **every** call and
summing into a tracker, you always know the live total and the breakdown by job. Because
the recording sits in one wrapper that all calls go through, nothing is missed —
including retries (5.9), which is exactly where hidden spend hides. A budget check in the
same wrapper can refuse further calls once a limit is hit, converting "surprise bill"
into "job stopped itself at ₹X".

### The code, every line explained

```python
from collections import defaultdict
import threading

# Provider's published prices (per 1M tokens) — keep these in config, not hard-coded.
PRICE_IN  = 3.00 / 1_000_000     # cost per input token
PRICE_OUT = 15.00 / 1_000_000    # cost per output token (output usually costs more)

class UsageTracker:
    def __init__(self, budget=None):
        self.by_job = defaultdict(lambda: {"in": 0, "out": 0, "calls": 0})
        self.budget = budget                  # optional spend cap in currency units
        self.lock = threading.Lock()          # safe under concurrent calls (5.2 / 1.3)

    def add(self, job, in_tok, out_tok):
        with self.lock:                        # protect shared counters across threads
            s = self.by_job[job]
            s["in"] += in_tok; s["out"] += out_tok; s["calls"] += 1
            if self.budget is not None and self.total_cost() > self.budget:
                raise RuntimeError(f"budget {self.budget} exceeded: {self.total_cost():.2f}")

    def total_cost(self):
        return sum(s["in"] * PRICE_IN + s["out"] * PRICE_OUT for s in self.by_job.values())

    def report(self):                          # per-job breakdown for logs/dashboards
        for job, s in sorted(self.by_job.items(),
                             key=lambda kv: kv[1]["in"] + kv[1]["out"], reverse=True):
            cost = s["in"] * PRICE_IN + s["out"] * PRICE_OUT
            print(f"{job}: {s['calls']} calls, {s['in']+s['out']} tokens, ${cost:.2f}")

# --- one wrapper that ALL calls go through ------------------------------
tracker = UsageTracker(budget=50.0)            # stop if this run would exceed $50
def tracked_call(prompt, *, job):
    resp = llm_api(prompt=prompt)
    u = resp["usage"]                          # the field you were throwing away
    tracker.add(job, u["input_tokens"], u["output_tokens"])
    return resp["text"]

# usage:
answer = tracked_call(my_prompt, job="nightly_summary")
# at the end:
tracker.report()    # -> "nightly_summary: 1200 calls, 2.1M tokens, $XX.XX" etc.

# --- also log per-call for after-the-fact analysis ----------------------
# Emit a structured log line per call (Area 7 logging): {"job":..., "in":..., "out":...,
# "cost":...}. Then you can aggregate spend by job/day/user from logs, not guesswork.
```

### Impact

- **Cost visibility:** you know spend per job/feature/user in real time, so the
  month-end bill holds no surprises and you can pinpoint what's expensive.
- **Runaway protection:** a budget guard halts a misbehaving loop before it spends
  thousands — the difference between a ₹50 cap and a ₹50,000 accident.
- **Optimisation targeting:** the per-job breakdown shows where to focus (caching, 1.13;
  smaller prompts; batching, 5.14) for the biggest savings.

### Pros & cons / when NOT to

**Reach for usage accounting when:** you use any metered/paid API at volume — LLMs,
embeddings, geocoding, SMS, cloud APIs — especially in automated jobs that can loop.

**Watch out / when NOT to:**
- **Track at a single choke point.** If calls bypass the wrapper, their cost is
  invisible — route *all* calls (including retries, 5.9) through one tracked function or
  client, or you'll undercount exactly where overspend hides.
- **Prices change and tiers differ** — keep rates in config, not hard-coded, and update
  them; otherwise your "cost" drifts from the real bill.
- **In-process counters are per-process.** Across many workers/replicas, aggregate via
  logs or a shared store (Redis/DB) for a true total; a local budget guard only caps one
  process.
- **A hard budget that *raises* can abort useful work mid-job** — decide whether to hard
  stop, warn-and-continue, or degrade (cheaper model). Match the policy to the job's
  importance.
- **Don't log secrets/PII** alongside usage — log token *counts* and ids, not full
  prompts, unless you've accounted for privacy (Area 7).

### Where this shows up

- **Real work — LLM/embedding pipelines:** the standard way to keep RAG/agent costs under
  control and attribute spend to features or customers (Area 9).
- **Real work — multi-tenant products:** metering per-customer usage for billing, quotas,
  or fair-use limits.
- **Real work — cloud/data jobs:** tracking API units or bytes processed per pipeline to
  catch a job whose cost suddenly jumps.
- **Pattern mapping (secondary):** no DSA analogue; it's an observability/accounting
  practice (ties to metrics & structured logging, Area 7) applied to the cost dimension
  of external calls.

[↑ Back to top](#contents)

