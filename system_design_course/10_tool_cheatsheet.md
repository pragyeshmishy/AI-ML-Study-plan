<a id="contents"></a>
# Chapter 10 — Tool Cheat-Sheet / Decision Tables

Yeh chapter quick-reference hai — "X chahiye? → Y use karo, Z nahi". Jab design karte waqt
turant decide karna ho, yahan dekho. (Detail Ch 5/6 mein hai; yeh fast lookup.) Har table ke
neeche ek "rule of thumb" line.

---

## Contents

- [10.1 — "Mujhe X chahiye → yeh tool" (need → tool)](#101)
- [10.2 — Storage decision table](#102)
- [10.3 — Serving decision table](#103)
- [10.4 — Batch vs Stream decision](#104)
- [10.5 — "Kab NAHI use karna" (over-engineering traps)](#105)
- [10.6 — ML-specific quick picks](#106)

---

<a id="101"></a>
## 10.1 — "Mujhe X chahiye → yeh tool"

| Mujhe yeh chahiye... | → Use karo | NAHI yeh (galat tool) |
|---|---|---|
| Repeat-kaam ka result jaldi | Cache (Redis) | (sirf jab repeat ho; unique pe nahi) |
| Ek se zyada server pe load baatna | Load balancer | — |
| Producer/consumer ko decouple | Message queue (Kafka/SQS) | (simple req-response pe nahi) |
| Raw/bada/unstructured data sasta store | Object storage / lake (S3) | Warehouse (mehenga blobs ke liye) |
| Clean tabular data pe fast SQL | Warehouse (BigQuery/Snowflake) | Lake (slow query) |
| Joins + transactions + consistency | SQL (Postgres) | NoSQL (limited joins) |
| Single-key fast lookup at scale | Key-value (Redis/DynamoDB) | SQL (overkill) |
| Meaning-based (semantic) search | Vector DB + ANN | SQL scan (slow), keyword (misses meaning) |
| Multi-step scheduled pipeline | Orchestrator (Airflow) | cron+scripts (no deps/retry) |
| Seconds-fresh event processing | Stream processor (Flink) | batch (basi) |
| Compute > one machine | Distributed (Spark/Dask) | (ek machine fit? → pandas/multiproc) |
| Train/serve feature consistency | Feature store (or shared fn) | duplicate feature code (skew!) |
| Reproducible packaging | Docker | (almost always yes) |
| Multi-service auto-scale at scale | Kubernetes | (small app → managed/serverless) |

> **Rule of thumb:** tool ko *us kaam ke hisaab se* chuno jo sabse zyada hota hai. Fashion ya
> "resume pe achha lagega" se nahi.

---

<a id="102"></a>
## 10.2 — Storage decision table

| Data / access pattern | → Store | Kyun |
|---|---|---|
| Raw events/images/blobs, sasta | Object storage / lake (S3) | sasta, kuch bhi, schema-on-read |
| Clean tables, analytics/training, SQL | Warehouse | fast SQL on big tabular |
| Relational, joins, transactions | SQL (Postgres) | consistency + joins |
| Fast lookup by key, serving | Key-value (Redis) | O(1), low-latency |
| Flexible/evolving JSON records | Document (MongoDB) | schema flexibility |
| Huge writes, time-ordered (logs) | Wide-column (Cassandra) | write throughput |
| Embeddings, similarity search | Vector DB (FAISS/pgvector/Pinecone) | ANN nearest-neighbour |
| Metrics/telemetry over time | Time-series DB | time-optimised |

> **Rule of thumb:** ek system aksar *kai* stores use karta hai (RAG: Postgres metadata + vector
> DB + Redis cache + S3 raw). Har store apna best kaam kare — sab ek mein mat thoso.

---

<a id="103"></a>
## 10.3 — Serving decision table

| Situation | → Serving mode | Kyun |
|---|---|---|
| Predictions precompute ho sakti, turant nahi chahiye | **Batch** + lookup | simplest, sasta, high-throughput |
| Per-request, real-time, waiting user | **Online** API | fresh, any input, low latency |
| Continuous event flow pe scoring | **Streaming** | event-time freshness |
| "Real-time lag raha par input predictable" | **Batch precompute + cache lookup** | online ki complexity bina speed |

> **Rule of thumb:** batch + lookup use karo jab tak online *sach mein* na chahiye. Bahut
> "real-time" needs precompute+cache se solve ho jaati hain — sasta aur simple. Online sirf jab
> input unpredictable (sab precompute nahi kar sakte).

---

<a id="104"></a>
## 10.4 — Batch vs Stream decision

| Sawaal | Batch | Stream |
|---|---|---|
| Freshness need | minutes/hours OK | seconds zaroori |
| Complexity | simple | hard (late events, windowing, state) |
| Cost | sasta | mehenga |
| Reprocess/backfill | easy | hard |
| Debug | easy | hard |
| Example | nightly training, daily scoring | real-time fraud, live personalisation |

> **Rule of thumb:** **batch se shuru karo** jab tak sub-minute freshness genuine business-need na
> ho. Premature streaming sabse common over-engineering (8.7) hai. "Kya sach mein seconds
> chahiye?" — poocho.

---

<a id="105"></a>
## 10.5 — "Kab NAHI use karna" (over-engineering traps)

| Tool | NAHI use karo jab... | Iske bajay |
|---|---|---|
| Kubernetes | chhota app / prototype | ek container + managed service (Cloud Run) |
| Spark/Dask | data ek machine pe fit | pandas + multiprocessing (Spark *slower* hoga!) |
| Streaming (Flink) | minutes/hours freshness OK | batch (simpler/sasta) |
| Microservices | chhoti team, simple app | monolith (pehle), split baad mein |
| Vector DB (managed) | hazaar vectors, low traffic | FAISS file / pgvector |
| Feature store (product) | single small model | shared feature function |
| Cache | har request unique / fast-changing data | direct compute (cache ulta nuksaan) |
| Message queue | simple synchronous req-response | direct call |
| Deep model | tabular data, baseline kaafi | gradient-boosted trees / logistic |

> **Rule of thumb:** har tool ka cost (complexity, paisa, maintenance) hai. "Kya *real*
> requirement ise force kar rahi?" — agar nahi, simplest cheez use karo (Ch 1.4 / 8.1). Yeh table
> over-engineering se bachata hai.

---

<a id="106"></a>
## 10.6 — ML-specific quick picks

| Problem | → Pick |
|---|---|
| Tabular data, strong baseline | Gradient-boosted trees (XGBoost/LightGBM) — often beats deep |
| Imbalanced classes | Class weights + precision/recall/PR-AUC (NOT accuracy, 8.4) |
| Too many items to score per request | Two-stage: retrieval → ranking |
| Train/serve consistency | Feature store / shared function (no skew, 8.16) |
| Repeated expensive LLM/embedding calls | Cache by content-hash (9.12) |
| LLM needs your private data | RAG (not fine-tuning, for most cases) |
| RAG retrieval weak | Measure first (recall@k); then hybrid/re-rank (D6) |
| GPU out of memory | Smaller batch → mixed precision → grad accumulation (9.3) |
| Model decaying in prod | Monitor drift → retrain on schedule (6.6) |
| Safe model rollout | Shadow → canary → A/B, instant rollback (6.5) |
| Reproducible model | Pipeline + tracking + seed + pinned env (6.3) |

> **Rule of thumb:** ML mein — *simplest model that meets the bar* (baseline pehle), data/features
> > model (feature quality usually beats model choice), aur *system around model* (serving,
> monitoring, skew) hi success decide karta hai, model nahi.

[↑ Back to top](#contents)