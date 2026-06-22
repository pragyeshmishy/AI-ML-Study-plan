# Area 1 — Pythonic Craft & Vocabulary

The "vocabulary" you reach for to write Python that is correct, readable, and fast
*because* it uses the language the way it was designed — not C or Java translated
into Python syntax. These are the moves that, once they're reflexes, change how you
*see* a problem. Bias throughout: examples from data/ML work you actually do.

---

<a id="contents"></a>
## Contents

- [1.1 — "I'm building a list with a loop and an append" → comprehensions](#1.1)
- [1.2 — "I built a giant list just to loop over it once" → generators & `yield`](#1.2)
- [1.3 — "I opened it, but did it ever get closed?" → context managers (`with`)](#1.3)
- [1.4 — "My function remembers data between calls I never told it to" → the mutable default argument trap](#1.4)
- [1.5 — "I'm managing loop indices by hand" → `enumerate` & `zip`](#1.5)
- [1.6 — "I'm pulling values out by index, one line each" → unpacking & starred assignment](#1.6)
- [1.7 — "I keep pasting the same timing/logging/retry code into every function" → decorators](#1.7)
- [1.8 — "I want a function that takes any number of arguments" → `*args` & `**kwargs`](#1.8)
- [1.9 — "Two values look equal but my `if` does the wrong thing" → `is` vs `==`](#1.9)
- [1.10 — "I check everything before I act, and it's still racy" → EAFP vs LBYL](#1.10)
- [1.11 — "I'm gluing strings together with + and it's a mess" → f-strings](#1.11)
- [1.12 — "I keep writing fiddly loops to batch, chain, or group" → itertools](#1.12)
- [1.13 — "The same expensive call runs again with the same inputs" → functools](#1.13)
- [1.14 — "My object prints as gibberish and won't compare or sort" → dunder methods](#1.14)
- [1.15 — "I need to sort by something other than the default order" → sorting with `key`](#1.15)
- [1.16 — "I'm writing loops and index math to grab parts of a sequence" → slicing](#1.16)
- [1.17 — "My empty-check works until a 0 or empty string shows up" → truthiness](#1.17)
- [1.18 — "I compute a value, then immediately test it — in two lines" → the walrus operator](#1.18)
- [1.19 — "Four lines of if/else just to pick one of two values" → conditional expressions](#1.19)
- [1.20 — "I'm layering default settings under user overrides" → dict merge & setdefault](#1.20)
- [1.21 — "A tower of if/elif inspecting the shape of my data" → the match statement](#1.21)
- [1.22 — "I passed the wrong type and only found out when it crashed" → type hints](#1.22)

---


<a id="1.1"></a>
## 1.1 — "I'm building a list with a loop and an append" → comprehensions

### The situation

You have a list of pixel brightness values read from a greyscale image — plain
integers from 0 to 255, where 0 is black and 255 is white:

```python
pixels = [0, 128, 255, 64, 200, ...]   # thousands of integers, 0–255
```

Most machine-learning models train better when inputs are scaled to the range 0.0–1.0
instead of 0–255 (this is called **normalisation** — squeezing values into a small,
consistent range so no single feature dominates). To normalise, you divide every
pixel by 255. Coming from C or Java, you'd write it as a build-a-list loop:

```python
scaled = []                         # start with an empty list to collect results
for p in pixels:                    # walk every pixel value
    scaled.append(p / 255)          # divide by 255, tack the result onto the end
# scaled is now [0.0, 0.502, 1.0, 0.251, 0.784, ...]
```

It works. But every experienced Python engineer who reads it thinks *"why isn't that
a comprehension?"* — and more importantly, it's **slower** and **noisier** than it
needs to be.

### What's really going on

This three-line pattern — **make empty list, loop, append** — is so common that
Python has dedicated syntax *and* a dedicated fast path in the interpreter for it.
It's called a **list comprehension**: a single expression that builds a list by
describing *what each element should be*, instead of spelling out the mechanical
steps of accumulation.

The deeper idea: a loop-with-append describes **how** to build the list (the
bookkeeping — create, iterate, append). A comprehension describes **what** the list
*is* ("each pixel divided by 255"). Shifting from *how* to *what* is the essence
of "Pythonic" — you state intent and let the language handle the mechanics.

There's also a real performance reason, not just style. In the loop version, Python
must look up the `.append` **method** (a function attached to the list object) and
**call** it once per element — and method lookups + calls are relatively expensive in
Python. A comprehension does the appending in optimised C code *inside the
interpreter*, skipping that per-item Python-level method call entirely. On large data
that's a measurable speed-up (often ~30–50% faster for the build itself).

### The move

Replace the build-loop-append pattern with a **list comprehension**:

```python
scaled = [p / 255 for p in pixels]
```

Read it left-to-right as a sentence: *"give me `p / 255`, for each `p` in `pixels`."*
The **expression on the left** (`p / 255`) is what each element becomes; the
**`for` clause** is the loop that feeds it.

You can add a **filter** with an `if` at the end. Say the list also contains some
`None` entries (dead pixels that the camera failed to read), and you want to keep only
the real readings:

```python
valid = [p / 255 for p in pixels if p is not None]
```

Read: *"each pixel divided by 255, for every pixel, but only if the pixel isn't
None."* The `if` decides which items make it in — replacing a loop with an
`if`/`append` inside.

### Why it works

A comprehension is one expression that the interpreter recognises and runs through an
optimised internal routine. There's no separate `.append` lookup per element, no
half-built list visible to the rest of your code, and the whole thing evaluates to
the finished list in one go. You get **what** you wanted (the derived list) without
narrating **how** to assemble it.

### The code, every line explained

```python
# --- The loop version (what you'd write in Java/C) -----------------------
scaled = []                          # empty list to accumulate into
for p in pixels:                     # iterate every pixel value
    scaled.append(p / 255)           # look up .append, call it, grow the list

# --- The comprehension (Pythonic) ----------------------------------------
scaled = [p / 255 for p in pixels]
#         └──┬───┘ └─────┬──────┘
#        expression:    the loop:
#        what each      where items
#        element becomes come from

# --- With a filter: keep only the real readings (skip dead None pixels) --
valid = [p / 255 for p in pixels if p is not None]
#                                   └──────┬──────┘
#                                    filter: only items for which
#                                    this is True are included
# `is not None` checks identity against None (Python's "no value" object).
# Use `is`/`is not` for None — not ==. (Covered fully in scenario 1.x on is vs ==.)

# --- Transform AND filter together ---------------------------------------
# Say each reading is a dict {"sensor": "A", "temp": "19.4"} and we want the
# temperatures as floats, but only for sensor "A":
temps = [float(r["temp"]) for r in readings if r["sensor"] == "A"]
# For each reading r, IF its sensor is "A", convert its temp string to a float.
# float("19.4") turns the text "19.4" into the number 19.4. Others are skipped.

# --- Dict and set comprehensions: same idea, different brackets ----------
id_to_temp = {r["sensor"]: r["temp"] for r in readings}  # {} key:value -> DICT
unique_sensors = {r["sensor"] for r in readings}         # {} single value -> SET
# These replace the same loop-and-insert pattern for dicts and sets.
```

### Impact

- **Speed:** ~30–50% faster than loop+append for building the list, because the
  per-element Python method call disappears. Matters on large feature/data arrays.
- **Clarity:** intent is on one line — a reader sees *what* the list is immediately.
- **Fewer bugs:** no half-initialised list, no chance of appending in the wrong place
  or forgetting to reset the accumulator between runs.

### Pros & cons / when NOT to

**Reach for a comprehension when:** you're building a list/dict/set by transforming
and/or filtering an iterable, and each element is a **simple expression**.

**Do NOT use one when:**
- **The body needs multiple statements** (try/except, several intermediate variables,
  logging, a nested branch). Forcing that into a comprehension makes it unreadable —
  a plain loop is the right, honest choice.
- **It gets nested two-plus levels deep** (`[x for sub in data for x in sub if ...]`).
  One level of nesting is fine; beyond that, readability collapses — use a loop or a
  generator function.
- **You only need to iterate once and not store the result** — then use a *generator*
  expression (round brackets) to avoid building the whole list in memory. (That's its
  own scenario — lazy evaluation / memory.)
- **The result is huge** and you'd hold it all in RAM unnecessarily — again, prefer a
  generator.

The rule: a comprehension should fit comfortably on one line and read like a
sentence. If it doesn't, that's the language telling you to use a loop.

### Where this shows up

- **Real work — feature prep:** `[normalize(x) for x in raw]`, building feature lists
  or cleaned columns in any ML preprocessing step.
- **Real work — filtering datasets:** `[r for r in rows if r.is_valid]` to drop bad
  rows before training — the everyday "clean the data" line.
- **Real work — building lookups:** `{r.id: r for r in rows}` is the index-building
  step behind the dict join (a data-wrangling scenario) — written as one line.
- **Pattern mapping (secondary):** comprehensions are the idiomatic way to express the
  "transform" and "filter" steps that show up constantly in array/string LeetCode
  problems (e.g. building a list of indices that satisfy a condition).
[↑ Back to top](#contents)

---

<a id="1.2"></a>
## 1.2 — "I built a giant list just to loop over it once" → generators & `yield`

### The situation

You have a large file — say a 10-million-row CSV of sensor readings, `data.csv`, that
looks like this on disk:

```
2026-01-01T00:00:00, sensor_A, 19.4
2026-01-01T00:00:01, sensor_A, 19.5
2026-01-01T00:00:02, sensor_B,
2026-01-01T00:00:03, sensor_A, 19.6
... (10 million more lines)
```

Each line is raw text: a timestamp string, a sensor id, and a temperature reading —
and some rows are dirty (notice the third line has a **missing** temperature). Before
you can train on this, each line must be **parsed and cleaned**, meaning:

- split the text line on commas into its three fields,
- convert the temperature from the string `"19.4"` into an actual `float` number,
- attach the parsed timestamp,
- and drop or default the rows where the reading is missing.

So you write a helper `parse(line)` that does exactly that for one line — turning the
raw text `"2026-01-01T00:00:00, sensor_A, 19.4"` into a clean record like
`{"ts": ..., "sensor": "sensor_A", "temp": 19.4}`. Then you write a function that
applies it to the whole file and hands back the cleaned list:

```python
def clean_rows(path):
    result = []                       # accumulate every cleaned record here
    for line in open(path):           # read the file one text line at a time
        result.append(parse(line))    # parse+clean that line, add to the list
    return result                     # hand back ALL 10 million cleaned records

for row in clean_rows("data.csv"):    # then walk them once to train
    train_step(row)                   # feed one record into the model
```

It works fine on a 1,000-row sample. But on the real 10-million-row file your process
**balloons to several GB of RAM** and may get killed by the operating system (an
"out of memory" / OOM kill — the OS terminating your program for using too much
memory). Yet look at how you *use* the result: you walk it **once**, front to back,
touching one record at a time in `train_step`. You never needed all 10 million cleaned
records sitting in memory *simultaneously* — but `clean_rows` built and stored every
one of them before `train_step` ever saw the first.

### What's really going on

You materialised the **entire** result set in memory just to consume it one item at a
time. "Materialise" means actually constructing and storing every element. The list
holds all 10M parsed rows simultaneously, even though at any given moment
`train_step` only touches **one**.

The realisation: when you **produce a sequence** and the caller **consumes it once,
in order**, you don't need to store the whole thing. You can produce each item
**on demand** — hand one out, let the caller use it, then produce the next — so only
**one item lives in memory at a time**. This is called **lazy evaluation** ("lazy" =
compute it only when it's actually needed, not ahead of time).

The tool for this in Python is the **generator**.

### The move

Turn the function into a **generator** by replacing `return`-a-list with **`yield`**
per item:

```python
def clean_rows(path):
    for line in open(path):
        yield parse(line)             # hand out ONE row, then pause here
```

A **generator** is a function that produces a sequence **lazily** — it computes and
hands back one value at a time, pausing between each. The keyword that makes it a
generator is **`yield`**. `yield value` means *"give the caller this value now, then
freeze this function exactly where it is — local variables, loop position, everything
— until the caller asks for the next one."*

### Why it works

The magic is that **`yield` pauses the function instead of ending it.** A normal
`return` runs the function to completion and throws away its internal state. `yield`
suspends the function mid-execution, keeping the loop variable and position alive, and
**resumes** from that exact spot when the next item is requested.

So the loop `for row in clean_rows(path)` works like this under the hood: ask the
generator for a row → it runs until it hits `yield`, hands you the parsed row, and
freezes → you call `train_step(row)` → ask for the next → it **un-freezes**, reads the
next line, parses, yields again. Only **one parsed row exists at any instant**. The
file is also read one line at a time (because `open()` is itself lazy), so neither the
file nor the result list is ever fully in memory.

Memory goes from **O(n)** (all n rows stored) to **O(1)** (one row at a time) — flat,
regardless of whether the file has 10 thousand or 10 billion rows.

### The code, every line explained

```python
# --- Eager version: builds the whole list (memory = O(n)) ----------------
def clean_rows(path):
    result = []
    for line in open(path):
        result.append(parse(line))   # all n rows held at once
    return result                    # caller gets a fully-built list

# --- Lazy version: a generator (memory = O(1)) ---------------------------
def clean_rows(path):
    for line in open(path):          # open() yields lines lazily too
        yield parse(line)            # produce one row, pause, resume on demand
# NOTE: the moment a function contains `yield`, calling it does NOT run the
# body. It returns a "generator object" — a paused recipe. The body only runs
# as you pull items out of it.

gen = clean_rows("data.csv")         # nothing parsed yet! gen is a paused recipe.
first = next(gen)                    # next(gen) runs the body until the first yield,
                                     # returns that row, then freezes. ONE row parsed.
for row in clean_rows("data.csv"):   # the normal way to drain a generator:
    train_step(row)                  # each loop pulls the next row, uses it, discards.
# When the function's own loop ends (file exhausted), the generator is "done":
# the for-loop stops automatically (it raises StopIteration internally).

# --- Generator EXPRESSION: the one-liner form ----------------------------
# Same as a list comprehension but with ROUND brackets -> lazy, not stored.
total = sum(row.value for row in clean_rows("data.csv"))
#           └──────────────┬──────────────────────────┘
#           a generator expression: produces values one at a time straight
#           into sum(), so the 10M values are never all held in memory.
# Compare: sum([row.value for row in ...])  # the [] version builds the full
# list first (wasteful). Dropping the brackets makes it lazy and O(1) memory.
```

### Impact

- **Memory:** O(n) → O(1). This is the difference between an OOM kill and a job that
  runs in a flat, tiny memory footprint on arbitrarily large data.
- **Latency to first item:** the eager version makes you wait until *all* n rows are
  built before anything happens; a generator yields the **first** row immediately, so
  downstream work starts right away (important for streaming/pipelines).
- **Composability:** generators chain — one generator can feed another (clean → filter
  → batch) with each stage still O(1) memory. (Its own pipeline scenario later.)

### Pros & cons / when NOT to

**Reach for a generator when:** you produce a sequence consumed **once, in order**, or
the data is **large / unbounded / streaming** (files, API pages, training batches).

**Watch out / when NOT to:**
- **Single-use:** a generator is exhausted after one pass. Looping over it a second
  time yields **nothing** — it's not a stored list. If you need to iterate repeatedly,
  materialise it once with `list(gen)` (and accept the memory cost).
- **No len(), no indexing:** you can't do `len(gen)` or `gen[5]` — there's nothing
  stored to measure or index. If you need random access or a count up front, use a
  list.
- **Tiny data:** for a few hundred items you'll loop over multiple times, a plain list
  is simpler and the memory saving is irrelevant. Don't add laziness you don't need.
- **Side effects + laziness can surprise you:** because the body only runs as you
  consume, code inside the generator (including an `open()` or a DB call) executes
  *later* than you might expect. Don't rely on a generator's body having run until
  you've actually drained it.

### Where this shows up

- **Real work — training data loaders:** stream batches from disk so you never load the
  full dataset into RAM. Every `DataLoader` / `tf.data` pipeline is this idea.
- **Real work — large file/ETL processing:** `for row in clean_rows(huge_file)` to
  transform a file bigger than memory line by line.
- **Real work — paginated APIs:** a generator that `yield`s items page by page lets the
  caller iterate "all results" without you buffering every page. (See the pagination
  scenario in the APIs area.)
- **Pattern mapping (secondary):** generators implement the **iterator** pattern; in
  algorithm problems they're handy for producing values on the fly (e.g. an in-order
  tree traversal that `yield`s nodes lazily, or generating combinations without storing
  them all).
[↑ Back to top](#contents)

---

<a id="1.3"></a>
## 1.3 — "I opened it, but did it ever get closed?" → context managers (`with`)

### The situation

You have a list of result records — say model predictions like
`{"id": "img_001", "label": "cat", "score": 0.92}` — and you want to write them to a
CSV file, one comma-separated line each (`format_row` turns one dict into the text
`"img_001,cat,0.92\n"`). You open the file, write each line, and move on:

```python
f = open("results.csv", "w")        # open the file for writing
for row in results:
    f.write(format_row(row))        # turn the record into a CSV line, write it
f.close()                           # close it when done
```

Looks fine. But two things go wrong in real code. First, if `format_row` or `.write`
**raises an exception** partway through, the line `f.close()` is **never reached** —
the file is left open, and on many systems your buffered writes are **lost or
truncated** because they were never flushed to disk. Second, in a long-running service
that opens files (or database connections, or sockets) in a loop, forgetting
`.close()` leaks **file handles** — a limited OS resource — until the process hits
"too many open files" and crashes.

### What's really going on

The real problem is **guaranteeing cleanup even when things go wrong.** Any resource
you *acquire* — a file, a DB connection, a network socket, a lock — must be *released*,
and it must be released **whether the code in between succeeds or throws**. Relying on
a `.close()` call at the bottom is fragile: any early `return`, exception, or `break`
between open and close silently skips it.

You *could* solve this manually with `try/finally` (a block whose `finally` part runs
no matter what — covered fully in the error-handling area):

```python
f = open("results.csv", "w")
try:
    for row in results:
        f.write(format_row(row))
finally:
    f.close()                       # runs even if the try block raises
```

That's correct but verbose, and you'd repeat it for every resource. Python has
dedicated syntax that does exactly this for you: the **context manager**, used via the
**`with`** statement.

### The move

Wrap the resource in a **`with`** block:

```python
with open("results.csv", "w") as f:   # acquire the file, bind it to f
    for row in results:
        f.write(format_row(row))
# <- the file is AUTOMATICALLY closed here, the instant the block ends,
#    whether it ended normally OR because an exception was raised inside it.
```

A **context manager** is any object that knows how to do **setup** when you enter a
block and **teardown** when you leave it. The `with` statement runs the setup, binds
the result to the name after `as`, runs your block, and then *guarantees* the teardown
— exceptions included. For a file, teardown means "flush buffered writes and close the
handle."

### Why it works

Under the hood, the `with` statement uses two special methods on the object:

- **`__enter__`** — runs when you enter the block; its return value is what `as f`
  binds to. (For a file, it returns the open file object.)
- **`__exit__`** — runs when you leave the block *for any reason* — normal completion,
  `return`, `break`, or an exception. (For a file, it closes the handle.)

Because Python calls `__exit__` as part of unwinding the block — the same machinery as
`finally` — there is **no path out of the block that skips cleanup**. That's the whole
guarantee. `with` is essentially `try/finally` with the boilerplate hidden and the
intent made obvious.

### The code, every line explained

```python
# --- Files: the everyday case --------------------------------------------
with open("results.csv", "w") as f:   # __enter__ opens the file, returns it -> f
    for row in results:
        f.write(format_row(row))
# __exit__ flushes + closes f here, guaranteed. No .close() to forget.

# --- Multiple resources in one with --------------------------------------
with open("in.csv") as src, open("out.csv", "w") as dst:
    for line in src:                  # read from one file...
        dst.write(transform(line))    # ...write to another
# BOTH files are closed on exit, even if transform() raises. Order: dst closed
# first, then src (reverse of how they were opened).

# --- Locks: the SAME pattern protects a shared resource ------------------
from threading import Lock
lock = Lock()                         # a lock = a "only one thread at a time" gate
with lock:                            # __enter__ acquires the lock
    shared_counter += 1               # critical section: only one thread in here
# __exit__ RELEASES the lock here — even if the body raised. Forgetting to
# release a lock on an error path is a classic deadlock cause; `with` prevents it.

# --- Write your OWN context manager with contextlib ----------------------
from contextlib import contextmanager
import time

@contextmanager                       # this decorator turns a generator into a
def timed(label):                     # context manager (decorators: scenario 1.x)
    start = time.perf_counter()       # SETUP: runs on entering the block
    try:
        yield                         # <- the block's body runs at this yield
    finally:
        dur = time.perf_counter() - start
        print(f"{label} took {dur:.3f}s")   # TEARDOWN: runs on exit, even on error

with timed("training epoch"):         # use it like any context manager
    run_epoch(model, data)            # whatever happens, the timing prints
# Everything before `yield` is __enter__; everything after is __exit__.
```

### Impact

- **Correctness/reliability:** resources are released on every exit path, eliminating
  the leaked-handle and lost-write bugs that only show up under errors or load — the
  kind that pass every test and then fail in production.
- **Clarity:** `with` makes the resource's *lifetime* visually explicit — it lives
  exactly as long as the indented block, no more.
- **Less code:** replaces the 5-line `try/finally` boilerplate with one line, and you
  can't forget the cleanup half.

### Pros & cons / when NOT to

**Reach for `with` when:** you acquire anything that must be released — files, sockets,
DB connections/cursors, locks, `subprocess` pipes, temporary directories, even "set a
state then restore it" (e.g. `torch.no_grad()` in PyTorch is a context manager that
turns gradient tracking off inside the block and back on after).

**Notes / when it doesn't apply:**
- **The object must support the protocol** (`__enter__`/`__exit__`). Most resource
  objects in the standard library and major frameworks do. If something doesn't, wrap
  it with `contextlib.contextmanager` as shown, or `contextlib.closing`.
- **Long-lived resources** that intentionally outlive a single block (e.g. a connection
  pool created once at startup and reused for the app's lifetime) are **not** a fit for
  a `with` around your whole program — manage those explicitly. `with` is for scoped,
  "use it here and release it" lifetimes.
- **Don't return the resource out of the block** expecting it to still be open — once
  the block exits, it's closed. Keep the usage inside the `with`.

### Where this shows up

- **Real work — every file/DB interaction:** reading datasets, writing model outputs,
  DB cursors — `with` is the default, non-negotiable way to do I/O safely.
- **Real work — locks in concurrent code:** `with lock:` is the standard way to guard a
  critical section so the lock is always released (ties to the races/locks scenarios).
- **Real work — ML framework state:** `with torch.no_grad():` during inference,
  `with mlflow.start_run():` to ensure a run is closed/logged even on failure.
- **Real work — temp resources:** `with tempfile.TemporaryDirectory() as d:` auto-
  deletes the directory on exit — handy for scratch space in data jobs.
- **Pattern mapping (secondary):** no direct algorithm analogue; this is a
  resource-safety idiom. The transferable idea is "acquire/release must be balanced,"
  which also underlies the stack-based bracket-matching family of problems.
[↑ Back to top](#contents)

---

<a id="1.4"></a>
## 1.4 — "My function remembers data between calls I never told it to" → the mutable default argument trap

### The situation

You write a helper that collects items into a list, with a sensible-looking default
so the caller can omit it:

```python
def add_feature(value, into=[]):      # default: start with an empty list
    into.append(value)
    return into

print(add_feature(1))                 # expect [1]      -> [1]    ✓
print(add_feature(2))                 # expect [2]      -> [1, 2] ✗ !!
print(add_feature(3))                 # expect [3]      -> [1, 2, 3] ✗ !!
```

The second call returns `[1, 2]` — it **remembered** the `1` from the first call,
even though you passed a fresh argument and expected a clean start. The list is
somehow **shared across every call**. In real code this shows up as a function that
mysteriously accumulates data from previous runs, or two unrelated objects that
silently share state — a maddening bug because the function body looks completely
correct.

### What's really going on

This is the single most famous gotcha in Python, and it comes from one rule:
**a default argument value is created ONCE, when the function is defined — not each
time the function is called.**

When Python first reads the `def add_feature(value, into=[])` line, it evaluates `[]`
**once**, builds a single empty list, and stores it as *the* default. Every call that
omits `into` reuses **that same one list object**. Because a list is **mutable** (it
can be changed in place — `.append` modifies the existing list rather than making a
new one), each call's `.append` piles onto the same shared list. The list survives
between calls because it's attached to the function itself, not recreated per call.

> **Mutable vs immutable** — the heart of this. *Mutable* objects can be changed in
> place: `list`, `dict`, `set`. *Immutable* objects cannot — `int`, `str`, `tuple`,
> `float`, `bool`; "changing" one actually makes a new object. The trap only bites with
> **mutable** defaults, because only those can be modified in place to carry state
> forward. A default of `0` or `"x"` is harmless — you can't mutate it.

### The move

**Never use a mutable object as a default.** Use `None` as the default — a safe,
immutable sentinel meaning "nothing was passed" — and create the real mutable object
*inside* the function body, so it's fresh on every call:

```python
def add_feature(value, into=None):    # safe default: the immutable None
    if into is None:                  # caller didn't supply one...
        into = []                     # ...so make a BRAND NEW list, this call only
    into.append(value)
    return into
```

### Why it works

The `if into is None: into = []` line runs **on every call**, so a new empty list is
created each time the caller omits the argument — no sharing, no memory between calls.
`None` itself is immutable and a single shared `None` is harmless because you never
modify it; you only *check* it with `is None` and then replace it.

Using `None` as the sentinel (rather than, say, an empty list) also correctly
distinguishes "caller passed nothing" from "caller deliberately passed an empty list,"
which can matter.

### The code, every line explained

```python
# --- The TRAP: mutable default, created once, shared forever -------------
def add_feature(value, into=[]):      # [] built ONCE at definition time
    into.append(value)                # mutates the ONE shared list
    return into
# add_feature(1) -> [1]; add_feature(2) -> [1, 2]  (leaked state!)

# --- The FIX: None sentinel + fresh object inside ------------------------
def add_feature(value, into=None):    # None is immutable -> safe as a default
    if into is None:                  # `is None` = identity check for "not given"
        into = []                     # fresh list per call -> no shared state
    into.append(value)
    return into
# add_feature(1) -> [1]; add_feature(2) -> [2]  (correct, independent)

# --- Same trap with a dict default (and the same fix) --------------------
def tag(record, labels=None):         # NOT labels={}
    if labels is None:
        labels = {}                   # fresh dict each call
    labels[record.id] = record.label
    return labels

# --- Proof of "evaluated once": a timestamp default freezes at import ----
import time
def log_event(name, when=time.time()):   # WRONG: time.time() runs ONCE, at def
    return f"{name} @ {when}"
# Every call shows the SAME timestamp — the import-time one — not "now".
# Fix: default to None, then `when = time.time()` inside the body so it's
# evaluated per call.

# --- When a mutable default is actually FINE (deliberate caching) --------
def fib(n, _cache={}):                # intentionally shared dict as a memo store
    if n in _cache:                   # the "evaluated once" behaviour is the POINT:
        return _cache[n]              # the cache must persist across calls
    _cache[n] = n if n < 2 else fib(n-1, _cache) + fib(n-2, _cache)
    return _cache[n]
# This is the rare case where you WANT the shared-across-calls property.
# The leading underscore signals "internal, don't pass this." But prefer
# functools.lru_cache for real memoization (its own scenario) — clearer intent.
```

### Impact

- **Correctness:** eliminates a class of "phantom state" bugs where a function leaks
  data between calls, or two objects unexpectedly share a list/dict. These are
  notoriously hard to spot because the body looks right and tests that call the
  function once never reveal it.
- **Predictability:** each call starts from a clean slate, which is what every reader
  assumes a default like `[]` means.

### Pros & cons / when NOT to

- The `None`-sentinel pattern is **the** standard fix — there's essentially no downside;
  it's a few extra lines that make the function correct.
- **The one exception** is when you *deliberately* want state that persists across calls
  (a cache/memo), shown above — but even then, `functools.lru_cache` or an explicit
  class attribute usually expresses the intent more clearly than a sneaky mutable
  default.
- **Linters catch this:** tools like `ruff`/`pylint` flag "mutable default argument"
  (rule B006). Worth enabling so the trap is caught before review.

### Where this shows up

- **Real work — config/option dicts:** `def build_model(layers, opts=None)` — a mutable
  `opts={}` default would let one model's tweaks bleed into the next model built.
- **Real work — accumulator helpers:** any `def collect(x, results=None)` that gathers
  items; the trap makes a second dataset's results pile onto the first's.
- **Real work — dataclasses (related):** the same rule is why `@dataclass` **forbids**
  `tags: list = []` and makes you write `tags: list = field(default_factory=list)` —
  `default_factory` calls `list()` fresh per instance. (Covered in the dataclass
  scenario.)
- **Pattern mapping (secondary):** the deliberate-cache version is exactly the
  memoization technique behind top-down dynamic programming (e.g. Fibonacci, climbing
  stairs) — the same "persist across calls" property, used on purpose.
[↑ Back to top](#contents)

---

<a id="1.5"></a>
## 1.5 — "I'm managing loop indices by hand" → `enumerate` & `zip`

### The situation

Two everyday looping needs, both usually done the clumsy way.

**Need 1 — I want the position *and* the item:**

```python
i = 0                                 # manual counter
for prediction in predictions:
    print(i, prediction)              # I want "row number + value"
    i += 1                            # easy to forget, easy to misplace
```

**Need 2 — I want to walk two lists together** (e.g. predictions vs ground-truth
labels, side by side):

```python
for i in range(len(predictions)):     # loop over indices...
    pred = predictions[i]             # ...then index into BOTH lists
    actual = labels[i]
    if pred != actual:
        errors += 1
```

Both work, but both are noisy, and both are **bug magnets**: an off-by-one on the
counter, forgetting `i += 1`, or `range(len(...))` when the two lists aren't the same
length.

### What's really going on

In both cases you're doing **manual bookkeeping that the language can do for you**.
The `range(len(x))` idiom in particular is a dead giveaway that you're "thinking in C"
— treating a Python sequence like a raw array you must index — when Python wants you to
iterate over **items**, not indices.

- For Need 1, the realisation: *"I don't need to maintain a counter; I need each item
  paired with its index."*
- For Need 2, the realisation: *"I don't need indices at all; I need the two sequences
  walked in lockstep, one pair at a time."*

Python has a built-in for each: **`enumerate`** pairs each item with its index, and
**`zip`** walks multiple sequences together.

### The move

**`enumerate(seq)`** yields `(index, item)` pairs, so the counter is handled for you:

```python
for i, prediction in enumerate(predictions):
    print(i, prediction)
```

**`zip(a, b, ...)`** yields tuples that pair up the i-th item of each sequence, so you
walk them in lockstep without indices:

```python
for pred, actual in zip(predictions, labels):
    if pred != actual:
        errors += 1
```

### Why it works

`enumerate` wraps the sequence and, as you iterate, hands back a running count
alongside each item — the `i, prediction` on the left **unpacks** that `(index, item)`
pair into two names automatically. No counter variable, nothing to increment, nothing
to misplace.

`zip` pulls one item from *each* sequence per step and bundles them into a tuple;
`pred, actual` unpacks that tuple. It iterates by **items**, so there are no index
expressions to get wrong. Both are **lazy** (like generators, 1.2) — they produce
pairs on demand rather than building a new list, so they're memory-cheap on large
data.

One important `zip` behaviour: it **stops at the shortest** sequence. If `predictions`
has 100 items and `labels` has 98, `zip` yields 98 pairs and silently ignores the
extra 2 — which is sometimes what you want and sometimes a hidden bug (see when-not-to).

### The code, every line explained

```python
# --- enumerate: index + item, no manual counter --------------------------
for i, prediction in enumerate(predictions):
    #   │  │              └ wraps the sequence, yields (0, pred0), (1, pred1), ...
    #   │  └ the item at that position
    #   └ the running index, maintained for you
    print(i, prediction)

# Start counting from 1 instead of 0 (e.g. human-readable row numbers):
for line_no, line in enumerate(file, start=1):   # start= sets the first index
    print(f"line {line_no}: {line.strip()}")     # 1, 2, 3, ... not 0, 1, 2

# --- zip: walk two (or more) sequences in lockstep -----------------------
for pred, actual in zip(predictions, labels):
    #   │     │        └ yields (pred0, actual0), (pred1, actual1), ...
    #   │     └ i-th item of labels
    #   └ i-th item of predictions
    if pred != actual:
        errors += 1

# Three at once works too:
for name, pred, actual in zip(feature_names, preds, labels):
    ...

# --- zip + enumerate together: index AND paired items --------------------
for i, (pred, actual) in enumerate(zip(preds, labels)):
    # note the (pred, actual) parentheses: enumerate yields (i, item) where the
    # item is itself the zip pair, so we unpack it in one go.
    if pred != actual:
        print(f"mismatch at row {i}: predicted {pred}, actual {actual}")

# --- zip to BUILD a dict (pair keys with values) -------------------------
metrics = dict(zip(["accuracy", "precision", "recall"], [0.91, 0.88, 0.84]))
# -> {"accuracy": 0.91, "precision": 0.88, "recall": 0.84}

# --- zip(*...) : the "unzip"/transpose trick -----------------------------
pairs = [(1, "a"), (2, "b"), (3, "c")]
nums, letters = zip(*pairs)           # * unpacks the list into separate args, so
                                      # zip pairs all 1st items, all 2nd items:
                                      # nums = (1, 2, 3); letters = ('a','b','c')
# Handy for splitting a list of (x, y) samples into an X list and a y list.
```

### Impact

- **Correctness:** removes off-by-one and forgotten-increment bugs, and the
  `range(len())` indexing class of errors entirely.
- **Clarity:** the loop reads as "for each index and item…" or "for each prediction
  paired with its label…", which is the actual intent.
- **Memory/speed:** both are lazy iterators — no intermediate index list, cheap on
  large datasets.

### Pros & cons / when NOT to

**Reach for `enumerate` when:** you need the position *and* the item (numbering rows,
recording the index of a match, building `{i: item}`).

**Reach for `zip` when:** you process several equal-length sequences in parallel —
predictions vs labels, features vs names, columns of a table row by row.

**Watch out / when NOT to:**
- **`zip` truncates to the shortest input silently.** If the sequences *should* be the
  same length and a mismatch is a bug, use **`zip(a, b, strict=True)`** (Python 3.10+),
  which raises `ValueError` on length mismatch instead of quietly dropping items.
- **You genuinely need indices for arithmetic** — e.g. comparing `a[i]` with `a[i+1]`
  (neighbours), or jumping by a step. There, indexing or `range` is legitimate;
  `enumerate`/`zip` don't replace *every* index use, only the bookkeeping ones.
- **`zip` is single-use** like any iterator: if you need the zipped result twice,
  wrap it in `list(...)`.

### Where this shows up

- **Real work — evaluation loops:** `for pred, actual in zip(preds, labels)` to compute
  accuracy/confusion-matrix counts — the canonical ML metric loop.
- **Real work — labelled logging/reporting:** `enumerate` to print "row 42 failed
  validation" with the exact position in the dataset.
- **Real work — column/feature handling:** `zip(feature_names, row)` to pair each value
  in a row with its column name when building records or dicts.
- **Real work — batching/splitting samples:** the `zip(*batch)` transpose to split a
  list of `(input, target)` pairs into parallel input/target lists for a model.
- **Pattern mapping (secondary):** `enumerate` is constant in array problems that must
  return *indices* (e.g. "two sum" returns positions, not values); `zip(a, a[1:])`
  pairs each element with its neighbour — a clean way to express "compare adjacent
  elements" problems.
[↑ Back to top](#contents)

---

<a id="1.6"></a>
## 1.6 — "I'm pulling values out by index, one line each" → unpacking & starred assignment

### The situation

You have a record as a tuple or list and you pull the pieces out positionally:

```python
row = ("C-1024", "Mumbai", 4999.0)    # (customer_id, city, amount)
customer_id = row[0]                  # one line...
city = row[1]                         # ...per...
amount = row[2]                       # ...field
```

Or you want to split a list into "the first thing" and "everything else":

```python
parts = line.split(",")               # e.g. ["epoch", "0.91", "0.88", "0.84"]
header = parts[0]                      # "epoch"
rest = parts[1:]                       # ["0.91", "0.88", "0.84"]  -> slice by hand
```

Both work, but the index numbers (`[0]`, `[1]`, `[2]`, `[1:]`) are noise, and a
mis-numbered index silently grabs the wrong field.

### What's really going on

Python lets you assign **multiple names at once** from any sequence — this is called
**unpacking** (or *destructuring*): you write the *shape* of the data on the left and
Python distributes the pieces into the names. You're describing the structure once
instead of indexing into it repeatedly. It's not just shorter — naming all the fields
on one line documents the record's layout at a glance, and Python checks the count
matches (catching "I forgot a column" bugs immediately).

For the "first vs rest" case, the **starred target** (`*name`) captures "all the
remaining items" into a list, so you don't hand-slice.

### The move

Assign the names all at once by mirroring the structure:

```python
customer_id, city, amount = row       # three names <- three-item sequence
```

Use a **starred name** to absorb the variable-length middle or tail:

```python
header, *values = parts               # header = first item; values = list of the rest
```

### Why it works

When the left side of `=` is several names (or a nested pattern), Python iterates the
right-hand sequence and binds each element to the matching name **by position**. If
the counts don't match, it raises `ValueError: too many values to unpack` (or "not
enough") — so a wrong-shaped row fails **loudly and immediately** instead of silently
giving you the wrong field three lines later.

A `*name` target is greedy-but-fair: Python first satisfies all the plain names around
it, then `*name` scoops up **whatever is left** into a list. That's how `header,
*values = parts` always puts the first element in `header` and the remainder in
`values`, regardless of how many items there are.

### The code, every line explained

```python
# --- Basic unpacking: name every field on one line ----------------------
row = ("C-1024", "Mumbai", 4999.0)
customer_id, city, amount = row       # binds by position; counts must match
# If row had 2 or 4 items, this raises ValueError -> the bug surfaces here, now.

# --- Swap without a temp variable ----------------------------------------
a, b = b, a                           # the right side builds a tuple (b, a) first,
                                      # then unpacks it into a, b. No temp needed.

# --- Starred target: first / rest ----------------------------------------
parts = ["epoch", "0.91", "0.88", "0.84"]
header, *values = parts               # header="epoch"; values=["0.91","0.88","0.84"]
*init, last = parts                   # init=["epoch","0.91","0.88"]; last="0.84"
first, *middle, last = parts          # first="epoch"; middle=["0.91","0.88"]; last="0.84"
# The starred name always becomes a LIST (possibly empty), the others are single items.

# --- Ignore fields you don't need with _ ---------------------------------
customer_id, _, amount = row          # `_` is a conventional "throwaway" name:
                                      # it means "I must unpack this slot but don't
                                      # care about it." (It's a real variable named _,
                                      # just a signal to readers it's unused.)
_, *features = row                    # skip the first column (label), keep features

# --- Nested unpacking: mirror nested structure --------------------------
record = ("C-1024", (19.0, 72.8))     # (id, (lat, lon))
cust_id, (lat, lon) = record          # parentheses on the left mirror the nesting
# cust_id="C-1024", lat=19.0, lon=72.8

# --- Unpacking in a loop (combines with zip/enumerate from 1.5) ---------
points = [(1, 2), (3, 4), (5, 6)]
for x, y in points:                   # each (x, y) tuple unpacks straight into x, y
    plot(x, y)

# --- Real ML shape: split label from features per row -------------------
for label, *features in dataset_rows: # first column is the target, rest are inputs
    X.append(features)                # features is a list of the remaining columns
    y.append(label)
```

### Impact

- **Correctness:** the count check turns silent wrong-field bugs into an immediate,
  obvious `ValueError`. Mismatched-shape data fails at the unpack, not deep in
  downstream logic.
- **Clarity:** one line names the whole record, documenting its layout. A reader sees
  `customer_id, city, amount = row` and instantly knows the row's structure.
- **Less code:** no index arithmetic, no manual slicing, no temp variable for swaps.

### Pros & cons / when NOT to

**Reach for unpacking when:** a function returns several values, you iterate tuples/
pairs, you split a sequence into head/tail, or you're naming the fields of a fixed-
shape record.

**Watch out / when NOT to:**
- **You don't know the length and there's no star** → plain unpacking raises on a
  mismatch. Either use a `*` target to absorb the variable part, or index defensively.
- **Many fields (5+) with no natural names in order** → positional unpacking gets
  error-prone (easy to transpose two). Prefer a `NamedTuple`/`dataclass` so you access
  by *name* (`row.amount`) instead of relying on position. (Own scenario in the design
  area.)
- **The starred capture on huge data** builds a real list of "the rest" — fine for a
  row's columns, but don't `first, *rest = ten_million_items` if you only needed the
  first (that copies ~10M items into `rest`). Use an iterator/`next()` instead.

### Where this shows up

- **Real work — functions returning multiple values:** `loss, accuracy = evaluate(model)`
  — unpacking a returned tuple is the everyday way to read multi-value results.
- **Real work — splitting features/labels:** `label, *features = row` while loading a
  dataset, exactly as shown — a daily data-prep line.
- **Real work — parsing structured lines:** `key, *vals = line.split(",")` for CSV/log
  rows with a fixed first field and a variable tail.
- **Real work — coordinate/shape handling:** `batch, channels, height, width = tensor.shape`
  to read a tensor's dimensions into named variables in one line.
- **Pattern mapping (secondary):** `a, b = b, a` swap appears constantly in in-place
  array algorithms (reversing, partitioning, sorting); `first, *rest` mirrors the
  head/tail decomposition used in recursive list processing.
[↑ Back to top](#contents)

---

<a id="1.7"></a>
## 1.7 — "I keep pasting the same timing/logging/retry code into every function" → decorators

### The situation

You want to know how long each step of your pipeline takes, so you paste timing code
into every function:

```python
def load_data(path):
    start = time.perf_counter()       # timing boilerplate...
    result = _actually_load(path)     # ...the one real line...
    print(f"load_data took {time.perf_counter() - start:.2f}s")  # ...more boilerplate
    return result

def train(model, data):
    start = time.perf_counter()       # the SAME boilerplate again
    result = _actually_train(model, data)
    print(f"train took {time.perf_counter() - start:.2f}s")
    return result
```

The actual work is one line; the timing is copy-pasted noise around it. Same story for
logging entry/exit, retrying on failure, or checking a cache — you end up duplicating
the *same wrapper logic* across dozens of functions, and changing it means editing
every copy.

### What's really going on

You're mixing two separate concerns in one place: **what the function does** (load,
train) and a **cross-cutting behaviour** wrapped around it (timing, logging, retry).
"Cross-cutting" means it applies to *many* functions regardless of what they do. Copy-
pasting it couples that behaviour to each function and scatters it everywhere.

The realisation: *the wrapper logic is identical; only the inner function changes.* So
you want to write the wrapper **once** and **apply** it to any function — wrap a
function in extra behaviour without touching the function's own body. That's exactly
what a **decorator** is.

A **decorator** is a function that takes a function and returns a new function that
*adds behaviour around* the original. This is possible because in Python **functions
are first-class objects** — you can pass a function as an argument, return one from
another function, and store one in a variable, just like an int or a list.

### The move

Write the wrapper once as a decorator, then apply it with **`@decorator`** above any
function:

```python
@timed                                # apply the "timing" behaviour to this function
def load_data(path):
    return _actually_load(path)       # the body is now JUST the real work

@timed                                # reuse the same behaviour, zero duplication
def train(model, data):
    return _actually_train(model, data)
```

### Why it works

The line `@timed` above `def load_data` is shorthand for
`load_data = timed(load_data)` — Python passes your function into `timed`, and rebinds
the name `load_data` to whatever `timed` returns. `timed` returns a **wrapper
function** that runs the extra logic (start timer, call the real function, stop timer)
and hands back the real function's result. So when anyone later calls `load_data(...)`,
they're really calling the wrapper, which times the inner call transparently.

Because the wrapper accepts `*args, **kwargs` (1.x) and passes them straight through,
**one decorator works on any function regardless of its signature** — that's what makes
it reusable across your whole codebase.

### The code, every line explained

```python
import time
from functools import wraps           # preserves the wrapped function's identity

def timed(func):                      # a decorator takes the function to wrap
    @wraps(func)                      # copies func's name/docstring onto wrapper, so
                                      # load_data still "looks like" load_data to tools
                                      # and tracebacks (without this, it'd show as
                                      # "wrapper", which breaks debugging & help()).
    def wrapper(*args, **kwargs):     # accepts ANY arguments -> works on any function.
                                      # *args = positional args as a tuple;
                                      # **kwargs = keyword args as a dict. (Own scenario.)
        start = time.perf_counter()   # the "before" behaviour
        result = func(*args, **kwargs)   # call the REAL function, forwarding all args
        dur = time.perf_counter() - start
        print(f"{func.__name__} took {dur:.3f}s")   # the "after" behaviour
        return result                 # hand back the real result, unchanged
    return wrapper                    # the decorator returns the wrapped version

@timed                                # == load_data = timed(load_data)
def load_data(path):
    return _actually_load(path)

load_data("data.csv")                 # actually calls wrapper -> times the inner call
                                      # prints e.g. "load_data took 1.231s"
```

```python
# --- A decorator that takes ARGUMENTS (e.g. retry N times) ---------------
def retry(times):                     # outer fn takes the CONFIG (how many retries)
    def decorator(func):              # middle fn takes the function (as usual)
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)   # success -> return immediately
                except Exception as e:
                    if attempt == times - 1:       # last attempt failed -> give up
                        raise                       # re-raise the real error
                    print(f"retry {attempt+1}/{times} after {e}")
        return wrapper
    return decorator

@retry(times=3)                       # retry(3) returns `decorator`, which wraps fetch
def fetch(url):
    return http_get(url)              # transient failures now retried up to 3x
# The extra layer exists because @retry(3) must first consume the argument (3),
# THEN receive the function. Three nested functions = "decorator with arguments".
```

### Impact

- **No duplication:** the cross-cutting logic lives in one place; fix or improve it once
  and every decorated function benefits. Removing it is deleting one `@line`.
- **Readability:** each function's body shrinks to its real job; the `@timed`/`@retry`
  tag declares the added behaviour up front, like a label.
- **Composability:** stack decorators (`@timed` then `@retry(3)` on the same function)
  to combine behaviours without writing combined code.

### Pros & cons / when NOT to

**Reach for a decorator when:** the *same wrapping behaviour* applies to many functions
— timing, logging, retry, caching, auth checks, input validation, registering a
function in a table.

**Watch out / when NOT to:**
- **Always use `functools.wraps`** on the inner wrapper. Without it, the decorated
  function loses its real `__name__`, docstring, and signature — breaking tracebacks,
  `help()`, and some frameworks. It's a one-line habit that prevents real debugging
  pain.
- **Don't hide important control flow.** A decorator that silently swallows errors or
  changes return values can make code hard to reason about — the behaviour is "invisible"
  at the call site. Use them for genuinely orthogonal concerns, not core logic.
- **Debugging through layers:** a stack of decorators adds frames to tracebacks and a
  little call overhead. Fine for I/O-bound work; for a hot inner loop called millions of
  times, the per-call wrapper overhead can matter (measure — performance area).
- **One-off behaviour** used by a single function doesn't need a decorator; just write it
  inline. Decorators pay off through *reuse*.

### Where this shows up

- **Real work — you already use them:** `@property`, `@staticmethod`, `@dataclass`,
  `@app.route(...)` (Flask/FastAPI), `@pytest.fixture`, `@functools.lru_cache` — all
  decorators. Understanding the mechanism demystifies the frameworks you use daily.
- **Real work — experiment/util plumbing:** `@timed` on pipeline stages, `@retry` on
  flaky API/DB calls, a `@log_call` for tracing, `@cache` for expensive pure functions.
- **Real work — registration:** `@register("resnet")` above a model-builder function to
  auto-add it to a registry dict — common in ML frameworks for selecting models/configs
  by name.
- **Pattern mapping (secondary):** memoization decorators (`@lru_cache`) turn an
  exponential recursive solution (Fibonacci, grid paths) into a fast top-down DP with a
  single line — a direct bridge to the dynamic-programming scenarios.
[↑ Back to top](#contents)

---

<a id="1.8"></a>
## 1.8 — "I want a function that takes any number of arguments" → `*args` & `**kwargs`

### The situation

You're writing a small helper that logs a message along with some context values. But
the *number* of context values is different at every call site — sometimes a user id,
sometimes a user id and a request id, sometimes nothing extra:

```python
log_event("login failed")                         # no extra context
log_event("login failed", "user_42")              # one extra value
log_event("login failed", "user_42", "req_9981")  # two extra values
```

If you define the function with fixed parameters, you're stuck:

```python
def log_event(message, ctx1, ctx2):   # demands EXACTLY two context values
    ...
log_event("login failed")             # TypeError: missing 2 required arguments!
```

You could add defaults (`ctx1=None, ctx2=None`), but then you're guessing the maximum
number of extras, and the day someone passes three you're back to editing the
signature. The same pain appears with **named** options: a `connect()` that should
accept `timeout=5`, `retries=3`, `ssl=True` — any subset, in any combination.

### What's really going on

You need a function whose **arity** (the number of arguments it accepts) is *flexible*
rather than fixed. There are two flavours of "extra arguments":

- **Positional** extras — values passed by position, like `"user_42"`, `"req_9981"`.
- **Keyword** extras — values passed by name, like `timeout=5`, `retries=3`.

Python lets a function collect "however many positional extras arrive" into one
parameter, and "however many keyword extras arrive" into another. The two tools are
written **`*args`** (for positional) and **`**kwargs`** (for keyword). The names
`args`/`kwargs` are just convention — it's the `*` and `**` that do the work.

### The move

Use `*args` to gather extra positional values into a **tuple**, and `**kwargs` to
gather extra named values into a **dict**:

```python
def log_event(message, *args, **kwargs):
    # args   = a tuple of the extra positional values, e.g. ("user_42", "req_9981")
    # kwargs = a dict of the extra named values,        e.g. {"level": "error"}
    ...
```

### Why it works

The `*` in a function definition means "soak up all remaining **positional**
arguments into a tuple." So after `message` is filled, anything else passed by
position lands in `args` as a tuple — zero items, one, or fifty, your code doesn't
change. The `**` means "soak up all remaining **keyword** arguments into a dict,"
mapping each name to its value.

The exact same symbols do the **reverse** job when *calling* a function — there they
**unpack** instead of gather: `f(*some_list)` spreads the list out into separate
positional arguments, and `f(**some_dict)` spreads the dict out into separate
`name=value` keyword arguments. Same symbol, two directions: in a `def` it *collects*;
in a call it *spreads*. This symmetry is what lets a wrapper accept anything and pass
it straight through — exactly how the decorators in 1.7 forwarded `(*args, **kwargs)`.

### The code, every line explained

```python
# --- Gathering: *args collects extra positionals into a TUPLE ------------
def log_event(message, *args):
    #                   └ any positional values after `message` land here as a tuple
    print(message, "| context:", args)

log_event("login failed")                    # args = ()            (empty tuple)
log_event("login failed", "user_42")         # args = ("user_42",)
log_event("login failed", "user_42", "req_9981")  # args = ("user_42", "req_9981")

# --- Gathering: **kwargs collects extra keywords into a DICT -------------
def connect(host, **kwargs):
    #             └ any name=value args land here as a dict
    timeout = kwargs.get("timeout", 30)       # read an option with a default
    retries = kwargs.get("retries", 3)        # .get(key, default) -> no KeyError
    print(host, timeout, retries, kwargs)

connect("db.local")                           # kwargs = {}
connect("db.local", timeout=5)                # kwargs = {"timeout": 5}
connect("db.local", timeout=5, ssl=True)      # kwargs = {"timeout": 5, "ssl": True}

# --- Both together (order is fixed): normal, *args, **kwargs -------------
def record(event, *args, **kwargs):
    print(event, args, kwargs)
record("click", 10, 20, user="u1", page="home")
# event="click"; args=(10, 20); kwargs={"user": "u1", "page": "home"}
# The ORDER in the def must be: regular params -> *args -> **kwargs.

# --- Spreading (the reverse): * and ** at the CALL site ------------------
coords = [10, 20]
record("click", *coords)              # *coords spreads the list -> record("click", 10, 20)
opts = {"user": "u1", "page": "home"}
record("click", **opts)               # **opts spreads the dict -> user="u1", page="home"

# --- The classic use: a pass-through wrapper (same as decorators, 1.7) ---
def with_logging(func, *args, **kwargs):
    print(f"calling {func.__name__}")
    return func(*args, **kwargs)       # forward EXACTLY what we received, unchanged
# with_logging works for ANY function regardless of its arguments.
```

### Impact

- **Flexibility:** one signature handles 0, 1, or many extra arguments — no editing
  the function each time a call site needs another value.
- **Clean forwarding:** wrappers, decorators, and thin "adapter" functions can pass
  arguments through to an inner function without knowing or caring what they are.
- **Readable call sites:** `**kwargs` lets callers pass options by name
  (`timeout=5`), which is self-documenting compared to a long list of positional
  values where you must remember what each position means.

### Pros & cons / when NOT to

**Reach for `*args`/`**kwargs` when:** the argument count genuinely varies, or you're
writing a **wrapper/decorator/adapter** that must forward arbitrary arguments to
something else.

**Watch out / when NOT to:**
- **Don't use them to be lazy about a clear signature.** If a function really takes a
  `host`, a `port`, and a `timeout`, *name those parameters explicitly*. A function
  that takes `**kwargs` and silently reads `kwargs["host"]` hides what it needs —
  callers can't tell from the signature, IDEs can't autocomplete, and a typo like
  `hsot=...` passes silently and is ignored instead of erroring. Explicit parameters
  are self-checking documentation.
- **`**kwargs` swallows typos.** Because unknown names are accepted into the dict, a
  misspelled option name won't raise — it just sits unused in `kwargs`. If you accept
  a known set of options, prefer explicit keyword parameters (possibly with defaults)
  so wrong names fail loudly.
- **Force keyword-only where it aids clarity:** a bare `*` in the signature
  (`def f(a, *, verbose=False)`) makes `verbose` **keyword-only** — callers must write
  `verbose=True`, never a mystery positional `True`. Useful for boolean flags.

### Where this shows up

- **Real work — decorators & wrappers:** every reusable decorator (1.7) uses
  `(*args, **kwargs)` to wrap functions of any shape — timing, retry, caching, auth.
- **Real work — framework/config plumbing:** ML APIs like `Model(**config)` spread a
  config dict into named constructor arguments, so a model's hyperparameters can live
  in a JSON/YAML file and be unpacked in one call.
- **Real work — subclass `__init__` forwarding:** `super().__init__(*args, **kwargs)`
  passes a subclass's arguments up to the parent class without re-listing them all.
- **Real work — adapter functions:** wrapping a third-party client call so you can add
  logging/metrics while forwarding whatever arguments the caller supplied.
- **Pattern mapping (secondary):** less an algorithm tool, more a plumbing skill —
  but the call-site `*` unpack is the idiomatic way to spread a computed list of
  arguments into a function (e.g. `max(*row)` or `zip(*matrix)` to transpose, seen in
  1.5).
[↑ Back to top](#contents)

---

<a id="1.9"></a>
## 1.9 — "Two values look equal but my `if` does the wrong thing" → `is` vs `==`

### The situation

You're checking whether a function returned the special "no result" marker `None`, and
you write it with `==`:

```python
result = lookup(user_id)              # returns a value, or None if not found
if result == None:                    # looks reasonable...
    handle_missing()
```

It usually works — but it's subtly wrong, and one day it bites. Worse, consider this
real surprise with integers that *look* identical:

```python
a = 1000
b = 1000
print(a == b)                         # True  — the values are equal
print(a is b)                         # False (!) — surprising

x = 256
y = 256
print(x is y)                         # True  — also surprising, given the above
```

Same code shape (`is`), two different answers, purely because of the *number*. If you
ever use `is` to compare values, your program can behave differently for `256` versus
`1000` — a baffling, almost unreproducible bug.

### What's really going on

`==` and `is` answer two **different questions**, and confusing them is the root cause:

- **`==` asks: "are these two values equal?"** — do they *mean* the same thing? It
  calls the object's equality logic (the `__eq__` method, 1.x on dunders). `1000 ==
  1000.0` is `True`; two different lists with the same contents are `==`.
- **`is` asks: "are these the exact same object in memory?"** — not "equal", but
  *identical* — the very same object, at the same memory address. Two separate lists
  with identical contents are **never** `is` each other, because they're two distinct
  objects.

The integer weirdness above comes from an optimisation: CPython (the standard Python
implementation) **pre-creates and reuses** small integers from -5 to 256, so every
`256` in your program is literally the *same* cached object → `is` is `True`. But
`1000` is built fresh each time → two different objects → `is` is `False`. This is an
implementation detail you must **never** rely on — which is exactly why you must not
use `is` to compare values.

### The move

Simple rule:

- Use **`is`** / **`is not`** **only** for the three singletons: `None`, `True`,
  `False` — and in practice almost always for `None`. ("Singleton" = an object the
  language guarantees exists exactly once, so identity *is* a safe test for it.)
- Use **`==`** / **`!=`** for **everything else** — comparing values, contents,
  numbers, strings, lists.

```python
if result is None:                    # correct: identity check against the singleton
    handle_missing()

if count == 1000:                     # correct: value comparison uses ==
    ...
```

### Why it works

`None` is a **singleton**: there is only ever **one** `None` object in the entire
running program, and every `None` you see is that same object. So "is this the same
object as `None`?" (`is None`) is exactly equivalent to "is this `None`?" — and it's
faster (a direct identity check, no `__eq__` call) and safe from a class of bugs:
a custom object could define a misleading `__eq__` that makes `obj == None` return
`True` by accident, but `obj is None` can **never** be fooled, because identity can't
be overridden.

For real values, `==` is what you mean — "equal in value" — and it works correctly
regardless of whether the two objects happen to be cached or freshly built.

### The code, every line explained

```python
# --- None: ALWAYS use is / is not ----------------------------------------
if result is None:        # right: the one-and-only None object
    ...
if result is not None:    # right: "has a real value"
    ...
# Avoid:  if result == None  -> works usually, but calls __eq__ (slower) and can
# be subverted by a weird custom __eq__. Linters flag `== None` for this reason.

# --- Values, numbers, strings, containers: ALWAYS use == -----------------
if name == "admin":       # right: comparing string VALUE
    ...
if a == 1000:             # right: comparing number value (is would be unreliable!)
    ...
if user_list == ["a"]:    # right: compares CONTENTS, element by element
    ...

# --- Why `is` on values is a trap ----------------------------------------
x = 256; y = 256
print(x is y)             # True  (256 is cached and reused)
a = 1000; b = 1000
print(a is b)             # False (1000 built fresh each time -> different objects)
print(a == b)             # True  (== checks value, the answer you actually want)

# --- Two equal-looking lists are NOT the same object ---------------------
p = [1, 2, 3]
q = [1, 2, 3]
print(p == q)             # True  — same contents
print(p is q)             # False — two separate list objects in memory
r = p
print(r is p)             # True  — r is just another NAME for the SAME list object
r.append(4)               # mutating through r...
print(p)                  # [1, 2, 3, 4]  — ...is visible through p (same object!)

# --- True/False: prefer truthiness, but `is` is valid for the singleton --
flag = get_flag()
if flag:                  # BEST: just test truthiness (covered in the truthiness scenario)
    ...
# `if flag is True:` is technically valid but usually unnecessary and can be WRONG if
# flag is a truthy non-bool (e.g. 1, "yes") — `is True` would be False for those.
```

### Impact

- **Correctness:** eliminates the "works for 256, fails for 1000" class of bug and the
  "a clever `__eq__` made `== None` lie" class. `is None` is bulletproof.
- **Speed (minor):** `is` is a pointer comparison — no method call — so `is None` is
  marginally faster than `== None`. Tiny, but free.
- **Readability:** `is None` is the universally recognised idiom; reviewers and
  linters expect it, so following the rule keeps your code unsurprising.

### Pros & cons / when NOT to

- **The rule has essentially no downside** — it's a clarity-and-correctness win with no
  trade-off. `is` for `None`/`True`/`False`; `==` for everything else.
- **Don't use `is` to compare strings**, even though it *sometimes* appears to work.
  Short string literals are often **interned** (cached and reused, like small ints),
  so `"ab" is "ab"` may be `True` — but strings built at runtime
  (`"a" + "b" is "ab"`) can be `False`. Always compare strings with `==`.
- **`is` for identity is legitimate and useful** in its own right — e.g. checking
  "are these two variables pointing at the *same* object?" (as with `r is p` above),
  or sentinel patterns where you create a unique marker object and test identity
  against it. The rule is about not using `is` as a *value* comparison.

### Where this shows up

- **Real work — the None-default pattern (1.4):** `if arg is None: arg = []` — the
  correct, idiomatic way to detect "caller passed nothing" and build a fresh default.
- **Real work — optional return values:** any `lookup`/`find`/`get` that returns
  `None` on "not found" must be checked with `is None` to branch correctly.
- **Real work — sentinel markers:** when `None` is itself a *valid* value, you create
  a unique marker — `_MISSING = object()` — and test `if value is _MISSING:`. Identity
  is the whole point: nothing else can equal that private object.
- **Real work — aliasing bugs:** understanding that `b = a` makes `b` *another name*
  for the same mutable object (not a copy) explains a huge category of "why did
  changing one change the other?" bugs (deep-dive in the copy/deepcopy scenario in the
  memory area).
- **Pattern mapping (secondary):** in linked-list and tree problems, `is`/identity
  matters when detecting whether two pointers reference the same node (e.g. cycle
  detection compares node identity, not value, since values can repeat).
[↑ Back to top](#contents)

---

<a id="1.10"></a>
## 1.10 — "I check everything before I act, and it's still racy" → EAFP vs LBYL

### The situation

You want to read a value out of a config dictionary, convert it to a number, and use
it. Coming from many languages, you *check first* — does the key exist? is it a
number? — before doing the work:

```python
config = {"timeout": "30", "name": "job1"}

# "Look Before You Leap": test every precondition first
if "timeout" in config:                       # does the key exist?
    if config["timeout"].isdigit():           # is it all digits?
        timeout = int(config["timeout"])       # only now convert
    else:
        timeout = 30
else:
    timeout = 30
```

Three levels of nesting to read one value. And it's *still* not fully correct:
`.isdigit()` is `True` for `"30"` but `False` for `"-5"` and `"3.5"`, so valid inputs
slip through to the default. Each new precondition adds another `if`. The code is all
*guarding* and barely any *doing*.

### What's really going on

There are two philosophies for handling "something might go wrong":

- **LBYL — "Look Before You Leap":** check all the preconditions *before* you act
  (`if key in dict`, `if x != 0`, `if file exists`). This is the default instinct from
  C/Java.
- **EAFP — "Easier to Ask Forgiveness than Permission":** just *attempt* the
  operation, and catch the exception if it fails. This is the **Pythonic** style — the
  language is built around exceptions being cheap and normal, not exceptional.

> **Exception** = Python's signal that something went wrong (a `KeyError` for a
> missing dict key, a `ValueError` for a bad conversion, etc.). **`try/except`** lets
> you *attempt* code in the `try` block and *handle* a specific failure in the
> `except` block, instead of checking for it beforehand.

LBYL has two real problems. First, **the checks and the action can drift apart** — you
test `isdigit()` but the actual conversion rule (`int()`) accepts different inputs, so
your guard doesn't match reality. Second, in concurrent or I/O code there's a **race
condition**: the world can change *between* your check and your action — a file you
just confirmed exists gets deleted before you open it. EAFP has no gap: you attempt
and handle the result atomically.

### The move

Attempt the operation inside `try`, and handle the specific failure in `except`:

```python
try:
    timeout = int(config["timeout"])   # attempt: read AND convert in one go
except (KeyError, ValueError):         # KeyError = key missing; ValueError = not a number
    timeout = 30                       # any failure -> fall back to the default
```

For the common "read a dict key with a default" case, the even simpler tool is
`dict.get(key, default)` — but the `try/except` form is the general pattern when the
"action" is more than a lookup.

### Why it works

You let the operation *itself* be the test. `int(config["timeout"])` either succeeds
(the key exists **and** the value converts) or raises a specific exception telling you
exactly which part failed. There's no separate guard to keep in sync with the action,
because the action **is** the check. And because the attempt and the handling are a
single unit, nothing can change in between — closing the race-condition gap.

Catching **specific** exception types (`KeyError`, `ValueError`) — not a bare
`except:` — means you only handle the failures you actually expect, and genuinely
unexpected errors (a bug, a `KeyboardInterrupt`) still propagate loudly instead of
being silently swallowed. (Full treatment in the error-handling area.)

### The code, every line explained

```python
config = {"timeout": "30", "name": "job1"}

# --- LBYL: check-then-act, nested and fragile ----------------------------
if "timeout" in config and config["timeout"].lstrip("-").isdigit():
    timeout = int(config["timeout"])
else:
    timeout = 30
# Still wrong for "3.5"; the guard (.isdigit) doesn't match the action (int()).

# --- EAFP: attempt-then-handle, flat and correct -------------------------
try:
    timeout = int(config["timeout"])   # do the real thing
except (KeyError, ValueError):         # catch exactly the ways it can fail:
    #     │         └ value exists but won't convert to int ("abc", "3.5")
    #     └ key "timeout" not present at all
    timeout = 30                       # one fallback handles both cases
# The conversion rule and the validity test are now THE SAME THING -> no drift.

# --- The race condition LBYL can't fix -----------------------------------
import os
# LBYL (buggy under concurrency):
if os.path.exists(path):               # checked: file is here...
    f = open(path)                     # ...but it may have been DELETED in between!
                                       # -> FileNotFoundError despite the check
# EAFP (correct): no gap between check and use
try:
    f = open(path)                     # just try to open it
except FileNotFoundError:
    f = create_default(path)           # handle the "not there" case atomically

# --- The everyday shortcut for dict reads: .get() ------------------------
name = config.get("name", "unnamed")  # returns config["name"], or "unnamed" if absent
# .get is LBYL-free sugar for the most common case; reach for it before try/except
# when the only failure is "key missing".

# --- EAFP shines with "duck typing" --------------------------------------
def total_length(x):
    try:
        return len(x)                  # works for anything that HAS a length...
    except TypeError:                  # ...and cleanly handles things that don't
        return 0
# We didn't check "is x a list or str or dict?" — we just used it and handled the
# case where it doesn't support len(). "If it quacks like a duck, treat it as one."
```

### Impact

- **Correctness:** the action is its own validity test, so guards can't drift from
  reality, and the check-then-act race condition disappears.
- **Flatter code:** one `try/except` replaces a pyramid of nested `if`s — fewer
  branches to read and fewer to get wrong.
- **Performance (the happy path is free):** in Python, *setting up* a `try` is nearly
  free; you only pay a cost when an exception actually fires. So when failures are
  rare (the usual case), EAFP is as fast or faster than running an explicit check
  every single time.

### Pros & cons / when NOT to

**Reach for EAFP when:** the operation itself naturally raises a clear exception
(dict/attribute access, type conversion, file/network I/O), or there's any
check-then-act race (files, shared state, external services).

**Prefer LBYL / a guard when:**
- **The check is cheap and the failure is genuinely expected and frequent.** If half
  your inputs are missing the key, a `try/except` firing constantly is noisier (and
  slower) than `config.get(...)` or an `if`. EAFP's "free" assumption holds only when
  exceptions are *rare*.
- **The operation has side effects that can't be undone** before it fails partway. If
  attempting it does irreversible damage (charges a card, then errors), you must
  validate *first* — you can't "ask forgiveness" after money moved. (Connects to
  idempotency/transactions in the robustness area.)
- **You'd catch too broad a net.** If the only clean way to handle it is a bare
  `except:` that hides real bugs, a targeted `if` check is clearer.

The balance: EAFP is the Python default, but reach for `.get()`/a guard when the
"failure" is a normal, frequent, side-effect-free branch.

### Where this shows up

- **Real work — config & input parsing:** reading optional settings and converting
  types, with sane fallbacks — exactly the `int(config[...])` example.
- **Real work — file & network I/O:** open/read/request inside `try`, handle
  `FileNotFoundError` / connection errors — the race-free way to touch the outside
  world (ties to the timeouts/retries scenarios in the APIs area).
- **Real work — optional fields in records:** pulling fields from messy JSON/API
  responses where a key may be absent — `try/except KeyError` or `.get()` rather than
  pre-checking every level.
- **Real work — duck typing in generic code:** utility functions that accept "anything
  list-like" attempt the operation and handle the type that doesn't support it, rather
  than enumerating allowed types.
- **Pattern mapping (secondary):** less an algorithm tool; but the principle "let the
  operation report its own failure" underlies clean recursion base cases (e.g. catch
  the empty/edge case via the natural failure rather than pre-checking every call).
[↑ Back to top](#contents)

---

<a id="1.11"></a>
## 1.11 — "I'm gluing strings together with + and it's a mess" → f-strings

### The situation

You want to build a log line reporting a training result — a message that mixes fixed
text with variable values (an epoch number, an accuracy, a learning rate):

```python
epoch = 3
accuracy = 0.9166666
lr = 0.001

# Concatenation with + : you must convert every non-string by hand
msg = "epoch " + str(epoch) + ": acc=" + str(accuracy) + " lr=" + str(lr)
# -> "epoch 3: acc=0.9166666 lr=0.001"
```

Three problems jump out. You must wrap every number in `str(...)` (forget one and you
get `TypeError: can only concatenate str to str`). The quotes-plus-spaces dance
(`" lr="`) is fiddly and easy to get wrong (missing space → `acc=0.9lr=0.001`). And
the accuracy prints as an ugly `0.9166666` when you wanted `91.67%`.

### What's really going on

You're doing **string interpolation** — inserting values into a template of text — but
with the clumsiest possible tool (`+`). Interpolation is so common that Python has
purpose-built syntax for it: the **f-string** ("formatted string literal"), introduced
in Python 3.6.

An f-string lets you embed the *expression itself* directly inside the string, in
`{curly braces}`, and Python evaluates it and inserts its value — converting to text
automatically. It also supports a **format specification** after a colon
(`{value:spec}`) that controls *how* the value is rendered: decimal places, padding,
percentage, thousands separators, and so on. So the "make it readable" problem
(`91.67%`) is solved in the same place.

### The move

Put an `f` before the opening quote and drop expressions in `{braces}`:

```python
msg = f"epoch {epoch}: acc={accuracy:.2%} lr={lr}"
# -> "epoch 3: acc=91.67% lr=0.001"
```

No `str()` calls, no `+`, no quote juggling — and `:.2%` formats the accuracy as a
percentage with two decimals in the same breath.

### Why it works

The `f` prefix tells Python: "this is a template — evaluate anything in `{}` and
insert its text form." Each `{...}` is a real expression evaluated in the current
scope, so you can put variables, arithmetic, function calls, or attribute access
inside. After an optional `:`, the **format spec** is a mini-language telling Python
how to render that value (`.2f` = 2 decimal places, `%` = as a percentage, `,` =
thousands separators, `>10` = right-align in 10 columns, etc.). Conversion to string
happens automatically, so numbers, `None`, lists — anything — drop in without manual
`str()`.

### The code, every line explained

```python
epoch, accuracy, lr = 3, 0.9166666, 0.001

# --- Basic interpolation: {expr} is evaluated and inserted ---------------
msg = f"epoch {epoch}: acc={accuracy} lr={lr}"
# -> "epoch 3: acc=0.9166666 lr=0.001"   (values inserted, but not yet pretty)

# --- Format specs after a colon control HOW it's rendered ----------------
f"{accuracy:.2f}"        # "0.92"     -> .2f = fixed-point, 2 decimal places
f"{accuracy:.2%}"        # "91.67%"   -> % multiplies by 100 and adds the % sign
f"{1234567:,}"           # "1,234,567"-> , inserts thousands separators
f"{lr:.0e}"              # "1e-03"    -> scientific notation
f"{epoch:03d}"           # "003"      -> d = integer, 0-padded to width 3
f"{'cat':>8}"            # "     cat" -> right-align in 8 columns (< left, ^ centre)

# --- Any expression works inside the braces, not just names --------------
f"total: {price * qty}"          # arithmetic
f"name: {user.name}"             # attribute access
f"first: {items[0]}"             # indexing
f"upper: {name.upper()}"         # method call

# --- The = debugging shortcut (Python 3.8+): prints name AND value -------
f"{accuracy=:.2f}"       # "accuracy=0.92"  -> great for quick debug logging
# The =} echoes the expression text before its value; saves typing the label.

# --- Multi-line f-strings for readable templates -------------------------
report = (
    f"Run summary\n"
    f"  epoch:    {epoch}\n"
    f"  accuracy: {accuracy:.2%}\n"
    f"  lr:       {lr:.0e}\n"
)

# --- Watch the brace: to print a LITERAL { } double it --------------------
f"{{not a placeholder}}"  # -> "{not a placeholder}"  (doubled braces escape)
```

### Impact

- **Readability:** the template reads like the final output, with values shown exactly
  where they land — far clearer than `+`-chains or positional `%`/`.format()`.
- **Fewer bugs:** no manual `str()` (so no `TypeError`), no mis-placed spaces or
  quotes, and formatting lives next to the value it formats.
- **Speed:** f-strings are the **fastest** formatting method in Python — they compile
  to direct value insertion, beating `%`-formatting and `str.format()` and vastly
  beating `+`-concatenation in a loop (the latter also covered in the performance area
  on `str.join`).

### Pros & cons / when NOT to

**Reach for f-strings when:** you build any string from a mix of text and values —
logs, messages, file paths, SQL/prompt templates you assemble yourself, report lines.
They are the default in modern Python (3.6+).

**Watch out / when NOT to:**
- **Logging:** prefer `logger.info("processed %s rows", n)` (the `%s` lazy form) over
  `logger.info(f"processed {n} rows")`. With the lazy form, the string is only built
  **if** that log level is actually enabled — an f-string is always built, even when
  the message would be discarded. Minor for one line, real in a hot loop. (See the
  logging scenario.)
- **SQL queries and shell commands:** **never** f-string user-supplied values directly
  into SQL or a shell command — that's how SQL injection and command injection happen.
  Use parameterised queries (`cursor.execute("... WHERE id=%s", (uid,))`) and argument
  lists for subprocess. f-strings build *text*; they do not *escape* anything.
- **Translatable/user-facing text** that must support multiple languages usually needs
  a templating/i18n system, not inline f-strings.
- **The expression inside `{}` should stay simple.** A long, nested expression in a
  brace hurts readability — compute it into a variable first, then interpolate.

### Where this shows up

- **Real work — logging & progress:** `f"epoch {e}: loss {loss:.4f}"` is the everyday
  training/ETL progress line; `:.4f`-style specs keep numeric logs aligned and
  readable.
- **Real work — building paths & filenames:** `f"checkpoints/model_{epoch:03d}.pt"`
  to generate zero-padded, sortable artefact names.
- **Real work — assembling prompts/templates:** composing an LLM prompt or a config
  string from variables — with the SQL/injection caveat above when values are
  untrusted.
- **Real work — quick debugging:** `print(f"{x=}, {y=}")` to dump several variables
  with their names in one line.
- **Pattern mapping (secondary):** not an algorithm tool; but clean output formatting
  matters when a problem requires returning results as formatted strings (e.g.
  "format the time as HH:MM:SS", zero-padding with `{n:02d}`).
[↑ Back to top](#contents)

---

<a id="1.12"></a>
## 1.12 — "I keep writing fiddly loops to batch, chain, or group" → itertools

### The situation

Three loop-writing chores keep coming up while preparing data, and each one you write
by hand with index arithmetic and temporary lists.

**Chore 1 — send records to an API in batches of 100** (most APIs reject "one row at a
time" as too slow and "all 50,000 at once" as too big):

```python
records = [...]                          # say 50,000 record dicts
batch = []                               # temporary accumulator
for r in records:
    batch.append(r)
    if len(batch) == 100:                # full batch -> send it
        send(batch)
        batch = []                       # reset for the next batch
if batch:                                # don't forget the leftover partial batch!
    send(batch)
```

**Chore 2 — treat several files as one continuous stream** (e.g. logs split across
`jan.log`, `feb.log`, `mar.log`) without first merging them into one giant list.

**Chore 3 — group already-sorted rows by a key** (e.g. sales rows sorted by region,
and you want per-region blocks).

Each is doable by hand, but the batching code above is exactly the kind of thing with
an easy off-by-one (forget the trailing `if batch:` and you silently drop the last
partial batch — a real, common bug).

### What's really going on

These are all **standard iteration patterns** — batching, chaining, grouping — and the
standard library module **`itertools`** provides battle-tested, memory-efficient tools
for them. "Battle-tested" matters here: the trailing-partial-batch bug you can
introduce by hand is already handled correctly inside the library.

The deeper point: `itertools` tools are **lazy iterators** (like generators, 1.2) —
they produce items on demand rather than building intermediate lists, so they work on
huge or streaming data with flat memory. You stop writing the *mechanics* of iteration
and instead *name* the pattern you want.

### The move

Reach for the matching `itertools` tool (plus `batched`, which lives in `itertools`
from Python 3.12):

- **batching** → `itertools.batched(iterable, n)`
- **chaining** several iterables into one → `itertools.chain(a, b, c)`
- **grouping** consecutive equal-key items → `itertools.groupby(iterable, key=...)`

```python
from itertools import batched, chain, groupby

for batch in batched(records, 100):      # yields tuples of up to 100 items
    send(batch)                          # trailing partial batch handled for you
```

### Why it works

Each tool encapsulates the bookkeeping you'd otherwise hand-write. `batched` keeps an
internal counter and yields a chunk every `n` items, automatically yielding the final
short chunk when the source runs out — so the "forgot the leftover" bug cannot happen.
`chain` holds a list of iterables and steps through the first to exhaustion, then the
next, presenting them as one continuous stream without copying anything. `groupby`
walks a sequence and starts a new group every time the **key changes from the previous
item** — which is why the input must be *sorted by that key* first (otherwise the same
key appears in multiple non-adjacent groups).

All three are lazy, so they add essentially no memory overhead regardless of input
size.

### The code, every line explained

```python
from itertools import batched, chain, groupby

# --- batched: fixed-size chunks, partial last chunk handled --------------
records = list(range(250))               # pretend: 250 records
for batch in batched(records, 100):      # batched(iterable, n) -> tuples of size n
    print(len(batch))                    # 100, then 100, then 50 (the leftover!)
    send(batch)
# No manual accumulator, no `if batch:` at the end. (Python 3.12+; before that,
# use the well-known recipe or more-itertools.chunked.)

# --- chain: glue iterables into one continuous stream --------------------
jan = open("jan.log"); feb = open("feb.log"); mar = open("mar.log")
for line in chain(jan, feb, mar):        # iterate jan fully, then feb, then mar
    process(line)                        # as ONE stream; no big merged list built
# chain.from_iterable(list_of_iterables) does the same when you have them in a list:
all_rows = chain.from_iterable([file1_rows, file2_rows, file3_rows])

# --- groupby: collapse consecutive equal-key runs into groups ------------
sales = [                                # NOTE: already sorted by region!
    {"region": "north", "amt": 10},
    {"region": "north", "amt": 15},
    {"region": "south", "amt": 7},
]
key = lambda r: r["region"]              # the grouping key (1.5 covered lambda)
for region, group in groupby(sales, key=key):
    #   │       └ a lazy iterator over the rows in THIS run of equal keys
    #   └ the key value shared by the run
    rows = list(group)                   # materialise this group's rows to use twice
    print(region, sum(r["amt"] for r in rows))   # north 25 / south 7

# --- WHY groupby needs sorted input (the classic gotcha) -----------------
unsorted = ["a", "b", "a"]               # 'a' appears in two separate runs
[(k, list(g)) for k, g in groupby(unsorted)]
# -> [('a', ['a']), ('b', ['b']), ('a', ['a'])]  -- THREE groups, two of them 'a'!
# Fix: sort first -> sorted(unsorted) gives ['a','a','b'] -> two clean groups.
```

### Impact

- **Correctness:** the off-by-one / dropped-final-batch class of bug disappears —
  the library handles edge cases you'd otherwise re-derive each time.
- **Memory:** all lazy — batching 50 million records or chaining ten huge files stays
  flat in memory, never building a combined list.
- **Clarity:** `batched(records, 100)` states intent in one phrase versus a six-line
  accumulator loop a reader must decode.

### Pros & cons / when NOT to

**Reach for itertools when:** you're batching for APIs/DB writes, concatenating
multiple sources, or grouping sorted data — the everyday "shape a stream" chores.

**Watch out / when NOT to:**
- **`groupby` requires the data sorted by the key** — its single most common bug. If
  it isn't sorted, either `sorted(...)` it first (O(n log n), needs the data in
  memory) or use `defaultdict(list)` to group *unsorted* data in one pass (covered in
  the data-wrangling area). Use `groupby` when data is *already* sorted (e.g. straight
  from a sorted DB query or a sorted file) so you avoid re-sorting.
- **`batched` is Python 3.12+.** On older versions use `more_itertools.chunked` or the
  documented grouper recipe — don't silently assume it's available.
- **The group iterator from `groupby` is consumed lazily and shares the underlying
  cursor** — if you advance to the next group without materialising the current one
  (`list(group)`), the previous group's items are lost. Materialise each group you
  need to use more than once.
- **Don't over-reach:** for a simple "do X to each item" a plain loop or comprehension
  (1.1) is clearer than forcing an itertools tool.

### Where this shows up

- **Real work — batched API/DB writes:** sending embeddings or rows in chunks of N to
  respect payload limits and rate limits (ties to batching in the APIs area).
- **Real work — multi-file/multi-shard ingestion:** `chain` over a month's worth of
  daily log/data files processed as a single stream in an ETL job.
- **Real work — run-length summarisation:** `groupby` over time- or category-sorted
  rows to produce per-day or per-category aggregates without pulling everything into a
  DataFrame.
- **Pattern mapping (secondary):** `groupby`-style "collapse consecutive equal
  elements" is exactly the run-length-encoding pattern (e.g. "string compression"
  problems); `chain` mirrors merging multiple sequences before a single pass.
[↑ Back to top](#contents)

---

<a id="1.13"></a>
## 1.13 — "The same expensive call runs again with the same inputs" → functools

### The situation

You have a function that is **pure** (same inputs always give the same output) but
**expensive** — say it calls a slow API or does heavy computation to look up the
geographic region for a customer's postcode:

```python
def region_for(postcode):                # slow: hits an external lookup service
    return geo_api.lookup(postcode)      # ~200 ms each call

for order in orders:                     # 100,000 orders, but only ~500 unique postcodes
    r = region_for(order.postcode)       # re-calls the API even for repeats!
    ...
```

Most of those 100,000 calls are **repeats** — the same postcode appears thousands of
times — yet you pay the 200 ms every single time. You also have two related smaller
annoyances: you keep writing `lambda x: round(x, 2)` style wrappers to "pre-fill" an
argument, and you occasionally need to combine a whole list down to one value with a
custom rule.

### What's really going on

Three distinct everyday needs, all served by the standard-library module
**`functools`** (tools that operate *on functions*):

- **Caching repeated calls** — remember past results so identical inputs return
  instantly. This is **memoization** ("memo" = a remembered note: store the answer the
  first time, look it up thereafter).
- **Pre-filling arguments** — make a new function from an existing one with some
  arguments already fixed (a **partial application**).
- **Folding a sequence to one value** — repeatedly combine elements left-to-right with
  a function (a **reduce/fold**).

The realisation for the main problem: a pure function's output depends *only* on its
inputs, so once you've computed `region_for("12345")` you never need to compute it
again — you can trade a little memory to store the answer and skip the 200 ms forever.

### The move

- **memoization** → put `@functools.lru_cache` (or `@cache`) above the function.
- **pre-filling** → `functools.partial(func, fixed_arg)`.
- **folding** → `functools.reduce(func, iterable, start)`.

```python
from functools import lru_cache

@lru_cache(maxsize=None)                 # remember every distinct input's result
def region_for(postcode):
    return geo_api.lookup(postcode)      # the slow call now runs ONCE per postcode
```

### Why it works

`lru_cache` ("Least Recently Used cache") wraps your function in a hidden dictionary
that maps **the arguments** to **the result**. On each call it builds a key from the
arguments; if that key is already in the dict it returns the stored result instantly
(no function body runs); otherwise it runs the body once, stores the result, and
returns it. "LRU" means if you set a size limit, it evicts the least-recently-used
entries when full — bounding memory. This is a **decorator** (1.7) — it transparently
wraps the function, so call sites don't change at all.

`partial` builds a new function object that remembers some arguments and forwards the
rest — cleaner and faster than a `lambda` wrapper, and it carries the original
function's metadata. `reduce` applies a two-argument function cumulatively: it takes
the running result and the next item, repeatedly, collapsing the sequence to a single
value.

### The code, every line explained

```python
from functools import lru_cache, cache, partial, reduce

# --- lru_cache: memoize a pure, expensive function -----------------------
@lru_cache(maxsize=None)                 # maxsize=None -> unbounded (cache everything)
def region_for(postcode):
    return geo_api.lookup(postcode)      # body runs once per distinct postcode
# 2nd+ call with a seen postcode returns the stored answer with ZERO API calls.
region_for.cache_info()                  # -> hits, misses, size: proof it's working
region_for.cache_clear()                 # wipe it (e.g. if underlying data changed)

# @cache (Python 3.9+) is just @lru_cache(maxsize=None) with a shorter name:
@cache
def fib(n):                              # classic: memoization turns exponential
    return n if n < 2 else fib(n-1) + fib(n-2)   # recursion into linear time

# --- partial: pre-fill arguments to make a specialised function ----------
round2 = partial(round, ndigits=2)       # round() with ndigits fixed at 2
round2(3.14159)                          # -> 3.14   (same as round(3.14159, ndigits=2))
# Useful where an API wants a one-argument function:
prices = list(map(round2, raw_prices))   # apply the specialised fn across a list

# A common real use: fix the first argument of a handler
def log(level, message): ...
warn = partial(log, "WARNING")           # warn(msg) == log("WARNING", msg)

# --- reduce: fold a sequence into one value with a custom rule -----------
nums = [3, 5, 2, 8]
total = reduce(lambda acc, x: acc + x, nums, 0)   # 0 ->+3 ->+5 ->+2 ->+8 = 18
#                    │     │            │    └ start value (the initial acc)
#                    │     └ next item from nums
#                    └ acc = the running result so far
# For plain sum this is silly (use sum()); reduce shines for NON-builtin folds, e.g.
# merging a list of dicts, or chaining .union() across many sets:
merged = reduce(lambda a, b: {**a, **b}, list_of_dicts, {})
```

### Impact

- **Speed:** memoization turns "200 ms × 100,000 calls" into "200 ms × 500 unique
  postcodes" — often a 100×+ reduction in wall-clock and external-API load.
- **Cost:** for paid APIs (LLM/geo/etc.), caching repeated calls directly cuts the
  bill — each duplicate is free.
- **Clarity:** `partial` removes throwaway `lambda` wrappers; `@cache` expresses
  "this is memoized" in one line at the definition site.

### Pros & cons / when NOT to

**Reach for `lru_cache` when:** the function is **pure** and inputs **repeat**.
Reach for `partial` to adapt a function's signature; `reduce` for custom folds.

**Watch out / when NOT to:**
- **Only cache pure functions.** If the result depends on time, randomness, files, or
  any external state that can change, caching returns stale answers. `region_for` is
  safe only if postcode→region never changes during the run; if it can, set a TTL
  (covered in the caching scenarios) or don't cache.
- **Arguments must be hashable** (1.1) — `lru_cache` builds its key from them. You
  can't cache a function called with a `list` or `dict` argument (`TypeError`);
  convert to a tuple/frozenset, or redesign.
- **Unbounded caches grow forever.** `maxsize=None` on a function called with millions
  of *distinct* inputs is a memory leak. Set a finite `maxsize` (e.g. 10_000) so LRU
  eviction caps it.
- **`reduce` is often less readable than a plain loop or a built-in.** Python's author
  deliberately moved it out of built-ins. Prefer `sum`/`max`/`min`/`any`/`all` when
  they fit; use `reduce` only for genuinely custom accumulation, and consider a
  clear `for` loop if the lambda gets hairy.
- **Caching on methods** can keep instances alive (the cache holds `self`), causing
  leaks — be cautious memoizing instance methods on long-lived objects.

### Where this shows up

- **Real work — expensive pure lookups:** geo/currency/reference-data lookups, parsing
  the same config repeatedly, or any deterministic transform called in a hot loop.
- **Real work — LLM/embedding cost control:** `@lru_cache` (or a persistent cache) over
  an embedding call so identical text isn't re-embedded and re-billed (ties to the
  embedding-cache scenario in the DL/LLM area).
- **Real work — callbacks & handlers:** `partial` to bind context into a callback the
  framework will call with fewer arguments (common in async/event code).
- **Real work — combining many things:** `reduce` to union many sets, merge many
  config dicts, or compose a list of transforms into one.
- **Pattern mapping (secondary):** `@cache` on a recursive function is the *one-line*
  way to convert an exponential brute-force recursion into top-down dynamic
  programming (Fibonacci, climbing stairs, grid paths) — a direct bridge to the DP
  scenarios in Area 11.
[↑ Back to top](#contents)

---

<a id="1.14"></a>
## 1.14 — "My object prints as gibberish and won't compare or sort" → dunder methods

### The situation

You make a small class to hold a data point and try to use it like you'd use a built-in
value:

```python
class Point:
    def __init__(self, x, y):    # __init__ sets up a new instance (covered in OOP area)
        self.x = x
        self.y = y

p = Point(1, 2)
print(p)                         # <__main__.Point object at 0x10a3f5d90>  -- gibberish!
print(p == Point(1, 2))          # False (!) -- looks equal, but isn't
points = [Point(3, 1), Point(1, 2)]
points.sort()                    # TypeError: '<' not supported between Point instances
```

Everything that "just works" for an `int` or a `str` — printing readably, comparing
with `==`, sorting, putting in a set, calling `len()` — **fails or misbehaves** on your
object. The `==` returning `False` for two identical points is especially dangerous: it
silently breaks deduplication, test assertions, and "is this in the list?" checks.

### What's really going on

Python's built-in operations (`print`, `==`, `<`, `len`, `in`, `[]`) don't have special
knowledge of your class — they work by calling **special methods** with double
underscores around their names, universally called **"dunder" methods** ("dunder" =
"double underscore", i.e. `__name__`). For example, `print(p)` calls `p.__str__()`,
`a == b` calls `a.__eq__(b)`, `len(x)` calls `x.__len__()`.

If your class doesn't define them, you inherit the defaults from `object`: `__repr__`
prints the unhelpful `<...object at 0x...>`, and `__eq__` falls back to **identity** —
"are these the exact same object in memory?" (the `is` behaviour from 1.9) — which is
why two separate `Point(1,2)` instances compare unequal.

The fix is to **implement the dunder methods** for the behaviours you want, teaching
your object how to participate in Python's standard operations.

### The move

Define the dunder methods for the operations you need:

- readable printing → `__repr__`
- value equality → `__eq__` (plus `__hash__` to stay set/dict-usable)
- ordering/sorting → `__lt__` (or let `@dataclass(order=True)` generate them)
- `len(obj)` → `__len__`; `x in obj` / `obj[i]` → `__contains__` / `__getitem__`

In practice, for plain data-holders you rarely write these by hand — **`@dataclass`
generates `__init__`, `__repr__`, and `__eq__` for you** (full treatment in the design
area). But you must know the dunders to understand what it generates and to customise.

### Why it works

When you write `a == b`, Python literally calls `a.__eq__(b)`. By defining `__eq__` to
compare the *contents* (`self.x == other.x and self.y == other.y`), you make `==` mean
"same value" instead of "same object". Likewise `print(p)` calls `__repr__` to get the
text to show, and `sorted(points)` calls `__lt__` ("less than") on pairs to order them.
You're not overriding magic — you're filling in the methods the built-ins were always
going to call.

### The code, every line explained

```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):                  # called by print() and the REPL
        return f"Point(x={self.x}, y={self.y})"
        # CONVENTION: __repr__ should look like valid code that recreates the object.
        # (There's also __str__ for "pretty" user-facing text; if you define only
        #  __repr__, Python uses it for both — so __repr__ alone is the 80% win.)

    def __eq__(self, other):             # called by ==
        if not isinstance(other, Point): # guard: only compare Point to Point
            return NotImplemented        # return NotImplemented (not False) so Python
                                         # can try the other operand's __eq__ / fall back
        return (self.x, self.y) == (other.x, other.y)   # compare by VALUE (tuple compare)

    def __hash__(self):                  # REQUIRED if you define __eq__ AND want the
        return hash((self.x, self.y))    # object usable in sets/dict keys. Equal objects
                                         # MUST have equal hashes -> hash the same fields.

    def __lt__(self, other):             # called by < , and thus by sorted()/min()/max()
        return (self.x, self.y) < (other.x, other.y)   # sort by x, then y

p = Point(1, 2)
print(p)                                 # Point(x=1, y=2)   <- readable now
print(p == Point(1, 2))                  # True              <- value equality
print(sorted([Point(3, 1), Point(1, 2)]))# [Point(x=1, y=2), Point(x=3, y=1)]
seen = {Point(1, 2)}                      # usable in a set because __hash__ is defined
print(Point(1, 2) in seen)               # True

# --- The shortcut you'll actually use most of the time -------------------
from dataclasses import dataclass

@dataclass(order=True)                    # auto-generates __init__, __repr__, __eq__,
class Point:                              # AND ordering dunders (__lt__ etc.) because
    x: int                                # order=True. Fields compared top-to-bottom.
    y: int
# This single decorator replaces all the boilerplate above. You only hand-write
# dunders when you need behaviour @dataclass doesn't give you.

# --- A container-like object: __len__ and __getitem__ --------------------
class Dataset:
    def __init__(self, rows):
        self._rows = rows
    def __len__(self):                    # makes len(dataset) work
        return len(self._rows)
    def __getitem__(self, i):             # makes dataset[i] AND iteration work
        return self._rows[i]
ds = Dataset([10, 20, 30])
print(len(ds))                            # 3
print(ds[1])                              # 20
for row in ds:                            # __getitem__ also enables for-loops
    ...
```

### Impact

- **Correctness:** value `==` fixes silent failures in dedup, `in` checks, and test
  assertions (`assert result == Point(1, 2)` now works).
- **Interoperability:** your object slots into the whole language — `sorted`, `set`,
  `dict` keys, `max`, `len`, `for` — instead of being a second-class citizen.
- **Debuggability:** a good `__repr__` turns log lines and tracebacks from
  `<object at 0x...>` into `Point(x=1, y=2)`, saving real debugging time.

### Pros & cons / when NOT to

**Reach for dunders when:** you build a class that should behave like a value
(comparable, printable, hashable) or like a container (`len`, indexing, iteration).

**Watch out / when NOT to:**
- **`__eq__` without `__hash__` makes the object unhashable.** Defining `__eq__` sets
  `__hash__` to `None` automatically (Python's safety rule), so the object can no longer
  go in a set or be a dict key until you also define `__hash__`. `@dataclass(eq=True,
  frozen=True)` handles this pair correctly for you.
- **Equal objects must hash equal**, and you should only hash **immutable** fields. If
  you hash a field then mutate it, the object gets "lost" in its set/dict (it's filed
  under the old hash). Hash only fields that never change — or make the class `frozen`.
- **Don't go dunder-crazy.** Overloading operators like `+` (`__add__`) or `[]` on
  objects where it isn't intuitive makes code cryptic. Implement only the behaviours a
  reader would naturally expect (a "Money" type adding with `+` is fine; a "User"
  object supporting `user1 + user2` is confusing).
- **Prefer `@dataclass`** for plain data holders — hand-written dunders are for when you
  need custom logic the dataclass can't express.

### Where this shows up

- **Real work — value objects & configs:** small typed records (a `BoundingBox`, a
  `ModelConfig`, a `Money`) that you compare, sort, log, and dedup — `@dataclass` plus
  the odd custom dunder.
- **Real work — test assertions:** `assert got == Expected(...)` only works when `__eq__`
  compares by value; pytest's readable failure diffs rely on `__repr__`.
- **Real work — custom datasets/containers:** ML `Dataset` classes implement `__len__`
  and `__getitem__` so the framework's `DataLoader` can index and iterate them — a
  direct, daily example.
- **Real work — sorting domain objects:** `__lt__`/`@dataclass(order=True)` to sort
  records by a natural ordering, or to push them into a heap (1.x / Area 3 heapq).
- **Pattern mapping (secondary):** defining `__lt__` lets your objects go into `heapq`
  and `sorted` directly — useful in graph/scheduling problems where you order custom
  node/task objects by priority.
[↑ Back to top](#contents)

---

<a id="1.15"></a>
## 1.15 — "I need to sort by something other than the default order" → sorting with `key`

### The situation

You have a list of order records (dicts) and you want them sorted — but not by their
natural order. You want highest-value orders first, and for ties, the most recent:

```python
orders = [
    {"id": "A", "amount": 250.0, "ts": "2026-01-03"},
    {"id": "B", "amount": 900.0, "ts": "2026-01-01"},
    {"id": "C", "amount": 250.0, "ts": "2026-01-05"},
]
```

Coming from other languages you might reach for writing a comparison function ("given
two orders, which comes first?") or sorting repeatedly. Plain `sorted(orders)` doesn't
even work — it raises `TypeError: '<' not supported between instances of 'dict'`,
because dicts have no natural order. So how do you say "sort by amount descending, then
by timestamp descending"?

### What's really going on

Python's sorting (`sorted(...)` and `list.sort()`) doesn't need you to write a
comparison function. Instead it asks: *"for each item, what value should I sort it
by?"* — and you answer with a **key function**: a function that takes one item and
returns the value to order it on. Python calls your key function **once per item**,
then sorts by those computed values.

This is the **decorate-sort-undecorate** idea, built in: you tell Python the *sort key*
for each element rather than how to compare pairs. It's simpler (one function, not
pairwise logic), faster (key computed once per item, not on every comparison), and
composes cleanly for multi-level sorts.

### The move

Pass a **`key=`** function to `sorted()` (or `.sort()`):

```python
top = sorted(orders, key=lambda o: o["amount"], reverse=True)
```

For multi-level sorting, return a **tuple** of the keys in priority order — Python
compares tuples element by element:

```python
top = sorted(orders, key=lambda o: (o["amount"], o["ts"]), reverse=True)
```

### Why it works

`key` is a function called once on each element to produce its **sort value**. Python
then orders the elements by those values using its normal comparison rules. Returning a
**tuple** works because tuples compare **lexicographically** — it compares the first
elements; only if they're equal does it compare the second, and so on. So
`(amount, ts)` means "sort by amount; break ties by ts" — exactly the multi-level sort
you wanted, with no custom comparator.

Python's sort is also **stable**: items that compare equal keep their original relative
order. That's what lets you do multi-level sorts as *separate* passes when directions
differ (sort by the secondary key first, then the primary), which we'll use below.

### The code, every line explained

```python
orders = [
    {"id": "A", "amount": 250.0, "ts": "2026-01-03"},
    {"id": "B", "amount": 900.0, "ts": "2026-01-01"},
    {"id": "C", "amount": 250.0, "ts": "2026-01-05"},
]

# --- Sort by one field --------------------------------------------------
by_amount = sorted(orders, key=lambda o: o["amount"])
#                          └ key fn: for each order o, sort by its "amount"
# ascending by default: B is last? no -> [A(250), C(250), B(900)] (A,C keep input order)

by_amount_desc = sorted(orders, key=lambda o: o["amount"], reverse=True)
# reverse=True flips to descending: [B(900), A(250), C(250)]

# --- Multi-level: tuple key, SAME direction for all levels --------------
top = sorted(orders, key=lambda o: (o["amount"], o["ts"]), reverse=True)
# compares amount first; ties broken by ts. Both descending.
# -> [B(900), C(250, ts 01-05), A(250, ts 01-03)]   (C before A: later ts wins)

# --- Multi-level with DIFFERENT directions: two stable passes -----------
# Want: amount DESC, but ts ASC for ties. Can't express opposite dirs in one tuple
# for non-numeric keys, so sort by the SECONDARY key first, then the primary:
tmp = sorted(orders, key=lambda o: o["ts"])               # secondary: ts ascending
result = sorted(tmp, key=lambda o: o["amount"], reverse=True)  # primary: amount desc
# stability preserves the ts order within equal-amount groups.
# (Numeric secondary key trick: negate it -> key=lambda o: (-o["amount"], o["ts"]).)

# --- operator.itemgetter / attrgetter: faster, cleaner than lambda ------
from operator import itemgetter, attrgetter
by_amount = sorted(orders, key=itemgetter("amount"))      # dict key access, no lambda
# for objects with attributes: sorted(points, key=attrgetter("x"))

# --- Same key= works on min/max too -------------------------------------
biggest = max(orders, key=itemgetter("amount"))           # the single largest order
```

### Impact

- **Expressiveness:** any ordering — by computed value, by multiple fields, mixed
  directions — without writing comparison logic.
- **Speed:** the key is computed once per item (n calls), versus a comparison function
  called O(n log n) times. For an expensive key this is a real saving.
- **Clarity:** `key=itemgetter("amount")` reads as "sort by amount"; a pairwise
  comparator reads as a puzzle.

### Pros & cons / when NOT to

**Reach for `key=` when:** you sort by anything other than the elements' natural order
— a field, a computed property, length, absolute value, or several keys at once.

**Watch out / when NOT to:**
- **`sorted()` returns a new list; `.sort()` sorts in place** and returns `None`. Don't
  write `orders = orders.sort()` — that sets `orders` to `None`. Use `.sort()` only for
  its side effect, `sorted()` when you want a result.
- **Opposite directions on non-numeric keys** can't be done in a single tuple key (you
  can't "reverse" just one element). Use the two-pass stable-sort approach, or negate
  numeric keys (`-x`).
- **The key function runs on every element** — if it's expensive (e.g. a DB call),
  precompute the keys or cache them; don't hide slow work in a key.
- **For huge data where you only want the top few**, don't full-sort — use `heapq.
  nlargest(n, data, key=...)` (Area 3), which is O(n log k) instead of O(n log n).

### Where this shows up

- **Real work — ranking & reporting:** "top N customers by revenue", "slowest requests
  first", "most recent events" — all `key=` sorts, often multi-level.
- **Real work — deterministic output:** sorting records by a stable key before writing,
  so diffs and downstream comparisons are reproducible.
- **Real work — sorting model outputs:** ordering predictions by confidence score
  descending to take the top-k, or candidates by a composite (score, recency) key.
- **Real work — preparing data for `groupby` (1.12):** you must sort by the group key
  first; the same `key=` function feeds both.
- **Pattern mapping (secondary):** custom-key sorting is the first step of countless
  algorithm problems — "merge intervals" (sort by start), "meeting rooms", "largest
  number" (custom string comparator), and any greedy approach that processes items in a
  chosen order.
[↑ Back to top](#contents)

---

<a id="1.16"></a>
## 1.16 — "I'm writing loops and index math to grab parts of a sequence" → slicing

### The situation

You keep needing sub-ranges of lists and strings, and you do it the long way:

```python
filename = "model_2026_01_03.ckpt"

# Want the extension without the dot — count characters by hand:
ext = ""
for i in range(len(filename) - 4, len(filename)):   # last 4 chars... fragile
    ext += filename[i]                               # -> "ckpt"

# Want all rows except the header of a data file:
rows = lines[1:len(lines)]                           # works but verbose

# Want the last element:
last = mylist[len(mylist) - 1]                       # index math, easy to get wrong
```

Index arithmetic with `len(...) - 1`, manual character-by-character loops, off-by-one
risks everywhere. Python has a built-in, far cleaner way to take any contiguous chunk
of a sequence.

### What's really going on

You're extracting a **contiguous sub-sequence** — a "slice." Python supports
**slicing** natively on any sequence (list, string, tuple) with the syntax
`seq[start:stop:step]`, and **negative indices** that count from the end. This replaces
the whole family of "loop over a range of indices and collect" chores with one
expression.

Two rules unlock all of it:

- **Indices point *between* elements, and `stop` is exclusive.** `seq[1:4]` gives
  elements at positions 1, 2, 3 — *not* 4. ("Exclusive" = the stop position is the
  first one *left out*.) This is why `seq[a:b]` has exactly `b - a` elements, and why
  `seq[1:]` (header skipped) plus `seq[:1]` (just the header) perfectly reconstruct the
  whole.
- **Negative indices count from the end:** `-1` is the last element, `-2` the
  second-last. So "the last 4 characters" is just `s[-4:]`, no `len()` needed.

### The move

Use slice syntax `seq[start:stop:step]`, omitting parts you don't need and using
negative indices to count from the end:

```python
ext   = filename[-4:]    # last 4 characters
body  = lines[1:]        # everything except the first row (the header)
last  = mylist[-1]       # the last element
```

### Why it works

`seq[start:stop:step]` returns a **new** sequence containing the elements from `start`
up to (but not including) `stop`, taking every `step`-th one. Each part has a sensible
default: omit `start` → from the beginning; omit `stop` → to the end; omit `step` →
every element. Negative numbers are interpreted as "length + that number", so `-1`
means the last position — letting you address the tail without computing `len()`.
Because `stop` is exclusive and out-of-range bounds are clamped (not errors), slices
are forgiving: `seq[:100]` on a 3-element list just returns all 3.

### The code, every line explained

```python
s = "model_2026_01_03.ckpt"
nums = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# --- start:stop (stop is EXCLUSIVE) -------------------------------------
nums[2:5]      # [2, 3, 4]      positions 2,3,4 — NOT 5
nums[:3]       # [0, 1, 2]      omit start -> from the beginning
nums[7:]       # [7, 8, 9]      omit stop  -> to the end
nums[:]        # [0..9]         a full (shallow) COPY of the list

# --- negative indices: count from the end -------------------------------
nums[-1]       # 9              last element (no len() needed)
nums[-3:]      # [7, 8, 9]      last three
nums[:-1]      # [0..8]         everything EXCEPT the last (drop trailing item)
s[-4:]         # "ckpt"         last 4 chars
s[:-5]         # "model_2026_01_03"   drop the ".ckpt" (5 chars)

# --- step: take every k-th element --------------------------------------
nums[::2]      # [0, 2, 4, 6, 8]   every 2nd element
nums[1::2]     # [1, 3, 5, 7, 9]   every 2nd, starting at 1
nums[::-1]     # [9, 8, ..., 0]    step -1 REVERSES the sequence (idiom!)
s[::-1]        # "tkc...ledom"     same trick reverses a string

# --- the header/body split (clean, no len) ------------------------------
header, body = lines[0], lines[1:]     # first row vs the rest
# (Compare with starred unpacking from 1.6: header, *body = lines — same intent.)

# --- slice ASSIGNMENT: replace a chunk in place (lists only) ------------
nums[1:4] = [100, 200]    # remove positions 1-3, splice in 2 new items
# nums is now [0, 100, 200, 4, 5, 6, 7, 8, 9] — length changed in place

# --- a slice is a COPY: mutating it doesn't touch the original ----------
first_three = nums[:3]    # new list; appending to it won't affect nums
# BUT it's a SHALLOW copy — nested objects are shared (see copy/deepcopy, Area 2).
```

### Impact

- **Clarity & correctness:** `s[-4:]` and `lines[1:]` say exactly what they do and
  remove the `len()-1` arithmetic where off-by-ones hide.
- **Less code:** whole index-loop-and-collect blocks collapse to one expression.
- **Speed:** slicing is implemented in C and builds the result in one shot — faster
  than a Python-level loop appending characters/elements.

### Pros & cons / when NOT to

**Reach for slicing when:** you need a contiguous sub-range, the head/tail, a reversed
copy, or every-k-th element.

**Watch out / when NOT to:**
- **A slice makes a *copy*** (for lists/strings). `big[:]` or `big[1000:2000]` on a
  huge list allocates a new list of that size — fine usually, but in a hot loop or on
  massive data that copy is real memory/time. To *view* without copying large numeric
  data, use NumPy arrays (whose slices are views, not copies — Area 2) or `islice` from
  itertools for lazy slicing of iterators.
- **Slicing only works on sequences** (list, str, tuple, bytes, range). It does **not**
  work on sets or dicts (no order/position) or on general iterators/generators — for
  those use `itertools.islice(gen, start, stop)`.
- **Shallow copy gotcha:** `grid[:]` copies the outer list but the inner lists are
  shared — mutating `grid[:][0]` still changes the original's row. (copy vs deepcopy,
  Area 2.)
- **Over-clever slices hurt readability.** `a[1:-1:2]` packs three ideas into six
  characters — fine once understood, but add a comment when the intent isn't obvious.

### Where this shows up

- **Real work — file/record handling:** dropping a header row (`rows[1:]`), taking the
  last N log lines (`lines[-N:]`), stripping a known suffix/prefix from names.
- **Real work — windows over sequences:** `series[i:i+window]` to take a rolling window
  of a time series for a moving average or a model's input sequence.
- **Real work — train/test splits by position:** `data[:split]` / `data[split:]` for a
  simple chronological split (with the caveat that random splits need shuffling — ML
  area).
- **Real work — reversing & sampling:** `seq[::-1]` to reverse, `seq[::10]` to
  down-sample every 10th row for a quick look at large data.
- **Pattern mapping (secondary):** slicing is everywhere in array/string problems —
  `s[::-1]` for palindrome checks, `arr[:k]`/`arr[k:]` for partitioning, window slices
  in sliding-window problems (Area 11), though in tight algorithm loops index pointers
  often beat copying slices.
[↑ Back to top](#contents)

---

<a id="1.17"></a>
## 1.17 — "My empty-check works until a 0 or empty string shows up" → truthiness

### The situation

You're validating a config value and want to apply a default when the user didn't
provide one. You write what looks obviously correct:

```python
def get_timeout(config):
    timeout = config.get("timeout")      # may be a number, or None if absent
    if not timeout:                      # "if no timeout was given, use default"
        return 30
    return timeout

get_timeout({"timeout": 60})             # 60   ✓
get_timeout({})                          # 30   ✓ (absent -> None -> default)
get_timeout({"timeout": 0})              # 30   ✗ !! user asked for 0, got 30
```

The user explicitly set `timeout: 0` (meaning "no timeout / don't wait"), but your code
silently overrode it with 30. The same trap hits empty strings (`name = "" `treated as
"no name"), empty lists, and `0.0`. The check *looks* like "is it missing?" but it
actually means something subtly different.

### What's really going on

Every Python object has a **truth value** — when you put it in an `if` or use `not`,
Python asks the object "are you truthy or falsy?" This is called **truthiness**. The
rule: a set of values are **falsy** (treated as `False`), and *everything else* is
**truthy**.

The falsy values you'll actually meet:

- `None`
- `False`
- **any zero number:** `0`, `0.0`, `0j`
- **any empty container/sequence:** `""`, `[]`, `{}`, `()`, `set()`
- objects whose `__len__` returns 0 (1.14)

So `if not timeout:` is true for `None` **and** `0` **and** `0.0` — it really means
"is `timeout` falsy?", which lumps together "absent" (`None`) with "explicitly zero"
(`0`). Those are different intentions, and conflating them is the bug.

### The move

**Decide which question you're actually asking**, and write *that*:

- "Is the value **missing**?" → test against `None` explicitly: `if timeout is None:`
- "Is the container **empty**?" → the truthiness check is correct and idiomatic:
  `if not items:`

```python
def get_timeout(config):
    timeout = config.get("timeout")
    if timeout is None:                  # ONLY missing -> default; 0 is kept
        return 30
    return timeout
```

### Why it works

`is None` (1.9) asks the precise question "was no value supplied?" and treats a real
`0` as a real value, because `0 is None` is `False`. You've separated "absent" from
"falsy". When you genuinely mean "empty", the bare truthiness test (`if not items:`) is
both correct and the recognised Pythonic idiom — it catches `[]`, `""`, `{}` in one
clean check, which is *better* than `len(items) == 0`.

The skill is matching the test to the intent: truthiness for "is there anything here?",
`is None` for "was this provided?".

### The code, every line explained

```python
# --- The trap: truthiness when you meant "missing" -----------------------
if not timeout:        # True for None, 0, 0.0 -> wrongly defaults an explicit 0
    timeout = 30

# --- The fix: ask the exact question ------------------------------------
if timeout is None:    # True ONLY for missing; 0 / 0.0 pass through as real values
    timeout = 30

# --- Truthiness IS the right tool for "empty container?" ----------------
items = []
if not items:          # idiomatic + correct: empty list is falsy
    print("nothing to process")
# Prefer this over:  if len(items) == 0:  (works, but wordier and less Pythonic)
if items:              # "if there's at least one item"
    process(items)

# --- The classic None-vs-empty distinction ------------------------------
def first_or_default(rows):
    if rows is None:        # rows weren't fetched at all (e.g. query failed)
        raise ValueError("rows is None — fetch failed")
    if not rows:            # rows fetched fine, but the result was empty []
        return "no data"
    return rows[0]
# Two DIFFERENT conditions that `if not rows:` alone would merge and mishandle.

# --- Falsy quick-reference (each evaluates as False in an if) ------------
for v in [None, False, 0, 0.0, "", [], {}, (), set()]:
    assert not v                        # every one of these is falsy
for v in [1, -1, 0.1, "0", " ", [0], {"a": 1}]:
    assert v                            # truthy! note "0" (non-empty str) and [0]
# GOTCHA: the STRING "0" is truthy (it's a non-empty string), as is "False".
# Parsing "0"/"False" from text needs real conversion, not a truthiness check.

# --- Truthiness + 'or' for a default value (works ONLY when 0/'' aren't valid) --
name = user_input or "anonymous"        # if user_input is "" or None -> "anonymous"
# Handy, BUT it treats "" the same as missing. Fine for names; WRONG for a count
# where 0 is meaningful -> use the explicit `is None` form there.
```

### Impact

- **Correctness:** stops the "valid 0 / empty string silently replaced" class of bug,
  which is common in config parsing, counts, and amounts.
- **Clarity of intent:** `is None` vs `if not x:` documents *which* question the code
  asks, so the next reader (and you, later) isn't guessing.
- **Idiomatic emptiness checks:** `if not items:` is shorter and clearer than
  `len(items) == 0`, and works across all container types.

### Pros & cons / when NOT to

**Use truthiness (`if x:` / `if not x:`) when:** you mean "is this container non-empty?"
or "is this a meaningful/truthy value?" and `0`/`""` are *not* valid inputs you must
preserve.

**Use `is None` / `is not None` when:** you must distinguish "absent" from a legitimate
falsy value (`0`, `0.0`, `""`, `[]`). This is the rule whenever zero/empty are valid
data — counts, amounts, scores, optional flags.

**Watch out:**
- **`x or default` collapses falsy to the default.** Great for "name or anonymous",
  wrong for "retries or 3" when `retries=0` is a real choice. Reach for `x if x is not
  None else default` (the ternary, 1.19) when 0/'' matter.
- **The string `"0"` and `"False"` are truthy.** Never use truthiness to interpret text
  from a file/env var/CSV — `if config["debug"]:` is `True` for the string `"False"`.
  Convert explicitly (Area 3, safe coercion).
- **NumPy/pandas break the simple rule.** `if some_array:` raises *"truth value of an
  array is ambiguous"*, and pandas NA has its own behaviour — use `.any()`/`.all()`/
  `.empty`/`pd.isna()` there, not bare truthiness (Area 3/8).

### Where this shows up

- **Real work — config & argument defaults:** the exact `timeout`/`retries` case —
  distinguishing "user didn't set it" from "user set it to 0".
- **Real work — guarding empty results:** `if not rows: return` early-exits cleanly
  when a query or filter produced nothing, before code that assumes `rows[0]` exists.
- **Real work — parsing flags from text:** remembering `"0"`/`"false"` are truthy is
  what saves you from a feature flag that's always on.
- **Real work — data with valid zeros:** sensor readings, prices, counts where `0` is
  meaningful — the difference between `is None` and truthiness decides whether your
  pipeline drops real data.
- **Pattern mapping (secondary):** the empty-check idiom `if not stack:` /
  `while queue:` is the standard, clean base/termination condition in stack-, queue-,
  and BFS/DFS-based algorithms (Area 11) — checking "is the structure empty?" by
  truthiness.
[↑ Back to top](#contents)

---

<a id="1.18"></a>
## 1.18 — "I compute a value, then immediately test it — in two lines" → the walrus operator

### The situation

You call a function, store the result, then check it. The result variable exists only
to be tested and then used once:

```python
data = fetch_next_page()         # get a page of results
while data:                      # keep going while there's data
    process(data)
    data = fetch_next_page()     # ...and we have to repeat the call here. Ugh.
```

Notice `fetch_next_page()` is written **twice** — once before the loop, once at the
bottom — a duplication that's easy to forget to keep in sync. The same shape appears
with `if`:

```python
match = pattern.search(line)     # compute...
if match:                        # ...test...
    use(match.group())           # ...use. Three lines, `match` lives only for this.
```

### What's really going on

You want to **assign a value and use that value in the same expression** — compute,
test, and capture in one go. Standard `=` assignment is a *statement*, so it can't live
inside an `if`/`while` condition; that's why you're forced to assign on one line and
test on the next (or duplicate the call).

Python 3.8 added the **walrus operator** `:=` (named for its `:=` eyes-and-tusks look),
formally the **assignment expression**. Unlike `=`, it both assigns *and* evaluates to
the assigned value, so you can use it *inside* a condition or comprehension.

### The move

Use `name := expression` inside the condition to assign and test at once:

```python
while data := fetch_next_page():     # assign data, then test its truthiness
    process(data)                    # called ONCE, no duplication
```

### Why it works

`data := fetch_next_page()` runs the call, binds the result to `data`, **and** the
whole expression evaluates to that result — which `while` then tests for truthiness
(1.17). So one line does the assign, the test, and makes `data` available in the body.
The duplicated call vanishes because the single in-condition call serves every
iteration. The variable it binds (`data`, `match`) lives on in the surrounding scope,
exactly as a normal assignment would.

### The code, every line explained

```python
# --- while loop: read until exhausted, no duplicated call ----------------
while data := fetch_next_page():     # assign + test; stops when a falsy page returns
    process(data)
# vs the old two-place version that called fetch_next_page() before AND inside.

# --- reading a file/stream in chunks ------------------------------------
with open("big.bin", "rb") as f:
    while chunk := f.read(8192):     # read 8 KB; f.read returns b"" (falsy) at EOF
        handle(chunk)                # loop ends cleanly when the empty bytes arrive

# --- if: compute, test, and capture for the body in one line ------------
if (match := pattern.search(line)):  # assign match, test it; parens optional in if
    use(match.group())               # match is available here AND below
# Without walrus this is the 3-line compute/test/use shown in the situation.

# --- comprehension: avoid computing an expensive value twice ------------
# WRONG (computes transform(x) twice per item — once to test, once to keep):
out = [transform(x) for x in items if transform(x) is not None]
# RIGHT (compute once, name it, reuse the name):
out = [y for x in items if (y := transform(x)) is not None]
#          │                  └ assign y = transform(x), then test y
#          └ ...and reuse that same y as the kept value. One call per item.

# --- handy in guard checks: bind the thing you just validated -----------
if (n := len(queue)) > 100:          # bind n, compare it...
    log.warning("queue backed up: %d items", n)   # ...and reuse n in the message
```

### Impact

- **No duplicated work or code:** the "call before the loop *and* inside it" pattern
  collapses to one call site, removing a real keep-in-sync bug source.
- **Compute-once in comprehensions:** lets a filtered comprehension avoid calling an
  expensive function twice per element — both a speed win and a correctness win (if the
  function isn't pure).
- **Tighter scope:** the bound name exists right where it's used, instead of a
  throwaway line above.

### Pros & cons / when NOT to

**Reach for the walrus when:** a loop reads-until-empty (`while chunk := ...`), or you
compute a value purely to test-and-then-use it, or a comprehension would otherwise call
the same function twice.

**Watch out / when NOT to:**
- **Don't sacrifice readability to save a line.** If the surrounding expression is
  already busy, a plain `=` on its own line is clearer. The walrus earns its place when
  it *removes duplication*, not merely to be terse.
- **Precedence/parentheses:** `:=` binds loosely, so wrap it when mixing with other
  operators — `while (n := next(it)) is not None:` needs the parens. When unsure,
  parenthesise the walrus expression.
- **Don't confuse `:=` with `=`.** They're different: `=` is a statement (can't go in a
  condition); `:=` is an expression (can't be a bare top-level statement —
  `x := 5` alone is a syntax error; just use `x = 5`).
- **Python 3.8+ only.** Not available on older interpreters.

### Where this shows up

- **Real work — reading streams/pages:** `while chunk := stream.read(n)` for files,
  sockets, and `while page := api.next()` for paginated APIs (ties to pagination in the
  APIs area) — the cleanest exhaust-the-source loop.
- **Real work — regex extraction:** `if (m := re.search(...)):` when scanning log lines
  or parsing fields, using the match immediately.
- **Real work — expensive filters in pipelines:** comprehensions over a dataset where
  the predicate and the kept value share an expensive computation (a model score, a
  parse) — compute once with `:=`.
- **Real work — guard-and-report:** binding a measured quantity (`n := len(...)`,
  `r := response.status_code`) to both branch on it and log it.
- **Pattern mapping (secondary):** common in tight loops for problems that "consume
  until empty" (stack/queue processing) or that test-and-use a computed value each
  iteration, keeping the loop body compact.
[↑ Back to top](#contents)

---

<a id="1.19"></a>
## 1.19 — "Four lines of if/else just to pick one of two values" → conditional expressions

### The situation

You want a variable to take one of two values depending on a condition. You write the
full `if/else` block:

```python
if score >= 0.5:
    label = "positive"
else:
    label = "negative"
```

Four lines, and the variable name `label` is repeated in both branches — which is
exactly where someone later edits one branch and forgets the other. The only thing
that actually varies is the *value*; the assignment is the same both ways.

### What's really going on

This is a **value choice**, not a control-flow branch: you're not doing different
*work* in each case, you're selecting between two *values* for one assignment. Python
has an expression for precisely this — the **conditional expression**, commonly called
the **ternary operator** ("ternary" = takes three operands: the value-if-true, the
condition, the value-if-false):

```python
value_if_true if condition else value_if_false
```

Because it's an **expression** (it evaluates to a value), it can sit directly on the
right of an `=`, inside a function call, or inside a comprehension — places a
multi-line `if` statement cannot go.

### The move

Collapse the two-branch assignment into one conditional expression:

```python
label = "positive" if score >= 0.5 else "negative"
```

Read it left-to-right: *"`label` is 'positive' if score ≥ 0.5, else 'negative'."*

### Why it works

Python evaluates the **condition** first; if it's truthy (1.17), the whole expression
becomes the value before the `if`; otherwise it becomes the value after `else`. The
variable name appears **once**, so the two-branches-out-of-sync edit bug can't happen.
Only the chosen side is evaluated (it **short-circuits**), so the unused branch's
expression never runs — which matters if a branch has a cost or could error.

### The code, every line explained

```python
# --- The everyday value choice ------------------------------------------
label = "positive" if score >= 0.5 else "negative"
#        └ value if true            └cond      └ value if false
# `label` written once; only one side is evaluated.

# --- The safe-default form (pairs with truthiness, 1.17) ----------------
timeout = given if given is not None else 30   # keep an explicit 0; default only on None
# Use THIS (not `given or 30`) when 0/'' are valid values you must preserve.

# --- Inside a function call (no temp variable needed) -------------------
print(f"{count} item" + ("s" if count != 1 else ""))   # naive pluralisation
send(payload, retries=5 if is_critical else 1)          # pick an argument inline

# --- Inside a comprehension: transform each item conditionally ----------
# NOTE: here the if/else goes BEFORE the `for` — it chooses the VALUE.
clipped = [x if x <= 100 else 100 for x in readings]    # cap each reading at 100
#          └────── conditional expression ──────┘ └── the loop ──┘
# Contrast with a FILTER (1.1), where `if` goes AFTER the for and DROPS items:
big_only = [x for x in readings if x > 100]             # keeps only x > 100
# Transform-each (value choice) -> if/else before for.
# Keep-some (filter)            -> if after for. Different jobs!

# --- Chaining is legal but usually a smell ------------------------------
grade = "A" if s >= 90 else "B" if s >= 80 else "C"     # reads okay for a short ladder
# Beyond 2-3 rungs, prefer a dict lookup or a normal if/elif chain for clarity.

# --- When NOT to compress: side effects / different WORK ----------------
# If the branches DO things (not just produce a value), keep a real if statement:
if user.is_admin:
    grant_access(user); log_admin_action(user)     # multiple actions -> statement, not ternary
else:
    deny(user)
```

### Impact

- **Less duplication:** the assigned name appears once, removing the "edited one branch,
  forgot the other" bug.
- **Usable inline:** picks a value right inside a call, f-string, or comprehension —
  no throwaway variable or pre-loop setup.
- **Clarity for simple choices:** a one-line value choice reads as a single thought
  instead of a four-line block the eye must assemble.

### Pros & cons / when NOT to

**Reach for the ternary when:** you're choosing between **two values** for an
assignment, argument, or comprehension element, and each side is a simple expression.

**Watch out / when NOT to:**
- **Branches that *do work*, not just yield a value, belong in an `if` statement.** If
  each side calls functions, logs, or runs several steps, a ternary forces them into
  expressions and hurts readability. Ternary is for *values*, `if` is for *actions*.
- **Don't nest/chain deeply.** One level is clear; `a if p else b if q else c` is the
  practical limit. More rungs → use `if/elif/else` or a `dict` mapping
  (`{"hi": ...}.get(...)`), which is often the cleanest "pick by key" form.
- **Mind the order — it's value-cond-value, not cond-value-value.** Coming from C's
  `cond ? a : b`, the Python order (`a if cond else b`) trips people up; read it as an
  English sentence to keep it straight.
- **In comprehensions, don't confuse the two `if` positions:** `if/else` *before* the
  `for` chooses each element's value; a bare `if` *after* the `for` filters elements
  out. Mixing them up silently changes behaviour.

### Where this shows up

- **Real work — labels & thresholds:** turning a model score into a class label, a
  status into a colour, a count into singular/plural text — the canonical value choice.
- **Real work — safe defaults:** `x if x is not None else default` for config/optional
  arguments where `0`/`""` are valid (the correct partner to the truthiness rules in
  1.17).
- **Real work — conditional arguments:** choosing a batch size, retry count, or path
  inline based on a flag, without a preceding `if` block.
- **Real work — per-row transforms:** capping/flooring/relabelling values inside a
  list or DataFrame comprehension (e.g. clip outliers) in one pass.
- **Pattern mapping (secondary):** compact value selection shows up constantly in
  algorithm code — `dp[i] = max(...) if cond else ...`, choosing the next pointer/
  direction, or building a result element conditionally inside a comprehension.
[↑ Back to top](#contents)

---

<a id="1.20"></a>
## 1.20 — "I'm layering default settings under user overrides" → dict merge & setdefault

### The situation

You have default settings and a user-supplied override, and you want the user's values
to win where present, falling back to defaults everywhere else:

```python
defaults = {"timeout": 30, "retries": 3, "verbose": False}
user     = {"timeout": 60, "verbose": True}

# You want: {"timeout": 60, "retries": 3, "verbose": True}
```

The hand-written merge is a loop you keep re-typing, and it's easy to merge in the
wrong direction (letting defaults overwrite the user's choices):

```python
config = {}
for k, v in defaults.items():    # copy defaults...
    config[k] = v
for k, v in user.items():        # ...then let user values overwrite. Two loops.
    config[k] = v
```

A related chore: building a "key → list" grouping where you must create the empty list
the first time you see each key (the `KeyError`-on-first-touch problem from grouping).

### What's really going on

Two everyday dict operations have clean, modern syntax that most people don't reach for:

- **Merging** two dicts with a clear "who wins" rule. The winner is whichever dict is
  applied **last** — later keys overwrite earlier ones. Getting the order right *is*
  the whole task.
- **"Get this key, but if it's missing, set it to a default first"** — done in one step
  with `dict.setdefault`, avoiding the manual "if key not in d: d[key] = ..." dance.

The realisation: you're not writing custom logic, you're doing standard dict
composition — and Python 3.9+ gives you an operator (`|`) for it, with `{**a, **b}`
working on older versions too.

### The move

Merge with the **`|`** operator (3.9+) or **`{**a, **b}`** unpacking, putting the
**winner last**:

```python
config = defaults | user        # user's keys overwrite defaults'  (3.9+)
config = {**defaults, **user}   # same result, works on all 3.x
```

For "read-or-initialise a key", use **`setdefault`**:

```python
groups.setdefault(key, []).append(item)
```

### Why it works

`a | b` builds a **new** dict by taking all of `a`, then overlaying all of `b` — so for
any key in both, `b`'s value wins because it's applied last. `{**a, **b}` does the
identical thing: `**` "spreads" each dict's key-value pairs into the new literal, left
to right, last-wins. Both **copy** into a fresh dict, leaving the originals untouched.

`d.setdefault(key, default)` returns `d[key]` if the key exists; if not, it first
*inserts* `key: default` and then returns that default — so the single line
`groups.setdefault(k, []).append(x)` always has a real list to append to, even the
first time. (For heavy grouping, `defaultdict(list)` from Area 3 is cleaner, but
`setdefault` is the zero-import, one-off tool.)

### The code, every line explained

```python
defaults = {"timeout": 30, "retries": 3, "verbose": False}
user     = {"timeout": 60, "verbose": True}

# --- Merge: winner goes LAST --------------------------------------------
config = defaults | user        # {"timeout": 60, "retries": 3, "verbose": True}
#        └ base       └ overrides win
# Flip the order and defaults would clobber the user — almost always a bug:
wrong  = user | defaults        # {"timeout": 30, ...} -> user's 60 LOST

# --- Same thing on Python < 3.9 -----------------------------------------
config = {**defaults, **user}   # ** spreads pairs into a new dict, left-to-right

# --- In-place merge: update the left dict instead of making a new one ---
settings = dict(defaults)       # a copy so we don't mutate the original defaults
settings |= user                # |= updates settings in place (3.9+)
settings.update(user)           # the classic equivalent (all versions)

# --- setdefault: read, or initialise-then-read, in one step -------------
groups = {}
for item in [("a", 1), ("b", 2), ("a", 3)]:
    key, val = item
    groups.setdefault(key, []).append(val)
    #      │           │   └ created ONLY if key is missing
    #      │           └ the default value to insert on first touch
    #      └ returns the existing OR just-created list, ready to .append
# groups -> {"a": [1, 3], "b": [2]}  — no KeyError, no manual if-check.

# --- setdefault for a "count/accumulate" cache --------------------------
seen = {}
seen.setdefault("x", 0)         # ensures "x" exists at 0 if not already present
# (For pure counting prefer Counter; for grouping prefer defaultdict — Area 3.)

# --- Building config from many layers (left-to-right precedence) --------
final = {**SYSTEM_DEFAULTS, **env_config, **cli_args}
# rightmost wins: CLI overrides env, which overrides system defaults. One line.
```

### Impact

- **Correctness:** a single, explicit "winner-last" expression removes the
  wrong-direction merge bug that two manual loops invite.
- **Clarity:** `defaults | user` reads as "defaults, overridden by user" — the layering
  intent is visible at a glance.
- **Less code:** the two-loop merge and the "if key not in d" guard each collapse to one
  expression.

### Pros & cons / when NOT to

**Reach for `|` / `{**a, **b}` when:** combining config layers, applying overrides, or
building a dict from several sources with clear precedence. Reach for `setdefault` for a
one-off "init key if absent then use it".

**Watch out / when NOT to:**
- **Merging is *shallow*.** Nested dicts aren't deep-merged — a whole nested dict in
  `user` *replaces* the one in `defaults`, it doesn't merge inside it. For nested
  config you need a recursive deep-merge (or a library); `|` won't do it.
- **`|` is Python 3.9+.** Use `{**a, **b}` for portability across older interpreters.
- **`setdefault` always evaluates its default argument**, even when the key exists. If
  the default is expensive to build (`setdefault(k, expensive())`), `expensive()` runs
  every call regardless — use `defaultdict` (which calls the factory only on a miss) or
  an explicit check instead.
- **For real grouping/counting, prefer `defaultdict`/`Counter`** (Area 3) — they're
  clearer and avoid `setdefault`'s eager-default cost in loops.
- **Duplicate-key data loss:** merging silently drops the loser's value for shared
  keys. If you need to *combine* values (sum, concatenate) rather than overwrite, that's
  a reduce/group operation, not a merge.

### Where this shows up

- **Real work — layered configuration:** system defaults < environment < CLI/overrides
  is the standard precedence stack in almost every application and training script —
  one `{**...}` line.
- **Real work — request/option building:** merging default headers/params with
  per-call overrides before an API request (ties to the APIs area).
- **Real work — building lookups/groupings:** `setdefault(k, []).append(v)` to invert a
  mapping or bucket records when you don't want a `defaultdict` import.
- **Real work — hyperparameter overrides:** a base config dict overlaid with an
  experiment's tweaks, so each run records exactly `base | experiment`.
- **Pattern mapping (secondary):** "merge two maps", building adjacency structures, and
  frequency/group maps (`setdefault`) are common building blocks in graph and
  hashing-based problems (Area 11), though there `defaultdict`/`Counter` usually read
  best.
[↑ Back to top](#contents)

---

<a id="1.21"></a>
## 1.21 — "A tower of if/elif inspecting the shape of my data" → the match statement

### The situation

You're handling events that arrive as dicts with different shapes depending on a
`"type"` field, and you branch on both the type *and* the fields inside:

```python
event = {"type": "click", "x": 10, "y": 20}

if event["type"] == "click" and "x" in event and "y" in event:
    handle_click(event["x"], event["y"])
elif event["type"] == "scroll" and "delta" in event:
    handle_scroll(event["delta"])
elif event["type"] == "key" and "code" in event:
    handle_key(event["code"])
else:
    ignore(event)
```

Each branch repeats `event["type"] ==`, manually checks which keys exist, then digs the
values back out by key. It's verbose, and every branch re-extracts fields by hand —
easy to typo a key or forget an existence check.

### What's really going on

You're doing **structural pattern matching**: branching on the *shape* of the data (its
type, which keys/fields it has) and, in the same step, **pulling out** the pieces you
need. The if/elif chain conflates three jobs — test the discriminator, verify the
shape, and extract the values — and makes you write all three by hand in every branch.

Python 3.10 added the **`match`/`case`** statement for exactly this. It's *not* a plain
C-style switch on a single value; it matches against **patterns** that can describe
structure — "a dict with a `type` of `'click'` and `x`, `y` keys" — and **binds** the
matched parts to variables automatically (called **capturing**).

### The move

Use `match` on the value and `case` patterns that describe each shape, capturing fields
inline:

```python
match event:
    case {"type": "click", "x": x, "y": y}:   # matches shape AND binds x, y
        handle_click(x, y)
    case {"type": "scroll", "delta": d}:
        handle_scroll(d)
    case _:                                    # _ = the catch-all ("default")
        ignore(event)
```

### Why it works

`match value:` evaluates the subject once, then tries each `case` pattern top to bottom,
running the **first** that matches. A pattern like `{"type": "click", "x": x, "y": y}`
matches if the subject is a mapping that has a `"type"` key equal to `"click"` **and**
has `"x"` and `"y"` keys — and in the same move it **binds** those values to the names
`x` and `y`, so you skip the manual `event["x"]` extraction. A literal in the pattern
(`"click"`) means "must equal this"; a bare name (`x`) means "match anything and capture
it". The wildcard `_` matches everything, serving as the default branch.

### The code, every line explained

```python
match event:
    case {"type": "click", "x": x, "y": y}:
        #    └ literal: must equal "click"   └ capture: bind whatever's here to x, y
        handle_click(x, y)                   # x, y are ready — no event["x"] needed

    case {"type": "scroll", "delta": d}:
        handle_scroll(d)

    case {"type": "key", "code": code} if code in VALID_KEYS:
        #                                  └ a GUARD: extra condition that must also hold
        handle_key(code)                   # only matches if code is valid

    case {"type": t}:                        # any other event that at least has a type
        log.warning("unhandled event type: %s", t)

    case _:                                  # catch-all default (no type key at all)
        ignore(event)

# --- Matching sequences (by structure/length), with capture -------------
command = ["move", 10, 20]
match command:
    case ["move", x, y]:                     # a 3-item list starting with "move"
        move_to(x, y)                        # x=10, y=20 captured
    case ["quit"]:                           # exactly the 1-item list ["quit"]
        shutdown()
    case ["log", *rest]:                     # "log" then ANY number of items -> rest (1.6)
        log_all(rest)                        # *rest captures the remaining items as a list

# --- Matching by TYPE, and alternatives with | --------------------------
match value:
    case int() | float():                    # | = "or": matches an int OR a float
        use_number(value)
    case str() if value.strip():             # a non-empty string (guard)
        use_text(value)
    case None:                               # the literal None
        use_default()

# --- The trap: a bare NAME is a capture, not a comparison ---------------
LIMIT = 100
match n:
    case LIMIT:        # WRONG: this does NOT compare n to 100 — it binds n to `LIMIT`
        ...            # and matches EVERYTHING. Capitalised names are still captures!
    # To compare against a constant, qualify it: use `case SomeEnum.LIMIT:` (a dotted
    # name is treated as a value to match) or add a guard: `case x if x == LIMIT:`.
```

### Impact

- **Less repetition:** the discriminator test, shape check, and field extraction become
  one pattern per branch instead of three hand-written pieces.
- **Safer extraction:** captured names only bind when the shape actually matches, so you
  can't read a field that isn't there — the existence check is built into the pattern.
- **Readability:** the patterns visually mirror the data shapes, so a reader sees the
  handled cases at a glance.

### Pros & cons / when NOT to

**Reach for `match` when:** you branch on the **structure or type** of data — event/
message dispatch, parsing nested JSON shapes, AST/command handling, or several
list/tuple layouts.

**Watch out / when NOT to:**
- **A bare lowercase *or* uppercase name in a `case` is a capture, not a comparison** —
  the single biggest gotcha. `case LIMIT:` matches anything and rebinds `LIMIT`. To
  match a constant, use a **dotted** name (`case Color.RED:`) or a guard
  (`case x if x == LIMIT:`).
- **It's not just a faster `if` for simple equality.** For a plain "one value, a few
  equal-to checks", an `if/elif` or a `dict` dispatch (`{"click": handle_click}`) is
  often simpler. `match` earns its keep when you're destructuring *shape*.
- **Python 3.10+ only.** Don't use it in code that must run on 3.9 or earlier.
- **Order matters and first match wins** — put specific patterns before general ones,
  and remember `case _:` should come last (anything after it is unreachable).

### Where this shows up

- **Real work — message/event dispatch:** handling webhook payloads, queue messages, or
  websocket events that share a `type`/`kind` field but carry different fields — match on
  the shape and pull out what each needs.
- **Real work — parsing nested API/JSON responses:** branching on response shapes (a
  success body vs an error body vs a paginated body) and destructuring in one step.
- **Real work — command/DSL handling:** interpreting structured commands or config
  entries given as lists/dicts, like the `["move", x, y]` example.
- **Pattern mapping (secondary):** structural matching and destructuring map neatly onto
  recursive processing of nested/tree structures (e.g. walking an expression tree or
  nested JSON in Area 11's recursion scenarios), where each `case` handles one node
  shape.
[↑ Back to top](#contents)

---

<a id="1.22"></a>
## 1.22 — "I passed the wrong type and only found out when it crashed" → type hints

### The situation

You write a function and call it slightly wrong — and nothing complains until it blows
up at runtime, possibly deep inside, possibly in production:

```python
def average(values):
    return sum(values) / len(values)

average("123")        # no error here... runs sum("123") -> TypeError much later,
                      # or worse, silently does the wrong thing for some inputs
average([1, 2, 3])    # the intended use — but the signature never said so
```

Six months later, someone (maybe you) reads `def average(values):` and has to *guess*:
a list of what? ints? floats? could it be a single number? The function's contract — what
it accepts and what it returns — lives only in your head and the implementation.

### What's really going on

Python is **dynamically typed**: variables don't declare their type, and types are only
checked as code runs. That's flexible, but it means a wrong type is caught *late* (at the
crash) or *never* (silent misbehaviour), and the function's expected inputs/outputs
aren't written down anywhere a reader or tool can see.

**Type hints** (also called *annotations*, added progressively from Python 3.5+) let you
*annotate* what types a function expects and returns:

```python
def average(values: list[float]) -> float:
```

Crucially, hints are **not enforced at runtime** by Python itself — the interpreter
ignores them for execution. Their power comes from **static type checkers** (tools like
`mypy` or `pyright`/Pylance, "static" = analyse the code *without running it*) that read
the hints and flag mismatches *before* you run anything, plus the IDE autocompletion and
documentation they enable.

### The move

Annotate parameters with `name: type` and the return with `-> type`:

```python
def average(values: list[float]) -> float:
    return sum(values) / len(values)
```

Now a checker flags `average("123")` as an error *before* you run it, and your editor
knows `average(...)` returns a `float`.

### Why it works

A type hint records the *intended* type next to the name. A static checker then traces
types through your code: it knows `average` wants a `list[float]`, sees `"123"` is a
`str`, and reports the mismatch — at edit/CI time, not at 2 a.m. in production. The
hints also feed your IDE, so autocomplete and inline docs work, and they serve as
always-accurate documentation (unlike a comment, a checker *verifies* the hint stays
true). Because Python ignores them at runtime, adding hints never changes behaviour or
speed — they're a safety net laid over the same code.

### The code, every line explained

```python
# --- Basic annotations: params and return ------------------------------
def average(values: list[float]) -> float:   # takes a list of floats, returns a float
    return sum(values) / len(values)
# `list[float]` = a list whose elements are floats. `-> float` = the return type.
# (Pre-3.9 you'd import and write List[float] from `typing`; 3.9+ uses built-in list.)

# --- Common building blocks ---------------------------------------------
name: str = "job1"                  # variable annotation (rarely needed; inferred)
counts: dict[str, int] = {}         # dict mapping str keys to int values
ids: set[int] = set()               # a set of ints
pair: tuple[int, str] = (1, "a")    # a 2-tuple: first int, second str

# --- Optional / "might be None": the most useful one --------------------
def find_user(uid: int) -> "User | None":   # returns a User OR None (3.10+ syntax)
    ...
# `X | None` means "X or None" — signals the caller MUST handle the missing case.
# Pre-3.10: Optional[User] from typing means exactly the same thing.

# --- "Any of these types": union ----------------------------------------
def to_text(x: int | float | str) -> str:    # accepts any of the three
    return str(x)

# --- Functions, callables, and containers of containers -----------------
from typing import Callable
def apply(fn: Callable[[int], int], xs: list[int]) -> list[int]:
    #          └ a function taking one int, returning an int
    return [fn(x) for x in xs]
matrix: list[list[float]] = [[1.0, 2.0], [3.0, 4.0]]   # nested types compose

# --- Hints are NOT enforced at runtime (proof) --------------------------
average("123")          # Python RUNS this line without complaint at definition;
                        # only a checker (mypy/pyright) flags it beforehand. Python
                        # itself won't raise until sum("123") fails at execution.

# --- Alias a complex type for readability -------------------------------
Vector = list[float]
def dot(a: Vector, b: Vector) -> float:      # reads cleaner than list[float] twice
    return sum(x * y for x, y in zip(a, b))
```

### Impact

- **Bugs caught early:** type mismatches surface at edit/CI time instead of as runtime
  crashes — especially valuable across module boundaries and on large codebases.
- **Self-documenting contracts:** the signature states what goes in and what comes out;
  no guessing from the body or stale comments.
- **Better tooling:** autocomplete, go-to-definition, and refactoring become reliable
  because the editor knows the types.

### Pros & cons / when NOT to

**Reach for type hints when:** writing functions others (or future-you) will call,
public APIs, library code, or anything non-trivial in a shared/long-lived codebase.
They pay off most at boundaries between modules.

**Watch out / when NOT to:**
- **They're not runtime validation.** A hint does **not** stop bad data at runtime — if
  the input comes from a user/API/file, you still need real validation (Area 3,
  pydantic/manual checks). Hints catch *programmer* mistakes via a checker, not *data*
  mistakes at runtime.
- **You must actually run a checker.** Hints with no `mypy`/`pyright` in your editor or
  CI are just documentation — helpful, but they won't *catch* anything. Wire the checker
  in or the safety net isn't there.
- **Don't over-engineer.** For a tiny throwaway script or an obvious local helper, heavy
  generic hints add noise for little gain. Start with function signatures (params +
  return); that's 90% of the value. Avoid contorting code to satisfy the checker.
- **Hints can drift if ignored** — but unlike comments, a checker will catch the drift,
  *if* you run it.

### Where this shows up

- **Real work — function & API contracts:** annotating the inputs/outputs of pipeline
  steps, utilities, and service functions so callers can't pass the wrong shape
  unnoticed.
- **Real work — data models:** type hints are the *foundation* of `@dataclass` and
  `pydantic` models (Areas 3/10) — the field types you annotate drive validation,
  serialisation, and editor support.
- **Real work — refactoring safety:** changing a function's signature and letting the
  checker flag every now-broken call site across a large codebase — a refactor you'd
  fear without hints.
- **Real work — ML interfaces:** documenting that a function takes `np.ndarray` /
  `list[float]` and returns a `float` score, so model-serving glue code is checked at
  the seams.
- **Pattern mapping (secondary):** not an algorithm tool, but hints (`Optional[Node]`
  for a tree pointer, `list[list[int]]` for a grid) make data-structure-heavy algorithm
  code in Area 11 far easier to read and to get right the first time.

[↑ Back to top](#contents)

