# AI / ML Study Plan

A personal study and interview-preparation repository for **Machine Learning Engineering**,
covering Python problem-solving craft, ML/DL/LLM engineering, data-structures-and-algorithms,
and a complete Senior-ML-Engineer interview-prep track — plus working notes and mini-books on
RAG evaluation, LLM token optimisation, and related projects.

The material is written in plain, layman-but-technical English: every concept leads with the
*problem* before the jargon, every term is explained inline, and examples are drawn from real
data / ML / API / systems work.

---

## Repository structure

```
AI-ML-Study-plan/
├── README.md                          ← you are here
├── google-python-problem-solving/     ← the main field guide + interview prep
└── mydocs/                            ← working notes, mini-books, project docs
    ├── Copilot/                       (RAG/LLM mini-books, study plans, goals)
    └── SS/                            (architecture & lambda notes)
```

---

## Part 1 — `google-python-problem-solving/`  (the field guide)

A **scenario-based** guide that trains the reflex *"I'm feeling X → the real problem is Y →
reach for Z."* It is **not** a syntax tutorial — it's a library of ~190 real situations a
working ML/data engineer hits, each in a fixed 8-part format:

> situation (with concrete sample data) → what's really going on → the move → why it works →
> code with every line explained → impact → pros/cons & when-not-to → where it shows up.

### The 11 areas (the core guide)

| Area | File | Theme |
|---|---|---|
| 1 | `area_1_pythonic_craft.md` | Pythonic craft & vocabulary (comprehensions, generators, decorators, context managers, dunders…) |
| 2 | `area_2_memory_performance.md` | Memory & performance (profiling, O(n²) smells, `__slots__`, caching, vectorising) |
| 3 | `area_3_data_wrangling.md` | Data wrangling & data engineering (CSV/JSON/Parquet, pandas, dates, dedup/group/join) |
| 4 | `area_4_text_content.md` | Text & content processing (normalisation, regex, hashing, chunking, fuzzy match) |
| 5 | `area_5_apis_concurrency.md` | APIs, I/O & concurrency (threads, async, retries, rate limits, polling, streaming) |
| 6 | `area_6_parallelism_scale.md` | Parallelism & scale (multiprocessing, the GIL, pickling cost, shared memory) |
| 7 | `area_7_robustness_batch.md` | Robustness & batch survival (validation, idempotency, checkpointing, atomic writes) |
| 8 | `area_8_ml_broad.md` | ML scenarios (leakage, imbalance, metrics, CV, seeds, serving skew) |
| 9 | `area_9_dl_llm.md` | DL & LLM (tensor shapes, GPU OOM, tokens, chunking, RAG, parsing LLM output) |
| 10 | `area_10_design_shipping.md` | Design & shipping (dataclasses, dependency injection, tests, feature flags) |
| 11 | `area_11_dsa_patterns.md` | LeetCode / DSA patterns (hashing, two-pointers, sliding window, DP, graphs…) |

Start at **`INDEX.md`** — it lists every scenario with clickable links and a per-area map.
Each area file also has its own clickable table of contents and "back to top" links.

---

## Part 2 — Interview prep (inside `google-python-problem-solving/`)

A complete, self-contained prep track for **Senior ML Engineer** loops at Google, Meta,
Amazon, Nvidia, Anthropic, OpenAI, and Netflix. Start at **`INTERVIEW_PREP.md`** for the
company-by-company roadmap and an 8-week schedule.

| Doc | File | What it builds |
|---|---|---|
| 1 | `interview_area_12_dsa_problem_bank.md` | DSA problem bank — 12 patterns, ~150 curated problems, timed-rep method, 5 mock solves with full answers |
| 2 | `interview_area_13_ml_system_design.md` | ML system design — a 7-step framework, 2 full worked designs (recsys + RAG), cheat-sheet, 2 mocks with answers |
| 3 | `interview_area_14_behavioral_leadership.md` | Behavioural / Leadership — STAR method, Amazon's 16 LPs, an 8-story bank, 3 full model answers |
| 4 | `interview_area_15_mock_interviews_communication.md` | Mock interviews & communication — think-aloud method, interview lifecycle, 2 fully annotated transcripts |

**Each company's loop is tagged** throughout: the "grind" cluster (Google/Meta/Amazon) gates on
DSA; the "practical" cluster (Anthropic/OpenAI/Netflix) weights system design + communication;
Nvidia leans systems/performance (and often C++/CUDA, which is noted as out-of-scope).

---

## Part 3 — `mydocs/`  (working notes & mini-books)

Personal project notes, study plans, and longer-form mini-books:

- **`Copilot/`** — mini-books and references including LLM RAG-evaluation with dbt, advanced
  LangGraph token optimisation, multi-model strategy, auto-summary rules/plans, and annual
  study/goal timelines.
- **`SS/`** — architecture notes and a Lambda data-retention prompt for a scheduling-service
  project (internal service names generalised).

> These are working documents (some also provided as `.docx`), kept here as a personal
> knowledge base alongside the structured field guide.

---

## How to use this repo

1. **Learning the craft:** work through `google-python-problem-solving/` area by area via
   `INDEX.md`. Read each scenario, then try to reproduce the "move" from memory.
2. **Interview prep:** open `INTERVIEW_PREP.md`, pick your target companies, follow the
   roadmap and 8-week schedule, and do the mocks **out loud and timed**.
3. **Reference:** dip into `mydocs/` for the RAG/LLM mini-books and project notes.

---

## Conventions

- **Plain English first** — concepts are framed as a relatable problem before any jargon;
  terms are defined inline (no separate glossary).
- **Concrete examples** — real sample data, real outputs, real failure modes.
- **British/Indian spelling** (optimise, behaviour, normalise) throughout.
