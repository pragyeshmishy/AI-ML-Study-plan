<a id="contents"></a>
# Chapter 8 — Anti-patterns / Mistakes Gallery

Yeh chapter common **galtiyon** ka gallery hai — jo log baar-baar karte hain. Har ek ke liye:
**galti kya hai, kaise pehchanein (symptom), kyun hoti hai, aur sahi kya hai.** Inhe jaan lena
adhe achhe designs bana deta hai — kyunki galat se bachna khud ek skill hai.

---

## Contents

- [8.1 — Over-engineering (sabse badi galti)](#81)
- [8.2 — Monitoring/observability bhool jaana](#82)
- [8.3 — Train/serve skew](#83)
- [8.4 — Data leakage](#84)
- [8.5 — Accuracy pe bharosa (imbalanced data)](#85)
- [8.6 — No fallback (model down = sab down)](#86)
- [8.7 — Premature streaming (jab batch kaafi tha)](#87)
- [8.8 — Eval ke bina RAG/LLM tuning](#88)
- [8.9 — Idempotency na hona (re-run = duplicate)](#89)
- [8.10 — Cost ignore karna jab tak bill na aaye](#810)

---

<a id="81"></a>
## 8.1 — Over-engineering (sabse badi galti)

**Galti kya hai:** Chhoti problem ke liye bada, complex solution — Kafka + Spark + Kubernetes +
microservices, jahan ek Postgres + cron job kaafi tha.

**Kaise pehchanein (symptom):** System banane mein hafte lag rahe, deploy karne mein dar lagta,
debug karna painful, 5 alag systems chal rahe par users sirf 2,000. "Future mein chahiye hoga"
sun-ne ko milta hai justification mein.

**Kyun hoti hai:** Log "scalable", "production-grade" dikhna chahte hain; FAANG blogs padh ke
unke billion-scale solutions chhoti problem pe laga dete hain; "agar future mein..." (jo aksar
aata hi nahi).

**Sahi kya hai:** Simple se shuru (Ch 1.4). Complexity *tabhi* add karo jab ek *real* requirement
force kare (data ek machine mein nahi → tab distributed; QPS handle nahi → tab scale). YAGNI —
"You Aren't Gonna Need It".

> **Example:** 10,000 docs pe chatbot → ek FAISS file + script kaafi. Distributed vector DB
> cluster + agentic RAG + K8s pehle din se = over-engineering. *Jab* docs 10M ho jayein, *tab*
> scale karo.

> **Ek line:** Default mode = simplest thing that works. "Bada" banane se pehle poocho — "kya
> koi *real* number/requirement ise force kar raha hai, ya main sirf fancy dikhna chahta hoon?"

---

<a id="82"></a>
## 8.2 — Monitoring/observability bhool jaana

**Galti kya hai:** System bana ke deploy kar diya, par monitoring nahi — pata hi nahi chalता ki
production mein kaisा chal raha hai jab tak kuch toot na jaye.

**Kaise pehchanein:** Production issues users ki shikायat se pata chalti hain, aapke dashboard se
nahi. "Sab theek lag raha hai" — par koi metric nahi dekh raha. Model decay hafton baad pakdा
jaata hai (revenue gire toh).

**Kyun hoti hai:** Monitoring "baad mein add karenge" wali cheez ban jaati hai (aur kabhi add
nahi hoti); deploy karne ki khushi mein observability bhool jaate hain; ML mein extra — model
silently decay karta hai bina error ke (8.16).

**Sahi kya hai:** Monitoring model/system ke *saath* ship karo, baad mein nahi (6.6). Track:
latency/error rate (operational), prediction distribution, **data drift**, aur model quality (jab
labels aayein). Alerts lagao. (Ch 2.6 — yeh senior signal hai.)

> **Example:** Recommendation model deploy kiya, 3 hafte baad pata chala CTR dheere-dheere gir
> raha tha (data drift) — kyunki koi drift monitor nahi tha. Agar drift alert hota, week 1 mein
> retrain ho jaata.

> **Ek line:** Unmonitored production system = aankh band karke gaadi chalana. Design ke saath
> poocho — "yeh fail kaise hoga aur main *kaise* jaanunga?" Jawab na ho toh design adhoora hai.

---

<a id="83"></a>
## 8.3 — Train/serve skew

**Galti kya hai:** Training mein features ek tareeke se compute, serving mein doosre tareeke se —
model ko production mein alag input milता hai jo training se match nahi karta.

**Kaise pehchanein:** Model offline (test) pe great, production mein kharab — *bina kisi error
ke*. Predictions "thodी off" lagti hain par crash nahi. Sabse confusing bug, kyunki sab kuch
"chal raha" dikhता hai.

**Kyun hoti hai:** Training notebook mein pandas se feature banaya, serving code (alag service,
alag language kabhi) mein dobara likha — aur woh thodा alag nikla. Do alag codepaths = inevitable
drift.

**Sahi kya hai:** Feature ko *ek baar* compute karo, dono (train + serve) use karein — feature
store (6.2) ya at minimum ek **shared function**/saved pipeline (8.16). Do implementations =
guaranteed skew.

> **Example:** Training mein "avg last 30 days" pichhle 30 calendar days se, serving mein last 30
> *records* se — alag values → model confused. Fix: ek shared definition dono jagah.

> **Ek line:** Features ko kabhi do jagah alag-alag compute mat karo. Ek definition, dono paths.
> Yeh #1 silent production-ML killer hai.

---

<a id="84"></a>
## 8.4 — Data leakage

**Galti kya hai:** Training mein aisी information use kar li jo prediction-time pe available nahi
hoti (ya test-set ki info training mein aa gayi) — model "cheat" karke offline great score deta
hai jo production mein reproduce nahi hota.

**Kaise pehchanein:** Offline accuracy *shak ke layak achhi* (0.98 on a hard problem) par
production mein crash (0.61). "Yeh model toh kamaal hai!" — yahi warning sign hai.

**Kyun hoti hai:** Feature future info use karta hai (jaise "account_closed_date" se churn predict
— jo event ke *baad* pata chalta hai); ya scaling/imputation poore data pe fit kiya *split se
pehle* (test stats leak); ya time-series ko random split kiya (future se past predict).

**Sahi kya hai:** Split *pehle*, phir transforms sirf training pe fit (8.1, pipeline); time-series
mein time-based split; sirf woh features jo prediction-time pe genuinely available hain;
point-in-time correctness (feature store, 6.2).

> **Example:** Churn model ne "support tickets in last 90 days" use kiya — par woh feature churn
> hone ke *baad* update hota tha. Offline 0.97, production useless. Fix: sirf pre-churn-time
> available features.

> **Ek line:** *Bahut achhा* offline score = leakage suspect karo, celebrate mat karo. Future
> ya test info training mein nahi aani chahiye. Split pehle, fit-on-train only.

---

<a id="85"></a>
## 8.5 — Accuracy pe bharosa (imbalanced data)

**Galti kya hai:** Imbalanced problem (fraud, disease, rare events) pe **accuracy** ko metric maan
liya — jahan accuracy bilkul bekaar hai.

**Kaise pehchanein:** "Mera model 99% accurate hai!" par woh actually kabhi positive predict hi
nahi karta. Fraud <1% hai toh "sab not-fraud" bolne wala model 99%+ accurate hai aur poori tarah
useless.

**Kyun hoti hai:** Accuracy default/familiar metric hai; log dekhte nahi ki positive class kitni
rare hai; confusion matrix nahi dekha.

**Sahi kya hai:** Imbalanced pe accuracy chhodo — **precision/recall/F1/PR-AUC** dekho rare class
ke liye (8.4). Threshold tune karo cost ke hisaab se (default 0.5 aksar galat). Aur model ko rare
class pe dhyान dilao (class weights/resampling).

> **Example:** Fraud detector 99.2% accurate — khush hue. Confusion matrix dekha: 0 frauds caught.
> Useless. Recall pe optimize kiya (cost: kuch false positives), ab actual frauds pakadta hai.

> **Ek line:** Imbalanced data pe accuracy mat dekho — woh jhoothi khushi deti hai. Rare class ki
> recall/precision dekho. "99% accurate" sunke poocho — "positive class kitni rare hai?"

---

<a id="86"></a>
## 8.6 — No fallback (model/service down = poora system down)

**Galti kya hai:** Maan liya ki model/dependency hamesha available rahega — fail hone pe koi
fallback nahi, toh ek component girne se poora user-experience tut jaata hai.

**Kaise pehchanein:** "Model service down ho toh kya hoga?" ka jawab "...poora app crash" hai.
Ek dependency ki hichki pe users ko error page. Single point of failure.

**Kyun hoti hai:** Happy-path soch (sab theek chalega); failure modes (Ch 2.6) skip kiye; "yeh toh
kabhi down nahi hoga" (har cheez kabhi down hoti hai).

**Sahi kya hai:** Har critical dependency ke liye fallback (5.10): model down → popularity-based
default / cached results / simpler model; LLM down → raw retrieved chunks dikhao; timeouts + retry
+ circuit breaker (Ch 5). Graceful degradation — kuch dena, error nahi.

> **Example:** Recommendation model service down — poora homepage khali. Fix: fallback to "popular
> in your region" (non-personalised par *kuch* toh dikhe). User ko pata bhi nahi chalता.

> **Ek line:** Har critical dependency ke liye poocho — "yeh down ho toh user ko *kuch* milega ya
> error?" Fallback (degraded-but-working) hamesha error-page se behtar. Failure plan karo, maan
> ke mat chalo.

---

<a id="87"></a>
## 8.7 — Premature streaming (jab batch kaafi tha)

**Galti kya hai:** Real-time streaming (Kafka + Flink) bana liya jahan ek nightly batch job kaafi
tha — bina us freshness ki real zaroorat ke.

**Kaise pehchanein:** Streaming infra chal raha hai par koi *sach mein* seconds-fresh data use
nahi kar raha; debugging painful (late events, windowing); ek simple "daily recompute" se kaam
chal jaata. "Real-time" cool lagता tha isliye banaya.

**Kyun hoti hai:** Real-time "modern/impressive" lagता hai; freshness requirement clarify nahi ki
(Ch 2.1); batch ko "purana tareeka" samajh ke skip kiya.

**Sahi kya hai:** Batch se shuru karo jab tak sub-minute freshness *genuinely* business need na ho
(6.4/A7). Streaming bahut zyada complex hai (late/out-of-order events, state, exactly-once) —
sirf jab seconds matter karein (real-time fraud, live personalisation).

> **Example:** Team ne "real-time dashboard" ke liye Flink pipeline banaya — par business ko hourly
> updates se kaam chal jaata. Months of streaming complexity, jise ek hourly batch SQL replace kar
> sakta tha.

> **Ek line:** "Kya sach mein seconds chahiye?" — yeh poocho. 90% cases mein batch kaafi hai, aur
> woh *bahut* simpler/sasta/debuggable hai. Streaming ka cost zyada hai; bina zaroorat mat lo.

---

<a id="88"></a>
## 8.8 — Eval ke bina RAG/LLM tuning

**Galti kya hai:** RAG/LLM system ke knobs (chunk size, k, prompt, model) "vibes" se tune karna —
koi eval set nahi, "yeh better lag raha hai" pe decisions.

**Kaise pehchanein:** "Maine prompt change kiya, ab behtar lag raha hai" — par koi number nahi.
Quality kabhi up kabhi down, pata nahi kyun. Jab answer kharab aaye, pata nahi retrieval ki galti
thi ya generation ki.

**Kyun hoti hai:** Eval set banana "boring" lagता hai; LLM output subjective lagता hai (measure
kaise?); jaldi ship karne ka pressure.

**Sahi kya hai:** Ek eval set banao (question → expected answer/sources). **Retrieval** (recall@k)
aur **generation** (faithfulness, LLM-as-judge) *alag* measure karo (D5) — pata chale kaunsा half
fail. Phir measured weakness pe ek technique add karo (D6), randomly sab nahi.

> **Example:** Team mahino RAG "improve" karti rahi prompt tweaks se — par retrieval hi tooti thi
> (galat chunks aa rahe the), prompt se kuch farak nahi padता. Eval hota toh week 1 mein pata
> chalता ki retrieval fix karna hai.

> **Ek line:** Bina eval ke aap blind tune kar rahe ho. Chhota eval set banao, retrieval vs
> generation *alag* maapo. "Better lag raha hai" evidence nahi hai (8.5/8.14).

---

<a id="89"></a>
## 8.9 — Idempotency na hona (re-run = duplicate/corruption)

**Galti kya hai:** Pipeline/job aisा banaya jo dobara chalाne pe data *duplicate* ya double-count
kar deta — kyunki re-run safe nahi hai.

**Kaise pehchanein:** Job fail hua, re-run kiya, ab rows duplicate. Ya retry ne customer ko
double-charge kar diya. Backfill karne se darr lagता hai ("kahin data kharab na ho jaye").

**Kyun hoti hai:** Maan liya job sirf ek baar chalega (par retries, crashes, manual re-runs hote
hi hain); append-only writes bina dedup; "at-least-once" queues duplicates dete hain (A6).

**Sahi kya hai:** Har step ko safe-to-rerun banao (B6/7.4): deterministic keys + upsert
(insert-or-replace), ya partition overwrite (re-run pe us din ka data replace, append nahi);
queue consumers idempotent (event-id se dedup). "Re-run" hamesha safe hona chahiye.

> **Example:** Daily feature job crash hua aadhe mein, re-run kiya — ab aadha data double. Fix:
> job partition (date) ko *overwrite* karta hai, append nahi — re-run safe.

> **Ek line:** Pipelines *re-run honge hi* (retry, crash, manual). Pehle din se safe-to-rerun
> banao — deterministic keys + upsert/overwrite. "Re-run" kabhi destructive nahi hona chahiye.

---

<a id="810"></a>
## 8.10 — Cost ignore karna jab tak bill na aaye

**Galti kya hai:** System bana liya bina cost socne — phir month-end bill dekh ke shock. ML mein
khaas (LLM tokens, GPU hours tezi se add up hote hain).

**Kaise pehchanein:** "Bill itna kaise aaya?!" Koi cost monitoring nahi; har request pe LLM call
bina cache; GPU 24/7 idle chal raha; saara data forever store.

**Kyun hoti hai:** Development mein cost dikhता nahi (chhota volume); "pehle kaam karwa lo, cost
baad mein"; per-operation cost × volume ka napkin math nahi kiya (Ch 4.7).

**Sahi kya hai:** Design-time pe cost estimate (4.7 — tokens×price×volume); caching repeated LLM/
embedding calls (9.12 — aksar 50%+ bachata hai); per-query cost monitoring + alert (5.20);
right-size GPU/model; data retention policy. (Detail Ch 12.)

> **Example:** Chatbot, 100k queries/day, har query ~$0.013 → ~$40,000/month. Bill aane pe pata
> chala. Caching same/similar queries ne 60% bachaya. Agar napkin math (4.7) pehle hota, caching
> day-1 se hoti.

> **Ek line:** Cost ek design constraint hai, baad ki soch nahi. Design-time pe
> tokens/GPU-hours × volume ka hisaab lagao; caching + monitoring day-1 se. "$40k/month" surprise
> nahi hona chahiye.

[↑ Back to top](#contents)