<a id="top"></a>
# Chapter 06 — Pipes, Redirects, aur Unix Philosophy

Yeh chapter shell ki sabse **taakatvar** cheez sikhata hai — chhote-chhote commands ko aapas mein
**jodna** taaki woh milke bada kaam karein. Yehi Unix ki asli soch ("philosophy") hai, aur yehi
shell ko itna powerful banati hai.

Isko samajhne ke liye pehle ek cheez jaan-ni zaroori hai: har command ka input kahan se aata hai aur
output kahan jata hai. Woh "streams" (dhaaraayein) kehlate hain — wahi se shuru karte hain.

Yeh theory-heavy chapter hai, har symbol (`|`, `>`, `>>`, `<`, `2>`) ka literal matlab kholega.

---

## Is chapter ka index

- [6.1 — Teen streams: stdin, stdout, stderr (input, output, error)](#s6-1)
- [6.2 — Unix philosophy: chhote tools jo ek kaam achhe se karein](#s6-2)
- [6.3 — Pipe `|` — ek command ka output, doosre ka input](#s6-3)
- [6.4 — Redirect output: `>` (naya) aur `>>` (jodo)](#s6-4)
- [6.5 — Redirect input: `<` (file se input do)](#s6-5)
- [6.6 — Error stream alag: `2>`, aur `2>&1` (error ko output ke saath)](#s6-6)
- [6.7 — `/dev/null` — "kachra-peti" (output ko phenko)](#s6-7)
- [6.8 — `tee` — output ko screen AUR file dono mein](#s6-8)
- [6.9 — Common pipe-building blocks: `grep`, `sort`, `uniq`, `cut`, `wc`](#s6-9)
- [6.10 — Poora pipeline banana (ek real misaal step-by-step)](#s6-10)
- [6.11 — Nuances aur caveats](#s6-11)
- [6.12 — Real-life scenarios](#s6-12)

---

<a id="s6-1"></a>
## 6.1 — Teen streams: stdin, stdout, stderr (input, output, error)

Har command ke teen "raaste" (streams — data ke aane-jaane ke channels) hote hain. Inhe samajhna
poore chapter ki neev hai.

- **stdin** (standard input) — command ka **input** kahan se aata hai. Default: keyboard (aap jo
  type karo). "std-in" = standard input.
- **stdout** (standard output) — command ka **normal output** kahan jata hai. Default: screen
  (terminal). "std-out" = standard output. Jab `ls` files dikhata, woh stdout pe.
- **stderr** (standard error) — command ke **error messages** kahan jate hain. Default: screen bhi
  (par yeh ek *alag* channel hai). "std-err" = standard error.

**Yeh alag kyun (stdout aur stderr dono screen pe dikhte, phir farak kya)?** Kyunki yeh do **alag
channels** hain — normal output ek taraf, errors doosri taraf. Dikhte dono screen pe hain, par aap
inhe **alag-alag jagah bhej sakte ho** (jaise output file mein, errors screen pe). Yeh alag-alag
handle karna production mein bahut kaam aata (6.6).

**Numbers bhi hote hain in streams ke (yeh yaad rakho, 6.6 mein kaam aayega):**
- **stdin = 0**, **stdout = 1**, **stderr = 2**.
- Isiliye error redirect karne ko `2>` likhte hain — woh `2` matlab stderr (6.6). Yeh number samajhe
  bina `2>&1` jaise cheezein confuse karti hain.

**Analogy:** socho ek machine (command). Uske paas ek input-pipe (stdin — jahan se kachcha maal
aata), ek output-pipe (stdout — jahan se bani cheez nikalti), aur ek "error-alarm" pipe (stderr —
jahan se problem ki khabar nikalti). Teeno alag pipes. Aap har pipe ko alag jagah jod sakte ho —
yehi redirects aur pipes karte hain.

> **Yaad rakhne wali baat:** Har command ke 3 streams: stdin (0, input — default keyboard), stdout
> (1, normal output — default screen), stderr (2, errors — default screen par alag channel). Inhe
> alag-alag jagah bhej sakte ho — yeh redirects/pipes ki neev.

[↑ Back to top](#top)

---

<a id="s6-2"></a>
## 6.2 — Unix philosophy: chhote tools jo ek kaam achhe se karein

Shell itna powerful kyun hai? Iske peeche ek soch hai jise **Unix philosophy** kehte hain. Ek line
mein: **"Har tool ek hi kaam kare, par woh kaam bahut achhe se kare — aur tools ko aapas mein jodo
taaki bade kaam ho jaayein."**

Matlab: ek vishaal (giant) command jo sab kuch kare — woh Unix ka tareeka nahi. Iski jagah, bahut
saare chhote commands hain, har ek ek chhota kaam mein master:
- `grep` — sirf text dhoondhta (filter karta).
- `sort` — sirf lines sort karta.
- `wc` — sirf ginti karta.
- `cut` — sirf columns nikalta.

Akele yeh chhote lagte hain. Par jab aap inhe **pipe (`|`) se jodte ho**, toh yeh milke ek bahut
powerful kaam kar dete hain — jaise Lego blocks jodke bada model banana.

**Misaal (samajhne ko, poora 6.10 mein):** "log file mein sabse zyada aane wale 5 errors kaunse
hain?" — koi ek command nahi hai iske liye. Par aap jodte ho: `grep` (errors nikalo) → `sort`
(lagao) → `uniq -c` (gino) → `sort` (ginti se) → `head` (top 5). Paanch chhote tools, ek powerful
jawab.

**Yeh soch kyun matter karti:** jab aap ek nayi problem dekhein, Unix-tareeka hai "isko chhote steps
mein todo, har step ke liye ek chhota tool, phir pipe se jodo". Ek "sab kuch karne wala" tool
dhoondhne ke bajaye. Yeh soch aapko shell mein bahut productive banati hai.

> **Yaad rakhne wali baat:** Unix philosophy = chhote tools, har ek ek kaam mein master, pipe se
> jodke bade kaam. Ek vishaal tool nahi — chhote tools ka combination. Problem ko steps mein todo,
> har step ek tool, pipe se jodo.

[↑ Back to top](#top)

---

<a id="s6-3"></a>
## 6.3 — Pipe `|` — ek command ka output, doosre ka input

**Pipe** ka symbol hai `|` (keyboard pe aksar `\` ke saath, Shift daba ke). Iska kaam: **pehle
command ka output (stdout) seedha doosre command ke input (stdin) mein daal do** — bina beech mein
file banaye.

**Structure: `command1 | command2`**

```
ls | wc -l
```
- **Padho:** `ls` (files list karo) `|` (uska output aage do) `wc -l` (lines gino).
- **Kya hua:** `ls` ne files ki list banayi (output), pipe ne woh list `wc -l` ko di (input), `wc
  -l` ne lines gin di. **Natija:** is folder mein kitni files/folders hain — ek number.
- Yeh Ch 4.10 wala teaser tha — ab poora. `ls` ki list `wc -l` ke input mein "beh" gayi (isliye
  "pipe" — paani ki tarah ek se doosre mein).

**Kaise samjhein — `|` = "aage bhej do":** `|` ke baayen wale command ka jo output screen pe aata,
woh screen pe na jaake, `|` ke daayen wale command ke input mein chala jata. Jaise ek pipe se paani
ek tank se doosre mein.

**Kai pipes ek saath (chain):**
```
cat log.txt | grep "error" | wc -l
```
- Padho: `cat log.txt` (poori file ka content) → `grep "error"` (usmein se sirf "error" wali lines
  chuno) → `wc -l` (un lines ko gino). **Natija:** file mein kitni "error" lines hain.
- Teen tools ek chain mein — har ek pichhle ka output leta, apna kaam karta, aage deta. Yeh 6.2 wali
  philosophy live hai.

**Zaroori samajh — pipe file nahi banata:** data beech mein kahin save nahi hota, seedha ek command
se doosre mein "behta" hai (memory mein). Yeh fast hai aur koi temp file nahi bachti. (Agar output
save karna ho toh redirect `>` chahiye — 6.4.)

> **Yaad rakhne wali baat:** `|` (pipe) = pehle command ka output → doosre ka input (bina file
> banaye). `ls | wc -l` (files gino), `cat f | grep x | wc -l` (chain). Data ek se doosre mein
> "behta". Unix philosophy ka asli auzaar.

[↑ Back to top](#top)

---

<a id="s6-4"></a>
## 6.4 — Redirect output: `>` (naya) aur `>>` (jodo)

Pipe output ko *doosre command* mein bhejta. **Redirect** output ko ek **file** mein bhejta hai
(screen pe dikhane ke bajaye file mein save karo).

**`>` — output ko file mein daalo (file ko OVERWRITE karo):**
```
ls > filelist.txt
```
- **`>`** = "output is file mein daalo". `ls` ka output screen pe na jaake `filelist.txt` mein chala
  gaya. Ab woh file mein files ki list save hai.
- **KHATRA — `>` file ko OVERWRITE karta:** agar `filelist.txt` pehle se thi (usmein kuch tha), toh
  `>` uska **poora purana content mita ke** naya likhta hai. Bina warning. Yeh `>` ka sabse bada
  khatra — galti se zaroori file pe `>` = data gaya.

**`>>` — output ko file ke AAKHIR mein JODO (append):**
```
echo "naya line" >> filelist.txt
```
- **`>>`** = "output ko file ke aakhir mein jodo (append karo)". Purana content **rehta hai**, naya
  uske neeche jud jata. Kuch mitta nahi.
- **`>` vs `>>` (ek line mein):** `>` = mita ke naya likho (overwrite). `>>` = purane ke aage jodo
  (append). Do `>>` = "jodo", ek `>` = "replace".

**Kab kaunsa:**
- Fresh file/report banani hai → `>` (par dhyan, purani mit jayegi).
- Log/record mein aur lines jodni hain (purani rakhni hain) → `>>`. Logs hamesha `>>` se bante
  (warna har baar purana mit jaye).

**Misaal — dono ka farak:**
```
echo "line1" > file.txt     # file.txt mein sirf: line1
echo "line2" > file.txt     # file.txt mein sirf: line2 (line1 MIT gaya! overwrite)
echo "line3" >> file.txt    # file.txt mein: line2, line3 (line3 juda)
```

> **Yaad rakhne wali baat:** `>` = output file mein daalo par purana content MITA ke (overwrite —
> khatra!). `>>` = output file ke aakhir mein JODo (append, purana rehta). Report → `>`, logs →
> `>>`. Galti se `>` zaroori file pe = data gaya.

[↑ Back to top](#top)

---

<a id="s6-5"></a>
## 6.5 — Redirect input: `<` (file se input do)

Jaise `>` output ko file mein bhejta, waise `<` **input ko file se leta** — matlab command ka
stdin keyboard se na aake, ek file se aaye.

```
sort < names.txt
```
- **`<`** = "input is file se lo". `sort` ko input `names.txt` se mila (keyboard se nahi). `sort` ne
  us file ki lines sort karke dikha di.
- **Note:** zyadatr commands file ka naam seedha argument mein bhi le lete hain (`sort names.txt` —
  same result). Toh `<` km use hota. Par kuch commands sirf stdin se padhte (argument nahi lete) —
  wahan `<` zaroori.

**Direction yaad rakhna (tir/arrow ki tarah):** `>` output ko *bahar* file mein (command → file).
`<` input ko *andar* file se (file → command). Arrow jis taraf point kare, data us taraf jata.

> **Yaad rakhne wali baat:** `<` = command ko input file se do (keyboard ke bajaye). `command <
> file`. `>` output bahar bhejta (command→file), `<` input andar laata (file→command). Arrow ki
> disha = data ki disha.

[↑ Back to top](#top)

---

<a id="s6-6"></a>
## 6.6 — Error stream alag: `2>`, aur `2>&1` (error ko output ke saath)

Yaad karo 6.1 — stdout (normal output, number **1**) aur stderr (errors, number **2**) alag channels
hain. Ab woh number kaam aayega. `>` akela sirf stdout (1) ko redirect karta; error (2) phir bhi
screen pe rehta.

**Problem dekho:**
```
ls notes.txt nahi_hai.txt > out.txt
```
- Agar `notes.txt` hai par `nahi_hai.txt` nahi — toh `ls` ka normal output (jo mila) `out.txt` mein
  chala jayega (`>` = stdout), **par error** ("nahi_hai.txt not found") **phir bhi screen pe** dikhega.
  Kyunki `>` sirf stdout (1) bhejta, stderr (2) ko nahi.

**`2>` — sirf error ko file mein bhejo:**
```
ls nahi_hai.txt 2> errors.txt
```
- **`2>`** = "stream number 2 (stderr) ko file mein bhejo". Ab error `errors.txt` mein gaya, screen
  saaf. `2` woh stderr ka number hai (6.1). (`>` akela `1>` ka short hai — stdout.)

**`2>&1` — error ko bhi wahin bhejo jahan output ja raha (sabse confusing, dhyan se):**
```
./script.sh > sab.txt 2>&1
```
- Iska matlab: "output (1) ko `sab.txt` mein daalo, **aur error (2) ko bhi wahin bhejo jahan 1 ja
  raha** (`2>&1`)". Natija: normal output AUR errors dono `sab.txt` mein.
- **`2>&1` ko tod ke:** `2` (stderr) `>` (redirect) `&1` ("stream 1 jahan ja raha, wahin"). Woh `&1`
  ka matlab "1 wali jagah" — file `1.txt` nahi (isliye `&`, taaki `1` ko file-naam na samjhe).
- **Order matter karta:** `> sab.txt 2>&1` sahi (pehle 1 ki jagah set, phir 2 ko wahin bhejo). Ulta
  `2>&1 > sab.txt` galat kaam karega (jab 2 ko bheja tab 1 abhi screen pe tha).

**`&>` — dono ek saath (short, aasaan):**
```
./script.sh &> sab.txt
```
- **`&>`** = "stdout AUR stderr dono is file mein" — `> sab.txt 2>&1` ka chhota roop. Yaad rakhne
  mein aasaan. (Bash/zsh mein chalta; purane `sh` mein `2>&1` wala use karo — portable.)

**Kyun zaroori:** production scripts mein aap sab (output + errors) ek log file mein chahte ho taaki
baad mein debug kar sako. `command &> logfile` ya `command > logfile 2>&1` — yeh standard hai.

> **Yaad rakhne wali baat:** `>` sirf stdout (1) bhejta; error (2) ke liye `2>`. `2>&1` = "error ko
> bhi wahin bhejo jahan output ja raha" (`&1` = "1 wali jagah"). `&>` = dono ek saath (short). Logs
> mein sab chahiye toh `&> logfile`.

[↑ Back to top](#top)

---

<a id="s6-7"></a>
## 6.7 — `/dev/null` — "kachra-peti" (output ko phenko)

**`/dev/null`** ek special "file" hai (asal mein device) jo ek **kachra-peti (black hole)** ki tarah
kaam karti hai — jo kuch bhi ismein bhejo, woh gayab ho jata, kahin save nahi hota. "null" = kuch
nahi.

**Kab chahiye:** kabhi aapko kisi command ka output **nahi chahiye** — use dekhna nahi, save nahi
karna, bs chup karana hai. Use `/dev/null` mein bhej do.

```
./script.sh > /dev/null
```
- Script ka normal output `/dev/null` mein gaya = gayab = screen saaf. (Sirf errors dikhenge, kyunki
  woh stderr pe hain.)

**Sab kuch chup (output + errors dono phenko):**
```
./script.sh > /dev/null 2>&1
```
- Output `/dev/null` mein, aur errors bhi wahin (`2>&1`, 6.6). Ab kuch nahi dikhega — poori tarah
  chup. Yeh tab jab aapko sirf command *chalani* hai, uska koi output/error nahi chahiye (jaise
  background checks, cron jobs).

**Ek common use — sirf yeh dekhna ki command safal hui ya nahi (output ki parwah nahi):**
```
command > /dev/null 2>&1
echo $?
```
- Output phenk diya, par `$?` (6.6 wala exit code) se pata chal jayega safal thi ya nahi. "Kaam hua
  ki nahi, bs yeh batao, output mat dikhao."

> **Yaad rakhne wali baat:** `/dev/null` = kachra-peti (jo bhejo gayab). `> /dev/null` = output
> phenko (chup karao). `> /dev/null 2>&1` = output + errors dono phenko (poori chup). Jab output
> nahi chahiye, sirf command chalani ho.

[↑ Back to top](#top)

---

<a id="s6-8"></a>
## 6.8 — `tee` — output ko screen AUR file dono mein

Kabhi aap output ko **dekhna bhi** chahte ho (screen pe) **aur save bhi** karna chahte ho (file
mein) — dono ek saath. `>` sirf file mein bhejta (screen pe nahi dikhta). Yahan **`tee`** aata hai.

**Naam ka matlab:** plumbing mein ek "T"-shape ka joint hota jo ek paani ki dhaara ko do mein baant
deta. `tee` wahi karta — output ko do taraf: screen pe bhi, file mein bhi.

```
ls | tee filelist.txt
```
- `ls` ka output `tee` ko pipe hua. `tee` ne use **screen pe bhi dikhaya AUR** `filelist.txt` mein
  **bhi save kiya**. Dono ek saath.

**Append version — `tee -a`:**
```
./script.sh | tee -a log.txt
```
- **`-a`** = **a**ppend (jodo, `>>` jaisa). Screen pe dikhao, aur file ke *aakhir mein jodo* (purana
  na mite). Bina `-a` ke `tee` file ko overwrite karta (`>` jaisa).

**Kab kaam ka:** jab ek lamba command chal raha ho aur aap uska output live dekhna chahte ho *aur*
baad ke liye file mein bhi rakhna chahte ho. Jaise ek build/install command — screen pe progress
dekho, aur `tee` se log bhi ban jaye taaki fail ho toh baad mein padh sako.

> **Yaad rakhne wali baat:** `tee file` = output screen pe bhi dikhao AUR file mein bhi save karo
> (T-joint jaisa, dhaara do taraf). `tee -a` = file ke aakhir mein jodo (append). `>` sirf file
> mein; `tee` dono jagah.

[↑ Back to top](#top)

---

<a id="s6-9"></a>
## 6.9 — Common pipe-building blocks: `grep`, `sort`, `uniq`, `cut`, `wc`

Yeh woh chhote tools hain jo pipe (`|`) ke saath sabse zyada jode jaate hain. Har ek ek chhota kaam
karta (6.2 wali philosophy) — inhe jaan lo, phir jodna aasaan (6.10). (Inka poora detail Chapter 12
mein; yahan pipe ke context mein basic.)

**`grep` — text filter (sirf matching lines rakho):**
```
grep "error" log.txt
```
- Sirf woh lines dikhata jismein "error" hai. Baaki chhod deta. Pipe mein sabse common filter:
  `... | grep "error"` = "aage aa rahe data mein se sirf error wali lines".
- Useful flags: `-i` (chhota-bada akshar ignore), `-v` (ULTA — jinme NAHI hai woh dikhao), `-c`
  (ginti), `-n` (line number). (Ch 12 mein poora.)

**`sort` — lines ko order mein lagao:**
```
sort names.txt
```
- Lines ko alphabetical (ya `-n` se numerical) order mein lagata. Flags: `-n` (numbers ki tarah
  sort — warna "10" "2" se pehle aa jata as text), `-r` (ulta/reverse), `-u` (unique — duplicate
  hata do).

**`uniq` — laga-tar duplicate lines hatao (ya gino):**
```
sort data.txt | uniq
```
- **Zaroori:** `uniq` sirf **laga-tar (adjacent)** duplicates hatata — isliye pehle `sort` karna
  padta (taaki same lines saath aa jaayein). `sort | uniq` standard jodi hai.
- **`uniq -c`** = har unique line ki **ginti** dikhata (`c` = count). "kaunsi cheez kitni baar aayi"
  ka jawab — analysis mein bahut kaam ka.

**`cut` — line se ek "column" nikaalo:**
```
cut -d',' -f2 data.csv
```
- **`-d','`** = delimiter (alag karne wala) comma hai (`d` = delimiter). **`-f2`** = field/column
  number 2 (`f` = field). Matlab: "har line ko comma pe todo, doosra tukda do". CSV se ek column
  nikaalne ka aasaan tareeka.

**`wc -l` — ginti (Ch 4.10):** lines gino. Pipe ke aakhir mein aksar "kitne" ka jawab.

> **Yaad rakhne wali baat:** Pipe ke building blocks: `grep` (matching lines filter), `sort` (order
> mein lagao), `uniq` (adjacent duplicates hatao/`-c` gino — sort ke baad), `cut -d -f` (column
> nikaalo), `wc -l` (gino). Inhe jodke bade jawab (6.10).

[↑ Back to top](#top)

---

<a id="s6-10"></a>
## 6.10 — Poora pipeline banana (ek real misaal step-by-step)

Ab sab jodte hain. Yeh Unix ki asli taakat hai. **Sawaal:** "ek web server ki log file
(`access.log`) mein, sabse zyada request bhejne wale top 5 IP address kaunse hain?"

Koi ek command iska jawab nahi deti. Par hum chhote tools jodenge — ek-ek step build karte hain:

**Step 1 — log ki har line ka pehla shabd (IP address) nikaalo:**
```
cut -d' ' -f1 access.log
```
- Log ki har line space se shuru hoti hai IP se. `cut -d' ' -f1` = "space pe todo, pehla tukda (IP)
  do". Ab humare paas sirf IP addresses ki list hai (har request ka ek).

**Step 2 — un IPs ko sort karo (taaki same IP saath aayein):**
```
cut -d' ' -f1 access.log | sort
```
- Pipe se `sort` ko diya. Ab same IP ek saath (uniq ke liye zaroori, 6.9).

**Step 3 — har IP kitni baar aaya, gino:**
```
cut -d' ' -f1 access.log | sort | uniq -c
```
- `uniq -c` = har unique IP ki ginti. Ab output: `  15 1.2.3.4`, `  3 5.6.7.8`... (ginti + IP).

**Step 4 — ginti ke hisaab se sort karo (sabse zyada upar), ulta:**
```
cut -d' ' -f1 access.log | sort | uniq -c | sort -rn
```
- `sort -rn` = `-n` (number ki tarah, ginti pe) `-r` (reverse, bada pehle). Ab sabse zyada request
  wala IP sabse upar.

**Step 5 — sirf top 5 lo:**
```
cut -d' ' -f1 access.log | sort | uniq -c | sort -rn | head -n 5
```
- `head -n 5` = pehli 5 lines (Ch 4.9). **Natija:** top 5 IP with unki request-ginti.

**Dekho kya hua:** 5 chhote tools (`cut`, `sort`, `uniq`, `sort`, `head`) — har ek ek chhota kaam —
pipe se jode, aur ek aisa jawab mila jiske liye koi single command nahi thi. **Yehi Unix philosophy
live hai** (6.2). Aur agar aap top 10 chahte, bs `head -n 10`. Alag question? Blocks badal do.

> **Yaad rakhne wali baat:** Bade jawab = chhote tools pipe se jodo, ek-ek step build karke. Top-IP
> misaal: `cut` (IP nikaalo) → `sort` (saath laao) → `uniq -c` (gino) → `sort -rn` (zyada upar) →
> `head` (top N). Har step test karke aage badho.

[↑ Back to top](#top)

---

<a id="s6-11"></a>
## 6.11 — Nuances aur caveats

- **`>` chup-chaap overwrite karta (sabse bada khatra):** `command > important.txt` — `important.txt`
  ka poora content mit jayega, bina warning. Zaroori file pe `>` chalane se pehle do baar socho.
  Append (`>>`) safe hai jab purana rakhna ho. (Kuch shells mein `set -o noclobber` overwrite rokta
  — advanced.)

- **`uniq` ke pehle `sort` bhoolna = galat ginti:** `uniq` sirf *adjacent* (saath-saath) duplicates
  hatata. Bina sort ke, door-door bikhre duplicates alag-alag gine jayenge. Hamesha `sort | uniq`.

- **Pipe mein har command alag process hai:** `a | b | c` — teeno saath chalte (parallel), data
  behta jata. Iska matlab kabhi exit code (`$?`) sirf *aakhri* command (`c`) ka milta, beech wale
  fail ho toh chhup jate. (Bash mein `set -o pipefail` isse pakadta — Ch 14.)

- **`2>&1` ka order:** `> file 2>&1` sahi (pehle output-jagah set, phir error wahin). `2>&1 > file`
  galat (jab error redirect kiya tab output abhi screen pe tha). Order ulta = kaam ulta.

- **Pipe stdout bhejta, stderr nahi:** `command1 | command2` — sirf stdout (1) aage jata; errors (2)
  phir bhi screen pe. Agar error bhi pipe karna ho toh `command1 2>&1 | command2`.

- **`echo "text" > file` bar-bar chalana = har baar overwrite:** loop mein galti se `>` use kiya toh
  har baar file reset ho jayegi, sirf aakhri line bachegi. Loop mein log ke liye `>>` (append)
  chahiye. Yeh common bug hai (Ch 10 loops ke saath).

- **Space `|` ke aas-paas optional par padhne mein achha:** `ls|wc -l` aur `ls | wc -l` dono chalte.
  Spaces ke saath padhna aasaan — aadat daal lo.

[↑ Back to top](#top)

---

<a id="s6-12"></a>
## 6.12 — Real-life scenarios

**Scenario 1 — "Log mein kitne errors aaye?"** Ek app log hai, aap jaanna chahte ho aaj kitni error
lines. `grep "ERROR" app.log | wc -l` — grep ne error lines chuni, wc -l ne gini. Ek number mil
gaya. Roz ki debugging cheez.

**Scenario 2 — "Command ka output baad ke liye save karo."** Aap ek lamba diagnostic command chala
rahe ho aur output baad mein team ko bhejna hai. `./diagnose.sh > report.txt 2>&1` — output aur
errors dono `report.txt` mein (6.6). Ab file bhej do. Ya live bhi dekhna ho toh `./diagnose.sh 2>&1
| tee report.txt` (6.8 — screen + file dono).

**Scenario 3 — "Sabse bade 5 files dhoondho folder mein."** Disk analysis: `du -ah . | sort -rh |
head -n 5` — `du` (sizes) → `sort -rh` (bade pehle, human-readable) → `head` (top 5). Pipeline se
turant jawab (6.10 wali soch).

**Scenario 4 — "Ek cron job chup chalani hai."** Aap ek background/scheduled task chala rahe ho aur
uska output kahin nahi chahiye (sirf chale). `./task.sh > /dev/null 2>&1` — output aur error dono
phenke (6.7). Terminal saaf, task chup chalti.

**Scenario 5 — "CSV se ek column nikaalo aur unique values dekho."** Ek CSV mein "city" column hai
(3rd), aap unique cities chahte ho. `cut -d',' -f3 data.csv | sort | uniq` — column nikaala, sort,
duplicates hataye. Data exploration ka aam pattern.

**Saar:** Chapter 6 shell ki asli taakat hai. Teen streams (stdin/stdout/stderr) samajh ke aap `|`
(command jodo), `>`/`>>` (file mein save), `2>`/`&>` (errors handle), `/dev/null` (phenko), `tee`
(dono jagah) use kar sakte ho. Unix philosophy — chhote tools pipe se jodna — aapko har naye problem
ka jawab "build" karne deta hai, bana-banaya command dhoondhne ke bajaye.

[↑ Back to top](#top)

---

> **Chapter 06 khatam.** Ab tak: teen streams (stdin=0, stdout=1, stderr=2); Unix philosophy (chhote
> tools jodo); `|` (pipe — output→input); `>`/`>>` (file mein overwrite/append); `<` (input file
> se); `2>`/`2>&1`/`&>` (error redirect); `/dev/null` (phenko); `tee` (screen+file); building blocks
> (`grep`/`sort`/`uniq`/`cut`); aur poora pipeline banana. **Agla chapter:** permissions — `rwx`,
> `chmod`, `chown`, `sudo`, aur `./script.sh` mein `./` ka poora kaaran.

[↑ Back to top](#top)
