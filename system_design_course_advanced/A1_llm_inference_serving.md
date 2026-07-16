<a id="contents"></a>
# A1 — LLM Inference Serving at Scale (Principal-level)

> **Sample doc** — yeh advanced layer ka level dikhane ke liye hai. Language plain (Hinglish),
> par topics aur decisions principal-grade. Har section mein: decision matrix, real numbers,
> "why X not Y" with the breaking point, **kam-se-kam 2 comprehensive worked examples** (named
> scenario + numbers + jo decision actually liya gaya), production failure modes, aur woh
> one-liner jo aap Google architecture review mein defend karoge.

Yeh chapter LLM ko production mein *serve* karne ka system design hai — woh layer jo aksar poore
LLM product ka **sabse bada cost aur sabse bada latency bottleneck** hota hai. Agar interviewer
poochे "you served LLMs in prod — walk me through the serving stack and why these choices", yeh
woh jawab hai.

---

## Contents

- [A1.1 — Pehle physics samjho: LLM inference memory-bound hai, compute-bound nahi](#a11)
- [A1.2 — Prefill vs decode: do bilkul alag workloads ek request mein](#a12)
- [A1.3 — KV cache: woh cheez jo sab kuch decide karti hai](#a13)
- [A1.4 — Continuous batching & PagedAttention (naive batching kyun 60% GPU waste karta hai)](#a14)
- [A1.5 — Serving framework decision: vLLM vs TGI vs Triton vs TensorRT-LLM](#a15)
- [A1.6 — Parallelism: tensor vs pipeline vs replica (kab kaunsa)](#a16)
- [A1.7 — Quantization & speculative decoding (latency/cost levers)](#a17)
- [A1.8 — Capacity & cost model (real numbers)](#a18)
- [A1.9 — Production failure modes & SLO engineering](#a19)
- [A1.10 — The architecture-review defense (one-liners)](#a110)

---

<a id="a11"></a>
## A1.1 — Pehle physics samjho: LLM inference memory-bound hai, compute-bound nahi

**Decision jo isse nikalti hai:** poora serving design — batching, hardware choice, cost — isi ek
fact pe khada hai. Jo engineer yeh nahi samajhta woh galat cheez optimize karta hai.

**Asli baat:** autoregressive decode (token-by-token generation) mein, har naya token generate
karne ke liye GPU ko **poore model ke weights HBM (GPU memory) se read** karne padte hain, par
arithmetic bahut kam hota hai (ek token ka matmul). Matlab GPU ka *compute* (FLOPs) idle baithा
rehta hai, aur **memory bandwidth** bottleneck ban jaata hai. Yeh "memory-bound" regime hai.

**Numbers se (yeh interview mein bolna):** ek A100 ke paas ~312 TFLOPS (bf16) compute hai par
~2 TB/s HBM bandwidth. Decode mein arithmetic intensity (FLOPs per byte read) bahut kam hoti hai —
toh aap us 312 TFLOPS ka shayad 5-10% use kar paate ho. GPU "busy" dikhता hai par actually weights
padhne ka wait kar raha hai. *Isiliye* ek request ko serve karna GPU ko barely use karta hai —
aur yahi se batching ki poori zaroorat aati hai (A1.4).

**Iska seedha consequence (design decisions):**
- **Throughput badhane ka tareeka = batching** (ek hi weight-read pe kai requests ka kaam), GPU
  upgrade nahi. Compute already idle hai.
- **Latency (per-token) bandwidth se bandhi hai** — bigger batch se per-token latency *barely*
  badhती hai (kyunki bottleneck memory read hai, compute nahi) — yeh counterintuitive insight hai
  jo batching ko itna powerful banata hai.
- **Prefill alag kahani hai** (A1.2) — woh compute-bound hai.

**Pros & cons (is mental model ka):** ✅ aap turant jaante ho ki batching #1 lever hai aur "bada
GPU lo" aksar galat jawab hai. ❌ —; yeh foundational physics hai, har LLM-serving decision isse
derive hoti hai.

**Examples (concrete, walked through):**

- **Example 1 — "Bada GPU lo" galti (A100 → H100 upgrade jo kuch nahi badla):** ek team ka chatbot
  slow tha (TPOT ~80ms). Manager ne kaha "A100 se H100 pe move karo, woh tez hai." Upgrade kiya —
  H100 ka compute ~3× hai (~990 TFLOPS bf16) par HBM bandwidth sirf ~1.6× (~3.35 TB/s). Single-
  request decode memory-bound hai, toh latency sirf ~1.5× behtar hui (bandwidth ratio ke barabar),
  3× nahi — par bill ~2.3× badh gaya. **Asli fix tha batching** (jo unhone kiya hi nahi): same A100
  pe continuous batching on karke unka throughput 6× badh gaya bina ek bhi naya GPU ke. Sabak:
  memory-bound workload pe compute-heavy GPU ka paisa waste — pehle batching, phir hardware.
- **Example 2 — Batch=1 vs batch=32 par per-token latency ka chamatkar:** ek 7B model, A100. Batch=1:
  decode ~120 tokens/sec (TPOT ~8ms). Batch=32: throughput ~2,600 tokens/sec (~80 tok/s/request),
  par per-request TPOT sirf ~12ms hua — 32× zyada kaam, latency mein sirf ~1.5× farak. **Kyun?**
  Batch=1 mein bhi GPU ko poore weights padhne padte the (memory-bound); batch=32 mein woh *same*
  weight-read 32 requests ke kaam aa gaya — compute bacha hua tha, use bhar diya. Yeh woh
  counterintuitive number hai jo batching ko #1 lever banata hai.

> **Architecture-review line:** *"Decode is memory-bandwidth bound, not compute bound — on an
> A100 we were at ~7% MFU per single request because we were bottlenecked reading 13GB of weights
> per token from HBM at 2TB/s. That's why our entire serving strategy is built around batching to
> amortise the weight read across requests, not around bigger GPUs."*

---

<a id="a12"></a>
## A1.2 — Prefill vs decode: do bilkul alag workloads ek request mein

**Decision jo isse nikalti hai:** aapke do alag latency metrics (TTFT vs TPOT), batching strategy,
aur kab "prefill-decode disaggregation" karna hai — sab isse.

**Asli baat:** ek LLM request ke do phase hote hain, aur woh hardware ko *bilkul ulta* use karte
hain:

- **Prefill** (prompt process karna): poore input prompt ke saare tokens ek saath process hote hain
  — ek bada parallel matmul. Yeh **compute-bound** hai (GPU ka FLOPs use hota hai). Output: pehla
  token + saare prompt tokens ka KV cache. Yeh **TTFT** (Time To First Token) decide karta hai.
- **Decode** (baaki tokens generate karna): ek-ek token, autoregressive, har step pe poore weights
  read. Yeh **memory-bound** hai (A1.1). Yeh **TPOT** (Time Per Output Token) decide karta hai.

**Numbers (kyun yeh matter karta):** maan lo prompt 2,000 tokens ka hai, output 200 tokens. Prefill
ek hi forward pass mein 2,000 tokens "kha" leta hai (parallel) — bhaari compute, par ek baar.
Decode 200 baar chalta hai, har baar ek token, har baar poore weights read. Toh:
- Lamba prompt + chhota output (RAG, summarization) = **prefill-dominated**, compute-heavy.
- Chhota prompt + lamba output (creative generation, agents) = **decode-dominated**, memory-heavy.

**Yeh design ko kaise badalta hai:**
- **Do alag SLOs:** "p95 TTFT < 500ms" aur "p95 TPOT < 50ms" — yeh alag cheezein hain, alag tune
  hoti hain. Ek single "latency" number LLM serving mein meaningless hai. (Yeh bolna interview mein
  instantly seniority dikhata hai.)
- **Prefill aur decode ek doosre ko block karte hain:** agar ek bada prefill (long prompt) GPU pe
  chal raha hai, toh baaki sabke decode steps ruk jaate hain → TPOT spike (yeh ek real production
  jitter source hai, A1.9). Iska fix: **chunked prefill** (lambe prompt ko tukdon mein process
  karo taaki decode steps beech mein chalte rahein) — vLLM mein default-ish.
- **Prefill-decode disaggregation (advanced):** prefill aur decode ko *alag GPU pools* pe chalao
  (alag machines). DistServe/Splitwise ne dikhaya yeh dono SLOs alag-alag hit karne deta hai bina
  ek doosre ko bigaade. **Kab karna:** jab traffic mixed ho (kuch long-prompt, kuch long-output)
  aur dono SLOs tight hon, aur aap tens-of-GPUs pe ho. **Kab NAHI:** chhote setup pe yeh
  operational complexity worth nahi — ek hi pool + chunked prefill theek.

**Pros & cons (disaggregation):** ✅ TTFT aur TPOT independently optimize, ek doosre ka jitter
nahi. ❌ KV cache ko prefill-node se decode-node bhejna padta hai (network transfer cost), zyada
machines, complex routing. Sirf scale pe justify.

**Examples (concrete, walked through):**

- **Example 1 — RAG chatbot (prefill-dominated) ka asli kharcha:** ek enterprise RAG bot har query
  pe 10 retrieved chunks + system prompt = ~6,000 prompt tokens bhejta hai, aur jawab average ~250
  tokens. Yahan prefill = 6,000 tokens ek pass mein (bhaari compute), decode = 250 steps. Naap ke
  dekho: poore request ke GPU-time ka ~55% prefill mein gaya, sirf ~45% decode mein — kyunki prompt
  output se 24× bada hai. Team ne galti se "decode tez karo" (speculative decoding) pe time lagaya,
  jabki bottleneck prefill tha. **Sahi fix:** prompt chhota karo (10 chunks → 4 reranked chunks,
  D-series), prefix-cache the fixed system prompt → TTFT 900ms se 350ms. Sabak: pehle naapो request
  prefill-heavy hai ya decode-heavy, phir optimize.
- **Example 2 — Long prompt ek aadmi ka, jitter sabko (the shared-GPU incident):** ek code-assistant
  pe zyadatar prompts chhote the (~500 tokens), par kabhi-kabhi koi pूra 30,000-token file paste kar
  deta. Jab woh bada prefill GPU pe chalta, us ~400ms ke dauraan baaki saare users ke decode steps
  ruk jaate → unka TPOT 40ms se spike hokar 250ms (sab ko hichki). Dashboard pe p99 TPOT spiky tha
  bina kisi traffic spike ke — pehchanna mushkil. **Fix:** chunked prefill on kiya (30k-token prefill
  ko 2k-token tukdon mein toda, beech-beech mein sabke decode steps chalte rahe) → p99 TPOT smooth.
  Sabak: ek request ka size sabki latency bigaad sakta hai jab tak prefill ko chunk na karo.

> **Architecture-review line:** *"We tracked TTFT and TPOT as separate SLOs because prefill is
> compute-bound and decode is memory-bound — different workloads. Long RAG prompts were
> prefill-dominated and spiking decode latency for everyone on the shared GPU, so we first turned
> on chunked prefill, and past ~40 GPUs moved to prefill/decode disaggregation to isolate them."*

---

<a id="a13"></a>
## A1.3 — KV cache: woh cheez jo sab kuch decide karti hai

**Decision jo isse nikalti hai:** aapka **max batch size**, **max context length**, kitni
concurrent requests ek GPU handle karega, aur OOM kab hoga — sab KV cache se. Yeh LLM serving ka
*sabse* important resource hai, model weights ke baad.

**Asli baat:** har generated token ke liye, model har layer pe ek **Key** aur **Value** vector
store karta hai taaki agle tokens unhe dobara compute na karein (warna har step pe poora prompt
re-process hota). Yeh stored K/V = **KV cache**. Yeh per-request, per-token, per-layer grows.

**KV cache size ka formula (yeh yaad rakho, interview mein derive karo):**

```
KV bytes = 2 (K and V)
         × num_layers
         × num_kv_heads × head_dim   (= hidden size, ya GQA mein chhota)
         × seq_len (prompt + generated)
         × batch_size
         × dtype_bytes (2 for fp16)
```

**Concrete number (Llama-2-13B, fp16):** ~40 layers, hidden ~5120, fp16. Per token per request
≈ 2 × 40 × 5120 × 2 bytes ≈ **800 KB/token**. Ek 4,000-token sequence = ~3.2 GB *sirf KV cache ka*,
ek request ke liye. Ek A100-40GB pe weights ~26GB le lete hain (fp16) → bachे ~14GB → matlab sirf
~4 aise requests fit honge. **Yahi aapka asli concurrency limit hai — GPU compute nahi, KV cache
memory.**

**Yeh har badi decision ko drive karta hai:**
- **Max batch size = (free VRAM after weights) / (KV per request)**. Throughput planning ka core.
- **Context length mehenga hai** — KV cache `seq_len` ke saath linear badhता hai. 32k-context
  support karna = 8× KV cache vs 4k. Isiliye long-context serving itna costly hai.
- **GQA/MQA (Grouped/Multi-Query Attention):** KV heads kam karke KV cache nateक्ती se chhota karta
  hai (Llama-2-70B GQA use karta hai) — isiliye modern models ise adopt karte hain, *purely
  serving cost* ke liye.
- **Naive KV cache 60-80% memory waste karta hai** (fragmentation + over-reservation) — yeh
  PagedAttention solve karta hai (A1.4).

**Pros & cons (KV cache as a concept):** ✅ decode ko O(1)-per-token banata hai (warna O(n²) total).
❌ memory hog — yeh aapki concurrency aur context-length ki asli deewar hai. Iske bina LLM serving
samajhना impossible.

**Examples (concrete, walked through):**

- **Example 1 — "32k context support karo" feature ka chhupa hua bill:** product team ne kaha
  "humein 32k-token context chahiye long documents ke liye." Engineer ne KV math ki: 13B model,
  ~800KB/token. 32k context = ~25GB KV *per request*. Ek A100-80GB pe weights ~26GB → bachे ~54GB →
  matlab sirf ~2 concurrent 32k-requests fit honge. Jabki 4k-context pe wahi GPU ~17 concurrent
  requests handle karta tha. Yaani 32k feature ne effective throughput ~8× gira diya — same hardware
  pe. **Decision:** 32k sirf ek premium tier ke liye (alag GPU pool), aam users 8k pe; warna cost
  phat jaata. Sabak: context-length ek throughput/cost decision hai, sirf ek feature flag nahi.
- **Example 2 — GQA model switch ne concurrency 4× kiya (Llama-2-13B → 70B-GQA wali family):** ek
  team multi-head-attention (MHA) wala 13B chala rahi thi, har layer ke saare KV heads store ho rahe
  the (~800KB/token). Woh ek GQA-based model pe gaye jisme 8 KV heads the 40 ke bajaye (Grouped-Query
  Attention) → KV cache per token ~5× chhota (~170KB/token). Result: same A100-40GB pe concurrent
  requests ~4 se badhkar ~18 ho gaye, throughput 4×+, bina koi GPU jode. Quality barabar (GQA ka
  whole point yahi hai). Sabak: modern models GQA/MQA *serving cost* ke liye adopt karte hain — yeh
  architecture choice directly aapka GPU bill decide karti hai.

> **Architecture-review line:** *"Our concurrency ceiling wasn't compute, it was KV cache. On a
> 40GB A100, 13B weights left ~14GB, and at ~800KB/token a 4K-context request needs ~3GB of KV — so
> ~4 concurrent requests. We moved to GQA models and PagedAttention to push effective concurrency
> 3-4x without adding GPUs."*

---

<a id="a14"></a>
## A1.4 — Continuous batching & PagedAttention (naive batching kyun GPU waste karta hai)

**Decision jo isse nikalti hai:** yeh *the* reason hai ki aap vLLM/TGI use karte ho na ki khud ka
Flask + `model.generate()`. Yeh samajh ke aap 5-20× throughput ka difference defend kar sakte ho.

**Problem 1 — Static batching ka waste:** maan lo aap 8 requests ek batch mein daalte ho. Request
A 20 tokens generate karta hai, B 500 tokens. Static batching mein poora batch tab tak GPU pakde
rehta hai jab tak *sabse lamba* (B) khatam na ho. A apne 20 tokens ke baad 480 steps tak idle slot
ghере rehta hai. Real traffic mein output-lengths bahut alag hote hain → **GPU 50-70% idle**.

**Solution — Continuous (in-flight) batching:** batch ko har decode step pe *dynamically* update
karo. Jaise hi A khatam hua, uska slot turant ek nayी waiting request ko de do — poore batch ka
wait nahi. GPU hamesha bhara rehta hai. Yeh single change aksar **2-4× throughput** deta hai bina
hardware add kiye. (vLLM, TGI, TensorRT-LLM sab yeh karte hain; tumhara naive loop nahi karta.)

**Problem 2 — KV cache memory fragmentation:** naive serving har request ke liye max-context-length
ka contiguous KV cache block *pehle se reserve* karta hai ("agar 2048 tokens bane toh?"). Zyadatar
requests itne tokens banाते nahi → reserved-but-unused memory = waste. Plus contiguous blocks =
fragmentation. Result: 60-80% KV memory waste.

**Solution — PagedAttention (vLLM ka core idea):** KV cache ko OS virtual-memory ki tarah **non-
contiguous fixed-size pages** mein todो. Request ko tokens banते waqt page-by-page allocate karo
(pehle se nahi). Fayde: (1) ~96%+ memory utilisation (waste ~4%), (2) pages **share** ho sakte hain
— ek hi system-prompt ya beam-search ke common prefix ka KV cache copies ke beech share (copy-on-
write). Iska seedha matlab: **same GPU pe 2-4× zyada concurrent requests** = directly cost down.

**Kaise dikhता hai end-to-end:** continuous batching (GPU idle nahi) + PagedAttention (memory waste
nahi) milके vLLM ko naive HF-pipeline serving se **up to ~24× throughput** (vLLM paper claim,
real-world typically 5-15×) deते hain. *Yeh* woh number hai jo "humne vLLM kyun chuna" justify
karता hai.

**Pros & cons:** ✅ massive throughput/cost win, longer effective context, prefix-sharing.
❌ implementation complex (isliye library use karte ho, khud nahi likhte); prefix-caching ke memory
accounting ko monitor karna padता hai (A1.9).

**Examples (concrete, walked through):**

- **Example 1 — Flask + `model.generate()` se vLLM (8 workers → 1 replica):** ek startup ka pehla
  LLM service Flask tha, har request `model.generate()` ko akela call karta (effectively batch=1),
  8 GPU workers behind a load balancer, ~40 req/s peak handle kar paата tha aur GPU utilisation
  dashboards pe sirf ~25% dikhता. Unhone vLLM pe switch kiya (continuous batching + PagedAttention):
  ek hi A100 replica ~120 req/s handle karne laga, GPU utilisation ~70%. 8 workers ka kaam ~1.5
  replicas mein — GPU bill ~80% kam. Koi model change nahi, sirf serving layer. Sabak: agar aap
  `generate()` ko per-request call kar rahe ho, aap 5-10× paisa jala rahe ho.
- **Example 2 — Static batch ka "sabse lamba ke wait" ka waste, numbers mein:** ek summarization
  service static batching use karti thi, batch=16. Ek batch mein output lengths: 14 requests ~30
  tokens (chhote summaries), 2 requests ~600 tokens (lambe docs). Static mein poora batch 600 steps
  tak GPU pakdे raha — woh 14 chhote requests apne 30 tokens ke baad 570 steps tak slot ghере idle
  baithe rahe. Measured GPU idle ~62%. Continuous batching on karte hi: chhote requests turant
  finish hokar slot chhod dete, naye waiting requests bhar jaate → idle ~8%, throughput ~3.1×. Sabak:
  jab output lengths variable hon (almost always), static batching ka tail-wait poora GPU kha jaata.

> **Architecture-review line:** *"Naive static batching left the GPU 50-70% idle because the whole
> batch waited on the longest sequence, and pre-reserved KV cache wasted ~70% of memory. Continuous
> batching keeps the GPU full and PagedAttention pushes KV utilisation past 95% with prefix-sharing
> — together that's why one vLLM replica did the work of ~8 of our old Flask workers."*

---

<a id="a15"></a>
## A1.5 — Serving framework decision: vLLM vs TGI vs Triton vs TensorRT-LLM

**Decision jo isse nikalti hai:** yeh woh "why this tool not that" hai jo interviewer *zaroor*
poochega agar aap bolo "we served LLMs". Niche decision matrix + breaking points.

**Decision matrix:**

| Framework | Best at | Throughput | Ops complexity | Kab chuno | Kab NAHI |
|---|---|---|---|---|---|
| **vLLM** | High-throughput OSS serving | ★★★★★ (PagedAttention) | Low-medium | Default choice — OSS models, apna infra, best tput/$ | Agar multi-framework ensemble ya non-LLM models bhi serve karne hon |
| **TGI** (HF) | HF ecosystem, easy deploy | ★★★★ | Low | HF Hub se seedha, quick prod, enterprise support chahiye | Ekdum bleeding-edge throughput chahiye (vLLM aksar aage) |
| **TensorRT-LLM** | NVIDIA-optimised raw speed | ★★★★★ (lowest latency) | **High** | Last-mile latency/$ squeeze, fixed model, NVIDIA-only, scale itna ki compile-effort worth | Fast iteration / models frequently badalte (compile step heavy) |
| **Triton Inference Server** | Multi-model, multi-framework serving platform | ★★★★ (with TRT-LLM backend) | High | Ek platform pe LLM + embeddings + rerankers + classic models, ensembles | Sirf ek LLM serve karna (vLLM simpler) |

**"Why X not Y" — the real reasoning:**
- **vLLM vs TGI:** dono continuous batching karte hain. vLLM ka PagedAttention aksar throughput
  mein aage; TGI ka HF integration + enterprise support smoother. *Breaking point:* ag HuggingFace
  ecosystem mein deeply invested ho aur support chahiye → TGI; agar raw tput/$ chahiye apne SRE
  team ke saath → vLLM.
- **vLLM vs TensorRT-LLM:** TRT-LLM model ko *compile* karता hai (kernel fusion, optimised
  attention) → lowest latency aur best $/token. *Cost:* har model/config change pe recompile,
  NVIDIA-locked, debugging hard. *Breaking point:* prototype/iteration phase → vLLM; ek stable
  model jise aap massive scale pe chala rahe ho aur 15-20% latency/cost bhi matter karता hai →
  TRT-LLM (aksar Triton ke andar backend ke roop mein).
- **Triton kab:** jab serving ek *platform* ban jaye — LLM + embedding model + reranker + ek fraud
  classifier, sab ek hi serving fleet pe, with ensembles/DAGs. Triton orchestration deta hai; vLLM
  single-purpose hai.

**Migration story (yeh interview gold hai):** "Started on vLLM for fast iteration → model froze →
moved the hot path to TensorRT-LLM behind Triton for ~30% lower p99 and better $/token, kept vLLM
for experimental models." Yeh ek defensible evolution hai, ek dum-decision nahi.

**Pros & cons (framework choice generally):** ✅ sahi framework = 2-30× cost/latency difference.
❌ har ek ka lock-in/ops cost; "best" framework depends on your stage (iterate vs scale), team
(SRE depth), aur hardware (NVIDIA-only?).

**Examples (concrete, walked through):**

- **Example 1 — Startup (vLLM) vs bank (Triton+TRT-LLM), same 13B model, alag sahi jawab:** ek
  startup naye models har 2 hafte try karti hai (Mistral, Llama, Qwen swap karte rehte). Unke liye
  **vLLM** sahi — ek line mein naya HuggingFace model load, koi compile step nahi, fast iteration.
  Wahi 13B ek bank ek fixed compliance-approved model ko 18 mahine tak chalाegा, 2,000 req/s pe, aur
  hardware NVIDIA H100 hai. Unke liye **TensorRT-LLM behind Triton** sahi — ek baar compile (kuch
  ghante ka effort) se ~30% lower p99 aur better $/token, jo us volume pe lakhon $/saal bachata hai;
  iteration ki zaroorat nahi toh compile-cost ek baar ka hai. Same model, ulta framework — kyunki
  *stage aur volume* alag. Sabak: "best framework" jaisा kuch nahi, context decide karता hai.
- **Example 2 — Triton kyun (jab serving ek platform ban gaya):** ek RAG product shuru mein sirf ek
  LLM serve karta tha (vLLM kaafi tha). Phir add hua: ek embedding model (queries embed karne ko),
  ek cross-encoder reranker, aur ek small "query classifier" (intent detect). Ab 4 alag models, 4
  alag deployments, 4 alag autoscaling configs — ops nightmare. Team **Triton** pe consolidate hui:
  saare 4 models ek serving fleet pe, ek ensemble DAG (classify → embed → retrieve → rerank →
  LLM), LLM ke liye TRT-LLM backend. Ek jagah monitoring/scaling, GPU sharing better. Sabak: jab
  serving single-model se multi-model *platform* ban jaye, Triton jaisा orchestration layer justify
  hota hai — vLLM akela single-purpose hai.

> **Architecture-review line:** *"We defaulted to vLLM for throughput-per-dollar on OSS models.
> Once a model stabilised at high volume we compiled it with TensorRT-LLM behind Triton for ~30%
> lower p99 and better cost/token, while keeping vLLM for fast-moving experimental models. Triton
> was the choice specifically because we co-served embeddings and rerankers in the same fleet."*

---

<a id="a16"></a>
## A1.6 — Parallelism: tensor vs pipeline vs replica (kab kaunsa)

**Decision jo isse nikalti hai:** "model GPU mein fit nahi ho raha / latency kam karni hai / aur
throughput chahiye" — teeno ka jawab alag parallelism hai. Inhe confuse karna common galti hai.

**Teen cheezein, teen alag problems:**

| Strategy | Kya karta hai | Kis problem ko solve karta | Cost |
|---|---|---|---|
| **Replication (data parallel)** | Poora model har GPU pe copy; requests baant do | **Throughput** (zyada QPS) | Simplest; har GPU independent |
| **Tensor parallelism (TP)** | Ek hi layer ke weights ko GPUs mein split (har matmul shard) | **Model fit nahi hota** + **latency** kam | Har token pe GPUs ke beech all-reduce — fast interconnect (NVLink) zaroori |
| **Pipeline parallelism (PP)** | Layers ko GPUs mein baanto (GPU0: layer 1-10, GPU1: 11-20...) | **Model fit nahi hota** (bahut bada) | "Bubble" idle time; latency add karta |

**"Why X not Y" — real reasoning:**
- **Replica first:** agar model ek GPU pe fit hota hai, *hamesha* replication se scale karo. Sabse
  simple, no comms overhead, linear throughput. TP/PP sirf tab jab model fit hi na ho ya
  single-request latency kam karni ho.
- **TP for fit + latency:** 70B model fp16 = ~140GB, ek 80GB GPU pe fit nahi → TP across 2-4 GPUs.
  Bonus: TP single-request latency bhi kam karता hai (matmul split = parallel compute). *Breaking
  point:* TP sirf ek node ke andar achha (NVLink ~600GB/s); node ke paar (slow network) TP ka
  all-reduce kill kar deta hai latency.
- **PP across nodes:** jab model itna bada ho ki ek node ke saare GPUs mein bhi na fit ho → PP se
  layers ko nodes mein baanto. PP ka comms kम hai (sirf boundary pe activations pass) toh
  cross-node tolerable, par "pipeline bubble" idle time aata hai.
- **Real combo:** bade models pe **TP within node + PP across nodes + replication for throughput** —
  teeno ek saath. Example: 70B → TP=4 (ek node ke 4 GPUs), phir us node ko 6× replicate for QPS.

**Numbers:** TP=2 se single-request latency ~1.7× faster (ideal 2×, minus all-reduce overhead). Par
TP=8 pe all-reduce overhead itna ki diminishing returns — isiliye TP aksar ≤ ek node ke GPUs.

**Pros & cons:** ✅ sahi parallelism = fit + latency + throughput sab address. ❌ TP interconnect-
hungry (galat jagah = slow); PP bubbles; over-parallelising chhote model = waste (replica better).

**Examples (concrete, walked through):**

- **Example 1 — Cross-node TP ka blunder (NVLink vs Ethernet):** ek team ne 70B model ko TP=8 pe
  daalा, par unke paas ek node mein sirf 4 GPUs the — toh TP 2 nodes ke paar gaya (4 + 4), aur un
  nodes ke beech connection normal 25 Gb/s Ethernet tha, NVLink nahi. Har decode step pe TP ka
  all-reduce har token pe nodes ke beech data bhejता hai — woh Ethernet pe ~10× slow tha intra-node
  NVLink (~600 GB/s) ke comparison mein. Result: TP=8 cross-node ne latency *kharab* kar di (TPOT
  ~3× badh gaya) bina kisi fayde ke. **Fix:** TP=4 ek node ke andar (NVLink) rakha aur model ko fit
  karne ke liye FP8 quantization use ki (140GB → ~70GB, 4×80GB mein aaram se) → latency theek. Sabak:
  TP ki seema NVLink hai — node ke bahar TP mat le jao.
- **Example 2 — 70B ka full combo (TP + replica), ek shopping assistant 500 req/s pe:** model
  Llama-2-70B fp16 (~140GB) ek 80GB GPU pe fit nahi. Plan: (1) **TP=4** ek 4×A100-80GB node ke andar
  (NVLink) → model fit + single-request latency ~3× behtar; ek aisa 4-GPU unit ~80 req/s deta hai.
  (2) 500 req/s ke liye us 4-GPU unit ko **7× replicate** (= 28 GPUs) + headroom → 8 units = 32
  GPUs. Yaani TP "fit + latency" ke liye, replication "throughput" ke liye — dono ka kaam alag, dono
  saath. PP (pipeline) use *nahi* kiya kyunki model ek node mein TP se fit ho gaya; PP sirf tab aata
  jab ek node bhi kam pad jaye. Sabak: replicate-for-QPS aur TP-for-fit ko mila kar socho.

> **Architecture-review line:** *"70B in fp16 didn't fit on one 80GB GPU, so we used tensor
> parallelism across 4 GPUs within a node — NVLink made the per-token all-reduce cheap — then
> replicated that 4-GPU unit for throughput. We avoided cross-node TP because the all-reduce over
> the network would have dominated decode latency."*

---

<a id="a17"></a>
## A1.7 — Quantization & speculative decoding (latency/cost levers)

**Decision jo isse nikalti hai:** "GPU bill aadha karna hai" ya "TPOT half karna hai" bina model
badle — yeh do levers. Par dono ke trade-offs hain jo defend karne padte hain.

**Lever 1 — Quantization (weights ko kam bits mein):** fp16 (16-bit) se INT8/FP8 (8-bit) ya INT4
(4-bit) pe le jao. Kyunki decode memory-bound hai (A1.1), aadhे bits = aadhा memory read = **~2×
faster decode + aadhी VRAM** (matlab bada batch ya chhoti GPU).

| Scheme | Bits | Quality loss | Kab |
|---|---|---|---|
| FP8 | 8 | Bahut kam (H100 native) | Default jab H100 ho — almost free win |
| INT8 (SmoothQuant/LLM.int8) | 8 | Kam | Wide support, safe |
| INT4 (AWQ, GPTQ) | 4 | Noticeable on hard tasks | Memory-constrained, cost-critical; *eval karke* |

**Breaking point:** INT4 chhote models (7B) pe quality noticeably gira sakta hai (especially
reasoning/code); bade models (70B) INT4 ko better tolerate karte hain. **Rule:** quantize karo,
phir *apne eval set pe* quality measure karo (kabhi blindly nahi) — yeh woh discipline hai jo
principal dikhata hai.

**Lever 2 — Speculative decoding (latency without quality loss):** ek chhota "draft" model K tokens
guess karता hai (sasta, fast), phir bada "target" model un K tokens ko *ek hi parallel forward
pass* mein verify karता hai. Jo match karte hain woh accept (ek step mein kai tokens!), pehla
mismatch pe target ka token lo. Output **bit-exact same** as target model (yeh key — koi quality
loss nahi), par **2-3× faster decode** jab draft accuracy achhi ho.

**Breaking point / kab NAHI:** speculative decoding tabhi jeetta hai jab draft model target se
kaafi sehmat ho (acceptance rate high). Agar workload diverse/hard ho (draft galat guesses karta) →
wasted verification compute, gain nahi. Aur draft model extra VRAM leta hai (KV cache budget kam).
Best for: predictable domains, low-traffic-but-latency-critical (jab batch chhota ho aur GPU idle
ho — speculative us idle compute ko use karता hai).

**Pros & cons:** ✅ quantization = direct cost/VRAM/throughput win; speculative = latency win without
quality loss. ❌ quantization quality risk (eval zaroori); speculative gains workload-dependent +
extra VRAM + complexity. Dono levers, magic nahi.

**Examples (concrete, walked through):**

- **Example 1 — INT4 ne paisa bachaya par code-quality giraya (eval ne pakda):** ek team ne ek 7B
  code-assistant ko INT4 (AWQ) quantize kiya — VRAM ~14GB se ~4GB, ek sasti L4 GPU pe fit, cost ~3×
  kam. Demo pe theek laga. Par unka eval set (HumanEval-style pass@1) chalाya: fp16 ~62% se INT4
  ~51% gir gaya — code generation INT4 ke rounding errors pe sensitive hai (ek galat token = compile
  fail). **Decision:** chhote 7B pe INT4 reject; INT8 (SmoothQuant) pe gaye — quality ~61% (barabar),
  VRAM ~7GB, cost abhi bhi ~2× kam. Sabak: quantize karo *phir apne task ke eval pe naapो* —
  INT4 chhote/hard-task models pe risky, blindly mat lo.
- **Example 2 — Speculative decoding jeeta (predictable domain) vs haara (diverse chat):** ek
  customer-support bot jo zyadatar templated/predictable jawab deta hai (return policy, order
  status) — yahan ek 1B draft model target 70B se ~85% tokens pe sehmat tha (acceptance high), toh
  speculative decoding ne TPOT ~2.4× kam kar diya, output bit-identical. Wahi technique ek
  open-ended creative-writing bot pe lagaya: draft sirf ~35% tokens pe sehmat (output diverse,
  unpredictable) → zyadatar speculative tokens reject, verification compute waste, net gain ~1.1×
  (barely worth the extra 1B model ka VRAM). **Decision:** support bot pe on, creative bot pe off.
  Sabak: speculative decoding ka fayda acceptance-rate pe depend karta — predictable domain pe huge,
  diverse domain pe negligible.

> **Architecture-review line:** *"On H100s we ran FP8 weights — nearly free given native support —
> which halved KV/weight memory traffic and roughly doubled decode throughput. For our
> latency-critical low-QPS path we added speculative decoding with a 1B draft model, getting ~2.3x
> faster TPOT at bit-identical output because the domain was predictable enough for high acceptance."*

---

<a id="a18"></a>
## A1.8 — Capacity & cost model (real numbers, end-to-end)

**Decision jo isse nikalti hai:** "kitne GPU chahiye aur mahine ka kitna bill?" — yeh aap whiteboard
pe derive kar paao, yahi capacity-planning question ka asli jawab hai.

**Worked example (interview mein yeh chalाo):** ek chatbot, **100 req/s** peak, average **2,000
prompt tokens + 300 output tokens**, model 13B on A100-40GB, p95 TPOT target 50ms.

**Step 1 — ek replica ka throughput:** continuous batching ke saath ek A100 13B pe realistically
~throughput ~2,500-4,000 output tokens/sec deता hai (model/seq-len pe depend). Maan lo **3,000
tok/s**.

**Step 2 — demand:** 100 req/s × 300 output tokens = **30,000 output tokens/sec** chahiye. (Prefill
alag — 100 × 2,000 = 200k prompt tokens/sec process karne ka compute bhi chahiye, par woh batched +
fast.)

**Step 3 — replicas:** 30,000 / 3,000 = **10 GPUs** decode ke liye, + headroom for prefill spikes
aur p95 → round up to **~13-14 A100s**. (Yeh woh "headroom" judgement hai jo seniority dikhata hai
— utilisation 100% pe chalाoge toh p95 latency tej barbaad hogi, A1.9.)

**Step 4 — cost:** ~14 × A100 @ ~$2/GPU-hr (cloud, on-demand) ≈ $28/hr ≈ **~$20k/month**.
Optimizations: FP8/quantization (~2× tput → ~7 GPUs → ~$10k), off-peak autoscale-down (~-30%),
prefix-caching for repeated system prompts (~-15% prefill). Realistic landed: **~$7-8k/month**.

**Token-economics framing:** $20k/month ÷ (100 req/s × 300 tok × 2.6M sec/month) ≈ cost per
million output tokens. Yeh number aap self-hosted vs API (GPT-4o-mini etc.) compare karne ke liye
use karte ho — *that's the build-vs-buy decision*.

**Build vs buy (the real call):** low/spiky volume → API (no idle GPU, pay-per-token). High steady
volume → self-host (API ka per-token markup self-hosting se mehenga ho jaता hai past a breakeven,
typically tens-of-millions tokens/day). Yeh breakeven calculate karna = principal-level answer.

**Examples (concrete, walked through):**

- **Example 1 — Build-vs-buy breakeven ek internal tool ke liye (API jeeta):** ek company ka internal
  doc-search bot ~200 employees use karte, peak ~3 req/s, average ~8M output tokens/month. Self-host:
  even ek single A100 (~$1,450/month on-demand, ya ~$700 reserved) chahiye 24×7 — par utilisation
  sirf ~5% (employees din mein thodी der use karte). Yaani $700-1,450/month ek mostly-idle GPU pe.
  API route: 8M tokens × ~$0.60/M (GPT-4o-mini-class) = ~$5/month output + thodा input ≈ **<$50/month
  total**. **Decision:** API — spiky low-volume internal tool pe self-hosting ka idle-GPU cost
  bevkoofi hai. Sabak: low/spiky volume pe API ka pay-per-token hamesha jeetता; idle GPU = jalta paisa.
- **Example 2 — Same product scale pe ulta ho gaya (self-host jeeta):** wahi company ka external
  customer-facing feature chal pada — ~150M output tokens/month, steady traffic (din-raat usage,
  global users). API pe: 150M × ~$0.60/M ≈ **~$90k/month** (sirf output; input chunks ke saath aur
  zyada). Self-host: ~14 A100s ka humara model ~$20k/month on-demand, FP8 + reserved instances ke
  saath ~$7-8k/month, aur woh ~150M+ tokens aaraam se serve karta high utilisation pe. **Decision:**
  is volume pe self-host ~10× sasta — breakeven cross ho gaya (~tens-of-millions tokens/day). Sabak:
  same product, volume badalne pe build-vs-buy *palat* jaata — breakeven ko dobara calculate karo
  jab scale badle, ek baar ka decision nahi.

> **Architecture-review line:** *"At 100 RPS and 300 output tokens, that's 30k tok/s; one A100
> replica did ~3k tok/s, so ~10 GPUs plus headroom for p95 and prefill spikes — about 14 A100s,
> ~$20k/month on-demand. FP8 and off-peak scaling took it to ~$8k. Below our volume the per-token
> API price beat self-hosting, so the breakeven calc is what justified building."*

---

<a id="a19"></a>
## A1.9 — Production failure modes & SLO engineering

**Decision jo isse nikalti hai:** yeh woh "tumne kya break hote dekha aur kaise fix kiya" hai —
real prod experience ka proof. Interviewer yahin separate karता hai jisne *padha* hai vs jisne
*chalाya* hai.

**Failure modes (har ek + signal + fix):**
- **KV cache OOM under load:** traffic spike → concurrent requests × long contexts → KV cache GPU
  memory cross → requests crash/evict. *Signal:* OOM errors, preemption spikes. *Fix:* admission
  control (max concurrent), max-context limits per request, autoscale on KV-utilisation (not just
  GPU%).
- **Latency-throughput tension (the big one):** batch bada karo → throughput up par per-request
  TPOT up (queueing). *Signal:* p99 TPOT spike at high utilisation. *Fix:* batch size cap, SLO-aware
  scheduling, GPU ko ~70-80% pe chalाo (100% = latency cliff).
- **Prefill blocking decode:** ek lamba prompt aaya → uska bhaari prefill sabke decode ko rok deta →
  TPOT jitter sabke liye. *Fix:* chunked prefill (A1.2), ya prefill/decode disaggregation.
- **Head-of-line blocking:** ek bahut-lamba-output request batch slot ghере rehता. *Fix:* continuous
  batching (already helps), max-tokens cap.
- **Cold start:** naya replica = weights load (13-140GB GPU pe) = minutes. Autoscale slow. *Fix:*
  pre-warmed pool, faster weight loading, predictive scaling (traffic se pehle).
- **Cache stampede / prefix-cache thrash:** prefix-cache memory accounting galat → eviction storms.
  *Fix:* monitor cache hit-rate + eviction rate as first-class metrics.

**SLO engineering (kya measure karein):** TTFT p50/p95/p99, TPOT p50/p95/p99 (separately!), queue
wait time, KV-cache utilisation, batch size distribution, tokens/sec/GPU, preemption rate. "Average
latency" LLM serving mein useless — distribution + tail dekho.

**Examples (concrete incident walkthroughs):**

- **Example 1 — The latency cliff (95% utilisation pe traffic spike):** cost bachane ke liye team ne
  autoscaling ko ~95% GPU utilisation pe set kiya tha (GPU ko "bhar ke" chalाo). Ek marketing email
  gaya → traffic 2× spike. GPU already 95% pe tha, toh nayी requests queue mein lagne lagi; KV cache
  bhi bhar gaya toh chalti requests *preempt* (evict) hone lagi aur dobara chalni padi. p99 TPOT
  50ms se 400ms pe chala gaya, kuch requests timeout. **Root cause:** 95% utilisation pe koi headroom
  nahi tha spike ya p99 ke liye — yeh ek "cliff" hai, gradual nahi. **Fix:** (1) target utilisation
  ~75%, (2) admission control (max concurrent requests, baaki ko fail-fast ya queue with timeout),
  (3) autoscale trigger ko GPU% se badal kar **KV-cache utilisation** pe rakha (woh asli bottleneck
  tha). p99 stable ho gaya. Sabak: LLM serving mein latency-vs-utilisation linear nahi — last 20%
  utilisation ek cliff hai, headroom rakho.
- **Example 2 — Cold-start ne autoscaling bekaar kar di:** ek service spiky traffic pe autoscale
  karti thi — par jab naya replica chahiye hota, naya pod 70B model ke ~140GB weights disk/network se
  GPU pe load karta ~4-6 min leta tha. Traffic spike 30 sec mein aa jaता, replica 5 min baad ready —
  tab tak spike khatam ho chuka hota aur users ko 5 min errors/slowness mili. Autoscaling "kaam kar
  rahi" thi par bemtlab. **Fix:** (1) ek **pre-warmed warm pool** (2 extra replicas hamesha ready,
  thodा cost par instant), (2) weights ko faster load karne ko local NVMe pe cache + safetensors
  fast-load, load time ~6 min se ~90 sec, (3) **predictive scaling** — traffic patterns (daily peak
  9am) se pehle hi scale-up schedule. Sabak: LLM cold-start minutes mein hota (weights bade), toh
  reactive autoscaling akelी kaafi nahi — warm pool + predictive scaling chahiye.

> **Architecture-review line:** *"Our worst incident was a latency cliff: we'd pushed GPU
> utilisation to ~95% for cost, and a traffic spike sent p99 TPOT from 50ms to 400ms because of
> queueing and KV-cache preemption. We added admission control, capped batch size, set a target of
> ~75% utilisation, and turned on chunked prefill — p99 stabilised and we autoscaled on KV
> utilisation rather than GPU percent."*

---

<a id="a110"></a>
## A1.10 — The architecture-review defense (one-liners)

Yeh woh compressed answers hain jo aap Google/Meta system-design round mein, ya apne prod review
mein, 30 second mein bol sakte ho. Har ek ke peeche poora reasoning upar hai.

1. **"Why is LLM serving its own problem?"** — Decode is memory-bandwidth bound, not compute bound;
   a single request barely uses the GPU, so the entire design is about batching to amortise the
   per-token weight read.
2. **"What limits concurrency?"** — Not compute — KV cache memory. Weights + per-request KV
   (~800KB/token for 13B) set how many requests fit; that's why we use GQA models and PagedAttention.
3. **"Why vLLM/TGI not a Flask loop?"** — Continuous batching keeps the GPU full instead of 50-70%
   idle, and PagedAttention pushes KV utilisation past 95% with prefix-sharing — together ~5-15×
   throughput.
4. **"Two latency SLOs?"** — Yes: TTFT (prefill, compute-bound) and TPOT (decode, memory-bound) are
   different workloads and are tuned and even disaggregated separately.
5. **"How do you cut cost?"** — FP8/INT8 quantization (eval-gated), speculative decoding for
   latency-critical low-QPS paths, off-peak autoscaling, prefix-caching, and a build-vs-buy
   breakeven on cost-per-million-tokens.
6. **"How do you scale the model itself?"** — Replicate if it fits; tensor-parallel within a node
   (NVLink) for fit+latency; pipeline-parallel across nodes only when it won't fit in one node.
7. **"What broke in prod?"** — The latency cliff at high utilisation: fixed with admission control,
   batch caps, ~75% utilisation target, chunked prefill, and autoscaling on KV-cache utilisation.

---

> **Is sample ka maqsad:** dikhaना ki "layman explanation" ka matlab "layman topic" nahi. Upar har
> cheez plain Hinglish mein samjhaayi gayi — par topics (PagedAttention, KV-cache math, TP/PP,
> speculative decoding, prefill/decode disaggregation, latency cliff) woh hain jo ek 10-saal ka ML
> engineer prod mein face karta hai aur ek principal review mein defend karta hai.
>
> **Agar yeh level theek hai → main A2-A7 isi bar pe bana dunga** (RAG at scale, distributed
> training & GPU, data/feature platforms, serving/reliability/rollout, API design, scaling & cost).

[↑ Back to top](#contents)
