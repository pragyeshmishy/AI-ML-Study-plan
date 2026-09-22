<a id="contents"></a>
# Conversational AI at Billion Scale — 50M Concurrent, 150ms Latency, Long-Term Memory

> **Google L5 ML Engineer Interview Prep** — yeh doc ek conversational AI system design karta hai
> jo 1 billion users serve kare, 50 million concurrent handle kare, 150ms mein pehla token de,
> aur saalon tak yaad rakhe. Har section mein: real numbers, decision matrix, worked examples,
> failure modes, aur architecture-review line.
>
> **Style:** Hinglish, education-first. DC-Copilot ek real production system hai — har section
> ke end mein ek "DC-Copilot Connection" subsection mein dikhaya gaya hai ki woh aaj kya karta
> hai aur Google-scale pe kya badlega. Baaki sab universal hai.

---

## Contents

- [1 — Scale Numbers Ka Physics](#s1)
- [2 — Latency Budget Engineering](#s2)
- [3 — Global Traffic Routing](#s3)
- [4 — Compute Orchestration](#s4)
- [5 — LLM Inference for 150ms First Token](#s5)
- [6 — State Management at 50M Concurrent](#s6)
- [7 — Long-Term Memory Architecture](#s7)
- [8 — Vector Search at Billion Scale](#s8)
- [9 — Multi-Layer Caching](#s9)
- [10 — Streaming & Real-time Delivery](#s10)
- [11 — Full Architecture + DC-Copilot Enhancement Map](#s11)

---

<a id="s1"></a>
## 1 — Scale Numbers Ka Physics

**Decision jo isse nikalti hai:** poora system design inn numbers se derive hota hai. Agar yeh
galat estimate kiye, toh ya toh over-provision karoge (paisa waste) ya under-provision (system crash).
Interview mein yeh back-of-envelope math dikhana L5 ka signal hai.

**Asli baat:** "50 million concurrent" sunne mein ek number lagta hai, par engineering mein iska
matlab hai: **kitne messages per second, kitni GPU chahiye, kitni RAM, kitna network bandwidth.**
Har number doosre se derive hota hai — ek chain hai.

### Back-of-Envelope Calculation (Step by Step)

Sochiye ek WhatsApp-size chat app, par har message pe AI response dena hai.

**Step 1 — Messages per second:**
```
50M concurrent users
Average user sends 1 message every 30 seconds (typing + reading time)
Messages/sec = 50,000,000 ÷ 30 = ~1,670,000 msg/sec = ~1.67M msg/sec
```

**Step 2 — Active LLM inferences:**
```
Har message pe ek LLM call chahiye
Average LLM call duration = 2 seconds (first token 150ms + full generation ~2s)
Active inferences at any time = 1.67M × 2 = ~3.34M
With queuing + batching efficiency: ~2M simultaneous GPU inferences
```

**Step 3 — GPU count:**
```
vLLM on A100 with continuous batching (batch=64): ~600 requests/sec/GPU
GPUs needed = 1,670,000 ÷ 600 = ~2,783 GPUs (base)
With 20% headroom: ~3,300 A100 GPUs
With H100 (2x throughput): ~1,650 H100 GPUs
```

**Step 4 — API Pod count:**
```
Har pod async I/O se ~5,000 concurrent requests handle karta hai
(FastAPI/uvicorn with uvloop, mostly I/O bound — waiting for LLM)
Pods = 50,000,000 connections ÷ 5,000/pod = 10,000 pods
```

**Step 5 — Memory (RAM):**
```
Per-session state: ~8KB (messages + context + metadata)
Hot state: 50M × 8KB = 400GB (Redis cluster)
Per-pod memory: 4GB app + 2GB cache = 6GB
Total pod RAM: 10,000 × 6GB = 60TB
GPU memory: 3,300 × 80GB (A100) = 264TB HBM
```

**Step 6 — Network bandwidth:**
```
Average response: 500 tokens × 4 bytes/token = 2KB
Streaming overhead (SSE/WebSocket headers): ~1KB extra
Per response: ~3KB outbound
Outbound: 1.67M × 3KB = ~5 GB/sec = ~40 Gbps sustained
Inbound (user messages): 1.67M × 0.5KB = ~835 MB/sec = ~6.7 Gbps
```

**Step 7 — Storage:**
```
Long-term memory: 1B users × 100 memories × 1KB = 100TB (Bigtable)
Vector embeddings: 10B chunks × 6KB = 60TB (Milvus)
Session checkpoints: 50M × 20KB = 1TB (DynamoDB)
Document chunks: shared across tenants, ~5TB (OpenSearch/Milvus)
```

### Summary Table

| Component | Calculation | Number | Monthly Cost (est.) |
|-----------|-----------|--------|-------------------|
| API Pods | 50M ÷ 5K/pod | **10,000 pods** | ~$365K |
| GPU (A100) | 1.67M req/s ÷ 600/GPU | **3,300 GPUs** | ~$2.5M |
| Redis | 50M × 8KB | **400GB, 64 shards** | ~$40K |
| DynamoDB | 50M × 2 items | **100M items, 2M RCU** | ~$170K |
| Long-term Memory | 1B × 100 × 1KB | **100TB Bigtable** | ~$2.6K |
| Vector DB | 10B × 6KB | **60TB, 200 shards** | ~$100K |
| Network | 40 Gbps out | **~5 GB/sec** | ~$50K |
| **Total** | | | **~$3.6M/month = ~$43M/year** |

> **Per user per year:** $43M ÷ 1B = **$0.043/user/year** — yeh Google/Meta scale pe
> reasonable hai (WhatsApp ~$0.03/user/year for infrastructure).

### Worked Examples

**Example 1 — ChatGPT Scale Comparison:**
OpenAI ka ChatGPT reportedly ~10M concurrent users peak pe handle karta hai (2024 estimates).
Humara target 50M hai — **5x ChatGPT.** ChatGPT reportedly ~30,000 A100-equivalent GPUs use
karta hai, par woh longer responses generate karta hai (average ~300 tokens vs hamara ~150).
Proportionally: 30K × (50M/10M) × (150/300) = **75K GPU-equivalent** agar same model size
use karein. Par hum model routing se 60% queries chhote model pe bhejenge → actual ~3,300 A100.
Yeh feasible hai kyunki 60% queries simple hain (greetings, follow-ups).

**Example 2 — WhatsApp Infrastructure Analogy:**
WhatsApp 2B users, ~100M concurrent handle karta hai — 2x humara target. Par WhatsApp mein
AI nahi hai (sirf message relay). Humara system har message pe 100ms GPU compute karta hai.
WhatsApp ka infra ~$1B/year hai, humara ~$43M/year — kyunki WhatsApp ko media storage
(photos/videos = petabytes) chahiye, humein nahi.

### Production Failure Modes

- **Capacity math galat:** agar average think time 30s nahi 15s nikla → messages/sec doubles → GPU shortage → latency spike → cascading failure. **Fix:** monitor actual msg/sec, not estimated. Auto-scale trigger at 70% capacity, not 90%.
- **Bursty traffic:** Super Bowl ke time 10x spike. Steady-state math kaam nahi aayega. **Fix:** pre-provision for predicted events + serverless overflow (Lambda/Cloud Functions for non-LLM work).

> **Architecture-review line:** *"At 50M concurrent with 30-second think time, we're at 1.67M
> msg/sec requiring 3,300 A100s with continuous batching at batch-64. The $43M/year TCO at
> $0.043/user/year is in line with comparable large-scale consumer AI products."*

### DC-Copilot Connection

DC-Copilot aaj ~100-1,000 concurrent sessions handle karta hai — ek ECS cluster, single region.
50M concurrent ke liye **50,000x** scale chahiye. Par important baat: DC-Copilot ka two-phase
design (chatInitialize + chat) already smart hai — Snowflake queries sirf ek baar hote hain.
Yeh pattern Google-scale pe bhi kaam karega with caching layer added.

[↑ Back to top](#contents)

---

<a id="s2"></a>
## 2 — Latency Budget Engineering

**Decision jo isse nikalti hai:** har component ko ek fixed millisecond budget milta hai.
Agar koi component apna budget kha jaaye, doosre ko compensate karna padega ya SLO miss hoga.
Yeh discipline system design ka backbone hai.

**Asli baat:** 150ms mein poora AI response generate karna impossible hai — GPT-4 level model
ko ek sentence likhne mein 1-3 seconds lagte hain. Toh **150ms ka matlab hai "first token"** —
pehla word user ko 150ms mein dikhna chahiye, baaki words stream hote rahenge.

Jaise phone pe baat karte ho — doosra insaan "Haan..." bolna 150ms mein start karta hai
(fast), phir poora sentence 5 seconds mein bolta hai (normal). Woh "Haan..." ka feel chahiye.

### 150ms Breakdown (Har Millisecond Ka Hisaab)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Component         │ Budget │ Technique                    │ Fallback│
├───────────────────┼────────┼──────────────────────────────┼─────────┤
│ DNS Resolution    │   2ms  │ Anycast + client DNS cache   │   5ms   │
│ Edge → Region     │   3ms  │ PoP in same city as region   │  10ms   │
│ API Routing       │   5ms  │ gRPC (binary, no JSON parse) │  15ms   │
│ State Load        │  10ms  │ DAX in-memory cache          │  20ms   │
│ Intent Classify   │   8ms  │ DistilBERT local (not LLM)   │ 200ms!  │
│ Memory Retrieval  │   7ms  │ Redis (hot) + async Bigtable │  50ms   │
│ LLM First Token   │ 100ms  │ vLLM, speculative decode     │ 500ms+  │
│ Stream to Client  │   7ms  │ Persistent WebSocket, no TLS │  15ms   │
│ Safety Buffer     │   8ms  │ For network jitter           │    —    │
├───────────────────┼────────┼──────────────────────────────┼─────────┤
│ TOTAL             │ 150ms  │                              │ 815ms   │
└──────────────────────────────────────────────────────────────────────┘
```

Dekho "Fallback" column — agar koi bhi optimization na karo toh **815ms** lagega.
Optimization se 150ms possible hai. Sabse bada saving: LLM (500→100ms) aur Intent (200→8ms).

### Key Insight: TTFT vs TPOT (Two Different SLOs)

Yeh A1 mein detail mein cover hua hai (A1.2), par yahan conversational AI ke angle se:

- **TTFT (Time To First Token) = 150ms SLO** — user ko feel ho ki AI ne sunna aur respond karna shuru kiya
- **TPOT (Time Per Output Token) = 30-50ms** — tokens kitni speed se aate hain (reading speed se fast hona chahiye)
- **Total response time = TTFT + (num_tokens × TPOT)** = 150ms + (200 × 40ms) = ~8.15 seconds for 200 tokens

Interview mein yeh clarification dena zaruri hai — interviewer specifically TTFT pooch raha hai.

### Decision Matrix: Latency Budget Tight Ho Toh Kya Kaat-ein?

| Priority | What to Cut | Saves | Risk |
|----------|------------|-------|------|
| 1 | Intent from LLM → DistilBERT | 192ms | Slightly lower intent accuracy (~95% vs ~98%) |
| 2 | State from DynamoDB → DAX/Redis | 10-14ms | Cache staleness (acceptable for chat state) |
| 3 | REST → gRPC | 10ms | Client compatibility (need gRPC-Web gateway) |
| 4 | Full model → model routing (7B for simple) | 60-80ms | Quality drop for simple queries (acceptable) |
| 5 | Skip summarization subgraph | 0ms latency (async) | Memory growth (handle with background job) |

### Worked Examples

**Example 1 — E-commerce Chatbot (Prefill-Heavy):**
Imagine Flipkart ka AI assistant. User poochta hai "mere order ka status kya hai" — system
ko product catalog, order history, return policy sab prompt mein daalna hai. Prompt size:
~4,000 tokens. Prefill (processing prompt) compute-bound hai: 4,000 tokens on A100 = ~80ms.
Add network + routing = 120ms. LLM first token barely 150ms mein aata hai.
**Decision:** prompt ko compress karo — 4,000 → 2,000 tokens (top-K retrieval, not full history).
Prefill: 40ms. Ab comfortable under budget. Sabak: **lambe prompts se TTFT badh jaata hai.**

**Example 2 — Healthcare Assistant (Decode-Heavy):**
Ek telemedicine bot. Doctor ka note generate karna hai — 500+ tokens output, medically
accurate hona chahiye. Yahan TTFT fast hai (chhota prompt = 500 tokens, prefill ~15ms),
par TPOT critical hai — doctor 20 seconds wait nahi karega 500 tokens ke liye.
TPOT at 40ms = 500 × 40ms = 20 seconds. Unacceptable.
**Decision:** speculative decoding (medical domain draft model) → TPOT 20ms → 10 seconds.
Plus parallel generation: diagnosis + prescription as 2 concurrent LLM calls → 5 seconds perceived.
Sabak: **TTFT aur TPOT alag optimize hote hain.**

### Production Failure Modes

- **One component spikes:** DynamoDB ka p99 normally 8ms, par agar hot partition hit ho toh 200ms
  spike. Yeh akela poora budget kha jaata hai. **Fix:** DAX cache as shield — 99% reads never
  hit DynamoDB directly.
- **LLM cold start:** vLLM node restart hone pe pehle 10-20 requests slow (KV cache empty, CUDA
  warmup). **Fix:** health check mein "warm" status — pod ready tabhi mano jab 5 test inferences
  <100ms mein complete ho jaayein.

> **Architecture-review line:** *"Our 150ms TTFT budget allocates 100ms to LLM inference with
> speculative decoding, 8ms to local DistilBERT intent classification (replacing a 200ms LLM
> call), and <1ms to DAX-cached state loads. The single biggest unlock was moving intent
> classification off the LLM — that alone saved 192ms."*

### DC-Copilot Connection

DC-Copilot aaj ka latency: ~2-4 seconds TTFT. Breakdown:
- DynamoDB checkpoint load: 15ms ✅ (already ok)
- LangGraph node traversal (Translation → Profanity → Intent → Context → LLM): ~200ms overhead
- Azure OpenAI API call: **800-2000ms** ← yeh sabse bada bottleneck
- SSE stream setup: 50ms

Google-scale pe: Azure OpenAI hataao, self-hosted vLLM lagao (100ms).
ClassifyIntentNode mein LLM call hataao, DistilBERT lagao (2ms).
Net saving: ~1,800ms. New TTFT: ~150ms. Achievable.

[↑ Back to top](#contents)

---

<a id="s3"></a>
## 3 — Global Traffic Routing

**Decision jo isse nikalti hai:** 50M users duniya bhar se aate hain — agar sab ek data center
pe hit karein toh (a) latency high for distant users, (b) single point of failure. Multi-region
mandatory hai, aur routing smart hona chahiye.

**Asli baat:** socho Zomato hai. Bangalore mein user hai toh Bangalore kitchen se delivery aaye.
Delhi mein user hai toh Delhi kitchen se. Agar Bangalore kitchen band ho jaaye, Delhi wala
sambhaal le. Yahi **geo-routing + failover** hai.

### Architecture: 3 Layers of Routing

```
Layer 1 — DNS (Global):
  User browser → DNS query → Anycast IP resolve
  Anycast: ek IP address, par sabse paas ka server respond karta hai
  Latency: <2ms (DNS cached in browser/OS after first lookup)

Layer 2 — Edge (Regional):
  300+ PoPs (Points of Presence) worldwide — like mini-servers at ISPs
  Job: TLS termination (SSL handshake yahan hota hai, backend tak plain),
       WebSocket upgrade, basic rate limiting
  Latency: <3ms (same city as user typically)

Layer 3 — Regional Load Balancer:
  Routes to nearest healthy region (8 regions globally)
  Weighted routing: region capacity ke hisaab se traffic bhejo
  Health checks: har 5 seconds, unhealthy region se traffic hataao
```

### 8 Regions — Traffic Distribution

| Region | Location | Est. Users | Envoy Nodes | API Pods | GPUs (A100) |
|--------|----------|-----------|-------------|----------|-------------|
| us-east-1 | Virginia | 8M | 80 | 1,600 | 528 |
| us-west-2 | Oregon | 5M | 50 | 1,000 | 330 |
| eu-west-1 | Ireland | 7M | 70 | 1,400 | 462 |
| eu-central-1 | Frankfurt | 5M | 50 | 1,000 | 330 |
| ap-south-1 | Mumbai | 10M | 100 | 2,000 | 660 |
| ap-northeast-1 | Tokyo | 6M | 60 | 1,200 | 396 |
| ap-southeast-1 | Singapore | 5M | 50 | 1,000 | 330 |
| sa-east-1 | São Paulo | 4M | 40 | 800 | 264 |
| **Total** | | **50M** | **500** | **10,000** | **3,300** |

> Mumbai sabse bada region hai (10M) — India ke 1.4B population aur high smartphone adoption
> ke wajah se. Yeh realistic hai (WhatsApp ka bhi India biggest market hai).

### Tools & Unka Kaam

| Tool | Kya Karta Hai | Speciality | Kab Use |
|------|--------------|-----------|---------|
| **Google Cloud Global LB** | Anycast IP, auto-routes to nearest region | Single IP globally, integrated health checks | GCP pe ho toh default choice |
| **AWS Global Accelerator** | Anycast over AWS backbone network | Bypasses public internet (lower jitter) | AWS pe ho toh yeh use karo |
| **Cloudflare** | CDN + DDoS + edge compute | 300+ PoPs, Workers for edge logic | Edge pe rate limiting/auth karna ho |
| **Envoy Proxy** | L7 load balancer, service mesh | C++ (fast), 100K+ conn/node, gRPC native | Backend mein service-to-service |
| **Istio** | Service mesh control plane (uses Envoy) | mTLS, traffic splitting, canary deploys | K8s mein microservices manage karna ho |

### Worked Examples

**Example 1 — Riot Games (League of Legends) — Gaming Routing:**
Riot 180M monthly players handle karta hai globally. Har player ko <35ms latency chahiye
(game responsiveness). Unhone har region mein dedicated server cluster rakha, plus ek custom
routing system "Riot Direct" banaya jo ISP peering points pe apna hardware rakhta hai.
Result: player ka packet seedha nearest server pe jaata hai, public internet ke 5-6 hops skip.
**Lesson for us:** Google-scale AI pe bhi dedicated peering worth hai agar budget allow kare —
public internet pe 10-50ms extra lag typical hai.

**Example 2 — Netflix Open Connect — CDN at Scale:**
Netflix 300M subscribers, peak pe ~15M concurrent streams. Unhone apna CDN banaya — "Open
Connect Appliances" jo ISPs ke data centers mein physically rakhte hain. Content user ke
ISP ke andar se serve hota hai. Latency: near-zero for cached content.
**Lesson:** AI responses cache nahi ho sakte (dynamic hain), par **prompt templates, system
prompts, aur static assets** edge pe cache karo. Sirf dynamic part (LLM output) region se aaye.

### Production Failure Modes

- **Region outage:** AWS us-east-1 down (happens ~1-2x/year historically). 8M users ka traffic
  instantly us-west-2 aur eu-west-1 pe shift. Those regions ko **2x headroom** chahiye to absorb.
  **Fix:** every region at max 60% capacity normally, 40% buffer for failover absorption.
- **DNS propagation delay:** DNS change mein 30-300 seconds lag. Unhealthy region se traffic
  immediately hatana ho toh DNS slow hai. **Fix:** anycast + BGP route withdrawal — network level
  pe instant failover, DNS pe depend mat karo.
- **Cross-region data inconsistency:** User us-east-1 pe chatInitialize karta hai, phir flight
  mein ap-south-1 pe /chat karta hai. DynamoDB Global Table mein replication lag ~100-300ms.
  **Fix:** session affinity (sticky routing) — same user same region pe jab tak session active.

> **Architecture-review line:** *"We run 8 regions with Anycast routing through Global
> Accelerator, each region at 60% capacity for failover absorption. Session affinity keeps
> a user pinned to one region for the session lifetime, avoiding cross-region state
> inconsistency during DynamoDB Global Tables replication lag."*

### DC-Copilot Connection

DC-Copilot aaj: single region (likely us-east-1), ALB → ECS. Agar us-east-1 down ho toh
poora system down. Koi geo-routing nahi.

Google-scale pe: 8 regions, Anycast DNS, session affinity. ECS → Kubernetes (GKE/EKS).
Multi-tenant routing (`/api/v1/{productCode}/{tenantId}/chat`) already sahi hai —
tenant-based routing per region mein extend ho sakta hai.

[↑ Back to top](#contents)

---

<a id="s4"></a>
## 4 — Compute Orchestration

**Decision jo isse nikalti hai:** 10,000 pods ko manually manage karna impossible hai. Kubernetes
+ smart autoscaling chahiye jo traffic ke saath breathe kare. Par AI workloads ke liye standard
CPU-based autoscaling kaam nahi karta.

**Asli baat:** socho airport hai. Peak hours pe 50 counters khulte hain. Off-peak pe 10. Smart
counter management = autoscaling. Par AI mein twist: CPU low rehta hai even when pod overloaded
(I/O bound — LLM response ka wait).

### Why Standard CPU-Based Autoscaling Fails for AI

Normal web apps: CPU high → scale up. AI chat pods mein:
- CPU mostly **idle** (90% time = LLM ka wait)
- CPU 20% pe bhi pod overloaded (1000 WebSocket connections blocking)

**Fix:** Custom metrics:

| Metric | Threshold | Scale Action |
|--------|-----------|-------------|
| Active WebSocket connections | >3,000/pod | Scale up (target: 5K/pod) |
| Request queue depth | >50 pending | Scale up aggressively |
| P99 TTFT | >120ms | Scale up preemptively |
| GPU queue wait | >50ms | Scale GPU pool up |
| Connections <1K for 10 min | Sustained low | Scale down conservatively |

### Pod Pre-warming

Naya pod cold start: **15-20 seconds** (container pull + Python import + model load +
connection pools + health check). At 1.67M msg/sec, 20 sec = 33M messages affected.

**Fixes:**
1. **Over-provision 20%:** 2,000 extra pods always ready. Cost: $73K/month.
2. **Warm pool:** 500 pods fully initialized, no traffic, instant switch. Cost: $18K/month.
3. **Pre-scale before events:** known peaks (Black Friday, product launch) → scale 24h before.

### Graceful Degradation

```
Level 1 (latency ~180ms): Disable summarization, smaller model for simple intents
Level 2 (latency ~300ms): Priority queue (enterprise first), rate limit free tier
Level 3 (system at risk): Circuit breaker, shed 50% to overflow queue, alert on-call
```

### Cost

| Component | Count | Monthly |
|-----------|-------|---------|
| API Pods (c5.xlarge) | 10,000 | $1.2M |
| Warm Pool | 500 | $61K |
| Spare 20% | 2,000 | $244K |
| K8s Control Plane | 8 clusters | $42K |
| **Total Compute** | | **$1.55M/month** |

### Worked Examples

**Example 1 — Black Friday Spike:**
Normal: 20M concurrent. Black Friday: 80M (4x). Pre-scale 24h before from 10K→25K pods.
Autoscaler handles remaining burst. Warm pool absorbs first wave. SLO maintained for 95%.

**Example 2 — Region Failure (Mumbai Down):**
Mumbai = 10M concurrent. Traffic shifts to Singapore+Tokyo. Those regions at 60% capacity →
can absorb ~7M. Remaining 3M hit degradation level 2 for ~5 min while pods scale.
**Rule:** no single region >15% of global traffic.

### Production Failure Modes

- **Autoscaler flapping:** scale up → cost alarm → down → SLO breach → up. **Fix:** cooldown
  period (5 min), hysteresis (up at 70%, down at 30%).
- **Noisy neighbor:** one tenant floods. **Fix:** per-tenant rate limiting at gateway.

> **Architecture-review line:** *"We scale on WebSocket connections and P99 TTFT, not CPU.
> A 500-pod warm pool gives instant surge. Each region at 60% capacity for failover absorption."*

### DC-Copilot Connection

ECS tasks (manual scaling) → K8s HPA on custom metrics. `CopilotDependencies` init-at-startup
pattern works perfectly in K8s pods too.

[↑ Back to top](#contents)

---

<a id="s5"></a>
## 5 — LLM Inference for 150ms First Token

**Decision jo isse nikalti hai:** external API se 150ms impossible (network + inference = 250ms+).
Self-hosted mandatory. Plus model routing saves 73% GPUs.

**Asli baat:** aaj aap raw material bahar se mangwate ho (API call). Delivery mein time lagta hai.
Factory ke andar workshop laga lo (self-hosted) — delivery time zero.

### External API vs Self-Hosted

| Factor | Azure OpenAI API | Self-Hosted vLLM |
|--------|-----------------|-----------------|
| TTFT (p50) | 300-800ms | 60-100ms |
| TTFT (p99) | 1-3 seconds | 120-150ms |
| Cost/1M tokens | $10-30 (GPT-4) | ~$2-5 (GPU amortized) |
| At 50M concurrent | 167 Azure deployments, $22M/month | 1,200 A100s, $2.2M/month |

### Model Routing (73% GPU Savings)

```
User Message → DistilBERT Intent (2ms) →
  greetings, meta_answer (60%) → 7B Mistral (20ms TTFT)
  contextual, general (25%) → 13B Llama (50ms TTFT)
  diagnosis, fix, complex (15%) → 70B Llama (100ms TTFT)
```

| Model | Traffic | msgs/sec | GPUs Needed |
|-------|---------|---------|-------------|
| 7B | 60% | 1M | 125 A100s |
| 13B | 25% | 417K | 260 A100s |
| 70B | 15% | 250K | 520 A100s |
| **Total** | | 1.67M | **905 → 1,200 with headroom** |

**Without routing: 3,300 GPUs. With routing: 1,200. Savings: 73%.**

### Speculative Decoding

1. Draft model (7B) generates 5 tokens in ~10ms
2. Target model (70B) verifies all 5 in one forward pass (~20ms)
3. Acceptance rate ~75% → effective speedup: **2.5x**
4. TTFT: draft model's first token in 4ms. Even with rejection+regeneration: <25ms.

### Optimization Stack (Tools)

| Tool | Purpose | Speedup |
|------|---------|---------|
| **vLLM** | Serving engine, PagedAttention, continuous batching | 2-4x throughput |
| **TensorRT-LLM** | NVIDIA GPU optimizer, kernel fusion, graph opt | 2-3x inference speed |
| **INT8 Quantization** | 32-bit → 8-bit weights | 2x throughput, <1% quality loss |
| **Speculative Decoding** | Draft+verify pattern | 2-3x generation speed |
| **Continuous Batching** | Add/remove requests each step | 3-5x throughput vs static |
| **Tensor Parallelism** | Split model across GPUs | Near-linear with GPU count |

### Worked Examples

**Example 1 — SaaS Startup Self-Host Migration:**
10K concurrent, support bot. OpenAI: $40K/month, TTFT 400-800ms. Self-hosted 8 A100s + vLLM
+ 13B model: $19K/month, TTFT 80ms. **Savings: 52% cost, 5-10x latency.** Needed 2 ML engineers
for ops ($30K/month) — net break-even at this scale. At 50M concurrent: self-hosted wins massively.

**Example 2 — Model Routing Quality Check:**
DistilBERT routes complex medical query to 7B → wrong answer. No error, just bad quality.
**Fix:** confidence threshold — <0.85 → route to 70B. Plus 1% sampling: score 7B responses
with 70B, alert on quality regression.

> **Architecture-review line:** *"Model routing cut GPUs 73% (3,300→1,200). DistilBERT intent
> classification at 2ms replaced 200ms LLM call. Speculative decoding on 70B gives <100ms TTFT."*

### DC-Copilot Connection

`LLMService.stream()` → Azure OpenAI → replace with vLLM cluster.
`ClassifyIntentNode` LLM call → DistilBERT fine-tuned on 10 intents.
`CopilotDependencies` gets 3 LLM clients (7B, 13B, 70B) instead of 1.

[↑ Back to top](#contents)

---

<a id="s6"></a>
## 6 — State Management at 50M Concurrent

**Decision:** 50M sessions ka state = 400GB hot (Redis), 1TB warm (DynamoDB+DAX). Consistency:
strong same-region, eventual cross-region.

**Asli baat:** 50M log ek saath phone pe baat kar rahe hain. Har ek ki "file" <10ms mein ready
chahiye. Ek computer ki RAM mein nahi aayega — distribute karna padega.

### Storage Strategy

| State | Size/Session | Total | Latency | Store | TTL |
|-------|-------------|-------|---------|-------|-----|
| Hot (current turn) | 2KB | 100GB | <1ms | Redis | 30 min |
| Warm (full session) | 20KB | 1TB | <5ms | DynamoDB+DAX | 30 days |
| Cold (old) | 20KB | 10TB+ | <50ms | DynamoDB | 1 year |
| Profile | 5KB | 5TB | <10ms | Bigtable | Permanent |

### Redis Cluster Design

```
400GB ÷ 64 shards = 6.25GB/shard
Each shard: 1 primary + 2 replicas = 192 Redis instances
Shard key: consistent hash on session_id (MurmurHash3, 150 virtual nodes)
Read: <0.5ms | Write: <1ms | Cluster throughput: 6.4M ops/sec
We need: 1.67M msg/sec × 3 ops/msg = 5M ops/sec → comfortable headroom
```

### DynamoDB Global Tables + DAX

```
8 regions, async replication (100-300ms lag)
100M items, 2M RCU peak, 200K WCU peak
DAX per region: 3 nodes (64GB each) = 192GB → 95% cache hit rate
Effective read latency: 0.95 × 0.5ms + 0.05 × 5ms = 0.7ms
DAX cost: $10.5K/month (saves ~$700K/month vs raw DynamoDB throughput)
```

### Worked Examples

**Example 1 — Discord:** 19M concurrent. Redis for presence (<1ms), Cassandra for messages.
Separate hot/persistent state. Same pattern as ours.

**Example 2 — Slack:** Workspace-sharded MySQL. We shard by session_id (not tenant_id) to
avoid hot spots — tenant-based sharding causes big-tenant hot shards.

### Production Failure Modes

- **Redis node failure:** auto-promote replica in <5s. 5s of DynamoDB fallback (5ms vs 0.5ms).
- **DynamoDB hot partition:** use session UUID as PK, not tenant prefix.
- **Split brain:** Redis Cluster quorum — writes need majority ack.

> **Architecture-review line:** *"64-shard Redis (400GB, <0.5ms), DynamoDB Global Tables behind
> DAX (<1ms, 95% hit). Consistent hashing on session_id with 150 vnodes, <5% skew."*

### DC-Copilot Connection

`DeferredDynamoDBSaver` (single region, no cache) → Global Tables + DAX + Redis.
`FIXED_CHECKPOINT_ID` pattern scales perfectly — keep it. Add Redis as hot tier.
Read path: Redis → DAX → DynamoDB (3 tiers, fastest first).

[↑ Back to top](#contents)


---

<a id="s7"></a>
## 7 — Long-Term Memory Architecture (Core Section)

**Decision jo isse nikalti hai:** conversational AI mein "memory" sirf current chat ka nahi —
user ki preferences, past interactions, learned patterns saalon tak yaad rehne chahiye. Iske
bina har baar user naye insaan se baat kar raha hai. Memory = competitive moat.

**Asli baat:** sochiye aapka family doctor hai. Pehli visit pe sab batana padta hai — allergies,
dawayiyaan, history. Par 10 saal baad bhi woh doctor ko yaad hai "inhe penicillin se allergy
hai, diabetes hai, metformin le rahe hain." Woh kabhi nahi poochta "aapko kya allergy hai?"
Yeh **long-term memory** hai. Aaj ke chatbots mein yeh nahi hai — har conversation naya.

### 5 Memory Types (Human Brain Se Inspired)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MEMORY PYRAMID                              │
│                                                                     │
│         ┌───────────────────┐                                       │
│         │  WORKING MEMORY   │  Redis, <1ms, 400GB                   │
│         │  Current conv     │  "Abhi kya baat ho rahi hai"          │
│         │  TTL: session     │  50M sessions × 8KB                   │
│         ├───────────────────┤                                       │
│         │  SESSION MEMORY   │  DynamoDB+DAX, <5ms, 1TB              │
│         │  Days-weeks       │  "Kal kya baat hui thi"               │
│         │  TTL: 30 days     │  50M × 20KB (checkpoint)              │
│         ├───────────────────┤                                       │
│         │  EPISODIC MEMORY  │  Bigtable, <5ms, 100TB                │
│         │  Months-years     │  "6 months pehle AC repair ki thi"    │
│         │  Decay: e^(-t/S)  │  1B users × 100 episodes × 1KB       │
│         ├───────────────────┤                                       │
│         │  SEMANTIC MEMORY  │  Bigtable+VectorDB, <10ms, 25TB       │
│         │  Permanent facts  │  "User Hindi prefer karta hai"        │
│         │  No decay         │  1B × 50 facts × 0.5KB + embeddings   │
│         ├───────────────────┤                                       │
│         │  PROCEDURAL MEM   │  Graph DB, <15ms, 10TB                │
│         │  Learned workflows│  "User ko diagrams pasand hain"       │
│         │  Reinforced by use│  1B × 5 workflows × 2KB               │
│         └───────────────────┘                                       │
│                                                                     │
│  Total: ~140TB storage, <10ms avg retrieval                         │
│  Cost: ~$15K/month storage + ~$50K/month compute = ~$65K/month      │
└─────────────────────────────────────────────────────────────────────┘
```

### Memory Type Details

#### 1. Working Memory (Redis)
- **Kya:** current conversation ka state — last few messages, current intent, active context
- **Where:** Redis Cluster (same as Section 6)
- **Size:** 50M × 8KB = 400GB
- **Latency:** <1ms
- **TTL:** session end + 30 minutes
- **Example:** "User ne abhi poocha 'AC compressor kab change hua tha?' — yeh working memory mein hai"

#### 2. Session Memory (DynamoDB)
- **Kya:** full conversation history + checkpoint — multiple turns ka context
- **Where:** DynamoDB Global Tables + DAX
- **Size:** 50M × 20KB = 1TB
- **Latency:** <5ms (DAX) / <15ms (direct)
- **TTL:** 30 days
- **Example:** "Kal user ne 3 questions pooche the AC ke baare mein — yeh session memory mein hai"

#### 3. Episodic Memory (Bigtable — NEW)
- **Kya:** important events/interactions from past — summarized as "episodes"
- **Where:** Bigtable (Google's wide-column DB, or HBase open-source equivalent)
- **Row key:** `user_id#reverse_timestamp` (newest first scan)
- **Size:** 1B users × 100 episodes avg × 1KB = **100TB**
- **Latency:** <5ms (Bigtable is optimized for sequential reads on row key prefix)
- **TTL:** no hard delete — governed by forgetting curve (see below)
- **Example:** "6 months pehle user ne building 42 ke chiller repair ke baare mein poocha tha.
   Diagnosis tha: refrigerant leak at compressor valve. Fix: replaced valve + recharged."

**Bigtable schema:**
```
Row key: user_id#reverse_timestamp (e.g., "u123#99999999999-1695000000")
Column families:
  - summary: {text: "AC compressor valve replacement", importance: 0.85}
  - entities: {equipment: "Carrier CVHF910", location: "Building 42", issue: "refrigerant leak"}
  - embedding: {vector: [0.023, -0.108, ...] (1536 dims, stored as bytes)}
  - metadata: {session_id: "...", conversation_turns: 8, resolved: true}
```

**Why Bigtable (not DynamoDB for this)?**
- DynamoDB: max item 400KB, expensive at 100TB scale ($25K/month at on-demand)
- Bigtable: no item size limit, 100TB at $0.026/GB = **$2,600/month**. 10x cheaper.
- Bigtable sequential scan on row key prefix = perfect for "give me user X's last 20 episodes"

#### 4. Semantic Memory (Bigtable + Vector DB — NEW)
- **Kya:** permanent facts about user — preferences, skills, constraints
- **Where:** Bigtable (structured facts) + Vector DB (searchable embeddings)
- **Bigtable size:** 1B × 50 facts × 0.5KB = **25TB** ($650/month)
- **Vector index:** 50B fact embeddings × 6KB = **300TB** (stored on disk, indexed portion in RAM)
- **Latency:** <10ms (vector search)
- **TTL:** permanent (no decay) — only user-initiated deletion

**Fact examples:**
```json
{
  "user_id": "u123",
  "facts": [
    {"key": "preferred_language", "value": "Hindi", "confidence": 0.99, "source": "explicit"},
    {"key": "expertise_level", "value": "senior_technician", "confidence": 0.85, "source": "inferred"},
    {"key": "common_equipment", "value": ["Carrier CVHF910", "Trane XR15"], "confidence": 0.90},
    {"key": "allergy_warning", "value": "refrigerant_sensitivity", "confidence": 0.95, "critical": true}
  ]
}
```

#### 5. Procedural Memory (Graph DB — NEW)
- **Kya:** learned interaction patterns — how this user likes to work
- **Where:** Neo4j or JanusGraph (graph database)
- **Size:** 1B × 5 workflows × 2KB = **10TB**
- **Latency:** <15ms (graph traversal)
- **Example:** "User X always asks for diagnosis first, then spare parts, then time estimate —
  proactively offer this sequence. User Y prefers seeing the manual page first."

**Graph structure:**
```
(User) -[:PREFERS]-> (WorkflowPattern)
  (WorkflowPattern) -[:STEP_1]-> (Action: "show_diagnosis")
  (WorkflowPattern) -[:STEP_2]-> (Action: "list_spare_parts")
  (WorkflowPattern) -[:STEP_3]-> (Action: "estimate_time")

(User) -[:UNDERSTANDS]-> (Concept: "HVAC_terminology")
(User) -[:PREFERS_FORMAT]-> (Format: "diagrams_over_text")
```

### Memory Write Pipeline (Post-Conversation)

Har conversation end hone ke baad ek **async pipeline** chalta hai:

```
Conversation Ends
      │
      ▼
┌─────────────────┐    ┌──────────────────┐    ┌───────────────────┐
│ Episode          │    │ Fact Extractor   │    │ Pattern Detector  │
│ Summarizer (LLM) │    │ (NER + LLM)      │    │ (Rule-based +     │
│                  │    │                  │    │  statistical)     │
│ "User asked about│    │ Entities:        │    │ "User's 5th time  │
│  chiller repair. │    │  equip: CVHF910  │    │  asking diagnosis │
│  Diagnosis: valve│    │  issue: leak     │    │  before parts"    │
│  leak. Fixed."   │    │  pref: Hindi     │    │                   │
└────────┬────────┘    └────────┬─────────┘    └────────┬──────────┘
         │                      │                       │
         ▼                      ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌───────────────────┐
│ Embedding Gen   │    │ Importance       │    │ Graph Update      │
│ (text-embed-3)  │    │ Scorer           │    │ (Neo4j write)     │
│ 1536-dim vector │    │ score = recency  │    │ Reinforce or      │
│                 │    │ × relevance      │    │ create workflow    │
│                 │    │ × explicit_signal│    │ edge              │
└────────┬────────┘    └────────┬─────────┘    └───────────────────┘
         │                      │
         ▼                      ▼
┌──────────────────────────────────────────┐
│           MEMORY STORE                    │
│  Bigtable (episodes + facts)             │
│  Vector DB (embeddings)                  │
│  Graph DB (procedures)                   │
└──────────────────────────────────────────┘
```

**Cost of write pipeline:**
- LLM summarization: 7B model, ~500 tokens/conversation → 0.001 cent/conversation
- Embedding: text-embedding-3-large, ~$0.0001/conversation
- At 1.67M conversations/sec peak... but write pipeline is **async + batched**.
  Batch 100 conversations → 1 LLM call → amortized cost negligible.

### Memory Read Pipeline (Per Request)

```
New User Message arrives
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  MEMORY RETRIEVER (runs in parallel, max 7ms budget)    │
│                                                          │
│  1. Always-Include (Redis, <1ms):                        │
│     → Top-5 permanent facts (prefs, safety, critical)    │
│     → Cached in Redis per user_id, refreshed hourly      │
│                                                          │
│  2. Recency Filter (Bigtable, <3ms):                     │
│     → Last 10 episodes by reverse timestamp scan         │
│     → Single row-range scan, very fast                   │
│                                                          │
│  3. Relevance Search (Vector DB, <5ms):                  │
│     → Embed current query → kNN search → top-5 episodes  │
│     → Runs in parallel with recency filter               │
│                                                          │
│  4. Importance Threshold:                                │
│     → Merge results, deduplicate                         │
│     → Filter: keep score > 0.3                           │
│     → Rank by: 0.4×relevance + 0.3×recency + 0.3×importance │
│                                                          │
│  5. Compress (local, <1ms):                              │
│     → Take top-10 memories, summarize into ~500 tokens   │
│     → Use template: "[MEMORY] user prefers Hindi.        │
│       6 months ago: chiller valve leak diagnosed..."      │
│                                                          │
│  6. Inject into System Prompt                            │
│     → Before user message, after system instructions     │
└─────────────────────────────────────────────────────────┘
```

### Forgetting Curve (Ebbinghaus — Memory Decay)

```
Retention = e^(-t / S)

Where:
  t = time since last access (days)
  S = strength (starts at 1, increases with each recall)

Recall schedule:
  First recall: S = 1.5
  Second recall: S = 3.0
  Third recall: S = 7.0
  Fourth recall: S = 21.0
  Fifth recall: S = ∞ (permanent)

Example:
  Memory created Day 0, S=1.0
  Day 1: retention = e^(-1/1) = 0.37 (37%) — fading fast
  Day 7: retention = e^(-7/1) = 0.001 (0.1%) — basically gone

  BUT if recalled on Day 1: S becomes 1.5
  Day 7: retention = e^(-6/1.5) = 0.018 (1.8%) — still fading
  
  If recalled again Day 3: S becomes 3.0
  Day 30: retention = e^(-27/3) = 0.0001 — gone
  
  If recalled 5+ times: S = ∞ → retention = 1.0 forever
  "User prefers Hindi" — recalled every conversation → permanent
```

**Why forgetting matters at scale:**
- 1B users × 100 episodes = 100TB. Without forgetting, grows unbounded.
- With forgetting: ~30% of memories decay to 0 within 30 days → auto-cleanup job
  removes them → storage stays ~100TB steady state.

### Privacy & GDPR

- **Per-user encryption:** AES-256, key per user, stored in KMS
- **Right to forget:** user says "delete my data" → purge all 5 tiers for that user_id
  → Bigtable: delete all rows with user_id prefix (~1ms scan + batch delete)
  → Vector DB: delete embeddings with user_id filter
  → Graph DB: delete user node and all edges
- **Tenant isolation:** memories NEVER cross tenants. Even in shared Bigtable, row key
  starts with tenant_id.
- **Memory consent:** user can opt-out of long-term memory (only working + session)
- **Audit log:** every memory access logged for compliance

### Cost Summary

| Component | Storage | Monthly Cost | Notes |
|-----------|---------|-------------|-------|
| Bigtable (episodes) | 100TB | $2,600 | $0.026/GB/month |
| Bigtable (facts) | 25TB | $650 | Same rate |
| Vector DB (Milvus) | 300TB disk, 30TB RAM | $100K | Managed cluster |
| Graph DB (Neo4j) | 10TB | $25K | Enterprise license |
| Write pipeline (LLM) | — | $5K | 7B model, batched |
| Redis (hot facts) | 50GB | $3K | Cached top facts |
| **Total Memory Layer** | **~435TB** | **~$136K/month** | **$0.0016/user/year** |

### Worked Examples

**Example 1 — Google Assistant "Morning Flights" Memory:**
User books flights 15 times over 2 years, always morning. Semantic memory extracts fact:
`{preferred_flight_time: "morning", confidence: 0.95}`. Next time user says "book a flight
to Delhi" → assistant pre-filters morning flights, asks "morning flight jaise hamesha?"
User never explicitly said "I prefer morning" — system inferred from 15 episodes.
S (strength) after 15 recalls = ∞ → permanent fact.

**Example 2 — Healthcare Chatbot (Multi-Tier Memory in Action):**
Patient: diabetic, takes metformin, allergic to penicillin, last visit 3 months ago.
- **Semantic (permanent):** `{condition: "diabetes", medication: "metformin", allergy: "penicillin"}`
  → always injected into prompt. If doctor prescribes penicillin, AI flags immediately.
- **Episodic (decaying):** "3 months ago: routine checkup, HbA1c was 7.2, doctor recommended
  more exercise" → relevant if patient asks about progress.
- **Procedural:** "Patient understands medical jargon, prefers detailed explanations with numbers,
  asks follow-up questions about side effects" → AI adjusts response style.

### Production Failure Modes

- **Memory poisoning:** bad conversation → wrong fact extracted → becomes permanent.
  "User said 'my AC uses R-22 refrigerant' but meant neighbor's AC."
  **Fix:** confidence threshold (>0.85 for semantic memory). Low-confidence → store as episodic
  (decaying) not semantic (permanent). User can manually correct via "that's not right" trigger.
- **Privacy leak:** user A's memory leaks into user B's retrieval due to vector DB bug.
  **Fix:** mandatory tenant_id filter on EVERY vector search query. Post-retrieval assertion
  (check user_id on every returned memory). Same pattern as DC-Copilot's OpenSearch TENANT_LEAK check.
- **Memory bloat:** power user with 10,000 episodes → retrieval slow, prompt too long.
  **Fix:** importance-based pruning. Keep top-500 episodes by importance score. Archive rest
  to cold storage (S3). Retrieve from archive only if explicitly asked.

> **Architecture-review line:** *"Five-tier memory: Redis working (400GB, <1ms), DynamoDB
> session (1TB, <5ms), Bigtable episodic (100TB, <5ms), Bigtable+Vector semantic (25TB, <10ms),
> Neo4j procedural (10TB, <15ms). Ebbinghaus forgetting curve with spaced repetition keeps
> storage at steady-state 100TB. Per-user cost: $0.0016/year. Tenant isolation enforced at
> every tier with post-retrieval assertion."*

### DC-Copilot Connection

DC-Copilot aaj:
- `SummarizationNodeWrapper` → langmem, 512-token running summary. Session-only.
- No episodic/semantic/procedural memory. Har naya session = blank slate.
- Technician ke past interactions yaad nahi rehte.

Google-scale pe:
- Keep langmem for within-session summarization (it works well)
- Add post-conversation write pipeline → extract episodes + facts
- Per-technician profile in Bigtable: skill level, common equipment, language preference
- Equipment memory graph in Neo4j: "Is building ke saare ACs mein compressor fail pattern"
  (aaj yeh Snowflake mein SQL query hai, graph mein faster + relationship-aware)
- Memory injection in `LLMInvokeNode`: before building prompt, retrieve top-10 memories
  → inject as `[TECHNICIAN MEMORY]` block in system prompt

[↑ Back to top](#contents)

---

<a id="s8"></a>
## 8 — Vector Search at Billion Scale

**Decision jo isse nikalti hai:** single-cluster OpenSearch (current) 10B vectors handle nahi
kar sakta — memory aur throughput dono toot jaayenge. Distributed vector DB chahiye with smart
sharding aur compressed indexes.

**Asli baat:** sochiye ek library mein 10 billion pages hain. Aapko ek question poocha aur 5
sabse relevant pages chahiye 10ms mein. Normal search (exact match) se nahi milega — meanings se
match karna hai. Yeh **vector similarity search** hai. 10B pages ki library ek rack mein nahi
aayegi — 200 racks (shards) mein todna padega.

### Current Approach Breaks at Scale

DC-Copilot aaj: 2 OpenSearch domains, HNSW index, ~millions of vectors.

| Aspect | Current (OpenSearch) | At 10B vectors |
|--------|---------------------|---------------|
| Index size | ~50GB | **60TB** |
| RAM needed (HNSW) | ~50GB | **60TB RAM** (impossible!) |
| Query latency | <20ms | **200ms+** (disk thrashing) |
| Single cluster | works | **breaks** (no horizontal scale) |

**HNSW (Hierarchical Navigable Small World)** = best recall, but stores entire graph in RAM.
At 60TB, you'd need ~750 machines with 80GB RAM each just for the index. Unaffordable.

### Solution: IVF-PQ + Distributed Milvus

**IVF-PQ (Inverted File Index with Product Quantization):**
- **IVF:** divides vectors into clusters (like chapters in a book). Search only relevant clusters.
- **PQ:** compresses each 1536-dim vector from 6KB → 192 bytes (32x compression).
  Splits vector into 48 sub-vectors of 32 dims each, quantizes each to 1 byte.

| Algorithm | RAM per 10B vectors | Recall@10 | Latency | Best For |
|-----------|-------------------|-----------|---------|----------|
| HNSW (brute) | 60TB | 99.5% | <5ms | Small scale (<100M) |
| IVF-PQ | **1.8TB** | 95-97% | <10ms | Billion scale ✅ |
| ScaNN (Google) | **2TB** | 96-98% | <8ms | Google infra ✅ |
| DiskANN | **200GB** (SSD-backed) | 95% | <15ms | Ultra-cheap, slightly slower |

**IVF-PQ math:**
```
10B vectors × 1536 dims × 4 bytes = 60TB (raw)
After PQ compression: 10B × 192 bytes = 1.8TB (in RAM)
After IVF partitioning: only search ~1% of vectors per query
Effective search space: 100M vectors → 10ms
```

### Milvus Cluster Architecture

```
┌───────────────────────────────────────────────────┐
│                MILVUS CLUSTER                      │
│                                                    │
│  Query Coordinator → routes query to right shards  │
│                                                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐             │
│  │ Shard 1 │ │ Shard 2 │ │...200   │  200 shards │
│  │ 50M vec │ │ 50M vec │ │ 50M vec │  50M each   │
│  │ 9GB RAM │ │ 9GB RAM │ │ 9GB RAM │  IVF-PQ     │
│  └─────────┘ └─────────┘ └─────────┘             │
│                                                    │
│  Query Nodes: 50 (128GB RAM each)                  │
│  Each node hosts ~4 shards in memory               │
│  Total RAM: 50 × 128GB = 6.4TB (1.8TB index +     │
│             headroom for query processing)          │
│                                                    │
│  Data Nodes: 100 (for raw vector storage on disk)  │
│  Object Storage (S3): 60TB raw vectors (backup)    │
│                                                    │
│  Replication: 3 replicas → 600 shard-replicas      │
│  Throughput: ~50K queries/sec at <10ms p99          │
│  Index build: ~4 hours distributed (100 nodes)     │
└───────────────────────────────────────────────────┘
```

### Sharding Strategy

**Shard by tenant_id** (not random hash):
- All vectors for a tenant on same shard → single-shard query (fast)
- Big tenants (>50M vectors) get dedicated shards
- Small tenants share shards (bin-packing)

**Why not random hash:** cross-shard scatter-gather for every query = high latency.
Tenant-based = single-shard hit for 95% of queries.

### Cost

| Component | Spec | Monthly Cost |
|-----------|------|-------------|
| Query Nodes (50×r5.4xlarge) | 128GB RAM, 16 vCPU | $73K |
| Data Nodes (100×m5.2xlarge) | 32GB RAM, 500GB SSD | $44K |
| S3 (backup) | 60TB | $1.4K |
| **Total** | | **~$118K/month** |

### Worked Examples

**Example 1 — Spotify Recommendation (1B+ Tracks):**
Spotify stores track embeddings for 100M+ songs. Started with Annoy (approximate NN library),
migrated to Vespa (distributed search) when scale hit billions of user-track interactions.
IVF-PQ with 512 clusters. Search: 10ms for top-30 recommendations.
**Lesson:** start simple (Annoy/HNSW), migrate when you hit memory wall.

**Example 2 — Pinterest Visual Search (Billions of Pins):**
Pinterest: 300B+ pin embeddings. Uses custom IVF-PQ with 200+ shards.
Query: user uploads image → embed → search → return visually similar pins in <50ms.
They run on custom hardware with NVMe SSDs for disk-based search.
**Lesson:** at extreme scale, disk-based indexes (DiskANN) become attractive — trade 5ms
latency for 10x RAM savings.

### Production Failure Modes

- **Shard imbalance:** one tenant uploads 500M documents → that shard 10x bigger than others.
  **Fix:** auto-split large shards. Monitor shard size, trigger rebalance at 2x median.
- **Stale index:** new documents uploaded but not yet indexed. Embedding pipeline lag.
  **Fix:** near-real-time indexing with Milvus's streaming insert. Trade-off: index quality
  slightly worse during high-ingestion periods.
- **Recall degradation:** IVF-PQ recall drops from 97% to 90% as data distribution shifts.
  **Fix:** periodic re-training of PQ codebook (monthly) and IVF centroids (weekly).

> **Architecture-review line:** *"10B vectors on IVF-PQ compress from 60TB to 1.8TB in-memory
> across 200 Milvus shards (50M vectors each). Tenant-based sharding gives single-shard queries
> for 95% of traffic. 50 query nodes at 128GB RAM each, <10ms p99, $118K/month."*

### DC-Copilot Connection

DC-Copilot aaj: 2 OpenSearch managed domains, HNSW, single region. `asset_embeddings` index
and `workorder_embeddings` index. Works fine at current scale.

Google-scale pe:
- Merge into single Milvus cluster with collection-per-type
- `OpenSearchServerlessClient` → `MilvusClient` (API similar, kNN syntax different)
- `context_retrieve()` stays same — change underlying search call
- Tenant isolation: `ACCOUNTID` filter → Milvus partition key on tenant_id (more efficient)
- `expanded_k=15, k=8` retrieval pattern stays (good quality filtering)

[↑ Back to top](#contents)

---

<a id="s9"></a>
## 9 — Multi-Layer Caching

**Decision jo isse nikalti hai:** bina caching ke 1.67M msg/sec Snowflake/DB pe hit karoge →
instant meltdown. 3-layer cache se 72% requests DB tak pahunchte hi nahi.

**Asli baat:** socho office mein kaam kar rahe ho. Notes chahiye:
- **L1 (desk pe):** apne desk pe pade hain → 1 second mein mil gaye. Par sirf apne notes.
- **L2 (shared shelf):** team ki shared bookshelf → 30 seconds mein mil gaye. Sabke shared.
- **L3 (library):** company library → 10 minutes. Sab kuch hai, par slow.

Software mein: L1 = in-process memory, L2 = Redis, L3 = Snowflake/DB.

### 3-Layer Cache Architecture

| Layer | Where | Size | TTL | Latency | Hit Rate | What's Cached |
|-------|-------|------|-----|---------|----------|--------------|
| L1 | In-process (Python dict/LRU) | 2GB per pod | 5 min | <0.1ms | ~30% | Same-pod, same-asset repeat queries |
| L2 | Redis Cluster | 200GB (32 shards) | 1 hour | <1ms | ~60% (of L1 misses) | Cross-pod, any-asset cached data |
| L3 | Snowflake | ∞ | Real-time | 50-2000ms | 100% | Source of truth |

**Combined hit rate:** `1 - (1-0.30) × (1-0.60) = 72%`
Only 28% of requests reach Snowflake.

**With DC-Copilot's chatInitialize pattern** (Snowflake only at session start):
- New sessions/sec: 50M concurrent ÷ avg 10-min session = ~83K new sessions/sec
- With 72% cache hit: only **23K Snowflake queries/sec** → manageable

### Cache Invalidation Strategies

| Strategy | How | Pros | Cons | Use When |
|----------|-----|------|------|----------|
| **TTL-based** | Cache expires after fixed time | Simple, no coordination | Stale data for TTL duration | Maintenance history (staleness OK) |
| **Event-driven** | DB change → invalidate cache | Always fresh | Complex pipeline needed | Critical data (user profile) |
| **Write-through** | Write to cache + DB together | Strong consistency | Slower writes, complexity | Session state |
| **Cache-aside** | App checks cache, misses go to DB | Simple, lazy population | First request slow | Most common pattern |

**DC-Copilot recommendation:** TTL-based for maintenance history (changes rarely, 1-hour TTL fine).
Event-driven for user preferences (if user changes language, should reflect immediately).

### Thundering Herd Problem

**Scenario:** popular asset (e.g., common AC model in 1000 buildings). Cache entry expires.
1,000 pods simultaneously get cache miss → 1,000 identical Snowflake queries.

```
Normal: 1 query → cache → done
Thundering herd: 1000 queries → cache miss → 1000 DB queries → DB overload
```

**Solutions:**

1. **Request coalescing (singleflight):**
   ```python
   # First request acquires lock, fetches from DB
   # Other 999 requests wait for first one's result
   # Only 1 Snowflake query instead of 1000
   
   async with cache.lock(key):
       result = await cache.get(key)
       if result is None:
           result = await snowflake.query(key)  # Only runs once
           await cache.set(key, result, ttl=3600)
   ```

2. **Probabilistic early expiration:**
   ```python
   # Instead of all keys expiring at exactly TTL:
   # Each key expires at TTL ± random(0, 60 seconds)
   # Distributes thundering herd over 60-second window
   
   actual_ttl = base_ttl + random.uniform(-60, 60)
   ```

3. **Background refresh:** 80% of TTL pe background thread silently refreshes.
   Cache never actually expires → zero thundering herd.

### Cost

| Component | Spec | Monthly |
|-----------|------|---------|
| L1 (in-process) | Free (pod memory) | $0 |
| L2 (Redis 200GB) | ElastiCache, 32 shards | $12K |
| L3 (Snowflake) | Reduced queries (-72%) | Saves ~$50K vs uncached |
| **Net savings** | | **~$38K/month saved** |

### Worked Examples

**Example 1 — Facebook TAO (Trillion Reads/Day):**
Facebook TAO: distributed cache for social graph. 1 trillion reads/day. Multi-layer:
L1 (follower cache, per-server) → L2 (TAO leader, per-region) → L3 (MySQL shard).
Hit rate: 99.8% — only 0.2% reaches MySQL. They invented "read-your-writes" consistency —
user always sees their own writes immediately, others may see stale data briefly.
**Lesson:** 99%+ hit rate possible with smart cache hierarchy.

**Example 2 — Netflix EVCache (10TB+ Redis):**
Netflix: 30M+ ops/sec across 10TB+ distributed Redis. They built EVCache on top of
memcached — auto-replication across AZs, consistent hashing, hot-key detection.
Hot keys (trending shows) replicated to all cache nodes to avoid single-point bottleneck.
**Lesson:** identify hot keys proactively. In our case: popular equipment models, common
failure patterns → pre-warm these in L2 cache.

### Production Failure Modes

- **Cache poisoning:** wrong data gets cached, serves stale/incorrect results for TTL duration.
  **Fix:** version tag in cache key. When schema changes → new version → old cache ignored.
- **Redis cluster down:** 200GB cache gone, all traffic hits Snowflake → DB overload.
  **Fix:** circuit breaker on Snowflake. If query rate >50K/sec → return degraded response
  with cached-from-last-known data (stale better than error).
- **Memory leak in L1:** Python dict grows unbounded, pod OOM-killed.
  **Fix:** `functools.lru_cache(maxsize=50000)` or `cachetools.TTLCache` with hard limit.

> **Architecture-review line:** *"Three-layer cache: L1 in-process (2GB, <0.1ms, 30% hit),
> L2 Redis (200GB, <1ms, 60% hit), L3 Snowflake (source of truth). Combined 72% hit rate
> means only 23K Snowflake queries/sec from 83K new sessions/sec. Request coalescing prevents
> thundering herd on popular assets."*

### DC-Copilot Connection

DC-Copilot aaj: **zero caching.** `SnowflakeClient` directly queries on every chatInitialize.
Pool of 3-100 connections, but no result cache.

Google-scale pe:
- Add `cachetools.TTLCache` in `DataAccessLayer` for L1
- Add Redis layer in `CopilotDependencies` for L2
- `context_precompute.py` checks L2 before Snowflake
- `SnowflakeClient` pool stays as L3

[↑ Back to top](#contents)

---

<a id="s10"></a>
## 10 — Streaming & Real-time Delivery

**Decision jo isse nikalti hai:** 50M concurrent connections = 50M open sockets. SSE (current)
se itna scale nahi hoga — WebSocket + gRPC backend chahiye. Token batching se network calls
3-5x kam.

**Asli baat:** socho stadium mein 50,000 log commentary sun rahe hain. Har ek ko apna earpiece
chahiye (connection). Agar har word alag message mein bhejo → network overloaded. Battar:
3-4 words ek saath bhejo, 50ms ke gap mein → sunne wale ko pata bhi nahi chalega par network
traffic 4x kam ho gaya.

### SSE vs WebSocket vs gRPC Streaming

| Feature | SSE (Current) | WebSocket | gRPC Streaming |
|---------|--------------|-----------|---------------|
| Direction | Server → Client only | Bidirectional | Bidirectional |
| Protocol | HTTP/1.1 | HTTP upgrade | HTTP/2 |
| Memory/conn | ~50KB | ~30KB | ~10KB |
| 50M conn RAM | **2.5TB** | **1.5TB** | **500GB** |
| Multiplexing | No (1 conn = 1 stream) | No | Yes (100 streams/conn) |
| Browser support | Yes | Yes | Via gRPC-Web proxy |
| Best for | Simple server push | Interactive apps | Backend-to-backend |

**Architecture decision:**
- **Client ↔ Gateway:** WebSocket (browser compatible, bidirectional for typing indicators)
- **Gateway ↔ Backend:** gRPC streaming (binary, efficient, multiplexed)
- **Backend ↔ LLM:** gRPC streaming (same network, maximum efficiency)

### Connection Management at 50M

```
Client (50M browsers/apps)
    │ WebSocket
    ▼
┌─────────────────────────────────────────┐
│  ENVOY GATEWAY LAYER                     │
│  500 nodes × 100K connections = 50M      │
│  Per node: 128GB RAM, 32 cores (C++)     │
│  TLS termination at this layer           │
│  Rate limiting: 10 msg/sec per user      │
│  Connection draining: 30s graceful close │
└────────────────┬────────────────────────┘
                 │ gRPC (multiplexed)
                 ▼
┌─────────────────────────────────────────┐
│  API PODS (10,000)                       │
│  Each pod: 5,000 gRPC streams            │
│  Async handlers (Python asyncio/uvloop)  │
│  No TLS here (internal network, mTLS     │
│  handled by Istio service mesh)          │
└────────────────┬────────────────────────┘
                 │ gRPC
                 ▼
┌─────────────────────────────────────────┐
│  vLLM GPU CLUSTER                        │
│  Token generation → gRPC stream back     │
│  Continuous batching across streams      │
└─────────────────────────────────────────┘
```

### Token Batching (Network Optimization)

LLM generates 1 token every 15-30ms. Each token = 1 network frame.

**Without batching:** 1.67M msg/sec × 200 tokens × 1 frame/token = **334M frames/sec** network-wide

**With 50ms batch window:** collect 3-5 tokens, send as 1 frame.
334M ÷ 4 = **83.5M frames/sec** → 4x reduction.

User perception: imperceptible. Human reading speed ~250 words/min = 1 word/240ms.
50ms batching < reading speed. User sees smooth streaming.

```python
# Token batching pseudocode
buffer = []
last_flush = time.monotonic()

async for token in llm.stream():
    buffer.append(token)
    now = time.monotonic()
    if len(buffer) >= 5 or (now - last_flush) >= 0.050:
        await websocket.send("".join(buffer))
        buffer.clear()
        last_flush = now
```

### Backpressure (Slow Client Handling)

Problem: mobile user on 3G — can't read tokens as fast as LLM generates them.
Without backpressure → server buffer grows → OOM.

**Fix:** per-connection buffer limit (1KB). If full → drop oldest tokens, mark gap.
Client reconnects with `last_token_id` → server replays from checkpoint.

### Cost

| Component | Count | Monthly |
|-----------|-------|---------|
| Envoy nodes (c5.9xlarge) | 500 | $220K |
| Network (40 Gbps out) | — | $50K |
| **Total streaming** | | **$270K/month** |

### Worked Examples

**Example 1 — Twitch (30M Concurrent Viewers):**
Twitch streams live video to 30M concurrent. Each viewer = persistent connection.
They use custom edge servers (C++), RTMP ingest, HLS delivery. Video is 1000x heavier
than text tokens, so their infra is massive. Our text streaming is trivially simple
by comparison — but connection management patterns are same (edge termination,
regional routing, graceful degradation to lower quality).

**Example 2 — WhatsApp (2B Users, E2E Encrypted):**
WhatsApp maintains 2B registered connections (persistent XMPP-like protocol).
Not all concurrent — but 100M+ active at peak. Custom protocol optimized for
mobile (minimal overhead, binary framing). Battery optimization: heartbeat
interval adjusts based on network type (WiFi: 1 min, 4G: 5 min, 3G: 15 min).
**Lesson:** connection keepalive strategy matters for mobile users.

### Production Failure Modes

- **Envoy node crash:** 100K connections dropped instantly. Users see disconnect.
  **Fix:** client auto-reconnect with exponential backoff. Load balancer detects
  node death in <5s, stops routing new connections.
- **WebSocket hijacking:** attacker opens 100K connections from one IP, DoS.
  **Fix:** per-IP connection limit (100 max), CAPTCHA after 50 rapid connects.
- **Token ordering:** network reorder causes tokens to arrive out of sequence.
  **Fix:** sequence number on each token frame. Client reorders in 100ms buffer.

> **Architecture-review line:** *"500 Envoy nodes terminate 50M WebSocket connections at
> 100K/node, translating to gRPC streams to 10K API pods. Token batching at 50ms windows
> reduces network frames 4x with imperceptible impact. Per-connection 1KB buffer with
> backpressure prevents slow-client OOM."*

### DC-Copilot Connection

DC-Copilot aaj: FastAPI `StreamingResponse` with SSE. `event_generator()` yields
`StreamMessage` objects (start/content/done/error). Works for ~1K concurrent.

Google-scale pe:
- SSE → WebSocket (client-facing) + gRPC (backend)
- `LLMInvokeNode.get_stream_writer()` → gRPC stream writer
- `copilot_api_response_stream()` → gRPC server streaming handler
- Token batching layer between LLM output and client delivery
- LangGraph `stream_mode="custom"` stays — it's transport-agnostic

[↑ Back to top](#contents)

---

<a id="s11"></a>
## 11 — Full Architecture + DC-Copilot Enhancement Map

### Architecture Diagram: Global View

```
╔══════════════════════════════════════════════════════════════════════╗
║                        GLOBAL EDGE LAYER                            ║
║  Anycast DNS → 300+ CDN Edge PoPs → TLS Termination                ║
║  50M users, <2ms routing                                            ║
╚═══════════════════════════════╦══════════════════════════════════════╝
                                ║
        ┌───────────────────────╬───────────────────────┐
        ▼                       ▼                       ▼
╔═══════════════╗   ╔═══════════════╗   ╔═══════════════╗
║   US-EAST-1   ║   ║   EU-WEST-1   ║   ║   AP-SOUTH-1  ║  ×8 regions
║   8M users    ║   ║   7M users    ║   ║   10M users   ║
║               ║   ║               ║   ║               ║
║ ┌───────────┐ ║   ║ ┌───────────┐ ║   ║ ┌───────────┐ ║
║ │ 80 Envoy  │ ║   ║ │ 70 Envoy  │ ║   ║ │100 Envoy  │ ║
║ │ 100K/node │ ║   ║ │ 100K/node │ ║   ║ │ 100K/node │ ║
║ └─────┬─────┘ ║   ║ └─────┬─────┘ ║   ║ └─────┬─────┘ ║
║       │gRPC   ║   ║       │       ║   ║       │       ║
║ ┌─────▼─────┐ ║   ║ ┌───────────┐ ║   ║ ┌───────────┐ ║
║ │1,600 Pods │ ║   ║ │1,400 Pods │ ║   ║ │2,000 Pods │ ║
║ │5K req/pod │ ║   ║ │           │ ║   ║ │           │ ║
║ └─────┬─────┘ ║   ║ └─────┬─────┘ ║   ║ └─────┬─────┘ ║
║       │       ║   ║       │       ║   ║       │       ║
║ ┌─────▼─────┐ ║   ║ ┌───────────┐ ║   ║ ┌───────────┐ ║
║ │ 528 A100  │ ║   ║ │ 462 A100  │ ║   ║ │ 660 A100  │ ║
║ │ vLLM      │ ║   ║ │ vLLM      │ ║   ║ │ vLLM      │ ║
║ │ 7B/13B/70B│ ║   ║ │           │ ║   ║ │           │ ║
║ └───────────┘ ║   ║ └───────────┘ ║   ║ └───────────┘ ║
╚═══════╦═══════╝   ╚═══════╦═══════╝   ╚═══════╦═══════╝
        ║                   ║                   ║
        ╚═══════════════════╬═══════════════════╝
                            ║
╔═══════════════════════════╩══════════════════════════════╗
║                     DATA LAYER (per region)              ║
║                                                          ║
║  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ ║
║  │ Redis Cluster│  │ DynamoDB     │  │ Milvus Cluster │ ║
║  │ 50GB/region  │  │ Global Table │  │ 25 shards/     │ ║
║  │ 8 shards     │  │ + DAX (3     │  │ region         │ ║
║  │ <0.5ms read  │  │   nodes)     │  │ <10ms search   │ ║
║  └──────────────┘  │ <1ms read    │  └────────────────┘ ║
║                    └──────────────┘                      ║
║  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ ║
║  │ Bigtable     │  │ Neo4j        │  │ Snowflake      │ ║
║  │ 12.5TB/region│  │ (Graph DB)   │  │ (L3 Cache)     │ ║
║  │ LTM episodes │  │ Procedures   │  │ Source of truth │ ║
║  │ + facts      │  │ <15ms        │  │ via L1/L2 cache│ ║
║  └──────────────┘  └──────────────┘  └────────────────┘ ║
╚══════════════════════════════════════════════════════════╝
```

### Request Flow with Latency

```
User types "AC ka compressor kab change hua tha?"
  │
  │ [2ms] Anycast DNS → nearest Edge PoP
  ▼
Edge PoP (TLS termination, WebSocket upgrade already done)
  │
  │ [3ms] Edge → Regional Load Balancer
  ▼
Regional LB → API Pod (gRPC)
  │
  │ [<1ms] DAX cache → load session state (checkpoint)
  │ [2ms] DistilBERT → intent: "maintenance_history" (complex)
  │
  │ [in parallel, max 7ms]:
  │   ├─ [<1ms] Redis → hot facts ("user prefers Hindi")
  │   ├─ [3ms] Bigtable → last 10 episodes for this user
  │   └─ [5ms] Milvus → kNN search → top-5 relevant docs
  │
  │ [<1ms] Merge memories → compress to 500 tokens
  │ [<1ms] Build prompt (system + memory + context + user message)
  ▼
vLLM GPU Cluster
  │
  │ [~15ms] Speculative decode: draft model (7B) generates 5 tokens
  │ [~20ms] Target model (70B) verifies batch → 4/5 accepted
  │ [~60ms] Generate remaining tokens until first word complete
  │ TOTAL TTFT: ~95ms
  ▼
gRPC stream → Envoy → WebSocket → User sees: "Aapke"
  │
  │ [7ms] streaming delivery
  ▼
User sees first token at ~125ms (well within 150ms SLO)
  │
  │ [next 3-5 seconds] tokens stream at 30ms/token
  ▼
Full response: "Aapke AC ka compressor 6 mahine pehle change hua tha,
Building 42 mein. Us waqt diagnosis tha refrigerant leak at compressor
valve. Previous technician Raj ne replace kiya tha estimated 2.5 ghante
mein. Kya aap usi issue ke baare mein pooch rahe hain?"
```

### DC-Copilot: Complete Enhancement Map

| # | Component | DC-Copilot Today | Google-Scale Enhanced | Impact |
|---|-----------|-----------------|---------------------|--------|
| 1 | **API Protocol** | REST + SSE (FastAPI) | WebSocket + gRPC | -10ms, 50M conn support |
| 2 | **Load Balancing** | ALB, single region | Anycast, 8 regions, 500 Envoy | Global, <5ms routing |
| 3 | **Compute** | ECS tasks (~5 instances) | K8s 10K pods, HPA custom metrics | 50M concurrent |
| 4 | **LLM** | Azure OpenAI API (GPT-4) | Self-hosted vLLM (7B/13B/70B) | -400ms, 73% GPU savings |
| 5 | **Intent Classify** | LLM call (200ms) | DistilBERT local (2ms) | -198ms latency |
| 6 | **State (hot)** | None (direct DynamoDB) | Redis 400GB, 64 shards | <0.5ms reads |
| 7 | **State (warm)** | DynamoDB single region | Global Tables + DAX, 8 regions | <1ms, global access |
| 8 | **Checkpointing** | DeferredDynamoDBSaver | Same pattern + Redis hot tier | Keep FIXED_CHECKPOINT_ID ✅ |
| 9 | **Vector Search** | 2 OpenSearch domains | Milvus 200 shards, IVF-PQ | 10B vectors, <10ms |
| 10 | **Caching** | None | L1(2GB) + L2(Redis 200GB) + L3(SF) | 72% cache hit |
| 11 | **Memory** | langmem 512-token summary | 5-tier: working→session→episodic→semantic→procedural | Years of memory |
| 12 | **Summarization** | SummarizationSubgraph (langmem) | Same + post-conv memory extraction | Keep langmem ✅ |
| 13 | **Streaming** | FastAPI SSE | WebSocket + gRPC + token batching | 4x less network, 50M scale |
| 14 | **Tenant Isolation** | 3-layer (key scope + filter + assertion) | Same + memory tier isolation | Keep all 3 layers ✅ |

### What to KEEP from DC-Copilot (Already Good)

1. **Two-phase design (chatInitialize + chat)** — Snowflake only once. Perfect pattern.
2. **DeferredDynamoDBSaver + FIXED_CHECKPOINT_ID** — 1 write/request, no history bloat.
3. **Tenant isolation (3-layer)** — session key scoping + filter + assertion.
4. **LangGraph state machine** — node-based flow with parallel fan-out.
5. **langmem summarization** — running summary with RemoveMessage for checkpoint trimming.
6. **Source mode routing** — asset/location/site/meter/unknown context strategies.

### Cost Summary

| Layer | Monthly Cost | % of Total |
|-------|-------------|-----------|
| GPU Inference (1,200 A100s) | $2.2M | 61% |
| API Compute (10K pods + warm pool) | $1.55M | 15% (*see note) |
| Streaming (500 Envoy) | $270K | 7.5% |
| State (Redis + DynamoDB + DAX) | $195K | 5.4% |
| Vector DB (Milvus) | $118K | 3.3% |
| Memory (Bigtable + Neo4j + pipeline) | $136K | 3.8% |
| Caching (L2 Redis) | $12K | 0.3% |
| Network | $50K | 1.4% |
| **Total** | **~$3.6M/month = $43M/year** | |

> *Note: with model routing, GPU cost dropped from $6M to $2.2M — this is the single biggest cost optimization.*

**Per-user economics:** $43M ÷ 1B users = **$0.043/user/year = ₹3.6/user/year**

### Interview Cheat Sheet

**"150ms latency kaise?"**
1. Self-hosted LLM (saves 200ms+ vs API)
2. DistilBERT for intent (2ms vs 200ms LLM call) — **biggest single win**
3. Model routing (simple→7B at 20ms, complex→70B at 100ms)
4. Speculative decoding (2.5x faster generation)
5. DAX/Redis state cache (<1ms vs 15ms DynamoDB)
6. gRPC + HTTP/2 (binary, multiplexed, connection reuse)
7. Predictive pre-fetch (context ready before user sends)
8. **Clarify: 150ms = TTFT, stream the rest** — this is the correct framing

**"50M concurrent kaise?"**
1. 8-region deployment, Anycast routing (6.25M/region)
2. 500 Envoy nodes (100K conn/node) for WebSocket termination
3. K8s HPA on custom metrics (connections, P99 TTFT, queue depth)
4. 500-pod warm pool for instant surge capacity
5. Redis 64-shard cluster for hot state (400GB, <0.5ms)
6. DynamoDB Global Tables for cross-region state
7. Graceful degradation (3 levels: soft→medium→hard)

**"Long-term memory kaise?"**
1. 5-tier memory (working→session→episodic→semantic→procedural)
2. Post-conversation extraction pipeline (LLM summarize + NER fact extract)
3. Ebbinghaus forgetting curve (e^(-t/S), strength grows with recall)
4. Retrieval: recency × relevance × importance scoring, top-10 memories
5. Bigtable for episodes (100TB, $2.6K/month), Vector DB for semantic search
6. GDPR: per-user encryption, right-to-forget, tenant isolation at every tier
7. **Cost: $0.0016/user/year** for full long-term memory

**"Cost kitna?"**
- Total: **$43M/year for 1B users** ($0.043/user/year)
- GPU is 61% of cost — model routing saved 73% here
- Comparable to: WhatsApp (~$1B/year but includes media), ChatGPT (~$700M/year estimated)
- Much cheaper per-user due to model routing + no media storage

[↑ Back to top](#contents)

---

*Prepared for Google L5 ML Engineer Interview. Based on DC-Copilot production architecture analysis + industry-standard scaling patterns from Google, Meta, Discord, Spotify, Netflix.*
