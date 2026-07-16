<a id="contents"></a>
# Chapter 11 — MLOps & Deployment Lifecycle

**MLOps** = ML systems ko reliably *ship aur operate* karne ki practice (jaise DevOps, par ML ke
liye, with extra: data + model versioning, retraining, drift). Yeh chapter "model ban gaya" se
"model production mein chal raha aur maintained hai" tak ka poora loop sikhaता hai.

---

## Contents

- [11.1 — MLOps kya hai aur kyun (DevOps se kya extra)](#111)
- [11.2 — CI/CD for ML (kya test karein)](#112)
- [11.3 — Versioning: code + data + model](#113)
- [11.4 — Deployment strategies (shadow/canary/blue-green)](#114)
- [11.5 — Automated retraining (kab aur kaise)](#115)
- [11.6 — Maturity levels (manual → fully automated)](#116)

---

<a id="111"></a>
## 11.1 — MLOps kya hai aur kyun (DevOps se kya extra)

**Kya hai:** MLOps = tools + practices jo ML model ko develop → deploy → operate → maintain
karne ke poore loop ko reliable + automated banate hain. DevOps ka ML version, par 3 extra cheezon
ke saath: **data**, **model**, aur **continuous retraining**.

**Problem kya solve karta hai:** Normal software mein sirf *code* deploy hota hai. ML mein code +
**data** + **model** — teeno version + track + deploy karne padte hain, aur model **decay** karta
hai (drift, 6.6) toh use *retrain* bhi karna padता hai. Bina MLOps ke: "production model dobara
nahi bana sakta" (8.8), "kaunsा version live hai pata nahi", "model 3 hafte se decay ho raha tha
pata nahi chala". MLOps yeh sab fix karta hai.

**DevOps se kya extra (3 cheez):**
1. **Data versioning** — code git mein hai, par *data* bhi version karna padता hai (kaunse data pe
   train hua?). Tools: DVC, lakeFS, ya immutable data snapshots.
2. **Model versioning + registry** — har model artifact + uska lineage (data/code/metrics) track.
3. **Continuous retraining + monitoring** — model decay karta hai, toh monitor → drift → retrain
   loop chahiye (normal code "decay" nahi karta).

**Kaise (example):** Ek MLOps setup: code git mein, data DVC se versioned, training pipeline
(Airflow) jo model ko MLflow registry mein daalती hai, CI jo data+model validate karta hai, canary
deployment, aur drift-monitoring jo retrain trigger karता hai. Sab automated + reproducible.

**Pros & cons:** ✅ reproducible, auditable, reliable, fast iteration, no "works on my machine".
❌ kaafi infra + discipline; chhote experiment ke liye over-kill (yeh production systems ke liye).

> **Ek line:** MLOps = DevOps + (data versioning + model versioning + retraining/monitoring loop).
> Kyunki ML mein code akela nahi — data aur model bhi version + deploy + maintain hote hain, aur
> model decay karta hai.

---

<a id="112"></a>
## 11.2 — CI/CD for ML (kya test karein)

**Kya hai:** **CI** (Continuous Integration) = har code change pe automated tests chalाo. **CD**
(Continuous Deployment) = pass hone pe automatically deploy. ML mein CI/CD normal software se
zyada test karta hai — code + data + model.

**Problem kya solve karta hai:** Normal CI sirf code test karta hai. ML mein code theek ho par
*data* kharab (schema badla, nulls bade) ya *model* kharab (accuracy gir gayi) ho sakta hai. Bina
ML-specific CI ke, ek bura model ya corrupt data chup-chाp production mein chala jaata hai.

**Kya test karein (ML CI mein):**
- **Code tests** (normal) — unit tests, lint.
- **Data validation** — schema, null-rate, ranges, distribution (B5/8.x). Naya data expected shape
  ka hai?
- **Model validation** — naya model baseline se behtar ya barabar? (8.14). Agar accuracy gir gayi
  → deploy *mat* karo (auto-block).
- **Train/serve consistency** — features dono jagah same? (8.16).
- **Integration** — serving endpoint actually load hota hai aur sane prediction deta hai?

**Kaise (example):** Pull request aaya → CI chalता hai: code tests + data validation + model
training pe a small set + "naya model eval baseline se behtar?" check. Sab pass → CD model ko
**registry** mein daalता hai aur **canary** deploy karता hai (11.4). Accuracy gir gayi? → CI fail,
deploy block.

**Pros & cons:** ✅ bura code/data/model production mein jaane se rukta hai; fast, safe iteration;
har change validated. ❌ ML CI banana mushkil (data/model tests flaky ho sakte, eval slow); infra
chahiye.

> **Ek line:** ML CI/CD code *+ data + model* test karta hai. Naya model baseline se kharab? →
> auto-block deploy. Yeh woh safety net hai jo bura model production mein jaane se rokta hai
> (8.14).

---

<a id="113"></a>
## 11.3 — Versioning: code + data + model

**Kya hai:** ML mein teen cheezein version karni padti hain taaki koi bhi result *reproduce* ho
sake: **code** (git), **data** (kaunse exact data pe train hua), **model** (kaunsा artifact +
config + metrics).

**Problem kya solve karta hai:** "Production wala model dobara banao" — agar aapko nahi pata
*kaunse data*, *kaunse code*, *kaunse hyperparameters* ne use banaya, toh impossible (8.8). Sirf
code version karna kaafi nahi — same code + *alag data* = alag model. Teeno chahiye.

**Kaise (teeno version):**
- **Code:** git (commit hash). Normal.
- **Data:** DVC / lakeFS / immutable snapshots — "yeh model `data_v2026-06-01` pe trained". Mutable
  `data.csv` jo badalti rehti = reproducibility tutti.
- **Model:** registry (MLflow) — artifact + lineage (data version + git commit + hyperparams +
  metrics + seed, 8.7).

**Kaise (example):** Model `v4` register hua with: git commit `a1b2c3`, data version
`2026-06-01`, hyperparams (config), seed 42, metrics (F1 0.87), pinned environment (7.15).
6 mahine baad "v4 kaise bana?" → registry se sab pata, aur exactly reproduce kar sakte ho.

**Pros & cons:** ✅ full reproducibility, audit (regulated industries ke liye zaroori), safe
rollback, debugging ("kya badla v3 se v4?"). ❌ data versioning storage khaata hai (big datasets
ke snapshots); discipline chahiye.

> **Ek line:** Code + data + model — *teeno* version karo, warna model reproduce nahi hoga. "Same
> code" kaafi nahi; "same data + same code + same config" = same model. Yeh reproducibility ki
> neev hai.

---

<a id="114"></a>
## 11.4 — Deployment strategies (shadow / canary / blue-green)

**Kya hai:** Naya model/version production mein *gradually + safely* daalne ke tareeke, taaki bura
model sabko ek saath na hit kare. **Shadow** (saath chalाo, output use mat karo, compare),
**canary** (chhote % ko do), **blue-green** (do environments, switch), with **instant rollback**.

**Problem kya solve karta hai:** Naya model offline great lag sakta hai par live data pe fail
(8.16). "Big-bang" (seedha 100%) = bura model sabko hit, panic redeploy (8.6/Area 10.12). Gradual
rollout = bounded blast radius + real-data validation pehle.

**Strategies (kab kaunsi):**
- **Shadow:** naya model real traffic *score* karta hai par output user ko nahi jaata — sirf
  purane se compare. Risk-free validation on real data. Use jab naya model bilkul untested ho.
- **Canary:** naya model 5% traffic ko serve, metrics dekho, healthy toh 5%→50%→100% ramp. Use jab
  shadow pass ho gaya, ab real users pe thodा test.
- **Blue-green:** do full environments (blue=current, green=new); green ready hone pe traffic
  switch (aur problem ho toh wापस blue). Fast rollback, par double resources.
- **Instant rollback (sabke saath):** flag/switch se turant purane version pe — *hamesha* rakho.

**Kaise (example):** `v4` deploy → shadow (1 hafta, `v3` se compare, output v3 hi) → canary 5%
(metrics+latency watch) → 50% → 100% → agar kabhi metrics gire, flag flip → `v3` instantly.

**Pros & cons:** ✅ bounded blast radius, real-data validation, calm rollback. ❌ traffic-splitting
+ monitoring infra chahiye; blue-green double resources; gradual rollout dheema (par safe).

> **Ek line:** Naya model kabhi seedha 100% mat karo. Shadow (risk-free) → canary (small %) →
> ramp, with instant rollback. Offline-better ≠ online-better — live pe validate karo (6.5/8.14).

---

<a id="115"></a>
## 11.5 — Automated retraining (kab aur kaise)

**Kya hai:** Model ko fresh data pe *automatically* dobara train karna — kyunki model time ke saath
decay karta hai (drift, 6.6). "Train once, deploy forever" galat hai.

**Problem kya solve karta hai:** Duniya badalti hai (naye patterns, seasonality, naye fraud
tricks), toh live data training-data se drift karता hai aur model purana/galat ho jaata hai. Manual
retraining bhool jaate hain ya late karte hain. Automated retraining model ko fresh rakhता hai.

**Kab retrain karein (triggers):**
- **Scheduled** — fixed interval (daily/weekly). Simple, predictable. Jab data steadily badalta ho.
- **Drift-triggered** — monitoring (6.6) drift detect kare toh retrain. Smarter — sirf jab zaroorat.
- **Performance-triggered** — live metric (jab labels aayein) gire toh retrain.
- **Data-volume-triggered** — enough naya labelled data jama ho toh.

**Kaise (example):** Drift monitor (6.6) feature distribution shift detect karta hai → retraining
pipeline (6.3) trigger hota hai on fresh data → naya model eval baseline se behtar? (CI, 11.2) →
canary deploy (11.4) → ramp. Poora loop automated, par har naya model **validate** hota hai pehle
(blindly deploy nahi).

**Pros & cons:** ✅ model fresh rehta hai, decay se bachta hai, manual effort kam. ❌ retraining
cost (compute, Ch 12); automated-but-unvalidated retraining khatarnाk (bura data → bura model auto-
deploy — isliye CI validation zaroori); over-frequent retraining waste.

> **Ek line:** Model decay karta hai → retrain karna padta hai. Scheduled (simple) ya
> drift-triggered (smart), *par har retrained model validate karke* deploy karo (CI, 11.2) —
> automated retraining bina validation = bura model auto-ship karne ka risk.

---

<a id="116"></a>
## 11.6 — Maturity levels (manual → fully automated)

**Kya hai:** MLOps ek din mein nahi aata — yeh levels mein evolve hota hai, manual se fully
automated tak. Apni team ka level pehchano aur *agla* step lo, seedha top pe mat koodo.

**Problem kya solve karta hai:** Log ya toh zero MLOps (sab manual, notebook se prod) ya seedha
"full automation" (over-engineering, 8.1) try karte hain. Levels samajhne se aap apni team ke
hisaab se *sahi agla* step lete ho.

**Maturity levels:**
- **Level 0 — Manual:** notebook mein train, haath se deploy. Koi versioning/CI/monitoring. *Theek
  for:* early experiment, ek-do models. *Problem:* reproduce nahi hota, decay pakdा nahi jaata.
- **Level 1 — Pipelines + tracking:** training pipeline (6.3), experiment tracking (8.15), model
  registry, basic monitoring. Reproducible. *Most teams ko yahan hona chahiye.*
- **Level 2 — CI/CD:** automated testing (code+data+model, 11.2), automated deployment (canary,
  11.4). Fast, safe iteration.
- **Level 3 — Full automation:** drift-triggered automated retraining (11.5), self-healing,
  full monitoring. *Sirf jab* aapke paas bahut models / high-velocity ho.

**Kaise (example):** Ek startup Level 0 pe theek hai (ek model, manual). Jab woh model production-
critical ban jaye → Level 1 (pipeline + registry + monitoring). Jab kai models / frequent updates
→ Level 2 (CI/CD). Level 3 sirf jab scale (dozens of models) justify kare.

**Pros & cons:** ✅ apni team ke hisaab se *sahi* investment (na zyada, na kam). ❌ —; bas yeh samjho
ki har team ko Level 3 ki zaroorat *nahi* (over-engineering, 8.1). Level 1 zyadatar production
teams ke liye sweet spot hai.

> **Ek line:** MLOps levels mein aata hai (manual → pipeline → CI/CD → full auto). Apna level
> pehchano, *agla* step lo — seedha "full automation" pe mat koodo (over-engineering). Zyadatar
> teams ke liye Level 1 (pipeline + registry + monitoring) sahi hai.

[↑ Back to top](#contents)