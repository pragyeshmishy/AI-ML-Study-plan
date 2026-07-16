<a id="top"></a>
# Chapter 03 — Command ki Anatomy (ek command ke saare hisse)

Ab tak humne kuch commands dekhe — `ls`, `cd`, `pwd`. Par humne yeh nahi samjha ki ek command
*banti kaise hai* — uske andar kaunse-kaunse hisse hote hain, aur shell unhe kaise padhta hai.

Yeh chapter woh "grammar" sikhata hai. Jaise ek angrezi vakya (sentence) mein subject-verb-object
hote hain, waise hi ek shell command ke bhi fixed hisse hote hain. Ek baar yeh grammar samajh gaye,
toh aap **koi bhi** nayi command dekh ke uska matlab tod sakte ho — chahe woh command aapne pehle
kabhi na dekhi ho. Yeh chapter isiliye poore guide ka sabse "unlock karne wala" chapter hai.

Yeh theory-heavy hai, aur har chhote symbol (jaise `-`, `--`, space) ka literal matlab kholega.

---

## Is chapter ka index

- [3.1 — Ek command ke teen hisse: command, options, arguments](#s3-1)
- [3.2 — Pehla hissa: command (kya karna hai)](#s3-2)
- [3.3 — Doosra hissa: arguments (kis cheez pe karna hai)](#s3-3)
- [3.4 — Teesra hissa: options/flags (kaise karna hai)](#s3-4)
- [3.5 — `-` vs `--` : short flag vs long flag (literal farak)](#s3-5)
- [3.6 — Flags ko jodna (`-la` = `-l -a`) aur kab NAHI jod sakte](#s3-6)
- [3.7 — Value lene wale flags (`-m "msg"`, `-n 5`)](#s3-7)
- [3.8 — Aam flags ka matlab: `-v -r -f -i -h` (har command mein milenge)](#s3-8)
- [3.9 — Spaces ka role: shell kaise tod ke padhta hai](#s3-9)
- [3.10 — `--help`, `man`, `tldr` : khud se seekhne ke teen tareeke](#s3-10)
- [3.11 — Shell command ko dhoondhti kaise hai: `which`, `type`, PATH](#s3-11)
- [3.12 — Nuances aur caveats](#s3-12)
- [3.13 — Real-life scenarios](#s3-13)

---

<a id="s3-1"></a>
## 3.1 — Ek command ke teen hisse: command, options, arguments

Har shell command, chahe kitni bhi lambi ho, aam taur pe teen tarah ke hisson se banti hai. Ek
misaal se dekhte hain:

```
ls -l /Users/pragyesh
```

Ise tod ke dekho — teen hisse hain:

```
ls        -l        /Users/pragyesh
^         ^         ^
|         |         `- ARGUMENT  (kis cheez pe kaam karna hai)
|         `- OPTION/FLAG  (kaise karna hai)
`- COMMAND  (kya karna hai)
```

- **Command** (`ls`) — kya kaam karna hai. Yeh hamesha sabse pehle aata hai.
- **Option / Flag** (`-l`) — kaam *kaise* karna hai (yeh behaviour badalta hai). "Option" aur "flag"
  ek hi cheez ke do naam hain (log dono bolte hain).
- **Argument** (`/Users/pragyesh`) — kaam *kis cheez pe* karna hai (target — file, folder, ya text).

Ek angrezi jumle se compare karo, samajh pakki ho jayegi:
- **Command** = verb (kriya) — "dikhao" (`ls`)
- **Option** = adverb (kaise) — "detail ke saath" (`-l`)
- **Argument** = object (kis pe) — "us folder ka" (`/Users/pragyesh`)

Matlab poora command ka matlab: *"us folder (`/Users/pragyesh`) ko detail ke saath (`-l`) dikhao
(`ls`)"*.

**Zaroori baat — order aur separator:** in hisson ko **space** se alag kiya jata hai. Space hi shell
ko batata hai "yeh ek hissa khatam, agla shuru". (Space ka poora role 3.9 mein — yeh bahut important
hai.) Command hamesha pehle; options aur arguments uske baad (inka order aksar flexible hota hai, par
command pehle hi rehta).

**Har command mein teeno zaroori nahi:** kai commands sirf command se chal jaate hain (jaise `pwd` —
na option na argument). Kai mein sirf argument hota hai (`cd Downloads`). Yeh teen-hissa dhaancha
(structure) ek "template" hai — har command ismein se jitna chahiye utna use karta hai.

> **Yaad rakhne wali baat:** Command = kya karna (verb), Option/Flag = kaise karna (adverb),
> Argument = kis pe karna (object). Space se alag hote hain. Command hamesha pehle. Yeh grammar har
> command pe lagti hai.

[↑ Back to top](#top)

---

<a id="s3-2"></a>
## 3.2 — Pehla hissa: command (kya karna hai)

**Command** woh pehla shabd hai jo aap type karte ho — yeh batata hai ki *kaunsa kaam* karna hai.
Asal mein command ek **program ka naam** hota hai (ek chhoti file jo disk pe padi hai aur kaam
karti hai). Jaise `ls` ek program hai, `cd` ek command hai, `python3` ek program hai.

Do tarah ke commands hote hain (yeh farak aage kaam aayega):
- **External command (bahar wala program):** yeh disk pe ek alag file hoti hai. Jaise `ls` actually
  `/bin/ls` file hai (yaad karo Chapter 1 — `/bin` = binaries folder). Jab aap `ls` likhte ho, shell
  us file ko dhoondh ke chalata hai. (Dhoondhta kaise hai — 3.11 mein PATH.)
- **Built-in command (shell ke andar wala):** kuch commands shell ke *andar* hi bane hote hain, alag
  file nahi. Jaise `cd` — yeh koi `/bin/cd` file nahi hai, yeh shell ka apna hissa hai. Kyun? Kyunki
  `cd` ko shell ki apni "current location" badalni padti hai, jo sirf shell khud kar sakta hai.

**Kaise pata karein command external hai ya built-in?** `type` command se (3.11 mein detail):
```
type ls
type cd
```
- `type ls` bolega: `ls is /bin/ls` (external — file hai).
- `type cd` bolega: `cd is a shell builtin` (built-in — shell ke andar).

Abhi yeh yaad rakhna zaroori nahi ki kaunsa kya hai — bas yeh samajh lo ki **command ek naam hai
jise shell kisi program (ya apne built-in) se jodta hai.** Aage jab "command not found" error
aayega (3.11), tab yeh samajh kaam aayegi.

> **Yaad rakhne wali baat:** Command = pehla shabd = kaunsa kaam. Aksar yeh disk pe ek program-file
> hoti hai (jaise `/bin/ls`), kabhi shell ke andar built-in (jaise `cd`). `type <naam>` se pata
> chalta hai kaunsa hai.

[↑ Back to top](#top)

---

<a id="s3-3"></a>
## 3.3 — Doosra hissa: arguments (kis cheez pe kaam karna hai)

**Argument** woh cheez hai jis *par* command kaam karta hai — target. Yeh aksar ek file, folder, ya
koi text hota hai. Command ke baad, space chhod ke likha jata hai.

Misaalein:
```
cat notes.txt
```
- `cat` = command (file ka content dikhao), `notes.txt` = argument (kis file ka).

```
mkdir project
```
- `mkdir` = command (folder banao), `project` = argument (kis naam ka folder).

**Ek command ke kai arguments ho sakte hain:**
```
cp file1.txt file2.txt backup/
```
- `cp` = command (copy karo), aur teen arguments: `file1.txt`, `file2.txt` (kya copy karna),
  `backup/` (kahan). Har argument space se alag.

**Argument ka order kabhi matter karta hai:** upar `cp` mein — pehle "kya copy karna", aakhri mein
"kahan". Agar order galat kiya toh galat kaam ho jayega. Har command ke apne niyam hote hain ki
argument kis order mein aate hain (yeh `--help` se pata chalta, 3.10).

**Argument aur option/flag mein farak (yeh confuse karta hai):** argument aam text/file-naam hota
hai (jaise `notes.txt`). Flag `-` se shuru hota hai (jaise `-l`). Shell isi `-` se pehchanta hai ki
"yeh option hai, argument nahi". (3.4 aur 3.9 mein detail.)

> **Yaad rakhne wali baat:** Argument = jis cheez pe kaam karna (file/folder/text), command ke baad.
> Kai arguments space se alag ho sakte hain. Order kabhi matter karta hai. Flag (`-` wala) se alag
> hota hai.

[↑ Back to top](#top)

---

<a id="s3-4"></a>
## 3.4 — Teesra hissa: options/flags (kaise karna hai)

**Option** (ya **flag** — same cheez) command ka behaviour badalta hai — batata hai ki kaam *kaise*
karna hai. Yeh hamesha ek **dash `-`** (ya do dash `--`) se shuru hota hai. Yehi `-` shell ko batata
hai "yeh koi file-naam nahi, yeh ek setting hai".

Yaad karo Chapter 2 ka `ls`:
```
ls -l
```
- `-l` ek flag hai. `ls` ka kaam (files dikhao) wahi rehta hai, par `-l` batata hai "detail ke saath
  (long format mein) dikhao". Behaviour badla, kaam wahi.

**"Flag" naam kahan se aaya?** Socho ek switch/jhanda (flag) jo ya toh "on" hota hai ya "off". `-l`
lagaya = "long format ON". Nahi lagaya = "OFF" (normal). Isiliye inhe flag kehte hain — yeh koi
setting ko on/off karte hain.

**Ek command pe kai flags:**
```
ls -l -a
```
- `-l` (long format ON) aur `-a` (hidden files bhi dikhao ON). Dono ek saath. Do settings on ki.

**Flag ke bina command chalta hai (flag optional hai):** `ls` akela bhi chalta hai (default
behaviour). Flag tab lagate ho jab default se alag kuch chahiye. Isiliye ise "option" bhi kehte hain
— yeh optional hai, aapki marzi.

**Flag ka literal roop kyun chhota hota hai (`-l`, `-a`)?** Kyunki yeh aksar kisi angrezi shabd ka
pehla akshar hota hai — `-l` = **l**ong, `-a` = **a**ll (Chapter 2 mein dekha). Isiliye flag yaad
rakhna aasaan ho jata hai jab aap uska poora shabd jaante ho.

> **Yaad rakhne wali baat:** Option/Flag = behaviour badalne wali setting, `-` se shuru. `-` isliye
> taaki shell samajh jaye "yeh setting hai, file nahi". Optional hote hain. Aksar kisi shabd ka
> pehla akshar (`-l`=long).

[↑ Back to top](#top)

---

<a id="s3-5"></a>
## 3.5 — `-` vs `--` : short flag vs long flag (literal farak)

Flags do roop mein aate hain — ek dash (`-`) wala aur do dash (`--`) wala. Dono ka matlab same ho
sakta hai, par likhne ka tareeka aur niyam alag. Yeh farak samajhna zaroori hai.

**Short flag — ek dash `-` + ek akshar:**
```
ls -a
```
- `-a` = short flag. Ek `-` ke baad ek single akshar (`a`). Yeh chhota, jaldi likhne wala roop hai.
  Aksar experienced log yehi use karte hain (kam typing).

**Long flag — do dash `--` + poora shabd:**
```
ls --all
```
- `--all` = long flag. Do `--` ke baad poora shabd (`all`). Yeh `-a` ke barabar hi hai — **same
  kaam** karta hai, bas poore naam se. Yeh padhne mein clear hai (naya banda samajh jaye `--all`
  matlab "sab").

**Toh `-a` aur `--all` same hain?** Haan, is case mein bilkul same. Bahut se flags ke do roop hote
hain: chhota (`-a`) aur poora (`--all`). Aap koi bhi use kar sakte ho — result same.

**Do dash `--` kyun (ek se kaam chalta tha)?** Do wajah:
1. **Clarity:** `--verbose` padh ke turant samajh aata hai; `-v` ke liye yaad karna padta hai.
   Scripts mein aksar long flags use karte hain taaki koi aur (ya future aap) padh ke samajh jaye.
2. **Naam ka takraav (clash) bachane ke liye:** ek dash short (single akshar) ke liye reserved hai,
   do dash poore shabd ke liye. Isse shell confuse nahi hota. (Aur single-letter flags sirf 26 ho
   sakte hain a-z; poore shabd unlimited.)

**Kab kaunsa use karein:**
- **Terminal pe khud type karte waqt** → short (`-a`) — jaldi.
- **Script mein likhte waqt** → long (`--all`) — padhne wale ko clear, aur 6 mahine baad khud ko bhi.

**Ek khaas cheez — akela `--` (do dash, kuch nahi uske baad):** yeh ek special signal hai jo bolta
hai "yahan se aage sab arguments hain, koi flag nahi — chahe woh `-` se shuru kyun na ho". Yeh tab
kaam aata jab kisi file ka naam hi `-` se shuru ho (rare, par hota hai). Abhi bas itna jaan lo ki
akela `--` ka matlab "flags khatam, ab sirf files". (Yeh 3.12 mein aur.)

> **Yaad rakhne wali baat:** `-a` = short flag (ek dash, ek akshar, jaldi). `--all` = long flag (do
> dash, poora shabd, clear). Aksar dono same kaam karte hain. Terminal pe short, script mein long.
> Akela `--` = "ab aage sab files, koi flag nahi".

[↑ Back to top](#top)

---

<a id="s3-6"></a>
## 3.6 — Flags ko jodna (`-la` = `-l -a`) aur kab NAHI jod sakte

Ek badi convenience — **short flags ko ek saath jod sakte ho**. Yeh Chapter 2 mein `ls -ltr` mein
dekha tha; ab kyun aur kab, woh samajhte hain.

**Jodna (combining):**
```
ls -l -a          # alag-alag (do flags)
ls -la            # jude hue — bilkul same result
```
- `-la` = `-l` + `-a` ek saath. Ek `-` ke baad dono akshar (`l` aur `a`). Shell ise "l aur a dono
  flags" samajh leta hai.
- Isiliye `ls -ltr` = `-l -t -r` teeno ek saath (Chapter 2.10).

**Yeh kaam kaise karta hai (kyun jud jaate hain):** shell jaanta hai ki short flags single-akshar
hote hain. Toh `-la` dekhke woh soch leta hai "yeh ek nahi, do flags hain: l, a". Har akshar ek alag
flag. Isiliye order bhi aksar matter nahi karta — `-la` aur `-al` same.

**Kab NAHI jod sakte (zaroori caveat):**
1. **Long flags jod nahi sakte:** `--all --long` ko `--alllong` nahi likh sakte. Long flags hamesha
   alag, poore. Sirf **short** (single-dash) flags jud sakte hain.
2. **Jab flag koi value leta ho** (3.7), toh use aakhri mein rakhna padta hai (ya alag). Jaise
   `tar -czf backup.tar` — yahan `f` value (`backup.tar`) leta hai, isliye `f` aakhri mein hai.
   Isko beech mein daloge toh gadbad. (3.7 mein detail.)

**Chhota misaal jodne ka fayda:**
```
grep -i -v -n "error" log.txt      # teen alag flags
grep -ivn "error" log.txt          # jude — same kaam, kam typing
```
- `-ivn` = `-i` (ignore case) + `-v` (invert) + `-n` (line number). Teeno ek saath. (Yeh flags Ch 12
  mein grep ke saath aayenge — abhi sirf jodna dikhaya.)

> **Yaad rakhne wali baat:** Short flags jud sakte hain: `-la` = `-l -a`. Sirf single-dash (short)
> wale, long (`--`) nahi. Value lene wala flag aakhri mein rakho. Jodna sirf kam-typing ke liye,
> result same.

[↑ Back to top](#top)

---

<a id="s3-7"></a>
## 3.7 — Value lene wale flags (`-m "msg"`, `-n 5`)

Ab tak ke flags on/off switch the (`-l` = long ON). Par kuch flags ko ek **value** bhi chahiye hoti
hai — matlab flag ke baad ek aur cheez, jo us flag ko batati hai "kitna" ya "kya".

**Misaal 1 — `git commit -m "message"`:**
```
git commit -m "Fixed the login bug"
```
- `-m` flag akela adhoora hai — ise ek value chahiye: commit ka message. Yahan value hai
  `"Fixed the login bug"`. `-m` = **m**essage. Toh `-m "..."` = "message yeh hai".
- Value quotes (`"..."`) mein isliye kyunki usmein spaces hain (3.9 mein poora kaaran — spaces shell
  ko confuse karte hain, quotes unhe ek saath bandh dete hain).

**Misaal 2 — `head -n 5 file.txt`:**
```
head -n 5 notes.txt
```
- `head` = file ki shuruaat dikhao. `-n` flag ko ek value chahiye: kitni lines? Yahan `5`. Toh
  `-n 5` = "5 lines". Bina value ke `-n` ka koi matlab nahi.

**Value flag ke saath likhne ke do tareeke (dono chalte hain):**
```
head -n 5 notes.txt        # flag, space, value (aam tareeka)
head -n5 notes.txt         # flag se chipka (bina space) — kabhi chalta
head --lines=5 notes.txt   # long flag ke saath = se value jodte hain
```
- Short flag: value space ke baad (`-n 5`) — sabse common.
- Long flag: value `=` se jodte hain (`--lines=5`). Yeh convention hai long flags ke liye.

**Yeh 3.6 (jodna) se kaise juda:** yaad karo maine kaha "value lene wala flag aakhri mein". Ab
samajh aayega — agar aap `tar -czf backup.tar` likhte ho, toh `-czf` mein `c`, `z` on/off hain par
`f` value (`backup.tar`) leta hai. Isiliye `f` aakhri akshar hai — uske turant baad value aati hai.
Agar `f` beech mein hota, shell confuse ho jata "value kiske liye hai".

**Kaise pehchanein ki flag value leta hai ya nahi?** Yeh har command ka apna niyam hai — `--help`
(3.10) mein likha hota hai. Jaise `-n` ke aage `<number>` likha ho toh value chahiye; `-l` ke aage
kuch na ho toh woh sirf switch hai.

> **Yaad rakhne wali baat:** Kuch flags value lete hain (`-m "msg"`, `-n 5`) — flag ke baad woh cheez
> jo use complete kare. Short mein space se (`-n 5`), long mein `=` se (`--lines=5`). Value wale flag
> ko jodte waqt aakhri mein rakho. `--help` batata hai kaunsa flag value leta hai.

[↑ Back to top](#top)

---

<a id="s3-8"></a>
## 3.8 — Aam flags ka matlab: `-v -r -f -i -h` (har command mein milenge)

Kuch flags itne common hain ki **bahut saare alag-alag commands** mein same matlab ke saath milte
hain. Inhe ek baar seekh lo, toh nayi command mein bhi guess kar loge. (Yeh 100% niyam nahi — kuch
commands apna matlab rakhte hain — par yeh convention aksar sach hoti hai.)

| Flag | Kis shabd se | Aam matlab | Poora example (chala ke) | Kis case mein valid / kab use |
|---|---|---|---|---|
| `-v` | **v**erbose | "zyada detail bolo" — command bataye woh kya-kya kar raha (verbose = baatuni) | `cp -v a.txt b.txt` → output: `a.txt -> b.txt` (kya copy hua dikhaya) | Jab command chup-chaap kaam karti aur aap dekhna chahte "kya ho raha" — bade copy/move/install mein progress dekhne ko |
| `-r` / `-R` | **r**ecursive | "andar tak, folder ke sab andar-wale bhi" (recursive = baar-baar andar) | `cp -r project/ backup/` → poora `project` folder (andar ki har file/sub-folder samet) copy | Jab kaam ek **folder** pe hai (file pe nahi) — `cp`/`rm`/`chmod`/`grep` folder pe chalate waqt. Bina `-r`, folder pe yeh commands mana kar dete |
| `-f` | **f**orce | "zabardasti karo, poocho mat, warning ignore" | `rm -f purani.log` → bina "sure?" pooche turant delete (file na ho toh bhi error nahi) | Jab aap **sure** ho aur confirm-prompt nahi chahiye — scripts/automation mein (jahan koi `y` dabane wala nahi). Interactive kaam mein avoid (galti ka risk) |
| `-i` | **i**nteractive | "har step pe poocho (confirm maango)" — force ka ulta | `rm -i *.txt` → har file pe `remove a.txt? (y/n)` poochega | Jab aap **sure nahi** aur galti se bachna hai — bulk/important delete se pehle safety. `-f` ka ulta |
| `-h` | **h**elp YA **h**uman-readable | context pe: `--help` = madad; `-h` (size ke saath) = KB/MB mein | `ls -lh` → size `1048576` ke bajaye `1.0M` (insaan-padhne-yogya) | `-h` size-wale commands (`ls -lh`, `du -h`, `df -h`) mein — jab bytes ke bade number samajhna mushkil. (Alag context: `--help` = madad) |
| `-a` | **a**ll | "sab, chhupe hue bhi" | `ls -a` → normal files + `.env`, `.git` (hidden, `.` se shuru — Ch 2) bhi dikhega | Jab **hidden files/cheezein** bhi chahiye — `.env`/`.git` dhoondhte waqt (Ch 2.12), ya "poora" dekhna ho |
| `-l` | **l**ong | "detail/lamba format" | `ls -l` → har file ek line: permissions, owner, size, date (Ch 2.11) | Jab sirf naam kaafi nahi — file ki **detail** (permissions/size/date) chahiye. Aksar `-a`/`-h`/`-t` ke saath (`ls -lah`) |
| `-n` | **n**umber / **n**ame | context pe: "kitni (number)" ya "sirf dikhao, karo mat (dry-run)" | `head -n 3 log.txt` → sirf pehli **3** lines (Ch 4.9) | Jab aapko **kitni** (ginti) batani ho — `head -n 5`, `tail -n 20`. (Kuch commands mein `-n` = "dry-run: dikhao, karo mat") |
| `-o` | **o**utput | "output yahan daalo (file mein)" | `curl -o page.html example.com` → output screen pe nahi, `page.html` file mein save | Jab command ka result **file mein save** karna ho (screen pe dikhane ke bajaye) — `curl -o`, `sort -o`, compilers `-o` |
| `-q` | **q**uiet | "chup raho, kuch mat bolo" (verbose ka ulta) | `grep -q "error" log.txt` → kuch print nahi, sirf exit code (mila=0, Ch 5.6) | Jab output **nahi chahiye**, sirf "kaam hua ya nahi" (exit code) — scripts mein `if grep -q ...` (Ch 12.10). `-v` ka ulta |

**Do sabse khatarnaak (dhyan se) — `-r` aur `-f`:**
- **`-r` (recursive):** folder aur uske *andar ka sab kuch*. `rm -r project` poora `project` folder
  + andar ki har file/folder uda dega. Bahut powerful, bahut khatarnak.
- **`-f` (force):** "poocho mat, kar do". Normally shell important cheez delete karne se pehle
  confirm maang sakta hai; `-f` woh safety hata deta hai.
- **`rm -rf`** (dono saath) = "recursively, forcefully delete" = **sabse khatarnak command** — poora
  folder tree bina kuch pooche mita deta hai. (Iska poora khatra Chapter 4 aur anti-patterns mein.)
  Abhi bas yeh jaan lo: `-rf` dekho toh ruk ke socho.

**Fayda samajhne ka:** ab agar aap ek nayi command dekhein, jaise `cp -rv src dst`, toh aap bina
manual padhe guess kar sakte ho: `-r` = recursive (folder ke andar sab), `-v` = verbose (batao kya
copy ho raha). Yeh "flag-vocabulary" nayi commands ko turant samajhne ki chaabi hai.

> **Yaad rakhne wali baat:** Aam flags ka matlab commands ke beech aksar same: `-v` verbose (detail
> bolo), `-r` recursive (andar tak), `-f` force (poocho mat), `-i` interactive (poocho), `-h`
> help/human-size, `-q` quiet. `rm -rf` = sabse khatarnak, dhyan se.

[↑ Back to top](#top)

---

<a id="s3-9"></a>
## 3.9 — Spaces ka role: shell kaise tod ke padhta hai

Yeh section chhota lagta hai par **bahut zaroori** hai — bahut si "command kaam nahi kar rahi" wali
galtiyan spaces ki wajah se hoti hain.

**Space shell ke liye "separator" hai.** Jab aap command likhte ho, shell use spaces pe tod ke
alag-alag tukdon (jinhe "tokens" kehte hain — matlab alag-alag shabd/hisse) mein baant leta hai.
Har token ya toh command hai, ya flag, ya argument.

```
cp   file1.txt   backup/
```
- Shell dekhta hai: teen tokens (spaces se alag) — `cp` (command), `file1.txt` (arg1), `backup/`
  (arg2). Kitne bhi spaces daalo (ek ya paanch), shell unhe ek separator hi maanta hai.

**Ab asli problem — file naam mein khud space ho toh?** Maan lo ek folder hai `My Documents` (beech
mein space). Aap likhte ho:
```
cd My Documents
```
- Shell ise **do tokens** samajhta hai: `My` (arg1) aur `Documents` (arg2). Woh sochta hai "cd ko do
  cheezein di gayi" — aur confuse hokar error deta hai (`cd: too many arguments` ya `My: no such
  directory`). Kyunki shell ko nahi pata ki `My Documents` ek hi naam hai — uske liye space = alag
  cheez.

**Do solution (dono zaroori jaan-na):**
1. **Quotes mein daalo** (sabse aam):
```
cd "My Documents"
```
   - Quotes (`"..."`) shell ko bolte hain "yeh sab ek hi cheez hai, ismein wale space ko separator
     mat samjho". (Quotes ka poora chapter aage hai — Ch 5 — abhi bas yeh use.)
2. **Space se pehle `\` (backslash) lagao** (escape karna):
```
cd My\ Documents
```
   - `\` shell ko bolta hai "agla character (yahan space) special nahi, use naam ka hissa samjho".
     Ise "escape karna" kehte hain — `\` agle character ka special-matlab hata deta hai. (Ch 5.)

**Yeh 3.7 se kaise juda:** yaad karo `git commit -m "Fixed the login bug"` — message mein spaces
the, isliye quotes zaroori the. Bina quotes ke shell `Fixed`, `the`, `login`, `bug` ko alag
arguments samajh leta aur error deta. Ab samajh aaya kyun quotes the.

**Chhota rule:** jahan kisi naam/value mein space ho — use quotes mein daalo. Yeh 90% space-wali
galtiyan bacha leta hai.

> **Yaad rakhne wali baat:** Space = shell ka separator (tokens alag karne wala). File naam mein khud
> space ho toh shell confuse hota — use `"quotes"` mein daalo ya space se pehle `\` lagao. Yeh bahut
> common galti-source hai.

[↑ Back to top](#top)

---

<a id="s3-10"></a>
## 3.10 — `--help`, `man`, `tldr` : khud se seekhne ke teen tareeke

Aapko har command ke saare flags yaad rakhne ki zaroorat nahi — koi nahi rakhta. Zaroori yeh hai ki
aap **khud se pata karna** jaante ho ki kisi command ke kya flags hain, kya kaam karta hai. Iske
teen tareeke hain, aasaan se detailed tak.

**1. `--help` — jaldi, command ke saath hi:**
```
ls --help
```
- Yeh command ka chhota "help screen" dikhata hai — saare flags aur unka ek-line matlab. Sabse fast.
- Kuch commands (khaaskar Mac ke purane wale) `--help` nahi, `-h` samajhte hain — dono try karo.
- **Kab use:** "is command ke flags kya hain, jaldi dekhna hai" — yeh.

**2. `man` — poora manual (detailed):**
```
man ls
```
- `man` = **man**ual. Yeh command ki poori documentation kholta hai — har flag ka detail, examples,
  sab kuch. `--help` se kaafi zyada.
- Yeh ek "pager" (scroll karne wala viewer) mein khulta hai. Chalane ke liye:
  - **Arrow keys / Space** = neeche scroll.
  - **`/word`** = koi shabd search karo (jaise `/recursive`).
  - **`q`** = **q**uit (bahar niklo). *(Yaad karo Chapter 1 — atak jao toh `q`.)*
- **Kab use:** "is command ko theek se samajhna hai, detail chahiye" — yeh.

**3. `tldr` — insaan-friendly, sirf examples:**
```
tldr tar
```
- `tldr` = "Too Long; Didn't Read" (bahut lamba tha, padha nahi). Yeh `man` ka chhota, practical
  version hai — theory nahi, sirf **common examples** dikhata hai (jaise "file zip karne ko: `tar
  -czf ...`").
- Yeh pehle se installed nahi hota — alag se install karna padta hai (`brew install tldr` Mac pe).
- **Kab use:** "mujhe theory nahi, bas ek kaam ka example chahiye jaldi" — yeh sabse practical hai.

**Teeno ka farak (ek line mein):**
- `--help` = flags ki quick list.
- `man` = poora manual (sab detail, `q` se bahar).
- `tldr` = sirf kaam ke examples (install karna padta).

**Sabse zaroori aadat:** koi nayi command mile aur samajh na aaye — pehle `--help` ya `tldr`
maaro. Yeh "khud se seekhna" hi asli skill hai; flag ratne ki zaroorat nahi.

> **Yaad rakhne wali baat:** Flags yaad mat rakho — khud pata karo. `command --help` (quick flag
> list), `man command` (poora manual, `q` se bahar), `tldr command` (sirf examples, install karna
> padta). Nayi command? Pehle `--help`/`tldr`.

[↑ Back to top](#top)

---

<a id="s3-11"></a>
## 3.11 — Shell command ko dhoondhti kaise hai: `which`, `type`, PATH

Jab aap `ls` type karte ho, shell ko kaise pata chalta hai ki `ls` ka program kahan (kis file mein)
hai? Yeh samajhna zaroori hai — kyunki jab "command not found" error aata hai, iski jadd yahi hoti
hai.

**PATH kya hai:** **PATH** ek environment variable (ek setting jismein value rakhi hai — Chapter 5
mein detail) hai jo folders ki ek **list** rakhta hai. Jab aap koi command likhte ho, shell in
folders mein ek-ek karke dhoondhta hai ki us naam ka program kahin pada hai kya. Pehla milne wala
chala deta hai.

Apna PATH dekho:
```
echo $PATH
```
- **`echo`** = screen pe dikhao, **`$PATH`** = PATH variable ki value (yaad karo `$` = "iske andar ki
  value do" — Chapter 1 wala `$0`/`$SHELL`). 
- **Output (misaal):** `/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin`
- **Matlab:** yeh `:` (colon) se alag folders ki list hai. Shell command dhoondhne ke liye pehle
  `/usr/local/bin` dekhega, phir `/usr/bin`, phir `/bin`... Yahan `:` separator hai (jaise path mein
  `/` separator tha).

**`which` — batata hai command kahan mila:**
```
which ls
```
- **Output:** `/bin/ls`
- **Matlab:** `ls` program `/bin/ls` file mein hai — shell ne PATH ke folders mein dhoondh ke yahan
  paya. `which` = "kaunsi file chalegi jab main yeh command likhun".

**`type` — thoda zyada batata hai (built-in bhi):**
```
type cd
type ls
```
- `type cd` → `cd is a shell builtin` (yaad karo 3.2 — cd shell ke andar hai, file nahi).
- `type ls` → `ls is /bin/ls` (external file).
- `type` `which` se behtar hai kyunki yeh built-in commands ko bhi pehchan leta hai (jinki koi file
  nahi hoti, isliye `which` unhe nahi dhoondh pata).

**"command not found" ab samajh aayega:** jab shell PATH ke saare folders mein dhoondh ke bhi command
na paye, toh `command not found` deta hai. Iska matlab: ya toh naam galat likha (typo), ya woh
program installed nahi, ya woh installed hai par uska folder PATH mein nahi hai. (Aakhri wala tab
hota jab aap koi tool install karte ho par shell use nahi dhoondh pata — tab uska folder PATH mein
add karna padta, Chapter 8 wala `.zshrc` editing yaad karo.)

> **Yaad rakhne wali baat:** PATH = folders ki list (`:` se alag) jahan shell command dhoondhta hai.
> `echo $PATH` (list dekho), `which ls` (kahan mila), `type cd` (built-in ya file). "command not
> found" = typo, ya installed nahi, ya PATH mein folder nahi.

[↑ Back to top](#top)

---

<a id="s3-12"></a>
## 3.12 — Nuances aur caveats

- **Flag ka order aksar matter nahi karta, par kabhi karta hai.** `ls -l -a` aur `ls -a -l` same.
  Par kuch commands mein order matter karta hai (khaaskar jab do flags aapas mein takrate ho — jaise
  ek `-q` quiet aur ek `-v` verbose, tab aakhri wala jeetta hai). Aam taur pe flags ka order free
  hai, par argument ka order (jaise `cp` mein source-phir-destination) fixed hota hai.

- **`-` se shuru hone wale file naam problem karte hain.** Agar galti se koi file `-file.txt` naam ki
  ban jaye, toh `rm -file.txt` fail hoga — shell `-file.txt` ko flag samjhega. Solution: `rm --
  -file.txt` (akela `--` = "aage sab files hain", 3.5 wala) ya `rm ./-file.txt` (`./` laga do).

- **Har command apne flags rakhta hai — universal nahi.** `-n` ka matlab `head` mein "number of
  lines" hai, par `grep` mein "line number dikhao", aur kisi aur mein "dry-run (karo mat, dikhao)".
  Convention (3.8) aksar sach hai par 100% nahi — confuse ho toh `--help` dekho.

- **Mac aur Linux ke flags kabhi alag hote hain.** Mac (BSD) aur Linux (GNU) ke commands ke kuch flags
  alag hain. Jaise `ls -h` dono pe hai, par kuch advanced flags sirf ek pe. Isiliye script likhte
  waqt, agar woh Linux server pe chalni hai, Linux ke flags use karo (Mac pe test karke dhoka ho
  sakta).

- **Flags case-sensitive hote hain.** `-r` aur `-R` alag ho sakte hain! Jaise `sort -r` (reverse)
  vs kisi aur command mein `-R` (recursive). Chhota-bada akshar matter karta — dhyan se.

- **`--help` khud kabhi error jaisa dikhta hai.** Kuch purane commands `--help` nahi samajhte aur
  ulta error de dete hain (ya kaam kar dete hain!). Jaise `rm --help` theek, par kuch tools pe
  `--help` unexpected. Safe rehne ko `man` use karo agar `--help` ajeeb kare.

[↑ Back to top](#top)

---

<a id="s3-13"></a>
## 3.13 — Real-life scenarios

**Scenario 1 — "Nayi command mili, samajh nahi aa rahi."** Aapko ek script mein `tar -xzvf
backup.tar.gz` dikha. Ab aap tod sakte ho: `tar` = command, aur `-xzvf` = 4 short flags jude
(`x`=extract, `z`=gzip, `v`=verbose, `f`=file). `backup.tar.gz` = argument. Samajh na aaye toh
`tar --help` ya `tldr tar`. Chapter 3 ki grammar se aap koi bhi command tod sakte ho.

**Scenario 2 — "Command not found, jabki tool install kiya tha."** Aapne ek Python tool install
kiya par terminal `command not found` de raha. Ab aap jaante ho (3.11) — `which toolname` (kahan
hai?), `echo $PATH` (uska folder list mein hai?). Aksar tool install hota hai par uska folder PATH
mein nahi — use `.zshrc` mein PATH mein add karna padta (Ch 8 + Ch 5).

**Scenario 3 — "Space wale filename pe command fail."** Aap `cd Project Files` likhte ho aur error
aata hai. Ab aap jaante ho (3.9) — space separator hai, shell `Project` aur `Files` alag samajh
raha. Fix: `cd "Project Files"` (quotes). Yeh roz ki galti hai jab folder naam mein space ho.

**Scenario 4 — "Galti se `rm -rf` samajh nahi aaya kya karega."** Kisi ne bola `rm -rf build/` chala
do. Ab aap jaante ho (3.8) — `-r` recursive (andar sab), `-f` force (bina pooche). Matlab `build`
folder + andar ka sab kuch bina confirm ke uda dega. Ab aap ruk ke soch sakte ho "sahi folder toh
hai na?" — yeh soch bada nuksaan bachati hai.

**Scenario 5 — "Flag chahiye par yaad nahi."** Aapko files ko size ke hisaab se sort karke dekhna hai
par flag yaad nahi. `ls --help` maaro (ya `man ls`), `/size` search karo (man mein) — mil jayega
(`-S`). Aap ko flags ratne ki zaroorat nahi thi — khud dhoondhna aana chahiye (3.10).

**Saar:** Chapter 3 aapko ek "command tod-ne wala lens" deta hai. Ab har command — chahe kitni bhi
ajeeb dikhe — aap uske hisson (command / flags / arguments) mein tod ke samajh sakte ho, aur jo na
pata ho woh `--help`/`man`/`tldr` se khud nikaal sakte ho. Yeh ratne se aazadi hai.

[↑ Back to top](#top)

---

> **Chapter 03 khatam.** Ab tak: command ke teen hisse (command/option/argument); command external
> vs built-in; short flag (`-a`) vs long flag (`--all`); flags jodna (`-la`); value lene wale flags
> (`-m "msg"`); aam flags (`-v -r -f -i -h`); spaces ka separator-role aur quotes; `--help`/`man`/
> `tldr` se khud seekhna; aur `which`/`type`/PATH se command-dhoondhna. **Agla chapter:** file aur
> folder operations — `touch`, `mkdir`, `cp`, `mv`, `rm`, `cat`, aur inke flags + `rm -rf` ka khatra.

[↑ Back to top](#top)
