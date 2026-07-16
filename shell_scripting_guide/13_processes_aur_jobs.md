<a id="top"></a>
# Chapter 13 — Processes aur Jobs (chalte programs ko dekhna aur control karna)

Ab tak humne commands chalaye aur scripts likhi. Par jab koi program chal raha hota, woh ek
**process** ban jata — aur kabhi aapko use dekhna, rokna, ya background mein bhejna padta. Yeh
chapter batata hai chalte programs ko kaise dekhein (`ps`, `top`), rokein (`kill`), aur background
mein chalayein (`&`, `nohup`).

Yeh production mein bahut kaam aata — jaise ek server chalana, ek atki hui process rokna, ya ek lamba
job background mein daalna. Yeh theory-heavy chapter hai.

---

## Is chapter ka index

- [13.1 — Process kya hai (ek chalta hua program)](#s13-1)
- [13.2 — `ps` — chalti processes dekhna](#s13-2)
- [13.3 — `top` / `htop` — live process monitor](#s13-3)
- [13.4 — Signals aur `kill` — process ko rokna](#s13-4)
- [13.5 — `kill -9` — zabardasti rokna (aur kab)](#s13-5)
- [13.6 — Foreground vs Background (`&`, `Ctrl+Z`, `bg`, `fg`)](#s13-6)
- [13.7 — `jobs` — background jobs dekhna](#s13-7)
- [13.8 — `nohup` aur `&` — terminal band hone pe bhi chalta rahe](#s13-8)
- [13.9 — `;` vs `&&` vs `&` — commands chalane ke tareeke](#s13-9)
- [13.10 — Nuances aur caveats](#s13-10)
- [13.11 — Real-life scenarios](#s13-11)

---

<a id="s13-1"></a>
## 13.1 — Process kya hai (ek chalta hua program)

**Process** ek **chalta hua program** hai. Farak samajho: ek program (jaise `python`, ya aapki
script) disk pe ek file hai — jab woh **chalta** hai, toh memory mein ek "process" ban jata. Ek hi
program ki kai processes ek saath chal sakti (jaise 3 browser tabs = 3 processes).

**Har process ka ek PID (Process ID):** OS har chalti process ko ek unique **number** deta —
**PID** (Process ID). Yeh uski "pehchaan" hai. Jab aapko kisi process ko rokna/dekhna ho, aap uske
PID se baat karte ho. (Yaad karo Ch 5.6 — `$$` current shell ka PID deta.)

**Analogy:** program = ek recipe (kaagaz pe likhi). Process = us recipe se actually banta khaana
(chal raha kaam). Ek recipe se kai baar khaana bana sakte (kai processes). Har "bante khaane" ko ek
token-number (PID) mil jata taaki pehchana ja sake.

**Process ke states (haal):** ek process **running** (chal rahi), **sleeping** (wait kar rahi, jaise
input ka), ya **stopped** (ruki, 13.6) ho sakti. `ps`/`top` (13.2/13.3) yeh haal dikhate.

**Parent aur child:** ek process doosri ko shuru kar sakti — jaise aapka shell (parent) ek command
(child) chalata. Isiliye "process tree" banta (jaise filesystem tree, Ch 2). Terminal band hone pe
uske child processes ko aksar signal milta (13.8 — yeh Ch 1.12 wala "terminal band = kaam ruk gaya"
ka asli kaaran).

> **Yaad rakhne wali baat:** Process = chalta hua program (memory mein). Program = disk pe file;
> process = uska chalta roop. Har process ka unique PID (number) — usse use dekhte/rokte hain. Ek
> program ki kai processes ho sakti.

[↑ Back to top](#top)

---

<a id="s13-2"></a>
## 13.2 — `ps` — chalti processes dekhna

**`ps`** = **p**rocess **s**tatus — chalti processes ki list dikhata hai (ek snapshot — us pal ki
tasveer).

**Akela `ps` (sirf aapke current shell ki):**
```
ps
```
- Output: sirf aapke is terminal mein chal rahi processes (thodi si). Zyada kaam ka nahi akela.

**`ps aux` — SAARI processes (yeh sabse use hota):**
```
ps aux
```
- **`aux`** (yeh purana BSD-style flags, bina `-`): `a` (saare users ki), `u` (detailed/user-friendly
  format), `x` (background wali bhi). Milke: system ki **saari** processes, detail ke saath.
- **Output columns:** `USER` (kiski), `PID` (number, 13.1), `%CPU`, `%MEM` (kitna CPU/memory kha
  rahi), `COMMAND` (kya chal raha). Yeh sab ek process ke bare mein batata.

**Kisi khaas process ko dhoondhna — `grep` ke saath (Ch 12):**
```
ps aux | grep python
```
- Saari processes → `grep python` (sirf python wali). "Kya koi python chal raha, uska PID kya" — yeh
  jaanne ka standard tareeka. PID mil gaya toh use `kill` (13.4) kar sakte.
- **Chhota trap:** `grep python` khud ek process hai, toh woh bhi list mein aa jata (`grep python`
  wali line). Ignore karo ya `grep [p]ython` (trick) use karo.

**`ps -ef` — ek aur common format:**
```
ps -ef | grep nginx
```
- `-ef` (Linux/System-V style): `e` (saari), `f` (full format, parent-PID ke saath). `ps aux` aur
  `ps -ef` dono saari processes dete, bs format thoda alag. Dono common — jo mile use karo.

> **Yaad rakhne wali baat:** `ps` = chalti processes ka snapshot. `ps aux` (ya `ps -ef`) = SAARI
> processes detail ke saath (PID, CPU, MEM, command). `ps aux | grep naam` = khaas process + PID
> dhoondho (phir kill kar sakte). grep khud bhi list mein aata.

[↑ Back to top](#top)

---

<a id="s13-3"></a>
## 13.3 — `top` / `htop` — live process monitor

`ps` ek **snapshot** (ek pal) deta. **`top`** ek **live, updating** view deta — processes real-time
mein dikhti hain, har kuch second update hoti (jaise ek dashboard).

```
top
```
- Full-screen live view khulta. Upar: system summary (total CPU, memory, load). Neeche: processes ki
  list, **CPU/memory ke hisaab se sorted** (sabse zyada khane wali upar). Har 1-2 second update.
- **Kab kaam ka:** "system slow kyun hai? kaun si process CPU/memory kha rahi?" — `top` turant
  dikha deta sabse bhaari process. Server pe roz ka diagnostic.
- **Bahar nikalna:** **`q`** (quit — Ch 1 wala, atke toh `q`).

**`htop` — behtar, colorful version:**
```
htop
```
- `htop` = `top` ka improved version — colors, scroll, mouse, aasaan kill karna. Zyada friendly. Par
  pehle se installed nahi hota (`brew install htop` Mac, ya server pe install). Jab available ho,
  `top` se behtar.

**`top` mein kya dekhein:** `%CPU` (CPU usage), `%MEM` (memory), `PID` (kill ke liye), `COMMAND`.
Agar ek process 100% CPU kha rahi (atki/runaway), yahan turant dikhegi — PID note karo, phir `kill`
(13.4).

> **Yaad rakhne wali baat:** `top` = live process monitor (real-time updating, CPU/memory sorted —
> bhaari process upar). "System slow kyun" ka turant jawab. `q` se bahar. `htop` = behtar/colorful
> version (install karna padta). PID note karke kill kar sakte.

[↑ Back to top](#top)

---

<a id="s13-4"></a>
## 13.4 — Signals aur `kill` — process ko rokna

Ek chalti process ko rokne (ya use kuch batane) ke liye, aap use ek **signal** bhejte ho. **Signal**
= ek chhota "message" jo OS process ko deta ("ruk jao", "band ho jao", etc.). Iske liye command hai
**`kill`** (naam daraana hai, par yeh sirf signal bhejta — hamesha "maarna" nahi).

**Basic — `kill PID`:**
```
kill 12345
```
- `12345` = process ka PID (13.1 — `ps`/`top` se mila). Yeh default signal **SIGTERM** (terminate —
  "shaanti se band ho jao") bhejta. Process ko mauka milta apna kaam samet ke (files save, cleanup)
  band hone ka. Yeh "polite" tareeka hai — pehle yeh try karo.

**Signals kya hain (kuch common):**

| Signal | Number | Matlab |
|---|---|---|
| SIGTERM | 15 | "shaanti se band ho jao" (default, cleanup ka mauka) |
| SIGKILL | 9 | "abhi, zabardasti mar jao" (koi cleanup nahi, 13.5) |
| SIGINT | 2 | "interrupt" — yeh `Ctrl+C` bhejta hai (Ch 1) |
| SIGHUP | 1 | "hang-up" — terminal band hone pe (Ch 1.12, 13.8) |

- Toh `Ctrl+C` (Ch 1) asal mein SIGINT signal bhejna tha — ab poora juda. Aur terminal band = SIGHUP
  (Ch 1.12) — 13.8 mein `nohup` isse bachata.

**Signal choose karke bhejna:**
```
kill -15 12345      # SIGTERM (= default, polite)
kill -2 12345       # SIGINT (jaise Ctrl+C)
kill -9 12345       # SIGKILL (zabardasti, 13.5)
```
- `-15`, `-9` = kaunsa signal (number). `kill` (bina number) = `-15` (SIGTERM).

**Naam se kill — `pkill` / `killall`:**
```
pkill python          # "python" naam wali processes ko signal
killall firefox       # "firefox" naam wali sab
```
- PID dhoondhne ke bajaye seedha naam se. **Dhyan** — yeh us naam ki *saari* processes ko maar deta
  (agar 3 python chal rahe, teeno). Precise chahiye toh PID se `kill`.

> **Yaad rakhne wali baat:** `kill PID` = process ko signal bhejo (default SIGTERM 15 = "shaanti se
> band ho"). Signals: SIGTERM (15, polite), SIGKILL (9, zabardasti), SIGINT (2 = Ctrl+C), SIGHUP (1
> = terminal band). `pkill naam` = naam se (saari us naam wali). Pehle polite (15), phir 9.

[↑ Back to top](#top)

---

<a id="s13-5"></a>
## 13.5 — `kill -9` — zabardasti rokna (aur kab)

**`kill -9 PID`** sabse taakatvar — signal **SIGKILL** (9) bhejta, jo process ko **turant, zabardasti**
maar deta — koi mauka nahi, koi cleanup nahi.

```
kill -9 12345
```
- Process turant mar jati — bina kuch save kiye, bina samet. OS use force se hata deta. Yeh "last
  resort" (aakhri upaay) hai.

**`-9` vs normal kill (15) — farak aur kab:**
- **`kill PID` (15, SIGTERM):** "shaanti se band ho jao" — process apna kaam samet sakti (files save,
  connections band, temp cleanup). **Pehle hamesha yeh try karo.**
- **`kill -9 PID` (SIGKILL):** "abhi maro" — koi cleanup nahi. Sirf tab jab normal `kill` kaam na
  kare (process **atki** hai, respond nahi kar rahi).

**Kab `-9` (aur kab nahi):**
- **Use `-9`:** jab process poori tarah **atki/hang** hai aur normal `kill` (15) se nahi ruk rahi
  (kuch second wait karke dekho pehle). Tab `-9`.
- **Avoid `-9` pehle:** seedha `-9` mat maaro — kyunki cleanup nahi hoti, toh: aadhe-likhe files,
  corrupt data, locked resources reh sakte. Databases/important services pe `-9` last resort.
- **Rule:** pehle `kill PID` (15). 5-10 second wait. Na ruke → `kill -9 PID`. "Pehle politely, phir
  zabardasti."

**Yeh khatarnak kyun (khaaskar databases):** ek database ko `-9` se maaro toh woh apna data disk pe
theek se save/close nahi kar pati — corruption ho sakti. Isliye services ko hamesha pehle graceful
(15) rokne ka mauka do.

> **Yaad rakhne wali baat:** `kill -9 PID` = SIGKILL = turant zabardasti maro (koi cleanup nahi).
> Sirf jab process atki ho aur normal `kill` (15) na chale. Pehle `kill PID` (polite) + wait, phir
> `-9`. `-9` pe cleanup nahi → data corrupt ho sakta (databases pe dhyan).

[↑ Back to top](#top)

---

<a id="s13-6"></a>
## 13.6 — Foreground vs Background (`&`, `Ctrl+Z`, `bg`, `fg`)

Jab aap ek command chalate ho, woh aam taur pe **foreground** mein chalti — matlab terminal use
"pakde" rehti, aap kuch aur nahi kar sakte jab tak woh khatam na ho. **Background** mein bhejne se woh
chalti rehti aur terminal aapko wapas mil jata (aur kaam kar sakte ho).

**`&` — command ko background mein chalao:**
```
long_task.sh &
```
- **`&`** (command ke aakhir mein) = "ise background mein chalao". Command shuru hoti par terminal
  turant wapas (aap aage kaam kar sakte). Output: `[1] 12345` — `[1]` = job number (13.7), `12345` =
  PID.
- **Kab:** lamba kaam (backup, build, download) jo chalta rahe aur aap beech mein terminal use karo.

**`Ctrl+Z` — chalti (foreground) command ko ROKo (pause):**
```
# ek command chal rahi hai, aapne Ctrl+Z dabaya
```
- **`Ctrl+Z`** = chalti foreground command ko **stop/pause** (ruk gayi, mari nahi — SIGTSTP signal).
  Terminal wapas. Ab woh "stopped" state mein (13.1). Isse aap ek command ko temporarily rok ke kuch
  aur kar sakte.

**`bg` — ruki command ko background mein chalao:**
```
bg
```
- `Ctrl+Z` se roki command ko `bg` (**b**ack**g**round) se background mein chala do — ab woh chalti
  rahegi par background mein (terminal free). "Rok ke background mein daalna."

**`fg` — background/ruki command ko wapas foreground mein:**
```
fg
```
- `fg` (**f**ore**g**round) = background/stopped job ko wapas foreground mein le aao (terminal us pe
  wapas). Jab aap us command pe wapas dhyan dena chahte ho.

**Poora flow (yeh yaad rakho):**
```
long_task.sh          # foreground mein chal rahi
Ctrl+Z                # roki (stopped), terminal wapas
bg                    # background mein chala di (chalti rahegi)
fg                    # wapas foreground mein (agar chahiye)
```

> **Yaad rakhne wali baat:** Foreground = terminal pakde (default); background = terminal free, kaam
> chalta rahe. `command &` (background mein shuru), `Ctrl+Z` (chalti ko roko/pause), `bg` (roki ko
> background mein chalao), `fg` (wapas foreground). Lambe kaam background mein.

[↑ Back to top](#top)

---

<a id="s13-7"></a>
## 13.7 — `jobs` — background jobs dekhna

Jab aap kai cheezein background mein daal dete ho (13.6), toh **`jobs`** batata hai kaun-kaun si
chal rahi hain (is terminal ke).

```
jobs
```
- **Output (misaal):**
  ```
  [1]  Running    long_task.sh &
  [2]- Stopped    vim notes.txt
  [3]+ Running    backup.sh &
  ```
- **`[1]`, `[2]`** = **job number** (PID se alag — yeh is terminal ke andar chhota number). `Running`
  (chal rahi) ya `Stopped` (`Ctrl+Z` se roki, 13.6). Phir command.
- **`+`** = "current" job (default jispe `fg`/`bg` kaam karega), **`-`** = "next" wala.

**Job number se `fg`/`bg` (specific job):**
```
fg %2          # job number 2 ko foreground mein
bg %1          # job number 1 ko background mein
kill %3        # job number 3 ko kill
```
- **`%2`** = "job number 2" (`%` = job-reference). Jab kai jobs ho aur ek specific pe kaam karna ho.
  `fg` akela = current (`+`) job; `fg %2` = exactly job 2.

**Job number vs PID (farak):** **PID** (13.1) system-wide unique number (`kill` ke liye, `ps` mein
dikhta). **Job number** (`[1]`) sirf is terminal ke andar, chhota (1,2,3). `jobs` job-number deta,
`ps` PID deta. Dono se process pe kaam kar sakte (`kill %1` job se, `kill 12345` PID se).

**Zaroori — jobs sirf is terminal ke:** `jobs` sirf *isi* terminal se shuru ki background processes
dikhata. Doosre terminal ki ya system ki baaki processes ke liye `ps aux` (13.2). Jobs = "mere is
terminal ke background kaam".

> **Yaad rakhne wali baat:** `jobs` = is terminal ke background/stopped jobs (job-number `[1]`,
> Running/Stopped). `%2` = job number 2 (`fg %2`, `kill %2`). Job-number (terminal-local, chhota) vs
> PID (system-wide, `ps`). `jobs` sirf is terminal ke.

[↑ Back to top](#top)

---

<a id="s13-8"></a>
## 13.8 — `nohup` aur `&` — terminal band hone pe bhi chalta rahe

Yeh section Ch 1.12 wali gutthi suljhata — "terminal band kiya toh mera lamba kaam ruk gaya, kyun?"
Aur uska fix.

**Problem (Ch 1.12 + 13.4 wala SIGHUP):** jab aap terminal band karte ho, uske andar chal rahi
processes ko **SIGHUP** signal (13.4 — "hang-up", terminal chala gaya) milta, aur woh **ruk jati**.
Toh sirf `command &` (background) kaafi nahi — terminal band = SIGHUP = kaam gaya, chahe background
mein ho.

**Solution — `nohup` (no hang-up):**
```
nohup long_task.sh &
```
- **`nohup`** = "**no** **h**ang-**up**" — "is command ko SIGHUP se bacha do (ignore karo)". Ab
  terminal band ho jaye toh bhi command chalti rahegi. `&` (background) ke saath jodte hain —
  `nohup ... &` = "background mein, aur terminal band pe bhi zinda".
- **Output kahan jata:** terminal band ho toh output kahan? `nohup` default output ko `nohup.out`
  file mein daal deta (current folder mein). Ya aap khud redirect karo: `nohup task.sh > mylog.txt
  2>&1 &` (Ch 6.6 — output+error log mein).

**Yeh Ch 1.13 Scenario 5 wala tha:** "lamba training job terminal band karte hi ruk gaya" — ab fix
pata: `nohup python train.py > train.log 2>&1 &`. Ab laptop band karo, SSH toot jaye — job chalti
rahegi, log `train.log` mein.

**Behtar alternative — `tmux` / `screen` (zikr):** `nohup` simple hai par thoda kachcha (wapas
process se "connect" nahi kar sakte, sirf log dekh sakte). **`tmux`** (ya `screen`) ek "session"
banata jo terminal band hone pe bhi zinda rehta, aur aap baad mein us session se **wapas jude** sakte
ho (jaise chhod ke gaye the). Lambe/interactive kaam ke liye `tmux` behtar. (Yeh apna topic hai —
Ch 16 mein zikr.) Abhi: quick background job → `nohup ... &`; lamba/wapas-judna ho → `tmux`.

> **Yaad rakhne wali baat:** Terminal band = SIGHUP = background kaam bhi ruk jata. `nohup command &`
> = SIGHUP ignore, terminal band pe bhi chalti rahe (output `nohup.out` ya redirect karo). Ch 1.12
> ka fix. Lambe/wapas-judne wale kaam ke liye `tmux` behtar (Ch 16).

[↑ Back to top](#top)

---

<a id="s13-9"></a>
## 13.9 — `;` vs `&&` vs `&` — commands chalane ke tareeke

Yeh teen symbols commands ko chalane/jodne ke alag tareeke hain — dikhne mein milte-julte, par bilkul
alag. (Ch 9.10 mein `&&`/`||` dekhe; ab poora set ek jagah.)

**`;` (semicolon) — ek ke baad ek (chahe fail ho):**
```
command1 ; command2
```
- **`;`** = "command1 chalao, phir command2 chalao — chahe command1 fail ho ya pass". Dono chalenge,
  bina ek doosre ki parwah. "Bs ek ke baad ek."

**`&&` (double-and) — safal ho toh hi agla (Ch 9.10):**
```
command1 && command2
```
- **`&&`** = "command1 chalao, aur **safal** ho (exit 0) toh hi command2". Fail → command2 nahi.
  "Safal ho toh hi aage." (Ch 9.10.)

**`&` (single-and) — background mein (13.6):**
```
command1 &
```
- **`&`** = "command1 ko **background** mein chalao, terminal wapas do". Yeh jodta nahi, background
  bhejta (13.6). Bilkul alag kaam.

**Teeno ka farak (ek saath — yeh yaad rakho):**

| Symbol | Matlab |
|---|---|
| `a ; b` | a, phir b (chahe a fail ho) |
| `a && b` | a, phir b **sirf agar a safal** |
| `a \|\| b` | a, phir b **sirf agar a fail** (Ch 9.10) |
| `a &` | a ko background mein (b nahi, terminal free) |

**Common confusion — `&` vs `&&`:** ek `&` = background (13.6), do `&&` = "safal ho toh aage" (Ch
9.10). Bilkul alag! `command &` (background bhej diya) vs `command && next` (safal ho toh next). Ek
akshar ka farak, ulta kaam. Dhyan se.

**Misaalein:**
```
mkdir build && cd build           # bana, safal ho toh andar jao (&&)
backup.sh ; echo "done"           # backup, phir "done" (chahe backup fail — ;)
long_download.sh &                # background mein download (&)
```

> **Yaad rakhne wali baat:** `;` = ek ke baad ek (chahe fail). `&&` = safal ho toh hi agla (Ch 9.10).
> `||` = fail ho toh agla. `&` = background (13.6, jodta nahi). BADA trap: `&` (background) vs `&&`
> (safal-toh-aage) — ek akshar, ulta kaam.

[↑ Back to top](#top)

---

<a id="s13-10"></a>
## 13.10 — Nuances aur caveats

- **`kill` "maarna" nahi, "signal bhejna" hai:** naam daraana hai par `kill` signal bhejta (13.4) —
  aksar band karne ka, par technically message. `kill -15` polite, `kill -9` zabardasti.

- **Pehle `kill` (15), phir `-9` (dohra raha):** seedha `-9` mat maaro — cleanup nahi hoti, data
  corrupt ho sakta (13.5). Polite (15) + wait, phir `-9` last resort. Databases pe khaaskar.

- **`&` background hai, `&&` "aur/safal-toh" — ek akshar ka farak (13.9):** `command &` (background)
  vs `command && next` (safal toh next). Galti se ek `&` daal do jahan `&&` chahiye tha → command
  background mein chali gayi, `next` alag chal gaya. Dhyan se.

- **Background job ka output terminal mein ghus sakta:** `command &` (bina redirect) — uska output
  achanak aapke terminal pe aa sakta jab aap kuch aur kar rahe (confusing). Background jobs ka output
  redirect karo: `command > out.log 2>&1 &` (Ch 6.6).

- **`nohup` ke bina `&` terminal band pe marta (13.8):** sirf `&` (background) SIGHUP se nahi bachta —
  terminal band = job gaya. Lambe kaam ke liye `nohup ... &` ya `tmux`.

- **`ps aux | grep x` mein grep khud dikhta (13.2):** `grep` process khud list mein aata (`grep x`
  wali line). Confuse mat ho — woh aapki asli process nahi. `grep [x]...` trick se hata sakte.

- **PID reuse hota:** ek process khatam hone ke baad uska PID number kisi nayi process ko mil sakta.
  Toh purana PID note karke bahut baad mein `kill` mat karo — ho sakta ab woh koi aur process ho.
  Fresh `ps`/`top` se current PID lo.

- **Zombie/defunct processes:** kabhi `ps` mein `<defunct>` ya "zombie" dikhta — yeh khatam ho chuki
  par parent ne "collect" nahi ki. Aam taur pe ignore karo (parent handle karega); yeh normal hai,
  panic mat karo.

[↑ Back to top](#top)

---

<a id="s13-11"></a>
## 13.11 — Real-life scenarios

**Scenario 1 — "Ek process atki hai, band karni hai."** App hang ho gayi, terminal se `Ctrl+C` kaam
nahi kar raha (shayad woh doosre terminal/background mein). `ps aux | grep appname` (PID dhoondho,
13.2) → `kill PID` (polite, 13.4) → na ruke toh `kill -9 PID` (13.5). Standard "process rokna" flow.

**Scenario 2 — "Server slow hai, kaun kha raha resources?"** `top` (13.3) chalao — CPU/memory ke
hisaab se sorted, sabse bhaari process upar. Mil gaya (jaise ek runaway python 100% CPU) → PID note →
`kill`. Server diagnostic ka pehla step.

**Scenario 3 — "Lamba training job, laptop band karna hai."** ML training ghanton chalega, aap laptop
le ke jaana chahte ho. `nohup python train.py > train.log 2>&1 &` (13.8) — background + SIGHUP-safe +
log file. Laptop band/SSH toot jaye, job chalti rahegi, progress `train.log` mein (`tail -f
train.log`, Ch 4.9). Ch 1.13 Scenario 5 ka poora fix.

**Scenario 4 — "Ek command chalte-chalte kuch aur karna hai."** Aap ek bada file download kar rahe
(foreground, terminal atka), par ek chhota kaam yaad aaya. `Ctrl+Z` (download roko) → `bg` (background
mein chala do) → ab terminal free, apna kaam karo → `fg` (wapas download pe agar chahiye). Ya shuru
se `download &` (13.6).

**Scenario 5 — "Do commands chain — sahi symbol chuno."** "Build karo, aur *safal ho toh* deploy":
`build.sh && deploy.sh` (`&&`, safal-toh, 13.9). Agar `;` use karte (`build.sh ; deploy.sh`) toh
build fail hone pe bhi deploy chal jata — galat/khatarnak. Sahi symbol (`&&`) chuno.

**Saar:** Chapter 13 ne chalte programs ka control diya — `ps`/`top` (dekho, PID lo), `kill`
(`-15` polite → `-9` zabardasti), foreground/background (`&`, `Ctrl+Z`, `bg`, `fg`, `jobs`), `nohup`
(terminal band pe zinda). Sabse practical: pehle polite `kill` phir `-9`, lambe kaam `nohup ... &`
(ya tmux), aur `&` (background) vs `&&` (safal-toh) ka farak.

[↑ Back to top](#top)

---

> **Chapter 13 khatam.** Ab tak: process (chalta program) + PID; `ps aux` (dekho), `top`/`htop`
> (live monitor); signals + `kill` (SIGTERM 15 → SIGKILL 9), `pkill`; foreground/background (`&`,
> `Ctrl+Z`, `bg`, `fg`), `jobs` (`%1`); `nohup ... &` (terminal band pe zinda); aur `;` vs `&&` vs
> `&`. **Agla chapter:** error handling aur robust scripts — `set -euo pipefail`, `trap`, defensive
> scripting, debugging.

[↑ Back to top](#top)