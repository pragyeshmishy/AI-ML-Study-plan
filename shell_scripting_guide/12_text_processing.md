<a id="top"></a>
# Chapter 12 — Text Processing (grep, sed, awk — production ka workhorse)

Yeh chapter woh teen tools sikhata hai jo shell mein **text/data ke saath kaam** karne ke liye sabse
zyada use hote — **grep** (dhoondho/filter), **sed** (badlo/replace), **awk** (columns/data
process). Yeh "workhorse" (mehnati ghoda) tools hain — logs padhna, config badalna, CSV se data
nikaalna, sab inse hota. Production/data engineering mein yeh roz kaam aate.

Yeh theory-heavy chapter hai — har tool ka core, aur regex (pattern) ki basics kholega.

---

## Is chapter ka index

- [12.1 — Teen tools, teen kaam (grep/sed/awk ka farak)](#s12-1)
- [12.2 — `grep` — text dhoondhna/filter karna](#s12-2)
- [12.3 — `grep` ke zaroori flags (`-i -v -n -r -c -E`)](#s12-3)
- [12.4 — Regex basics (pattern likhna: `^ $ . * []`)](#s12-4)
- [12.5 — `sed` — find aur replace (`s/purana/naya/`)](#s12-5)
- [12.6 — `sed` ke aur kaam (lines delete, in-place edit)](#s12-6)
- [12.7 — `awk` — columns aur data process](#s12-7)
- [12.8 — `awk` se calculations aur conditions](#s12-8)
- [12.9 — Teeno ko pipe se jodna (real workflows)](#s12-9)
- [12.10 — Nuances aur caveats](#s12-10)
- [12.11 — Real-life scenarios](#s12-11)

---

<a id="s12-1"></a>
## 12.1 — Teen tools, teen kaam (grep/sed/awk ka farak)

Pehle badi tasveer — teen tools, kaunsa kis kaam ke liye. Yeh clear ho jaye toh kabhi confuse nahi
honge "kaunsa use karun".

- **`grep` = DHOONDHO/FILTER** — "jis line mein yeh pattern hai, woh dikhao" (baaki chhod do). Text
  mein se matching lines nikaalna. (Ch 6.9 mein chhua.)
- **`sed` = BADLO/REPLACE** — "yeh text mile toh use is se badal do". Stream mein find-and-replace,
  ya lines delete/insert. ("Stream EDitor" — behte data ko edit karta.)
- **`awk` = COLUMNS/DATA** — "har line ko columns mein todo, un columns pe kaam karo" (nikaalo, jodo,
  calculate). Structured data (CSV, tables, logs) ke liye. (Naam iske teen banane walon ke naamon
  se: Aho, Weinberger, Kernighan.)

**Ek line mein farak:**
- Kuch **dhoondhna** (kaun si lines)? → `grep`.
- Kuch **badalna** (replace/delete)? → `sed`.
- **Columns/fields** pe kaam (2nd column, sum)? → `awk`.

**Teeno line-by-line kaam karte:** yeh teeno input ko **ek-ek line** padhte hain aur har line pe apna
kaam. Isliye yeh pipe (Ch 6) ke saath perfect jode jaate — ek ka output doosre ko. Aur teeno **file
badalte nahi** (by default) — sirf output dete (jab tak aap `>` ya `sed -i` na karo).

**Overlap hai (par simple pe simple use karo):** `awk` itna powerful hai ki grep/sed ka kaam bhi kar
sakta, aur `sed` bhi thoda dhoondh sakta. Par best practice: **simple kaam simple tool se** — sirf
dhoondhna hai toh grep (awk se nahi), sirf replace toh sed. Right tool for the job.

> **Yaad rakhne wali baat:** `grep` = dhoondho/filter (matching lines), `sed` = badlo/replace
> (find-replace, delete), `awk` = columns/data (fields pe kaam, calculate). Teeno line-by-line, pipe
> ke saath perfect, file badalte nahi (default). Simple kaam = simple tool.

[↑ Back to top](#top)

---

<a id="s12-2"></a>
## 12.2 — `grep` — text dhoondhna/filter karna

**`grep`** text mein se woh lines dhoondhta hai jismein aapka diya pattern hai — baaki chhod deta.
(Naam ek purane editor command se: "**g**lobally search for a **r**egular **e**xpression and
**p**rint" — global regex print.)

**Basic:**
```
grep "error" logfile.txt
```
- `logfile.txt` ki woh saari lines dikhayega jismein "error" shabd hai. Baaki lines chhod di.
  Structure: `grep "pattern" file`.

**Pipe ke saath (Ch 6.9 wala — sabse common):**
```
cat logfile.txt | grep "error"
some_command | grep "error"
```
- Kisi bhi command ke output mein se "error" wali lines filter. `grep` pipe mein sabse zyada use
  hone wala filter — "aage aa rahe data mein se sirf yeh wali lines".

**Kai files mein dhoondhna:**
```
grep "TODO" *.py
```
- Saari `.py` files mein "TODO" dhoondho. Output mein har match ke aage file ka naam bhi (kis file
  mein mila). Codebase mein kuch dhoondhne ka aam tareeka.

**`grep` line-level pe kaam karta:** yeh **poori line** dikhata hai jismein match hua (sirf matched
shabd nahi, poori line). Agar aapko sirf matched hissa chahiye toh `-o` flag (12.3). By default —
jis line mein pattern, woh poori line.

> **Yaad rakhne wali baat:** `grep "pattern" file` = woh lines dikhao jismein pattern hai (baaki
> chhod do). Pipe mein: `... | grep "x"` (filter). `grep "x" *.py` (kai files). Poori matching line
> deta (Ch 6.9 ka core tool).

[↑ Back to top](#top)

---

<a id="s12-3"></a>
## 12.3 — `grep` ke zaroori flags (`-i -v -n -r -c -E`)

`grep` ke kuch flags itne kaam ke ki inhe zaroor jaan-na chahiye:

| Flag | Kis shabd se | Kaam |
|---|---|---|
| `-i` | **i**gnore-case | Chhota-bada akshar ignore ("Error"="error"="ERROR") |
| `-v` | in**v**ert | ULTA — jinme pattern NAHI hai woh dikhao |
| `-n` | **n**umber | Line number bhi dikhao (kaunsi line pe) |
| `-r` | **r**ecursive | Folder ke andar sab files mein dhoondho (Ch 3.8) |
| `-c` | **c**ount | Ginti dikhao (kitni lines match hui), lines nahi |
| `-l` | **l**ist | Sirf file-naam dikhao (kaun si files mein mila) |
| `-o` | **o**nly | Sirf matched hissa dikhao (poori line nahi) |
| `-E` | **E**xtended regex | Advanced patterns enable (12.4) |
| `-w` | **w**ord | Poora shabd match ("cat" mein "category" nahi) |

**Sabse kaam ke — misaalein:**

**`-i` (case ignore):**
```
grep -i "error" log.txt
```
- "Error", "ERROR", "error" — sab match. Logs mein case alag hota, isliye `-i` bahut use hota.

**`-v` (invert — jinme NAHI hai):**
```
grep -v "DEBUG" log.txt
```
- "DEBUG" wali lines *chhod* do, baaki dikhao. Noise hatane mein kaam aata ("DEBUG lines mat dikhao").

**`-rn` (recursive + line number — codebase search):**
```
grep -rn "TODO" .
```
- Current folder (aur andar sab, `-r`) ki har file mein "TODO" dhoondho, line-number ke saath (`-n`).
  "Poore project mein TODO kahan-kahan" — ek nazar mein. Yeh developer ka roz ka command.

**`-c` (ginti):**
```
grep -c "error" log.txt
```
- Kitni lines mein "error" — sirf number (lines nahi). `grep "error" log.txt | wc -l` ka short form.

**Flags jodna (Ch 3.6):** `grep -in`, `grep -rn`, `grep -ivc` — sab jud sakte. `grep -irn "error" .`
= case-ignore + recursive + line-number.

> **Yaad rakhne wali baat:** `-i` (case ignore), `-v` (invert/NAHI wali), `-n` (line number), `-r`
> (recursive/folder), `-c` (ginti), `-l` (file-naam), `-o` (sirf match), `-w` (poora shabd), `-E`
> (advanced regex). `grep -rn "x" .` = codebase search. Jud sakte (`-irn`).

[↑ Back to top](#top)

---

<a id="s12-4"></a>
## 12.4 — Regex basics (pattern likhna: `^ $ . * []`)

**Regex** (Regular Expression — "niyamit abhivyakti") ek **pattern** likhne ka tareeka hai — "aisa
text jo is shape ka ho". Sirf exact shabd nahi, balki "shuru mein yeh", "koi bhi digit", "yeh ya
woh". `grep` (aur `sed`/`awk`) patterns isse likhte. Yeh ek bada topic hai; yahan sirf sabse kaam ke.

**Core symbols (yeh yaad rakho):**

| Symbol | Matlab | Misaal |
|---|---|---|
| `^` | line ki **shuruaat** | `^error` = line jo "error" se shuru ho |
| `$` | line ka **ant** | `error$` = line jo "error" pe khatam ho |
| `.` | koi bhi **ek** character | `c.t` = cat, cot, cut (beech mein kuch bhi) |
| `*` | pichhla item **0 ya zyada** baar | `ab*` = a, ab, abb, abbb |
| `[...]` | in mein se **koi ek** | `[0-9]` = koi ek digit, `[abc]` = a ya b ya c |
| `[^...]` | in ke **alawa** koi | `[^0-9]` = jo digit nahi |
| `\` | agle symbol ka special-matlab hatao (escape) | `\.` = literal dot (koi-bhi nahi) |

**Misaalein (grep ke saath):**

**`^` — line ki shuruaat:**
```
grep "^error" log.txt
```
- Sirf woh lines jo "error" se **shuru** hoti hain (beech mein "error" wali nahi). `^` = anchor to
  start.

**`$` — line ka ant:**
```
grep "\.txt$" list.txt
```
- Lines jo ".txt" pe **khatam** hoti hain (`\.` = literal dot, `$` = end). File-list mein sirf .txt
  wali.

**`[0-9]` — digits:**
```
grep "[0-9][0-9][0-9]" file.txt
```
- Lines jismein 3 consecutive digits hain (jaise koi ID/number). `[0-9]` = ek digit, teen baar.

**`-E` (extended regex) — aur symbols:** basic grep mein kuch symbols (`+`, `?`, `|`, `()`) ko `\`
chahiye. `-E` (ya `egrep`) se yeh seedha:
```
grep -E "error|warning" log.txt      # "error" YA "warning" (| = ya)
grep -E "[0-9]+" file.txt            # ek ya zyada digits (+ = 1+)
```
- `-E` ke saath: `|` (ya), `+` (1 ya zyada), `?` (0 ya 1), `()` (group). Modern regex. **Aam taur pe
  `-E` use karo** patterns ke liye — zyada natural.

**Abhi itna kaafi:** regex bahut gehra hai, par yeh 7-8 symbols 90% kaam kar dete. Zaroorat pade toh
`man grep` ya online regex reference. Shuruaat mein `^`, `$`, `.`, `*`, `[0-9]`, aur `-E` ka `|`/`+`
yaad rakho.

> **Yaad rakhne wali baat:** Regex = text pattern. `^` (shuruaat), `$` (ant), `.` (koi ek char), `*`
> (0+ baar), `[0-9]` (ek digit), `[^..]` (alawa), `\.` (literal dot). `-E` se `|` (ya), `+` (1+),
> `()`. Aam taur `grep -E` use karo. Yeh 90% kaam.

[↑ Back to top](#top)

---

<a id="s12-5"></a>
## 12.5 — `sed` — find aur replace (`s/purana/naya/`)

**`sed`** = **s**tream **ed**itor — behte text (stream) ko edit karta. Sabse common kaam: **find aur
replace** (kuch dhoondho, kisi aur se badlo).

**Basic substitute — `s/purana/naya/`:**
```
sed 's/error/ERROR/' log.txt
```
- **`s/error/ERROR/`** — `s` = **s**ubstitute (badlo). Format: `s/dhoondho/badlo-se/`. Yeh har line
  mein pehla "error" dhoondh ke "ERROR" se badal deta. `/` = separator (teen hisse: s, purana, naya).
- **Note:** yeh output pe badla dikhata hai — **original file badalti nahi** (12.1 wala — sed default
  file nahi chhedta). File badalne ko `-i` (12.6).

**`g` — har match (sirf pehla nahi):**
```
sed 's/error/ERROR/g' log.txt
```
- **`g`** = **g**lobal — line mein har "error" badlo (sirf pehla nahi). Bina `g`, ek line mein sirf
  pehla "error" badalta. Aam taur pe `g` chahiye (sab badlo).

**Pipe ke saath:**
```
echo "hello world" | sed 's/world/duniya/'
```
- Output: `hello duniya`. `sed` ne "world" ko "duniya" se badla. Pipe mein text transform karne ka
  common tareeka.

**Alag separator (jab text mein `/` ho):**
```
sed 's|/old/path|/new/path|' file.txt
```
- Agar dhoondhne/badalne mein `/` ho (jaise file paths), toh `/` separator confuse karega. Aap koi
  aur separator use kar sakte — `s|...|...|` (pipe) ya `s#...#...#`. `sed` pehle character ko
  separator maan leta. Paths badalne mein bahut kaam ka.

> **Yaad rakhne wali baat:** `sed 's/purana/naya/'` = find-replace (`s`=substitute, `/`=separator).
> `g` = har match (bina g sirf pehla). Output pe badla, file nahi (default). Path mein `/` ho toh
> `s|..|..|` (alag separator). Pipe mein text transform.

[↑ Back to top](#top)

---

<a id="s12-6"></a>
## 12.6 — `sed` ke aur kaam (lines delete, in-place edit)

`sed` sirf replace nahi karta — lines delete/print bhi, aur file ko directly badal bhi sakta.

**`-i` — file ko DIRECTLY badlo (in-place):**
```
sed -i 's/old/new/g' config.txt
```
- **`-i`** = **i**n-place — output screen pe nahi, **file khud** badal do. Ab `config.txt` mein
  actual change ho gaya (12.5 wala default sirf dikhata tha).
- **KHATRA:** `-i` file ko permanent badal deta, bina backup. Galat pattern = file bigad gayi, undo
  nahi (Ch 4.5 jaisa). **Safety — pehle bina `-i` chala ke dekho** (output theek hai?), phir `-i`.
- **Mac vs Linux farak (zaroori):** Mac (BSD sed) pe `-i` ko backup-extension chahiye: `sed -i ''
  's/.../.../'` (khaali `''`). Linux (GNU sed) pe seedha `sed -i 's/.../.../'`. Yeh "mere Mac pe alag,
  server pe alag" wala classic case (Ch 1.7). Backup ke saath safe: `sed -i.bak 's/.../.../'` (dono
  pe chalta, `.bak` backup banata).

**Line delete — `d`:**
```
sed '/DEBUG/d' log.txt
```
- **`/pattern/d`** = jis line mein "DEBUG" hai, use **d**elete (output se hatao). Noise hatane mein
  kaam aata. (Yeh `grep -v "DEBUG"` jaisa — dono se DEBUG lines gayab.)

**Specific line number delete:**
```
sed '1d' file.txt          # pehli line hatao (jaise CSV header)
sed '1,3d' file.txt        # line 1 se 3 tak hatao
```
- `1d` = line 1 delete. `1,3d` = line 1-3. CSV ka header hatane mein (`1d`) bahut common.

**Specific line print — `-n` + `p`:**
```
sed -n '5,10p' file.txt
```
- `-n` (chup raho) + `5,10p` (line 5-10 **p**rint) = sirf lines 5 se 10 dikhao. Badi file ka ek hissa
  dekhne ko (jaise `head`/`tail` ka beech-wala version).

> **Yaad rakhne wali baat:** `sed -i` = file khud badlo (KHATRA — pehle bina -i test karo; Mac pe
> `-i ''` ya safe `-i.bak`). `/pattern/d` = matching line delete, `1d` = pehli line (CSV header),
> `sed -n '5,10p'` = sirf woh lines dikhao.

[↑ Back to top](#top)

---

<a id="s12-7"></a>
## 12.7 — `awk` — columns aur data process

**`awk`** structured data (columns/fields wala — CSV, tables, logs) ke liye bana hai. Yeh har line ko
apne aap **columns mein tod** deta, aur aap un columns pe kaam karte ho. Data engineering mein bahut
kaam ka.

**Core idea — automatic columns (`$1`, `$2`...):** awk har line ko **whitespace (space/tab) pe tod**
ke columns bana leta:
- **`$1`** = pehla column, **`$2`** = doosra, ... **`$0`** = poori line.
- (Note: yeh awk ke *apne* `$1` hain — shell ke `$1` (Ch 11) se alag. awk ki apni bhasha hai.)

**Ek column nikaalna:**
```
awk '{print $2}' data.txt
```
- **`{print $2}`** = har line ka doosra column chhaapo. `awk '{...}'` — brackets mein "har line pe
  kya karna". Yahan sirf column 2. Log/table se ek column nikaalne ka aasaan tareeka.

**Kai columns:**
```
awk '{print $1, $3}' data.txt
```
- Column 1 aur 3 (comma se — output mein space aa jata). Beech wale (2) chhod diye. Columns
  reorder/select karne mein handy.

**Custom separator — `-F` (CSV ke liye):**
```
awk -F',' '{print $2}' data.csv
```
- **`-F','`** = **F**ield separator comma hai (default whitespace, par CSV comma-separated). Ab awk
  line ko comma pe todta — `$2` = doosra comma-field. CSV se column nikaalne ka standard (Ch 6.9 ka
  `cut` se zyada powerful).

**awk vs cut (kab kaunsa):** `cut` (Ch 6.9) bhi columns nikalta — simple cases mein cut kaafi (`cut
-d',' -f2`). Par awk zyada powerful — calculations, conditions, reorder, multiple fields ek saath.
Simple single-column → cut; kuch bhi complex (math, filter, format) → awk.

> **Yaad rakhne wali baat:** `awk '{print $2}'` = har line ka column 2 (awk khud whitespace pe todta;
> `$1 $2...` columns, `$0` poori line). `-F','` = comma-separator (CSV). Columns select/reorder.
> Simple = cut, complex = awk.

[↑ Back to top](#top)

---

<a id="s12-8"></a>
## 12.8 — `awk` se calculations aur conditions

`awk` sirf columns nahi nikalta — un pe **hisaab** (sum, average) aur **conditions** (filter) bhi
karta. Yehi use grep/sed se alag banata.

**Condition — sirf kuch lines (jaise filter):**
```
awk '$3 > 100' sales.txt
```
- `$3 > 100` = "jis line ka column 3, 100 se bada hai, woh dikhao". awk ne har line ka 3rd column
  check kiya, sirf matching dikhayi. Yeh grep jaisa filter par **column-value pe** (grep sirf text
  match karta, awk number-compare kar sakta).

**Condition + specific columns:**
```
awk -F',' '$3 > 100 {print $1, $3}' sales.csv
```
- "Jis row ka column 3 > 100, uska column 1 aur 3 dikhao". Filter + select ek saath. Data analysis
  ka common pattern.

**Sum/total nikaalna (calculation):**
```
awk '{sum += $2} END {print sum}' numbers.txt
```
- **`{sum += $2}`** = har line pe, column 2 ko `sum` mein jodo (running total). **`END {print sum}`**
  = saari lines ke baad (`END` = "sab khatam hone pe"), final sum chhaapo. Yeh "ek column ka total"
  ka standard tareeka. (awk apne variables khud handle karta, `$` bina.)

**Average:**
```
awk '{sum += $2; count++} END {print sum/count}' numbers.txt
```
- Sum + ginti (`count++`), ant mein `sum/count` = average. awk mein poora chhota calculation ho jata.

**`BEGIN` aur `END` (special blocks):**
- **`BEGIN {...}`** = lines process karne se **pehle** (jaise header chhaapna, variables set karna).
- **`END {...}`** = saari lines ke **baad** (jaise total, summary).
- Beech wala `{...}` = **har line** pe. Toh awk ka poora shape: `BEGIN{setup} {har-line} END{summary}`.

> **Yaad rakhne wali baat:** awk conditions: `$3 > 100` (column-value pe filter). Calculation:
> `{sum += $2} END {print sum}` (total). `BEGIN{}` (pehle), `{}` (har line), `END{}` (baad mein).
> awk = grep+cut+calculator ek mein — number/column pe kaam.

[↑ Back to top](#top)

---

<a id="s12-9"></a>
## 12.9 — Teeno ko pipe se jodna (real workflows)

Asli taakat tab aati jab grep/sed/awk ko pipe (Ch 6) se jodo — har ek apna hissa kare. Yeh Ch 6.10
(Unix philosophy) ka data-processing version hai.

**Workflow 1 — log se error IPs ki ginti:**
```
grep "ERROR" access.log | awk '{print $1}' | sort | uniq -c | sort -rn
```
- `grep "ERROR"` (sirf error lines) → `awk '{print $1}'` (har line ka IP nikaalo) → `sort` (saath
  laao) → `uniq -c` (gino) → `sort -rn` (zyada upar). "Kaunse IP se sabse zyada errors" — Ch 6.10
  jaisa par grep+awk ke saath.

**Workflow 2 — CSV se ek column, clean karke, unique:**
```
awk -F',' '{print $3}' data.csv | grep -v "^$" | sort | uniq
```
- `awk` (column 3 nikaalo) → `grep -v "^$"` (khaali lines hatao — `^$` = shuru-turant-ant = khaali
  line, `-v` = ULTA) → `sort | uniq` (unique values). Column ki safaai + unique.

**Workflow 3 — replace + filter:**
```
cat config.txt | sed 's/localhost/prod-server/g' | grep -v "^#"
```
- `sed` (localhost → prod-server sab jagah) → `grep -v "^#"` (comment lines `#` se shuru wali hatao).
  Config ko transform + comments hatao. Deploy scripts mein aisa common.

**Har tool apna kaam (yeh soch):** grep filter kare, awk column nikaale/calculate kare, sed badle,
sort/uniq organize kare. Kisi ek tool se sab nahi — jodo. Jab bhi ek text-problem dikhe, socho
"kaunse chhote steps? har step kaunsa tool?" (Ch 6.2 philosophy).

> **Yaad rakhne wali baat:** grep/sed/awk ko pipe se jodo — har apna hissa. `grep` (filter) → `awk`
> (column/calc) → `sort`/`uniq` (organize) → `sed` (transform). `grep -v "^$"` (khaali hatao),
> `grep -v "^#"` (comments hatao). Text-problem = chhote steps, har step ek tool.

[↑ Back to top](#top)

---

<a id="s12-10"></a>
## 12.10 — Nuances aur caveats

- **`sed -i` Mac vs Linux (dohra raha — bahut common trap):** Linux `sed -i 's/.../.../'`; Mac `sed
  -i '' 's/.../.../'` (khaali `''` chahiye). Safe dono pe: `sed -i.bak 's/.../.../'` (backup banata).
  Yeh #1 "mere Mac pe alag" issue text-processing mein (Ch 1.7).

- **Regex special characters escape karna:** `.`, `*`, `[`, `$` regex mein special hain (12.4). Agar
  literal chahiye (jaise actual dot), `\` lagao (`\.`). `grep "3.14"` → `.` koi-bhi-char match karega
  (3x14 bhi); `grep "3\.14"` → literal 3.14. Bhoolna = unexpected matches.

- **Quotes pattern ke around zaroori:** `grep error file` (bina quotes) aksar chalta par risky —
  agar pattern mein space/special ho toh toota. Hamesha `grep "pattern"` (quotes, Ch 5.10).

- **`grep` khaali output = koi match nahi (error nahi):** agar grep ko kuch na mile, woh khaali output
  deta aur exit code 1 (Ch 5.6). Yeh "fail" nahi — bs "match nahi mila". Scripts mein `if grep -q
  "x" file` (`-q` = quiet, sirf exit code) se check karo mila ya nahi.

- **awk ke `$1` vs shell ke `$1`:** awk ke andar `$1` = awk ki column (12.7), shell ke `$1` = script
  argument (Ch 11). Alag duniyaein! awk single-quotes mein hota (`awk '{print $1}'`) taaki shell uske
  `$1` ko na chhede. Double-quotes mein daloge toh shell ghus jayega — bug.

- **`cut` simple, `awk` powerful — over-engineer mat karo:** sirf ek column comma-se nikaalna hai toh
  `cut -d',' -f2` kaafi (Ch 6.9) — awk ki zaroorat nahi. awk tab jab calculation/condition/multiple
  cheezein. Right tool.

- **Bade files pe `sed`/`awk` streaming (memory-safe):** yeh line-by-line padhte (12.1), poori file
  memory mein nahi laate — isliye GB ki files pe bhi chalte (Python mein poora file load karne se
  ulta). Yeh production data-processing mein bada plus.

[↑ Back to top](#top)

---

<a id="s12-11"></a>
## 12.11 — Real-life scenarios

**Scenario 1 — "Log mein aaj ke errors dhoondho."** `grep -i "error" app.log | grep "2026-06-30"` —
error lines, phir aaj ki date wali (do grep pipe). Ya `grep -in "error" app.log` (line-number ke
saath) taaki file mein jaake dekh sako. Debugging ka roz ka pehla step.

**Scenario 2 — "Config mein server address badalna (sab jagah)."** Dev se prod pe jaate waqt:
`sed -i.bak 's/localhost:5432/prod-db:5432/g' config.yaml` (12.6). Sab jagah badla, `.bak` backup
bhi bana (safe). `-i.bak` Mac+Linux dono pe chalta. Deploy mein common.

**Scenario 3 — "CSV se total sales nikaalo."** `sales.csv` mein amount 4th column. `awk -F','
'{sum += $4} END {print "Total:", sum}' sales.csv` (12.8). awk ne poori file ka 4th column jod ke
total diya — ek line mein. Data analysis ka aam kaam.

**Scenario 4 — "Codebase mein purana function-naam dhoondho."** Refactor se pehle: `grep -rn
"oldFunctionName" .` (12.3) — poore project mein kahan-kahan use hua, file+line ke saath. Badalne se
pehle scope samajhne ko. Har developer roz.

**Scenario 5 — "Log se top 10 sabse zyada aane wale errors."** `grep "ERROR" app.log | sed
's/[0-9]*//g' | sort | uniq -c | sort -rn | head -10` — errors → numbers hatao (`sed`, taaki same
error jinme sirf ID alag ho woh group ho) → gino → top 10. Teeno tools + pipe (12.9). Production
incident analysis.

**Saar:** Chapter 12 ke teen tools text/data ke saath har kaam karte — `grep` (dhoondho/filter,
`-irn`), `sed` (badlo/replace `s///g`, `-i` se file), `awk` (columns `$1 $2`, calculations `sum+=`).
Regex (`^ $ . [0-9]`) patterns deta. Sabse practical: pipe se jodo (har tool ek hissa), `sed -i`
backup ke saath (`-i.bak`), aur simple pe simple tool (cut vs awk). Yeh production/data-engineering
ka roz ka workhorse hai.

[↑ Back to top](#top)

---

> **Chapter 12 khatam.** Ab tak: teen tools ka farak; `grep` (filter, `-i -v -n -r -c -E`, regex
> `^$.*[]`); `sed` (`s/old/new/g`, `-i` in-place + Mac/Linux farak, `/pattern/d` delete); `awk`
> (columns `$1 $2`, `-F','`, conditions `$3>100`, calculations `sum+=`, `BEGIN`/`END`); teeno pipe
> se jodna. **Agla chapter:** processes aur jobs — `ps`, `top`, `kill`, background (`&`), `nohup`,
> `jobs`/`fg`/`bg`.

[↑ Back to top](#top)
