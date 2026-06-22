# Area 4 — Text & Content Processing

Text is the messiest data you handle: the same word arrives in three cases, five
whitespace variants, and two Unicode encodings — and you still need to compare, extract,
deduplicate, chunk, and search it reliably. These are the moves for turning raw,
inconsistent text into something a program can trust. Bias throughout: data/NLP/data-
engineering work, but these are general text skills, not LLM-only tricks.

---

<a id="contents"></a>
## Contents

- [4.1 — "Messy text: whitespace, case, unicode" → normalisation](#4.1)
- [4.2 — "Extract structured info from text" → regex essentials](#4.2)
- [4.3 — "Match/replace patterns at scale" → compiled regex & groups](#4.3)
- [4.4 — "Stable IDs / cache keys from content" → hashing (hashlib)](#4.4)
- [4.5 — "Detect near-duplicate text" → normalisation keys & shingling](#4.5)
- [4.6 — "Fuzzy similarity between strings" → edit distance / ratio](#4.6)
- [4.7 — "Extract text from HTML/markdown" → parsing vs regex](#4.7)
- [4.8 — "Split text into chunks (chars/sentences/tokens)" → chunking](#4.8)
- [4.9 — "Build strings/templates safely" → join, templates, escaping](#4.9)
- [4.10 — "Search within large text efficiently" → find/in vs regex vs index](#4.10)

---


<a id="4.1"></a>
## 4.1 — "Messy text: whitespace, case, unicode" → normalisation

### The situation

You're deduplicating a column of company names scraped from three different sources.
These four strings all refer to the *same* company, but every one is byte-for-byte
different:

```python
names = [
    "  Café  Corp ",        # leading/trailing spaces, double space in the middle
    "CAFÉ CORP",            # all caps
    "Café Corp",            # the "é" is a single Unicode character: U+00E9
    "Café Corp",            # the "é" is TWO characters: "e" + a combining accent (U+0065 U+0301)
]
```

The last two look identical on screen but are **not equal** in Python:

```python
print(names[2] == names[3])     # False (!) — same glyphs, different byte sequences
print(len(names[2]), len(names[3]))   # 8 9  — one has an extra "hidden" character
```

If you build a `set(names)` to find unique companies, you get **four** entries when the
true answer is **one**. Every downstream count, join, and group-by is now wrong.

### What's really going on

"Equal text" to a human and "equal text" to a computer are different things. A computer
compares strings **code point by code point** (a *code point* is the numeric ID Unicode
assigns to each character — `é` is U+00E9). Two strings match only if every code point is
identical. Human-equal strings differ in ways the bytes don't forgive:

- **Whitespace** — leading/trailing spaces, tabs, double spaces, newlines.
- **Case** — `CORP` vs `corp`.
- **Unicode composition** — `é` can be stored as **one** pre-composed code point (U+00E9)
  *or* as a plain `e` **plus** a separate "combining accent" code point (U+0301). Both
  render as "é"; neither equals the other byte-wise. This is the sneakiest one because the
  difference is invisible.

The fix is **normalisation**: pushing every variant through the *same* set of
transformations so that human-equal strings become byte-equal. You pick one canonical
form and force everything into it before you ever compare.

### The move

Build a small **normalise** function that applies a fixed pipeline — Unicode-normalise,
strip, collapse internal whitespace, lower-case — and run *every* string through it before
comparing, deduping, or using it as a key:

```python
import unicodedata, re

def normalise(s):
    s = unicodedata.normalize("NFC", s)   # unify the two "é" representations
    s = s.strip()                          # drop leading/trailing whitespace
    s = re.sub(r"\s+", " ", s)             # collapse any run of whitespace to one space
    return s.casefold()                    # aggressive lower-casing for comparison
```

### Why it works

Each step removes one *axis* of meaningless variation:

- **`unicodedata.normalize("NFC", s)`** rewrites the string into a canonical Unicode form,
  so the two-code-point `é` and the one-code-point `é` both become the **same** single
  code point. After this, byte-equality matches human-equality on accented text.
- **`.strip()`** removes the leading/trailing whitespace that carries no meaning.
- **`re.sub(r"\s+", " ", s)`** replaces every run of whitespace (spaces, tabs, newlines)
  with a single space, so `"Café  Corp"` and `"Café Corp"` converge.
- **`.casefold()`** lower-cases *aggressively* for comparison (more thorough than
  `.lower()` — it also handles non-English cases like German `ß` → `ss`).

Run all four messy names through this and they collapse to the **single** string
`"café corp"` — so `set` correctly reports one unique company.

### The code, every line explained

```python
import unicodedata          # standard library: Unicode metadata + normalisation
import re                   # regular expressions — used here just to collapse whitespace

def normalise(s):
    # Unicode normalisation: pick a canonical form so "the same" text is byte-identical.
    # "NFC" = Normalization Form C = "composed": prefer single pre-composed characters
    # (e + combining-accent  ->  é). This is the right default for storage/comparison.
    s = unicodedata.normalize("NFC", s)

    s = s.strip()           # remove leading/trailing whitespace (spaces, tabs, newlines)

    # \s = any whitespace char; + = "one or more". Replace any run with a single space,
    # so "Café   Corp\t" -> "Café Corp". (Regex is covered fully in 4.2.)
    s = re.sub(r"\s+", " ", s)

    # casefold() = case-insensitive lower-casing for COMPARISON. Stronger than lower():
    # "STRASSE".casefold() == "straße".casefold()  (handles ß -> ss). Use for matching;
    # use .lower() if you need to DISPLAY normal lower-case text.
    return s.casefold()

names = ["  Café  Corp ", "CAFÉ CORP", "Café Corp", "Café Corp"]
#                                                     └ "Cafe" + U+0301 combining accent
unique = {normalise(n) for n in names}   # set comprehension over the normalised forms
print(unique)                            # {'café corp'}  — exactly ONE, as intended

# --- NFC vs NFD: composed vs decomposed ----------------------------------
a = "é"                       # could be either form depending on the source
print(len(unicodedata.normalize("NFC", a)))   # 1  — composed: one code point
print(len(unicodedata.normalize("NFD", a)))   # 2  — decomposed: e + combining accent
# NFC for storage/comparison (compact). NFD is occasionally useful when you want to
# STRIP accents: decompose, then drop the combining marks (shown next).

# --- Stripping accents entirely (e.g. "café" -> "cafe") ------------------
def strip_accents(s):
    decomposed = unicodedata.normalize("NFD", s)        # split é -> e + accent
    # category(ch) == "Mn" means "Mark, nonspacing" — i.e. a combining accent.
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
print(strip_accents("Café Corp"))    # "Cafe Corp"  — accents removed
```

### Impact

- **Correctness:** dedup, group-by, joins, and `set`/`dict` keys become reliable —
  human-equal text now compares equal, so counts and matches stop being silently wrong.
- **Fewer "impossible" bugs:** the invisible composed/decomposed `é` bug is one of the
  hardest to spot by eye; normalising up front makes it disappear before it confuses you.
- **One place to reason about:** all the messy-text rules live in one function, so the
  rest of your code can assume clean, canonical strings.

### Pros & cons / when NOT to

**Reach for a normalise step when:** text comes from multiple/unknown sources and you'll
**compare, dedupe, group, or key** on it — names, emails, tags, search terms, join keys.

**Watch out / when NOT to:**
- **Don't normalise away meaning you need.** Case can matter (`pH` vs `PH`, code
  identifiers, passwords — *never* casefold a password). Whitespace can matter (indentation
  in code, formatting in a document you must reproduce). Normalise a **comparison copy**,
  keep the original for display/storage.
- **`casefold()` is for matching, not display.** Show users their original text; use the
  normalised form only as the internal key.
- **NFC vs NFKC:** `NFKC` also folds "compatibility" characters (e.g. the ligature `ﬁ` →
  `fi`, full-width `Ａ` → `A`). Great for aggressive search matching, but it *changes
  visible characters*, so don't use it where exact reproduction matters.
- **Locale edge cases:** Turkish dotted/dotless "i" can surprise case-folding; if you
  process one specific language deeply, check its rules.

### Where this shows up

- **Real work — entity/record deduplication:** cleaning a names/addresses/SKU column
  before a join or `groupby` — normalising is the step that makes "the same thing written
  differently" actually merge.
- **Real work — search & lookup keys:** normalising a query and the indexed text the same
  way so "Café" finds "cafe" — the foundation under search and autocomplete.
- **Real work — NLP preprocessing:** the first stage of almost any text pipeline
  (tokenisation, embeddings, classification) is normalising whitespace/case/Unicode so the
  model sees consistent input.
- **Pattern mapping (secondary):** "canonical form so equal things hash equal" is the same
  idea behind grouping anagrams (sort the letters to get a canonical key) — normalise, then
  use the normalised value as a dict/set key.
[↑ Back to top](#contents)

---

<a id="4.2"></a>
## 4.2 — "Extract structured info from text" → regex essentials

### The situation

You have a list of log lines and you need to pull the **timestamp**, **level**, and
**numeric latency** out of each one so you can analyse slow requests:

```python
line = "2026-06-18 14:03:21 ERROR request_id=abc123 latency=842ms path=/api/predict"
```

You want, from that one line:

```python
{"date": "2026-06-18", "level": "ERROR", "latency_ms": 842}
```

You *could* attack it with `.split()` and slicing — split on spaces, hope the fields are
always in the same position, hand-chop `"842ms"` to drop the `ms`. But the moment a log
line has an extra space, a missing field, or a slightly different order, your positional
slicing grabs the wrong thing and you get silent garbage.

### What's really going on

You're trying to **find and extract pieces of text that match a pattern**, not a fixed
position. The shape "a date, then a word in capitals, then `latency=` followed by digits"
is a *pattern*, and Python has a dedicated tool for describing and matching patterns: the
**regular expression** (regex).

A **regex** is a small language for describing the *shape* of text — "some digits", "a
word", "an `@` with text on both sides". You write the shape once, and the regex engine
finds every place in the text that matches it. The key extra power is the **capture
group**: parentheses `( )` around part of the pattern tell the engine "remember exactly
what matched *here*", so you can pull that piece out separately.

### The move

Write a regex with **capture groups** around the parts you want, then use `re.search` to
find it and `.group(n)` (or named groups) to extract each piece:

```python
import re

m = re.search(
    r"(\d{4}-\d{2}-\d{2})\s+(\w+)\b.*?latency=(\d+)ms",
    line,
)
if m:
    date, level, latency = m.group(1), m.group(2), int(m.group(3))
```

### Why it works

Each token in the pattern describes one shape, and each `( )` captures a slice:

- **`\d`** matches a single digit; **`\d{4}`** means "exactly four digits". So
  `\d{4}-\d{2}-\d{2}` matches `2026-06-18`.
- **`\s+`** matches one or more whitespace characters (the gap between fields).
- **`\w+`** matches one or more "word characters" (letters, digits, underscore) — it grabs
  the level word `ERROR`. **`\b`** is a *word boundary*: a zero-width marker between a word
  char and a non-word char, so the match ends cleanly at the word's edge.
- **`.*?`** matches "any characters, as few as possible" — the lazy wildcard that skips
  over the middle (`request_id=abc123 `) without overshooting.
- **`(\d+)ms`** captures the run of digits *before* the literal `ms`, so you get `842`, not
  `842ms`.

`re.search` scans the whole string for the **first** place the pattern matches and returns
a **match object** (or `None` if nothing matched). `.group(1)` returns what the **first**
parenthesised group captured, `.group(2)` the second, and so on. Because you matched by
*shape*, a stray extra space (`\s+` absorbs it) or reordered tail no longer breaks you.

### The code, every line explained

```python
import re

line = "2026-06-18 14:03:21 ERROR request_id=abc123 latency=842ms path=/api/predict"

# r"..."  = a RAW string: backslashes are passed through literally to the regex engine
#           instead of being treated as Python escapes. ALWAYS write regexes as r"...".
pattern = r"(\d{4}-\d{2}-\d{2})\s+(\w+)\b.*?latency=(\d+)ms"
#           └──────┬──────────┘    └┬┘            └─┬─┘
#           group 1: the date    group 2: level   group 3: digits before "ms"
#  \d  = one digit (0-9)            \w = word char [A-Za-z0-9_]
#  {4} = exactly 4 of the previous  \s = whitespace      + = one or more
#  .*? = any chars, as FEW as possible (lazy) -> skip the middle without overshooting

m = re.search(pattern, line)   # scan the string; return a Match object, or None
if m:                          # ALWAYS check: re.search returns None on no match,
                               # and None.group(...) would raise AttributeError
    date    = m.group(1)       # "2026-06-18"  — what group 1 captured
    level   = m.group(2)       # "ERROR"
    latency = int(m.group(3))  # 842           — convert the captured digit-text to int
    print(date, level, latency)

# --- NAMED groups: (?P<name>...) so you read by name, not by number -----
pattern = r"(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<level>\w+)\b.*?latency=(?P<ms>\d+)ms"
m = re.search(pattern, line)
print(m.group("date"), m.group("level"))   # read by NAME — clearer, reorder-safe
print(m.groupdict())   # {'date': '2026-06-18', 'level': 'ERROR', 'ms': '842'} — a dict!

# --- A regex character-class cheat-sheet (the pieces you'll actually use) ---
# .      any single character (except newline)
# \d \D  a digit / a NON-digit
# \w \W  a word char [A-Za-z0-9_] / a NON-word char
# \s \S  whitespace / NON-whitespace
# [abc]  exactly one of a, b, or c    [^abc] one char that is NOT a/b/c
# [a-z]  one char in the range a..z    a|b   a OR b (alternation)
# ?      0 or 1     *  0 or more     +  1 or more    {2,5} between 2 and 5
# ^ $    start / end of the string (or line, with re.MULTILINE)
# ( )    CAPTURE group     (?: )  group WITHOUT capturing     \b word boundary

# --- A common real extraction: pull all emails out of a blob ------------
text = "ping alice@acme.io or bob_99@data.co.uk, not 'foo@'"
emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)   # findall -> list of matches
print(emails)        # ['alice@acme.io', 'bob_99@data.co.uk']
# [\w.+-]+ = the local part (letters/digits/dot/plus/dash), @, domain, dot, TLD.
# NOTE: this is a PRACTICAL email matcher, not a fully RFC-correct one (those are huge).
```

### Impact

- **Robustness:** matching by *shape* survives extra whitespace, reordered tails, and
  optional fields that positional splitting silently mishandles.
- **Extraction in one shot:** capture groups pull several fields out of one pattern in a
  single pass, with `.groupdict()` handing you a ready-made dict.
- **Expressiveness:** a one-line pattern replaces a tangle of `split`/`find`/slice logic
  that's hard to read and easy to get subtly wrong.

### Pros & cons / when NOT to

**Reach for regex when:** you extract or validate text with a clear *shape* — dates, IDs,
key=value pairs, phone/email-like tokens, log fields, simple delimited formats.

**Watch out / when NOT to:**
- **Don't parse nested/recursive formats with regex** — HTML, JSON, source code, anything
  with arbitrary nesting. Regex can't reliably handle "balanced brackets". Use a real
  parser (see 4.7 for HTML). The famous warning "now you have two problems" is about
  exactly this misuse.
- **`re.search` returns `None` on no match** — always guard with `if m:` before calling
  `.group`, or you'll hit `AttributeError: 'NoneType' object has no attribute 'group'`.
- **Greedy vs lazy bites people:** `.*` is *greedy* (matches as much as possible) and will
  overshoot past the first `ms`; `.*?` is *lazy* (as little as possible). Reach for lazy
  when matching "up to the next delimiter".
- **Readability:** a dense regex is write-once, read-never. Use **named groups**, and for
  anything non-trivial use **verbose mode** (`re.VERBOSE`) to write the pattern across
  multiple commented lines.

### Where this shows up

- **Real work — log/trace parsing:** extracting timestamps, levels, latencies, status
  codes from log lines for monitoring or analysis — exactly the example above.
- **Real work — data cleaning:** pulling numbers out of "842ms"/"$1,299"/"12 kg" strings,
  or validating that an ID/email/phone column matches an expected shape before a join.
- **Real work — NLP preprocessing:** finding URLs, mentions, hashtags, or sentence
  boundaries to strip or tokenise before feeding text to a model.
- **Pattern mapping (secondary):** regex engines are finite-state machines under the hood;
  the "match a shape, capture pieces" mindset maps to string-scanning interview problems
  (validating number formats, tokenising expressions) — though those are usually solved by
  hand to show the underlying logic.
[↑ Back to top](#contents)

---

<a id="4.3"></a>
## 4.3 — "Match/replace patterns at scale" → compiled regex & groups

### The situation

You're redacting personally-identifiable information from 5 million log lines before
shipping them to an analytics warehouse. Every line may contain emails and phone numbers
that must become `[EMAIL]` and `[PHONE]`:

```python
line = "user alice@acme.io logged in from +1-415-555-0100"
# want: "user [EMAIL] logged in from [PHONE]"
```

Your first version calls `re.sub` with the pattern as a string, inside the loop over all
5M lines:

```python
for line in lines:                               # 5,000,000 iterations
    line = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", line)
    line = re.sub(r"\+?\d[\d-]{7,}\d", "[PHONE]", line)
    ...
```

It works on a sample but feels sluggish on the full file. There are two issues: the
pattern string is **re-parsed into a regex on every single call** (10 million compilations
total), and when you want to *rewrite* matches — not just find them — you're not yet using
the full power of capture groups in the replacement.

### What's really going on

Every time you pass a *string* pattern to `re.sub`/`re.search`/`re.findall`, Python must
**compile** it — translate the pattern text into an internal matching machine — before it
can run. Python caches a handful of recent patterns, but relying on that cache is fragile,
and the lookup itself has a cost. When the same pattern is used many times, you want to
**compile it once** into a reusable pattern object and call methods on *that*.

The second realisation is about **replacement with groups**: `re.sub` can do more than
swap a fixed string in. The replacement text can **refer back to captured groups** (with
`\1`, `\2`, or `\g<name>`), or you can pass a **function** that receives each match and
returns its replacement — so you can transform, not just delete.

### The move

**Compile each pattern once** at module load with `re.compile`, then reuse the compiled
object. Use **backreferences** or a **replacement function** in `sub` to rewrite matches:

```python
import re

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")   # compiled ONCE, reused for every line
PHONE = re.compile(r"\+?\d[\d-]{7,}\d")

def redact(line):
    line = EMAIL.sub("[EMAIL]", line)   # method on the compiled object — no re-parsing
    line = PHONE.sub("[PHONE]", line)
    return line
```

### Why it works

`re.compile(pattern)` does the parsing **once** and returns a **pattern object** that holds
the pre-built matching machine. Calling `EMAIL.sub(...)`, `EMAIL.search(...)`, etc. reuses
that machine directly — no per-call compilation, no cache lookup. Over millions of calls
this removes a real, repeated cost, and it also reads better: the named constant `EMAIL`
documents intent far better than an inline pattern string.

For replacement, `sub` walks the string, and for **each** non-overlapping match it
substitutes your replacement. If the replacement is a **string**, `\1` inside it is a
**backreference** — "insert whatever group 1 captured here". If the replacement is a
**function**, `sub` calls it with the match object for every match and inserts the string
you return — letting you compute a different replacement per match (mask all but the last
digits, look up a value, etc.).

### The code, every line explained

```python
import re

# --- Compile ONCE (module level), reuse millions of times ----------------
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"\+?\d[\d-]{7,}\d")
#  \+?  an optional literal "+"   \d a digit   [\d-]{7,} 7+ of digit-or-dash

def redact(line):
    line = EMAIL.sub("[EMAIL]", line)   # .sub(replacement, text): swap every match
    line = PHONE.sub("[PHONE]", line)   # reusing the compiled object — fast
    return line

print(redact("user alice@acme.io from +1-415-555-0100"))
# "user [EMAIL] from [PHONE]"

# --- Backreferences in the replacement: reformat, don't just delete ------
# Turn "2026-06-18" (YYYY-MM-DD) into "18/06/2026" (DD/MM/YYYY) by reordering groups.
DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")     # 3 capture groups: Y, M, D
reformatted = DATE.sub(r"\3/\2/\1", "2026-06-18") # \3=day \2=month \1=year
print(reformatted)                                 # "18/06/2026"
# \1 \2 \3 in the REPLACEMENT string = "insert what group 1/2/3 captured". With named
# groups (?P<y>...), use \g<y> instead of \1.

# --- A replacement FUNCTION: compute each replacement individually -------
# Mask a card-like number, keeping only the last 4 digits: 4111111111111111 -> ****1111
CARD = re.compile(r"\b\d{13,16}\b")
def mask(match):                       # sub calls this with the Match object per match
    digits = match.group(0)            # group(0) = the ENTIRE matched text
    return "*" * (len(digits) - 4) + digits[-4:]
print(CARD.sub(mask, "card 4111111111111111 ok"))  # "card ************1111 ok"

# --- finditer: stream matches with positions (memory-cheap on big text) --
for m in EMAIL.finditer("a@x.io and b@y.io"):
    print(m.group(0), m.start(), m.end())   # each email + its character offsets
# finditer yields Match objects LAZILY (one at a time) — unlike findall which builds
# the whole list. Prefer finditer on large text or when you need positions.

# --- Useful flags, set once at compile time ------------------------------
CASE = re.compile(r"error", re.IGNORECASE)        # match Error, ERROR, error
MULTI = re.compile(r"^\d+", re.MULTILINE)         # ^ matches start of EACH line
VERBOSE = re.compile(r"""
    (\d{4}) - (\d{2}) - (\d{2})     # year - month - day, whitespace/comments ignored
""", re.VERBOSE)                                   # write complex patterns readably
```

### Impact

- **Speed:** compiling once turns N parse-and-run calls into one parse plus N runs — a
  measurable win in any loop over many strings, and it removes reliance on the internal
  cache.
- **Power:** backreferences and replacement functions let `sub` **reformat and transform**
  text (reorder date parts, mask digits, normalise units), not merely delete it.
- **Readability/reuse:** named compiled constants (`EMAIL`, `PHONE`) document what each
  pattern is and are reused across functions, instead of duplicated inline strings.

### Pros & cons / when NOT to

**Reach for `re.compile` when:** the same pattern runs many times (loops, hot paths,
reused across functions). **Reach for a replacement function** when the substitution
depends on *what* matched (masking, lookups, per-match formatting).

**Watch out / when NOT to:**
- **Compiling a one-off pattern is pointless** — used once, `re.search(r"...", s)` is fine
  and reads more directly. Compile for *reuse*, not as a reflex.
- **`sub` replaces non-overlapping matches left-to-right** — overlapping patterns won't all
  fire. If you need overlapping logic, restructure the pattern or scan with `finditer`.
- **Backreference syntax differs by context:** inside the *pattern* a backreference is
  `\1` (match "the same text again"); inside the *replacement string* `\1` means "insert
  group 1". Easy to conflate — and in replacement strings, prefer raw strings so `\1`
  isn't read as an escape.
- **Catastrophic backtracking:** patterns with nested quantifiers like `(\w+)+` can blow up
  to exponential time on certain inputs (a denial-of-service risk on untrusted text). Keep
  patterns simple; for untrusted input consider the third-party `regex` module's timeouts.

### Where this shows up

- **Real work — PII redaction / data masking:** stripping emails, phones, IDs from logs or
  datasets before sharing — compiled patterns applied across millions of records.
- **Real work — bulk text cleaning:** normalising units, reformatting dates, collapsing
  markup, or fixing a systematic typo across a whole corpus with a `sub` pass.
- **Real work — tokenising for NLP:** a compiled set of patterns splits text into
  tokens/sentences far faster than recompiling per document.
- **Pattern mapping (secondary):** "do the expensive setup once, reuse it" is the same
  principle as precomputing a lookup table before a loop — the optimisation behind many
  "preprocess, then answer queries fast" problems.
[↑ Back to top](#contents)

---

<a id="4.4"></a>
## 4.4 — "Stable IDs / cache keys from content" → hashing (hashlib)

### The situation

You run an expensive embedding service: given a chunk of text, it returns a 1,536-number
vector, and each call costs money and ~200ms. You want to **cache** the result so the same
text is never embedded twice — across runs, across machines, today and next month. You need
a **key** for the cache that is:

- the **same** every time for the **same** text,
- **different** for different text,
- short and filesystem-safe (you want to name a cache file after it).

The text itself is unusable as a key — it can be megabytes long, contain slashes and
newlines, and you can't name a file `"The quick brown fox\n...4000 chars..."`. Python's
built-in `hash()` looks tempting:

```python
key = hash("some chunk of text")     # -> e.g. 8743029174... or -33125...
```

But `hash()` is **not stable across runs**: by default Python randomises string hashing for
security, so `hash("foo")` gives a *different* number every time you start the program. Use
it as a cache key and your "cache" misses 100% of the time after a restart.

### What's really going on

You need a **content hash**: a function that maps any input to a fixed-size "fingerprint"
where the same input *always* produces the same fingerprint, and different inputs almost
never collide. A **hash** here means a *cryptographic* hash — a deterministic, fixed-length
digest of the bytes.

Two distinctions matter:

- **`hash()` (built-in)** is for in-memory dict/set lookups *within a single run*. It's
  fast but **deliberately randomised per process** and **not portable** — never persist it.
- **`hashlib` hashes (SHA-256, etc.)** are **deterministic and stable forever**, the same
  on every machine and every run. They produce a fixed-length **hex digest** (a string of
  hex characters) that's perfect as a persistent, portable key.

The other subtlety: hashing operates on **bytes**, not text. You must **encode** the string
to bytes (almost always UTF-8) first, so that the *same* text always becomes the *same*
bytes before hashing.

### The move

Use **`hashlib.sha256`** on the UTF-8-encoded text and take the **hex digest** as your
stable key:

```python
import hashlib

def content_key(text):
    data = text.encode("utf-8")            # text -> bytes (deterministic encoding)
    return hashlib.sha256(data).hexdigest()  # bytes -> fixed 64-char hex fingerprint
```

### Why it works

`hashlib.sha256` implements SHA-256, a cryptographic hash that is **deterministic** (same
bytes in → same digest out, always) and produces a fixed **256-bit** result regardless of
input size — rendered as a **64-character hex string** by `.hexdigest()`. Because it's
deterministic and defined by a public standard, the digest is identical on every machine,
every Python version, and forever — exactly what a persistent cache key needs.

Encoding with `.encode("utf-8")` first guarantees the *same* text maps to the *same* bytes
(UTF-8 is unambiguous and universal), so the whole pipeline text → bytes → digest is
stable. The chance of two different texts producing the same SHA-256 digest (a *collision*)
is astronomically small — far below anything you'd hit in practice — so distinct content
gets distinct keys.

### The code, every line explained

```python
import hashlib                 # standard library: cryptographic hash functions

def content_key(text):
    data = text.encode("utf-8")          # encode: str -> bytes. UTF-8 is the standard,
                                         # deterministic choice. hashlib needs BYTES.
    return hashlib.sha256(data).hexdigest()
    #      └ build a SHA-256 hasher fed with `data`
    #                            └ .hexdigest() -> 64-char hex string like "9f86d08..."

key = content_key("the quick brown fox")
print(key)        # 9ecb36561341d18eb65484e833efea61edc74b84cf5e6ae1b81c63533e25fc8f
print(len(key))   # 64  — fixed length no matter how big the input was

# Same input -> same key, ALWAYS (this is the whole point):
assert content_key("hello") == content_key("hello")

# --- Why NOT the built-in hash() for persistence ------------------------
print(hash("hello"))   # some big int — DIFFERENT every time you restart Python
# Built-in hash() is randomised per process for security; great for in-memory dicts,
# useless as a saved/shared key. hashlib is stable; hash() is not.

# --- Using it as a cache: filename or dict key --------------------------
import os
def embed_cached(text):
    key = content_key(text)
    path = f"cache/{key}.json"           # key is short, hex, filesystem-safe
    if os.path.exists(path):             # cache HIT: same text seen before
        return load_json(path)           # skip the expensive call
    vec = call_embedding_api(text)       # cache MISS: do the work once
    save_json(path, vec)
    return vec

# --- Hashing a LARGE file without loading it all into memory ------------
def file_key(path):
    h = hashlib.sha256()                 # create an empty hasher
    with open(path, "rb") as f:          # "rb" = read BYTES (no decoding)
        for block in iter(lambda: f.read(8192), b""):  # read 8 KB at a time until b""
            h.update(block)              # feed each chunk in; hasher accumulates state
    return h.hexdigest()                 # final digest over the whole file, O(1) memory
# .update() can be called repeatedly — the result is as if you hashed the whole thing
# at once. Essential for files too big for RAM.

# --- Shorter keys / different algorithms --------------------------------
hashlib.md5(b"x").hexdigest()            # 32 hex chars — FASTER, fine for NON-security
                                         # dedup/cache keys, but cryptographically broken:
                                         # never use MD5 for passwords/signatures.
hashlib.sha256(b"x").hexdigest()[:16]    # truncate to 16 chars if you want shorter keys
                                         # (slightly higher collision odds, usually fine)
```

### Impact

- **Stable, portable keys:** the same content yields the same key across runs and machines,
  so caches, dedup tables, and content-addressed stores actually *hit* — turning repeated
  expensive work (embeddings, API calls, computations) into a one-time cost.
- **Fixed size from any input:** a 4 KB chunk and a 4 GB file both reduce to a 64-char
  string — usable as a dict key, filename, or database column.
- **Cheap change-detection:** if a file/record's hash is unchanged, its content is
  unchanged — so you can skip reprocessing (the basis of incremental pipelines).

### Pros & cons / when NOT to

**Reach for `hashlib` when:** you need a **persistent or shared** key derived from content
— caching expensive results, deduplicating records, content-addressed storage, detecting
"has this changed since last run?", or generating a stable ID for a document.

**Watch out / when NOT to:**
- **Don't use the built-in `hash()` for anything you persist or share** — it's randomised
  and process-local. It's only for in-memory `dict`/`set` keys within one run.
- **Hashing is one-way:** you cannot get the text back from a digest. That's a feature for
  privacy, but it means the hash is an *identifier*, not storage.
- **Passwords need a SLOW, salted hash** — not plain SHA-256/MD5. Use `bcrypt`/`argon2`
  /`hashlib.pbkdf2_hmac`. Fast hashes are *meant* to be fast, which is exactly wrong for
  password storage (it helps attackers guess). Different job entirely.
- **MD5/SHA-1 are broken for security** (signatures, integrity against an adversary) but
  *fine* for non-adversarial dedup/cache keys where you just need a fast fingerprint. Use
  SHA-256 when in doubt.
- **Normalise first if "same content" should ignore formatting.** Hash the *normalised*
  text (4.1) if `"Hello "` and `"hello"` should share a cache entry — otherwise they get
  different keys.

### Where this shows up

- **Real work — embedding/LLM caches:** key each text chunk by its SHA-256 so re-embedding
  the same content next run is free — a standard cost-saver in RAG pipelines (see 9.12).
- **Real work — deduplication & idempotency:** a content hash as a dedup key skips
  re-processing identical records, and as an idempotency key prevents running the same job
  twice (ties to 7.4/7.5).
- **Real work — incremental builds/ETL:** hash inputs to detect "unchanged since last run"
  and skip recomputation — how build systems and data pipelines avoid redundant work.
- **Pattern mapping (secondary):** hashing underpins hash maps/sets (O(1) lookup) and is the
  core trick in the **Rabin–Karp** substring search and rolling-hash problems — reduce a
  big object to a small comparable fingerprint.
[↑ Back to top](#contents)

---

<a id="4.5"></a>
## 4.5 — "Detect near-duplicate text" → normalisation keys & shingling

### The situation

You're building a training corpus and need to drop duplicate documents — but the
duplicates aren't *exact*. These three product descriptions are clearly "the same" content
with trivial edits:

```python
docs = [
    "The X200 camera shoots 4K video and has a 30x zoom lens.",
    "The X200 camera shoots 4K video and has a 30x zoom lens!!!",   # extra punctuation
    "the x200 CAMERA shoots 4k video and has a 30x  zoom lens",     # case + spacing
]
```

Exact-hash dedup (4.4) treats all three as different — their bytes differ — so all three
survive into your corpus, inflating it with near-copies that bias the model. But these are
short documents that differ only in *surface form*. A harder case is two long articles
where one is a lightly-reworded version of the other: not identical, not trivially
different either — they **share most of their content** but aren't equal even after
normalisation.

### What's really going on

"Near-duplicate" splits into two different problems, each with its own move:

1. **Surface-form duplicates** (case/punctuation/spacing differ, content identical). The
   move is a **normalisation key**: aggressively normalise (4.1) — lower-case, strip
   punctuation, collapse whitespace — then hash. Documents that normalise to the same text
   get the same key and dedupe exactly. Cheap and exact for this class.

2. **Partial-overlap duplicates** (one is a reworded/extended version of the other — same
   sentences, different order or with insertions). Normalisation won't make them equal, so
   you need a **similarity measure**. The standard move is **shingling + Jaccard
   similarity**:
   - A **shingle** (or *k-gram*) is a contiguous run of *k* tokens. Slicing a document into
     all its overlapping k-word shingles turns it into a **set** of small pieces.
   - **Jaccard similarity** between two sets = `|intersection| / |union|` — the fraction of
     pieces they *share* out of all pieces either has. Two docs that share most shingles
     score near 1.0; unrelated docs score near 0.0.

Shingling captures "do these share lots of local word-sequences?" which is exactly what
"near-duplicate" means for longer text.

### The move

For surface duplicates, build a **normalisation key** and dedupe with a `set`. For
partial-overlap duplicates, **shingle** each document into a set and compare with
**Jaccard similarity**:

```python
import re

def dedup_key(text):
    t = text.casefold()                       # case-insensitive
    t = re.sub(r"[^\w\s]", "", t)             # drop punctuation
    t = re.sub(r"\s+", " ", t).strip()        # collapse whitespace
    return t                                   # same surface content -> same key

def shingles(text, k=3):
    words = dedup_key(text).split()           # normalise, then split into tokens
    return {tuple(words[i:i+k]) for i in range(len(words) - k + 1)}  # set of k-grams

def jaccard(a, b):
    return len(a & b) / len(a | b)            # shared shingles / total shingles
```

### Why it works

The **normalisation key** removes every axis of *surface* variation, so two docs that say
the same thing in different formatting collapse to the identical string — then a `set` (or
the hash of 4.4) deduplicates them exactly, in one pass.

For **shingling**, turning each document into the *set* of its overlapping k-word sequences
captures local structure: if two documents share most of their three-word runs, they're
saying mostly the same things in mostly the same order. **Jaccard** then scores the
overlap as `shared / total`. Using **sets** makes intersection (`&`) and union (`|`) cheap,
and the score is bounded in `[0, 1]`: identical content → 1.0, fully disjoint → 0.0. You
pick a threshold (say 0.8) above which two docs are "near-duplicates".

Choosing `k` trades sensitivity: small `k` (1–2 words) matches loosely (more false
positives); larger `k` (3–5) requires longer shared runs (stricter). `k=3` is a common
default for prose.

### The code, every line explained

```python
import re

def dedup_key(text):
    t = text.casefold()                  # aggressive lower-case (4.1) for matching
    t = re.sub(r"[^\w\s]", "", t)        # [^\w\s] = any char that is NOT word/whitespace
                                         # i.e. remove punctuation/symbols
    t = re.sub(r"\s+", " ", t).strip()   # collapse runs of whitespace -> single space
    return t

docs = [
    "The X200 camera shoots 4K video and has a 30x zoom lens.",
    "The X200 camera shoots 4K video and has a 30x zoom lens!!!",
    "the x200 CAMERA shoots 4k video and has a 30x  zoom lens",
]
seen, unique = set(), []
for d in docs:
    key = dedup_key(d)                   # all three normalise to the SAME string
    if key not in seen:                  # O(1) membership test in a set
        seen.add(key)
        unique.append(d)                 # keep the FIRST occurrence (original form)
print(len(unique))                       # 1  — the three surface-variants collapse to one

# --- Shingling + Jaccard for PARTIAL-overlap near-duplicates ------------
def shingles(text, k=3):
    words = dedup_key(text).split()      # normalise first, then tokenise on whitespace
    # build every contiguous k-word window; store as a SET of tuples (tuples are hashable)
    return {tuple(words[i:i+k]) for i in range(len(words) - k + 1)}
    #        └ words[i:i+k] is a k-word slice; tuple() makes it usable as a set element

def jaccard(a, b):
    if not a or not b:                   # guard against empty sets (avoid divide-by-zero)
        return 0.0
    return len(a & b) / len(a | b)       # & = set intersection (shared), | = union (all)

d1 = "the cat sat on the mat in the sun"
d2 = "the cat sat on the warm mat in the sun"     # one word inserted
print(round(jaccard(shingles(d1), shingles(d2)), 2))   # ~0.5  — high overlap

d3 = "stock prices fell sharply on tuesday morning"   # unrelated
print(round(jaccard(shingles(d1), shingles(d3)), 2))   # 0.0   — no shared 3-grams

# --- Using a threshold to flag near-duplicates --------------------------
THRESHOLD = 0.8
def is_near_duplicate(a, b, k=3):
    return jaccard(shingles(a, k), shingles(b, k)) >= THRESHOLD
```

### Impact

- **Cleaner corpora:** surface-variant duplicates collapse exactly; reworded near-copies get
  a tunable similarity score — so you remove redundancy that would otherwise bias a model or
  inflate counts.
- **Tunable strictness:** the `k` (shingle size) and the Jaccard threshold give you a dial
  from "loosely similar" to "almost identical", matched to how aggressive you want dedup.
- **Set-based and explainable:** Jaccard is just shared/total — easy to reason about and
  debug, unlike opaque similarity scores.

### Pros & cons / when NOT to

**Reach for a normalisation key when:** duplicates differ only in surface form
(case/punctuation/spacing) — it's exact, O(1) per doc, and trivially scalable.

**Reach for shingling + Jaccard when:** documents partially overlap (reworded, extended,
reordered) and you need a *degree* of similarity rather than equal/not-equal.

**Watch out / when NOT to:**
- **All-pairs comparison is O(n²).** Comparing every document to every other is fine for
  thousands but explodes for millions. At scale, use **MinHash + LSH** (locality-sensitive
  hashing — the `datasketch` library) to find candidate near-duplicates without comparing
  all pairs. Shingling/Jaccard is the *concept*; MinHash/LSH is the scalable implementation.
- **Shingling ignores meaning.** It matches *surface word-sequences*, so "big" vs "large"
  count as different. For *semantic* near-duplicates (same meaning, different words), use
  embeddings + cosine similarity (9.14) instead.
- **Choose `k` deliberately:** too small → unrelated docs share common short phrases and
  score falsely high; too large → tolerant of almost no edits. Tune on your data.
- **Very short texts** have few shingles, so a single shared/changed word swings the score
  wildly — Jaccard is most reliable on longer text.

### Where this shows up

- **Real work — training-data deduplication:** removing near-duplicate documents/web pages
  before pretraining or fine-tuning, a known driver of model quality and a standard corpus-
  cleaning step.
- **Real work — plagiarism / content-overlap detection:** flagging articles, answers, or
  support tickets that are reworded copies of each other.
- **Real work — record linkage:** collapsing "the same" catalogue entry, customer, or
  address written slightly differently (normalisation key first, similarity for the rest).
- **Pattern mapping (secondary):** shingling is the k-gram/sliding-window idea applied to
  tokens; Jaccard-over-sets and MinHash connect to the "approximate membership / similarity
  via hashing" family (bloom filters, rolling hashes).
[↑ Back to top](#contents)

---

<a id="4.6"></a>
## 4.6 — "Fuzzy similarity between strings" → edit distance / ratio

### The situation

You're matching free-typed city names against a clean reference list. Users make typos, and
exact matching fails on every near-miss:

```python
reference = ["London", "Manchester", "Birmingham", "Liverpool"]
typed = "Manchestar"        # one letter wrong: 'a' instead of 'e'
print(typed in reference)   # False — exact match misses a single-character typo
```

`"Manchestar"` is *obviously* meant to be `"Manchester"` — one character differs — but
`in` gives a flat `False`. You need a way to say "how *close* are these two strings?" so you
can pick the nearest reference entry, with a confidence you can threshold. This is different
from 4.5: there you compared whole documents by shared word-sequences; here you compare
short strings **character by character**, where single-letter typos matter.

### What's really going on

You want a **fuzzy** (approximate) string match: a numeric measure of how similar two
strings are at the character level. The foundational measure is **edit distance** (also
called **Levenshtein distance**): the **minimum number of single-character edits** —
insertions, deletions, or substitutions — needed to turn one string into the other.

- `"Manchestar"` → `"Manchester"` needs **1** substitution (`a`→`e`) → edit distance 1.
- `"cat"` → `"cart"` needs **1** insertion → edit distance 1.
- `"kitten"` → `"sitting"` needs **3** edits → edit distance 3.

A raw distance isn't directly comparable across different string lengths (distance 2 is huge
for 3-letter words, tiny for 50-letter ones), so it's usually turned into a **ratio** in
`[0, 1]`: 1.0 = identical, lower = more different, normalised by length. You then pick the
reference string with the highest ratio (or lowest distance) and accept it if it clears a
threshold.

### The move

Use Python's built-in **`difflib.SequenceMatcher`** for a quick similarity ratio with no
dependencies, or the third-party **`rapidfuzz`** library when you need speed and a richer
toolkit. Pick the best match above a threshold:

```python
from difflib import SequenceMatcher

def ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()   # similarity in [0, 1], 1.0 = identical

def best_match(query, choices, cutoff=0.8):
    scored = ((c, ratio(query, c)) for c in choices)   # (choice, score) for each
    best, score = max(scored, key=lambda cs: cs[1])    # the highest-scoring choice
    return best if score >= cutoff else None            # accept only if confident enough
```

### Why it works

`SequenceMatcher.ratio()` returns `2 * M / T`, where `M` is the number of matching
characters and `T` is the total length of both strings — a length-normalised similarity in
`[0, 1]`. Identical strings score 1.0; a single typo in a 10-letter word scores ~0.9; an
unrelated string scores near 0. Because it's normalised, the same threshold works for short
and long strings alike.

`best_match` scores the query against every candidate and takes the **maximum** — the
nearest reference entry — but only returns it if the score clears `cutoff`, so a query with
*no* good match returns `None` rather than a confidently-wrong guess. The `cutoff` is your
precision/recall dial: higher = stricter (fewer false matches, more misses), lower = more
forgiving.

Under the hood, true Levenshtein distance is computed by **dynamic programming** — filling a
table where each cell is the cheapest way to align prefixes of the two strings — which is
O(len_a × len_b). For matching one query against a big list, `rapidfuzz` implements this in
optimised C and is dramatically faster than `difflib`.

### The code, every line explained

```python
# --- difflib: built-in, zero dependencies -------------------------------
from difflib import SequenceMatcher

def ratio(a, b):
    # SequenceMatcher(isjunk, a, b); None = no characters treated as "junk".
    # .ratio() -> float in [0,1]: 1.0 identical, 0.0 nothing in common.
    return SequenceMatcher(None, a, b).ratio()

print(round(ratio("Manchester", "Manchestar"), 2))   # 0.9  — very close (1 typo)
print(round(ratio("Manchester", "Liverpool"), 2))    # 0.21 — clearly different

reference = ["London", "Manchester", "Birmingham", "Liverpool"]

def best_match(query, choices, cutoff=0.8):
    scored = ((c, ratio(query, c)) for c in choices)  # generator of (choice, score)
    best, score = max(scored, key=lambda cs: cs[1])   # max by the score field
    return best if score >= cutoff else None          # None if nothing clears the bar

print(best_match("Manchestar", reference))   # "Manchester" — typo corrected
print(best_match("Tokyo", reference))        # None — no close match, don't guess

# --- difflib's own convenience helper -----------------------------------
import difflib
print(difflib.get_close_matches("Birmingam", reference, n=1, cutoff=0.7))
# ['Birmingham']  — returns up to n best matches above cutoff, already sorted

# --- Explicit edit (Levenshtein) distance, if you want the raw count ----
# (rapidfuzz provides this fast; here's the idea spelled out for clarity)
def edit_distance(a, b):
    # DP table: prev[j] = distance between a[:i] and b[:j]. Classic O(len(a)*len(b)).
    prev = list(range(len(b) + 1))            # row 0: turning "" into b[:j] costs j inserts
    for i, ca in enumerate(a, 1):
        cur = [i]                             # column 0: turning a[:i] into "" costs i deletes
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1       # substitution is free if the chars match
            cur.append(min(
                prev[j] + 1,                  # delete a char from a
                cur[j-1] + 1,                 # insert a char into a
                prev[j-1] + cost,             # substitute (or match)
            ))
        prev = cur
    return prev[-1]                           # bottom-right cell = full edit distance
print(edit_distance("kitten", "sitting"))     # 3

# --- rapidfuzz: the production tool (pip install rapidfuzz) --------------
# from rapidfuzz import fuzz, process
# fuzz.ratio("Manchester", "Manchestar")            # 90.0  (0-100 scale, C-fast)
# process.extractOne("Manchestar", reference)       # ('Manchester', 90.0, 1) best match
# 'process.extract' / 'extractOne' do the score-everything-and-pick-best loop for you,
# orders of magnitude faster than difflib over large candidate lists.
```

### Impact

- **Typo-tolerant matching:** single-character errors, transpositions, and minor edits no
  longer cause a hard miss — you recover the intended value with a confidence score.
- **Thresholdable confidence:** the ratio gives a tunable cutoff so you can trade false
  matches against missed matches deliberately, and return `None` rather than guess.
- **No model needed:** pure string maths — deterministic, explainable, and cheap for short
  strings, with `rapidfuzz` making it fast even at scale.

### Pros & cons / when NOT to

**Reach for edit distance / ratio when:** matching **short strings** where *character-level*
typos matter — names, cities, product codes, deduping a column of slightly-misspelled
labels, correcting user input against a known list.

**Watch out / when NOT to:**
- **It's O(len_a × len_b) per comparison.** Matching one query against a huge list is
  O(n × m) overall — fine for hundreds/thousands, slow for millions in pure Python. Use
  `rapidfuzz` (C-optimised) and/or pre-filter candidates (e.g. by first letter or length).
- **It's surface-level, not semantic.** "NYC" vs "New York City" are character-wise very
  different but mean the same thing — edit distance scores them low. For meaning-based
  similarity use embeddings (9.14); for word-overlap on longer text use shingling (4.5).
- **Length-normalise before thresholding.** Use the *ratio*, not raw distance, so one
  threshold works regardless of string length.
- **Word-order changes hurt char-level ratios.** "John Smith" vs "Smith John" scores low;
  `rapidfuzz`'s `token_sort_ratio`/`token_set_ratio` handle reordered words by sorting tokens
  first — reach for those on multi-word fields.

### Where this shows up

- **Real work — data cleaning / entity resolution:** snapping messy free-text values
  (cities, company names, product titles) to a canonical reference list before joining or
  grouping — the classic "fuzzy join".
- **Real work — search & autocomplete:** "did you mean…?" suggestions and typo-tolerant
  lookup against a dictionary of known terms.
- **Real work — deduplication of short records:** catching near-identical names/SKUs that an
  exact or normalisation key (4.5) misses because of a single typo.
- **Pattern mapping (secondary):** edit distance is a canonical **string dynamic-programming**
  problem (Area 11.23) — the same DP table powers longest-common-subsequence and sequence-
  alignment problems; recognising "minimum edits to transform A into B" is the tell.
[↑ Back to top](#contents)

---

<a id="4.7"></a>
## 4.7 — "Extract text from HTML/markdown" → parsing vs regex

### The situation

You're building a corpus from scraped web pages and need the **visible text** — no tags, no
scripts, no styling — out of HTML like this:

```python
html = """
<div class="article">
  <h1>Quarterly Results</h1>
  <p>Revenue grew <b>12%</b> to $4.2M.</p>
  <script>trackEvent('view');</script>
  <p>See <a href="/q3">the full report</a>.</p>
</div>
"""
```

You want:

```
Quarterly Results
Revenue grew 12% to $4.2M.
See the full report.
```

The tempting first move is a regex (4.2/4.3) to "just strip the tags":

```python
import re
text = re.sub(r"<[^>]+>", "", html)   # remove anything between < and >
```

It *almost* works — but it leaves the `trackEvent('view');` JavaScript in (that's text
*between* `<script>` tags, not a tag itself), it mangles HTML entities like `&amp;` into
literal `&amp;`, and it falls apart on the first comment, attribute containing `>`, or
unclosed tag. You're fighting the format instead of reading it.

### What's really going on

HTML and Markdown are **nested, structured** formats — tags contain tags, attributes can
contain `<` and `>`, comments and `<script>`/`<style>` blocks hold non-content text. Regex
matches *flat* patterns; it has no concept of "this tag is *inside* that one" or "ignore
everything inside `<script>`". Trying to extract content from a nested format with regex is
the textbook case of the wrong tool — it handles the easy 90% and silently corrupts the
hard 10%.

The right move is a **parser**: a library that *understands* the format's grammar, builds a
proper tree of elements, and lets you ask structured questions ("give me all the visible
text", "find every `<a>` tag", "get the `href` attribute"). For HTML the standard choice is
**BeautifulSoup**; for Markdown you convert to HTML (with `markdown`) and then parse, or use
a Markdown parser directly. The parser handles entities, malformed markup, and nesting
correctly because that's its entire job.

### The move

Parse the HTML with **BeautifulSoup**, drop the non-content tags (`<script>`, `<style>`),
then ask for the text:

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")     # build a navigable tree of the document
for tag in soup(["script", "style"]):         # find non-content tags...
    tag.decompose()                            # ...and remove them from the tree
text = soup.get_text(separator="\n", strip=True)   # all visible text, one block per line
```

### Why it works

BeautifulSoup **parses** the HTML into a tree of element objects — it knows where each tag
starts and ends, what's nested inside what, and how to decode entities (`&amp;` → `&`,
`&nbsp;` → a space). Because it models the *structure*, you can operate on it semantically:
`soup(["script", "style"])` finds those elements wherever they are, and `.decompose()`
deletes them and their contents from the tree entirely — solving the "JavaScript leaks into
my text" problem that regex can't.

`get_text()` then walks the cleaned tree and concatenates the **text nodes** (the actual
content between tags), correctly skipping the tags themselves. `separator="\n"` puts each
text run on its own line and `strip=True` trims surrounding whitespace, giving clean,
readable output. The parser absorbs malformed markup (unclosed tags, stray `>`) gracefully,
where a regex would derail.

### The code, every line explained

```python
from bs4 import BeautifulSoup          # pip install beautifulsoup4

html = """
<div class="article">
  <h1>Quarterly Results</h1>
  <p>Revenue grew <b>12%</b> to $4.2M.</p>
  <script>trackEvent('view');</script>
  <p>See <a href="/q3">the full report</a>.</p>
</div>
"""

# "html.parser" is Python's built-in parser (no extra install). For messy real-world
# pages, "lxml" (faster) or "html5parser" (browser-like) are common alternatives.
soup = BeautifulSoup(html, "html.parser")    # -> a tree you can navigate and query

for tag in soup(["script", "style"]):        # soup([...]) finds ALL tags with those names
    tag.decompose()                           # remove the tag AND its contents from the tree
                                              # (this is why the JS no longer appears in text)

text = soup.get_text(separator="\n", strip=True)
#                    │                 └ trim whitespace around each text run
#                    └ join separate text nodes with newlines instead of running together
print(text)
# Quarterly Results
# Revenue grew 12% to $4.2M.
# See the full report.

# --- Targeted extraction: pull specific structured pieces ----------------
title = soup.find("h1").get_text(strip=True)        # first <h1>'s text -> "Quarterly Results"
links = [a["href"] for a in soup.find_all("a")]     # every <a>'s href attribute -> ["/q3"]
#         └ a["href"] reads an ATTRIBUTE by name; find_all returns ALL matching tags
print(title, links)

# --- Entities are decoded for you (regex would leave them mangled) -------
snippet = BeautifulSoup("Tom &amp; Jerry &lt;3", "html.parser")
print(snippet.get_text())                    # "Tom & Jerry <3"  — entities decoded properly

# --- MARKDOWN: convert to HTML, then parse (or strip simply) -------------
import markdown                                # pip install markdown
md = "# Title\n\nSome **bold** text and a [link](http://x.io)."
as_html = markdown.markdown(md)               # "<h1>Title</h1><p>Some <strong>bold</strong>..."
plain = BeautifulSoup(as_html, "html.parser").get_text(separator="\n", strip=True)
print(plain)                                  # "Title\nSome bold text and a link."
# Rendering markdown -> HTML -> parse gives correct plain text, handling links, emphasis,
# code blocks, lists, etc. — far more robust than regex-stripping markdown syntax by hand.

# --- The library that just does HTML-to-clean-text -----------------------
# For "I just want the readable text", the `trafilatura` or `readability-lxml` libraries
# also strip nav/boilerplate and extract the main article body — built on parsers, not regex.
```

### Impact

- **Correctness:** entities decode properly, `<script>`/`<style>` content is excluded, and
  nested/malformed markup is handled — eliminating the silent corruption a regex strip leaves
  behind.
- **Structured access:** beyond plain text, you can pull *specific* pieces — titles, links,
  table cells, attributes — by querying the tree, which regex can't do reliably.
- **Maintainability:** the parser absorbs the format's edge cases so you don't accrete an
  ever-growing pile of regex special-cases as new pages break the old pattern.

### Pros & cons / when NOT to

**Reach for a parser when:** you extract content or structure from HTML, XML, or Markdown —
any **nested** markup. This is non-negotiable for real-world pages.

**Watch out / when NOT to:**
- **The one regex exception:** stripping a *single, known, flat* tag from a *trusted*,
  simple string (e.g. removing `<b>...</b>` from your own templated snippet) is fine with
  regex. The rule is about *arbitrary nested* markup, not every angle bracket you ever see.
- **JavaScript-rendered pages:** BeautifulSoup parses the HTML *as delivered*. If content is
  built client-side by JS (single-page apps), the HTML is nearly empty — you need a headless
  browser (Playwright/Selenium) to render first, *then* parse.
- **Parser choice matters:** `html.parser` is built-in and fine; `lxml` is faster on large
  pages; `html5lib` is the most browser-faithful on broken markup. Pick per need.
- **Don't over-extract:** `get_text()` includes nav menus, footers, and boilerplate. For
  "just the article", use a content-extraction library (`trafilatura`/`readability`) rather
  than hand-filtering.

### Where this shows up

- **Real work — web-scraping corpora:** turning crawled HTML into clean text for training,
  search indexing, or RAG ingestion — the standard first step of any scraping pipeline.
- **Real work — document ingestion:** extracting text and structure from HTML emails, exports,
  Markdown docs, or Confluence/wiki pages before chunking (4.8) and embedding.
- **Real work — targeted scraping:** pulling specific fields (prices, titles, table rows,
  links) from pages by querying the parse tree rather than brittle string slicing.
- **Pattern mapping (secondary):** parsing nested markup is a **tree** problem — the parser
  builds a DOM tree and `get_text` is essentially a depth-first traversal collecting leaf
  text nodes (ties to tree-traversal patterns in Area 11), which is exactly why a flat regex
  can't express it.
[↑ Back to top](#contents)

---

<a id="4.8"></a>
## 4.8 — "Split text into chunks (chars/sentences/tokens)" → chunking

### The situation

You have a 40,000-character support article and an embedding model that only accepts ~512
tokens (~2,000 characters) of input at a time. To index the article for retrieval, you must
split it into pieces small enough to embed. The naive split is by fixed character count:

```python
text = "...40,000 characters of article..."
chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]   # slice every 2000 chars
```

It runs, but it cuts blindly. A chunk boundary can land in the **middle of a word** or
**mid-sentence**:

```
chunk 5 ends: "...the recommended approach is to res"
chunk 6 starts: "tart the service and verify the..."
```

Now "restart" is split across two chunks; neither chunk contains the whole instruction, so a
retrieval query like "how do I restart the service" matches *neither* well. And a fact that
straddles the boundary is lost to both chunks. The split destroyed the very meaning you're
trying to index.

### What's really going on

Chunking is about cutting text into pieces that are **small enough** for a size limit while
**preserving meaning** at the boundaries. Two forces are in tension:

- A hard **size budget** measured in *characters* or, more precisely, **tokens** (the units
  the model actually counts — roughly word-pieces; "restarting" might be 2 tokens). The
  model rejects or truncates anything over its limit, so you cannot exceed it.
- **Semantic boundaries** — sentences and paragraphs are natural break points; words are the
  minimum unit you should never split. Cutting *on* these boundaries keeps each chunk
  self-contained.

So the move is to split on the **largest natural boundary that keeps you under budget**:
prefer paragraph breaks, then sentence breaks, then word breaks — never mid-word. And
because a single fact can still span a boundary, chunks usually **overlap** slightly: the
end of one chunk is repeated at the start of the next, so context that straddles a cut isn't
lost to retrieval.

### The move

Split on **sentence/paragraph boundaries**, **accumulate** sentences into a chunk until
adding the next would exceed the budget, then start a new chunk — carrying a small **overlap**
from the previous chunk:

```python
import re

def chunk_text(text, max_chars=2000, overlap=200):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())   # split on sentence ends
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) + 1 > max_chars and current:
            chunks.append(current.strip())                  # flush the full chunk
            current = current[-overlap:] + " " + s          # carry overlap into the next
        else:
            current += " " + s
    if current.strip():
        chunks.append(current.strip())
    return chunks
```

### Why it works

`re.split(r"(?<=[.!?])\s+", text)` breaks the text **after** sentence-ending punctuation:
the `(?<=[.!?])` is a **lookbehind** (a zero-width assertion meaning "the character just
before here is `.`, `!`, or `?`") and `\s+` is the whitespace after it — so the split lands
*between* sentences, leaving each sentence intact. You now have clean semantic units instead
of arbitrary character ranges.

The accumulation loop **greedily packs** whole sentences into the current chunk until adding
one more would breach `max_chars`, then flushes the chunk. Because it only ever adds *whole
sentences*, no chunk ends mid-sentence (and certainly not mid-word). The `current[-overlap:]`
copies the last `overlap` characters of the just-finished chunk to the front of the next one,
so a fact spanning the boundary appears — complete — in at least one chunk. The result: every
chunk is under budget, ends on a sentence boundary, and shares context with its neighbour.

### The code, every line explained

```python
import re

def chunk_text(text, max_chars=2000, overlap=200):
    # Split into sentences. (?<=[.!?]) is a LOOKBEHIND: a zero-width check that the
    # PREVIOUS char is . ! or ? — so we split on the whitespace AFTER a sentence end,
    # keeping the punctuation attached to its sentence.
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    chunks, current = [], ""              # finished chunks; the chunk we're filling
    for s in sentences:
        # If adding this sentence would overflow the budget AND we already have content,
        # flush the current chunk and start a new one with an overlap tail.
        if len(current) + len(s) + 1 > max_chars and current:
            chunks.append(current.strip())
            current = current[-overlap:] + " " + s   # last `overlap` chars carried forward
        else:
            current += " " + s            # still fits: append the sentence
    if current.strip():                   # don't forget the final partial chunk
        chunks.append(current.strip())
    return chunks

article = "First sentence. Second one is here. " * 200   # ~7000 chars
parts = chunk_text(article, max_chars=2000, overlap=150)
print(len(parts), [len(p) for p in parts])   # several chunks, each <= ~2000 chars
# Every chunk ends after a full sentence; consecutive chunks share ~150 chars of context.

# --- Counting TOKENS, not characters, against a model limit -------------
# Models budget in TOKENS (word-pieces), not characters. ~4 chars ≈ 1 token in English,
# but that's a rough rule — measure exactly with the model's own tokeniser:
# import tiktoken
# enc = tiktoken.get_encoding("cl100k_base")   # the tokeniser for many OpenAI models
# n_tokens = len(enc.encode(chunk))            # exact token count for THIS text
# Then chunk by token count instead of len(chunk): accumulate until n_tokens > max_tokens.

# --- Simpler strategies for simpler needs -------------------------------
# 1) Fixed-character with overlap (when boundaries don't matter much):
def char_chunks(text, size=2000, overlap=200):
    step = size - overlap                        # advance less than `size` to create overlap
    return [text[i:i+size] for i in range(0, len(text), step)]

# 2) Paragraph-first (split on blank lines), then fall back to sentences if a
#    paragraph alone exceeds the budget — a common "recursive" chunking shape:
def paragraphs(text):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]   # split on blank lines

# --- Production tools do exactly this, configurably ----------------------
# LangChain's RecursiveCharacterTextSplitter tries a LIST of separators in order
# (paragraph -> line -> sentence -> word), recursing into pieces that are still too big.
# Same principle: split on the largest natural boundary that keeps each piece under budget.
```

### Impact

- **Retrieval quality:** chunks that end on sentence boundaries and overlap slightly keep
  facts intact, so embedding/search matches the *whole* relevant passage instead of a
  severed fragment — directly improving RAG recall.
- **Respects hard limits:** every chunk stays under the model's token/character budget, so
  embedding/inference calls don't fail or silently truncate.
- **Tunable:** chunk size and overlap are dials you set to balance context-per-chunk against
  the number of chunks (cost) for your specific model and data.

### Pros & cons / when NOT to

**Reach for boundary-aware chunking when:** you feed long text to a size-limited model —
embeddings, summarisation, RAG ingestion — and the meaning at chunk boundaries matters.

**Watch out / when NOT to:**
- **Characters ≈ tokens is only a rough guide.** If you're near a hard token limit, count
  with the model's **actual tokeniser** (e.g. `tiktoken`), not `len(text)` — a chunk that's
  fine in characters can still bust the token budget, especially for code or non-English text.
- **Naive sentence-splitting missteps** on "Dr.", "U.S.A.", decimals ("3.14"), and
  abbreviations — the `[.!?]` regex treats those dots as sentence ends. For high-quality
  splitting use a real sentence tokeniser (`nltk.sent_tokenize`, `spaCy`).
- **Too much overlap wastes money:** overlap duplicates text into multiple chunks, so every
  duplicated token is embedded/processed twice. Keep it to the minimum that preserves
  cross-boundary context (often 10–20% of chunk size).
- **Some content shouldn't be split mid-structure:** tables, code blocks, and lists lose
  meaning if cut. Split on structural boundaries (paragraphs/sections) first, and treat such
  blocks as atomic where possible.

### Where this shows up

- **Real work — RAG ingestion:** splitting documents before embedding so each vector
  represents a coherent passage — the core preprocessing step of any retrieval system (ties
  to 9.9).
- **Real work — long-document summarisation:** chunk → summarise each → combine, when the
  document exceeds the model's context window.
- **Real work — streaming/batch text processing:** breaking huge logs or transcripts into
  bounded pieces for per-chunk classification, tagging, or extraction.
- **Pattern mapping (secondary):** the greedy "pack items into bounded bins" loop is a
  **sliding-window / greedy partition** pattern; choosing the largest valid boundary that
  fits is the same shape as word-wrap and bin-packing-style problems.
[↑ Back to top](#contents)

---

<a id="4.9"></a>
## 4.9 — "Build strings/templates safely" → join, templates, escaping

### The situation

Three everyday string-building tasks, each usually done the fragile way.

**Task 1 — assemble one string from many pieces.** You build a CSV line by `+`-ing in a
loop:

```python
fields = ["2026-06-18", "ERROR", "timeout after 30s"]
line = ""
for f in fields:
    line += f + ","          # builds "2026-06-18,ERROR,timeout after 30s,"
line = line[:-1]             # then hack off the trailing comma
```

**Task 2 — fill a reusable template** where the *template text* is fixed but supplied
separately from your code (a config file, a user-editable message):

```python
template = "Hello {name}, your job {job_id} finished."   # comes from a config file
msg = template.format(name=user, job_id=jid)             # what if the template has stray { }?
```

**Task 3 — put a value into SQL/HTML/a shell command.** You f-string it in directly:

```python
query = f"SELECT * FROM users WHERE name = '{name}'"     # name from user input...
```

Each looks fine and each has a sharp edge: the `+`-loop is slow and leaves a trailing
separator; `.format()` crashes if the externally-supplied template contains a literal brace;
and the f-stringed SQL is a **security hole** — a `name` of `'; DROP TABLE users; --` becomes
executable SQL.

### What's really going on

These are three distinct sub-skills under "build strings safely":

- **Joining** many pieces with a separator: the right tool is **`str.join`**, which is both
  faster and cleaner than `+`-in-a-loop and never leaves a dangling separator.
- **Templating** with text that comes from *outside* your source code: f-strings can't help
  (they're baked into the code at parse time), and `.format()` chokes on stray braces from
  untrusted templates. **`string.Template`** uses `$name` placeholders and is safe against
  malformed/hostile template text.
- **Escaping**: when a value crosses into a *different language* — SQL, HTML, shell — it must
  be **escaped** or, better, passed through that language's **parameterisation** mechanism so
  it's treated as *data*, never as *code*. f-strings build plain text; they do **not** escape
  anything, which is exactly how injection bugs happen.

The unifying idea: match the tool to *where the string is going* and *where its parts come
from*.

### The move

Use **`str.join`** to assemble pieces, **`string.Template`** for externally-supplied
templates, and the target system's **parameterisation/escaping** (never raw f-strings) when a
value enters SQL/HTML/shell:

```python
line = ",".join(fields)                       # join: separator.join(iterable)

from string import Template
msg = Template("Hello $name, job $job_id done.").safe_substitute(name=user, job_id=jid)

cursor.execute("SELECT * FROM users WHERE name = %s", (name,))   # parameterised SQL
```

### Why it works

**`",".join(fields)`** asks the *separator* to stitch an iterable of strings together,
inserting the separator *between* elements only — so there's no trailing comma to trim. It
builds the result in one optimised pass in C, allocating the final string once, instead of
the `+`-loop's repeated "make a new bigger string each iteration" (which is O(n²) on long
inputs — see 2.4).

**`string.Template`** uses `$name` placeholders and is designed for templates that come from
*outside* your code. Its `.safe_substitute()` fills known placeholders and **leaves unknown
ones untouched** rather than raising — so a malformed or partially-filled template degrades
gracefully instead of crashing, and there are no `{}`-brace collisions.

For **escaping**, parameterised SQL (`%s` placeholder + a tuple of values) sends the query
structure and the data *separately* to the database driver, which binds the value as pure
data — so `'; DROP TABLE users; --` is stored/searched as a literal string, not executed.
The same principle applies to HTML (`html.escape` turns `<` into `&lt;` so it can't become a
tag) and shell (`shlex.quote`, or better, pass an argument *list* to `subprocess` so no shell
parses it).

### The code, every line explained

```python
# --- join: assemble pieces with a separator, no trailing junk ------------
fields = ["2026-06-18", "ERROR", "timeout after 30s"]
line = ",".join(fields)            # "2026-06-18,ERROR,timeout after 30s"  (no trailing comma)
#       └ SEPARATOR.join(iterable): the separator goes BETWEEN items only
paragraph = "\n".join(lines)       # join log lines with newlines
csv_row = ",".join(str(x) for x in row)   # join MUST get strings -> convert non-strings first
# Why not "+": += in a loop rebuilds the whole string each time (O(n²)); join is one pass.

# --- string.Template: safe for templates supplied from OUTSIDE your code -
from string import Template
tmpl = Template("Hello $name, your job $job_id finished.")   # $name placeholders
msg = tmpl.substitute(name="Asha", job_id="J-91")            # fills ALL; missing -> KeyError
print(msg)        # "Hello Asha, your job J-91 finished."
# .safe_substitute leaves unknown placeholders as-is instead of raising — robust for
# partially-known data or user-editable templates:
print(Template("Hi $name, $unknown").safe_substitute(name="Asha"))  # "Hi Asha, $unknown"
# Use $$ for a literal dollar sign. Template has no code execution -> safe with untrusted text.

# --- SQL: NEVER f-string values in; use parameter placeholders ----------
name = "'; DROP TABLE users; --"                  # hostile input
# WRONG: f"SELECT * FROM users WHERE name = '{name}'"  -> SQL INJECTION
# RIGHT: pass the value separately; the driver binds it as DATA, not code:
cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
#                                                 │      └ a TUPLE of values to bind
#                                                 └ placeholder (%s for many drivers; ? for sqlite)
# The query TEXT and the VALUES travel separately, so `name` can never become executable SQL.

# --- HTML: escape values so they can't become markup --------------------
import html
user_input = "<script>alert('x')</script>"
safe = html.escape(user_input)     # "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;"
page = f"<p>{safe}</p>"            # now it RENDERS as text, not an executable script tag
# (Real web templating — Jinja2 etc. — auto-escapes by default; this is the manual version.)

# --- Shell: pass an argument LIST (no shell parsing) or quote -----------
import subprocess, shlex
filename = "my file; rm -rf /"     # hostile
# RIGHT: a list -> the args go straight to the program, no shell interprets the ';':
subprocess.run(["ls", "-l", filename])           # filename is ONE literal argument
# If you MUST build a shell string, quote each value:
cmd = f"ls -l {shlex.quote(filename)}"           # shlex.quote escapes it safely

# --- textwrap / format-spec niceties for human-facing strings -----------
import textwrap
print(textwrap.fill("a very long line ...", width=40))   # wrap to 40-column lines
print(f"{'name':<10}{'score':>6}")                       # column alignment (see 1.11)
```

### Impact

- **Correctness:** `join` eliminates trailing-separator bugs and the O(n²) slowdown of
  `+`-in-a-loop; `Template` survives stray braces and missing keys instead of crashing.
- **Security:** parameterised SQL, HTML-escaping, and argument-list `subprocess` close the
  injection holes that direct f-string interpolation opens — the difference between a working
  query and a dropped table.
- **Clarity:** each tool signals intent — `join` says "stitch these", `Template` says
  "external template", `execute(sql, params)` says "value is data" — so readers and reviewers
  see the safety boundary.

### Pros & cons / when NOT to

**Reach for `join` when:** building one string from many pieces with a separator (CSV lines,
paths, sentences, any delimited output). **Reach for `Template`** when the template text comes
from config/users. **Reach for parameterisation/escaping** whenever a value crosses into SQL,
HTML, shell, or any other language.

**Watch out / when NOT to:**
- **`join` requires strings.** `",".join([1, 2])` raises `TypeError` — convert first
  (`",".join(map(str, nums))` or a generator). It joins an *iterable*, so a generator
  expression works directly.
- **f-strings (1.11) are still the right default for *internal*, *trusted* text** — log
  lines, file names, messages assembled from your own variables. The caveat is specifically
  values that (a) come from untrusted input AND (b) cross into another language. Don't
  cargo-cult `Template`/escaping onto every string.
- **Never roll your own SQL/HTML escaping with `str.replace`** — it's a moving target with
  edge cases. Use the driver's parameterisation, a real HTML-escaping function, or a
  templating engine that auto-escapes.
- **`Template.substitute` raises `KeyError`/`ValueError`** on missing keys or bad syntax;
  use `safe_substitute` when partial filling is acceptable.

### Where this shows up

- **Real work — building output files & reports:** `"\n".join(rows)` / `",".join(fields)` to
  assemble CSV, TSV, logs, or text reports without trailing-separator bugs.
- **Real work — query & command construction:** parameterised SQL for any database access,
  and argument-list `subprocess` for shelling out — the standard safe patterns in data
  pipelines.
- **Real work — prompt & message templating:** filling user-editable or config-stored
  templates (notification messages, LLM prompt skeletons) with `string.Template` or a proper
  templating engine, keeping the template separate from code.
- **Pattern mapping (secondary):** not an algorithm per se, but `str.join` is *the* idiomatic
  way to emit a result string in interview problems (e.g. "return the path as `a/b/c`"), and
  recognising the O(n²) `+`-in-a-loop trap is a standard performance point (2.4).
[↑ Back to top](#contents)

---

<a id="4.10"></a>
## 4.10 — "Search within large text efficiently" → find/in vs regex vs index

### The situation

Three search needs that people reflexively reach for regex to solve — often the wrong call.

**Need 1 — does this exact word appear?**

```python
text = open("server.log").read()      # a 200 MB log file as one string
import re
if re.search(r"ERROR", text):          # regex... for a fixed word?
    alert()
```

**Need 2 — where is it (and how many)?**

```python
positions = [m.start() for m in re.finditer(r"timeout", text)]   # regex for a literal
count = len(re.findall(r"timeout", text))
```

**Need 3 — repeatedly check "does this document contain term X?" for thousands of terms
against the same large corpus**, re-scanning the whole text every time:

```python
for term in ten_thousand_terms:
    if term in big_text:               # scans all 200 MB, once PER term -> O(terms × text)
        hits.append(term)
```

Need 1 and 2 use a regex engine to find a **fixed literal** — paying for pattern compilation
and engine machinery you don't need. Need 3 re-scans the entire corpus thousands of times.
All three pick a heavier tool than the job requires.

### What's really going on

"Search" isn't one operation — the right tool depends on *what* you're matching and *how
often*:

- **Fixed literal, occasionally** → use plain **`in`** (membership) and **`str.find`/
  `.index`/`.count`**. These are simple substring operations implemented in fast C; they
  don't compile a pattern and beat regex for literal matches.
- **A *pattern* (shape, alternatives, wildcards)** → use **regex** (4.2/4.3). Regex earns its
  cost only when you genuinely match a shape, not a fixed string.
- **The same large text searched many times** (many queries against one corpus) → don't
  re-scan; build an **index** once (a `set` of tokens, an inverted index, or a real
  full-text index) and answer each query in O(1)–O(log n). Scanning N-character text for Q
  queries is O(N×Q); indexing makes it O(N) to build + O(1) per query.

The instinct to "just use regex for everything" is the trap: it's the right tool for
*patterns*, the wrong (slower, heavier) tool for *literals*, and irrelevant when the real fix
is an index.

### The move

Use **`in` / `.find` / `.count`** for literal one-off searches; reserve **regex** for actual
patterns; build a **set or inverted index** when you query the same text repeatedly:

```python
if "ERROR" in text:                       # literal membership — fast, no regex
    alert()

pos = text.find("timeout")                # first index, or -1 if absent
n = text.count("timeout")                 # how many occurrences

words = set(text.split())                 # build a token index ONCE...
hits = [t for t in terms if t in words]   # ...then each lookup is O(1)
```

### Why it works

**`x in text`** and **`text.find(x)`** run a substring search in optimised C (CPython uses an
efficient algorithm internally), with no pattern to compile and no regex engine overhead. For
a fixed string they're both simpler to read and faster than `re.search(re.escape(x), text)`.
`.find` returns the index (or `-1`), `.index` does the same but raises if absent, and
`.count` returns the number of non-overlapping occurrences — covering "is it there", "where",
and "how many" without a regex.

**Regex** pays off precisely when the target is a *shape* — `r"\d{4}-\d{2}-\d{2}"`,
`r"error|warning|fatal"`, `r"user_\w+"` — things `in`/`find` cannot express. Using it for a
plain literal spends the engine's setup cost for nothing.

For **repeated** queries, the win is algorithmic, not constant-factor. Scanning a 200 MB
string is O(N); doing that once per term over 10,000 terms is O(N × Q) — minutes of work.
Building a `set` of the text's tokens is O(N) **once**, after which `term in word_set` is an
O(1) hash lookup — so 10,000 queries cost ~10,000 O(1) lookups, not 10,000 full scans. For
*phrase* or *ranked* search over many documents, the same idea scales up to an **inverted
index** (term → list of documents/positions), which is what search engines like Whoosh,
Elasticsearch, or SQLite FTS build for you.

### The code, every line explained

```python
text = "2026-06-18 ERROR timeout after 30s; retry; ERROR again; timeout"

# --- Need 1: "is this literal present?" -> in (membership) --------------
if "ERROR" in text:        # substring search in C; returns True/False. No regex needed.
    pass
# Compare: re.search(r"ERROR", text) compiles a pattern and runs the engine — slower,
# and you must re.escape() the string if it might contain regex metacharacters.

# --- Need 2: "where / how many?" -> find / index / count ----------------
i = text.find("timeout")   # 17  — index of FIRST occurrence; -1 if not found
j = text.find("timeout", i + 1)  # 60 — search again from just past the first hit
n = text.count("timeout")  # 2   — number of non-overlapping occurrences
# .index("x") is like .find but RAISES ValueError if absent (use when "missing" is a bug).
# To get ALL positions of a literal, loop with find:
def all_positions(s, sub):
    out, start = [], 0
    while (k := s.find(sub, start)) != -1:   # walrus (:=): assign and test in one step
        out.append(k)
        start = k + 1                         # advance past this hit to find the next
    return out
print(all_positions(text, "ERROR"))          # [11, 38]

# --- When regex is the RIGHT tool: a PATTERN, not a literal -------------
import re
levels = re.findall(r"\b(?:ERROR|WARN|FATAL)\b", text)   # alternation — can't do with `in`
dates  = re.findall(r"\d{4}-\d{2}-\d{2}", text)          # a SHAPE — can't do with find
# If the thing you search varies in form, regex; if it's one fixed string, in/find.

# --- Need 3: repeated queries on the same text -> INDEX once ------------
big_text = open("corpus.txt").read()    # imagine this is huge
word_set = set(big_text.split())        # build a token index ONCE: O(N)
terms = ["timeout", "kafka", "oom", ...]  # thousands of terms to check
hits = [t for t in terms if t in word_set]   # each check is O(1) hash lookup, not a scan
# Re-scanning big_text per term would be O(N) EACH TIME -> O(N × len(terms)). The set
# turns Q scans into Q O(1) lookups. (Caveat: split() matches WHOLE tokens, not substrings.)

# --- Substring index for MANY substring queries: build position map -----
from collections import defaultdict
# For whole-word lookups with positions, map each token to where it occurs:
positions = defaultdict(list)
for idx, word in enumerate(big_text.split()):
    positions[word].append(idx)          # term -> [word-positions]  (a tiny inverted index)
# Now "where does 'timeout' occur?" is positions["timeout"] — instant, no rescan.

# --- For real full-text/phrase/ranked search: use a library -------------
# SQLite FTS5, Whoosh, or Elasticsearch build proper inverted indexes with phrase,
# prefix, and relevance ranking. Reach for these once "grep the file" stops scaling.
```

### Impact

- **Speed on the common case:** `in`/`find` beat regex for literal matches by skipping
  compilation and engine overhead — meaningful when scanning large strings or in hot loops.
- **Algorithmic win on repeated search:** indexing turns O(N × Q) re-scanning into O(N) build
  + O(1) per query — the difference between seconds and minutes (or hours) at scale.
- **Right-sized tooling:** matching the tool to the need keeps code simpler and clearer —
  regex only where a *pattern* genuinely exists, an index only where queries repeat.

### Pros & cons / when NOT to

**Use `in`/`find`/`count` when:** the target is a **fixed literal** and you search it
occasionally. **Use regex when:** you match a **pattern** (alternatives, shapes, wildcards).
**Build an index when:** you run **many queries** against the **same** large text.

**Watch out / when NOT to:**
- **`split()`-into-a-set matches whole tokens, not substrings.** `"time" in word_set` is
  `False` even if `"timeout"` is present, because the *token* is `"timeout"`. Use a set for
  whole-word lookups; for substring queries you need a substring index (suffix automaton/
  array) or a real search engine.
- **Don't over-index for a one-off.** Building an index costs O(N) up front — pointless if
  you only search once. The index pays off across *many* queries.
- **`re.escape` literals you feed to regex.** If you do use regex with a string that may
  contain metacharacters (`.`, `*`, `(`), wrap it in `re.escape(s)` or it'll match the wrong
  thing — another reason to prefer `in`/`find` for literals.
- **Memory of `.read()`:** loading a 200 MB file as one string to search costs 200 MB of RAM.
  For huge files, scan line-by-line (`for line in f:` — a generator, 1.2/2.13) or memory-map
  it (`mmap`) instead of reading it whole.

### Where this shows up

- **Real work — log triage:** `"ERROR" in line` while streaming a log file is the everyday
  fast filter; regex only when you match a *shaped* field (timestamp, request id).
- **Real work — keyword tagging / filtering:** checking thousands of documents against a term
  list — build a set/inverted index of each document's tokens rather than re-scanning text
  per term.
- **Real work — search features:** "contains this term?" lookups in an app graduate from
  `in`/`find` to SQLite FTS or Elasticsearch once you need phrases, ranking, or prefix search
  at scale.
- **Pattern mapping (secondary):** substring search is the classic **string-matching** family
  — `str.find` is the built-in stand-in for KMP/Rabin–Karp (Area 11), and "preprocess into an
  index, then answer queries fast" is the inverted-index / hashing pattern behind autocomplete
  and the trie problems (11.25).

[↑ Back to top](#contents)

