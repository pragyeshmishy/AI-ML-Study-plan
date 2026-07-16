<a id="top"></a>
# Chapter 11 — Input aur Arguments (script ko cheezein dena)

Ab tak humne scripts likhi jo fixed kaam karti. Par asli scripts ko **input** chahiye — user se, ya
command chalate waqt. Jaise `./backup.sh myfile.txt` — yahan `myfile.txt` script ko diya "argument"
hai. Yeh chapter batata hai script cheezein kaise leti hai: command-line arguments (`$1`), user se
poochna (`read`), aur proper flag-parsing (`getopts`).

Yeh theory-heavy chapter hai — har special variable (`$1`, `$@`, `$#`) aur `read`/`getopts` kholega.

---

## Is chapter ka index

- [11.1 — Do tarah ke input: arguments vs interactive](#s11-1)
- [11.2 — Positional arguments: `$1`, `$2`, ... `$9`](#s11-2)
- [11.3 — `$@`, `$*`, `$#` — saare arguments aur ginti](#s11-3)
- [11.4 — `shift` — arguments ko khiskana](#s11-4)
- [11.5 — Input validation: argument diya ya nahi (`$#` check)](#s11-5)
- [11.6 — `read` — user se interactive input lena](#s11-6)
- [11.7 — `read` ke flags: `-p`, `-s`, `-r`](#s11-7)
- [11.8 — `getopts` — proper flag parsing (`-v`, `-f file`)](#s11-8)
- [11.9 — Nuances aur caveats](#s11-9)
- [11.10 — Real-life scenarios](#s11-10)

---

<a id="s11-1"></a>
## 11.1 — Do tarah ke input: arguments vs interactive

Ek script do tareeke se input le sakti hai. Farak samajhna zaroori — kab kaunsa use karein.

**1. Command-line arguments (script chalate waqt diye):**
```
./backup.sh notes.txt daily
```
- Yahan `notes.txt` aur `daily` **arguments** hain — script ke naam ke baad, space se alag diye
  (Ch 3 wala). Script inhe `$1`, `$2` se padhti (11.2). User ne chalate hi de diya, script ruk ke
  poochti nahi.
- **Kab:** jab input pehle se pata ho, ya script automate/schedule karni ho (cron — koi baithke
  jawab dene wala nahi). Yeh scripts ka main tareeka hai.

**2. Interactive input (script chalte waqt poochti hai):**
```
./setup.sh
# Script poochti: "Aapka naam? " -> aap type karte ho
```
- Script `read` (11.6) se **ruk ke poochti** hai, user type karta, phir aage. Baat-cheet (interactive)
  jaisa.
- **Kab:** jab input pehle se na pata ho aur user se lena ho (jaise password, confirmation "sure?
  y/n"). Par automate nahi ho sakta (koi jawab dega tab chalega).

**Kaunsa behtar?** Aam taur pe **arguments** (tareeka 1) — kyunki automate ho sakte, fast, aur
scriptable. `read` (interactive) sirf tab jab genuinely user se poochna ho (password, dangerous
action ki confirmation). Production/automation scripts arguments use karte; interactive setup-wizard
jaise cheezon mein `read`.

> **Yaad rakhne wali baat:** Do input tareeke — arguments (`./script.sh x y`, `$1`/`$2` se padho,
> automate-friendly) aur interactive (`read` se ruk ke poocho, user type kare). Aam taur arguments
> behtar (automate); `read` sirf jab genuinely poochna ho.

[↑ Back to top](#top)

---

<a id="s11-2"></a>
## 11.2 — Positional arguments: `$1`, `$2`, ... `$9`

Jab aap script ko arguments dete ho, woh **numbered variables** mein aate hain — position ke hisaab
se. Isliye "positional" (position wale). Yeh Ch 5.6 mein chhua tha — ab poora.

```
./greet.sh Pragyesh Mishra 30
```
- Script ke andar:
  - **`$0`** = script ka naam khud (`./greet.sh`) — Ch 5.6 wala (0th = command khud).
  - **`$1`** = `Pragyesh` (pehla argument)
  - **`$2`** = `Mishra` (doosra)
  - **`$3`** = `30` (teesra)
- Har argument apni position ke number pe. Space se alag (Ch 3) — teen alag arguments.

**Script mein use:**
```
#!/bin/bash
echo "Script: $0"
echo "Pehla naam: $1"
echo "Doosra naam: $2"
echo "Umar: $3"
```
- Chalao `./greet.sh Pragyesh Mishra 30` → output har variable ki value. Yeh script-ko-input dene ka
  sabse basic tareeka.

**`$1` se `$9` tak, phir `${10}`:** single-digit (`$1`-`$9`) seedha. Par 10th aur aage ke liye braces
zaroori: `${10}`, `${11}` (Ch 5.4 wala — warna `$10` ko shell `$1` + `0` samajh leta). Aam scripts
mein itne arguments km hote, par jaan lo.

**Position matter karti (order):** `$1` hamesha *pehla* diya argument. Agar user order badal de
(`./greet.sh 30 Pragyesh`), toh `$1=30`, `$2=Pragyesh` — galat. Isliye scripts mein aksar batate hain
"usage: `./script.sh <naam> <umar>`" taaki user sahi order de (11.5).

> **Yaad rakhne wali baat:** Arguments numbered variables mein: `$0` (script naam), `$1` (pehla),
> `$2` (doosra)... Position se (space-alag). 10+ ke liye `${10}` (braces). Order matter karta —
> `$1` = pehla diya. Script-input ka basic tareeka.

[↑ Back to top](#top)

---

<a id="s11-3"></a>
## 11.3 — `$@`, `$*`, `$#` — saare arguments aur ginti

Kabhi aapko individual `$1`, `$2` nahi, balki **saare arguments ek saath** ya unki **ginti** chahiye.
Teen special variables:

**`$#` — kitne arguments aaye (ginti):**
```
#!/bin/bash
echo "Aapne $# arguments diye"
```
- `./script.sh a b c` → `$#` = `3`. Yeh input-validation mein sabse kaam ka (11.5) — "kya user ne
  itne arguments diye jitne chahiye?"

**`$@` — saare arguments (ek-ek alag):**
```
for arg in "$@"
do
    echo "Argument: $arg"
done
```
- **`$@`** = saare arguments ki list. `for ... in "$@"` = har argument pe loop (Ch 10.2). `./script.sh
  a b c` → teen baar, `$arg` = a, b, c. Jab number of arguments pata na ho aur sab pe kaam karna ho.

**`$*` vs `$@` (subtle par important farak):**
- **`"$@"`** (quotes ke saath) = har argument **alag** rehta (chahe usmein space ho). Yeh **hamesha
  use karo**.
- **`"$*"`** = saare arguments **ek single string** ban jate (jud ke). Kam use hota.
- Farak sirf tab dikhta jab kisi argument mein space ho. Rule: **`"$@"` use karo** (arguments alag,
  safe) — yeh 99% sahi hai. `"$*"` bhoolo.

**Poora misaal:**
```
#!/bin/bash
echo "Total arguments: $#"
echo "Saare: $@"
echo "Ek-ek:"
for arg in "$@"; do
    echo "  - $arg"
done
```
- `./script.sh apple banana cherry` → `Total: 3`, `Saare: apple banana cherry`, phir ek-ek list.
  Yeh variable-number-of-inputs handle karne ka standard tareeka.

> **Yaad rakhne wali baat:** `$#` = arguments ki ginti (validation ke liye), `"$@"` = saare arguments
> alag-alag (loop mein use, HAMESHA quotes), `"$*"` = sab jud ke ek string (kam use). Rule: `"$@"`
> use karo. `$#` se check "kitne aaye".

[↑ Back to top](#top)

---

<a id="s11-4"></a>
## 11.4 — `shift` — arguments ko khiskana

**`shift`** arguments ko ek position **khiska deta** hai — `$2` ban jata `$1`, `$3` ban jata `$2`,
aur pehla wala nikal jata. Jaise ek line mein sabse aage wala hat gaya, baaki aage badh gaye.

```
#!/bin/bash
echo "Pehle: $1"     # maan lo: apple
shift
echo "Shift ke baad: $1"   # ab: banana
```
- `./script.sh apple banana cherry` — pehle `$1=apple`. `shift` ke baad `$1=banana` (apple nikal
  gaya, sab ek aage khiske). `$#` bhi ek kam ho jata.

**Kab kaam ka — pehle argument ko alag treat karo, baaki process karo:**
```
command=$1       # pehla argument = command (jaise "start")
shift            # use hata do
# ab "$@" mein sirf baaki arguments (command ke aage wale)
echo "Command: $command, baaki: $@"
```
- `./tool.sh deploy server1 server2` — `$1` (deploy) ko `command` mein rakha, `shift` se hata diya,
  ab `"$@"` = `server1 server2` (sirf baaki). Yeh tab useful jab pehla argument "kya karna" ho aur
  baaki "kis pe".

**Loop mein `shift` (arguments ek-ek process karna):**
```
while [ $# -gt 0 ]
do
    echo "Processing: $1"
    shift
done
```
- `while [ $# -gt 0 ]` = "jab tak arguments bache hain" (`$#` > 0). Har baar `$1` process karo, phir
  `shift` (agla `$1` ban jaye, `$#` ghate). Sab process hone pe `$#`=0, loop ruk gaya. Yeh manual
  argument-processing ka ek tareeka (getopts, 11.8, isse zyada structured hai).

> **Yaad rakhne wali baat:** `shift` = arguments ek position khiskao (`$2`→`$1`, pehla nikal jata,
> `$#` ghate). Use: pehle argument ko alag treat karo (command), baaki `"$@"` mein rahe. Loop mein
> `while [ $# -gt 0 ]; do ...; shift; done` se sab process.

[↑ Back to top](#top)

---

<a id="s11-5"></a>
## 11.5 — Input validation: argument diya ya nahi (`$#` check)

Achhi script pehle **check karti hai ki sahi input mila** — warna aage crash/galat kaam. Yeh
"validation" (jaanch) production scripts ki zaroori aadat hai.

**Sabse common — zaroori argument diya ya nahi:**
```
#!/bin/bash
if [ $# -lt 1 ]
then
    echo "Usage: $0 <filename>"
    exit 1
fi
echo "Processing: $1"
```
- `[ $# -lt 1 ]` = "agar arguments 1 se kam hain (matlab 0 = koi nahi diya)" (Ch 9.7). Toh:
  - **Usage message** dikhao — user ko batao sahi tareeka (`$0` = script naam, Ch 5.6). Yeh
    professional touch hai — user ko guess nahi karna padta.
  - **`exit 1`** — script rok do, fail code ke saath (Ch 5.6 — non-zero = fail). Aage mat badho
    kyunki input hi nahi.
- Yeh Ch 9.13 Scenario 2 wala tha — ab poora context.

**`-z` se bhi check (khaali argument):**
```
if [ -z "$1" ]
then
    echo "Error: filename zaroori hai"
    exit 1
fi
```
- `[ -z "$1" ]` = "agar `$1` khaali hai" (Ch 9.9). Yeh bhi common — `$#` "ginti" check karta, `-z`
  "khaali" check. Dono theek; `$#` zyada precise jab exact number chahiye.

**File actually hai ya nahi (aur ek layer):**
```
if [ ! -f "$1" ]
then
    echo "Error: file '$1' nahi mili"
    exit 1
fi
```
- Sirf argument mila kaafi nahi — woh file *actually* honi bhi chahiye (`-f`, Ch 9.7 + `!` Ch 9.10).
  Yeh defensive scripting — argument diya, par galat/na-maujood file ho toh pehle pakdo.

**Validation ka pattern (yaad rakho):** script ke shuru mein — (1) sahi ginti arguments? (`$#`), (2)
khaali toh nahi? (`-z`), (3) file/folder actually hai? (`-f`/`-d`). Fail pe usage-message + `exit 1`.
Yeh "fail fast" — galat input pe turant ruko, aage crash na ho.

> **Yaad rakhne wali baat:** Validation script ke shuru mein: `[ $# -lt 1 ]` (arguments mile?),
> `[ -z "$1" ]` (khaali?), `[ ! -f "$1" ]` (file hai?). Fail pe `echo "Usage: $0 ..."; exit 1`.
> "Fail fast" — galat input pe turant ruko, professional usage-message do.

[↑ Back to top](#top)

---

<a id="s11-6"></a>
## 11.6 — `read` — user se interactive input lena

**`read`** user se ek line input **maangta** hai — script ruk jati, user type karta + Enter, aur woh
value ek variable mein aa jati.

```
echo "Aapka naam kya hai?"
read naam
echo "Namaste, $naam!"
```
- `read naam` — script ruk gayi, cursor blink. User type karta (jaise `Pragyesh`) + Enter. Woh
  `naam` variable mein chala gaya. Phir `echo` — `Namaste, Pragyesh!`.
- Yeh interactive input (11.1) — script baat-cheet karti.

**Kai values ek saath:**
```
echo "Naam aur umar (space se):"
read naam umar
echo "$naam ki umar $umar"
```
- `read naam umar` — user `Pragyesh 30` type kare, toh `naam=Pragyesh`, `umar=30` (space se alag ho
  gaye). Ek se zyada variables ek `read` mein.

**`read` file se bhi (Ch 10.7 wala):** yaad karo `while read line; do ...; done < file` — wahan
`read` file ki lines padh raha tha (keyboard nahi). `read` dono se kaam karta — interactive
(keyboard) ya redirect (`< file`). Context pe depend.

**Kab use, kab nahi (11.1 dohra):** `read` sirf jab genuinely user se poochna ho (jaise confirmation
"delete karun? (y/n)", ya password). Automate/scheduled scripts mein `read` **mat** use karo — koi
jawab dega nahi, script atak jayegi. Wahan arguments (`$1`) use karo.

> **Yaad rakhne wali baat:** `read naam` = user se input maango (script rukti, user type kare, `naam`
> mein aata). `read a b` = kai values (space se). File se bhi (`< file`, Ch 10.7). Sirf genuine
> interactive kaam mein — automate scripts mein nahi (atak jayegi).

[↑ Back to top](#top)

---

<a id="s11-7"></a>
## 11.7 — `read` ke flags: `-p`, `-s`, `-r`

`read` ke kuch flags use behtar banate hain — khaaskar prompt aur password ke liye.

**`-p` — prompt inline (ek line mein poocho):**
```
read -p "Aapka naam: " naam
echo "Namaste, $naam!"
```
- **`-p "text"`** = prompt dikhao aur usi line pe input lo (`p` = prompt). Bina `-p` ke aapko alag
  `echo` karna padta (11.6). `-p` se saaf: `Aapka naam: ` phir wahin cursor. Cleaner.

**`-s` — silent (input dikhao mat — passwords ke liye):**
```
read -sp "Password: " pass
echo    # nayi line (kyunki -s ne Enter ka newline nahi dikhaya)
echo "Password mil gaya (length: ${#pass})"
```
- **`-s`** = silent (`s` = silent). User jo type kare woh screen pe **dikhe nahi** (jaise password
  fields mein dots/kuch nahi). Passwords/secrets ke liye zaroori — koi peeche se dekh na le.
- `-sp` = `-s` + `-p` jode (Ch 3.6 flags jodna). `${#pass}` = pass ki length (Ch 5.4 style).

**`-r` — raw (backslash ko literal rakho):**
```
read -r line
```
- **`-r`** = raw (`r` = raw). Bina `-r`, `read` backslash (`\`) ko "escape character" samajh leta aur
  kha jata. `-r` se `\` literal rehta. **Hamesha `-r` use karo** (jab tak khaas kaaran na ho) — yeh
  Ch 10.7 mein `while IFS= read -r` mein dekha. Safe default.

**Teeno saath (common pattern):**
```
read -rp "Filename: " filename
read -rsp "Password: " password
```
- `-rp` = raw + prompt (normal input). `-rsp` = raw + silent + prompt (password). Yeh professional
  input-lene ke standard combos.

**Timeout `-t` (bonus):** `read -t 10 answer` = 10 second wait, na aaya toh aage badho (na atke).
Automate-ish scripts mein jahan default chahiye.

> **Yaad rakhne wali baat:** `read -p "prompt: " var` (inline prompt), `-s` (silent — passwords,
> dikhe nahi), `-r` (raw — backslash literal, HAMESHA use karo). Combos: `-rp` (normal), `-rsp`
> (password). `-t N` (timeout).

[↑ Back to top](#top)

---

<a id="s11-8"></a>
## 11.8 — `getopts` — proper flag parsing (`-v`, `-f file`)

Ab tak arguments position se aate the (`$1`, `$2`). Par asli tools **flags** lete hain (`-v`, `-f
file` — Ch 3 wala). Jaise `./deploy.sh -v -f config.txt`. Inhe theek se handle karne ka standard
tareeka hai **`getopts`** (get-options).

**Kyun `getopts` (position se kyun nahi):** flags kisi bhi order mein aa sakte (`-v -f x` ya `-f x
-v`), kuch value lete kuch nahi (Ch 3.7), kuch optional. Position (`$1`) se yeh handle karna
painful. `getopts` yeh saaf karta — "kaunse flags allowed, kaunsa value leta" bata do, woh parse kar
deta.

**Structure:**
```
while getopts "vf:" opt
do
    case "$opt" in
        v)
            echo "Verbose ON"
            ;;
        f)
            echo "File: $OPTARG"
            ;;
        *)
            echo "Galat flag"
            exit 1
            ;;
    esac
done
```

Tod ke:
- **`getopts "vf:" opt`** — `"vf:"` = kaunse flags allowed. `v` (koi value nahi), `f:` (colon `:` ka
  matlab "yeh value leta", Ch 3.7 wala `-f file`). `opt` = har baar jo flag mila woh ismein aata.
- **`while getopts ...`** = "jab tak flags hain, ek-ek parse karo" (loop, Ch 10.4).
- **`case "$opt" in`** = har flag pe alag kaam (Ch 9.11). `v)` → verbose, `f)` → file.
- **`$OPTARG`** = value-lene wale flag ki value (`f` ke saath jo diya, jaise `config.txt`). "OPT
  ARGument" — flag ka argument.

**Chalao:**
```
./deploy.sh -v -f config.txt
```
- `getopts` `-v` dekha → `v)` → "Verbose ON". `-f config.txt` dekha → `f)`, `$OPTARG=config.txt` →
  "File: config.txt". Order badal do (`-f config.txt -v`) — phir bhi sahi kaam (getopts order-safe).

**Colon `:` ka matlab (yeh Ch 3.7 se juda):** `"vf:"` mein — jis flag ke baad `:` hai (`f:`), woh
**value leta** (`-f something`); jiske baad nahi (`v`), woh sirf switch (`-v`). Yeh exactly Ch 3.7
wala "value lene wale flag" hai — getopts mein `:` se batate.

**Kab use:** jab aapka script **flags** le (professional CLI tool jaisa) — `-v`, `-o output`, etc.
Simple scripts (sirf 1-2 positional arguments) mein `$1`/`$2` kaafi; flags wale tools mein `getopts`.

> **Yaad rakhne wali baat:** `getopts "vf:" opt` = flags parse karo (`v` = switch, `f:` = value-lene
> wala, `:` = value). `while getopts ...; do case "$opt" in v) ...; f) ...$OPTARG...; esac; done`.
> `$OPTARG` = flag ki value. Order-safe. Flags wale tools ke liye; simple scripts mein `$1`/`$2`.

[↑ Back to top](#top)

---

<a id="s11-9"></a>
## 11.9 — Nuances aur caveats

- **`$1` ko `"$1"` (quotes) mein use karo:** agar argument mein space ho (`./s.sh "my file.txt"`),
  toh bina quotes `$1` toot jata (Ch 5.12). `"$1"` safe. Har argument-use pe quotes.

- **`$10` galat, `${10}` sahi:** double-digit arguments ke liye braces (11.2). `$10` ko shell `$1`
  + literal `0` samajhta. 10+ arguments ke liye `${10}`.

- **`read` automate scripts mein atka deta:** scheduled/cron script mein `read` — koi type karne wala
  nahi, script hamesha wait karti (atki). Automate mein arguments (`$1`) use karo, `read` nahi.
  (11.6.)

- **`-r` `read` mein hamesha:** bina `-r`, backslash kha jata. `read -r` (ya `-rp`, `-rsp`) — safe
  default. Bhoolna = weird backslash bugs.

- **`"$@"` vs `"$*"` (dohra raha):** `"$@"` = arguments alag (sahi, loop mein), `"$*"` = jud ke ek.
  Hamesha `"$@"` (11.3). `$*` bhoolo.

- **`getopts` sirf short flags (`-v`) — long (`--verbose`) nahi:** `getopts` built-in sirf single-dash
  short flags handle karta. Long flags (`--verbose`, Ch 3.5) ke liye manual parsing ya external tool
  chahiye. Simple tools ke liye short flags kaafi.

- **`exit 1` validation ke baad zaroori:** galat input pe sirf `echo "error"` kaafi nahi — `exit 1`
  bhi karo (Ch 5.6), warna script aage chalti rahegi galat/khaali input ke saath (crash/galat kaam).
  "Error message + exit" saath mein.

- **`getopts` ke baad `shift $((OPTIND-1))`:** flags parse hone ke baad, bache positional arguments
  (jaise filenames) ko access karne ko `shift $((OPTIND-1))` karte hain (`$OPTIND` = kitne flags
  process hue). Advanced, par jab flags + files dono ho tab zaroori.

[↑ Back to top](#top)

---

<a id="s11-10"></a>
## 11.10 — Real-life scenarios

**Scenario 1 — "Script ko file do, woh process kare."** `./convert.sh data.csv` — script `$1`
(data.csv) leti, validate karti (`[ ! -f "$1" ] && exit`, 11.5), phir process. Yeh sabse basic
argument-use — automate-friendly (cron se bhi chala sakte).

**Scenario 2 — "Usage message jab galat chalao."** User `./backup.sh` (bina file) chala de. Script:
`if [ $# -lt 1 ]; then echo "Usage: $0 <file> [destination]"; exit 1; fi` (11.5). User ko turant
sahi tareeka pata chal gaya — guess nahi karna. Har professional script yeh karti.

**Scenario 3 — "Dangerous action ki confirmation."** Script kuch delete karne wali hai. Pehle
poocho: `read -p "Sure? Yeh sab delete hoga (y/n): " ans; [ "$ans" != "y" ] && exit` (11.6/11.7).
User `y` na de toh ruk jao. Interactive confirmation — accidental disaster se bachao.

**Scenario 4 — "Password chupa ke lo."** Ek setup script ko DB password chahiye. `read -rsp "DB
Password: " db_pass` (11.7) — `-s` se screen pe dikhta nahi (koi peeche se na dekhe). Secrets ke
liye standard.

**Scenario 5 — "Flags wala proper CLI tool."** Aap ek deploy tool banate ho: `./deploy.sh -e prod
-v -f config.yaml` (environment, verbose, config-file). `getopts "e:vf:"` (11.8) se parse — `-e` aur
`-f` value lete (`:`), `-v` switch. Order koi bhi, getopts handle karta. Professional CLI banane ka
tareeka.

**Saar:** Chapter 11 ne scripts ko "input lene wala" banaya. Arguments (`$1`, `$@`, `$#`) automate-
friendly input; `read` (`-rsp`) interactive; `getopts` proper flags. Sabse practical: shuru mein
**input validate** karo (`$#` check + usage + `exit 1`), arguments/variables `"$@"`/`"$1"` quote
karo, aur `read` sirf genuine interactive kaam mein (automate mein arguments).

[↑ Back to top](#top)

---

> **Chapter 11 khatam.** Ab tak: arguments (`$1..$9`, `${10}`), `$@`/`$*`/`$#` (saare/ginti),
> `shift` (khiskana), input validation (`$#` + usage + `exit 1`), `read` (interactive), `read` flags
> (`-p` prompt, `-s` silent/password, `-r` raw), aur `getopts` (proper flag parsing, `$OPTARG`).
> **Agla chapter:** text processing — `grep` (regex/patterns), `sed` (find-replace), `awk`
> (columns/data) — production ka workhorse.

[↑ Back to top](#top)