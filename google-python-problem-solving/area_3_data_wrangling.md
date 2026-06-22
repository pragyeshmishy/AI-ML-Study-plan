# Area 3 — Data Wrangling & Data Engineering

The unglamorous 80% of every data/ML job: getting messy real-world data off disk and
into a shape you can trust. These are the moves for reading dirty files, surviving
missing values, normalising types and dates, joining and grouping records, and
reaching for pandas only when it earns its place. Bias throughout: examples from the
data-prep work that sits in front of every model.

---

<a id="contents"></a>
## Contents

- [3.1 — "My CSV chokes on types and missing values" → robust CSV reading](#3.1)
- [3.2 — "A JSONL corpus too big for RAM" → stream line-delimited JSON](#3.2)
- [3.3 — "Pulling fields from deeply nested JSON" → safe `.get` chains / walking](#3.3)
- [3.4 — "Dirty values crash my conversions" → safe coercion (int/float/bool)](#3.4)
- [3.5 — "Missing or null fields everywhere" → defaults & sentinel handling](#3.5)
- [3.6 — "Validate incoming data against a shape" → schema validation (pydantic/dataclass)](#3.6)
- [3.7 — "Parse and normalise dates/timestamps" → datetime & timezones](#3.7)
- [3.8 — "Date arithmetic — within last N days, durations" → `timedelta`](#3.8)
- [3.9 — "Text encoding/decoding errors (UTF-8/BOM)" → encoding handling](#3.9)
- [3.10 — "Processing a directory of files robustly" → pathlib & glob](#3.10)
- [3.11 — "Pick the right on-disk format" → CSV/JSON/JSONL/Parquet/pickle trade-offs](#3.11)
- [3.12 — "Sanity-check a dataset before trusting it" → null counts, ranges, balance](#3.12)
- [3.13 — "Have I seen this before / dedup" → set membership](#3.13)
- [3.14 — "How many of each" → `Counter`](#3.14)
- [3.15 — "Group records by a field" → `defaultdict(list)`](#3.15)
- [3.16 — "Match two datasets on a key" → dict join](#3.16)
- [3.17 — "Find the top N" → `heapq`](#3.17)
- [3.18 — "Look up by two+ fields" → composite/tuple keys](#3.18)
- [3.19 — "Sort by multiple fields" → key functions & multi-key sort](#3.19)
- [3.20 — "Search/insert in sorted data" → `bisect`](#3.20)
- [3.21 — "DataFrame: vectorised ops vs row loops" → pandas thinking](#3.21)
- [3.22 — "DataFrame: group-by & merge" → split-apply-combine](#3.22)
- [3.23 — "Handle NaN/missing in arrays & frames" → fillna/dropna/masks](#3.23)
- [3.24 — "Reshape: pivot / explode lists into rows" → wide↔long](#3.24)

---


<a id="3.1"></a>
## 3.1 — "My CSV chokes on types and missing values" → robust CSV reading

### The situation

You have an export of sensor readings, `readings.csv`, that looks innocent:

```
sensor_id,temp_c,humidity,recorded_at
A1,19.4,55,2026-01-01T00:00:00
A1,,57,2026-01-01T00:01:00
A2,21.0,,2026-01-01T00:02:00
A1,not_a_number,60,2026-01-01T00:03:00
```

You write the obvious loop: split each line on commas, pull out the fields, convert
`temp_c` to a float:

```python
for line in open("readings.csv"):
    sensor, temp, humidity, ts = line.strip().split(",")   # split on commas
    temp = float(temp)                                      # convert to a number
    ...
```

It breaks almost immediately, in three different ways:

- **Row 2** has an empty `temp_c` (`""`). `float("")` raises `ValueError`.
- **Row 4** has the literal text `not_a_number`. `float("not_a_number")` raises
  `ValueError`.
- And the moment any field contains a comma inside quotes — e.g. an address
  `"Mumbai, MH"` — `line.split(",")` shreds it into the wrong number of fields and
  every subsequent column shifts. Your `sensor, temp, humidity, ts = ...` unpack then
  raises `ValueError: too many values to unpack`.

"Robust CSV reading" concretely means: **(a)** parse the file with something that
understands CSV's quoting rules so embedded commas don't break it, **(b)** address
columns by *name* not position, and **(c)** convert each field with a fallback so one
bad cell doesn't kill the whole run. Before: row 4 crashes the job. After: row 4's
temp becomes `None` (a flagged missing value) and processing continues.

### What's really going on

CSV *looks* like "text split on commas", but it is a real format with rules:
fields can be **quoted** (`"Mumbai, MH"`) so they may contain commas, newlines, and
escaped quotes. Hand-rolling `split(",")` reimplements a parser badly and gets the
quoting wrong. Python's standard library ships a correct one: the **`csv` module**.

Separately, the type problem is its own thing: real CSV cells are *all text*, and some
of that text is empty or garbage. Converting needs to be **defensive** — attempt the
conversion, and on failure produce a sentinel (`None`) rather than crashing. (That
defensive-conversion idea gets its own deep dive in 3.4; here we use the simplest
form.)

### The move

Use **`csv.DictReader`**, which parses quoting correctly *and* hands you each row as a
dict keyed by the header names — then convert fields through a tiny safe helper:

```python
import csv

def to_float(s):                              # safe string -> float
    try:
        return float(s)                       # attempt the conversion
    except (ValueError, TypeError):           # empty, garbage, or None
        return None                           # flag as missing, don't crash

with open("readings.csv", newline="") as f:   # newline="" is required for csv (below)
    for row in csv.DictReader(f):             # row is a dict: {"sensor_id": "A1", ...}
        temp = to_float(row["temp_c"])        # address by NAME; bad cells -> None
        ...
```

### Why it works

`csv.DictReader` reads the first line as the **header** and yields every subsequent row
as a dict mapping `header -> cell`. Because it implements the CSV quoting rules, a
quoted `"Mumbai, MH"` arrives as one field, not two — the column-shift bug is gone.
Addressing by name (`row["temp_c"]`) means inserting or reordering columns upstream
doesn't silently break your indices.

The `to_float` helper turns "this cell won't convert" from a crash into a `None` you
can detect and handle later (drop the row, impute a value, count it as missing). One
dirty cell costs you one `None`, not the whole job.

### The code, every line explained

```python
import csv

# A "sentinel" is a stand-in value meaning "no real value here"; None is Python's.
def to_float(s):                          # convert one cell to float, safely
    try:
        return float(s)                   # "19.4" -> 19.4 ; "" and "abc" raise
    except (ValueError, TypeError):       # ValueError: bad text; TypeError: got None
        return None                       # sentinel: this reading is missing/invalid

# newline="" : tell open() NOT to translate newlines itself — the csv module handles
# line endings internally. Omitting it can corrupt rows that contain embedded newlines
# inside quoted fields. ALWAYS pass newline="" when opening a file for csv.
with open("readings.csv", newline="") as f:
    reader = csv.DictReader(f)            # first line becomes the field names (header)
    for row in reader:                    # each row: {"sensor_id": "A1", "temp_c": "", ...}
        sensor   = row["sensor_id"]       # by NAME, not row[0] — order-independent
        temp     = to_float(row["temp_c"])      # "" or "not_a_number" -> None
        humidity = to_float(row["humidity"])    # missing -> None
        ts       = row["recorded_at"]     # leave as text for now (parsed in 3.7)
        if temp is None:                  # decide policy for missing readings:
            continue                      # ...here we skip them (could also impute)
        process(sensor, temp, humidity, ts)

# --- Writing CSV correctly is the mirror image: DictWriter ---------------
rows = [{"sensor_id": "A1", "temp_c": 19.4}, {"sensor_id": "A2", "temp_c": 21.0}]
with open("out.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["sensor_id", "temp_c"])  # fix column order
    writer.writeheader()                  # write the header row first
    writer.writerows(rows)                # DictWriter quotes/escapes for you

# --- A non-comma delimiter (TSV, semicolon-separated European exports) ----
# reader = csv.DictReader(f, delimiter="\t")   # tab-separated; ";" for many EU files
# Don't guess: csv.Sniffer().sniff(sample) can detect the delimiter if you must.
```

### Impact

- **Correctness:** quoting/embedded-comma bugs vanish — the single biggest source of
  silent column-shift corruption in hand-rolled parsers.
- **Robustness:** one malformed cell becomes a detectable `None`, not a crash, so a
  10-million-row file isn't killed by row 4.
- **Maintainability:** name-based access survives upstream column reordering; the code
  reads as "the temperature column", not "column 1".

### Pros & cons / when NOT to

**Reach for `csv.DictReader` when:** you're reading real-world CSV/TSV with a header
and need named, quoting-correct access — the default for any delimited text file.

**Watch out / when NOT to:**
- **It's still all strings.** `DictReader` does *no* type conversion — every value is
  text. You must coerce (3.4) and handle missing (3.5) yourself.
- **For heavy analytical work, jump to pandas** (`pd.read_csv`, 3.21) — it does typed
  parsing, missing-value handling, and is far faster for column maths. Use the `csv`
  module when you want streaming, low-dependency, row-at-a-time control (e.g. a file
  bigger than RAM — combine with the generator pattern from 1.2).
- **`newline=""` is not optional.** Forgetting it works on simple files and then
  mangles any row with a newline inside a quoted field — a classic intermittent bug.
- **Giant files:** `DictReader` is itself lazy (yields row by row), so it streams
  fine; but `list(reader)` pulls everything into memory — don't, on a huge file.

### Where this shows up

- **Real work — dataset ingestion:** loading a labelled CSV before training, coercing
  feature columns and dropping/imputing the rows that won't parse.
- **Real work — ETL from exports:** ingesting CRM/billing/sensor exports that contain
  quoted free-text fields (addresses, comments) where naive splitting corrupts rows.
- **Real work — interop:** writing model predictions back out as CSV for a downstream
  team, with `DictWriter` guaranteeing correct quoting.
- **Pattern mapping (secondary):** not an algorithm pattern; it's the parsing-boundary
  discipline — "parse once at the edge into clean typed records" — that underlies the
  validate-at-the-boundary scenarios in the robustness area (7.1).
[↑ Back to top](#contents)

---

<a id="3.2"></a>
## 3.2 — "A JSONL corpus too big for RAM" → stream line-delimited JSON

### The situation

You've been handed a 40 GB training corpus, `corpus.jsonl`, where every line is one
self-contained JSON object (this format is **JSONL** / **JSON Lines** / NDJSON —
"newline-delimited JSON"):

```
{"id": "doc1", "text": "the cat sat", "lang": "en"}
{"id": "doc2", "text": "le chat", "lang": "fr"}
{"id": "doc3", "text": "the dog ran", "lang": "en"}
... (20 million more lines)
```

You reach for the obvious "load the JSON file" call:

```python
import json
data = json.load(open("corpus.jsonl"))    # parse the whole file as one JSON value
for doc in data:
    process(doc)
```

Two things go wrong. First, `json.load` **fails immediately** with
`json.JSONDecodeError: Extra data` — because the file is *not* one JSON document, it's
millions of separate ones stacked vertically. Second, even if it were one giant JSON
array, `json.load` would try to build the **entire** 40 GB structure in memory at once
and your process would be OOM-killed (out-of-memory — the OS terminating you for using
too much RAM, as in 1.2).

### What's really going on

`json.load` (note: no "s") is for reading **one** JSON document from a file in its
entirety. JSONL deliberately is *not* one document — it's a stream of independent
documents, **one per line**, precisely so you can process it **line by line** without
ever holding more than one record in memory.

The realisation is the same as the generator insight from 1.2: you consume these
records **once, in order**, so you never need them all in memory simultaneously. The
right move is to read the file line by line and parse **each line on its own** with
`json.loads` (note: the "s" = "string" — parse a JSON *string*, not a file).

### The move

Iterate the file (which yields one line at a time, lazily) and parse each line
individually with **`json.loads`**, wrapped in a **generator** so the whole pipeline
stays O(1) in memory:

```python
import json

def read_jsonl(path):
    with open(path, encoding="utf-8") as f:   # files iterate line by line, lazily
        for line in f:                         # one text line at a time
            line = line.strip()                # drop trailing newline / stray spaces
            if line:                           # skip blank lines (common at EOF)
                yield json.loads(line)         # parse THIS line into a dict, hand it out

for doc in read_jsonl("corpus.jsonl"):         # only ONE doc in memory at any moment
    process(doc)
```

### Why it works

Opening a file gives you an object that **iterates one line at a time** — it never
loads the whole file. For each line, `json.loads(line)` parses just that single
small JSON object. Wrapping it in a generator with `yield` (1.2) means the caller
pulls one record, uses it, and discards it before the next is parsed — so memory is
**O(1)** (one record) regardless of whether the file is 40 KB or 40 GB.

Writing JSONL is the exact mirror: serialise each record with `json.dumps` and write it
followed by `\n`, so each object lands on its own line.

### The code, every line explained

```python
import json

# --- Reading: a streaming generator (O(1) memory) ------------------------
def read_jsonl(path):
    with open(path, encoding="utf-8") as f:   # encoding="utf-8": JSON is UTF-8 (see 3.9)
        for line in f:                         # lazy: one line per iteration
            line = line.strip()                # remove the "\n" and surrounding space
            if not line:                       # blank line? skip it
                continue
            yield json.loads(line)             # parse one JSON object -> a dict
# json.loads (string) vs json.load (file): loads takes TEXT, load takes a FILE OBJECT.

# --- A robust reader that survives ONE bad line --------------------------
def read_jsonl_safe(path):
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):   # 1-based line numbers (1.5)
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)         # attempt to parse this line
            except json.JSONDecodeError as e:  # a single corrupt line...
                print(f"skipping bad line {line_no}: {e}")   # ...log and skip it,
                continue                       # don't let it kill a 20M-line job

# --- Writing JSONL: one json.dumps per line ------------------------------
records = [{"id": "doc1", "text": "hi"}, {"id": "doc2", "text": "bye"}]
with open("out.jsonl", "w", encoding="utf-8") as f:
    for rec in records:
        f.write(json.dumps(rec, ensure_ascii=False))   # serialise dict -> JSON text
        f.write("\n")                          # one object PER LINE — the whole point
# ensure_ascii=False keeps non-English characters readable (é, 中) instead of \uXXXX.

# --- Consuming the stream with O(1) memory all the way through -----------
en_count = sum(1 for doc in read_jsonl("corpus.jsonl") if doc["lang"] == "en")
# The generator expression feeds sum() one doc at a time; 40 GB never sits in RAM.
```

### Impact

- **Memory:** O(n) → O(1). The difference between an OOM kill and a job that streams a
  terabyte in a flat, tiny footprint.
- **Latency to first record:** processing starts on line 1 — you don't wait for a 40 GB
  parse to finish before anything happens.
- **Resilience:** the `read_jsonl_safe` variant means one corrupt line costs one record,
  not the entire corpus (ties to partial-failure handling, 7.9).

### Pros & cons / when NOT to

**Reach for JSONL streaming when:** the data is large, arrives incrementally, or is
naturally a *sequence of records* (logs, events, training examples, API exports).
JSONL is the de-facto format for ML corpora precisely because it streams.

**Watch out / when NOT to:**
- **A single normal `.json` file is NOT JSONL.** If the file is one big JSON
  array/object, `json.loads(line)` per line fails — use `json.load(f)` (whole file) or
  a streaming parser like `ijson` for a huge single document.
- **Each line must be complete JSON on its own.** If a producer wrote pretty-printed
  (multi-line indented) JSON objects, they span several lines and line-splitting breaks
  — JSONL requires one compact object per line.
- **Generators are single-use** (1.2): one pass exhausts the stream. Need two passes?
  Re-open the file (cheap) rather than `list(...)`-ing 40 GB into memory.
- **Tiny files:** for a few hundred records that fit comfortably in RAM, `json.load` of
  a normal JSON array is simpler — don't add streaming you don't need.

### Where this shows up

- **Real work — LLM/ML training corpora:** virtually all large text/instruction
  datasets ship as `.jsonl`; you stream them into tokenisation/training so the dataset
  never has to fit in memory (ties to data loaders, 1.2).
- **Real work — log & event pipelines:** application logs and analytics events are
  commonly one-JSON-object-per-line, streamed through ETL.
- **Real work — API bulk exports:** large "export everything" endpoints return NDJSON so
  the client can process while the server is still sending.
- **Pattern mapping (secondary):** the streaming-generator structure is the iterator
  pattern again (1.2); the "process a stream, keep O(1) state" shape underlies running
  aggregates and the single-pass scans in Area 11.
[↑ Back to top](#contents)

---

<a id="3.3"></a>
## 3.3 — "Pulling fields from deeply nested JSON" → safe `.get` chains / walking

### The situation

An API returns a user record where the field you actually want — the city — is buried
four levels deep, and not every record has every level filled in:

```python
record = {
    "user": {
        "id": "u_42",
        "profile": {
            "address": {
                "city": "Berlin",
                "geo": {"lat": 52.52, "lon": 13.40}
            }
        }
    }
}
```

You write the natural chain of square brackets:

```python
city = record["user"]["profile"]["address"]["city"]   # "Berlin"
```

It works on *this* record. Then the next record arrives with no address (the user never
filled it in):

```python
record2 = {"user": {"id": "u_43", "profile": {}}}      # profile is empty
city = record2["user"]["profile"]["address"]["city"]   # KeyError: 'address'  -> CRASH
```

One missing level anywhere in the chain raises `KeyError` and kills the loop. Real API
and document data is *full* of optional nesting like this. "Pulling fields safely"
concretely means: reach four levels down and get `"Berlin"` when it's there, and a
default (say `None` or `"unknown"`) when *any* level along the way is missing — without
a crash and without a pyramid of `if`s.

### What's really going on

`d["key"]` **demands** the key exists and raises `KeyError` if not. With a chain, the
*first* missing link breaks everything. You're using the strict accessor when you want
a *forgiving* one.

`dict.get(key, default)` is the forgiving accessor: it returns `d[key]` if present, or
`default` (which itself defaults to `None`) if absent — **no exception**. The trick for
nesting is to make each step return an empty dict `{}` on a miss, so the *next* `.get`
still has something safe to call `.get` on. This is "walking" the structure defensively,
one safe step at a time.

### The move

Chain **`.get(key, {})`** at each level so a missing branch degrades to an empty dict
instead of crashing, then `.get` the final value with your real default:

```python
city = (
    record.get("user", {})        # {} if no "user"
          .get("profile", {})     # {} if no "profile"
          .get("address", {})     # {} if no "address"
          .get("city")            # None if no "city" (final default)
)
```

For repeated use, wrap the pattern in a tiny **`dig`** helper that walks a path of keys.

### Why it works

Each `.get(key, {})` guarantees its result is *something you can keep calling `.get` on*
— either the real nested dict, or an empty one. So a missing `"address"` makes that step
return `{}`, and `{}.get("city")` quietly returns `None` instead of raising. The default
on the **final** `.get` is the value you actually want when the path doesn't exist. The
whole chain can never raise `KeyError`, because no step ever uses strict `[]` access.

### The code, every line explained

```python
# --- The strict chain: one missing level = KeyError ----------------------
# city = record["user"]["profile"]["address"]["city"]   # crashes if ANY level absent

# --- Safe .get chain: each miss degrades to {} ---------------------------
city = (record.get("user", {})        # value of "user", or {} if missing
              .get("profile", {})     # then "profile", or {}
              .get("address", {})     # then "address", or {}
              .get("city"))           # finally "city", or None (get's default)
# Reading "Berlin" works; the empty-profile record yields None — no crash.

# --- A reusable walker: dig(record, "user", "profile", "address", "city") -
def dig(d, *keys, default=None):       # *keys = the path, as separate arguments (1.8)
    for key in keys:                   # walk one level per key
        if isinstance(d, dict):        # only descend if we still have a dict
            d = d.get(key)             # step down; missing -> None
        else:
            return default             # path broke (hit a non-dict/None) -> default
    return d if d is not None else default

city = dig(record, "user", "profile", "address", "city")          # "Berlin"
city = dig(record2, "user", "profile", "address", "city", default="unknown")  # "unknown"

# --- Walking through a LIST level (e.g. first address of many) -----------
data = {"user": {"addresses": [{"city": "Berlin"}, {"city": "Paris"}]}}
first_city = (data.get("user", {})
                  .get("addresses", [{}])   # default to a 1-element list of {} ...
                  [0]                        # ... so [0] is always safe
                  .get("city"))              # "Berlin"
# When indexing a list that might be empty, default to [{}] so [0] never IndexErrors.

# --- Python 3.10+ structural match for fixed-shape extraction ------------
match record:
    case {"user": {"profile": {"address": {"city": str(city)}}}}:  # bind city if shape fits
        found = city                  # "Berlin"
    case _:                           # any other shape
        found = None
# match (1.21) is great when you want "extract IFF the whole shape matches".
```

### Impact

- **Robustness:** the loop survives records with missing optional fields — the normal
  case in real API/document data — instead of dying on record #2.
- **Clarity:** `dig(rec, "user", "profile", "city")` states the path in one readable
  line versus four nested `if key in ...` guards.
- **Consistency:** every missing path yields the *same* explicit default, so downstream
  code has one "missing" value to check rather than guessing where the chain broke.

### Pros & cons / when NOT to

**Reach for `.get` chains / `dig` when:** extracting **optional** fields from nested
API responses, config trees, or document stores where levels may be absent.

**Watch out / when NOT to:**
- **`.get(k, {})` masks real bugs if the field is supposed to be mandatory.** If a
  missing `"user"` means the data is corrupt, you *want* the loud `KeyError` (or an
  explicit validation step, 3.6) — don't paper over structural errors you should catch.
- **It silently conflates "absent" with "present but null".** `.get("city")` returns
  `None` for both "no city key" and `"city": null`. If you must distinguish them, check
  membership (`"city" in d`) explicitly.
- **Deeply repetitive extraction across many fields** is a sign you should validate the
  whole record into a typed object once (pydantic, 3.6) and then access attributes
  safely, rather than `dig`-ging field by field everywhere.
- **`jmespath` / `glom`** are third-party libraries purpose-built for path extraction
  from nested data — worth it when paths get complex (wildcards, filters).

### Where this shows up

- **Real work — API response parsing:** pulling specific fields out of large, deeply
  nested JSON from REST/GraphQL responses where many fields are optional.
- **Real work — config & manifest reading:** safely reading `config["model"]["params"]
  ["lr"]` from a nested YAML/JSON config that may omit sections.
- **Real work — LLM tool/function-call outputs:** extracting `arguments.location` from a
  nested tool-call payload that isn't guaranteed to be fully populated (ties to parsing
  LLM JSON, 9.10).
- **Pattern mapping (secondary):** `dig` is a small **tree traversal** — walking down a
  nested structure by a path — the same descent used in trie/tree-path problems
  (Area 11), just over dicts instead of nodes.
[↑ Back to top](#contents)

---

<a id="3.4"></a>
## 3.4 — "Dirty values crash my conversions" → safe coercion (int/float/bool)

### The situation

You're converting a column of "amounts" that came from a spreadsheet export. The values
*look* numeric but are a minefield of human formatting:

```python
raw = ["42", "42.0", " 42 ", "1,000", "$50", "", "N/A", "true", None, "3.5"]
amounts = [int(x) for x in raw]      # the naive conversion
```

It explodes on the *second* element: `int("42.0")` raises `ValueError` (because `int`
won't parse a string with a decimal point), and even if you switch to `float`, you'll
still hit `float("1,000")`, `float("$50")`, `float("")`, `float("N/A")` and
`float(None)` — five more `ValueError`/`TypeError` crashes. A single bad cell in a
million-row column kills the entire job.

"Safe coercion" concretely means a function that takes *any* of these messy inputs and
returns either a clean number or an agreed sentinel — never raises. Before:
`int("42.0")` → crash. After: `to_float("1,000")` → `1000.0`, `to_float("N/A")` →
`None`, and the loop finishes.

### What's really going on

Two separate problems hide here. First, **`int` and `float` are strict parsers** — they
accept only their exact grammar (`int("42.0")` and `float("1,000")` are both invalid by
design). Second, real data carries **formatting noise** (thousands separators, currency
symbols, whitespace, "N/A" placeholders) that you must *strip* before a parser will
accept it.

So safe coercion is two steps: **clean** the string (strip noise), then **attempt** the
conversion inside `try/except` (the EAFP style from 1.10), returning a sentinel on
failure. Wrapping this once means every messy cell is handled the same way.

There's also a notorious trap with **booleans**: `bool("false")` is `True`, and so is
`bool("0")` and `bool("no")` — because `bool` of *any* non-empty string is `True`. It
only checks "is the string non-empty", not what it *says*. Boolean coercion from text
needs an explicit lookup table, not `bool()`.

### The move

Write small, total (never-raising) coercion helpers — clean then convert in a `try`:

```python
def to_float(value, default=None):
    if value is None:
        return default
    s = str(value).strip().replace(",", "").lstrip("$")  # clean noise first
    try:
        return float(s)                                  # then attempt the parse
    except ValueError:
        return default                                   # garbage -> sentinel

def to_int(value, default=None):
    f = to_float(value, None)                            # reuse float, then narrow
    return int(f) if f is not None else default          # int(42.0) is fine
```

For booleans, map known truthy/falsy *strings* explicitly — never use `bool()` on text.

### Why it works

The cleaning step (`strip`, `replace(",", "")`, `lstrip("$")`) turns the *valid-but-
noisy* inputs (`" 42 "`, `"1,000"`, `"$50"`) into strings the strict parser accepts.
The `try/except` then catches the *genuinely* unparseable inputs (`"N/A"`, `""`) and
converts the crash into a sentinel. Building `to_int` on top of `to_float` is the key
move: it lets `"42.0"` succeed (parse to `42.0`, then narrow to `42`), which strict
`int()` refuses outright.

For booleans, an explicit string→bool map reads the *content* of the text, fixing the
`bool("false") == True` trap by design.

### The code, every line explained

```python
# --- Safe float: clean the noise, then attempt the parse -----------------
def to_float(value, default=None):
    if value is None:                     # None can't be cleaned as text -> default
        return default
    s = str(value).strip()                # ensure str, drop surrounding whitespace
    s = s.replace(",", "")                # "1,000" -> "1000" (thousands separators)
    s = s.lstrip("$").lstrip("£")         # strip a leading currency symbol if present
    try:
        return float(s)                   # "42", "42.0", "1000", "50" all parse now
    except ValueError:                    # "", "N/A", "abc" -> not a number
        return default                    # sentinel instead of a crash

# --- Safe int: go via float so "42.0" works ------------------------------
def to_int(value, default=None):
    f = to_float(value, None)             # reuse the cleaning + float parse
    if f is None:
        return default
    return int(f)                         # int(42.0) -> 42 ; truncates 3.9 -> 3 (beware!)

# --- Safe bool: an EXPLICIT lookup, never bool() on a string -------------
_TRUE  = {"true", "t", "yes", "y", "1", "on"}     # lowercase truthy spellings
_FALSE = {"false", "f", "no", "n", "0", "off"}    # lowercase falsy spellings
def to_bool(value, default=None):
    if isinstance(value, bool):           # already a real bool -> return as-is
        return value
    s = str(value).strip().lower()        # normalise case + whitespace (see 4.1)
    if s in _TRUE:  return True
    if s in _FALSE: return False
    return default                        # unrecognised -> sentinel
# WHY not bool("false")? bool() is True for ANY non-empty string -> "false" -> True!
# bool() tests emptiness, not meaning. Always map known strings explicitly.

# --- Putting it together on the messy column -----------------------------
raw = ["42", "42.0", " 42 ", "1,000", "$50", "", "N/A", "true", None, "3.5"]
cleaned = [to_float(x) for x in raw]
# -> [42.0, 42.0, 42.0, 1000.0, 50.0, None, None, None, None, 3.5]
#    valid-but-noisy parsed;  truly-bad -> None;  "true" isn't a float -> None.
```

### Impact

- **Robustness:** the conversion step becomes *total* — it always returns, so one dirty
  cell yields a `None` to handle, never a job-killing exception.
- **Correctness:** the cleaning recovers genuinely-valid values (`"1,000"`, `"$50"`,
  `" 42 "`) that strict parsers would wrongly reject, and the explicit bool map kills the
  `bool("false")` trap.
- **Consistency:** every column converts through the same helpers, so "missing/invalid"
  is uniformly represented as your chosen sentinel.

### Pros & cons / when NOT to

**Reach for safe coercion when:** ingesting human- or system-generated text columns
(CSV cells, form inputs, scraped values, config strings) where formatting is inconsistent.

**Watch out / when NOT to:**
- **`int(float_value)` truncates toward zero** — `to_int("3.9")` gives `3`, not `4`. If
  you mean to round, use `round()`; decide deliberately.
- **Silently defaulting can hide systematic problems.** If 30% of a column coerces to
  `None`, that's not noise — it's a schema mismatch you should *surface* (count it, 3.12),
  not quietly swallow.
- **Locale differs:** some regions use `.` as the thousands separator and `,` as the
  decimal point (`1.000,50` = 1000.5). The simple `replace(",", "")` above assumes the
  Anglo convention — handle locale explicitly if your data uses the other.
- **For whole-DataFrame work, use pandas' typed parsers:** `pd.to_numeric(col,
  errors="coerce")` does exactly this (bad → `NaN`) across a column far faster than a
  Python loop (3.21, 3.23). The hand-rolled helpers are for row-at-a-time / non-pandas code.

### Where this shows up

- **Real work — feature ingestion:** coercing raw feature columns to numeric before
  training, turning unparseable cells into `NaN`/`None` for the imputation step (8.x).
- **Real work — config & env vars:** environment variables are *always* strings;
  `to_bool(os.environ.get("DEBUG"))` and `to_int(os.environ.get("WORKERS"))` safely turn
  them into typed values (ties to 12-factor config, 7.15).
- **Real work — form / API payload parsing:** user-supplied "numbers" arrive as messy
  strings; coerce-with-default at the boundary before they enter your logic.
- **Pattern mapping (secondary):** this is the "parse, don't validate-later" discipline —
  convert to the right type *once* at the edge — which underpins the boundary-validation
  scenarios (7.1) and pairs with the missing-value handling in 3.5.
[↑ Back to top](#contents)

---

<a id="3.5"></a>
## 3.5 — "Missing or null fields everywhere" → defaults & sentinel handling

### The situation

You're flattening user records into a feature row, but the records are ragged — every
one is missing *something*, and "missing" shows up in several disguises:

```python
records = [
    {"name": "Ann", "age": 30, "country": "DE", "score": 0},
    {"name": "Bob", "age": None, "country": "FR"},          # age is null; score absent
    {"name": "Cy",  "age": 25, "country": "",   "score": 7},# country is empty string
    {"name": "Di",  "country": "IN", "score": 0},           # age key absent entirely
]
```

You try to read fields directly:

```python
for r in records:
    age = r["age"]                       # KeyError on Di (no "age" key)
    label = "active" if r["score"] else "idle"   # KeyError on Bob (no "score")
```

It crashes on the absent keys. And even the rows that don't crash hide a subtler bug:
`r["score"]` for Ann is `0`, and `if r["score"]` treats `0` as falsy — so Ann (a real
score of zero) gets labelled `"idle"` exactly like someone with no score at all. You
have **three distinct kinds of "nothing"** — *key absent*, *value is `None`*, and
*value is an empty/zero placeholder* — and they need different handling. "Handling
missing fields" concretely means: give each field a sensible default when truly absent,
and **not** confuse a legitimate `0`/`""` with missing.

### What's really going on

There are genuinely different states, and conflating them is the root bug:

- **Key absent** — the field was never provided. `r["age"]` raises `KeyError`.
- **Value is `None`** — the field exists but is explicitly null.
- **Value is "empty"** — `0`, `""`, `[]`: a *real* value that happens to be falsy (1.17).

`dict.get(key, default)` solves *key absent* cleanly. But to also catch explicit `None`,
you often want "give me the value, but if it's missing **or** null, use the default" —
which `.get` alone doesn't do (`{"age": None}.get("age", 25)` returns `None`, not `25`,
because the key *is* present). And you must **never** lean on truthiness to detect
missing, or you'll mistake a valid `0` for absent.

### The move

Use `.get` with a default for absent keys; add an explicit `is None` step (or the `or`
idiom, carefully) when null should also fall back; and reserve truthiness checks for
when you genuinely mean "empty or zero", not "missing".

```python
age = r.get("age", 0)                    # absent -> 0
if age is None:                          # present-but-null -> also fall back
    age = 0

country = r.get("country") or "unknown"  # "" (falsy) OR None OR absent -> "unknown"
                                         # OK here because "" should count as missing

score = r.get("score", 0)               # absent -> 0
has_score = "score" in r                 # distinguish "real 0" from "no score" if needed
```

### Why it works

`r.get("age", 0)` returns the stored value if the key exists and `0` otherwise — no
`KeyError`. The separate `if age is None` step handles the *other* missing-disguise
(explicit null) with an identity check (1.9), which can't be fooled. The `x or default`
idiom is a deliberate, different tool: it falls back on **any** falsy value (`None`,
`""`, `0`, `[]`) — perfect when an empty string really does mean "no country", but
**dangerous** when `0` is a valid value (it would wrongly replace it). Choosing between
`.get(k, d)` and `x or d` is choosing *which* notions of "missing" you want to collapse.

### The code, every line explained

```python
records = [
    {"name": "Ann", "age": 30, "country": "DE", "score": 0},
    {"name": "Bob", "age": None, "country": "FR"},
    {"name": "Cy",  "age": 25, "country": "",   "score": 7},
    {"name": "Di",  "country": "IN", "score": 0},
]

for r in records:
    # --- absent key: .get supplies a default, no KeyError ----------------
    age = r.get("age", 0)                 # Di has no "age" -> 0
    # --- present-but-None: catch it explicitly ---------------------------
    if age is None:                       # Bob's age is None -> also fall back
        age = 0
    # The two lines above as a one-liner WHEN 0 is an acceptable fallback for null:
    age = r.get("age") or 0               # absent->None->0 ; None->0 ; 0 stays 0 (0 or 0)
    # ^ subtle: this is fine here ONLY because the fallback (0) equals the falsy case.

    # --- empty string should mean "missing": `or` is the right tool ------
    country = r.get("country") or "unknown"   # "" -> "unknown"; "DE" stays "DE"

    # --- DANGER: don't use `or` when 0 is a VALID value ------------------
    score_wrong = r.get("score") or 99    # Ann's real 0 -> wrongly becomes 99!  BUG
    score_right = r.get("score", 99)      # absent -> 99; Ann's 0 stays 0        CORRECT
    # Use `.get(k, default)` (only "absent" falls back) when 0/""/[] are legitimate.

    # --- distinguish "real zero" from "no score at all" ------------------
    if "score" in r:                      # membership test = "was it provided?"
        label = "active" if r["score"] > 0 else "zero-but-present"
    else:
        label = "no-score"

# --- setdefault: fill a missing key in place (and return it) -------------
for r in records:
    r.setdefault("score", 0)              # if "score" absent, insert it as 0; else leave
# After this every record HAS a "score" key — handy before building a DataFrame.

# --- dict.get's default is evaluated eagerly -----------------------------
# r.get("x", expensive())   # expensive() runs even when "x" IS present! If the default
# is costly, guard it:  r["x"] if "x" in r else expensive()
```

### Impact

- **Robustness:** ragged records stop crashing — every field read has a defined outcome.
- **Correctness:** the `0`-is-valid bug (treating a real zero as missing) is avoided by
  choosing `.get(k, default)` over `or` when zeros/empties matter — a genuinely common
  source of silent data corruption.
- **Clarity:** the code documents, per field, *what missing means here* (absent? null?
  empty?) rather than leaving it implicit.

### Pros & cons / when NOT to

**Reach for these when:** assembling records from sources with optional/nullable fields
— exactly the everyday "not every row has every column" situation.

**Watch out / when NOT to:**
- **`x or default` silently eats valid `0`, `""`, `[]`, `False`.** This is the #1 bug in
  this area. Use it *only* when those falsy values genuinely mean "missing"; otherwise
  use `.get(key, default)` (which falls back on *absence only*).
- **A `None` default to `.get` doesn't distinguish absent from explicit null** — if that
  difference matters, test `"key" in r` separately.
- **Imputation is a modelling decision, not a parsing one.** Filling a missing `age`
  with `0` vs the column mean vs a "missing" indicator changes model behaviour — for ML
  features, do it deliberately downstream (8.x), don't bury it in the loader.
- **Mutable defaults:** never write `r.get("tags", [])` and then mutate the returned list
  expecting it to persist — and never reuse one shared list as a default across rows
  (the 1.4 trap). Build a fresh container per record.

### Where this shows up

- **Real work — feature assembly:** building a fixed-width feature row from records that
  omit optional fields, choosing per-feature defaults before vectorising.
- **Real work — API/config merging:** layering a user config over defaults, where absent
  keys take the default but an explicit `false`/`0` from the user must be respected.
- **Real work — event enrichment:** events with optional metadata (`utm_source`,
  `referrer`) where empty/absent both mean "unknown" — the `or "unknown"` case.
- **Pattern mapping (secondary):** this is the precise-semantics-of-"empty" discipline
  from truthiness (1.17), applied to data; the absent/null/empty trichotomy recurs in
  every "sparse record" problem.
[↑ Back to top](#contents)

---

<a id="3.6"></a>
## 3.6 — "Validate incoming data against a shape" → schema validation (pydantic/dataclass)

### The situation

A webhook delivers user-signup events that *should* look like this:

```python
good = {"user_id": "u_42", "age": 30, "email": "a@x.com", "is_premium": True}
```

But you don't control the producer, so you also receive these:

```python
bad1 = {"user_id": "u_43", "age": "thirty", "email": "a@x.com"}   # age is text
bad2 = {"age": 30, "email": "a@x.com"}                            # user_id missing
bad3 = {"user_id": "u_44", "age": -5, "email": "not-an-email"}    # nonsense values
```

If you just trust the dict and do `event["age"] + 1`, `bad1` raises `TypeError` deep
inside your business logic, `bad2` raises `KeyError`, and `bad3` sails through and
**corrupts your database** with a negative age and a malformed email — the worst case,
because nothing crashes; it's just wrong forever.

"Validate against a shape" concretely means: declare once that a valid event has a
**`user_id: str` (required), `age: int` in 0–150 (required), `email: str` matching an
email pattern (required), `is_premium: bool` (optional, default False)** — and then run
every incoming dict through that declaration so it's either **converted into a clean,
typed object** or **rejected with a precise error** *at the boundary*, before it touches
your logic.

### What's really going on

You're doing **schema validation** — checking that data conforms to an expected
*structure and set of constraints* (a "schema" = the declared shape: which fields exist,
their types, and what counts as valid). Hand-writing `if/isinstance/raise` for every
field is verbose, easy to get inconsistent, and gives poor error messages.

The Pythonic move is to **declare the schema once, declaratively**, and let a tool do
the checking. **pydantic** is the de-facto library for this: you write a class with
typed fields, and it validates *and coerces* incoming data, raising a single structured
error listing everything wrong. For lighter needs with no dependency, a **`@dataclass`**
plus a `__post_init__` check covers a lot of ground (though it does not auto-validate
types — you add the checks).

### The move

Declare a **pydantic `BaseModel`** with typed, constrained fields; construct it from the
incoming dict; catch `ValidationError` to reject bad input:

```python
from pydantic import BaseModel, EmailStr, Field, ValidationError

class SignupEvent(BaseModel):
    user_id: str                              # required string
    age: int = Field(ge=0, le=150)            # required int, 0 <= age <= 150
    email: EmailStr                           # required, validated email
    is_premium: bool = False                  # optional, defaults to False

try:
    event = SignupEvent(**incoming_dict)      # validate + coerce in one step
except ValidationError as e:
    log_and_reject(e)                         # precise, structured error
```

### Why it works

pydantic reads the type annotations and `Field(...)` constraints as a *specification*
and enforces them when you construct the model. It **coerces** where sensible (the
string `"30"` becomes `int 30`) and **rejects** where not (`"thirty"` can't become an
int → error). A missing required field, a wrong type, an out-of-range number, or a
malformed email each produce a `ValidationError` that names the *exact* field and
problem — so you fail at the boundary with a clear message, never deep inside business
logic. After construction, `event.age` is a real `int` you can trust; the rest of your
code never re-checks.

### The code, every line explained

```python
from pydantic import BaseModel, EmailStr, Field, ValidationError

class SignupEvent(BaseModel):             # a "model" = one declared record shape
    user_id: str                          # required: no default -> must be present
    age: int = Field(ge=0, le=150)        # ge/le = "greater/less than or equal" bounds
    email: EmailStr                       # EmailStr: a string that must look like email
    is_premium: bool = False              # has a default -> optional in the input

# --- Valid input: coerced into a typed object ----------------------------
event = SignupEvent(user_id="u_42", age="30", email="a@x.com")
# note age="30" (a string) is COERCED to int 30; is_premium defaults to False.
print(event.age, type(event.age))         # 30 <class 'int'>
print(event.model_dump())                 # -> clean dict, ready to store/serialise

# --- Invalid inputs: precise, structured rejection -----------------------
for bad in [
    {"user_id": "u_43", "age": "thirty", "email": "a@x.com"},   # age not numeric
    {"age": 30, "email": "a@x.com"},                            # user_id missing
    {"user_id": "u_44", "age": -5, "email": "not-an-email"},    # range + email fail
]:
    try:
        SignupEvent(**bad)
    except ValidationError as e:
        print(e.error_count(), "problem(s):", [d["loc"] for d in e.errors()])
        # e.errors() lists each failure: which field (loc) and why (msg, type).

# --- Custom cross-field / value rules with a validator -------------------
from pydantic import field_validator
class SignupEvent2(SignupEvent):
    @field_validator("user_id")           # run extra logic on a specific field
    @classmethod
    def must_have_prefix(cls, v):
        if not v.startswith("u_"):        # enforce a business rule pydantic can't infer
            raise ValueError("user_id must start with 'u_'")
        return v                          # validators return the (possibly cleaned) value

# --- Dependency-free alternative: dataclass + __post_init__ --------------
from dataclasses import dataclass
@dataclass
class Signup:                             # @dataclass auto-generates __init__ etc. (1.14)
    user_id: str
    age: int
    email: str
    is_premium: bool = False
    def __post_init__(self):              # runs right after __init__ — your checks here
        if not isinstance(self.age, int) or not (0 <= self.age <= 150):
            raise ValueError(f"bad age: {self.age!r}")
        if "@" not in self.email:
            raise ValueError(f"bad email: {self.email!r}")
# NOTE: @dataclass does NOT enforce types itself — the annotations are hints only;
# you must add the isinstance/range checks. pydantic does this automatically.
```

> Note: pydantic is a third-party library (`pip install pydantic`, with `pydantic[email]`
> for `EmailStr`). The API shown is pydantic v2. The dataclass alternative uses only the
> standard library.

### Impact

- **Fail at the boundary, not in the depths:** bad data is rejected the moment it
  arrives with a precise message, instead of causing a cryptic `TypeError` five functions
  later — or worse, silently corrupting storage.
- **Trust downstream:** once an object validates, every later line can treat its fields
  as correctly typed and in-range — no defensive re-checking.
- **Self-documenting:** the model *is* the spec — anyone reading it sees exactly what a
  valid record requires.

### Pros & cons / when NOT to

**Reach for schema validation when:** data crosses a trust boundary — API requests,
webhooks, file ingestion, config files, LLM structured output, queue messages.

**Watch out / when NOT to:**
- **pydantic coercion can be *too* helpful:** by default it will turn `"30"` into `30`
  and `1` into `True`. If you need strictness (reject a string where an int is required),
  use strict types/`Strict` mode — know which behaviour you want.
- **Validation has a cost.** For millions of rows in a tight loop, per-row pydantic
  construction is slower than vectorised pandas checks (3.12/3.23). Validate at the
  *boundary* (per request/message), not on every row of a bulk numeric job.
- **`@dataclass` does not validate types** — the annotations are documentation only at
  runtime. Either add explicit `__post_init__` checks or use pydantic if you want real
  enforcement.
- **Don't over-model internal, already-trusted data.** Validation pays off where data is
  *untrusted*; re-validating data you produced yourself one line ago is noise.

### Where this shows up

- **Real work — API request bodies:** FastAPI uses pydantic models as endpoint signatures
  so every request is validated automatically before your handler runs (ties to 10.x).
- **Real work — config loading:** parse a YAML/JSON config into a typed settings model so
  a typo'd or out-of-range setting fails loudly at startup, not at 3 a.m. (7.15).
- **Real work — LLM structured output:** validate (and repair) the JSON an LLM returns
  against a schema before trusting it as tool arguments (9.10, 9.11).
- **Pattern mapping (secondary):** no algorithm analogue; it's the "parse, don't validate
  repeatedly" boundary discipline that 3.4/3.5 feed into and 7.1 generalises.
[↑ Back to top](#contents)

---

<a id="3.7"></a>
## 3.7 — "Parse and normalise dates/timestamps" → datetime & timezones

### The situation

Your events arrive with timestamps in a depressing variety of formats, from different
upstream systems:

```python
"2026-01-01T12:30:00Z"         # ISO 8601, UTC (the "Z" means Zulu = UTC)
"2026-01-01T12:30:00+05:30"    # ISO 8601 with an offset (e.g. +05:30)
"01/02/2026"                   # is this 1 Feb or 2 Jan?? day/month ambiguity
"2026-01-01 12:30:00"          # ISO-ish but no timezone at all
1735734600                      # a Unix epoch integer (seconds since 1970-01-01 UTC)
```

You need to compare them, sort them, and bucket events "by day". But comparing a string
`"01/02/2026"` to `"2026-01-01..."` sorts alphabetically (wrong), and the *real* trap:
some timestamps carry a timezone and some don't. Subtract a "no timezone" datetime from
a "UTC" one and Python raises `TypeError: can't subtract offset-naive and offset-aware
datetimes`. "Normalise" concretely means: parse every one of these into a Python
`datetime` object that is **timezone-aware and in UTC**, so they're all directly
comparable and unambiguous.

### What's really going on

A timestamp string is just text until you **parse** it into a `datetime` object, which
knows it's a moment in time and can be compared, subtracted, and formatted. The crucial
distinction is **naive vs aware**:

- A **naive** datetime has *no timezone* (`tzinfo is None`) — it's "12:30 somewhere",
  meaningless for comparison across systems. `datetime.now()` and a parsed
  `"2026-01-01 12:30:00"` are naive.
- An **aware** datetime carries a timezone, so it pins an *exact* instant. `12:30 UTC`
  and `18:00 +05:30` are the *same* instant; awareness lets Python know that.

The golden rule of timestamp handling: **parse to aware-UTC at the boundary, store and
compute in UTC, convert to local time only for display.** Mixing naive and aware is the
source of nearly every datetime bug.

### The move

Parse with the right tool per format, then force everything to **aware UTC**:

- ISO 8601 strings → `datetime.fromisoformat(s)` (Python 3.11+ handles the trailing `Z`).
- Custom/ambiguous formats → `datetime.strptime(s, fmt)` with an explicit format string.
- Epoch numbers → `datetime.fromtimestamp(n, tz=timezone.utc)`.
- Naive results → attach UTC with `.replace(tzinfo=timezone.utc)`; aware-but-elsewhere →
  `.astimezone(timezone.utc)`.

### Why it works

Each parser turns text into a `datetime`. `fromisoformat` understands the ISO grammar
(including offsets); `strptime` reads a format string you supply (`%d/%m/%Y`), which
*disambiguates* `01/02/2026` because *you* declare day-first. Once parsed, the
naive/aware fix makes every datetime carry UTC, so `<`, `==`, subtraction, and grouping
all operate on comparable absolute instants. Converting to UTC (not just "having a
timezone") means two events from different zones are stored identically and sort
correctly.

### The code, every line explained

```python
from datetime import datetime, timezone

# --- ISO 8601 (the good case): fromisoformat -----------------------------
a = datetime.fromisoformat("2026-01-01T12:30:00Z")        # 3.11+ accepts the "Z"
b = datetime.fromisoformat("2026-01-01T12:30:00+05:30")   # offset preserved
print(a.tzinfo, b.tzinfo)            # both AWARE: UTC, and +05:30
# On Python <3.11, "Z" isn't accepted; replace it: s.replace("Z", "+00:00").

# --- Custom / ambiguous format: strptime with an explicit pattern --------
d = datetime.strptime("01/02/2026", "%d/%m/%Y")           # %d=day %m=month %Y=4-digit yr
print(d)                              # 2026-02-01 00:00:00  (declared day-first)
# strptime("01/02/2026", "%m/%d/%Y") would instead read it as 2 January — YOU decide.
# Result is NAIVE (no tz in the string) -> must attach one (below).

# --- Epoch seconds -> aware UTC ------------------------------------------
e = datetime.fromtimestamp(1735734600, tz=timezone.utc)   # ALWAYS pass tz=utc for epochs
# Without tz=, fromtimestamp uses the machine's LOCAL zone -> non-reproducible. Don't.

# --- The naive/aware fix: make EVERYTHING aware-UTC ----------------------
naive = datetime.strptime("2026-01-01 12:30:00", "%Y-%m-%d %H:%M:%S")  # tzinfo is None
aware_utc = naive.replace(tzinfo=timezone.utc)   # ATTACH UTC: "this clock time IS UTC"
#                          ^ use replace ONLY when you KNOW the naive time was already UTC.

elsewhere = b                                     # the +05:30 one
to_utc = elsewhere.astimezone(timezone.utc)       # CONVERT: shifts the clock to UTC
print(to_utc.isoformat())            # 2026-01-01T07:00:00+00:00  (12:30+05:30 == 07:00 UTC)
# replace(tzinfo=...) RELABELS without shifting; astimezone() SHIFTS to the new zone.
# Using the wrong one is a classic "off by the offset" bug.

# --- Now they're all comparable ------------------------------------------
events = [a, to_utc, aware_utc]
print(sorted(events))                # sorts by true instant — correct
# NEVER mix: sorted([a, naive]) -> TypeError (can't compare aware with naive).

# --- Display in local time ONLY at the edge ------------------------------
from zoneinfo import ZoneInfo        # stdlib timezone database (Python 3.9+)
local = ZoneInfo("Europe/Berlin")    # named zone -> handles DST correctly
print(a.astimezone(local).strftime("%Y-%m-%d %H:%M %Z"))   # format for humans, last step
```

### Impact

- **Correctness:** all timestamps become comparable absolute instants — sorting,
  "before/after", and dedup-by-time work right regardless of source format/zone.
- **No naive/aware crashes:** forcing aware-UTC at the boundary eliminates the
  `TypeError` and the silent "off by N hours" class of bugs.
- **Reproducibility:** epochs parsed with explicit `tz=utc` give the same result on every
  machine, not whatever the server's local zone happens to be.

### Pros & cons / when NOT to

**Reach for this when:** ingesting timestamps from logs, APIs, files, or databases —
i.e. always, the moment more than one system is involved.

**Watch out / when NOT to:**
- **`replace(tzinfo=...)` vs `astimezone()` are different.** `replace` *relabels* (assert
  "this was already that zone"); `astimezone` *converts* (shift the clock). Confusing
  them produces a time wrong by the offset. Use `replace` only to label a naive time you
  *know* the zone of.
- **Never use bare `datetime.now()`** for stored timestamps — it's naive and local. Use
  `datetime.now(timezone.utc)`.
- **`strptime` is strict:** the string must match the format exactly or it raises
  `ValueError` — wrap it in safe-coercion (3.4) if input is dirty, and prefer
  `fromisoformat` for ISO data (it's far faster than `strptime`).
- **For messy free-text dates** ("next Tuesday", "Jan 3rd '26"), reach for the
  third-party `dateutil.parser` or `pendulum` — but beware `dateutil`'s guessing can
  silently misread ambiguous dates; pin a format when you can.

### Where this shows up

- **Real work — event/log pipelines:** normalising timestamps from many services to UTC
  so they can be merged, sorted, and windowed (feeds directly into 3.8's "last N days").
- **Real work — time-series features:** deriving hour-of-day / day-of-week features for
  an ML model requires correctly-zoned datetimes, or the features are subtly wrong.
- **Real work — partitioning data by date:** bucketing records into daily files/folders
  (`2026-01-01/`) needs an unambiguous, zone-consistent notion of "which day".
- **Pattern mapping (secondary):** parsing to a canonical comparable form is the same
  "normalise before you compare" idea behind canonical-key dedup (3.13, 4.5); sorting
  datetimes is just key-based sorting (3.19) with a datetime key.
[↑ Back to top](#contents)

---

<a id="3.8"></a>
## 3.8 — "Date arithmetic — within last N days, durations" → `timedelta`

### The situation

You have a list of events, each with an aware-UTC timestamp (parsed via 3.7), and three
everyday questions:

```python
events = [
    {"id": "e1", "ts": datetime(2026, 6, 18, 11, 0, tzinfo=timezone.utc)},  # today
    {"id": "e2", "ts": datetime(2026, 6, 10, 9, 0,  tzinfo=timezone.utc)},  # 8 days ago
    {"id": "e3", "ts": datetime(2026, 1, 1, 0, 0,   tzinfo=timezone.utc)},  # months ago
]
```

1. **"Which events happened in the last 7 days?"** You instinctively reach for
   arithmetic on day-numbers and immediately get tangled: months have different lengths,
   the year boundary wraps, and subtracting `18 - 10 = 8` only works within one month.
2. **"How long did this job run?"** You have a start and end datetime and want a
   human-readable `"1h 26m"`.
3. **"What's the timestamp 90 days from now?"** Adding 90 to a day number overflows the
   month.

Doing any of this by hand with year/month/day integers is a swamp of edge cases. The
question is really about **durations** — spans of time — and Python has a dedicated type
for them.

### What's really going on

A `datetime` is a *point* in time; the gap between two points is a **duration**, and
Python represents it with **`timedelta`**. The key insight: **`datetime - datetime`
gives a `timedelta`**, and **`datetime ± timedelta` gives a `datetime`**. So all date
arithmetic reduces to:

- **"within the last N days"** → compute a *cutoff* = `now - timedelta(days=N)`, then
  keep events whose `ts >= cutoff`. No day-counting; subtraction handles months and
  years for you.
- **"how long"** → `end - start` is a `timedelta`; ask it for `.total_seconds()` and
  format.
- **"N days from now"** → `now + timedelta(days=N)`.

`timedelta` does all the calendar arithmetic correctly — leap years, month lengths,
year wraps — so you never touch raw day-numbers.

### The move

Reduce every date-arithmetic question to a `timedelta`: subtract two datetimes to get a
duration, add/subtract a `timedelta` to shift a datetime, and compare against a computed
cutoff for "within the last N".

- **"within the last N days"** → `now - timedelta(days=N)`, then keep `ts >= cutoff`.
- **"how long did it take"** → `end - start` (a `timedelta`), then `.total_seconds()`.
- **"N days from now"** → `now + timedelta(days=N)`.

### The code, every line explained

```python
from datetime import datetime, timezone, timedelta

now = datetime(2026, 6, 18, 12, 0, tzinfo=timezone.utc)   # pretend "now" (aware UTC)

# --- "within the last 7 days": compare against a cutoff ------------------
cutoff = now - timedelta(days=7)          # datetime - timedelta -> datetime
print(cutoff.isoformat())                 # 2026-06-11T12:00:00+00:00
recent = [e for e in events if e["ts"] >= cutoff]   # keep ts on/after the cutoff
# e1 (today) is in; e2 (8 days ago) is OUT; e3 (months ago) is OUT.
# BOTH sides must be aware (or both naive) — mixing raises TypeError (see 3.7).

# --- duration between two points: datetime - datetime -> timedelta -------
start = datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc)
end   = datetime(2026, 6, 18, 11, 26, tzinfo=timezone.utc)
elapsed = end - start                     # a timedelta of 1h 26m
print(elapsed)                            # 1:26:00
print(elapsed.total_seconds())            # 5160.0  <- ALWAYS use total_seconds() for the
                                          #    full span; do NOT use .seconds (see below)

# --- format a timedelta as "1h 26m" --------------------------------------
def human(td):                            # td: a timedelta
    secs = int(td.total_seconds())        # whole span in seconds (handles >1 day)
    h, rem = divmod(secs, 3600)           # divmod(a,b) -> (a//b, a%b): hours + remainder
    m, s = divmod(rem, 60)                # remainder -> minutes + seconds
    return f"{h}h {m}m {s}s"
print(human(elapsed))                     # "1h 26m 0s"

# --- future/past points -------------------------------------------------
deadline = now + timedelta(days=90)       # 90 days ahead — month/year wrap handled
yesterday = now - timedelta(days=1)
in_90_min = now + timedelta(minutes=90)   # timedelta takes weeks/days/hours/minutes/...

# --- the .days / .seconds TRAP -------------------------------------------
td = timedelta(hours=26, minutes=30)      # 1 day 2.5 hours
print(td.days, td.seconds)                # 1   9000   <- .seconds is the LEFTOVER within
                                          #    the day (2h30m=9000s), NOT the total!
print(td.total_seconds())                 # 95400.0   <- the actual total. Use THIS.
# Reading .seconds expecting the grand total is a very common, silent bug.

# --- compare durations directly ------------------------------------------
if elapsed > timedelta(hours=1):          # timedeltas compare like numbers
    print("job took over an hour")
```

### Why it works

`timedelta` stores a span normalised into days, seconds, and microseconds, and Python's
datetime arithmetic operators are overloaded so the calendar logic lives inside them.
Because subtracting two datetimes yields a `timedelta` and adding one back yields a
datetime, every "how far apart" or "shift by" question is one operator — and leap years
and month lengths are handled by the library, not your arithmetic. Filtering "last N
days" as `ts >= now - timedelta(days=N)` is robust precisely because it never reasons
about day-of-month; it compares absolute instants.

### Impact

- **Correctness:** month-length, year-wrap, and leap-year edge cases vanish — they're
  the library's problem, not yours.
- **Clarity:** `now - timedelta(days=7)` reads exactly as the intent, versus a tangle of
  modular day arithmetic.
- **Reliability:** comparing aware datetimes against a computed cutoff is the canonical,
  bug-resistant way to express recency windows.

### Pros & cons / when NOT to

**Reach for `timedelta` when:** computing recency windows, durations, deadlines,
time-to-live, or any "shift a time by an amount".

**Watch out / when NOT to:**
- **`.seconds` ≠ total seconds.** `.days`/`.seconds`/`.microseconds` are *components*;
  for the whole span always use `.total_seconds()`. This is the single most common
  `timedelta` bug.
- **`timedelta` has no "months" or "years"** — because they're variable-length. "One
  month later" is ambiguous; for true calendar offsets (add 1 month, end of month) use
  `dateutil.relativedelta` or `pandas` offsets, not `timedelta(days=30)`.
- **Both operands must match in awareness** (3.7) — subtracting a naive from an aware
  datetime raises `TypeError`. Normalise to aware-UTC first.
- **DST and "wall-clock" arithmetic:** adding `timedelta(days=1)` to an aware time in a
  DST-observing zone adds exactly 24 hours, which may land on a different wall-clock hour
  across a DST change. For "same time tomorrow" semantics, work in UTC or use a
  calendar-aware library.

### Where this shows up

- **Real work — recency filters:** "active users in the last 30 days", "errors in the
  last hour" — `ts >= now - timedelta(...)` is the workhorse, both in Python and as the
  equivalent SQL/pandas filter.
- **Real work — job timing & SLAs:** measuring stage durations for logs/metrics
  (`human(end - start)`), and enforcing timeouts/deadlines (5.8).
- **Real work — TTL/cache expiry & retries:** "retry after 5 minutes", "token expires in
  1 hour" — durations added to a base time (ties to backoff, 5.9).
- **Pattern mapping (secondary):** "events within a moving time window" is the
  time-based **sliding window** (Area 11) — keep items whose timestamp is within
  `[now - window, now]`, a direct cousin of fixed-size window problems.
[↑ Back to top](#contents)

---

<a id="3.9"></a>
## 3.9 — "Text encoding/decoding errors (UTF-8/BOM)" → encoding handling

### The situation

You open a CSV that a colleague exported from Excel and read it the obvious way:

```python
text = open("export.csv").read()
```

and get a crash:

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 14: invalid continuation byte
```

Or it *doesn't* crash, but the first column header comes out as `"﻿sensor_id"`
instead of `"sensor_id"` — so `row["sensor_id"]` raises `KeyError` even though the column
is clearly there. Or accented names like `café` and `Köln` appear as `cafÃ©` and `KÃ¶ln`
(mojibake — text decoded with the wrong encoding). All three are the *same underlying
problem* wearing different masks.

"Handling encoding" concretely means: read the bytes with the **correct character
encoding** so `0xe9` becomes `é`, strip the invisible **BOM** so the first header is
clean, and decide what to do with genuinely undecodable bytes instead of crashing.

### What's really going on

Files on disk are **bytes**, not text. To turn bytes into characters you need to know
the **encoding** — the rulebook mapping byte sequences to characters. **UTF-8** is the
modern default and handles every character, but plenty of real files are in other
encodings:

- **`latin-1` / `cp1252`** (Windows-1252) — common in older European exports; the byte
  `0xe9` *is* `é` in latin-1 but is *invalid* in UTF-8, hence the crash.
- A **BOM** ("Byte Order Mark") is an invisible marker (`﻿`, bytes `EF BB BF` in
  UTF-8) that some Windows tools — notably Excel — prepend to files. When you read with
  plain `utf-8`, the BOM survives and glues itself to your first field.

So the crash, the `﻿` header, and the mojibake are all "decoded with the wrong
encoding (or didn't strip the BOM)". The fixes: specify the right `encoding=`, use
**`utf-8-sig`** to auto-strip a UTF-8 BOM, and use an **`errors=`** policy for bytes you
can't otherwise salvage.

### The move

Always pass an explicit `encoding=` to `open`, use **`utf-8-sig`** to auto-strip a BOM
from Excel-origin files, and choose an **`errors=`** policy for undecodable bytes:

```python
text = open("export.csv", encoding="utf-8-sig").read()   # strips a BOM if present
# wrong-encoding crash? name the real one:  encoding="cp1252"
# can't avoid bad bytes?  errors="replace"  (survive, mark the damage)
```

### The code, every line explained

```python
# --- ALWAYS specify encoding explicitly (never rely on the OS default) ---
text = open("export.csv", encoding="utf-8").read()
# The default encoding is platform-dependent (utf-8 on Linux/mac, often cp1252 on
# Windows) -> code that "works on my machine" breaks elsewhere. Be explicit.

# --- BOM: use utf-8-sig to swallow the Excel byte-order mark -------------
text = open("export.csv", encoding="utf-8-sig").read()
# "utf-8-sig" decodes UTF-8 AND strips a leading BOM if present. Now the first
# header is "sensor_id", not "﻿sensor_id" -> row["sensor_id"] works.
# It's safe even when there is NO BOM, so it's a good default for Excel-origin files.

# --- Wrong-encoding crash: name the actual encoding ----------------------
# If 0xe9 is really latin-1 'é', decode as latin-1 (or cp1252 for curly quotes etc.):
text = open("legacy.csv", encoding="cp1252").read()    # Windows-1252 European export
# cp1252 is a superset of latin-1 covering smart quotes, em-dashes, the € sign.

# --- errors=: what to do with bytes you can't decode ---------------------
# "strict" (default): raise on the first bad byte.
# "replace": substitute each bad byte with the U+FFFD replacement char (...): never
#   crashes, but you LOSE information — you can see WHERE it broke.
text = open("messy.csv", encoding="utf-8", errors="replace").read()
# "ignore": silently drop bad bytes (dangerous — hides data loss). Avoid unless sure.
# "backslashreplace": keep bad bytes as \xNN escapes (good for debugging what's there).

# --- Detect the encoding when you genuinely don't know -------------------
import chardet                          # third-party: pip install chardet
raw = open("unknown.csv", "rb").read()  # read RAW BYTES ("rb"), no decoding
guess = chardet.detect(raw)             # -> {"encoding": "ISO-8859-1", "confidence": 0.73}
text = raw.decode(guess["encoding"])    # decode with the detected encoding
# Detection is a GUESS (probabilistic). Prefer asking the source for the true encoding;
# use detection only as a fallback, and log what it picked.

# --- WRITING: be explicit on the way out too -----------------------------
with open("out.csv", "w", encoding="utf-8", newline="") as f:   # newline="" for csv (3.1)
    f.write(text)
# Write utf-8 (no BOM) for interoperability; write utf-8-sig ONLY if a downstream
# Windows tool (Excel) specifically needs the BOM to display non-ASCII correctly.

# --- bytes <-> str directly (the layer underneath open()) ---------------
b = "café".encode("utf-8")              # str -> bytes:  b'caf\xc3\xa9'
s = b.decode("utf-8")                   # bytes -> str:  "café"
# "encode" = text to bytes (going to disk/network); "decode" = bytes to text (coming in).
```

### Why it works

Specifying `encoding=` tells Python the exact rulebook to turn bytes into characters, so
`0xe9` is interpreted correctly instead of choking the UTF-8 decoder. `utf-8-sig`
recognises and consumes the BOM bytes, so the invisible marker never leaks into your
first field. `errors="replace"` swaps the strict "raise on bad byte" policy for a
lossy-but-survivable one, letting a mostly-good file through while marking the damaged
spots. And reading in binary (`"rb"`) plus `chardet` gives you a fallback when the source
won't tell you the encoding.

### Impact

- **Robustness:** the `UnicodeDecodeError` crash and the `﻿`-glued-header `KeyError`
  both disappear — two of the most common "works locally, breaks in prod / on this one
  file" failures.
- **Correctness:** accented and non-Latin text round-trips intact instead of becoming
  mojibake, which matters for names, addresses, and any non-English corpus.
- **Portability:** explicit encodings make the code behave identically on Windows, mac,
  and Linux, killing the platform-default surprise.

### Pros & cons / when NOT to

**Reach for explicit encoding handling when:** reading *any* text file you didn't create
this minute — exports, third-party data, scraped content, user uploads.

**Watch out / when NOT to:**
- **`errors="ignore"` silently destroys data.** Prefer `"replace"` (you can see the
  damage) or fix the encoding. Never `ignore` on data you must keep faithfully.
- **`latin-1` "never fails"** — it maps all 256 byte values to characters — so decoding
  garbage as latin-1 *appears* to work while producing nonsense. Don't use it as a lazy
  "make the error go away" fix; use the *correct* encoding.
- **Detection is probabilistic**, not authoritative. `chardet` can be confidently wrong
  on short files. Treat its output as a hint and log it.
- **Don't write a BOM by default.** `utf-8-sig` *output* adds a BOM that can break
  non-Windows parsers (and shell tools). Write plain `utf-8` unless a specific consumer
  demands the BOM.

### Where this shows up

- **Real work — ingesting third-party/Excel CSVs:** the `utf-8-sig` + explicit-encoding
  combo is the standard first line of defence on any "spreadsheet someone emailed me".
- **Real work — multilingual NLP corpora:** decoding text data correctly so non-English
  characters survive into tokenisation (garbage-in here silently degrades a model).
- **Real work — log/scrape ingestion:** web-scraped or legacy-system text often isn't
  UTF-8; detecting/specifying encoding prevents corrupt records entering the pipeline.
- **Pattern mapping (secondary):** no algorithm analogue; it's the bytes-vs-text boundary
  discipline — the same "decode at the edge into a clean canonical form (UTF-8 str)" idea
  that mirrors parsing-at-the-boundary (3.1, 7.1) and feeds text normalisation (4.1).
[↑ Back to top](#contents)

---

<a id="3.10"></a>
## 3.10 — "Processing a directory of files robustly" → pathlib & glob

### The situation

You have a data folder and want to process every JSON file in it, including ones in
subfolders:

```
data/
  2026-01/
    events_a.json
    events_b.json
  2026-02/
    events_c.json
  notes.txt          # NOT json — must be skipped
```

You write it with old-style string paths and `os`:

```python
import os
folder = "data"
for name in os.listdir(folder):                 # only the TOP level, not subfolders
    path = folder + "/" + name                  # manual string concatenation (fragile)
    if name.endswith(".json"):
        process(open(path).read())
```

Three problems. `os.listdir` is **not recursive**, so the files in `2026-01/` are
missed. The `folder + "/" + name` string-glue breaks on Windows (which uses `\`), and
doubles up slashes if `folder` already ends in `/`. And manually filtering `.json`,
stripping extensions to derive output names, and creating output folders all become
fiddly string surgery. "Process a directory robustly" concretely means: find the right
files (recursively, by pattern), build output paths safely and cross-platform, and skip
the non-matching ones — without string hacking.

### What's really going on

A filesystem path is a *structured thing* — a sequence of directory names plus a
filename with a stem and a suffix — but the old `os.path` API treats it as a raw string
you slice and concatenate by hand. That's where the bugs live: separators, extensions,
recursion.

**`pathlib`** (standard library) models a path as a **`Path` object** with methods and
operators that understand structure: `/` to join (correctly, per-OS), `.glob`/`.rglob`
to find files by pattern (recursively), `.stem`/`.suffix`/`.name` to decompose, and
`.read_text`/`.mkdir` for I/O. **Glob** is the wildcard pattern language for matching
filenames: `*` matches any run of characters within one path segment, `**` matches
across nested directories.

### The move

Use a **`Path`** object and its structure-aware methods instead of string paths: `/` to
join, `.rglob`/`.glob` to find files by pattern, `.stem`/`.suffix` to decompose, and
`.read_text`/`.mkdir` for I/O:

```python
from pathlib import Path
for path in Path("data").rglob("*.json"):   # recursive, pattern-matched
    process(path.read_text(encoding="utf-8"))
```

### The code, every line explained

```python
from pathlib import Path

root = Path("data")                       # a Path object, not a string

# --- find files by pattern, RECURSIVELY ----------------------------------
for path in root.rglob("*.json"):         # rglob = recursive glob: every *.json at ANY depth
    #                    └ "*" = any chars in a name; rglob descends into subfolders
    process(path.read_text(encoding="utf-8"))   # Path.read_text: open+read+close in one
# rglob("*.json") finds events_a/b/c.json across 2026-01/ and 2026-02/, skips notes.txt.
# Non-recursive variants:
#   root.glob("*.json")       -> only the top level
#   root.glob("2026-*/*.json")-> one level down, folders starting "2026-"
#   root.glob("**/*.json")    -> same as rglob (** spans directories)

# --- joining paths: the / operator (cross-platform, no string glue) ------
out_dir = root / "processed"              # Path("data/processed") — correct separator
nested  = root / "2026-01" / "events_a.json"   # chain as many segments as you like
# Never do folder + "/" + name again. / handles separators and avoids double slashes.

# --- decompose a path: name, stem, suffix, parent ------------------------
p = Path("data/2026-01/events_a.json")
print(p.name)     # "events_a.json"   (filename with extension)
print(p.stem)     # "events_a"        (filename WITHOUT the extension)
print(p.suffix)   # ".json"           (the extension, including the dot)
print(p.parent)   # Path("data/2026-01")   (the containing directory)
# Derive an output name cleanly: same stem, new extension, new folder:
out_path = out_dir / f"{p.stem}.parquet"  # data/processed/events_a.parquet

# --- create output dirs safely (no crash if they exist) ------------------
out_dir.mkdir(parents=True, exist_ok=True)   # parents=True: make intermediate dirs too;
                                             # exist_ok=True: don't raise if already there

# --- existence / type checks, the robust way -----------------------------
if p.exists() and p.is_file():            # guard before reading (or just EAFP, 1.10)
    ...
for d in root.iterdir():                  # iterate immediate children (files AND dirs)
    if d.is_dir():
        print("subfolder:", d.name)

# --- process MANY matched files, skipping bad ones (partial-failure) -----
results = []
for path in sorted(root.rglob("*.json")):  # sorted() -> deterministic, reproducible order
    try:
        results.append(process(path.read_text(encoding="utf-8")))
    except Exception as e:                 # one bad file shouldn't kill the batch (7.9)
        print(f"skipping {path}: {e}")
# sorted() matters: rglob's order is filesystem-dependent; sort for reproducible runs.
```

### Why it works

`Path` knows a path's structure, so the operations that were error-prone string surgery
become safe method calls: `/` inserts the correct separator for the OS, `.glob`/`.rglob`
walk the tree and filter by pattern in one call, and `.stem`/`.suffix` decompose without
guessing where the dot is. `rglob`/`glob` return **lazy generators** (1.2), so iterating
a directory with a million files doesn't build a giant list. Wrapping the per-file body
in `try/except` turns "one corrupt file" into "skip and log", not "lose the whole run".

### Impact

- **Correctness & portability:** no separator/extension string bugs; identical behaviour
  on Windows, macOS, Linux.
- **Less code:** `read_text`, `mkdir(parents=True, exist_ok=True)`, and `/` replace
  multi-line `os.path` incantations.
- **Robustness at scale:** recursive globbing finds everything; `sorted` makes runs
  reproducible; per-file `try/except` makes a directory job survive bad files.

### Pros & cons / when NOT to

**Reach for `pathlib` when:** you touch the filesystem at all — listing, finding,
joining, reading, writing paths. It's the modern default; prefer it over `os.path`.

**Watch out / when NOT to:**
- **`rglob("*")` on a huge tree can be slow** and may follow into directories you didn't
  intend. Narrow the pattern (`rglob("*.json")`) and consider `os.scandir`/`os.walk` for
  performance-critical massive trees.
- **Glob order is not guaranteed** — it's filesystem-dependent. If processing order
  matters (or for reproducibility), wrap in `sorted(...)`.
- **Some third-party APIs still want strings.** Most modern libraries accept `Path`, but
  if one doesn't, pass `str(path)`.
- **Globs don't recurse into hidden/permission-denied dirs gracefully** — a
  `PermissionError` mid-walk can abort iteration; wrap in `try/except` if traversing
  untrusted trees.

### Where this shows up

- **Real work — dataset & shard ingestion:** `root.rglob("*.parquet")` to gather every
  shard of a partitioned dataset, then stream them (ties to `chain`, 1.12, and 3.2).
- **Real work — batch file processing:** converting a folder of raw files to a processed
  format, deriving each output name from the input `.stem` (an everyday ETL loop).
- **Real work — checkpoint/artefact management:** finding the latest model checkpoint
  (`max(dir.glob("model_*.pt"), key=...)`) or cleaning old runs.
- **Pattern mapping (secondary):** `rglob`/`os.walk` is a **tree/graph traversal** of the
  directory tree (Area 11) — visiting every node (file) reachable from a root, the same
  DFS shape as walking nested data (3.3).
[↑ Back to top](#contents)

---

<a id="3.11"></a>
## 3.11 — "Pick the right on-disk format" → CSV/JSON/JSONL/Parquet/pickle trade-offs

### The situation

You have a cleaned dataset — 50 million rows, 30 columns, mostly numeric — and you need
to save it so a training job can reload it tomorrow. You default to CSV because it's
familiar:

```python
df.to_csv("dataset.csv")        # 18 GB on disk; reload takes 4 minutes
```

Then you notice the pain: the file is **18 GB**, reloading takes minutes, every numeric
column comes back as a *string* you must re-coerce (3.4), and when you only need 3 of
the 30 columns you *still* read all 18 GB. Meanwhile a colleague saved the same data as
**Parquet**: 1.5 GB, loads in seconds, types preserved, and reading 3 columns touches
only those 3. The question "what format should I save this in?" has a real,
consequential answer that depends on *what the data is* and *how it'll be used*.

### What's really going on

There is no single best format — each trades off along the same axes, and the right
choice depends on your access pattern:

- **Human-readable vs binary** — can you `cat` it and diff it, or is it opaque bytes?
- **Typed vs untyped** — does the format remember that a column is `int64`, or is
  everything text you must re-parse?
- **Row-oriented vs columnar** — is it laid out row-by-row (good for "read whole
  records, append rows") or column-by-column (good for "scan a few columns of many
  rows", and compresses far better because like values sit together)?
- **Streamable vs whole-file** — can you process it record-by-record without loading it
  all (3.2), or must you read the entire thing?
- **Portable vs Python-only / unsafe** — can any tool/language read it, or only Python
  (and is loading it a security risk)?

The realisation: **CSV is a lowest-common-denominator interchange format, not a storage
format for large typed tabular data.** For that, columnar **Parquet** usually wins
decisively.

### The move

Match the format to the access pattern rather than defaulting to CSV:

- small / human-readable / cross-tool → **CSV** (or **JSON** if nested);
- large records, streamed, possibly nested → **JSONL** (3.2);
- large tabular data at rest, analytical reads → **Parquet** (usually the answer);
- a trusted, short-lived Python object → **pickle** (never for untrusted input).

### The code, every line explained

```python
# --- CSV: text, untyped, row-oriented, universal -------------------------
df.to_csv("d.csv", index=False)          # everyone can read it; great for small/interchange
# + human-readable, diffable, opens in Excel, any language reads it.
# - large & slow; NO types (all strings on reload -> re-coerce, 3.4); no column pruning.
# USE FOR: small data, handoffs to non-Python tools, anything a human must eyeball.

# --- JSON: text, typed-ish, nested, whole-file ---------------------------
import json; json.dump(record, open("r.json", "w"))
# + represents NESTED/ragged structures (CSV can't); human-readable; universal.
# - whole document must be parsed at once (no streaming); verbose/large for tabular data.
# USE FOR: config, single nested objects, API payloads — NOT big tabular datasets.

# --- JSONL: text, nested, ROW-STREAMABLE (see 3.2) -----------------------
# one JSON object per line -> stream millions of records with O(1) memory.
# + streamable, append-friendly, handles nested records, line-by-line resilient.
# - still text (bigger than binary), no column pruning, parsing cost per line.
# USE FOR: large record/event/ML-corpus data processed sequentially.

# --- Parquet: BINARY, typed, COLUMNAR, compressed ------------------------
df.to_parquet("d.parquet")               # needs pyarrow (or fastparquet) installed
just3 = pd.read_parquet("d.parquet", columns=["a", "b", "c"])  # reads ONLY those columns
# + small (columnar compression), fast, PRESERVES dtypes, column & row-group pruning,
#   read by pandas/Spark/DuckDB/Polars/many languages.
# - binary (not human-readable/diffable); needs a library; poor for tiny/nested-irregular.
# USE FOR: the DEFAULT for large analytical/ML tabular data at rest. Usually the answer.

# --- pickle: BINARY, Python-only, arbitrary objects ----------------------
import pickle; pickle.dump(any_python_object, open("o.pkl", "wb"))
# + saves ANY Python object exactly (models, custom classes, nested dicts); fast.
# - PYTHON-ONLY; version-fragile (may not reload across library versions);
#   *** SECURITY: unpickling untrusted data can execute arbitrary code. NEVER load a
#       pickle you didn't create. ***
# USE FOR: short-lived caches/checkpoints of Python objects you trust. Not interchange,
#   not long-term archival, not anything received from outside.
```

### Why it works

Matching the format to the access pattern eliminates wasted work. Columnar Parquet
stores each column contiguously, so (a) similar values compress dramatically and (b)
reading 3 of 30 columns skips the other 27 entirely — the two reasons it crushes CSV on
size and speed for analytical reads. Text formats (CSV/JSON/JSONL) win when a *human* or
a *foreign tool* must read the file, and JSONL adds streamability. pickle wins only when
you must round-trip an arbitrary *Python object* and you fully trust the source.

### Impact

- **Size & speed:** switching large typed tabular data from CSV to Parquet routinely
  gives ~10× smaller files and far faster loads — directly cutting storage cost and job
  time.
- **Correctness:** Parquet preserving dtypes removes the entire re-coercion step (3.4)
  and the "my ints came back as strings" class of bug.
- **Safety:** knowing pickle's code-execution risk prevents a serious security hole when
  handling files from elsewhere.

### Pros & cons / when NOT to

**Quick decision guide:**
- **Small, must be human-readable / cross-tool** → **CSV** (or JSON if nested).
- **Large records, streamed/appended, possibly nested** → **JSONL** (3.2).
- **Large tabular data at rest, analytical reads** → **Parquet** (the usual default).
- **A Python object you trust, short-lived** → **pickle** (never for untrusted input).
- **Config / single nested document** → **JSON / YAML**.

**Watch out / when NOT to:**
- **Don't archive in pickle.** It's fragile across versions and unsafe to load from
  others — use Parquet/JSONL for anything kept or shared.
- **Parquet needs a library** (`pyarrow`) and isn't human-readable — for a 200-row config
  it's overkill; CSV/JSON is simpler.
- **CSV at scale is a trap** — its familiarity hides real cost; reach for it only when
  interchange/readability is the actual requirement.

### Where this shows up

- **Real work — feature stores / training data:** cleaned datasets persisted as Parquet
  so training and analysis reload fast with correct types and column pruning.
- **Real work — ML corpora & event logs:** JSONL for large, streamable, possibly-nested
  record collections (the de-facto LLM dataset format).
- **Real work — model/checkpoint caching:** pickle (or framework-specific formats) for
  trusted, short-lived Python objects — with the security caveat front of mind (8.9).
- **Pattern mapping (secondary):** no algorithm analogue; it's the "choose the data
  structure for the access pattern" principle (2.9) applied to *disk* — columnar vs row,
  streamable vs whole-file — the storage-layer version of picking the right container.
[↑ Back to top](#contents)

---

<a id="3.12"></a>
## 3.12 — "Sanity-check a dataset before trusting it" → null counts, ranges, balance

### The situation

A fresh dataset lands and you pipe it straight into training. The model trains, scores
98% accuracy, and you ship it — then it fails in production. Digging in, you find what
you'd have caught in 60 seconds of *looking* at the data first:

```
rows:        100,000
age column:  31% are NULL; min = -3; max = 9999   # impossible values
label:       99.2% class "no", 0.8% class "yes"   # wildly imbalanced
country:     one value "DE" for 99,998 of 100,000 rows  # near-constant column
signup_date: 4,000 rows dated in the year 1970     # epoch-zero parse failures
```

The 98% "accuracy" was the model learning to always predict "no". The `age` of `9999`
is a sentinel someone used for "unknown". The 1970 dates are failed timestamp parses.
*None of this is visible* unless you deliberately profile the data. "Sanity-check"
concretely means computing, per column: **how many are missing**, the **range/extremes**
of numeric columns, the **distribution/balance** of categorical and label columns, and
the **count of duplicates** — then eyeballing those numbers against what you *expect*.

### What's really going on

This is **exploratory data validation** — the discipline of *interrogating* a dataset
before trusting it, distinct from per-record schema validation (3.6). Schema validation
asks "is each row well-formed?"; sanity-checking asks "is the dataset as a *whole*
sane?" — questions only visible in aggregate: a column that's 31% null, a label that's
99% one class, a "constant" feature that carries no information, a numeric range that
includes impossible values.

The move is to compute a small battery of aggregate statistics and *compare them to your
expectations*. The numbers themselves are easy; the value is in the habit of looking
**before** you train, because every one of these issues silently produces a model that
looks fine and behaves wrong.

### The move

Before trusting a dataset, compute a small battery of aggregate checks and compare them
against your expectations: **null counts/fractions** per column, **min/max** of numerics,
**value distribution** of categoricals/labels, and **duplicate counts** — via pandas
(`isna`, `describe`, `value_counts`, `duplicated`) or streaming `Counter`s.

### The code, every line explained

```python
import pandas as pd
df = pd.read_parquet("dataset.parquet")   # or read_csv, etc.

# --- shape & a first eyeball ---------------------------------------------
print(df.shape)                # (rows, columns) — does the row count match expectations?
print(df.head())               # look at actual values — the cheapest, most underrated check
print(df.dtypes)               # did numeric columns load as numbers, or as 'object' (text)?

# --- MISSINGNESS: count and fraction of nulls per column -----------------
print(df.isna().sum())                 # absolute null count per column
print((df.isna().mean() * 100).round(1))   # PERCENT null per column (mean of a 0/1 mask)
# A column that's 31% null needs a decision (impute/drop, 3.5/3.23) BEFORE training.

# --- NUMERIC RANGES: catch impossible / sentinel values ------------------
print(df.describe())                   # count, mean, std, min, 25/50/75%, max per numeric col
# Read min/max against reality: age min=-3 or max=9999 are impossible -> bad data or a
# sentinel (someone coded "unknown" as 9999). describe() surfaces both instantly.
suspicious = df[(df["age"] < 0) | (df["age"] > 120)]   # isolate the offending rows to inspect
print(len(suspicious))

# --- BALANCE: distribution of categorical & label columns ----------------
print(df["label"].value_counts())              # raw counts per class
print(df["label"].value_counts(normalize=True))# FRACTIONS -> 0.992 "no", 0.008 "yes"
# A 99/1 split means "accuracy" is meaningless (predict majority -> 99%); you need
# class weighting / resampling and a metric like F1/AUC (ties to imbalance, 8.4/8.5).
print(df["country"].nunique())                 # 1 unique value -> a CONSTANT column:
# constant (or near-constant) features carry no signal — flag for removal.

# --- DUPLICATES: exact and key-based -------------------------------------
print(df.duplicated().sum())                   # fully-duplicate rows
print(df.duplicated(subset=["user_id"]).sum()) # rows sharing a key that should be unique
# Unexpected duplicates inflate counts and cause train/test leakage (8.1) if a row
# appears in both splits.

# --- pure-Python version (no pandas), streaming over records -------------
from collections import Counter
nulls, label_counts, n = Counter(), Counter(), 0
amin, amax = float("inf"), float("-inf")
for rec in read_jsonl("data.jsonl"):           # the streaming reader from 3.2
    n += 1
    for k, v in rec.items():
        if v is None or v == "":
            nulls[k] += 1                       # tally missing per field
    label_counts[rec.get("label")] += 1         # tally label distribution (Counter, 3.14)
    age = rec.get("age")
    if isinstance(age, (int, float)):
        amin, amax = min(amin, age), max(amax, age)  # running range, O(1) memory
print(n, dict(nulls), label_counts.most_common(), amin, amax)
```

> Note: the pandas examples above are written idiomatically but were **not executed**
> (pandas is not installed in this environment). The method names and semantics
> (`isna`, `describe`, `value_counts(normalize=True)`, `duplicated`) are standard pandas.

### Why it works

Every defect that ruins a model in production has an *aggregate signature*: missingness
shows up as a high null fraction, sentinels and parse failures show up as impossible
min/max, useless features show up as `nunique() == 1`, and imbalance shows up in
`value_counts(normalize=True)`. Computing this handful of summaries surfaces all of them
in one pass, *before* they're laundered through training into a misleadingly good score.
The check is cheap; the bug it prevents is expensive and invisible later.

### Impact

- **Catches silent killers early:** label imbalance, leakage-via-duplicates, sentinel
  values, and dead columns are found in seconds instead of after a failed deployment.
- **Right metric, right preprocessing:** seeing a 99/1 split tells you accuracy is the
  wrong metric and that you need weighting/resampling — *before* you waste a training run.
- **Builds trust deliberately:** "I looked at the nulls, ranges, and balance" replaces
  "the model trained, so the data must be fine" — the assumption that bites hardest.

### Pros & cons / when NOT to

**Reach for this when:** *any* new or refreshed dataset enters your pipeline — make it a
required first step, not an optional one.

**Watch out / when NOT to:**
- **Summary stats hide multimodality and outliers.** A sane-looking mean can mask a
  bimodal distribution or a few extreme outliers — back up `describe()` with a histogram
  / quantiles for important columns.
- **`describe()` ignores non-numeric columns** by default — check categorical columns
  separately with `value_counts` / `nunique`.
- **On huge data, profile a sample** (`df.sample(100_000)`) or compute streaming
  aggregates (the pure-Python version) rather than loading everything — but be aware a
  sample can miss rare-but-important issues.
- **Tooling exists:** `pandas.DataFrame.describe`, `ydata-profiling` (auto full report),
  or Great Expectations (codified, automated data-quality assertions in a pipeline) scale
  this up — graduate to them once the manual checks become routine.

### Where this shows up

- **Real work — pre-training data audit:** the mandatory "look before you train" step;
  catching imbalance, leakage, and bad values that would otherwise produce a deceptively
  good offline score (8.1, 8.4, 8.5).
- **Real work — pipeline data-quality gates:** automated null/range/balance assertions
  that fail a daily ETL run when the incoming data drifts out of expected bounds (7.x).
- **Real work — drift monitoring:** comparing today's distribution against the training
  distribution to detect train/serve skew (8.16).
- **Pattern mapping (secondary):** these are single-pass aggregate scans — counts, min/
  max, frequency tables — the same running-aggregate pattern as `Counter` (3.14) and the
  one-pass statistics computed over streams.
[↑ Back to top](#contents)

---

<a id="3.13"></a>
## 3.13 — "Have I seen this before / dedup" → set membership

### The situation

You're streaming events and must process each unique `user_id` only once (e.g. send one
welcome email per user). You track who you've seen in a list:

```python
seen = []                                  # users processed so far
for event in events:                       # say 5,000,000 events
    uid = event["user_id"]
    if uid not in seen:                    # have we processed this user?
        process(uid)
        seen.append(uid)
```

On a small test it's instant. On the real 5-million-event stream it **slows to a crawl**
and seems to hang. The logic is correct — the *data structure* is wrong. `uid not in
seen` scans the **entire list** every time, comparing against every element, so with n
events and many uniques you do roughly n²/2 comparisons: 5 million events becomes
trillions of comparisons. The fix is not cleverer code — it's storing `seen` in a
structure where "have I seen this?" is instant.

### What's really going on

`x in some_list` is an **O(n)** operation: Python walks the list element by element
until it finds `x` or reaches the end. Inside a loop over n items, that's **O(n²)** — the
accidental-quadratic smell (2.2). The operation you actually want — *membership testing*,
"is this element present?" — is exactly what a **`set`** is built for.

A **set** is an unordered collection of **unique** elements backed by a **hash table**:
it computes a hash of each element to jump more or less directly to where it would be
stored, so `x in some_set` is **O(1)** on average — constant time, independent of how
many elements are already in it. Membership in a set of 5 million is as fast as
membership in a set of 5. (This is the same O(1)-structure choice covered generally in
2.9; here it's applied to dedup.)

### The move

Store "what I've seen" in a **`set`**, not a list, so the membership test is O(1):

```python
seen = set()
for x in items:
    if x not in seen:        # O(1) hash lookup, not an O(n) scan
        seen.add(x)
        process(x)
```

### The code, every line explained

```python
# --- "have I seen this?" — use a SET, not a list -------------------------
seen = set()                               # empty set: O(1) membership + uniqueness
for event in events:
    uid = event["user_id"]
    if uid not in seen:                    # O(1) average lookup (hash), not O(n) scan
        process(uid)
        seen.add(uid)                      # .add (not .append); duplicates are ignored
# n events -> O(n) total instead of O(n²). The hang disappears.

# --- dedup a whole list, ORDER NOT important -----------------------------
unique = set(all_ids)                      # build a set in one pass -> duplicates collapse
# or as a list: unique = list(set(all_ids))   (order is arbitrary)

# --- dedup a whole list, PRESERVING first-seen order ---------------------
seen, ordered = set(), []
for x in all_ids:
    if x not in seen:                      # set for the fast check...
        seen.add(x)
        ordered.append(x)                  # ...list to remember the order
# Shortcut for HASHABLE items, Python 3.7+: dict keys keep insertion order & are unique:
ordered = list(dict.fromkeys(all_ids))     # same result, one line

# --- set operations: compare two collections fast ------------------------
a = {"u1", "u2", "u3"}; b = {"u2", "u3", "u4"}
print(a & b)        # intersection: {"u2","u3"}  — ids in BOTH (e.g. in train AND test!)
print(a | b)        # union:        all unique ids across both
print(a - b)        # difference:   {"u1"}       — in a but not b
print(a ^ b)        # symmetric diff: in exactly one of the two
# These are O(len) and replace nested-loop comparisons between two lists.

# --- the hashable requirement -------------------------------------------
# Set elements must be HASHABLE (immutable): str, int, tuple OK; list/dict are NOT.
# seen.add(["a", "b"])     # TypeError: unhashable type: 'list'
seen.add(("a", "b"))       # use a TUPLE for a composite key (ties to 3.18)
# To dedup whole records (dicts), hash a canonical key instead — see below.

# --- dedup complex records by a canonical key ----------------------------
seen = set()
for rec in records:                        # rec is a dict (unhashable)
    key = (rec["user_id"], rec["date"])    # build a hashable key from the fields you
    if key not in seen:                    #   consider "the same" (your dedup rule)
        seen.add(key)
        keep(rec)
# The key defines identity; normalise it first (lowercase, strip) for fuzzy dedup (4.5).
```

### Why it works

A set stores elements in a hash table: to test membership it hashes the element and
looks in the corresponding slot, so it doesn't scan — it jumps. That makes `in` average
**O(1)** regardless of size, turning the O(n²) loop into O(n). Sets also *enforce*
uniqueness (adding a duplicate is a no-op), so they double as the dedup container itself.
The set algebra operators (`&`, `|`, `-`, `^`) implement collection comparisons in one
fast call instead of nested loops.

### Impact

- **Speed:** O(n²) → O(n). The difference between a job that hangs on 5 million items and
  one that finishes in a second — often the single biggest speed-up in data code.
- **Clarity:** `if uid not in seen` with a set states intent ("is this new?") while being
  fast; intent and performance align.
- **Correctness:** built-in uniqueness removes the manual "did I already add this?"
  bookkeeping.

### Pros & cons / when NOT to

**Reach for a set when:** you need fast membership tests, deduplication, or
collection-vs-collection comparisons (overlap, difference).

**Watch out / when NOT to:**
- **Elements must be hashable** (immutable). Lists and dicts can't go in a set; use a
  tuple of their fields (3.18) or hash a canonical string (4.4).
- **Sets are unordered.** If you need to preserve order while deduping, pair a set with a
  list, or use `dict.fromkeys` (above).
- **Memory cost:** a set of 5 million ids holds all of them — fine usually, but on a
  truly unbounded stream where you only need *approximate* dedup, a probabilistic
  structure (Bloom filter) trades a tiny error rate for far less memory.
- **Tiny collections:** for a handful of items, a list scan is fine and a set is
  needless ceremony — the win is at scale.

### Where this shows up

- **Real work — dedup before training:** removing duplicate rows/documents so the same
  example doesn't appear in both train and test (a direct cause of leakage, 8.1).
- **Real work — "process once" / idempotency:** a set (or persistent dedup store) of
  already-handled ids so re-running a job doesn't reprocess or double-charge (7.4, 7.5).
- **Real work — overlap checks:** `set(train_ids) & set(test_ids)` to *prove* there's no
  leakage between splits — one of the most valuable one-liners in ML hygiene.
- **Pattern mapping (secondary):** "seen set" is the core of countless algorithm
  problems — cycle detection, visited-tracking in BFS/DFS graph traversal (Area 11), and
  the hashing half of two-sum-style "have I seen the complement?" patterns (11.1).
[↑ Back to top](#contents)

---

<a id="3.14"></a>
## 3.14 — "How many of each" → `Counter`

### The situation

You want the distribution of class labels in a dataset to check for imbalance (3.12):

```python
labels = ["cat", "dog", "cat", "bird", "cat", "dog"]
```

You write the count-by-hand idiom you've written a hundred times:

```python
counts = {}                                # empty dict of label -> count
for label in labels:
    if label in counts:                    # already seen this label?
        counts[label] += 1                 # bump it
    else:
        counts[label] = 1                  # first time: initialise to 1
# counts == {"cat": 3, "dog": 2, "bird": 1}
```

It works, but it's four lines of bookkeeping for a one-line idea, and the
`if/else`-to-initialise pattern is easy to fumble (forget the `else` and you get a
`KeyError` on the first occurrence). Then the follow-up questions pile on: *what are the
two most common labels?* *how many distinct labels?* — each needing more code.

### What's really going on

You're computing a **frequency count** — "how many times does each distinct value
appear?" — one of the most common operations in data work. The standard library has a
purpose-built tool: **`collections.Counter`**, a `dict` subclass specialised for
counting. It removes the initialise-or-increment dance entirely (a missing key counts as
0, not a `KeyError`) and adds frequency-specific methods like `most_common`.

The deeper point mirrors 3.13: you're choosing the *right structure for the job*. A
`Counter` *is* a dict (so all dict operations work), but its constructor counts an
iterable for you and its `most_common` answers the top-N question directly.

### The move

Use **`collections.Counter`** — feed it the iterable and it tallies in one call, with a
missing key counting as 0 and `most_common(n)` for the top values:

```python
from collections import Counter
counts = Counter(labels)             # {"cat": 3, "dog": 2, "bird": 1}
counts.most_common(2)                # [("cat", 3), ("dog", 2)]
```

### The code, every line explained

```python
from collections import Counter

labels = ["cat", "dog", "cat", "bird", "cat", "dog"]

# --- count an iterable in ONE call ---------------------------------------
counts = Counter(labels)               # Counter({"cat": 3, "dog": 2, "bird": 1})
# The constructor walks the iterable and tallies — no loop, no if/else.

# --- a missing key counts as 0, not a KeyError ---------------------------
print(counts["cat"])                   # 3
print(counts["fish"])                  # 0  <- absent key returns 0 (does NOT raise)
# This is the key convenience: counts[x] += 1 always works, even for a brand-new x.

# --- most_common: the top-N question, built in ---------------------------
print(counts.most_common(2))           # [("cat", 3), ("dog", 2)]  — sorted by count desc
print(counts.most_common())            # all of them, most-frequent first
# (For top-N by a numeric field of records, use heapq.nlargest instead — see 3.17.)

# --- other handy bits ----------------------------------------------------
print(len(counts))                     # 3  — number of DISTINCT values (like nunique)
print(sum(counts.values()))            # 6  — total number of items counted
print(list(counts.elements()))         # ["cat","cat","cat","dog","dog","bird"] — expand back

# --- counting with a generator (O(1) memory over a stream) ---------------
# Don't build a giant list just to count it — feed Counter a generator (1.2):
word_counts = Counter(
    word
    for line in open("corpus.txt", encoding="utf-8")
    for word in line.split()           # stream words; Counter tallies as they arrive
)
print(word_counts.most_common(10))     # the 10 most frequent words

# --- arithmetic between Counters -----------------------------------------
a = Counter({"cat": 3, "dog": 2})
b = Counter({"cat": 1, "bird": 5})
print(a + b)                           # add counts: Counter({"bird":5,"cat":4,"dog":2})
print(a - b)                           # subtract (drops <=0): Counter({"cat":2,"dog":2})
print(a & b)                           # min of each: Counter({"cat": 1})  (intersection)
# Useful for combining counts across shards/batches, or diffing two distributions.

# --- equivalent without Counter, for comparison --------------------------
# counts = {}
# for x in labels:
#     counts[x] = counts.get(x, 0) + 1   # .get(x, 0) is the dict way to default missing
# Counter just packages this pattern (plus most_common) into a tested, readable tool.
```

### Why it works

`Counter` overrides `__missing__` so that accessing an absent key returns `0` instead of
raising — which is exactly what "increment a count" needs, eliminating the initialise
step. Its constructor accepts any iterable and tallies in a single C-level pass (fast),
and it keeps an internal structure that lets `most_common(n)` return the top values
sorted by count without you writing a sort. Because it's still a `dict`, everything you
know about dicts (iteration, `.items()`, membership) applies unchanged.

### Impact

- **Less code, fewer bugs:** one `Counter(iterable)` replaces the four-line
  initialise-or-increment loop and removes the "forgot to initialise → KeyError" mistake.
- **Right answers fast:** `most_common`, `len` (distinct), and `sum(values())` give the
  frequency, cardinality, and total without extra passes.
- **Composability:** Counter arithmetic merges counts across batches/shards cleanly —
  ideal for map-reduce-style aggregation.

### Pros & cons / when NOT to

**Reach for `Counter` when:** you need frequencies, a histogram, the most/least common
values, or to merge counts — the everyday "how many of each".

**Watch out / when NOT to:**
- **Keys must be hashable** (like set elements, 3.13) — count tuples for composite keys
  (3.18), not lists.
- **`most_common()` with no argument sorts everything** — O(k log k) in the number of
  distinct keys; fine usually, but if you only need the top few, pass `n`.
- **For numeric columns in a DataFrame, use pandas** `value_counts()` (3.12) — it's
  vectorised and integrates with the rest of your analysis; `Counter` shines in pure-
  Python / streaming code.
- **`Counter` counts occurrences, not sums.** To total a *value* per key (e.g. revenue
  per region), that's a group-and-sum — use `defaultdict(float)` or pandas `groupby`
  (3.15, 3.22), not `Counter`.

### Where this shows up

- **Real work — class balance & label distribution:** the first check on any
  classification dataset (3.12, 8.4) — `Counter(labels).most_common()`.
- **Real work — vocabulary & token frequency:** building word/token frequency tables for
  NLP (vocab construction, rare-token filtering), streamed over a corpus.
- **Real work — log/event analysis:** counting error codes, endpoints hit, or status
  codes to find the most frequent failures.
- **Pattern mapping (secondary):** frequency maps are the backbone of "anagram groups",
  "top-k frequent elements" (11.12, often `Counter` + `heapq`), and "first unique
  character" problems — `Counter` is the idiomatic Python answer to all of them.
[↑ Back to top](#contents)

---

<a id="3.15"></a>
## 3.15 — "Group records by a field" → `defaultdict(list)`

### The situation

You have a flat list of transactions and want them grouped by region, so you can sum or
inspect each region's transactions together:

```python
txns = [
    {"region": "north", "amount": 10},
    {"region": "south", "amount": 7},
    {"region": "north", "amount": 15},
    {"region": "west",  "amount": 3},
    {"region": "south", "amount": 2},
]
# want: {"north": [ {..10..}, {..15..} ], "south": [...], "west": [...]}
```

You write the group-by-hand idiom:

```python
groups = {}
for t in txns:
    region = t["region"]
    if region not in groups:               # first transaction for this region?
        groups[region] = []                # create the bucket
    groups[region].append(t)               # then append into it
```

It works, but every grouping you ever write repeats that "if the key isn't there,
create an empty list first" ceremony — and the day you forget it, `groups[region]
.append(t)` raises `KeyError` because the bucket doesn't exist yet.

### What's really going on

This is **grouping** — partitioning records into buckets by a key — the in-memory,
*unsorted-input* counterpart to `itertools.groupby` (1.12, which needs sorted input).
The friction is the "create the bucket on first sight" step. `collections.defaultdict`
removes it: a **`defaultdict`** is a dict that, when you access a *missing* key,
automatically creates a default value for it (using a factory function you supply)
*before* returning it — so `groups[region].append(t)` just works on the first
transaction, because accessing `groups[region]` auto-creates an empty list.

The factory is the argument: `defaultdict(list)` makes missing keys default to a fresh
`[]`; `defaultdict(int)` to `0` (a hand-rolled Counter); `defaultdict(set)` to an empty
set (group into unique members).

### The move

Group with a **`defaultdict`**, whose missing keys auto-create the right empty container
(no "create the bucket first" step):

```python
from collections import defaultdict
groups = defaultdict(list)           # missing key -> a fresh []
for t in txns:
    groups[t["region"]].append(t)    # append works on first sight — bucket auto-created
```

### The code, every line explained

```python
from collections import defaultdict

# --- group into lists: the canonical use ---------------------------------
groups = defaultdict(list)             # missing key -> a NEW empty list, automatically
for t in txns:
    groups[t["region"]].append(t)      # accessing groups[region] auto-creates [] if absent
# groups == {"north": [...,...], "south": [...,...], "west": [...]}
# No "if region not in groups" — the defaultdict handles first-sight creation.
# NOTE: defaultdict(list) — pass the TYPE `list`, not a call `list()`; it's the FACTORY.

# --- then aggregate per group --------------------------------------------
for region, items in groups.items():
    total = sum(t["amount"] for t in items)
    print(region, total)               # north 25 / south 9 / west 3

# --- group-and-SUM directly with defaultdict(int) (no intermediate lists) -
totals = defaultdict(int)              # missing key -> 0
for t in txns:
    totals[t["region"]] += t["amount"] # 0 + amount on first sight; accumulates after
# totals == {"north": 25, "south": 9, "west": 3}   — one pass, O(1) memory per key

# --- group into SETS (collect unique members per key) --------------------
users_by_region = defaultdict(set)
for t in txns:
    users_by_region[t["region"]].add(t.get("user_id"))   # unique users per region

# --- the standard-dict equivalent: setdefault ----------------------------
groups = {}
for t in txns:
    groups.setdefault(t["region"], []).append(t)
# setdefault(key, default) returns groups[key], inserting `default` first if absent.
# Works without importing defaultdict, but RE-EVALUATES the default [] every call
# (cheap here) and reads less clearly for repeated grouping — defaultdict is preferred.

# --- a subtle defaultdict GOTCHA: reads create keys ----------------------
d = defaultdict(list)
_ = d["never_appended"]                # just LOOKING UP a missing key CREATES it!
print(dict(d))                         # {"never_appended": []}  — an empty bucket appeared
# If you only want to CHECK presence without creating, use `key in d` or .get(key),
# never d[key]. After building, convert with dict(d) to get normal KeyError behaviour.
```

### Why it works

`defaultdict` overrides the dict's `__missing__` hook: when you index a key that isn't
present, instead of raising `KeyError` it calls the factory you passed (`list`, `int`,
`set`, ...) to manufacture a default, stores it under that key, and returns it. So
`groups[region].append(t)` on a brand-new region transparently becomes "create `[]`,
store it, append to it". This collapses the three-line create-then-append into one line
and makes the `KeyError` impossible. Crucially — unlike `groupby` (1.12) — it works on
**unsorted** input in a single O(n) pass.

### Impact

- **Less code, no KeyError:** the create-the-bucket ceremony disappears; grouping becomes
  one line in the loop.
- **One-pass and flexible:** groups unsorted data in O(n) without a sort (cheaper than
  `sorted(...)` + `groupby` when you don't otherwise need the data sorted).
- **Right tool per aggregation:** `list` to collect, `int` to sum/count, `set` to collect
  uniques — the factory expresses the intent.

### Pros & cons / when NOT to

**Reach for `defaultdict` when:** grouping or accumulating into per-key collections from
**unsorted** data — the everyday "bucket these records by some field".

**Watch out / when NOT to:**
- **Reads create keys.** Merely *looking up* a missing key inserts a default — surprising
  if you later iterate and find phantom empty buckets. Use `in`/`.get` for pure presence
  checks, and `dict(d)` to "freeze" it back to KeyError-on-missing behaviour.
- **Already-sorted data → `itertools.groupby`** (1.12) streams groups with O(1) memory
  and no full dict; prefer it when input is sorted by the key (e.g. from a sorted DB
  query).
- **DataFrame data → pandas `groupby`** (3.22) is vectorised and far faster for
  split-apply-combine over columns; `defaultdict` is for pure-Python / streaming records.
- **Counting specifically → `Counter`** (3.14) is clearer than `defaultdict(int)` for
  plain frequencies (though `defaultdict(int)` wins when you sum a *value*, not occurrences).

### Where this shows up

- **Real work — group-then-aggregate ETL:** summing revenue per region, averaging latency
  per endpoint, collecting events per user — the in-memory split-apply-combine before (or
  instead of) pandas.
- **Real work — building an inverted index / adjacency:** `defaultdict(list)` mapping
  term → documents containing it, or node → neighbours — the construction step for search
  and graph code.
- **Real work — bucketing for batched processing:** grouping records by shard/partition
  key before writing each group to its own file (ties to 3.10).
- **Pattern mapping (secondary):** `defaultdict(list)` *is* the adjacency-list builder for
  graph problems (Area 11) and the bucket step in bucket/radix-style grouping; the
  "group by key" shape recurs in anagram-grouping and partition problems.
[↑ Back to top](#contents)

---

<a id="3.16"></a>
## 3.16 — "Match two datasets on a key" → dict join

### The situation

You have two datasets that share a key and need to combine them — attach each order's
customer name from a separate customers table:

```python
customers = [                              # ~10,000 customers
    {"id": "c1", "name": "Ann"},
    {"id": "c2", "name": "Bob"},
]
orders = [                                 # ~1,000,000 orders
    {"order_id": "o1", "customer_id": "c1", "amount": 50},
    {"order_id": "o2", "customer_id": "c2", "amount": 30},
    {"order_id": "o3", "customer_id": "c1", "amount": 20},
]
# want each order enriched with the customer's name
```

The natural nested loop — for each order, scan customers for the match:

```python
for o in orders:
    for c in customers:                    # scan ALL customers for EVERY order
        if c["id"] == o["customer_id"]:
            o["name"] = c["name"]
            break
```

On a small sample it's fine. On 1,000,000 orders × 10,000 customers it's **10 billion**
comparisons — minutes-to-hours of pointless scanning. This is a SQL-style **join** done
the slow way; you're rediscovering the accidental O(n×m) (2.2).

### What's really going on

A **join** matches rows from two datasets on a shared **key**. The nested loop is
O(n×m) because for each of n orders it linearly scans all m customers. The fix is the
same insight as 3.13/2.9: replace the *linear scan* of the lookup side with an **O(1)
hash lookup** by first building a **dict index** keyed on the join field.

Build the smaller side once into `{key: record}` (an index). Then each lookup is O(1),
so the whole join is **O(n + m)** — build the index in O(m), do n constant-time lookups.
This is exactly what a database does under the hood ("hash join").

### The move

Build a **dict index** of the lookup side keyed on the join field, then look up in O(1) —
turning the O(n×m) nested loop into O(n + m):

```python
by_id = {c["id"]: c for c in customers}      # index once, O(m)
for o in orders:
    o["name"] = (by_id.get(o["customer_id"]) or {}).get("name")   # O(1) per order
```

### The code, every line explained

```python
# --- STEP 1: build an index of the lookup side: {key: record} ------------
by_id = {c["id"]: c for c in customers}    # dict comprehension (1.1): id -> customer
# by_id == {"c1": {...Ann...}, "c2": {...Bob...}} — built once, O(m).
# If ids can repeat and you want ALL matches, build {key: [records]} with defaultdict (3.15).

# --- STEP 2: enrich each order via O(1) lookup ---------------------------
for o in orders:
    c = by_id.get(o["customer_id"])        # O(1) hash lookup; None if no match (3.5)
    o["name"] = c["name"] if c else None   # handle the "no matching customer" case
# Total: O(m) to index + O(n) lookups = O(n + m). Billions of comparisons -> millions.

# --- INNER vs LEFT join: what to do with non-matches ---------------------
# LEFT join (keep every order, name=None when unmatched):
enriched = [{**o, "name": (by_id.get(o["customer_id"]) or {}).get("name")} for o in orders]
# INNER join (keep ONLY orders that have a matching customer):
matched = [
    {**o, "name": by_id[o["customer_id"]]["name"]}
    for o in orders
    if o["customer_id"] in by_id           # the filter makes it an inner join
]
# {**o, "name": ...} builds a NEW merged dict (dict unpacking, 1.20) — doesn't mutate o.

# --- one-to-MANY: group the many side, then attach -----------------------
from collections import defaultdict
orders_by_customer = defaultdict(list)     # customer_id -> [their orders]  (3.15)
for o in orders:
    orders_by_customer[o["customer_id"]].append(o)
for c in customers:
    c["orders"] = orders_by_customer.get(c["id"], [])   # attach each customer's orders
# This is the "group then join" pattern: index the many side, look up from the one side.

# --- detect key problems BEFORE joining ----------------------------------
ids = [c["id"] for c in customers]
assert len(ids) == len(set(ids)), "duplicate customer ids — index would silently drop rows!"
# {c["id"]: c ...} keeps only the LAST record per duplicate key — a silent data-loss trap.
unmatched = [o for o in orders if o["customer_id"] not in by_id]   # orphan orders
print(f"{len(unmatched)} orders have no customer")   # surface match failures (3.12)
```

### Why it works

Indexing turns "find the customer with this id" from a linear scan (O(m)) into a hash
lookup (O(1)). You pay O(m) once to build the dict, then every one of the n joins is
constant-time, so the total is O(n + m) instead of O(n×m). The dict *is* the hash table
a database builds for a hash join — you're doing the same algorithm by hand. Choosing
`{key: record}` vs `{key: [records]}` (via `defaultdict(list)`) decides one-to-one vs
one-to-many; filtering on `key in index` decides inner vs left.

### Impact

- **Speed:** O(n×m) → O(n + m). On the example that's ~10 billion operations down to
  ~1 million — the difference between a job that hangs and one that's instant.
- **Correctness:** explicit `.get`/`in` handling makes "no match" a defined outcome
  (left join with `None`, or inner join that drops it) rather than an accident.
- **Visibility:** counting orphans and asserting key-uniqueness surfaces the data-quality
  problems (duplicate keys, missing references) that silent joins hide.

### Pros & cons / when NOT to

**Reach for a dict join when:** combining two in-memory datasets on a shared key — the
everyday "enrich A with fields from B".

**Watch out / when NOT to:**
- **Duplicate keys in the index side silently lose data:** `{c["id"]: c ...}` keeps only
  the last record per id. If keys aren't unique, use `defaultdict(list)` and decide how to
  combine, or dedup first (3.13).
- **Unmatched keys need a policy.** Decide inner (drop) vs left (keep with `None`)
  *deliberately*, and count the non-matches — silently dropping unmatched rows is a
  classic source of "where did my rows go?".
- **Both sides huge / out of memory** → this is when you reach for pandas `merge` (3.22),
  a database, or Spark — but the algorithm is identical; only the engine changes.
- **Composite join keys** (match on two+ fields) → key the index on a *tuple* of those
  fields (3.18), e.g. `{(r["date"], r["region"]): r}`.

### Where this shows up

- **Real work — feature enrichment:** joining a fact table (events/orders) with dimension
  tables (user profiles, product metadata) to assemble a feature set before training.
- **Real work — label attachment:** matching predictions back to ground-truth labels by
  id to compute metrics (the `zip`-when-aligned case, 1.5, generalised to keyed matching).
- **Real work — reference-data lookups:** mapping codes to descriptions (country code →
  name, sku → product) by indexing the small reference table once.
- **Pattern mapping (secondary):** this is the hash-join algorithm; the same "index one
  side, probe with the other" trick is two-sum's complement lookup (11.1) and underlies
  most "match elements across two collections" problems.
[↑ Back to top](#contents)

---

<a id="3.17"></a>
## 3.17 — "Find the top N" → `heapq`

### The situation

You have 10 million predictions and want the **20 with the highest confidence** to
review:

```python
preds = [
    {"id": "p1", "score": 0.91},
    {"id": "p2", "score": 0.40},
    # ... 10,000,000 of these
]
```

The obvious move is sort everything, then slice:

```python
top20 = sorted(preds, key=lambda p: p["score"], reverse=True)[:20]
```

It's correct, but you just **sorted 10 million records to keep 20** — O(n log n) work
and, worse, `sorted` builds a fully-sorted copy of all 10 million in memory, only to
discard 9,999,980 of them. When you only need the top (or bottom) N and N is small, full
sorting is wasteful on both time and memory.

### What's really going on

"Top N" doesn't require ordering *everything* — it only requires *maintaining the N best
seen so far*. The data structure for "keep track of the smallest/largest few efficiently"
is a **heap**: a binary tree (stored compactly in a list) that always keeps the smallest
element at the front, with O(log k) insert and O(log k) removal of that smallest. Python
provides it via the **`heapq`** module (a "min-heap" — smallest on top).

The trick for top-N-largest: keep a heap of size N. For each new item, if it's bigger
than the heap's smallest (the front), pop the smallest and push the new one. After one
pass you're left with exactly the N largest — using only O(N) memory and O(n log N) time,
not O(n log n). `heapq.nlargest`/`nsmallest` package this pattern so you rarely write the
heap by hand.

### The move

Use **`heapq.nlargest`/`nsmallest`** with a `key`, which keep a heap of size N instead of
sorting everything — O(n log N) time and O(N) memory, and it works over a stream:

```python
import heapq
top20 = heapq.nlargest(20, preds, key=lambda p: p["score"])
```

### The code, every line explained

```python
import heapq

# --- the easy way: heapq.nlargest / nsmallest with a key ----------------
top20 = heapq.nlargest(20, preds, key=lambda p: p["score"])   # 20 highest by score
bot20 = heapq.nsmallest(20, preds, key=lambda p: p["score"])  # 20 lowest by score
# Internally keeps a heap of size 20 -> O(n log 20) time, O(20) extra memory.
# `key` works exactly like in sorted() (1.15) — extract the value to compare on.

# --- works on a STREAM/generator too (never materialise all n) ----------
top20 = heapq.nlargest(20, (p for p in read_jsonl("preds.jsonl")),  # generator (1.2, 3.2)
                        key=lambda p: p["score"])
# Processes 10M records with O(20) memory — the whole point vs sorted().

# --- a heap as a running structure (e.g. streaming top-N) ---------------
heap = []                                  # a min-heap, represented as a plain list
for p in preds:
    if len(heap) < 20:
        heapq.heappush(heap, (p["score"], p["id"]))      # push (sort_value, payload) tuples
    elif p["score"] > heap[0][0]:          # heap[0] is the SMALLEST kept so far
        heapq.heapreplace(heap, (p["score"], p["id"]))   # pop smallest, push new — one op
# After the pass, `heap` holds the 20 largest (as (score, id) tuples), smallest-first.
top20 = sorted(heap, reverse=True)         # sort just those 20 for presentation

# --- heap basics (a priority queue) --------------------------------------
h = []
heapq.heappush(h, 5); heapq.heappush(h, 1); heapq.heappush(h, 3)
print(heapq.heappop(h))                    # 1  — always removes the SMALLEST. O(log n).
print(h[0])                                # peek at the smallest without removing
# For a MAX-heap (largest on top), negate the priority: push -value, negate on pop.

# --- tie-breaking: avoid comparing the payload dict ----------------------
# heappush(h, (score, dict)) FAILS if two scores tie (it then compares the dicts, which
# are unorderable -> TypeError). Add a unique tiebreaker:
import itertools
counter = itertools.count()                # 0,1,2,... unique increasing ints
heapq.heappush(h, (p["score"], next(counter), p))   # (score, seq, payload): seq breaks ties
```

### Why it works

A heap keeps its smallest element instantly accessible (`h[0]`) and supports
insert/pop-smallest in O(log k) for a heap of size k. For top-N-largest you cap the heap
at N: each incoming item is compared against the current smallest of the N kept; if it's
larger it displaces it. So you only ever store N items and do O(log N) work per element —
O(n log N) total, versus O(n log n) to sort everything. When N ≪ n (the usual case for
"top 20 of 10 million"), that's a massive saving, and it works over a stream because you
never need all n in memory at once.

### Impact

- **Memory:** O(n) (full sorted copy) → O(N) (just the N kept) — lets you take the top-N
  of data far larger than RAM via a generator.
- **Speed:** O(n log n) → O(n log N); for N=20, n=10M, ~log₂(20)≈4.3 vs log₂(10M)≈23 per
  element — several times less comparison work.
- **Clarity:** `heapq.nlargest(20, data, key=...)` states "top 20 by score" in one line.

### Pros & cons / when NOT to

**Reach for `heapq` when:** you need the top/bottom N (N small relative to total),
especially over a large or streaming dataset, or you need a **priority queue** (always
pull the current best/worst).

**Watch out / when NOT to:**
- **If N is close to n, just sort.** `nlargest(n-5, data)` saves nothing; `sorted` is
  simpler and the heap overhead isn't worth it. The win is when N ≪ n.
- **`nlargest(1)`/`nsmallest(1)` → use `max`/`min`** with a `key` — simpler and faster
  for a single extremum.
- **Tuple tie-breaking:** when pushing `(priority, payload)` tuples, equal priorities make
  Python compare the payloads, which may be unorderable (dicts) → `TypeError`. Insert a
  unique sequence counter as a middle element (shown above).
- **DataFrame data → pandas** `df.nlargest(20, "score")` is the vectorised equivalent
  (3.21). `heapq` is for pure-Python/streaming records.

### Where this shows up

- **Real work — top-k retrieval:** the k most similar vectors/documents to a query in a
  RAG/recommendation system (the brute-force top-k before an ANN index; ties to 9.14).
- **Real work — review queues & triage:** surfacing the N highest-loss training examples,
  the N most expensive queries, or the N largest files — without sorting everything.
- **Real work — streaming leaderboards/metrics:** maintaining the running top-N over an
  unbounded event stream with bounded memory.
- **Pattern mapping (secondary):** this is the canonical **heap / priority-queue** family
  — "kth largest element", "top-k frequent" (`Counter` + `heapq`, 3.14), and "merge k
  sorted lists" (11.12) — and the priority queue behind Dijkstra (11.18).
[↑ Back to top](#contents)

---

<a id="3.18"></a>
## 3.18 — "Look up by two+ fields" → composite/tuple keys

### The situation

You're aggregating sales and need totals broken down by **two** fields together —
region *and* product — not by either one alone:

```python
sales = [
    {"region": "north", "product": "A", "amount": 10},
    {"region": "north", "product": "B", "amount": 5},
    {"region": "south", "product": "A", "amount": 7},
    {"region": "north", "product": "A", "amount": 3},   # same (north, A) as row 1
]
# want: {(north, A): 13, (north, B): 5, (south, A): 7}
```

Your instinct is a nested dict — region → product → total:

```python
totals = {}
for s in sales:
    r, p = s["region"], s["product"]
    if r not in totals:                    # create the outer bucket...
        totals[r] = {}
    totals[r][p] = totals[r].get(p, 0) + s["amount"]   # ...then the inner
# totals == {"north": {"A": 13, "B": 5}, "south": {"A": 7}}
```

It works but is awkward: two levels of "create-if-missing", and every later operation
(iterate all, sort by total, look one up) means juggling two layers. Looking up
"north + A" is `totals["north"]["A"]` — and any missing level raises (3.3).

### What's really going on

When the *identity* of a bucket is a **combination** of fields, the natural key is that
combination itself — a **tuple** `(region, product)` — not a tree of nested dicts. A
tuple is **immutable and hashable**, so it can be a dict key or set element directly.
Keying on `(region, product)` gives a **flat** dict where one lookup, one update, and one
iteration handle the multi-field grouping — no nesting.

This is the same idea that lets sets dedup composite identities (3.13) and dicts join on
multi-column keys (3.16): bundle the fields into a tuple and treat the bundle as one key.

### The move

Bundle the fields into a **tuple** and use that as a single dict/set key — a flat
structure instead of nested dicts:

```python
from collections import defaultdict
totals = defaultdict(int)
for s in sales:
    totals[(s["region"], s["product"])] += s["amount"]   # composite tuple key
```

### The code, every line explained

```python
from collections import defaultdict

# --- composite tuple key: flat, one level -------------------------------
totals = defaultdict(int)                  # (region, product) -> total  (defaultdict, 3.15)
for s in sales:
    key = (s["region"], s["product"])      # the COMPOSITE key: a tuple of both fields
    totals[key] += s["amount"]             # one update, no nesting
# totals == {("north","A"): 13, ("north","B"): 5, ("south","A"): 7}

# --- lookup, iterate, sort: all one-level operations ---------------------
print(totals[("north", "A")])              # 13 — direct lookup by the pair
for (region, product), amt in totals.items():   # unpack the tuple key (1.6) while iterating
    print(region, product, amt)
top = max(totals, key=totals.get)          # the (region, product) with the highest total
ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)  # rank all buckets

# --- composite keys in a SET (dedup on multiple fields) ------------------
seen = set()
for s in sales:
    key = (s["region"], s["product"], s["amount"])   # "same" = all three match
    if key in seen:
        continue
    seen.add(key)
    ...                                    # process only first occurrence of each combo

# --- composite keys for a multi-field JOIN (ties to 3.16) ---------------
prices = [{"region": "north", "product": "A", "price": 2.0}]
price_index = {(p["region"], p["product"]): p["price"] for p in prices}   # tuple-keyed index
for s in sales:
    unit = price_index.get((s["region"], s["product"]))   # match on BOTH fields at once

# --- WHY a tuple and not a list ------------------------------------------
# key = [s["region"], s["product"]]        # TypeError: unhashable type: 'list'
key = (s["region"], s["product"])          # tuples are immutable -> hashable -> valid key
# Order matters: ("A","B") != ("B","A"). Keep field order consistent everywhere.
# Beware None/empty in key fields: (None, "A") is a distinct, valid key — normalise first.

# --- when a tuple key gets unwieldy: a NamedTuple reads better -----------
from collections import namedtuple
Key = namedtuple("Key", ["region", "product"])   # a tuple with NAMED fields
totals = defaultdict(int)
for s in sales:
    totals[Key(s["region"], s["product"])] += s["amount"]
print(totals[Key("north", "A")])           # 13 — same hashing, but k.region/k.product read clearly
```

### Why it works

Python dicts and sets key on **hashable** objects, and a tuple of hashable values is
itself hashable — its hash combines the hashes of its elements, so `(region, product)`
identifies a bucket as precisely as the pair of values does. Because the key is a single
flat value, all the multi-field grouping/lookup/dedup/join operations collapse to
ordinary single-key dict/set operations — no nested structure to traverse or guard. A
`namedtuple` is still a tuple (same hashing) but adds field names for readability when
the key has several parts.

### Impact

- **Simplicity:** flat single-level dict replaces nested dicts — one create-if-missing,
  one lookup, one iteration, no per-level guarding (3.3).
- **Uniformity:** multi-field grouping, dedup, and joins all become the same single-key
  pattern, so the same tools (`defaultdict`, `Counter`, set ops, dict join) apply directly.
- **Correctness:** the tuple captures "these fields together define identity" exactly,
  avoiding the bugs of stringly-concatenated keys (see below).

### Pros & cons / when NOT to

**Reach for a tuple key when:** a bucket/lookup/dedup identity is defined by two or more
fields together — multi-dimensional aggregation, multi-column joins, composite dedup.

**Watch out / when NOT to:**
- **Don't fake it with string concatenation.** `f"{region}_{product}"` *seems* to work
  but breaks when a value contains the separator (`"a_b" + "c"` collides with `"a" +
  "b_c"`) and loses the typed components. A tuple has no separator ambiguity and keeps the
  parts addressable.
- **Key fields must be hashable & stable.** Normalise them first (case, whitespace, `None`
  vs `""`, float precision) — `("North", "A")` and `("north", "A")` are *different* keys,
  a silent source of split buckets (ties to normalisation, 4.1).
- **Order is significant:** `(region, product)` ≠ `(product, region)`. Pick one order and
  use it everywhere.
- **Many fields / heavy reuse → a `@dataclass(frozen=True)` or `NamedTuple`** is clearer
  and self-documenting than a bare positional tuple, and is still hashable.
- **DataFrame data → pandas** groups on multiple columns directly
  (`groupby(["region","product"])`, 3.22) and builds a MultiIndex — the vectorised
  equivalent of the tuple key.

### Where this shows up

- **Real work — multi-dimensional aggregation:** revenue by (region, product), error rate
  by (service, status_code), metrics by (model, dataset) — the pure-Python `groupby`-on-
  several-columns.
- **Real work — composite-key joins/dedup:** matching or deduping records that are unique
  only on a combination of fields (e.g. (user_id, date)) — 3.13, 3.16.
- **Real work — sparse matrices / co-occurrence:** `{(row, col): value}` to store only the
  non-zero cells of a large sparse matrix, or `{(word_i, word_j): count}` co-occurrence.
- **Pattern mapping (secondary):** tuple state keys are the standard memoization key for
  multi-parameter DP (`@cache` on `f(i, j)`; 1.13) and for "visited" sets over grid
  coordinates `(row, col)` in BFS/DFS (Area 11).
[↑ Back to top](#contents)

---

<a id="3.19"></a>
## 3.19 — "Sort by multiple fields" → key functions & multi-key sort

### The situation

You have employee records and need them ordered the way a report wants them: **by
department (A→Z), then within each department by salary (highest first), then by name
(A→Z) to break ties**:

```python
employees = [
    {"dept": "eng",   "salary": 90, "name": "Bob"},
    {"dept": "eng",   "salary": 90, "name": "Ann"},
    {"dept": "sales", "salary": 70, "name": "Cy"},
    {"dept": "eng",   "salary": 95, "name": "Di"},
]
# want: eng/Di(95), eng/Ann(90), eng/Bob(90), sales/Cy(70)
```

You reach for what you'd do in another language — sort, and pass a comparison function
that decides "which of these two comes first":

```python
def compare(a, b):                         # the C/Java instinct: a comparator
    if a["dept"] != b["dept"]:
        return -1 if a["dept"] < b["dept"] else 1
    if a["salary"] != b["salary"]:
        return -1 if a["salary"] > b["salary"] else 1   # note: reversed for desc
    return -1 if a["name"] < b["name"] else 1
# ...then sorted(employees, key=functools.cmp_to_key(compare))
```

It's verbose, error-prone (one flipped sign and the order is silently wrong), and slow
(a Python function call per comparison). Python wants you to describe *what to sort by*,
not *how to compare two items*.

### What's really going on

Python's `sorted`/`list.sort` are built around a **key function**, not a comparator: you
supply a function that maps each item to the **value it should be sorted by**, and Python
sorts by those values. (This is the same `key=` mechanism as 1.15 — here applied to sort
*records* by several *fields* at once.) For multiple fields, the key returns a **tuple**
of the fields in priority order: Python compares tuples element by element, so it sorts
by the first field, breaks ties with the second, then the third — exactly the report's
rule.

Two facts make this clean. First, **tuple comparison is lexicographic**: `(a1, b1) <
(a2, b2)` compares `a1` vs `a2` first, and only looks at `b` if the `a`s are equal — so a
tuple key *is* multi-level sorting. Second, Python's sort is **stable**: items that
compare equal keep their original relative order, which lets you handle mixed
ascending/descending directions with successive sorts.

### The move

Pass a **key function returning a tuple** of the fields in priority order; Python compares
tuples lexicographically, so it sorts by the first field, then breaks ties with the next:

```python
ranked = sorted(employees, key=lambda e: (e["dept"], -e["salary"], e["name"]))
# dept asc, salary desc (negated), name asc
```

### The code, every line explained

```python
# --- multi-key sort: the key returns a TUPLE of fields, in priority order -
ranked = sorted(
    employees,
    key=lambda e: (e["dept"], -e["salary"], e["name"])
    #               │          │             └ 3rd: name ASCENDING (tie-break)
    #               │          └ 2nd: salary DESCENDING — negate the number to flip it
    #               └ 1st: dept ASCENDING
)
# Python compares the tuples lexicographically -> dept asc, then salary desc, then name asc.
# Result: eng/Di(95), eng/Ann(90), eng/Bob(90), sales/Cy(70)  — exactly as wanted.

# --- descending: negate numbers, OR use reverse= (whole-key) ------------
sorted(employees, key=lambda e: e["salary"], reverse=True)   # single field, desc
# reverse=True flips the ENTIRE ordering. For MIXED directions (dept asc, salary desc)
# you cannot use reverse=; negating the numeric field is the trick (above).

# --- mixed directions when a field ISN'T numeric: stable multi-pass ------
# You can't negate a string. Exploit STABLE sort: sort by the LEAST significant key
# first, then the most significant last. Each later sort preserves earlier ties' order.
s = sorted(employees, key=lambda e: e["name"])                # least significant first
s = sorted(s, key=lambda e: e["salary"], reverse=True)        # then salary desc
s = sorted(s, key=lambda e: e["dept"])                        # MOST significant last
# Same result as the tuple key, and it handles "string desc + number asc" cleanly.

# --- operator.itemgetter / attrgetter: faster, clearer than lambda -------
from operator import itemgetter, attrgetter
sorted(employees, key=itemgetter("dept", "salary"))   # dept then salary (both ascending)
# itemgetter("dept","salary") returns a function pulling (e["dept"], e["salary"]) — a
# tuple key, in C, so it's faster than a Python lambda. (attrgetter for objects: .dept)
# (No per-field direction control with itemgetter — use the lambda/tuple form for that.)

# --- sort in place vs return a new list ----------------------------------
employees.sort(key=itemgetter("dept"))    # .sort() sorts the list IN PLACE, returns None
new = sorted(employees, key=itemgetter("dept"))   # sorted() returns a NEW sorted list
# Use .sort() to reorder an existing list; sorted() when you must keep the original.
```

### Why it works

`sorted` calls your key function **once per item** (O(n) calls), caches the resulting
keys, and orders by them with an efficient O(n log n) comparison sort — versus a
comparator that's invoked O(n log n) times, each a Python call. Because tuples compare
lexicographically, returning `(dept, -salary, name)` *is* the multi-level rule, with no
hand-written branching to get wrong. And because the sort is **stable**, the
sort-least-significant-first technique composes correctly: each pass leaves the relative
order of the previous pass's ties intact, building up the full ordering.

### Impact

- **Correctness:** the tuple key encodes the exact priority order declaratively — no
  flipped-sign comparator bugs.
- **Speed:** key functions are called O(n) times (and `itemgetter` runs in C), versus an
  O(n log n)-call Python comparator — often several times faster.
- **Clarity:** one line states "sort by dept, then salary desc, then name" — readable as
  the spec itself.

### Pros & cons / when NOT to

**Reach for a tuple key when:** ordering records by several fields with a fixed priority —
reports, leaderboards, deterministic output ordering.

**Watch out / when NOT to:**
- **Mixed directions with a non-numeric field:** you can't negate a string. Either use
  the stable multi-pass technique (above) or wrap with a custom key (e.g. `reverse` a
  string sort by sorting a transformed key) — don't try to cram it into one `reverse=`.
- **Heterogeneous/None field values break comparison:** a tuple key containing both `int`
  and `None` (or `str` and `int`) raises `TypeError: '<' not supported`. Normalise/coerce
  first (3.4) or supply a sentinel that sorts predictably (e.g. `(e["salary"] is None,
  e["salary"])` to push `None`s to one end).
- **DataFrame data → pandas** `df.sort_values(["dept","salary"], ascending=[True,False])`
  is the vectorised equivalent with per-column direction (3.21).
- **Only need the top few, not a full order → `heapq.nlargest`** (3.17) avoids sorting
  everything.

### Where this shows up

- **Real work — deterministic, reproducible output:** sorting records by stable multi-key
  order before writing, so diffs/golden tests are stable across runs (ties to 3.10's
  `sorted(rglob(...))` and regression tests, 10.11).
- **Real work — ranking & leaderboards:** ordering candidates/predictions by a primary
  score then tie-breakers (recency, id) for display or selection.
- **Real work — preparing grouped reports:** ordering rows by group then within-group
  metric before a `groupby` pass (1.12) or for human-readable tables.
- **Pattern mapping (secondary):** tuple-key sorting is the idiomatic answer to "sort by
  X then Y" interview problems and the preprocessing step for interval/greedy algorithms
  that require sorted-by-start-then-end input (11.7, 11.24).
[↑ Back to top](#contents)

---

<a id="3.20"></a>
## 3.20 — "Search/insert in sorted data" → `bisect`

### The situation

Two related needs on data that's already **sorted**.

**Need 1 — bucket a value into a range.** You convert numeric scores to letter grades:

```python
def grade(score):                          # 0–59 F, 60–69 D, 70–79 C, 80–89 B, 90+ A
    if score >= 90:  return "A"
    if score >= 80:  return "B"
    if score >= 70:  return "C"
    if score >= 60:  return "D"
    return "F"
```

That's fine for 5 grades. But the same shape appears with **hundreds** of breakpoints —
tax brackets, latency-percentile buckets, age bins — and the if-ladder becomes a long,
error-prone chain you scan top to bottom (O(k) comparisons per value).

**Need 2 — keep a list sorted as you add to it.** You repeatedly insert values and want
the list to stay ordered, so you `list.append(x)` then `list.sort()` — re-sorting the
whole list (O(n log n)) on every single insert.

### What's really going on

When data is **sorted**, you don't need to scan it linearly — you can **binary search**:
repeatedly halve the search range, finding the position in **O(log n)** instead of O(n).
Both needs are binary search in disguise: bucketing is "where would this value fall among
the breakpoints?", and ordered insertion is "where does this value go to keep the list
sorted?". Python's **`bisect`** module does both — it finds the insertion position for a
value in a sorted list in O(log n), and `insort` inserts there while preserving order.

The subtlety is *which side of equal values*: `bisect_left` returns the position
**before** any equal elements, `bisect_right` (a.k.a. `bisect`) the position **after** —
which matters for boundary values (is a score of exactly 90 an "A"?).

### The move

Use **`bisect`** on the sorted data: `bisect_right`/`bisect_left` to find a position in
O(log n) (for bucketing or range queries), and `insort` to insert while keeping order:

```python
import bisect
i = bisect.bisect_right(breakpoints, score)   # which band does score fall in?
bisect.insort(sorted_list, x)                 # insert, staying sorted, without re-sorting
```

### The code, every line explained

```python
import bisect

# --- Need 1: bucket a value with bisect (replaces the if-ladder) ---------
breakpoints = [60, 70, 80, 90]             # the boundaries, sorted ascending
grades      = "FDCBA"                       # F below 60, then D,C,B, A at 90+
def grade(score):
    i = bisect.bisect_right(breakpoints, score)   # how many breakpoints are <= score
    return grades[i]                              #   -> index into the grade bands
# bisect_right(breakpoints, 90) = 4 -> grades[4] = "A"; score 89 -> 3 -> "B".
print([grade(s) for s in [55, 60, 72, 89, 90, 100]])   # ['F','D','C','B','A','A']
# O(log k) per lookup regardless of how many breakpoints — scales to hundreds of bins.
# Choosing _right means 60 -> "D" (60 falls in the 60–69 band). Use _left if you want
# a value exactly ON a boundary to fall in the LOWER band instead — pick deliberately.

# --- find an element's position / membership in a sorted list ------------
a = [1, 3, 5, 5, 7]
print(bisect.bisect_left(a, 5))            # 2  — index of the FIRST 5 (before equals)
print(bisect.bisect_right(a, 5))           # 4  — index AFTER the last 5
# "is x present?" in a sorted list, in O(log n):
def contains(sorted_list, x):
    i = bisect.bisect_left(sorted_list, x)
    return i < len(sorted_list) and sorted_list[i] == x
# (For pure membership a set is simpler/O(1), 3.13; bisect shines when you ALSO need
#  position, ranges, or the data is kept sorted for other reasons.)

# --- count values in a range [lo, hi] in O(log n) ------------------------
lo_i = bisect.bisect_left(a, 3)            # first index >= 3
hi_i = bisect.bisect_right(a, 5)           # first index > 5
print(hi_i - lo_i)                          # 3 values in [3, 5] (the 3 and the two 5s)

# --- Need 2: keep a list sorted on insert with insort --------------------
nums = [10, 20, 30, 40]
bisect.insort(nums, 25)                    # finds position (O(log n)) AND inserts
print(nums)                                # [10, 20, 25, 30, 40] — still sorted
# Beats append+sort: insort is O(n) (the insert shifts elements) but AVOIDS the O(n log n)
# full re-sort per insertion. For many incremental inserts, that's a big saving.

# --- searching sorted RECORDS by a field: bisect on a key list -----------
events = sorted(all_events, key=lambda e: e["ts"])   # sorted by timestamp
times  = [e["ts"] for e in events]                   # parallel list of just the keys
start  = bisect.bisect_left(times, cutoff)           # first event at/after cutoff (3.8)
recent = events[start:]                              # slice — all events in the window
# bisect works on a list of comparable KEYS; build that key list alongside the records.
```

### Why it works

Binary search exploits sortedness: each comparison halves the remaining candidates, so
locating a position takes O(log n) steps — for a million elements, ~20 comparisons versus
up to a million for a linear scan or if-ladder. `bisect` returns the index where a value
would be inserted to keep the list sorted; reading the band *around* that index buckets
the value, and `insort` performs the insert at that index so the list stays ordered
without a re-sort. The `left`/`right` variants control tie handling at exact boundaries,
which is the only thing you must choose deliberately.

### Impact

- **Speed:** O(k)/O(n) → O(log n) for lookups and bucketing; insertion avoids the
  O(n log n) full re-sort. On large breakpoint tables or hot lookup paths this is a real
  win.
- **Clarity & scale:** a hundred-bin classification is a 2-line `bisect` call, not a
  hundred-branch if-ladder you can mis-order.
- **Correctness:** explicit `left`/`right` choice makes boundary behaviour (the "exactly
  90" case) intentional rather than accidental.

### Pros & cons / when NOT to

**Reach for `bisect` when:** the data is **sorted** and you need positional search, range
bucketing, range counts, or to maintain sorted order on insert.

**Watch out / when NOT to:**
- **The list MUST already be sorted** — `bisect` gives silently wrong answers on unsorted
  data (it doesn't check). Sort once up front; if data arrives unsorted and changes
  constantly, reconsider the structure.
- **Pure membership/lookup → a `set`/`dict`** is O(1) and simpler (3.13/2.9). Use `bisect`
  when you specifically need *order*: nearest value, range queries, or sorted insertion.
- **Many inserts into a large list → `insort` is still O(n)** per insert (shifting
  elements). For heavy insert+query workloads, a balanced-tree/`sortedcontainers`
  (`SortedList`) gives O(log n) inserts.
- **DataFrame data → pandas** `pd.cut`/`searchsorted` bucket and binary-search columns in
  a vectorised way (3.21).

### Where this shows up

- **Real work — binning continuous features:** discretising a numeric feature into
  buckets (age groups, score bands, percentile bins) for analysis or as model input — the
  grade example generalised.
- **Real work — time-window queries on sorted events:** finding the slice of a
  timestamp-sorted log within `[start, end]` in O(log n) (ties to 3.8's recency windows).
- **Real work — sampling from a distribution:** building a cumulative-weight array and
  `bisect`-ing a random draw to pick a weighted-random item (used in samplers/data
  loaders).
- **Pattern mapping (secondary):** `bisect` *is* binary search — the foundation of
  "search a sorted array", "search-on-the-answer", and "insert position" problems
  (11.5, 11.6); knowing the stdlib tool means you rarely hand-roll the off-by-one-prone
  binary-search loop.
[↑ Back to top](#contents)

---

<a id="3.21"></a>
## 3.21 — "DataFrame: vectorised ops vs row loops" → pandas thinking

### The situation

You have a DataFrame of orders and need a new column — the total with 18% tax — plus a
flag for large orders. Coming from plain Python, you loop over the rows:

```python
import pandas as pd
df = pd.DataFrame({"amount": [100.0, 250.0, 30.0, 500.0]})   # thousands→millions of rows

totals = []
for i in range(len(df)):                   # loop over row indices
    row = df.iloc[i]                        # fetch row i (slow: builds a Series each time)
    totals.append(row["amount"] * 1.18)     # compute, append
df["total"] = totals
```

On a few rows it's fine. On a million rows it's **agonisingly slow** — often *hundreds of
times* slower than it needs to be — because each `df.iloc[i]` materialises a row object
and every operation runs in interpreted Python. `df.apply(..., axis=1)` and
`df.iterrows()` are the same trap dressed up. Pandas is screaming at you to **not loop**.

### What's really going on

A pandas **DataFrame** is a table of **columns**, and each column (a **Series**) is backed
by a contiguous **NumPy array** — numbers packed together in memory. Operations on a whole
column are **vectorised**: the arithmetic runs in compiled C/NumPy over the entire array at
once, with no per-element Python interpreter overhead and using CPU-friendly bulk memory
access. "Vectorised" = "express the operation on the whole column/array, not element by
element" — the same idea as Area 2's "vectorise the hot path" (2.12), here as the *primary
way you write pandas*.

The mental shift: stop thinking "for each row, do X" and start thinking "transform this
*column* into that *column*." A Python row-loop throws away pandas' entire performance
model; a vectorised expression uses it.

### The move

Stop looping over rows; express the operation on the **whole column** so it runs
vectorised in C, and select rows with **boolean masks**:

```python
df["total"] = df["amount"] * 1.18            # whole column at once — no loop
big = df[df["amount"] > 200]                  # boolean mask selects rows
```

### The code, every line explained

```python
import pandas as pd
df = pd.DataFrame({"amount": [100.0, 250.0, 30.0, 500.0], "region": ["n","s","n","w"]})

# --- vectorised arithmetic: operate on the WHOLE column at once ----------
df["total"] = df["amount"] * 1.18          # multiplies every element in C — no loop
# df["amount"] is a Series (a NumPy-backed column); * 1.18 applies to all rows at once.

# --- vectorised boolean mask: a condition over the whole column ----------
df["is_large"] = df["amount"] > 200        # -> a boolean Series [F, T, F, T]
# Comparisons vectorise too; the result is a per-row True/False column.

# --- conditional column: np.where (vectorised if/else) -------------------
import numpy as np
df["tier"] = np.where(df["amount"] > 200, "big", "small")   # if/else across the column
# For MULTIPLE conditions, use np.select or pd.cut (binning) — still vectorised.

# --- filter rows with a boolean mask (no loop) ---------------------------
big = df[df["amount"] > 200]               # keep rows where the mask is True
big = df[(df["amount"] > 200) & (df["region"] == "n")]   # combine masks with & | ~
# IMPORTANT: use &, |, ~ (bitwise) NOT and/or/not, and parenthesise each condition —
# Python's and/or don't work element-wise on Series and raise/ misbehave.

# --- string operations vectorise via .str --------------------------------
df["region"] = df["region"].str.upper()    # uppercases every value in C (see 4.1)

# --- the SLOW anti-patterns to avoid -------------------------------------
# for i in range(len(df)): df.iloc[i]...    # WORST: per-row Python + object creation
# for _, row in df.iterrows(): ...          # SLOW: builds a Series per row
# df.apply(lambda r: r["amount"]*1.18, axis=1)  # SLOW: Python call per row (axis=1)
# All ~10–1000x slower than df["amount"]*1.18 on large data. Reach for apply(axis=1)
# ONLY when a row genuinely can't be vectorised (e.g. calls an external API per row).

# --- when you MUST do a complex per-element transform: vectorise the parts -
# Instead of apply over rows, combine vectorised column ops:
df["score"] = (df["amount"] - df["amount"].mean()) / df["amount"].std()   # z-score, vectorised
```

> Note: these pandas examples are written to be idiomatically correct but were **not
> executed** here (pandas isn't installed in this environment). The APIs shown
> (`Series` arithmetic, boolean masks, `np.where`, `.str`, `iterrows`/`apply`) are
> standard and stable across pandas 1.x/2.x.

### Why it works

A vectorised column operation hands the whole array to NumPy, which loops in compiled C
over contiguous memory — no Python bytecode per element, no boxing of each value into a
Python object, and good CPU cache behaviour. A Python row-loop does the opposite: it
pays interpreter overhead and object-construction cost *per row*, which is where the
100×+ slowdown comes from. Boolean masks work because a comparison produces a True/False
array that pandas uses to select rows in one C-level pass — again no loop.

### Impact

- **Speed:** vectorised column ops are routinely 10–1000× faster than row loops on large
  frames — often the single biggest performance lever in data code.
- **Clarity:** `df["total"] = df["amount"] * 1.18` states the transform on the column
  directly; intent and speed align.
- **Less code:** masks and `np.where` replace multi-line loops with one expression.

### Pros & cons / when NOT to

**Reach for vectorised pandas/NumPy when:** transforming, filtering, or computing over
columns of a DataFrame — i.e. the normal case.

**Watch out / when NOT to:**
- **`and`/`or`/`not` don't work on Series** — use `&`/`|`/`~` and parenthesise each
  condition (`(a > 1) & (b < 2)`); forgetting this is the #1 pandas beginner error.
- **`apply(axis=1)`/`iterrows` are the loop in disguise** — only acceptable when the
  per-row work genuinely can't be vectorised (e.g. an I/O call per row). Even then,
  consider batching.
- **Chained-assignment / `SettingWithCopyWarning`:** assign back to the frame explicitly
  (`df["x"] = ...` or use `.loc`), don't mutate a slice you got from filtering.
- **Tiny data:** for a handful of rows the speed difference is irrelevant; don't pull in
  pandas just to multiply 5 numbers (plain Python, 1.1, is lighter).
- **Bigger than RAM → Polars/Dask/DuckDB** (6.12) keep the vectorised model but scale out.

### Where this shows up

- **Real work — feature engineering:** computing derived feature columns (ratios,
  z-scores, flags, bins) across a training table — vectorised, not row-by-row.
- **Real work — bulk cleaning:** applying type coercion, masks, and string normalisation
  to whole columns (the vectorised counterpart of 3.4/4.1).
- **Real work — batch inference prep:** building the feature matrix for predicting on
  millions of rows at once (8.10).
- **Pattern mapping (secondary):** the "operate on the whole array, not element by element"
  mindset is the core of NumPy/tensor thinking (9.1) and the array-vectorisation scenario
  (2.12) — the same shift from scalar loops to bulk operations.
[↑ Back to top](#contents)

---

<a id="3.22"></a>
## 3.22 — "DataFrame: group-by & merge" → split-apply-combine

### The situation

You have a sales DataFrame and need two classic things:

```python
import pandas as pd
sales = pd.DataFrame({
    "region":  ["n", "s", "n", "w", "s"],
    "product": ["A", "A", "B", "A", "B"],
    "amount":  [10, 7, 15, 3, 2],
})
```

1. **Aggregate per group:** total and average `amount` per region — and per
   (region, product). In plain Python you'd reach for `defaultdict` (3.15); in pandas
   there's a dedicated, faster idiom.
2. **Combine with another table:** attach each product's category from a separate
   `products` table — the join from 3.16, but on DataFrames.

Doing either with row loops (3.21) is slow and verbose; pandas has first-class,
vectorised operations for both.

### What's really going on

**Group-by** is the **split-apply-combine** pattern: *split* the rows into groups by a
key, *apply* an aggregation to each group, *combine* the results into a new table. It's
the DataFrame version of 3.15's `defaultdict` grouping plus 3.14's per-group counting,
but vectorised in C and expressed in one chained call.

**Merge** is a relational **join** (3.16) on one or more key columns — pandas builds the
hash index and matches rows for you, with explicit control over join type (inner/left/
right/outer) and what happens to unmatched rows.

Both are the workhorses of tabular analysis; thinking in "split-apply-combine" and "join
on keys" is the pandas equivalent of the pure-Python grouping/joining moves you already
know.

### The move

Use **`groupby(...).agg(...)`** for split-apply-combine aggregation and **`merge(...)`**
for key-based joins — both vectorised, with explicit join type and validation:

```python
summary = sales.groupby("region")["amount"].agg(["sum", "mean"])
joined  = sales.merge(products, on="product", how="left", validate="many_to_one")
```

### The code, every line explained

```python
import pandas as pd

# --- GROUP-BY: split-apply-combine ---------------------------------------
by_region = sales.groupby("region")["amount"].sum()   # split by region, sum amount
# -> a Series indexed by region: n=25, s=9, w=3. (split -> apply sum -> combine)
avg = sales.groupby("region")["amount"].mean()         # mean per region instead

# multiple aggregations at once with .agg --------------------------------
summary = sales.groupby("region")["amount"].agg(["sum", "mean", "count"])
# -> a DataFrame: one row per region, columns sum/mean/count.

# group by MULTIPLE keys -> a MultiIndex (the tuple-key idea, 3.18) -------
cross = sales.groupby(["region", "product"])["amount"].sum()
# -> indexed by (region, product) pairs: (n,A)=10, (n,B)=15, (s,A)=7, ...
cross = cross.reset_index()                # flatten the MultiIndex back into columns

# named aggregations (clear output column names) -------------------------
report = sales.groupby("region").agg(
    total=("amount", "sum"),               # new col "total" = sum of "amount"
    avg=("amount", "mean"),
    n=("amount", "size"),                  # group size (row count)
).reset_index()

# transform: per-group value broadcast BACK to every row (not collapsed) --
sales["region_total"] = sales.groupby("region")["amount"].transform("sum")
# each row gets ITS region's total (25 for n-rows) — useful for shares: amount/region_total.

# --- MERGE: join two DataFrames on a key (3.16, vectorised) -------------
products = pd.DataFrame({"product": ["A", "B"], "category": ["food", "tool"]})
joined = sales.merge(products, on="product", how="left")
#                                  │           └ join type: keep ALL sales rows...
#                                  └ the key column present in BOTH frames
# how="inner": only matched rows; "left": all left rows (NaN where no match);
# "right"/"outer": symmetric variants. Default is "inner".

# merge on DIFFERENTLY-NAMED keys ----------------------------------------
joined = sales.merge(products, left_on="product", right_on="product", how="left")

# detect merge problems with the indicator + validate --------------------
chk = sales.merge(products, on="product", how="left", indicator=True)
print(chk["_merge"].value_counts())        # both / left_only / right_only — find non-matches
joined = sales.merge(products, on="product", how="left", validate="many_to_one")
# validate= raises if the key relationship isn't as you assert (e.g. unexpected dup keys,
# which would otherwise FAN OUT rows silently — a classic merge bug).
```

> Note: these pandas examples are written to be idiomatically correct but were **not
> executed** here (pandas isn't installed). The named-aggregation, `transform`, and
> `merge(..., validate=, indicator=)` APIs are standard in pandas ≥1.x.

### Why it works

`groupby` partitions the rows by the key (using hashing, like `defaultdict`), then runs
each aggregation in vectorised C over each group's values, and assembles the results into
a new indexed structure — the whole split-apply-combine in one pass, far faster than a
Python loop. `transform` is the variant that returns a result *aligned to the original
rows* (same length) instead of one row per group, so you can write per-group values back
as a column. `merge` builds a hash table on the key (the hash join of 3.16) and matches
rows in bulk, with `how=` choosing the unmatched-row policy and `validate=` guarding the
key cardinality that, if wrong, silently multiplies rows.

### Impact

- **Speed & brevity:** vectorised group-by and merge replace slow `defaultdict`/dict-join
  loops over large frames with one expression each.
- **Expressiveness:** `.agg`/named aggregations compute several summaries per group at
  once; `transform` cleanly produces per-group-relative features (shares, deviations).
- **Safety:** `indicator`/`validate` surface the unmatched-rows and duplicate-key
  problems that otherwise corrupt a merge silently.

### Pros & cons / when NOT to

**Reach for groupby/merge when:** aggregating tabular data by key(s) or combining tables
on shared columns — the bread and butter of analysis.

**Watch out / when NOT to:**
- **Merge row fan-out:** if the "one" side actually has duplicate keys, a `left` merge
  *multiplies* rows (every left row matches several right rows). Assert with
  `validate="many_to_one"` (or dedup the right side, 3.13) — this is the most common
  silent merge bug.
- **`groupby` drops NaN keys by default** — rows whose group key is NaN vanish from the
  result. Pass `dropna=False` if missing keys form a meaningful group.
- **`.apply` on groups can be slow** — prefer built-in agg functions (`sum`, `mean`,
  `size`) or named aggregations; reserve `.apply(custom_fn)` for genuinely custom logic.
- **Pure-Python / streaming data → `defaultdict`+`Counter`** (3.15/3.14) and dict join
  (3.16) — pandas earns its keep on columnar in-memory tables, not row-at-a-time streams.
- **Bigger than RAM → Polars/DuckDB/Spark** keep group-by/join but scale out (6.12).

### Where this shows up

- **Real work — aggregate features & reports:** per-user/per-region/per-day summaries
  (sum, mean, count, distinct) as model features or dashboard rows.
- **Real work — assembling training tables:** merging fact tables with dimension/lookup
  tables to enrich features (the DataFrame form of 3.16), with validation to avoid fan-out.
- **Real work — per-group normalisation:** `transform` to compute group-relative features
  (a row's share of its group, deviation from group mean) — common in feature engineering.
- **Pattern mapping (secondary):** split-apply-combine is grouping (3.15) + aggregation;
  merge is the hash join (3.16, 11.1) — pandas is the vectorised, large-scale expression
  of those same two moves.
[↑ Back to top](#contents)

---

<a id="3.23"></a>
## 3.23 — "Handle NaN/missing in arrays & frames" → fillna/dropna/masks

### The situation

You load a feature table and the missing values from 3.5 are now sitting in a DataFrame
as **`NaN`**:

```python
import pandas as pd, numpy as np
df = pd.DataFrame({
    "age":    [30.0, np.nan, 25.0, np.nan],
    "income": [50.0, 60.0, np.nan, 40.0],
    "city":   ["DE", None, "FR", "IN"],
})
```

Then things break in confusing ways. `df["age"].mean()` quietly *ignores* the NaNs (sometimes
what you want, sometimes a hidden bias). `df["age"] == np.nan` returns **all False** — even
for the rows that *are* NaN — so your "find the missing rows" filter finds nothing. And a
model fit on this raises "Input contains NaN". "Handle NaN" concretely means: **detect** it
correctly, then either **drop** the affected rows/columns or **fill** (impute) them with a
chosen value — deliberately, because the choice changes your results.

### What's really going on

**`NaN`** ("Not a Number") is a special floating-point value pandas/NumPy use to mark
**missing** numeric data. Its defining, surprising property: **`NaN` is not equal to
anything, including itself** (`np.nan == np.nan` is `False`). That's why `== np.nan` never
works — you must test with `.isna()`/`.notna()` (or `np.isnan`), which check the *missing*
flag directly.

Once you can *detect* missing, you choose a *policy*:

- **drop** — remove rows (or columns) that contain missing values (`dropna`). Simple, but
  throws away data and can bias the result if missingness isn't random.
- **fill / impute** — replace missing with a value (`fillna`): a constant, the column
  mean/median, forward-fill from the previous row, etc. Keeps all rows but invents values.

There's no universally correct choice — it's a modelling decision (which is why 3.5 flagged
imputation as deliberate). The skill is doing it *explicitly and consistently*.

### The move

Detect missing with **`.isna()`** (never `== np.nan`), then choose a policy: **`dropna`**
to remove affected rows/columns, or **`fillna`** to impute a chosen value:

```python
df["age"].isna().sum()                        # count missing (== np.nan is always False!)
df = df.fillna({"age": df["age"].median(), "city": "unknown"})   # per-column policy
```

### The code, every line explained

```python
import pandas as pd, numpy as np

# --- DETECT: never use == np.nan; use .isna()/.notna() -------------------
df["age"].isna()                 # boolean Series: True where age is NaN
df.isna().sum()                  # count of NaN per column (the missingness check, 3.12)
missing_rows = df[df["age"].isna()]      # FILTER to the missing rows (mask, 3.21)
# df["age"] == np.nan -> ALL False (NaN != NaN). This is the trap; .isna() is the fix.

# --- DROP: remove rows/cols with missing values --------------------------
df.dropna()                      # drop any ROW containing ANY NaN (here: rows 1,2,3 go)
df.dropna(subset=["age"])        # drop rows where SPECIFICALLY age is NaN
df.dropna(axis=1)                # drop any COLUMN containing a NaN (axis=1 = columns)
df.dropna(thresh=2)              # keep rows with at least 2 non-NaN values
# dropna returns a NEW frame; reassign (df = df.dropna(...)) or pass inplace=True.

# --- FILL / impute: replace missing with a chosen value ------------------
df["age"].fillna(0)                          # constant
df["age"].fillna(df["age"].mean())           # column MEAN (ignores NaN automatically)
df["age"].fillna(df["age"].median())         # median — robust to outliers (often better)
df["city"].fillna("unknown")                 # categorical -> a sentinel category
df["income"].ffill()                         # forward-fill: carry last valid value down
df["income"].bfill()                         # back-fill: use the next valid value
# fill the WHOLE frame per-column with a dict of policies:
df = df.fillna({"age": df["age"].median(), "income": 0, "city": "unknown"})

# --- aggregations and NaN: know the default ------------------------------
df["age"].mean()                 # SKIPS NaN by default (mean of [30,25] = 27.5, not /4)
df["age"].sum(min_count=1)       # use min_count to force NaN if too few valid values
df["age"].mean(skipna=False)     # force NaN-aware: result is NaN if any value is NaN
# Knowing "agg silently skips NaN" prevents the hidden-bias bug: a 50%-missing column's
# "mean" is the mean of the half that's present — which may not represent the column.

# --- NumPy arrays: the same NaN rules ------------------------------------
a = np.array([1.0, np.nan, 3.0])
a == np.nan                      # array([False, False, False]) — same trap
np.isnan(a)                      # array([False,  True, False]) — the correct detector
a.mean()                         # nan — NumPy mean is NOT NaN-skipping by default!
np.nanmean(a)                    # 2.0 — use the nan* functions to skip NaN in NumPy
# CONTRAST: pandas aggregations skip NaN by default; raw NumPy ones do NOT. Don't mix
# up the two — np.array([1,nan]).mean() is nan, but pd.Series([1,nan]).mean() is 1.0.

# --- pandas <NA> / nullable dtypes (brief) -------------------------------
# Newer pandas has nullable Int64/boolean dtypes using pd.NA (so ints can be "missing"
# without becoming floats). Behaviour is similar; isna()/fillna() still apply.
```

> Note: these pandas/NumPy examples are written to be idiomatically correct but were
> **not executed** here (pandas/NumPy aren't installed). The behaviours described —
> `NaN != NaN`, pandas aggregations skipping NaN while raw NumPy `.mean()` does not, and
> the `isna`/`dropna`/`fillna`/`ffill` APIs — are standard and well-established.

### Why it works

`isna()`/`np.isnan` test the *missing* status directly rather than relying on equality,
sidestepping the `NaN != NaN` rule that makes `== np.nan` useless. `dropna` and `fillna`
then implement the two policies as vectorised operations over whole columns. Knowing the
aggregation defaults (pandas skips NaN; raw NumPy doesn't) lets you predict what a mean or
sum actually computed — and decide whether silently-skipped missingness is acceptable or a
bias you must address by imputing first.

### Impact

- **Correctness:** detecting missing with `.isna()` fixes the "filter finds zero missing
  rows" bug, and knowing the skip-NaN aggregation default prevents silently biased
  statistics.
- **Model-ready data:** explicit drop/fill removes the NaNs that crash model fitting, with
  a recorded, intentional policy rather than an accidental one.
- **Consistency:** a per-column fill dict applies the same imputation everywhere, so train
  and serve use identical handling (ties to train/serve skew, 8.16).

### Pros & cons / when NOT to

**Reach for this when:** any numeric/tabular data with missing values heads toward
analysis or a model.

**Watch out / when NOT to:**
- **Never `== np.nan`** — it's always False. Use `.isna()`/`.notna()`/`np.isnan`.
- **`dropna` can bias your data.** If missingness correlates with the target (e.g. failed
  sensors during outages), dropping those rows skews the dataset. Check *why* values are
  missing before dropping.
- **Mean/median imputation leaks if fit on the whole dataset.** Compute the fill value on
  the **training set only**, then apply it to validation/test — otherwise you leak test
  information into training (8.1, 8.12). Use scikit-learn's `SimpleImputer` inside a
  Pipeline to enforce this.
- **pandas vs NumPy aggregation defaults differ** (skip vs not). Don't assume; use
  `np.nanmean`/`skipna=` explicitly when it matters.
- **A "missing" indicator can be a feature.** Sometimes *that a value is missing* is
  predictive — add a boolean `age_was_missing` column before filling.

### Where this shows up

- **Real work — preprocessing before modelling:** the impute/drop step that turns a raw
  feature table into something a model can fit, done train-only to avoid leakage (8.12).
- **Real work — robust metrics over dirty data:** computing column statistics that
  correctly account for (rather than silently skip) missingness during the dataset audit
  (3.12).
- **Real work — time-series gaps:** `ffill`/`bfill`/interpolation to fill missing readings
  in sensor or financial series before feature extraction.
- **Pattern mapping (secondary):** boolean masking with `isna()` is the same mask-and-
  select pattern as 3.21; the "missing as a distinct state" idea is the array/DataFrame
  form of the absent/null/empty trichotomy from 3.5.
[↑ Back to top](#contents)

---

<a id="3.24"></a>
## 3.24 — "Reshape: pivot / explode lists into rows" → wide↔long

### The situation

Two reshaping needs that come up constantly.

**Need 1 — long ↔ wide.** Your measurements are stored **long** (one row per
observation), but the report (or model) wants them **wide** (one row per entity, one
column per metric):

```python
import pandas as pd
long = pd.DataFrame({                       # LONG: one row per (date, metric)
    "date":   ["d1", "d1", "d2", "d2"],
    "metric": ["temp", "humid", "temp", "humid"],
    "value":  [19.0, 55, 21.0, 60],
})
# want WIDE:  date | temp | humid
#             d1   | 19.0 | 55
#             d2   | 21.0 | 60
```

**Need 2 — explode a list column into rows.** One record holds a *list* in a field, and
you want one row per list element:

```python
orders = pd.DataFrame({
    "order_id": ["o1", "o2"],
    "items":    [["A", "B", "C"], ["D"]],   # a LIST inside each cell
})
# want one row per item: (o1,A),(o1,B),(o1,C),(o2,D)
```

Doing either by hand — nested loops building new rows — is fiddly and slow. pandas has
direct operations: `pivot`/`melt` for wide↔long, and `explode` for list→rows.

### What's really going on

This is **reshaping**: changing the *layout* of the same data, not its content.

- **Long (tidy) format** has one row per observation, with the variable name in one
  column and its value in another — easy to aggregate, filter, and store, and the natural
  output of group-bys.
- **Wide format** spreads one categorical column out into multiple columns — what humans
  read in tables and what many models expect as a feature matrix.

`pivot` goes **long → wide** (spread a column's values into new columns); `melt` goes
**wide → long** (gather columns back into rows). They're inverses. `explode` is a
different reshape: it takes a column whose cells contain lists and **unnests** each list
into separate rows, duplicating the other fields — turning a one-row-many-items record
into many one-item rows (the DataFrame analogue of flattening, and the inverse of a
group-into-list, 3.15).

### The move

Reach for the dedicated reshape ops: **`pivot`/`pivot_table`** (long→wide), **`melt`**
(wide→long), and **`explode`** (a list-valued column → one row per element):

```python
wide = long.pivot(index="date", columns="metric", values="value")
flat = orders.explode("items")                # one row per list element
```

### The code, every line explained

```python
import pandas as pd

# --- LONG -> WIDE: pivot (spread a column into multiple columns) ---------
wide = long.pivot(index="date", columns="metric", values="value")
#                  │              │                └ cell values come from here
#                  │              └ each distinct value becomes a NEW COLUMN (temp, humid)
#                  └ one row per distinct date (the row index)
# wide:  date as index, columns temp/humid. .reset_index() to make date a column again.
wide = wide.reset_index()

# pivot_table when there can be DUPLICATE index/column pairs (needs aggregation) --
wt = long.pivot_table(index="date", columns="metric", values="value", aggfunc="mean")
# plain pivot RAISES if (date, metric) isn't unique; pivot_table aggregates duplicates
# (here, averages them). Use pivot_table whenever collisions are possible.

# --- WIDE -> LONG: melt (gather columns into rows) -----------------------
back = wide.melt(id_vars="date",            # column(s) to KEEP as identifiers
                 var_name="metric",          # name for the new "which column" column
                 value_name="value")         # name for the new value column
# back is the original long shape again — melt is the inverse of pivot.

# --- EXPLODE: a list-valued column -> one row per element ----------------
flat = orders.explode("items")              # each list element becomes its own row
# flat: (o1,A),(o1,B),(o1,C),(o2,D) — order_id is REPEATED for each item.
flat = flat.reset_index(drop=True)          # tidy the index after exploding
# Empty lists / NaN in the column produce a single row with NaN (control via ignore_index).

# --- the inverse of explode: group list back up (3.15 in pandas) ---------
regrouped = flat.groupby("order_id")["items"].agg(list).reset_index()
# -> back to one row per order with a list of items. groupby+agg(list) re-nests.

# --- exploding a column of DICTS / JSON -> columns (json_normalize) ------
nested = pd.DataFrame({"id": [1], "geo": [{"lat": 52.5, "lon": 13.4}]})
expanded = pd.json_normalize(nested["geo"])  # dict keys -> columns: lat | lon
# For deeply nested JSON, pd.json_normalize(records, record_path=..., meta=...) flattens
# it into a tabular frame (the DataFrame counterpart of walking nested JSON, 3.3).

# --- pure-Python explode (no pandas), for streaming records --------------
flat_rows = [
    {"order_id": o["order_id"], "item": item}   # one new dict per item
    for o in records
    for item in o["items"]                       # nested comprehension = explode (1.1)
]
```

> Note: these pandas examples are written to be idiomatically correct but were **not
> executed** here (pandas isn't installed). The `pivot`, `pivot_table`, `melt`, `explode`,
> and `json_normalize` APIs are standard pandas; `pivot` raising on duplicate index/column
> pairs (vs `pivot_table` aggregating them) is the key behavioural distinction to remember.

### Why it works

`pivot` reads the `columns=` field's distinct values and creates one output column per
value, placing each `values=` cell at the (index, column) intersection — a vectorised
scatter. `melt` does the reverse gather. They preserve all the data; only its arrangement
changes. `explode` walks each list cell and emits one row per element while *broadcasting*
the row's other fields to each new row — the unnesting operation — which is exactly the
nested-comprehension flatten (`for o ... for item in o["items"]`) done in C over the
whole column.

### Impact

- **Right shape for the consumer:** long for storage/aggregation/tidy analysis, wide for
  human reports and many model inputs — reshaping bridges the two without re-deriving the
  data.
- **Brevity & speed:** one `pivot`/`melt`/`explode` call replaces a hand-rolled
  row-building loop and runs vectorised.
- **Unnests nested data:** `explode`/`json_normalize` flatten list- and dict-valued cells
  into a clean tabular frame ready for analysis.

### Pros & cons / when NOT to

**Reach for reshaping when:** the data's layout doesn't match what the next step expects —
long↔wide conversions, or unnesting list/dict columns into rows/columns.

**Watch out / when NOT to:**
- **`pivot` raises on duplicate (index, columns) pairs** — use `pivot_table` with an
  `aggfunc` when collisions are possible (it aggregates; `pivot` only reshapes unique
  cells).
- **`explode` multiplies rows** — a record with a 100-element list becomes 100 rows;
  exploding several columns or large lists can blow up row counts (and memory) fast.
- **Wide format with many distinct categories → an explosion of columns** (e.g. pivoting
  on a high-cardinality id creates thousands of sparse columns). Keep wide for
  low-cardinality categoricals.
- **Tidy/long is usually the better *storage* format**; reshape to wide as a final
  presentation/modelling step, not as how you persist data (ties to format choice, 3.11).
- **Pure-Python / streaming → nested comprehensions** (1.1) explode records without pandas.

### Where this shows up

- **Real work — building feature matrices:** pivoting long event/measurement logs into a
  one-row-per-entity wide table that a model consumes (e.g. per-user metric columns).
- **Real work — unnesting multi-value fields:** `explode` to turn an order's item list,
  a document's tag list, or a user's session events into one-row-per-element for analysis.
- **Real work — flattening API/JSON dumps:** `json_normalize` to turn nested API responses
  into a flat analytical table (the bulk counterpart of 3.3's per-record walking).
- **Pattern mapping (secondary):** `explode` is the flatten/unnest operation (nested-loop
  comprehension, 1.1); pivot/melt are the tabular form of transpose/regroup — the same
  "rearrange without changing content" idea as `zip(*rows)` transposition (1.5).

[↑ Back to top](#contents)

