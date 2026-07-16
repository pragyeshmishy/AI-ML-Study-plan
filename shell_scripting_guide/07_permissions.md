<a id="top"></a>
# Chapter 07 — Permissions aur Ownership (kaun kya kar sakta)

Chapter 2 mein `ls -l` ki output mein humne ek ajeeb sa hissa dekha tha — `-rwxr-xr-x`. Humne kaha
tha "yeh permissions hain, poora Ch 7 mein". Ab woh chapter aa gaya.

**Permissions** batate hain ki **kaun** (kaunsa user) kisi file/folder pe **kya** (padh/likh/chala)
kar sakta hai. Yeh Linux/Mac ki security ki neev hai — isiliye ek user doosre ki files nahi bigaad
sakta, aur system files aam user se surakshit rehti hain.

Yeh theory-heavy chapter hai — har akshar (`r`, `w`, `x`), har number (`755`), aur `./script.sh`
mein `./` ka poora kaaran kholega.

---

## Is chapter ka index

- [7.1 — Permissions kyun hoti hain (ek multi-user system ki soch)](#s7-1)
- [7.2 — Teen kaam: read (r), write (w), execute (x)](#s7-2)
- [7.3 — Teen log: owner, group, others](#s7-3)
- [7.4 — `ls -l` ki permission-string poora padhna (`-rwxr-xr-x`)](#s7-4)
- [7.5 — `chmod` — permissions badalna (symbolic tareeka: `+x`)](#s7-5)
- [7.6 — `chmod` numbers ka raaz (`755`, `644` — yeh kahan se aate)](#s7-6)
- [7.7 — `./script.sh` mein `./` aur execute bit ka poora kaaran](#s7-7)
- [7.8 — `chown` aur `chgrp` — maalik/group badalna](#s7-8)
- [7.9 — `sudo` — root banke kaam karna (aur khatra)](#s7-9)
- [7.10 — Nuances aur caveats](#s7-10)
- [7.11 — Real-life scenarios](#s7-11)

---

<a id="s7-1"></a>
## 7.1 — Permissions kyun hoti hain (ek multi-user system ki soch)

Linux/Unix shuru se hi **multi-user** system hain — matlab ek computer (khaaskar server) pe kai log
ek saath kaam karte hain. Ek college server pe sau students, ek company server pe kai engineers. Ab
socho — agar koi bhi kisi ki bhi file padh/badal/mita sake, toh chaos ho jaye.

**Permissions yeh problem solve karti hain:** har file/folder pe likha hota hai ki "kaun ise padh
sakta, kaun badal sakta, kaun chala sakta". Isse:
- Aapki private files doosre nahi padh sakte (jab tak aap permission na do).
- System ki zaroori files (jaise `/bin/ls`) aam user badal/mita nahi sakta — sirf admin (root).
- Ek galat program poore system ko nuksaan nahi pahuncha sakta (uski permission limited hai).

**Do sawaalon ka jawab hoti hain permissions:**
1. **Kya kaam?** — read (padhna), write (likhna/badalna), execute (chalana). — Section 7.2
2. **Kaun kar sakta?** — owner (maalik), group (ek team), others (baaki sab). — Section 7.3

In do (kya + kaun) ko mila ke poori permission banti hai. Yeh Windows se alag soch hai (jahan yeh
km dikhti) — Linux/Mac mein yeh har file pe saaf likhi hoti aur roz kaam aati.

> **Yaad rakhne wali baat:** Permissions isliye — Linux/Unix multi-user hain, sabki files/system ko
> ek doosre se surakshit rakhna zaroori. Do sawaal: KYA kaam (read/write/execute) + KAUN kar sakta
> (owner/group/others). Dono milke permission.

[↑ Back to top](#top)

---

<a id="s7-2"></a>
## 7.2 — Teen kaam: read (r), write (w), execute (x)

Kisi file/folder pe teen tarah ke kaam ho sakte hain. Har ek ka ek akshar hai:

- **`r` = read (padhna):** file ka content padh sakte ho (jaise `cat`, `less`). Folder ke liye:
  uski list dekh sakte ho (`ls`).
- **`w` = write (likhna/badalna):** file ka content badal/likh sakte ho. Folder ke liye: usmein nayi
  files bana/delete kar sakte ho.
- **`x` = execute (chalana):** file ko ek program ki tarah **chala** sakte ho (jaise ek script).
  Folder ke liye: `x` ka matlab thoda alag — us folder ke *andar ja sakte ho* (`cd`).

**File vs folder pe matlab (yeh confuse karta hai — table):**

| Akshar | File pe matlab | Folder pe matlab |
|---|---|---|
| `r` (read) | content padho | andar ki list dekho (`ls`) |
| `w` (write) | content badlo | andar files banao/mitao |
| `x` (execute) | program ki tarah chalao | andar jao (`cd`) |

**`x` sabse interesting hai:** file pe `x` = "yeh chalne wali cheez hai" (script/program). Ek text
file (jaise `notes.txt`) pe `x` nahi hota (woh chalne wali cheez nahi). Ek script (jaise
`deploy.sh`) pe `x` hona zaroori hai warna woh chalegi nahi (7.7 mein poora — yehi `./script.sh` ka
kaaran).

> **Yaad rakhne wali baat:** Teen kaam — `r` (read/padho), `w` (write/badlo), `x` (execute/chalao).
> File aur folder pe inka matlab thoda alag (table). `x` khaas: file pe "chalne wali cheez", folder
> pe "andar ja sakte" (`cd`).

[↑ Back to top](#top)

---

<a id="s7-3"></a>
## 7.3 — Teen log: owner, group, others

Ab "kaun" — permissions teen tarah ke logon ke liye alag-alag set hoti hain:

- **Owner (maalik)** — jisne file banayi, ya jise di gayi. Aam taur pe aap apni files ke owner ho.
  ("user" bhi kehte, isliye kabhi `u`.)
- **Group (samuh/team)** — ek group of users. Linux mein users ko groups mein daala ja sakta (jaise
  "developers" group). File ka ek group hota — us group ke saare log ye permission paate. (`g`.)
- **Others (baaki sab)** — jo na owner hai na us group mein — matlab system ke baaki saare users.
  (`o`.)

**Kyun teen level?** Taaki aap alag-alag logon ko alag access de sako. Misaal: ek file jo:
- **Owner** padh-likh sake (aapki file, aap sab kuch karo).
- **Group** sirf padh sake (aapki team dekhe par badle nahi).
- **Others** kuch na kar sake (baaki sab ke liye band).

Yeh flexibility zaroori hai — har file ke liye teen alag audiences ko alag rights.

**`a` = all (teeno ek saath):** kabhi aap teeno (owner+group+others) ko ek saath set karna chahte ho
— uske liye `a` (all) hai (7.5 mein use).

> **Yaad rakhne wali baat:** Teen log — owner (`u`, maalik), group (`g`, ek team), others (`o`, baaki
> sab). Har ek ke liye alag r/w/x set hoti. Isse alag logon ko alag access. `a` = all (teeno saath).

[↑ Back to top](#top)

---

<a id="s7-4"></a>
## 7.4 — `ls -l` ki permission-string poora padhna (`-rwxr-xr-x`)

Ab do cheezein (kya + kaun) jod ke, `ls -l` ki woh string padho. Chapter 2 mein preview kiya tha —
ab poora tod ke.

```
-rwxr-xr-x  1  pragyesh  staff  1024  Jun 30  deploy.sh
```

Pehla hissa `-rwxr-xr-x` — **10 akshar**. Ise aise todo:

```
-    rwx      r-x      r-x
^    ^        ^        ^
|    |        |        `- OTHERS ki permissions (baaki sab)
|    |        `- GROUP ki permissions
|    `- OWNER ki permissions
`- type (- = file, d = folder, l = link)
```

- **Pehla akshar (`-`) = type** (kya cheez hai — 7 mein permission nahi):
  - `-` = normal file, `d` = directory (folder), `l` = link (shortcut). (Ch 2 wala.)
- **Agle 9 = teen group of 3** — owner, group, others. Har group mein `rwx` order fixed:
  - **`rwx` (owner):** read haan, write haan, execute haan — owner sab kuch kar sakta.
  - **`r-x` (group):** read haan, write **nahi** (`-` = yeh permission nahi), execute haan.
  - **`r-x` (others):** read haan, write nahi, execute haan.

**`-` ka matlab:** jahan akshar hai (jaise `r`) = woh permission **hai**. Jahan `-` hai = woh
permission **nahi** hai. Order hamesha `rwx` — toh `r-x` matlab "read hai, write nahi, execute hai".

**Ek aur misaal — ek normal text file:**
```
-rw-r--r--  1 pragyesh staff  200 Jun 30 notes.txt
```
- `-` = file. `rw-` (owner: read+write, execute nahi — text file chalane wali nahi). `r--` (group:
  sirf read). `r--` (others: sirf read). Yeh ek typical document ki permission hai — owner badal
  sakta, baaki sirf padh sakte.

**Folder ki misaal:**
```
drwxr-xr-x  5 pragyesh staff  160 Jun 30 project
```
- `d` = folder. `rwx` (owner: list dekho, banao/mitao, andar jao). `r-x` (group aur others: list
  dekho aur andar jao, par bana/mita nahi sakte). Yeh typical folder permission.

> **Yaad rakhne wali baat:** `-rwxr-xr-x` = type(1) + owner(3) + group(3) + others(3). Har group
> `rwx` order mein; akshar = permission hai, `-` = nahi. `rw-r--r--` = typical file (owner
> read+write, baaki read). `drwxr-xr-x` = typical folder.

[↑ Back to top](#top)

---

<a id="s7-5"></a>
## 7.5 — `chmod` — permissions badalna (symbolic tareeka: `+x`)

**`chmod`** = **ch**ange **mod**e ("mode" = permissions ka purana naam). Yeh file/folder ki
permissions badalta hai. Do tareeke hain — **symbolic** (aksharon se, aasaan samajhne mein) aur
**numeric** (numbers se, 7.6). Pehle symbolic.

**Symbolic structure: `chmod [kaun][+/-][kya] file`**
- **kaun:** `u` (owner), `g` (group), `o` (others), `a` (all).
- **`+`** = permission **do** (add), **`-`** = permission **hatao** (remove), **`=`** = exactly yeh
  set karo.
- **kya:** `r`, `w`, `x`.

**Sabse common — script ko chalne-laayak banana:**
```
chmod +x deploy.sh
```
- **`+x`** = "execute permission do". (Kaun nahi likha toh `a` = sabko.) Ab `deploy.sh` chalne-laayak
  (executable) ban gayi. Yeh sabse zyada use hone wala chmod hai — nayi script banao, `chmod +x`
  karo, phir chalao (7.7).

**Aur misaalein:**
```
chmod u+x script.sh      # sirf owner ko execute do
chmod g-w file.txt       # group se write hatao (ab group badal nahi sakti)
chmod o-r secret.txt     # others se read hatao (baaki log padh nahi sakte)
chmod a+r public.txt     # sabko read do
```
- Padho: `u+x` = "owner ko execute do", `g-w` = "group se write hatao", `o-r` = "others se read
  hatao", `a+r` = "all ko read do". Seedha angrezi jaisa.

**Symbolic ka fayda:** padhne mein clear ("owner ko execute do"), aur sirf ek permission badalta —
baaki chhedta nahi. Jab ek chhota change chahiye (jaise `+x`), symbolic sabse aasaan.

> **Yaad rakhne wali baat:** `chmod [kaun][+/-][kya] file`. `chmod +x script.sh` = chalne-laayak
> banao (sabse common). `u/g/o/a` (kaun) + `+`/`-` (do/hatao) + `r/w/x` (kya). Symbolic = ek
> permission aasaani se badlo.

[↑ Back to top](#top)

---

<a id="s7-6"></a>
## 7.6 — `chmod` numbers ka raaz (`755`, `644` — yeh kahan se aate)

Aap `chmod 755 script.sh` bahut dekhoge. Yeh numbers pehli baar jaadu lagte, par inke peeche seedha
hisaab hai. Ek baar samajh gaye toh hamesha ke liye clear.

**Har permission ka ek number:**
- **`r` (read) = 4**
- **`w` (write) = 2**
- **`x` (execute) = 1**
- (Kuch nahi = 0)

**Ek group (owner/group/others) ki permission = un numbers ka JOD:**
- `rwx` = 4+2+1 = **7** (sab)
- `rw-` = 4+2+0 = **6** (read+write)
- `r-x` = 4+0+1 = **5** (read+execute)
- `r--` = 4+0+0 = **4** (sirf read)
- `---` = 0 (kuch nahi)

**Teen number = teen groups (owner, group, others):**
```
chmod 755 script.sh
```
- `7` (owner) `5` (group) `5` (others). Tod do:
  - `7` = `rwx` (owner: sab).
  - `5` = `r-x` (group: read+execute).
  - `5` = `r-x` (others: read+execute).
- Yeh `-rwxr-xr-x` ke barabar hai (7.4 wali string)! Numbers aur symbols do tareeke, same cheez.

**Do sabse common numbers (yaad rakh lo):**
- **`755`** = owner sab (`rwx`), baaki read+execute (`r-x`). **Scripts aur folders** ke liye standard
  (sab chala/dekh sakte, sirf owner badal sakta).
- **`644`** = owner read+write (`rw-`), baaki sirf read (`r--`). **Normal files/documents** ke liye
  standard (owner badle, baaki padhe).

**Numeric vs symbolic — kab kaunsa:**
- **Numeric (`755`):** poori permission ek saath set karni ho (teeno groups). Fast, exact. Scripts
  aur setup mein common.
- **Symbolic (`+x`):** sirf ek cheez badalni ho (jaise bs execute add). Aasaan aur clear.

> **Yaad rakhne wali baat:** `r`=4, `w`=2, `x`=1; ek group ki perm = jod. Teen number = owner/group/
> others. `755` = `rwxr-xr-x` (scripts/folders), `644` = `rw-r--r--` (files). Numeric = poora set
> ek saath; symbolic (`+x`) = ek cheez badlo.

[↑ Back to top](#top)

---

<a id="s7-7"></a>
## 7.7 — `./script.sh` mein `./` aur execute bit ka poora kaaran

Ab do puraani gutthiyaan ek saath suljhti hain — Chapter 2 ka `./` aur Chapter 7 ka `x` (execute).
Yeh sawaal har naye banda poochta hai: "apni script chalane ke liye `./script.sh` kyun? Sirf
`script.sh` kyun nahi?" — aur "Permission denied kyun aata hai?"

**Sawaal 1 — `./` kyun (yaad karo Ch 2.5 aur Ch 3.11):**
```
script.sh          # aksar: command not found
./script.sh        # sahi
```
- Jab aap `script.sh` (bina `./`) likhte ho, shell use **PATH ke folders mein dhoondhta** hai (Ch
  3.11) — `/bin`, `/usr/bin` etc. Aapki script current folder mein hai, PATH mein nahi — toh shell
  use nahi paata → `command not found`.
- **`./`** = "yehi folder" (Ch 2.5). `./script.sh` matlab "PATH mein mat dhoondho, yeh script **isi
  folder** mein hai — yahin se chalao". Ab shell ko exact jagah pata, chala deta.
- **Yeh security bhi hai:** agar current folder automatically PATH mein hota, toh koi kisi folder mein
  `ls` naam ki bburi script rakh deta aur aap `ls` chalate toh woh chal jati! `./` zaroori hone se
  aap jaan-boojh ke "yeh local script chala raha hoon" bolte ho.

**Sawaal 2 — `Permission denied` (execute bit):**
```
./script.sh
# bash: ./script.sh: Permission denied
```
- Yeh tab aata jab script pe **execute (`x`) permission nahi** hai (7.2). File chalne-laayak nahi
  hai — bs ek text file hai jismein commands likhe hain, par "chalne" ka nishaan (`x`) nahi.
- **Fix — `chmod +x` (7.5):**
```
chmod +x script.sh      # execute permission do
./script.sh             # ab chalegi
```
- `chmod +x` ne `x` bit laga di — ab file "executable" (chalne-laayak) hai, aur `./script.sh` chal
  jayega.

**Poora cycle (nayi script banane se chalane tak — yeh yaad rakho):**
```
nano script.sh          # 1. likho (Ch 8)
chmod +x script.sh      # 2. chalne-laayak banao (x bit)
./script.sh             # 3. chalao (./ = yahin se)
```
- Yeh teen step har baar jab aap nayi script banao. `chmod +x` + `./` — dono zaroori. (Alternative:
  `bash script.sh` — isme `x` bit ya `./` ki zaroorat nahi, kyunki aap seedha bash ko de rahe;
  par `./script.sh` "proper" tareeka hai — Ch 8 mein dekha.)

> **Yaad rakhne wali baat:** `./script.sh` — `./` (Ch 2.5) shell ko batata "PATH nahi, yehi folder"
> (warna command not found + security). `x` bit (`chmod +x`) file ko chalne-laayak banata (warna
> Permission denied). Nayi script: likho → `chmod +x` → `./chalao`.

[↑ Back to top](#top)

---

<a id="s7-8"></a>
## 7.8 — `chown` aur `chgrp` — maalik/group badalna

Permissions "kaun kya kar sakta" batati hain (7.2-7.6). Par "kaun owner/group hai" — woh bhi badla
ja sakta. Do commands:

**`chown` = **ch**ange **own**er (maalik badlo):**
```
sudo chown pragyesh notes.txt
```
- `notes.txt` ka owner ab `pragyesh` ban gaya. (`sudo` isliye — 7.9 — kyunki owner badalna aam taur
  pe admin ka kaam hai.)
- **Owner + group ek saath:**
```
sudo chown pragyesh:staff notes.txt
```
- `pragyesh:staff` = owner `pragyesh`, group `staff` (`:` se alag). Dono ek saath.

**`chgrp` = **ch**ange **gr**ou**p** (sirf group badlo):**
```
sudo chgrp developers project/
```
- `project/` folder ka group `developers` ban gaya — ab us group ke saare log group-permissions
  paate.

**Kab zaroori:** aksar server pe — jab ek file galat owner ki ban gayi (jaise root ne banayi par
aapko chahiye), ya ek folder ko ek team (group) ke saath share karna ho. Roz ke Mac use mein kam,
par server/production mein common.

**`-R` (recursive) — poore folder tree pe:**
```
sudo chown -R pragyesh:staff project/
```
- **`-R`** = recursive (Ch 3.8) — `project` aur uske andar ki har file/folder ka owner/group badlo.
  Poora tree ek saath. (Dhyan — galat jagah `-R chown` bahut kuch badal deta.)

> **Yaad rakhne wali baat:** `chown user file` = owner badlo, `chown user:group file` = dono. `chgrp
> group file` = sirf group. `-R` = poore folder tree pe. Aksar `sudo` chahiye (admin kaam). Server/
> sharing mein common.

[↑ Back to top](#top)

---

<a id="s7-9"></a>
## 7.9 — `sudo` — root banke kaam karna (aur khatra)

**`sudo`** = "**s**uper**u**ser **do**" — matlab "yeh command **root** (superuser/admin — Ch 1, Ch
2.1) ke roop mein chalao". Root woh sabse taakatvar account hai jo kuch bhi kar sakta — system files
badal sakta, kisi ki bhi file, sab kuch.

**Kab chahiye:** kuch kaam aam user (aap) nahi kar sakte kyunki permission nahi — system files
badalna, software install karna, doosron ki files chhedna. Wahan `sudo` laga ke aap "thodi der ke
liye root" ban jate ho.

```
sudo apt-get install nginx      # software install (root kaam)
sudo chown pragyesh file        # kisi file ka owner badalna
sudo nano /etc/hosts            # system config file edit (Ch 8)
```
- Har jagah `sudo` isliye — yeh kaam root-level hain, aam user ko permission nahi. `sudo` se woh
  permission mil jati (thodi der ke liye).
- **Password poochega:** `sudo` pehli baar aapka password maangta (confirm karne ko ki aap sach mein
  admin ho). Yeh security hai.

**KHATRA — `sudo` matlab saari safety hat gayi:** jab aap `sudo` lagate ho, aap root ban jate ho —
aur root ke liye koi rok-tok nahi. Ek galat `sudo rm -rf` poore system ko uda sakta (aam user hota
toh permission-denied se ruk jata; root ko koi nahi rokta). Isiliye:
1. **`sudo` sirf tab jab sach mein zaroori** — har command pe reflexively `sudo` mat lagao.
2. **`sudo` ke saath command do baar padho** — khaaskar `rm`, `chmod -R`, `>` (overwrite) ke saath.
3. **`sudo rm -rf /` ya kuch aisa kabhi nahi** (Ch 4.5 wala, par root ke saath aur ghatak).

**"Permission denied" ka matlab kabhi "sudo lagao" hota, kabhi nahi:** agar aap system file badalne
ki koshish mein denied ho rahe → shayad `sudo` chahiye. Par agar apni hi file pe denied → shayad
`chmod`/`chown` (7.5/7.8) issue hai, `sudo` nahi. Pehle socho kyun denied hua.

> **Yaad rakhne wali baat:** `sudo command` = us command ko root (admin) ke roop mein chalao — jab
> aam user ko permission nahi (install, system files). Password maangta. KHATRA: root ke liye koi
> rok nahi — `sudo` ke saath (khaaskar `rm -rf`) bahut dhyan se. Zaroori ho tabhi `sudo`.

[↑ Back to top](#top)

---

<a id="s7-10"></a>
## 7.10 — Nuances aur caveats

- **Mac aur Linux thoda alag:** Mac (aapka laptop) single-user jaisa feel deta, par andar se yehi
  permission system hai. Server (Linux) pe permissions roz zyada matter karti (multi-user). Concept
  same, par server pe aap inse zyada takraoge.

- **`chmod 777` — sabko sab kuch (khatarnak shortcut, mat karo):** `777` = owner+group+others sabko
  `rwx` (sab). Log "kaam nahi kar raha" ki frustration mein `chmod 777` maar dete hain — yeh security
  hole hai (koi bhi badal/chala sakta). Kabhi zaroorat na samajh ke `777` mat lagao — sahi permission
  socho (aksar `755` ya `644` kaafi).

- **Folder pe `x` na ho toh andar nahi ja sakte (chahe `r` ho):** yeh confuse karta — folder pe
  `r` (list dekho) hai par `x` (andar jao) nahi, toh `ls` toh chalega par `cd` nahi. Folder ke liye
  `x` "andar jaane" ka permission hai (7.2). Isiliye folders aksar `755` (jismein `x` hai).

- **Nayi script pe by default `x` nahi hota:** jab aap `nano script.sh` se nayi script banate ho, woh
  `644` (bina `x`) banti hai. Isiliye har nayi script pe `chmod +x` karna padta (7.7). Yeh bhoolna
  "Permission denied" ka #1 kaaran.

- **`sudo` ka password time-limited hota:** ek baar `sudo` password daala, toh kuch minute (aam taur
  5) tak dobara nahi maangta. Iske baad phir maangega. Yeh convenience + security ka balance.

- **Root/`#` prompt pe extra dhyan (Ch 1 wala):** agar prompt `#` dikha raha (root) toh aap already
  root ho — har command bina rok-tok chalegi. `$` (aam user) pe system aapko galtiyon se rokta;
  `#` pe nahi. `#` dekho toh double-careful.

- **`chown` khud ki file pe bhi aksar `sudo` maangta:** ajeeb lagta — apni file ka owner badalne ko
  bhi `sudo`? Kyunki owner badalna security-sensitive hai (aap kisi aur ko file "de" rahe), isliye
  system ise admin-kaam maanta.

[↑ Back to top](#top)

---

<a id="s7-11"></a>
## 7.11 — Real-life scenarios

**Scenario 1 — "Nayi script chalao, Permission denied."** Aapne `deploy.sh` likhi, `./deploy.sh`
chalaya — `Permission denied`. Ab aap jaante ho (7.7) — `x` bit nahi hai. `chmod +x deploy.sh`, phir
`./deploy.sh`. Yeh har developer roz face karta — nayi script = `chmod +x` zaroori.

**Scenario 2 — "Server pe file edit nahi ho rahi."** Aap ek config file (`/etc/nginx/nginx.conf`)
edit karne gaye — `nano` khula par save pe "read-only" ya permission error. Ab aap jaante ho (7.9) —
system file, aam user ko write nahi. `sudo nano /etc/nginx/nginx.conf` — ab root ke roop mein edit,
save ho jayega.

**Scenario 3 — "Team ke saath folder share karna."** Aapko ek project folder apni team (group
`developers`) ke saath share karna hai taaki sab padh-likh sakein. `sudo chgrp -R developers
project/` (group set, 7.8) + `chmod -R 775 project/` (group ko `rwx`, 7.6). Ab team ka har banda kaam
kar sakta.

**Scenario 4 — "`chmod 777` maarne wala tha, ruk gaya."** Kuch "kaam nahi kar raha" tha aur aap
frustration mein `chmod 777` maarne wale the. Ab aap jaante ho (7.10) — `777` = sabko sab (security
hole). Aapne socha kya *actually* chahiye — script chalani thi, toh `chmod +x` kaafi tha, `777`
nahi. Sahi permission = km se km jitni zaroori.

**Scenario 5 — "`ls -l` mein `d` aur `-` samajh nahi aa raha tha."** Ek folder ki listing dekhi aur
`drwxr-xr-x` vs `-rw-r--r--` confuse kiya. Ab aap padh sakte ho (7.4) — pehla `d` = folder, `-` =
file; agle 9 = owner/group/others ke rwx. Ek nazar mein pata "yeh folder hai, owner sab kar sakta,
baaki sirf dekh sakte".

**Saar:** Chapter 7 batata hai "kaun kya kar sakta" — `r`/`w`/`x` (kya) × owner/group/others (kaun).
`ls -l` se permissions padho, `chmod` (+x ya 755/644) se badlo, `chown`/`chgrp` se owner/group,
`sudo` se root-kaam. Do sabse practical: har nayi script pe `chmod +x` (7.7), aur `sudo` sirf zaroori
ho tab (bahut dhyan se, 7.9).

[↑ Back to top](#top)

---

> **Chapter 07 khatam.** Ab tak: permissions kyun (multi-user); teen kaam (`r`/`w`/`x`) aur file vs
> folder pe matlab; teen log (owner/group/others); `ls -l` string padhna; `chmod` symbolic (`+x`)
> aur numeric (`755`/`644`); `./script.sh` + execute bit ka poora kaaran; `chown`/`chgrp`; aur `sudo`
> (root-kaam + khatra). **Agla chapter (Ch 9):** conditions aur logic — `if/else`, `[ ]` vs `[[ ]]`,
> comparisons, `&&`/`||`. (Ch 8 file-editing hum pehle kar chuke.)

[↑ Back to top](#top)
