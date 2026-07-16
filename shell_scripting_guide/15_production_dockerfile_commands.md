<a id="top"></a>
# Chapter 15 — Production aur Dockerfile ke liye Sahi Commands Likhna

Yeh chapter thoda alag hai — yeh Docker *sikhane* wala nahi (maan raha hoon aap Docker use karte
ho). Yeh sikhata hai ki **Dockerfiles aur production scripts mein shell commands SAHI tareeke se
kaise likhein** — taaki woh reliable, chhote, aur repeatable hon. Yeh woh "command-writing craft"
hai jo aam local commands aur production-grade commands mein farak banati.

Yeh saara Ch 1-14 pe khada hai — bs focus ab "production mein kaise likhein" pe. Theory + real
patterns.

---

## Is chapter ka index

- [15.1 — Local command vs production command — soch ka farak](#s15-1)
- [15.2 — `RUN` chaining: `&&` se commands jodna (aur kyun)](#s15-2)
- [15.3 — Long commands ko readable rakhna (`\` line-continuation)](#s15-3)
- [15.4 — Non-interactive commands (`-y`, `DEBIAN_FRONTEND`)](#s15-4)
- [15.5 — Cleanup usi layer mein (cache/temp hatao)](#s15-5)
- [15.6 — Idempotent commands (dobara chale toh bhi theek)](#s15-6)
- [15.7 — Exit code safety in chains (fail toh build fail)](#s15-7)
- [15.8 — Pinning aur exact versions (repeatable builds)](#s15-8)
- [15.9 — Nuances aur caveats](#s15-9)
- [15.10 — Real-life scenarios](#s15-10)

---

<a id="s15-1"></a>
## 15.1 — Local command vs production command — soch ka farak

Jo command aap apne terminal pe jaldi se chalate ho, aur jo command ek Dockerfile/production script
mein jaati hai — dono mein soch alag honi chahiye. Yeh farak samajhna is chapter ki neev hai.

**Local (aapke terminal pe) — "bs chal jaye":**
- Ek baar chalani hai, aap dekh rahe ho.
- Fail ho toh aap dekh ke fix kar loge (interactive).
- Prompt aaye ("sure? y/n") toh aap `y` daal doge.
- Cleanup? "baad mein dekh lenge".

**Production/Dockerfile — "reliable, repeatable, chhota":**
- **Repeatable:** har baar exactly same result (aaj, kal, kisi aur machine pe). Ch 1.13 wala "mere
  machine pe chala" nahi chalega.
- **Non-interactive:** koi baithke `y` dabane wala nahi — command khud handle kare (`-y`, 15.4).
- **Fail-safe:** ek command fail ho toh poora build fail ho (chhupe nahi — Ch 14 wali soch, 15.7).
- **Chhota/clean:** Docker images mein har command ek "layer" banati; extra kachra (cache, temp)
  image ko bada karta — usi jagah saaf karo (15.5).

**Ek misaal se farak (package install):**
```
# Local — theek hai
apt-get install nginx

# Production/Dockerfile — sahi tareeka
RUN apt-get update && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*
```
- Local wala interactive (prompt aayega), cleanup nahi, ek fail chhup sakta. Production wala:
  `-y` (non-interactive, 15.4), `&&` (chaining + fail-safe, 15.2), `--no-install-recommends` (chhota,
  15.5), `rm -rf .../lists` (cache cleanup usi layer, 15.5). Yeh saara is chapter mein.

**Yeh chapter ka maqsad:** aapko woh "production reflexes" dena — jab aap Dockerfile ya deploy script
likho, toh automatically `-y`, `&&`, cleanup, pinning aayein. Yeh chhoti aadaten reliable systems
banati.

> **Yaad rakhne wali baat:** Local command = "bs chal jaye" (interactive, aap dekh rahe). Production/
> Dockerfile command = repeatable + non-interactive (`-y`) + fail-safe (`&&`) + chhota (cleanup) +
> pinned. Soch ka farak — yeh chapter woh "production reflexes" deta.

[↑ Back to top](#top)

---

<a id="s15-2"></a>
## 15.2 — `RUN` chaining: `&&` se commands jodna (aur kyun)

Dockerfiles mein aap `&&` se commands jode dekhoge — `RUN a && b && c`. Yeh Ch 9.10/13.9 wala `&&`
hai, par yahan do khaas kaaran se.

**Kaaran 1 — har `RUN` ek "layer" banata (chhota image):**
- Docker mein har `RUN` line ek alag **layer** (image ka ek tukda) banati. Zyada `RUN` = zyada layers
  = bada image + slow.
- Isliye related commands ko **ek `RUN`** mein `&&` se jodo — ek layer, chhota image:
```
# BURA — teen layers
RUN apt-get update
RUN apt-get install -y nginx
RUN rm -rf /var/lib/apt/lists/*

# ACHHA — ek layer (&& se jude)
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*
```

**Kaaran 2 — `&&` fail-safe hai (Ch 9.10):**
- `&&` = "pehla safal ho toh hi agla" (Ch 9.10). Toh `apt-get update && apt-get install` — agar
  `update` fail hua, `install` chalta hi nahi (aur build fail hota, 15.7). Yeh sahi hai — purane
  package-list se install nahi karna chahiye.
- Agar aap `;` (Ch 13.9) use karte (`update ; install`), toh update fail hone pe bhi install chal
  jata — galat/purane data se. Isliye Dockerfiles mein **`&&`** (fail-safe), `;` nahi.

**`&&` se jodna ka poora pattern:**
```
RUN command1 \
    && command2 \
    && command3
```
- `\` (line-continuation, 15.3) se har command apni line pe (readable), `&&` se jude (ek layer +
  fail-safe). Yeh Dockerfile ka standard `RUN` shape.

**Yeh sirf Docker nahi — koi bhi chain jahan "safal ho toh aage" chahiye:** deploy scripts mein bhi
`build && test && deploy` — har step safal ho toh hi agla. `&&` production mein "sequential-with-
safety" ka standard.

> **Yaad rakhne wali baat:** Dockerfile `RUN a && b && c` — do kaaran: (1) ek layer (chhota image,
> `&&` se jodo na ki alag `RUN`), (2) fail-safe (`&&` = safal-toh-aage, Ch 9.10; `;` nahi kyunki
> woh fail pe bhi aage). Standard: `\` + `&&` se readable chain.

[↑ Back to top](#top)

---

<a id="s15-3"></a>
## 15.3 — Long commands ko readable rakhna (`\` line-continuation)

Production commands lambi ho jati hain (kai flags, kai jude commands). Ek line mein sab likhna
padhne-layak nahi rehta. **`\`** (backslash line ke aakhir mein) command ko **kai lines mein** todne
deta.

**`\` — ek command, kai lines:**
```
apt-get install -y --no-install-recommends \
    nginx \
    curl \
    ca-certificates
```
- **`\`** line ke bilkul aakhir mein = "yeh command agli line pe jaari hai" (line abhi khatam nahi).
  Shell teeno lines ko ek command samajhta. Isse lambi command padhne-layak, har cheez apni line pe.
- **ZAROORI — `\` ke baad kuch nahi (space bhi nahi):** `\` line ka aakhri character hona chahiye.
  Agar `\` ke baad ek space bhi hai (`\ `), toh woh line-continuation nahi rahega aur command toot
  jayegi — bahut confusing bug. `\` ke turant baad newline.

**`&&` ke saath (15.2 + 15.3 milke — Dockerfile standard):**
```
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*
```
- Har command apni line (`\` se continue), `&&` se jude (ek layer + fail-safe). Yeh sabse common
  production `RUN` shape — readable AUR sahi.

**Kyun readable matter karta:** 6 mahine baad (ya koi aur) yeh Dockerfile padhega. Ek lambi line mein
sab thusa hua — samajhna mushkil, galti dhoondhna mushkil. Har cheez apni line pe = ek nazar mein
saaf, aur `git diff` mein bhi ek cheez badalne pe sirf woh line dikhti (poori line nahi). Maintainable
code.

> **Yaad rakhne wali baat:** `\` (line ke aakhir mein) = command agli line pe jaari (kai lines mein
> todo, readable). `\` ke baad kuch nahi (space bhi nahi — warna toota). `\` + `&&` = Dockerfile
> standard (har command apni line, jude, fail-safe). Readable = maintainable.

[↑ Back to top](#top)

---

<a id="s15-4"></a>
## 15.4 — Non-interactive commands (`-y`, `DEBIAN_FRONTEND`)

Production/Dockerfile mein **koi insaan nahi baitha** jo prompt ka jawab de. Agar command "sure?
(y/n)" pooche aur koi jawab na de, toh build **atki** reh jayegi (ya fail). Isliye har command ko
**non-interactive** (bina pooche chalne wala) banana zaroori.

**`-y` — "haan" pehle se de do:**
```
apt-get install -y nginx
```
- Bina `-y`, `apt-get install` poochta "install karun? (y/n)". Local mein aap `y` daal dete. Production
  mein koi nahi — build atki. **`-y`** = "**y**es, sab jagah haan maan lo, mat poocho". Ab bina ruke
  install.
- Yeh Ch 3.8 wala `-y`/`-i` ka ulta — `-i` (interactive/poocho) local ke liye, `-y` (yes/mat-poocho)
  production ke liye.

**`DEBIAN_FRONTEND=noninteractive` — aur gehre prompts ke liye:**
```
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata
```
- Kuch packages (jaise `tzdata` — timezone) install ke beech **aur** prompts poochte hain (jaise
  "kaunsa timezone?") jo `-y` bhi nahi rok pata. **`DEBIAN_FRONTEND=noninteractive`** (ek environment
  variable, Ch 5.7) us package ko batata "koi prompt mat poocho, default le lo". Command ke aage laga
  do.
- Yeh ek env-variable hai command ke liye (Ch 5.7 wala local export, par yahan ek command ke aage
  inline).

**Doosre common non-interactive flags:**
- `rm -f` (Ch 4.5) — bina pooche delete (force). `cp -f`, `mv -f` — bina pooche overwrite.
- `git ... --no-edit` — commit message editor na khole.
- `pip install ... --quiet` ya `-q` — kam output.
- General soch: **koi bhi command jo prompt kar sakti, use non-interactive flag do** (`-y`, `-f`,
  `--yes`, `--force`, `--non-interactive` — tool pe depend).

**Kyun zaroori:** ek interactive command production build ko **hang** kar deti (prompt pe atki, koi
jawab dega nahi). Ya CI timeout ho jata. Non-interactive banana = build reliably chalta bina insaan
ke. Yeh automation ki basic zaroorat.

> **Yaad rakhne wali baat:** Production mein koi prompt ka jawab dene wala nahi — commands
> non-interactive banao. `-y` (apt/yum — "haan mat poocho"), `DEBIAN_FRONTEND=noninteractive` (gehre
> prompts), `-f` (force). Interactive command = build hang/timeout. Automation = non-interactive.

[↑ Back to top](#top)

---

<a id="s15-5"></a>
## 15.5 — Cleanup usi layer mein (cache/temp hatao)

Docker images chhote hone chahiye (fast download/deploy). Package installs cache/temp files chhod
jate — unhe **usi `RUN` layer mein** saaf karna zaroori. "Usi layer mein" — yeh key hai.

**Problem — cache image mein reh jata:**
```
RUN apt-get update && apt-get install -y nginx
```
- `apt-get update` package-list `/var/lib/apt/lists/` mein download karta (cache) — yeh install ke
  baad bekaar hai, par image mein reh jata (extra MBs).

**Solution — usi RUN mein cleanup:**
```
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*
```
- Aakhir mein `rm -rf /var/lib/apt/lists/*` = apt ka cache hatao (Ch 4.5). Ab woh cache image mein
  nahi.
- **`--no-install-recommends`** = sirf zaroori packages install karo, "recommended" (extra, aksar
  bekaar) nahi — image aur chhota.

**KEY POINT — cleanup USI `RUN` mein (alag mein nahi):**
```
# BEKAAR — alag RUN mein cleanup se image chhota NAHI hota!
RUN apt-get install -y nginx
RUN rm -rf /var/lib/apt/lists/*      # yeh cache "hatata" par...
```
- Yaad karo 15.2 — har `RUN` ek **layer**. Layer ek baar banne ke baad "freeze" ho jata. Agar aap
  layer-1 mein cache banao aur layer-2 mein hatao — layer-1 mein cache **phir bhi hai** (image mein
  jama), layer-2 sirf "upar se" hatata dikhata. Image chhota nahi hua.
- Isliye cleanup **usi `RUN`** (usi layer) mein hona chahiye jismein cache bana — tab woh layer
  bante-waqt hi saaf, image mein aata hi nahi. Yeh Docker-layer ki soch is chapter ka core insight.

**Common cleanup patterns:**
```
# apt (Debian/Ubuntu)
&& rm -rf /var/lib/apt/lists/*

# pip
&& pip install --no-cache-dir ...       # cache banao hi mat

# apk (Alpine)
&& apk add --no-cache ...               # cache banao hi mat

# general temp
&& rm -rf /tmp/*
```
- Kuch tools mein "cache banao hi mat" flag hota (`--no-cache-dir`, `--no-cache`) — yeh cleanup se
  behtar (banta hi nahi). Jahan flag na ho, `rm -rf` se usi layer mein hatao.

> **Yaad rakhne wali baat:** Image chhota rakho — cache/temp **usi `RUN` layer mein** saaf karo
> (`&& rm -rf /var/lib/apt/lists/*`). Alag `RUN` mein cleanup bekaar (purani layer mein cache reh
> jata). `--no-install-recommends`, `--no-cache-dir` (cache banao hi mat). Layer-soch = key.

[↑ Back to top](#top)

---

<a id="s15-6"></a>
## 15.6 — Idempotent commands (dobara chale toh bhi theek)

**Idempotent** (ek bada shabd — matlab "dobara chalao toh bhi wahi safe result, kuch toota nahi").
Production scripts aksar dobara chalti hain (retry, re-deploy, re-run) — toh commands aise likho ki
dobara chalne pe crash/duplicate na ho.

**Non-idempotent (dobara chalne pe fail/galat):**
```
mkdir /app/data          # dobara chalao -> "File exists" error!
```
- Pehli baar folder banega. Doosri baar (re-run) — "already exists" error, script ruk sakti (`set -e`
  ke saath, Ch 14). Dobara chalna safe nahi.

**Idempotent (dobara chalne pe bhi theek):**
```
mkdir -p /app/data       # dobara chalao -> koi error nahi (Ch 4.2)
```
- **`mkdir -p`** (Ch 4.2 wala) — folder hai toh chup-chaap chhod deta (error nahi). Chahe pehli baar
  ya dasvin baar chalao — safe. Yeh idempotent hai.

**Common idempotent patterns:**
```
mkdir -p dir                       # -p (hai toh theek)
rm -f file                         # -f (nahi hai toh bhi theek, Ch 4.5)
ln -sf target link                 # -f (link phir se banao)
cp -f source dest                  # overwrite (hamesha same result)
[ -f config ] || cp default config # sirf agar nahi hai tab banao (Ch 9.10)
```
- Soch: "agar cheez pehle se woh state mein hai, toh error mat do — bs ensure karo woh state hai".
  `-p`, `-f`, ya `[ condition ] ||` (check-then-do) se.

**Kyun zaroori (production reality):** scripts fail hoke retry hoti, deploys dobara chalte, cron jobs
baar-baar. Agar script sirf "pehli baar" chal sakti (dobara pe crash), toh yeh reliable nahi.
Idempotent commands se script kitni bhi baar chale — safe, same result. Yeh production automation ki
zaroori quality.

> **Yaad rakhne wali baat:** Idempotent = dobara chalao toh bhi safe, same result (crash/duplicate
> nahi). `mkdir -p` (hai toh theek), `rm -f` (nahi hai toh theek), `[ -f x ] || create` (sirf agar
> nahi). Production scripts retry/re-run hoti — idempotent banao.

[↑ Back to top](#top)

---

<a id="s15-7"></a>
## 15.7 — Exit code safety in chains (fail toh build fail)

Production mein sabse khatarnak — ek command **chup-chaap fail** ho par build/script **safal dikhe**
aur aage badh jaye (Ch 14.1 wali soch, ab Docker/pipeline context mein). Isse "aadha-bana" image ya
galat deploy ho sakta.

**Docker mein — `RUN` ka exit code:**
- Docker har `RUN` ka exit code dekhta — non-zero (fail) toh **build ruk jata** (achha). Par yeh
  tabhi kaam karta jab command apna fail-exit sahi de.

**Problem — pipe mein chhupa fail (Ch 6.11/14.4):**
```
RUN curl -s https://example.com/script.sh | bash
```
- `curl` fail ho (URL galat, network) par `bash` (khaali input pe) "success" — poore pipe ka exit 0
  (Ch 6.11). Docker sochega "RUN safal", build aage — jabki script download hi nahi hua! Chhupa fail.

**Solution — `set -o pipefail` (Ch 14.4) `RUN` mein:**
```
RUN set -o pipefail && curl -sf https://example.com/script.sh | bash
```
- `set -o pipefail` (Ch 14.4) — pipe mein koi bhi fail ho toh poora fail. Ab `curl` fail → RUN fail →
  build fail (sahi). Plus `curl -f` (`-f` = fail on HTTP error — curl ka apna, taaki 404 pe bhi fail
  de). (Dockerfile mein `SHELL ["/bin/bash", "-o", "pipefail", "-c"]` se bhi set kar sakte poore
  Dockerfile ke liye.)

**Chained commands — `&&` (15.2) already fail-safe:**
```
RUN make build && make test && make install
```
- `&&` (Ch 9.10) — koi bhi step fail → aage nahi → RUN fail → build fail. Yeh sahi hai. Agar `;` use
  karte, fail chhup jata. `&&` = production chains mein fail-safety.

**Explicit exit check (jab zaroori):**
```
RUN ./configure && make || (echo "Build fail" >&2; exit 1)
```
- Fail pe apna message + explicit `exit 1` (Ch 14.7). Clarity ke liye — build-log mein saaf dikhe
  kya fail hua.

**Soch (Ch 14 ka production version):** production mein "chup-chaap galat" sabse bura. Har command/
chain ka fail **loud** hona chahiye (build/deploy ruke, na ki galat aage badhe). `&&` (chains),
`pipefail` (pipes), `-f`/`-e` flags — sab isliye ki fail chhupe nahi. Fail-fast production ki jaan.

> **Yaad rakhne wali baat:** Production mein fail chhupna sabse bura (aadha-bana image/galat deploy).
> `&&` chains fail-safe (Ch 9.10); pipes mein `set -o pipefail` (Ch 14.4) + `curl -f`; explicit
> `|| (echo; exit 1)` clarity ko. Fail loud ho (build ruke), chup-chaap aage nahi.

[↑ Back to top](#top)

---

<a id="s15-8"></a>
## 15.8 — Pinning aur exact versions (repeatable builds)

**Pinning** = exact version likhna (na ki "latest"). Yeh production ki sabse zaroori aadat repeatable
builds ke liye — taaki aaj, kal, 6 mahine baad, sab jagah **same** build bane. Ch 1.13 wala "mere
machine pe chala" ka bada kaaran yeh bhi hai.

**Problem — "latest"/unpinned (har baar alag):**
```
FROM python:latest              # "latest" — aaj 3.12, kal 3.13 ho sakta!
RUN pip install requests        # koi bhi version — aaj 2.31, kal 2.35
```
- `latest` aur unpinned versions **badalte rehte**. Aaj build mein Python 3.12 + requests 2.31; do
  mahine baad wahi Dockerfile Python 3.13 + requests 2.35 laa sakta — aur kuch toot sakta (breaking
  change). Build "repeatable" nahi — same file, alag result. Debug nightmare.

**Solution — exact versions pin karo:**
```
FROM python:3.12.3-slim         # exact version
RUN pip install requests==2.31.0    # exact (== se)
```
- **`python:3.12.3-slim`** — exact Python version (aur `-slim` = chhota variant). **`requests==2.31.0`**
  — exact package version (`==` = "exactly yeh"). Ab har baar, har jagah — same versions, same build.
  Repeatable.

**Pinning ke levels:**
- **Base image:** `FROM node:20.11.1-alpine` (exact), na ki `node:latest`.
- **Packages:** `pip install x==1.2.3`, `apt-get install nginx=1.24.*` (exact ya close).
- **Lock files:** `package-lock.json`, `requirements.txt` (exact versions), `poetry.lock` — yeh saari
  dependencies pin karti. Production mein lock-file commit karo aur usse install (`pip install -r
  requirements.txt`, `npm ci`).

**Trade-off (jaan-na):** pinning se aapko manually update karna padta (security patches ke liye) —
"latest" automatic update deta par unpredictable. Production mein **predictability > convenience** —
pin karo, phir soch-samajh ke (test karke) update karo. Auto-update se production mein surprise-break
bahut mahanga.

**Yeh Ch 1.13 se juda:** "mere machine pe chala, server pe nahi" ka ek bada kaaran alag versions
hai. Pinning se dono jagah same version — yeh problem katm. Repeatable = reliable.

> **Yaad rakhne wali baat:** Pinning = exact versions (`python:3.12.3`, `requests==2.31.0`), na
> "latest"/unpinned. Kyunki repeatable build chahiye — same file har jagah same result (Ch 1.13 fix).
> Lock files (`requirements.txt`, `npm ci`). Production: predictability > auto-update convenience.

[↑ Back to top](#top)

---

<a id="s15-9"></a>
## 15.9 — Nuances aur caveats

- **`\` ke baad space = tuta command (dohra raha — bahut common):** line-continuation `\` line ka
  bilkul aakhri character ho. Ek trailing space (`\ `) aur command toot jayegi, ajeeb error. Editor
  mein "trailing whitespace dikhao" on karo.

- **Cleanup usi `RUN` mein (15.5 — sabse miss hone wala):** alag `RUN` mein `rm` se image chhota nahi
  hota (purani layer mein cache reh jata). `&&` se usi RUN mein cleanup. Yeh Docker-layer soch bina
  samjhe log alag `RUN` mein cleanup likh dete (bekaar).

- **`apt-get update` aur `install` alag `RUN` mein mat karo:** agar `RUN apt-get update` alag layer
  mein aur `RUN apt-get install` alag mein — Docker cache ke karan `update` purana ho sakta jab
  `install` chale ("cache invalidation" issue). Hamesha `update && install` ek `RUN` mein (15.2).

- **`-y` sab tools mein alag:** `apt-get`/`yum` → `-y`; `pip` → koi prompt nahi (par `--quiet`); `npm`
  → `--yes`; `apk` → `--no-cache` bhi non-interactive. Har tool ka apna non-interactive tareeka —
  `--help` (Ch 3.10) se dekho.

- **Alpine (`sh`) mein bash-syntax nahi (Ch 1.7):** Alpine images mein `/bin/sh` (bash nahi). Agar
  `RUN` mein bash-only syntax (`[[ ]]`, arrays) use kiya toh fail. Alpine pe POSIX `sh` syntax, ya
  pehle `apk add bash`. (Ch 1.9/9.8 wala.)

- **`pipefail` default nahi in Dockerfile `RUN`:** Dockerfile ka `RUN` default `/bin/sh -c` use karta
  (pipefail off). Pipes mein fail chahiye toh `RUN set -o pipefail && ...` ya top pe `SHELL ["/bin/
  bash", "-o", "pipefail", "-c"]`. (15.7.)

- **Secrets Dockerfile mein hardcode mat karo:** `ENV PASSWORD=secret123` ya `RUN ... --password
  secret` — yeh image mein permanently reh jata (koi bhi image inspect karke padh le). Secrets ke
  liye build-args/runtime-env/secret-mounts use karo, hardcode nahi. (Security — Ch 13 course wala.)

- **`COPY` se pehle `.dockerignore`:** `COPY . .` sab kuch copy karta — `.git`, `node_modules`, temp.
  `.dockerignore` (jaise `.gitignore`) se bekaar cheezein skip — chhota image, fast build. (Yeh
  Docker-specific par command-hygiene ka hissa.)

[↑ Back to top](#top)

---

<a id="s15-10"></a>
## 15.10 — Real-life scenarios

**Scenario 1 — "Docker image bahut bada ban raha."** Aapki image 1.5GB hai, chhoti honi chahiye.
Wajah (15.5): alag `RUN` mein cleanup, `--no-install-recommends` nahi, cache reh raha. Fix: `RUN
apt-get update && apt-get install -y --no-install-recommends pkg && rm -rf /var/lib/apt/lists/*` (ek
layer, cleanup usi mein). Image aadhi ho gayi.

**Scenario 2 — "Build machine pe hang ho gaya."** CI build ek prompt pe atka (`Configuring tzdata`
timezone poochh raha), timeout ho gaya. Fix (15.4): `RUN DEBIAN_FRONTEND=noninteractive apt-get
install -y tzdata`. Ab koi prompt nahi, build chalta. Non-interactive = automation ki jaan.

**Scenario 3 — "Do mahine purana Dockerfile ab build nahi ho raha."** Same Dockerfile jo pehle chalti
thi, ab fail. Wajah (15.8): `FROM python:latest` — ab naya Python aa gaya jo kuch tod raha. Fix: pin
karo `FROM python:3.12.3-slim` + `requirements.txt` mein exact versions. Ab repeatable — kabhi bhi
same build.

**Scenario 4 — "Script download-and-run chup-chaap fail ho gaya."** `RUN curl -s url | bash` — curl
fail (404) par build "safal", par script chala hi nahi (aadhi image). Fix (15.7): `RUN set -o
pipefail && curl -sf url | bash` — ab curl fail → build fail (loud). Chhupa fail pakda.

**Scenario 5 — "Deploy script dobara chala, crash ho gaya."** Deploy script `mkdir /app/data` +
`ln -s ...` — pehli baar theek, re-deploy pe "File exists" crash (15.6). Fix: `mkdir -p` (hai toh
theek) + `ln -sf` (force). Ab idempotent — kitni bhi baar deploy, safe. Retry-safe.

**Saar:** Chapter 15 ne local-commands ko production-grade banana sikhaya. `&&` chaining (ek layer +
fail-safe), `\` (readable), `-y`/`DEBIAN_FRONTEND` (non-interactive), cleanup usi layer mein (chhota
image), idempotent (`-p`/`-f`, retry-safe), fail-loud (`pipefail`/`&&`), aur pinning (repeatable).
Yeh saari Ch 1-14 ki cheezein production-lens se — reliable, repeatable, chhote commands. Yeh "craft"
aam engineer aur production-engineer mein farak banati.

[↑ Back to top](#top)

---

> **Chapter 15 khatam.** Ab tak: local vs production soch; `RUN` chaining (`&&` — ek layer +
> fail-safe); `\` line-continuation (readable); non-interactive (`-y`, `DEBIAN_FRONTEND`); cleanup
> usi layer mein (`&& rm -rf`, chhota image); idempotent (`mkdir -p`, `rm -f`, retry-safe); exit-code
> safety (`pipefail`, `&&`, fail-loud); aur pinning (exact versions, repeatable). **Agla chapter:**
> handy tools + cheat-sheet — `tar`, `curl`, `ssh`, `rsync`, aliases, `.bashrc`, aur quick decision
> tables.

[↑ Back to top](#top)