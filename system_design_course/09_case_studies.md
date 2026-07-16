<a id="contents"></a>
# Chapter 9 — Step-by-Step Case Studies

Ab sab kuch jodते hain. Yeh chapter poore designs **live** karta hai — ek vague problem se shuru,
phir 7-step process (Ch 2) apply karke, napkin math (Ch 4), tools (Ch 5), aur trade-offs ke saath
end-to-end. Aise padho jaise aap interviewer ke saamne baithe ho aur main bol-bol ke design kar
raha hoon.

---

## Contents

- [9.1 — Case study: RAG chatbot for company docs](#91)
- [9.2 — Case study: Real-time recommendation system](#92)
- [9.3 — Case study: Fraud detection system](#93)

---

<a id="91"></a>
## 9.1 — Case study: "Company docs pe ek QA chatbot banao"

### Step 1 — Requirements clarify (Ch 2.1)
> "Pehle clarify karunga:
> - **Functional:** user natural-language sawaal poochega, system company docs se grounded answer
>   dega *with citations* (taaki bharosा ho, hallucinate na lage).
> - **Scale:** maan lo ~1 million documents, ~5,000 employees, peak ~10 concurrent queries.
> - **Latency:** answer 2-3 second mein (streaming se feel fast).
> - **Constraints:** docs mein access-permissions hain (har koi har doc nahi dekh sakta);
>   per-query LLM cost budget; private data (security, Ch 13).
> - **'Achha' kya:** answer correct + grounded (docs se, made-up nahi) + sahi source cite kare."

### Step 2 — Napkin math (Ch 4)
> "- **Storage:** 1M docs, maan lo avg 10 chunks each = 10M chunks. Har embedding 1536-dim×4 bytes
>   = ~6KB. Total vectors = 10M × 6KB = **~60GB**. → ek bade machine ki RAM mein aa *sakta* hai,
>   par safe ke liye managed vector DB.
> - **QPS:** 10 concurrent, low — ek-do serving instances kaafi. (Yeh recsys jaisा high-QPS nahi.)
> - **Cost:** 10 concurrent, maan lo 50k queries/day, har ~$0.01 (tokens) = **~$500/day** → caching
>   se kम karna hoga (9.12)."

> *Insight:* scale moderate hai — yeh over-engineer karne ki zaroorat *nahi*. Ek vector DB + ek
> LLM API + caching kaafi. (Ch 1.4 / 8.1 — simple se shuru.)

### Step 3 — High-level design (Ch 2.3)
```
OFFLINE (ingestion):
[Docs] → [Load+clean] → [Chunk] → [Embed (cache)] → [(Vector DB)] + metadata(perms,source)

ONLINE (per query):
[User Q] → [API] → [embed query] → [(Vector DB) top-k, perm-filtered]
                                        │
                                        ▼
                                  [Prompt builder (token budget)]
                                        │
                                        ▼
                                  [LLM] ──stream──> Answer + citations
                                        │
                                  [validate: grounded? "don't know"?]
            [Monitoring: recall@k, faithfulness, cost/query]
```

### Step 4 — Deep-dive (Ch 2.4) — retrieval (asli mushkil yahan)
> "Retrieval quality answer quality ko *cap* karti hai, toh yahan dhyान:
> - **Chunking (9.9):** semantic boundaries pe (paragraph/heading), overlap ke saath taaki
>   boundary-spanning fact na kate. Token-sized (~500 tokens).
> - **Embedding model:** query aur docs *same* model (warna retrieval tutega). Content-hash cache
>   (9.12) taaki re-ingest sasta.
> - **Top-k:** k=5 se shuru. Agar eval (Step neeche) dikhaye relevant chunks miss ho rahe → top-20
>   retrieve + **re-rank** to best-5 (D6).
> - **Permission filter:** vector DB metadata se — user sirf apne allowed docs search kare (Ch 13)."

### Step 5 — Bottlenecks & scaling (Ch 2.5)
> "- **Bottleneck = LLM call** (slow + mehenga, har query). Fix: **cache** same/similar queries
>   (9.12), **stream** tokens (feel fast), rate-limit per user (5.11).
> - Vector DB 60GB — ag docs 10x bade ho jayein (600GB), tab sharding. Abhi nahi.
> - Ingestion incremental (sirf changed docs re-embed, B6) — 1M docs roz re-embed mat karo."

### Step 6 — Failures & monitoring (Ch 2.6)
> "- **LLM down?** → fallback: raw retrieved chunks dikha do (poora crash nahi, 5.10/8.6).
> - **Nothing relevant retrieved?** → LLM bole 'mujhe yeh nahi pata' (hallucinate se behtar).
> - **Monitor:** retrieval recall@k + generation faithfulness (alag, D5), cost/query (5.20),
>   latency p99. Eval set banao taaki tuning blind na ho (8.8)."

### Step 7 — Trade-offs summary (Ch 2.7)
> "- **Vector DB + top-k** chuna (semantic search); cost — exact terms miss ho sakte, eval dikhaye
>   toh **hybrid** add karunga.
> - **Embeddings cache** kiya (sasta re-run); cost — naye docs re-embed (incremental se handle).
> - **Agentic RAG abhi NAHI** (over-engineering, 8.1) — simple top-k se shuru, eval-driven improve.
> - **Caching + streaming** — cost aur perceived-latency dono ke liye."

> **Is case study ka seekh:** scale moderate tha, toh maine *simple* design rakha (ek vector DB,
> ek LLM, caching) — over-engineer nahi kiya. Mushkil retrieval-quality mein thi, toh wahan
> deep-dive kiya. Eval-first rakha taaki improvements measured hon.

---

<a id="92"></a>
## 9.2 — Case study: "Real-time recommendation system banao"

### Step 1 — Requirements clarify
> "- **Functional:** user app khole toh personalised feed (20 items).
> - **Scale:** 100M users, 10M items, peak ~30,000 QPS (napkin neeche).
> - **Latency:** real-time, p99 < 100ms (user wait kar raha).
> - **Metric:** watch-time/engagement (sirf clicks nahi — clickbait se bachna), online A/B se.
> - **Failure cost:** kharab rec = user bore, par fatal nahi → availability > perfect accuracy."

### Step 2 — Napkin math
> "- **QPS:** 100M users × 10 opens/day = 1B/day ÷ ~100k sec = ~10k avg, ×3 peak = **~30k QPS**.
>   → many replicas + load balancer (Ch 5).
> - **Items:** 10M — har request pe sabko score = 10M × 30k QPS = impossible. → **two-stage**
>   (yeh number ne architecture decide kiya).
> - **Item embeddings:** 10M × 6KB = ~60GB → ANN index (shard if needed)."

### Step 3 — High-level design
```
OFFLINE (batch): [events]→[features]→[feature store]; [items]→[embed]→[(ANN index)];
                 [training data]→[train retrieval+ranker]→[registry]
ONLINE: [User]→[API]→[feature store online]→ STAGE1 [Retrieval→ANN: 10M→500]
                                           → STAGE2 [Ranker: score 500]
                                           → [top 20 + business rules] → User
        [Monitoring: CTR/watch-time, latency, drift]
```

### Step 4 — Deep-dive: two-stage (asli design decision)
> "- **Stage 1 retrieval:** two-tower model — user-tower + item-tower, trained so user-vector
>   item-vectors ke paas ho jo woh pasand karega. Serve: user embed → ANN index se ~500 nearest.
>   Sasta + scalable (9.14).
> - **Stage 2 ranking:** sirf 500 candidates ko heavy model (gradient-boosted / deep) se full
>   features pe score. 500 manageable hai 100ms mein.
> - **Simple baseline pehle:** 'most popular in region' — pipeline validate + A/B baseline. Phir
>   two-tower+ranker (Ch 1.4)."

### Step 5 — Bottlenecks & scaling
> "- **Bottleneck = per-request scoring** — two-stage se solved (10M→500→20).
> - **30k QPS:** stateless serving replicas + load balancer; user features feature-store online
>   se (~ms).
> - **Hot items/users:** cache.  **Item embeddings:** offline precompute (request pe nahi)."

### Step 6 — Failures & monitoring
> "- **Model service down?** → fallback: popularity-based feed (non-personalised par *kuch* —
>   8.6). - **Cold start** (naya user/item): popularity/content-based jab tak data na ho.
> - **Monitor:** watch-time, CTR, latency p99, feature drift (8.16) → drift pe retrain.
> - **Feedback loop risk:** model ke apne recs hi next training-data — thodा exploration rakho
>   warna rich-get-richer."

### Step 7 — Trade-offs summary
> "- **Two-stage** (scale ke liye, thodी precision trade — isliye re-rank).
> - **Offline embeddings** (fast, par fresh nahi — daily refresh).
> - **watch-time metric** (clicks nahi — clickbait se bachna).
> - **Exploration slots** (short-term engagement thodा kam, par long-term catalog health)."

> **Seekh:** napkin math (10M items × 30k QPS) ne *turant* two-stage force kiya. Metric choice
> (watch-time vs clicks) business-critical tha. Fallback + exploration = senior signals.

---

<a id="93"></a>
## 9.3 — Case study: "Payment fraud detection banao"

### Step 1 — Requirements clarify
> "- **Functional:** transaction ke time fraud detect karke block/flag.
> - **Real-time ya baad mein?** — maan lo real-time block (payment path), toh latency *tight*
>   (~tens of ms).
> - **Scale:** maan lo 5,000 transactions/sec peak.
> - **Cost asymmetry (critical):** missed fraud (false negative) = seedha paisa loss; genuine
>   customer block (false positive) = customer gussa + lost sale. Kaun zyada bura? — yeh metric
>   decide karega. Maan lo missed-fraud zyada mehenga, par false-positives bhi controlled.
> - **Labels:** chargebacks se aate hain, *hafton baad* (delayed labels — yeh design affect karta)."

### Step 2 — Napkin math
> "- **QPS:** 5,000/sec real-time — har ek <50ms mein decide. Toh features pre-fetched/precomputed
>   hone chahiye, heavy compute request-time pe nahi.
> - **Imbalance:** fraud <1% → 5000/sec mein ~50 fraud, 4950 genuine. Accuracy bekaar (8.4)."

### Step 3 — High-level design
```
OFFLINE: [historical txns + chargeback labels]→[features]→[train model]→[registry]
STREAMING: [txn events]→[Kafka]→[Flink: per-card last-5min velocity]→[feature store online]
ONLINE (payment path):
  [Txn]→[Rules layer (known-bad → instant block)]→[feature store online (~ms)]
       →[Fraud model → score]→ {high: block/step-up | med: human review | low: allow}
  [Monitoring: precision/recall, drift]   [Fallback: rules-only if model down]
```

### Step 4 — Deep-dive: rules + model + imbalance
> "- **Rules + model dono:** rules fast + explainable (known fraud patterns, instant block); model
>   novel patterns pakadta hai. Standard in fraud.
> - **Streaming velocity features:** 'last 5 min per card count/sum' — real-time chahiye (Flink,
>   6.4), batch basi ho jayega. Feature store online se serve.
> - **Imbalance handling (8.4):** class weights / careful resampling (train fold only, 8.1);
>   metric = recall (catch fraud) watching precision (don't over-block); threshold cost se tune,
>   default 0.5 nahi.
> - **Interpretable model** (gradient-boosted trees) — fraud block ko *justify* karna padta hai
>   (risk/compliance team)."

### Step 5 — Bottlenecks & scaling
> "- **Latency (payment path):** features precomputed/streamed (request pe heavy compute nahi);
>   model fast (trees). - **5000 QPS:** stateless model replicas + load balancer.
> - **Streaming velocity:** Flink scales with partitions (per-card)."

### Step 6 — Failures & monitoring
> "- **Model down?** → *fail-open ya fail-closed?* (a values decision, 7.2): safety-critical →
>   rules-only + flag-for-review (block-everyone nahi). - **Fraud adapts** (constant drift) →
>   monitor precision/recall, frequent retrain.
> - **Delayed labels:** quality monitoring lags (chargebacks weeks later) — interim, monitor
>   prediction distribution + manual review feedback.
> - **Human review queue** for borderline scores."

### Step 7 — Trade-offs summary
> "- **Rules + model** (fast/explainable + novel-catching).
> - **Recall-leaning threshold** (miss-fraud mehenga, par false-positives controlled — cost-driven).
> - **Streaming velocity features** (real-time zaroori, batch basi).
> - **Interpretable model** (compliance — fraud block justify karna padta).
> - **Human-in-loop** for borderline (auto-block sabko nahi)."

> **Seekh:** cost asymmetry (miss vs false-block) ne metric+threshold decide kiya — yeh fraud ka
> crux hai. Imbalance ne accuracy reject karwaya. Delayed labels ne monitoring strategy badli.
> Rules+model+human = mature real-world design.

> **Teeno case studies ka common dhaaga:** har ek mein — (1) requirements clarify, (2) napkin
> math ne architecture force kiya (RAG: moderate→simple; recsys: huge→two-stage; fraud:
> real-time→streaming), (3) asli mushkil pe deep-dive, (4) fallback + monitoring, (5) trade-offs
> with reasons. Yahi 7-step process (Ch 2) har problem pe lagta hai.

[↑ Back to top](#contents)