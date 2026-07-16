<a id="top"></a>
# Chapter 14 — Error Handling aur Robust Scripts (galtiyon se surakshit scripts)

Ab tak humne scripts likhi jo "happy path" (sab theek chala toh) pe kaam karti. Par asli production
scripts ko **galtiyon ke liye taiyar** hona chahiye — file na mile, command fail ho, network toot
jaye. Agar script galti ko ignore karke aage chalti rahe, toh **aadha kaam, galat state, ya data-loss**
ho sakta. Yeh chapter batata hai scripts ko "robust" (mazboot) kaise banayein.

Yeh Ch 5.6 (exit code) aur Ch 9.4 (`set -e`) ko poora karta hai. Yeh theory-heavy, production-focused
chapter hai.

---

## Is chapter ka index

- [14.1 — Kyun error handling (bina iske script khatarnak)](#s14-1)
- [14.2 — `set -e` — pehli galti pe ruk jao](#s14-2)
- [14.3 — `set -u` — undefined variable pe error](#s14-3)
- [14.4 — `set -o pipefail` — pipe ki galti pakdo](#s14-4)
- [14.5 — `set -euo pipefail` — teeno ek saath (standard header)](#s14-5)
- [14.6 — `trap` — script ruke toh cleanup karo](#s14-6)
- [14.7 — Manual error check (`||` se exit, exit codes)](#s14-7)
- [14.8 — Defensive scripting (input/file check pehle)](#s14-8)
- [14.9 — Debugging: `set -x`, `bash -x`, echo](#s14-9)
- [14.10 — Nuances aur caveats](#s14-10)
- [14.11 — Real-life scenarios](#s14-11)

---

<a id="s14-1"></a>
## 14.1 — Kyun error handling (bina iske script khatarnak)

Shell scripts ka ek **khatarnak default** hai: agar koi command fail ho jaye, script **rukta nahi**
— woh agli line chala deta, jaise kuch hua hi nahi. Yeh chhota lagta hai par bahut ghatak.

**Ek dangerous misaal:**
```
cd /app/data
rm -rf *
```
- Soch: "data folder mein jao, sab clean karo". Par agar `cd /app/data` **fail** ho (folder nahi
  hai, typo)? Bina error handling ke, script agli line chala deta — `rm -rf *` — par ab aap **galat
  folder** mein ho (jahan `cd` fail hua, wahin reh gaye, shayad home ya `/`)! Poora galat folder saaf
  ho gaya. **Ek fail hui `cd` ne disaster bana diya.**
- Yeh exactly woh case hai jahan `set -e` (14.2) zindagi bachata — `cd` fail hote hi script ruk
  jata, `rm` chalta hi nahi.

**Bina error handling ke kya-kya bura hota:**
- **Galat state:** aadha kaam ho ke ruk gaya, system ajeeb haalat mein.
- **Data loss:** upar wala `rm` disaster, ya galat file overwrite (Ch 6.4 `>`).
- **Chhupi galti:** script "safal" dikhi par andar kuch fail tha — baad mein pata chalta jab nuksaan
  ho chuka.
- **Debug mushkil:** kahan fail hua pata nahi (script chalti rahi, error dab gaya).

**Error handling ka maqsad:** script ko batao "galti ho toh **ruk jao** (aage galat kaam mat karo),
aur **saaf batao** kya-kahan fail hua". Yeh do cheezein (fail-fast + clarity) production scripts ko
safe banati. "Chup-chaap galat" se "ruk ke batao" behtar hai.

> **Yaad rakhne wali baat:** Shell ka khatarnak default — command fail ho toh script rukta nahi,
> aage chala deta (galat state/data-loss). Error handling = "galti pe ruko + saaf batao". Fail-fast
> + clarity. `cd` fail → `rm` galat folder mein = disaster (yeh `set -e` rokta).

[↑ Back to top](#top)

---

<a id="s14-2"></a>
## 14.2 — `set -e` — pehli galti pe ruk jao

**`set -e`** shell ko batata: "koi bhi command **fail** ho (non-zero exit, Ch 5.6) toh script
**turant ruk jao**". Yeh error handling ki sabse zaroori line.

```
#!/bin/bash
set -e

cd /app/data      # agar yeh fail hua...
rm -rf *          # ...toh yeh chalega HI NAHI (script ruk gaya)
```
- Bina `set -e` (14.1 wala disaster): `cd` fail → `rm` galat jagah chal gaya.
- `set -e` ke saath: `cd` fail → exit non-zero → script **turant ruk gaya** → `rm` chala hi nahi.
  Disaster tal gaya. `-e` = **e**xit-on-error.

**Kaise kaam karta:** har command ke baad shell uska exit code (Ch 5.6) check karta. `0` (success) →
aage. Non-zero (fail) → script ruk jao (exit). "Pehli galti pe rok do."

**Kab command "fail" nahi gini jati (zaroori nuance):**
- **`if`/`while` conditions mein:** `if command; then` — yahan command fail hona normal hai (condition
  jhooth), `set -e` isse nahi rokta. Sirf "unexpected" fail rokta.
- **`||` ke saath:** `command || echo "fail"` — yahan aapne fail handle kar liya, `set -e` nahi
  rokta.
- Toh `set -e` sirf woh fails pakadta jo aapne handle nahi kiye — jo "surprise" hain.

**`set -e` ki seema (jaan-na zaroori):** yeh perfect nahi — kuch cases mein fail miss kar deta (jaise
pipe ke beech ka command, isliye `pipefail` chahiye — 14.4; ya function ke andar kuch cases). Par
yeh 90% surprise-fails pakadta hai aur har script mein hona chahiye. Iski seema ke liye baaki `set`
options (14.3-14.5).

> **Yaad rakhne wali baat:** `set -e` = koi command fail (non-zero) ho toh script turant ruko (`-e` =
> exit-on-error). `cd` fail → `rm` nahi chalega (disaster tala). `if`/`while`/`||` wale expected
> fails nahi rokta — sirf surprise fails. Har script ke top pe.

[↑ Back to top](#top)

---

<a id="s14-3"></a>
## 14.3 — `set -u` — undefined variable pe error

**`set -u`** shell ko batata: "koi variable use ho jo **set hi nahi hua** (undefined) toh error do,
khaali maan ke aage mat badho". Yeh Ch 5.12 wala "undefined = khaali" bug pakadta.

**Problem (bina `-u`):**
```
#!/bin/bash
rm -rf "$HOME/$foldr/"      # typo: 'foldr' (asli 'folder')
```
- `$foldr` set nahi hua (typo — `folder` likhna tha). Bina `-u`, shell use **khaali** maan leta —
  toh command ban jata `rm -rf "$HOME/"` = **poora home folder uda do!** Ek typo, aur disaster. (Ch
  5.12 wala.)

**Solution — `set -u`:**
```
#!/bin/bash
set -u
rm -rf "$HOME/$foldr/"      # ab: error "foldr: unbound variable", script ruk gaya
```
- `set -u` ke saath, `$foldr` (undefined) use karte hi shell **error** deta (`unbound variable`) aur
  script ruk jata — `rm` chala hi nahi. Typo turant pakda gaya, disaster tala. `-u` = **u**ndefined-
  error (variables).

**Kyun zaroori:** variable-naam mein typo (`$flie` for `$file`) sabse common bug hai. Bina `-u` woh
chup-chaap khaali chala jata (galat kaam). `-u` se woh loud error banta — turant pata, aage nuksaan
nahi.

**Ek dhyan — jaan-boojh ke khaali/optional variables:** kabhi aap chahte ho ki variable set na ho toh
default use ho (error nahi). Uske liye `${var:-default}` (Ch 5.4 ka advanced) — "agar var set nahi
toh default". `set -u` ke saath yeh syntax use karo optional variables ke liye. Jaise `${1:-}` = "agar
$1 nahi diya toh khaali (error nahi)".

> **Yaad rakhne wali baat:** `set -u` = undefined (set-nahi-hua) variable use ho toh error do (khaali
> maan ke aage mat badho). Typo (`$foldr`) turant pakda jata — chup-chaap khaali-chalne ka disaster
> (Ch 5.12) rukta. Optional var ke liye `${var:-default}`.

[↑ Back to top](#top)

---

<a id="s14-4"></a>
## 14.4 — `set -o pipefail` — pipe ki galti pakdo

Yeh Ch 6.11 wali gutthi suljhata — "pipe mein beech ka command fail ho toh chhup jata". `set -o
pipefail` use pakadta.

**Problem (bina pipefail):**
```
cat nahi_hai.txt | grep "error" | wc -l
```
- Yaad karo Ch 6.11 — pipe mein exit code sirf **aakhri** command (`wc -l`) ka milta. Yahan `cat
  nahi_hai.txt` fail hua (file nahi), par `wc -l` safal (usne 0 gina), toh poore pipe ka exit `0`
  (success!) — jabki asal mein pehla command fail tha. Galti **chhup gayi**. `set -e` (14.2) bhi ise
  miss kar deta (kyunki aakhri command success).

**Solution — `set -o pipefail`:**
```
#!/bin/bash
set -o pipefail
cat nahi_hai.txt | grep "error" | wc -l    # ab: poora pipe FAIL (kyunki cat fail)
```
- `set -o pipefail` = "pipe ka exit code = agar **koi bhi** command fail ho toh fail (sirf aakhri
  nahi)". Ab `cat` fail → poora pipe fail → (`set -e` ke saath) script ruk gaya. Chhupi galti ab loud.

**`set -e` ke saath kyun zaroori:** `set -e` "fail pe ruko" karta, par pipe ki galti use dikhti hi
nahi thi (aakhri success). `pipefail` pipe ki asli fail dikhata, phir `set -e` use pakad ke rokta.
Dono milke pipe-fails handle karte. Isliye teeno saath (14.5).

**Kab matter karta:** jab aap pipes use karo (Ch 6 — bahut hota) aur beech ka command fail ho sakta
(file na mile, command error). Bina pipefail woh chhup jata; iske saath pakda jata. Production data-
pipelines mein zaroori.

> **Yaad rakhne wali baat:** `set -o pipefail` = pipe ka exit = koi bhi command fail toh fail (sirf
> aakhri nahi, Ch 6.11 fix). Bina iske beech ki galti chhup jati (aakhri success dikhta). `set -e` ke
> saath milke pipe-fails pakadta. Pipes use karo toh zaroori.

[↑ Back to top](#top)

---

<a id="s14-5"></a>
## 14.5 — `set -euo pipefail` — teeno ek saath (standard header)

Teeno options (14.2-14.4) ko ek line mein jodte hain — yeh production scripts ka **standard header**
hai. Ch 9.4 mein teaser diya tha; ab poora.

```
#!/bin/bash
set -euo pipefail
```
- **`-euo pipefail`** = `-e` (fail pe ruko) + `-u` (undefined variable error) + `-o pipefail` (pipe
  fail pakdo) — teeno ek saath (Ch 3.6 flags jodna: `-e -u -o pipefail` → `-euo pipefail`).
- Yeh do lines (shebang + set) har achhi production script ka top hain. Isse script "strict mode"
  mein aa jata — galtiyon pe ruk-ke-batata, chup-chaap-galat nahi.

**Har ek ne kya bacha (recap):**
- `-e` — command fail → ruko (14.2, `cd`-`rm` disaster).
- `-u` — undefined variable → error (14.3, `$foldr` typo disaster).
- `-o pipefail` — pipe fail → pakdo (14.4, chhupi pipe galti).

**Kyun "standard":** yeh teen sabse common script-disasters (silent fail, typo, pipe-fail) ek saath
rokte. Bina inke script "optimistic" (sab theek maan ke) chalti — jo production mein khatarnak.
Inke saath script "paranoid" (har galti pe savdhaan) ban jati. Isiliye experienced log har script
mein yeh daalte.

**Ek chhota trade-off (jaan-na):** `set -e`/`-u` kabhi over-strict ho sakte — jaise ek command jo
"fail" hona expected hai (jaise `grep` ka no-match, Ch 12.10) script ko rok sakta. Aise jagah aap
`command || true` (Ch 9.10 — "fail ho toh bhi theek") likhte ho — "yeh fail expected hai, ruko mat".
Toh strict mode + selective `|| true` jahan zaroori = balance.

**Poora template (yeh yaad rakho — har script aise shuru):**
```
#!/bin/bash
set -euo pipefail

# yahan aapka script...
```

> **Yaad rakhne wali baat:** `set -euo pipefail` = production script ka standard header (`-e` fail-
> ruko + `-u` undefined-error + `pipefail` pipe-fail). Teen common disasters rokta = "strict mode".
> Expected fail ho toh `command || true`. Har script `#!/bin/bash` + `set -euo pipefail` se shuru.

[↑ Back to top](#top)

---

<a id="s14-6"></a>
## 14.6 — `trap` — script ruke toh cleanup karo

**`trap`** ek "safety net" hai — yeh batata "jab script ruke/exit ho (chahe safal ya fail), toh yeh
cleanup-kaam zaroor karo". Jaise temp files hatana, lock release karna. Isse `set -e` (fail pe ruko)
ke saath bhi cleanup na chhoote.

**Problem:** maan lo script ek temp file banati, kaam karti, phir temp hatati. Par agar beech mein
fail ho (`set -e` ne roka), toh temp-hatane wali line chali hi nahi — temp file reh gayi (kachra).

**Solution — `trap`:**
```
#!/bin/bash
set -euo pipefail

tempfile="/tmp/mydata_$$"       # $$ = PID, unique naam (Ch 5.6)

cleanup() {
    rm -f "$tempfile"
    echo "Cleanup ho gaya"
}
trap cleanup EXIT

# ab kaam...
echo "data" > "$tempfile"
# ... chahe yahan fail ho ya safal, cleanup ZAROOR chalega
```
- **`trap cleanup EXIT`** = "jab script **EXIT** ho (kisi bhi tarah — safal, fail, ya `Ctrl+C`), toh
  `cleanup` function chalao" (Ch 10.8 function). `cleanup` temp file hata deta.
- Ab chahe script safal ho ya beech mein fail (`set -e`), `trap` ka `cleanup` **hamesha** chalega —
  temp file kabhi nahi reh jata. Yeh "chahe kuch bhi ho, yeh zaroor karo" ka tareeka.

**`trap` ka structure — `trap 'kya-karo' KAB`:**
- **KAB (signals/events):** `EXIT` (script khatam, sabse common), `ERR` (koi command fail ho), `INT`
  (Ctrl+C, SIGINT Ch 13.4), `TERM` (kill).
- **kya-karo:** ek function (jaise `cleanup`) ya commands.
```
trap cleanup EXIT              # exit pe cleanup
trap 'echo "Roka gaya!"' INT   # Ctrl+C pe message
```

**Kab kaam ka:** jab script koi "temporary state" banati jise saaf karna zaroori — temp files, lock
files, background processes (Ch 13), mounted drives. `trap ... EXIT` ensure karta ki woh cleanup
chhoote na, chahe script kaise bhi khatam ho. Production scripts mein common.

> **Yaad rakhne wali baat:** `trap cleanup EXIT` = "script kisi bhi tarah exit ho (safal/fail/Ctrl+C)
> toh `cleanup` zaroor chalao". Temp files/locks hatane ke liye — `set -e` fail pe bhi cleanup na
> chhoote. `trap 'kya' KAB` (EXIT/ERR/INT). Safety net.

[↑ Back to top](#top)

---

<a id="s14-7"></a>
## 14.7 — Manual error check (`||` se exit, exit codes)

`set -e` automatic hai (fail pe ruko). Par kabhi aap **khud** check karna chahte ho — apna message
dena, ya alag kaam karna fail pe. Iske tareeke:

**`||` se exit + message (Ch 9.10 wala):**
```
cp important.txt backup/ || { echo "Backup FAIL hua!"; exit 1; }
```
- **`command || { ... }`** = "command fail ho toh yeh block chalao" (Ch 9.10 `||`). Yahan: copy fail
  → message + `exit 1`. `{ ... }` mein kai commands group (echo + exit). Yeh "fail pe apna handling"
  ka aam tareeka.

**Exit code check karke (`$?`, Ch 5.6):**
```
./deploy.sh
if [ $? -ne 0 ]; then
    echo "Deploy fail — rollback kar rahe"
    ./rollback.sh
    exit 1
fi
```
- `$?` (pichhli command ka exit, Ch 5.6) check — non-zero (fail) → rollback. Jab fail pe kuch
  **specific** karna ho (jaise rollback), na ki bs ruk jana. **Note:** `$?` turant check karo (Ch
  5.12 — beech mein command na aaye).

**Apni script se sahi exit code do (`exit N`):**
```
if [ ! -f "$input" ]; then
    echo "Error: input file nahi mili" >&2
    exit 1
fi
# ... kaam safal ...
exit 0
```
- **`exit 1`** (fail) / **`exit 0`** (success) — aapki script khud sahi exit code de (Ch 5.6). Isse
  jo koi aapki script ko call kare (ya `&&`/`||` mein use kare), use pata chale safal hui ya nahi.
  **`>&2`** = error message ko stderr pe bhejo (Ch 6.6 — errors alag channel pe, best practice).

**`set -e` vs manual — kab kaunsa:**
- **`set -e`** — general "koi bhi surprise fail → ruko" (default safety, har script).
- **Manual (`||`/`$?`)** — jab fail pe **specific action** chahiye (message, rollback, retry) na ki
  sirf ruk jana. Dono saath use hote — `set -e` background safety, manual jahan khaas handling.

> **Yaad rakhne wali baat:** Manual error check: `command || { echo "fail"; exit 1; }` (fail pe apna
> handling), ya `$?` check (Ch 5.6, specific action jaise rollback). Apni script `exit 0`/`exit 1`
> de (caller ko pata chale). Errors `>&2` (stderr). `set -e` general, manual jahan khaas action.

[↑ Back to top](#top)

---

<a id="s14-8"></a>
## 14.8 — Defensive scripting (input/file check pehle)

**Defensive scripting** = script ke shuru mein hi sab "zaroori shartein" check karo — file hai?
input mila? tool installed hai? — **pehle**, taaki baad mein beech mein crash na ho. "Pehle jaanch,
phir kaam." Yeh Ch 11.5 (validation) ka bada roop.

**Ek defensive script ka shuru (yeh pattern yaad rakho):**
```
#!/bin/bash
set -euo pipefail

# 1. Arguments mile? (Ch 11.5)
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input-file>" >&2
    exit 1
fi

input="$1"

# 2. Input file actually hai? (Ch 9.7)
if [ ! -f "$input" ]; then
    echo "Error: '$input' nahi mili" >&2
    exit 1
fi

# 3. Zaroori tool installed hai?
if ! command -v jq &> /dev/null; then
    echo "Error: 'jq' install nahi hai" >&2
    exit 1
fi

# Ab safe — asli kaam shuru
echo "Processing $input..."
```
- Teen check pehle: (1) arguments, (2) file maujood, (3) tool installed — har fail pe clear message +
  `exit 1`. Sab pass hone ke *baad* asli kaam. Ab beech mein "file nahi mili" wala crash nahi hoga.

**`command -v tool` — tool installed hai ya nahi (naya, kaam ka):**
- **`command -v jq`** = "kya `jq` command maujood hai?" (Ch 3.11 `which` jaisa, par script-safe).
  `&> /dev/null` (Ch 6.7 — output phenko, sirf success/fail chahiye). `! command -v jq` = "agar jq
  NAHI hai" (Ch 9.10 `!`). Script jo external tool pe depend kare, use pehle check kare — warna
  beech mein "command not found".

**Defensive checks ki list (jo relevant ho):**
- Zaroori arguments diye? (`$#`, `-z`)
- Files/folders maujood? (`-f`, `-d`, `-e`)
- Zaroori tools installed? (`command -v`)
- Zaroori permissions? (`-r`, `-w`, `-x`, Ch 7)
- Zaroori environment variables set? (`-z "${VAR:-}"`)

**Kyun "defensive":** jaise defensive driving (dusron ki galti maan ke chalna), defensive scripting
"kuch bhi galat ho sakta" maan ke pehle check karta. Yeh scripts ko production-ready banata — galat
input pe saaf error (crash/half-work nahi). Thodi extra lines, par bahut reliability.

> **Yaad rakhne wali baat:** Defensive scripting = shuru mein sab shartein check (arguments, files,
> tools, permissions) + clear error + `exit 1`, PHIR asli kaam. `command -v tool` = tool installed?
> "Pehle jaanch phir kaam" — beech-crash se bachao, production-ready.

[↑ Back to top](#top)

---

<a id="s14-9"></a>
## 14.9 — Debugging: `set -x`, `bash -x`, echo

Jab script galat kaam kare aur samajh na aaye kyun, toh **debugging** — dekhna ki script actually kya
kar rahi, line-by-line. Teen tareeke:

**`set -x` — har command chalne se pehle dikhao (trace):**
```
#!/bin/bash
set -x           # trace ON
name="Pragyesh"
echo "Hello $name"
```
- **`set -x`** = "har command ko chalane se **pehle**, uska (expanded) roop screen pe dikhao" (`-x` =
  execution trace). Output mein `+` ke saath har line dikhti jaisi woh actually chali (variables ki
  values ke saath):
  ```
  + name=Pragyesh
  + echo 'Hello Pragyesh'
  Hello Pragyesh
  ```
- Isse dikhta hai ki `$name` kya bana, kaunsi line chali. "Script andar kya kar rahi" ka X-ray.

**`set +x` — trace band karo:**
```
set -x           # ON
# ... jo debug karna hai ...
set +x           # OFF (yahan se normal)
```
- **`+x`** (plus) = trace OFF. Sirf ek hisse ko debug karna ho toh `set -x` ... `set +x` ke beech
  rakho. (`-` = ON, `+` = OFF — yeh ulta lagta par yehi convention.)

**`bash -x script.sh` — poori script trace karo (bina script badle):**
```
bash -x myscript.sh
```
- Script ke andar `set -x` daale bina, use `bash -x` se chalao — poori script trace ho jayegi. Jab
  aap script badalna nahi chahte, bs ek baar dekhna hai kya ho raha. Quick debugging.

**Sabse simple — `echo` daalo (print debugging):**
```
echo "DEBUG: name is '$name', count is '$count'"
```
- Beech-beech mein `echo` daal ke variables ki values dekho — "yahan tak name kya tha?". Sabse basic
  par bahut effective. (Ch 5 wala `echo "[$var]"` — brackets se khaali bhi dikhta.) Baad mein yeh
  debug-echos hata dena.

**Debugging ka flow:** (1) `bash -x script.sh` — kahan galat ho raha, kaunsi line pe. (2) us jagah
`echo` ya `set -x`/`set +x` se detail. (3) variable values check (`echo "[$var]"`). Yeh "script kya
soch rahi" dikha deta.

> **Yaad rakhne wali baat:** Debugging: `set -x` (har command trace, `+` ke saath dikhta), `set +x`
> (band), `bash -x script.sh` (poori script trace bina badle), aur `echo "DEBUG: $var"` (simple print
> debugging). Galat kaam? `bash -x` se dekho kahan-kya ho raha.

[↑ Back to top](#top)

---

<a id="s14-10"></a>
## 14.10 — Nuances aur caveats

- **`set -e` sab kuch nahi pakadta:** yeh perfect nahi — function ke andar, `if`/`while` conditions,
  ya command-substitution `$(...)` mein kuch fails miss ho sakte. Isliye critical jagah manual check
  (14.7) bhi rakho. `set -e` "zyadatar" safety, "poori" nahi.

- **`set -e` + expected fail = accidental exit:** `grep "x" file` no-match pe fail (Ch 12.10) hota —
  `set -e` ke saath yeh script rok dega (jabki aap sirf check kar rahe the). Aise jagah `grep "x"
  file || true` ("fail theek hai") ya `if grep -q ...` use karo. Strict mode ke saath expected fails
  handle karo.

- **`set -u` + optional variable = error:** agar variable jaan-boojh ke optional hai (jaise ek flag
  jo user de bhi na de), `set -u` use undefined pe error dega. Fix: `${var:-default}` ya `${var:-}`
  (14.3) — "set nahi toh default/khaali, error nahi".

- **`trap` sirf usi shell mein (background nahi):** `trap ... EXIT` current shell/script ke exit pe
  chalta. Background processes (Ch 13, `&`) ya subshells alag — unke liye alag handling. Basic cleanup
  ke liye `trap EXIT` kaafi.

- **`pipefail` `set -e` ke bina adhoora:** `set -o pipefail` pipe ka fail-exit-code *set* karta, par
  us pe *rukta* `set -e` (14.2). Dono saath (`-eo pipefail`) chahiye — akela pipefail sirf exit-code
  set karega, rokega nahi.

- **`>&2` errors ke liye (14.7):** error messages stdout (normal output) pe nahi, stderr pe bhejo
  (`echo "error" >&2`, Ch 6.6). Taaki jab koi aapke script ka output pipe/redirect kare, error alag
  dikhe aur normal output mein na ghuse. Best practice.

- **Debug-echos production mein hatao:** `echo "DEBUG: ..."` (14.9) debugging ke liye — kaam ho gaya
  toh hata do (ya `set -x`/`+x` use karo taaki toggle ho). Warna production output mein debug-kachra.

- **`set -euo pipefail` sab jagah copy mat karo bina samjhe:** yeh strict hai — kuch legacy/simple
  scripts mein over-strict ho ke chalti hui cheez tod sakta. Samajh ke lagao (khaaskar `-e` aur
  expected fails). Par nayi production scripts mein default yehi.

[↑ Back to top](#top)

---

<a id="s14-11"></a>
## 14.11 — Real-life scenarios

**Scenario 1 — "`cd` fail hua, `rm` ne galat jagah safai kar di."** Classic disaster (14.1) — bina
`set -e`, `cd /app/data` (typo/na-maujood) fail hua par script `rm -rf *` current folder mein chala
gaya. Fix: har script `set -euo pipefail` (14.5) se shuru — `cd` fail hote hi ruk jata, `rm` chalta
hi nahi. Yeh #1 error-handling lesson.

**Scenario 2 — "Variable typo se home folder uda."** `rm -rf "$HOME/$bakcup/"` (typo — `backup`).
Bina `set -u`, `$bakcup` khaali → `rm -rf "$HOME/"` = disaster (14.3). `set -u` se typo turant
"unbound variable" error, script ruk gaya. Home safe.

**Scenario 3 — "Deploy fail hua, temp files reh gaye."** Deploy script temp files banati thi, beech
mein fail hui (`set -e` ne roka), temp reh gaye (kachra jama). Fix: `trap cleanup EXIT` (14.6) — chahe
fail ho ya safal, cleanup zaroor chalega, temp hamesha saaf. Production scripts mein standard.

**Scenario 4 — "Data pipeline chup-chaap galat result de raha."** `cat data.csv | process | save` —
`cat` fail (file missing) par `save` "success" (khaali data save), poora pipe success dikha. Galat
data save ho gaya bina error (14.4). Fix: `set -o pipefail` — pehla fail poore pipe ko fail banata,
`set -e` rokta. Chhupi galti loud.

**Scenario 5 — "Script galat chal rahi, samajh nahi kyun."** Ek script galat output de rahi, code
theek dikhta. `bash -x script.sh` (14.9) chalaya — trace mein dikha ki ek variable expected se alag
value bana raha tha (`$file` khaali tha kyunki argument nahi mila). Turant pata chal gaya. `bash -x`
= debugging ka X-ray.

**Saar:** Chapter 14 scripts ko production-safe banata. `set -euo pipefail` (standard header —
fail-ruko + undefined-error + pipe-fail), `trap` (cleanup zaroor), manual check (`||`/`$?` specific
handling), defensive scripting (pehle sab check), aur debugging (`bash -x`, `echo`). Sabse practical:
**har script `#!/bin/bash` + `set -euo pipefail` se shuru**, temp-state pe `trap cleanup EXIT`, aur
shuru mein defensive checks. Yeh "chup-chaap galat" se "ruk ke batao" ka farak hai.

[↑ Back to top](#top)

---

> **Chapter 14 khatam.** Ab tak: error handling kyun (silent-fail disaster); `set -e` (fail pe ruko),
> `set -u` (undefined-error), `set -o pipefail` (pipe-fail), `set -euo pipefail` (standard header);
> `trap cleanup EXIT` (cleanup zaroor); manual check (`||`/`$?`/`exit`/`>&2`); defensive scripting
> (`command -v`, pehle-check); debugging (`set -x`, `bash -x`, `echo`). **Agla chapter:** production/
> Dockerfile ke liye sahi commands likhna — RUN chaining, cleanup, idempotency, non-interactive.

[↑ Back to top](#top)