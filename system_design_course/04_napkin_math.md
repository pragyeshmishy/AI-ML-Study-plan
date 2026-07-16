<a id="contents"></a>
# Chapter 4 — Napkin Math (Capacity Estimation)

"Napkin math" = woh mota-mota hisaab jo aap ek napkin (ya whiteboard ke corner) pe karte ho —
QPS, storage, memory, cost. Exact nahi, par *order of magnitude* (100 ya 100 million?) bata deta
hai. Yeh skill aksar sabse kamzor hoti hai par sabse zaroori — kyunki yahi numbers decide karte
hain ki ek machine chahiye ya ek cluster.

---

## Contents

- [4.1 — Napkin math kyun? (numbers se architecture decide hota hai)](#41)
- [4.2 — Reference numbers (yaad rakhne layak)](#42)
- [4.3 — QPS nikalna (requests per second)](#43)
- [4.4 — Storage estimate karna](#44)
- [4.5 — Memory estimate (kya RAM mein aayega?)](#45)
- [4.6 — ML-specific: GPU memory, tokens, embeddings](#46)
- [4.7 — Cost estimate (LLM/GPU ka paisa)](#47)

---

<a id="41"></a>
## 4.1 — Napkin math kyun? (numbers se architecture decide hota hai)

**Kya seekhna hai:** Design se *pehle* mota-mota hisaab lagao. Yeh numbers — QPS, storage,
memory — aapko batate hain ki system *kis tier* mein hai, aur poora architecture isi pe depend
karta hai.

**Problem kya solve karta hai:** Bina numbers ke aap guess kar rahe ho. "Ek machine kaafi hai?"
— pata nahi. Hisaab lagao: agar data 600GB hai, toh turant pata — ek machine ki RAM mein nahi
aayega, sharding chahiye. Numbers guess ko *decision* mein badal dete hain.

**Numbers kya decide karte hain (examples):**
- **Storage 10GB?** → ek machine, simple. **10TB?** → distributed storage / warehouse.
- **QPS 100?** → ek server. **100,000?** → load balancer + many replicas + caching.
- **600GB embeddings?** → ek RAM mein nahi → sharded vector DB.
- **1M LLM calls/day at ₹2 each?** → ₹20 lakh/day → caching urgently chahiye (Ch 12).

**Example (numbers ne architecture badla):**
- "Real-time recommendations chahiye, 10M items." Napkin: har request pe 10M items score karna =
  impossible (10M × QPS). Yeh number turant batata hai — **two-stage** design chahiye (retrieval
  se 10M → 1000, phir rank). Bina hisaab ke aap shayad seedha "sabko score karo" likh dete.

**Pros & cons:** Faayda — sahi tier ka system, har decision justified, surprises se bach. Nuksaan
— exact nahi (isliye "napkin"), par order-of-magnitude kaafi hai. Galat number se zyada bura hai
*koi* number na hona.

> **Ek line:** Aapko exact answer nahi chahiye — bas yeh jaanna hai ki number *chhota* hai ya
> *bahut bada*. "600GB" sunke turant "ek machine mein nahi" — bas yahi insight design badal deta
> hai.

---

<a id="42"></a>
## 4.2 — Reference numbers (yaad rakhne layak)

**Kya seekhna hai:** Kuch basic numbers yaad rakho — inse aap turant hisaab laga sakte ho bina
calculator ke. Yeh aapke "mental constants" hain.

**Time / scale constants:**
- **1 din ≈ 86,400 seconds** (round off to **~100,000** for easy mental math — "ek lakh seconds
  in a day").
- **1 month ≈ 2.5 million seconds.**
- **Powers:** 1 thousand = 10³ (KB), 1 million = 10⁶ (MB), 1 billion = 10⁹ (GB), 1 trillion =
  10¹² (TB).

**Data size constants (rough):**
- **1 character ≈ 1 byte.** A short text field ≈ 100 bytes. A row/record ≈ 1 KB (rough default).
- **1 ASCII page of text ≈ 2-4 KB.**
- **1 embedding vector:** dimensions × 4 bytes (float32). *(1536-dim ≈ 6 KB.)*
- **1 image (compressed) ≈ 100KB-1MB; raw bigger.**

**Latency constants (rough, "kitna time lagta hai"):**
- **Memory (RAM) read:** ~100 nanoseconds (super fast).
- **SSD read:** ~100 microseconds. **Disk (HDD):** ~10 milliseconds.
- **Network within datacenter:** ~0.5 ms. **Across internet:** ~50-150 ms.
- **DB query (simple, indexed):** ~1-10 ms. **LLM call:** ~500ms-several seconds.

**Example (use karke):** "100 million documents embed karne hain, har vector 1536-dim." Storage:
100M × (1536 × 4 bytes) = 100M × ~6KB = **~600 GB**. Turant pata: ek machine ki RAM (say 64GB)
mein nahi aayega → sharded vector DB. Sirf yaad-kiye numbers se yeh nikal aaya.

**Pros & cons:** Faayda — yeh constants yaad ho toh aap seconds mein estimate kar lete ho, bina
ruke. Nuksaan — yaad karne padte hain (par bahut kam hain — ek din mein seekh jaoge), aur yeh
rough hain (exact nahi, par kaafi).

> **Ek line:** Bas yeh yaad rakho — *din mein ~1 lakh second, record ~1KB, embedding ~dims×4
> bytes, RAM fast/disk slow/LLM call dheema.* Inse 90% napkin math ho jaata hai.

---

<a id="43"></a>
## 4.3 — QPS nikalna (requests per second)

**Kya seekhna hai:** QPS = Queries Per Second = system pe har second kitni requests aati hain.
Yeh decide karta hai ki ek server kaafi hai ya kai chahiye (load balancer ke saath).

**Formula (simple):**
- **Average QPS** = total requests per day ÷ seconds per day (~86,400, ya ~100,000 for easy math).
- **Peak QPS** = average × **2 to 3** (kyunki traffic even nahi hota — din mein peak hours hote
  hain). Design hamesha *peak* ke liye karo, average ke liye nahi.

**Step-by-step example (recsys):**
- "100 million users, har user din mein average 10 baar feed kholता hai."
- Total requests/day = 100M × 10 = **1 billion requests/day**.
- Average QPS = 1,000,000,000 ÷ 100,000 = **~10,000 QPS**.
- Peak QPS = 10,000 × 3 = **~30,000 QPS**.
- *Insight:* ek server ~1000-5000 QPS handle karta hai (rough), toh 30,000 QPS ke liye ~10+
  replicas + load balancer chahiye (Ch 5). Number ne architecture bata diya.

**Read vs write QPS (important):** aksar reads >> writes. (*Twitter: log padhte zyada hain, tweet
karte kam.*) Inhe alag estimate karo — kyunki reads ko cache/replicas se scale karte hain, writes
ko alag (sharding) se.

**Pros & cons:** Faayda — turant pata ek machine ka kaam hai ya cluster ka; scaling plan clear.
Nuksaan — assumptions pe depend (users × frequency) — par woh aap requirements (Ch 2.1) se poochte
ho, toh theek.

> **Ek line:** QPS = (users × requests-per-user-per-day) ÷ ~1 lakh, phir peak ke liye ×3. Yeh
> ek number batata hai ek server chahiye ya pachaas.

---

<a id="44"></a>
## 4.4 — Storage estimate karna

**Kya seekhna hai:** Total data kitna store hoga — yeh decide karta hai ki ek disk/DB kaafi hai
ya distributed storage (lake/warehouse, sharding) chahiye.

**Formula:** Total storage = number of items × size per item. (Aur growth ke liye time se multiply
— "per day × 365 = per year".)

**Step-by-step example (events):**
- "Har user din mein 100 events generate karta hai, 100M users, har event ~500 bytes."
- Per day = 100M × 100 × 500 bytes = 100M × 50KB = **5 TB/day**.
- Per year = 5TB × 365 = **~1.8 PB/year**.
- *Insight:* yeh ek machine pe impossible → data lake (S3) mein raw store, warehouse mein curated
  (Ch 6). Aur retention policy chahiye (saara forever nahi rakh sakte — Ch 12 cost).

**ML-specific example (vector store):**
- "100M document chunks, har embedding 1536-dim float32."
- Vector size = 1536 × 4 bytes = ~6 KB. Total = 100M × 6KB = **~600 GB** (sirf vectors; metadata
  alag).
- *Insight:* 600GB ek typical RAM (64-256GB) mein nahi → sharded vector DB across machines.

**Pros & cons:** Faayda — turant pata storage tier (one disk vs lake vs sharded); retention/cost
ki zaroorat bhi dikhती hai. Nuksaan — size-per-item ka estimate galat ho toh poora hisaab off,
par order-of-magnitude usually theek rehta hai.

> **Ek line:** Storage = items × size-each (× time for growth). Yeh batata hai ek disk pe aayega,
> ya lake/warehouse/sharding chahiye. PB suna? = definitely distributed.

---

<a id="45"></a>
## 4.5 — Memory estimate (kya RAM mein aayega?)

**Kya seekhna hai:** Memory (RAM) estimate karna = kya aapka cache/index/working-set ek machine
ki RAM mein aa jayega? Agar nahi, toh sharding ya disk-based approach chahiye.

**Problem kya solve karta hai:** Bahut systems "RAM mein rakho for speed" pe depend karte hain
(cache, vector index, in-memory DB). Par RAM limited hai (ek machine pe ~64-512GB typical). Agar
aapka data RAM se bada hai, toh design badalna padega. Yeh check critical hai.

**Formula:** Working set size = items-to-keep-in-memory × size-each. Compare with machine RAM.

**Step-by-step example (cache):**
- "Top 1M users ki profiles cache karni hain, har profile ~2KB."
- Cache size = 1M × 2KB = **2 GB**. → easily ek machine ki RAM mein (Redis pe). Theek.
- Ab: "saare 100M users cache karne hain" → 100M × 2KB = **200 GB**. → ek typical machine mein
  nahi → distributed cache (Redis cluster) ya sirf hot users cache karo (sab nahi).

**ML example (vector index in RAM):**
- FAISS index ko RAM mein rakhna fast hai. 600GB vectors (4.4) ek machine ki RAM mein nahi → ya
  sharding (kai machines), ya disk-based ANN index (thodा slow par fits), ya compression
  (quantization — vectors chhote karo).

**Pros & cons:** Faayda — aap pehle hi jaan lete ho ki "RAM mein rakho" plan chalega ya nahi, aur
accordingly shard/compress/disk decide karte ho. Nuksaan — koi nahi; yeh check na karna = runtime
pe OOM (out of memory) crash.

> **Ek line:** Jo bhi RAM mein rakhna chahte ho (cache/index), uska size nikalo aur machine RAM
> (~64-256GB) se compare karo. Bada hai? → shard karo, compress karo, ya sirf hot data rakho.

---

<a id="46"></a>
## 4.6 — ML-specific: GPU memory, tokens, embeddings

**Kya seekhna hai:** ML/LLM systems mein kuch special napkin-math hota hai — GPU memory fit hogi
ya nahi, kitne tokens, kitne embeddings. Yeh ML-specific constraints hain jo normal web systems
mein nahi aate.

**GPU memory (training/inference):**
- GPU ki memory (VRAM) limited hai — common: 16GB, 40GB, 80GB.
- Training mein VRAM = model weights + gradients + optimizer state + **activations** (activations
  aksar sabse bada, aur batch-size × sequence-length ke saath badhता hai).
- *Example:* "Model train karte waqt CUDA out of memory aa raha hai." Napkin: batch size 64 se
  16 karo → activations ~4x kam → fit ho jayega. Ya mixed precision (16-bit) → ~half memory.
  (Detail Area 9.3 mein.)

**Tokens (LLM context):**
- LLM tokens mein sochta hai (~4 characters = 1 token in English; ~¾ word). Context window (max
  tokens) shared between input + output.
- *Example:* "8192-token context. System prompt 500 tokens, output ke liye 1000 reserve. Bachे
  ~6700 tokens for retrieved chunks. Har chunk ~500 tokens → ~13 chunks fit honge." Yeh napkin
  RAG mein decide karta hai kitne chunks bhejna.

**Embeddings throughput:**
- *Example:* "1M texts embed karne hain. API 100 texts/batch, har call 300ms." 1M ÷ 100 = 10,000
  calls × 300ms = 3000s = ~50 min *if sequential*. Parallel 10x → ~5 min. Yeh batching +
  concurrency ki zaroorat batata hai (Area 5.14).

**Pros & cons:** Faayda — ML-specific bottlenecks (GPU OOM, token limits, embedding time) pehle hi
dikh jaate hain. Nuksaan — yeh estimates rougher hain (activation memory depends on architecture),
par order-of-magnitude phir bhi useful.

> **Ek line:** ML mein 3 cheez napkin pe check karo — *GPU memory* (batch × seq fit hoga?),
> *tokens* (context budget mein kitna aayega?), *embedding throughput* (kitna time/parallelism?).
> Yeh ML-specific limits design badal dete hain.

---

<a id="47"></a>
## 4.7 — Cost estimate (LLM/GPU ka paisa)

**Kya seekhna hai:** ML systems mein paisa tezi se udta hai — LLM calls, GPU hours, storage. Ek
mota cost estimate pehle hi laga lo, warna bill dekh ke heart attack aata hai. (Detail Ch 12.)

**Formula:** Cost = number of operations × cost per operation. (LLM: tokens × price-per-token.
GPU: hours × price-per-hour.)

**Step-by-step example (LLM cost):**
- "Chatbot, 100,000 queries/day, har query ~2000 input tokens + 500 output tokens."
- Maan lo LLM price: input $3/million tokens, output $15/million tokens.
- Per query = (2000 × $3/1M) + (500 × $15/1M) = $0.006 + $0.0075 = **~$0.013/query**.
- Per day = 100,000 × $0.013 = **~$1,300/day** = ~$40,000/month!
- *Insight:* yeh bahut zyada hai → **caching** urgently chahiye (same questions repeat hote hain,
  9.12), ya chhota/sasta model, ya kam tokens (chote prompts). Cost napkin ne turant bata diya ki
  caching optional nahi, zaroori hai.

**GPU cost example:**
- "Training job, 4 GPUs, 24 hours, GPU ~$2/hour." = 4 × 24 × $2 = **~$192/run**. Roz train karoge
  toh ~$6000/month. → kya itni baar train karna zaroori hai? (Ch 12).

**Pros & cons:** Faayda — cost surprise se bachte ho, aur caching/model-size/retrain-frequency
jaise decisions number ke saath justify karte ho. Nuksaan — prices badalte rehte hain (estimate
rough), par order-of-magnitude ("$40/month ya $40,000/month?") clear ho jaata hai.

> **Ek line:** ML mein hamesha *cost per operation × volume* nikalo (LLM: tokens×price, GPU:
> hours×rate). "$40,000/month" jaisा number turant batata hai ki caching/optimization optional
> nahi — zaroori hai. Paisa bhi ek design constraint hai.

[↑ Back to top](#contents)