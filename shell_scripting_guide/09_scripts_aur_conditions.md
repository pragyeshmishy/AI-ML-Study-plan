<a id="top"></a>
# Chapter 09 — Scripts likhna aur Conditions (agar-toh logic)

Ab tak humne commands ek-ek karke chalaye. Ab hum unhe ek **file mein likhke** ek "script" banayenge
— taaki poora kaam ek baar likho aur baar-baar chalao. Aur phir sikhenge **conditions** (agar-toh
logic) — taaki script "soch" sake ("agar file hai toh yeh karo, warna woh").

Yeh do cheezein milke aapko "commands chalane wale" se "scripts likhne wale" bana deti hain. Yeh
theory-heavy chapter hai — shebang, script chalane ke teen tareeke, aur har comparison-operator ka
matlab kholega.

---

## Is chapter ka index

- [9.1 — Script kya hai (commands ki ek file)](#s9-1)
- [9.2 — Shebang `#!/bin/bash` — pehli line ka raaz](#s9-2)
- [9.3 — Script chalane ke teen tareeke (`bash x.sh` vs `./x.sh` vs `source`)](#s9-3)
- [9.4 — Comments (`#`) aur script ko safe banane wali lines (`set -e`)](#s9-4)
- [9.5 — Condition kya hai: exit code se "sach/jhooth"](#s9-5)
- [9.6 — `if / then / else / fi` — basic structure](#s9-6)
- [9.7 — `[ ]` test: file aur number comparisons](#s9-7)
- [9.8 — `[ ]` vs `[[ ]]` — farak (aur bash mein kaunsa)](#s9-8)
- [9.9 — String comparisons (`=`, `-z`, `-n`)](#s9-9)
- [9.10 — `&&`, `||`, `!` — commands ko logic se jodna](#s9-10)
- [9.11 — `case` — kai options mein se ek chunna](#s9-11)
- [9.12 — Nuances aur caveats](#s9-12)
- [9.13 — Real-life scenarios](#s9-13)

---

<a id="s9-1"></a>
## 9.1 — Script kya hai (commands ki ek file)

**Script** ek simple text file hai jismein aap **commands ek ke baad ek likhte ho** — wahi commands
jo aap terminal pe type karte. Jab aap script "chalate" ho, shell us file ki har line ko upar se
neeche, ek-ek karke chala deta — jaise aapne khud type ki ho.

**Kyun script banayein (jab terminal pe chala hi sakte hain):**
- **Dobara use:** ek baar likho, hazaar baar chalao. Roz ke kaam (backup, deploy, cleanup) baar-baar
  type karne ke bajaye ek script.
- **Kam galti:** 10 commands haath se chalao toh ek bhoolne/galat karne ka risk. Script mein woh
  fixed hain — hamesha same order, same tareeka.
- **Doosron ko do:** ek script kisi aur ko de sakte ho, woh bina samjhe chala le.
- **Automate:** script ko schedule kar sakte ho (jaise roz raat 2 baje chale — cron, Ch 16).

**Ek chhota script kaisa dikhta (file `hello.sh`):**
```
#!/bin/bash
echo "Namaste!"
echo "Aaj ki date: $(date)"
```
- Teen lines. Pehli (`#!/bin/bash`) ek special line hai (9.2). Baaki do woh commands jo aap terminal
  pe bhi chala sakte the (`echo`, `$(date)` — Ch 5). Jab yeh script chalega, dono echo chalenge.

**`.sh` extension:** scripts ka naam aksar `.sh` pe khatam hota (`hello.sh`, `deploy.sh`) — `sh` =
shell. Yeh zaroori nahi (shell ko farak nahi padta), par **convention** hai taaki insaan dekh ke
samajh jaye "yeh ek shell script hai". (Yaad karo Ch 3 — extension shell ke liye matlab nahi rakhta,
par insaan ke liye clarity.)

> **Yaad rakhne wali baat:** Script = commands ki text file, shell upar-se-neeche chala deta (jaise
> aapne type ki hon). Fayda: dobara-use, kam galti, automate. Naam `.sh` (convention, insaan ke
> liye).

[↑ Back to top](#top)

---

<a id="s9-2"></a>
## 9.2 — Shebang `#!/bin/bash` — pehli line ka raaz

Script ki pehli line aksar `#!/bin/bash` hoti hai. Yeh ajeeb symbols hain — inhe **shebang** kehte
hain (`#!` ka naam "shebang" = "sh" + "bang", jahan `!` ko "bang" bolte hain). Yeh line batati hai
ki **is script ko kaunse program se chalana hai**.

**Tod ke:**
```
#!/bin/bash
```
- **`#!`** = shebang marker — "yeh line batati hai kaunsa interpreter (chalane wala program) use
  karna hai". Yeh file ke bilkul shuru mein (pehli line, pehla character) hona chahiye.
- **`/bin/bash`** = us program ka path (Ch 2 wala) — matlab "isko **bash** se chalao, jo `/bin/bash`
  file mein hai". (Yaad karo Ch 1 — `/bin/bash` = root ke bin folder mein bash program.)

**Kyun zaroori (yeh Chapter 1 se juda):** yaad karo alag-alag shell hote hain (bash, zsh, sh — Ch
1.7). Ek script bash ke liye likhi ho sakti, ya sh ke liye. Shebang batata hai "confusion mat karo —
ise **bash** se chalao". Bina shebang ke, system guess karta (ya aapka default shell use karta), jo
galat ho sakta — aur "mere machine pe chala, server pe nahi" wali problem (Ch 1.13) aati.

**Common shebangs:**
- `#!/bin/bash` — bash se chalao (sabse common, aapke scripts ke liye).
- `#!/bin/sh` — sh (POSIX) se — maximum portable (Ch 1.9), Alpine Docker jaise jagah.
- `#!/usr/bin/env python3` — Python script ke liye ("env se python3 dhoondh ke chalao").

**`#!/usr/bin/env bash` — ek behtar tareeka:** kabhi bash `/bin/bash` mein na hokar kahin aur ho
(alag systems). `#!/usr/bin/env bash` = "env command se bash dhoondho, jahan bhi ho" — yeh zyada
portable hai. Par `#!/bin/bash` bhi 99% jagah chalta.

**Yaad karo Ch 1.13:** "mere Mac (zsh) pe chala, server (bash) pe nahi" — iska fix yehi shebang tha.
Script ke top pe `#!/bin/bash` likho aur bash-syntax use karo, toh woh dono jagah bash se chalegi.

> **Yaad rakhne wali baat:** Shebang `#!/bin/bash` = script ki pehli line, batati "isko bash se
> chalao" (`#!` = shebang marker, `/bin/bash` = kaunsa program). Zaroori taaki sahi shell chale
> (Ch 1 wali portability). `#!/usr/bin/env bash` zyada portable.

[↑ Back to top](#top)

---

<a id="s9-3"></a>
## 9.3 — Script chalane ke teen tareeke (`bash x.sh` vs `./x.sh` vs `source`)

Ek script ko chalane ke teen tareeke hain — teeno thoda alag kaam karte hain. Yeh farak samajhna
zaroori hai.

**1. `bash script.sh` — bash ko seedha do:**
```
bash hello.sh
```
- Aap seedha `bash` command ko script ki file dete ho — "yeh file chalao". Yahan `x` (execute)
  permission ki **zaroorat nahi** (Ch 7.7 wala), aur shebang bhi ignore hota (kyunki aapne khud bash
  bol diya). Ek **naya bash** khulta hai, script chalti, phir band. Quick testing ke liye achha.

**2. `./script.sh` — file ko khud chalao (proper tareeka):**
```
./hello.sh
```
- Yeh Ch 7.7 wala — `./` (yehi folder se) + file ko seedha chalana. Iske liye **`x` permission
  zaroori** (`chmod +x hello.sh` pehle), aur **shebang zaroori** (taaki system jaane kaunse shell se
  chalana). Yeh "proper" tareeka hai — script ek asli program ki tarah chalti. Ek naya shell (jo
  shebang mein likha) khulta hai script ke liye.

**3. `source script.sh` (ya `. script.sh`) — CURRENT shell mein chalao:**
```
source hello.sh
```
- Yeh sabse alag hai (Ch 8.9 mein `.zshrc` ke saath dekha). Upar ke do naya shell kholte hain script
  ke liye; `source` script ko **aapke current shell mein hi** chalata — koi naya shell nahi.
- **Farak kyun matter karta:** agar script koi variable set kare (`naam=X`) ya `cd` kare, toh:
  - `bash`/`./` se — woh naye shell mein hua, aapke shell pe koi asar nahi (script khatam, sab gaya).
  - `source` se — woh aapke shell mein hua, toh variable/`cd` **aapke shell mein reh jata**.
- Isiliye `.zshrc` ko `source` karte hain (Ch 8.9) — taaki settings current shell mein aayein.

**Ek table (yaad rakhne ko):**

| Tareeka | Naya shell? | `x` bit chahiye? | Shebang use? | Variable/cd aapke shell pe? |
|---|---|---|---|---|
| `bash x.sh` | Haan | Nahi | Nahi | Nahi |
| `./x.sh` | Haan | **Haan** (`chmod +x`) | **Haan** | Nahi |
| `source x.sh` | **Nahi** (current) | Nahi | Nahi | **Haan** (reh jata) |

**Kab kaunsa:**
- **Testing/quick run** → `bash x.sh` (koi chmod jhanjhat nahi).
- **Proper script chalana** → `./x.sh` (ek baar `chmod +x`, phir program ki tarah).
- **Settings/variables current shell mein chahiye** → `source x.sh` (jaise `.zshrc`).

> **Yaad rakhne wali baat:** `bash x.sh` (quick, `x` bit nahi chahiye), `./x.sh` (proper, `chmod +x`
> + shebang chahiye), `source x.sh` (current shell mein — variable/`cd` reh jata, `.zshrc` ke liye).
> Pehle do naya shell; source current.

[↑ Back to top](#top)

---

<a id="s9-4"></a>
## 9.4 — Comments (`#`) aur script ko safe banane wali lines (`set -e`)

**Comments — `#` se:**
```
# Yeh ek comment hai — shell ise ignore karta
echo "Hello"    # yeh bhi comment (command ke baad)
```
- **`#`** ke baad jo bhi likho, shell use **ignore** karta (chalata nahi). Yeh insaanon ke liye
  notes hain — "yeh line kya kar rahi, kyun". (Dhyan — shebang `#!` special hai, woh comment nahi.)
- **Kyun zaroori:** 3 mahine baad apni hi script padho toh comments batate hain "yeh kya tha". Ya
  doosre ko samajhne mein. Achhi script mein comments hote.

**Script ko "safe" banane wali teen lines (top pe daalte hain):**
```
#!/bin/bash
set -e
set -u
set -o pipefail
```
Yeh teen lines (aksar ek saath `set -euo pipefail`) script ko galtiyon pe rukne wali banati hain.
Inka poora detail Chapter 14 (error handling) mein, par abhi jaan lo:
- **`set -e`** = "koi command fail ho (non-zero exit, Ch 5.6) toh script **turant ruk jao**". Bina
  iske, script fail hone ke baad bhi agli lines chalata rehta (jo khatarnak — aadha kaam, galat
  state). `-e` = exit-on-error.
- **`set -u`** = "koi undefined variable use ho toh error do" (Ch 5.12 wala — typo se khaali variable
  ka bug pakadta). `-u` = undefined-error.
- **`set -o pipefail`** = "pipe (Ch 6) mein beech ka command fail ho toh use pakdo" (warna sirf
  aakhri ka exit dikhta, Ch 6.11).

**Abhi bs itna:** achhi production script ka top aksar `#!/bin/bash` + `set -euo pipefail` hota. Yeh
"safety belt" hai — galti hone pe script chup-chaap galat kaam karne ke bajaye ruk jati. (Ch 14 mein
kyun aur kaise, poora.)

> **Yaad rakhne wali baat:** `#` = comment (shell ignore karta, insaan ke notes). `set -e` (fail pe
> ruko), `set -u` (undefined variable pe error), `set -o pipefail` (pipe fail pakdo) — script ki
> safety belt, top pe daalte. Poora Ch 14.

[↑ Back to top](#top)

---

<a id="s9-5"></a>
## 9.5 — Condition kya hai: exit code se "sach/jhooth"

**Condition** (shart) ek aisa sawaal hai jiska jawab "sach" (true — haan) ya "jhooth" (false — nahi)
hota. Jaise "kya file maujood hai?", "kya x, 5 se bada hai?". Iske jawab pe script alag-alag kaam
karti (agar-toh) — 9.6.

**Shell mein sach/jhooth kaise decide hota (yeh Ch 5.6 se juda — ulta lagega):** shell exit code
(`$?`, Ch 5.6) use karta:
- **Exit code `0` = SUCCESS = "sach" (true)**.
- **Non-zero (1, 2...) = FAIL = "jhooth" (false)**.

**Yeh ulta hai (dhyan se):** aam programming mein `0` = false, `1` = true hota. Shell mein **ULTA** —
`0` = true (sach). Kyun? Kyunki `0` ka matlab "koi error nahi" (Ch 5.6 — success), aur "koi error
nahi" = "sab theek" = "sach". Ise yaad rakho: **shell mein 0 = achha = sach**.

**Ek command khud ek condition hai:** kyunki har command exit code deta (Ch 5.6), aap kisi bhi
command ko condition ki tarah use kar sakte ho. Jaise:
```
ls notes.txt
echo $?
```
- Agar `notes.txt` hai → `ls` success → exit `0` → condition "sach". Nahi hai → `ls` fail → exit
  `1` → "jhooth". Toh "kya notes.txt hai?" is condition ka jawab `ls` ke exit code se milta.

**Conditions ke liye special: `test` command aur `[ ]`:** file/number/string check karne ke liye ek
khaas command hai — `test` — jo sach/jhooth (exit code) deta. Aur `[ ]` uska hi doosra roop hai
(9.7). Yeh conditions likhne ka standard tareeka hai.

> **Yaad rakhne wali baat:** Condition = sawaal jiska jawab sach/jhooth. Shell mein exit code se:
> `0` = success = **SACH** (ulta yaad rakho — 0 achha), non-zero = fail = jhooth. Har command ek
> condition ban sakta (exit code se). File/number check ke liye `test`/`[ ]` (9.7).

[↑ Back to top](#top)

---

<a id="s9-6"></a>
## 9.6 — `if / then / else / fi` — basic structure

**`if`** condition check karke, uske sach/jhooth pe alag kaam karta hai — "agar yeh sach hai toh yeh
karo, warna woh". Yeh har programming ki basic cheez hai.

**Structure:**
```
if [ condition ]
then
    # sach hone pe yeh chalega
else
    # jhooth hone pe yeh chalega
fi
```

- **`if`** = "agar". Iske baad condition (aksar `[ ]` mein, 9.7).
- **`then`** = "toh" — iske baad wali lines tab chalti jab condition sach.
- **`else`** = "warna" — iske baad wali lines tab jab condition jhooth. (Optional — na chahiye toh
  chhod do.)
- **`fi`** = "if" ULTA likha (`if` → `fi`) = "if block yahan khatam". Yeh zaroori hai — batata block
  kahan band hua. (Bash ka style — block ko ulte shabd se band karna.)

**Ek asli misaal — file hai ya nahi:**
```
if [ -f notes.txt ]
then
    echo "File maujood hai"
else
    echo "File nahi mili"
fi
```
- **`[ -f notes.txt ]`** = condition: "kya `notes.txt` ek file hai jo maujood hai?" (`-f` = file
  test, 9.7). Sach → "File maujood hai". Jhooth → "File nahi mili".

**Ek line mein bhi likha ja sakta (`;` se):**
```
if [ -f notes.txt ]; then echo "hai"; else echo "nahi"; fi
```
- **`;`** (semicolon) = "ek command khatam, agli shuru" (jaise line break) — isse `if`/`then`/`fi`
  ko ek line mein daal sakte. Terminal pe jaldi likhne mein kaam aata. Script mein alag lines
  padhne mein achhi.

**`elif` — "warna agar" (kai conditions):**
```
if [ "$x" -gt 10 ]; then
    echo "bada"
elif [ "$x" -eq 10 ]; then
    echo "barabar"
else
    echo "chhota"
fi
```
- **`elif`** = else + if = "warna agar" — jab pehli jhooth par ek aur condition check karni ho. Kai
  `elif` ho sakte. (`-gt`/`-eq` = number comparisons, 9.7.)

> **Yaad rakhne wali baat:** `if [ condition ]; then ...; else ...; fi`. `if`=agar, `then`=toh,
> `else`=warna, `fi`=block khatam (`if` ulta). `elif`=warna-agar (aur condition). Sach pe `then`
> wala, jhooth pe `else` wala chalta.

[↑ Back to top](#top)

---

<a id="s9-7"></a>
## 9.7 — `[ ]` test: file aur number comparisons

`[ ]` (square brackets) andar hum "condition" likhte hain. Yeh asal mein `test` command ka doosra
roop hai — `[ -f notes.txt ]` aur `test -f notes.txt` bilkul same. `[ ]` padhne mein aasaan lagta
(isliye zyada use hota).

**ZAROORI — `[ ]` ke andar spaces:** `[` ke baad aur `]` ke pehle **space zaroori** hai:
```
[ -f notes.txt ]      # SAHI (spaces hain)
[-f notes.txt]        # GALAT — error!
```
- Kyun? Kyunki `[` asal mein ek **command** hai (test ka roop), aur command ke baad space chahiye
  (Ch 3 wala separator). `[-f` ko shell ek ajeeb command samajh leta. Yeh #1 galti hai `[ ]` mein.

**File tests (yeh yaad rakho — bahut use hote):**

| Test | Sach jab... |
|---|---|
| `[ -f file ]` | `file` ek maujood **f**ile hai |
| `[ -d dir ]` | `dir` ek maujood **d**irectory (folder) hai |
| `[ -e path ]` | `path` **e**xist karta (file ya folder, kuch bhi) |
| `[ -r file ]` | `file` **r**eadable hai (padh sakte) |
| `[ -w file ]` | `file` **w**ritable hai |
| `[ -x file ]` | `file` e**x**ecutable hai (chala sakte, Ch 7) |
| `[ -s file ]` | `file` khaali nahi hai (**s**ize > 0) |

**Number comparisons (yeh alag dikhte — akshar se, symbol se nahi):**

| Test | Matlab (kis shabd se) | Sach jab |
|---|---|---|
| `[ "$a" -eq "$b" ]` | **eq**ual | a barabar b |
| `[ "$a" -ne "$b" ]` | **n**ot **e**qual | a barabar nahi b |
| `[ "$a" -gt "$b" ]` | **g**reater **t**han | a bada b se |
| `[ "$a" -lt "$b" ]` | **l**ess **t**han | a chhota b se |
| `[ "$a" -ge "$b" ]` | **g**reater/**e**qual | a bada-ya-barabar |
| `[ "$a" -le "$b" ]` | **l**ess/**e**qual | a chhota-ya-barabar |

- **Numbers ke liye `-gt`/`-lt` (symbols `>`/`<` nahi!):** yeh confuse karta — number comparison mein
  `-gt` (word) use hota, `>` nahi. Kyunki `[ ]` ke andar `>` ko shell "redirect" (Ch 6) samajh leta!
  Isliye numbers ke liye `-eq -gt -lt` etc. (Strings ke liye `=` hota — 9.9.)

**Misaal (dono saath):**
```
count=5
if [ "$count" -gt 3 ]; then
    echo "count 3 se bada hai"
fi
```
- `[ "$count" -gt 3 ]` = "kya count (5) 3 se bada hai?" — haan → chalega. Note `"$count"` double
  quotes mein (Ch 5.10 — safe).

> **Yaad rakhne wali baat:** `[ ]` = test (condition). Andar spaces ZAROORI (`[ -f x ]`). File: `-f`
> (file), `-d` (folder), `-e` (exist). Numbers: `-eq -ne -gt -lt -ge -le` (word se, `>`/`<` nahi —
> woh redirect ban jata). `"$var"` quotes mein.

[↑ Back to top](#top)

---

<a id="s9-8"></a>
## 9.8 — `[ ]` vs `[[ ]]` — farak (aur bash mein kaunsa)

Bash mein conditions do tarah likhi ja sakti — single `[ ]` aur double `[[ ]]`. Dono milte-julte,
par `[[ ]]` naya aur behtar hai (sirf bash/zsh mein, `sh` mein nahi).

**`[ ]` (single) — purana, har shell mein (POSIX):**
- Yeh `test` command hai (9.7). Har shell mein chalta (bash, sh, sab) — isliye **portable**.
- Par isme kuch panga: variables ko quotes mein rakhna zaroori (warna khaali/space se toot jata), aur
  `&&`/`||` andar seedha nahi chalte.

**`[[ ]]` (double) — naya, bash/zsh mein, behtar:**
```
if [[ "$name" == "Pragyesh" && "$count" -gt 3 ]]; then
    echo "dono sach"
fi
```
- `[[ ]]` ke andar aap `&&` (aur), `||` (ya) seedha use kar sakte ho — do conditions ek saath.
- Yeh variables ke saath zyada "forgiving" hai (khaali variable pe km toota), aur pattern-matching
  (`==` ke saath `*`) bhi karta.
- **Par sirf bash/zsh mein** — agar script `#!/bin/sh` (POSIX) hai toh `[[ ]]` fail hoga. `#!/bin/bash`
  mein theek.

**Ek table:**

| Cheez | `[ ]` (single) | `[[ ]]` (double) |
|---|---|---|
| Kahan chalta | har shell (portable) | sirf bash/zsh |
| `&&`/`||` andar | nahi (bahar chahiye) | **haan** (seedha) |
| Variable quotes | zaroori (warna toota) | km zaroori (safe) |
| Pattern matching (`*`) | nahi | haan |

**Kaunsa use karein (seedha jawab):**
- **`#!/bin/bash` script (aapka aam case)** → **`[[ ]]`** use karo — behtar, safe, aasaan.
- **`#!/bin/sh` (portable/Alpine)** → `[ ]` use karo (kyunki `[[ ]]` sh mein nahi).
- Yaad karo Ch 1.7 — bash aur sh ka farak. `[[ ]]` bash-only hone ki wajah se yeh "mere machine pe
  chala, Alpine pe nahi" ka ek kaaran ban sakta.

> **Yaad rakhne wali baat:** `[ ]` = purana, har shell (portable), variables quote karo. `[[ ]]` =
> naya, sirf bash/zsh, `&&`/`||` seedha chalte, safe. Bash script mein `[[ ]]` behtar; `sh`/portable
> mein `[ ]`.

[↑ Back to top](#top)

---

<a id="s9-9"></a>
## 9.9 — String comparisons (`=`, `-z`, `-n`)

Numbers ke liye `-eq`/`-gt` the (9.7). Text (strings) compare karne ke apne tests hain:

| Test | Sach jab |
|---|---|
| `[ "$a" = "$b" ]` | a aur b same text hain (barabar) |
| `[ "$a" != "$b" ]` | a aur b alag hain |
| `[ -z "$a" ]` | a **z**ero-length hai (khaali) |
| `[ -n "$a" ]` | a **n**on-empty hai (kuch hai) |

**Strings ke liye `=` (ek), numbers ke liye `-eq` (dohra raha hoon — yeh confuse karta):**
```
[ "$name" = "Pragyesh" ]      # STRING compare — = (single)
[ "$count" -eq 5 ]            # NUMBER compare — -eq
```
- Text barabar? → `=`. Number barabar? → `-eq`. Galat use karoge (jaise numbers pe `=`) toh yeh text
  ki tarah compare karega (`"10" = "10.0"` false, jabki numbers barabar). Sahi test chuno.
- (`[[ ]]` mein string ke liye `==` bhi chalta — `=` aur `==` dono theek `[[ ]]` mein.)

**`-z` aur `-n` — bahut kaam ke (khaali check):**
```
if [ -z "$name" ]; then
    echo "Naam nahi diya gaya!"
fi
```
- **`-z`** = "khaali hai?" (zero-length). Yeh check karne ka standard tareeka ki koi variable/input
  diya gaya ya nahi. Jaise script mein — agar user ne argument nahi diya, `$1` khaali, `-z` se pakdo.
- **`-n`** = ulta ("kuch hai?"). `[ -n "$name" ]` = "naam diya gaya hai".

**Quotes yahan aur zaroori:** `[ -z $name ]` (bina quotes) — agar `$name` khaali hai toh yeh `[ -z ]`
ban jata (ajeeb, error/galat). `[ -z "$name" ]` (quotes) mein khaali `$name` `""` ban jata, `[ -z ""
]` — sahi. Isliye string tests mein **hamesha `"$var"`** (Ch 5.10/5.12 wala).

> **Yaad rakhne wali baat:** String: `=` (barabar), `!=` (alag), `-z` (khaali?), `-n` (kuch hai?).
> Numbers = `-eq` etc., strings = `=` (alag!). `-z "$x"` = input diya ya nahi check karne ka standard.
> String tests mein `"$var"` quotes zaroori.

[↑ Back to top](#top)

---

<a id="s9-10"></a>
## 9.10 — `&&`, `||`, `!` — commands ko logic se jodna

Yeh teen operators commands/conditions ko "aur/ya/nahi" se jodte hain. Yeh Ch 5.6 (exit code) pe
khade hain.

**`&&` = "aur" / "safal ho toh hi aage":**
```
mkdir project && cd project
```
- **`&&`** = "pehla command **safal** ho (exit 0), **tabhi** doosra chalao". Yahan: folder banao, aur
  *agar ban gaya toh* usmein jao. Agar `mkdir` fail (folder pehle se ya permission nahi) toh `cd`
  nahi chalega. Yeh "safal ho toh hi aage" ka standard tareeka.

**`||` = "ya" / "fail ho toh yeh karo":**
```
cd project || echo "Folder nahi mila"
```
- **`||`** = "pehla command **fail** ho, **tabhi** doosra chalao". Yahan: folder mein jao, *ya agar
  na ja sako toh* error dikhao. Fail-hone-par-kuch-karo ka tareeka.

**Ek saath (common pattern):**
```
command && echo "safal" || echo "fail"
```
- Safal → "safal", fail → "fail". (Chhota if-else jaisa.)

**`!` = "nahi" (ulta karo):**
```
if [ ! -f notes.txt ]; then
    echo "File NAHI hai"
fi
```
- **`!`** = condition ko ulta karo. `[ ! -f notes.txt ]` = "agar notes.txt file **nahi** hai". `-f`
  sach deta jab file hai; `!` use ulta karke "jab file nahi hai" bana deta.

**Yeh `&&`/`||` `if` se kaise alag:** `if` bada, clear block deta (multi-line logic). `&&`/`||` chhote,
ek-line "yeh-toh-woh" ke liye. Chhote check → `&&`/`||`. Bada logic → `if`. Dono exit code pe khade
(Ch 5.6).

> **Yaad rakhne wali baat:** `&&` = safal ho toh aage (`mkdir x && cd x`). `||` = fail ho toh yeh
> (`cd x || echo error`). `!` = ulta (`[ ! -f x ]` = file nahi hai). Chhote check `&&`/`||`, bada
> logic `if`. Sab exit-code pe.

[↑ Back to top](#top)

---

<a id="s9-11"></a>
## 9.11 — `case` — kai options mein se ek chunna

Jab ek variable ki value ke hisaab se **kai alag-alag** kaam karne ho, tab `if/elif/elif/elif...`
lamba aur bhadda ho jata. `case` uska saaf tareeka hai — "value yeh hai toh yeh, woh hai toh woh".

**Structure:**
```
case "$variable" in
    pattern1)
        # kaam 1
        ;;
    pattern2)
        # kaam 2
        ;;
    *)
        # koi match nahi (default)
        ;;
esac
```

- **`case "$var" in`** = "is variable ki value dekho".
- Har **`pattern)`** = "agar value yeh hai toh...", uske baad kaam.
- **`;;`** = "is option ka kaam khatam" (do semicolon — case ka block-end, `if` ke `fi` jaisa har
  option pe).
- **`*)`** = "koi bhi (default)" — agar upar koi match nahi hua (`*` = kuch bhi, Ch 4.11 wildcard).
- **`esac`** = "case" ULTA (`case` → `esac`) = poora case block khatam (jaise `if`→`fi`).

**Asli misaal — user input pe kaam:**
```
echo "Kya karna hai? (start/stop/restart)"
read action
case "$action" in
    start)
        echo "Service shuru kar rahe..."
        ;;
    stop)
        echo "Service band kar rahe..."
        ;;
    restart)
        echo "Service restart kar rahe..."
        ;;
    *)
        echo "Galat option: $action"
        ;;
esac
```
- `read action` = user se input lo (Ch 11 mein poora). `case` us value ko match karta — `start` →
  ek kaam, `stop` → doosra, kuch aur → default (`*`) galat-option message. Yeh service scripts mein
  bahut common pattern hai.

**Pattern mein `|` (ya) aur `*` (wildcard):**
```
case "$answer" in
    y|yes|Y)    echo "Haan" ;;
    n|no|N)     echo "Nahi" ;;
    *)          echo "Samajh nahi aaya" ;;
esac
```
- `y|yes|Y` = "y ya yes ya Y" (`|` = ya). Ek pattern mein kai values. Yes/no jaise input ke liye
  handy.

**`case` vs `if-elif`:** jab ek hi variable ki value ke kai fixed cases ho (jaise start/stop/restart)
→ `case` saaf. Jab alag-alag conditions ho (jaise number ranges, file checks) → `if-elif`. `case`
"ek cheez, kai values" ke liye best.

> **Yaad rakhne wali baat:** `case "$var" in pattern) ...;; *) ...;; esac` — ek variable ki value ke
> kai fixed options ke liye (start/stop/restart). `;;` = option-end, `*)` = default, `esac` = case
> ulta (block-end). `|` = ya (`y|yes`). Kai fixed values → case, warna if-elif.

[↑ Back to top](#top)

---

<a id="s9-12"></a>
## 9.12 — Nuances aur caveats

- **`[ ]` ke andar spaces (dohra raha — #1 galti):** `[ -f x ]` sahi, `[-f x]` ya `[ -f x]` galat.
  `[` ek command hai, dono taraf space chahiye. Yeh sabse common condition-error hai.

- **Numbers `-eq`, strings `=` — mix mat karo:** `[ "$a" = "$b" ]` text compare (character-by-
  character); `[ "$a" -eq "$b" ]` number compare (value). `[ "10" = "10.0" ]` false (text alag), par
  `[ 10 -eq 10 ]`... — sahi test chuno warna galat result.

- **Variables hamesha `"$var"` (quotes) conditions mein:** agar `$var` khaali ya space-wali ho, bina
  quotes condition toot jati (`[ -z $var ]` khaali pe `[ -z ]` ban jata). Quotes = safe. (Ch 5.12.)

- **`[[ ]]` sirf bash/zsh — `sh` mein nahi:** agar `#!/bin/sh` likha aur `[[ ]]` use kiya, Alpine/
  minimal system pe fail hoga. Bash script mein `[[ ]]` theek; portable chahiye toh `[ ]`. (9.8.)

- **`0 = true` ka confusion:** yaad rakho shell mein exit `0` = success = sach (ulta from normal
  programming). `if command` mein — command success (`0`) → then chalta. Yeh baar-baar confuse karta,
  par logic yehi (0 = koi error nahi = achha).

- **`=` assignment vs comparison:** `x=5` (assignment, space nahi, Ch 5.2) aur `[ "$x" = "5" ]`
  (comparison, spaces ke saath) — dono `=` par bilkul alag. Context (bracket ke andar = compare,
  bahar = assign) aur spaces se farak.

- **`fi`/`esac`/`;;` bhoolna = syntax error:** `if` ko `fi` se, `case` ko `esac` se band karna
  zaroori; `case` mein har option `;;` se. Bhoole toh "unexpected end of file" jaisa error. Block
  hamesha band karo.

[↑ Back to top](#top)

---

<a id="s9-13"></a>
## 9.13 — Real-life scenarios

**Scenario 1 — "File hai tabhi process karo."** Aapka script ek data file process karta, par woh
file honi chahiye warna crash. `if [ -f "$datafile" ]; then process; else echo "File nahi mili";
exit 1; fi` (9.6/9.7). File-check pehle, tabhi aage — yeh defensive scripting (Ch 14) ki basic.

**Scenario 2 — "User ne argument diya ya nahi."** Aapka script ek naam maangta hai (`$1`, Ch 11).
Agar user bina diye chala de: `if [ -z "$1" ]; then echo "Usage: ./script.sh <naam>"; exit 1; fi`
(9.9). `-z` se khaali-check — user ko sahi tareeka bata do. Har achhi script yeh karti.

**Scenario 3 — "Folder banao aur usmein jao (safal ho toh)."** `mkdir -p build && cd build` (9.10).
`&&` se — folder bana toh hi `cd`. Agar `mkdir` fail, `cd` nahi hoga (galat jagah kaam nahi karega).
Ek-line safe pattern.

**Scenario 4 — "Service script (start/stop/restart)."** Aap ek app manage karne ka script likhte ho
jo `./app.sh start` ya `stop` ya `restart` leta. `case "$1" in start) ...;; stop) ...;; esac`
(9.11). Yeh service/deploy scripts ka classic structure — kai fixed actions.

**Scenario 5 — "Command safal hui ya nahi, uspe alag message."** Aap ek backup command chalate ho
aur result batana hai. `if backup_command; then echo "Backup safal"; else echo "Backup FAIL"; exit
1; fi` (9.5/9.6 — command khud condition). Exit code se success/fail, uspe user ko clear feedback.

**Saar:** Chapter 9 ne aapko "script likhne wala" bana diya — shebang + chalane ke tareeke (9.1-9.3),
aur logic: `if/else` (9.6), `[ ]`/`[[ ]]` tests (9.7-9.9), `&&`/`||` (9.10), `case` (9.11). Sabse
practical: har condition `"$var"` quotes mein, `[ ]` mein spaces, aur `0 = sach` yaad rakho. In se
aapki script "soch" sakti hai — input check kar sakti, safal/fail pe alag kaam.

[↑ Back to top](#top)

---

> **Chapter 09 khatam.** Ab tak: script (commands ki file), shebang (`#!/bin/bash`), chalane ke 3
> tareeke (`bash`/`./`/`source`), comments + `set -euo pipefail`; conditions — exit code se sach/
> jhooth (`0`=sach), `if/then/else/fi`, `[ ]` file/number tests, `[ ]` vs `[[ ]]`, string tests
> (`=`/`-z`), `&&`/`||`/`!`, aur `case`. **Agla chapter:** loops (`for`, `while`) aur functions —
> kaam ko baar-baar/organize karna.

[↑ Back to top](#top)
