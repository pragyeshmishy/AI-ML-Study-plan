<a id="contents"></a>
# Chapter 5 — Building Blocks / Tools (Kab use karein, KAB NAHI)

Ab tools. Har tool ke liye: **kya hai, kya problem solve karta hai, kab use karein, KAB NAHI,
aur trade-off.** Sabse important hissa hai **"kab NAHI"** — kyunki galat tool sahi tool se zyada
nuksaan karta hai. Har tool ke saath ML example.

---

## Contents

- [5.1 — Load balancer](#51)
- [5.2 — Cache (Redis/Memcached)](#52)
- [5.3 — Databases: SQL vs NoSQL](#53)
- [5.4 — Message queue / streaming (Kafka, SQS)](#54)
- [5.5 — Object storage (S3) & data lake](#55)
- [5.6 — Data warehouse (BigQuery/Snowflake)](#56)
- [5.7 — Vector database](#57)
- [5.8 — Orchestrator (Airflow/Dagster)](#58)
- [5.9 — Stream processor (Flink/Spark Streaming)](#59)
- [5.10 — Distributed compute (Spark/Dask)](#510)
- [5.11 — Feature store](#511)
- [5.12 — Containers & Kubernetes](#512)

---

<a id="51"></a>
## 5.1 — Load balancer

**Kya hai:** Ek component jo aane wali requests ko multiple servers (replicas) mein baant deta
hai, aur dead/overloaded server ko skip karta hai.

**Problem kya solve karta hai:** Jab ek server load handle nahi kar pata, aap kai servers lagate
ho (horizontal scaling). Par "kaunsi request kaunse server pe jaye" — yeh decide karne wala koi
chahiye. Load balancer wahi hai. Bina iske aap multiple servers use hi nahi kar sakte.

**Kab use karein:** Jab ek se zyada server/replica ho — yaani lagभग har production serving setup.
Yeh scale (load baant) aur availability (ek server mare toh baaki pe bhej) dono deta hai.

**Kab NAHI:** Single server/prototype mein zaroorat nahi (extra complexity). Aur batch jobs mein
(jo request-response nahi hain) iska role nahi.

**Kaise (ML example):** 10 model-serving replicas ke aage load balancer — inference requests sabme
baant deta hai (round-robin ya "least busy"), health-check se dead replica skip karta hai, aur
canary deploy ke liye 5% traffic naye model ko bhej sakta hai (Ch 11).

**Pros & cons:** ✅ scale + redundancy + zero-downtime deploys. ❌ ek aur component (khud highly-
available hona chahiye, warna single point of failure ban jaayega); sticky-session needs
complexity badhati hain.

> **Ek line:** Ek se zyada server = load balancer chahiye. Single server = bhool jao.

---

<a id="52"></a>
## 5.2 — Cache (Redis / Memcached)

**Kya hai:** Ek fast (usually in-memory) store jo mehenge kaam ka result rakhता hai, taaki dobara
woh kaam na karna pade — repeat request turant serve ho.

**Problem kya solve karta hai:** Same mehenga kaam baar-baar karna time aur paisa barbaad karta
hai. ML mein toh aur bhi — same text re-embed karna, same LLM call dobara (paisa!), same features
re-compute karna.

**Kab use karein:** Jab same mehenga computation/lookup same input ke saath repeat hota hai, aur
result jaldi nahi badalta. Faayda repeat-rate ke saath badhता hai (zyada repeat = zyada faayda).

**Kab NAHI:** (1) Agar har request *unique* hai (koi repeat nahi) — cache khali faayda nahi dega,
sirf memory khaayega. (2) Agar data bahut tezi se badalta hai — cache stale (purana/galat) data
dega. (3) Choti/sasti computation ke liye — cache ka overhead faayde se zyada.

**Kaise (ML examples):** Embedding cache (text→vector, content-hash key — re-ingest pe paisa
bache, 9.12); LLM response cache (same prompt→same answer, bill kam); feature cache (precomputed
user features).

**Pros & cons:** ✅ bada speed + cost win on repeated work. ❌ **invalidation** mushkil (data badle
toh cache galat — TTL ya content-hash key use karo); memory cost; cache-miss pe full price.

> **Ek line:** Cache tab jab kaam *mehenga* + *repeat* + *slowly-changing* ho. All-unique ya
> fast-changing data pe cache mat lagao — woh ulta nuksaan. "Stale data chalega?" — yeh sawaal
> pehle poocho.

---

<a id="53"></a>
## 5.3 — Databases: SQL vs NoSQL

**Kya hai:** Data store karne ki jagah. **SQL/relational** (Postgres, MySQL) = structured tables,
fixed schema, powerful queries + joins + transactions. **NoSQL** = non-relational, specific shapes
ke liye: **key-value** (Redis/DynamoDB — fast lookup), **document** (MongoDB — flexible JSON),
**wide-column** (Cassandra — huge writes).

**Problem kya solve karta hai:** Alag data aur alag access-pattern ko alag store chahiye. Sab kuch
ek store mein thosna (jaise 100M embeddings Postgres mein daal ke scan karna) = terrible
performance. Sahi store common query ko fast banata hai.

**Kab kaunsa (chooser):**
- **SQL** — structured data, joins chahiye, transactions/consistency zaroori (labels, user
  records, experiment metadata). Default for "real" relational data.
- **Key-value** — single key se fast lookup at scale (feature cache, sessions).
- **Document** — flexible/evolving schema, self-contained records (raw event JSON, configs).
- **Wide-column** — massive write throughput, time-ordered (logs, telemetry).

**Kab NAHI:** SQL ko 100M-vector similarity search ke liye mat use karo (vector DB chahiye, 5.7).
NoSQL ko mat use karo jab complex joins/transactions chahiye (SQL behtar). Key-value ko mat use
karo jab tumhe range/complex queries chahiye.

**Kaise (ML example):** Ek RAG system aksar *kai* DB use karta hai — Postgres (doc metadata,
permissions), vector DB (embeddings, 5.7), Redis (LLM/embedding cache), S3 (raw docs). Har store
apna best kaam karta hai.

**Pros & cons:** ✅ SQL — consistency, joins, mature; NoSQL — scales/flexes for its shape. ❌ SQL —
horizontal scaling mushkil, schema chahiye; NoSQL — weaker consistency, limited joins, access-
pattern ke around model karna padta hai.

> **Ek line:** Store ko *us query ke hisaab se* chuno jo sabse zyada chalti hai — fashion se nahi.
> Exact-key lookup → key-value; joins/transactions → SQL; similarity search → vector DB.

---

<a id="54"></a>
## 5.4 — Message queue / streaming (Kafka, SQS, RabbitMQ)

**Kya hai:** Producer (kaam/data banane wala) aur consumer (process karne wala) ke *beech* ek
buffer, jo messages tab tak rakhता hai jab tak consumer ready na ho. **Queue** (SQS/RabbitMQ) =
point-to-point, har message ek baar. **Streaming log** (Kafka) = messages retained + *replayable*
by multiple readers.

**Problem kya solve karta hai:** Producer aur consumer alag speed pe chalte hain aur tightly-jude
nahi hone chahiye. Agar producer seedha consumer ko de aur consumer slow/down ho → kaam loss ya
producer block. Queue **decouple** karta hai — producer drop karke aage badhता hai, consumer apni
speed pe pull karta hai, consumer crash ho toh messages wait karte hain.

**Kab use karein:** Producer/consumer alag speed; kaam ko many workers mein baatna; pipeline stages
jodna; fire-and-forget background jobs; traffic spike absorb karna (backpressure).

**Kab NAHI:** Simple synchronous request-response ke liye (jahan caller turant jawab chahta hai —
queue sirf latency badhayega). Choti scale pe jahان decoupling ki zaroorat nahi (over-engineering).
Jab strict ordering/exactly-once critical ho aur aap us complexity ke liye ready nahi.

**Kaise (ML example):** API "embed this document" jobs queue pe daalती hai; worker-pool pull karke
embed karta hai, API se independent scale karta hai. Ya: events → Kafka → consumer feature banata
hai (streaming, 5.9).

**Pros & cons:** ✅ decoupling, buffering, independent scaling, resilience (consumer crash pe kaam
bacha rehta hai). ❌ ek aur system; **at-least-once delivery** = duplicates aa sakte → consumer
**idempotent** hona chahiye (Area 7.4); ordering/exactly-once mushkil; latency badhती hai.

> **Ek line:** Queue tab jab producer aur consumer ki speed alag ho ya unhe alag karna ho. Simple
> request→response ke liye queue mat lagao. Aur consumer ko hamesha idempotent banao (duplicates
> aayenge).

---

<a id="55"></a>
## 5.5 — Object storage (S3) & data lake

**Kya hai:** **Object storage** (S3, GCS) = sasti, unlimited storage for files of any type (JSON,
images, Parquet, model artifacts). **Data lake** = object storage ko raw-data ke landing zone ki
tarah use karna (schema-on-read — structure tab lagao jab padho).

**Problem kya solve karta hai:** Aapke paas bahut saara raw/bada/unstructured data hai (logs,
images, events) jo sasti jagah store karna hai, aur abhi pata nahi future mein kaise use karoge.
Warehouse (5.6) ismein mehenga padega; object storage sasta aur kuch bhi rakh leta hai.

**Kab use karein:** Raw data landing (events, logs, training images), model artifacts, backups,
kuch bhi bada/unstructured. ELT ka "load raw" step (Area B1). Jab aap data ko abhi store karke
baad mein transform karna chahte ho.

**Kab NAHI:** Fast queries ke liye nahi (object storage slow hai random access pe — warehouse ya
DB chahiye). Low-latency serving ke liye nahi. Transactional data ke liye nahi (SQL).

**Kaise (ML example):** Raw events aur training images S3 mein land karte hain (lake). Ek ELT job
inka subset clean karke warehouse mein daalता hai (tabular training ke liye), jabki vision model
images ko seedha S3 se padhता hai.

**Pros & cons:** ✅ super sasta, unlimited, kuch bhi rakh leta hai, future-proof (raw rakha hai toh
baad mein re-transform kar sakte). ❌ slow queries; governance ke bina "data swamp" ban jaata hai
(bekaar files ka dher); low-latency serving ke layak nahi.

> **Ek line:** Object storage/lake = sasta "sab kuch raw daal do" landing zone. Fast query ya
> serving ke liye yahan se warehouse/DB/cache mein le jao. Lake ko swamp banne se bachao
> (organise + govern).

---

<a id="56"></a>
## 5.6 — Data warehouse (BigQuery / Snowflake / Redshift)

**Kya hai:** Ek structured store jo *clean, tabular* data pe fast analytical queries (SQL) ke liye
optimised hai. Schema-on-write (structure load pe enforce hota hai). Massive compute for big SQL.

**Problem kya solve karta hai:** Lake (5.5) mein raw data sasta padा hai par query karna slow/messy
hai. Analysts aur training jobs ko *clean, modelled* tables pe *fast* SQL chahiye. Warehouse wahi
deta hai — terabytes pe seconds mein aggregation/joins.

**Kab use karein:** Clean curated tables (features, labels, metrics) jinpe analysts aur ML pipelines
SQL chalाte hain. ELT ka "transform" step (dbt warehouse mein chalta hai). BI dashboards.

**Kab NAHI:** Raw/unstructured data (images, blobs) ke liye nahi (lake sasta). Low-latency
*serving* (per-request lookup) ke liye nahi (key-value/cache chahiye — warehouse analytical hai,
transactional nahi). Bahut chhote data ke liye over-kill (ek Postgres kaafi).

**Kaise (ML example):** Raw events lake mein → ELT (dbt) clean feature/label tables banata hai
warehouse mein → training pipeline (Ch 6) warehouse se features padhता hai. Analysts wahi tables
pe dashboards banate hain.

**Pros & cons:** ✅ fast SQL on huge data, clean/governed, mature ecosystem. ❌ mehenga (compute +
storage), tabular-only (blobs nahi), serving-latency ke layak nahi. Lake + warehouse aksar saath
use hote hain (raw + curated).

> **Ek line:** Warehouse = clean tabular data pe fast SQL (analytics + training data prep). Raw
> blobs → lake. Per-request serving → cache/key-value. Warehouse analytical hai, real-time serving
> nahi.

---

<a id="57"></a>
## 5.7 — Vector database (FAISS, Pinecone, Weaviate, pgvector)

**Kya hai:** Ek store jo embeddings (vectors) rakhता hai aur query-vector ke sabse *similar*
vectors dhoond deta hai — nearest-neighbour search, usually cosine similarity, ANN
(Approximate Nearest Neighbour) index se fast.

**Problem kya solve karta hai:** Meaning se search karna (keyword se nahi) — "money back" se
"refund" wala chunk milna chahiye, bhale shabd alag hon. Aur yeh millions of vectors pe
milliseconds mein. Keyword search meaning miss karta hai; brute-force scan millions pe slow.
Vector DB + ANN dono solve karta hai.

**Kab use karein:** RAG retrieval (D-section), semantic search, "similar items/docs" by embedding,
recommendation candidate-generation by embedding similarity.

**Kab NAHI:** Exact-key lookup ke liye nahi (key-value/dict O(1) — vector DB overkill, 11.1).
Chhote data (kuch hazaar vectors) ke liye ek FAISS file/`pgvector` kaafi, managed cloud vector DB
zaroori nahi. Jab exact-term match chahiye (codes, names) — pure vector miss karta hai, hybrid
chahiye (D6).

**Kaise (ML example):** Documents chunk + embed karke vector DB mein metadata ke saath store
(ingestion). Query aaye → same model se embed → top-k similar chunks → LLM ko bhejo. Metadata
filtering se permissions/freshness handle.

**Pros & cons:** ✅ fast semantic retrieval at scale, metadata filtering. ❌ ANN *approximate* hai
(thodी accuracy trade speed ke liye); query aur docs *same* embedding model use karein warna tutega;
exact terms miss (hybrid chahiye); top-k *similar* ≠ *relevant* (re-ranking chahiye, D6).

> **Ek line:** Vector DB = meaning-based (semantic) search at scale. Exact-key lookup ke liye
> key-value, exact-term match ke liye keyword/hybrid. Query aur docs same embedding model — yeh
> rule mat todo.

---

<a id="58"></a>
## 5.8 — Orchestrator (Airflow / Dagster / Prefect)

**Kya hai:** Ek tool jo multi-step pipelines ko schedule aur run karta hai, sahi order mein,
dependencies ke saath — steps ko ek **DAG** (Directed Acyclic Graph) ki tarah model karke. Retry,
alert, monitoring, re-run sab deta hai.

**Problem kya solve karta hai:** Real pipeline = kai steps with dependencies (extract → transform
→ train → deploy), aur steps fail hote hain. Cron + shell scripts ka dher yeh nahi keh sakta "B
tabhi chalao jab A pass ho, C ko 3 baar retry karo, D fail ho toh alert, aur E se re-run karne
do." Orchestrator yeh sab karta hai.

**Kab use karein:** Koi bhi scheduled multi-step pipeline with dependencies — yaani zyadatar
data/ML pipelines. Scheduling + dependency-order + retries + monitoring + re-run chahiye toh.

**Kab NAHI:** Low-latency *real-time/streaming* ke liye nahi (orchestrator batch/scheduled ke liye
bana hai — streaming ke liye Flink, 5.9). Ek hi simple step ke liye over-kill (cron kaafi). Request-
time serving ke liye nahi.

**Kaise (ML example):** Airflow DAG: `extract_events → validate → build_features → train_model →
evaluate → (agar baseline se behtar) deploy`. Har task apni dependency declare karता hai;
orchestrator topological order mein chalata hai (11.17), transient fail pe retry+backoff (5.9), aur
dashboard pe dikhता hai kya chala/fail. 3 baje train fail ho toh retry, aur aap us step se re-run
kar sakte ho bina extract dohrाye.

**Pros & cons:** ✅ reliability (retry, alert), visibility (DAG view), dependency management,
reproducibility. ❌ ek aur system seekhna/chalाना; DAGs bade ho ke tangle ban sakte; *batch* ke liye
hai, *streaming* ke liye nahi.

> **Ek line:** Multi-step scheduled pipeline = orchestrator (Airflow). Dependency/retry/re-run
> khud script mat karo. Par real-time streaming ke liye yeh galat tool hai (woh 5.9).

---

<a id="59"></a>
## 5.9 — Stream processor (Flink / Spark Streaming / Kafka Streams)

**Kya hai:** Ek tool jo events ko *continuously*, aate hi process karta hai (batch ki tarah
schedule pe nahi). Aksar Kafka (5.4) se events leta hai aur near-real-time mein transform/aggregate
karta hai.

**Problem kya solve karta hai:** Kuch decisions nightly batch ka wait nahi kar sakte. Fraud model
ko "last 5 minutes ki transactions" chahiye, ya recommender ko abhi-abhi dekhी cheez pe react
karna hai — din mein ek baar wala pipeline bekaar hai (data tab tak basi).

**Kab use karein:** Jab seconds ki freshness *sach mein* business requirement ho — real-time fraud,
live personalisation, up-to-the-second monitoring/alerting, instant feature updates.

**Kab NAHI:** Jab minutes/hours ki lag chalती hai (batch use karo — *bahut* simpler). Yeh sabse
common over-engineering hai — log streaming bana lete hain jahan batch kaafi tha. Streaming complex
hai (late events, windowing, state) — bina zaroorat ke mat lo.

**Kaise (ML example):** Transaction events → Kafka → Flink job jo "per card, last 5 min ka
count/sum" maintain karta hai (windowed aggregation, sliding window 11.3 jaisा par event-stream
pe) → yeh feature low-latency store mein likhता hai → fraud model scoring pe padhता hai. Features
hamesha seconds-fresh.

**Pros & cons:** ✅ real-time freshness, turant react, load smooth. ❌ genuinely *mushkil* — late/
out-of-order events, windowing, exactly-once vs at-least-once, state management; debug aur reprocess
batch se kathin.

> **Ek line:** Stream processor tab jab sub-minute freshness zaroori ho. Warna batch — woh simpler,
> sasta, easy-to-reprocess. "Kya sach mein seconds chahiye?" — yeh poocho, kyunki streaming ka cost
> zyada hai.

---

<a id="510"></a>
## 5.10 — Distributed compute (Spark / Dask / Ray)

**Kya hai:** Ek framework jo computation ko *many machines* (a cluster) mein baant deta hai, jab ek
machine ke cores/RAM kaafi nahi. Data ko partitions mein baant ke parallel process karta hai, with
fault-tolerance.

**Problem kya solve karta hai:** Multiprocessing (ek machine ke cores) ki ek limit hai — woh us
machine ki RAM/CPU tak. Jab data ya compute ek machine se bada ho (500GB dataset, ya days-long
job), toh cluster chahiye. Distributed framework yeh handle karta hai (data partition, scheduling,
node-failure recovery).

**Kab use karein:** Data ek machine ki RAM mein nahi aata *aur* easily stream/chunk nahi kar sakte;
ya compute ko ek machine ke cores se zyada chahiye (terabytes ka ETL, distributed featurisation).

**Kab NAHI (important):** Jab data ek machine pe fit hota hai (pandas + multiprocessing kaafi —
Spark *slower* hoga cluster/JVM overhead ki wajah se!). Yeh badi over-engineering galti hai — 2GB
file pe Spark cluster lagana. Pehle single-machine options (streaming/chunking, multiprocessing)
khatam karo.

**Kaise (ML example):** 500GB events ka feature engineering — ek machine pe impossible. Dask/Spark
data ko partitions mein baant ke cluster pe process karता hai (lazy + out-of-core). Par 5GB file ke
liye? — pandas + chunking kaafi, Spark nuksaan.

**Pros & cons:** ✅ single-machine ceiling todta hai, out-of-core, fault-tolerant. ❌ cluster/JVM/
network overhead → chhote data pe *slower* than single machine; debug mushkil (distributed stack
traces); paisa (cluster). Sabse chhota fitting tool chuno (kabhi DuckDB/Polars ek machine pe kaafi).

> **Ek line:** Distributed compute *sirf* tab jab data/compute ek machine se bada ho. Ek machine pe
> fit? → pandas/multiprocessing — Spark mat lagao (woh ulta dheema hoga). Distribution free nahi
> hai.

---

<a id="511"></a>
## 5.11 — Feature store (Feast / Tecton)

**Kya hai:** Ek central system jo features ko compute, store, aur serve karta hai — *consistently*
for both **training** and **serving**. Offline store (warehouse — historical, training ke liye) +
online store (key-value — current values, serving ke liye).

**Problem kya solve karta hai:** Sabse bada production-ML bug — **train/serve skew** (Area 8.16).
Aap training notebook mein feature ek tareeke se compute karte ho, serving code mein doosre — model
ko serving pe alag input milता hai aur woh chup-chाp underperform karta hai. Feature store feature
ko *ek baar* define karता hai, dono paths use karte hain — skew impossible. Saath hi feature reuse
aur point-in-time correctness (no leakage, 8.1).

**Kab use karein:** Jab features kai models/teams mein share hote hain, ya real-time compute hote
hain, ya train/serve skew ka risk hai (lagभग hamesha at scale).

**Kab NAHI:** Chhote single-model project mein full feature-store product over-kill — bas ek *shared
function* jo dono (train aur serve) use karein, wahi principle deta hai lightweight. Product tab jab
scale/multiple-models ho.

**Kaise (ML example):** "avg order value 30d" feature *ek baar* define; offline store ise
historically materialise karta hai (training), online store current value serve karता hai
(inference) — same definition, no skew. Point-in-time joins ensure training row sirf wahi feature
values use kare jo *us waqt* known the (no future leakage).

**Pros & cons:** ✅ train/serve skew khatam, feature reuse, point-in-time correctness, real-time
features. ❌ kaafi infrastructure; single small model ke liye over-kill (shared function use karo).

> **Ek line:** Feature store ka *principle* (feature ek baar compute karo, train aur serve dono use
> karein — no skew) hamesha zaroori; *product* (Feast/Tecton) scale aur multiple models pe. Chhote
> project mein shared function kaafi.

---

<a id="512"></a>
## 5.12 — Containers (Docker) & Kubernetes

**Kya hai:** **Docker container** = aapka code + saari dependencies + environment ek portable
package mein, taaki "mere machine pe chalta hai" problem khatam ho — har jagah same chalega.
**Kubernetes (K8s)** = many containers ko many machines pe chalाne/scale/heal karne wala
orchestrator (auto-restart, auto-scale, load-balance).

**Problem kya solve karta hai:** Docker — environment mismatch (different library versions train vs
prod, Area 7.15) khatam karता hai; reproducible deployment. K8s — jab aapko bahut saare service
instances chalाne, auto-scale, aur fail hone pe auto-restart chahiye, manually karna impossible.

**Kab use karein:** Docker — lagभग hamesha (reproducible packaging; ML mein especially, GPU/CUDA
deps). K8s — jab aapke paas multiple services chalाne hain at scale, auto-scaling/self-healing
chahiye, ya already K8s ecosystem mein ho.

**Kab NAHI:** K8s ek *chhote* app/prototype ke liye massive over-engineering hai — ek container ek
server pe (ya a managed service like Cloud Run / a serverless function) kaafi. K8s ki complexity
(yaml, networking, operators) bina real scale ke sirf dard hai. Yeh sabse classic over-engineering
trap hai (Ch 8).

**Kaise (ML example):** Model-serving code ko Docker image mein pack karo (model + python + CUDA
deps) — har environment mein same. Phir K8s pe deploy: 10 replicas, auto-scale on load, ek crash ho
toh auto-restart, rolling/canary deploys (Ch 11).

**Pros & cons:** ✅ Docker — reproducibility, portability (huge win, lagभग always worth it). K8s —
auto-scale, self-heal, rolling deploys at scale. ❌ K8s — bada learning curve aur operational
complexity; chhote scale pe over-kill (managed serverless aksar behtar).

> **Ek line:** Docker — haan, lagभग hamesha (reproducible packaging). Kubernetes — *sirf* jab real
> scale/multi-service ho; chhote app pe ek container + managed service kaafi, K8s sirf dard. Yeh
> over-engineering #1 hai.

[↑ Back to top](#contents)