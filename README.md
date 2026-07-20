# 🚀 AI / ML Study Plan

> A self-built study & interview-prep library for **Machine Learning Engineers** — Python craft,
> DSA, ML system design, shell scripting, and full interview tracks. Everything is written
> **problem-first**: the situation before the jargon, every term explained inline, every example
> concrete (real data, real outputs, dry-runs).

---

## ⚡ At a glance

Pick the folder that matches your goal, then jump to its section below.

| 📁 Folder | What it is | Language | Start here |
|---|---|---|---|
| [`google-python-problem-solving/`](google-python-problem-solving/) | ~190 Python problem-solving scenarios + a 4-part interview-prep track | English | `INDEX.md` |
| [`dsa_guide/`](dsa_guide/) | 13-chapter DSA guide (arrays → DP), senior-interview lens | Hinglish | `01_interview_strategy.md` |
| [`system_design_course/`](system_design_course/) | 14-chapter AI/ML system-design course (fundamentals) | Hinglish | `00_START_HERE.md` |
| [`system_design_course_advanced/`](system_design_course_advanced/) | Principal-level deep-dives (LLM serving at scale) | Hinglish | `A1_llm_inference_serving.md` |
| [`shell_scripting_guide/`](shell_scripting_guide/) | 18-chapter Unix/Linux/bash guide (terminal → production) | Hinglish | `01_terminal_aur_shell.md` |
| [`RAG_Copilot Tutorials/`](RAG_Copilot%20Tutorials/) | Long-form mini-books & project notes (RAG eval, LangGraph) | English | `Copilot/` |

> **Two languages by design:** the Python guide & interview prep are in **English**; the DSA,
> system-design, and shell guides are in **Hinglish** (Hindi + English, Roman script) — a plain,
> conversational "senior explaining over chai" style. Technical terms stay in English throughout.

---

## `google-python-problem-solving/`

A **scenario-based** field guide (~190 scenarios) that trains the reflex *"I'm feeling X → the
real problem is Y → reach for Z."* Not a syntax tutorial — a library of real situations a working
ML/data engineer hits, each in a fixed 8-part format (situation → what's really going on → the
move → why → line-by-line code → impact → pros/cons → where it shows up).

- **11 core areas** (`area_1` … `area_11`): Pythonic craft · memory & performance · data wrangling
  · text processing · APIs/I-O/concurrency · parallelism & scale · robustness & batch · ML
  scenarios · DL & LLM · design & shipping · DSA patterns. (Plus `band_a_data.md` on getting the
  right answer out of in-memory data.)
- **4-part interview track** (`interview_area_12`–`15`): DSA problem bank · ML system design ·
  behavioural/leadership · mock interviews & communication — tagged per company (Google, Meta,
  Amazon, Nvidia, Anthropic, OpenAI, Netflix).

▶️ Start at **`INDEX.md`** (every scenario, clickable) or **`INTERVIEW_PREP.md`** (company roadmap
+ 8-week schedule).

---

## `dsa_guide/`

A 13-chapter DSA guide built for a **Senior ML Engineer (8–10 YOE)** targeting Google/Microsoft —
average coder → DSA-confident. **Pattern-first** (not a 500-problem grind), with a senior lens:
fluency, clean code, communication, and *what to skip*. Every problem shows a clear
**Input → Output** example and a **dry-run trace**; Python throughout.

- **Ch 01–02:** interview strategy (per-topic weightage, what to skip, how to talk through a
  problem) + Big-O foundations.
- **Ch 03–12:** arrays · hashing · strings · linked-lists/stacks/queues · recursion & backtracking
  · trees · heaps · graphs · binary-search & sorting · dynamic programming & greedy.
- **Ch 13:** a master **signal → pattern** cheat-sheet + honest self-assessment.

▶️ Start at **`01_interview_strategy.md`**.

---

## `system_design_course/`

A 14-chapter course teaching **AI/ML system design from first principles** — how to *think*, how
to *act*, how to *draw*, and which tool to use when (and when NOT). Trains the senior mindset:
**requirements → constraints → trade-offs**, with pros/cons on every choice.

- **Thinking & process:** mindset · 7-step method · diagramming · napkin-math (capacity estimation).
- **Tools & ML specifics:** building blocks (12 tools, each with when/when-not) · ML system design
  (feature stores, serving, RAG) · reference blueprints · anti-patterns · end-to-end case studies.
- **Operating it:** tool cheat-sheet · MLOps lifecycle · cost/FinOps · security & privacy.

▶️ Start at **`00_START_HERE.md`**.

---

## `system_design_course_advanced/`

The principal-level layer — built to answer *"If Google asks what system design you did in
production and why this tool not that, what will you say?"* Decision matrices, real numbers,
"why X not Y" with breaking points, and production failure modes.

- **`A1_llm_inference_serving.md`** — LLM inference serving at scale: KV-cache math, continuous
  batching, PagedAttention, vLLM vs TGI vs Triton vs TensorRT-LLM, tensor/pipeline parallelism,
  quantization, speculative decoding, capacity & cost modelling, the p99 "latency cliff".
- **`SAMPLE_tutorial_style.md`** — a ground-up tutorial treatment of one concept (intuition →
  mechanics → trace → diagram → tool table → examples).

---

## `shell_scripting_guide/`

An 18-chapter guide from *"what even is a terminal"* to production-grade scripts and Dockerfile
commands. Its signature: it breaks down the **literal meaning of every symbol and flag** (why
`$0`, why `/bin/bash`, what `-rf` really does), with examples and real scenarios throughout.

- **Basics:** terminal/shell/kernel & types · filesystem navigation · command anatomy (flags,
  `--help`, PATH) · file operations.
- **Core scripting:** `$` & variables · pipes/redirects & the Unix philosophy · permissions ·
  editing in the terminal (nano/VIM/`.zshrc`) · conditions · loops & functions · arguments.
- **Applied:** text processing (grep/sed/awk) · processes & jobs · error handling · writing the
  right commands for production/Dockerfiles · handy-tools cheat-sheet · common gotchas.

▶️ Start at **`01_terminal_aur_shell.md`**.

---

## `RAG_Copilot Tutorials/`

The deepest material in this repo — long-form **mini-books** and real project notes built around
**DC-Copilot**, a production RAG system for maintenance work orders. Most of it lives in
**`Copilot/`**; a small **`SS/`** subfolder holds scheduling-service architecture notes.

### 📕 The two flagship mini-books (`Copilot/`)

**1. `minibook_llm_rag_evaluation_dbt.md` — LLM Evaluation, Advanced RAG, Re-Ranking & AWS DBT**
*(~14,000 lines · "Zero to Expert")*
A practitioner's guide to **knowing whether your RAG system is actually good**. Sections are
tagged **(Depth)** = exhaustive first-principles deep-dive, or **(Med)** = concise-but-complete.
Every concept is grounded in the DC-Copilot RAG system alongside general examples.
- **Evaluation metrics, one per section** — BLEU, ROUGE, METEOR, BERTScore, Perplexity; the full
  **RAGAS** suite (Faithfulness, Answer Relevancy, Context Precision/Recall/Relevancy, Answer
  Correctness & Semantic Similarity); Human eval; **LLM-as-a-Judge**; custom domain metrics — plus
  a head-to-head comparison of all of them.
- **Advanced RAG & Re-Ranking** — retrieval quality, re-ranking methods.
- **AWS + dbt** — data/transformation layer for the eval pipeline.
- Ends with a **glossary & index** defining every term used.

**2. `langgraph_minibook_advanced_token_optimization.md` — Advanced LangGraph & Token/Prompt
Optimization** *(~30,000 lines · 20 chapters)*
The Production Engineer's minibook, in two parts, where **every chapter follows an identical
23-section template** (Also-Known-As → layman explanation → depth → do's/don'ts → real scenarios…)
so topics compare side-by-side.
- **Part 1 — Advanced LangGraph:** human-in-the-loop, graph persistence & time-travel debugging,
  dynamic graph construction, multi-agent orchestration, streaming/async, error-recovery & retry
  nodes, LangSmith observability, subgraph composition, map-reduce patterns, framework alternatives.
- **Part 2 — Token/Prompt Optimization:** context-window management, message compaction/
  summarization, and cost/latency reduction techniques.

### 🛠️ Copilot project notes (`Copilot/`)

Real design & implementation docs from the DC-Copilot work (internal service names generalised):
- **`multi_model_strategy_plan.md`** — per-node model routing for the chat API & auto-summarisation
  (routing cheap tasks to `gpt-4o-mini`) to cut ~30% latency; includes before/after latency
  breakdowns.
- **`rules_auto_summary_source_type_rules.md`** — the "golden rule" + six work-order source-type
  cases for auto-summary (asset/site/location combinations).
- **`auto_summary_all_source_types_plan.md`** — implementation plan to extend auto-summary to all
  source types (site/location array handling, test status).
- **`MINIBOOK_CONTINUATION_PROMPT.md`** & **`PROMPT_FORMAT_CH7_DOCX.md`** — the authoring prompts &
  23-section template used to generate/format the mini-books consistently.

### 📅 Career tracking (`Copilot/`)

- **`annual_goals_and_study_timeline.md`** — 7 annual goals (production excellence, LLM/RAG depth,
  infra ownership, platform thinking, collaboration, tech leadership, growth) + a phased study plan.
- **`annual_goals_tracking.md`** — the live progress tracker: per-phase topic checklists
  (LLM/RAG eval, Terraform, advanced RAG, re-ranking, dbt) + a weekly manager-review log.

### `SS/`
Scheduling-service architecture notes — `ARCHITECTURE_DIFFERENCES.md` (current vs target) and a
Lambda data-retention prompt.

---

## 🎯 How to use this repo

| Your goal | Where to go |
|---|---|
| Sharpen Python / ML-engineering reflexes | `google-python-problem-solving/` → `INDEX.md` |
| Prep a Senior ML interview loop | `INTERVIEW_PREP.md` + `dsa_guide/` + `system_design_course*/` |
| Learn / revise DSA | `dsa_guide/` — read a chapter, then practise that pattern |
| Learn ML system design | `system_design_course/` → `system_design_course_advanced/` |
| Get comfortable in the terminal | `shell_scripting_guide/` |
| Reference RAG/LLM project work | `RAG_Copilot Tutorials/` |

> **On practice:** these guides teach the *patterns and reasoning* — a strong base, but not a
> substitute for doing. For DSA especially, pair the guide with ~100–150 LeetCode problems
> (pattern-wise) and a few timed, spoken mock interviews.

---

## ✍️ Conventions

- **Problem-first** — every concept starts as a relatable problem before any jargon; terms defined
  inline (no separate glossary).
- **Concrete examples** — real sample data, real outputs, real failure modes, dry-run traces.
- **Navigable** — every doc has its own clickable table of contents and "back to top" links.
- **Spelling** — British/Indian (optimise, behaviour, normalise) in the English docs.

---

*A personal, evolving knowledge base — built to learn deeply and interview confidently.* 🌱
