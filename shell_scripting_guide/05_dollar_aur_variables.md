<a id="top"></a>
# Chapter 05 — `$` ka poora raaz aur Variables

Ab tak `$` humein kai jagah dikha — `$SHELL`, `$0`, `$PATH`. Par humne kabhi theek se nahi samjha ki
yeh `$` symbol *hai kya* aur kyun lagta hai. Yeh chapter poora `$` kholega — kyunki `$` shell ki
sabse important cheez hai, aur ise samjhe bina scripts likhna namumkin hai.

Ek line mein: **`$` ka matlab hai "iske aage wali cheez ki VALUE nikaalo, uska naam nahi"**. Par
iske kai roop hain — chaliye ek-ek karke poore detail mein.

Yeh chapter theory-heavy hai, aur `$` ke har roop ka literal matlab kholega.

---

## Is chapter ka index

- [5.1 — Variable kya hai (ek dabba jismein value rakhi hai)](#s5-1)
- [5.2 — Variable banana: `x=5` (aur spaces ka mana kyun)](#s5-2)
- [5.3 — `$` ka pehla roop: variable ki value nikalna (`$x`)](#s5-3)
- [5.4 — `${x}` — curly braces kyun aur kab](#s5-4)
- [5.5 — `$` ka doosra roop: command substitution `$(...)`](#s5-5)
- [5.6 — `$` ka teesra roop: special variables (`$?`, `$$`, `$0`, `$1`)](#s5-6)
- [5.7 — Environment variables aur `export` (`PATH`, `HOME`)](#s5-7)
- [5.8 — `echo` — screen pe dikhana (aur uske flags)](#s5-8)
- [5.9 — `printf` — echo se behtar, controlled output](#s5-9)
- [5.10 — Quotes ka poora raaz: `'single'` vs `"double"` vs bina quotes](#s5-10)
- [5.11 — Backtick `` ` `` vs `$(...)` (purana vs naya)](#s5-11)
- [5.12 — Nuances aur caveats](#s5-12)
- [5.13 — Real-life scenarios](#s5-13)

---

<a id="s5-1"></a>
## 5.1 — Variable kya hai (ek dabba jismein value rakhi hai)

**Variable** (matlab "badalne wala") ek **naam** hai jise aap kisi value (data) pe chipka dete ho —
jaise ek dabbe pe label. Baad mein us naam se aap value ko wapas nikaal sakte ho. Programming mein
yeh sabse basic cheez hai; shell mein bhi yehi.

**Analogy:** socho ek dabba hai jispe aapne label likha `naam`, aur usmein rakha `"Pragyesh"`. Ab
jab bhi aapko woh value chahiye, aap "us `naam` wale dabbe ki value do" bolte ho — aur `"Pragyesh"`
mil jata hai. Variable wahi dabba + label hai.

**Kyun zaroori:** value ko ek baar rakh lo, phir baar-baar us naam se use karo. Agar value badalni ho
toh ek jagah badlo, sab jagah update ho jayegi. Scripts mein yeh bahut kaam aata — jaise ek file ka
path ek variable mein rakh do, phir 10 jagah us variable se use karo.

**Do hisse har variable ke:**
- **Naam (label):** jaise `naam`, `count`, `filepath`. Yeh aap chunte ho.
- **Value (andar rakha data):** jaise `"Pragyesh"`, `5`, `/home/user/data.csv`.

**Zaroori farak — naam vs value (yehi `$` ka poora khel hai):** jab aap `naam` likhte ho, woh
**label** hai. Jab aap `$naam` likhte ho (dollar ke saath), woh **value** hai (`"Pragyesh"`). Yeh
farak Chapter ka dil hai — `$` hi woh cheez hai jo "label" ko "value" mein badalta hai (5.3).

> **Yaad rakhne wali baat:** Variable = ek naam (label) jispe ek value (data) rakhi hai — jaise
> labelled dabba. Naam se value nikalne ke liye `$` lagta hai (`naam` = label, `$naam` = value).

[↑ Back to top](#top)

---

<a id="s5-2"></a>
## 5.2 — Variable banana: `x=5` (aur spaces ka mana kyun)

Variable banane ka tareeka bilkul seedha hai — `naam=value`:

```
naam=Pragyesh
count=5
filepath=/home/user/data.csv
```
- **`naam=Pragyesh`** — ek variable `naam` banaya, usmein value `Pragyesh` rakhi. Bas.
- Ab `naam` (label) `Pragyesh` (value) ko point karta hai.

**SABSE ZAROORI niyam — `=` ke aas-paas SPACE NAHI:**
```
naam=Pragyesh       # SAHI
naam = Pragyesh     # GALAT — error dega!
```
- **Kyun galat?** Yaad karo Chapter 3 — space shell ke liye separator hai (tokens alag karta). Jab
  aap `naam = Pragyesh` likhte ho (spaces ke saath), shell ise **teen alag tokens** samajhta hai:
  `naam` (ek command!), `=` (argument), `Pragyesh` (argument). Woh sochta hai "`naam` naam ki koi
  command chalao" — aur `command not found` deta.
- Bina space (`naam=Pragyesh`) — shell ise ek hi cheez samajhta hai: "variable assignment". Isiliye
  `=` ke dono taraf space bilkul nahi. Yeh #1 galti hai jo naye log karte hain.

**Value mein space ho toh — quotes:**
```
naam="Pragyesh Mishra"
```
- Agar value mein khud space hai (do shabd), toh quotes zaroori (Ch 3.9 wala) — warna shell
  `Mishra` ko alag samjhega. Quotes value ko ek saath bandh dete hain (5.10 mein poora).

**Naam ke niyam:**
- Letters, numbers, underscore (`_`) — jaise `my_var`, `count2`, `FILE_PATH`.
- Number se shuru nahi (`2count` galat).
- Case-sensitive: `Naam` aur `naam` alag variables (Ch 2 wala case funda).
- Convention: apne variables lowercase (`count`), environment/important UPPERCASE (`PATH`, `HOME`) —
  yeh sirf ek aadat hai, zaroori nahi.

> **Yaad rakhne wali baat:** Variable banao: `naam=value` — `=` ke aas-paas **space NAHI** (space se
> shell confuse hokar error deta). Value mein space ho toh `"quotes"` mein. Naam letters/numbers/`_`,
> case-sensitive.

[↑ Back to top](#top)

---

<a id="s5-3"></a>
## 5.3 — `$` ka pehla roop: variable ki value nikalna (`$x`)

Ab asli baat — variable banaya toh uski value **nikalte kaise hain?** Yahin `$` aata hai.

**Niyam:** variable ke naam ke aage `$` lagao — shell us naam ki jagah uski value rakh dega.

```
naam=Pragyesh
echo $naam
```
- **`echo $naam`** — `echo` = screen pe dikhao (5.8), `$naam` = "naam variable ki VALUE". Shell
  `$naam` ko `Pragyesh` se badal deta, phir `echo Pragyesh` chalta.
- **Output:** `Pragyesh`

**Farak dekho — `$` ke saath vs bina:**
```
echo naam       # output: naam  (yeh sirf ek shabd hai, literal text)
echo $naam      # output: Pragyesh  (yeh variable ki value hai)
```
- `naam` (bina `$`) = literal shabd "naam" — shell iske andar dekhta hi nahi.
- `$naam` (with `$`) = "naam variable ke andar ki value" — shell use `Pragyesh` bana deta.
- **Yehi `$` ka asli kaam hai:** "yeh ek variable ka naam hai — iski jagah iski VALUE rakh do".

**Yeh humne Chapter 1 mein dekha tha:** yaad karo `echo $SHELL` — `$SHELL` matlab "SHELL variable ki
value" (`/bin/zsh`). Ab poora samajh aaya — `$` ne `SHELL` naam ko uski value se badla. Waise hi
`$PATH` (Ch 3) = PATH variable ki value.

**`$` ke bina variable ka koi matlab nahi (nikalne mein):** agar aap `$` bhool gaye toh shell value
nahi nikalega, sirf literal naam dikhayega. Yeh common galti hai — "mera variable kaam nahi kar
raha" ka matlab aksar "`$` lagana bhool gaye".

> **Yaad rakhne wali baat:** Variable ki value nikalne ko naam ke aage `$` lagao: `$naam` =
> "naam ki value". Bina `$` ke woh sirf literal shabd hai. `$` ka kaam: "naam ko value se badal do".
> Yeh `$SHELL`/`$PATH` wahi cheez thi.

[↑ Back to top](#top)

---

<a id="s5-4"></a>
## 5.4 — `${x}` — curly braces kyun aur kab

Aapne kabhi `${naam}` (curly braces `{ }` ke saath) dekha hoga aur socha "yeh `$naam` se alag kya
hai?" Jawab: **matlab bilkul same hai** — dono variable ki value dete hain. Braces sirf shell ko
saaf batane ke liye hain ki "variable ka naam yahan **khatam** ho raha hai".

**Kab zaroori — jab variable ke turant baad koi aur akshar ho:**
```
file=report
echo $file_2026        # GALAT: shell "file_2026" naam dhoondhega (jo hai hi nahi) -> khaali
echo ${file}_2026      # SAHI: report_2026
```
- Pehle case mein, shell confuse — usne socha variable ka naam `file_2026` hai (kyunki `_` bhi naam
  ka valid hissa hai, 5.2). Woh variable hai nahi, toh khaali value.
- `${file}_2026` mein braces ne clearly bola "variable `file` yahan khatam (`}`), uske baad `_2026`
  alag text hai". Output: `report_2026`.

**Simple case mein zaroorat nahi:**
```
echo $naam        # theek — aage koi confusing akshar nahi
echo ${naam}      # yeh bhi theek — bas extra braces
```
- Jab variable ke baad space ya koi non-naam character ho, braces ki zaroorat nahi — `$naam` kaafi.

**Rule of thumb:** normally `$naam` likho. Braces `${naam}` tab jab variable ke turant baad koi
letter/number/underscore chipka ho, taaki shell confuse na ho ki naam kahan khatam hua. (Braces ke
aur advanced use bhi hain — jaise default value dena — par woh aage; abhi yeh main use.)

> **Yaad rakhne wali baat:** `${naam}` = `$naam` (same value), braces sirf "naam yahan khatam" batate
> hain. Zaroori tab jab variable ke turant baad koi letter/number/`_` ho (`${file}_2026`). Warna
> `$naam` kaafi.

[↑ Back to top](#top)

---

<a id="s5-5"></a>
## 5.5 — `$` ka doosra roop: command substitution `$(...)`

Ab `$` ka ek aur powerful roop — **command substitution**. Iska matlab: "ek command chalao, aur
uske OUTPUT ko yahan value ki tarah rakh do".

**Syntax: `$(command)`** — dollar ke baad brackets mein ek command.

```
aaj=$(date)
echo $aaj
```
- **`$(date)`** — `date` ek command hai jo abhi ka time/tareekh deta hai. `$(date)` matlab "`date`
  command chalao aur uska output yahan daal do". Woh output `aaj` variable mein chala gaya.
- **`echo $aaj`** — output: `Mon Jun 30 14:20:00 IST 2026` (jo bhi `date` ne diya).

**Farak samajho — `$naam` vs `$(command)`:**
- **`$naam`** = ek variable ki value nikaalo (jo pehle se rakhi hai).
- **`$(command)`** = ek command chalao aur uska output value bana lo (naya banao).
- Dono `$` se shuru, par `$(...)` mein brackets hain aur andar ek command hoti hai.

**Seedha use (variable ke bina bhi):**
```
echo "Aaj ki date: $(date)"
echo "Is folder mein $(ls | wc -l) files hain"
```
- `$(date)` ka output seedha line mein aa gaya. Doosre mein — `$(ls | wc -l)` = "ls chalao, uski
  lines gino" (Ch 4.10 + Ch 6 pipe) ka output (ek number) seedha vaakya mein. Yeh bahut powerful
  hai — command ka result text mein embed kar diya.

**Kyun kaam ka:** scripts mein aksar aapko kisi command ka result aage use karna hota. Jaise "current
folder ka naam ek variable mein rakho": `dir=$(basename $(pwd))`. Ya "aaj ki date se backup file ka
naam banao": `backup="data_$(date +%Y%m%d).csv"`. Command ka output value ban jata — yeh scripting
ki reedh (backbone) hai.

> **Yaad rakhne wali baat:** `$(command)` = command chalao, uska OUTPUT value bana lo. `$naam` se
> farak: `$naam` purani value nikalta, `$(...)` nayi command chala ke output banata. Scripts mein
> command ka result aage use karne ka tareeka.

[↑ Back to top](#top)

---

<a id="s5-6"></a>
## 5.6 — `$` ka teesra roop: special variables (`$?`, `$$`, `$0`, `$1`)

Shell mein kuch **pehle se bane** (built-in) variables hote hain jinki value shell khud rakhta hai.
Inhe "special variables" kehte hain. Yeh `$` ke saath aate hain, par inka naam ek symbol ya number
hota hai. Sabse kaam ke:

**`$?` — pichhli command ka exit code (safal/asafal):**
```
ls notes.txt
echo $?
```
- **`$?`** = "abhi-abhi jo command chali, woh safal hui ya nahi" — ek number deta hai.
- **`0`** = safal (success — sab theek). **Koi bhi non-zero** (1, 2, 127...) = fail (kuch galat).
- Upar: agar `notes.txt` hai → `ls` safal → `$?` = `0`. Agar nahi hai → `ls` fail → `$?` = `1` (ya
  aur).
- **Kyun kaam ka:** scripts mein yeh check karte hain "pichhla kaam safal tha? tabhi aage badho".
  Yeh error handling ki neev hai (Ch 14). Ulta lagta hai par yaad rakho: **`0` = achha**, baaki bura.

**`$$` — abhi chal rahe shell ka process ID (PID):**
```
echo $$
```
- **`$$`** = current shell ka **process ID** (PID — har chalte program ko OS ek number deta,
  Ch 13). Output jaise `48213`. Scripts mein unique temp file naam banane ko kaam aata (`temp_$$`).

**`$0`, `$1`, `$2`... — script/command ke arguments (positional):**
- Yeh humne Chapter 1 mein chhua tha — ab poora. Jab aap ek script chalate ho arguments ke saath,
  woh arguments in numbered variables mein aate hain:
  - **`$0`** = script/command ka apna naam (0th cheez — Ch 1 wala `echo $0`).
  - **`$1`** = pehla argument, **`$2`** = doosra, aur aage.
- Misaal — maan lo ek script `greet.sh` hai jismein `echo "Hello $1"`, aur aap chalate ho:
```
./greet.sh Pragyesh
```
  - Yahan `$1` = `Pragyesh` (pehla argument). Output: `Hello Pragyesh`.
- **`$0` mein `0` kyun = naam?** Yaad karo Ch 1 — arguments 0 se ginte hain, aur 0th "argument"
  hamesha command khud hota hai. `$1` se aapke diye arguments shuru. (Yeh Ch 11 mein poora.)

**Kuch aur (jaan-ne bhar ke):** `$#` = kitne arguments aaye (ginti), `$@` = saare arguments ek saath.
Yeh Chapter 11 (input/arguments) mein detail se.

> **Yaad rakhne wali baat:** Special variables: `$?` = pichhli command safal? (`0`=haan, non-zero=
> fail), `$$` = current shell ka PID, `$0` = script ka naam, `$1 $2...` = script ke arguments. `$?`
> error-handling ki neev (Ch 14), `$1` script-input ki (Ch 11).

[↑ Back to top](#top)

---

<a id="s5-7"></a>
## 5.7 — Environment variables aur `export` (`PATH`, `HOME`)

Ab tak jo variables banaye (`naam=Pragyesh`) woh **local** the — sirf aapke current shell mein zinda,
aur us shell se chale kisi doosre program tak nahi jaate. **Environment variables** alag hain — yeh
"poore environment" mein hote hain aur shell se chale programs ko bhi milte hain.

**Farak ek misaal se:**
```
naam=Pragyesh          # local variable — sirf is shell mein
export naam=Pragyesh   # environment variable — is shell + iske chalaye programs ko bhi
```
- **`export`** command variable ko "upgrade" karta hai — local se environment banata. `export`
  matlab "isko bahar (chale programs tak) bhej do". Bina `export` ke, agar aap is shell se koi
  Python script chalao, use `naam` nahi dikhega. `export` ke baad dikhega.

**Kyun zaroori:** bahut se programs apni settings environment variables se lete hain. Jaise ek app
`DATABASE_URL` environment variable dhoondh sakti hai. Aap `export DATABASE_URL="..."` karke use woh
value dete ho. Yeh programs ko config dene ka standard tareeka hai.

**Common built-in environment variables (yeh pehle se set hote):**
- **`PATH`** — folders ki list jahan shell command dhoondhta (Ch 3.11). Sabse important.
- **`HOME`** — aapke home folder ka path (`/Users/pragyesh`). `~` isi se aata hai (Ch 2).
- **`USER`** — aapka username. **`SHELL`** — default shell (Ch 1). **`PWD`** — current folder.
- Dekho: `echo $HOME`, `echo $USER` — inki values dikhengi.

**Saare environment variables dekhna:**
```
env
```
- **`env`** command saare environment variables ki list dikhata hai (naam=value format). Bahut saare
  honge — yeh aapke shell ka poora "environment" hai.

**Zaroori caveat — `export` sirf current shell + aage ke liye:** jab aap terminal band karte ho,
yeh export kiya variable chala jata (temporary). Hamesha ke liye chahiye toh use `.zshrc`/`.bashrc`
mein daalo (Ch 8 wala) — taaki har naye terminal mein automatically set ho.

> **Yaad rakhne wali baat:** Local variable (`naam=x`) sirf current shell mein; environment variable
> (`export naam=x`) chale programs ko bhi milta. `export` = "bahar bhej do". `PATH`/`HOME`/`USER`
> built-in env vars. `env` = sab dekho. Permanent chahiye toh `.zshrc` mein.

[↑ Back to top](#top)

---

<a id="s5-8"></a>
## 5.8 — `echo` — screen pe dikhana (aur uske flags)

**`echo`** ka matlab hai "goonj/dohrana" — yeh apne aage jo diya jaye use **screen pe chhaap deta**
hai. Yeh humne poore guide mein use kiya; ab poora.

```
echo Hello World
```
- Output: `Hello World`. Seedha text screen pe.

**Variable ke saath (5.3 wala):**
```
naam=Pragyesh
echo Hello $naam
```
- Output: `Hello Pragyesh`. `echo` ne `$naam` ki value dikhayi.

**Do kaam ke flags:**

**`-n` — aakhir mein nayi line mat daalo:**
```
echo -n "Loading"
```
- Normally `echo` ke baad cursor agli line pe chala jata (ek "newline" daalta). `-n` woh rok deta —
  cursor usi line pe rehta. Progress dikhane mein kaam aata (`Loading...` ek hi line pe banana).

**`-e` — special characters ko samjho (jaise `\n` = nayi line):**
```
echo -e "Line1\nLine2"
```
- **`-e`** = "escape sequences enable karo". `\n` matlab "nayi line" (newline). `-e` ke saath output:
  do lines mein `Line1` aur `Line2`. Bina `-e` ke, `\n` literal `\n` hi chhap jata (Mac ke zsh mein
  behaviour thoda alag — 5.9 mein printf isiliye behtar).
- Common escapes: `\n` (nayi line), `\t` (tab — bade space).

> **Yaad rakhne wali baat:** `echo` = text/variable screen pe dikhao. `-n` = aakhir mein nayi line
> mat daalo (usi line pe raho), `-e` = `\n`/`\t` jaise special chars ko samjho. `echo` simple output
> ka standard tareeka.

[↑ Back to top](#top)

---

<a id="s5-9"></a>
## 5.9 — `printf` — echo se behtar, controlled output

**`printf`** = "print formatted" (formatted = saanche/format mein). Yeh `echo` jaisa hi output deta,
par zyada control ke saath aur **har system pe same** behave karta (echo ka `-e` kuch systems pe
kaam karta kuch pe nahi — printf reliable hai).

```
printf "Hello %s\n" "Pragyesh"
```
- **`%s`** = ek "placeholder" (jagah-rakhne wala) — matlab "yahan ek string (text) aayegi". Jo value
  baad mein di (`"Pragyesh"`) woh `%s` ki jagah aa jati.
- **`\n`** = nayi line (printf hamesha samajhta hai, `-e` ki zaroorat nahi — isiliye behtar).
- Output: `Hello Pragyesh` (phir nayi line).

**Kai placeholders:**
```
printf "Naam: %s, Umar: %d\n" "Pragyesh" 30
```
- **`%s`** = string (text), **`%d`** = number (digit/integer). Pehla `%s`←`Pragyesh`, `%d`←`30`.
  Output: `Naam: Pragyesh, Umar: 30`.

**`echo` vs `printf` — kab kaunsa:**
- **`echo`** — jaldi, simple text dikhana. Roz ke chhote kaam. (99% baar yeh use hota.)
- **`printf`** — jab format control chahiye (columns, decimals), ya script ko har system pe same
  chalna ho (portable — Ch 1 wala), ya `\n`/`\t` reliable chahiye. Scripts mein professional log
  banane ko.

**Zaroori caveat — printf mein `\n` khud daalna padta:** `echo` apne aap aakhir mein nayi line
daalta; `printf` **nahi** deta jab tak aap khud `\n` na likho. Isiliye printf ke format string ke
aakhir mein aksar `\n` hota. Bhoole toh output agli command se chipak jayega.

> **Yaad rakhne wali baat:** `printf "text %s\n" value` = formatted output, `%s`=string/`%d`=number
> placeholder. `echo` se behtar: har system pe same, `\n` reliable. Par `\n` khud daalna padta
> (echo apne aap deta). Simple = echo, controlled/portable = printf.

[↑ Back to top](#top)

---

<a id="s5-10"></a>
## 5.10 — Quotes ka poora raaz: `'single'` vs `"double"` vs bina quotes

Yeh section **bahut important** hai — quotes shell ki sabse confusing cheez hain, aur bugs ka #1
source. Teen tarah likha ja sakta: bina quotes, single quotes (`'`), double quotes (`"`). Teeno alag
behave karte hain.

Ek variable set karke teeno dekhte hain:
```
naam=Pragyesh
```

**1. Bina quotes — variable expand hota, par spaces todte hain:**
```
echo $naam            # output: Pragyesh
echo Hello   World    # output: Hello World (extra spaces gayab — shell ne toda)
```
- Bina quotes, shell `$naam` ki value nikalta (expand karta) — achha. Par woh spaces pe tokens todta
  hai (Ch 3.9), toh multiple spaces ek ho jate, aur space wali cheezein bikhar jati.

**2. Double quotes `"..."` — variable expand hota, spaces safe:**
```
echo "Hello $naam"        # output: Hello Pragyesh
echo "Hello   World"      # output: Hello   World (spaces bache!)
```
- **Double quotes ke andar `$` KAAM karta hai** — `$naam` phir bhi value banta (`Pragyesh`). Par
  spaces/special stuff safe rehte (shell todta nahi). **Yeh sabse zyada use hota** — "value bhi
  chahiye, aur safe bhi".

**3. Single quotes `'...'` — kuch expand NAHI, sab literal:**
```
echo 'Hello $naam'        # output: Hello $naam  (literally! value nahi)
```
- **Single quotes ke andar `$` KAAM NAHI karta** — sab kuch literal, jaise likha waise. `$naam`
  literal `$naam` hi chhapta, value nahi. Jab aapko `$` ya koi special char ko *literally* dikhana
  ho (bina expand kiye), single quotes.

**Ek table mein (yaad rakhne ko):**

| Tareeka | `$variable` expand? | Spaces safe? | Kab use |
|---|---|---|---|
| Bina quotes | Haan | Nahi (todta) | Simple single-word cheezein |
| `"double"` | **Haan** | **Haan** | **Default — value chahiye + safe** |
| `'single'` | Nahi (literal) | Haan | Jab `$`/special ko literally dikhana ho |

**Sabse zaroori rule:** **jab confuse ho, double quotes `"..."` use karo.** Yeh 90% cases mein sahi
hai — variable bhi expand hota, aur spaces/special safe. Bina quotes wali "word-splitting" bugs se
bachne ka yehi tareeka hai (jaise `rm $file` jahan `$file` mein space ho — bina quotes disaster,
`"$file"` safe).

> **Yaad rakhne wali baat:** `"double"` = `$` expand + spaces safe (DEFAULT, 90% cases). `'single'` =
> sab literal, `$` kaam nahi (jab `$` ko waise hi dikhana ho). Bina quotes = expand par spaces todta
> (risky). Confuse? → double quotes.

[↑ Back to top](#top)

---

<a id="s5-11"></a>
## 5.11 — Backtick `` ` `` vs `$(...)` (purana vs naya)

Aapko purane scripts mein **backtick** (`` ` `` — keyboard pe `1` ke baayein, `~` ke saath wali key)
dikhega, jaise `` aaj=`date` ``. Yeh command substitution ka **purana tareeka** hai — bilkul `$(date)`
jaisa hi kaam karta.

```
aaj=`date`        # purana tareeka (backtick)
aaj=$(date)       # naya tareeka — same kaam
```
- Dono `date` command chala ke output `aaj` mein daalte hain. Result same.

**Toh farak kya, aur kaunsa use karein?** **Hamesha `$(...)` use karo, backtick nahi.** Do wajah:

1. **Nesting (ek ke andar ek) — `$(...)` mein aasaan, backtick mein painful:**
```
echo $(dirname $(pwd))        # $(...) — saaf, ek ke andar ek aaram se
```
   - Backtick ke saath andar-andar command daalna bahut mushkil aur galti-prone hai (backtick ko
     "escape" karna padta). `$(...)` mein bracket ke andar bracket seedha kaam karta.

2. **Padhne mein clear:** `$(...)` mein shuru aur end (`(` aur `)`) saaf dikhte. Backtick shuru-end
   ek jaisa dikhta (`` ` `` dono taraf), aur `'` (single quote) se confuse hota — chhoti screen pe
   pehchanna mushkil.

**Toh backtick sirf jaan-ne ke liye:** aapko *likhna* kabhi nahi (hamesha `$(...)`), par *padhna*
aana chahiye — kyunki purane scripts/tutorials mein backtick milega, aur aapko samajhna chahiye ki
"yeh bhi command substitution hai, `$(...)` jaisa".

> **Yaad rakhne wali baat:** Backtick `` `cmd` `` = purana command substitution, `$(cmd)` = naya —
> same kaam. Hamesha `$(...)` likho (nesting aasaan, padhne mein clear). Backtick sirf padhne/
> pehchanne ke liye (purane code mein milega).

[↑ Back to top](#top)

---

<a id="s5-12"></a>
## 5.12 — Nuances aur caveats

- **`=` ke aas-paas space = sabse common galti (dohra raha hoon):** `x = 5` galat, `x=5` sahi. Space
  se shell `x` ko command samajh leta. Yaad rakho — assignment mein `=` chipka hua.

- **`$var` ko hamesha `"$var"` (double quotes) mein rakho scripts mein:** agar variable ki value mein
  space ho (jaise ek file-path `My File.txt`), toh bina quotes `rm $file` ko shell `rm My File.txt`
  (do arguments) bana deta — galat file delete ho sakti. `"$file"` safe. Yeh "quote your variables"
  rule professional scripting ka sabse bada niyam hai.

- **Undefined variable = khaali (error nahi):** agar aap aisa variable use karo jo set hi nahi hua
  (`echo $tyfoo`), shell use **khaali** (kuch nahi) maan leta — error nahi deta. Yeh bugs chhupata
  hai (typo kiya variable naam mein, aur chup-chaap khaali chala gaya). Ch 14 mein `set -u` isse
  bachata (undefined pe error dega).

- **Single quote ke andar single quote nahi daal sakte:** `'it's'` toot jayega (beech wala `'` ko
  end samajhta). Aise mein double quotes use karo (`"it's"`) ya escape (Ch 3.9).

- **`$?` turant check karo:** `$?` sirf *pichhli* command ka result rakhta. Agar aapne beech mein
  koi aur command (jaise `echo`) chala di, toh `$?` ab us `echo` ka result dega, purani ka nahi.
  Isliye exit code turant next line pe check/save karo.

- **`export` permanent nahi:** terminal band = export gaya. Hamesha ke liye `.zshrc`/`.bashrc` mein
  (Ch 8). Yeh bhoolne se "maine set kiya tha par naye terminal mein nahi hai" wali confusion hoti.

- **CAPS vs small naam:** convention hai environment/constants CAPS (`PATH`), apne temp vars small
  (`count`). Par yeh sirf aadat — shell dono ko same treat karta (bs case-sensitive, `Path` ≠
  `PATH`).

[↑ Back to top](#top)

---

<a id="s5-13"></a>
## 5.13 — Real-life scenarios

**Scenario 1 — "Path ek jagah rakho, kai jagah use karo."** Aapke script mein ek data folder ka path
baar-baar aata hai. Ek variable: `data_dir="/home/user/project/data"`. Ab har jagah `"$data_dir"`
use karo. Path badalna ho? Sirf ek line badlo, poora script update. Yeh variables ka asli fayda.

**Scenario 2 — "Date-wala backup file naam banao."** Aapko roz ka backup chahiye jismein date ho.
`backup="data_$(date +%Y%m%d).csv"` (command substitution, 5.5). Aaj chala toh `data_20260630.csv`
banega. Har din alag naam, automatic. Yeh scripting mein bahut common pattern.

**Scenario 3 — "Command safal hui tabhi aage badho."** Script mein aap ek file download karte ho,
phir process karna hai — par sirf tab jab download safal ho. Download ke baad `$?` check karo (`0` =
safal, 5.6). Yeh error handling ki neev hai (Ch 14 mein poora, `&&` ke saath).

**Scenario 4 — "Variable kaam nahi kar raha (khaali aa raha)."** Aapne `echo $filename` kiya par
kuch nahi aaya. Do common wajah (5.3, 5.12): (1) `$` lagana bhool gaye, ya (2) variable set hi nahi
hua / naam mein typo. `echo "[$filename]"` karke dekho — agar `[]` khaali aaya toh variable set nahi.

**Scenario 5 — "Space wale filename ne script toda."** Aapke script mein `rm $file` tha, aur ek din
`$file` ki value `My Report.pdf` (space wali) thi — `rm` ne `My` aur `Report.pdf` do alag samjhe,
galat cheez delete/error. Fix: hamesha `rm "$file"` (double quotes, 5.10/5.12). Yeh production bug
ka classic source hai.

**Saar:** Chapter 5 shell scripting ka dil hai. `$` ke teen roop — `$var` (value), `$(cmd)` (command
ka output), `$?`/`$1` (special) — sab yaad rakho. Sabse bada practical sabak: **variables ko hamesha
`"double quotes"` mein use karo** (`"$var"`) — yeh spaces/word-splitting ke 90% bugs bacha leta.

[↑ Back to top](#top)

---

> **Chapter 05 khatam.** Ab tak: variable (`naam=value`, `=` pe space nahi); `$var` (value nikalna);
> `${var}` (braces kab); `$(cmd)` (command substitution); special vars (`$?` `$$` `$0` `$1`);
> environment variables + `export`; `echo` aur `printf`; aur quotes (`'single'` vs `"double"` vs
> bina) — sabse zaroori `"$var"` ki aadat. **Agla chapter:** pipes aur redirects (`|`, `>`, `>>`,
> `2>`) aur Unix philosophy — chhote tools ko jodna.

[↑ Back to top](#top)
