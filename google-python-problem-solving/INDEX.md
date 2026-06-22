# Python Problem-Solving Field Guide

This is **not** a Python syntax course. It is a library of **situations a working
engineer actually hits**, and the **moves** you reach for when you recognise the
shape of each one. The goal is to train the reflex:

> *"I'm feeling X → the real problem is Y → reach for Z."*

That reflex is the "where do I even start?" muscle. LeetCode/interview patterns are
noted only as a **secondary** mapping — never the reason a scenario exists.

---

## How to read every scenario

Each scenario file follows the same shape so you can study it cold:

1. **The situation** — what you're staring at, in plain words.
2. **What's really going on** — the hidden shape of the problem (the diagnosis).
3. **The move** — the technique/tool you reach for.
4. **Why it works** — the mechanism, in layman-but-technical language.
5. **The code, every line explained** — no line left unexplained, every jargon
   word defined *inline* the first time it appears (no separate glossary).
6. **Impact** — what measurably changes (speed / memory / clarity / reliability).
7. **Pros & cons / when NOT to** — so you don't cargo-cult it.
8. **Where this shows up** — a real work example (sales / API / data / ML / ops)
   **+** the algorithmic pattern it maps to, if any.

**Inclusion test applied to every scenario:** *"Would a working engineer hit this
in a normal month of building data / API / ML / ops systems?"* If it's only a
code-golf trick, it's cut.

---

## Progress tracker

Legend: ✅ done · ⬜ pending

**Structure: 11 Areas.** Areas 1–2 are universal craft (Pythonic vocabulary, memory
& speed). Areas 3–10 are practical engineering biased toward data / ML / DL / LLM /
data-engineering work. Area 11 is a standalone LeetCode/DSA pillar (not ML-biased).
**Total planned: ~195 scenarios.** Count is live.

| Area | Theme | File | Count |
|---|---|---|---|
| 1 | Pythonic craft & vocabulary | `area_1_pythonic_craft.md` | 22 |
| 2 | Memory & performance (universal) | `area_2_memory_performance.md` | 16 |
| 3 | Data wrangling & data engineering | `area_3_data_wrangling.md` | 24 |
| 4 | Text & content processing | `area_4_text_content.md` | 10 |
| 5 | APIs, I/O & concurrency | `area_5_apis_concurrency.md` | 20 |
| 6 | Parallelism & scale (CPU) | `area_6_parallelism_scale.md` | 12 |
| 7 | Robustness & batch survival | `area_7_robustness_batch.md` | 15 |
| 8 | ML scenarios (broad) | `area_8_ml_broad.md` | 16 |
| 9 | DL & LLM tributary | `area_9_dl_llm.md` | 15 |
| 10 | Design & shipping | `area_10_design_shipping.md` | 12 |
| 11 | LeetCode / DSA patterns | `area_11_dsa_patterns.md` | 30 |

---

### Area 1 — Pythonic craft & vocabulary
File: `area_1_pythonic_craft.md`

- ✅ 1.1 — "Building a list with a loop and append" → comprehensions
- ✅ 1.2 — "Built a giant list to loop over once" → generators & yield
- ✅ 1.3 — "Opened it, but did it get closed?" → context managers (with)
- ✅ 1.4 — "Function remembers data between calls" → mutable default trap
- ✅ 1.5 — "Managing loop indices by hand" → enumerate & zip
- ✅ 1.6 — "Pulling values out by index one line each" → unpacking & starred
- ✅ 1.7 — "Pasting the same timing/retry code everywhere" → decorators
- ✅ 1.8 — "Function that takes any number of arguments" → *args / **kwargs
- ✅ 1.9 — "Values look equal but if does wrong thing" → is vs ==
- ✅ 1.10 — "Check everything before acting, still racy" → EAFP vs LBYL
- ✅ 1.11 — "Gluing strings with + is a mess" → f-strings
- ✅ 1.12 — "Looping to batch/group/chain sequences" → itertools essentials
- ✅ 1.13 — "Reusable caching/partials/folding" → functools (lru_cache, partial, reduce)
- ✅ 1.14 — "My object prints as gibberish / won't compare" → dunder methods
- ✅ 1.15 — "Sorting by a computed property or multiple keys" → sort with key
- ✅ 1.16 — "Grabbing sub-ranges and reversing sequences" → slicing & negative indices
- ✅ 1.17 — "Empty/zero/None handling with verbose ifs" → truthiness
- ✅ 1.18 — "Compute a value and test it in one step" → the walrus operator
- ✅ 1.19 — "if/else just to pick one of two values" → ternary & conditional expressions
- ✅ 1.20 — "Merging and updating dicts" → dict merge, unpacking, setdefault
- ✅ 1.21 — "Switch-case on a value / shape" → match statement (structural pattern)
- ✅ 1.22 — "Type hints that catch bugs before runtime" → typing essentials

### Area 2 — Memory & performance (universal)
File: `area_2_memory_performance.md`

- ✅ 2.1 — "It's slow and I'm guessing why" → profile before optimising (cProfile, timeit)
- ✅ 2.2 — "Spot the accidental O(n²)" → the nested-loop smell
- ✅ 2.3 — "Make it work → correct → fast" → the optimisation order
- ✅ 2.4 — "Building a big string in a loop is slow" → str.join vs +
- ✅ 2.5 — "Millions of small objects eat all my RAM" → __slots__
- ✅ 2.6 — "Changing one copy changed the other" → copy vs deepcopy & aliasing
- ✅ 2.7 — "Loading the whole thing to use a bit" → lazy evaluation & generators
- ✅ 2.8 — "Same pure computation repeated" → precompute & lookup tables
- ✅ 2.9 — "Dict/set lookups vs scanning a list" → choosing O(1) structures
- ✅ 2.10 — "Memory keeps climbing in a long run" → reference cycles & leaks
- ✅ 2.11 — "Numbers stored as Python objects are huge" → array / memoryview / numpy
- ✅ 2.12 — "Looping in Python over arrays is slow" → vectorise the hot path
- ✅ 2.13 — "Reading a huge file spikes memory" → chunked / buffered I/O
- ✅ 2.14 — "Repeated work across calls" → caching layers & lru_cache sizing
- ✅ 2.15 — "Which is faster — I'll just measure" → micro-benchmarking correctly
- ✅ 2.16 — "Integer/string interning & identity surprises" → small-object caching

### Area 3 — Data wrangling & data engineering
File: `area_3_data_wrangling.md`

- ✅ 3.1 — "CSV chokes on types and missing values" → robust CSV reading
- ✅ 3.2 — "A JSONL corpus too big for RAM" → stream line-delimited JSON
- ✅ 3.3 — "Pulling fields from deeply nested JSON" → safe .get chains / walking
- ✅ 3.4 — "Dirty values crash my conversions" → safe coercion (int/float/bool)
- ✅ 3.5 — "Missing or null fields everywhere" → defaults & sentinel handling
- ✅ 3.6 — "Validate incoming data against a shape" → schema validation (pydantic/dataclass)
- ✅ 3.7 — "Parse and normalise dates/timestamps" → datetime & timezones
- ✅ 3.8 — "Date arithmetic — within last N days, durations" → timedelta
- ✅ 3.9 — "Text encoding/decoding errors (UTF-8/BOM)" → encoding handling
- ✅ 3.10 — "Processing a directory of files robustly" → pathlib & glob
- ✅ 3.11 — "Pick the right on-disk format" → CSV/JSON/JSONL/Parquet/pickle trade-offs
- ✅ 3.12 — "Sanity-check a dataset before trusting it" → null counts, ranges, balance
- ✅ 3.13 — "Have I seen this before / dedup" → set membership
- ✅ 3.14 — "How many of each" → Counter
- ✅ 3.15 — "Group records by a field" → defaultdict(list)
- ✅ 3.16 — "Match two datasets on a key" → dict join
- ✅ 3.17 — "Find the top N" → heapq
- ✅ 3.18 — "Look up by two+ fields" → composite/tuple keys
- ✅ 3.19 — "Sort by multiple fields" → key functions & multi-key sort
- ✅ 3.20 — "Search/insert in sorted data" → bisect
- ✅ 3.21 — "DataFrame: vectorised ops vs row loops" → pandas thinking
- ✅ 3.22 — "DataFrame: group-by & merge" → split-apply-combine
- ✅ 3.23 — "Handle NaN/missing in arrays & frames" → fillna/dropna/masks
- ✅ 3.24 — "Reshape: pivot / explode lists into rows" → wide↔long

### Area 4 — Text & content processing
File: `area_4_text_content.md`

- ✅ 4.1 — "Messy text: whitespace, case, unicode" → normalisation
- ✅ 4.2 — "Extract structured info from text" → regex essentials
- ✅ 4.3 — "Match/replace patterns at scale" → compiled regex & groups
- ✅ 4.4 — "Stable IDs / cache keys from content" → hashing (hashlib)
- ✅ 4.5 — "Detect near-duplicate text" → normalisation keys & shingling
- ✅ 4.6 — "Fuzzy similarity between strings" → edit distance / ratio
- ✅ 4.7 — "Extract text from HTML/markdown" → parsing vs regex
- ✅ 4.8 — "Split text into chunks (chars/sentences/tokens)" → chunking
- ✅ 4.9 — "Build strings/templates safely" → join, templates, escaping
- ✅ 4.10 — "Search within large text efficiently" → find/in vs regex vs index

### Area 5 — APIs, I/O & concurrency
File: `area_5_apis_concurrency.md`

- ✅ 5.1 — "My program spends its life waiting" → recognising I/O-bound work
- ✅ 5.2 — "Call thousands of endpoints fast" → ThreadPoolExecutor
- ✅ 5.3 — "Sync vs async — the actual difference" → blocking vs non-blocking
- ✅ 5.4 — "Thousands of concurrent calls, few threads" → asyncio & event loop
- ✅ 5.5 — "Mixing sync and async code" → to_thread / run_in_executor
- ✅ 5.6 — "Overlap the wait with useful work" → producer/consumer threads
- ✅ 5.7 — "Pipeline stages handing off work" → queue between threads
- ✅ 5.8 — "The API randomly fails" → timeouts as a hard requirement
- ✅ 5.9 — "Retry without making it worse" → exponential backoff + jitter
- ✅ 5.10 — "Stop calling a dead service" → circuit breaker & fallback
- ✅ 5.11 — "I'm getting 429'd" → client-side rate limiting
- ✅ 5.12 — "Cap how many run at once" → semaphore
- ✅ 5.13 — "The data comes in pages" → pagination patterns
- ✅ 5.14 — "Process items in batches" → batching API calls
- ✅ 5.15 — "Job isn't done when API returns" → polling for a result
- ✅ 5.16 — "Poll without hammering the server" → intervals, backoff & deadlines
- ✅ 5.17 — "Polling is wasteful — push instead" → webhooks vs polling
- ✅ 5.18 — "Re-opening the connection each call" → session reuse & pooling
- ✅ 5.19 — "Stream a response as it arrives" → streamed downloads / SSE
- ✅ 5.20 — "Track cost/usage across many calls" → usage accounting

### Area 6 — Parallelism & scale (CPU)
File: `area_6_parallelism_scale.md`

- ✅ 6.1 — "Is this I/O-bound or CPU-bound?" → the decision that changes everything
- ✅ 6.2 — "Use all my cores" → multiprocessing for true parallelism
- ✅ 6.3 — "Why threads didn't speed up my math" → the GIL in plain words
- ✅ 6.4 — "The easy door to parallelism" → ProcessPoolExecutor
- ✅ 6.5 — "Apply one function across millions of rows" → Pool.map / imap
- ✅ 6.6 — "Moving data between workers costs more" → serialization (pickle) cost
- ✅ 6.7 — "Split work into chunks" → chunksize & granularity
- ✅ 6.8 — "Workers share a big read-only dataset" → shared memory vs copying
- ✅ 6.9 — "Collect results from many workers" → as_completed & ordering
- ✅ 6.10 — "One bad item kills the batch" → isolating worker failures
- ✅ 6.11 — "Load the model once per worker" → initializer / warm workers
- ✅ 6.12 — "Too big for one machine" → when to reach for Dask/Spark

### Area 7 — Robustness & batch survival
File: `area_7_robustness_batch.md`

- ✅ 7.1 — "I can't trust this input" → validate at the boundary
- ✅ 7.2 — "Fail loud vs fail safe" → choosing the failure mode
- ✅ 7.3 — "Catching every error hides bugs" → specific exceptions, no bare except
- ✅ 7.4 — "Running it twice double-charges" → idempotency
- ✅ 7.5 — "Safe re-runs of a job" → dedupe keys & manifests
- ✅ 7.6 — "Don't lose work if it crashes halfway" → checkpointing
- ✅ 7.7 — "Resume a long job where it stopped" → resumable jobs
- ✅ 7.8 — "Half-written file corrupts everything" → atomic writes
- ✅ 7.9 — "10k docs, 12 fail — don't lose the 9,988" → partial-failure handling
- ✅ 7.10 — "Long job with no feedback" → progress, ETA, heartbeats
- ✅ 7.11 — "Two things touched the same data" → races explained
- ✅ 7.12 — "Sidestep locking entirely" → single-owner via queues
- ✅ 7.13 — "I can't see what prod is doing" → logging vs print
- ✅ 7.14 — "Config & secrets done right" → env vars / 12-factor
- ✅ 7.15 — "Works on my machine, not in prod" → reproducible environments & lockfiles

### Area 8 — ML scenarios (broad)
File: `area_8_ml_broad.md`

- ✅ 8.1 — "My model scores great in training, awful live" → train/test leakage
- ✅ 8.2 — "Categorical columns the model can't read" → encoding (one-hot/label/target)
- ✅ 8.3 — "One feature dominates because of scale" → scaling/normalisation
- ✅ 8.4 — "95% accuracy but it predicts one class" → imbalanced data
- ✅ 8.5 — "Accuracy is the wrong number to trust" → choosing metrics
- ✅ 8.6 — "One split got lucky/unlucky" → cross-validation
- ✅ 8.7 — "Results change every run" → seeds & determinism
- ✅ 8.8 — "Retrain gives different answers" → reproducible pipelines
- ✅ 8.9 — "Saving and loading a model safely" → serialization & versioning
- ✅ 8.10 — "Predict on millions of rows" → batch inference
- ✅ 8.11 — "NaN/inf blew up training" → numerical stability
- ✅ 8.12 — "Fit the scaler on train only" → transform leakage & pipelines
- ✅ 8.13 — "Feed data to the model in batches" → data loaders & batching
- ✅ 8.14 — "Compare two models fairly" → held-out sets & significance
- ✅ 8.15 — "Track experiments & params" → experiment logging
- ✅ 8.16 — "Feature columns drift over time" → train/serve skew

### Area 9 — DL & LLM tributary
File: `area_9_dl_llm.md`

- ✅ 9.1 — "Shape mismatch errors everywhere" → tensor shapes & broadcasting
- ✅ 9.2 — "Sequences of different lengths in a batch" → padding & masking
- ✅ 9.3 — "CUDA out of memory" → batch size, grad accumulation, mixed precision
- ✅ 9.4 — "Training loss is NaN" → exploding/vanishing gradients
- ✅ 9.5 — "Save/restore training to resume" → checkpoints (model+optimizer)
- ✅ 9.6 — "Data loading starves the GPU" → workers & prefetch
- ✅ 9.7 — "Inference is slow / no_grad forgotten" → eval mode & no_grad
- ✅ 9.8 — "Count tokens & fit a context budget" → tokenisation & limits
- ✅ 9.9 — "Chunk documents for embeddings" → chunking strategy
- ✅ 9.10 — "Parse LLM JSON output safely" → fences, malformed, re-ask
- ✅ 9.11 — "Validate LLM structured output" → schema + repair
- ✅ 9.12 — "Re-embedding costs money every run" → embedding cache
- ✅ 9.13 — "Stream tokens to the user" → streaming responses
- ✅ 9.14 — "Retrieve relevant chunks" → vector similarity basics
- ✅ 9.15 — "Track LLM cost/latency across calls" → usage & budget tracking

### Area 10 — Design & shipping
File: `area_10_design_shipping.md`

- ✅ 10.1 — "Passing the same 5 values around" → group into a dataclass
- ✅ 10.2 — "This function does six things" → split by responsibility
- ✅ 10.3 — "Class or just a dict?" → when a class earns its keep
- ✅ 10.4 — "Magic values scattered everywhere" → constants & enums
- ✅ 10.5 — "Hard to test because it does I/O inline" → dependency injection
- ✅ 10.6 — "Swap an implementation without rewriting callers" → depend on interfaces
- ✅ 10.7 — "Coupling I'll regret" → dependency direction
- ✅ 10.8 — "Ship a change without breaking things" → tests as a safety net
- ✅ 10.9 — "Mock/fake the LLM/API in tests" → test doubles
- ✅ 10.10 — "Reproduce a bug before fixing it" → failing-test-first
- ✅ 10.11 — "I changed behaviour and didn't notice" → regression/golden tests
- ✅ 10.12 — "Roll out safely / roll back fast" → feature flags & staged release

### Area 11 — LeetCode / DSA patterns
File: `area_11_dsa_patterns.md`

- ✅ 11.1 — "Find pairs/elements fast" → arrays + hashing
- ✅ 11.2 — "Scan a sorted array from both ends" → two pointers
- ✅ 11.3 — "Best window of size/condition" → sliding window
- ✅ 11.4 — "Range sums asked repeatedly" → prefix sums
- ✅ 11.5 — "Search a sorted space" → binary search
- ✅ 11.6 — "Minimise the max / search on answer" → binary search on answer
- ✅ 11.7 — "Overlapping ranges" → interval merging & sorting
- ✅ 11.8 — "Detect a cycle / find middle" → fast & slow pointers
- ✅ 11.9 — "Reverse / reorder a linked list" → pointer manipulation
- ✅ 11.10 — "Next greater / smaller element" → monotonic stack
- ✅ 11.11 — "Sliding window max / min" → monotonic deque
- ✅ 11.12 — "Kth largest / merge K sorted" → heaps
- ✅ 11.13 — "Visit every node in a tree" → tree DFS (recursive & iterative)
- ✅ 11.14 — "Level-by-level traversal" → tree BFS
- ✅ 11.15 — "Search/insert in ordered tree" → BST operations
- ✅ 11.16 — "Explore a grid / graph" → graph BFS/DFS
- ✅ 11.17 — "Order tasks with dependencies" → topological sort
- ✅ 11.18 — "Shortest path with weights" → Dijkstra
- ✅ 11.19 — "Group connected things" → union-find (disjoint set)
- ✅ 11.20 — "Try all combinations with pruning" → backtracking
- ✅ 11.21 — "Overlapping subproblems, 1D" → dynamic programming (1D)
- ✅ 11.22 — "Grid/2D choices" → dynamic programming (2D)
- ✅ 11.23 — "Compare/align two sequences" → string DP (edit distance, LCS)
- ✅ 11.24 — "Locally-optimal works" → greedy & how to know it's safe
- ✅ 11.25 — "Prefix lookups / autocomplete" → tries
- ✅ 11.26 — "Flip/scan bits" → bit manipulation tricks
- ✅ 11.27 — "Walk a matrix in a pattern" → matrix traversal (spiral/rotate)
- ✅ 11.28 — "Break a problem into subproblems" → recursion fundamentals
- ✅ 11.29 — "Generate all subsets/permutations" → combinatorial enumeration
- ✅ 11.30 — "Which pattern is this?" → reading a problem to pick the approach

---

*Each scenario is written in the 8-part format, in ≤100-line chunks, British spelling,
with concrete problem statements. Areas may be filled in parallel since each is a
separate file.*
