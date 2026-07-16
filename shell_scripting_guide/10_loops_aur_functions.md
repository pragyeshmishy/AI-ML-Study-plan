<a id="top"></a>
# Chapter 10 — Loops aur Functions (baar-baar karna, kaam organize karna)

Chapter 9 mein humne conditions seekhi (agar-toh). Ab do aur building blocks: **loops** (ek kaam
baar-baar karna — jaise 100 files pe same kaam) aur **functions** (ek kaam ko ek naam de ke bar-bar
bulana). Yeh do cheezein aapke scripts ko chhote-repetitive se powerful-organized bana deti hain.

Yeh theory-heavy chapter hai — har loop type, aur function ke saare hisse kholega.

---

## Is chapter ka index

- [10.1 — Loop kya hai (ek kaam baar-baar)](#s10-1)
- [10.2 — `for` loop — ek list ke har item pe kaam](#s10-2)
- [10.3 — `for` se files pe kaam (safe tareeka)](#s10-3)
- [10.4 — `while` loop — jab tak condition sach](#s10-4)
- [10.5 — `until` loop — jab tak condition jhooth](#s10-5)
- [10.6 — `break` aur `continue` — loop ko rokna/skip karna](#s10-6)
- [10.7 — File ko line-by-line padhna (`while read`)](#s10-7)
- [10.8 — Function kya hai (kaam ko ek naam)](#s10-8)
- [10.9 — Function ko arguments dena (`$1` andar)](#s10-9)
- [10.10 — Function se value wapas lena (return/echo)](#s10-10)
- [10.11 — Nuances aur caveats](#s10-11)
- [10.12 — Real-life scenarios](#s10-12)

---

<a id="s10-1"></a>
## 10.1 — Loop kya hai (ek kaam baar-baar)

**Loop** (matlab "chakkar/ghera") ek aisa structure hai jo ek kaam ko **baar-baar** chalata — jab tak
koi shart poori na ho, ya list khatam na ho. Bina loop ke, agar aapko 100 files pe same kaam karna
ho, toh 100 baar command likhni padegi. Loop se: ek baar likho, woh 100 baar chala dega.

**Kyun zaroori:** computer ki sabse badi taakat hai "same kaam bina thake baar-baar karna". Loop wahi
deta. Misaal:
- 500 images ko resize karna — ek loop, har image pe same command.
- Ek file ki har line process karna — loop har line pe.
- Jab tak server ready na ho, check karte raho — loop with condition.

**Do main tarah ke loops (soch ka farak):**
- **`for`** — jab aapke paas ek **list** ho (files, numbers, naam) aur har item pe kaam karna ho.
  "Har X ke liye, yeh karo." (10.2)
- **`while`** — jab tak ek **condition sach** ho, chalte raho. "Jab tak yeh sach hai, yeh karo."
  (10.4)

Farak: `for` "ginti/list pata hai" (har item), `while` "pata nahi kitni baar, jab tak condition".
Dono ka use alag scenario mein — aage dekhenge.

> **Yaad rakhne wali baat:** Loop = ek kaam baar-baar (list khatam ya condition tak). `for` = list ke
> har item pe (ginti pata). `while` = jab tak condition sach (ginti pata nahi). Computer ki "bina
> thake repeat" wali taakat.

[↑ Back to top](#top)

---

<a id="s10-2"></a>
## 10.2 — `for` loop — ek list ke har item pe kaam

**`for`** loop ek list ke **har item** pe ghum ke, har ek pe same kaam karta.

**Structure:**
```
for item in list
do
    # yahan kaam (item use karo)
done
```
- **`for item in list`** = "list ke har cheez ko baari-baari `item` mein rakho".
- **`do`** = "karo" — iske baad wala kaam har item pe chalega.
- **`done`** = "ho gaya" — loop block khatam (jaise `if` ka `fi`).
- **`item`** ek variable hai (koi bhi naam) jo har chakkar mein list ki agli value banta. Use `$item`
  se access karo (Ch 5.3).

**Misaal 1 — naamon ki list pe:**
```
for naam in Amit Bhavna Chetan
do
    echo "Namaste, $naam!"
done
```
- List: `Amit Bhavna Chetan` (space se alag, teen items). Loop teen baar chalega — har baar `$naam`
  agla naam. Output: `Namaste, Amit!`, `Namaste, Bhavna!`, `Namaste, Chetan!`.

**Misaal 2 — numbers pe (range `{1..5}`):**
```
for i in {1..5}
do
    echo "Number: $i"
done
```
- **`{1..5}`** = 1 se 5 tak ki list (bash ka "brace expansion" — `{start..end}`). Loop 5 baar,
  `$i` = 1,2,3,4,5. Output: Number 1 se 5.

**Misaal 3 — C-style `for` (numbers pe, aur control):**
```
for (( i=1; i<=5; i++ ))
do
    echo "Count: $i"
done
```
- Yeh purane C-language jaisa `for` hai (bash mein): `i=1` (shuru), `i<=5` (jab tak), `i++` (har baar
  1 badhao). Jab exact number-control chahiye. (`{1..5}` aasaan hai simple cases mein.)

> **Yaad rakhne wali baat:** `for item in list; do ...; done` = list ke har item pe kaam (`$item`
> use karo). List: shabd (`Amit Bhavna`), range (`{1..5}`), ya files (10.3). `do`/`done` = block.
> C-style `for ((...))` jab number-control chahiye.

[↑ Back to top](#top)

---

<a id="s10-3"></a>
## 10.3 — `for` se files pe kaam (safe tareeka)

Sabse common `for` use — ek folder ki **files pe** kaam. Par yahan ek trap hai (space wale naam),
toh dhyan se.

**Files pe loop — glob (`*`) se:**
```
for file in *.txt
do
    echo "Processing: $file"
done
```
- **`*.txt`** = saari `.txt` files (Ch 4.11/6.11 wala wildcard — shell ise file-naamon ki list mein
  badal deta). Loop har `.txt` file pe chalega, `$file` = har file ka naam.

**Asli kaam ki misaal — saari images ka backup:**
```
for img in *.jpg
do
    cp "$img" "backup/$img"
done
```
- Har `.jpg` file ko `backup/` folder mein copy. `$img` har baar agli image. **Note `"$img"` double
  quotes mein** — bahut zaroori (aage).

**ZAROORI — quotes (`"$file"`) warna space wale naam todenge:** yaad karo Ch 5.10/5.12. Agar kisi
file ka naam `my report.txt` (space wala) hai, aur aap bina quotes `cp $file ...` likhte ho, toh
shell `my` aur `report.txt` do alag samajh leta — galat kaam. Hamesha **`"$file"`** (quotes mein) —
tab space-wala naam bhi ek rehta.

**Ek common trap — khaali folder / no match:** agar folder mein koi `.txt` file nahi, toh `for file
in *.txt` mein `*.txt` literal `*.txt` hi reh jata (expand nahi hota), aur loop ek baar chalega
`$file = "*.txt"` ke saath — galat. Isse bachne ko `if [ -e "$file" ]` check ya `shopt -s nullglob`
(advanced) — abhi bs jaan lo ki khaali-match ka yeh corner-case hota.

> **Yaad rakhne wali baat:** `for file in *.txt; do ... "$file" ...; done` = har matching file pe
> kaam. HAMESHA `"$file"` (quotes) — space wale naam todne se bachao. Khaali folder pe `*.txt` literal
> reh jata (corner case).

[↑ Back to top](#top)

---

<a id="s10-4"></a>
## 10.4 — `while` loop — jab tak condition sach

**`while`** loop tab tak chalta jab tak ek **condition sach** hai. `for` "list ke items" pe chalta
tha; `while` "condition" pe — pata nahi kitni baar, jab tak condition sach.

**Structure:**
```
while [ condition ]
do
    # kaam (jab tak condition sach)
done
```
- **`while [ condition ]`** = "jab tak yeh condition sach hai" (condition = Ch 9 wali `[ ]`).
- Har chakkar se pehle condition check hoti — sach → kaam chalta; jhooth → loop khatam.
- `do`/`done` — same jaisa `for`.

**Misaal — counter (1 se 5):**
```
i=1
while [ "$i" -le 5 ]
do
    echo "Count: $i"
    i=$((i + 1))
done
```
- `i=1` (shuru). `[ "$i" -le 5 ]` = "jab tak i, 5 se chhota-ya-barabar" (Ch 9.7). Har baar `echo`,
  phir `i=$((i + 1))` (i ko 1 badhao). Jab i=6 hua, condition jhooth, loop ruk gaya.
- **`$(( ... ))`** = arithmetic (ganit) — iske andar math hota. `$((i + 1))` = "i mein 1 jodo". Yeh
  shell mein numbers pe calculation ka tareeka (variables ke saath `$` bhi optional andar).

**ZAROORI — counter badhana mat bhoolna (warna infinite loop):** `while` mein aksar aap khud kuch
badalte ho (jaise `i` badhana) taaki condition kabhi jhooth ho. Agar bhool gaye (upar `i=$((i+1))`
na ho), toh condition hamesha sach rahegi aur loop **kabhi nahi rukega** ("infinite loop") — screen
bharta rahega. Bachne ko: `Ctrl+C` (Ch 1). Hamesha ensure karo ki loop ke andar kuch aisa ho jo
condition ko eventually jhooth kare.

**`while true` — jaan-boojh ke infinite (jab tak `break` na ho):**
```
while true
do
    # kuch kaam
    # kisi condition pe: break
done
```
- **`true`** hamesha success (exit 0 = sach, Ch 9.5), toh `while true` hamesha chalta — jaan-boojh
  ke infinite. Ise `break` (10.6) se rokte hain jab andar koi shart poori ho. Monitoring/waiting
  loops mein use hota (jaise "server ready hone tak check karte raho").

> **Yaad rakhne wali baat:** `while [ condition ]; do ...; done` = jab tak condition sach. `$((i+1))`
> = math (counter badhao). Counter badhana mat bhoolna — warna infinite loop (`Ctrl+C` se roko).
> `while true` = jaan-boojh infinite (break se roko).

[↑ Back to top](#top)

---

<a id="s10-5"></a>
## 10.5 — `until` loop — jab tak condition jhooth

**`until`** `while` ka ulta hai — yeh tab tak chalta jab tak condition **jhooth** hai (matlab
"chalte raho JAB TAK yeh sach na ho jaye").

```
until [ condition ]
do
    # kaam (jab tak condition jhooth rahe)
done
```
- **`while`** = "jab tak SACH" (sach pe chalta). **`until`** = "jab tak JHOOTH" (jhooth pe chalta,
  sach hote hi rukta).

**Kab kaam ka — kisi cheez ke "ready" hone ka wait:**
```
until ping -c1 server.com &> /dev/null
do
    echo "Server ka wait kar rahe..."
    sleep 5
done
echo "Server ready!"
```
- `ping ... server.com` — server tak pahunchne ki koshish (`&> /dev/null` = output phenko, Ch 6.7).
  `until` = "jab tak ping fail (jhooth), wait karte raho". Jaise hi server aa gaya (ping success =
  sach), loop ruk gaya, "Server ready!". `sleep 5` = 5 second ruko (Ch 16).
- Yeh "kisi cheez ke taiyar hone tak wait" ka natural tareeka — `until <ready-condition>`.

**`until` vs `while` (ek line):** dono same kaam kar sakte, bs condition ulti. `until [ x ]` =
`while [ ! x ]` (Ch 9.10 ka `!`). Jo padhne mein natural lage woh use karo — "ready hone tak wait"
`until` se saaf, "chalte rehna jab tak valid" `while` se saaf.

> **Yaad rakhne wali baat:** `until [ condition ]` = jab tak condition JHOOTH (sach hote hi rukta) —
> `while` ka ulta. "Kisi cheez ke ready hone tak wait" ka natural tareeka (`until ready; do wait`).
> `sleep N` = N second ruko.

[↑ Back to top](#top)

---

<a id="s10-6"></a>
## 10.6 — `break` aur `continue` — loop ko rokna/skip karna

Loop ke andar do control-words: `break` (poora loop rok do) aur `continue` (yeh chakkar chhod ke
agle pe jao).

**`break` — loop se turant bahar:**
```
for i in {1..100}
do
    if [ "$i" -eq 10 ]
    then
        break
    fi
    echo "$i"
done
```
- `break` = "loop yahin khatam, bahar niklo". Yahan i=10 pe `break` — loop 1 se 9 chhaap ke ruk gaya
  (10 aur aage nahi). Jab loop ke beech mein koi shart poori ho aur aage chalane ka matlab na ho.

**`continue` — yeh chakkar chhodo, agle pe jao:**
```
for i in {1..5}
do
    if [ "$i" -eq 3 ]
    then
        continue
    fi
    echo "$i"
done
```
- `continue` = "is chakkar ka baaki kaam chhodo, agle item pe jao (loop chalta rahega)". Yahan i=3
  pe `continue` — 3 ka `echo` skip hua, par loop chalta raha. Output: 1,2,4,5 (3 gayab).

**Farak (ek line):** `break` = poora loop khatam (bahar). `continue` = sirf yeh chakkar skip (loop
jaari). `break` "bas, ho gaya"; `continue` "isko chhodo, aage badho".

**Kab kaam ke:**
- `break` — kuch dhoondh rahe the aur mil gaya (aur dekhne ka matlab nahi), ya error aa gaya (ruk
  jao).
- `continue` — kuch items skip karne hain (jaise galat/khaali ko chhodo, baaki process karo).

> **Yaad rakhne wali baat:** `break` = poora loop rok ke bahar niklo (mil gaya/error). `continue` =
> yeh chakkar skip, agle pe jao (loop jaari). `break` = bas ho gaya; `continue` = isko chhodo aage
> badho.

[↑ Back to top](#top)

---

<a id="s10-7"></a>
## 10.7 — File ko line-by-line padhna (`while read`)

Ek bahut common kaam — ek file ki **har line** pe kaam karna (jaise ek list of names/URLs process
karna). Iska standard tareeka: `while read`.

```
while read line
do
    echo "Line: $line"
done < names.txt
```
- **`read line`** = ek line padho aur `line` variable mein rakho (Ch 11 mein `read` poora). `while
  read line` = "jab tak lines hain, ek-ek padhte raho".
- **`< names.txt`** (loop ke aakhir mein) = input file se do (Ch 6.5 redirect). Yeh file ki har line
  loop ko feed karta.
- Har chakkar mein `$line` = file ki agli line. File khatam → `read` fail → loop ruk gaya.

**Safe version (recommended) — `IFS= read -r`:**
```
while IFS= read -r line
do
    echo "Line: $line"
done < names.txt
```
- **`-r`** = backslash (`\`) ko literal rakho (warna `read` use special samajh leta). **`IFS=`** =
  line ke aage-peeche ke spaces na todo (poori line jaisi hai waisi). Yeh "proper" tareeka hai —
  lines ko bilkul waisa padhta jaisa file mein. Yaad rakho: **file padhne ko `while IFS= read -r
  line`**.

**Kyun `cat file | while read` nahi (common galti):** log `cat names.txt | while read line` likhte
hain — yeh chalta par ek subtle problem: pipe (Ch 6) ke karan loop ek alag "subshell" mein chalta,
aur loop ke andar set kiye variables bahar nahi aate. `< file` (redirect) se yeh problem nahi.
Isliye **`done < file`** tareeka behtar hai.

> **Yaad rakhne wali baat:** File line-by-line: `while IFS= read -r line; do ...; done < file`. `-r`
> (backslash literal) + `IFS=` (spaces safe) = proper. `< file` (redirect) use karo, `cat | while`
> nahi (subshell variable-problem). Har `$line` file ki agli line.

[↑ Back to top](#top)

---

<a id="s10-8"></a>
## 10.8 — Function kya hai (kaam ko ek naam)

**Function** = commands ke ek group ko ek **naam** de dena, taaki baad mein sirf woh naam bulao aur
poora group chal jaye. Jaise ek "chhoti custom command" jo aap khud banate ho.

**Kyun zaroori:**
- **Dobara use:** ek kaam jo script mein baar-baar aata (jaise "log likhna", "cleanup") — use ek
  function bana do, phir sirf naam se bulao. Copy-paste nahi.
- **Organize:** bada script chhote functions mein baant do — har function ek kaam. Padhne/samajhne
  mein aasaan.
- **Ek jagah fix:** kaam badalna ho toh sirf function mein badlo, sab jagah update.

**Structure (do tareeke, dono chalte):**
```
# Tareeka 1
greet() {
    echo "Namaste!"
}

# Tareeka 2 (function keyword ke saath)
function greet {
    echo "Namaste!"
}
```
- **`greet() { ... }`** — `greet` naam ka function, `{ }` ke andar uska kaam. Tareeka 1 (`naam()`)
  zyada common aur portable.
- Function **define karne se chalta nahi** — sirf "ban jata" (ready). Chalane ko naam bulao:
```
greet
```
- Sirf `greet` likho (jaise koi command) — function chal gaya, output `Namaste!`. Function ko chalane
  ko koi bracket nahi (jaise Python mein `greet()` hota — shell mein sirf `greet`).

**ZAROORI — function pehle define, phir use:** shell script upar-se-neeche padhta hai (Ch 9.1). Toh
function ko **use karne se pehle define** karna zaroori — script mein function upar likho, uska call
neeche. Warna "command not found" (abhi define nahi hua).

**Chhota poora misaal:**
```
#!/bin/bash

log() {
    echo "[LOG] $1"
}

log "Script shuru"
log "Kaam ho raha"
log "Script khatam"
```
- `log` function define kiya (ek message chhaapta). Phir teen baar bulaya. `$1` = function ko diya
  argument (10.9). Output: `[LOG] Script shuru` etc. Yeh "apni chhoti command banana" hai.

> **Yaad rakhne wali baat:** Function = commands ke group ko ek naam (`naam() { ... }`), phir naam se
> bulao (`naam` — bracket nahi). Fayda: dobara-use, organize, ek jagah fix. Define PEHLE, use BAAD
> (script upar-neeche padhta).

[↑ Back to top](#top)

---

<a id="s10-9"></a>
## 10.9 — Function ko arguments dena (`$1` andar)

Jaise script ko arguments milte hain (`$1`, `$2` — Ch 5.6, Ch 11), waise hi **function ko bhi** —
function ke naam ke baad jo cheezein likho, woh uske andar `$1`, `$2`... ban jati.

```
greet() {
    echo "Namaste, $1! Aapki umar $2 hai."
}

greet Pragyesh 30
```
- `greet Pragyesh 30` — function ko do arguments diye. Andar: `$1` = `Pragyesh`, `$2` = `30`. Output:
  `Namaste, Pragyesh! Aapki umar 30 hai.`
- **Note:** yeh wahi `$1`/`$2` hai jo scripts mein hota (Ch 5.6), par function ke andar yeh
  **function ke** arguments hain (script ke nahi). Function ke andar `$1` = function ko diya pehla
  argument.

**Ek useful misaal — reusable function:**
```
backup_file() {
    cp "$1" "$1.backup"
    echo "Backup banaya: $1.backup"
}

backup_file notes.txt
backup_file data.csv
```
- `backup_file` ek file ko backup karta — `$1` = jo file di. Do baar bulaya, alag files ke saath. Ek
  baar likha, kai baar use — yeh function ka asli fayda (10.8).

**`$@` — saare arguments ek saath:**
```
show_all() {
    echo "Saare arguments: $@"
    echo "Kitne aaye: $#"
}
show_all a b c
```
- **`$@`** = function ko diye saare arguments (Ch 11 mein poora). **`$#`** = kitne aaye (ginti).
  Output: `Saare arguments: a b c`, `Kitne aaye: 3`. Jab function ko variable number of arguments
  handle karne ho.

> **Yaad rakhne wali baat:** Function ko arguments: naam ke baad likho (`greet Pragyesh 30`), andar
> `$1`/`$2`... se milte. Yeh function ke arguments (script ke nahi). `$@` = saare, `$#` = ginti.
> Reusable function (`backup_file "$1"`) = ek baar likho, kai baar use.

[↑ Back to top](#top)

---

<a id="s10-10"></a>
## 10.10 — Function se value wapas lena (return/echo)

Function kaam karke koi "jawab" wapas de — iske do tareeke hain, aur inmein farak samajhna zaroori
(yeh confuse karta).

**Tareeka 1 — `echo` se value "wapas" (yeh sabse use hota):**
```
get_date() {
    echo "$(date +%Y-%m-%d)"
}

today=$(get_date)
echo "Aaj: $today"
```
- Function `echo` se value "output" karta. Use pakadne ko command substitution `$(...)` (Ch 5.5) —
  `today=$(get_date)` matlab "get_date chalao, uska output `today` mein". Yeh function se **data**
  (string/number) wapas lene ka standard tareeka.

**Tareeka 2 — `return` se exit code (sirf success/fail, 0-255):**
```
is_file() {
    if [ -f "$1" ]; then
        return 0    # success (sach)
    else
        return 1    # fail (jhooth)
    fi
}

if is_file notes.txt; then
    echo "File hai"
fi
```
- **`return`** value nahi, ek **exit code** (0-255, Ch 5.6) deta — sirf "safal/asafal" batane ke liye.
  `return 0` = success (sach), `return 1` = fail. Ise `if` mein condition ki tarah use karte (Ch
  9.5 — function bhi ek command jaisa, exit code deta).

**BADa farak (yeh galti aam hai):** `return` se aap **data (string/number) wapas nahi le sakte** —
woh sirf 0-255 ka exit code hai. Agar aapko koi value (naam, path, result) chahiye, toh **`echo` +
`$(...)`** use karo (tareeka 1). `return` sirf "haan/na" (success/fail) ke liye.
- Galat soch: `return "$naam"` — yeh kaam nahi karega (naam exit-code nahi ban sakta).
- Sahi: `echo "$naam"` function mein, aur `x=$(function)` bahar.

**Ek line mein:** data chahiye → `echo` + `$(...)`. Sirf success/fail → `return` (exit code, `if`
mein use).

> **Yaad rakhne wali baat:** Function se DATA (string/number) wapas: `echo` karo, `x=$(function)` se
> pakdo. Sirf SUCCESS/FAIL: `return 0/1` (exit code, `if` mein use). `return` se data nahi milta
> (sirf 0-255) — yeh #1 galti. Data = echo, haan/na = return.

[↑ Back to top](#top)

---

<a id="s10-11"></a>
## 10.11 — Nuances aur caveats

- **Loop variables ko `"$var"` (quotes) — dohra raha hoon:** `for f in *.txt; do cp "$f" ...`. Bina
  quotes, space-wale filenames toot jate (Ch 5.12). Har loop mein variable quote karo.

- **Infinite loop ka dhyan:** `while` mein counter/condition badalna mat bhoolna, warna kabhi nahi
  rukega (`Ctrl+C` se roko, 10.4). `while true` sirf tab jab `break` (10.6) andar ho.

- **`cat file | while read` — subshell trap:** pipe se loop alag subshell mein chalta, uske andar set
  variables bahar nahi aate ("maine loop mein count badhaya par bahar 0 hai"). `done < file`
  (redirect) use karo, pipe nahi (10.7).

- **`>` loop ke andar = har baar overwrite (Ch 6.11):** `for f in *; do echo "$f" > list.txt; done`
  — har chakkar file reset, sirf aakhri bacha. Loop mein append `>>` chahiye, ya `>` loop ke *bahar*
  (poore loop ka output redirect).

- **Function define pehle, call baad (10.8):** script upar-se padhta; function ko use se pehle define
  karo warna "command not found".

- **`return` vs `echo` (10.10 — sabse bada function-confusion):** data (naam/path) chahiye toh `echo`
  + `$(...)`, sirf success/fail toh `return`. `return "$string"` galat.

- **Function ke andar variables "global" hote (default):** function mein banaya variable bahar bhi
  dikhta (aur ulta) — yeh bugs de sakta. Local rakhne ko `local x=5` (function ke andar `local`
  keyword). Bade scripts mein function ke variables `local` karo taaki takraav na ho.

- **`{1..5}` bash-only:** yeh brace-range bash/zsh mein; `sh` mein nahi. Portable chahiye toh `seq
  1 5` (command) ya C-style `for`. (Ch 1.7 wala shell-farak.)

[↑ Back to top](#top)

---

<a id="s10-12"></a>
## 10.12 — Real-life scenarios

**Scenario 1 — "500 images resize/convert karni hain."** Ek folder mein bahut images, sab pe same
kaam. `for img in *.jpg; do convert "$img" -resize 800x "resized/$img"; done` (10.3). Ek loop, sab
images process. Manual karna namumkin hota — loop ne minute mein kar diya.

**Scenario 2 — "Ek list of servers/URLs check karo."** Aapke paas `servers.txt` mein server naam
hain, har ek ka status check karna. `while IFS= read -r server; do ping -c1 "$server" &>/dev/null &&
echo "$server UP" || echo "$server DOWN"; done < servers.txt` (10.7 + 9.10). Har line ek server,
loop sab check karta.

**Scenario 3 — "Server ready hone tak wait karo."** Deploy script mein, app start ki par ready hone
mein time lagta. `until curl -s localhost:8080/health &>/dev/null; do echo "waiting..."; sleep 2;
done` (10.5). Ready hote hi loop rukta, aage badhta. Deploy automation mein common.

**Scenario 4 — "Repetitive kaam ko function bana do."** Aapke script mein "timestamp ke saath log
likhna" 20 jagah aata. Ek function: `log() { echo "$(date +%H:%M:%S) - $1"; }` (10.8/10.9). Ab
har jagah `log "message"`. Format badalna ho? Sirf function mein badlo, 20 jagah update. DRY (Don't
Repeat Yourself).

**Scenario 5 — "Loop mein galti se sab file reset ho gayi."** Aapne `for f in *.log; do process "$f"
> output.txt; done` likha, aur end mein `output.txt` mein sirf aakhri file ka result tha. Ab aap
jaante ho (10.11) — loop ke andar `>` har baar overwrite. Fix: `>>` (append) ya loop ke bahar
redirect: `for f in *.log; do process "$f"; done > output.txt`.

**Saar:** Chapter 10 ne scripts ko powerful banaya — `for` (list ke items), `while`/`until`
(condition tak), `break`/`continue` (control), `while read` (file lines), aur functions (kaam ko
naam de ke reuse). Sabse practical: loop-variables `"$var"` quote karo, infinite-loop se bacho,
function se data `echo`+`$(...)` se lo (return se nahi), aur `>` vs `>>` loop mein dhyan.

[↑ Back to top](#top)

---

> **Chapter 10 khatam.** Ab tak: loops — `for` (list/files/`{1..5}`), `while` (condition tak),
> `until` (jab tak jhooth), `break`/`continue`, `while IFS= read -r` (file line-by-line); functions
> — define (`naam() {}`), arguments (`$1` andar), value wapas (`echo`+`$(...)` for data, `return`
> for success/fail), `local` variables. **Agla chapter:** input aur arguments — `$1..$9`, `$@`,
> `$#`, `shift`, `read`, aur `getopts` (proper flag parsing).

[↑ Back to top](#top)