# Area 10 — Design & Shipping

The previous areas were about making code *work*, *fast*, and *robust*. This area is about
keeping it **buildable and shippable** as it grows: structuring code so it's easy to change,
testing it so changes are safe, and rolling it out so a mistake doesn't take down
production. The recurring theme: the code runs today, but the way it's *organised* decides
whether you can still change it safely in six months — and whether shipping a change is calm
or terrifying.

---

<a id="contents"></a>
## Contents

- [10.1 — "I keep passing the same five values into every function" → group into a dataclass](#10.1)
- [10.2 — "This one function is 200 lines and does six different things" → split by responsibility](#10.2)
- [10.3 — "Should this be a class or just a dict?" → when a class earns its keep](#10.3)
- [10.4 — "What does 0.8 mean here, and why is 'active' spelled three different ways?" → constants & enums](#10.4)
- [10.5 — "I can't test this function without hitting the real database/API" → dependency injection](#10.5)
- [10.6 — "Switching from local files to S3 means rewriting twenty call sites" → depend on interfaces](#10.6)
- [10.7 — "Changing one module mysteriously breaks three others" → coupling & dependency direction](#10.7)
- [10.8 — "I'm scared to change this code in case I break something" → tests as a safety net](#10.8)
- [10.9 — "My tests cost money, are slow, and fail when the API is down" → mock/fake external dependencies](#10.9)
- [10.10 — "I fixed the bug, but how do I know it's fixed and stays fixed?" → reproduce with a failing test first](#10.10)
- [10.11 — "A refactor silently changed the output and nobody noticed for a month" → regression & golden tests](#10.11)
- [10.12 — "We deployed the new feature to everyone at once and it took down production" → feature flags & staged rollout](#10.12)

---


<a id="10.1"></a>
## 10.1 — "I keep passing the same five values into every function" → group into a dataclass

### The situation

A set of related values travels together through your whole codebase, passed individually
into function after function:

```python
def train(lr, batch_size, epochs, optimizer, weight_decay, model, data): ...
def evaluate(lr, batch_size, epochs, optimizer, weight_decay, model, data): ...
def log_run(lr, batch_size, epochs, optimizer, weight_decay): ...

train(0.001, 32, 100, "adam", 0.01, model, data)   # which positional arg is which?!
```

The same five hyperparameters thread through every function. Every signature is long, call
sites are a guessing game of positional arguments (is `0.01` the weight decay or something
else?), and adding a sixth hyperparameter means editing *every* function signature and
*every* call. It's noisy, error-prone, and painful to change.

### What's really going on

Several values that **always travel together** and represent **one concept** ("the training
configuration") are being passed around as loose, separate arguments. This is a design smell:
the relatedness isn't expressed in the code, so it can't be reused, named, validated, or
extended in one place. The fix is to **group them into a single object** — a type that
*names* the concept and bundles its fields.

Python's **`@dataclass`** is built for exactly this: a decorator (1.7) that turns a class of
typed fields into a clean record — auto-generating `__init__`, `__repr__`, and `__eq__`
(1.14) — so you define the fields once and pass *one* `TrainConfig` instead of five loose
arguments.

> When several values always move together and mean one thing, **bundle them into a type**
> (a `@dataclass`). It names the concept, shortens signatures (pass one object, not five
> args), makes fields accessible by name (`cfg.lr`, not positional guessing), and means
> adding a field is one edit — not a change to every signature and call site.

### The move

Define a `@dataclass` for the concept and pass that one object:

```python
from dataclasses import dataclass

@dataclass
class TrainConfig:
    lr: float = 0.001          # typed fields with defaults; __init__/__repr__/__eq__ free
    batch_size: int = 32
    epochs: int = 100
    optimizer: str = "adam"
    weight_decay: float = 0.01

def train(cfg: TrainConfig, model, data): ...     # one config object, not five loose args
```

### Why it works

`@dataclass` reads the typed field declarations and generates the boilerplate (`__init__` to
construct it, `__repr__` so it prints readably, `__eq__` so configs compare by value, 1.14),
so you write only the fields. Bundling them means every function takes one `cfg` and reads
`cfg.lr` *by name* — no positional ambiguity — and adding a field is a single line in the
dataclass, not a signature change rippling through the codebase. The config also becomes a
*thing* you can pass around, log (8.15), serialise, and validate in one place. Type hints
(1.22) on the fields give editor/checker support, and defaults make optional settings
explicit.

### The code, every line explained

```python
from dataclasses import dataclass, field, asdict

@dataclass
class TrainConfig:
    lr: float = 0.001                  # each field: name, type (1.22), optional default
    batch_size: int = 32
    epochs: int = 100
    optimizer: str = "adam"
    weight_decay: float = 0.01
    # MUTABLE defaults need default_factory (the 1.4 trap applies to dataclasses!):
    layers: list[int] = field(default_factory=lambda: [128, 64])   # NOT  = [128, 64]

# --- construct by NAME, pass ONE object ---------------------------------
cfg = TrainConfig(lr=0.0005, epochs=50)    # only override what you need; rest use defaults
def train(cfg: TrainConfig, model, data):
    for _ in range(cfg.epochs):            # access fields by name -> self-documenting
        step(model, data, lr=cfg.lr, wd=cfg.weight_decay)

train(cfg, model, data)                    # one arg, not five — and no positional guessing
print(cfg)    # TrainConfig(lr=0.0005, batch_size=32, ...)  -> readable __repr__ for free (8.15)

# --- adding a field is ONE edit -----------------------------------------
# add `dropout: float = 0.1` to the dataclass -> every function that takes cfg can use it,
# NO signature changes, NO call-site changes. Compare to threading a 6th positional arg.

# --- frozen (immutable) config: safer, hashable -------------------------
@dataclass(frozen=True)                    # fields can't be reassigned after creation
class FrozenConfig:                        # -> prevents accidental mutation; usable as a
    lr: float; batch_size: int             #    dict key / in a set (1.14 __hash__)

# --- serialise to/from dict (logging 8.15, configs 7.14) ----------------
asdict(cfg)                                # -> {"lr": 0.0005, "batch_size": 32, ...}
cfg2 = TrainConfig(**loaded_dict)          # rebuild from a JSON/YAML config file

# --- for VALIDATED config, use pydantic instead (3.6/7.1) ---------------
# @dataclass doesn't validate values; pydantic.BaseModel does (range/type checks) — use it
# when the config comes from untrusted input (a file/env/user), not just internal code.
```

### Impact

- **Readable, stable signatures:** functions take one named object instead of a long
  positional list, so call sites are self-documenting and adding a field doesn't churn every
  signature.
- **One place to manage the concept:** defaults, types, validation, serialisation, and
  logging of the config all live with the type — not scattered.
- **Fewer argument bugs:** named access (`cfg.lr`) eliminates the positional-argument
  mix-ups (passing weight_decay where lr was expected) that loose args invite.

### Pros & cons / when NOT to

**Group into a dataclass when:** several values always travel together and represent one
concept — configs, records, coordinates, parameter bundles, DTOs.

**Watch out / when NOT to:**
- **The mutable-default trap applies** (1.4) — `field(default_factory=list)`, never
  `= []`/`= {}` as a dataclass default, or all instances share one object.
- **Use pydantic, not `@dataclass`, when the data is untrusted** — `@dataclass` doesn't
  validate values; config from files/env/users needs validation (3.6/7.1). `@dataclass` is
  for *internal* records where you trust the inputs.
- **Don't over-group** — bundling *unrelated* values into one "god object" just to shorten
  signatures couples things that should be separate. Group values that genuinely belong
  together and change together.
- **A plain dict can suffice for a quick, dynamic bag of values** — but a dataclass wins
  when you want named access, type checking, defaults, and a fixed shape; reach for it once
  the dict's keys are effectively a fixed schema (the "class or dict?" call, 10.3).
- **Consider `frozen=True`** for configs that shouldn't change after creation — it prevents
  accidental mutation and makes the object hashable.

### Where this shows up

- **Real work — ML/training configs:** bundling hyperparameters into a `TrainConfig` passed
  through train/eval/log — and logged as one record for reproducibility (8.8/8.15).
- **Real work — request/response DTOs:** grouping the fields of an API payload or a domain
  record into a typed object instead of loose args or bare dicts.
- **Real work — passing context:** a `RequestContext`/`PipelineContext` object carrying the
  handful of values many functions need, instead of threading them individually.
- **Pattern mapping (secondary):** no DSA analogue; it's the "group related data into a
  type" design principle — the structural complement to choosing the right data structure
  (Area 3) and the basis for the class-vs-dict decision (10.3).
[↑ Back to top](#contents)

---

<a id="10.2"></a>
## 10.2 — "This one function is 200 lines and does six different things" → split by responsibility

### The situation

You have a function that grew over time into a monster that fetches, validates, transforms,
trains, evaluates, and saves — all in one body:

```python
def run_pipeline(path):
    raw = open(path).read(); rows = parse(raw)          # 1. load
    rows = [r for r in rows if valid(r)]                 # 2. validate
    feats = [transform(r) for r in rows]                 # 3. transform
    model = fit(feats)                                   # 4. train
    score = evaluate(model, feats)                       # 5. evaluate
    save(model); log(score); send_email(score)           # 6. persist + notify
    # ...200 lines, six concerns, impossible to test or reuse any part in isolation
```

You can't test the transform without also loading a file and sending an email; you can't
reuse the training step elsewhere; and when something breaks, you're debugging a 200-line
haystack. Changing one concern risks the others.

### What's really going on

The function violates the **single-responsibility principle**: it does many distinct jobs,
so it has many reasons to change, can't be tested or reused in parts, and is hard to reason
about. The fix is to **split it into small functions that each do one thing**, then have a
thin orchestrator call them in sequence. Each piece becomes independently testable (10.8),
reusable, and replaceable.

The signal is concrete: if you can describe a function with "and" ("it loads *and* validates
*and* trains..."), or it has comment-headed sections, those sections are usually separate
functions waiting to be extracted. A good function does one thing at one level of
abstraction and is small enough to hold in your head.

> **Single responsibility:** each function does *one* job, so it has one reason to change
> and can be tested/reused alone. Split a do-everything function into focused functions
> (load, validate, transform, train, evaluate, save) and a thin **orchestrator** that calls
> them. The smell: a function you describe with "and", or that's too long to grasp at once.

### The move

Extract each concern into its own function; keep a thin orchestrator that wires them
together:

```python
def run_pipeline(path):                 # the orchestrator: reads like a table of contents
    rows  = load(path)
    rows  = validate(rows)
    feats = transform(rows)
    model = train(feats)
    score = evaluate(model, feats)
    persist(model, score)
```

### Why it works

Each extracted function has a single, nameable job, so you can **test it in isolation** (pass
`transform` some rows, assert the features — no file, no email; 10.8), **reuse it**
elsewhere (call `train` from a different pipeline), and **change it safely** (rewrite
`transform` without touching loading or saving). The orchestrator becomes a high-level
summary you can read top-to-bottom to understand the flow, with details hidden in the
focused functions — one consistent level of abstraction. Debugging narrows to the one small
function that's wrong, instead of scanning 200 lines. The decomposition also exposes natural
seams for dependency injection (10.5) and error isolation (7.9) per step.

### The code, every line explained

```python
# --- each function: ONE responsibility, independently testable ----------
def load(path):                          # ONLY loading -> test with a temp file
    return parse(open(path).read())

def validate(rows):                      # ONLY validation (7.1) -> test with bad rows
    return [r for r in rows if is_valid(r)]

def transform(rows):                     # ONLY feature transform -> test pure input->output
    return [featurise(r) for r in rows]

def train(feats):                        # ONLY training -> reuse from other pipelines
    return fit(feats)

def evaluate(model, feats):              # ONLY evaluation (8.5) -> test with a known model
    return score(model, feats)

def persist(model, score):               # ONLY side effects: save + notify
    save(model); log.info("score=%.3f", score)

# --- the orchestrator: thin, readable, just wiring ----------------------
def run_pipeline(path):
    rows  = load(path)                   # reads like the steps of the pipeline
    rows  = validate(rows)
    feats = transform(rows)
    model = train(feats)
    score = evaluate(model, feats)
    persist(model, score)
    return score
# Want to test transform? -> transform(sample_rows). No file, no training, no email.
# Want to reuse train elsewhere? -> import and call it. Each piece stands alone.

# --- how to FIND the split points ---------------------------------------
# - comment-headed sections ("# load", "# validate") -> each is a function
# - "and" in the description ("loads AND validates AND...") -> separate jobs
# - mixed abstraction levels (byte-wrangling next to business logic) -> split by level
# - a chunk you'd want to TEST or REUSE on its own -> extract it

# --- don't over-split ---------------------------------------------------
# extracting a one-line function used once, or splitting so finely you can't follow the
# flow, harms readability too. Aim for functions that do one MEANINGFUL thing, not atoms.
```

### Impact

- **Testable in isolation:** each small function can be unit-tested directly (10.8) — you
  test `transform` without files or emails — which a 200-line monolith makes impossible.
- **Reusable & replaceable:** focused functions can be called from other pipelines and
  rewritten independently, so the code adapts to change instead of resisting it.
- **Readable & debuggable:** the orchestrator is a high-level summary; bugs localise to one
  small function instead of hiding in a long body.

### Pros & cons / when NOT to

**Split by responsibility when:** a function does multiple distinct jobs, is too long to
grasp, or you want to test/reuse part of it — i.e. whenever the "and" smell appears.

**Watch out / when NOT to:**
- **Don't over-split.** Extracting trivial one-liners used once, or fragmenting logic so
  finely that following the flow means jumping through ten functions, hurts readability as
  much as a monolith. Split into *meaningful* units, not atoms.
- **Keep one level of abstraction per function** — don't mix low-level byte-wrangling with
  high-level business logic in the same body; that mix is itself a signal to split.
- **Watch for shared mutable state across the split** — if extracted functions secretly
  depend on each other's side effects, you've split the lines but not the responsibilities;
  pass data explicitly (return values / a config object, 10.1) instead.
- **Pure functions are easiest to test** — push side effects (I/O, email, saving) to the
  edges (the `persist` step), keeping the middle (transform, train) pure where you can
  (1.x); this also enables dependency injection (10.5).
- **Premature decomposition can be wrong** — if you don't yet know the right seams, a
  cohesive function is fine; refactor when the responsibilities become clear (or when it
  starts hurting).

### Where this shows up

- **Real work — data/ML pipelines:** breaking a do-everything script into load → validate →
  transform → train → evaluate → persist, each testable and reusable (the structure behind
  reproducible pipelines, 8.8).
- **Real work — request handlers:** splitting a fat endpoint into parse/validate (7.1) →
  business logic → persist → respond, so each is testable and the handler stays thin.
- **Real work — refactoring legacy code:** the first move on an inherited 500-line function
  is to extract its sections into named functions behind a thin orchestrator.
- **Pattern mapping (secondary):** no DSA analogue; it's the decomposition principle — break
  a big problem into small, independent sub-problems with a coordinator — the same
  divide-and-conquer instinct as breaking down a hard problem (Area 11, 11.28/11.30).
[↑ Back to top](#contents)

---

<a id="10.3"></a>
## 10.3 — "Should this be a class or just a dict?" → when a class earns its keep

### The situation

You're modelling some data and reach instinctively for a class — or a dict — without a clear
reason:

```python
# as a dict:
user = {"name": "Alice", "age": 30, "email": "a@x.com"}
user["nmae"]          # silent typo -> KeyError at runtime, or worse, a missing key (3.x)

# as a class with methods you may not need:
class User:
    def __init__(self, name, age, email): ...
    def greet(self): ...; def deactivate(self): ...   # behaviour bolted on "just in case"
```

Both work, and beginners often pick by habit. But the choice has real consequences: the dict
has no fixed shape (any key, any typo, no checks), while a needlessly heavy class adds
ceremony. When does a class actually *earn its keep* over a plain dict (or dataclass)?

### What's really going on

The real question is **does this data have associated *behaviour* and *invariants*, or is it
just a bag of values?** That distinction decides the tool:

- **Plain dict** — good for *dynamic*, schema-less, short-lived data: parsed JSON you pass
  through, keyword-args you forward, a quick mapping. Downsides: no fixed shape, typos fail
  silently or late (3.x), no type checking, no methods.
- **`@dataclass`** (10.1) — good for a *fixed-shape record*: named fields, types (1.22),
  defaults, `__repr__`/`__eq__` for free, but **no meaningful behaviour** beyond holding
  data. The sweet spot for most "structured data" — more than a dict, less than a full
  class.
- **Full class** — earns its keep when the data has **behaviour that operates on its own
  state** and **invariants to enforce** (e.g. a `BankAccount` whose `withdraw` must keep the
  balance ≥ 0). Methods + encapsulation are the point; if there are none, a class is
  overkill.

> Choose by **behaviour + invariants**, not habit. *Bag of dynamic values* → **dict**.
> *Fixed-shape record, no real behaviour* → **`@dataclass`** (the common right answer).
> *Data with methods that act on its state and rules to maintain* → **full class**. A class
> with no methods is just a verbose dataclass; a dict where you always access fixed keys is
> a dataclass waiting to happen.

### The move

Match the tool to whether there's behaviour/invariants:

```python
# dynamic, pass-through data -> dict
config_overrides = {"lr": 0.01, "epochs": 50}     # forwarded as **kwargs, schema-free

# fixed-shape record, no behaviour -> dataclass (10.1)  ← the usual answer
@dataclass
class User:
    name: str; age: int; email: str

# data WITH behaviour + invariants -> full class
class BankAccount:
    def withdraw(self, amount): ...    # enforces balance >= 0 — methods are the point
```

### Why it works

Picking by behaviour+invariants gives each case the right amount of structure. A **dict**
keeps dynamic data flexible where a fixed schema would just get in the way. A **dataclass**
gives a record a *fixed, named, typed shape* — so `user.emial` is caught by your editor/
checker (1.22) instead of failing silently like `user["emial"]`, and you get `__repr__`/
`__eq__` for free (1.14) — without the ceremony of a hand-written class. A **full class**
earns its keep only when there's *behaviour that acts on the object's own state* and *rules
to keep true*: encapsulating the balance behind `deposit`/`withdraw` lets the class *enforce*
"balance ≥ 0", which a dict or dataclass can't. The anti-patterns fall out of the rule: a
class with only getters/setters is a dataclass written the long way; a dict whose keys are
always the same fixed set is a dataclass waiting to happen.

### The code, every line explained

```python
from dataclasses import dataclass

# --- DICT: dynamic / schema-free / pass-through -------------------------
resp = json.loads(api_text)            # unknown/variable keys -> a dict is honest
overrides = {"lr": 0.01}               # forwarded as **overrides (1.8); no fixed shape
# downside: resp["totl"] is a silent typo (KeyError or missing); no types, no methods.

# --- DATACLASS: fixed-shape record, no real behaviour (the common case) -
@dataclass
class User:
    name: str
    age: int
    email: str
u = User("Alice", 30, "a@x.com")
u.emial                                # AttributeError immediately + editor/checker flags it
                                       # (vs dict["emial"] failing silently/late) — typed shape
# more than a dict (names, types, __repr__, __eq__), less than a hand-written class.

# --- FULL CLASS: behaviour + invariants to enforce ----------------------
class BankAccount:
    def __init__(self, balance=0):
        self._balance = balance        # encapsulated: callers go through methods, not the field
    def withdraw(self, amount):
        if amount > self._balance:     # INVARIANT enforced here — the reason it's a class
            raise ValueError("insufficient funds")
        self._balance -= amount
    def deposit(self, amount):
        self._balance += amount
# The methods that ACT on and PROTECT the state are what justify a full class.

# --- the anti-patterns the rule rules out -------------------------------
# class Point:                         # no behaviour, just fields -> use @dataclass
#     def __init__(self, x, y): self.x, self.y = x, y
#     def get_x(self): return self.x   # getters/setters with no logic = verbose dataclass
#
# row = {"id": 1, "name": "A", "active": True}   # ALWAYS these exact keys, accessed everywhere
#                                                # -> a fixed schema in disguise -> dataclass

# --- when untrusted/validated: pydantic (3.6/7.1) -----------------------
# data from files/APIs/users needs validation -> pydantic.BaseModel, not a bare dataclass.
```

### Impact

- **Right amount of structure:** dicts stay flexible where flexibility helps; dataclasses
  give records a safe typed shape; classes encapsulate behaviour — each avoids the costs of
  the others.
- **Fewer silent bugs:** a typed record turns `user.emial` into an immediate, editor-flagged
  error instead of a dict's silent `KeyError`/missing-key (3.x).
- **Clearer intent:** the choice communicates meaning — a `BankAccount` class says "this has
  rules"; a dataclass says "this is a record"; a dict says "this is dynamic."

### Pros & cons / when NOT to

**Decide by behaviour + invariants when:** modelling any data — which is constantly.

**Watch out / when NOT to:**
- **Default to a dataclass for structured data** — it's the right answer far more often than
  either a bare dict (no shape/typo safety) or a full class (overkill without behaviour).
- **A class with no methods (just fields/getters/setters) is a dataclass written the long
  way** — don't write the ceremony; use `@dataclass`.
- **A dict with a fixed, always-the-same key set is a dataclass in disguise** — promote it
  to a typed record to catch typos and document the shape; keep dicts for *genuinely
  dynamic* keys.
- **Untrusted/validated data wants pydantic** (3.6/7.1), not a bare dataclass — dataclasses
  don't validate values.
- **Don't add behaviour "just in case"** — methods that don't enforce invariants or operate
  on state are speculative; YAGNI. Add them when a real rule/behaviour appears.
- **Avoid the god-class** — bundling unrelated state+behaviour into one big class is as bad
  as a do-everything function (10.2); keep classes cohesive.

### Where this shows up

- **Real work — modelling domain data:** users, orders, configs, predictions — usually
  dataclasses (or pydantic for validated input); full classes when there's real behaviour
  (a state machine, an account, a connection).
- **Real work — pass-through/dynamic data:** parsed JSON, kwargs, flexible mappings — dicts,
  promoted to a typed model only at the boundary where the shape matters (7.1).
- **Real work — refactoring:** turning a dict-with-fixed-keys (or a fields-only class) into a
  dataclass to gain type safety and a readable shape.
- **Pattern mapping (secondary):** no DSA analogue; it's the data-modelling judgment behind
  representation choices — the design-level cousin of choosing the right data structure for
  the job (Area 3), now also weighing *behaviour*, not just access patterns.
[↑ Back to top](#contents)

---

<a id="10.4"></a>
## 10.4 — "What does 0.8 mean here, and why is 'active' spelled three different ways?" → constants & enums

### The situation

Unexplained literal values and bare strings are scattered through the code:

```python
if score > 0.8:                       # what is 0.8? why 0.8? where else is it used?
    flag(item)
if user["status"] == "active":        # "active" typed by hand everywhere...
    ...
if u["status"] == "Active":           # ...and someone capitalised it here -> silent mismatch
if order.type == 1:                    # what does type 1 mean?? 2? 3?
```

These are **magic values**: literal numbers and strings with no name explaining what they
mean or enforcing which values are valid. The `0.8` threshold appears in five files (change
the policy → hunt them all down); `"active"` is retyped by hand (one typo or capitalisation
silently breaks a comparison); `type == 1` is meaningless without a decoder ring.

### What's really going on

A literal value buried in code carries **no meaning** (why 0.8?), **no single source of
truth** (the same threshold duplicated everywhere), and **no validation** (any string/number
is accepted, so typos like `"Active"` pass silently). Two fixes:

- **Named constants** for meaningful values: define `SCORE_THRESHOLD = 0.8` once, use the
  name everywhere. The name documents intent, and changing the value is one edit.
- **Enums** for a fixed *set* of allowed values: replace bare strings/ints
  (`"active"`, `1`) with `Status.ACTIVE`. The enum *names* each value, gives one canonical
  spelling, and makes an invalid value a clear error (and editor-autocompletable) instead of
  a silent typo.

> **Magic value** = a literal (number/string) in code with no name or validation. Replace
> meaningful literals with **named constants** (one source of truth, self-documenting) and
> fixed sets of choices with **`Enum`s** (canonical, typo-proof, autocompletable). The smell:
> the same literal in many places, or a bare string/int whose valid values live only in your
> head.

### The move

Name meaningful literals as constants; model fixed choice-sets as enums:

```python
from enum import Enum

SCORE_THRESHOLD = 0.8                  # named once; the name explains it; one place to change

class Status(str, Enum):               # the canonical set of allowed statuses
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"

if score > SCORE_THRESHOLD: flag(item)        # self-documenting
if user.status == Status.ACTIVE: ...           # typo-proof, autocompletable
```

### Why it works

A named constant gives the value **meaning** (`SCORE_THRESHOLD` says what `0.8` is) and a
**single source of truth** — change the policy in one place and every use updates, instead of
grepping five files and missing one. An `Enum` defines the **complete, canonical set** of
valid values once: you reference `Status.ACTIVE` (autocompleted by your editor, checked by a
type checker), so a misspelling like `Status.ACTIV` is an immediate error rather than a
silent string mismatch (`"Active" != "active"`). The enum also documents *all* the legal
values in one place — answering "what are the possible statuses?" that bare strings/ints
leave to tribal knowledge — and `type == 1` becomes the self-explaining `type == OrderType.
RETURN`.

### The code, every line explained

```python
from enum import Enum

# --- named constants: meaning + single source of truth ------------------
SCORE_THRESHOLD = 0.8                   # CONSTANT (UPPER_CASE convention); define ONCE
MAX_RETRIES = 3                         # (5.9) — the name explains the number
TIMEOUT_S = 10                          # (5.8) — change here -> changes everywhere it's used
if score > SCORE_THRESHOLD:             # reads as intent, not a mystery number
    flag(item)

# --- Enum: a fixed, canonical set of allowed values ---------------------
class Status(str, Enum):                # `str, Enum` -> members ARE strings (JSON-friendly)
    ACTIVE = "active"                   # name = ACTIVE, value = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"

user.status = Status.ACTIVE             # canonical; editor autocompletes; checker validates
if user.status == Status.ACTIVE: ...    # typo Status.ACTIV -> AttributeError immediately
# vs the bug it prevents:
# if user["status"] == "Active": ...    # "Active" != "active" -> silently always False

# --- enums make "what are the valid values?" answerable -----------------
list(Status)                            # [Status.ACTIVE, Status.SUSPENDED, Status.CLOSED]
Status("active")                        # parse from a stored string; raises if not a valid value
# -> the full set is documented in ONE place, not scattered as bare strings.

# --- IntEnum / auto() when the underlying value doesn't matter ----------
from enum import IntEnum, auto
class OrderType(IntEnum):               # type == 1 was meaningless; now it's named
    PURCHASE = auto()                   # auto() assigns 1, 2, 3... so you don't hand-number
    RETURN = auto()
    EXCHANGE = auto()
if order.type == OrderType.RETURN: ...  # self-documenting vs `== 2`

# --- where constants live -----------------------------------------------
# module-level constants near the top, or a constants.py / config (7.14) for shared ones.
# NOTE: values that change per ENVIRONMENT (URLs, keys) are CONFIG (7.14), not constants —
# constants are fixed facts of the code; config is environment-specific.
```

### Impact

- **Self-documenting code:** `SCORE_THRESHOLD`/`Status.ACTIVE` state intent where `0.8`/
  `"active"` left readers guessing.
- **One place to change:** a named constant means policy changes are a single edit, not a
  fragile grep-and-replace across files.
- **Typo-proof choices:** enums turn silent string/int mismatches (the `"Active"` bug) into
  immediate, editor-flagged errors, and document the full set of valid values.

### Pros & cons / when NOT to

**Use constants/enums when:** a literal has meaning or is repeated (constant), or a field has
a fixed set of valid values (enum) — statuses, types, categories, modes, thresholds.

**Watch out / when NOT to:**
- **Distinguish constants from config** (7.14) — fixed facts of the code (a mathematical
  threshold, a status set) are constants; values that vary per environment (URLs, keys,
  tunable limits) belong in config/env, not hard-coded constants.
- **Don't over-constant the obvious** — `x * 2` doesn't need `DOUBLE = 2`; naming
  self-evident literals adds noise. Name values that are *unclear*, *policy*, or *repeated*.
- **Use `str, Enum`/`IntEnum` for serialisation-friendliness** — plain `Enum` members aren't
  their values, which complicates JSON/DB storage; `(str, Enum)` members compare and
  serialise as their string value.
- **Enums integrate with validation** (3.6/9.11) — pydantic uses an enum field to reject
  out-of-set values automatically; reuse the same enum for parsing and validation.
- **A single-use, locally-obvious literal is fine inline** — the win is for *meaningful*,
  *repeated*, or *constrained-set* values, not every number.

### Where this shows up

- **Real work — status/type/category fields:** the canonical enum use — replacing bare
  strings/ints for order status, user role, event type so they're typo-proof and documented
  (pairs with categorical encoding awareness, 8.2, and validation, 9.11).
- **Real work — thresholds & limits:** named constants for score thresholds, retry counts
  (5.9), timeouts (5.8), batch sizes — one source of truth, easy to tune.
- **Real work — config vs constants split:** deciding which literals are fixed code facts
  (constants) vs environment-specific (config, 7.14).
- **Pattern mapping (secondary):** no DSA analogue; it's the naming/single-source-of-truth
  principle — give meaningful values names and constrain valid sets — improving readability
  and preventing the silent-mismatch class of bug (1.9/1.17).
[↑ Back to top](#contents)

---

<a id="10.5"></a>
## 10.5 — "I can't test this function without hitting the real database/API" → dependency injection

### The situation

A function creates its own dependencies inside its body — a database connection, an API
client — so you can't test it without those real systems:

```python
def process_order(order_id):
    db = PostgresDB(connect("prod-db.internal"))   # creates its OWN db connection, INSIDE
    client = PaymentAPI(api_key=os.environ["KEY"])  # creates its OWN payment client, INSIDE
    order = db.get_order(order_id)
    client.charge(order.amount)                      # hits the REAL payment API
    db.mark_paid(order_id)

# to TEST this you'd need a real prod DB and would CHARGE a real card. You can't unit-test it.
```

The function is **welded to its dependencies**: it hard-codes *which* database and *which*
payment client it uses and builds them itself. There's no way to substitute a fake for a
test, point it at a staging DB, or swap the payment provider — without editing the function.

### What's really going on

The function both **decides what its dependencies are** and **uses them** — two concerns
fused together. This makes it untestable (you can't substitute a fake, 10.9), inflexible
(can't swap implementations), and tightly coupled to specific external systems. The fix is
**dependency injection (DI)**: instead of the function *creating* its dependencies, it
*receives* them as parameters. The caller decides what to pass — the real DB in production,
a fake/mock in tests (10.9), a staging client in staging.

This inverts control: the dependency is provided from *outside*, so the function depends on
*what it's given*, not on a hard-coded choice. It's the structural enabler of testing (10.8/
10.9) and of swapping implementations (10.6).

> **Dependency injection** = passing a function/object its dependencies (db, client, clock)
> as arguments instead of constructing them internally. The caller chooses what to inject —
> real in production, a **fake/mock** in tests (10.9). It makes code testable in isolation
> and lets you swap implementations without editing the consumer. The smell: a function that
> `connect()`s / instantiates a client / reads a global *inside* its body.

### The move

Pass dependencies in as parameters; let the caller decide what to provide:

```python
def process_order(order_id, db, payment_client):    # dependencies INJECTED, not created
    order = db.get_order(order_id)
    payment_client.charge(order.amount)
    db.mark_paid(order_id)

# production wires the real ones:
process_order(oid, db=PostgresDB(...), payment_client=PaymentAPI(...))
# tests inject fakes — no real DB, no real charge:
process_order(oid, db=FakeDB(orders={oid: order}), payment_client=FakePayment())
```

### Why it works

Because the function *receives* `db` and `payment_client` rather than constructing them, the
caller controls what they are. In production you wire the real Postgres and payment client;
in a **test** you pass a `FakeDB` (an in-memory stand-in) and a `FakePayment` that records
calls instead of charging a card — so the function runs in complete isolation, fast and
safe, with no prod database and no real money moved (10.9). The same seam lets you swap a
staging client, a different payment provider, or a different storage backend *without
editing `process_order`* — it depends on the *interface* its arguments satisfy (10.6), not a
hard-coded class. You've separated "what to use" (caller's decision) from "how to use it"
(the function's job).

### The code, every line explained

```python
# --- BEFORE: dependencies created inside -> untestable, welded ----------
def process_order(order_id):
    db = PostgresDB(connect("prod-db"))     # hard-coded prod DB, built INSIDE
    client = PaymentAPI(os.environ["KEY"])   # hard-coded real client, built INSIDE
    ...                                       # can't test without prod + charging a card

# --- AFTER: dependencies injected as parameters -------------------------
def process_order(order_id, db, payment_client):   # receive them; don't create them
    order = db.get_order(order_id)
    payment_client.charge(order.amount)
    db.mark_paid(order_id)

# production composition root: wire real dependencies at the EDGE of the app
def main():
    db = PostgresDB(connect(os.environ["DATABASE_URL"]))   # config from env (7.14)
    pay = PaymentAPI(os.environ["PAYMENT_KEY"])
    process_order(oid, db, pay)              # inject the real ones here, once

# --- tests: inject fakes -> fast, isolated, safe (10.9) -----------------
class FakeDB:
    def __init__(self, orders): self.orders = orders; self.paid = []
    def get_order(self, i): return self.orders[i]
    def mark_paid(self, i): self.paid.append(i)
class FakePayment:
    def __init__(self): self.charges = []
    def charge(self, amt): self.charges.append(amt)   # RECORDS instead of charging

def test_process_order():
    db, pay = FakeDB({1: Order(amount=50)}), FakePayment()
    process_order(1, db, pay)
    assert pay.charges == [50]            # assert behaviour, no real API/DB, no real money
    assert db.paid == [1]

# --- defaults keep call sites tidy when you don't always inject ---------
def fetch(url, *, client=None):
    client = client or requests.Session()   # default to real; tests pass a fake (1.17/1.4)
    return client.get(url)
# inject ONLY at the boundaries you need to swap; don't over-parameterise everything.

# --- "composition root": wire dependencies ONCE, at the entry point -----
# push dependency CREATION to the edge (main()/startup); the core logic only RECEIVES
# them. This keeps the testable core free of I/O setup (pairs with split-by-resp, 10.2).
```

### Impact

- **Testable in isolation:** inject fakes to unit-test logic with no real DB/API/charges —
  fast, deterministic, safe tests (10.8/10.9), where the welded version was untestable.
- **Swappable implementations:** change DB, payment provider, or client without editing the
  consumer — the function depends on an interface, not a concrete class (10.6).
- **Clear separation:** "what to use" is decided at the app's edge (composition root);
  "how to use it" lives in focused logic — cleaner coupling (10.7).

### Pros & cons / when NOT to

**Inject dependencies when:** a unit does I/O or uses external systems you'd want to fake in
tests or swap in production — DBs, HTTP clients, queues, the clock, the filesystem, an LLM
client.

**Watch out / when NOT to:**
- **Inject at the seams that matter, don't over-parameterise** — threading every tiny helper
  through as a parameter is noise. Inject the *external/expensive/swappable* dependencies
  (I/O, clients, clock); construct trivial internal objects inline.
- **Push creation to a composition root** (main/startup, 10.2) — wire real dependencies once
  at the edge; keep the core logic receiving, not building. Scattering `connect()` calls
  through the code is the smell DI removes.
- **Defaults keep ergonomics** — `client=None` then `client or RealClient()` lets prod calls
  stay short while tests inject fakes (mind the mutable-default trap, 1.4 — default to
  `None`, build inside).
- **DI isn't a heavy framework in Python** — you usually just pass arguments; you rarely
  need a DI container. Don't over-engineer.
- **Inject the clock/randomness too** for deterministic tests — a function that calls
  `time.now()`/`random()` internally is as untestable as one that hits a DB (ties to seeds,
  8.7).

### Where this shows up

- **Real work — testable business logic:** injecting the DB/API/queue so the core logic is
  unit-tested with fakes (10.9) and only integration tests touch real systems (10.8).
- **Real work — swapping providers/backends:** changing storage, payment, or LLM provider by
  injecting a different implementation behind the same interface (10.6).
- **Real work — ML serving:** injecting the model/feature store/clients into handlers so they
  can be faked in tests and swapped between environments (7.14).
- **Pattern mapping (secondary):** no DSA analogue; it's the inversion-of-control design
  principle — depend on abstractions provided from outside — the enabler of testing (10.8/
  10.9) and interface-based design (10.6).
[↑ Back to top](#contents)

---

<a id="10.6"></a>
## 10.6 — "Switching from local files to S3 means rewriting twenty call sites" → depend on interfaces

### The situation

Your code calls a *specific* storage implementation directly, everywhere:

```python
# scattered across the codebase:
with open(f"/data/{key}.json") as f:  data = json.load(f)        # local files, here
open(f"/data/{key}.json", "w").write(json.dumps(obj))             # ...and here
# ...20 more places that all assume LOCAL FILES.

# now the requirement changes: store in S3 instead. You must find and rewrite ALL of them.
```

Every call site hard-codes *how* storage works (local files via `open`). When the
requirement changes to S3 (or a database, or a cache), there's no single place to change —
you hunt down and rewrite twenty scattered call sites, risking missing some.

### What's really going on

The code depends on a **concrete implementation** (local file I/O) instead of an
**abstraction** ("something that can store and load by key"). Because the *how* is spread
everywhere, swapping it touches everywhere. The fix is to **depend on an interface** — define
*what* operations you need (`save(key, obj)` / `load(key)`) as an abstract contract, write
the storage logic behind it, and have all the call sites use the *interface*. Then swapping
local→S3 is writing one new implementation of the interface; the call sites don't change.

This is the **dependency inversion** idea: high-level code depends on an abstraction, and
concrete implementations plug in behind it. Combined with injection (10.5), the
implementation is chosen at the edge and passed in — so the same code runs on local files in
dev and S3 in prod.

> Depend on an **interface** (an abstract contract of the operations you need), not a
> **concrete implementation**. Define `save`/`load`; write `LocalStore` and `S3Store` behind
> it; call sites use the interface. Swapping implementations becomes adding one class, not
> rewriting every caller. In Python, the interface can be an **ABC** (abstract base class) or
> just a **Protocol** (structural "duck typing", 1.10) — anything with the right methods.

### The move

Define the interface (the operations you need), implement it for each backend, and have
callers use the interface — injected (10.5):

```python
from typing import Protocol

class Store(Protocol):                 # the CONTRACT: what callers depend on
    def save(self, key: str, obj: dict) -> None: ...
    def load(self, key: str) -> dict: ...

def process(store: Store, key):        # depends on the INTERFACE, not local files
    data = store.load(key); ...; store.save(key, data)
```

### Why it works

Callers now depend only on the `Store` contract — "I can `save` and `load` by key" — not on
*how* that's done. Each backend (`LocalStore`, `S3Store`, `DBStore`) implements that contract
in its own way; because every call site uses the interface, swapping backends means writing
*one new class* and changing *one wiring line* (which implementation you inject, 10.5) — the
twenty call sites are untouched. A `Protocol` makes this duck-typed: any object with `save`/
`load` *is* a `Store`, no inheritance required (structural typing, the EAFP/duck-typing
spirit of 1.10), and a type checker (1.22) verifies implementations match. It also makes
testing trivial — a `FakeStore` is just another implementation (10.9).

### The code, every line explained

```python
from typing import Protocol

# --- the INTERFACE: the operations callers depend on --------------------
class Store(Protocol):                 # Protocol = structural interface (duck typing, 1.10)
    def save(self, key: str, obj: dict) -> None: ...   # no body — just the CONTRACT
    def load(self, key: str) -> dict: ...
# any object with matching save/load IS a Store — no `class X(Store)` inheritance needed.

# --- implementations behind the interface ------------------------------
import json, pathlib
class LocalStore:                      # one backend: local files
    def __init__(self, root): self.root = pathlib.Path(root)
    def save(self, key, obj): (self.root / f"{key}.json").write_text(json.dumps(obj))
    def load(self, key): return json.loads((self.root / f"{key}.json").read_text())

class S3Store:                         # another backend: S3 — SAME interface
    def __init__(self, bucket, client): self.bucket, self.client = bucket, client
    def save(self, key, obj): self.client.put_object(Bucket=self.bucket, Key=key, Body=json.dumps(obj))
    def load(self, key): return json.loads(self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read())

# --- callers depend on the INTERFACE; injected (10.5) -------------------
def process(store: Store, key):        # works with ANY Store implementation
    data = store.load(key)
    data["processed"] = True
    store.save(key, data)
# swap backends by changing ONE wiring line, not the 20 call sites:
process(LocalStore("/data"), key)      # dev
process(S3Store("my-bucket", boto3.client("s3")), key)   # prod — same process() code

# --- ABC alternative: enforce the contract via inheritance --------------
from abc import ABC, abstractmethod
class Store(ABC):
    @abstractmethod
    def save(self, key, obj): ...      # subclasses MUST implement, or instantiation errors
    @abstractmethod
    def load(self, key): ...
# Protocol = looser/duck-typed (no inheritance); ABC = explicit, enforced at instantiation.
# Prefer Protocol for "any object that quacks like a Store"; ABC when you want a base class.

# --- the smell this fixes -----------------------------------------------
# open(f"/data/{key}.json") scattered everywhere -> the IMPLEMENTATION leaked into every
# caller. Behind a Store interface, the implementation lives in ONE class.
```

### Impact

- **Swap implementations cheaply:** local→S3→DB becomes one new class + one wiring change,
  not a hunt-and-rewrite across every call site — the code adapts to changing requirements.
- **Decoupled, focused callers:** business logic depends on *what* it needs (save/load), not
  *how* storage works, so storage changes don't ripple into logic (cleaner coupling, 10.7).
- **Trivially testable:** a fake implementation of the interface (10.9) lets you test callers
  without the real backend — the interface is the test seam.

### Pros & cons / when NOT to

**Depend on an interface when:** a dependency has (or may have) **multiple implementations**
— storage backends, notification channels, payment providers, model/LLM providers, caches —
or you need to fake it in tests (10.9).

**Watch out / when NOT to:**
- **Don't abstract prematurely (YAGNI).** An interface with exactly one implementation that
  will never change is speculative complexity. Introduce the interface when a *second*
  implementation appears (or is clearly imminent), or when you need a test fake — not
  by default.
- **Keep the interface minimal and focused** — define only the operations callers actually
  need (save/load), not a kitchen-sink contract. A bloated interface is as coupling as none.
- **Prefer `Protocol` for duck-typed flexibility** (any matching object qualifies, 1.10);
  use an **ABC** when you want an enforced base class or shared default methods.
- **Leaky abstractions bite** — if an interface exposes backend-specific quirks (S3 keys vs
  file paths), callers end up coupled anyway. Design the contract around the *concept*, not
  one backend's API.
- **This composes with DI (10.5)** — the interface defines *what*, injection supplies
  *which*; together they decouple and make testable. One without the other is half the
  benefit.

### Where this shows up

- **Real work — pluggable backends:** storage (local/S3/GCS), caches (memory/Redis),
  notifications (email/Slack), payment/LLM providers — all behind an interface so the choice
  is a config/wiring decision (7.14/10.5).
- **Real work — testing:** the interface is the seam where a `FakeStore`/`FakeClient` plugs
  in for fast, isolated tests (10.9).
- **Real work — ML provider abstraction:** wrapping different embedding/LLM providers behind
  one interface so you can switch vendors or A/B them without rewriting callers (9.x).
- **Pattern mapping (secondary):** no DSA analogue; it's the dependency-inversion /
  program-to-an-interface principle — depend on abstractions, plug in concretes — the
  structural partner of dependency injection (10.5).
[↑ Back to top](#contents)

---

<a id="10.7"></a>
## 10.7 — "Changing one module mysteriously breaks three others" → coupling & dependency direction

### The situation

Your modules import each other freely, and a small change cascades:

```python
# models.py
from email_service import send_email     # a data model imports... an email service?!
class User:
    def save(self):
        db.save(self)
        send_email(self.email, "saved")   # the model now depends on email, db, and more

# email_service.py
from models import User                   # ...and email imports models -> CIRCULAR import
```

Edit `email_service` and `models` breaks; edit `models` and `email_service` breaks; and the
circular import (`models` ↔ `email_service`) causes `ImportError`s. Everything is wired to
everything, so no module can change — or be tested — alone.

### What's really going on

The modules are **tightly coupled** and their **dependencies point in tangled directions**.
Two distinct problems:

- **Too much coupling:** a change in one module forces changes in others because they know
  too much about each other's internals. Low coupling means modules interact through small,
  stable interfaces (10.6), so internal changes stay contained.
- **Wrong dependency direction:** dependencies should flow **one way**, from high-level
  policy toward low-level details — and never form **cycles**. A `User` data model importing
  an email service is backwards (a core entity depending on a peripheral service) and creates
  a circular import.

The guiding rule: **dependencies should point inward/downward and never cycle.** Stable,
high-level core logic shouldn't depend on volatile, low-level details; details depend on the
core (via interfaces, 10.6/10.5). Break cycles by extracting the shared abstraction or moving
the dependency to the orchestration layer (10.2).

> **Coupling** = how much modules depend on each other's internals; aim for **low** coupling
> via small interfaces (10.6). **Dependency direction** should be one-way (high-level core ←
> low-level details) and **acyclic** — no A→B→A cycles (which also cause circular imports).
> The smell: a change rippling across modules, or two modules importing each other.

### The move

Make data models depend on nothing peripheral; move orchestration (save + email) up to a
service/coordinator layer so dependencies flow one way:

```python
# models.py — a pure data model, depends on NOTHING peripheral
@dataclass
class User:
    name: str; email: str

# user_service.py — the ORCHESTRATOR depends on models + email (one direction, no cycle)
def register(user: User, db, mailer):       # injected deps (10.5)
    db.save(user)
    mailer.send(user.email, "welcome")
```

### Why it works

Moving the "save then email" orchestration **out** of `User` and **up** into a service layer
removes the model's dependency on email/db entirely — `models.py` now imports nothing
peripheral, so it can't participate in a cycle and changes to email/db can't break it. The
dependency now flows **one way**: the service depends on the model and on injected
interfaces (`db`, `mailer`, 10.5/10.6), never the reverse. The circular import disappears
because `email_service` no longer needs `models`. Each layer can change behind its interface
without rippling: swap the mailer (10.6), and only the wiring changes; edit the model's
fields, and only direct users care. Low coupling + acyclic, inward-pointing dependencies =
modules you can change and test in isolation.

### The code, every line explained

```python
# --- BEFORE: tangled, circular, high coupling ---------------------------
# models.py:        from email_service import send_email   # model -> email (wrong way)
# email_service.py: from models import User                # email -> model -> CYCLE
# editing either breaks the other; ImportError from the circular import.

# --- AFTER: layered, one-way dependencies -------------------------------
# layer 1 (core/innermost): pure data, NO peripheral deps
from dataclasses import dataclass
@dataclass
class User:                            # knows nothing about db/email/http
    name: str
    email: str

# layer 2 (services): orchestrates, depends on core + injected interfaces (10.5/10.6)
def register(user: User, db, mailer):  # db/mailer are INTERFACES, passed in
    db.save(user)                      # depends DOWNWARD on abstractions
    mailer.send(user.email, "welcome") # no import of email_service into models

# layer 3 (edge/main): wires concrete implementations (composition root, 10.5)
def main():
    register(User("A", "a@x.com"), db=PostgresDB(...), mailer=SmtpMailer(...))

# --- dependency rule, stated --------------------------------------------
# core (entities)  <-  services (use cases)  <-  edge (db, http, email, main)
# arrows point INWARD: outer layers depend on inner; inner NEVER imports outer.
# stable core (rarely changes) doesn't depend on volatile details (often change).

# --- breaking a cycle when you're stuck in one --------------------------
# if A needs B and B needs A, usually ONE of them is doing too much:
#   1. extract the shared piece into a 3rd module both depend on (one direction), OR
#   2. move the cross-dependency UP to an orchestrator that imports both (10.2), OR
#   3. depend on an INTERFACE (10.6) so the direction inverts (B depends on an abstraction
#      that A implements, not on A directly).
# (last resort: a local/deferred import inside a function — a smell, not a fix.)

# --- spotting coupling problems -----------------------------------------
# - circular imports (ImportError) -> a dependency cycle to break
# - "change X, must also change Y, Z" -> too much coupling; hide internals behind interfaces
# - a low-level/core module importing a high-level/peripheral one -> wrong direction
```

### Impact

- **Contained changes:** low coupling + one-way dependencies mean editing one module doesn't
  ripple into others — the difference between a codebase you can evolve and one you're afraid
  to touch.
- **No circular imports:** acyclic dependencies eliminate the `ImportError` tangles and the
  "A needs B needs A" deadlocks.
- **Testable & swappable:** a stable core depending on injected interfaces (10.5/10.6) can be
  tested and have its details swapped without disturbing the logic.

### Pros & cons / when NOT to

**Mind coupling & direction when:** structuring modules/packages, especially as a codebase
grows past a few files — and immediately whenever a circular import appears.

**Watch out / when NOT to:**
- **Core/entities must not depend on peripheral details** — a data model importing email/db/
  http is the classic wrong-direction smell and a cycle waiting to happen. Push orchestration
  up to a service layer (10.2).
- **Break cycles structurally, not with hacks** — extract a shared module, move the
  dependency to an orchestrator, or invert via an interface (10.6). A deferred import inside
  a function silences the error but leaves the bad design.
- **Don't over-layer a tiny project** — strict hexagonal/clean-architecture layering is
  overkill for a 200-line script; apply it proportionally as the code grows. The *principle*
  (one-way, acyclic, low coupling) scales down; the *ceremony* shouldn't.
- **Watch for the change-ripple signal** — "I touched X and Y/Z broke" means they're too
  coupled; hide internals behind a smaller interface (10.6) so changes stay local.
- **Some coupling is fine** — modules *must* interact; the goal is *low* and *directed*
  coupling through stable interfaces, not zero coupling.

### Where this shows up

- **Real work — package/module structure:** organising a codebase so domain logic doesn't
  depend on frameworks/DB/HTTP — those depend inward via interfaces (10.5/10.6); the basis of
  layered/clean architecture.
- **Real work — fixing circular imports:** the immediate, concrete trigger — a cycle forces
  you to rethink which module should depend on which.
- **Real work — large refactors:** reducing coupling so teams can change their module without
  breaking others, and so changes stay reviewable (10.2).
- **Pattern mapping (secondary):** the "dependencies must be acyclic and directed" rule is
  literally a **DAG / topological-ordering** problem (Area 11, 11.17) — modules form a
  dependency graph that must have no cycles and a valid layering order.
[↑ Back to top](#contents)

---

<a id="10.8"></a>
## 10.8 — "I'm scared to change this code in case I break something" → tests as a safety net

### The situation

You need to refactor or extend a piece of code, but you have no way to know if your change
broke existing behaviour — so you change it nervously, click around manually, and hope:

```python
def calculate_discount(price, customer_tier, quantity):
    # 40 lines of branching logic for tiers, bulk discounts, promotions...
    return final_price

# you need to add a new tier. Did your change break the existing tiers? bulk discounts?
# the only way you "know" is manual testing -> slow, incomplete, and you WILL miss a case.
```

Every change is a gamble. Manual checking is slow and never covers all the branches, so
regressions slip through to production, and fear of breaking things makes the code
*ossify* — nobody wants to touch it.

### What's really going on

Without **automated tests**, you have no fast, repeatable way to verify that code does what
it should and *keeps* doing it after changes. The fix is a **test suite**: code that calls
your code with known inputs and **asserts** the expected outputs, runnable in seconds. Tests
turn "I hope this still works" into "the suite is green, so the behaviours I captured still
hold" — a **safety net** that catches regressions the moment you introduce them, freeing you
to change code with confidence.

The bedrock are **unit tests**: fast, isolated tests of one function/unit (enabled by
single-responsibility, 10.2, and dependency injection, 10.5). `pytest` is the standard tool —
write functions named `test_*` that call your code and `assert` results.

> A **test** runs your code on known inputs and **asserts** the expected output;
> a **test suite** is many tests run together in seconds. **Unit tests** check one unit in
> isolation (fast, no real DB/API — inject fakes, 10.5/10.9). The payoff is a **safety net**:
> a change that breaks captured behaviour turns a test red *immediately*, so you refactor and
> extend without fear of silent regressions.

### The move

Write `pytest` tests that assert behaviour for normal cases and edge cases; run them on every
change:

```python
# test_discount.py — run with: pytest
def test_bronze_no_discount():
    assert calculate_discount(100, "bronze", 1) == 100

def test_gold_gets_10_percent():
    assert calculate_discount(100, "gold", 1) == 90

def test_bulk_discount_applies():
    assert calculate_discount(100, "bronze", 100) == 80   # bulk kicks in at qty 100
```

### Why it works

Each test pins one expected behaviour as an executable `assert`. Run `pytest` and it executes
them all in seconds, reporting exactly which (if any) fail. Now when you add a new tier, you
rerun the suite: if your change broke gold's 10% or the bulk discount, the relevant test goes
**red immediately** with the failing values — you catch the regression *as you make it*,
before it ships, instead of discovering it in production weeks later. Because unit tests are
fast and isolated (no real DB/API — you inject fakes, 10.5/10.9), you can run them constantly,
which is what makes them a *net* rather than a chore. The tests also document intended
behaviour and let you refactor freely: green suite = behaviours preserved.

### The code, every line explained

```python
# test_discount.py  (pytest auto-discovers files/functions named test_*)
import pytest
from discount import calculate_discount

# --- one behaviour per test, descriptive names --------------------------
def test_bronze_no_discount():
    assert calculate_discount(100, "bronze", 1) == 100     # given inputs -> expected output

def test_gold_gets_10_percent():
    assert calculate_discount(100, "gold", 1) == 90

# --- EDGE CASES are where bugs hide (Area 11 / 11.x mindset) ------------
def test_zero_quantity():
    assert calculate_discount(100, "gold", 0) == 0          # boundary: qty 0
def test_invalid_tier_raises():
    with pytest.raises(ValueError):                          # assert it FAILS correctly (7.2)
        calculate_discount(100, "platinum", 1)               # unknown tier -> error

# --- parametrize: many cases, one test (DRY) ----------------------------
@pytest.mark.parametrize("price,tier,qty,expected", [
    (100, "bronze", 1, 100),
    (100, "gold", 1, 90),
    (100, "gold", 100, 72),     # gold + bulk stack
])
def test_discount_cases(price, tier, qty, expected):
    assert calculate_discount(price, tier, qty) == expected  # runs once per row

# --- fixtures: shared setup (and inject fakes, 10.5/10.9) ---------------
@pytest.fixture
def fake_db():
    return FakeDB(orders={1: Order(amount=50)})              # reusable test dependency
def test_process_uses_db(fake_db):
    process_order(1, db=fake_db, payment_client=FakePayment())   # unit test, no real systems
    assert fake_db.paid == [1]

# --- run them -----------------------------------------------------------
# $ pytest                 # run all, in seconds
# $ pytest -k discount     # run matching tests
# $ pytest -x              # stop at first failure
# green = captured behaviours still hold; red = you just broke one (with the exact values).

# --- what to test (prioritise) ------------------------------------------
# - the HAPPY path (normal inputs)            - core business logic / tricky branches
# - EDGE cases (0, empty, None, boundaries — 1.17)   - error cases (does it fail right? 7.2)
# - REGRESSIONS: when you fix a bug, add a test that would have caught it (10.10)
```

### Impact

- **Change without fear:** a green suite means refactors and new features don't silently
  break existing behaviour — the safety net that keeps code malleable instead of ossified.
- **Fast, complete feedback:** seconds to verify dozens of branches that manual testing would
  cover slowly and incompletely — regressions caught at authoring time, not in production.
- **Living documentation:** tests state intended behaviour precisely (and stay true, unlike
  comments), so they explain the code and its edge cases to the next reader.

### Pros & cons / when NOT to

**Write tests when:** code has non-trivial logic, will be changed/extended, or matters in
production — i.e. essentially all real code. Prioritise the tricky/critical parts.

**Watch out / when NOT to:**
- **Test behaviour, not implementation** — assert *what* the function returns/does, not its
  internal steps; tests coupled to implementation break on every refactor and become a
  burden instead of a net.
- **Cover edge cases, not just the happy path** — 0/empty/None/boundaries (1.17) and error
  cases (7.2) are where bugs live; a test suite that only checks the obvious case gives false
  confidence.
- **Keep unit tests fast and isolated** — inject fakes (10.5/10.9) so they don't hit real
  DBs/APIs; slow tests get skipped, and a net you don't run isn't a net.
- **Don't chase 100% coverage as a goal** — coverage is a hint, not the point; a covered line
  with a weak assertion tests nothing. Aim to capture *meaningful behaviours*, especially
  risky ones.
- **Tests need maintenance** — they're code too; brittle, over-specified, or flaky tests
  (10.x) erode trust. A flaky test that "sometimes fails" is worse than none — fix or delete
  it.

### Where this shows up

- **Real work — every maintained codebase:** a test suite run in CI is the baseline that lets
  a team change code safely; it gates merges and deploys (10.12).
- **Real work — refactoring safely:** writing/running tests before a refactor so "still
  green" proves behaviour is preserved (the enabler of 10.2/10.6 changes).
- **Real work — testable design:** single-responsibility (10.2) + dependency injection (10.5)
  exist largely to make code unit-testable with fakes (10.9).
- **Pattern mapping (secondary):** no DSA analogue directly, but the discipline of enumerating
  edge cases (empty, boundary, error) is exactly the case-analysis mindset that solves and
  verifies algorithm problems (Area 11, 11.30 / verifying correctness).
[↑ Back to top](#contents)

---

<a id="10.9"></a>
## 10.9 — "My tests cost money, are slow, and fail when the API is down" → mock/fake external dependencies

### The situation

Your code calls an LLM/payment/API, and your tests call the *real* thing:

```python
def test_summarise():
    result = summarise(article)        # calls the REAL LLM API
    assert "summary" in result
# this test: costs money every run (5.20), takes seconds, is non-deterministic (the LLM's
# output varies), and FAILS when the API is down or rate-limits (5.11) — for reasons that
# have NOTHING to do with your code being correct.
```

Tests that hit real external systems are slow, flaky, expensive, and non-deterministic — so
they break for reasons unrelated to your logic, and a test suite you can't trust (or afford
to run constantly) isn't the safety net it should be (10.8).

### What's really going on

A unit test should verify **your code**, not a third party. When your code depends on an
external system (LLM, API, DB, clock, queue), you replace that dependency in the test with a
**test double** — a stand-in that behaves predictably — so the test is fast, deterministic,
free, and offline. This is exactly what dependency injection (10.5) and interfaces (10.6)
set up: pass a double instead of the real client.

Two main kinds of double:

- **Fake** — a lightweight *working* implementation (an in-memory store, a canned-response
  client). You control its behaviour; tests assert against it.
- **Mock** — an object that *records* how it was called so you can assert the interaction
  ("was `charge(50)` called once?"), and can be programmed to return canned values. Python's
  `unittest.mock` provides these.

> A **test double** replaces a real dependency in a test with a controllable stand-in.
> A **fake** is a simple working implementation (in-memory DB, canned client); a **mock**
> records/asserts calls and returns programmed values. Use them (via DI, 10.5) so unit tests
> are fast, free, deterministic, and offline — testing *your* logic, not the third party's
> uptime.

### The move

Inject a fake/mock in the test instead of the real client (DI, 10.5); assert your code's
behaviour against it:

```python
def test_summarise():
    fake_llm = lambda prompt: "a canned summary"     # a fake: predictable, free, instant
    result = summarise(article, llm=fake_llm)        # inject it (10.5) instead of the real LLM
    assert result == "a canned summary"               # deterministic -> a real assertion
```

### Why it works

Because `summarise` *receives* its `llm` (DI, 10.5) rather than calling a hard-coded client,
the test passes a `fake_llm` that returns a fixed string instantly and for free. Now the test
exercises *your* code — does `summarise` build the prompt right, handle the response, parse it
(9.10)? — without any network, cost, or randomness, so it's fast, deterministic, and runnable
offline thousands of times (10.8). A **mock** goes further when you care about the
*interaction*: it records that `charge(50)` was called exactly once, letting you assert side
effects without performing them. The double stands in precisely because your code depends on
an *interface* (10.6), not a concrete client — so any object with the right shape works.

### The code, every line explained

```python
# --- FAKE: a simple working stand-in you control ------------------------
def test_summarise_builds_and_returns():
    fake_llm = lambda prompt: "canned summary"        # returns a fixed value, no network
    out = summarise(article, llm=fake_llm)            # injected (10.5)
    assert out == "canned summary"                     # deterministic assertion

class FakePayment:                                     # records calls instead of charging
    def __init__(self): self.charges = []
    def charge(self, amt): self.charges.append(amt)
def test_checkout_charges_total():
    pay = FakePayment()
    checkout(cart, payment=pay)
    assert pay.charges == [150]                        # assert the side effect, no real money

# --- MOCK: record/assert interactions (unittest.mock) -------------------
from unittest.mock import Mock
def test_notify_called_once():
    mailer = Mock()                                    # auto-records all calls
    register(User("A", "a@x.com"), db=FakeDB(), mailer=mailer)
    mailer.send.assert_called_once_with("a@x.com", "welcome")  # assert HOW it was called
    mock_resp = Mock(); mock_resp.json.return_value = {"ok": True}   # program return values
    client = Mock(); client.get.return_value = mock_resp

# --- patch: replace a dependency you CAN'T inject (last resort) ---------
from unittest.mock import patch
@patch("mymodule.requests.get")                        # swap the real call inside the module
def test_fetch(mock_get):
    mock_get.return_value.json.return_value = {"data": 1}
    assert fetch("http://x") == {"data": 1}
# PREFER injection (10.5) over patch — patch is brittle (couples the test to import paths)
# and is the fallback for code you can't easily refactor to accept the dependency.

# --- the trade-off: doubles can drift from reality ----------------------
# A fake that returns "canned summary" tests YOUR logic, NOT that the real API still works
# or still returns that shape. So ALSO keep a few INTEGRATION tests (10.x) that hit the real
# (or a sandbox) system, run less often, to catch contract drift the fakes can't.

# --- record/replay (VCR-style) for HTTP ---------------------------------
# tools like vcrpy record real HTTP responses ONCE, then replay them in tests -> realistic
# fixtures without live calls. A middle ground between hand-fakes and live integration.
```

### Impact

- **Fast, free, deterministic unit tests:** no network, no cost (5.20), no flakiness — so the
  suite (10.8) runs in seconds on every change and you actually trust/run it.
- **Tests your logic, not their uptime:** failures mean *your* code is wrong, not that the API
  was down or rate-limited (5.11) — the whole point of isolating the unit.
- **Assert interactions safely:** mocks let you verify side effects ("charged once") without
  performing them — testing payment/notification logic without real money/emails.

### Pros & cons / when NOT to

**Use test doubles when:** unit-testing code that depends on external/slow/costly/
non-deterministic systems — APIs, LLMs, DBs, the clock, queues, the filesystem.

**Watch out / when NOT to:**
- **Don't mock everything — keep some integration tests.** A double tests your logic but
  *not* that the real dependency still behaves as assumed; the fake can drift from reality.
  Pair unit tests (with doubles) with a few slower integration tests (10.x) against the real/
  sandbox system to catch contract changes.
- **Prefer injection (10.5) over `patch`** — passing a fake as an argument is clean and
  refactor-stable; `patch` couples the test to import paths and breaks when you move code. Use
  `patch` only when you can't inject.
- **Don't over-specify mocks** — asserting *every* internal call makes tests brittle (they
  break on harmless refactors, 10.8). Assert the interactions that *matter* (the charge
  happened), not every step.
- **Fakes must stay faithful** — a fake that behaves differently from the real thing (ignores
  an error the real API raises) gives false confidence. Model the behaviours your code relies
  on, including failures (test the retry/timeout paths, 5.8/5.9).
- **Mock the boundary you own, at the right level** — mock *your* client interface (10.6), not
  deep third-party internals, so the test survives library changes.

### Where this shows up

- **Real work — testing API/LLM clients:** faking the LLM/payment/HTTP client so tests of
  prompt-building, parsing (9.10/9.11), and error handling (5.8/5.9) run free and offline.
- **Real work — testing business logic:** injecting a `FakeDB`/`FakePayment` (10.5) to unit
  test order/checkout logic without real systems or money.
- **Real work — the test pyramid:** many fast unit tests with doubles at the base, fewer slow
  integration tests against real systems on top — the standard balance.
- **Pattern mapping (secondary):** no DSA analogue; it's the testing technique that makes
  dependency injection (10.5) and interfaces (10.6) pay off — substitute a controllable
  stand-in at the seam to isolate the unit under test (10.8).
[↑ Back to top](#contents)

---

<a id="10.10"></a>
## 10.10 — "I fixed the bug, but how do I know it's fixed and stays fixed?" → reproduce with a failing test first

### The situation

A bug report comes in: "discount is wrong for gold-tier bulk orders." You dive into the code,
spot something that looks off, change it, and... do you actually know you fixed *that* bug?
And what stops it silently coming back later?

```python
# you eyeball the code, tweak a line, click around manually:
calculate_discount(100, "gold", 100)   # returns 72 now... is that right? was it the bug?
# you "think" it's fixed. No proof it reproduced the report, no guard against regression.
```

Fixing by inspection-and-hope has two holes: you might fix the *wrong* thing (the symptom you
imagined, not the actual reported bug), and even if you fix it, nothing prevents a future
change from reintroducing it.

### What's really going on

The disciplined fix is **write a failing test that reproduces the bug *first*, then make it
pass.** This flips bug-fixing from guesswork into a verifiable loop:

1. **Reproduce:** write a test asserting the *correct* expected behaviour for the reported
   case. Run it — it should **fail**, proving you've actually captured the bug (not imagined
   one).
2. **Fix:** change the code until that test goes **green** — now you have proof the fix
   addresses *this specific* bug.
3. **Stays fixed:** the test stays in the suite (10.8) as a **regression test** — if anyone
   ever reintroduces the bug, it goes red immediately.

A test that fails *before* the fix and passes *after* is proof the fix works; a test that
passes before you've fixed anything wasn't reproducing the real bug. This is the
bug-fixing application of test-driven discipline.

> **Reproduce-first:** before fixing a bug, write a test that asserts the correct behaviour
> for the reported case and confirm it **fails** — that proves you've reproduced the *actual*
> bug. Then fix until it's green. The test remains as a **regression test** (10.11) so the bug
> can't silently return. Fixing without a failing test risks fixing the wrong thing and
> guarantees nothing about the future.

### The move

Write a test for the reported case asserting the *correct* result, watch it fail, then fix
until green:

```python
# 1. REPRODUCE: write the test FIRST — it should FAIL on the current buggy code
def test_gold_bulk_discount():
    # report: gold + 100 units should be 28% off -> 72; current code returns the wrong value
    assert calculate_discount(100, "gold", 100) == 72
# run pytest -> RED. Good: the bug is reproduced and pinned down.
# 2. FIX the code until this test is GREEN.  3. It STAYS as a regression test.
```

### Why it works

Running the test *before* fixing anything and seeing it **fail** proves two things: the bug is
real and you've captured *it* (not a different issue you imagined). That failing assertion also
defines "fixed" precisely — you change code until exactly this goes green, so you can't fool
yourself that an unrelated tweak solved it. Once green, the test joins the suite (10.8)
permanently: any future change that reintroduces the bug flips it red instantly, so the bug
can't quietly return (a regression test, 10.11). The whole loop turns "I think I fixed it" into
"here's executable proof it was broken and now isn't, forever."

### The code, every line explained

```python
# --- STEP 1: reproduce the bug as a FAILING test ------------------------
def test_gold_bulk_discount():
    # encode the CORRECT expected behaviour from the bug report
    assert calculate_discount(100, "gold", 100) == 72
# $ pytest -k gold_bulk
# FAILED: assert 90 == 72   <- the bug, reproduced and PROVEN (current code gives 90)
# If this PASSED here, you have NOT reproduced the real bug — investigate before "fixing".

# --- STEP 2: fix the code until the test passes -------------------------
# (edit calculate_discount so gold+bulk discounts stack correctly)
# $ pytest -k gold_bulk
# PASSED  <- proof the fix addresses THIS specific reported case

# --- STEP 3: keep it — it's now a REGRESSION test (10.11) ---------------
# the test lives in the suite forever; if someone later breaks gold+bulk again,
# it goes RED in CI immediately (10.12), before the regression ships.

# --- a good bug-fix commit bundles BOTH ---------------------------------
# the failing-then-passing test AND the fix, together -> reviewers see the bug captured
# and the fix proven (10.8). "Fixed discount bug" with no test is unverifiable.

# --- when the repro is hard: shrink it ----------------------------------
# can't reproduce from the report alone? get the exact inputs (log them, 7.13), then
# MINIMISE: strip the case down to the smallest input that still fails -> easier to fix
# and a cleaner regression test. (Same "minimal failing case" instinct as debugging, 2.1.)

# --- the anti-pattern ---------------------------------------------------
# read code -> "this looks wrong" -> change it -> click around -> "seems fine now".
# You may have fixed a DIFFERENT (or no) bug, and nothing stops it returning. No proof.
```

### Impact

- **Proof you fixed the right thing:** a test that fails before and passes after is evidence
  you reproduced and resolved the *actual* reported bug — not a guess.
- **Permanent protection:** the test becomes a regression guard (10.11) in the suite (10.8),
  so the same bug can't silently return — bugs get fixed *once*.
- **Clearer debugging:** writing the repro forces you to pin down exact inputs and expected
  output, which often reveals the cause faster than reading code.

### Pros & cons / when NOT to

**Reproduce-first when:** fixing any non-trivial bug, especially one reported from production
or one that could plausibly recur.

**Watch out / when NOT to:**
- **If your "repro" test passes before you fix anything, you haven't reproduced the bug** —
  you're about to fix the wrong thing. Get the exact failing inputs (logs, 7.13) and keep
  trying until the test is red for the *reported* reason.
- **Test the behaviour, not your guess at the cause** — assert the correct *output* for the
  case; don't bake in assumptions about *why* it's wrong, or the test passes for the wrong
  reason.
- **Minimise the repro** — shrink to the smallest input that still fails; a bloated repro test
  is a poor regression guard and harder to debug (same instinct as isolating in 2.1).
- **Bundle the test with the fix** — a bug-fix PR with no failing-then-passing test is
  unverifiable; reviewers (and future you) can't confirm it (10.8).
- **Some bugs are genuinely hard to unit-test** (timing/concurrency, 7.11; environment) — do
  your best to capture them (even an integration/flaky-prone test with a note), but don't let
  "hard to test" become "no test and no proof."

### Where this shows up

- **Real work — every bug fix:** the professional default — reproduce as a failing test, fix,
  keep the test. It's how bug-fix PRs are reviewed and how bugs stay fixed.
- **Real work — production incident follow-up:** after an incident, a regression test for the
  exact failure prevents the same outage recurring (ties to 10.11).
- **Real work — TDD in general:** the same red→green loop applied proactively to new features,
  not just bugs.
- **Pattern mapping (secondary):** it's the scientific-method/verification discipline — form a
  precise, falsifiable check, confirm it fails, then make it pass — the same rigour as
  verifying an algorithm's correctness with a failing edge case (Area 11).
[↑ Back to top](#contents)

---

<a id="10.11"></a>
## 10.11 — "A refactor silently changed the output and nobody noticed for a month" → regression & golden tests

### The situation

You refactor a complex function — a report generator, a data transform with 50 fields, a
pipeline's output — for speed or clarity. It still runs, tests pass, you ship. A month later
someone notices the output has been subtly *different* the whole time: a field is formatted
differently, a value is off, an edge case changed:

```python
# you refactored generate_report() for readability. it still returns a big dict/string.
# your unit tests check a few fields — but not the WHOLE output — so a change to field #37
# slips through unnoticed. The refactor was supposed to preserve behaviour; it didn't.
```

For complex outputs, spot-checking a few fields isn't enough — a refactor meant to *preserve*
behaviour can alter it in ways no individual assertion catches.

### What's really going on

Two related needs. A **regression test** locks in a *specific* behaviour so a future change
can't silently alter it (10.10's bug test is one example). For *large/complex* outputs,
asserting every field by hand is impractical — so you use a **golden test** (a.k.a. snapshot/
characterisation test): capture the known-good output once as a stored reference ("golden
file"), and have the test compare future output against it. Any difference — anywhere in the
output — fails the test and shows a diff.

This is the safety net for "this big output must not change unexpectedly." Before a refactor,
you snapshot the current output as the golden; after, the test proves the output is
*byte-for-byte identical* (behaviour preserved) — or shows you exactly what changed so you can
decide if it's intended.

> A **regression test** pins a specific behaviour so it can't silently change. A **golden/
> snapshot test** captures a complex output as a stored reference and diffs future runs
> against it — catching *any* unintended change without hand-asserting every field. Use it to
> verify a refactor preserved behaviour, or to guard a large output (report, transform,
> serialised result). When a change is *intended*, you re-bless (update) the golden.

### The move

Capture the known-good output as a golden file once; the test diffs future output against it:

```python
def test_report_matches_golden():
    result = generate_report(sample_input)
    golden = json.loads(open("tests/golden/report.json").read())   # the blessed reference
    assert result == golden          # ANY difference, anywhere, fails with a diff
```

### Why it works

The golden file is a *complete* snapshot of correct output, so comparing against it catches a
change to *any* field — including the field #37 a hand-written assertion never checked. Before
refactoring, you generate the golden from the current (correct) code; after refactoring, a
green test proves the output is identical, i.e. behaviour was preserved — exactly the
guarantee a "make it cleaner/faster, don't change what it does" refactor needs (10.2/2.x). If
the output *does* change, the test fails and shows precisely what differed, forcing a
deliberate decision: a bug (fix it) or an intended change (update — "re-bless" — the golden).
Either way, no silent drift. Snapshot-test libraries (e.g. `syrupy` for pytest) automate
capturing, comparing, and updating goldens.

### The code, every line explained

```python
import json

# --- a plain golden test (no library) -----------------------------------
GOLDEN = "tests/golden/report.json"
def test_report_golden():
    result = generate_report(sample_input)         # current output
    with open(GOLDEN) as f:
        golden = json.load(f)                       # the blessed, known-good reference
    assert result == golden                         # full-output comparison -> catches ANY drift

# --- creating / UPDATING the golden (re-blessing) -----------------------
# generate it the first time, or when a change is INTENTIONAL and reviewed:
#   python -c "import json; from app import generate_report, sample_input; \
#              json.dump(generate_report(sample_input), open('tests/golden/report.json','w'), indent=2)"
# COMMIT the golden file -> reviewers see the exact expected output AND any future diff to it.

# --- snapshot libraries automate the capture/diff/update loop -----------
# pytest + syrupy:
def test_report(snapshot):
    assert generate_report(sample_input) == snapshot   # first run: records; later: compares
# update intentionally with:  pytest --snapshot-update   (then REVIEW the diff before commit)

# --- the refactor workflow this enables ---------------------------------
# 1. before refactor: capture golden from the CURRENT (correct) output
# 2. refactor for clarity/speed (10.2 / Area 2)
# 3. run the golden test -> GREEN means behaviour preserved; a diff means you changed output
#    -> investigate: bug (fix) or intended (re-bless + note it in review)

# --- making goldens stable (avoid false diffs) --------------------------
# normalise NON-deterministic bits or the test flakes on every run (10.x flaky tests):
#   - timestamps/ids/random -> inject fixed values (10.5) or strip/replace before compare
#   - dict ordering / float precision -> sort keys, round floats (json.dumps(sort_keys=True))
#   - seed any randomness (8.7)
# a golden full of changing values produces diffs unrelated to real behaviour -> noise.

# --- review the diff; never blindly re-bless ----------------------------
# the DANGER: `--snapshot-update` on a red test "to make it pass" can enshrine a BUG as the
# new golden. Always READ the diff and confirm the change is intended before updating.
```

### Impact

- **Catches silent output drift:** a full-output comparison flags *any* unintended change a
  refactor introduces — including fields no hand-written assertion covers — so "preserve
  behaviour" refactors are actually verified.
- **Cheap coverage of complex outputs:** one golden test guards a 50-field report or a large
  serialised result without writing 50 assertions.
- **Deliberate change control:** an output change can't slip through unnoticed — it either
  fails as a bug or is consciously re-blessed and reviewed.

### Pros & cons / when NOT to

**Use regression/golden tests when:** guarding a large/complex output against unintended
change, or verifying a refactor preserved behaviour — reports, data transforms, serialised
results, rendered output.

**Watch out / when NOT to:**
- **Normalise non-determinism or goldens flake** — timestamps, ids, random values, dict order,
  float precision cause false diffs every run (10.x). Inject fixed values (10.5), seed (8.7),
  sort keys, round floats before comparing.
- **Never blindly `--snapshot-update` a red test** — that can enshrine a *bug* as the new
  golden. Always read the diff and confirm the change is intended; re-blessing is a reviewed
  decision, not a way to make tests pass.
- **Golden tests check "did it change", not "is it correct"** — a wrong-but-stable output
  stays green. Pair them with behaviour-asserting unit tests (10.8) that encode *correctness*,
  not just *constancy*; use goldens for drift detection, not as your only tests.
- **Over-broad goldens are brittle** — snapshotting a huge output where only part matters means
  every minor change fails the test. Snapshot the meaningful part, or assert the stable subset.
- **Commit and review goldens** — a golden nobody reads is just a rubber stamp; the diff in
  code review is where the value is.

### Where this shows up

- **Real work — refactoring complex logic:** snapshot the output, refactor (10.2/Area 2),
  confirm the golden is unchanged — proof behaviour was preserved.
- **Real work — report/serialisation/transform code:** guarding large structured outputs
  (JSON/CSV/rendered docs) against accidental format or value changes.
- **Real work — ML/LLM output drift (with care):** snapshotting deterministic pipeline outputs;
  for non-deterministic model output, normalise or assert properties instead (8.x/9.x).
- **Pattern mapping (secondary):** no DSA analogue; it's characterisation/snapshot testing —
  pin the current behaviour as a reference to detect change — complementing the
  reproduce-first regression test (10.10) and the unit-test safety net (10.8).
[↑ Back to top](#contents)

---

<a id="10.12"></a>
## 10.12 — "We deployed the new feature to everyone at once and it took down production" → feature flags & staged rollout

### The situation

You ship a new feature (or model, or risky change) by deploying it to 100% of users
instantly:

```python
def recommend(user):
    return new_recommender(user)     # replaced the old one for EVERYONE, all at once
# the new recommender has a bug that only shows under real load -> EVERY user is now
# affected, and "rolling back" means an emergency redeploy while the site is broken.
```

Big-bang releases mean a problem the tests didn't catch (load, real data, edge cases) hits
*all* users at once, and recovery requires a panicked redeploy — maximum blast radius,
slowest recovery.

### What's really going on

Shipping is risky because tests (10.8–10.11) can't catch *everything* — real traffic, scale,
and data surface issues that didn't appear offline. The mitigation is to **decouple deploy
from release** and **limit blast radius**: roll the change out *gradually* and be able to turn
it off *instantly* without a redeploy.

Two tools:

- **Feature flag** — a runtime switch that turns a feature on/off (or on for *some* users)
  without deploying new code. You deploy the code "dark" (flag off), then flip it on when
  ready, and flip it *off instantly* if something's wrong — an **instant rollback** that
  doesn't require a redeploy.
- **Staged rollout** — enable the change for a *growing fraction* (1% → 10% → 50% → 100%),
  watching metrics (7.10/9.15) at each step. A problem shows up at 1% affecting few users, not
  100% affecting everyone — and you halt/roll back before wide impact. This is also how
  **canary** releases and **A/B tests** (8.14) work.

> A **feature flag** is a runtime on/off switch for a feature (no redeploy to toggle),
> enabling **instant rollback** and **dark launches**. A **staged/canary rollout** enables a
> change for a growing fraction of users while watching metrics, so problems surface at small
> blast radius and you can halt early. Together they make releasing a *gradual, reversible*
> operation instead of an all-or-nothing gamble.

### The move

Gate the change behind a flag and roll it out to a growing fraction, watching metrics:

```python
def recommend(user):
    if flags.enabled("new_recommender", user):     # runtime switch, per-user
        return new_recommender(user)               # only the rolled-out fraction get it
    return old_recommender(user)                    # everyone else stays on the safe path
# roll out: 1% -> watch metrics (7.10/9.15) -> 10% -> 50% -> 100%; flip OFF instantly if bad.
```

### Why it works

The flag check decides *at runtime* who gets the new path, so deploying the code and releasing
the feature are separate: you ship it off ("dark"), then enable it for 1% of users. If the new
recommender misbehaves under real load, only ~1% are affected and your metrics (7.10/9.15)
show it while blast radius is tiny — you flip the flag **off instantly**, with no redeploy, and
everyone falls back to the proven `old_recommender`. Because rollout is gradual, each
expansion (10% → 50% → 100%) is a checkpoint where you confirm metrics are healthy before
widening. This turns a release from an irreversible all-at-once bet into a controlled,
observable, instantly-reversible process — and the same mechanism powers canary deploys and
A/B experiments (8.14) that measure the *real* impact (8.5) before committing.

### The code, every line explained

```python
# --- flag-gated code path: deploy dark, release gradually ---------------
def recommend(user):
    if flags.enabled("new_recommender", user):    # per-user runtime decision (no redeploy)
        return new_recommender(user)
    return old_recommender(user)                   # safe fallback for everyone not in rollout

# --- percentage rollout (deterministic per user, not random per call) ---
import hashlib
def in_rollout(feature, user_id, pct):
    # hash user+feature -> stable 0–99 bucket; same user always gets the same answer
    h = int(hashlib.sha256(f"{feature}:{user_id}".encode()).hexdigest(), 16) % 100
    return h < pct                                 # pct=1 -> ~1% of users; raise pct to widen
# IMPORTANT: bucket by a STABLE id, not random() per request, or a user flips between
# old/new on every call -> inconsistent experience and unmeasurable results.

# --- the rollout procedure ----------------------------------------------
# 1. deploy with flag at 0% (code is live but DARK — nobody sees it)
# 2. enable for internal users / 1% -> watch error rate, latency (9.15), business metrics
# 3. healthy? widen 1% -> 10% -> 50% -> 100%, checking metrics at each step
# 4. problem at any step? set the flag to 0% -> INSTANT rollback, no redeploy, no panic

# --- instant kill switch (the main payoff) ------------------------------
# flags.set("new_recommender", 0)   # turn it off NOW for everyone — seconds, not a deploy
# compare to big-bang: rollback = emergency redeploy while production is broken.

# --- A/B testing reuses the same machinery (8.14) -----------------------
# split users into flag-on vs flag-off, compare the REAL KPI between groups -> decide if the
# new version is actually better in production, not just offline (8.5/8.14).

# --- clean up flags afterwards (avoid flag debt) ------------------------
# once new_recommender is at 100% and proven, REMOVE the flag and the old path. Stale flags
# accumulate into untested dead branches and config complexity -> delete them deliberately.
```

### Impact

- **Bounded blast radius:** a bad change hits 1% of users, caught by metrics, instead of 100%
  — the difference between a minor blip and a full outage.
- **Instant, calm rollback:** flipping a flag off recovers in seconds without a redeploy,
  versus a panicked emergency deploy while production is down.
- **Decouples deploy from release & enables experiments:** ship code dark and release on your
  schedule; reuse the same flags for canary releases and A/B tests (8.14) that measure real
  impact before full commitment.

### Pros & cons / when NOT to

**Use flags & staged rollout when:** shipping risky or user-facing changes — new features, a
new model/recommender, performance-sensitive rewrites, anything where offline tests can't fully
de-risk real traffic.

**Watch out / when NOT to:**
- **Bucket by a stable id, not per-request randomness** — `random()` per call flips a user
  between old/new constantly (jarring UX, unmeasurable). Hash a stable user/account id so
  assignment is consistent.
- **Watch metrics at each stage** (7.10/9.15) — a staged rollout without observability is just
  a slower big-bang; the point is to *detect* problems at small scale and halt.
- **Clean up flags after rollout** — leaving permanent flags creates "flag debt": untested dead
  code paths and config sprawl. Remove the flag and old path once the change is proven at 100%.
- **Flags add branching complexity** — every flag doubles a code path; too many interacting
  flags get hard to reason about and test. Use them for genuine release risk, not as permanent
  config (that's 7.14), and keep them short-lived.
- **Not everything needs a flag** — a trivial, low-risk change behind comprehensive tests
  (10.8) may not warrant the overhead; reserve the machinery for changes with real blast
  radius.

### Where this shows up

- **Real work — production feature releases:** flag-gated, percentage rollouts are the
  standard way mature teams ship user-facing changes safely (LaunchDarkly, Unleash, or a
  homegrown flag service).
- **Real work — ML model rollout:** releasing a new model to 1% → 100% while monitoring
  metrics, with an instant flag-off if quality/latency regress (9.15) — and A/B testing it vs
  the old model (8.14).
- **Real work — incident mitigation:** flipping a flag to disable a misbehaving feature as the
  fast first response during an incident, before diagnosing.
- **Pattern mapping (secondary):** no DSA analogue; it's the risk-management/blast-radius
  principle for shipping — make releases gradual, observable, and reversible — the deployment
  capstone that the testing scenarios (10.8–10.11) lead up to.

[↑ Back to top](#contents)

