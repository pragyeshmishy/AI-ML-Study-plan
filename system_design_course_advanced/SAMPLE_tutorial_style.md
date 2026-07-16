<a id="contents"></a>
# SAMPLE — Tutorial-style section (concept ground se sikhाya gaya)

> **Yeh sample kyun:** pehle A1 mein har section "explanation + decision matrix + situation/
> resolution examples" tha. Aapne kaha woh sirf situation-resolution hai, **tutorial nahi**. Toh
> yahan ek concept ko *ground se* teach kiya gaya hai — intuition se mechanics tak, ek live trace
> ke saath — aur uske *baad* decision/numbers/examples aate hain. Agar yeh format theek lage, main
> A1 ke har section ko aise rebuild karunga aur A2-A7 isi style mein banaunga.
>
> **Sample concept:** Continuous Batching & PagedAttention (vLLM ka dil).

---

## Contents

- [Part 1 — Pehle samasya ko *mehsoos* karo (intuition)](#p1)
- [Part 2 — Static batching mechanically kaise kaam karta hai (step-by-step trace)](#p2)
- [Part 3 — Continuous batching: wahi trace, behtar tareeke se](#p3)
- [Part 4 — KV cache memory ka dूsra problem (kyun PagedAttention chahiye)](#p4)
- [Part 5 — PagedAttention mechanically (OS paging se analogy + trace)](#p5)
- [Part 6 — Visual: poora flow + kaunsa tool kab (pros/cons table)](#p6)
- [Part 7 — Worked examples (situation → resolution)](#p7)
- [Part 8 — Pros/cons, kab NAHI, aur defense line](#p8)

---

<a id="p1"></a>
## Part 1 — Pehle samasya ko *mehsoos* karo (intuition)

Tutorial ka pehla kaam: aapko *problem* feel karaana, solution batane se pehle. Kyunki agar problem
clear nahi, solution rата-rataya lagega.

**Ek roz-marra ki analogy:** socho ek **bus** hai jo passengers (requests) ko le jaati hai. Bus
chalने ka kharcha (driver, diesel, route) lagbhag *fixed* hai — chahe 1 passenger ho ya 40. Toh
agar aap har passenger ke liye alag bus chalाo, aapka per-passenger kharcha bahut zyada. Behtar: ek
hi bus mein 40 passengers bithao — wahi diesel, 40 logon mein बँट gaya.

GPU bilkul yeh bus hai. Ek decode step mein GPU ko **poore model ke weights HBM se padhne padte
hain** (yeh "diesel" hai — fixed, mehenga). Chahe aap 1 request ka token banाo ya 40 ka — weights
to ek hi baar padhे jaate hain us step mein. Toh 1 request = poora diesel, 1 passenger. **40
requests ek batch mein = wahi diesel, 40 passengers.** Yahi batching ka asli idea hai (A1.1 ka
physics yaad karo: decode memory-bound hai, weight-read hi diesel hai).

**Ab asli samasya (jahan tutorial shuru hota hai):** maan lo bus mein 40 seats hain, aur aap chahte
ho bus hamesha bhari rahe. Par har passenger ka **safar alag lambाi ka hai** — koi 2 stop baad utar
jaata (chhota jawab, 20 tokens), koi 30 stop tak jaata (lamba jawab, 500 tokens). Agar aapka niyam
hai "bus tabhi wapas aayegi jab *aakhri* passenger utar jaaye", toh jo log 2 stop pe utar gaye, unki
seats 28 stop tak **khaali ghूmती rehती hain** — par aap nayे passenger nahi bitha sakte (bus "chal
rahi hai")!

Yeh exactly **static batching** ki barbaadi hai. Aur ise theek karna = **continuous batching**.
Doosri taraf, ek aur alag samasya hai — har passenger apने saath kitna *samaan* (KV cache memory)
le jaa sakta, aur woh samaan dabbe mein kaise rakha jaaye — woh **PagedAttention** solve karta hai
(Part 4-5).

Do alag samasya, do alag solution. Tutorial inhe alag-alag kholega.

**Diagram — bus analogy ↔ GPU (intuition picture):**

```
   ❌ Har request alag "bus"               ✅ Ek bus, kayी passengers
   (no batching)                           (batching)

   [Bus] → 1 passenger                      [Bus] → 🧍🧍🧍🧍🧍🧍🧍🧍
   diesel: pura, 1 banda                    diesel: pura, 8 bande
   [Bus] → 1 passenger                      ───────────────────────
   diesel: pura, 1 banda                    per-passenger diesel = 1/8
   [Bus] → 1 passenger
   diesel: pura, 1 banda            "diesel" = GPU weight-read (fixed/step)
   ───────────────────────          "passenger" = ek request ka 1 token
   per-passenger diesel = pura       Zyada passengers/bus = sasta per-token
```

**Tools/approach table — ek request vs kayी ek saath kaise chalाo:**

| Approach | Kaise | Pros | Cons | Kab use karein |
|---|---|---|---|---|
| **No batching** (1 req at a time) | Har request alag forward pass | Simplest code | GPU ~5-10% used, mehenga per-token | Sirf seekhne/debug; ek-do offline calls |
| **Static batching** | N requests ek saath, saath khatam | No-batch se behtar tput | Idle seats (Part 2), tail-wait | Predictable/uniform output lengths (rare) |
| **Continuous batching** | Har step pe finished swap-out, naya in | Best tput, GPU bhara | Scheduler complex (library karti hai) | **Default** real-time serving (variable lengths) |

> **Part 1 takeaway:** GPU = bus jiska "diesel" (weight-read) fixed hai → isliye batching. Par
> passengers ke safar ki lambाi alag → seats khaali ghoomती hain → yeh do problems (idle seats +
> samaan rakhna) hi continuous batching aur PagedAttention solve karte hain.

[↑ Back to top](#contents)

---

<a id="p2"></a>
## Part 2 — Static batching mechanically kaise kaam karta hai (step-by-step trace)

Ab intuition ko *mechanics* mein badalte hain. "Decode step" kya hota hai, exactly, aur static
batching us pe kaise chalta hai — ek live trace se.

**Pehle "decode step" ko define karo (yeh foundation hai):** LLM ek baar mein ek token banata hai.
Ek **decode step** = GPU ek forward pass chalाता hai jo batch ki *har* active request ke liye *ek*
naya token nikaalता hai. Step ke baad har request ek token lamba ho gaya. Phir agla step. Yeh
loop tab tak chalता hai jab tak request ka jawab poora na ho (ya `<end>` token aaye, ya max-tokens).

**Setup for the trace:** maan lo batch slot 4 hain (chhota rakha samajhne ko). Char requests aati
hain, har ek ka jawab alag lambाi ka hoga (jo hum *pehle se nahi jaante* — model jab `<end>` dega
tab pata chalega):

```
Request   Jawab kitne tokens ka banega (yeh aage chal ke pata chalega)
  R1            3 tokens
  R2            8 tokens
  R3            2 tokens
  R4            6 tokens
```

**Static batching ka niyam:** chaaron ko ek batch mein bithao, step-by-step sab ka token banाo, aur
batch tab khatam jab *sabse lamba* (R2, 8 tokens) poora ho. Ab trace (`#` = us step pe token bana,
`.` = request khatam ho chuki, seat khaali par *use nahi ho rahi*):

```
Step:     1  2  3  4  5  6  7  8
R1        #  #  #  .  .  .  .  .     (3 tokens, step 3 pe khatam)
R2        #  #  #  #  #  #  #  #     (8 tokens, sabse lamba)
R3        #  #  .  .  .  .  .  .     (2 tokens, step 2 pe khatam)
R4        #  #  #  #  #  #  .  .     (6 tokens, step 6 pe khatam)
```

**Ab waste ginो (yeh asli sabak hai):** har step mein 4 seats hain → 8 steps × 4 seats = **32
seat-steps** total capacity. Par actual kaam (jitne `#` hain) = 3+8+2+6 = **19 token-generations**.
Baaki 32 − 19 = **13 seat-steps khaali ghoomे** (woh saare `.`). Yaani GPU ne ~40% steps mein us
seat pe kuch nahi banaya — *par seat blocked thi, koi naya passenger nahi baith sakta tha jab tak
poora batch (R2) khatam na ho*.

**Mechanically yeh kyun hota hai:** static batching framework batch ko **ek atomic unit** maanता
hai. Saare requests ek saath shuru, ek saath khatam (aakhri ke saath). Beech mein koi seat khaali
hui toh woh khaali hi rehti — kyunki naya request add karne ke liye batch ko *rok ke* dobара banाna
padega, jo static design nahi karta. Real traffic mein jawab-lambाiyan 10× tak alag hoti hain
(20 token vs 500 token), toh yeh waste 50-70% tak chala jaata hai.

**Diagram — static batch ka "atomic block" (seats blocked till longest):**

```
  Seat ┌─────────────────────────────────────────┐
   R1  │ ███ · · · · ·  ← 3 tok, phir 5 step IDLE  │
   R2  │ ████████       ← 8 tok (longest, sabko rok│ rakha)
   R3  │ ██ · · · · · ·  ← 2 tok, phir 6 step IDLE  │
   R4  │ ██████ · ·     ← 6 tok, phir 2 step IDLE  │
       └─────────────────────────────────────────┘
        1 2 3 4 5 6 7 8  ← steps     █=kaam  ·=IDLE (blocked seat)
        ▲ batch yahan tak "locked"; naya req step-9 se pehle nahi ghus sakta
   Capacity 32 seat-steps | Kaam 19 | Waste 13 (~40%)
```

**Tools table — kaun static batching deta hai (aur kya woh isse aage gaya):**

| Tool | Default batching | Static-only? | Pros | Cons | Kab relevant |
|---|---|---|---|---|---|
| **Raw PyTorch `generate()` loop** | Manual static (ya batch=1) | Haan | Full control, simple | Idle-seat waste, khud manage | Research/offline batch jobs |
| **TF-Serving / TorchServe (classic)** | Static dynamic-batching window | Mostly | Mature, non-LLM ke liye theek | LLM variable-length pe idle waste | Classic ML (fixed-shape), LLM ke liye nahi |
| **vLLM / TGI / TRT-LLM** | **Continuous** (static se aage) | Nahi | Idle-seat problem solved | Thodा setup | LLM serving — yeh static ki problem hi hata dete |

> **Part 2 takeaway:** Static batching mein batch ek atomic block hai — sab saath shuru/khatam.
> Jaldi khatam hone wali requests apni seat *blocked* chhod jaati hain aakhri request tak. Trace
> mein 32 mein se sirf 19 seat-steps kaam aaye, 13 (~40%) waste — aur real traffic mein yeh aur bura.

[↑ Back to top](#contents)

---

<a id="p3"></a>
## Part 3 — Continuous batching: wahi trace, behtar tareeke se

Ab *exact same* 4 requests, par continuous (in-flight) batching ke niyam se — taaki aap farak khud
gin sako.

**Continuous batching ka naya niyam:** batch ko atomic block mat maano. **Har decode step ke baad
check karo:** koi request `<end>` pe pahunch gayी? Agar haan, use turant batch se nikaal do aur uski
khaali seat pe **agla waiting request bitha do** — poore batch ke khatam hone ka wait *nahi*.

**Naya setup:** wahi R1-R4 (3,8,2,6 tokens), par ab 2 aur requests queue mein wait kar rahe hain:

```
Queue mein: R5 (4 tokens banega), R6 (3 tokens banega)
```

Trace (jab koi request khatam → uski seat agle waiting request ko, *usi* ya *agle* step se):

```
Step:     1  2  3  4  5  6  7  8
Seat A    R1 R1 R1 R5 R5 R5 R5 .     (R1 step3 pe khatam → R5 step4 se shuru)
Seat B    R2 R2 R2 R2 R2 R2 R2 R2    (R2 poore 8 steps)
Seat C    R3 R3 R6 R6 R6 .  .  .     (R3 step2 pe khatam → R6 step3 se shuru)
Seat D    R4 R4 R4 R4 R4 R4 .  .     (R4 poore 6 steps)
```

**Ab dobara waste gino:** R3 ki seat (C) step 2 pe khaali hui → step 3 se R6 ne le li (sirf 0 step
waste). R1 ki seat (A) step 3 pe khaali → step 4 se R5 ne le li. Yaani jaise hi seat khaali hui,
turant bhar gayी — koi lambा "blocked but idle" gap nahi. Us 8-step window mein humne 4 ke bajaye
**6 requests** nikaal diye (R1-R6), wahi GPU, wahi steps.

**Throughput ka farak, numbers mein:** static run ne 8 steps mein 4 requests + 19 tokens diye.
Continuous run ne 8 steps mein 6 requests + (3+8+2+6+4+3)=26 tokens diye — **~37% zyada kaam, same
hardware, same time.** Real traffic (zyada variable lengths, badा batch jaise 64-256 slots) pe yeh
farak **2-4× throughput** ban jaata hai. Aur yeh poora fayda *sirf scheduling badalne* se aaya —
model, GPU, kuch nahi badla.

**Ek sookshma baat (jo seniority dikhati hai):** naya request jo beech mein add hota hai (R5, R6)
use pehle apna **prefill** chalाna padta hai (uska prompt process karke KV cache banाna) us se
pehle ki woh decode batch mein judе. Isliye real schedulers ko prefill aur decode ko interleave
karna padता hai — aur yahीं se "ek bada prefill sabke decode ko rok deta hai" wali jitter aati hai
(A1.2 ka chunked-prefill yaad karo). Tutorial isliye in concepts ko jodता hai.

**Diagram — seat khaali hote hi naya request swap-in (no idle gap):**

```
  Seat ┌──────────────────────────────────────────────┐
   A   │ R1 R1 R1 │R5 R5 R5 R5     ← R1 khatam→R5 turant │
   B   │ R2 R2 R2  R2 R2 R2 R2 R2  ← R2 chalta raha      │
   C   │ R3 R3 │R6 R6 R6           ← R3 khatam→R6 turant  │
   D   │ R4 R4 R4  R4 R4 R4        ← R4                    │
       └──────────────────────────────────────────────┘
        1  2  3  4  5  6  7  8   ← steps
        │     ▲ step3: R1 done, R5 queue se SWAP-IN (seat A)
        │  ▲ step2: R3 done, R6 SWAP-IN (seat C)
   8 steps mein 4 ke bajaye 6 requests nikle (~37% zyada), idle gap ≈ 0
```

**Tools table — continuous batching kaun deta hai aur kaise tune hota hai:**

| Tool | Continuous batching | Tuning knobs | Pros | Cons | Kab use karein |
|---|---|---|---|---|---|
| **vLLM** | Native (in-flight) | `max_num_seqs`, `max_num_batched_tokens` | Best tput, prefix-cache, OSS | Self-host ops | **Default** OSS serving |
| **TGI** | Haan | `max_batch_total_tokens`, `max_concurrent_requests` | HF-native, support | Thodा kam tput kabhi | HF stack + enterprise |
| **TensorRT-LLM** | In-flight batching | Engine build config | Lowest latency | Compile per-change | Fixed model, scale |
| **Ray Serve + backend** | Backend pe (vLLM) | Replica autoscale | Multi-model orchestration | Extra layer | Distributed/multi-replica fleet |

> **Part 3 takeaway:** Continuous batching = har step ke baad khatam-huई request ko nikaalो, seat
> turant agle waiting request ko do. Wahi 8 steps mein 4 ke bajaye 6 requests nikle (~37% zyada),
> sirf scheduling se. Naya joining request ka prefill interleave karna padता hai — wahीं jitter
> ka source.

[↑ Back to top](#contents)

---

<a id="p4"></a>
## Part 4 — KV cache memory ka doosra problem (kyun PagedAttention chahiye)

Continuous batching ne *time* ki barbaadi (idle seats) theek ki. Par ek doosra, alag problem hai —
*memory* ki barbaadi. Yeh samajhna zaroori hai warna PagedAttention "kyun" clear nahi hoga.

**Recap (A1.3 se):** har request apne har token ka KV cache GPU memory mein rakhता hai (~800KB/token
ek 13B model ke liye). Jaise-jaise jawab lamba hota, KV cache badhता jaata. Yeh request ki "samaan"
hai jo seat ke saath GPU memory mein rehni chahiye.

**Ab samasya — framework ko *pehle se* memory reserve karni padti thi:** purane serving systems ko
ek request shuru karte waqt batana padता tha "isko kitni memory chahiye?" Par jawab kitna lamba
hoga — yeh to *pehle se pata hi nahi* (model `<end>` kab dega, maloom nahi)! Toh framework
**safe-side** lekar *max possible* length ki memory reserve kar leta tha. Example: max context 2,048
tokens set hai → har request ke liye 2,048 tokens ka KV cache block *pehle se* allot, chahe woh
request actually sirf 50 tokens banाye.

**Yeh kitna waste hai, ek tasveer se:** maan lo 3 requests, max-reserve 2,048 tokens each, par
actual use alag:

```
Request   Reserve kiya    Actually use hua    Khaali pada (waste)
  R1        2048 tok          50 tok              1998 tok  (98% waste!)
  R2        2048 tok         600 tok              1448 tok  (71% waste)
  R3        2048 tok        1900 tok               148 tok  (7% waste)
```

Average: in 3 requests ne ~6,144 tokens ki memory pakdी, par use sirf ~2,550 — yaani **~58% GPU
memory khaali padी rahी, par "reserved" hone ki wajah se kisi aur request ko nahi mil saकती.** Yeh
ekzಾctly Part 2 wali idle-seat problem hai, par *memory* mein. Aur kyunki KV cache hi concurrency
ki deewar hai (A1.3), yeh waste seedha aapke concurrent-requests ko gira deता hai.

**Ek aur chhupa hua kharcha — fragmentation:** purane systems contiguous (ek saath laga hua) block
maangte the. GPU memory mein 1900-token ka contiguous block na mile (beech mein chhote khaali tukde
bikhre ho) toh request reject — bhale total free memory kaafi ho. Yeh "external fragmentation" hai,
bilkul jaise hard disk fragment hoti hai.

**Toh do takleefein:** (1) over-reservation (max maan ke reserve), (2) fragmentation (contiguous
chahiye). Dono milkar 60-80% KV memory waste karti thीं. Yahीं PagedAttention aata hai.

**Diagram — reserved (max) vs actually-used (over-reservation waste):**

```
  Reserve = 2048 tok har request ke liye (max maan ke). Actual use alag:

  R1  [█·······························]  50/2048   ← 98% khaali, par LOCKED
  R2  [█████████·····················]  600/2048  ← 71% khaali, par LOCKED
  R3  [████████████████████████████··] 1900/2048  ← 7% khaali
        █ = use hua    · = reserved-but-empty (kisi aur ko nahi milta)

  Total reserved ~6144 tok | use ~2550 | ~58% GPU memory locked-but-idle
  + Contiguous chahiye → fragmentation (free hai par bikhra → request reject)
```

**Tools table — KV memory allocation strategy:**

| Strategy / Tool | Allocation | Pros | Cons | Kab |
|---|---|---|---|---|
| **Naive reserve-to-max** (purane HF serving) | Pehle se max-len contiguous block | Simple | 60-80% waste, fragmentation | Avoid (legacy) |
| **PagedAttention** (vLLM) | Fixed blocks, on-demand, non-contiguous | <4% waste, sharing | — | **Default** |
| **Paged KV** (TGI, TRT-LLM) | vLLM jaisा paged | Same benefit, integrated | Tool-specific | Already in those tools |
| **CPU/disk offload** (DeepSpeed-Inference) | Overflow KV ko CPU/NVMe | Bada context fit | Slow (PCIe transfer) | Sirf jab GPU mem genuinely kam |

> **Part 4 takeaway:** Jawab-lambाi pehle se pata na hone ki wajah se purane systems *max* memory
> reserve karte the → 60-80% KV cache memory khaali-par-reserved padी rehती thी, aur contiguous
> requirement se fragmentation. Yeh memory-waste ka problem time-waste (Part 2) se alag hai —
> ise PagedAttention solve karता hai.

[↑ Back to top](#contents)

---

<a id="p5"></a>
## Part 5 — PagedAttention mechanically (OS paging se analogy + trace)

Ab solution, ground se. PagedAttention ka naam hi clue hai — yeh operating-system ke **virtual
memory paging** se udhार liya gaya idea hai. Pehle analogy, phir mechanics.

**OS paging ki yaad (analogy):** aapke laptop mein programs ko lagता hai unke paas ek bada
continuous memory hai, par actually OS memory ko chhote fixed-size **pages** (jaise 4KB) mein toड़ता
hai aur jahan-jahan jagah mile wahan rakhता hai (non-contiguous). Ek **page table** track karta hai
"program ka logical page X → physical memory mein kahan hai." Fayda: koi pehle se bada block reserve
nahi karna, fragmentation nahi (sab pages same size), aur do programs ek hi page *share* kar sakte
hain.

**PagedAttention bilkul yahी KV cache pe karta hai:**
1. GPU memory ko chhote fixed-size **KV blocks** mein toड़ो (maan lo har block = 16 tokens ka KV
   cache). Yeh "pages" hain.
2. Request ko **pehle se kuch reserve mat karo.** Jab woh tokens banाती hai aur ek block bhar jaata
   hai, *tabhi* ek naya block allot karo (on-demand) — page-by-page.
3. Ek **block table** (page table) per request rakhो: "is request ke logical tokens 0-15 → physical
   block #7, tokens 16-31 → physical block #2..." Blocks GPU memory mein *non-contiguous* ho sakte
   hain — table jod deta hai.

**Wahi 3 requests, ab PagedAttention se (Part 4 wala example dobara):** block size 16 tokens. Ab
koi 2,048 reserve nahi — sirf jitne tokens bane, utne blocks:

```
Request   Tokens bane   Blocks chahiye (16/block)   Memory pakdी (≈ actual)
  R1         50 tok        ceil(50/16) = 4 blocks       ~64 tokens worth (sirf ~14 waste)
  R2        600 tok        ceil(600/16) = 38 blocks     ~608 tokens worth (~8 waste)
  R3       1900 tok        ceil(1900/16)= 119 blocks    ~1904 tokens worth (~4 waste)
```

Pehle (Part 4) ~58% memory waste thी; ab waste sirf "aakhri aadhे-bhare block" ka — typically
**<4%**. Yaani lagbhag *poori* free memory asli requests ke kaam aati hai → **same GPU pe 2-4×
zyada concurrent requests**. Aur fragmentation gayब — saare blocks same size hain, koi bhi khaali
block kisi bhi request ko de sakte ho.

**Bonus jo OS-paging analogy se free milta hai — block sharing:** socho 100 requests sab ek hi lamba
system prompt se shuru hote hain ("You are a helpful assistant... [500 tokens of rules]"). Purane
system mein har request us 500-token prompt ka KV cache *alag* banata aur store karta — 100× waste.
PagedAttention mein woh common-prefix blocks **ek baar** bante hain aur saare 100 requests ke block
table us *same* physical block ko point karte hain (copy-on-write — agar koi badle tabhi copy). 500
tokens × 100 requests ka memory → ~500 tokens ka, ek baar. Yeh "prefix caching" ka mechanism hai.

**Ek chhota trace, sharing dikhane ko:**

```
Common prefix (500 tok) ke blocks: [P0][P1]...[P31]   <- ek baar bane, GPU mein ek jagah
R1 block table:  P0 P1 ... P31  →  [R1a][R1b]   (sirf R1 ke apne naye tokens ke blocks)
R2 block table:  P0 P1 ... P31  →  [R2a]        (wahी P0..P31 share, phir apne)
R3 block table:  P0 P1 ... P31  →  [R3a][R3b][R3c]
```

Dekha — P0..P31 (prefix) teeno ke table mein hai par physical memory mein *ek hi copy*. Sirf har
request ke unique tokens ke alag blocks. Yahी se "prefix-sharing se memory 2-4× behtar" wala number
aata hai.

**Diagram — block table logical→physical mapping (OS page-table jaisा):**

```
  Request ka "logical" view        Block table        GPU physical memory
  (lagta hai contiguous)           (mapping)          (bikhre, non-contiguous)
  ┌────────────────────┐                              ┌──┬──┬──┬──┬──┬──┬──┬──┐
  │ tok 0-15  (logical0)│──► block #7 ──────────────► │  │  │  │  │  │  │L0│  │
  │ tok 16-31 (logical1)│──► block #2 ──────────────► │  │  │L1│  │  │  │  │  │
  │ tok 32-47 (logical2)│──► block #5 ──────────────► │  │  │  │  │  │L2│  │  │
  └────────────────────┘                              └──┴──┴──┴──┴──┴──┴──┴──┘
   Allot ON-DEMAND (block bhar gaya tabhi agla). Reserve nahi. Frag nahi.

  Prefix SHARING (copy-on-write):
   R1 table:  [P0][P1]..[P31] → R1a R1b        ┐
   R2 table:  [P0][P1]..[P31] → R2a            ├─ P0..P31 = EK physical copy
   R3 table:  [P0][P1]..[P31] → R3a R3b R3c    ┘   (100 req → 1 prefix copy)
```

**Tools table — paging + prefix/KV caching support:**

| Tool | Paged KV | Auto prefix-cache | KV offload | Pros | Cons | Kab |
|---|---|---|---|---|---|---|
| **vLLM** | Haan | Haan (`enable_prefix_caching`) | Experimental | Sharing free, best mem-util | Cache accounting monitor karo | **Default**, shared-prompt workloads |
| **TGI** | Haan | Partial | Nahi | Integrated, HF | vLLM se kam knobs | HF stack |
| **TensorRT-LLM** | Haan | Haan (KV reuse) | Haan | Fastest + paged | Compile complexity | Fixed high-scale |
| **SGLang** | Haan (RadixAttention) | Haan (tree-based, strong) | — | Best for heavy prefix-sharing (agents, few-shot) | Newer ecosystem | Bahut shared-prefix / structured gen |

> **Part 5 takeaway:** PagedAttention = OS virtual-memory paging, KV cache pe lagaya. KV ko
> fixed-size blocks mein toड़ो, on-demand allot karo (pehle se reserve nahi), block-table se jod do.
> Natija: ~58% waste → <4%, fragmentation khatam, aur common prefixes ke blocks share ho jaate hain
> (prefix caching) — milkar 2-4× zyada concurrency.

[↑ Back to top](#contents)

---

<a id="p6"></a>
## Part 6 — Visual: poora flow + kaunsa tool kab (pros/cons table)

Ab sab jod ke ek tasveer mein dekhte hain — request GPU tak kaise pahunchti hai, aur kahan kaunsा
component kaam karta hai.

**Diagram — ek request ka safar (continuous batching + PagedAttention serving stack):**

```
                          ┌───────────────────────────────────────────────┐
   Users (1000s) ───────► │              API Gateway / LB                  │
                          │   (auth, rate-limit, routing)                  │
                          └───────────────────────┬───────────────────────┘
                                                   │
                                                   ▼
                          ┌───────────────────────────────────────────────┐
                          │            SCHEDULER (vLLM engine)             │
                          │  ┌──────────────┐      ┌──────────────────┐   │
   Naye requests ───────► │  │ Waiting queue │ ───► │ Running batch    │   │
                          │  └──────────────┘      │ (continuous:     │   │
   khatam → seat khaali ◄─┤        ▲               │  har step pe      │   │
   → queue se bharo       │        └───────────────┤  add/remove)     │   │
                          │                        └─────────┬────────┘   │
                          └──────────────────────────────────┼────────────┘
                                                              │ har decode step
                                                              ▼
                          ┌───────────────────────────────────────────────┐
                          │                   GPU                          │
                          │   Weights (fixed, 1 baar load)                 │
                          │   ┌─────────────────────────────────────────┐  │
                          │   │   KV cache = fixed-size BLOCKS (paged)   │  │
                          │   │  [B0][B1][B2][B3][B4][B5][B6][B7]...     │  │
                          │   │   ▲ block table per request inhe jodta   │  │
                          │   │   ▲ common-prefix blocks SHARED          │  │
                          │   └─────────────────────────────────────────┘  │
                          └───────────────────────────────────────────────┘

   Do alag optimizations, do alag jagah:
     • Continuous batching  → SCHEDULER level (kaun batch mein, kab) — TIME waste fix
     • PagedAttention       → GPU MEMORY level (KV blocks)          — MEMORY waste fix
```

**Static vs Continuous, side-by-side (GPU utilisation over time):**

```
  STATIC batching                         CONTINUOUS batching
  GPU% ▲                                  GPU% ▲
  100  │█▓▒░    ░░░░                       100  │████████████████
       │█▓▒░    ░░░░   (idle: batch ke     │████████████████
   50  │█▓▒░    ░░░░    aakhir mein         50  │████████████████
       │█▓▒░    ░░░░    seats khaali)            │████████████████
    0  └──────────────►time                  0  └──────────────►time
       avg ~30-50% used                         avg ~70-90% used
```

### Kaunsa tool kab — decision + pros/cons table

Yeh optimizations khud nahi likhते — frameworks deते hain. Kaunsा framework yeh kaise karta hai aur
kab chunein:

| Tool | Continuous batching? | PagedAttention / paged KV? | Pros | Cons | Kab use karein |
|---|---|---|---|---|---|
| **vLLM** | Haan (native) | Haan (iska invention) | Best throughput/$, prefix-caching, OSS, easy model swap | Self-host/SRE chahiye; bleeding-edge models pe kabhi patch wait | **Default** — OSS models, apna infra, max tput chahiye |
| **TGI** (HuggingFace) | Haan | Haan (paged KV) | HF Hub se seedha, enterprise support, polished | vLLM se thodा peeche raw tput mein kabhi | HF ecosystem mein deep ho, support contract chahiye |
| **TensorRT-LLM** | Haan (in-flight batching) | Haan | Lowest latency/$, kernel-compiled | Compile step heavy, NVIDIA-only, iteration slow | Fixed model, massive scale, last 20-30% latency nichod-na |
| **Triton Inference Server** | Backend pe (TRT-LLM/vLLM) | Backend pe | Multi-model platform, ensembles, ek fleet | Setup complex, single-LLM ke liye overkill | LLM + embeddings + rerankers ek hi serving fleet pe |
| **Naya khud ka Flask + `generate()`** | **Nahi** | **Nahi** | Sirf seekhne/demo ke liye simple | 5-15× slow, GPU idle, memory waste | **Kabhi nahi** production mein (yeh anti-pattern hai) |

**Decision rule (ek line):** OSS model + apna infra → **vLLM**. HF + support → **TGI**. Ek fixed
model massive scale pe → **TensorRT-LLM** (aksar **Triton** ke andar). Multi-model platform →
**Triton**. Flask loop → sirf prototype, prod mein kabhi nahi.

> **Part 6 takeaway:** Continuous batching scheduler-level pe time-waste theek karta hai;
> PagedAttention GPU-memory-level pe memory-waste. Dono vLLM/TGI/TRT-LLM/Triton mein built-in hain
> — aap khud Flask loop likhoge toh dono kho doge (5-15× slower). Tool choice stage + scale se:
> vLLM default, TRT-LLM for fixed high-scale, Triton for multi-model.

[↑ Back to top](#contents)

---

<a id="p7"></a>
## Part 7 — Worked examples (situation → resolution)

Ab jo Part 1-6 mein seekha, woh do real scenarios pe lagao. (Yeh woh "situation-resolution" wala
part hai — par ab iske *peeche* ka mechanism aap poora samajhte ho, ratta nahi.)

- **Example 1 — Flask loop se vLLM (8 workers → ~1.5 replica):** ek startup ka pehla LLM service
  Flask tha, har request `model.generate()` akela call karta (effectively batch=1, Part 6 ka
  anti-pattern). 8 GPU workers, ~40 req/s ceiling, GPU utilisation dashboards pe ~25% (yaad karo
  Part 2 ka static-idle + Part 4 ka memory-waste, dono ek saath ho rahe the). vLLM pe switch:
  continuous batching ne GPU bhar diya (~70%), PagedAttention ne memory waste khatam ki →
  **ek A100 replica ~120 req/s.** 8 workers ka kaam ~1.5 replica mein, GPU bill ~80% kam — bina
  model badle, sirf serving layer. *Mechanism jo isे samjhाता hai:* Part 2 (idle seats) + Part 4
  (reserved-but-empty memory) dono Flask loop mein active the; vLLM ne dono hata diye.

- **Example 2 — Prefix-caching ne ek bot ka prefill bill giraaya:** ek customer-support bot ka har
  query ek ~700-token system prompt + few-shot examples se shuru hota tha (sab queries mein *same*).
  Purane setup mein har request us 700-token prefix ka KV cache dobara banाता (prefill) aur store
  karता. Naap ke dekhа: GPU-time ka bada hissa is repeated prefix ke prefill mein jaa raha tha, aur
  KV memory mein 100s copies. vLLM ka **prefix-caching** (Part 5 ka block-sharing) on kiya → woh
  700-token prefix ke blocks *ek baar* bane, saare requests ne share kiye (copy-on-write). Natija:
  TTFT ~40% kam (prefill skip for shared part), KV memory free → concurrency up. *Mechanism:* Part
  5 ka "common-prefix blocks ek hi physical copy" — yeh exactly woh feature hai.

**Diagram — symptom → asli mechanism → fix (yeh mapping interview mein bolna):**

```
  SYMPTOM (jo dikhta)          ASLI MECHANISM (Part)        FIX
  ─────────────────────────────────────────────────────────────────────
  GPU util ~25%, slow      →   idle seats (Part 2) +    →  continuous batching
  par "GPU toh hai"            mem over-reserve (Part4)     + PagedAttention (vLLM)
  ─────────────────────────────────────────────────────────────────────
  TTFT high, same prompt   →   repeated prefix prefill  →  prefix-caching
  baar-baar                    + KV duplicate copies (P5)   (block sharing)
  ─────────────────────────────────────────────────────────────────────
  p99 spike at peak only   →   high-util queueing       →  ~75% util target +
                               (cliff)                      admission control
```

**Tools table — kaunsi situation mein kaunsा lever/tool:**

| Situation (symptom) | Tool/lever | Pros | Cons | Kab use karein |
|---|---|---|---|---|
| Low GPU util, batch=1 loop | vLLM/TGI (continuous + paged) | 5-15× tput, drop-in | Self-host ops | Almost always (Flask loop replace) |
| Same long prompt everywhere | Prefix-caching (vLLM/SGLang) | TTFT down, mem free | Cache monitor | Few-shot, system-prompt-heavy, agents |
| Model fit nahi / latency | TP within node (A1.6) | Fit + latency | NVLink-bound | 70B+ on one node |
| Last 20-30% latency/$ | TensorRT-LLM | Lowest latency | Compile, NVIDIA-lock | Fixed model, massive scale |

> **Part 7 takeaway:** Dono real wins (Flask→vLLM, prefix-caching) directly Part 2/4/5 ke
> mechanisms se aaye. Jab aap mechanism jaante ho, toh "kya optimize karein" guess nahi karna padta
> — aap *naap ke* bottleneck pe haath rakhте ho.

[↑ Back to top](#contents)

---

<a id="p8"></a>
## Part 8 — Pros/cons, kab NAHI, aur defense line

**Continuous batching + PagedAttention ke pros/cons (ek jagah):**

| Aspect | ✅ Pro | ❌ Con / dhyान |
|---|---|---|
| Throughput | 5-15× vs naive (idle seats + memory waste dono fix) | — |
| Memory | <4% KV waste, prefix-sharing | Prefix-cache ka memory-accounting monitor karna padta (eviction storms, A1.9) |
| Latency | GPU bhara → behtar avg latency | High utilisation pe queueing → p99 cliff; ~75% pe rakho |
| Effort | Library use karo (vLLM/TGI), khud mat likho | Self-hosting ops; framework lock-in |
| Quality | Koi change nahi (sirf scheduling/memory) | — |

**Diagram — decision flow (kaunsा serving setup chunein):**

```
                    START: LLM serve karna hai
                              │
              ┌───────────────┴────────────────┐
         Traffic high/steady?              Low/spiky?
              │ haan                          │ haan
              ▼                               ▼
     OSS model + apna infra?            API use karo (build-vs-buy,
       │ haan        │ HF-stack          A1.8) — idle GPU mat paalo
       ▼             ▼
     vLLM          TGI
       │
   Ek fixed model, massive scale, last 20-30% squeeze chahiye?
       │ haan
       ▼
   TensorRT-LLM (aksar Triton ke andar)
       │
   LLM + embeddings + rerankers ek hi fleet pe?
       │ haan
       ▼
   Triton (multi-model platform)
```

**Tools table — final pick by stage/scale (ek jagah recap):**

| Stage / need | Pick | Pros | Cons | Kab NAHI |
|---|---|---|---|---|
| Prototype / iterate fast | **vLLM** | Drop-in, OSS, model swap easy | Self-host | — |
| HF ecosystem + support | **TGI** | Polished, enterprise | Thodा kam tput | Max raw tput chahiye |
| Fixed model, huge scale | **TensorRT-LLM** | Lowest latency/$ | Compile, NVIDIA-only | Models frequently badalte |
| Multi-model platform | **Triton** | Ensembles, one fleet | Setup heavy | Sirf 1 LLM |
| Low/spiky volume | **Hosted API** | No idle GPU, pay-per-use | Per-token markup at scale | High steady volume |

**Kab NAHI / kab over-kill:**
- **Bahut low traffic (chhota internal tool, 1-2 req/s):** continuous batching ka fayda tab hai jab
  ek saath kayी requests hon. Ek-ek aane wali requests pe batch banta hi nahi — par koi nuksaan bhi
  nahi (vLLM phir bhi theek), bas "isliye fast hai" mat socho. Real lever yahan caching/API hoga.
- **Bohot lambे fixed outputs, koi variance nahi:** agar har request *exactly* same length deta (rare),
  static batching ki idle-seat problem hoti hi nahi — par aisा real workload milta nahi.
- **Khud likhne ki koshish:** continuous batching + paging khud likhna mahीनों ka kaam aur bugs ka
  pitara — isliye yeh "kab NAHI": kabhi khud mat likho, library lो.

**Defense line (Google review mein):** *"Naive serving wastes two independent things — GPU time
(static batches block on the longest sequence) and GPU memory (KV cache is over-reserved to max
length, ~60-80% wasted). Continuous batching fixes the time waste at the scheduler by swapping
finished requests out every decode step, and PagedAttention fixes the memory waste by treating KV
cache like OS paging — fixed blocks, allocated on demand, with shared blocks for common prefixes.
Together that's the ~10x throughput gap between a Flask `generate()` loop and vLLM, which is why we
never hand-roll serving."*

---

> **Is sample ka maqsad:** dikhana ki "tutorial" ka matlab — concept ko *ground se* sikhाना
> (intuition → mechanics → trace → diagram → tool-table → examples → pros/cons), na ki sirf
> situation-resolution. Har Part ek learning step hai.
>
> **Agar yeh format theek lage → main:** (1) A1 ke saare 10 sections isi tutorial-style mein
> rebuild karunga, aur (2) A2-A7 isi bar pe banaunga. Bataiye — yeh depth/format sahi hai?

[↑ Back to top](#contents)

