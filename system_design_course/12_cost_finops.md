<a id="contents"></a>
# Chapter 12 — Cost & FinOps for ML

ML systems mein paisa tezi se udta hai — GPUs, LLM tokens, storage, data transfer. **FinOps** =
cost ko ek first-class design constraint maanna (latency/scale jaisा). Yeh chapter sikhaता hai
ML ka paisa *kahan* jaata hai aur use *kaise* kam karein — bina quality giraye.

---

## Contents

- [12.1 — ML ka paisa kahan jaata hai](#121)
- [12.2 — LLM/API cost kam karna](#122)
- [12.3 — GPU/compute cost kam karna](#123)
- [12.4 — Storage & data cost](#124)
- [12.5 — Cost monitoring & alerts](#125)

---

<a id="121"></a>
## 12.1 — ML ka paisa kahan jaata hai

**Kya seekhna hai:** ML systems mein cost ke bade buckets pehchano — taaki pata ho *kahan* kaatna
hai. Aksar cost ka 80% kuch 1-2 cheezon mein hota hai (Pareto).

**Problem kya solve karta hai:** Bina jaane ki paisa kahan ja raha, aap galat jagah optimize karte
ho (jaise storage ₹100 bacha rahe jab LLM calls ₹40,000 kha rahe). Buckets pehchanke aap bade
faayde wali jagah focus karte ho.

**ML cost ke bade buckets:**
- **LLM/API calls** — token-based, *bahut* tezi se add up (har call paisa). Aksar #1 cost LLM apps
  mein. (*100k queries/day × $0.013 = ~$40k/month — Ch 4.7.*)
- **GPU compute** — training (bade GPUs, hours) + inference (GPU serving). Idle GPU = paisa jal
  raha bina kaam.
- **Storage** — data lake (sasta par bada), warehouse (mehenga), vectors, model artifacts,
  logs/backups. Forever-retention = bill badhता rehta.
- **Data transfer (egress)** — data ko networks/regions ke beech move karna (cloud egress mehenga
  ho sakta).
- **Managed services** — vector DB, feature store, orchestrator (managed = convenience, par cost).

**Kaise (example):** Ek RAG app ka bill breakdown: LLM calls 70%, embeddings 10%, vector DB 10%,
storage 5%, baaki 5%. → optimization focus = **LLM calls** (caching, smaller model), na ki
storage. Pareto: bada bucket pehle.

**Pros & cons:** ✅ pata chalta hai kahan kaatna hai (max impact); cost surprise se bachte ho.
❌ buckets measure karne ke liye cost monitoring chahiye (12.5).

> **Ek line:** Pehle pata karo paisa *kahan* ja raha (usually LLM/GPU #1). 80% cost aksar 1-2
> buckets mein — *wahan* optimize karo, choti cheezon mein nahi. Cost ek design constraint hai.

---

<a id="122"></a>
## 12.2 — LLM/API cost kam karna

**Kya seekhna hai:** LLM cost (tokens × price × volume) kam karne ke levers — yeh aksar ML apps ka
sabse bada bucket hai, toh sabse zyada impact.

**Problem kya solve karta hai:** Har LLM call paisa khaata hai, aur volume pe yeh huge ho jaata hai
(Ch 4.7 — $40k/month easily). Bina optimization ke yeh sustainable nahi.

**Levers (sabse impactful pehle):**
- **Caching (sabse bada lever):** same/similar queries ka answer cache (9.12). Repeated queries
  free ho jaati hain. *Aksar 40-60% bachata hai.* Embeddings bhi cache (content-hash).
- **Smaller/cheaper model:** har task ko biggest model ki zaroorat nahi. Simple tasks → chhota
  sasta model; sirf hard tasks → bada. (Routing: easy→cheap, hard→expensive.)
- **Fewer tokens:** chote prompts (zaroorat-bhar context, 9.8), kम retrieved chunks, concise system
  prompts. Token kam = cost kam.
- **Batching:** jahan real-time nahi, requests batch karo (5.14) — overhead amortise.
- **Cache + dedup at ingestion:** unchanged docs re-embed mat karo (9.12, incremental).

**Kaise (example):** $40k/month chatbot. Lever 1 — caching (same FAQs repeat): -50% = $20k. Lever
2 — easy queries chhote model pe route: -25% = $15k. Lever 3 — prompt trim (kam chunks): -10% =
$13.5k. Teen levers se ~$40k → ~$13.5k, bina quality giraye (eval se verify, 8.8).

**Pros & cons:** ✅ bada cost saving (LLM usually #1 bucket); caching often free quality. ❌ caching
needs invalidation care (stale answers); smaller-model routing needs eval (quality drop na ho);
prompt-trimming context kam kar sakta (balance).

> **Ek line:** LLM cost = tokens × price × volume. Sabse bada lever **caching** (repeated queries
> free), phir **smaller model** for easy tasks, phir **fewer tokens**. Quality eval se verify
> karo (8.8) — sasta karte waqt quality mat giraao.

---

<a id="123"></a>
## 12.3 — GPU/compute cost kam karna

**Kya seekhna hai:** GPU cost (training + inference) kam karne ke levers — GPUs mehenge hain, aur
idle/oversized GPU paisa jalाता hai.

**Problem kya solve karta hai:** GPU hours mehenge ($1-30+/hour depending on GPU). Idle GPU (kaam
nahi par chal raha), oversized GPU (zaroorat se bada), ya unnecessary frequent retraining — sab
paisa barbaad.

**Levers:**
- **Right-size the GPU:** chhote model ko 80GB GPU pe mat chalao; jitni VRAM chahiye utni lo.
  Inference aksar training se chhoti GPU pe ho jaata hai.
- **Spot/preemptible instances:** training (jo interrupt-tolerant hai with checkpointing, 7.6) ko
  spot instances pe chalao — 60-90% sasta. (Checkpoint zaroori taaki interrupt pe resume.)
- **Don't over-retrain:** roz retrain zaroori hai? Drift-triggered (11.5) retraining sirf jab
  zaroorat — fixed-daily se sasta agar data slowly badalta.
- **Batch inference + utilisation:** GPU ko bhookha mat rakho (data loading bottleneck, 6.6); batch
  karke utilisation high (8.10). Idle GPU band karo (autoscale to zero).
- **Mixed precision / quantization:** 16-bit ya quantized models — kam memory, faster, sasti GPU
  pe fit (9.3).

**Kaise (example):** Training job roz 4× 80GB GPU, 24h, $2/hr = ~$6k/month. Levers: (1) drift se
weekly retrain (roz nahi) = -70%; (2) spot instances = -70% on remaining; (3) right-size to 40GB =
-30%. Combined: $6k → ~$500/month.

**Pros & cons:** ✅ bada saving (GPU mehenga); spot instances huge discount. ❌ spot interrupt ho
sakte (checkpointing zaroori, 7.6); right-sizing needs testing; under-provisioning se OOM (9.3) ya
slow.

> **Ek line:** GPU cost — right-size (zaroorat-bhar VRAM), **spot instances** for interruptible
> training (checkpointing ke saath, 60-90% sasta), drift-triggered retrain (roz nahi), aur GPU ko
> idle/bhookha mat rakho. Idle GPU = jalta paisa.

---

<a id="124"></a>
## 12.4 — Storage & data cost

**Kya seekhna hai:** Storage aur data-transfer cost kam karna — yeh chhota lagता hai par bade data
pe (TB/PB) aur cloud egress pe add up hota hai.

**Problem kya solve karta hai:** "Storage toh sasta hai" — par 1.8 PB/year (Ch 4.4 example) pe
nahi. Aur forever-retention, galat storage tier, aur cross-region transfer (egress) bill badhate
hain chup-chाp.

**Levers:**
- **Retention policy:** sab data forever mat rakho. Purana raw data archive/delete (jo kabhi use
  nahi hota). (*7 saal purane logs chahiye?*)
- **Storage tiers:** frequently-accessed → fast/costly tier; rarely → cold/cheap tier (S3 Glacier
  jaisा). Cloud auto-tiering use karo.
- **Compression & format:** Parquet (columnar, compressed) raw JSON/CSV se *bahut* chhota aur
  faster (Ch 4.4 — 18GB CSV vs 1.5GB Parquet). Bada saving.
- **Avoid egress:** data ko same region/cloud mein rakho jahan compute hai; cross-region/cross-
  cloud transfer mehenga. Vector index ko bar-baar move mat karo.
- **Dedup:** same data multiple jagah store mat karo (content-hash, 9.12).

**Kaise (example):** 1PB raw logs S3 standard pe = mehenga. Levers: (1) 90-din baad Glacier (cold)
= -80% on old data; (2) Parquet + compression = -10x size; (3) 2-saal retention (purana delete).
Combined: bill ka bada hissa bach gaya.

**Pros & cons:** ✅ bade data pe real saving; Parquet quality+speed bhi deta hai. ❌ retention/
archiving needs governance (galti se zaroori data delete na ho); cold tier se retrieve slow+costly
(sirf rarely-accessed pe).

> **Ek line:** Storage — retention policy (sab forever nahi), tiers (hot/cold), Parquet+compression
> (10x chhota), aur egress avoid (data compute ke paas rakho). Chhota lagता hai par TB/PB pe add
> up hota hai.

---

<a id="125"></a>
## 12.5 — Cost monitoring & alerts

**Kya seekhna hai:** Cost ko *monitor* karo (jaise latency/errors) — per-feature/per-model/per-query
breakdown, with alerts. Jo measure nahi karte woh optimize nahi kar sakte.

**Problem kya solve karta hai:** Bina cost monitoring ke, month-end bill ek shock hota hai aur aap
nahi jaante *kya* mehenga tha. Ek runaway loop (bug se 10x LLM calls) ya cost spike pakdा nahi
jaata jab tak bill na aaye.

**Kaise (kya track karein):**
- **Per-query/per-operation cost:** har LLM call ke tokens+cost log (5.20), tagged by feature/user.
- **Aggregate by dimension:** cost by feature, by model, by team — pata chale *kaun* kha raha.
- **Budgets + alerts:** threshold cross ho toh alert (ya hard-stop runaway). *"Aaj ka LLM spend
  $X cross"* → alert.
- **Anomaly detection:** achanak cost spike (10x normal) = bug/abuse → turant alert, bill ka wait
  nahi.

**Kaise (example):** Har LLM call ek structured log: `{feature, model, tokens, cost, user}`.
Dashboard: cost by feature (pata chala "summarization" feature 70% kha raha). Budget alert: daily
spend $1500 cross → Slack alert. Ek din spike aaya (10x) → alert → pata chala ek retry-loop bug
infinite calls kar raha tha → turant fix, bill bachा.

**Pros & cons:** ✅ cost surprise nahi, runaway pakdा jaata turant, pata kahan optimize karein.
❌ monitoring infra; budgets ko maintain karna; per-call logging thodा overhead.

> **Ek line:** Cost ko latency/errors ki tarah *monitor* karo — per-query cost, breakdown by
> feature, budgets + alerts. Jo measure nahi karoge woh optimize nahi kar paoge, aur runaway cost
> bill aane *se pehle* pakadना hai.

[↑ Back to top](#contents)