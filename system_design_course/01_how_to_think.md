<a id="contents"></a>
# Chapter 1 — How to THINK (System Design ka Mindset)

Sabse pehle **soch** seekhni hai, tools baad mein. Zyadatar log seedha "main yeh database
use karunga, woh queue use karunga" pe kood jaate hain — aur fail ho jaate hain. Kyunki unhone
yeh socha hi nahi ki *requirement kya hai*. Yeh chapter wahi soch banata hai.

---

## Contents

- [1.1 — Sabse bada mental shift: "kaunsa tool" nahi, "kaunsa problem"](#11)
- [1.2 — Har design ke peeche 4 sawaal](#12)
- [1.3 — Trade-off thinking (har choice ka ek cost hota hai)](#13)
- [1.4 — "Simple se shuru karo" — over-engineering se kaise bachein](#14)
- [1.5 — Bottleneck dhoondhna (system kahan atak raha hai)](#15)
- [1.6 — Non-functional requirements (woh jo log bhool jaate hain)](#16)

---

<a id="11"></a>
## 1.1 — Sabse bada mental shift: "kaunsa tool" nahi, "kaunsa problem"

**Kya seekhna hai:** System design ka matlab components ki list yaad karna NAHI hai. Matlab hai —
problem ki *shape* pehchanna, phir uske hisaab se tool chunna.

**Problem kya solve karta hai (yeh soch kyun):** Agar aap pehle hi decide kar lo "main Kafka
use karunga", toh aap problem ko tool ke hisaab se mod rahe ho — ulta. Sahi tareeka: pehle
samjho *kya chahiye*, phir tool apne aap clear ho jaata hai.

**Example (galat vs sahi soch):**
- ❌ Junior: *"Recommendations banane hain? Main ek deep learning model train karunga aur API
  bana dunga."* — usne scale, latency, data, ya success-metric ke baare mein socha hi nahi.
- ✅ Senior: *"Pehle batao — kitne users? Real-time chahiye ya raat ko batch chalega? 10 million
  items hain toh main har request pe sabko score nahi kar sakta — toh do-stage design chahiye
  (pehle candidates filter, phir rank). Aur 'achha' ka matlab kya — clicks ya watch-time?"*

Dekho, senior ne **ek bhi tool** ka naam nahi liya pehle. Usne *problem ki shape* samjhi.

**Pros & cons (is soch ke):** Faayda — aap kabhi galat tool pe time waste nahi karte, aur har
choice ko justify kar sakte ho. Nuksaan — shuru mein dheemा lagta hai (turant code likhne ka
mann hota hai), par yahi dheemापन aage 10x time bachata hai.

> **Yaad rakho:** Interview ho ya real kaam — jo bhi problem aaye, pehle bolo *"Let me clarify
> the requirements"*. Seedha solution mat batao. Yeh ek line aapko junior se senior dikhati hai.

---

<a id="12"></a>
## 1.2 — Har design ke peeche 4 sawaal

**Kya seekhna hai:** Koi bhi system design problem aaye, in 4 sawaalon se shuru karo. Yeh aapka
"thinking checklist" hai.

**1. Scale kitna hai?** Kitne users, kitni requests per second (QPS), kitna data?
- *Example:* "100 users ke liye fraud detection" aur "100 million transactions/day ke liye fraud
  detection" — dono bilkul alag systems hain. Pehle wale mein ek script kaafi hai; doosre mein
  distributed streaming chahiye.

**2. Latency budget kya hai? (Real-time ya batch?)**
- *Example:* "Payment ke time fraud check" — yahan 50ms ke andar jawab chahiye (real-time).
  "Raat ko churn-risk nikalna" — yahan ghante lag sakte hain (batch). Latency requirement poora
  architecture badal deti hai.

**3. "Achha" ka matlab kya hai? (Success metric)**
- *Example:* Recommendation system mein — clicks maximize karein ya watch-time? Agar sirf clicks
  pe optimize karoge toh clickbait aa jayega. Metric galat chuna toh poora system galat banega.

**4. Failure ka cost kya hai?**
- *Example:* Fraud detection mein — ek fraud miss karna (false negative) seedha paisa loss hai;
  ek genuine customer ko block karna (false positive) customer ko gussa dilata hai. Yeh cost
  decide karta hai ki recall pe focus karein ya precision pe.

**Pros & cons:** Faayda — 30 second mein aap poori problem ka frame samajh lete ho. Nuksaan —
koi nahi, yeh hamesha karna chahiye. Inn 4 sawaal ko skip karna = galat system banana.

> **Example flow:** "Design a recommendation system" suna? Turant: *"4 sawaal — (1) kitne users
> aur items? (2) real-time feed ya batch? (3) clicks ya watch-time? (4) galat recommendation ka
> kya nuksaan?"* — bas, ab aap design kar sakte ho.

---

<a id="13"></a>
## 1.3 — Trade-off thinking (har choice ka ek cost hota hai)

**Kya seekhna hai:** System design mein koi cheez "free" nahi milti. Har faisle ka ek **cost**
hai. Senior engineer ki pehchान yahi hai ki woh cost ko *bolta* hai, chhupata nahi.

**Problem kya solve karta hai (yeh soch kyun):** Agar aap sochte ho "main isko fast bhi banaunga,
sasta bhi, aur simple bhi" — toh aap fantasy mein ho. Real mein aapko *chunna* padta hai. Jo log
trade-off nahi sochte, woh aisा system banate hain jo paper pe achha lagta hai par production mein
mehenga/dheema/tutta hai.

**Common trade-offs (har ek example ke saath):**
- **Speed vs Cost:** Recommendations ko precompute karke cache kar do → super fast, par storage +
  staleness ka cost. Ya har request pe live compute → fresh, par dheema aur mehenga (GPU).
- **Latency vs Throughput:** LLM requests ko batch karo → GPU ka throughput high, par har request
  thoda wait karega (latency up). (Ch 4 mein detail.)
- **Consistency vs Availability:** Feature store — read hamesha *bilkul* latest value de (strong
  consistency, mehenga) ya "kuch second purana chalega" (eventual, sasta aur fast)?
- **Simple vs Scalable:** Ek SQLite file → super simple, par ek machine tak. Distributed DB →
  unlimited scale, par 10x complexity.
- **Accuracy vs Latency:** Bada model = better predictions par dheema/mehenga; chhota model =
  fast/sasta par thodा kam accurate.

**Kaise bolna hai (interview/design mein):** Har choice ke saath bolo *"main X chun raha hoon
kyunki Y zaroori hai, iska cost Z hai, jo yahan acceptable hai kyunki..."*
- *Example:* "Main embeddings ko precompute karke vector DB mein daal raha hoon — retrieval fast
  hoga (zaroori, kyunki user wait kar raha hai), cost yeh ki naye documents ko re-embed karna
  padega, jo theek hai kyunki documents roz-roz nahi badalte."

**Pros & cons:** Faayda — aapka design defensible ban jaata hai, aur aap surprise se bachte ho
(production mein cost dikhe usse pehle aapne soch liya). Nuksaan — koi nahi; trade-off na sochna
hi asli nuksaan hai.

> **Ek line mein:** Jab bhi koi tool ya design chuno, turant pucho khud se — *"iska cost kya hai?
> aur kya yeh cost yahan acceptable hai?"* Agar jawab nahi pata, toh aapne abhi design nahi kiya,
> sirf guess kiya.

---

<a id="14"></a>
## 1.4 — "Simple se shuru karo" — over-engineering se kaise bachein

**Kya seekhna hai:** Hamesha *sabse simple* design se shuru karo jo kaam kar de. Complexity tabhi
add karo jab koi *real* requirement use force kare.

**Problem kya solve karta hai:** Naye engineers ka sabse bada gunaah — **over-engineering**. Woh
2,000 users ke app ke liye Kafka + Spark + Kubernetes + microservices laga dete hain, jahan ek
Postgres + ek cron job kaafi tha. Result: system itna complex ki na maintain hota hai, na debug,
aur paisa bhi barbaad.

**Kab complexity add karni hai (real reasons):**
- Data ek machine mein nahi aata → *tab* distributed (Ch 5).
- Ek machine QPS handle nahi kar pa rahi → *tab* horizontal scale + load balancer.
- Minutes/hours ki freshness kaafi nahi, seconds chahiye → *tab* streaming.
- Pehle yeh saare "agar future mein chahiye toh?" — yeh complexity add karne ka reason **nahi**
  hai. (YAGNI — "You Aren't Gonna Need It".)

**Example (sahi soch):**
- Task: "10,000 documents pe ek QA chatbot banao."
- ❌ Over-engineered: Kafka se ingestion, distributed vector DB cluster, multi-stage agentic RAG,
  auto-scaling Kubernetes — pehle din se.
- ✅ Simple-first: Ek script se documents chunk + embed karke ek local FAISS/`pgvector` index
  banao, top-k retrieve karke LLM ko bhejo. Chalega! *Jab* documents 10 million ho jayein ya QPS
  bade, *tab* managed vector DB aur scaling add karo.

**Pros & cons:** Faayda — kam code, jaldi ship, easy debug, kam paisa. Aur jab scale ki zaroorat
*sach mein* aaye, tab aap soch-samajh ke add karte ho. Nuksaan — kabhi-kabhi simple version ko
baad mein rewrite karna padta hai; par 90% case mein woh rewrite kabhi aata hi nahi, toh net
faayda.

> **Yaad rakho:** "Make it work → make it right → make it fast" — isi order mein. Pehle din se
> "fast aur scalable" banane ki koshish = aksar aisा system jo na kaam karta hai na samajh aata.
> Ek *deployed simple* system, ek *undeployed perfect* system se hamesha behtar hai.

---

<a id="15"></a>
## 1.5 — Bottleneck dhoondhna (system kahan atak raha hai)

**Kya seekhna hai:** Har system mein ek **bottleneck** hota hai — woh ek hissa jo poore system ki
speed decide karta hai. Optimize karna hai toh *us* hisse ko karo, baaki ko nahi.

**Problem kya solve karta hai:** Log galat jagah optimize karte hain. Jaise — code ko 2x fast
bana diya, par asli problem toh database tha jo har request pe 500ms le raha tha. Mehnat barbaad.
Bottleneck pehchano, warna aap us hisse ko tej kar rahe ho jo pehle se hi tej tha.

**Kaise pehchanein (soch ka tareeka):** Pucho — "system slow hai toh *kaunsa* resource exhaust ho
raha hai?"
- **CPU 100% pe ek core?** → CPU-bound, computation problem (Ch 5: multiprocessing).
- **CPU idle par phir bhi slow?** → I/O-bound, kisi cheez ka *wait* kar raha hai (API/DB/disk).
- **Memory bhar raha hai?** → data ko stream/chunk karo (Ch 5).
- **Network/disk saturate?** → woh transfer bottleneck hai.

**Example (ML context):**
- "Model serving slow hai." Dekha — GPU utilisation sirf 20%, par har request 2 second le raha
  hai. Matlab GPU bottleneck nahi hai — *data loading* hai (GPU bhookha baitha hai, data ka wait
  kar raha hai). Fix: data loading parallel karo (workers/prefetch), GPU upgrade *nahi*. Agar aap
  bina dekhe GPU upgrade kar dete, paisa barbaad hota aur problem rehti.

**Pros & cons:** Faayda — aap sahi jagah effort lagate ho, 1 fix se 10x improvement. Nuksaan —
bottleneck dhoondhne ke liye *measure* karna padta hai (guess nahi) — thoda time lagta hai, par
zaroori hai.

> **Sabse important rule:** **Measure karo, guess mat karo.** "Mujhe lagta hai yeh slow hai" —
> nahi. Profile karo, dekho *sach mein* kahan time ja raha hai, phir *us* jagah fix karo. (Ch 4
> mein measure karna seekhenge.)

---

<a id="16"></a>
## 1.6 — Non-functional requirements (woh jo log bhool jaate hain)

**Kya seekhna hai:** "Functional requirement" = system *kya* karega (recommendations de).
"Non-functional requirement" (NFR) = system *kaise* karega — kitna fast, kitna reliable, kitna
scalable, kitna secure. Log functional pe focus karke NFR bhool jaate hain — aur wahi production
mein system tod deta hai.

**Problem kya solve karta hai:** Aap aisा chatbot bana sakte ho jo *sahi* jawab deta hai
(functional ✅) par 30 second leta hai, ya 10 users pe crash ho jaata hai, ya kisi ka private data
leak kar deta hai. Functional theek tha, par NFR fail — aur system useless/khatarnaak hai.

**Important NFRs (har ek ki ek line + example):**
- **Latency:** kitni jaldi jawab? (*RAG chatbot ko 2-3 sec mein jawab chahiye, warna user chhod
  dega.*)
- **Throughput/Scale:** kitna load? (*Black Friday pe 10x traffic — handle hoga?*)
- **Availability:** kitna uptime? (*Fraud system down = transactions ruk jayein = bada nuksaan.*)
- **Reliability:** fail hone pe kya? (*Model service down ho toh fallback hai? ya poora app
  gir jaata hai?*)
- **Consistency:** data kitna fresh/sahi? (*Feature 2 second purana chalega ya bilkul latest
  chahiye?*)
- **Security/Privacy:** data safe hai? (*PII leak toh nahi ho raha? access control hai?* — Ch 13.)
- **Cost:** budget? (*Har LLM call paisa khaata hai — kya yeh sustainable hai?* — Ch 12.)
- **Maintainability:** 6 mahine baad koi aur isko samajh ke change kar payega?

**Example (soch ka):** "Design a RAG chatbot" — functional toh clear hai (docs pe QA). Par NFR
poocho: *"Latency budget? Kitne concurrent users? Documents kitne aur kitni baar update hote
hain? Har query ka cost budget? Private docs hain toh access control kaisे? Galat/hallucinated
jawab ka kya nuksaan?"* — yeh sawaal aapke poore architecture ko shape karte hain.

**Pros & cons:** Faayda — aap aisा system banate ho jo *sach mein* production mein chalta hai, na
ki sirf demo mein. Nuksaan — NFR sochne se design bada/complex lagta hai, par yeh complexity
*zaroori* hai (over-engineering se alag — yeh real requirements hain).

> **Ek line mein:** Functional requirement aapko batata hai *kya* banana hai; non-functional
> batata hai *kya woh production mein zinda rahega ya nahi*. Dono poocho — warna aap ek aisा
> system design karoge jo kaagaz pe sahi, asli duniya mein fail.

[↑ Back to top](#contents)
