<a id="contents"></a>
# Chapter 7 — Reference Architecture Blueprints

Yeh chapter ready-to-reuse **blueprints** deta hai — common AI/ML systems ke standard
architectures, diagram ke saath. Inhe yaad mat karo; *samjho* ki har box kyun hai. Apne problem
pe inhe adapt karo (requirements ke hisaab se boxes add/remove). Har blueprint: diagram + box-wise
explanation + key decisions.

---

## Contents

- [7.1 — Recommendation system (two-stage)](#71)
- [7.2 — RAG chatbot](#72)
- [7.3 — Real-time fraud detection](#73)
- [7.4 — Batch scoring pipeline](#74)
- [7.5 — Feature platform](#75)

---

<a id="71"></a>
## 7.1 — Recommendation system (two-stage)

**Kahan use hota hai:** YouTube/Netflix-style recommendations, e-commerce "you may like", feed
ranking. Jab items bahut zyada (millions) hon aur har request pe sabko score karna impossible ho.

**Blueprint:**
```
OFFLINE (batch, scheduled):
[User events] → [Feature pipeline] → [Feature store (offline)]
[Items]       → [Embed items]      → [(ANN index)]   (item embeddings precomputed)
[Training data] → [Train retrieval model + ranker] → [Model registry]

ONLINE (per request, low latency):
[User opens app]
      │
      ▼
[API/Gateway] → [Feature store (online)]  (user features fetch, ~ms)
      │
      ▼
STAGE 1: [Retrieval] → [(ANN index)]   (10M items → ~500 candidates, fast)
      │
      ▼
STAGE 2: [Ranker model]  (500 candidates ko precisely score, full features)
      │
      ▼
[Top 20] → [Business rules/filters] → User
                              │
                       [Monitoring: CTR, latency, drift]
```

**Box-wise (kyun har box):**
- **Two-stage (retrieval → ranking)** — *key decision*. 10M items har request pe score nahi kar
  sakte (napkin math, Ch 4). Stage 1 (sasta retrieval, ANN) 10M→500 laata hai; Stage 2 (heavy
  ranker) sirf 500 ko score karta hai. (Ch 2.5 bottleneck fix.)
- **Item embeddings offline precomputed** — request-time pe compute nahi (fast). (Cache idea.)
- **Feature store (online + offline)** — train/serve skew se bachne ke liye (6.2).
- **Business rules/filters** — already-seen hatao, diversity, freshness (model ke baad).
- **Monitoring** — CTR/watch-time + drift; gire toh retrain.

**Key decisions & trade-offs:** retrieval-then-rank (scale ke liye, thodी precision trade); offline
embeddings (fresh nahi par fast); exploration slots (naye items ko chance) vs pure exploitation;
cold-start (naye user/item → popularity fallback).

> **Adapt karo:** Chhote item-set (hazaar items)? → two-stage drop karo, seedha rank. Real-time
> nahi chahiye? → recommendations batch precompute karke store (6.4) — bahut simpler.

---

<a id="72"></a>
## 7.2 — RAG chatbot

**Kahan use hota hai:** Internal docs/support/manuals/codebase pe Q&A bot. Grounded + cited
answers chahiye, knowledge baar-baar update hota hai.

**Blueprint:**
```
OFFLINE (ingestion pipeline, runs on doc changes):
[Docs (PDF/HTML/MD)] → [Load + clean] → [Chunk (9.9)] → [Embed (9.12, cache)]
                                              → [(Vector DB)] + metadata (source, perms)

ONLINE (per query):
[User question]
      │
      ▼
[API] → [embed query] → [(Vector DB) top-k retrieve]  (+ metadata filter: perms)
                              │
                              ▼
                        [Re-rank? (D6)] → [Build prompt within token budget (9.8)]
                              │
                              ▼
                        [LLM service] ──stream tokens (9.13)──> User (+ citations)
                              │
                        [validate output (9.10/11): grounded? say "don't know"?]
                              │
                       [Monitoring: faithfulness, recall@k, cost/query (5.20)]
```

**Box-wise (kyun):**
- **Ingestion offline** — chunk/embed ek baar (ya doc-change pe), content-hash cache se re-ingest
  sasta (9.12).
- **Vector DB + metadata** — semantic retrieval (5.7) + permission filtering (kaunse docs yeh
  user dekh sakta).
- **Re-rank (optional)** — top-50 retrieve, cross-encoder se best-5 (precision, D6) — *agar* eval
  dikhaye zaroorat.
- **Prompt builder** — token budget mein best chunks fit (9.8), "sirf context se answer + cite".
- **Validate** — LLM untrusted; grounded check, nothing-relevant → "don't know" (hallucinate se
  bachao).
- **Monitoring** — retrieval (recall@k) + generation (faithfulness) *alag*, + cost/query.

**Key decisions & trade-offs:** chunk size (chhota = precise par kam context; bada = ulta);
top-k (zyada = answer milne ka chance par token cost); hybrid search (exact terms ke liye, D6);
LLM bottleneck hai (cache/rate-limit, 9.12/5.11).

> **Adapt karo:** Kam docs + low traffic? → ek FAISS file + simple top-k, managed vector DB ki
> zaroorat nahi. Exact terms (codes/names) miss ho rahe? → hybrid search add karo. Quality kam?
> → pehle measure (retrieval vs generation), phir us half ko fix karo.

---

<a id="73"></a>
## 7.3 — Real-time fraud detection

**Kahan use hota hai:** Payment-time fraud blocking. Real-time (tens of ms), heavily imbalanced
data, fraud constantly adapts.

**Blueprint:**
```
OFFLINE:
[Historical txns + chargeback labels] → [Feature pipeline] → [Train model]
                                                            → [Model registry]
[Streaming features pipeline]: [Txn events] → [Kafka] → [Flink: "last 5min per card"]
                                                            → [Feature store (online)]

ONLINE (in the payment path, tight latency):
[Transaction]
      │
      ▼
[API] → [Rules layer]  (known-bad patterns → instant block)
      │  (pass)
      ▼
[Feature store (online)]  (velocity features, ~ms)
      │
      ▼
[Fraud model]  → score
      │
      ├─ high risk → block / step-up auth
      ├─ medium    → [Human review queue]
      └─ low       → allow
      │
[Monitoring: precision/recall, drift, alert]   [Fallback: rules-only if model down]
```

**Box-wise (kyun):**
- **Rules layer + model** — *key decision*. Rules fast + explainable (known fraud patterns);
  model catches novel patterns. Dono saath (5.x — fraud mein standard).
- **Streaming features (Flink)** — "last 5 min velocity" real-time chahiye (6.4 streaming), batch
  basi ho jayega.
- **Imbalanced handling** — fraud <1%, toh accuracy bekaar; recall/precision per cost asymmetry
  (8.4).
- **Human review queue** — borderline scores human ko (auto-block sabko nahi).
- **Fallback** — model down → rules-only + flag, poora block-everyone nahi (5.10).

**Key decisions & trade-offs:** recall vs precision (miss fraud vs block genuine — cost-driven
threshold); latency budget (payment path = tight); fail-open vs fail-closed (model down pe allow
karein ya hold? — risk decision); label lag (chargebacks hafton baad → frequent retrain on drift).

> **Adapt karo:** Real-time block nahi, baad mein flag chalega? → streaming drop, batch scoring
> (7.4) — bahut simpler. Volume kam? → Flink ki zaroorat nahi.

---

<a id="74"></a>
## 7.4 — Batch scoring pipeline

**Kahan use hota hai:** "Sabko score karo" jahan real-time nahi chahiye — daily churn risk, lead
scoring, nightly recommendations precompute. Sabse simple ML serving (aur aksar best).

**Blueprint:**
```
[Scheduled trigger (Airflow, daily)]
      │
      ▼
[Load entities + features (warehouse / feature store offline)]
      │
      ▼
[Load model from registry]
      │
      ▼
[Batch inference] (vectorised / chunked / parallel — 8.10, Ch 5)
      │
      ▼
[Write scores → table / key-value store]
      │
      ▼
[App reads precomputed scores]  (sub-ms lookup, NO model call at request time)
      │
[Monitoring: job success, score distribution, drift]
```

**Box-wise (kyun):**
- **Scheduled (orchestrator)** — Airflow DAG (5.8), retry/alert/re-run.
- **Batch inference** — saare entities ek saath, vectorised/parallel (8.10) — high throughput,
  latency koi nahi (nobody waiting).
- **Precompute → store → lookup** — *key insight*. App request-time pe sirf lookup karta hai
  (sub-ms), koi model call nahi. "Real-time serving" ka feel bina online-serving complexity ke!
- **Idempotent writes** (B6/7.4) — re-run pe duplicate nahi, partition overwrite.

**Key decisions & trade-offs:** freshness (scores last-run jitne purane — daily kaafi?) vs cost
(zyada frequent run = zyada compute); precompute kaun se entities (sab ya sirf active?).

> **Adapt karo:** Yeh sabse under-rated pattern hai. Bahut "real-time" needs *actually* batch +
> lookup se solve ho jaati hain — cheaper, simpler, kम failure. Online serving (6.4) sirf jab
> input unpredictable ho (sab precompute nahi kar sakte).

---

<a id="75"></a>
## 7.5 — Feature platform

**Kahan use hota hai:** Jab kai models/teams same features use karte hain, ya real-time features
chahiye, ya train/serve skew bada risk hai. Yeh ek shared infrastructure hai, ek model nahi.

**Blueprint:**
```
SOURCES → [Feature pipelines]
            ├─ batch (Spark/dbt): historical features
            └─ streaming (Flink): real-time features
                        │
                        ▼
            ┌─ FEATURE STORE ──────────────────────────┐
            │  [Offline store (warehouse)]  → training  │
            │  [Online store (key-value)]   → serving   │
            │  feature definitions (ek baar, dono use)  │
            └────────────────────────────────────────────┘
                  │                          │
         [Training pipelines]         [Online serving]
         (point-in-time joins,        (low-latency
          no leakage 8.1)              feature fetch)
```

**Box-wise (kyun):**
- **Ek feature definition, dono stores** — *core idea*. Train/serve skew (8.16) khatam — same
  computation dono jagah.
- **Offline store (warehouse)** — historical values, training ke liye, point-in-time correct (no
  future leakage, 8.1).
- **Online store (key-value)** — current values, serving ke liye, ~ms fetch.
- **Batch + streaming pipelines** — slowly-changing features batch, real-time features streaming.

**Key decisions & trade-offs:** build vs buy (Feast/Tecton vs home-grown); online store freshness
vs cost; full platform (scale, many models) vs ek shared function (single model — 6.2 "kab NAHI").

> **Adapt karo:** Single small model? → full feature platform over-kill. Bas ek shared
> feature-computation function jo training aur serving dono import karein — wahi anti-skew
> principle, 1% effort. Platform tab jab features genuinely shared/real-time ho.

[↑ Back to top](#contents)