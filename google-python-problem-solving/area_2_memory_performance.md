# Area 2 — Memory & Performance

When a program is too slow or eats too much RAM, the instinct is to *guess* and start
rewriting. This area trains the opposite reflex: **measure first, understand the shape
of the cost (time vs memory, O(n) vs O(n²)), then reach for the one move that fits**.
The techniques are universal, but every example is biased toward the data/ML work you
do — feature processing, large arrays, batch jobs, embeddings, long-running pipelines.

---

<a id="contents"></a>
## Contents

- [2.1 — "It's slow and I'm guessing why" → profile before optimising](#2.1)
- [2.2 — "Spot the accidental O(n²)" → the nested-loop smell](#2.2)
- [2.3 — "Make it work → correct → fast" → the optimisation order](#2.3)
- [2.4 — "Building a big string in a loop is slow" → `str.join` vs `+`](#2.4)
- [2.5 — "Millions of small objects eat all my RAM" → `__slots__`](#2.5)
- [2.6 — "Changing one copy changed the other" → copy vs deepcopy & aliasing](#2.6)
- [2.7 — "Loading the whole thing to use a bit" → lazy evaluation & generators](#2.7)
- [2.8 — "Same pure computation repeated" → precompute & lookup tables](#2.8)
- [2.9 — "Dict/set lookups vs scanning a list" → choosing O(1) structures](#2.9)
- [2.10 — "Memory keeps climbing in a long run" → reference cycles & leaks](#2.10)
- [2.11 — "Numbers stored as Python objects are huge" → array / memoryview / numpy](#2.11)
- [2.12 — "Looping in Python over arrays is slow" → vectorise the hot path](#2.12)
- [2.13 — "Reading a huge file spikes memory" → chunked / buffered I/O](#2.13)
- [2.14 — "Repeated work across calls" → caching layers & `lru_cache` sizing](#2.14)
- [2.15 — "Which is faster — I'll just measure" → micro-benchmarking correctly](#2.15)
- [2.16 — "Integer/string interning & identity surprises" → small-object caching](#2.16)

---


<a id="2.1"></a>
## 2.1 — "It's slow and I'm guessing why" → profile before optimising

### The situation

Your feature-engineering script takes 90 seconds on a 200,000-row dataset and you need
it under 10. You *think* the slow part is the loop that computes a rolling average, so
you spend an afternoon rewriting it in clever vectorised code — and the script still
takes 88 seconds. The real culprit was a `json.loads` call buried in a helper that
re-parsed the same config file once per row. You optimised the wrong thing.

Here is the kind of code you're staring at:

```python
def process(rows):                       # 200,000 rows
    out = []
    for r in rows:
        cfg = load_config("settings.json")   # <-- re-reads + parses the file EVERY row
        out.append(transform(r, cfg))        # the part you THOUGHT was slow
    return out
```

You "know" `transform` is the expensive bit because it does the maths. You're guessing.

### What's really going on

Performance intuition is **unreliable** — even for experienced engineers. The slow
line is routinely *not* the one you suspect, because the cost hides in places you don't
look: a function call repeated more often than you realised, an accidental file read, a
data-structure choice (see 2.9), a hidden O(n²) (see 2.2). The only way to know is to
**measure** where the time actually goes.

The tool for "which function/line is eating the time?" is a **profiler** — a tool that
runs your program and records how long is spent in each function and how many times
each is called. Python ships one in the standard library: **`cProfile`**. For
"which of these two small snippets is faster?" the right tool is **`timeit`** (its own
scenario, 2.15). Profile first to *find* the hot spot; benchmark to *compare* fixes.

### The move

Run the code under `cProfile`, sort by cumulative time, and read the top of the table:

```python
import cProfile, pstats
cProfile.run("process(rows)", "profile.out")   # run + record into a file
pstats.Stats("profile.out").sort_stats("cumulative").print_stats(10)  # top 10
```

The output shows `load_config` called 200,000 times taking 80 of the 90 seconds — and
suddenly the fix is obvious: read the config **once**, before the loop.

### Why it works

`cProfile` instruments every function call: it records the call count, the time spent
*inside* the function itself (**tottime** — "total time", excluding sub-calls), and the
time spent in the function *plus everything it calls* (**cumtime** — "cumulative
time"). Sorting by cumulative time surfaces the call that dominates the whole run;
sorting by tottime surfaces the function doing the most work *itself*. You stop
guessing because the numbers point straight at the offender — including the
"I called it 200,000 times without realising" class of bug that no amount of staring at
the code reveals.

### The code, every line explained

```python
import cProfile          # the deterministic profiler (records every call)
import pstats            # formats/sorts the recorded stats

# --- Profile a whole function call ---------------------------------------
cProfile.run("process(rows)", "profile.out")   # runs process(rows), writes stats to file
#            └ the code to run, as a string    └ output file to save results into

# --- Read the results, sorted to find the hot spot -----------------------
stats = pstats.Stats("profile.out")     # load the recorded run
stats.sort_stats("cumulative")          # sort by cumtime: "what dominates end-to-end"
stats.print_stats(10)                   # print the 10 worst rows
# Columns you read:
#   ncalls   = how many times it was called   <- the "200000 calls?!" reveal
#   tottime  = time INSIDE this function alone (not its sub-calls)
#   cumtime  = time in this function + everything it calls
# Sort by "tottime" instead to find the function burning CPU in its own body.

# --- Lighter-weight: time just one block without the full profiler -------
import time
start = time.perf_counter()             # perf_counter = highest-resolution clock,
                                         # the correct timer for measuring durations
                                         # (NOT time.time(), which can jump if the
                                         #  system clock is adjusted)
process(rows)
print(f"took {time.perf_counter() - start:.2f}s")   # wall-clock duration of the block

# --- Line-by-line (third-party, when cProfile points at a big function) --
# pip install line_profiler ; then decorate the suspect function with @profile
# and run `kernprof -l -v script.py` to get PER-LINE timings inside it.
```

### Impact

- **Spend effort where it pays:** the **80/20 rule** holds almost universally — a tiny
  fraction of the code accounts for most of the runtime. Profiling finds that fraction
  so an afternoon's work gives a 10x speed-up instead of 2%.
- **Avoids wasted rewrites:** you don't refactor the innocent `transform` loop; you move
  one line out of it.
- **Objective, repeatable:** numbers, not hunches — and you can re-profile after a fix to
  confirm it actually helped (and didn't shift the bottleneck elsewhere).

### Pros & cons / when NOT to

**Reach for `cProfile` when:** something is slow and you don't have *certain*, measured
knowledge of why. That is almost always — profile before touching anything.

**Watch out / when NOT to:**
- **Profiler overhead skews micro-timings.** `cProfile` adds per-call overhead, so it
  inflates the *absolute* times of functions called millions of times. Use it to find
  *relative* hot spots, not to report "this takes exactly 1.2 ms" — use `timeit` (2.15)
  for precise micro-benchmarks.
- **Profile a realistic input.** Profiling a 100-row toy sample can hide an O(n²) that
  only bites at 200,000 rows. Use representative data sizes.
- **It measures CPU/wall time, not memory.** For "why is RAM climbing?" you need a
  *memory* profiler (`tracemalloc`, `memory_profiler`) — see 2.10.
- **Don't optimise what isn't slow enough to matter.** If the whole job runs in 2
  seconds once a day, profiling for sport wastes *your* time, the scarcer resource.

### Where this shows up

- **Real work — slow data pipelines:** finding that 90% of an ETL run is a per-row
  database round-trip or a repeated parse, not the transformation logic.
- **Real work — training/inference loops:** profiling to discover data loading (not the
  model maths) is starving the GPU, or that a Python-side preprocessing step dominates.
- **Real work — "the API is slow":** profiling a request handler to find the real cost is
  an N+1 query pattern, not the serialisation you blamed.
- **Pattern mapping (secondary):** profiling is how you *empirically confirm* an
  algorithm's complexity class in practice — the bridge between Big-O analysis (2.2) and
  the actual hot line in your code.
[↑ Back to top](#contents)

---

<a id="2.2"></a>
## 2.2 — "Spot the accidental O(n²)" → the nested-loop smell

### The situation

You need to find, for a list of new transactions, which ones are *not yet* recorded in
a list of known transactions. Both are lists of id strings. You write the obvious thing:

```python
known = [...]          # 50,000 already-recorded transaction ids
new = [...]            # 50,000 incoming transaction ids
missing = []
for n in new:                       # for every incoming id...
    if n not in known:              # ...scan the WHOLE known list to check membership
        missing.append(n)
```

On 500 ids it's instant. On 50,000 it takes minutes; on 200,000 it's effectively
frozen. Nothing *looks* wrong — there's only one visible `for` loop. But the runtime is
exploding far faster than the data is growing: doubling the input made it roughly four
times slower.

### What's really going on

There's a **hidden second loop**. `n not in known` is not a free check — for a **list**,
Python must scan it element by element, which is itself an O(n) loop. So the visible
`for n in new` (n iterations) times the invisible scan inside `in known` (n elements
each) gives **n × n = O(n²)** total work: for 50,000 × 50,000 that's **2.5 billion**
comparisons.

> **Big-O notation** describes how work *grows* with input size n, ignoring constant
> factors. **O(n)** = work grows in proportion to n (double the data, double the time).
> **O(n²)** = work grows with the *square* (double the data, **quadruple** the time).
> The "smell" of accidental O(n²) is a loop whose body contains *another* pass over the
> data — and that inner pass is often hidden inside an innocent-looking operation like
> `x in a_list`, `a_list.index(x)`, `del a_list[0]`, or a `.remove()`.

The realisation: the quadratic blow-up is the *membership test against a list*. Swap the
list for a structure with **O(1)** membership — a **set** or **dict** (see 2.9) — and the
inner loop vanishes.

### The move

Build a **set** of the known ids once (O(n)), then each `in` check is O(1):

```python
known_set = set(known)              # one O(n) pass to build a hash set
missing = [n for n in new if n not in known_set]   # each `in` is now O(1)
```

Total cost drops from O(n²) to **O(n)** — for this data, from ~2.5 billion operations
to ~100,000.

### Why it works

A **set** stores its elements in a **hash table** — a structure that computes a value's
*hash* (a number derived from the value) and uses it to jump almost directly to where
that value would live, instead of scanning. So `x in a_set` takes roughly **constant
time regardless of how many elements the set holds** — O(1) — whereas `x in a_list`
must walk the list — O(n). Building the set is one O(n) pass; the n membership checks
are then n × O(1) = O(n). The nested-loop structure is gone, so the n² disappears.

### The code, every line explained

```python
# --- The accidental O(n²): list membership inside a loop -----------------
missing = []
for n in new:                       # outer loop: n iterations
    if n not in known:              # `in` on a LIST scans up to n elements -> O(n)
        missing.append(n)           # total: O(n) * O(n) = O(n^2)

# --- The fix: O(1) membership via a set ----------------------------------
known_set = set(known)              # build hash set once: O(n) time, O(n) memory
missing = [n for n in new           # outer loop: n iterations...
           if n not in known_set]   # ...each membership test is O(1) -> total O(n)

# --- Other hidden quadratics to recognise --------------------------------
# 1) Building a list by repeatedly removing/searching:
for item in items:
    if item in seen:                # `in` on a list -> hidden O(n) scan
        ...
# 2) list.index() inside a loop is the same scan in disguise:
for x in xs:
    pos = ys.index(x)               # .index scans ys -> O(n) per call -> O(n^2)
# 3) Deleting from the FRONT of a list in a loop:
while data:
    head = data.pop(0)              # pop(0) shifts every remaining element -> O(n)
    ...                             # n pops * O(n) shift = O(n^2). Use collections.deque
                                    # (popleft is O(1)) for a queue.
# 4) String concatenation in a loop is a close cousin (its own scenario, 2.4).

# --- How to SPOT it before it ships --------------------------------------
# Ask of any loop body: "does this line itself loop over the data?"
#   x in list      -> yes (scan)        x in set/dict   -> no (hash)
#   list.index(x)  -> yes (scan)        list.append(x)  -> no (amortised O(1))
#   list.pop(0)    -> yes (shift)       list.pop()      -> no (end is O(1))
# Nested data loop  -> O(n^2). Confirm with cProfile on a LARGE input (2.1).
```

### Impact

- **Asymptotic, not constant, win:** going O(n²) → O(n) means the gap *widens without
  limit* as data grows — minutes become milliseconds, and "frozen" becomes "instant".
  No micro-optimisation (faster loop body, C extension) can rescue a quadratic
  algorithm; you must change the *shape*.
- **Memory trade:** you spend O(n) extra memory on the set to buy the O(n) time — almost
  always worth it (see 2.9 for the trade-off).

### Pros & cons / when NOT to

**Reach for "kill the nested scan" when:** a loop's body re-scans the data — membership
tests, `.index`, `.remove`, front-pops, or a literal inner loop over the same/another
big collection.

**Watch out / when NOT to:**
- **Tiny n:** for a handful of items, O(n²) is irrelevant and a list is simpler. The
  blow-up only matters at scale — don't add a set for a 10-element list.
- **Some problems are genuinely O(n²)** (comparing all pairs, e.g. a full distance
  matrix). Then the goal isn't to pretend otherwise but to *reduce the work* (spatial
  indexing, blocking, sampling) or accept it knowingly.
- **Order/duplicates:** a set discards duplicates and ordering. If you need those, use a
  dict (preserves insertion order, O(1) lookup) or keep the list *and* a companion set
  for the membership test.

### Where this shows up

- **Real work — deduplication & joins:** "which records are new?" / "match dataset A to
  dataset B on a key" — the canonical place a list-scan turns an overnight job into a
  five-second one (dict join, data-wrangling area).
- **Real work — feature lookups:** checking each row against a blocklist/allowlist of ids;
  a set membership keeps it linear at millions of rows.
- **Real work — graph/duplicate detection:** "have I visited this node/seen this hash?"
  must be a set, or BFS/DFS silently degrades to O(V²).
- **Pattern mapping (secondary):** this is the core insight behind the **arrays + hashing**
  family (e.g. two-sum): replace an O(n²) double loop with an O(n) pass plus a hash
  set/map. Recognising the hidden inner scan *is* the skill those problems test.
[↑ Back to top](#contents)

---

<a id="2.3"></a>
## 2.3 — "Make it work → correct → fast" → the optimisation order

### The situation

You're asked to build a function that scores a batch of model predictions against
labels and returns precision/recall. Eager to be efficient, you start by reaching for
NumPy vectorisation, a clever one-pass algorithm, and a caching layer — *before the
plain version even runs*. Three hours later you have fast code that returns the wrong
recall, and you can't tell whether the bug is in the maths or the optimisation, because
both were written at once.

The opposite failure is just as common: you write a clear, correct version, it runs in
40 ms on real data, and you *still* spend a day vectorising it to 4 ms — for a function
called once per batch where 40 ms never mattered.

### What's really going on

There's a **fixed order** to writing performant code, and skipping steps is what causes
both failures above:

1. **Make it work** — get a version that runs end-to-end, however naively.
2. **Make it correct** — verify it produces the right answer (tests, spot checks,
   known cases). Correctness is *not optional* and *not negotiable* — fast wrong code
   is worthless.
3. **Make it fast — only if measurement says you must.** Profile (2.1), find the real
   bottleneck, optimise *that*, and re-measure.

The deeper principle, attributed to Donald Knuth: *"premature optimisation is the root
of all evil."* Optimising before you have a correct baseline means (a) you can't tell if
your speed-up broke the answer, because there's no trusted reference to compare against,
and (b) you often optimise code that was never the bottleneck. The correct version is
your **oracle** — the thing you check the fast version *against*.

### The move

Write the simple correct version first; **keep it** as a reference; only then optimise,
comparing the fast version's output to the simple one on real data:

```python
# Step 1+2: simple, obviously-correct version — your oracle
def precision_simple(preds, labels):
    tp = sum(1 for p, y in zip(preds, labels) if p == 1 and y == 1)
    fp = sum(1 for p, y in zip(preds, labels) if p == 1 and y == 0)
    return tp / (tp + fp)

# Step 3 (ONLY if profiling says this is hot): the fast version
def precision_fast(preds, labels):
    import numpy as np
    p = np.asarray(preds); y = np.asarray(labels)
    tp = int(((p == 1) & (y == 1)).sum())
    fp = int(((p == 1) & (y == 0)).sum())
    return tp / (tp + fp)

assert precision_fast(preds, labels) == precision_simple(preds, labels)  # oracle check
```

### Why it works

Separating the three steps makes each one *debuggable in isolation*. When the simple
version is correct and tested, it becomes a trusted reference. Any future optimisation
is then a pure, checkable transformation: "does the fast version match the oracle on
these inputs?" If it diverges, you know the bug is in the optimisation, not the logic —
because the logic was already proven. And by gating step 3 on *measurement*, you only
pay the complexity cost of fast code where it actually buys something.

### The code, every line explained

```python
# --- Step 1 & 2: WORK + CORRECT (the oracle) -----------------------------
def dedupe_simple(rows):
    seen = []                       # naive, O(n^2) — but obviously correct
    out = []
    for r in rows:
        if r not in seen:           # we don't care that this is slow YET
            seen.append(r)
            out.append(r)
    return out
# Lock it in with tests on known inputs:
assert dedupe_simple([1, 1, 2, 3, 3]) == [1, 2, 3]   # the answer is PROVEN

# --- Step 3: FAST, only after profiling flags this as the bottleneck -----
def dedupe_fast(rows):
    seen = set()                    # O(1) membership (2.9) -> overall O(n)
    out = []
    for r in rows:
        if r not in seen:           # the optimisation: set, not list
            seen.add(r)
            out.append(r)
    return out

# --- Gate the optimisation behind a check against the oracle -------------
import random
sample = [random.randint(0, 50) for _ in range(1000)]
assert dedupe_fast(sample) == dedupe_simple(sample)   # same answer? then it's safe.
# Keep dedupe_simple in the tests forever as the regression reference.

# --- And gate it behind MEASUREMENT (don't optimise the cold path) -------
# Only replace dedupe_simple if cProfile (2.1) shows it's actually slow on
# real data. A correct-but-slow function that runs in 2 ms once a day is DONE.
```

### Impact

- **Correctness preserved:** the oracle catches any optimisation that silently changes
  the answer — the single most dangerous failure mode of "going fast".
- **Effort spent where it matters:** by gating step 3 on profiling, you avoid the
  "vectorised a function that runs once" trap and keep the codebase simple where speed
  is irrelevant.
- **Debuggability:** when something's wrong, you know *which layer* — logic or
  optimisation — because they were built and verified separately.

### Pros & cons / when NOT to

**Follow this order when:** building anything non-trivial — which is almost always. It's
a discipline, not a technique.

**Nuances / when NOT to:**
- **"Premature" ≠ "never".** The quote is not an excuse to write knowingly O(n²) code on
  data you *know* will be huge. Choosing the right *algorithm/data structure* up front
  (a set vs a list, 2.2/2.9) is design, not premature optimisation — it's part of step 1.
  The evil is *micro*-optimising (rewriting in C, unrolling loops) before correctness and
  measurement.
- **Throwaway scripts** may stop at step 2 forever — if it works and is fast enough, you
  are *done*. Stopping is a valid, often correct, decision.
- **Hard real-time/latency budgets** may force performance thinking into the design from
  the start — but even then you build a correct reference to validate against.

### Where this shows up

- **Real work — metrics & evaluation code:** a slow, obvious scoring function is the
  oracle that validates a fast vectorised one — bugs in metrics are silent and costly.
- **Real work — data transforms:** ship the clear pandas/loop version, profile the
  pipeline, vectorise *only* the stage that dominates (2.12).
- **Real work — ML feature engineering:** correctness of a feature first (does it match
  the spec on hand-checked rows?), speed second — a fast wrong feature poisons the model.
- **Pattern mapping (secondary):** in interviews this is "brute force first, then
  optimise" — state the O(n²) solution to prove you understand the problem, *then*
  improve to O(n) with hashing/two-pointers. The brute force is your correctness oracle.
[↑ Back to top](#contents)

---

<a id="2.4"></a>
## 2.4 — "Building a big string in a loop is slow" → `str.join` vs `+`

### The situation

You're serialising a large dataset to a single text blob — say turning 1,000,000 cleaned
records into newline-separated lines to write out or send to an API. You build the
output by concatenating with `+=`:

```python
report = ""                          # start with an empty string
for record in records:               # 1,000,000 records
    report += format_line(record)    # tack each formatted line onto the end
    report += "\n"                   # ...plus a newline
```

It produces the right text, but it's sluggish, and on some Python implementations
(PyPy, Jython) or slightly different code shapes it becomes *dramatically* slow — the
runtime growing quadratically with the number of records.

### What's really going on

**Strings in Python are immutable** — they cannot be changed in place (see 1.4's
mutable/immutable split). So `report += line` does **not** append to the existing
string; it **builds a brand-new string** containing all the old characters *plus* the
new ones, then rebinds `report` to it. The old string is thrown away.

That means each `+=` copies **all the characters accumulated so far**. On iteration k
you copy ~k characters. Summing over n iterations gives 1 + 2 + 3 + … + n ≈ **n²/2
character copies** — a hidden O(n²) (the same smell as 2.2), where the inner "loop" is
the character-by-character copy inside each concatenation.

> CPython has a *special optimisation* that sometimes mutates the string in place when
> it can prove the old one has no other references — which is why `+=` in a tight loop
> is often only modestly slow on CPython rather than catastrophic. But this optimisation
> is **fragile and implementation-specific**: it breaks if the string is referenced
> elsewhere, and it doesn't exist on other interpreters. Relying on it is a trap.

The fix is to **collect the pieces and join them once**. `str.join` knows the total
length up front, allocates the result buffer a single time, and copies each piece in
exactly once — O(n) total.

### The move

Build a **list** of pieces, then call `"".join(pieces)` once at the end:

```python
parts = [format_line(r) for r in records]   # collect pieces (list append is O(1))
report = "\n".join(parts)                    # ONE allocation, O(n) total copy
```

`"\n".join(parts)` glues the list elements together with `"\n"` between each — which
also removes the trailing-newline fiddliness of the `+=` version.

### Why it works

`str.join` does a **two-pass** job in C: first it sums the lengths of all the pieces to
compute the exact final size, allocates that buffer **once**, then copies each piece
into it a single time. Total character copies = the length of the output, i.e. O(n) —
versus O(n²) for repeated `+=`. Appending to a list in the meantime is amortised O(1)
(lists over-allocate so most appends don't copy), so the whole collect-then-join
pattern is linear.

### The code, every line explained

```python
# --- The trap: += rebuilds the whole string each time (O(n^2) worst case) -
report = ""
for record in records:
    report += format_line(record) + "\n"   # each += copies ALL chars so far
# On 1M records this can crawl; on non-CPython interpreters it's quadratic.

# --- The fix: collect pieces, join ONCE (O(n)) ---------------------------
parts = [format_line(r) for r in records]   # list of strings; appends are O(1)
report = "\n".join(parts)                    # single allocation + single copy pass
# join inserts "\n" BETWEEN pieces (n-1 separators), so no trailing newline.
# Want a trailing newline? add one: report = "\n".join(parts) + "\n"

# --- Even leaner: join straight from a generator (no intermediate list) --
report = "\n".join(format_line(r) for r in records)
# A generator expression (1.2) feeds pieces to join lazily. NOTE: join still
# must see them all to size the buffer, so it internally materialises them —
# memory is similar to the list, but the code is one clean line.

# --- The separator does double duty --------------------------------------
",".join(["a", "b", "c"])        # "a,b,c"   -> CSV-ish row
"".join(["un", "stop", "able"])  # "unstoppable" -> concatenate with NO separator
" ".join(words)                  # join words with single spaces

# --- join requires STRINGS — convert numbers first -----------------------
nums = [1, 2, 3]
", ".join(str(n) for n in nums)  # "1, 2, 3"   <- str() each; join won't coerce
# ", ".join(nums)  -> TypeError: sequence item 0: expected str, int found

# --- For building structured TEXT, prefer the real tool ------------------
# Building CSV? use the csv module. Building JSON? use json.dumps. Those handle
# quoting/escaping correctly — manual join is for simple, known-safe glue.
```

### Impact

- **Complexity:** O(n²) → O(n) in the worst case; even where CPython's optimisation
  hides it, `join` is reliably fast and portable across interpreters.
- **Clarity:** `"\n".join(parts)` states "these, separated by newlines" in one phrase,
  and removes off-by-one separator/trailing-newline bugs.
- **Predictability:** you don't depend on a fragile interpreter optimisation that can
  silently vanish when the code is refactored.

### Pros & cons / when NOT to

**Reach for `join` when:** you build a string from **many** pieces — rows of a report,
lines of a file, tokens of a sequence, a serialised payload.

**Watch out / when NOT to:**
- **A handful of pieces is fine with `+` or an f-string.** `name + ": " + value` or
  `f"{name}: {value}"` (1.11) is clearer for 2–4 known parts; reserve `join` for the
  *many-pieces-in-a-loop* case. The quadratic problem only exists at scale.
- **`join` needs an iterable of strings** — convert non-strings with `str()` first, or it
  raises `TypeError`.
- **Holding all pieces in memory** can itself be large for huge outputs — if the result
  is gigabytes, stream it to a file incrementally (write each piece with `f.write` inside
  a `with`, 1.3) rather than building one giant string (ties to chunked I/O, 2.13).
- **Structured formats** (CSV/JSON/XML) deserve their proper libraries for correct
  escaping — don't hand-join those.

### Where this shows up

- **Real work — serialising datasets:** building a large CSV/JSONL/text payload from many
  records before writing or sending it.
- **Real work — prompt/template assembly:** concatenating many retrieved chunks into one
  LLM prompt string (ties to chunking, Area 9) — `join` over the pieces, not `+=`.
- **Real work — log/report generation:** assembling a multi-thousand-line report from
  per-row formatted strings.
- **Pattern mapping (secondary):** "string compression"/"build result string" problems
  use a list-of-chars + `"".join` at the end as the idiomatic O(n) builder, exactly
  because per-character `+=` would be O(n²).
[↑ Back to top](#contents)

---

<a id="2.5"></a>
## 2.5 — "Millions of small objects eat all my RAM" → `__slots__`

### The situation

You represent each data point in a 10-million-row dataset as a small class instance —
a clean, attribute-access record:

```python
class Point:
    def __init__(self, x, y, label):
        self.x = x
        self.y = y
        self.label = label

points = [Point(x, y, lbl) for x, y, lbl in raw_rows]   # 10,000,000 of these
```

It reads beautifully (`p.x`, `p.label`) — but the process balloons to several gigabytes
of RAM and may get OOM-killed (the OS terminating it for using too much memory). Each
`Point` holds only three small values, yet each one is costing you *far* more than three
numbers' worth of memory.

### What's really going on

By default, **every Python instance carries its own dictionary** — the `__dict__` — to
store its attributes. That dict is what lets you add arbitrary attributes at runtime
(`p.z = 5` works even though `__init__` never mentioned `z`). Flexible, but expensive:
the dict has significant fixed overhead **per instance**, on top of the instance itself.

You can see it directly:

```python
import sys
p = Point(1, 2, "a")
sys.getsizeof(p)            # ~48 bytes for the instance object itself
sys.getsizeof(p.__dict__)  # ~296 bytes JUST for the attribute dict (CPython 3.13)
```

So each "three-number" record actually costs ~344 bytes, the overwhelming majority of
it the per-instance dict. Times 10 million, that dict overhead alone is gigabytes.

The realisation: you don't *need* the ability to add arbitrary attributes. Every `Point`
has exactly `x`, `y`, `label` and nothing else. If you tell Python the attribute names
are **fixed**, it can store them in a compact, fixed slot layout — like a C struct —
and skip the per-instance dict entirely. That's what **`__slots__`** does.

### The move

Declare the fixed attribute names in `__slots__`:

```python
class Point:
    __slots__ = ("x", "y", "label")     # fixed attribute set -> no per-instance dict
    def __init__(self, x, y, label):
        self.x = x
        self.y = y
        self.label = label
```

The class is used **identically** (`p.x`, `p.label` still work); only the memory layout
changes. Per-instance memory drops sharply — in this CPython, from ~344 bytes to ~56.

### Why it works

`__slots__` tells Python: "instances of this class have exactly these attributes —
allocate a fixed array of slots for them and **do not create a `__dict__`**." Attribute
access becomes a direct slot lookup (a fixed offset, like a struct field) rather than a
dict lookup, which is both **smaller** (no dict overhead per instance) and marginally
**faster** to read/write. The saving is *per instance*, so it scales with the number of
objects — which is exactly why it matters at millions of instances and is irrelevant at
a few dozen.

### The code, every line explained

```python
import sys

# --- Default: each instance carries a __dict__ (flexible but heavy) ------
class PointDict:
    def __init__(self, x, y, label):
        self.x, self.y, self.label = x, y, label

p = PointDict(1, 2, "a")
sys.getsizeof(p)             # instance object: ~48 bytes
sys.getsizeof(p.__dict__)    # PLUS the attribute dict: ~296 bytes  -> ~344 total
p.extra = 99                 # allowed: you can bolt on ANY attribute (that's the cost)

# --- With __slots__: fixed layout, no per-instance dict ------------------
class PointSlots:
    __slots__ = ("x", "y", "label")   # the ONLY attributes instances may have
    def __init__(self, x, y, label):
        self.x, self.y, self.label = x, y, label

s = PointSlots(1, 2, "a")
sys.getsizeof(s)             # ~56 bytes total, no separate dict -> ~6x smaller here
# s.extra = 99               # AttributeError! slots forbids unknown attributes
#                            # (this is a FEATURE: it catches attribute typos too)

# --- Usage is identical — only memory/layout changed ---------------------
s.x          # 1   (direct slot access, slightly faster than a dict lookup)
s.label      # "a"

# --- dataclasses support slots too (Python 3.10+) ------------------------
from dataclasses import dataclass
@dataclass(slots=True)        # generates __slots__ for you
class Sample:
    x: float
    y: float
    label: str
# Get the clean dataclass syntax AND the memory win in one decorator.

# --- Measuring the real-world saving on a big list -----------------------
import tracemalloc                      # stdlib memory tracker (see 2.10)
tracemalloc.start()
data = [PointSlots(i, i, "x") for i in range(1_000_000)]
print(tracemalloc.get_traced_memory()) # (current, peak) bytes — compare slots vs not
```

### Impact

- **Memory:** removes the per-instance dict overhead — commonly a **3–5x** reduction in
  per-object size for small records, which on millions of objects is the difference
  between fitting in RAM and an OOM kill.
- **Speed (minor):** slot attribute access is a touch faster than dict lookup, and lower
  memory means better cache behaviour and less GC pressure.
- **Safety bonus:** typos like `p.labl = ...` raise `AttributeError` instead of silently
  creating a new attribute.

### Pros & cons / when NOT to

**Reach for `__slots__` when:** you create **many** instances (hundreds of thousands+)
of a small, fixed-shape class — data points, graph nodes, parsed records, tree nodes.

**Watch out / when NOT to:**
- **You lose dynamic attributes.** Code (or libraries) that relies on setting arbitrary
  attributes at runtime, or on `instance.__dict__`, will break. Don't add slots to a
  class designed to be extended ad hoc.
- **Few instances → no point.** For a config object or a handful of singletons, the
  saving is nil and slots just add a constraint. Profile/measure memory (2.10) before
  reaching for it.
- **Inheritance subtleties:** if a subclass *doesn't* define `__slots__`, it regains a
  `__dict__` (losing the saving); and multiple inheritance with slots on several parents
  can conflict. Keep slotted classes simple.
- **Not a substitute for arrays.** If your "objects" are really *numbers*, millions of
  even slotted instances are still far heavier than a NumPy array or `array.array`
  (2.11) — for numeric data, store columns, not objects.

### Where this shows up

- **Real work — large in-memory datasets:** holding millions of parsed records/feature
  rows as objects when a DataFrame/array isn't a fit; slots keeps it in RAM.
- **Real work — graph/tree structures:** millions of node objects (graph algorithms,
  parse trees, spatial indices) shrink substantially with slots.
- **Real work — simulation/agent models:** many small stateful objects (particles,
  agents) where per-instance dict overhead dominates.
- **Pattern mapping (secondary):** in tree/graph LeetCode problems with huge node counts,
  a slotted `Node` class reduces memory; more broadly it's the "use a compact
  fixed-layout record instead of a flexible dict" instinct.
[↑ Back to top](#contents)

---

<a id="2.6"></a>
## 2.6 — "Changing one copy changed the other" → copy vs deepcopy & aliasing

### The situation

You have a base configuration for a model and you want to make a tweaked variant for an
experiment, without disturbing the original:

```python
base_config = {
    "lr": 0.01,
    "layers": [64, 32, 16],          # a nested list
    "name": "base",
}

variant = base_config                 # "copy" the config...
variant["name"] = "experiment_A"      # ...and tweak it
variant["layers"].append(8)           # add a layer to the variant

print(base_config["name"])            # "experiment_A"  (!!) — base changed too
print(base_config["layers"])          # [64, 32, 16, 8]  (!!) — and so did its layers
```

You never touched `base_config`, yet both its name *and* its layers changed. Two
"separate" configs are silently the same data.

### What's really going on

This is **aliasing** (introduced in 1.9). The line `variant = base_config` does **not**
copy anything — it makes `variant` a *second name* for the very same dict object in
memory. A Python variable is a *reference* (a label pointing at an object), and `=` just
points another label at the **same** object. Mutating through either name mutates the
one shared object.

The obvious fix is to make a copy — but there are **two kinds**, and the difference is
the crux:

> **Shallow copy** — `dict.copy()`, `list.copy()`, `copy.copy(x)` — creates a new
> *outer* container, but its elements are the **same objects** as the original's. The
> top level is independent; **nested** objects are still shared.
>
> **Deep copy** — `copy.deepcopy(x)` — recursively copies the container *and every
> object nested inside it*, all the way down. Nothing is shared.

A shallow copy fixes the `name` problem (top-level key) but **not** the `layers` problem,
because `layers` is a nested list still shared between the two dicts. That's the subtle
bug: a shallow copy *looks* like it worked until you mutate something nested.

### The move

Choose the copy depth that matches your data:

```python
import copy

# If the structure is FLAT (no nested mutable objects) -> shallow is enough:
variant = base_config.copy()          # new dict; fine if values are immutable

# If there are NESTED mutable objects you'll mutate independently -> deep:
variant = copy.deepcopy(base_config)  # fully independent clone, top to bottom
variant["layers"].append(8)           # base_config["layers"] is now UNAFFECTED
```

### Why it works

`copy.deepcopy` walks the entire object graph and reconstructs every mutable object it
finds, so the clone shares **nothing** mutable with the original — mutating the clone's
nested list cannot reach back to the original's. A **shallow** copy only duplicates the
outermost container and reuses the same inner objects, so it's correct *only* when those
inner objects are either immutable (ints, strings, tuples — which can't be mutated
anyway, 1.4) or you genuinely intend to share them.

`deepcopy` also correctly handles **shared references and cycles** inside the structure
(if the same sub-object appears twice, or A points to B which points back to A) by
remembering what it has already copied — something a hand-rolled recursive copy easily
gets wrong.

### The code, every line explained

```python
import copy

original = {"name": "base", "layers": [64, 32], "meta": {"seed": 1}}

# --- Aliasing: NOT a copy at all -----------------------------------------
alias = original                 # second NAME for the same object
alias["name"] = "x"              # mutates the one shared dict
original["name"]                 # "x"  -> they ARE the same object
alias is original                # True -> identity confirms it (1.9)

# --- Shallow copy: new outer, SHARED inner objects -----------------------
shallow = original.copy()        # or dict(original) / copy.copy(original)
shallow["name"] = "y"            # top-level key: independent now
original["name"]                 # unchanged (still "x") -> top level is separate
shallow["layers"].append(16)     # but layers is the SAME list object...
original["layers"]               # [64, 32, 16]  -> ...so original sees it too! (gotcha)
shallow["layers"] is original["layers"]   # True -> the nested list is shared

# --- Deep copy: new outer AND new inner, all the way down ----------------
deep = copy.deepcopy(original)   # recursively clones every nested object
deep["layers"].append(99)        # mutate the clone's nested list...
original["layers"]               # unchanged -> fully independent
deep["meta"]["seed"] = 42        # even deeply nested dicts are separate
original["meta"]["seed"]         # unchanged (still 1)

# --- The everyday version of this bug: shared default rows ---------------
row_template = {"hits": 0, "tags": []}
rows = [row_template.copy() for _ in range(3)]   # shallow copies...
rows[0]["tags"].append("x")      # ...but "tags" list is SHARED across all three!
rows[1]["tags"]                  # ["x"]  -> bug. Need deepcopy, or build fresh:
rows = [{"hits": 0, "tags": []} for _ in range(3)]   # fresh nested list per row (best)

# --- Slices and list() are shallow copies too ---------------------------
a = [[1, 2], [3, 4]]
b = a[:]                         # slice copy = SHALLOW (new outer list)
b.append([5])                    # adding a NEW element: a is unaffected
b[0].append(99)                  # mutating a SHARED inner list: a[0] changes too!
```

### Impact

- **Correctness:** eliminates the "I changed the copy and the original mutated" class of
  bug — among the most confusing because the code that mutates *looks* entirely local.
- **Conscious sharing:** you decide explicitly whether two structures share inner state,
  rather than discovering it by accident in production.

### Pros & cons / when NOT to

**Reach for:**
- **nothing (just reuse the reference)** when you only *read* and never mutate — copying
  is pure waste then.
- **shallow copy** when the container is flat, or its nested objects are immutable, or you
  *want* to share the inner objects.
- **`deepcopy`** when you need a truly independent clone of a nested mutable structure you
  will mutate separately.

**Watch out / when NOT to:**
- **`deepcopy` is expensive** — it allocates a full duplicate of the whole structure,
  O(total size) in time and memory. Deep-copying a huge nested object (or worse, one
  holding a giant array/DataFrame) in a hot loop is a real performance bug. Copy only
  the part you mutate, or restructure to avoid copying.
- **`deepcopy` of objects holding external resources** (open files, DB connections,
  locks, threads) is usually wrong or impossible — those can't be meaningfully cloned.
  Classes can customise `__deepcopy__` to control this.
- **Prefer immutability where you can:** if data never changes after creation (use a
  `tuple`, `frozenset`, or a frozen dataclass), aliasing is *safe* and you need no copies
  at all — the cleanest fix is often to not mutate in the first place.

### Where this shows up

- **Real work — config variants & experiments:** cloning a base config/hyperparameter
  dict per run — exactly the example — where a shallow copy silently links experiments.
- **Real work — default record templates:** the "shared nested list across rows" bug when
  seeding records/accumulators (close cousin of the mutable-default trap, 1.4).
- **Real work — protecting inputs:** a function that must not mutate its caller's data
  deep-copies the parts it modifies (ties to "validate/copy at the boundary", Area 7).
- **Pattern mapping (secondary):** backtracking problems must copy the partial solution
  before recursing (`path[:]` or `list(path)`) — forgetting it (appending to a shared
  list) is the classic bug that returns N references to the same final list.
[↑ Back to top](#contents)

---

<a id="2.7"></a>
## 2.7 — "Loading the whole thing to use a bit" → lazy evaluation & generators

### The situation

You want the **first 5 valid records** from a 20-GB log file — just to eyeball the
schema. You reach for the helper that already exists:

```python
def load_all(path):
    rows = []
    for line in open(path):          # read every one of ~200 million lines
        rec = parse(line)
        if rec is not None:          # keep only the valid ones
            rows.append(rec)
    return rows                      # returns a list of ALL valid records

first_five = load_all("events.log")[:5]   # ...then throw away all but 5
```

To get 5 records you parsed 200 million lines and built a multi-gigabyte list in RAM —
then sliced off 5 and discarded the rest. The job takes minutes (or OOM-kills) to
produce something you could have had in milliseconds.

### What's really going on

You're being **eager** when you could be **lazy**. *Eager* evaluation computes the
entire result up front; *lazy* evaluation computes each item **only when it's asked
for**, and not a moment sooner. Because you only consume 5 items, an eager `load_all`
does ~200 million × (read + parse) units of pointless work and holds the whole result
in memory.

This is the same machinery as generators in **Area 1's 1.2** — here viewed through the
*performance* lens: laziness changes both **how much work runs** (you stop after 5
items) and **how much memory is held** (one item at a time, O(1), not O(n)). The chain
of operations — read → parse → filter → take 5 — can flow through a **pipeline** where
each stage pulls one item from the previous and pushes it to the next, so nothing is
ever fully materialised.

### The move

Make the producer a **generator** (`yield` per item), then use a lazy "take first N"
instead of slicing a full list:

```python
def load_lazy(path):
    for line in open(path):          # open() is itself lazy — reads line by line
        rec = parse(line)
        if rec is not None:
            yield rec                # hand out ONE valid record, then pause

from itertools import islice
first_five = list(islice(load_lazy("events.log"), 5))   # pull exactly 5, then STOP
```

`load_lazy` parses lines only until 5 valid records have been yielded — then `islice`
stops pulling and the file is abandoned. You read maybe a few dozen lines, not 200
million.

### Why it works

A generator produces values **on demand**: `islice(gen, 5)` requests items one at a
time and stops after the fifth, so the generator's loop never runs past the line that
yields record #5. The expensive read+parse work for the other ~200 million lines
**never happens** — that's the time saving. And because only one record exists at a
time (the generator pauses between yields), memory stays flat regardless of file size —
that's the memory saving. Laziness turns "compute everything, use a bit" into "compute
exactly what's used."

### The code, every line explained

```python
from itertools import islice

# --- Eager: compute ALL, then take a few (wasteful) ----------------------
def load_all(path):
    rows = []
    for line in open(path):
        rec = parse(line)
        if rec is not None:
            rows.append(rec)         # build the entire list in memory
    return rows
first5 = load_all("events.log")[:5]  # parsed millions, kept 5. O(n) time AND memory.

# --- Lazy: a generator yields on demand ----------------------------------
def load_lazy(path):
    for line in open(path):          # lazy line reads (file isn't slurped whole)
        rec = parse(line)
        if rec is not None:
            yield rec                # produce one, pause; resume on next request

# islice(iterable, n) = a lazy "take the first n", the streaming form of [:n]
first5 = list(islice(load_lazy("events.log"), 5))   # pulls 5 items, then stops the gen

# --- Lazy PIPELINE: stages chained, each O(1) memory ---------------------
lines   = open("events.log")                         # stage 1: lazy lines
parsed  = (parse(line) for line in lines)            # stage 2: lazy parse (gen expr, 1.2)
valid   = (r for r in parsed if r is not None)       # stage 3: lazy filter
batched = islice(valid, 5)                           # stage 4: lazy take-5
result  = list(batched)              # ONLY here does anything actually run — pulling
#                                      5 items drags exactly enough work through stages.
# Nothing between stage 1 and 4 builds a list; data flows one item at a time.

# --- any()/next() also stop early on a lazy source -----------------------
has_error = any(r.level == "ERROR" for r in load_lazy("events.log"))
# any() short-circuits: it stops at the FIRST error and never reads the rest.
first_error = next((r for r in load_lazy("events.log") if r.level == "ERROR"), None)
# next(gen, default) pulls just one matching item then stops; default if none found.

# --- Be deliberate: when you DO need it all, materialise once ------------
all_rows = list(load_lazy("events.log"))   # explicit: "yes, I want the whole list"
```

### Impact

- **Work avoided:** with early termination (`islice`, `any`, `next`), you do **only as
  much computation as the consumer demands** — milliseconds instead of minutes when you
  need a prefix or a first match.
- **Memory:** O(n) → O(1) for the streamed portion — no giant intermediate list, so
  files larger than RAM are processable (ties to chunked I/O, 2.13).
- **Latency to first item:** the lazy version yields item #1 immediately; the eager one
  makes you wait for all n before anything is usable.

### Pros & cons / when NOT to

**Reach for laziness when:** you consume a sequence **once, in order**; you only need a
**prefix / first match / aggregate**; the data is **large/streaming**; or you're
chaining transform stages (a pipeline).

**Watch out / when NOT to:**
- **Single-use:** a generator is exhausted after one pass — looping again yields nothing.
  Need multiple passes or random access (`len`, `gen[i]`)? Materialise with `list(...)`
  and accept the memory (same caveat as 1.2).
- **You genuinely need the whole result anyway** (e.g. you must sort it, which requires
  all items) — laziness saves nothing then; be explicit with `list(...)`.
- **Side effects run late:** because the body only executes as you consume, an `open()`
  or DB call inside a generator happens *later* than the line suggests — don't rely on it
  having run until you've drained it.
- **Tiny data looped many times:** a plain list is simpler; don't add laziness you won't
  benefit from.

### Where this shows up

- **Real work — sampling/inspecting big data:** grab the first N rows of a huge
  file/query to check schema without loading it — the exact scenario.
- **Real work — ETL pipelines:** read → clean → filter → batch as chained generators so a
  file bigger than RAM streams through with flat memory.
- **Real work — training data loaders:** stream and transform batches on demand instead
  of preloading the dataset (every `DataLoader`/`tf.data` is this idea).
- **Pattern mapping (secondary):** "find the first element satisfying P" and "does any
  element satisfy P" are short-circuit scans — `next(...)`/`any(...)` over a generator is
  the idiomatic O(1)-extra-memory, early-exit form.
[↑ Back to top](#contents)

---

<a id="2.8"></a>
## 2.8 — "Same pure computation repeated" → precompute & lookup tables

### The situation

You're labelling a stream of 5,000,000 events. Each event has an integer severity 0–10,
and you must map it to a category and a colour using a rule that involves a small but
non-trivial computation:

```python
def classify(severity):              # called 5,000,000 times
    if severity <= 2:
        return ("low", "#2ecc71")
    elif severity <= 6:
        return ("medium", "#f39c12")
    else:
        return ("high", "#e74c3c")

labels = [classify(e.severity) for e in events]   # 5M calls
```

`classify` is cheap individually, but there are only **11 possible inputs** (severities
0 through 10), and you're recomputing the answer for the same handful of inputs five
million times. The function call overhead alone, times 5 million, is the cost — not the
logic.

### What's really going on

The computation is **pure** (output depends only on the input) and the **input domain
is small and known**. That means there are only 11 distinct answers in the entire run,
yet you compute them millions of times. The fix is to compute each distinct answer
**once**, store it in a fast structure keyed by the input, and thereafter **look it up**
instead of recomputing.

This is a **lookup table** (or **precomputed table**): trade a little memory (store the
answers) to eliminate repeated work (a dict/list index is a single O(1) operation, far
cheaper than re-running the function body and paying Python's per-call overhead).

> It's the cousin of memoisation (1.13's `lru_cache`): both cache results of a pure
> function. The distinction: **precompute** builds the whole table *up front* because the
> input domain is small and fully known; **memoise** fills the cache *lazily* as inputs
> arrive, for a large or unknown domain. Same principle — "compute once, reuse" — applied
> when you can enumerate every input vs when you can't.

### The move

Build the table once for all possible inputs, then index into it in the hot loop:

```python
# Precompute every answer ONCE (11 entries):
TABLE = {s: classify(s) for s in range(11)}   # {0:("low",...), 1:..., ..., 10:...}

labels = [TABLE[e.severity] for e in events]  # 5M dict lookups, ZERO recomputation
```

The hot loop now does a dict lookup per event instead of running `classify`'s branches
and absorbing a function call each time.

### Why it works

A dict lookup (or list index) is a single, highly-optimised O(1) operation — compute a
hash, jump to the slot — with none of the overhead of a Python function call (building a
stack frame, evaluating branches, returning). By moving the actual computation out of
the hot path and into a one-time table build, you pay the `classify` cost exactly 11
times total instead of 5,000,000 times. When the input is a small **integer range**, a
plain **list** indexed by the value is even faster than a dict (direct array offset, no
hashing): `TABLE[severity]` where `TABLE` is a list of 11 entries.

### The code, every line explained

```python
# --- The repeated pure computation (called millions of times) ------------
def classify(severity):
    if severity <= 2:   return ("low", "#2ecc71")
    elif severity <= 6: return ("medium", "#f39c12")
    else:               return ("high", "#e74c3c")

# --- Precompute a dict table: one entry per possible input ---------------
TABLE = {s: classify(s) for s in range(11)}   # build ONCE (11 calls total)
labels = [TABLE[e.severity] for e in events]  # hot loop: pure O(1) lookups

# --- Even faster for a small INTEGER domain: a list indexed by value -----
TABLE_LIST = [classify(s) for s in range(11)] # index i holds the answer for severity i
labels = [TABLE_LIST[e.severity] for e in events]
# TABLE_LIST[7] is a direct array offset — no hashing — fastest when keys are
# a dense 0..k integer range. Use a dict when keys are sparse or non-integer.

# --- Precompute a derived column you'll reuse across the program ---------
import math
LOG_LOOKUP = [math.log1p(i) for i in range(1000)]   # log(1+i) for counts 0..999
# Anywhere you'd call math.log1p(count) for small counts, index instead:
feat = LOG_LOOKUP[count] if count < 1000 else math.log1p(count)  # fallback for big

# --- The "hoist invariant work out of the loop" sibling pattern ----------
# If something inside a loop doesn't depend on the loop variable, compute it ONCE:
factor = expensive_constant()        # was being recomputed every iteration...
out = [x * factor for x in data]     # ...now computed once, reused n times.
# (This is the same bug class as the per-row config re-parse in 2.1.)
```

### Impact

- **Work eliminated:** the pure computation runs |domain| times instead of n times — for
  11 distinct inputs over 5M events, that's 11 computations instead of 5,000,000, the
  rest being cheap lookups.
- **Removes per-call overhead:** replacing a function call with a dict/list index in the
  hot loop is a real speed-up even when the function body is trivial, because Python
  function calls aren't free.
- **Memory cost is tiny and bounded:** the table is sized by the input domain (11
  entries here), not by n.

### Pros & cons / when NOT to

**Reach for precompute/lookup tables when:** a **pure** function with a **small, known
input domain** is called many times; or any invariant value is recomputed inside a loop
(hoist it out).

**Watch out / when NOT to:**
- **Large or unbounded input domain:** you can't precompute a table for every possible
  64-bit input. Use **memoisation** (`lru_cache`, 1.13/2.14) to cache lazily, or just
  accept the computation if it's genuinely cheap.
- **Impure functions:** if the result depends on time, randomness, external state, or
  mutable arguments, a cached table returns stale/wrong answers. Only cache pure
  computations (see 2.14 for invalidation).
- **The computation is already trivial AND called rarely:** a lookup table adds a layer
  for no measurable gain — profile (2.1) first; don't table-ify cold code.
- **Floats as keys:** be wary — floating-point values rarely repeat exactly, so a table
  keyed by raw floats gets few hits. Bucket/round them first if you must.

### Where this shows up

- **Real work — feature encoding:** mapping a small set of category codes / severity
  levels / status strings to vectors or labels via a precomputed dict, applied across
  millions of rows.
- **Real work — expensive transforms on a small domain:** precomputing `log`/`sqrt`/gamma
  values for a bounded integer range used repeatedly in scoring.
- **Real work — hoisting setup out of loops:** computing a normalisation constant, a
  compiled regex (Area 4), or a loaded config once before iterating — the everyday
  "stop redoing constant work" fix from 2.1.
- **Pattern mapping (secondary):** precomputed tables are the heart of many DP/counting
  problems — e.g. precomputing factorials/prefix sums (Area 11) so each query is O(1)
  instead of recomputed.
[↑ Back to top](#contents)

---

<a id="2.9"></a>
## 2.9 — "Dict/set lookups vs scanning a list" → choosing O(1) structures

### The situation

You're joining two datasets: for each of 1,000,000 order records you need the customer's
details, which live in a list of 100,000 customer records. You look each one up by id:

```python
customers = [...]                    # 100,000 dicts: {"id": ..., "name": ..., ...}
orders = [...]                       # 1,000,000 orders, each with a customer_id

def find_customer(cid):
    for c in customers:              # scan the list looking for a matching id
        if c["id"] == cid:
            return c
    return None

enriched = [(o, find_customer(o["customer_id"])) for o in orders]   # 1M lookups
```

It works on a sample and grinds to a halt on the real data. The benchmark tells the
story: scanning a 100,000-element list for membership is ~1 second per ~2,000 lookups
in one measurement here; doing it a million times is hopeless. Switching to a dict made
the same lookups roughly **3,000× faster** in that test.

### What's really going on

The data structure you pick *is* the algorithm. Each operation has a different cost
depending on the structure:

> - **list** — ordered, indexable by position. `lst[i]` is O(1), but **searching** by
>   value (`x in lst`, `lst.index(x)`, find-by-field) is **O(n)** — it scans.
> - **set** — unordered collection of unique items. **Membership** (`x in s`) is **O(1)**
>   average (hash lookup), but no positions, no duplicates.
> - **dict** — maps keys to values. **Lookup/insert/delete by key** is **O(1)** average
>   (hash lookup), and it preserves insertion order (Python 3.7+).

`find_customer` does an O(n) list scan, repeated 1,000,000 times → O(n × m) ≈ 100
billion comparisons (the same nested-loop blow-up as 2.2). The realisation: you're
**looking things up by a key**, so the right structure is the one built for
key-lookup — a **dict** — which turns each O(n) scan into an O(1) hit.

### The move

Build a dict **index** keyed by the lookup field once (O(m)), then every lookup is O(1):

```python
by_id = {c["id"]: c for c in customers}        # one O(m) pass to build the index
enriched = [(o, by_id.get(o["customer_id"])) for o in orders]   # each lookup O(1)
```

`by_id.get(cid)` returns the customer or `None` if absent — no scan, no `find_customer`.

### Why it works

A dict (and set) stores entries in a **hash table**: it computes a hash of the key and
uses it to jump almost directly to the bucket holding that key, so lookup time barely
changes whether the dict holds 100 or 100 million keys — O(1) average. Building the
index is a single O(m) pass; the n lookups are then n × O(1) = O(n). Total drops from
O(n × m) to O(n + m). The list never knew *how* you'd search it, so it could only
offer a linear scan; the dict is *designed* around key lookup.

### The code, every line explained

```python
# --- The trap: repeated linear scan of a list ---------------------------
def find_customer(cid):
    for c in customers:              # O(n) scan per call...
        if c["id"] == cid:
            return c
    return None
enriched = [(o, find_customer(o["customer_id"])) for o in orders]  # ...x 1M = O(n*m)

# --- The fix: build a dict index once, then O(1) lookups ----------------
by_id = {c["id"]: c for c in customers}        # dict comprehension (1.1): O(m) build
enriched = [(o, by_id.get(o["customer_id"]))   # .get -> value or None, no scan
            for o in orders]                   # total now O(n + m)

# --- set: when you only need "is it present?" (no associated value) -----
known_ids = {c["id"] for c in customers}       # set comprehension -> O(1) membership
new_orders = [o for o in orders                # which orders reference a KNOWN customer?
              if o["customer_id"] in known_ids]   # `in` on a set is O(1) (vs O(n) list)

# --- Choosing the structure by the operation you do MOST ----------------
#   "look up a value BY a key"        -> dict      (by_id[k])
#   "is this item present / unique?"  -> set       (x in s, dedupe)
#   "ordered, access by position,
#    iterate in order, small/append"  -> list      (lst[i], lst.append)
#   "fast add/remove at BOTH ends"    -> collections.deque (O(1) popleft; list is O(n))

# --- deque: the right queue (vs list.pop(0) which is O(n), see 2.2) -----
from collections import deque
q = deque(initial_items)             # double-ended queue
q.append(x)                          # O(1) push right
q.popleft()                          # O(1) pop left  (list.pop(0) would be O(n))

# --- The cost of the win: extra memory for the index --------------------
# by_id duplicates references to the m customers and the hash table overhead:
# O(m) extra memory bought O(n) time. Almost always worth it; see when-not-to.
```

### Impact

- **Asymptotic win:** O(n × m) → O(n + m). On this data, a job that was effectively
  frozen finishes in a fraction of a second — measured ~3,000× faster for the lookups.
- **Scales gracefully:** dict/set lookup stays ~constant as the data grows, so the fix
  keeps paying off as datasets get bigger (unlike micro-optimising the scan).
- **Clearer intent:** `by_id[k]` says "look up by id"; a scan loop hides that intent.

### Pros & cons / when NOT to

**Reach for a dict/set when:** you look things up by key or test membership more than a
couple of times — the moment a lookup happens inside a loop, index it.

**Watch out / when NOT to:**
- **Memory cost:** the index is O(m) extra memory plus hash-table overhead. Fine almost
  always; matters only when m is enormous and memory is tight (then consider a database,
  on-disk index, or processing in sorted order).
- **One-shot lookup:** if you search the list **once**, building a dict first is wasted
  work — a single scan is fine. The index pays off through *repeated* lookups.
- **Keys must be hashable:** dict keys and set elements must be immutable/hashable
  (numbers, strings, tuples — not lists or dicts). Use a tuple as a composite key
  (`(user_id, date)`) when you key by multiple fields.
- **Order/duplicates:** sets drop both; if you need positions or duplicates, use a list
  (optionally *plus* a companion set/dict for fast lookup).

### Where this shows up

- **Real work — dict joins:** matching two datasets on a key (orders↔customers,
  predictions↔labels) — the canonical "index one side, stream the other" pattern
  (data-wrangling area).
- **Real work — deduplication & membership:** "have I seen this id/hash before?" across
  millions of records is a `set` (ties to 2.2 and the dedup scenario).
- **Real work — counting & grouping:** `collections.Counter` (a dict) for frequencies and
  `defaultdict(list)` for grouping records by a field — O(1) per update vs scanning.
- **Pattern mapping (secondary):** "arrays + hashing" (two-sum, group-anagrams, dedup) is
  precisely this — replace an O(n²) scan with an O(1) hash lookup; `deque` underlies BFS
  and sliding-window problems where you push/pop both ends.
[↑ Back to top](#contents)

---

<a id="2.10"></a>
## 2.10 — "Memory keeps climbing in a long run" → reference cycles & leaks

### The situation

You have a long-running service that processes documents one at a time, indefinitely.
It should use roughly constant memory — one document in flight at a time. But over
hours, its memory creeps up: 300 MB, then 600 MB, then 1.2 GB, until it's killed and
restarted. Each individual document is small; nothing *should* accumulate. Yet RSS
(resident set size — the actual RAM the process holds) only ever goes up.

A common shape behind it:

```python
_cache = {}                          # module-level dict, never trimmed

def handle(doc):
    result = expensive_process(doc)
    _cache[doc.id] = result          # grows forever — every doc adds an entry
    log_entries.append(make_log(doc))    # another unbounded list
    return result
```

Or a subtler one: objects that point at each other and never get freed even after you
drop all your references to them.

### What's really going on

In Python you don't free memory manually; the **garbage collector (GC)** does. The
primary mechanism is **reference counting**: every object tracks how many references
point to it, and the instant that count hits zero, the object is freed immediately. A
"leak" in Python is therefore almost always **unintentional retention** — something is
still holding a reference, so the count never reaches zero. Two main culprits:

1. **Unbounded containers.** A module-level dict/list/set that you only ever *add* to —
   a cache, a log buffer, a "seen" set — grows without limit. It's not a bug in Python;
   you're holding every item on purpose, just never releasing them.

2. **Reference cycles.** Two objects that reference each other (A.child = B; B.parent =
   A), or any loop of references, keep each other's count above zero **even after you
   drop all outside references**. Reference counting alone can't reclaim a cycle (each
   still "sees" the other). Python has a *separate* cyclic GC that periodically finds and
   frees such cycles — but it runs intermittently, and objects with certain
   characteristics, or those referenced from a still-live cache, can linger.

> **`tracemalloc`** (standard library) is the tool that pins this down: it records where
> every allocation happened, so you can snapshot memory over time and see *which lines*
> are responsible for the growth.

### The move

Find the growth with `tracemalloc`, then bound it: cap caches, drop references you don't
need, and break cycles (or use **weak references** that don't keep objects alive):

```python
import tracemalloc
tracemalloc.start()
snap1 = tracemalloc.take_snapshot()
# ... run a chunk of work ...
snap2 = tracemalloc.take_snapshot()
for stat in snap2.compare_to(snap1, "lineno")[:10]:   # top 10 growth sites
    print(stat)                                        # points at the leaking line
```

Then fix the source — e.g. replace the unbounded `_cache` with a size-bounded one:

```python
from functools import lru_cache
@lru_cache(maxsize=10_000)           # bounded: evicts least-recently-used past 10k
def expensive_process(doc_id): ...
```

### Why it works

`tracemalloc` attributes live memory to the exact source line that allocated it, and
`compare_to` shows what *grew* between two snapshots — turning "memory climbs" from a
mystery into a specific line you can fix (the profiling discipline of 2.1, applied to
memory). Once you know the source: bounding a cache (`lru_cache(maxsize=...)` or an
explicit eviction policy) caps retention so old entries are freed; dropping references
(`del`, reassigning, or scoping work in a function so locals vanish on return) lets the
reference count hit zero; and for cycles, either break the link explicitly or use
`weakref` — a reference that lets you reach an object *without* incrementing its count,
so it can still be collected when nothing else holds it.

### The code, every line explained

```python
import tracemalloc

# --- Diagnose: snapshot, run work, snapshot, diff ------------------------
tracemalloc.start()                      # begin recording allocation sites
snap1 = tracemalloc.take_snapshot()      # baseline
for doc in batch:                        # do a representative chunk of work
    handle(doc)
snap2 = tracemalloc.take_snapshot()      # after
top = snap2.compare_to(snap1, "lineno")  # what grew, per source line
for stat in top[:10]:
    print(stat)                          # e.g. "handler.py:7: size=812 MiB ... +812 MiB"
#                                          -> the unbounded _cache line is the culprit

# --- Fix 1: BOUND an unbounded cache -------------------------------------
# Before: _cache = {}; _cache[k] = v   -> grows forever
from functools import lru_cache
@lru_cache(maxsize=10_000)               # keeps at most 10k entries; evicts LRU (2.14)
def expensive_process(doc_id):
    ...

# --- Fix 2: DROP references you no longer need ---------------------------
def handle(doc):
    result = expensive_process(doc.id)
    write_out(result)
    return result
# `result` is a LOCAL: when handle returns, its refcount drops to 0 and it's freed
# immediately. Keeping results in a module-level list instead = the leak.

# --- Fix 3: BREAK reference cycles, or use weakref -----------------------
import weakref
class Node:
    def __init__(self):
        self.children = []
        self._parent = None
    def add(self, child):
        self.children.append(child)
        child._parent = weakref.ref(self)   # weak ref: does NOT keep parent alive.
        # If this were `child._parent = self`, parent<->child form a CYCLE that
        # plain refcounting can't free; weakref breaks it. child._parent() to deref.

# --- Force a cyclic collection / inspect the GC (diagnostic) -------------
import gc
gc.collect()                             # run the cyclic collector now (rarely needed)
print(len(gc.garbage))                   # objects the GC couldn't free -> investigate
```

### Impact

- **Bounded memory:** a long-running process stays flat instead of climbing to an OOM
  kill — the difference between a service that runs for weeks and one that restarts
  hourly.
- **Pinpointed fixes:** `tracemalloc` turns "it leaks somewhere" into "line 7 holds 812
  MiB", so you fix the actual cause rather than sprinkling `gc.collect()` hopefully.

### Pros & cons / when NOT to

**Reach for this when:** memory grows over a long run, in a service/daemon/loop that
should be steady-state, or after adding a cache/buffer.

**Watch out / when NOT to:**
- **`gc.collect()` is not a fix.** Manually calling the collector treats the symptom; if
  something still references the data, it won't be freed regardless. Find and remove the
  retaining reference instead. Disabling the GC (`gc.disable()`) is an expert tactic for
  specific latency reasons, not a memory fix.
- **`tracemalloc` adds overhead** — it records every allocation, so don't leave it on in
  production hot paths; use it to *diagnose*, then turn it off.
- **Not every climb is a leak.** Caches and buffers that grow *to a bounded plateau* are
  fine; large transient spikes during a batch then released are normal. Distinguish
  "grows forever" (leak) from "grows then levels off" (working set).
- **Closures and exception tracebacks retain references** too — a captured variable or a
  stored exception (`exc.__traceback__`) can keep large objects alive longer than
  expected. Watch for those when a fix isn't obvious.

### Where this shows up

- **Real work — long-running services/daemons:** inference servers, queue consumers, ETL
  workers that must hold steady memory for days — the headline scenario.
- **Real work — accidental accumulation:** appending every result/log/metric to a
  module-level list "for later", or a never-trimmed memoisation dict (2.14).
- **Real work — graph/tree structures with back-pointers:** parent↔child cycles in parse
  trees or object graphs that linger; `weakref` for the back-pointer is the standard fix.
- **Pattern mapping (secondary):** no direct algorithm analogue, but it mirrors the
  resource-lifetime discipline of context managers (1.3) — every retained reference, like
  every acquired resource, must have a point where it's released.
[↑ Back to top](#contents)

---

<a id="2.11"></a>
## 2.11 — "Numbers stored as Python objects are huge" → array / memoryview / numpy

### The situation

You load 10,000,000 sensor readings as a plain Python list of floats to compute some
statistics:

```python
readings = [19.4, 19.5, 19.6, ...]   # 10,000,000 floats in a Python list
```

You expected ~80 MB (10M × 8 bytes, the size of a double-precision float). Instead the
process uses close to **400 MB** just for this one list. The numbers are tiny; the
*container* is enormous.

### What's really going on

In a Python list, **every element is a full Python object**, not a raw number. A single
Python `float` object costs ~24–32 bytes (it carries a type pointer and a reference
count on top of the 8-byte value), and the list also stores an **8-byte pointer** to
each of those objects. So each "8-byte number" actually costs ~32 (the object) + ~8
(the pointer) ≈ 40 bytes — five times the raw data. You can see the per-object cost:

```python
import sys
sys.getsizeof(1000)        # 28 bytes for ONE small int object (the value is ~8)
```

The realisation: a Python list is a **container of boxed objects** — flexible (it can
hold ints, strings, anything, mixed) but heavy. When your data is **homogeneous numbers**,
you don't need boxing; you want them packed **contiguously** as raw machine values, like
a C array. Three tools give you that, in increasing power:

> - **`array.array`** (stdlib) — a list-like sequence that stores raw numbers of one
>   fixed type (e.g. 4-byte int, 8-byte float) packed together. No per-element objects.
> - **`memoryview`** (stdlib) — a *view* into another object's raw bytes, so you can
>   slice/read large binary buffers **without copying** them.
> - **NumPy `ndarray`** — the standard for numeric work: packed, typed, contiguous, *and*
>   with fast vectorised operations (the subject of 2.12). For real numeric work this is
>   almost always the answer.

### The move

Store homogeneous numbers in a typed, packed structure instead of a list of objects:

```python
import numpy as np
readings = np.array([19.4, 19.5, ...], dtype="float64")   # contiguous 8-byte doubles
# ~80 MB for 10M float64 — just the raw data, no per-element Python objects.

# Stdlib-only alternative when you can't depend on numpy:
import array
readings = array.array("d", [19.4, 19.5, ...])            # "d" = C double (8 bytes)
```

### Why it works

`array.array` and NumPy store the numbers as **raw C values laid out back-to-back in one
block of memory** — no per-element Python object, no per-element pointer. 10M float64
values occupy exactly 10M × 8 = 80 MB plus a tiny fixed header, versus ~400 MB for the
list of boxed floats. The packing also makes them **cache-friendly** (the CPU reads
contiguous memory fast) and is the precondition for vectorised operations (2.12).
`memoryview` goes further: it lets you read or slice an existing buffer (a file's bytes,
another array) *as numbers* without allocating a copy at all — O(1) slicing of gigabytes.

### The code, every line explained

```python
import sys, array
import numpy as np

# --- The cost of boxing: a list of float OBJECTS ------------------------
lst = [float(i) for i in range(1_000_000)]
sys.getsizeof(lst)                 # ~8.4 MB for the list's POINTER array alone...
sys.getsizeof(lst[0])              # ...+ ~24 bytes for EACH float object it points to
# Total real cost ~ 40 MB for 1M floats. The numbers are 8 MB; the rest is overhead.

# --- array.array: packed raw numbers, one fixed type (stdlib) -----------
arr = array.array("d", range(1_000_000))   # "d"=double(8B). Type codes: i=int32,
#                                             q=int64, f=float32, d=float64, b=int8
sys.getsizeof(arr)                 # ~8 MB — just the raw doubles, no per-item objects
arr[5]                             # indexing returns a normal Python float on demand
arr.append(3.14)                   # list-like API, but all elements must be type "d"

# --- numpy: packed, typed, AND fast (the usual choice) ------------------
a = np.array(range(1_000_000), dtype="float64")   # contiguous 8-byte doubles
a.nbytes                           # 8000000 -> exact raw size, no boxing
a32 = a.astype("float32")          # half the memory if 32-bit precision is enough
a32.nbytes                         # 4000000 -> picking the right dtype is a real lever

# --- memoryview: slice a big buffer WITHOUT copying ----------------------
buf = bytearray(10_000_000)        # 10 MB raw buffer
mv = memoryview(buf)               # a view, not a copy
chunk = mv[1_000_000:2_000_000]    # slicing a memoryview is O(1) — shares the bytes,
#                                    allocates nothing. (Slicing bytes/bytearray COPIES.)
mv[0:4] = b"\x01\x02\x03\x04"      # can write through the view into the underlying buf

# --- Picking dtype is itself an optimisation -----------------------------
# Ages 0-120 -> int8 (1 byte) not int64 (8 bytes): 8x smaller.
ages = np.array([34, 51, 29], dtype="int8")
# But beware OVERFLOW: int8 holds -128..127; the wrong dtype silently wraps around.
```

### Impact

- **Memory:** ~4–5x smaller than a list of boxed numbers (and choosing a narrower dtype —
  float32 over float64, int8 over int64 — multiplies the saving again), turning
  doesn't-fit-in-RAM into fits-comfortably.
- **Speed:** contiguous memory is cache-friendly and unlocks vectorised C operations
  (2.12), which are orders of magnitude faster than Python-level loops.
- **Zero-copy slicing:** `memoryview` processes slices of huge buffers without
  duplicating them — important for large binary/I/O data (2.13).

### Pros & cons / when NOT to

**Reach for arrays/numpy when:** you hold **many homogeneous numbers** and care about
memory or speed — feature matrices, embeddings, signals, image/audio buffers, counters.

**Watch out / when NOT to:**
- **Heterogeneous or non-numeric data** (mixed types, strings, nested objects) doesn't
  fit a typed array — a list, dict, or DataFrame is the right tool. Arrays are for
  uniform numbers.
- **Small data:** for a few hundred numbers the overhead is irrelevant; a list is simpler
  and the saving is noise. Don't add numpy as a dependency for trivial sizes.
- **dtype overflow/precision is a real hazard:** narrow integer types wrap around silently
  on overflow, and float32 loses precision versus float64. Choose dtype deliberately and
  know the value range.
- **`array.array` lacks the maths:** it saves memory but has no vectorised operations —
  for actual computation reach for numpy. Use `array.array` only when you must stay
  stdlib-only.

### Where this shows up

- **Real work — feature matrices & embeddings:** storing millions of float vectors as a
  numpy array (float32) instead of lists-of-lists — the everyday ML memory win.
- **Real work — large numeric columns:** counts, timestamps-as-ints, sensor signals held
  as typed arrays rather than object lists.
- **Real work — binary I/O & zero-copy:** reading a large binary file into a buffer and
  slicing it with `memoryview` to avoid copying gigabytes (ties to 2.13).
- **Pattern mapping (secondary):** the packed-array idea underlies bit manipulation and
  counting-array techniques (e.g. a fixed-size count array indexed by value) where a
  dense numeric buffer beats a dict of objects.
[↑ Back to top](#contents)

---

<a id="2.12"></a>
## 2.12 — "Looping in Python over arrays is slow" → vectorise the hot path

### The situation

You have 1,000,000 raw feature values and need to apply a simple transform — multiply by
2 and add 1 — as part of preprocessing. You write the natural Python loop:

```python
import numpy as np
a = np.arange(1_000_000, dtype="float64")

out = []
for x in a:                          # loop in Python over a million elements
    out.append(x * 2.0 + 1.0)        # do the arithmetic one element at a time
```

It's correct but slow. Replacing the loop with a single vectorised expression made the
same computation roughly **95× faster** in a measurement here — and the code shrank to
one line.

### What's really going on

Even when your data is packed in a numpy array (2.11), **iterating it in a Python `for`
loop throws away the advantage**. Each iteration pays Python's per-element overhead: the
interpreter unboxes the numpy value into a Python `float` object, runs the bytecode for
the arithmetic, re-boxes the result, and appends it — interpreted, one element at a
time. A million elements means a million rounds of that overhead.

**Vectorisation** means expressing the operation on the **whole array at once**
(`a * 2.0 + 1.0`) so it runs inside numpy's **compiled C code** — a tight loop over
contiguous memory with no per-element Python overhead, often using the CPU's SIMD
instructions (Single Instruction, Multiple Data — one instruction processing several
numbers in parallel). The realisation: the slow part isn't the arithmetic, it's *doing
it from Python per element*. Push the loop down into C by operating on the array as a
unit.

### The move

Replace the element-by-element loop with a **whole-array expression**:

```python
out = a * 2.0 + 1.0                  # one vectorised operation over all 1M elements
```

For conditional logic, use **boolean masks** and `np.where` instead of `if` inside a
loop:

```python
clipped = np.where(a > 100, 100, a)  # element-wise: where a>100 use 100, else a
```

### Why it works

`a * 2.0 + 1.0` dispatches **once** into numpy, which runs a compiled C loop over the
array's contiguous memory: no per-element unboxing, no bytecode interpretation, no
`.append`. The arithmetic happens at native speed, frequently vectorised across multiple
values per CPU instruction. The result is a new array allocated in one block. Because the
data is already packed (2.11) and the operation is uniform, the whole thing is a single
fast pass — turning a million interpreted iterations into one compiled sweep.

### The code, every line explained

```python
import numpy as np
a = np.arange(1_000_000, dtype="float64")

# --- Slow: Python-level loop (per-element interpreter overhead) ----------
out = []
for x in a:
    out.append(x * 2.0 + 1.0)        # unbox -> compute -> rebox -> append, x1,000,000

# --- Fast: vectorised — one operation over the whole array ---------------
out = a * 2.0 + 1.0                  # numpy runs a compiled C loop; ~95x faster here
# Reads as the maths itself; no loop, no accumulator.

# --- Conditionals: boolean MASKS instead of if-in-a-loop -----------------
mask = a > 100                       # a boolean array: True where the condition holds
big = a[mask]                        # select only elements where mask is True (no loop)
a[mask] = 100                        # assign to just those elements (clip in place)
clipped = np.where(a > 100, 100, a)  # vectorised if/else: 100 where >100, else original

# --- Aggregations are vectorised too -------------------------------------
a.sum(); a.mean(); a.max(); a.std()  # whole-array reductions in C, not a Python loop

# --- Combine arrays element-wise (must be compatible shapes) -------------
b = np.ones(1_000_000)
c = a * b + 1                        # element-wise multiply then add, all in C
# Broadcasting: a (1,000,000,) * scalar, or (rows,cols) * (cols,) — numpy stretches
# the smaller shape to match without copying. (Shapes/broadcasting deep-dive: Area 9.)

# --- When there's NO vectorised form: push the loop to C another way -----
# np.vectorize is convenience, NOT speed (it still loops in Python). For genuine
# heavy custom loops, use numba @njit, Cython, or numpy ufuncs — measure (2.15).
```

### Impact

- **Speed:** commonly 10–100x faster than an equivalent Python loop (measured ~95x for
  the example), because the per-element interpreter overhead is eliminated entirely.
- **Clarity:** `a * 2.0 + 1.0` expresses intent as the mathematical operation, far
  clearer than a loop with an accumulator.
- **Memory note:** vectorised ops allocate result arrays; chaining many creates temporary
  arrays. For huge data, in-place ops (`a *= 2`) or `out=` parameters avoid the extra
  allocations.

### Pros & cons / when NOT to

**Reach for vectorisation when:** you apply a uniform numeric operation across a large
array/column — arithmetic, comparisons, clipping, normalisation, aggregations.

**Watch out / when NOT to:**
- **Not everything vectorises cleanly.** Logic with irregular control flow, early exits,
  or per-element dependence on previous results (true sequential recurrences) may not
  have a vectorised form. Don't contort code into unreadable masks just to avoid a loop —
  sometimes a loop (or numba) is the honest answer.
- **`np.vectorize` is a trap for speed** — it's a convenience wrapper that still loops in
  Python; it does **not** make things fast. Use real vectorised ops or a compiled tool.
- **Temporary arrays cost memory.** A long chain `((a*2)+1)*3 ...` allocates an
  intermediate array per step; on huge data use in-place operators or `np.add(a, b,
  out=a)` to reuse buffers.
- **Tiny arrays:** the dispatch overhead of a vectorised call can exceed a short Python
  loop for a handful of elements — vectorisation pays off at scale.

### Where this shows up

- **Real work — feature preprocessing:** normalising, scaling, clipping, one-hot
  arithmetic across whole columns/matrices instead of row loops (ties to 8.3 scaling).
- **Real work — pandas:** the same lesson — use vectorised column operations
  (`df["x"] * 2`) instead of `df.apply`/`iterrows` row loops (pandas thinking, Area 3).
- **Real work — embeddings/similarity:** computing dot products / norms over big matrices
  as single numpy operations rather than per-vector loops.
- **Pattern mapping (secondary):** masks and `np.where` are the array-thinking version of
  the "filter/transform" loop (1.1); reductions (`sum`, `max`) replace accumulator loops
  — the same shift from *how* to *what*, pushed down to C.
[↑ Back to top](#contents)

---

<a id="2.13"></a>
## 2.13 — "Reading a huge file spikes memory" → chunked / buffered I/O

### The situation

You need to count how many lines in a 30-GB log file contain the word "ERROR". You write
the obvious thing:

```python
with open("app.log") as f:
    contents = f.read()              # read the ENTIRE file into one string
    errors = contents.count("ERROR")
```

On a small log it's fine. On the 30-GB file, `f.read()` tries to load all 30 GB into a
single string in RAM at once — and the process either thrashes or is OOM-killed before
it counts a thing. The same happens with `f.readlines()` (builds a list of *every* line)
or `data = list(huge_iterable)`.

### What's really going on

`f.read()` is **eager**: it materialises the whole file in memory (the eager-vs-lazy
distinction from 2.7, applied to I/O). But you only need to look at a small piece at a
time — one line, or one fixed-size block — to do the counting. Holding all 30 GB
simultaneously is pure waste; peak memory should be the size of **one chunk**, not the
whole file.

The fix is **streaming**: read the file in pieces and process each piece before reading
the next, so memory stays flat (O(chunk) instead of O(file)).

> Two natural chunk shapes:
> - **Line by line** — iterating the file object (`for line in f`) yields one line at a
>   time, lazily. Perfect for text/CSV/JSONL where records are newline-delimited.
> - **Fixed-size blocks** — `f.read(size)` returns at most `size` bytes/chars per call.
>   Right for binary data, or text with no line structure, or when you want a predictable
>   memory ceiling regardless of line length.
>
> Python's file objects are also **buffered** by default: under the hood they read a
> block at a time from disk into a small buffer, so even line-by-line iteration doesn't
> do a syscall per line — you get streaming *and* efficient disk reads for free.

### The move

Iterate the file (line streaming) or loop on `f.read(size)` (block streaming) instead of
slurping it whole:

```python
# Line streaming: O(1 line) memory
errors = 0
with open("app.log") as f:           # `with` guarantees close (1.3)
    for line in f:                   # one line at a time, lazily — never loads the file
        if "ERROR" in line:
            errors += 1
```

### Why it works

Iterating a file object pulls lines on demand from a small internal buffer, so only one
line (plus the buffer) is in memory at any instant — peak memory is independent of file
size. `f.read(size)` does the same with explicit blocks. The OS and Python's buffering
mean these many small logical reads are served from memory most of the time, with actual
disk reads happening a block at a time. You process 30 GB while never holding more than a
few kilobytes — the textbook O(n) time, O(1) memory streaming pattern.

### The code, every line explained

```python
# --- The trap: read the whole file into memory --------------------------
with open("app.log") as f:
    contents = f.read()              # loads ALL 30 GB into one string -> OOM
    errors = contents.count("ERROR")

# --- Fix A: stream line by line (text/CSV/JSONL) -------------------------
errors = 0
with open("app.log") as f:           # `with`: file closed on exit, even on error (1.3)
    for line in f:                   # lazy: yields one line per iteration
        if "ERROR" in line:          # process THIS line, then it's discarded
            errors += 1
# Peak memory = one line. Works on a file far bigger than RAM.

# --- Fix B: fixed-size blocks (binary, or guaranteed memory ceiling) -----
import hashlib
h = hashlib.sha256()                 # e.g. hashing a huge file (Area 4)
with open("big.bin", "rb") as f:     # "rb" = read binary
    while chunk := f.read(1024 * 1024):   # walrus (1.18): read up to 1 MiB; loop till ""
        h.update(chunk)              # feed the block, then reuse the buffer
# read() returns b"" (falsy) at EOF -> the while loop ends. Peak memory = 1 MiB.

# --- Writing large output the same way: stream, don't buffer it all ------
with open("out.csv", "w") as f:
    for record in produce_records():     # a generator (2.7), not a giant list
        f.write(format_row(record))      # write incrementally; let buffering batch it
# Don't build one giant string then write once (that's the 2.4 problem at file scale).

# --- CSV/JSONL: stream with the right reader -----------------------------
import csv
with open("data.csv", newline="") as f:
    for row in csv.reader(f):        # csv.reader is itself a lazy iterator over rows
        process(row)                 # one row at a time, never the whole file

# --- Reading fixed-size blocks into a chunked transfer -------------------
def stream_blocks(path, size=65536): # a reusable generator of blocks (2.7)
    with open(path, "rb") as f:
        while block := f.read(size):
            yield block              # caller gets blocks lazily; memory stays flat
```

### Impact

- **Memory:** O(file) → O(chunk) — peak RAM becomes a few KB/MB regardless of whether the
  file is 30 MB or 30 TB. The difference between OOM and a job that just works.
- **Latency to first result:** streaming starts producing/counting immediately instead of
  waiting to load the whole file first.
- **Composability:** a block/line generator (2.7) feeds downstream stages, so the whole
  pipeline stays O(1) memory.

### Pros & cons / when NOT to

**Reach for streaming when:** the file is large (or unbounded/growing), or you only need
one pass over it — counting, filtering, transforming, hashing, line-delimited records.

**Watch out / when NOT to:**
- **Operations that need the whole file** (sorting all lines, random access by offset,
  parsing a format that isn't streamable like a single giant JSON object) can't be done
  one chunk at a time. Then either it must fit in memory, or you need an external/on-disk
  approach (a streaming JSON parser like `ijson`, sort via a database, or memory-map it).
- **Tiny files:** `f.read()` is simplest and fine; streaming adds nothing. Reserve it for
  data that's large or of unknown size.
- **Chunk boundaries split records:** with fixed-size *block* reads on text, a line or
  multibyte UTF-8 character can be split across two blocks — handle the boundary (keep a
  remainder) or use line iteration for text. (Encoding pitfalls: Area 3.)
- **Don't set the buffer absurdly small or large:** the default buffering is well-tuned;
  override `f.read(size)` block size only with a reason (e.g. matching a network/transfer
  unit).

### Where this shows up

- **Real work — log/data processing:** counting, filtering, or transforming multi-GB
  logs/CSVs/JSONL line by line in an ETL job — the everyday "file bigger than RAM" case.
- **Real work — hashing/checksums & uploads:** reading a large file in blocks to hash it
  or stream it to object storage without loading it whole (ties to streamed downloads,
  Area 5, and hashing, Area 4).
- **Real work — data loaders:** streaming training examples from disk in batches rather
  than preloading the dataset (2.7, Area 8/9).
- **Pattern mapping (secondary):** the "process a stream you can't fully hold" constraint
  is the streaming/online-algorithm setting — e.g. computing a running statistic or a
  top-K (heapq) in one pass without storing all elements.
[↑ Back to top](#contents)

---

<a id="2.14"></a>
## 2.14 — "Repeated work across calls" → caching layers & `lru_cache` sizing

### The situation

Your service embeds text for a similarity search. Computing an embedding calls a model
and takes ~50 ms. Many requests repeat the same text (popular queries, duplicate
documents), yet you recompute every time:

```python
def embed(text):                     # ~50 ms each: runs the model
    return model.encode(text)

# In a request handler called thousands of times/sec, with heavy repetition:
vec = embed(request.text)            # recomputes even for text seen seconds ago
```

In 1.13 you met `@lru_cache` and slapped `maxsize=None` on a function to memoise it. But
here that's dangerous: text is *unbounded and varied*, so an unbounded cache grows
forever — the exact leak from 2.10. You need caching that **bounds its memory** and you
need to think about **where** the cache lives.

### What's really going on

Caching trades memory for time: store results so repeated inputs return instantly. The
two decisions that matter are **how big** the cache may grow and **what gets evicted when
it's full** — plus, for anything beyond a single process, **where** the cache lives.

> - **`maxsize` (the size bound):** `@lru_cache(maxsize=N)` keeps at most N entries; when
>   full, it evicts the **L**east **R**ecently **U**sed entry — the one untouched
>   longest. This bounds memory at N results. `maxsize=None` means *unbounded* — only safe
>   when the input domain is genuinely small and finite (then it's really a precompute
>   table, 2.8).
> - **Cache layers (where it lives):** `lru_cache` is **in-process** — gone when the
>   process restarts, and not shared between workers/machines. For sharing across
>   processes or surviving restarts you need an *external* cache (Redis, Memcached) or an
>   on-disk cache. The pattern is the same; only the storage tier changes.

The realisation: an unbounded `maxsize=None` on a large/unknown input domain *is* a
memory leak. Pick a `maxsize` that fits your memory budget and captures the repetition;
for cross-process reuse, put the cache outside the process.

### The move

Bound the in-process cache with a sensible `maxsize`, and reach for an external cache
when reuse must cross process/restart boundaries:

```python
from functools import lru_cache

@lru_cache(maxsize=50_000)           # at most 50k embeddings cached; LRU eviction
def embed(text):
    return model.encode(text)        # runs only on a cache MISS

embed.cache_info()                   # hits/misses/currsize -> measure your hit rate
```

### Why it works

`lru_cache` keeps a dict from arguments to results plus a recency order. A **hit**
returns the stored result with zero recomputation; a **miss** runs the function, stores
the result, and — if the cache is at `maxsize` — drops the least-recently-used entry to
make room. Bounding at N means peak cache memory ≈ N × (result size), a number you can
reason about, while still serving the hot, frequently-repeated inputs (which stay
"recently used" and survive eviction). `cache_info()` lets you *measure* the hit rate so
you can size `maxsize` against real traffic rather than guessing.

### The code, every line explained

```python
from functools import lru_cache

# --- Bounded memoisation: cap size, evict least-recently-used ------------
@lru_cache(maxsize=50_000)           # memory bound = ~50k results, not infinite
def embed(text):
    return model.encode(text)        # body runs ONLY when text isn't cached

# --- Measure to size it: hit rate tells you if maxsize is right ----------
for t in sample_traffic:
    embed(t)
print(embed.cache_info())            # CacheInfo(hits=..., misses=..., maxsize=50000, currsize=...)
# High hits, currsize at maxsize -> consider raising maxsize (more memory, more hits).
# currsize << maxsize -> you over-allocated; lower it. Hits ~ 0 -> caching isn't helping.
embed.cache_clear()                  # drop everything (e.g. model/version changed)

# --- DANGER: unbounded cache on an unbounded input = a leak (2.10) -------
@lru_cache(maxsize=None)             # ONLY safe if `text` has few distinct values
def embed_bad(text):                 # with varied user text this grows without limit
    return model.encode(text)

# --- Caching needs HASHABLE, IMMUTABLE arguments -------------------------
# @lru_cache keys on the arguments, so they must be hashable:
@lru_cache(maxsize=1000)
def score(features):                 # features must be a TUPLE, not a list (lists
    ...                              # are unhashable). Convert: score(tuple(my_list))

# --- Layer 2: an EXTERNAL cache for cross-process / persistent reuse -----
# Pseudocode shape (Redis/Memcached/disk): same hit/miss logic, shared storage.
def embed_cached(text):
    key = "emb:" + hashlib.sha256(text.encode()).hexdigest()   # stable key (Area 4)
    cached = redis.get(key)
    if cached is not None:           # HIT: shared across all workers + survives restart
        return decode(cached)
    vec = model.encode(text)         # MISS
    redis.setex(key, 86400, encode(vec))      # store with a TTL (expire after 1 day)
    return vec
# TTL (time-to-live) is the external cache's eviction knob, alongside a size/memory cap.

# --- Invalidation: the hard part -----------------------------------------
# A cache returns STALE results if the underlying computation changes. Strategies:
#   - version the key:  "emb:v2:" + hash   (bump v2 when the model changes)
#   - TTL: let entries expire automatically (setex above)
#   - explicit clear:   embed.cache_clear() on a known change
```

### Impact

- **Speed:** repeated inputs return in microseconds instead of ~50 ms — on
  repetition-heavy traffic this can cut total work by the hit rate (e.g. 80% hits ≈ 5×
  fewer model calls).
- **Bounded memory:** `maxsize` caps the cache so it can't grow into the leak of 2.10,
  while LRU keeps the *useful* (hot) entries.
- **Scales across the system:** an external layer shares results across workers and
  survives restarts, multiplying the saving in a multi-process deployment.

### Pros & cons / when NOT to

**Reach for caching when:** a **pure**, expensive computation sees **repeated** inputs.
Both conditions matter — no repetition means no hits (pure overhead); impurity means
stale answers.

**Watch out / when NOT to:**
- **Impure functions:** caching anything that depends on time, randomness, or external
  mutable state returns stale/wrong results. Don't cache it (or cache with a short TTL and
  accept staleness).
- **Unbounded `maxsize=None`** on a large/unknown input domain is a leak — always bound
  it unless the domain is provably small (2.8).
- **Invalidation is genuinely hard** ("there are only two hard things… cache invalidation
  and naming"). When results *can* change, you must version keys, set TTLs, or clear
  explicitly — a stale cache is worse than no cache.
- **Cache key correctness:** the key must capture *every* input that affects the result
  (including config/version). Missing one returns the wrong cached value. Arguments must
  be hashable.
- **Low hit rate:** if inputs rarely repeat, the cache adds memory and lookup cost for no
  benefit — measure with `cache_info()` before keeping it.

### Where this shows up

- **Real work — embedding/feature caches:** never re-embed identical text/documents across
  runs — an external (Redis/disk) embedding cache is standard in RAG/LLM pipelines (9.12)
  and directly saves money on paid APIs.
- **Real work — expensive lookups:** memoising slow API/DB calls per process (1.13's
  postcode example), bounded so a long-running service doesn't leak.
- **Real work — repeated computations in pipelines:** caching a costly transform keyed by
  input hash so re-runs skip already-done work (ties to progress manifests, Area 7).
- **Pattern mapping (secondary):** bounded LRU is itself a classic design problem ("LRU
  Cache" — hash map + doubly-linked list for O(1) get/put); memoisation with `@cache`
  turns exponential recursions into linear DP (1.13, Area 11).
[↑ Back to top](#contents)

---

<a id="2.15"></a>
## 2.15 — "Which is faster — I'll just measure" → micro-benchmarking correctly

### The situation

You want to know whether a list comprehension or a `map` is faster for a transform, so
you write a quick timer:

```python
import time
start = time.time()
result = [f(x) for x in data]
print(time.time() - start)           # e.g. 0.0012
```

You run it once, get `0.0012`, run it again, get `0.0019`, run a third time and get
`0.0008`. The numbers swing by 2x between runs, you can't tell which approach wins, and
worse — you don't notice that the *first* run was slow because the function/data hadn't
been loaded into CPU cache yet. Your "measurement" is noise.

### What's really going on

Timing a single run of a fast operation is unreliable: the duration is dominated by
**noise** — other processes, CPU frequency scaling, cache warm-up, garbage collection,
and the coarse resolution of `time.time()`. To compare two small snippets you need to
**run each many times and take the best/representative time**, while controlling for the
things that distort it.

Python's **`timeit`** module is built precisely for this. It runs the snippet in a loop
many times, repeats that several times, and reports the timings — and it sidesteps the
common mistakes (it disables the garbage collector during the run, uses the
high-resolution `perf_counter`, and lets you separate one-time **setup** from the code
being timed).

> Key benchmarking principles `timeit` encodes:
> - **Repeat many times** — one iteration is noise; thousands average it out.
> - **Take the minimum, not the mean** — the fastest run is the one *least* disturbed by
>   background interference; the mean is inflated by random hiccups.
> - **Separate setup from the measured code** — building the input list shouldn't be
>   counted in the time for the operation under test.
> - **Benchmark realistic inputs** — micro-results on 10 items may invert at 10 million.

### The move

Use `timeit` to run each candidate many times and compare best-of-N:

```python
import timeit

setup = "data = list(range(10000))"          # one-time prep, NOT timed
t_comp = timeit.timeit("[x*2 for x in data]", setup=setup, number=1000)
t_map  = timeit.timeit("list(map(lambda x: x*2, data))", setup=setup, number=1000)
print(f"comprehension: {t_comp:.4f}s   map: {t_map:.4f}s")   # total for 1000 runs
```

In a notebook/REPL, the `%timeit` magic does the same with automatic loop-count tuning:
`%timeit [x*2 for x in data]`.

### Why it works

`timeit` runs the snippet `number` times in a tight loop so the total is large enough to
measure accurately, then (with `.repeat()`) repeats that whole loop several times so you
can take the **minimum** — the run least polluted by background noise. It uses
`time.perf_counter` (the highest-resolution monotonic clock) and **disables GC** during
timing so a garbage-collection pause doesn't randomly inflate one run. The `setup`
argument runs **once, untimed**, so input construction and imports don't contaminate the
measurement of the operation itself. The result is a stable, repeatable comparison
instead of a single noisy sample.

### The code, every line explained

```python
import timeit

# --- The right way: many runs, setup separated, best-of-N ----------------
setup = "data = list(range(10000))"          # runs ONCE per repeat, not timed
t = timeit.repeat(                            # repeat() returns a LIST of timings
    stmt="[x * 2 for x in data]",             # the code under test (as a string)
    setup=setup,                              # prep excluded from the timing
    number=1000,                              # runs stmt 1000x per repeat
    repeat=5,                                 # do that 5 times -> 5 totals
)
print(min(t))                                 # take the MINIMUM: least-disturbed run

# --- Comparing two candidates fairly -------------------------------------
comp = min(timeit.repeat("[x*2 for x in data]", setup=setup, number=1000, repeat=5))
mp   = min(timeit.repeat("list(map(d, data))",
                         setup=setup + "; d = lambda x: x*2", number=1000, repeat=5))
print(f"comprehension {comp:.4f}s vs map {mp:.4f}s -> {mp/comp:.2f}x")

# --- Timing a callable instead of a string (no setup string needed) ------
def transform(data): return [x * 2 for x in data]
data = list(range(10000))
t = min(timeit.repeat(lambda: transform(data), number=1000, repeat=5))
# Passing a lambda avoids stringly-typed code, but note: the lambda call adds a
# tiny constant overhead — fine for comparison, just be consistent across candidates.

# --- The MISTAKES timeit saves you from ----------------------------------
# 1) time.time() is low-resolution & can jump (clock adjustments). Use perf_counter
#    or timeit — never time.time() for durations.
# 2) Timing ONE run -> dominated by noise/cache warm-up. Always loop.
# 3) Taking the MEAN -> inflated by random pauses. Take the MIN of repeats.
# 4) Counting setup in the timing -> measures input-building, not the operation.
# 5) GC firing mid-run -> timeit disables GC during timing by default.

# --- Always benchmark a REALISTIC size -----------------------------------
# Results can INVERT with scale: a method that wins on 100 items can lose on 10M
# (cache effects, allocation patterns, algorithmic constants). Time the real size.
```

### Impact

- **Trustworthy comparisons:** stable best-of-N numbers let you actually decide between
  two implementations instead of chasing noise.
- **Avoids false conclusions:** controlling setup, GC, clock resolution, and warm-up
  prevents the classic "I optimised it and it got *slower*… or did it?" confusion.
- **Right tool for the right question:** `timeit` for *comparing small snippets*;
  `cProfile` (2.1) for *finding the hot spot in a whole program*. Don't confuse the two.

### Pros & cons / when NOT to

**Reach for `timeit`/`%timeit` when:** comparing two small, fast pieces of code where the
difference is hard to see by eye.

**Watch out / when NOT to:**
- **Micro-benchmarks can mislead about the whole program.** A snippet 2x faster in
  isolation may be irrelevant if it's 0.1% of runtime — *profile first* (2.1) to confirm
  the code even matters before micro-optimising it.
- **Synthetic inputs lie.** Timing on `range(100)` when production data is 10M rows, or on
  uniform data when real data is skewed, can reverse the result. Use representative data.
- **Beware shared mutable state in `stmt`.** If the timed statement mutates `data`, later
  iterations run on different (e.g. already-sorted) input — rebuild fresh input in setup
  per repeat when the operation is destructive.
- **Don't over-measure cold code.** Benchmarking something that runs once a day is wasted
  effort; spend the measurement budget on the hot path.

### Where this shows up

- **Real work — choosing an implementation:** deciding between two ways to do a hot
  transform (comprehension vs vectorised vs map) on a representative data size before
  committing.
- **Real work — validating an optimisation:** proving a change is *actually* faster (and
  by how much) rather than assuming — pairs with the correctness oracle of 2.3.
- **Real work — data-structure choices:** measuring dict vs list membership, set vs sorted
  list, on your real sizes to confirm the 2.9 intuition empirically.
- **Pattern mapping (secondary):** benchmarking is how you empirically confirm Big-O
  reasoning — plot time vs input size and watch a linear method stay flat while an O(n²)
  one curves up; the measurement validates the analysis (2.2).
[↑ Back to top](#contents)

---

<a id="2.16"></a>
## 2.16 — "Integer/string interning & identity surprises" → small-object caching

### The situation

You're debugging a comparison that behaves inconsistently. Two variables holding "the
same" value sometimes pass an `is` check and sometimes don't:

```python
a = 256
b = 256
print(a is b)        # True

x = 257
y = 257
print(x is y)        # ... depends! True in some contexts, False in others
```

The *value* equality (`==`) is always `True`, but the *identity* (`is`) flips depending
on the number, the Python version, and even whether the two literals are on the same
line or in the same function. If any of your logic uses `is` to compare values, it works
in testing and fails mysteriously in production.

### What's really going on

This builds directly on 1.9 (`is` vs `==`). CPython **pre-creates and reuses** a pool of
small integer objects — **-5 to 256** — so every `256` in your whole program is literally
the *same cached object*; hence `256 is 256` is reliably `True`. Numbers outside that
range (like `257`) are normally built fresh, so two `257`s are usually *different*
objects → `is` is `False`.

But there's a second, separate mechanism that muddies it: when the compiler processes a
**single code unit** (one function body, one module, one interactive line), it
**folds and shares identical constant literals** within that unit. So `x = 257; y = 257`
written on one line, or inside the same function, can make `x is y` come out `True` —
not because of the small-int cache, but because the compiler reused one constant object.
Type `x = 257` and `y = 257` as two separate statements at the interactive prompt and you
may well get `False`.

> **Interning** = reusing a single shared object for a given value instead of making
> duplicates. Python interns small ints (-5..256) and many short, identifier-like strings
> automatically, to save memory and speed up equality. **`sys.intern(s)`** lets you
> *force* interning of a string. The point of all this: **these are optimisations you
> benefit from but must never depend on for correctness** — which is exactly why the rule
> from 1.9 exists.

### The move

The defensive rule (1.9) makes the whole class of surprise vanish: **use `==` for values,
reserve `is` for `None`/`True`/`False`.** Then *separately*, when you have a genuine
memory/speed reason — millions of repeated strings — use interning **on purpose**:

```python
# Correctness: never compare values with `is`
if status == "active":          # right
    ...
# NOT: if status is "active"    # works by luck for some literals, breaks for others

# Optimisation (deliberate): intern repeated strings to save memory & speed ==
import sys
canonical = sys.intern(label)   # force one shared object per distinct label value
```

### Why it works

The defensive rule works because `==` asks the question you actually mean ("equal
value?") and is unaffected by whether objects happen to be cached or freshly built. `is`
asks "same object?", whose answer depends on interning internals you don't control — so
you simply never use it for values.

Deliberate interning works because once many strings are interned, all copies of a given
value point at **one** object: you store the characters **once** (memory saving across
millions of duplicates), and equality checks can short-circuit on identity (a fast
pointer compare before falling back to character comparison). It's the same "store the
distinct values once" idea as a lookup table (2.8), applied to strings.

### The code, every line explained

```python
# --- The small-int cache: -5..256 are shared singletons ------------------
a = 256; b = 256
a is b              # True  -> both are the ONE cached 256 object
a == b              # True  -> and they're equal in value (the thing you care about)

# --- Outside the cache: usually distinct objects -------------------------
x = 1000; y = 1000
x == y              # True  -> ALWAYS correct: equal value
x is y              # often False -> two separate 1000 objects (DON'T rely on either way)

# --- The compiler-constant-folding wrinkle -------------------------------
def f():
    p = 257
    q = 257
    return p is q   # may be True: compiler shared the literal 257 within this function
# Two SEPARATE interactive statements `p = 257` then `q = 257` may give False.
# Lesson: identity of equal ints is an IMPLEMENTATION DETAIL. Never branch on it.

# --- Strings: short identifier-like literals are often interned ----------
"abc" is "abc"                  # often True (compile-time interned)
s = "ab"; ("a" + "b") is s      # often False: built at RUNTIME, not interned
# So again: compare strings with ==, never is.

# --- Deliberate interning: dedupe millions of repeated strings -----------
import sys
labels = [sys.intern(row.category) for row in rows]   # e.g. 10M rows, ~50 categories
# Now all "electronics" entries share ONE string object instead of 10M copies:
#   - MEMORY: store each distinct category once, not per row
#   - SPEED:  category == "electronics" can short-circuit on identity
# Without intern, each row may hold its own copy of the same characters.

# --- The correctness rule (from 1.9), which sidesteps ALL of the above ---
if result is None:              # right: None is a true singleton
    ...
if count == 256:                # right: value comparison
    ...
# if count is 256:              # WRONG in principle even though it "works" for 256
```

### Impact

- **Correctness:** following "`==` for values, `is` for `None`/`True`/`False`" eliminates
  the entire "works for 256, fails for 257 / works on this line, fails on that one" class
  of bug — bugs that are maddening precisely because they're non-deterministic across
  versions and code shapes.
- **Memory/speed (deliberate interning):** for data with **massive string repetition**
  (categorical columns, tokens, repeated keys), interning collapses millions of duplicate
  strings to one object each — real memory savings and faster equality.

### Pros & cons / when NOT to

**Apply the correctness rule always.** Apply **deliberate interning** only when you have a
measured repetition problem.

**Watch out / when NOT to:**
- **Never use `is` for value comparison** — not for ints, not for strings, not "because it
  seemed to work". The cache/interning behaviour is an implementation detail that changes
  between CPython versions and other interpreters (PyPy etc.).
- **Don't intern unique or rarely-repeated strings.** Interning has a cost (a lookup +
  keeping the object alive in the intern pool); it only pays off when the *same* value
  recurs many times. Interning high-cardinality data wastes effort and can *retain*
  memory.
- **Interned strings live for the table's lifetime.** `sys.intern` keeps the string
  reachable, so interning a flood of distinct strings is itself a retention risk (2.10).
- **For categorical data, a proper categorical type is often better:** pandas
  `Categorical` / a dict of codes stores each distinct value once *and* gives you integer
  codes — usually a cleaner win than manual `sys.intern` for tabular data.

### Where this shows up

- **Real work — the `is None` discipline:** the practical payoff is the everyday
  `if x is None` / `== value` habit (1.4's None-default pattern), now understood at the
  mechanism level — you know *why* `is` on values is unsafe.
- **Real work — deduping repeated strings:** interning category labels, repeated JSON
  keys, or tokens across millions of records to cut memory (cousin of the categorical
  encoding in Area 8).
- **Real work — debugging "impossible" comparison bugs:** recognising that an
  intermittent `is`-based comparison is the culprit and replacing it with `==`.
- **Pattern mapping (secondary):** identity-vs-value matters in linked-list/tree problems
  where you compare whether two pointers reference the *same node* (`is`) versus nodes
  with equal *values* (`==`) — e.g. cycle detection compares node identity, since values
  can repeat (1.9).

[↑ Back to top](#contents)

