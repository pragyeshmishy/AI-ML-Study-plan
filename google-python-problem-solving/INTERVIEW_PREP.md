# Senior ML Engineer — Interview Prep Index

A complete, self-contained prep track for **Senior Machine Learning Engineer** interviews at
Google, Meta, Amazon, Nvidia, Anthropic, OpenAI, and Netflix. Four documents cover the four
things these loops actually test, each with explanations, examples, and **mock questions with
full answers**. You shouldn't need an outside source.

The four prep docs build on the 11-area Python problem-solving field guide (Areas 1–11) — they
reference it heavily, so keep both open.

---

## The four documents

| Doc | File | What it builds | Read if targeting |
|---|---|---|---|
| **1. DSA Problem Bank** | [interview_area_12_dsa_problem_bank.md](interview_area_12_dsa_problem_bank.md) | Speed on coding problems — 12 patterns, ~150 curated problems, 8-week plan, 5 mock solves | Google, Meta, Amazon (gate); others (screen) |
| **2. ML System Design** | [interview_area_13_ml_system_design.md](interview_area_13_ml_system_design.md) | Designing whole ML systems — 7-step framework, 2 full designs, cheat-sheet, 2 mocks | **All 7** (often decisive) |
| **3. Behavioural / Leadership** | [interview_area_14_behavioral_leadership.md](interview_area_14_behavioral_leadership.md) | STAR stories — Amazon's 16 LPs, an 8-story bank, question bank, 3 model answers | **All 7**; decisive at Amazon |
| **4. Mock Interviews & Communication** | [interview_area_15_mock_interviews_communication.md](interview_area_15_mock_interviews_communication.md) | Thinking out loud — think-aloud method, interview lifecycle, 2 full annotated transcripts | **All 7** (scored everywhere) |

> **The one-line model:** *recognise the pattern (Area 11) → have the reps to code it fast
> (Doc 1) → design the system and reason about trade-offs (Doc 2) → tell structured stories about
> how you work (Doc 3) → communicate clearly throughout (Doc 4).* That's what the loop measures.

---

## How the companies differ (and where to spend your time)

Three clusters, because the *same* prep is weighted very differently across them:

**1. The "grind" cluster — Google, Meta, Amazon.** DSA throughput is the gate. **Doc 1 is your
priority** — you must be fast and optimal. Then Docs 2–4.
- **Meta** — fastest/most ruthless on DSA (2 problems in ~40 min) + strong system design + impact-
  focused behavioural.
- **Google** — hardest DSA + strictest complexity/clean code + scale-heavy system design +
  "Googleyness".
- **Amazon** — medium DSA but **behavioural (Doc 3) is decisive** (16 LPs, Bar Raiser). Don't
  under-prepare Doc 3 for Amazon.

**2. The "practical" cluster — Anthropic, OpenAI, Netflix.** Less LeetCode-grind, more realistic
coding + system design + judgment. **Docs 2 and 4 are your priority**, and the underlying Areas
1–10 (especially 5, 7, 9, 10) are genuinely strong prep here.
- **Anthropic / OpenAI** — collaborative/pair-programming coding; **LLM system design** (RAG,
  agents, moderation, evals — Doc 2's design #2); mission/safety-minded behavioural.
- **Netflix** — senior judgment and candour over puzzle difficulty; fewer rounds, deeper
  trade-off reasoning; strong system design + crisp communication.

**3. The "systems/perf" cluster — Nvidia.** Performance, parallelism, GPU. Areas 2, 6, 9 align
well conceptually, but **many roles want C++/CUDA**, which these (Python) docs don't cover —
learn that separately. Use Doc 2 for training-infra/inference-service design questions.

---

## Per-company prep roadmap

Each row: the rounds you'll face and **where to spend effort** (★ = highest priority).

### Google
- **Rounds:** 4–5 coding (DSA), 1 ML system design, 1 "Googleyness & Leadership".
- **Priority:** ★ Doc 1 (hardest DSA, strict complexity/clean code) · ★ Doc 2 (scale: two-stage
  recsys, billions QPS) · Doc 4 (named on scorecard) · Doc 3 (collaboration/ambiguity).

### Meta
- **Rounds:** 2 coding (fast — 2 problems/45 min), 1–2 ML system design, 1 behavioural.
- **Priority:** ★ Doc 1 (speed + optimality is everything — drill timed reps) · ★ Doc 2 (feed/
  recsys ranking) · Doc 4 (must communicate *and* move fast) · Doc 3 (impact, conflict).

### Amazon
- **Rounds:** 2–3 coding (medium), 1 ML system design, **behavioural woven throughout (LPs)**.
- **Priority:** ★ Doc 3 (the 16 LPs can be decisive; Bar Raiser) · Doc 1 (medium DSA, very
  doable) · Doc 2 (practical: fraud, product recs) · Doc 4. **Tag every story to an LP.**

### Nvidia
- **Rounds:** coding (often C++/CUDA), systems/performance design, conventional behavioural.
- **Priority:** **C++/CUDA + Areas 2/6/9 (external to these docs)** · ★ Doc 2 (training-infra /
  inference-service design) · Doc 1 (patterns transfer; language doesn't) · Doc 3.

### Anthropic
- **Rounds:** practical/pair-programming coding, **LLM system design**, mission/safety behavioural.
- **Priority:** ★ Doc 2 (RAG/agents/moderation/evals — design #2 + Area 9) · ★ Doc 4 (pair format
  = communication *is* the interview) · Doc 3 (judgment, responsibility) · Doc 1 (lighter; a
  screen may include it). Areas 5/7/9/10 are strong prep.

### OpenAI
- **Rounds:** realistic coding, system design (incl. LLM + infra/scale), behavioural.
- **Priority:** ★ Doc 2 (LLM systems + scale) · ★ Doc 4 · Doc 1 (correctness/clean realistic code
  over puzzle difficulty) · Doc 3. Areas 5–9 strong.

### Netflix
- **Rounds:** fewer, deeper; senior coding, system design, culture/judgment behavioural.
- **Priority:** ★ Doc 2 (deep trade-off reasoning) · ★ Doc 3 (culture memo: candour, independent
  judgment) · ★ Doc 4 (crisp communication) · Doc 1 (lighter than the grind cluster). Areas 7/10/5
  match the senior-ownership bar.

---

## A suggested 8-week schedule (adjust to your timeline)

| Weeks | Focus | Docs |
|---|---|---|
| 1–2 | DSA patterns 1–6 + timed reps; start recording mocks | Doc 1, Doc 4 |
| 3–4 | DSA patterns 7–12 + timed reps; write your 8 STAR stories | Doc 1, Doc 3, Doc 4 |
| 5 | ML system design framework + work both designs; keep DSA reps warm | Doc 2 |
| 6 | More system design (do the mocks); rehearse STAR stories aloud | Doc 2, Doc 3 |
| 7 | **Mixed-mode** DSA (no pattern hint); full mock loops with a partner | Docs 1–4 |
| 8 | Company-specific polish (LPs for Amazon, LLM design for Anthropic/OpenAI, etc.); rest before the loop | All |

> **Two rules that matter more than the schedule:** (1) **timed, spoken, recorded practice** —
> not silent solving (Doc 4); (2) **re-solve problems and re-tell stories**, don't just consume
> them once. Spaced repetition is what converts "I understand it" into "I can do it under
> pressure."

---

## What these docs deliberately do NOT cover

So you know where to supplement:
- **C++/CUDA** (needed for some Nvidia/infra roles) — language-specific, learn separately.
- **Live human mock partners** — use Pramp / interviewing.io; a real listener is irreplaceable
  (Doc 4 explains how).
- **Company-specific question leaks** — check Glassdoor/Blind for recent, role-specific questions
  close to your loop.
- **Negotiation** — a separate skill once you have offers.

Everything else — patterns, problems, system-design frameworks, behavioural stories, and
communication technique, all with worked examples and answers — is in Docs 1–4.

