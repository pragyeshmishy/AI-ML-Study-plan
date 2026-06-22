# Area 7 — Robustness & Batch Survival

The previous areas made code *fast*. This area makes it *survive contact with the real
world*: dirty inputs, crashes halfway through a 10-hour job, jobs re-run by accident,
two processes touching the same data, and production where you can't attach a debugger.
The recurring theme: **assume things will fail, and design so failure is contained,
visible, and recoverable** — not catastrophic.

---

<a id="contents"></a>
## Contents

- [7.1 — "Bad data slipped deep into my pipeline and corrupted everything" → validate at the boundary](#7.1)
- [7.2 — "Should this error crash the program or be swallowed?" → fail loud vs fail safe](#7.2)
- [7.3 — "My except block hid the real bug for a week" → catch specific exceptions](#7.3)
- [7.4 — "The job ran twice and charged every customer twice" → idempotency](#7.4)
- [7.5 — "I re-ran the job and it redid everything from scratch" → dedupe keys & manifests](#7.5)
- [7.6 — "The training run crashed at hour 9 and I lost everything" → checkpointing](#7.6)
- [7.7 — "How do I make a long job that just continues after any interruption?" → resumable jobs](#7.7)
- [7.8 — "A crash mid-write left a half-written file that corrupts everything" → atomic writes](#7.8)
- [7.9 — "10,000 records, 12 are bad — and all 10,000 failed" → partial-failure handling](#7.9)
- [7.10 — "Is the 6-hour job still working or hung? No way to tell" → progress, ETA & heartbeats](#7.10)
- [7.11 — "Two threads incremented the counter and one update vanished" → race conditions](#7.11)
- [7.12 — "My locks are everywhere and I'm still getting bugs" → single-owner via queues](#7.12)
- [7.13 — "Production broke and my print statements told me nothing" → logging vs print](#7.13)
- [7.14 — "I hard-coded the API key and the DB URL, then leaked the key on GitHub" → config & secrets via env](#7.14)
- [7.15 — "It works on my machine but crashes in production" → reproducible environments & lockfiles](#7.15)

---


<a id="7.1"></a>
## 7.1 — "Bad data slipped deep into my pipeline and corrupted everything" → validate at the boundary

### The situation

Your pipeline ingests records from an external feed and processes them through ten
stages. A record arrives with `age: "thirty"` (a string, not a number) and `price:
-5`. Nothing checks it on the way in, so it flows through — until stage 8 does
`age * 2` and crashes, or worse, stage 6 silently writes the negative price to your
database:

```python
def ingest(record):
    save_to_db(record)              # no checks — whatever arrives goes straight in
    enqueue_for_processing(record)  # the bad record is now deep in the system
```

By the time it blows up (or silently corrupts data) you're ten stages and three systems
away from where the bad data entered, with no idea which record or feed caused it.

### What's really going on

The bad data entered at a **boundary** — the point where data crosses from outside your
control (an API, a file, user input, another team's service) into your system — and you
didn't check it there. Once unchecked data is inside, every downstream stage *assumes*
it's valid, so the failure surfaces far from the cause, and bad values can be persisted
before anything notices.

The principle is **validate at the boundary**: check and reject (or clean) data **at the
moment it enters**, so that everything inside your system can trust it. Inside, you
shouldn't need defensive checks everywhere — the boundary is the one place that enforces
the contract.

> A **boundary** is any entry point where external data arrives: an API request body, a
> file/row you parse, a queue message, a function exposed to other code. **Validation**
> = confirming the data matches the shape and rules you require (right types, required
> fields present, values in range) before you act on it — rejecting or coercing what
> doesn't.

This is the robustness counterpart to type hints (1.22): hints catch *programmer*
mistakes at edit time; boundary validation catches *data* mistakes at runtime.

### The move

Validate (and coerce) every record **at entry** against an explicit schema; reject bad
ones with a clear error before they go any further. `pydantic` is the standard tool
(also Area 3, 3.6):

```python
from pydantic import BaseModel, field_validator

class Record(BaseModel):
    age: int                              # must be (or coerce to) an int
    price: float

    @field_validator("price")
    @classmethod
    def price_non_negative(cls, v):
        if v < 0:
            raise ValueError("price must be >= 0")
        return v
```

### Why it works

`Record(**incoming)` parses the raw data against the declared types and rules **once, at
the boundary**. If `age` can't become an int or `price` is negative, it raises
immediately — with a precise message naming the field — *at the entry point*, where you
still know which record and feed it came from. Everything past that point receives a
validated `Record` and can trust `age` is an int and `price` ≥ 0, so downstream stages
need no defensive checks. Bad data is stopped at the door instead of corrupting state
ten stages in.

### The code, every line explained

```python
from pydantic import BaseModel, field_validator, ValidationError

class Record(BaseModel):
    id: str
    age: int                              # pydantic will coerce "30" -> 30, reject "thirty"
    price: float
    email: str | None = None              # optional field with a default

    @field_validator("price")
    @classmethod
    def non_negative(cls, v):             # custom rule beyond just "is a float"
        if v < 0:
            raise ValueError("price must be >= 0")
        return v

# --- validate AT the boundary (ingest), reject bad records there --------
def ingest(raw: dict):
    try:
        record = Record(**raw)            # parse + validate in one step
    except ValidationError as e:
        log.warning("rejected record %s: %s", raw.get("id"), e)   # know exactly what+why
        send_to_dead_letter(raw)          # quarantine for inspection, don't crash the feed
        return
    save_to_db(record)                    # everything downstream trusts `record`
    enqueue_for_processing(record)

# --- without a library: explicit checks at the boundary -----------------
def validate(raw):
    if not isinstance(raw.get("id"), str):        raise ValueError("id must be a string")
    try:
        age = int(raw["age"])                     # coerce; raises if "thirty"
    except (KeyError, ValueError, TypeError) as e:
        raise ValueError(f"bad age: {e}")
    price = float(raw["price"])
    if price < 0:                                 # range/business rule
        raise ValueError("price must be >= 0")
    return {"id": raw["id"], "age": age, "price": price}

# --- the principle, stated ----------------------------------------------
# Validate ONCE, at the edge. Inside the system, TRUST the validated data.
# Don't sprinkle `if isinstance(...)` through every downstream function — that's a
# sign the boundary isn't doing its job.
```

### Impact

- **Failures surface at the cause:** a bad record is caught at ingest, naming the field
  and record id — not as a cryptic crash ten stages away.
- **No silent corruption:** invalid values never reach the database/queue, so you don't
  discover the negative price weeks later in a report.
- **Simpler internals:** downstream code trusts the data and drops defensive clutter,
  because the boundary guarantees the contract.

### Pros & cons / when NOT to

**Reach for boundary validation when:** data enters your system from anywhere external —
APIs, files, queues, user input, another team's service.

**Watch out / when NOT to:**
- **Validate at the edge, not everywhere.** Re-checking the same data in every internal
  function is noise (and a sign the boundary is missing). Trust validated data inside.
- **Decide reject vs coerce per field.** Some bad data should be rejected (negative
  price); some should be cleaned (trim whitespace, parse "30" → 30). Be deliberate —
  silent coercion can hide upstream bugs.
- **Quarantine, don't crash, on bad records in a feed.** One bad record shouldn't kill
  the whole ingest — log it and route it to a dead-letter store (pairs with
  partial-failure, 7.9), so the good records keep flowing.
- **Trusted internal calls don't need heavy validation** — reserve it for true
  boundaries; over-validating internal, already-checked data adds cost for no safety.

### Where this shows up

- **Real work — API request handling:** validating request bodies (pydantic/FastAPI do
  this automatically) so handlers receive guaranteed-valid objects.
- **Real work — data ingestion/ETL:** checking each incoming row against a schema (3.6),
  quarantining bad rows to a dead-letter table instead of corrupting the warehouse.
- **Real work — ML feature pipelines:** validating feature ranges/types at ingest so a
  garbage value doesn't silently poison training (ties to data sanity checks, 3.12, and
  train/serve skew, 8.16).
- **Pattern mapping (secondary):** no DSA analogue; it's the "check preconditions at the
  trust boundary" principle — the runtime sibling of LBYL guards (1.10) applied at system
  edges.
[↑ Back to top](#contents)

---

<a id="7.2"></a>
## 7.2 — "Should this error crash the program or be swallowed?" → fail loud vs fail safe

### The situation

You're writing error handling and face the same choice repeatedly. Two examples pull in
opposite directions:

```python
# Case A: a config file required to even start the app
config = load_config("settings.yaml")     # if this is missing/broken, what should happen?

# Case B: enriching a log line with optional geo-data during a batch of 1M lines
geo = geo_lookup(ip)                       # if this one lookup fails, what should happen?
```

For Case A, silently continuing with a half-loaded config would be a disaster — the app
should **stop immediately**. For Case B, crashing the entire million-line batch because
one optional lookup failed would be absurd — it should **skip and continue**. Same
language construct (`try/except`), opposite correct behaviour.

### What's really going on

Every error handler embodies a choice between two philosophies:

- **Fail loud (fail fast):** when something is wrong, **stop and surface it** — raise,
  crash, alert. Best when continuing would produce wrong results or corrupt data, or
  when the error means a broken assumption you *must* know about.
- **Fail safe (fail soft):** when something is wrong, **degrade gracefully and keep
  going** — use a default, skip the item, return partial results. Best when the failure
  is non-critical and stopping would cause more harm than the failure itself.

The mistake is applying one philosophy everywhere. Swallowing *every* error (bare
`except: pass`) hides real bugs and corrupts data silently — the most dangerous habit in
the language. Crashing on *every* error makes a system fragile — one bad record kills a
batch. The skill is **deciding per error**: "if I continue past this, are my results
still trustworthy?" If no → fail loud. If yes → fail safe (and log it).

> **Fail loud** = let the error stop the operation and be seen (raise/alert).
> **Fail safe** = catch it, substitute a sensible fallback or skip, and continue —
> but *always record it*, so "safe" never means "silent."

### The move

Decide per error by asking "are results still trustworthy if I continue?" — fail loud
when no, fail safe (with logging) when yes:

```python
# Case A — required config: FAIL LOUD (stop now, the app can't run correctly)
config = load_config("settings.yaml")     # let it raise; don't catch and limp along

# Case B — optional enrichment: FAIL SAFE (skip, log, keep processing)
try:
    geo = geo_lookup(ip)
except GeoLookupError as e:
    log.warning("geo lookup failed for %s: %s", ip, e)   # recorded, not silent
    geo = None                            # degrade: line is still usable without geo
```

### Why it works

Matching the philosophy to the stakes keeps results trustworthy *and* the system
resilient. Failing loud on the config stops the program before it can produce wrong
output from a broken setup — the error is impossible to miss, caught in seconds rather
than as mysterious downstream nonsense. Failing safe on the optional lookup keeps the
million-line batch alive while still leaving a logged trail of what was skipped, so you
can quantify and investigate it later. Crucially, "fail safe" here is **not silent** —
the `log.warning` is what separates graceful degradation from hidden data loss.

### The code, every line explained

```python
import logging
log = logging.getLogger(__name__)

# --- FAIL LOUD: broken assumptions you MUST know about ------------------
config = load_config("settings.yaml")     # missing file -> let it raise -> app won't start
                                           # (better a loud crash now than wrong behaviour later)
assert model.n_features == data.shape[1], "feature count mismatch"   # invariant must hold

# --- FAIL SAFE: non-critical, continue with a fallback ------------------
def enrich(line):
    try:
        line.geo = geo_lookup(line.ip)     # nice-to-have, not essential
    except GeoLookupError as e:
        log.warning("geo failed for %s: %s", line.ip, e)   # RECORD it (not silent!)
        line.geo = None                    # degrade gracefully; line still processable
    return line

# --- THE DANGEROUS ANTI-PATTERN: swallow everything silently ------------
try:
    result = important_calculation()
except Exception:                          # catches EVERYTHING, including real bugs
    pass                                   # and HIDES them -> silent wrong results
# This is the worst habit in the language: a bug raises, you swallow it, the program
# carries on with corrupt/missing data and NO trace. Never `except: pass`.

# --- catch SPECIFIC exceptions, not a blanket Exception -----------------
try:
    value = int(raw)
except ValueError:                         # only the failure you EXPECT (bad number)
    value = 0                              # a genuine bug (e.g. TypeError) still surfaces
# Catching too broadly turns "fail safe" into "hide bugs". Be specific (7.3).

# --- the decision rule --------------------------------------------------
# "If I continue past this error, are my results still correct/trustworthy?"
#   NO  -> fail loud (raise/crash/alert): config, auth, invariant violations, data integrity
#   YES -> fail safe (fallback + LOG):    optional enrichment, one bad item in a batch,
#                                         a ret- ryable transient (pair with retries, 5.9)
```

### Impact

- **Trustworthy results:** failing loud where correctness depends on it means you never
  silently ship wrong output from a broken assumption.
- **Resilient batches:** failing safe on non-critical errors means one bad item/lookup
  doesn't destroy a long job — it degrades and logs instead.
- **No hidden bugs:** banning `except: pass` and catching specific exceptions keeps
  genuine bugs visible instead of swallowed.

### Pros & cons / when NOT to

**Apply the loud/safe decision to every error handler** — it's not optional; the only
mistake is not deciding and defaulting to "swallow everything."

**Watch out / when NOT to:**
- **`except: pass` (or bare `except Exception: pass`) is almost always wrong** — it hides
  real bugs and produces silent corruption. If you truly must continue, at minimum *log*
  the error (then it's fail-safe, not fail-silent).
- **Catch specific exceptions (7.3)** — a broad `except Exception` around a fail-safe
  fallback can mask a `TypeError`/`KeyError` that's actually a bug, disguising it as "just
  a skipped item."
- **Don't fail loud on the expected and routine** — a missing optional field or one bad
  row in a feed isn't a reason to crash; that's normal, handle it safe.
- **Don't fail safe on integrity-critical operations** — money movement, auth, writes
  that must be consistent. Degrading there hides corruption; fail loud and stop.
- **"Safe" requires a *sensible* fallback** — `None`/0/skip must actually be valid
  downstream (ties to truthiness traps, 1.17). A fallback that's silently wrong is worse
  than a crash.

### Where this shows up

- **Real work — startup vs runtime:** fail loud on missing config/secrets/migrations at
  startup (19.x); fail safe on transient per-request hiccups at runtime.
- **Real work — batch jobs:** fail safe per record (skip + log + dead-letter, 7.9) so a
  few bad rows don't sink a million-row job, while failing loud if the *whole input* is
  malformed (a systemic problem).
- **Real work — optional enrichment/features:** degrade gracefully when a nice-to-have
  service is down (pairs with circuit breakers/fallbacks, 5.10).
- **Pattern mapping (secondary):** no DSA analogue; it's the core error-handling judgment
  that underlies retries (5.9), validation (7.1), and partial-failure design (7.9).
[↑ Back to top](#contents)

---

<a id="7.3"></a>
## 7.3 — "My except block hid the real bug for a week" → catch specific exceptions

### The situation

You wrap a calculation in a broad try/except to be "safe", and a real bug hides inside
it for days:

```python
def parse_amount(raw):
    try:
        return float(raw["amount"])       # expect: raw might have a bad "amount" string
    except Exception:                      # catches EVERYTHING
        return 0.0                         # silently returns 0 on ANY error

# Later, someone renames the field to "total". Now raw["amount"] raises KeyError —
# but the broad except swallows it, so parse_amount silently returns 0.0 for EVERY
# record. Revenue reports read zero for a week before anyone notices.
```

You meant to handle "the amount string won't convert" (a `ValueError`). But
`except Exception` also caught the `KeyError` from the renamed field — a genuine bug —
and buried it under a plausible-looking `0.0`.

### What's really going on

A broad `except Exception` (or bare `except:`) catches **every** error, including ones
you never anticipated and that signal real bugs — a typo'd attribute (`AttributeError`),
a renamed key (`KeyError`), a `None` where you expected an object (`TypeError`). By
handling them all the same way, you convert "loud bug" into "silent wrong answer."

The fix is to **catch only the specific exception types you actually expect and know how
to handle**. Anything else should propagate — crash loudly — because an unexpected
exception *is* information: it's telling you an assumption broke.

> Python exceptions form a hierarchy (e.g. `ValueError`, `KeyError`, `TypeError` are all
> subclasses of `Exception`). Catching `ValueError` handles *only* value-conversion
> failures; a `KeyError` then sails past your handler and surfaces — exactly what you
> want for an unforeseen problem. Catching `Exception` flattens that distinction and
> swallows everything.

### The move

Catch the **narrowest** exception type(s) you actually expect; let everything else
propagate:

```python
def parse_amount(raw):
    try:
        return float(raw["amount"])
    except (KeyError, ValueError) as e:   # ONLY the failures you anticipate + can handle
        log.warning("bad amount in %s: %s", raw.get("id"), e)   # and log it
        return 0.0
# A renamed field now raises KeyError -> caught HERE and logged loudly (not silent 0s);
# an unforeseen TypeError still propagates and crashes -> you find the real bug fast.
```

### Why it works

By naming the exceptions you expect, the handler only fires for *those* — and you log
them, so even handled errors are visible. Any exception you *didn't* anticipate isn't
caught: it propagates up the stack with its full traceback, crashing loudly at (or near)
the cause. That's the desired behaviour for a bug — fast, visible failure (7.2, fail
loud) beats a plausible wrong answer. The week-long silent-zero incident becomes either
a logged warning (if it really is a bad amount) or an immediate crash with a traceback
pointing at the renamed field.

### The code, every line explained

```python
import logging
log = logging.getLogger(__name__)

# --- catch SPECIFIC, expected exceptions; log them ----------------------
try:
    value = float(raw["amount"])
except KeyError as e:                      # the field is missing
    raise ValueError(f"record missing 'amount': {raw.get('id')}") from e
    # `from e` keeps the original cause in the traceback (exception chaining) — you
    # see BOTH what you raised and the KeyError underneath it.
except ValueError:                         # the field exists but won't convert
    value = 0.0                            # a sensible, expected fallback

# --- the spectrum, worst to best ----------------------------------------
try: ...
except: pass                               # WORST: catches everything (even
                                           # KeyboardInterrupt/SystemExit), hides all bugs
try: ...
except Exception: pass                     # BAD: catches all normal errors, silent bugs
try: ...
except Exception as e: log.exception(e)    # OK-ish: at least it's LOGGED with a traceback
try: ...
except (KeyError, ValueError) as e: ...    # GOOD: only what you expect, handled + logged

# --- when a broad catch IS legitimate: a top-level safety net -----------
def worker(item):
    try:
        return process(item)
    except Exception:                      # acceptable HERE because we...
        log.exception("item %r failed", item)   # ...LOG the full traceback (not silent)
        return None                        # ...and isolate one item in a batch (6.10/7.9)
# A broad catch is fine ONLY at a boundary where you log fully and deliberately isolate
# failures — never as a quiet `pass` that discards the error.

# --- log.exception vs log.warning ---------------------------------------
# log.exception(...) inside an except block automatically includes the full traceback —
# use it so a swallowed error still leaves a complete trail to the cause.
```

### Impact

- **Bugs stay visible:** unforeseen errors crash loudly with a traceback instead of being
  buried under a fallback — you find them in minutes, not after a week of wrong reports.
- **Handlers do what they say:** an `except ValueError` block clearly handles *only* bad
  values, so a reader knows exactly what's anticipated.
- **Safe fallbacks stay safe:** narrow catching means your "return 0.0 on bad input"
  can't accidentally also mean "return 0.0 on a typo'd attribute."

### Pros & cons / when NOT to

**Catch specifically whenever you use try/except** — it's the default discipline, not an
optimisation.

**Watch out / when NOT to:**
- **Never `except: pass` or `except Exception: pass`** — the silent-bug machine. If you
  must catch broadly, *log the full traceback* (`log.exception`) so it's not silent.
- **A broad `except Exception` is acceptable only at deliberate boundaries** — a
  top-level request/worker handler that logs fully and isolates one unit's failure
  (6.10/7.9). Not in the middle of business logic.
- **Bare `except:` is worse than `except Exception:`** — it also catches
  `KeyboardInterrupt` and `SystemExit`, so you can't even Ctrl-C the program. Never use
  it.
- **Use `raise ... from e`** when re-raising, to preserve the original cause in the
  traceback (exception chaining) — don't discard the underlying error.
- **Don't over-narrow either** — if three sibling exceptions all mean "bad input here,"
  catch them as a tuple `(KeyError, ValueError, TypeError)` rather than missing one.

### Where this shows up

- **Real work — parsing/ingestion:** catch `ValueError`/`KeyError` on a specific field,
  let unexpected errors surface — so a schema change crashes loudly instead of producing
  silent zeros (pairs with boundary validation, 7.1).
- **Real work — API/DB clients:** catch the specific `Timeout`/`ConnectionError`/HTTP
  errors you retry (5.9), not a blanket `Exception` that would also swallow a bug in your
  own request-building code.
- **Real work — batch workers:** a logged, broad catch at the per-item boundary to
  isolate failures (6.10/7.9), with narrow catches inside the actual logic.
- **Pattern mapping (secondary):** no DSA analogue; it's the precision half of error
  handling that makes fail-loud/fail-safe (7.2) actually work as intended.
[↑ Back to top](#contents)

---

<a id="7.4"></a>
## 7.4 — "The job ran twice and charged every customer twice" → idempotency

### The situation

A nightly job sends invoices. It crashes halfway, so you re-run it — and customers who
were already invoiced get a **second** invoice. Or a retry (5.9) resends a request the
server already processed, creating a duplicate order:

```python
def send_invoice(customer):
    charge_card(customer.id, customer.amount)   # if this ran before, it charges AGAIN
    email_invoice(customer)

# Re-run after a crash, or a retry, or an at-least-once queue redelivery ->
# charge_card fires a SECOND time. Double charge.
```

The operation isn't safe to repeat. But repetition is *unavoidable* in real systems —
retries, crash-and-rerun, queues that deliver "at least once", a user double-clicking.
So the operation must be made safe to run more than once.

### What's really going on

The operation has a **side effect** (charging, inserting, sending) that *accumulates* on
repetition. You need it to be **idempotent**: running it twice has the **same effect as
running it once**. Then retries, re-runs, and duplicate deliveries become harmless — the
foundation that makes retry logic (5.9) and resumable jobs (7.7) actually safe.

> **Idempotent** = repeating the operation produces the same result as doing it once.
> Reading is naturally idempotent; "set X to 5" is idempotent (running it again leaves X
> at 5); "add 1 to X" is **not** (each run changes the result). The goal is to turn
> not-naturally-idempotent writes (charge, insert, send) into idempotent ones.

The standard mechanism is an **idempotency key**: a unique id for the *logical*
operation (not the attempt). The system records which keys it has already processed and
**skips or de-duplicates** repeats. "Charge for invoice #9876" carries key `invoice-9876`;
the first time it charges and records the key; any repeat sees the key and does nothing.

### The move

Give each logical operation a stable **idempotency key**, record processed keys, and
skip repeats — or use an operation that's idempotent by construction:

```python
def send_invoice(customer):
    key = f"invoice-{customer.invoice_id}"      # stable id for the LOGICAL operation
    if already_done(key):                        # seen this key before?
        return                                   # repeat -> do nothing (safe)
    charge_card(customer.id, customer.amount, idempotency_key=key)
    mark_done(key)                               # record so future runs skip it
```

### Why it works

The key identifies the *operation*, not the *attempt*, so every retry/re-run of "invoice
#9876" carries the same `invoice-9876`. The first execution charges and records the key;
any subsequent execution finds the key already recorded and returns without charging — so
N runs have the effect of exactly one. Payment APIs support this directly via an
`idempotency_key` header: the *provider* de-duplicates, so even a charge that succeeded
but whose response you never received (the classic retry ambiguity) won't double-charge.
For database writes, the same idea is an **upsert** keyed on a unique column — insert if
new, no-op/update if it exists — idempotent by construction.

### The code, every line explained

```python
# --- App-level idempotency: record processed keys -----------------------
def send_invoice(customer):
    key = f"invoice-{customer.invoice_id}"       # NOT a random per-attempt id — stable!
    if processed_store.exists(key):              # e.g. a row in a DB / Redis set
        log.info("invoice %s already sent, skipping", key)
        return
    charge_card(customer.id, customer.amount, idempotency_key=key)  # provider also dedupes
    email_invoice(customer)
    processed_store.add(key)                     # mark done AFTER success
# Re-run, retry, or duplicate delivery -> the exists() check makes repeats no-ops.

# --- Database upsert: idempotent by construction ------------------------
# "INSERT ... ON CONFLICT (id) DO NOTHING"  (Postgres) or INSERT OR IGNORE (SQLite):
cur.execute(
    "INSERT INTO orders (id, customer, amount) VALUES (%s, %s, %s) "
    "ON CONFLICT (id) DO NOTHING",               # id already there -> no duplicate row
    (order.id, order.customer, order.amount),
)
# Running this twice with the same order.id inserts ONE row. Idempotent.

# --- The ordering subtlety: when do you record the key? -----------------
# mark_done AFTER the side effect succeeds -> a crash BETWEEN charge and mark_done
# could still double-charge on rerun. For true safety, make the side effect ITSELF
# carry the key (provider idempotency_key / upsert), so even that gap is covered.
# Pure app-level "check then act" also has a race under concurrency (7.12) — use a
# unique DB constraint / atomic op so two workers can't both pass the check.

# --- Natural idempotency: prefer "set" over "increment" -----------------
status = "paid"      # SET status -> running twice still "paid"  (idempotent)
# balance += amount  # ADD -> running twice double-counts        (NOT idempotent)
```

### Impact

- **Safe retries & re-runs:** the thing that makes retry/backoff (5.9), at-least-once
  queues, and crash-and-rerun (7.7) usable without fear of duplicates — you can re-run a
  failed job freely.
- **No duplicate side effects:** no double charges, double orders, double emails — the
  failures that erode user trust and cause financial/data damage.
- **Composes with everything in this area:** idempotency is the precondition that lets
  checkpointing (7.6), resumable jobs (7.7), and skip-done manifests (7.10) work
  correctly.

### Pros & cons / when NOT to

**Make an operation idempotent when:** it has side effects (writes, charges, sends,
external calls) **and** it could ever be retried, re-run, or redelivered — which, in
practice, is essentially all of them.

**Watch out / when NOT to:**
- **The key must identify the *logical operation*, not the attempt.** A new random key
  per retry defeats the whole purpose — every retry looks "new". Derive it from stable
  data (invoice id, order id, a content hash, 4.4).
- **Check-then-act has a race under concurrency** (7.12) — two workers can both pass
  `exists()` before either records the key. Enforce idempotency with a **unique
  constraint / atomic upsert / provider key**, not just an app-level if-check, when
  concurrency is possible.
- **Mind the crash window.** If you record the key *after* the side effect, a crash in
  between can still duplicate on rerun. Pushing the key *into* the side effect (provider
  idempotency_key, upsert) closes that gap.
- **Reads/pure functions are already idempotent** — don't add machinery where there are
  no accumulating side effects.
- **Prefer "set"-style operations over "accumulate"** where you can — they're idempotent
  for free.

### Where this shows up

- **Real work — payments & orders:** idempotency keys on charge/refund/create-order calls
  so retries and double-submits never duplicate money movement (payment APIs mandate
  this).
- **Real work — message/queue consumers:** "at-least-once" delivery means you *will* get
  duplicates; idempotent handlers (dedupe by message/event id) are required — same as
  webhook handling (5.17).
- **Real work — batch/ETL jobs:** upserts keyed on a natural id so re-running a failed
  job doesn't duplicate rows (pairs with resumable jobs, 7.7, and skip-done, 7.10).
- **Pattern mapping (secondary):** the "have I seen this key?" dedupe is the set-membership
  pattern (Area 3, 3.13) applied to side effects; idempotent "set" vs non-idempotent "add"
  mirrors choosing operations with the right algebraic properties.
[↑ Back to top](#contents)

---

<a id="7.5"></a>
## 7.5 — "I re-ran the job and it redid everything from scratch" → dedupe keys & manifests

### The situation

A job processes 100,000 documents — embed each and write to a vector store. It finishes
80,000, then fails. You fix the bug and re-run:

```python
for doc in all_documents():           # all 100,000, every run
    vec = embed(doc)                  # re-embeds the 80,000 ALREADY done -> wasted time + cost
    vector_store.upsert(doc.id, vec)
```

The re-run starts from zero — re-embedding the 80,000 already-completed docs, wasting
hours and (for a paid embedding API) real money, before it even reaches the 20,000 that
still need doing.

### What's really going on

The job has no memory of **what it already completed**, so every run repeats all the
work. Idempotency (7.4) makes redoing *safe* (no duplicate rows), but it doesn't make it
*cheap* — you still pay to recompute. To re-run efficiently you need a record of
completed units so the job can **skip what's already done** and process only the
remainder.

The mechanism is a **manifest** (or dedupe-key store): a persistent record of the keys of
units already processed. Before doing a unit, check the manifest; if its key is there,
skip it. This makes a re-run resume the *work* (not just avoid duplicate side effects),
turning a failed-and-restarted job into "process the remaining 20,000."

> A **manifest** here = a durable list/set of identifiers for completed work units
> (a file of ids, a DB table, a Redis set). A **dedupe key** is the stable id of one
> unit (doc id, or a content hash, 4.4). "Skip if key in manifest" + "add key after
> success" = cheap, safe re-runs. (This is the cost-saving complement to idempotency,
> 7.4, and the basis of resumable jobs, 7.7.)

### The move

Keep a durable manifest of completed keys; skip any unit already in it, and append its
key right after it succeeds:

```python
done = load_done_keys("done.txt")          # set of ids completed in prior runs
for doc in all_documents():
    if doc.id in done:                      # already processed in an earlier run?
        continue                            # skip — no recompute, no cost
    vector_store.upsert(doc.id, embed(doc))
    append_done_key("done.txt", doc.id)     # record success durably, immediately
```

### Why it works

The manifest persists across runs, so a restart loads the set of completed ids and the
`if doc.id in done: continue` check skips them in O(1) (set membership, 3.13) — the
re-run does only the ~20,000 outstanding units. Appending each key *immediately after*
its unit succeeds (not at the end) means even a second crash only loses at most the
in-flight unit, and the *next* re-run picks up from there. Combined with idempotent
writes (7.4), this is robust: skipping handles the common case cheaply, and idempotency
covers the edge where a unit completed but its key wasn't recorded before the crash.

### The code, every line explained

```python
# --- File-based manifest (simple, durable, good for single-process jobs) -
def load_done_keys(path):
    try:
        with open(path) as f:
            return set(line.strip() for line in f)   # O(1) membership later (3.13)
    except FileNotFoundError:
        return set()                                 # first run: nothing done yet

def append_done_key(path, key):
    with open(path, "a") as f:                       # "a" = append; survives restarts
        f.write(key + "\n")
        f.flush()                                    # push to OS now, don't buffer
        # for max durability: os.fsync(f.fileno()) to force disk write before continuing

def run():
    done = load_done_keys("done.txt")
    for doc in all_documents():
        if doc.id in done:                           # skip completed units
            continue
        vector_store.upsert(doc.id, embed(doc))      # idempotent write (7.4)
        append_done_key("done.txt", doc.id)          # mark done AFTER success
# Re-run: only the remaining ~20,000 docs are processed. Hours/£ saved.

# --- DB manifest (better under concurrency / many workers, 6.x) ---------
# A 'processed(id PRIMARY KEY)' table; INSERT the id after success.
# Workers check membership with a SELECT, or rely on the unique constraint to dedupe
# (atomic — avoids the check-then-act race, 7.12, that a plain set has).

# --- content-hash keys: detect CHANGED inputs ---------------------------
import hashlib
def key_for(doc):
    return hashlib.sha256(doc.text.encode()).hexdigest()   # (4.4)
# Keying on a content HASH (not just id) means an EDITED document gets a new key and is
# reprocessed, while unchanged ones are skipped — useful for incremental re-runs.

# --- the ordering rule (same as 7.4) ------------------------------------
# Record the key only AFTER the unit's work succeeds. Recording before risks marking
# failed units as done; the small remaining crash-window is covered by idempotency (7.4).
```

### Impact

- **Cheap re-runs:** a failed job restarts and does only the outstanding work — minutes
  instead of re-processing everything, and no re-spend on paid APIs.
- **Incremental processing:** with content-hash keys, only new/changed inputs are
  processed on each run — the basis of incremental pipelines.
- **Confidence to re-run:** "just run it again" becomes a safe, cheap default after any
  failure (pairs with idempotency, 7.4).

### Pros & cons / when NOT to

**Reach for a manifest/dedupe store when:** a batch job is long, expensive, or likely to
be interrupted and re-run — especially with paid per-unit costs (embeddings, API calls).

**Watch out / when NOT to:**
- **Record keys *after* success, and make writes idempotent (7.4)** — so the crash
  window (done-but-not-recorded) can't cause duplicates *or* lost work.
- **A plain in-memory/file set has a check-then-act race under concurrency (7.12)** —
  multiple workers can both pass the skip check. Use a DB unique constraint / atomic
  insert as the manifest when many workers share it.
- **The manifest itself must be durable** — flush/fsync file appends, or use a DB; a
  manifest lost on crash defeats the purpose.
- **Keys must be stable and correct.** A random key per run never matches; an id that
  doesn't reflect content won't catch *changed* inputs (use a content hash if you need
  that). Wrong keys silently skip work that should run.
- **For truly huge key sets**, an in-memory set may not fit — use a DB/Redis or a Bloom
  filter; don't load 500M ids into RAM.

### Where this shows up

- **Real work — embedding/ingestion pipelines:** skip already-embedded documents on
  re-run so a failure doesn't re-bill the whole corpus (Area 9 RAG ingestion).
- **Real work — ETL backfills:** a manifest of processed partitions/files so a restarted
  backfill resumes instead of redoing terabytes.
- **Real work — incremental syncs:** content-hash keys to reprocess only records that
  changed since the last run.
- **Pattern mapping (secondary):** it's set-membership dedup (3.13) made durable and
  applied to *work units* — the persistent cousin of "have I seen this?" (A1.1) and the
  engine behind resumable jobs (7.7).
[↑ Back to top](#contents)

---

<a id="7.6"></a>
## 7.6 — "The training run crashed at hour 9 and I lost everything" → checkpointing

### The situation

A long-running computation builds up state over hours — a model training for 12 hours,
or an aggregation accumulating over a billion rows. It crashes near the end (an OOM, a
spot-instance reclaim, a transient error) and **all the accumulated progress is gone**:

```python
model = Model()
for epoch in range(100):              # 12 hours total
    train_one_epoch(model, data)      # progress lives ONLY in memory
# crash at epoch 87 -> model state vanishes -> start again from epoch 0
```

The work that *was* done (87 epochs of learned weights) existed only in memory, so the
crash erased it. Re-running means redoing those 9 hours from scratch.

### What's really going on

In-memory progress is **volatile** — a crash, kill, or power loss wipes it. For any
long job, you need to periodically **save the accumulated state to durable storage**, so
that after a failure you can **reload the last saved state and continue** instead of
restarting.

This is **checkpointing**: at intervals, write a snapshot of the job's state (model
weights + optimiser state + which epoch; or the partial aggregation + position in the
input) to disk/object storage. On restart, load the latest checkpoint and resume from
there.

> A **checkpoint** = a durable snapshot of everything needed to resume a job mid-flight.
> The art is choosing *what* to save (all state required to continue correctly) and *how
> often* (often enough to bound lost work, rare enough that saving doesn't dominate
> runtime). Where 7.5's manifest tracks *which discrete units are done*, checkpointing
> saves *continuous accumulated state* — and together they enable resumable jobs (7.7).

### The move

Periodically save all state needed to resume; on startup, load the latest checkpoint and
continue from there:

```python
start_epoch = 0
if checkpoint_exists():
    model, optimizer, start_epoch = load_checkpoint()   # resume where we left off

for epoch in range(start_epoch, 100):
    train_one_epoch(model, data)
    save_checkpoint(model, optimizer, epoch + 1)        # durable snapshot each epoch
```

### Why it works

Each `save_checkpoint` writes the *complete* resumable state to durable storage, so a
crash loses at most the work since the last save (one epoch here), not the whole run. On
restart, `load_checkpoint` restores that state and the loop resumes from `start_epoch` —
the 87 completed epochs are preserved. The key correctness detail is saving **everything
needed to continue**: for training that's not just the model weights but the **optimiser
state** (momentum/learning-rate schedule) and the epoch counter — omit the optimiser and
the resumed run trains differently than an uninterrupted one would.

### The code, every line explained

```python
import torch, os, tempfile

CKPT = "checkpoint.pt"

def save_checkpoint(model, optimizer, epoch):
    state = {
        "epoch": epoch,                          # WHERE to resume
        "model": model.state_dict(),             # learned weights
        "optimizer": optimizer.state_dict(),     # momentum/LR state — MUST save, or
                                                 # resumed training diverges from uninterrupted
    }
    # atomic write (7.8): write to temp, then rename, so a crash mid-save can't leave
    # a half-written checkpoint that fails to load.
    fd, tmp = tempfile.mkstemp(dir=".")
    torch.save(state, tmp)
    os.replace(tmp, CKPT)                        # atomic rename: old ckpt valid until this

def load_checkpoint(model, optimizer):
    state = torch.load(CKPT)
    model.load_state_dict(state["model"])
    optimizer.load_state_dict(state["optimizer"])
    return state["epoch"]                        # resume point

# --- resume-aware training loop -----------------------------------------
start_epoch = load_checkpoint(model, optimizer) if os.path.exists(CKPT) else 0
for epoch in range(start_epoch, 100):
    train_one_epoch(model, data)
    save_checkpoint(model, optimizer, epoch + 1) # bound lost work to one epoch

# --- non-ML example: checkpoint a long aggregation ----------------------
# Save {partial_totals, last_row_index} every N rows; on restart, reload and continue
# from last_row_index instead of re-scanning the billion rows from the start.

# --- choosing frequency: bound lost work vs save overhead ---------------
# Too rare  -> a crash loses a lot of progress.
# Too often -> saving (serialising GBs of weights) dominates runtime.
# Rule of thumb: checkpoint so that the MOST you can lose is acceptable (e.g. every
# epoch, or every N minutes) — and keep the LAST few checkpoints, not just one (so a
# crash DURING a save doesn't leave you with zero valid checkpoints).
```

### Impact

- **Bounds lost work:** a crash costs only the work since the last checkpoint (one
  epoch), not the entire run — hours saved on every failure.
- **Survives interruptions:** spot/preemptible instances, deploys, and OOM-kills become
  recoverable, enabling cheap interruptible compute for long jobs.
- **Enables resumability:** checkpoints are the state half of resumable jobs (7.7),
  combined with progress tracking to know where to continue.

### Pros & cons / when NOT to

**Reach for checkpointing when:** a job runs long enough that losing its progress to a
crash is painful — model training, large aggregations, multi-hour simulations/backfills.

**Watch out / when NOT to:**
- **Save *everything* needed to resume**, not just the obvious part. For training, the
  optimiser state and epoch/step counter matter as much as weights; a partial checkpoint
  resumes *incorrectly*, which is worse than not resuming.
- **Write checkpoints atomically (7.8).** A crash *during* a save can leave a truncated,
  unloadable file — write to a temp path and `os.replace`, and keep the previous
  checkpoint until the new one is complete.
- **Keep more than one checkpoint.** If you overwrite the only checkpoint and crash
  mid-write, you have nothing. Rotate the last few.
- **Tune frequency.** Too frequent and serialising large state dominates runtime; too
  rare and you lose a lot on crash. Match the interval to acceptable lost-work.
- **Short/cheap jobs don't need it** — if a re-run from scratch is quick, checkpointing
  is needless complexity.

### Where this shows up

- **Real work — model training:** every serious training loop checkpoints
  weights+optimiser+step so a crash or preemption doesn't waste GPU-hours (Area 9, 9.5).
- **Real work — long aggregations/backfills:** snapshotting partial results + input
  position so a billion-row job resumes mid-stream.
- **Real work — spot/preemptible compute:** checkpointing is what makes cheap
  interruptible instances usable for long jobs — you expect to be killed and resume.
- **Pattern mapping (secondary):** no DSA analogue; it's the durable-state-snapshot
  principle, paired with progress tracking (7.5) to form resumable jobs (7.7), and
  reliant on atomic writes (7.8) for safety.
[↑ Back to top](#contents)

---

<a id="7.7"></a>
## 7.7 — "How do I make a long job that just continues after any interruption?" → resumable jobs

### The situation

You're designing a 6-hour job that processes 100,000 items, and you want it to survive
*any* interruption — crash, deploy, Ctrl-C, machine reboot — by simply being re-run and
**continuing from where it stopped**, not restarting. You've met the pieces separately
(idempotency 7.4, manifest 7.5, checkpointing 7.6); now you need to combine them into one
coherent **resumable** design:

```python
def run_job(items):
    for item in items:                # 100,000 items, 6 hours
        process(item)                 # interrupted at item 62,000 -> re-run starts at 0?
```

The question is the *pattern*: what does a job need so that "just run it again" reliably
resumes rather than redoes or duplicates?

### What's really going on

A **resumable job** is one whose correct behaviour on re-run is "continue", achieved by
combining three properties this area already covered:

1. **Track progress durably** (7.5) — a manifest of completed item keys, or a saved
   position/cursor, so the job knows what's done.
2. **Make each unit idempotent** (7.4) — so the one in-flight unit at crash time, which
   may have half-completed, is safe to redo.
3. **Checkpoint accumulated state** (7.6) — if the job builds up state (totals, a model),
   snapshot it so it isn't rebuilt from scratch.

Put together: on startup, **load progress/state; skip what's done; process the rest;
record each completion durably and atomically.** The result is a job where re-running is
always safe and always cheap, regardless of *when* or *how* it was interrupted.

> A **resumable job** = progress tracking (where am I?) + idempotency (safe to redo the
> boundary unit) + checkpointing (don't rebuild accumulated state). The design goal: the
> *only* operational response to a failure is "run it again," and it Just Works.

### The move

Compose the three properties into one loop: load progress, skip done, process remaining,
record each completion durably:

```python
def run_job(items):
    done = load_done_keys()                  # 7.5: durable progress
    for item in items:
        if item.id in done:                  # skip completed
            continue
        process_idempotent(item)             # 7.4: safe even if half-done before a crash
        record_done(item.id)                 # durable, atomic (7.8), AFTER success
```

### Why it works

The loop is interruption-proof by construction. **Skip** (via the manifest, 7.5) means
already-completed items aren't redone — cheap resume. **Idempotent** processing (7.4)
means the single item that was mid-flight when the crash hit is safe to run again on
restart — no duplicate side effect. **Durable, atomic recording** (7.8) of each
completion means the progress record itself survives the crash and can't be left
half-written. Whatever moment the job dies — between items, mid-item, mid-record — the
next run lands in a consistent state and continues. Accumulated state (if any) is handled
by checkpointing (7.6) the same way.

### The code, every line explained

```python
import os, tempfile

# --- progress store (7.5): durable set of completed keys ----------------
def load_done_keys(path="progress.txt"):
    try:
        with open(path) as f:
            return set(l.strip() for l in f)     # O(1) skip checks (3.13)
    except FileNotFoundError:
        return set()

def record_done(key, path="progress.txt"):
    with open(path, "a") as f:
        f.write(key + "\n"); f.flush(); os.fsync(f.fileno())   # durable before continuing

# --- the resumable loop -------------------------------------------------
def run_job(items):
    done = load_done_keys()
    for item in items:
        if item.id in done:                      # (7.5) already processed -> skip
            continue
        process_idempotent(item)                 # (7.4) upsert / idempotency-key write
        record_done(item.id)                     # (7.8) record AFTER success, durably
    # Interrupted ANY time -> re-run resumes: done-set skips the rest, idempotency
    # covers the one in-flight item, fsync'd progress survives the crash.

# --- with accumulated state, add checkpointing (7.6) --------------------
def run_aggregation(rows):
    totals, start = load_checkpoint()            # (7.6) resume partial state + position
    for i, row in enumerate(rows[start:], start):
        update(totals, row)
        if i % 10_000 == 0:
            save_checkpoint(totals, i)           # snapshot every 10k rows (atomic, 7.8)
    finalise(totals)

# --- a graceful-shutdown nicety (ties to 7.x signal handling) -----------
# Catch SIGTERM/Ctrl-C to finish the current item and record it before exiting, so you
# stop on a CLEAN boundary rather than mid-item — fewer redos on the next run.

# --- the design checklist -----------------------------------------------
# [ ] progress tracked durably?      (skip done -> cheap resume)        7.5
# [ ] each unit idempotent?          (boundary unit safe to redo)       7.4
# [ ] accumulated state checkpointed?(don't rebuild from scratch)       7.6
# [ ] progress/checkpoint writes atomic & flushed? (survive crash)      7.8
# All four -> "just re-run it" always works.
```

### Impact

- **"Just re-run it" always works:** any interruption — crash, deploy, preemption,
  Ctrl-C — is recovered by re-running, with no manual cleanup and no duplicated effects.
- **Cheap recovery:** resume does only the outstanding work and keeps accumulated state,
  so a failure near the end costs minutes, not the whole run.
- **Operable systems:** jobs become safe to retry from cron/orchestrators automatically,
  the foundation of reliable batch infrastructure.

### Pros & cons / when NOT to

**Design for resumability when:** a job is long, expensive, or runs on interruptible
infrastructure — anything where a from-scratch restart is costly or where re-runs are
routine (cron, retries, orchestrators).

**Watch out / when NOT to:**
- **All three properties are needed together.** Progress tracking without idempotency can
  duplicate the in-flight unit; idempotency without progress tracking is safe but
  re-does everything (slow). Skipping checkpointing rebuilds accumulated state. Audit all
  four checklist items.
- **The progress/checkpoint writes must be durable *and* atomic (7.8)** — flush/fsync,
  and write-then-rename. A progress file that's buffered (lost on crash) or half-written
  breaks resume.
- **Watch the crash window** between "did the work" and "recorded it done" — idempotency
  (7.4) is what makes that window safe; don't rely on ordering alone.
- **Under concurrency (7.12), the progress store needs atomic dedupe** (DB unique
  constraint), not a plain file set, or two workers double-process the boundary items.
- **Don't over-engineer short jobs** — if a full restart is quick and side-effect-free,
  resumability is needless machinery.

### Where this shows up

- **Real work — large ingestion/embedding jobs:** the standard design for "embed 10M docs"
  so any interruption resumes cheaply without re-billing (combines 7.4/7.5/7.6; Area 9).
- **Real work — ETL backfills & migrations:** resumable by partition/cursor so a
  multi-hour migration restarts mid-way, not from zero.
- **Real work — interruptible/preemptible compute:** training and batch jobs on spot
  instances are *designed* to be killed and resumed (checkpointing + progress).
- **Pattern mapping (secondary):** no DSA analogue; it's the synthesis pattern of this
  area — idempotency (7.4) + durable progress (7.5) + checkpointing (7.6) + atomic writes
  (7.8) composed into one fault-tolerant design.
[↑ Back to top](#contents)

---

<a id="7.8"></a>
## 7.8 — "A crash mid-write left a half-written file that corrupts everything" → atomic writes

### The situation

Your job writes results to a file. It crashes (or is killed) **while writing** — and now
there's a truncated, half-written file on disk that *looks* like a real output:

```python
with open("results.json", "w") as f:
    json.dump(huge_results, f)        # crash MID-WRITE -> results.json is half-written
# Next run reads results.json -> invalid JSON, or worse, VALID-looking but truncated data
```

The partial file is the trap: a downstream reader either errors on the corrupt JSON, or
— more dangerously — reads it as if it were complete and silently works with truncated
data. And if this *overwrote* a previously-good file, the good version is gone too.

### What's really going on

Writing a file is **not atomic** — it happens incrementally, so a crash can leave the
file in a partial, inconsistent state. Anything reading that path can't tell "complete"
from "half-written." For outputs, checkpoints (7.6), and progress files (7.5), you need
the write to be **all-or-nothing**: either the new content is fully there, or the old
content is untouched — never a torn middle state.

The standard technique is **write-to-temp-then-rename**: write the full new content to a
*temporary* file, then **atomically rename** it over the destination. On the same
filesystem, `os.replace` (rename) is **atomic** — the destination path points at either
the old file or the fully-written new one, with no observable in-between. A crash during
the temp write leaves the temp file as garbage (deletable) but the real destination
untouched.

> **Atomic** = the operation either fully happens or not at all, with no partial state
> visible to others. File *content writes* aren't atomic, but a *rename* on the same
> filesystem is — which is why "write temp, then rename" gives you an atomic file
> update.

### The move

Write to a temp file in the same directory, flush it to disk, then `os.replace` it over
the destination:

```python
import os, tempfile, json

def atomic_write_json(path, data):
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d)            # temp file on the SAME filesystem
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
        f.flush(); os.fsync(f.fileno())          # force bytes to disk before the rename
    os.replace(tmp, path)                        # ATOMIC: dest = old OR fully-new, never torn
```

### Why it works

The destination path is only updated by the final `os.replace`, which is atomic on the
same filesystem — so any reader sees either the previous complete file or the new
complete file, never a half-written one. If the crash happens during the temp write, the
temp file is incomplete but the real destination still holds the last good version
(nothing lost). The `flush()` + `os.fsync()` before the rename force the OS to actually
write the bytes to disk first — without it, the rename could complete while the new
content is still in a buffer, so a power loss could leave the renamed file empty. Temp
file *in the same directory* matters because rename is only atomic within one filesystem.

### The code, every line explained

```python
import os, tempfile, json

def atomic_write_json(path, data):
    directory = os.path.dirname(path) or "."
    # mkstemp creates a unique temp file in the SAME dir (so rename stays on one FS)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:            # wrap the low-level fd as a file object
            json.dump(data, f)                   # write the FULL content to the temp file
            f.flush()                            # push from Python buffer to OS
            os.fsync(f.fileno())                 # force OS buffer -> physical disk
        os.replace(tmp, path)                    # atomic rename: dest now = complete new file
    except BaseException:
        os.unlink(tmp)                           # clean up the temp file on any failure
        raise
# Crash during json.dump -> tmp is garbage, `path` still holds the last good file.
# Crash after os.replace -> `path` is the complete new file. No torn state either way.

# --- the WRONG way (what corrupts files) --------------------------------
with open("results.json", "w") as f:             # opening "w" TRUNCATES immediately:
    json.dump(huge, f)                           # the old good file is gone the instant
                                                 # we open; a crash now -> empty/partial file

# --- this is exactly how checkpoints (7.6) and progress (7.5) stay safe -
# save_checkpoint() and the manifest writer use this same temp+rename so an
# interrupted save never destroys the previous valid checkpoint/progress.

# --- note: directories and fsync ----------------------------------------
# For maximum durability you can also fsync the DIRECTORY after rename so the rename
# itself is persisted; usually os.replace + the file fsync is enough for "not torn".
```

### Impact

- **No corrupt outputs:** readers always see a complete file — a crash mid-write can't
  produce truncated-but-valid-looking data that silently poisons downstream steps.
- **Old version preserved on failure:** an interrupted write leaves the previous good
  file intact, so you never lose working output to a failed overwrite.
- **Makes checkpoints/progress trustworthy:** atomic writes are what let checkpointing
  (7.6), manifests (7.5), and resumable jobs (7.7) rely on their saved files surviving a
  crash.

### Pros & cons / when NOT to

**Reach for atomic writes when:** writing files that matter and could be read by others
or re-read after a crash — outputs, checkpoints, progress files, caches, config you
generate.

**Watch out / when NOT to:**
- **Temp file must be on the same filesystem** as the destination (same directory is the
  safe default) — a rename *across* filesystems is a copy, which is **not** atomic.
- **`fsync` matters for power-loss durability.** Skipping it risks the rename landing
  while content is still buffered; include it for checkpoints/progress where a crash
  must not lose the bytes.
- **Append-style logs/manifests are different** — for an append-only progress file (7.5),
  you append+flush per line rather than rewrite the whole file; atomic-replace is for
  *whole-file* updates.
- **Doesn't make multi-file updates atomic** — if a consistent state spans several files,
  you need a different mechanism (write all temps, rename in a safe order, or use a DB
  transaction).
- **For structured/relational data, a database transaction** gives atomicity more simply
  than hand-rolled file swaps — don't reinvent it for data that belongs in a DB.

### Where this shows up

- **Real work — model checkpoints:** saving weights via temp+rename so a crash mid-save
  doesn't destroy the last good checkpoint (7.6; every robust training loop does this).
- **Real work — generated outputs/exports:** writing a report/dataset atomically so
  consumers never pick up a half-written file (pairs with streamed downloads, 5.19, which
  write to temp then rename on completion).
- **Real work — progress/manifest & cache files:** keeping resumable-job bookkeeping
  (7.5/7.7) intact across crashes.
- **Pattern mapping (secondary):** no DSA analogue; it's the durability/atomicity
  primitive underpinning checkpointing (7.6), resumable jobs (7.7), and any
  crash-safe persistence.
[↑ Back to top](#contents)

---

<a id="7.9"></a>
## 7.9 — "10,000 records, 12 are bad — and all 10,000 failed" → partial-failure handling

### The situation

A batch job processes 10,000 records. Twelve of them are malformed. The job either
crashes on the first bad one (losing the other 9,988), or — if wrapped in one big
try/except — abandons the *whole* batch when any record fails:

```python
def process_batch(records):
    for r in records:
        transform_and_save(r)         # record #97 raises -> the loop dies, 9,903 unprocessed
# OR:
def process_batch(records):
    try:
        for r in records:
            transform_and_save(r)
    except Exception:
        return "batch failed"         # ALL 10,000 thrown away because 12 were bad
```

Both treat the batch as all-or-nothing. But the correct outcome is obvious: process the
9,988 good records, and **separately** collect the 12 bad ones for inspection — don't let
a 0.12% bad-data rate destroy a whole batch.

### What's really going on

At scale, **some inputs will always be bad** — and that's normal, not exceptional. The
job should be designed so a per-item failure is **contained to that item**: catch it,
record it (which record, what error), and **keep going** with the rest. The failures
aren't ignored — they're routed to a **dead-letter** store (a quarantine list/table of
failed items with their errors) for later inspection or reprocessing.

This is the batch-level expression of fail-safe (7.2) and specific-exception handling
(7.3), and the same isolation idea as parallel worker failures (6.10): the unit of
failure is the **item**, not the **batch**. A good batch job's output is two streams:
*successes* (processed) and *failures* (quarantined with reasons) — plus a summary count.

> **Partial failure** = some units in a batch fail while others succeed; the design goal
> is to **isolate** failures per item, **record** them (dead-letter), and **complete** the
> rest, rather than all-or-nothing. A **dead-letter queue/store** holds the failed items
> + error so they can be examined and reprocessed without blocking the batch.

### The move

Wrap each item individually; collect successes and failures into separate streams, and
report both:

```python
def process_batch(records):
    succeeded, failed = [], []
    for r in records:
        try:
            succeeded.append(transform_and_save(r))
        except Exception as e:                  # isolate THIS item's failure
            failed.append({"record": r, "error": repr(e)})
    log.info("batch: %d ok, %d failed", len(succeeded), len(failed))
    if failed:
        write_dead_letter(failed)               # quarantine bad ones for inspection
    return succeeded, failed
```

### Why it works

The `try/except` is *inside* the loop, around one item — so a failure aborts only that
iteration's body, and the loop continues to the next record. The 9,988 good records are
processed and the 12 bad ones land in `failed` with their error text, ready to write to a
dead-letter store. Nothing is silently lost: you get both streams plus a count, so the
batch "succeeds" (does its job for the valid data) while the failures are visible and
recoverable. A spike in the failure count also becomes a signal — if 4,000 of 10,000
fail, that's not "bad rows," it's a systemic bug to investigate (not quarantine).

### The code, every line explained

```python
import logging
log = logging.getLogger(__name__)

def process_batch(records):
    succeeded, failed = [], []
    for r in records:
        try:
            result = transform_and_save(r)       # idempotent (7.4) so retries are safe
            succeeded.append(result)
        except (ValueError, KeyError) as e:      # specific expected bad-data errors (7.3)
            failed.append({"id": r.get("id"), "record": r, "error": repr(e)})
            # NOTE: do NOT re-raise — that would abort the batch. Contain it here.
    # report BOTH outcomes — never just "done"
    log.info("processed %d ok, %d failed (%.2f%%)",
             len(succeeded), len(failed), 100 * len(failed) / max(len(records), 1))
    if failed:
        write_dead_letter(failed)                # quarantine: a file/table of bad items
    return succeeded, failed

# --- the dead-letter store: failures you can inspect & reprocess --------
def write_dead_letter(failed, path="dead_letter.jsonl"):
    with open(path, "a") as f:                   # append; one JSON record per line (3.2)
        for item in failed:
            f.write(json.dumps(item) + "\n")
# Later: read dead_letter.jsonl, fix the cause, and REPROCESS just those items
# (idempotency, 7.4, makes reprocessing safe; manifest, 7.5, avoids redoing the good ones).

# --- guard against SYSTEMIC failure masquerading as "bad rows" ----------
rate = len(failed) / max(len(records), 1)
if rate > 0.10:                                  # >10% failing isn't bad data — it's a bug
    raise RuntimeError(f"abort: {rate:.0%} of batch failed — likely systemic")
    # fail LOUD (7.2) when the failure rate says the assumption, not the data, is broken.

# --- parallel version: same idea with as_completed (6.9/6.10) -----------
# In a process/thread pool, wrap each fut.result() in try/except and append to
# succeeded/failed — isolation per task instead of per loop iteration.
```

### Impact

- **Good data isn't held hostage:** 9,988 records get processed instead of zero — the
  batch does its job despite a few bad inputs.
- **Failures are visible and recoverable:** the dead-letter store records *which* items
  failed and *why*, so you can fix the cause and reprocess just those (safely, via
  idempotency 7.4).
- **Data-quality signal:** the failure count/rate surfaces problems — a sudden spike
  triggers a loud abort instead of silently quarantining thousands.

### Pros & cons / when NOT to

**Design for partial failure when:** processing batches of real-world data where some
inputs are expected to be malformed — ingestion, ETL, bulk API calls, parallel jobs.

**Watch out / when NOT to:**
- **Don't silently drop failures** — "skip and forget" hides data-quality issues.
  Quarantine with the error (dead-letter) and report a count; "skip and *record*" is the
  rule (7.2).
- **Set a failure-rate threshold that fails loud.** A few bad rows are normal; a large
  fraction failing means a systemic bug (wrong schema, broken upstream) — abort loudly
  rather than quarantining millions (7.2).
- **Catch specific exceptions per item (7.3)** — a blanket `except Exception` per item is
  acceptable for isolation *only if* you log the type/message, so genuine bugs aren't
  disguised as "just another bad record."
- **Some batches truly must be all-or-nothing** — e.g. a financial posting where partial
  application corrupts a ledger. Those need a transaction (all-or-nothing by design), not
  per-item isolation.
- **Make reprocessing safe** — dead-letter items will be retried; ensure idempotency
  (7.4) so reprocessing doesn't duplicate the successes.

### Where this shows up

- **Real work — data ingestion/ETL:** process valid rows, route invalid ones to a
  dead-letter table with errors — the standard pattern (pairs with boundary validation,
  7.1, which is where many of these failures are caught).
- **Real work — bulk API/queue processing:** "at-least-once" consumers dead-letter
  messages they can't process after retries (5.9), keeping the stream flowing.
- **Real work — parallel batch jobs:** per-item isolation in worker pools so one bad item
  doesn't sink the run (6.10), with failures collected for a report.
- **Pattern mapping (secondary):** no DSA analogue; it's the batch-scale fault-isolation
  principle — contain failure at the smallest unit — shared with circuit breakers (5.10)
  and worker-failure isolation (6.10).
[↑ Back to top](#contents)

---

<a id="7.10"></a>
## 7.10 — "Is the 6-hour job still working or hung? No way to tell" → progress, ETA & heartbeats

### The situation

You kick off a job over 2 million records. An hour passes with **no output**. Is it
making progress? Stuck on a slow record? Deadlocked? Silently doing nothing? You have no
way to know without killing it:

```python
def run(records):
    for r in records:                 # 2,000,000 of them, hours of work
        process(r)                    # ...total silence the entire time...
    print("done")                     # the ONLY output, at the very end (if it ever comes)
```

A long job that emits nothing is indistinguishable from a hung job — so you can't tell
whether to wait or intervene, and you can't estimate when it'll finish.

### What's really going on

The job has no **observability**: it doesn't report what it's doing while it runs. For
anything long, you need periodic signals of (a) **progress** — how many done, how fast,
and an **ETA** (estimated time remaining); and (b) **liveness** — a **heartbeat** proving
it's still alive and advancing, not wedged.

These answer different questions: progress/ETA is for *you* (should I wait 5 minutes or 5
hours?); a heartbeat is for *monitoring* (alert if no progress for N minutes → it's
hung). Without them, a long job is a black box, and the only way to "check" is to kill it
— which destroys the very progress you were unsure about.

> **Progress reporting** = periodic "X of N done, rate, ETA" output. **ETA** = items
> remaining ÷ current rate. **Heartbeat** = a regular "still alive at item X" signal
> (log line, metric, touched file, or DB timestamp) that monitoring watches; a stalled
> heartbeat means the job hung. (This is the operational sibling of logging, 7.14, and
> metrics, which the next scenarios cover.)

### The move

Emit periodic progress with an ETA (use `tqdm` for a quick bar, or log every N items),
and a heartbeat monitoring can watch:

```python
from tqdm import tqdm
for r in tqdm(records, desc="processing"):   # live bar: count, rate, and ETA, free
    process(r)
```

### Why it works

`tqdm` wraps the iterable and, on each step, updates a live display of count, items/sec,
and an ETA computed from the running rate — so "is it progressing and when will it
finish?" is answered at a glance, with one line of code. For headless jobs (cron,
servers, no terminal), you instead **log every N items** with the same count/rate/ETA,
which doubles as a heartbeat: monitoring alerts if no progress line appears for N minutes,
catching a hang. The ETA is just `remaining / rate`; a heartbeat is just "emit a liveness
signal on a regular cadence" — both turn the black box into something you can reason
about and alert on.

### The code, every line explained

```python
# --- Quick interactive progress: tqdm (count + rate + ETA, one line) ----
from tqdm import tqdm
for r in tqdm(records, desc="embedding", total=len(records)):
    process(r)                               # bar shows: 45%|####  | 900k/2M [03:12<03:55, 4.6k/s]
    #                                          ^progress  ^done/total ^elapsed<ETA, ^rate

# --- Headless/logged progress (cron, servers): log every N items --------
import time, logging
log = logging.getLogger(__name__)

def run(records):
    total = len(records)
    start = time.monotonic()
    for i, r in enumerate(records, 1):
        process(r)
        if i % 10_000 == 0 or i == total:    # report periodically, not every item
            elapsed = time.monotonic() - start
            rate = i / elapsed               # items per second so far
            eta = (total - i) / rate         # remaining items / rate = seconds left
            log.info("progress %d/%d (%.1f%%) | %.0f items/s | ETA %.0f min",
                     i, total, 100 * i / total, rate, eta / 60)
            # This line is ALSO the heartbeat: monitoring watches for it; if it stops
            # appearing for, say, 15 min, alert that the job has stalled.

# --- Heartbeat for monitoring (when there's no obvious progress to log) -
def heartbeat(item_index):
    # touch a file / write a timestamp to a DB / push a metric, on a regular cadence.
    with open("heartbeat.txt", "w") as f:    # atomic-ish liveness marker (or push a metric)
        f.write(f"{time.time()} at item {item_index}")
# An external watchdog checks heartbeat.txt's age; too old -> the job is hung -> alert/restart.

# --- pair with checkpointing/resume (7.6/7.7) ---------------------------
# Log progress AND checkpoint at the same interval, so the progress you SEE matches the
# state you could RESUME from after a crash.
```

### Impact

- **Black box → observable:** you can tell at a glance whether a long job is progressing,
  how fast, and when it'll finish — so you know whether to wait or intervene.
- **Hangs get detected:** a stalled heartbeat triggers an alert/restart instead of a job
  silently doing nothing for hours.
- **Planning & SLAs:** an ETA lets you decide if a job will meet a deadline (e.g. finish
  before a merge freeze) while it's still running, not after.

### Pros & cons / when NOT to

**Add progress + heartbeats when:** a job runs long enough that silence is
indistinguishable from a hang — batch processing, training, large ETL, anything over a
few minutes.

**Watch out / when NOT to:**
- **Don't log every item** — at 2M items, per-item logging floods logs and *slows the
  job* (I/O per item). Report every N items or every N seconds.
- **ETA is an estimate, not a promise** — it assumes a steady rate; uneven workloads make
  early ETAs unreliable. Use a moving-average rate, or just present it as approximate.
- **A heartbeat must reflect *real* progress**, not just "the process is running." A
  process stuck in an infinite loop is "alive" but not progressing — tie the heartbeat to
  *items completed*, so a stalled counter reveals the hang.
- **`tqdm` is for terminals** — in logs/cron it produces messy output; use logged
  progress lines there instead.
- **Don't over-instrument trivial jobs** — a 3-second script needs no progress bar.

### Where this shows up

- **Real work — data/embedding pipelines:** a `tqdm` bar or logged progress on the
  "process N million records" loop, so you know it's alive and when it'll finish (Area 9).
- **Real work — training loops:** per-epoch/step progress + ETA, with heartbeats so a
  hung GPU job is detected rather than silently wasting hours (Area 9).
- **Real work — scheduled/cron jobs:** logged progress lines double as heartbeats that
  monitoring/alerting watch to catch stalls (ties to logging, 7.14).
- **Pattern mapping (secondary):** no DSA analogue; it's the observability practice that
  makes long-running work operable — complementary to logging (7.14) and the foundation
  for alerting on stalls.
[↑ Back to top](#contents)

---

<a id="7.11"></a>
## 7.11 — "Two threads incremented the counter and one update vanished" → race conditions

### The situation

Several threads (5.2) each process items and increment a shared counter. At the end, the
total is **less** than the number of items processed — some increments silently
disappeared:

```python
counter = 0
def worker(items):
    global counter
    for _ in items:
        counter += 1                  # looks atomic, ISN'T — updates get lost

# 8 threads, 1,000,000 increments total -> final counter often < 1,000,000 (!)
```

The arithmetic is trivially correct, yet the result is wrong, *non-deterministically* —
run it again and you get a different (still-too-low) number. Nothing raised an error;
data just quietly went missing.

### What's really going on

`counter += 1` is **not a single, indivisible step** — it's really three: **read** the
current value, **add** one, **write** it back. With multiple threads, these steps can
**interleave**: thread A reads 100, thread B reads 100 (before A writes), both compute
101, both write 101 — two increments, but the counter advanced by one. One update was
lost. This is a **race condition**: the result depends on the unpredictable *timing* of
concurrent operations on shared mutable state.

> A **race condition** = a bug where the outcome depends on the relative timing of
> concurrent operations accessing **shared mutable state**, producing wrong/inconsistent
> results non-deterministically. The vulnerable region — the read-modify-write that must
> not be interleaved — is called a **critical section**.

Races appear wherever concurrent execution touches shared mutable data: threads (5.2)
sharing a dict/list/counter, multiple processes/workers updating the same DB row or file,
or the check-then-act gap in idempotency (7.4) and manifests (7.5). They're insidious
because they're **timing-dependent** — tests pass, then it fails rarely in production
under load, and is hard to reproduce.

### The move

Protect the critical section so only one thread can read-modify-write at a time — with a
**lock** (1.3) — or, better, avoid shared mutable state entirely (7.13):

```python
import threading
counter = 0
lock = threading.Lock()

def worker(items):
    global counter
    for _ in items:
        with lock:                    # only ONE thread in here at a time
            counter += 1              # read-modify-write is now indivisible
```

### Why it works

The `with lock:` block makes the read-modify-write **mutually exclusive**: a thread must
acquire the lock to enter, and any other thread that reaches it **waits** until the lock
is released. So the three steps (read, add, write) can't interleave across threads — each
increment completes fully before the next begins, and no updates are lost. The `with`
statement (1.3) guarantees the lock is released even if the body raises, preventing a
deadlock from a stuck lock. The cost is that threads serialise on that section — which is
why you keep critical sections *small* and, where possible, avoid sharing altogether.

### The code, every line explained

```python
import threading

# --- Lock: serialise the critical section -------------------------------
counter = 0
lock = threading.Lock()
def worker(items):
    global counter
    for _ in items:
        with lock:                    # acquire; others block until release
            counter += 1              # the critical section — now atomic across threads
        # keep the locked region MINIMAL: do slow work (I/O, compute) OUTSIDE the lock,
        # or you serialise everything and lose the concurrency.

# --- BETTER for counting: each thread counts locally, combine at the end -
def worker_local(items):
    local = 0
    for _ in items:
        local += 1                    # NO shared state -> no lock, no contention
    return local                      # combine the per-thread totals afterwards
totals = [worker_local(chunk) for chunk in chunks]   # (in a pool, collect results, 6.9)
final = sum(totals)                                  # one combine step, race-free

# --- BEST where applicable: don't share — return results, combine -------
# Have each worker RETURN its data and combine in ONE place (the main thread). No shared
# mutable state means no races at all. (This is 7.13 — sidestep locking via ownership.)

# --- multi-PROCESS / multi-machine races: a lock won't help -------------
# A threading.Lock is in-process only. Across processes or machines (workers updating
# the SAME DB row), use the database's atomicity:
#   UPDATE accounts SET balance = balance + 10 WHERE id = 1;   -- atomic in the DB
# or SELECT ... FOR UPDATE / a unique constraint / an atomic increment — NOT a read in
# Python then a write back (that re-creates the race across processes).

# --- the check-then-act race (ties to 7.4/7.5) --------------------------
# if key not in seen:        # thread A and B BOTH see "not in"...
#     seen.add(key); charge()# ...both charge. Use an atomic op / unique constraint, not
#                            # a Python-level check-then-act, when concurrency is possible.
```

### Impact

- **Correct results under concurrency:** no lost updates, no inconsistent shared state —
  the counter actually equals the number of increments.
- **Deterministic behaviour:** removes the timing-dependent, hard-to-reproduce bugs that
  pass tests and fail randomly in production.
- **Points toward better designs:** recognising races pushes you to local accumulation or
  no-shared-state designs (7.13) that avoid locking overhead entirely.

### Pros & cons / when NOT to

**Guard shared mutable state when:** multiple threads read-modify-write the same object,
counter, or collection concurrently.

**Watch out / when NOT to:**
- **Prefer avoiding shared state over locking it.** Local accumulation + combine (above),
  returning results from workers (6.9), or a thread-safe `queue.Queue` (5.6/7.13)
  sidestep races without lock contention. Reach for a lock only when sharing is
  unavoidable.
- **Keep critical sections tiny.** Holding a lock during slow work (I/O, heavy compute)
  serialises your threads and kills concurrency — lock only the read-modify-write.
- **Locks can deadlock.** Acquiring multiple locks in inconsistent orders can freeze
  threads waiting on each other (7.x deadlock); always use `with` (auto-release) and a
  consistent lock-ordering, or avoid multiple locks.
- **A `threading.Lock` is process-local** — useless across processes/machines. For
  multi-process or DB-row races, use database atomicity (atomic `UPDATE`, `SELECT FOR
  UPDATE`, unique constraints), not an in-process lock.
- **multiprocessing rarely needs locks for results** — workers have separate memory;
  return results and combine (6.9) instead of sharing.

### Where this shows up

- **Real work — threaded aggregation/counters:** any shared total/dict updated by
  multiple threads (5.2) — guard it, or accumulate locally and combine.
- **Real work — concurrent writes to one row:** multiple workers updating the same
  account balance / inventory count — use an atomic DB update, not read-then-write.
- **Real work — the idempotency/manifest race (7.4/7.5):** check-then-act on a shared
  "seen" set under concurrency needs an atomic op / unique constraint, not a Python
  if-check.
- **Pattern mapping (secondary):** no DSA analogue; it's the core concurrency-correctness
  problem, and it motivates the lock-free, single-owner designs in 7.12 (and the
  queue-based handoffs in 5.6).
[↑ Back to top](#contents)

---

<a id="7.12"></a>
## 7.12 — "My locks are everywhere and I'm still getting bugs" → single-owner via queues

### The situation

Your threaded program shares several mutable structures — a results dict, a counter, a
log buffer — and you've sprinkled locks (7.11) to protect them. It's now hard to reason
about: did you lock *every* access? Are two locks ever acquired in opposite orders
(deadlock risk)? A subtle bug still slips through where one access forgot the lock:

```python
results = {}; lock_r = threading.Lock()
counts = {};  lock_c = threading.Lock()
# every worker must remember to take the RIGHT lock for EVERY access... one miss = a race
def worker(item):
    with lock_r: results[item.id] = process(item)
    with lock_c: counts[item.type] += 1     # forget this lock once -> silent race (7.11)
```

Every shared structure multiplies the chances of a forgotten lock, a wrong lock, or a
deadlock. The locking *works* in principle but is fragile and hard to verify.

### What's really going on

Locks make shared mutable state *safe* but not *simple* — correctness depends on every
access, everywhere, taking the right lock in the right order, which humans get wrong. A
more robust design **removes the sharing**: instead of many threads mutating one
structure, **one thread owns the structure** and is the only one allowed to touch it.
Other threads don't mutate it — they **send messages** (via a thread-safe queue, 5.6)
to the owner, which applies the changes serially.

This is the **single-owner / message-passing** model: *don't communicate by sharing
memory; share memory by communicating.* The queue (`queue.Queue`) is already thread-safe,
so there are **no locks to manage** and **no races** — only one thread ever writes the
state, so its updates can't interleave.

> **Single-owner pattern:** one thread exclusively owns a piece of mutable state; all
> others send it work/updates through a thread-safe **queue**. Because only the owner
> mutates the state, concurrent access is impossible by construction — eliminating
> races (7.11) and the lock-management burden entirely.

### The move

Give the shared state one owner thread; other threads push updates onto a queue the owner
drains:

```python
import queue, threading
updates = queue.Queue()               # thread-safe channel to the owner

def owner():                          # the ONLY thread that touches `state`
    state = {}
    while (msg := updates.get()) is not None:   # drain until sentinel (1.18 walrus)
        state[msg["id"]] = msg["value"]         # serial, single-threaded -> no races
```

### Why it works

Only `owner` ever reads or writes `state`, so its updates execute one at a time, in
order — there's no concurrency *on the state itself*, hence no race and no lock needed.
Worker threads never touch `state`; they just `updates.put(msg)`, and `queue.Queue`
handles all the cross-thread synchronisation internally (it's thread-safe by design). The
result is the same concurrency benefit (many workers running at once) with the
correctness burden collapsed to a single, easy-to-verify rule: *only the owner mutates
the state.* You've traded "lock every access correctly everywhere" for "route every
update through one door."

### The code, every line explained

```python
import queue, threading

# --- single owner of the results state ----------------------------------
results_q = queue.Queue()             # workers -> owner channel (thread-safe, no locks)
DONE = object()                       # sentinel: "no more messages" (5.6)

def collector():                      # the SOLE owner/mutator of `results` and `counts`
    results, counts = {}, {}
    while True:
        msg = results_q.get()         # blocks until a message arrives
        if msg is DONE:
            break
        results[msg["id"]] = msg["value"]     # serial writes -> impossible to race
        counts[msg["type"]] = counts.get(msg["type"], 0) + 1
    save(results, counts)             # owner produces the final combined state

def worker(items):
    for item in items:
        value = process(item)         # heavy work happens in the worker (concurrent)
        results_q.put({"id": item.id, "value": value, "type": item.type})  # just SEND
        # NOTE: no lock, no shared dict access here — only a queue put.

# --- wire up: N workers + 1 owner ---------------------------------------
owner = threading.Thread(target=collector); owner.start()
workers = [threading.Thread(target=worker, args=(chunk,)) for chunk in chunks]
for w in workers: w.start()
for w in workers: w.join()            # wait for all producers to finish
results_q.put(DONE)                   # then tell the owner to stop
owner.join()

# --- contrast with the lock-heavy version (7.11) ------------------------
# lock-based: every worker mutates shared dicts, each guarded by the correct lock,
#             every access, forever — one omission = a race; two locks = deadlock risk.
# single-owner: workers never mutate shared state; ONE rule to uphold. Far easier to
#               get right and to reason about.

# --- the same idea elsewhere --------------------------------------------
# - Have workers RETURN results; combine in ONE place (6.9) — no owner thread needed.
# - asyncio (5.4): one event-loop thread owns state; tasks message via asyncio.Queue.
# - Actor model / Go channels / a DB as the single writer — all the same principle.
```

### Impact

- **Races eliminated by construction:** since only one thread mutates the state, there's
  nothing to interleave — no lost updates, no timing bugs, regardless of how many
  workers run.
- **No lock-management burden:** no remembering which lock guards what, no lock-ordering
  rules, no deadlocks — the queue is the only synchronisation, and it's already correct.
- **Easier to reason about and test:** the invariant "only the owner touches the state"
  is a single, checkable rule, versus auditing every access site for correct locking.

### Pros & cons / when NOT to

**Reach for single-owner/queues when:** multiple threads would otherwise share several
mutable structures, or when lock-based code has become hard to verify or deadlock-prone.

**Watch out / when NOT to:**
- **The owner can become a bottleneck** — all updates funnel through one thread. Fine when
  applying an update is cheap (dict write, counter bump); if the owner does heavy work per
  message, it serialises and limits throughput. Keep the owner's per-message work light.
- **The queue can grow unbounded** if workers outpace the owner — use a bounded
  `queue.Queue(maxsize=...)` for backpressure (5.6) so producers slow down rather than
  exhausting memory.
- **Shutdown needs care** (sentinels/`task_done`/`join`) — same discipline as
  producer/consumer (5.6); a missed sentinel hangs the owner.
- **Often you don't even need an owner thread** — having workers *return* results and
  combining them in one place (6.9) achieves the same "no shared mutation" with less
  machinery. Prefer that when the work is a pure map.
- **Cross-process/machine state** isn't solved by an in-process queue — use a real queue
  service or a database as the single writer (ties to 7.11's multi-process note).

### Where this shows up

- **Real work — concurrent aggregation:** workers compute and send partial results to one
  collector that owns the totals — no locks, no races (the robust alternative to 7.11's
  locked counter).
- **Real work — a single writer to a file/DB:** many producer threads, one writer thread
  draining a queue, so the output isn't interleaved/corrupted and needs no write lock.
- **Real work — async services:** the event loop (5.4) is inherently single-threaded;
  tasks pass messages via `asyncio.Queue` rather than sharing locked state — the same
  principle built into the model.
- **Pattern mapping (secondary):** this is the **actor / message-passing** concurrency
  model (Go channels, Erlang actors); the queue is a FIFO (BFS-style structure, Area 11)
  used to serialise access — "share memory by communicating."
[↑ Back to top](#contents)

---

<a id="7.13"></a>
## 7.13 — "Production broke and my print statements told me nothing" → logging vs print

### The situation

Your code uses `print` for diagnostics. In development it's fine. In production it falls
apart: the output has no timestamps, no severity, no source — and you can't *turn it
down* or *filter* it:

```python
def process(order):
    print(f"processing {order.id}")          # no time, no level, no module — just text
    if order.amount < 0:
        print("WARNING: negative amount")    # how do you find this among 10M lines?
    result = charge(order)
    print(f"done {order.id}")                # floods stdout; can't disable in prod
```

When something breaks at 2 a.m., you have a wall of undifferentiated text with no
timestamps to correlate events, no way to filter to just errors, and no control over
verbosity — so you can't answer "what happened, when, and how bad was it?"

### What's really going on

`print` writes plain strings to stdout with **no metadata and no control**. Production
diagnostics need structure and configurability: **when** (timestamp), **how severe**
(level), **where** (module/function), and the ability to **filter by severity** and
**route** output (to files, aggregators, etc.) *without editing code*. That's what the
**logging** module provides.

> The **`logging`** module emits records with a **timestamp**, a **severity level**
> (DEBUG < INFO < WARNING < ERROR < CRITICAL), and the **source** (logger name/module).
> You set a **level threshold** (e.g. show WARNING and above) to control verbosity
> centrally, and **handlers** route records to destinations (console, file, remote) —
> all configured once, not sprinkled through the code.

The levels are the key idea: you label each message by importance, then in production set
the threshold to INFO or WARNING (hiding noisy DEBUG) and crank it to DEBUG only when
investigating — *the same code*, different verbosity, no edits. `print` has none of this.

### The move

Use a module-level logger with levels, configured once at startup:

```python
import logging
log = logging.getLogger(__name__)            # one logger per module, named by module

def process(order):
    log.info("processing order %s", order.id)        # INFO: normal flow
    if order.amount < 0:
        log.warning("negative amount on %s", order.id)   # WARNING: notable, not fatal
    log.debug("charge response: %r", charge(order))      # DEBUG: hidden unless investigating
```

### Why it works

`getLogger(__name__)` gives each module its own named logger, so every record carries its
source. Calling `log.info/warning/error` tags the message with a **level**; a single
config at startup sets the threshold (show INFO+ in prod, DEBUG when debugging) and the
format (timestamp, level, module) — so you get correlatable, filterable output *without
touching the call sites*. The `%s`/`%r` placeholders are filled **lazily** — only if the
message is actually emitted at the current level — so a `log.debug(...)` in a hot loop
costs nothing when DEBUG is off (unlike an f-string, which always builds the string,
1.11). Handlers can route the same records to a file, the console, or a log aggregator,
configured once.

### The code, every line explained

```python
import logging

# --- configure ONCE, at program startup (not in libraries) --------------
logging.basicConfig(
    level=logging.INFO,                       # threshold: INFO and above shown (DEBUG hidden)
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    #        timestamp   level        module    the message  -> correlatable, filterable
)

# --- per-module logger --------------------------------------------------
log = logging.getLogger(__name__)             # name = module path; identifies the source

def process(order):
    log.debug("raw order: %r", order)         # only emitted if level <= DEBUG (off in prod)
    log.info("processing %s", order.id)        # %s filled LAZILY — not built if INFO is off
    try:
        charge(order)
    except PaymentError:
        log.exception("charge failed for %s", order.id)  # ERROR + full traceback (7.3)
        #   log.exception() = log.error() PLUS the current exception's stack trace
        raise

# --- the levels and when to use them ------------------------------------
# DEBUG    : detailed internal state, for investigating — noisy, off in prod
# INFO     : normal milestones — "started", "processed N", progress (7.10)
# WARNING  : something odd but handled — a retry, a skipped bad record (7.9)
# ERROR    : an operation failed — use log.exception() inside except for the traceback
# CRITICAL : the program can't continue — fail loud (7.2)

# --- why not print -------------------------------------------------------
# print("processing", order.id)   # no timestamp, no level, no source, can't filter,
#                                 # can't disable, can't route to a file/aggregator.
# print is for command-line TOOL OUTPUT meant for a user; logging is for DIAGNOSTICS.

# --- lazy formatting: prefer %-args over f-strings IN log calls ---------
log.debug("expensive %s", compute_summary())  # compute_summary() STILL runs (it's an arg)
# True saving is for the STRING build: log.debug("x=%s", x) builds nothing if DEBUG off,
# whereas log.debug(f"x={x}") always builds the string. (1.11 noted this.)

# --- libraries: get a logger, DON'T configure -------------------------- 
# In reusable code, only `log = logging.getLogger(__name__)` and log away.
# Let the APPLICATION call basicConfig/dictConfig — libraries that configure logging
# stomp on the app's setup.
```

### Impact

- **Debuggable production:** timestamped, levelled, sourced records let you reconstruct
  "what happened, when, how bad" and correlate events across a run — impossible with bare
  prints.
- **Controllable verbosity:** flip the threshold to DEBUG to investigate, back to INFO/
  WARNING for normal operation — same code, no edits, no redeploy of changed prints.
- **Routable & integrable:** the same records flow to files, rotating logs, or
  aggregators (ELK, CloudWatch, Datadog) via handlers — the basis for searching and
  alerting (ties to metrics/structured logging).

### Pros & cons / when NOT to

**Use logging when:** the code runs unattended — services, batch jobs, anything in
production or scheduled. Essentially all non-throwaway code.

**Watch out / when NOT to:**
- **Configure logging once, in the application, not in libraries.** A library that calls
  `basicConfig` overrides the app's logging setup. Libraries should only *get* a logger
  and emit.
- **Use the right level** — logging everything at INFO floods logs and hides real signal;
  reserve WARNING/ERROR for things worth attention so alerts mean something.
- **`log.exception()` only inside an `except` block** — it attaches the current
  traceback; calling it elsewhere logs "NoneType: None". Use `log.error(...)` outside
  except.
- **Prefer `%s`-style lazy args over f-strings in log calls** — the string is built only
  if emitted; matters in hot paths with DEBUG logging (1.11).
- **Don't log secrets/PII** — tokens, passwords, personal data don't belong in logs
  (security + privacy); redact them (ties to usage accounting, 5.20).
- **`print` is still right for CLI tools** whose *purpose* is to print output for a user —
  logging is for diagnostics, not user-facing program output.

### Where this shows up

- **Real work — every service and batch job:** structured, levelled logs are how you
  operate and debug anything running unattended (and they carry the progress/heartbeat
  lines from 7.10).
- **Real work — incident debugging:** filtering to ERROR, correlating by timestamp, and
  reading tracebacks (`log.exception`) to find a 2 a.m. failure's cause.
- **Real work — log aggregation/alerting:** routing records to a central system to search
  across machines and alert on error spikes — the next step beyond a single log file.
- **Pattern mapping (secondary):** no DSA analogue; it's the foundational observability
  practice, paired with progress/heartbeats (7.10) and the precursor to structured
  logging and metrics in production systems.
[↑ Back to top](#contents)

---

<a id="7.14"></a>
## 7.14 — "I hard-coded the API key and the DB URL, then leaked the key on GitHub" → config & secrets via env

### The situation

Your code has connection details and credentials written directly in the source:

```python
DB_URL = "postgres://admin:hunter2@prod-db.internal:5432/app"   # hard-coded!
API_KEY = "sk-live-9f8a7b6c5d4e3f2a1b0c"                         # SECRET in source!

def main():
    db = connect(DB_URL)
    client = ApiClient(API_KEY)
```

Two problems. The **secret** (API key, DB password) is now in your git history forever —
push to GitHub and it's leaked, scannable by bots within minutes. And the **config**
(which DB, which environment) is baked in, so running against staging vs production means
*editing code* — and you'll eventually run a test against the prod database by accident.

### What's really going on

You've **mixed configuration and secrets into the code**. They should be **external**:
the same code artifact should run in dev/staging/prod by reading *different values from
its environment*, and secrets should never touch source control. This is the core of the
**12-factor** app principle: *store config in the environment.*

> **Configuration** = values that vary by where the code runs (DB URL, log level,
> feature toggles, endpoints). **Secrets** = sensitive credentials (API keys, passwords,
> tokens). Both should come from **environment variables** (or a secrets manager) at
> runtime — read via `os.environ` — not be hard-coded. The code stays identical across
> environments; only the environment's values differ.

Hard-coding fails three ways: secrets leak (git history is forever), you can't change
environments without code edits (and risk pointing dev at prod), and the same build can't
be promoted dev→staging→prod (defeating reproducible deploys). Externalising config fixes
all three.

### The move

Read config and secrets from environment variables at startup; keep a local `.env`
(git-ignored) for development:

```python
import os
DB_URL  = os.environ["DATABASE_URL"]          # required: crash loudly if missing (7.2)
API_KEY = os.environ["API_KEY"]               # secret: from env, never in source
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")   # optional: default if unset
```

### Why it works

`os.environ["DATABASE_URL"]` reads the value the *environment* provides at runtime — so
the identical code connects to the dev DB on your laptop, staging in CI, and prod in
deployment, purely because each environment sets a different value. Secrets live in the
environment (or a secrets manager), never in the repo, so they can't leak via git and can
be rotated without a code change. Using `os.environ[...]` (not `.get`) for *required*
values makes a missing config **fail loudly at startup** (7.2) — far better than a
cryptic failure later. For local dev, a git-ignored `.env` file loaded by
`python-dotenv` supplies the values without exporting them by hand.

### The code, every line explained

```python
import os

# --- required values: fail loud if absent (7.2) -------------------------
try:
    DB_URL  = os.environ["DATABASE_URL"]      # KeyError at startup if not set -> obvious
    API_KEY = os.environ["API_KEY"]
except KeyError as e:
    raise RuntimeError(f"missing required env var: {e}") from e   # clear, loud failure

# --- optional values: default with .get ---------------------------------
LOG_LEVEL  = os.environ.get("LOG_LEVEL", "INFO")          # safe default if unset
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "100"))      # env values are STRINGS — cast!
DEBUG      = os.environ.get("DEBUG", "false").lower() == "true"
            # NOTE: env vars are strings; "false" is TRUTHY (1.17)! Compare explicitly,
            # never `if os.environ.get("DEBUG")` (that's True for the string "false").

# --- local development: a git-ignored .env file -------------------------
# .env  (NEVER commit this — add it to .gitignore):
#   DATABASE_URL=postgres://localhost:5432/dev
#   API_KEY=sk-test-localdevkey
from dotenv import load_dotenv
load_dotenv()                                  # loads .env into os.environ for local runs
# In real deployment, the platform (k8s secrets, CI vars, cloud secrets manager) sets
# the env vars — load_dotenv is just for local convenience.

# --- structured config with pydantic-settings (typed + validated) -------
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    database_url: str                          # required; reads DATABASE_URL from env
    api_key: str
    log_level: str = "INFO"                     # optional with default
    batch_size: int = 100                       # auto-cast from the env string + validated (7.1)
settings = Settings()                           # raises clearly if a required var is missing

# --- the cardinal rules -------------------------------------------------
# 1. NO secrets in source code or git history (scanners find them in minutes).
# 2. Add .env (and any secret files) to .gitignore.
# 3. If a secret IS committed, rotate it immediately — git history keeps it forever.
# 4. Same code, different env values per environment — never branch on hard-coded config.
```

### Impact

- **No leaked secrets:** credentials live in the environment/secrets manager, never in
  source or git history — closing the most common and damaging leak vector.
- **One artifact, every environment:** the same build runs in dev/staging/prod by
  reading different env values — enabling reproducible promotion and removing
  "edit-code-to-switch-env" accidents.
- **Loud, early failure:** a missing required var crashes at startup with a clear message
  (7.2), instead of a confusing failure mid-run.

### Pros & cons / when NOT to

**Externalise config/secrets when:** the code runs in more than one environment or
handles any credential — i.e. essentially all real applications.

**Watch out / when NOT to:**
- **Never commit secrets** — and if one is committed, *rotate it*, don't just delete the
  line (git history retains it; scanners and forks keep copies). Add `.env` to
  `.gitignore` from day one.
- **Env vars are strings** — cast them (`int(...)`, explicit bool checks). Remember
  `"false"`/`"0"` are *truthy* strings (1.17), so `if os.environ.get("DEBUG")` is wrong;
  compare explicitly.
- **Fail loud on missing *required* config** — use `os.environ[key]` (or
  pydantic-settings) so absence crashes at startup, not `.get` with a silent default
  that hides misconfiguration.
- **For many/typed settings, use a settings model** (pydantic-settings) — it casts,
  validates (7.1), and documents config in one place, beating scattered `os.environ`
  calls.
- **`.env` is for local dev only** — in production, use the platform's secret management
  (k8s secrets, cloud secrets manager, CI variables), not a file on disk.

### Where this shows up

- **Real work — every deployed service/job:** DB URLs, API keys, endpoints, log levels
  all come from env/secrets so the same image runs across environments (12-factor).
- **Real work — ML pipelines:** model registry URLs, cloud credentials, experiment-
  tracking keys, and data paths supplied per environment rather than hard-coded.
- **Real work — preventing the classic leak:** the #1 cause of credential leaks is a key
  committed to a repo; env-based config is the standard prevention (pairs with not
  logging secrets, 7.13/5.20).
- **Pattern mapping (secondary):** no DSA analogue; it's the configuration/secret-
  management discipline central to deployable, reproducible software (and connects to
  reproducible environments, 7.15).
[↑ Back to top](#contents)

---

<a id="7.15"></a>
## 7.15 — "It works on my machine but crashes in production" → reproducible environments & lockfiles

### The situation

Your code runs perfectly locally. You deploy it, and it crashes — or worse, behaves
*differently*:

```
# locally: works
# in prod: ImportError / AttributeError / subtly different model output
```

You investigate: your laptop has `pandas 2.1.4` and `numpy 1.26`, but the prod server
installed `pandas 2.3.0` and `numpy 2.0` — because your dependency list said only
`pandas` and `numpy` with **no versions**, so each environment grabbed whatever was
latest at install time. A function you rely on changed, or a default flipped, and your
code breaks where it "worked on my machine."

### What's really going on

"Works on my machine" almost always means **the environments differ** — different package
versions, transitive dependencies, or Python version. If you don't **pin** exact versions,
`pip install pandas` resolves to *whatever is newest today*, so two installs days apart
(your laptop vs the prod build) get different code. The fix is **reproducible
environments**: capture the *exact* versions of every package (direct **and**
transitive) so any machine installs an identical set.

> A **lockfile** records the exact, fully-resolved versions of every dependency
> (including dependencies-of-dependencies) so `install` produces a byte-for-byte
> identical environment everywhere. **Pinning** = specifying exact versions
> (`pandas==2.1.4`) rather than ranges (`pandas` / `pandas>=2`). A loose
> `requirements.txt` is a *wish*; a lockfile is a *guarantee*.

Two layers matter: a human-edited list of *direct* dependencies (what you want), and a
generated *lockfile* of everything resolved (what actually gets installed). Tools like
`pip-tools`, `poetry`, `uv`, or `pipenv` manage both; for full isolation,
**virtual environments** (and, in production, **containers/Docker**) ensure the
interpreter and OS libraries match too.

### The move

Pin exact versions in a lockfile, commit it, and install from it everywhere — inside an
isolated virtual environment:

```bash
python -m venv .venv && source .venv/bin/activate   # isolated env, not system Python
pip install pandas numpy                              # install what you need
pip freeze > requirements.txt                         # capture EXACT versions (a lockfile)
# everywhere else (CI, prod):
pip install -r requirements.txt                       # installs the identical set
```

### Why it works

`pip freeze` records the exact resolved version of *every* installed package — direct and
transitive — so `pip install -r requirements.txt` reproduces the same environment on any
machine, regardless of what's "latest" that day. Pinning removes the variable that caused
the drift: there's no resolution ambiguity, so prod gets the same `pandas 2.1.4` your
laptop tested with. The **virtual environment** isolates this project's packages from the
system Python and other projects, so installs don't collide. Committing the lockfile puts
the exact dependency set under version control, so a teammate (or a rollback) gets
precisely the environment that was tested.

### The code, every line explained

```bash
# --- virtual environment: isolate THIS project's packages ---------------
python -m venv .venv            # create an isolated environment in .venv/
source .venv/bin/activate       # use it (Windows: .venv\Scripts\activate)
# now `pip install` affects ONLY this project, not system Python or other projects.

# --- capture exact versions (a basic lockfile) --------------------------
pip install pandas numpy
pip freeze > requirements.txt   # writes pandas==2.1.4, numpy==1.26.4, + ALL transitive deps
# commit requirements.txt -> the exact set is in version control.

# --- reproduce anywhere -------------------------------------------------
pip install -r requirements.txt # CI, prod, teammate's laptop -> IDENTICAL packages
```

```text
# --- the two-layer approach (cleaner): direct list vs locked list -------
# requirements.in  (what YOU want — human-edited, loose is OK here):
#     pandas
#     numpy
# requirements.txt (GENERATED lockfile — exact, with hashes):
#     pip-compile requirements.in   # (pip-tools) resolves + pins everything
# Modern tools (poetry/uv) do both with one file + a lockfile:
#     pyproject.toml + poetry.lock / uv.lock  -> commit the lock.
```

```dockerfile
# --- containers: pin the interpreter + OS too (full reproducibility) ----
FROM python:3.11-slim            # pin the PYTHON VERSION (not just packages)
COPY requirements.txt .
RUN pip install -r requirements.txt   # same packages baked into the image
COPY . .
# The image is the ultimate lockfile: interpreter + libs + OS, identical everywhere.
```

```python
# --- the symptom this prevents ------------------------------------------
# Unpinned `pandas` -> laptop installs 2.1.4, prod installs 2.3.0 months later.
# A renamed kwarg / changed default in 2.3.0 -> "works on my machine", breaks in prod.
# Pinned `pandas==2.1.4` everywhere -> no version drift, no surprise.
```

### Impact

- **Eliminates version-drift bugs:** every environment runs identical package versions,
  so "works on my machine" stops being a category of production failure.
- **Reproducible builds & rollbacks:** a committed lockfile lets anyone recreate the
  exact tested environment, and lets you roll back dependencies as precisely as code.
- **Reliable ML results:** pinning numpy/pandas/framework versions keeps numeric behaviour
  and model outputs consistent across machines (ties to reproducibility/seeds, Area 8).

### Pros & cons / when NOT to

**Pin and lock dependencies when:** code runs anywhere other than the machine it was
written on — CI, production, a teammate's laptop. I.e. essentially every real project.

**Watch out / when NOT to:**
- **A loose `requirements.txt` (no `==`) is not reproducible** — it's a wish list. Pin
  exact versions or use a real lockfile (poetry/uv/pip-tools); commit it.
- **Pin the Python version too**, not just packages — a 3.10 vs 3.12 difference breaks
  code as readily as a package bump. Containers or version managers (pyenv) handle this.
- **Keep direct vs transitive separate.** Hand-pinning everything in one file makes
  upgrades painful; the `.in` + lockfile (or poetry/uv) split lets you state *intent*
  loosely and *lock* exactly.
- **Pinned deps still need maintenance** — frozen forever means missing security
  patches. Update deliberately and re-lock, don't drift accidentally.
- **Lockfiles don't capture system/OS libraries** (e.g. CUDA, libpng) — for those, you
  need a container image to be fully reproducible.

### Where this shows up

- **Real work — every deployment:** CI installs from the lockfile to build the same
  artifact that runs in prod — the baseline of reliable releases (pairs with config/env,
  7.14).
- **Real work — ML reproducibility:** pinning numpy/pandas/torch/sklearn versions so a
  model trained today reproduces tomorrow and on another machine (Area 8, seeds &
  determinism).
- **Real work — onboarding & collaboration:** a teammate clones the repo, installs from
  the lockfile, and gets exactly your environment — no "works for me" friction.
- **Pattern mapping (secondary):** no DSA analogue; it's the reproducibility/
  determinism discipline for environments — the dependency-level sibling of seeds (Area 8)
  and the foundation deploys and rollbacks rely on.

[↑ Back to top](#contents)

