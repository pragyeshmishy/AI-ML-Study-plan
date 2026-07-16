<a id="contents"></a>
# Chapter 6 — AI/ML System Design Specifics

Ab tak jo seekha (think/act/draw/math/tools) — woh sab systems pe lagta hai. Yeh chapter
**ML-specific** cheezein sikhaता hai jo normal web systems mein nahi aatीं: features, training,
serving, monitoring, drift, aur RAG. ML system ka asli sach — *model chhota hissa hai; uske
aas-paas ka system (features, serving, monitoring) hi success ya failure decide karta hai.*

---

## Contents

- [6.1 — ML system ka poora lifecycle (bada picture)](#61)
- [6.2 — Features aur feature store (train/serve skew)](#62)
- [6.3 — Training pipeline aur experiment tracking](#63)
- [6.4 — Model serving: batch vs online vs streaming](#64)
- [6.5 — Model registry, versioning, safe deployment](#65)
- [6.6 — Monitoring, drift, aur feedback loop](#66)
- [6.7 — RAG system design (end-to-end)](#67)

---

<a id="61"></a>
## 6.1 — ML system ka poora lifecycle (bada picture)

**Kya hai:** Har production ML system ek loop follow karta hai:
`data → features → training → evaluation → registry → deployment → serving → monitoring → (wapas
data)`. Yeh ek **loop** hai, line nahi — monitoring wapas retraining ko feed karta hai.

**Problem kya solve karta hai:** Beginners sochte hain "ML system = model". Reality mein model ek
chhota box hai bade system mein, aur zyadatar failures *baaki* boxes mein hoti hain — basi
features, train/serve mismatch, undetected drift. Poora lifecycle dekhna hi notebook-model se
production-system ki taraf le jaata hai.

**Stages (har ek aage detail mein):**
1. **Data** (Ch 5/B) — clean, validated data lake/warehouse mein.
2. **Features** (6.2) — data ko model inputs banao; feature store mein.
3. **Training** (6.3) — reproducible pipeline model train + log karta hai.
4. **Evaluation** (Area 8.5/8.6/8.14) — offline metrics + baseline se fair comparison.
5. **Registry** (6.5) — model artifact version + store.
6. **Deployment** (6.5) — safely roll out (canary/shadow/A-B).
7. **Serving** (6.4) — predictions do (batch/online/streaming).
8. **Monitoring** (6.6) — live metrics + drift dekho; retraining trigger → loop wapas.

**Example:** "Recommendation system banao" sunke agar aap seedha "transformer model" pe kood gaye,
toh aap 7 mein se 6 stages bhool gaye. Senior poore loop ki baat karta hai — kahan se data, kaise
features (skew se bachke), kaise serve (two-stage), kaise monitor (drift). Model ek line hai.

**Pros & cons:** ✅ poora lifecycle sochna junior-galti (sirf model pe focus) se bachata hai.
❌ poora system bahut infrastructure hai — isliye "simple se shuru" (ek baseline poore loop se)
behtar hai "fancy model bina serving/monitoring" se.

> **Ek line:** ML system = sirf model nahi, poora loop (data→features→train→serve→monitor→wapas).
> Pehle ek *patli slice* poore loop se banao (simple model, but deployed + monitored), phir har
> stage improve karo. Deployed simple model > undeployed great model.

---

<a id="62"></a>
## 6.2 — Features aur feature store (train/serve skew)

**Kya hai:** **Features** = model ke inputs, raw data se compute kiye (jaise "user ka 30-din ka
avg order value"). **Feature store** (Feast/Tecton, ya home-grown) = ek central system jo features
compute, store, aur serve karता hai — *consistently for both training and serving*.

**Problem kya solve karta hai:** Sabse bada production-ML bug — **train/serve skew** (Area 8.16).
Training mein feature ek tarah compute, serving mein doosri tarah → model ko serving pe alag input
milता hai jo training se match nahi karta → chup-chap underperform. Feature store feature *ek baar*
compute karta hai, dono use karte hain — skew impossible. Saath: feature reuse, aur point-in-time
correctness (no future leakage, 8.1).

**Kab use karein:** Features kai models/teams mein share, ya real-time compute, ya skew ka risk
(lagभग hamesha). Chhota project skip kar sakta hai (ek shared function dono paths use karein — wahi
principle, halka).

**Kaise (ML example):** Feature store mein **offline store** (warehouse — historical values,
training) + **online store** (Redis-jaisा — current value, serving). "avg order value 30d" *ek baar*
define; offline historically materialise (train), online current serve (inference) — same
definition, no skew. **Point-in-time joins** ensure training row sirf *us waqt* known values use
kare (no leakage, 8.1).

**Pros & cons:** ✅ train/serve skew khatam, reuse, point-in-time correctness, real-time features.
❌ kaafi infra; single small model ke liye over-kill (shared function use karo).

> **Ek line:** Feature store ka *principle* — feature ek baar compute, train aur serve dono use
> karein (no skew) — hamesha zaroori. *Product* scale pe. Skew sabse common silent killer hai;
> isse bachna #1 priority.

---

<a id="63"></a>
## 6.3 — Training pipeline aur experiment tracking

**Kya hai:** **Training pipeline** = automated, reproducible flow jo features + labels se ek
trained, evaluated, registered model banata hai (one-off notebook nahi). **Experiment tracking**
(MLflow, W&B) har run ke params, metrics, artifacts log karता hai (Area 8.15).

**Problem kya solve karta hai:** "Production wala model main dobara nahi bana sakta" wala
nightmare (8.8). Notebook mein haath se train kiya model — unsaved steps, bhool-gaye
hyperparameters — na reproduce hota, na audit, na retrain, na rollback. Pipeline + tracking har
model ko **reproducible** (same data+code+config → same model) aur har experiment ko **comparable**
banata hai.

**Kab use karein:** Koi bhi model jo production jayega, retrain hoga, ya alternatives se compare
hoga — yaani throwaway experiment ke alawa sab.

**Kab NAHI:** Pure exploration/prototyping mein notebook theek hai (speed). Pipeline tab jab model
*matter* karne lage.

**Kaise (ML example):** Training pipeline (Airflow/Kubeflow DAG, Ch 5): `load features → split (no
leakage, 8.1) → train → evaluate vs baseline (8.14) → agar behtar, register (6.5)` — versioned
config se driven, fixed seed (8.7), pinned environment (7.15). Har run MLflow mein log:
hyperparameters, data version, git commit, metrics, model artifact — toh "kaunse run ne prod model
banaya aur kaise?" ek query hai, yaaddasht nahi.

**Pros & cons:** ✅ reproducibility, comparability, auditability, safe retrain/rollback. ❌ notebook
se zyada upfront engineering; pipeline infra maintain karni padti.

> **Ek line:** Model production jaane se *pehle* notebook se pipeline pe shift karo. Notebook =
> exploration; pipeline = jo cheez pe aap depend karte ho. Reproducibility optional nahi.

---

<a id="64"></a>
## 6.4 — Model serving: batch vs online vs streaming

**Kya hai:** Trained model actually predictions kaise deta hai. Teen mode: **batch** (schedule pe
bade set ko score karke store), **online** (live API, per-request real-time prediction),
**streaming** (events ke flow pe score).

**Problem kya solve karta hai:** "Model deploy karo" ka matlab bilkul alag system hai depending on
*kab* prediction chahiye — alag latency, cost, complexity. Galat mode = ya paisa barbaad ya latency
requirement fail.

**Kab kaunsa:**
- **Batch** — predictions precompute ho sakti hain, turant nahi chahiye: nightly "churn risk for
  all users", daily recommendations store. Simplest, sasta.
- **Online** — prediction *abhi* chahiye, per-request, waiting user: payment-time fraud check, live
  search ranking, RAG answer. Low-latency scaled API chahiye (Ch 5).
- **Streaming** — continuous event flow pe: transactions ko aate hi score.

**Kab NAHI:** Online API mat banao jab batch+lookup kaafi ho (over-engineering — neeche dekho).
Streaming mat karo jab batch ki freshness chalती ho.

**Kaise (ML example):** *Batch* — scheduled job 50M users score karke table mein likhता hai, app
sirf lookup karta hai (sub-ms, koi model call nahi). *Online* — model ek REST/gRPC API ke peeche,
many replicas + load balancer (Ch 5), model per-worker ek baar load (6.11/Area 6.11), GPU
throughput ke liye requests batch. Serving code **bilkul wahi preprocessing** kare jo training ne
ki (saved pipeline, 8.16) — warna skew.

**Pros & cons:** ✅ batch — simple, sasta, high-throughput; online — fresh, any input; streaming —
event-flow fresh. ❌ batch — predictions basi (last run jitni purani), sirf precomputed entities;
online — low-latency infra/scaling/cost; streaming — sabse mushkil.

> **Ek line:** Batch use karo jab tak real-time *sach mein* na chahiye — precompute + lookup bahut
> sasta aur simple hai. "Real-time" lagne wali bahut needs batch+cache se solve ho jaati hain.
> Online sirf jab input unpredictable ho (sab precompute nahi kar sakte).

---

<a id="65"></a>
## 6.5 — Model registry, versioning, safe deployment

**Kya hai:** **Model registry** (MLflow Registry, SageMaker) = trained model artifacts + metadata
(kaunse data/code/metrics ne banaya) ka versioned store. **Safe deployment** = naya model version
*gradually + reversibly* roll out: **shadow** (saath chalाo, compare, output serve mat karo),
**canary** (chhote % traffic ko do), **A/B test** (live metrics pe compare), with **instant
rollback**.

**Problem kya solve karta hai:** (1) Registry bina — pata nahi *kaunsa* model prod mein hai, kaise
bana, rollback kaise (8.9). (2) "Big-bang" deploy (naya model seedha 100% traffic) — agar woh
offline theek par live data pe fail, toh *sabko* ek saath hit, aur panic redeploy (Area 10.12).

**Kab use karein:** Registry — koi bhi prod model. Safe deployment — koi bhi model *update* live
system mein, especially high-traffic/high-stakes.

**Kaise (ML example):** Training pipeline (6.3) naya `v4` register karता hai with metrics+lineage.
Deploy: pehle **shadow** (real traffic score karta hai, aap `v3` se compare karte ho, par users ko
`v3` hi milta hai) → phir **canary** 5% traffic, live metrics+latency dekho → 5%→50%→100% agar
healthy → **instant rollback** (flag flip) to `v3` agar metrics gire. Registry se "kaunsा version
live hai aur revert kaise?" trivial.

**Pros & cons:** ✅ registry — traceability, reproducibility, easy rollback; gradual deploy —
bounded blast radius, real-data validation, calm rollback. ❌ infra + process; shadow/canary ke
liye traffic-split + monitoring chahiye.

> **Ek line:** Naye model ko kabhi seedha 100% mat karo — pehle shadow ya canary, with instant
> rollback. Offline win (better metrics, 8.14) online win guarantee nahi karti — live traffic pe
> validate karo.

---

<a id="66"></a>
## 6.6 — Monitoring, drift, aur feedback loop

**Kya hai:** Deployed model ki **health** aur **quality** ko continuously dekhna, aur degrade hone
pe pakadna. Dekhne layak: **operational** (latency, error rate, throughput), **prediction**
(output distribution, confidence), **data drift** (input features training se shift), aur — jab
labels aayein — **model quality** (live accuracy/precision).

**Problem kya solve karta hai:** Model deploy hone ke baad "done" *nahi* hota — woh chup-chap
*decay* karta hai. Duniya badalti hai (naya user behaviour, naye fraud tricks, seasonality), toh
live data training se drift karता hai aur accuracy girती hai *bina koi error ke* (8.16). Bina
monitoring ke aapko users ki shikायat ya revenue-drop se pata chalता hai, hafton baad — apne system
se nahi.

**Kab use karein:** *Har* production model, hamesha. Yahi stage lifecycle loop (6.1) ko band karta
hai — monitoring hi retraining *trigger* karता hai.

**Kaise (ML example):** Dashboards + alerts: serving p99 latency + error rate; prediction
distribution (achanak shift = kuch galat); **feature drift** — live feature distributions vs
training set (statistical test ya PSI), diverge hone pe alert; aur jab ground-truth labels aayein
(jo lag kar sakte — fraud label hafton baad), live precision/recall vs offline estimate. Drift ya
quality-drop **retraining trigger** karता hai (6.3) on fresh data, naya model 6.5 se deploy — loop.
**Fallback** (Area 5.10) safe default deta hai agar model service fail ho.

**Pros & cons:** ✅ silent decay pakadta hai usse pehle ki costly ho, retraining loop band, confidence
to operate. ❌ monitoring infra; good drift metrics/thresholds chunna (zyada sensitive = false
alarms, loose = miss); label lag se quality-monitoring delayed.

> **Ek line:** Monitoring model ke *saath* ship karo, baad mein nahi — unmonitored prod model ek
> silent liability hai. **Drift** (duniya badli → retrain) ko **bug/skew** (code galat → fix) se
> alag pehchano; dono live metric girate hain par fix alag.

---

<a id="67"></a>
## 6.7 — RAG system design (end-to-end)

**Kya hai:** **RAG** (Retrieval-Augmented Generation) = LLM ko *aapke* data se answer dilana —
relevant text retrieve karke prompt mein daal ke. Do hisse: **offline ingestion** (docs taiyar
karna) + **online query** (sawaal ka jawab).

**Problem kya solve karta hai:** LLM sirf apni training-data jaanta hai — *aapke* private/current
docs nahi, aur unke baare mein poochо toh **hallucinate** karta hai. Fine-tuning mehenga + slow +
phir bhi hallucinate; saare docs prompt mein daalna impossible (context limit). RAG relevant facts
question-time pe deta hai — grounded, citable, aur docs badalne se turant update.

**Kab use karein:** Private/changing knowledge-base pe QA (internal docs, support, manuals,
codebase), grounded + cited answers chahiye. **Kab NAHI:** agar LLM ka built-in knowledge kaafi
ho, ya task retrieval-shaped na ho.

**Kaise (end-to-end design):**
```
OFFLINE (ingestion pipeline, batch):
[Docs] → [load+clean] → [chunk (9.9)] → [embed (9.12)] → [(Vector DB)] + metadata

ONLINE (per query):
[User Q] → [embed query] → [(Vector DB) top-k] → [re-rank?] → [build prompt
            within token budget (9.8)] → [LLM, stream (9.13)] → [validate (9.10/11)]
            → Answer + citations
```
- **Ingestion:** chunking quality-critical (9.9 — coherent + overlap); embeddings content-hash
  cache (9.12 — re-ingest sasta); metadata (source, permissions) for citations + filtering.
- **Query:** same embedding model as docs (warna tutega); top-k retrieve; prompt mein "sirf is
  context se answer do, sources cite karo"; nothing relevant mila → "mujhe nahi pata" (hallucinate
  se behtar).
- **Evaluate (D5):** retrieval (recall@k) aur generation (faithfulness) *alag* — pata chale kaunsa
  half fix karna.
- **Advanced (jab eval weakness dikhaye):** hybrid search (exact terms), re-ranking (precision),
  query rewriting, agentic (multi-hop). Sab ek saath mat lagao — measured weakness pe ek-ek.

**Pros & cons:** ✅ grounded/cited answers, knowledge update bina retrain, fine-tuning se sasta.
❌ retrieval quality answer quality ko *cap* karti hai (bura retrieval → bura answer); multi-
component system (build + eval); per-query LLM latency + cost (cache/rate-limit/track — 9.12/5.11/
5.20).

> **Ek line:** RAG = retrieve + generate. Asli mushkil "model jaanta hai?" se shift ho ke "sahi
> context retrieve kar paaye?" pe aa jaati hai — isliye chunking, embedding, aur retrieval eval pe
> sabse zyada dhyान. Simple top-k se shuru, measure (D5), phir ek advanced technique add karo jo
> weakness fix kare.

[↑ Back to top](#contents)