<a id="contents"></a>
# Chapter 2 — How to ACT (Step-by-Step Process)

Ch 1 mein *soch* seekhi. Ab *action* — jab aapke saamne ek blank problem ho (interview ya real
kaam), toh **kaunse step, kis order mein** karne hain. Yeh ek repeatable recipe hai — ratto mat,
samjho, phir har problem pe apply karo.

---

## Contents

- [2.0 — Poora process ek nazar mein (7 steps)](#20)
- [2.1 — Step 1: Requirements clarify karo](#21)
- [2.2 — Step 2: Scale estimate karo (back-of-envelope)](#22)
- [2.3 — Step 3: High-level design (boxes & arrows)](#23)
- [2.4 — Step 4: Har component deep-dive](#24)
- [2.5 — Step 5: Bottlenecks aur scaling](#25)
- [2.6 — Step 6: Failure modes aur monitoring](#26)
- [2.7 — Step 7: Trade-offs summarize karo](#27)
- [2.8 — Time management (interview mein 45 min kaise baatein)](#28)

---

<a id="20"></a>
## 2.0 — Poora process ek nazar mein (7 steps)

**Kya seekhna hai:** Koi bhi system design — chahe interview ho ya real — in 7 steps mein hota
hai, isi order mein. Yeh aapka GPS hai; isse aap kabhi "ab kya karun?" mein nahi atkoge.

**Problem kya solve karta hai:** Bina process ke log idhar-udhar koodte hain — pehle thoda
database socha, phir achanak API, phir wapas data. Interviewer (ya aap khud) confuse ho jaate
ho, aur kuch important cheez (jaise monitoring) chhoot jaati hai. Fixed process = complete +
organised design, har baar.

**Saat steps (yaad rakhne layak):**
1. **Requirements clarify karo** — kya banana hai, scale, latency, success-metric (Ch 1.2 ke 4
   sawaal). *Yahan jaldbaazi mat karo.*
2. **Scale estimate karo** — QPS, storage, memory ka mota-mota hisaab (Ch 4 — napkin math).
3. **High-level design** — bade boxes aur arrows banao (data → process → store → serve).
4. **Har component deep-dive** — interviewer (ya requirement) jis box pe focus chahe, usme ghuso.
5. **Bottlenecks aur scaling** — system kahan atkega, aur use kaise scale karoge.
6. **Failure modes aur monitoring** — kya-kya tut sakta hai, fallback kya, monitor kaise.
7. **Trade-offs summarize** — "maine X chuna kyunki Y, cost Z" — poora design ek line mein
   justify.

**Example (poora flow chhota karke):** "Design Twitter feed" →
(1) "kitne users, read-heavy ya write-heavy?" → (2) "200M users, ~1 lakh tweets/sec read" →
(3) boxes: user → API → feed service → cache → DB → (4) "feed kaise banti hai — push ya pull?"
deep-dive → (5) "celebrity ka 100M followers = bottleneck, hybrid approach" → (6) "cache gir jaye
toh DB pe load, fallback?" → (7) "maine push+pull hybrid chuna kyunki..."

**Pros & cons:** Faayda — complete, organised, kuch nahi chhutta, aur aap confident dikhte ho.
Nuksaan — koi nahi; ha, process ko *rigidly* mat follow karo agar interviewer kisi ek step pe
zyada time chahe (point 4 pe flexible raho).

> **Yaad rakho:** Steps 1-2 (requirements + scale) pe jaldbaazi sabse badi galti hai. Yahi neev
> hai. Galat neev pe sundar building bhi gir jaati hai.

---

<a id="21"></a>
## 2.1 — Step 1: Requirements clarify karo

**Kya seekhna hai:** Problem sunte hi solution mat batao. Pehle *sawaal* poocho — kya, kitna,
kab, kis-kis ke liye. Yeh 5 minute aapka poora design bachate hain.

**Problem kya solve karta hai:** Problem statements jaan-boojh ke vague hote hain ("design a
recommendation system" — bas itna). Agar aap apni assumptions pe design karne lago, toh aap
galat cheez bana doge. Clarify karna dikhata hai ki aap requirements-first sochte ho (senior
signal).

**Kya poochna hai (Ch 1.2 ke 4 sawaal + thodा aur):**
- **Functional:** system *exactly* kya karega? Input kya, output kya? (*"Recommendations — feed
  pe 20 items? ya 'aur dekho' page? input mein user history milegi?"*)
- **Scale:** users, QPS, data volume? (*"100M users? peak QPS? data kitna — GB ya TB?"*)
- **Latency:** real-time ya batch? budget? (*"Feed real-time chahiye ya raat ko precompute?"*)
- **Success metric:** "achha" ka matlab? (*"Clicks, watch-time, ya revenue?"*)
- **Constraints:** koi special cheez? (*"Privacy? Existing infra? Cost limit?"*)

**Example (real flow):**
- Interviewer: "Design a system to detect fraudulent transactions."
- Aap: *"Pehle clarify karun — (1) real-time block karna hai transaction ke time, ya baad mein
  flag? (2) volume kya — kitne transactions/sec peak pe? (3) false positive (genuine customer
  block) zyada bura hai ya false negative (fraud miss) zyada bura? (4) labels kab milte hain —
  turant ya hafton baad (chargebacks)?"*
- Yeh 4 sawaal poore design ko shape karte hain — real-time matlab streaming + low latency,
  imbalanced data matlab special handling, etc.

**Pros & cons:** Faayda — aap sahi problem solve karte ho, aur scope clear ho jaata hai (chhota
ya bada). Nuksaan — kuch log sochte hain "time waste ho raha", par ulta — yeh time aage ghante
bachata hai. Skip karna = galat system.

> **Ek line:** Jaldbaazi mat karo. "Let me clarify a few things first" bolo, 5 min sawaal
> poocho, *phir* design shuru karo. Yahi sabse pehla aur sabse important step hai.

---

<a id="22"></a>
## 2.2 — Step 2: Scale estimate karo (back-of-envelope)

**Kya seekhna hai:** Design karne se *pehle*, mota-mota hisaab lagao — kitni QPS, kitna storage,
kitni memory. Yeh numbers decide karte hain ki aapko ek machine chahiye ya ek cluster.

**Problem kya solve karta hai:** Bina numbers ke aap nahi keh sakte "yeh ek machine pe chalega ya
nahi". Estimate se aapko pata chalta hai ki problem *kis tier* mein hai — ek script, ek bada
server, ya distributed system. Yeh poora architecture decide karta hai.

**Kya estimate karna hai (Ch 4 mein detail, yahan soch):**
- **QPS (queries/sec):** total requests/day ÷ 86400 (seconds in a day), phir peak ke liye 2-3x.
- **Storage:** items × size-per-item. (*10M users × 1KB profile = 10GB.*)
- **Memory:** kya cache/index RAM mein aayega? (*100M embeddings × 1536 dims × 4 bytes ≈ 600GB →
  ek machine mein nahi aayega → sharding chahiye.*)
- **Bandwidth:** data in/out per second.

**Example (ML context):**
- "Embed 100 million documents." Hisaab: agar embedding API 100 docs/sec karta hai aur har call
  300ms, toh 100M ÷ 100 = 1M calls. Single-threaded toh hafte lag jayenge → matlab batching +
  parallelism chahiye (Ch 5). Aur 100M × 1536-dim × 4 bytes = ~600GB vectors → ek RAM mein nahi →
  vector DB with sharding. Yeh numbers ne *turant* architecture bata diya.

**Pros & cons:** Faayda — aap sahi tier ka system design karte ho (na over, na under). Numbers
aapke decisions ko justify karte hain. Nuksaan — exact nahi hota (isliye "back-of-envelope"), par
order-of-magnitude kaafi hai — "GB ya TB?", "100 ya 100 million?".

> **Ek line:** Exact answer ki zaroorat nahi — bas yeh jaanna hai ki number *chhota* hai ya
> *bahut bada*. 600GB sunke aap turant jaante ho "ek machine mein nahi aayega" — bas yahi insight
> chahiye.

---

<a id="23"></a>
## 2.3 — Step 3: High-level design (boxes & arrows)

**Kya seekhna hai:** Ab bade-bade components banao aur unhe arrows se jodo — data kahan se aata
hai, kahan process hota hai, kahan store hota hai, kahan se serve hota hai. Detail abhi nahi,
sirf bada picture.

**Problem kya solve karta hai:** Seedha kisi ek component ki detail mein ghusna (jaise "database
schema") — aur poora flow miss ho jaata hai. High-level design pehle banane se aap (aur
interviewer) poora system ek saath dekh lete ho, phir detail mein jaate ho.

**Kaise banana hai (soch):** Left-to-right data ka flow socho:
`Source/User → Entry point (API/gateway) → Processing → Storage → Serving → Output`
Har major responsibility = ek box. Box ke beech arrows = data ka flow (with direction).

**Example (RAG chatbot ka high-level):**
```
User question
     │
     ▼
[API / Gateway] ──> [Query Service] ──> [Vector DB]   (retrieve top-k chunks)
                          │
                          ▼
                     [LLM Service] <── [Prompt builder]
                          │
                          ▼
                   Answer + citations
   (alag se, offline: [Docs] → [Ingestion pipeline] → [Vector DB])
```
Bas itna — abhi har box ke andar kya hai woh nahi, sirf flow. (Diagram banana Ch 3 mein detail.)

**Pros & cons:** Faayda — poora system ek nazar mein dikhता hai, communication easy hota hai,
aur aap dekh lete ho ki kahin koi piece miss toh nahi. Nuksaan — koi nahi; bas dhyान rakho ki
isme atko mat — yeh 5-10 min ka kaam hai, phir deep-dive.

> **Ek line:** Pehle poora skeleton banao (boxes + arrows), phir ek-ek box mein ghuso. Skeleton
> banaye bina detail mein jaana = jungle mein bina naksha ghoomna.

---

<a id="24"></a>
## 2.4 — Step 4: Har component deep-dive

**Kya seekhna hai:** Ab high-level ke kisi ek (ya zyada) box ke *andar* jao — woh exactly kaise
kaam karega, kaunsa tool, kya data structure, kya schema.

**Problem kya solve karta hai:** High-level design "kya" batata hai, par "kaise" nahi. Interview
mein interviewer aksar ek box pe focus karega ("retrieval kaise karoge?"); real kaam mein har box
ko actually banana padta hai. Deep-dive yahi hai.

**Kaise karna hai (soch):** Jis box mein ghuso, uspe woh sawaal poocho jo Ch 1 mein seekhe — is
component ka scale? latency? data shape? Phir tool chuno (Ch 5) *with justification* (Ch 1.3
trade-off).

**Example (RAG ke "Query Service" box ka deep-dive):**
- "Yeh box: query embed karo → vector DB se top-k laao → prompt banao → LLM call."
- Detail: kaunsa embedding model (same as ingestion — warna retrieval tutega)? top-k kitna (5?
  re-ranking chahiye?)? prompt mein kitne chunks fit honge (token budget)? LLM call stream karein
  (latency feel)? output validate karein (hallucination)? Har choice ka reason bolo.

**Pros & cons:** Faayda — aap dikhate ho ki aap sirf buzzwords nahi jaante, actually bana sakte
ho. Detail = depth = senior signal. Nuksaan — *har* box ko equal detail mat do; jahan risk/
interest ho wahan ghuso, baaki ko light rakho (time management, 2.8).

> **Ek line:** Deep-dive wahan karo jahan asli mushkil/risk hai (jaise RAG mein retrieval
> quality, recsys mein candidate generation) — har trivial box mein nahi. Depth dikhao jahan
> matter karta hai.

---

<a id="25"></a>
## 2.5 — Step 5: Bottlenecks aur scaling

**Kya seekhna hai:** Apne design ko dekho aur poocho — "jab load 10x ho jayega, yeh kahan
atkega?" Phir us bottleneck ko scale karne ka plan batao.

**Problem kya solve karta hai:** Ek design jo aaj 100 users pe chalta hai, woh 100M pe gir
sakta hai. Bottleneck pehle se pehchanke (Ch 1.5) aap dikhate ho ki aapne scale socha hai — aur
real mein system production load jhel paata hai.

**Kaise socho (common bottlenecks aur fixes):**
- **Ek DB sab reads/writes jhel raha hai?** → read replicas (reads baant do), caching (Ch 5),
  ya sharding (data tukdon mein baant do).
- **Ek serving machine QPS handle nahi kar pa rahi?** → horizontal scale (zyada replicas) +
  load balancer (Ch 5).
- **Ek slow LLM/model call?** → caching (9.12), batching, ya chhota/faster model.
- **Ek hot key (celebrity user, popular item)?** → special handling/caching us key ke liye.

**Example (recsys):** "Feed service har request pe 10M items score kar raha hai" — yeh bottleneck
hai (10M × QPS = impossible). Fix: **two-stage** — pehle ek sasta retrieval model 10M → 1000
candidates laaye (ANN index), phir heavy ranker sirf 1000 ko score kare. Bottleneck gone.

**Pros & cons:** Faayda — system scale karta hai, aur aap proactive dikhte ho (problem aane se
pehle solve). Nuksaan — har cheez ko scale karne ke chakkar mein over-engineer mat karo (Ch 1.4)
— sirf *real* bottleneck ko, jo aapke scale estimate (2.2) se pata chalega.

> **Ek line:** Apne design ko "10x load" ka test do. Jo box sabse pehle girega, woh bottleneck
> hai — uska scaling plan batao, baaki ko chhedo mat.

---

<a id="26"></a>
## 2.6 — Step 6: Failure modes aur monitoring

**Kya seekhna hai:** Poocho — "kya-kya tut sakta hai? aur tab kya hoga?" Phir batao kaise pata
chalega (monitoring) aur fail hone pe kya hoga (fallback). **Yeh step seniors ko juniors se alag
karta hai.**

**Problem kya solve karta hai:** Junior maan leta hai sab theek chalega. Real duniya mein cheezein
*tutti* hain — DB down, model service crash, data drift. Agar aapne socha nahi, toh ek choti
failure poora system gira deti hai, aur aapko pata bhi raat ko users ke shikायat se chalta hai.

**Kya socho (har ek example ke saath):**
- **Koi service down ho gayi?** → fallback kya? (*Model down → popularity-based default
  recommendations do, poora app mat girao.*)
- **Dependency slow/flaky?** → timeout + retry + circuit breaker (Ch 5).
- **Data/model drift?** → monitor karo input distributions; drift pe retrain (Ch 6/11).
- **Kaise pata chalega kuch toot raha hai?** → metrics (latency, error rate), alerts, dashboards.
  Bina monitoring ke production = aankh band karke gaadi chalana.

**Example (RAG):** "LLM service down ho jaye toh?" → fallback: retrieved chunks raw dikha do (poora
crash nahi). "Retrieval mein kuch relevant nahi mila?" → LLM bole "mujhe yeh nahi pata" (galat
jawab banane se behtar). "Cost spike?" → per-query cost monitor + alert.

**Pros & cons:** Faayda — system production-ready banta hai, choti failures contain hoti hain,
aur aap *senior-level* maturity dikhate ho. Nuksaan — koi nahi; yeh step skip karna sabse common
"strong technical but rejected" reason hai.

> **Ek line:** Design ke baad poocho — "yeh fail kaise hoga, aur main kaise jaanunga?" Agar jawab
> nahi hai, toh design adhoora hai. Monitoring + fallback optional nahi, zaroori hai.

---

<a id="27"></a>
## 2.7 — Step 7: Trade-offs summarize karo

**Kya seekhna hai:** Ant mein, apne bade decisions ko summarize karo — "maine X chuna kyunki Y,
iska cost Z hai." Yeh aapke design ko *defensible* banata hai aur strong close deta hai.

**Problem kya solve karta hai:** Bina summary ke aapka design "yeh kar diya, woh kar diya" lagta
hai — bina yeh dikhaye ki aap *samajhte* ho ki har choice ka alternative aur cost tha. Trade-off
summary dikhati hai ki aapne soch-samajh ke chuna, randomly nahi.

**Kaise karna hai:** 3-4 bade decisions lo, har ek ko bolo: choice → reason → cost → kyun
acceptable.

**Example (RAG design close):**
- "Maine **vector DB + top-k retrieval** chuna kyunki semantic search chahiye; cost — exact
  keyword match miss ho sakta hai, isliye agar eval mein zaroorat dikhi toh **hybrid search** add
  karunga.
- **Embeddings precompute + cache** kiye — fast aur sasta re-run; cost — naye docs re-embed karne
  padte hain (incremental pipeline se handle).
- **LLM ko stream** kiya — user ko fast lage; cost — thodा extra complexity.
- Maine **agentic RAG abhi nahi** kiya — over-engineering hoti; eval mein zaroorat dikhe toh add
  karunga."

**Pros & cons:** Faayda — strong, confident close; dikhata hai aap trade-offs samajhte ho aur
*kya nahi kiya* aur *kyun* bhi jaante ho (jo equally important hai). Nuksaan — koi nahi.

> **Ek line:** Har bade decision ko ek line mein justify karo — *choice + reason + cost*. Aur jo
> aapne *jaan-boojh ke nahi kiya* (over-engineering se bachne ke liye), woh bhi bolo — yeh
> maturity dikhata hai.

---

<a id="28"></a>
## 2.8 — Time management (interview mein 45 min kaise baatein)

**Kya seekhna hai:** Interview mein time limited hota hai (~45 min). 7 steps ko time ke hisaab se
baatna ek skill hai — warna aap requirements mein 30 min laga doge aur monitoring tak pahunchoge
hi nahi.

**Rough time split (45 min ke liye):**
| Time | Step | Kya karein |
|---|---|---|
| 0-8 min | Requirements (2.1) + scale (2.2) | Sawaal poocho, numbers estimate karo. Jaldbaazi nahi, par atko bhi mat. |
| 8-15 min | High-level design (2.3) | Boxes + arrows, poora flow. |
| 15-32 min | Deep-dive (2.4) | Interviewer jis box pe chahe (ya sabse important), usme ghuso. |
| 32-40 min | Bottlenecks + failures (2.5, 2.6) | Scaling aur monitoring/fallback. |
| 40-45 min | Trade-offs (2.7) + sawaal | Summarize + interviewer se pucho. |

**Problem kya solve karta hai:** Bina time-sense ke log requirements ya kisi ek box mein atak
jaate hain, aur scaling/monitoring (jo senior signals hain) tak pahunchte hi nahi. Time baant ke
aap *poora* loop cover karte ho.

**Example:** Agar 20 min ho gaye aur aap abhi tak requirements mein ho, toh aapne galti ki —
aage badho. Agar interviewer ek box pe zyada interested hai, toh flexible raho par mentally check
karo ki aap monitoring/trade-offs bhool toh nahi rahe.

**Pros & cons:** Faayda — aap poora design cover karte ho, na ki aadha. Nuksaan — clock dekhna
distract karta hai; practice se yeh natural ho jaata hai (mock interviews — woh doosre doc mein
hai).

> **Ek line:** Time pe nazar rakho. Requirements + high-level pehle 15 min mein nipta do, taaki
> deep-dive, scaling, aur monitoring ke liye time bache. Aadha design (bina monitoring/trade-off)
> = weak.

[↑ Back to top](#contents)