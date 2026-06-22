<a id="contents"></a>
# Area 13 — ML System Design (Interview Prep)

This is the round that **every** company on your list tests for a Senior ML Engineer, and the
one most candidates are weakest at — because it's not about code, it's about **designing a
whole ML system out loud**: from a vague business ask to data, features, model, serving,
monitoring, and the trade-offs at each step.

This document gives you a **repeatable framework**, then walks two complete designs end to end,
then gives you **mock questions with full answers**. It's written so you can prepare entirely
from here.

---

## Which company does this target?

> **All 7 companies test ML system design at the senior level — it's often the *deciding*
> round.** But the flavour differs:
>
> - **Google / Meta** — scale and rigour: "design YouTube recommendations / the News Feed
>   ranker". They probe data pipelines, candidate generation vs ranking, online/offline metrics,
>   and serving at billions of QPS.
> - **Amazon** — practical + ownership: "design product recommendations / fraud detection".
>   Expect Leadership-Principles framing (Area 14) woven in: how you'd own it, handle failures.
> - **Netflix** — senior judgment over breadth: "design the recommendation system / the
>   thumbnail personaliser". Fewer rounds, deeper reasoning; they want staff-level trade-off
>   thinking.
> - **Anthropic / OpenAI** — increasingly **LLM-system** design: "design a RAG system / an
>   agent / an eval pipeline / content moderation with an LLM". This is where Area 9 pays off.
> - **Nvidia** — leans toward training-infra and performance: "design a distributed training
>   pipeline / a high-throughput inference service". Areas 6 & 9 matter most.
>
> **Sections below are tagged with the companies they most apply to.**

---

## Why ML system design is different from software system design

**The explanation:** a normal system-design interview ("design a URL shortener") is about
APIs, databases, caches, load balancers. ML system design includes all of that **plus** the
parts unique to machine learning: where the training data comes from, how features are
computed (and kept consistent between training and serving), how the model is trained,
evaluated, deployed, and monitored — and crucially, **how you measure success** when the system
is probabilistic, not deterministic.

**Why it trips people up:** candidates either (a) dive straight into model architecture
("I'd use a transformer") while ignoring data, serving, and metrics — which is junior behaviour,
or (b) treat it like pure software design and never mention training data, features, or model
evaluation. The senior signal is covering the **whole lifecycle** and reasoning about
**trade-offs** at each stage.

> **Impact:** at the senior level, *how you scope and structure* the problem matters more than
> the specific model you pick. An interviewer learns more from "here are the three places this
> could fail and how I'd measure each" than from "I'd use XGBoost."

---

## Contents

- [The 7-step framework (use this for EVERY question)](#framework)
- [Worked design 1 — Recommendation system (Netflix/YouTube)](#design1)
- [Worked design 2 — RAG system over company docs (Anthropic/OpenAI)](#design2)
- [Cheat-sheet: components & trade-offs](#cheatsheet)
- [Mock questions + full answers](#mock)

---

<a id="framework"></a>
## The 7-step framework (use this for EVERY question)

**Why a framework?** Under pressure, candidates ramble or skip whole areas. A fixed sequence
means you *always* cover the lifecycle and signal seniority by structure alone. Say the steps
out loud — "Let me start by clarifying requirements, then talk data, features, model, serving,
metrics, and finally the failure modes."

**Step 1 — Clarify requirements & scope.** *Why:* the ask is deliberately vague; jumping to a
solution without scoping is the top junior mistake. Ask: What's the business goal? What's the
scale (users, QPS, data volume)? Latency budget (real-time vs batch)? What does "good" mean?
*Example questions to ask:* "Is this real-time serving or a daily batch job?" "How many
predictions per second at peak?" "What's the cost of a false positive vs false negative?"

**Step 2 — Define the ML problem & success metrics.** *Why:* you must translate the business
goal into a measurable ML objective (Area 8.5). Distinguish **offline metrics** (precision/
recall/AUC on held-out data — what you optimise during development) from **online metrics**
(click-through, revenue, engagement — what the business actually cares about, measured via A/B
test). *Example:* "Offline I'll track recall@10; online I'll A/B test on watch-time, because a
better offline score doesn't guarantee a better product (Goodhart's law)."

**Step 3 — Data.** *Why:* models are only as good as their data. Where does training data come
from? How is it labelled? How much? Class imbalance (8.4)? How do you avoid leakage (8.1)?
*Example:* "Labels are implicit — a click is a positive, an impression-without-click is a
negative — but I must handle position bias and avoid leaking future info."

**Step 4 — Features.** *Why:* feature quality usually beats model choice. What features, from
what sources? How are they computed and stored? The big trap: **train/serve skew** (8.16) —
features must be computed *identically* offline and online (a feature store solves this).
*Example:* "User features (history), item features (metadata), context (time/device); served
from a feature store so training and serving use the same computation."

**Step 5 — Model.** *Why:* now (not first!) pick an approach, justifying it by the constraints
above. Start simple (a baseline), then justify complexity. For large systems, the
**candidate-generation → ranking** two-stage pattern is standard. *Example:* "Baseline:
logistic regression on hand features. Then a two-tower model for candidate retrieval + a
gradient-boosted ranker, because we can't score millions of items per request."

**Step 6 — Serving & scale.** *Why:* a model that can't serve within the latency/cost budget is
useless. Real-time vs batch? How do you scale to the QPS? Caching (precompute embeddings)?
*Example:* "Precompute item embeddings offline; at request time, retrieve nearest neighbours
(ANN index) then rank the top few hundred — keeps p99 under 100 ms."

**Step 7 — Monitoring, failure modes & iteration.** *Why:* this is the senior differentiator.
How do you know it's working in production? **Data drift** (8.16), model staleness, feedback
loops, fallbacks when the model is down (5.10). *Example:* "Monitor feature distributions for
drift, track online metrics with alerts, retrain on a schedule, and fall back to a
popularity-based recommender if the model service fails."

> **The flow, in one breath:** *clarify → ML problem + metrics → data → features → model →
> serving → monitoring/failure-modes.* If you cover these seven, in order, you cannot give a
> junior answer — even if your specific model choice is debatable.

> **Pros of the framework:** complete coverage, signals seniority, prevents rambling, gives the
> interviewer clear hooks to dig into. **Cons / when to flex:** don't rigidly recite all seven
> if the interviewer steers you deep into one (e.g. "let's focus on serving") — follow their
> lead, but mentally check you haven't dropped data or metrics entirely.

---

<a id="design1"></a>
## Worked design 1 — "Design a video recommendation system" *(target: Netflix, YouTube/Google, Meta, Amazon)*

This is the single most-asked ML system design question. Here's a full answer using the 7 steps.

### Step 1 — Clarify requirements
> "Let me clarify before designing. **Goal:** recommend videos a user is likely to watch, to
> maximise long-term engagement (watch-time), not just clicks. **Scale:** say 100M users, 10M
> videos, recommendations served in real time when a user opens the app — so **p99 latency
> under ~100 ms**. **Surface:** the home feed, ~20 recommendations. I'll assume we have watch
> history and basic video metadata."

*Why this matters:* stating scale (10M videos) immediately rules out "score every video per
request" and forces the two-stage design — showing you scope before solutioning.

### Step 2 — ML problem & metrics
> "I'll frame it as **ranking**: given a user and a candidate video, predict a score for
> expected engagement, then return the top-ranked. **Offline metrics:** recall@k and NDCG on
> held-out watch data. **Online metric (what we actually optimise):** A/B test on watch-time
> per user and retention — because optimising clicks alone leads to clickbait (Goodhart, 8.5).
> I'd guard against optimising a proxy that hurts the real goal."

### Step 3 — Data
> "**Training data** comes from logged interactions: a watch (or watch >30s) is a positive; an
> impression the user *didn't* watch is a negative. **Challenges I'd call out:** (a) **position
> bias** — items shown at the top get clicked more regardless of quality, so I'd log the
> position and correct for it; (b) **feedback loop** — the model's own recommendations generate
> the next training data, which can create a rich-get-richer bias, so I'd inject some
> exploration; (c) **leakage** (8.1) — never use future interactions as features for a past
> prediction."

### Step 4 — Features
> "Three groups: **user features** (watch history embeddings, demographics, recent activity),
> **video features** (category, length, age, historical engagement), **context** (time of day,
> device, what they just watched). Critically, these must be served from a **feature store** so
> the exact same computation runs in training and serving — otherwise **train/serve skew**
> (8.16) silently degrades the live model. Real-time features (last 5 videos watched) need
> low-latency lookup."

### Step 5 — Model: the two-stage pattern
> "I can't score 10M videos per request in 100 ms, so the standard design is **two stages:**
>
> 1. **Candidate generation (retrieval):** narrow 10M → ~1,000 cheaply. A **two-tower model** —
>    one tower embeds the user, one embeds the video — trained so a user's vector is close to
>    videos they engage with. At serving time, embed the user, then do an **approximate nearest
>    neighbour (ANN)** search over precomputed video embeddings (Area 9.14). Fast and scalable.
> 2. **Ranking:** score those ~1,000 candidates precisely with a heavier model — a gradient-
>    boosted tree or a deep network using the full feature set — and return the top 20.
>
> I'd start with a **simple baseline first** (logistic regression, or even 'most popular in your
> region') to validate the pipeline and have something to A/B against, then add the two-tower +
> ranker. Starting complex is a red flag; starting simple and justifying each addition is the
> senior move."

### Step 6 — Serving & scale
> "**Video embeddings are precomputed offline** (a daily batch job) and loaded into an ANN index
> (FAISS / a vector DB) — so retrieval is a fast vector lookup, not a model call over 10M items.
> The **user embedding** is computed at request time (or cached for a few minutes). The ranker
> scores only ~1,000 candidates, which fits the 100 ms budget. I'd **cache** recommendations for
> users who refresh quickly, and batch the ranker's scoring (Area 8.10) for throughput. To hit
> the QPS I'd horizontally scale the stateless serving layer behind a load balancer."

*Why this earns points:* "precompute embeddings, ANN retrieve, rank a few hundred" is the
exact production pattern — it shows you know how recommendations actually scale.

### Step 7 — Monitoring, failure modes, iteration
> "**Monitoring:** track online metrics (watch-time, retention) with alerts on drops; monitor
> **feature distributions for drift** (8.16) — if the live data shifts from training data, the
> model silently degrades; track serving latency (p99) and error rates. **Failure modes:** if
> the model service is down or slow, **fall back** (5.10) to a non-personalised popularity feed
> so users still get *something* — graceful degradation. **Iteration:** retrain on a schedule
> (e.g. daily) on fresh data via a **reproducible pipeline** (8.8) so the model doesn't go
> stale, and run every change as an **A/B test** (10.12) before full rollout, because offline
> wins don't always translate to online wins."

### Trade-offs to mention (the senior signal)
> - **Two-tower retrieval vs scoring everything:** two-tower is fast and scalable but less
>   precise than scoring every item; that's why we *re-rank* the candidates with a heavier model.
> - **Freshness vs cost:** real-time features and frequent retraining improve quality but cost
>   more; I'd tune retrain frequency to where the metric gains plateau.
> - **Exploration vs exploitation:** always showing the top prediction maximises short-term
>   engagement but starves new videos of data and worsens the feedback loop; I'd reserve a small
>   fraction of slots for exploration.
> - **Cold start:** new users/videos have no history — fall back to popularity / content-based
>   features until enough interaction data accumulates.

> **What a great answer covered:** the whole lifecycle, the two-stage pattern, train/serve skew,
> the offline-vs-online metric distinction, a fallback, and explicit trade-offs. Notice almost
> none of it was "which model" — that's the point.

---

<a id="design2"></a>
## Worked design 2 — "Design a RAG system to answer questions over company documents" *(target: Anthropic, OpenAI, and increasingly all)*

RAG (Retrieval-Augmented Generation) = let an LLM answer questions using *your* documents by
retrieving relevant chunks and putting them in the prompt. This is the modern LLM-system design
question. Same 7 steps; Area 9 is the foundation.

### Step 1 — Clarify requirements
> "**Goal:** a user asks a natural-language question; the system answers using our internal docs,
> with **citations** so answers are trustworthy and not hallucinated. **Scale:** say 1M documents,
> thousands of users, answers in a few seconds (streaming, 9.13). **Key constraints:** answers
> must be grounded in real docs (minimise hallucination), respect document access permissions,
> and stay within cost budget (LLM calls cost money, 5.20)."

### Step 2 — ML problem & metrics
> "Two sub-problems: **retrieval** (find the right chunks) and **generation** (write a grounded
> answer). **Retrieval metrics:** recall@k — do the retrieved chunks contain the answer?
> **Generation metrics:** faithfulness/groundedness (does the answer stick to the retrieved
> context, not hallucinate?), answer relevance, and citation accuracy. **How to measure:** build
> an **eval set** of question→correct-answer pairs; use an **LLM-as-judge** plus human spot-checks
> to score faithfulness. Online: thumbs-up/down feedback. Evaluation is the hard, often-skipped
> part — I'd call that out explicitly."

### Step 3 — Data (the documents)
> "**Ingestion pipeline:** load docs (PDF/HTML/markdown), **clean** the text (4.1), and **chunk**
> them (9.9) — this is quality-critical: chunks must be semantically coherent and overlap so
> facts spanning boundaries aren't split. I'd attach **metadata** (source, section, permissions,
> timestamp) to each chunk for citations and access control. **Embed** each chunk (9.12) and
> store in a vector DB. I'd **cache embeddings keyed by content hash** (9.12) so re-ingesting
> unchanged docs doesn't re-bill, and only re-embed changed docs (incremental, 7.5)."

### Step 4 — Features / representation
> "The 'features' here are the **embeddings** (9.14) — the query and chunks must use the **same
> embedding model** or retrieval breaks. I'd also consider **hybrid retrieval**: vector
> similarity (semantic) *plus* keyword/BM25 (exact terms like product codes, names) — pure
> vector search misses exact matches. Metadata enables **filtering** (only search docs this user
> may see)."

### Step 5 — Model / pipeline
> "The 'model' is really a **pipeline**: embed query → retrieve top-k chunks (ANN, 9.14) →
> optionally **re-rank** them with a cross-encoder for precision → assemble the top chunks into
> the prompt **within the token budget** (9.8) → call the LLM with an instruction to answer
> *only* from the provided context and cite sources → **parse/validate** the output (9.10/9.11).
> Start simple (top-k vector retrieval + a good prompt), then add re-ranking and hybrid search if
> eval shows retrieval is the bottleneck."

### Step 6 — Serving & scale
> "**Ingestion is offline/batch** (embed 1M docs once, incrementally update). **Query time** is:
> one embedding call + an ANN lookup (fast) + one LLM call (the slow, expensive part). I'd
> **stream** the answer token-by-token (9.13) so it *feels* fast. To control cost/latency I'd
> **cache** answers to repeated/similar questions, **rate-limit** per user (5.11), **batch**
> embedding calls during ingestion (5.14), and **track cost per query** (5.20). The vector DB
> scales horizontally; the LLM is the bottleneck, so caching and prompt-size control (fewer/
> smaller chunks within budget) are the main levers."

### Step 7 — Monitoring, failure modes, iteration
> "**Monitoring:** log retrieval recall and generation faithfulness on a rolling eval set;
> track cost/latency per query (5.20); collect user thumbs-up/down. **Failure modes:** if
> retrieval finds nothing relevant, the LLM should say *'I don't have information on that'*
> rather than hallucinate — I'd prompt and validate for that. If the LLM service is down, fall
> back (5.10) to returning the raw retrieved snippets. **Hallucination** is the core risk:
> mitigate with grounding instructions, citation requirements, and faithfulness checks.
> **Iteration:** docs change, so re-ingest on a schedule; evaluate retrieval and generation
> *separately* so I know which half to fix when answers are bad."

### Trade-offs to mention
> - **Chunk size (9.9):** small chunks = precise retrieval but may lack context; large chunks =
>   more context but dilute relevance and cost more tokens. Tune empirically on the eval set.
> - **Retrieve more vs less:** more chunks raise the chance the answer is present but cost more
>   tokens (9.8) and can confuse the model; re-ranking lets you retrieve broadly then keep best.
> - **Vector vs hybrid search:** hybrid catches exact terms vector search misses, at extra
>   complexity.
> - **Cost vs quality:** a bigger model / more context improves answers but costs more; pick the
>   smallest setup that passes the eval bar and track cost per query.
> - **Freshness:** real-time doc updates vs cheaper periodic re-ingestion.

> **What a great answer covered:** treating it as *retrieval + generation* with **separate
> evals**, the ingestion pipeline (chunk/embed/cache), hallucination as the central risk with
> concrete mitigations, cost control, and a fallback. The Area 9 scenarios are the building
> blocks — this design is where they all connect.

---

<a id="cheatsheet"></a>
## Cheat-sheet: components & trade-offs (quick reference)

| Component | The question to answer | Common choices / trade-off |
|---|---|---|
| **Serving mode** | Real-time or batch? | Real-time = low latency, complex; batch = simple, stale |
| **Metrics** (8.5) | Offline vs online? | Offline to develop, online A/B to decide |
| **Imbalance** (8.4) | Is the positive class rare? | Class weights / resampling; never trust accuracy |
| **Leakage** (8.1) | Could future/test info leak in? | Fit transforms on train only; time-based splits |
| **Feature store** (8.16) | Same features train & serve? | Yes → avoids train/serve skew |
| **Two-stage** | Too many items to score? | Retrieval (cheap) → ranking (precise) |
| **Embeddings/ANN** (9.14) | Semantic retrieval? | Precompute + ANN index for scale |
| **Caching** (1.13/9.12) | Repeated/expensive calls? | Cache results; persistent for cross-run |
| **Fallback** (5.10) | Model down or low-confidence? | Degrade to popularity/rules/raw results |
| **Monitoring** (8.16) | How know it works live? | Drift detection + online metrics + alerts |
| **Retraining** (8.8) | Does it go stale? | Scheduled retrain via reproducible pipeline |
| **Rollout** (10.12) | Safe to ship? | A/B test + staged rollout + instant rollback |

> **Use this as a checklist near the end:** "Have I covered metrics, leakage, serving,
> monitoring, and a fallback?" Ticking these off out loud is a strong closing move.

---

<a id="mock"></a>
## Mock questions + full answers

Attempt each yourself (15–20 min, out loud) using the 7-step framework, *then* read the answer.

---

### Mock 1 — "Design a fraud detection system for payments" *(target: Amazon, Meta, Netflix)*

**Full answer (condensed to the high-signal points):**

> **1. Clarify:** Goal = flag fraudulent transactions in **real time** (block before completion),
> so latency must be ~tens of ms. Scale = thousands of transactions/sec. **Crucial cost
> asymmetry:** a missed fraud (false negative) costs money directly; a false positive blocks a
> legitimate customer (annoyance + lost sale). I'd ask for the relative cost to set the metric.
>
> **2. ML problem & metrics:** Binary classification, but **heavily imbalanced** — fraud is well
> under 1% (8.4). So **accuracy is meaningless** (predicting 'not fraud' always scores 99%+). I'd
> optimise **recall** on the fraud class (catch frauds) while watching **precision** (don't block
> good customers), tuned to the cost asymmetry — likely **PR-AUC** and a tuned decision threshold,
> not the default 0.5.
>
> **3. Data:** Labels come from confirmed chargebacks/disputes — but they arrive **late** (weeks
> later), so my training labels lag reality. Severe imbalance → class weights or careful
> resampling *on the training fold only* (8.4/8.1). Watch for **leakage**: a feature like
> 'account_was_later_closed' is a proxy for the label and unavailable at prediction time.
>
> **4. Features:** transaction (amount, merchant, time), user history (velocity — how many
> transactions in the last hour/day), device/IP, and aggregates. **Velocity features need
> real-time computation** and a feature store so train/serve match (8.16). These behavioural
> aggregates are usually the strongest signal.
>
> **5. Model:** baseline = logistic regression / gradient-boosted trees (great on tabular, handle
> imbalance well, **interpretable** — important for fraud where you must explain a block).
> Justify complexity only if the baseline underperforms.
>
> **6. Serving:** real-time scoring in the payment path with a tight latency budget; precompute
> slow features, compute velocity features on the fly. A **rules layer** runs alongside the model
> (hard blocks for known-bad patterns) — common in fraud.
>
> **7. Monitoring/failure:** fraud **adapts** (concept drift is constant), so monitor metrics and
> **retrain frequently**; alert on precision/recall drift. **Fallback:** if the model is down,
> fall back to rules + flag-for-review rather than blocking everyone. Add a **human review queue**
> for borderline scores.
>
> **Trade-offs:** recall vs precision (cost-driven threshold); latency vs feature richness;
> auto-block vs human-review for ambiguous cases; model vs rules (rules are explainable and fast
> to update, the model catches novel patterns).

> **Why this scores well:** leads with the imbalance + cost asymmetry (the crux of fraud),
> rejects accuracy, mentions label lag and leakage, picks an *interpretable* model for a reason,
> and includes a rules layer + human review. It shows you understand the *domain*, not just ML.

---

### Mock 2 — "Design a content moderation system using an LLM" *(target: Anthropic, OpenAI, Meta)*

**Full answer (high-signal points):**

> **1. Clarify:** Goal = detect policy-violating content (hate, violence, spam, etc.) on a
> platform, at scale, with **low latency** if pre-publish, or near-real-time if post-publish.
> Scale = millions of items/day. **Cost asymmetry:** false negative = harmful content stays up
> (safety/reputation risk); false positive = censoring legitimate content (user harm, free-speech
> concerns). I'd clarify which the platform weights higher, and whether borderline cases go to
> human review.
>
> **2. ML problem & metrics:** Multi-label classification (an item can violate several
> policies). Per-category **precision and recall**; the threshold per category is set by the
> harm/cost trade-off. Online: appeal/overturn rate (how often human reviewers reverse the
> model) is a great quality signal. Heavily **imbalanced** — most content is fine (8.4).
>
> **3. Data:** labelled examples from human moderators (expensive, slow, and the policy
> definitions drift over time). Edge cases and sarcasm/context make labels noisy — I'd track
> inter-annotator agreement. Severe imbalance and constant new evasion tactics (concept drift).
>
> **4/5. Model — a tiered design (the key idea):**
> - **Tier 1 — cheap fast filter:** a small classifier / keyword + embedding model screens
>   everything. Most content is obviously fine → cleared cheaply.
> - **Tier 2 — LLM for the hard cases:** ambiguous items go to an LLM that can reason about
>   *context* (sarcasm, intent) with the policy in its prompt. The LLM returns a structured
>   verdict + rationale, which I **parse and validate** (9.10/9.11).
> - **Tier 3 — human review** for low-confidence or high-impact decisions, and for appeals.
>
> This tiering controls **cost** — you can't afford an LLM call on every one of millions of
> items, so the cheap tier handles the bulk and the LLM handles the few percent that are hard.
>
> **6. Serving:** Tier 1 real-time inline; Tier 2 LLM calls **rate-limited and batched** (5.11/
> 5.14) with **cost tracking** (5.20); async for post-publish. **Cache** verdicts for identical/
> near-identical content (4.4/9.12).
>
> **7. Monitoring/failure:** track per-category precision/recall, appeal-overturn rate, drift
> (new slang/evasion). **Fail safe vs fail loud (7.2) is a policy decision:** if the model is
> down, do you fail open (allow, risk harm) or fail closed (hold for review, risk delay)? For
> safety-critical categories, hold for human review. Continuous **eval set** + red-teaming, since
> adversaries actively probe for gaps.
>
> **Trade-offs:** precision vs recall is a *values* decision here, not just a metric; LLM
> accuracy/context vs cost/latency (hence tiering); automation vs human-in-the-loop for
> high-stakes or appealed decisions; fail-open vs fail-closed.

> **Why this scores well (esp. at Anthropic/OpenAI):** the **tiered cheap-filter → LLM → human**
> design (cost control), treating LLM output as untrusted (parse/validate, 9.10/9.11), framing
> precision/recall as a *values* trade-off, and the fail-open/closed policy question. It shows
> safety-aware, cost-aware LLM systems thinking — exactly their domain.

---

## Final advice for ML system design rounds

- **Always start by clarifying** — scale, latency, what "good" means, cost of each error type.
  Designing before scoping is the top failure.
- **Cover the whole lifecycle** (the 7 steps) — data and metrics and monitoring, not just the
  model. Juniors talk only about the model.
- **Start simple, justify complexity** — propose a baseline, then add pieces with reasons. Don't
  open with "I'd use a giant transformer."
- **Name the traps unprompted** — leakage (8.1), imbalance (8.4), train/serve skew (8.16),
  drift, fallback (5.10). Each one signals real production experience.
- **State trade-offs explicitly** — every choice has a cost; saying so is the senior signal.
- **Think out loud and use the whiteboard/structure** — draw the boxes (data → features → model
  → serving → monitoring). Communication is graded (Area 15).

> **Company recap:** **Google/Meta** — scale & rigour (two-stage, billions QPS). **Amazon** —
> practical + ownership/LP framing (Area 14). **Netflix** — deep senior judgment & trade-offs.
> **Anthropic/OpenAI** — LLM systems (RAG, agents, moderation, evals), safety- and cost-aware.
> **Nvidia** — training infra & performance (Areas 6 & 9).

[↑ Back to top](#contents)
