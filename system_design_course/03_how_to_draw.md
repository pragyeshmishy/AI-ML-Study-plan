<a id="contents"></a>
# Chapter 3 — How to DRAW (Diagram banane ki kala)

System design ka ek bada hissa hai **diagram banana** — boxes aur arrows se apna design dikhana.
Interview mein whiteboard pe, kaam mein design doc mein. Achha diagram aapki soch ko clear karta
hai (aapke liye bhi, doosron ke liye bhi). Yeh chapter sikhata hai *kya* banao, *kaise* banao,
aur kya *galti* mat karo.

---

## Contents

- [3.1 — Diagram kyun? (sirf dikhावा nahi)](#31)
- [3.2 — Visual vocabulary (boxes, arrows, symbols ka matlab)](#32)
- [3.3 — Left-to-right data flow (diagram ka layout)](#33)
- [3.4 — Layering & grouping (clutter se kaise bachein)](#34)
- [3.5 — Kya label karna hai (arrows pe protocol, data, numbers)](#35)
- [3.6 — Common diagram galtiyan](#36)
- [3.7 — Tools (whiteboard, Excalidraw, Mermaid)](#37)

---

<a id="31"></a>
## 3.1 — Diagram kyun? (sirf dikhावा nahi)

**Kya seekhna hai:** Diagram banana decoration nahi hai — yeh *sochne ka* aur *samjhane ka* tool
hai. Jab aap boxes banate ho, aapko khud clear hota hai ki system ke kitne hisse hain aur woh
kaise jude hain.

**Problem kya solve karta hai:** Sirf bol ke ("API database se baat karti hai, phir cache, phir
model...") — sun-ne wala (interviewer/teammate) confuse ho jaata hai, aur aap khud bhi track kho
dete ho. Diagram sab kuch ek jagah dikha deta hai — poora system ek nazar mein.

**Faayde (3 cheezein diagram deta hai):**
1. **Clarity (aapke liye):** boxes banate hi pata chalta hai kahin koi piece miss toh nahi
   (jaise "monitoring ka box hi nahi banaya!").
2. **Communication:** ek diagram 100 words se behtar samjhata hai. Interviewer turant aapka
   design "dekh" leta hai.
3. **Discussion anchor:** "is box pe focus karte hain" — diagram pe ungli rakh ke baat aage
   badhती hai.

**Example:** "RAG system" ko sirf shabdon mein samjhana vs ek diagram jisme `User → Query Service
→ Vector DB → LLM → Answer` aur alag se `Docs → Ingestion → Vector DB` dikhe — diagram mein 2
second mein poora system samajh aata hai, shabdon mein 2 minute aur phir bhi confusion.

**Pros & cons:** Faayda — clarity, communication, sab kuch organised. Nuksaan — koi nahi; bas
diagram ko *itna* fancy mat banao ki banane mein hi saara time chala jaye (interview mein simple
boxes kaafi hain).

> **Ek line:** Bolte waqt *saath-saath* diagram banao — "yeh API hai (box banaya), yeh DB se baat
> karti hai (arrow kheencha)..." Diagram aur baat ek saath chalein, taaki sun-ne wala follow kar
> sake.

---

<a id="32"></a>
## 3.2 — Visual vocabulary (boxes, arrows, symbols ka matlab)

**Kya seekhna hai:** Diagrams ki ek "bhasha" hoti hai — kaunsा shape kya matlab. Yeh standard
nahi hai 100%, par ek common samajh hai jo aapko use karni chahiye taaki sab samajh sakein.

**Basic vocabulary (har ek ka matlab + kab use):**
- **Rectangle (box)** = ek service/component/process. (*API, Query Service, LLM Service.*)
- **Cylinder** = a database / persistent storage. (*Postgres, vector DB.*) ASCII mein hum `[(DB)]`
  ya bas `[DB]` likh dete hain.
- **Arrow (→)** = data ya request ka flow, *direction ke saath*. (*User → API matlab user se API
  ko request jaati hai.*)
- **Double-headed arrow (↔)** = dono taraf flow (request + response). Aksar hum sirf request ki
  direction dikhate hain.
- **Dashed arrow (-->)** = async / background flow (turant nahi, baad mein). (*API --> queue,
  fire-and-forget.*)
- **Cloud/box labelled "external"** = bahar ka system (3rd-party API, LLM provider).
- **Cluster (box ke andar chhote boxes)** = ek cheez ke multiple replicas/instances.

**Example (ASCII mein simple notation):**
```
[User] ──request──> [ API ] ──> [(Database)]
                       │
                       └----async----> [Queue] ~~> [Worker]
```
Yahan: solid arrow = sync request, dashed/`~~>` = async background, cylinder-jaisा `[(Database)]`
= storage. Bas itni vocabulary se 90% diagrams ban jaate hain.

**Pros & cons:** Faayda — standard symbols use karne se sab turant samajh jaate hain, aapko
explain nahi karna padta. Nuksaan — over-complicate mat karo (10 alag shapes yaad rakhne ki
zaroorat nahi); box + arrow + cylinder se kaam chal jaata hai.

> **Ek line:** Kam se kam symbols use karo — box (service), cylinder (storage), solid arrow
> (sync), dashed arrow (async). Itne se hi clear diagram ban jaata hai; fancy shapes ki zaroorat
> nahi.

---

<a id="33"></a>
## 3.3 — Left-to-right data flow (diagram ka layout)

**Kya seekhna hai:** Diagram ko **left-to-right** (ya top-to-bottom) banao, data ke flow ke
hisaab se — jahan se data aata hai (left) se jahan jaata hai (right). Random jagah boxes mat
chipkao.

**Problem kya solve karta hai:** Agar boxes idhar-udhar bikhre hon aur arrows har taraf jaa rahe
hon (spaghetti), toh diagram samajh nahi aata — aur aapki soch bhi unclear lagti hai. Ek
consistent direction se diagram "padha" ja sakta hai, kahani ki tarah.

**Standard layout (flow ki direction):**
`Source/User (left) → Entry (API/gateway) → Processing → Storage → Serving → Output (right)`

**Example (sahi vs galat):**
```
SAHI (left-to-right, flow clear):
[User] ──> [API] ──> [Service] ──> [(DB)]
                         │
                         ▼
                      [Cache]

GALAT (boxes bikhre, arrows har taraf — spaghetti):
       [(DB)]
         ▲  ╲
[Service]──╲──[API]
   ▲         ╲ │
[Cache]<──────[User]   ← samajhna mushkil
```

**Pros & cons:** Faayda — diagram ek kahani ki tarah padha jaata hai (left se right), clean aur
professional dikhता hai. Nuksaan — kabhi-kabhi feedback loops (jaise monitoring → retraining)
peeche ki taraf jaate hain; unhe alag se ya dashed arrow se dikha do, par main flow left-to-right
hi rakho.

> **Ek line:** Data jahan se shuru hota hai woh left, jahan khatam wahां right. Arrows ज्यादातर
> ek hi direction (left→right) mein. Yeh ek simple rule poore diagram ko readable bana deta hai.

---

<a id="34"></a>
## 3.4 — Layering & grouping (clutter se kaise bachein)

**Kya seekhna hai:** Jab system bada ho, related boxes ko **group** karo (ek bade box/dotted
boundary ke andar) aur **layers** mein socho (client → service → data layer). Sab kuch ek flat
chitra mein mat thoso.

**Problem kya solve karta hai:** Bade systems mein 15-20 boxes ho sakte hain. Sab ek saath
dikhaoge toh clutter — kuch samajh nahi aata. Grouping/layering se aap pehle bada picture dikhate
ho, phir zarurat pade toh ek group ke andar zoom karte ho.

**Common layers (ML system mein):**
- **Client/Entry layer:** user, API gateway, load balancer.
- **Service/Compute layer:** business logic, model serving, query service.
- **Data layer:** databases, caches, vector DB, feature store, object store.
- **Offline/Batch layer (alag):** ingestion pipeline, training pipeline (yeh request-time se alag
  chalta hai).

**Example (grouping with a boundary):**
```
┌─ Online (request-time) ──────────────┐
│ [User] → [API] → [Query Svc] → [LLM] │
│                      │               │
│                      ▼               │
│                  [Vector DB]         │
└──────────────────────────────────────┘
┌─ Offline (batch) ─────────────────────┐
│ [Docs] → [Ingestion pipeline] → [Vector DB] │
└────────────────────────────────────────┘
```
Online aur offline ko alag group karne se turant clear hai ki kya request pe hota hai aur kya
background mein.

**Pros & cons:** Faayda — bade system bhi readable rehte hain; aap "online vs offline", "compute
vs storage" jaise concepts visually dikha dete ho. Nuksaan — chhote system (4-5 boxes) ke liye
grouping ki zaroorat nahi; yeh tab kaam aata hai jab boxes badein.

> **Ek line:** 5 se zyada boxes ho gaye? Related ko group karo (online/offline, compute/data).
> Pehle groups dikhao, phir ek group ke andar detail — yeh "zoom in/out" approach clutter khatam
> kar deti hai.

---

<a id="35"></a>
## 3.5 — Kya label karna hai (arrows pe protocol, data, numbers)

**Kya seekhna hai:** Sirf boxes aur arrows kaafi nahi — unpe **label** lagao. Arrow pe likho kya
data ja raha hai; box pe likho woh kya hai aur (zaroori ho toh) scale/tech.

**Problem kya solve karta hai:** Bina label ke arrow sirf "kuch connect hai" batata hai, par
*kya* nahi. "User → API" theek hai, par "User --(HTTPS, 10k QPS)--> API" zyada batata hai —
protocol, load, sab. Labels diagram ko self-explanatory banate hain.

**Kya label karna hai:**
- **Arrows pe:** kya data/request (`query`, `top-k chunks`, `embeddings`), protocol agar relevant
  (`HTTPS`, `gRPC`, `Kafka`), aur numbers agar discuss kar rahe (`~10k QPS`, `~50ms`).
- **Boxes pe:** component ka naam (`Query Service`), aur agar relevant toh tech (`Postgres`,
  `FAISS`) ya scale (`x10 replicas`).

**Example (labelled vs bare):**
```
BARE (kam info):
[User] ──> [API] ──> [Vector DB]

LABELLED (clear, discussable):
[User] ──question (HTTPS)──> [API] ──query embedding──> [Vector DB]
                                                          │ top-5 chunks
                                                          ▼
                                                     [LLM Service]
```
Labelled version mein turant pata hai kya flow ho raha hai har step pe.

**Pros & cons:** Faayda — diagram self-explanatory ban jaata hai, aur numbers (QPS/latency) dikhane
se aap scale-aware lagte ho. Nuksaan — *zyada* labels se clutter; sirf important data/protocol/
numbers likho, har choti cheez nahi.

> **Ek line:** Har arrow pe likho *kya* ja raha hai (data/request ka naam), aur jahan scale matter
> kare wahां number daalo (QPS, latency). Itna context diagram ko baat-cheet ke layak bana deta
> hai.

---

<a id="36"></a>
## 3.6 — Common diagram galtiyan (in se bacho)

**Kya seekhna hai:** Kuch galtiyan baar-baar hoti hain jo diagram ko confusing ya weak bana deti
hain. Inhe jaan lo taaki avoid kar sako.

**Galtiyan aur fix (har ek example ke saath):**
- ❌ **Pehle hi sabse zyada detail:** har box ke andar ki detail pehle dikha di, poora flow miss.
  → **Fix:** pehle high-level (Ch 2.3), phir zoom in.
- ❌ **Arrows bina direction:** lines toh hain par pata nahi data kis taraf ja raha. → **Fix:**
  hamesha arrowhead (→) lagao.
- ❌ **Spaghetti (boxes har jagah, arrows cross):** → **Fix:** left-to-right layout (3.3),
  grouping (3.4).
- ❌ **No labels:** sirf boxes-arrows, pata nahi kya flow ho raha. → **Fix:** label arrows (3.5).
- ❌ **Monitoring/failure boxes hi nahi:** sirf happy path banaya. → **Fix:** monitoring aur
  fallback ko bhi dikhao (yeh senior signal hai).
- ❌ **Online aur offline mix:** ingestion (batch) aur query (real-time) ek hi flat picture mein,
  confusing. → **Fix:** alag group karo (3.4).
- ❌ **Itna fancy ki time hi banane mein chala gaya:** → **Fix:** interview mein simple boxes
  kaafi; sundarta se zyada *clarity* matter karti hai.

**Example (galat → sahi soch):** Ek candidate ne RAG ka diagram banaya jisme ingestion aur query
dono ek hi tangle mein the, arrows bina direction, aur koi monitoring nahi. Interviewer confuse.
Sahi: do alag groups (offline ingestion, online query), arrows directed, ek chhota "monitoring"
box jo cost/latency track karta hai.

**Pros & cons:** Faayda — in galtiyon se bachke aapka diagram clear aur professional dikhता hai,
aur poora system (including failures) cover karta hai. Nuksaan — koi nahi.

> **Ek line:** Sabse badi galti — sirf "happy path" banana aur monitoring/failure bhool jaana.
> Doosri — spaghetti. Dono se bacho: left-to-right, labelled, grouped, with a monitoring box.

---

<a id="37"></a>
## 3.7 — Tools (whiteboard, Excalidraw, Mermaid)

**Kya seekhna hai:** Diagram banane ke alag-alag tools hain, situation ke hisaab se. Koi ek
"best" nahi — context pe depend karta hai.

**Tools aur kab use karein:**
- **Whiteboard / paper / tablet** — *interview* mein (in-person ya online whiteboard tool). Fast,
  rough, real-time. Yahan sundarta nahi, *speed aur clarity* matter karti hai. Practice karo
  taaki jaldi saaf boxes bana sako.
- **Excalidraw / draw.io / tldraw** — *design docs* aur *collaboration* ke liye. Hand-drawn jaisा
  look (Excalidraw) ya clean (draw.io). Easy, drag-drop, share karne layak.
- **Mermaid** — *code/markdown mein* diagram (text se banta hai, version-control friendly). Docs,
  READMEs, wikis mein best — kyunki text hai toh git mein track hota hai aur edit easy hai.
- **Cloud-specific (AWS/GCP diagram tools)** — jab actual infra dikhana ho specific services ke
  saath.

**Example (Mermaid — text se diagram):**
```
flowchart LR
    User -->|question| API
    API -->|embed query| VectorDB[(Vector DB)]
    VectorDB -->|top-k chunks| LLM[LLM Service]
    LLM -->|answer| User
```
Yeh text markdown mein render ho ke ek proper diagram ban jaata hai — docs ke liye perfect, kyunki
edit aur version-control easy.

**Pros & cons:**
- Whiteboard — fastest, interview-real, par save/share mushkil, redraw karna padta hai.
- Excalidraw/draw.io — clean, shareable, par ek alag tool kholna padta hai.
- Mermaid — version-controlled, docs ke saath rehta hai, par complex diagrams mein layout control
  kam, aur seekhne mein thodा time.

> **Ek line:** Interview ke liye whiteboard pe *fast saaf boxes* banane ki practice karo (yahi
> asli skill hai). Docs ke liye Mermaid (text, git-friendly) ya Excalidraw (clean, shareable).
> Tool se zyada *clarity* matter karti hai.

[↑ Back to top](#contents)