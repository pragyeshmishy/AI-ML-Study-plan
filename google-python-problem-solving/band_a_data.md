# Band A — Getting the Right Answer Out of Data

Scenarios about pulling correct results out of data that lives *inside your
program* (lists, records, rows you've already loaded). The recurring enemy in this
band is **re-scanning** — looking through the same data again and again when a
smarter structure would let you find things instantly.

---

## A1.1 — "Have I seen this before?" → set membership & dedup

### The situation

You're processing a stream of records — say, customer IDs from a sales export, or
user emails from a sign-up feed. You need to answer one of two questions over and
over:

- *"Have I already seen this ID?"* (skip duplicates)
- *"Is this email on the blocked list?"* (membership check)

Your first instinct is probably a **list** (an ordered collection of items, written
with square brackets: `seen = []`). You append IDs to it, and to check if an ID is
already there you write `if customer_id in seen`. It works on your 100-row test
file. Then you run it on the real 2-million-row export and it **crawls** — minutes,
not seconds.

### What's really going on

The hidden problem is **how `in` searches a list**.

When you write `customer_id in seen` and `seen` is a list, Python has no choice but
to walk the list from the front, comparing each element one by one, until it finds
a match or reaches the end. That walk is called a **linear scan** — "linear"
because the time it takes grows in a straight line with the number of items.

We describe that cost as **O(n)** ("oh of n"). This is **Big-O notation** — a way
to describe *how the work grows as the input grows*, ignoring constant details.
`n` means "the number of items." O(n) means "if you double the items, you roughly
double the work." (A separate scenario, A2.1, covers Big-O properly — for now just
read O(n) as "cost grows with the size of the list.")

Here's the trap: you don't do this check **once**. You do it **once per incoming
record**. If you have `n` incoming records and each check scans a list of up to `n`
items, the total work is `n × n = n²`. That's **O(n²)** ("oh of n squared") — the
silent killer. At 2 million records, n² is **4 trillion** comparisons. That's why
it crawls.

So the real shape of the problem is: *"I need a collection whose only job is to
answer 'is this thing in here?' instantly, no matter how big it gets."*

### The move

Use a **set** instead of a list.

A **set** is an unordered collection of **unique** items, written with curly braces:
`seen = set()`. Its defining superpower: checking membership (`x in seen`) takes
roughly the **same tiny amount of time whether it holds 10 items or 10 million**.

### Why it works

A set is built on a **hash table** (sometimes called a hash map). Here's the
mechanism in plain terms:

- When you add an item, Python runs it through a **hash function** — a piece of
  math that turns the item into a number called a **hash** (e.g. the string
  `"C-1024"` might hash to the number `8837261`).
- Python uses that number to decide *which slot* in an internal array the item goes
  into. Think of it as: the item's own value tells you where it's stored.
- To check `x in seen`, Python hashes `x`, jumps **directly** to that one slot, and
  looks only there. It does **not** walk the whole collection.

Because the lookup jumps straight to one spot instead of scanning, the cost is
**O(1)** ("oh of one") — **constant time**. "Constant" means it doesn't grow with
the number of items. One check costs the same on a 10-item set or a 10-million-item
set.

That single change turns your whole job from O(n²) into O(n): `n` records, each
with an O(1) check, is `n × 1 = n` total work.

### The code, every line explained

```python
# --- The SLOW version (a list) -------------------------------------------
seen = []                          # an empty LIST. Square brackets = list.
                                   # Lists keep order and allow duplicates,
                                   # but `x in list` is a linear scan: O(n).

for customer_id in incoming_ids:   # loop over every incoming record.
                                   # `incoming_ids` is whatever you're reading,
                                   # e.g. a list/stream of "C-1024" strings.

    if customer_id in seen:        # MEMBERSHIP CHECK. On a list this walks
                                   # the whole list each time -> the killer.
        continue                   # `continue` = skip the rest of this loop
                                   # iteration and go to the next item.
                                   # Here: it's a duplicate, so skip it.

    seen.append(customer_id)       # `.append(x)` adds x to the END of a list.
    process(customer_id)           # your real work (charge, store, send...).
```

```python
# --- The FAST version (a set) --------------------------------------------
seen = set()                       # an empty SET. NOTE: {} makes an empty
                                   # DICT, not a set — so use set() for empty.
                                   # Sets hold UNIQUE items and give O(1)
                                   # membership.

for customer_id in incoming_ids:
    if customer_id in seen:        # SAME line of code, but now it's O(1):
                                   # Python hashes customer_id and checks one
                                   # slot. Instant, regardless of set size.
        continue

    seen.add(customer_id)          # `.add(x)` is the set's version of append.
                                   # If x is already present, it's a no-op
                                   # (sets silently ignore duplicates).
    process(customer_id)
```

```python
# --- Bonus: dedup in ONE line when you don't need streaming --------------
unique_ids = set(incoming_ids)     # passing any iterable to set() builds a
                                   # set from it, dropping duplicates in O(n).
                                   # Use this when you just want the unique
                                   # values and don't care about order.

# If you DO need to preserve first-seen order while deduping:
unique_ordered = list(dict.fromkeys(incoming_ids))
                                   # dict.fromkeys(...) builds a dict whose KEYS
                                   # are the items (dicts keep insertion order
                                   # and drop dup keys); list(...) takes just
                                   # the keys back out, in original order.
```

### Impact

- **Speed:** the membership check goes from O(n) to O(1), turning an O(n²) job into
  O(n). On 2M records that's the difference between **~4 trillion** comparisons and
  **~2 million** — minutes down to a fraction of a second.
- **Memory:** a set costs a bit more memory per item than a list (it keeps spare
  slots so the hash table stays fast). You trade a little RAM for an enormous speed
  win. Almost always worth it.
- **Clarity:** `set` also *documents your intent* — a reader sees `set()` and
  immediately knows "uniqueness and membership matter here," which a list doesn't
  communicate.

### Pros & cons / when NOT to

**Reach for a set when:**
- You repeatedly ask "is X in here?"
- You need to drop duplicates.
- You don't care about order and don't need to store duplicates.

**Do NOT use a set when:**
- **Order matters** and you must keep it — sets are unordered. (Use a list, or the
  `dict.fromkeys` trick above to dedup *while* keeping order.)
- **You need duplicates** — e.g. counting how many times each value appears. A set
  throws duplicates away; you want a `Counter` for that (scenario A1.2).
- **The items aren't hashable.** Only **immutable** things (things that can't be
  changed in place — strings, numbers, tuples) can go in a set. You **cannot** put a
  list or a dict in a set, because their hash could change if you mutated them, which
  would break the table. Trying raises `TypeError: unhashable type: 'list'`.
- The collection is **tiny and checked rarely** — for 5 items checked once, a list
  is fine and the difference is invisible. (Don't optimise what doesn't hurt — A2.3.)

### Where this shows up

- **Real work — deduping a sales/ETL feed:** an upstream system sends the same order
  twice on a retry. A `seen_order_ids = set()` guard makes your import **idempotent-ish**
  (safe against repeats) for free. (Full idempotency is scenario D15.1.)
- **Real work — blocklist / allowlist checks:** "is this email/IP/domain blocked?"
  Load the blocklist into a set once at startup; every request then checks in O(1)
  instead of scanning a list per request.
- **Real work — "which IDs are new since yesterday?":** `today_ids - yesterday_ids`
  (set difference) gives you brand-new IDs in one operation; `today & yesterday`
  (intersection) gives the overlap. These set operations are themselves fast and
  expressive.
- **Pattern mapping (secondary):** this is the core trick behind a huge class of
  interview problems — "contains duplicate," "two-sum" (store seen numbers in a set/
  dict and check for the complement), "intersection of two arrays," "happy number."
  The unifying idea is always *"trade memory for instant lookups."*

---

## A1.2 — "How many of each?" → Counter

### The situation

You have a pile of records and you need a **tally**: how many orders came from each
country, how many times each error code appeared in a log, how many units of each
SKU (Stock Keeping Unit — a product's unique code) sold today. The output you want
is a mapping like `{"IN": 4201, "US": 3998, "DE": 1500, ...}`.

Your instinct is probably a **dict** (a collection of key → value pairs, written
with curly braces: `counts = {}`) where the key is the country and the value is the
running total. So you write:

```python
counts[country] = counts[country] + 1
```

…and on the very first record for a new country it **crashes** with
`KeyError: 'IN'`. A `KeyError` means "you asked for a key that isn't in the dict
yet." The country has no entry, so `counts[country]` can't be read to add 1 to it.

### What's really going on

The real problem is the **"first time I see a key" gap**. Counting has two cases
that feel like one:

1. **First sight** of a key → you need to *create* it starting at 0.
2. **Every later sight** → you need to *increment* the existing value.

Beginners handle this with an `if`-check on every record, which is noisy and easy to
get subtly wrong. The deeper realisation: *counting occurrences is such a universal
need that the standard library has a purpose-built tool for it.* You shouldn't be
hand-rolling the first-sight logic at all.

### The move

Use **`collections.Counter`** — a dict subclass (it *is* a dict, with extra
counting powers) whose entire job is tallying things.

`collections` is a **module** (a built-in file of ready-made tools) in Python's
**standard library** (the toolbox that ships with Python — nothing to install). You
get `Counter` with `from collections import Counter`.

### Why it works

`Counter` knows the first-sight rule for you: **asking for a key it has never seen
returns `0` instead of crashing.** So incrementing always works, even the first
time. And if you hand it an entire iterable up front, it does the whole tally in one
pass — O(n), one walk through the data.

### The code, every line explained

```python
from collections import Counter    # pull Counter out of the collections module.
                                    # `from X import Y` = "grab just Y from X"
                                    # so you can write Counter, not collections.Counter.

# --- Way 1: count an existing iterable in one shot -----------------------
orders = ["IN", "US", "IN", "DE", "IN", "US"]   # e.g. country of each order
counts = Counter(orders)           # ONE pass over orders, building the tally.
                                    # counts is now Counter({'IN': 3, 'US': 2, 'DE': 1})
                                    # (Counter prints itself sorted by highest count.)

print(counts["IN"])                # -> 3.  Reading a key works like any dict.
print(counts["FR"])                # -> 0.  KEY DIFFERENCE: a missing key returns 0,
                                    #         it does NOT raise KeyError. This is the
                                    #         whole reason counting is painless here.

# --- Way 2: count as records stream in (you don't have them all at once) -
counts = Counter()                 # empty counter; every key implicitly starts at 0.
for country in incoming_orders:    # one record at a time (e.g. from a feed/file)
    counts[country] += 1           # `+= 1` means counts[country] = counts[country] + 1.
                                    # On first sight, the right-hand side reads as 0,
                                    # so it becomes 1. No if-check, no KeyError.

# --- The payoff method: most_common -------------------------------------
top3 = counts.most_common(3)       # returns a LIST of (key, count) pairs, already
                                    # sorted from highest to lowest count, e.g.
                                    # [('IN', 3), ('US', 2), ('DE', 1)].
                                    # most_common() with no number returns ALL of them
                                    # in ranked order.
```

```python
# --- What you'd have written WITHOUT Counter (for contrast) --------------
counts = {}
for country in incoming_orders:
    if country not in counts:      # the manual "first sight" guard...
        counts[country] = 0        # ...create it at 0...
    counts[country] += 1           # ...then increment. Three lines doing what
                                    # Counter does in one, and easy to fumble.
```

### Impact

- **Correctness:** the `KeyError`-on-first-sight class of bug disappears entirely.
- **Speed:** building from an iterable is a single O(n) pass; `most_common(k)` uses
  an efficient heap internally, so getting the top *k* of *m* distinct keys is
  cheaper than fully sorting everything.
- **Clarity:** `Counter(orders)` says "I am tallying" in one glance. Intent is
  visible, which is itself a real maintenance win.

### Pros & cons / when NOT to

**Reach for Counter when:** you need frequencies, a histogram, "top N most common,"
or to compare two tallies (Counters support `+`, `-`, `&`, `|` to combine counts).

**Watch out:**
- A missing key returning `0` is *usually* what you want, but it means a typo in a
  key name won't error — it'll silently read as 0. If a missing key is genuinely a
  bug in your context, a plain dict's `KeyError` is the safer signal.
- `Counter` counts **hashable** items only (same rule as sets, A1.1 — strings,
  numbers, tuples yes; lists/dicts no).
- For **summing values** (e.g. total revenue per country, not *count* of orders),
  Counter is the wrong tool — you want `defaultdict(float)` or grouping (A1.3).
  Counter is specifically for *counting occurrences*.

### Where this shows up

- **Real work — log triage:** `Counter(line.split()[0] for line in logfile)` to see
  which status codes or services dominate your error log, then `.most_common(10)`.
- **Real work — sales dashboards:** units sold per SKU, orders per region, events
  per user — any "group and count" feeding a chart.
- **Real work — ML/data prep:** class balance in a labelled dataset
  (`Counter(labels)`) to spot that 95% of your training rows are one class — a
  problem you must see *before* training.
- **Pattern mapping (secondary):** frequency-based problems — "top K frequent
  elements," "majority element," "first unique character," "valid anagram"
  (two strings are anagrams iff their `Counter`s are equal).

---

## A1.3 — "Group these records by a field" → defaultdict(list)

### The situation

You have a flat list of records and you need them **bucketed by some field**. Given
a list of orders, you want all orders for each customer collected together:

```
input:  [order_A(cust=1), order_B(cust=2), order_C(cust=1), ...]
want:   {1: [order_A, order_C, ...], 2: [order_B, ...], ...}
```

You reach for a dict where each key maps to a **list** of records, and write:

```python
groups[cust_id].append(order)
```

…and again it's `KeyError` on the first order for each customer — because
`groups[cust_id]` doesn't exist yet, so there's no list to `.append` to.

### What's really going on

Same "first sight" gap as counting (A1.2), but now the missing value should start as
an **empty list** `[]` rather than `0`, because you're *accumulating items* into a
bucket, not adding up a number. The pattern is **grouping** (a.k.a. "bucketing" or a
one-to-many index): turning a flat sequence into `key → list of things with that
key`.

### The move

Use **`collections.defaultdict(list)`** — a dict that **auto-creates a default value
the first time you touch a missing key**.

You hand `defaultdict` a **factory** — a zero-argument callable that produces the
starting value. `list` (the type itself, no parentheses) is a factory that makes a
fresh empty list. So `defaultdict(list)` means "any missing key springs into
existence as `[]`."

> "Callable" = anything you can call with `()`. `list()` returns `[]`, so the bare
> name `list` *is* the factory. Use `defaultdict(int)` for counting-style 0s,
> `defaultdict(set)` for buckets of unique items, `defaultdict(list)` for lists.

### Why it works

When you access a key that isn't there, a normal dict raises `KeyError`. A
`defaultdict` instead **calls the factory, inserts that fresh value under the key,
and hands it back** — all before your `.append` runs. So `groups[cust_id]` always
returns a real list (empty on first sight), and `.append` just works.

### The code, every line explained

```python
from collections import defaultdict   # grab defaultdict from collections.

groups = defaultdict(list)            # a dict whose missing keys auto-init to [].
                                      # `list` is the FACTORY (no parentheses!).
                                      # Writing list() here would be wrong — you pass
                                      # the function itself, not its result.

for order in orders:                  # one flat record at a time
    groups[order.customer_id].append(order)
                                      # FIRST time we see a customer_id:
                                      #   defaultdict calls list() -> [], stores it,
                                      #   returns it, then .append(order) fills it.
                                      # LATER times: the list already exists; append.
                                      # Either way: no KeyError, no if-check.

# groups is now e.g. {1: [order_A, order_C], 2: [order_B], ...}

for customer_id, their_orders in groups.items():
                                      # .items() yields (key, value) PAIRS so you can
                                      # loop over both at once. their_orders is the list.
    print(customer_id, len(their_orders))   # e.g. how many orders each customer made
```

```python
# --- Without defaultdict (the manual version) ----------------------------
groups = {}
for order in orders:
    groups.setdefault(order.customer_id, []).append(order)
                                      # .setdefault(k, default): "give me groups[k];
                                      # if k is missing, first set it to default."
                                      # This works and is fine for one-offs, but
                                      # defaultdict is cleaner when you group a lot.
```

### Impact

- **Correctness:** removes the first-sight `KeyError` for accumulation, the way
  Counter does for counting.
- **Speed:** grouping `n` records is a single O(n) pass. The alternative — for each
  key, scanning the whole list to collect its members — would be O(n²). This is the
  same "don't re-scan" win as A1.1, applied to bucketing.
- **Clarity:** `defaultdict(list)` announces "I'm building one-to-many buckets."

### Pros & cons / when NOT to

**Reach for it when:** you turn a flat list into `key → many values`, build an index
("which orders belong to customer X?"), or invert a mapping.

**Watch out:**
- A `defaultdict` **creates entries just by *reading* a missing key.** If you write
  `if groups[some_id]:` to *test* for a key, you'll silently insert an empty list for
  `some_id` as a side effect. To check membership without creating, use
  `if some_id in groups:` (the `in` test never auto-creates).
- When you're done building and want "missing means error" behaviour back, convert
  with `dict(groups)` — a plain dict that raises `KeyError` again.
- If you only need **counts**, use `Counter` (A1.2). If you need **unique** members
  per bucket, use `defaultdict(set)` so duplicates collapse.

### Where this shows up

- **Real work — joining/enriching:** group line-items by `order_id`, then attach
  each group to its order header. (A different two-dataset match is the dict join,
  A1.4.)
- **Real work — building an inverted index:** `word → [doc_ids that contain it]`,
  the backbone of search and a building block in retrieval/RAG pipelines.
- **Real work — bucketing events:** group log events by `trace_id` to reconstruct
  each request's full journey across services.
- **Pattern mapping (secondary):** "group anagrams" (key = sorted letters → list of
  words), "group by frequency," adjacency lists for graphs (`defaultdict(list)`
  mapping node → its neighbours, used in BFS/DFS — see E22/Band-D graph scenarios).

---

## A1.4 — "Match two datasets together" → the dict join

### The situation

You have **two** separate datasets and need to stitch them by a shared key. Classic
shape: a list of `orders` (each has a `customer_id`) and a list of `customers`
(each has an `id`, `name`, `tier`). You want each order enriched with its customer's
name and tier.

The natural-but-naive code is a **nested loop**:

```python
for order in orders:
    for customer in customers:        # scan ALL customers for each order
        if customer.id == order.customer_id:
            order.customer_name = customer.name
            break
```

On small data it's fine. On 100k orders × 50k customers it's **5 billion**
comparisons and grinds to a halt.

### What's really going on

This is the **join** — the same operation a database does when you `JOIN` two
tables. The naive nested loop is literally what databases call a *nested-loop join*,
and its cost is **O(n × m)** (orders × customers): for every order you re-scan every
customer.

The realisation: *you are doing repeated lookups by a key (`customer.id`), and from
A1.1 you already know the fix for repeated lookups — a hash-based structure that
finds by key in O(1).* The only twist is you want to retrieve a **whole record**, not
just test membership, so you use a **dict** (key → record) instead of a set.

### The move

**Index one side into a dict first, then loop the other side once**, looking each
match up in O(1). This is the **hash join**.

Rule of thumb: build the index from the **smaller** dataset (less memory), then
stream the larger one against it.

### Why it works

You pay O(m) **once** to build `{customer.id: customer}`. After that, each of the
`n` orders does a single O(1) dict lookup to find its customer. Total work drops
from O(n × m) to **O(n + m)** — build the index (m) plus one pass over orders (n).
On 100k × 50k that's ~150k operations instead of ~5 billion.

### The code, every line explained

```python
# --- Step 1: index the smaller dataset by its key -----------------------
customers_by_id = {c.id: c for c in customers}
                                   # a DICT COMPREHENSION: {key_expr: value_expr for ...}.
                                   # For each customer c, it makes an entry
                                   #   key   = c.id   (what we'll look up by)
                                   #   value = c      (the whole customer record)
                                   # Result: {1: customer1, 2: customer2, ...}
                                   # Built in ONE O(m) pass.
                                   # NOTE: if two customers share an id, the later one
                                   # overwrites the earlier — keys are unique. If ids
                                   # aren't unique, group instead (defaultdict, A1.3).

# --- Step 2: stream the larger dataset, look up each match in O(1) -------
for order in orders:               # one pass over orders: O(n)
    customer = customers_by_id.get(order.customer_id)
                                   # .get(key) returns the value, or None if the key
                                   # is missing — it does NOT raise KeyError.
                                   # Using .get (not [key]) handles "order references
                                   # a customer we don't have" gracefully.
    if customer is None:           # the match failed — orphaned order.
        log.warning("Order %s references unknown customer %s",
                    order.id, order.customer_id)
        continue                   # skip enriching; deal with bad data explicitly.

    order.customer_name = customer.name   # enrich the order with data from the match
    order.customer_tier = customer.tier
```

```python
# --- If you need ALL orders per customer (one-to-many), combine A1.3+A1.4 -
from collections import defaultdict
orders_by_customer = defaultdict(list)
for order in orders:                       # O(n): group orders by their key
    orders_by_customer[order.customer_id].append(order)

for customer in customers:                 # O(m): now each customer's orders are ready
    their_orders = orders_by_customer.get(customer.id, [])
                                           # .get(key, default): return default ([]) if
                                           # the customer has no orders, instead of None.
    print(customer.name, len(their_orders))
```

### Impact

- **Speed:** O(n × m) → O(n + m). This is often the single biggest win in a data
  script — the difference between "never finishes" and "instant."
- **Memory:** you spend extra memory holding the index dict (roughly the size of the
  smaller dataset). Index the smaller side to keep that cost down.
- **Clarity:** "build index, then look up" is a recognisable, explainable shape; a
  triple-nested loop is not.

### Pros & cons / when NOT to

**Reach for the dict join when:** you combine two in-memory datasets on a key and
the naive version is (or would become) a nested loop.

**Watch out / when not to:**
- **Duplicate keys on the indexed side** silently lose data (later overwrites
  earlier). If the key isn't unique there, group with `defaultdict(list)` instead.
- **Both datasets are huge and won't fit in memory** → don't hand-roll this; push the
  join into a database or a tool built for out-of-core joins (e.g. pandas/Polars/SQL).
  Hash join in pure Python assumes the index fits in RAM.
- For **range or fuzzy matches** ("nearest timestamp," "price within 10%") a dict
  (exact-key) join doesn't apply — those need sorting + two pointers or interval logic.

### Where this shows up

- **Real work — enrichment/ETL:** the bread-and-butter "attach reference data to
  transactions" step in almost every data pipeline.
- **Real work — reconciliation:** match payments against invoices by `invoice_id`;
  index invoices, stream payments, and the orphans you log are exactly your
  exceptions report.
- **Real work — ML feature joins:** attach user features to event rows by `user_id`
  before training/serving.
- **Pattern mapping (secondary):** "two sum" and friends are a degenerate join (index
  seen numbers in a dict, look up the complement); database-style joins; "intersection
  of two arrays" with a dict to also carry counts.

---

## A1.5 — "Find the top N" → heapq

### The situation

Out of a large stream you need only the **few biggest (or smallest)**: the 10
highest-value orders today, the 5 slowest API calls, the 20 nearest stores to a
point. The dataset is large (millions), but **N is small** (10, 20, 100).

The obvious approach is **sort everything, then slice**:

```python
top10 = sorted(orders, key=lambda o: o.value, reverse=True)[:10]
```

It's correct and often *fine* — but you just sorted **2 million** items to keep
**10**, and if the data is a stream that doesn't all fit in memory, you can't sort
it at all.

### What's really going on

Sorting answers "what's the full order of *everything*?" — but you only asked "what
are the top 10?" You're **over-computing**: full sort is O(n log n)
("n log n" — grows a bit faster than linear; it's the cost of comparison sorting),
when the top-N question can be answered in O(n log N), and `log N` for N=10 is tiny.

The realisation: *you only ever need to remember the N best seen so far.* As you
stream, the moment you have more than N candidates, you can throw away the current
worst. The structure that makes "find and remove the current worst" cheap is a
**heap**.

### The move

Use **`heapq`** — Python's built-in **heap** (also called a **priority queue**): a
list kept in a special order so the **smallest** item is always instantly available
at the front, and inserting/removing keeps that property cheaply.

For "top N largest," keep a **min-heap of size N**: the smallest of your current
top-N sits at the front, so it's the first thing to evict when a bigger value
arrives. The single call `heapq.nlargest(N, data)` does all of this for you.

### Why it works

A heap is a binary tree flattened into a list where each parent is ≤ its children
(a **min-heap**), so the minimum is always at index 0 — readable in O(1). Push and
pop each cost O(log k) for a heap of size k, because the item only has to bubble up
or down the *height* of the tree (log k), not past every element.

For top-N you cap the heap at size N. Each of the n items does at most an O(log N)
push/pop, so total work is **O(n log N)**. With N=10, `log N ≈ 3.3` — effectively a
*single linear pass*, versus `log n ≈ 21` for a full sort of 2M items. And you only
ever hold **N** items in memory, so it works on infinite streams.

### The code, every line explained

```python
import heapq                        # the heap module (standard library).

# --- The easy door: nlargest / nsmallest --------------------------------
top10 = heapq.nlargest(10, orders, key=lambda o: o.value)
                                    # nlargest(N, iterable, key=...) returns the N
                                    # biggest items as a list, already sorted high->low.
                                    # `key` says WHAT to compare by: here each order's
                                    # .value. (lambda = a tiny inline one-expression
                                    # function; `lambda o: o.value` means "given o,
                                    # give back o.value".)
                                    # Internally keeps a size-10 heap -> O(n log 10),
                                    # and never holds more than 10 candidates.

slowest5 = heapq.nsmallest(5, calls, key=lambda c: c.duration)
                                    # nsmallest is the mirror image for the smallest N.
                                    # (For "slowest" you'd actually want nlargest on
                                    # duration; nsmallest shown just to illustrate.)

# --- Manual size-N min-heap: when data STREAMS and won't fit in memory ---
heap = []                           # a plain list, but we'll treat it as a heap.
for order in incoming_orders:       # one at a time; we never hold them all.
    heapq.heappush(heap, (order.value, order.id, order))
                                    # heappush keeps the heap ordered. We push a TUPLE
                                    # (value, id, order): heaps compare items left-to-
                                    # right, so they sort by value first. The id is a
                                    # TIE-BREAKER so Python never has to compare two
                                    # `order` objects (which may not be comparable and
                                    # would raise TypeError).
    if len(heap) > 10:              # we only want the top 10...
        heapq.heappop(heap)         # heappop removes & returns the SMALLEST item (front
                                    # of a min-heap). So we drop the current weakest,
                                    # keeping the heap at exactly the 10 largest so far.

top10 = sorted(heap, reverse=True)  # at the end, heap holds the 10 winners (unordered
                                    # among themselves); sort just those 10 for output.
top10 = [item[2] for item in top10] # pull the order object back out of each tuple.
```

### Impact

- **Speed:** O(n log N) vs O(n log n). When N ≪ n (ten out of millions) the
  difference is large and grows as the data grows.
- **Memory:** the streaming heap holds only **N** items, not all n — so it works on
  data far bigger than RAM, or on an unbounded stream. This memory property is often
  the *real* reason to use it, even more than speed.
- **Clarity:** `heapq.nlargest(10, ...)` states the intent ("top 10") far more
  directly than `sorted(...)[:10]`.

### Pros & cons / when NOT to

**Reach for a heap when:** you need the top/bottom N (N small) of a large or
streaming dataset, or a **priority queue** — "always process the highest-priority
item next" (job schedulers, Dijkstra's shortest path, merging sorted streams).

**When NOT to:**
- **You need everything sorted anyway** → just use `sorted()`; a heap doesn't help.
- **N is close to n** (top 900k of 1M) → `nlargest` actually falls back to sorting;
  no win. Heaps shine when N ≪ n.
- **You need the data sorted *out* of the heap repeatedly** and it's small/static —
  a plain sorted list may be simpler.
- **You only need the single max/min once** → just use `max()` / `min()`, O(n), no
  heap needed. A heap pays off when you need the extreme *repeatedly* as data changes.

### Where this shows up

- **Real work — "top N" everywhere:** highest-value customers, biggest error
  contributors, most-active users — dashboards and reports constantly ask for top N.
- **Real work — performance triage:** stream request logs, keep the 20 slowest, hold
  only 20 in memory regardless of log size.
- **Real work — priority job processing:** a worker pulls the highest-priority task
  next from a heap-based queue (connects to worker pools, B9.1).
- **Real work — merging sorted sources:** `heapq.merge(*sorted_streams)` lazily
  merges many pre-sorted files/streams into one sorted stream without loading them —
  classic for combining sorted daily exports.
- **Pattern mapping (secondary):** "Kth largest element," "top K frequent" (combine
  with Counter, A1.2), "merge K sorted lists," "find median from a data stream"
  (two heaps). The "Kth/top-K" family is a heap fingerprint.
