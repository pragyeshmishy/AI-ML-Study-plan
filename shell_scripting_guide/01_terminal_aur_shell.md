<a id="top"></a>
# Chapter 01 — Terminal, Shell, aur "yeh sab hota kya hai"

Yeh guide ka pehla chapter hai. Yahan hum bilkul zero se shuru kar rahe hain — maan ke chal rahe
hain ki aapne kabhi "black screen wala terminal" theek se samjha nahi. Is chapter ke baad aapko
pata hoga: terminal kya hai, shell kya hai, kernel kya hai, yeh sab ek doosre se kaise jude hain,
kitne tarah ke terminal/shell hote hain, aur **kis scenario mein kaunsa use karna chahiye**.

Yeh chapter **theory-heavy** hai jaan-bujh ke — kyunki agar yeh neev (foundation) clear ho gayi,
toh aage ke saare commands "ratta" nahi lagenge, samajh aayenge.

---

## Is chapter ka index

- [1.1 — Sabse pehle badi tasveer: computer se baat kaise hoti hai](#s1-1)
- [1.2 — Kernel kya hai (OS ka dil)](#s1-2)
- [1.3 — Shell kya hai (aapka translator)](#s1-3)
- [1.4 — Terminal kya hai (shell ki khidki)](#s1-4)
- [1.5 — Teeno ka rishta ek tasveer mein](#s1-5)
- [1.6 — Terminal vs Shell vs Console vs Prompt — naam ki confusion](#s1-6)
- [1.7 — Kitne tarah ke shell hote hain (bash, zsh, sh, fish...)](#s1-7)
- [1.8 — Kitne tarah ke terminal (emulator) hote hain](#s1-8)
- [1.9 — Kis scenario mein kya use karein (decision guide)](#s1-9)
- [1.10 — Aap abhi kaunsa shell/terminal chala rahe ho — kaise pata karein](#s1-10)
- [1.11 — Prompt ko padhna seekho (`user@host:~$` ka matlab)](#s1-11)
- [1.12 — Nuances aur caveats (bareek baatein jo log miss karte hain)](#s1-12)
- [1.13 — Real-life scenarios (yeh sab kahan kaam aata hai)](#s1-13)

---

<a id="s1-1"></a>
## 1.1 — Sabse pehle badi tasveer: computer se baat kaise hoti hai

Socho aapko computer se koi kaam karvana hai — jaise "meri saari files dikhao" ya "yeh folder
delete karo". Aap yeh kaam do tareeke se keh sakte ho:

1. **GUI se** — GUI (Graphical User Interface — matlab woh screen jisme icons, buttons, mouse se
   click karte ho). Jaise aap Finder/File Explorer kholke folder pe double-click karte ho.
2. **CLI se** — CLI (Command Line Interface — matlab text likhke command dena, mouse nahi). Jaise
   aap type karte ho `ls` aur enter dabate ho, aur saari files list ho jaati hain.

Yeh guide poori CLI ke baare mein hai — text likhke computer se kaam karwana.

**Ab ek zaroori baat:** jab aap CLI mein koi command likhte ho, woh command *seedhe* computer ke
hardware (CPU, memory, disk) tak nahi jaati. Beech mein kai "parat" (layers) hote hain jo aapki
baat ko translate karke aage bhejte hain. In parton ko samajhna hi is chapter ka asli maqsad hai.

Teen sabse important parat hain: **Kernel**, **Shell**, aur **Terminal**. Inhe ek-ek karke
kholte hain — aur analogy (roz-marra ki misaal) se samajhte hain taaki clear ho jaaye.

[↑ Back to top](#top)

---

<a id="s1-2"></a>
## 1.2 — Kernel kya hai (OS ka dil)

**Kernel** (uchcharan: "karnal" — matlab kisi cheez ka sabse andar ka core hissa) — yeh Operating
System (OS — jaise Linux, macOS, Windows) ka sabse andar wala, sabse important hissa hai.

Kernel ka kaam: **hardware ko control karna aur software ki request ko hardware tak pahunchana.**
Matlab jab kisi program ko file disk se padhni hai, ya memory chahiye, ya CPU pe kuch chalana hai —
woh seedhe hardware ko nahi bolta. Woh kernel se *request* karta hai, aur kernel actually hardware
se kaam karwata hai.

**Analogy (misaal):** socho ek bade office mein ek store-room hai jisme saara zaroori saamaan
(hardware — CPU, memory, disk) rakha hai. Aam log store-room mein ghus nahi sakte (kyunki gadbad ho
jaayegi). Ek **store-keeper (kernel)** hai jo store-room ko sambhalta hai. Aapko kuch chahiye toh
aap store-keeper ko bolte ho, woh laake deta hai. Kernel woh store-keeper hai — hardware ka akela
malik, jo sabki request handle karta hai.

**Aap kernel se seedhe baat nahi karte** — yeh important hai. Kernel bahut andar hai, technical hai.
Aapko ek "translator" chahiye jo aapki simple baat ko kernel ki bhasha mein badle. Woh translator
hi **shell** hai (agla section).

> **Yaad rakhne wali baat:** Kernel = OS ka core jo hardware chalata hai. Aap ise directly touch
> nahi karte; aapki commands shell ke through ghoom ke kernel tak pahunchti hain.

[↑ Back to top](#top)

---

<a id="s1-3"></a>
## 1.3 — Shell kya hai (aapka translator)

**Shell** (matlab "khol" ya "aavaran" — jaise anda ka bahri chhilka) — yeh ek **program** hai jo
aapki type ki hui command leta hai, use samajhta hai, aur kernel se woh kaam karwata hai. Phir
result (natija) wapas aapko dikhata hai.

Ise "shell" (khol) isliye kehte hain kyunki yeh kernel ke *upar ek parat* ki tarah baitha hai —
kernel andar, shell bahar. Aap bahar wali parat (shell) se baat karte ho, woh andar (kernel) tak
pahunchati hai.

**Shell exactly kya karta hai (step by step):**
1. Aap kuch type karte ho, jaise `ls` — aur Enter dabate ho.
2. Shell us text ko padhta hai (ise "parse karna" kehte hain — matlab tod ke samajhna).
3. Shell dhoondhta hai ki `ls` naam ka program kahan hai.
4. Shell kernel se bolta hai "yeh program chalao".
5. Program chalta hai, output banta hai.
6. Shell woh output aapki screen pe dikha deta hai.
7. Phir se ready — agli command ke liye (yeh "prompt" dikhata hai — section 1.11).

**Analogy:** shell ek **waiter (bearer)** hai restaurant mein. Aap (user) waiter ko order dete ho
("do roti, ek dal"). Waiter kitchen (kernel + hardware) tak order pahunchata hai, khaana banwata
hai, aur plate aapke saamne laake rakhta hai. Aap kitchen mein khud nahi ghuste — waiter beech mein
hai. Shell wahi waiter hai.

**Zaroori baat — shell sirf ek "translator" nahi, ek poori bhasha (language) hai.** Aap shell ko
sirf `ls` jaise chhote commands nahi, balki poore *programs* likhke de sakte ho — variables,
loops (baar-baar chalne wali cheez), conditions (agar-toh) ke saath. Jab aap yeh sab ek file mein
likhke save karte ho, use **shell script** kehte hain (aage ke chapters). Isiliye ise "shell
scripting" kehte hain.

> **Yaad rakhne wali baat:** Shell = woh program jo aapki command samajhke kernel se karwata hai
> aur result dikhata hai. Yeh ek programming language bhi hai (isi se scripts banti hain).

[↑ Back to top](#top)

---

<a id="s1-4"></a>
## 1.4 — Terminal kya hai (shell ki khidki)

Ab confusion yahaan hoti hai — log "terminal" aur "shell" ko ek hi samajh lete hain. Yeh alag hain.

**Terminal** (poora naam: terminal emulator — matlab "nakal karne wala") — yeh woh **window
(khidki/app)** hai jisme aap type karte ho aur text dekhte ho. Yeh bas ek *khaali dibba* hai jisme
shell chalta hai. Terminal ka kaam: aapse text lena (keyboard) aur text dikhana (screen). Bas.

Terminal khud kuch "samajhta" nahi — woh sirf aapke keyboard ka input shell ko deta hai, aur shell
ka output screen pe dikhata hai. Asli dimaag shell ka hai; terminal sirf khidki hai.

**Yeh "emulator" kyun kehlata hai?** Purane zamane mein (1970s) actual physical machine hoti thi —
ek keyboard + screen jo bade computer se tar (wire) se judi hoti thi — use "terminal" kehte the.
Aaj woh hardware nahi hai; aapke laptop pe ek *software* us purane hardware ki **nakal (emulate)**
karta hai. Isiliye "terminal emulator" — purane terminal ki nakal karne wala app.

**Analogy:** terminal ek **TV ka dibba (screen + remote)** hai. Shell woh **channel/program** hai
jo us TV pe chal raha hai. TV (terminal) toh bas dikhane aur input lene ka zariya hai — asli content
(shell) alag cheez hai. Aap alag-alag TV (terminal apps) pe wahi channel (shell) chala sakte ho.

**Ek line mein farak:**
- **Terminal** = khidki/app jahan aap type karte ho (dikhne aur type karne ka zariya).
- **Shell** = us khidki ke andar chalne wala program jo aapki command ka matlab samajhta hai.

> **Yaad rakhne wali baat:** Terminal = khidki (app). Shell = us khidki ke andar chalne wala
> "dimaag". Ek terminal ke andar koi bhi shell chal sakta hai (bash, zsh, etc.).

[↑ Back to top](#top)

---

<a id="s1-5"></a>
## 1.5 — Teeno ka rishta ek tasveer mein

Ab teeno (terminal, shell, kernel) ko ek saath dekhte hain — aapki command ka poora safar:

```
   AAP (user)
     │  type: ls -l   (aur Enter)
     ▼
 ┌───────────────────────────────────────────────┐
 │  TERMINAL (khidki/app — jaise iTerm, Terminal) │   ← sirf text lena/dikhana
 │    keyboard input  ───►                         │
 │                    ◄───  screen output          │
 │   ┌─────────────────────────────────────────┐  │
 │   │  SHELL (bash / zsh — command samajhta)   │  │   ← command parse + program dhundhna
 │   │      "ls -l ka matlab kya hai?"          │  │
 │   │              │  kernel se request        │  │
 │   │              ▼                            │  │
 │   │   ┌───────────────────────────────────┐  │  │
 │   │   │  KERNEL (hardware ka malik)        │  │  │   ← disk/CPU/memory chalata
 │   │   │   disk se file list nikaalo        │  │  │
 │   │   └───────────────┬───────────────────┘  │  │
 │   │       result ◄────┘                       │  │
 │   └─────────────────────────────────────────┘  │
 │       output text screen pe   ◄────             │
 └───────────────────────────────────────────────┘
     │
     ▼
   AAP output dekhte ho
```

**Safar padho (upar se neeche, phir wapas):** Aap terminal mein type karte ho → terminal woh text
shell ko deta hai → shell samajhta hai aur kernel se kaam karwata hai → kernel hardware (disk) se
kaam karke result deta hai → shell result ko format karta hai → terminal use screen pe dikhata hai.

**Yeh tasveer poore guide ki neev hai.** Jab bhi aage koi command chale aur samajh na aaye ki "yeh
kahan ho raha hai", is tasveer pe wapas aana.

> **Yaad rakhne wali baat:** Aap → Terminal (khidki) → Shell (dimaag) → Kernel (hardware-malik) →
> hardware. Aur result ulti taraf wapas. Teen alag cheezein, ek chain mein judi.

[↑ Back to top](#top)

---

<a id="s1-6"></a>
## 1.6 — Terminal vs Shell vs Console vs Prompt — naam ki confusion

Log in shabdon ko aapas mein mila dete hain. Chaliye har ek ko saaf kar dete hain, taaki jab koi
senior bole "terminal khol ke command maar" toh aapko exact pata ho kya-kya ho raha hai.

| Shabd | Asli matlab | Aam bol-chaal mein |
|---|---|---|
| **Terminal** | Woh app/khidki jisme aap type karte ho (terminal emulator) | "terminal khol" = app khol |
| **Shell** | Us khidki ke andar chalne wala command-samajhne wala program (bash/zsh) | Aksar "terminal" bol dete hain isko bhi (technically galat) |
| **Console** | Purane zamane mein: physical screen+keyboard jo seedhe machine se juda ho. Aaj: aksar "terminal" ka hi doosra naam | "console" ≈ terminal (modern use mein) |
| **Command line / CLI** | Text likhke command dene ka poora tareeka (concept) | "command line pe kar le" = CLI use kar |
| **Prompt** | Woh text jo shell dikhata hai jab woh aapki command ke liye ready hai (jaise `user@mac:~$`) | "prompt pe likh" = jahan cursor blink kar raha |
| **Bash / Zsh / sh** | Shell ke *specific naam/types* (brands ki tarah) | "bash script" = bash shell ke liye likhi script |

**Ek line mein:** Terminal woh dibba hai, shell us dibbe ka dimaag hai, prompt woh nishani hai ki
shell ready hai, aur bash/zsh shell ke brand-naam hain. "Console" aur "command line" aksar terminal
ke hi doosre naam ki tarah use hote hain.

**Caveat (savdhani):** rozmarra ki baat-cheet mein log "terminal" aur "shell" ko interchangeably
(ek doosre ki jagah) bol dete hain — aur usually koi problem nahi hoti. Par jab aapko problem
debug karni ho ("mera command bash mein chalta hai zsh mein nahi") — tab yeh farak samajhna zaroori
ho jata hai.

[↑ Back to top](#top)

---

<a id="s1-7"></a>
## 1.7 — Kitne tarah ke shell hote hain (bash, zsh, sh, fish...)

Shell ek hi type ka nahi hota — kai "brands" hain, jaise gaadi ke alag-alag brand. Sabka basic
kaam same (command samajhna) par syntax (likhne ka tareeka) aur features thode alag. Yeh jaanna
zaroori hai kyunki ek shell ki script doosre mein kabhi-kabhi nahi chalti.

| Shell | Poora naam | Khaasiyat | Kahan default milta hai |
|---|---|---|---|
| **sh** | Bourne Shell (Posix sh) | Sabse purana, minimal, har jagah chalta hai. "Lowest common denominator" (sabse basic jo sab jagah kaam kare). | Purane Unix, Alpine Linux (chhota Docker image) |
| **bash** | Bourne Again Shell | sh ka upgrade — variables, arrays, `[[ ]]`, bahut features. **Industry ka default** scripting ke liye. | Zyadatar Linux servers, Git Bash (Windows) |
| **zsh** | Z Shell | bash jaisa par aur powerful interactive features (autocomplete, themes jaise "Oh My Zsh"). | **macOS ka default** (2019 ke baad) |
| **fish** | Friendly Interactive Shell | Bahut user-friendly, colorful, auto-suggest. Par syntax bash se alag — scripts portable nahi. | Alag se install karna padta |
| **dash** | Debian Almquist Shell | Bahut fast aur light, sirf POSIX. Ubuntu mein `/bin/sh` actually dash hai. | Ubuntu/Debian ka `/bin/sh` |

**Sabse important teen aapke liye:**
- **bash** — production servers, Docker, CI/CD (automatic build/test system) — sab jagah. **Scripts
  isi mein likhna sabse safe hai.**
- **zsh** — aapke Mac pe interactive use ke liye default (jab aap khud type karke kaam karte ho).
- **sh** — jab script ko *har jagah* chalna ho (maximum portability — matlab kisi bhi system pe
  chal jaaye), tab sh mein likhte hain.

**bash vs zsh — asli farak (aapke liye khaas, kyunki aap Mac pe ho par servers bash hain):**
- **Interactive (khud type karne mein):** zsh behtar — behtar autocomplete (Tab dabane pe smart
  suggestions), themes, plugins. Isiliye Mac pe zsh default hai.
- **Scripting (file mein likhke chalana):** bash zyada universal. Server pe zsh shayad installed
  bhi na ho. Isiliye **scripts hamesha `#!/bin/bash` (ya `#!/bin/sh`) se likho**, zsh se nahi —
  taaki server pe chal jaayein.
- **Chhote syntax farak:** jaise arrays mein index zsh mein 1 se shuru, bash mein 0 se. Ya
  `echo` ka behaviour thoda alag. Yeh aage ke chapters mein aayenge; abhi bas itna jaan lo ki
  **"mere Mac (zsh) pe chala, server (bash) pe nahi chala" — yeh real problem hai** aur iska
  kaaran yehi shell-difference hai.

**Example scenario:** aapne Mac pe (zsh) ek script banayi jisme aapne zsh ka koi feature use kar
liya. Aapne wahi script company ke Linux server (bash) pe bheji — aur woh error de gayi. Kyun?
Kyunki woh feature bash mein tha hi nahi. **Solution:** script ke top pe `#!/bin/bash` likho aur
bash-compatible syntax use karo — phir dono jagah chalegi.

> **Yaad rakhne wali baat:** Shell ke brands hain — sh (basic/portable), bash (default scripting),
> zsh (Mac interactive), fish (friendly par non-portable). **Scripts bash/sh mein likho** taaki
> server pe chalein; interactive use jo marzi (zsh theek hai).

[↑ Back to top](#top)

---

<a id="s1-8"></a>
## 1.8 — Kitne tarah ke terminal (emulator) hote hain

Jaise shell ke brands hote hain, waise hi terminal (khidki wala app) ke bhi kai brands hain. Yaad
rakho — **terminal sirf khidki hai**, uska "brand" badalne se aapki command ka result nahi badalta,
sirf khidki ka look/feel aur convenience badalti hai (jaise tabs, colours, split-screen).

| Terminal (app) | Kis OS pe | Khaasiyat |
|---|---|---|
| **Terminal.app** | macOS (built-in) | Simple, pehle se installed. Kaam chala lega par basic. |
| **iTerm2** | macOS | Bahut popular — tabs, split panes (ek khidki mein kai hisse), search, colours. Power users ki pehli pasand. |
| **Warp** | macOS/Linux | Naya, modern — AI help, blocks mein output. Fancy. |
| **GNOME Terminal / Konsole** | Linux (desktop) | Linux desktops ke built-in terminals. |
| **Windows Terminal** | Windows | Microsoft ka naya terminal — WSL (Windows pe Linux), PowerShell, sab ek jagah. |
| **PuTTY** | Windows (purana) | Sirf remote server se connect karne (SSH) ke liye zyada use hota tha. |
| **VS Code ka integrated terminal** | Sab | Aapke code editor (VS Code) ke andar hi ek terminal — code aur command ek saath. (Aap abhi shayad yehi use kar rahe ho.) |

**Zaroori samajh:** in sab apps ke andar aap **koi bhi shell** chala sakte ho. Jaise iTerm2 (Mac
terminal) ke andar aap zsh bhi chala sakte ho aur bash bhi. Terminal (khidki) aur shell (dimaag)
alag-alag choose hote hain. Ek analogy: terminal = mobile phone ka brand (Samsung/Apple), shell =
usme chalne wala app (WhatsApp/Telegram). Phone koi bhi ho, app koi bhi chal sakta hai.

**Example:** aap VS Code ka integrated terminal (ek terminal emulator) kholte ho, aur uske andar
by-default aapka Mac ka zsh chal raha hai. Aap chaho toh usi VS Code terminal mein `bash` type
karke bash pe switch kar sakte ho — khidki wahi rahegi, dimaag badal jaayega.

> **Yaad rakhne wali baat:** Terminal app ka brand (iTerm/Terminal/VS Code) sirf convenience
> (look, tabs, split) badalta hai — command ka result nahi. Kisi bhi terminal ke andar koi bhi
> shell chal sakta hai.

[↑ Back to top](#top)

---

<a id="s1-9"></a>
## 1.9 — Kis scenario mein kya use karein (decision guide)

Ab practical sawaal — "mujhe kaunsa terminal aur kaunsa shell use karna chahiye?" Scenario ke
hisaab se:

**Shell chunne ka guide:**

| Scenario | Kaunsa shell | Kyun |
|---|---|---|
| Mac pe roz ka interactive kaam (khud type karke) | **zsh** (Mac ka default) | Behtar autocomplete/themes; already set hai |
| Ek script likhni hai jo *aapke aur doosron ke* servers pe chale | **bash** (`#!/bin/bash`) | Sab jagah milta hai, universal |
| Script ko *maximum jagah* chalna ho (Alpine Docker, purane systems) | **sh** (`#!/bin/sh`) | Sabse portable; har system pe hota hai |
| Docker image chhota (Alpine) hai | **sh** | Alpine mein bash hota hi nahi by default |
| Bahut fancy interactive experience chahiye, portability ki parwah nahi | **fish** | Sabse friendly, par scripts portable nahi |

**Terminal chunne ka guide:**

| Scenario | Kaunsa terminal | Kyun |
|---|---|---|
| Code likhte-likhte command chalana | **VS Code integrated terminal** | Code + command ek jagah, switch nahi karna |
| Mac pe serious terminal kaam (kai tabs/panes) | **iTerm2** | Split panes, search, profiles |
| Bas jaldi ek command chalani | **Terminal.app** (built-in) | Kholne mein fast, kuch install nahi karna |
| Remote server pe kaam (SSH) | Koi bhi + `ssh` command | Terminal sirf khidki; asli kaam SSH karta hai (Ch 16) |

**Sabse zaroori practical salah (aapke context ke liye):** aap ek ML engineer ho jo Mac pe kaam
karta hai par production Linux servers (bash) pe. Toh:
- **Interactive kaam:** Mac pe zsh + VS Code terminal ya iTerm2 — jo comfortable lage.
- **Koi bhi script/automation:** hamesha `#!/bin/bash` se likho (ya `#!/bin/sh` agar Alpine/portable
  chahiye) — taaki woh server aur Docker dono jagah bina badle chal jaaye. Yeh ek aadat (habit)
  bana lo — bahut si "mere machine pe chala tha" wali problems yahin ruk jaati hain.

> **Yaad rakhne wali baat:** Interactive = zsh (Mac) theek. Scripts/automation = bash ya sh
> (portable). Terminal app apni pasand se (iTerm/VS Code). Rule: script hamesha bash/sh mein
> likho, chahe aap zsh pe ho.

[↑ Back to top](#top)

---

<a id="s1-10"></a>
## 1.10 — Aap abhi kaunsa shell/terminal chala rahe ho — kaise pata karein

Theory kaafi ho gayi — ab do minute ka practical. Terminal kholke yeh commands chalao (type karo,
Enter dabao) aur dekho. Har command ke saath bataya hai output kaisa hoga aur uska matlab.

**1. Kaunsa shell chal raha hai abhi?**

```
echo $SHELL
```

- **Kya type kiya:** `echo $SHELL` — `echo` matlab "screen pe dikhao", `$SHELL` ek variable
  (dabba jisme value rakhi hai) jo aapke default shell ka path rakhta hai.
- **Output kaisa (Mac pe aksar):** `/bin/zsh`
- **Matlab:** aapka default shell zsh hai, jiska program `/bin/zsh` file mein hai.
- **Agar output** `/bin/bash` **aaye** → aapka default bash hai.

**Caveat (savdhani):** `$SHELL` aapka *default (login)* shell dikhata hai — zaroori nahi ki abhi
isi ke andar ho. Aapne beech mein `bash` type karke switch kiya ho toh `$SHELL` phir bhi purana
dikhaega. **Abhi actually kaunsa chal raha** — yeh dekhne ko:

```
echo $0
```

- **Output:** `-zsh` ya `zsh` ya `bash` — jo abhi *actually* chal raha hai.
- **Matlab:** `$0` current chalne wale shell ka naam rakhta hai. Yeh zyada bharosemand hai
  "abhi kya chal raha" ke liye.

**2. Bash ka version kya hai?**

```
bash --version
```

- **Output (pehli line):** `GNU bash, version 5.2.15 ...`
- **Matlab:** aapke paas bash version 5.2.15 hai. Version isliye matter karta hai kyunki naye
  features purane version mein nahi hote (Mac pe aksar bahut *purana* bash 3.2 hota hai — licensing
  wajah se — yeh ek famous caveat hai).

**3. Doosre shell mein switch karke dekhna (aur wapas aana):**

```
bash
```

- **Kya hua:** aap ek naye bash shell ke *andar* chale gaye (purana zsh peeche chal raha hai).
  Prompt thoda badal sakta hai. Ab `echo $0` karoge toh `bash` dikhega.
- **Wapas jaane ko:** `exit` type karo — aap phir apne zsh mein aa jaoge.

```
exit
```

**Ek chhota experiment (samajh pakki karne ko):** `bash` type karo → `echo $0` (dikhega `bash`) →
`exit` → `echo $0` (dikhega `zsh`). Isse aapko *khud dikh jaayega* ki terminal (khidki) wahi rahi,
par uske andar ka shell (dimaag) badla aur wapas aaya. Yeh section 1.4-1.5 ka live proof hai.

> **Yaad rakhne wali baat:** `echo $SHELL` = default shell. `echo $0` = abhi actually chal raha
> shell. `bash`/`zsh` type karke switch, `exit` se wapas. Version dekhne ko `bash --version`.

[↑ Back to top](#top)

---

<a id="s1-11"></a>
## 1.11 — Prompt ko padhna seekho (`user@host:~$` ka matlab)

Jab aap terminal kholte ho, cursor ke pehle kuch text hota hai jaise:

```
pragyesh@macbook ~/Downloads/tutorial %
```

Ise **prompt** (nishani ki shell ready hai) kehte hain. Yeh khud shell dikhata hai — yeh koi command
nahi, na hi aapko ise type karna hai. Yeh aapko *jaankari* deta hai. Har hissa padho:

```
pragyesh @ macbook  :  ~/Downloads/tutorial   %
   │        │            │                     │
   │        │            │                     └─ "prompt symbol" — ready ho, type karo
   │        │            └─ current directory (abhi aap kaunse folder mein ho)
   │        └─ hostname (computer ka naam)
   └─ username (kaun logged in hai)
```

- **username** (`pragyesh`) — kaun user abhi chal raha hai.
- **hostname** (`macbook`) — kaunse computer pe ho (remote server pe ho toh yahaan server ka naam
  dikhega — bahut kaam ka jab kai servers pe kaam ho, taaki galat machine pe command na maar do).
- **directory** (`~/Downloads/tutorial`) — abhi aap kaunse folder mein khade ho. `~` matlab aapki
  home directory (aapka apna personal folder, jaise `/Users/pragyesh`).
- **prompt symbol** — yeh sabse important nishani:
  - `$` → aap ek **aam user** ho (bash mein typical).
  - `%` → zsh ka default symbol (aam user).
  - `#` → **savdhan!** aap **root** (superuser — sabse taakatvar admin account) ho. `#` dikhe toh
    dhyan se — root koi bhi cheez delete/badal sakta hai, galti mahangi padti hai.

**Scenario — `$` vs `#` kyun important:** maan lo aap ek server pe ho aur prompt `#` dikha raha hai
(matlab root ho). Aapne galti se `rm -rf /` jaise koi khatarnak command maar diya — root hone ki
wajah se system tabah ho sakta hai. Agar aap aam user (`$`) hote, toh system aapko rokta ("permission
denied"). **Isiliye `#`/root pe hamesha extra dhyan.** (Permissions ka poora chapter aage — Ch 07.)

**Caveat:** prompt ka look **customizable** hai — log ise badal lete hain (rang, git branch, time
dikhane ke liye). Toh har kisi ka prompt alag dikh sakta hai. Ghabrao mat — underlying jaankari
(user, host, directory, `$`/`#`) wahi rehti hai, bas sajawat alag.

> **Yaad rakhne wali baat:** Prompt = shell ka "ready" signal + jaankari (kaun user, kaunsa
> computer, kaunsa folder). `$`/`%` = aam user, `#` = root (savdhan!). Prompt aap type nahi karte,
> woh aapko batata hai.

[↑ Back to top](#top)

---

<a id="s1-12"></a>
## 1.12 — Nuances aur caveats (bareek baatein jo log miss karte hain)

Yeh woh chhoti-chhoti baatein hain jo shuru mein confuse karti hain, aur agar pehle se pata ho toh
bahut waqt bachta hai.

- **"Terminal band kiya toh mera chal raha kaam bhi ruk gaya" — kyun?** Jab aap terminal band karte
  ho, uske andar chal rahe program ko aksar ek "band ho jao" signal (SIGHUP — hang-up signal)
  milta hai aur woh ruk jata hai. Isiliye lambe chalne wale kaam ke liye `nohup` ya `tmux`/`screen`
  (session ko zinda rakhne wale tools) use karte hain (Ch 13/16 mein). Abhi bas yeh jaan lo ki
  "terminal = program ka ghar; ghar toda toh program bhi gaya" (jab tak special intezam na ho).

- **login shell vs non-login, interactive vs non-interactive** — shell alag "modes" mein chalta
  hai. Jab aap terminal kholte ho toh "interactive login shell". Jab koi script chalti hai toh
  "non-interactive". Iska asar yeh hota hai ki *kaunsi settings file* padhi jaati hai (`.bashrc`,
  `.bash_profile`, `.zshrc` — Ch 16). Abhi sirf itna: "mere alias/setting terminal mein kaam karti
  hai par script mein nahi" — iska kaaran yehi mode-farak hai.

- **Mac ka bash bahut purana hai (version 3.2).** Apple ne licensing (kanooni) wajah se naya bash
  nahi diya. Toh Mac pe `bash` shayad 2007 wala ho. Naye features chahiye toh Homebrew (Mac ka
  package installer) se naya bash install karna padta hai. Server pe (Linux) yeh dikkat nahi.

- **`$SHELL` badalta nahi jab aap temporarily `bash` type karte ho.** (1.10 mein dekha) — yeh
  default batata hai, current nahi. Current ke liye `$0`. Yeh farak debugging mein bachata hai.

- **Terminal ka "brand" result nahi badalta, par settings badal sakti hain.** Jaise ek terminal
  UTF-8 (emoji/hindi dikhane wala format) support kare, doosra na kare — toh output ka *dikhna*
  alag ho sakta, par command ka *kaam* wahi. Colours/encoding terminal ki settings hain.

- **Copy-paste ka dhyan:** terminal mein `Ctrl+C` "copy" nahi hai — woh chal rahe program ko **rokne
  (interrupt)** ka signal hai! Copy ke liye Mac pe `Cmd+C`, paste `Cmd+V`. Yeh ek bahut common
  naye-log ki galti hai — `Ctrl+C` maar dete hain aur program band ho jata hai.

- **Command "atak" gayi lage toh:** kabhi aap koi command chalate ho aur kuch nahi hota, cursor bas
  blink karta hai. Do possibility: (1) program kaam kar raha hai (wait karo), ya (2) woh aapse input
  maang raha hai. Nikalne ka tareeka: `Ctrl+C` (rok do) ya `q` (kai viewers `q` se band hote hain,
  jaise `less`/`man`).

[↑ Back to top](#top)

---

<a id="s1-13"></a>
## 1.13 — Real-life scenarios (yeh sab kahan kaam aata hai)

Ab jodte hain — yeh saari theory asli kaam mein kahan lagti hai. (Yeh section har chapter ke ant
mein aayega — "topic cover karne ke baad, yeh kin situations mein use hota hai".)

**Scenario 1 — "Mere laptop pe chala, server pe nahi chala."** Aapne Mac (zsh) pe ek script banayi
aur woh company ke Linux server (bash) pe error de gayi. Ab aap *jaante ho* kyun — shell alag hai
(1.7). Solution: script ke top pe `#!/bin/bash` likho aur bash-compatible syntax use karo. Yeh sabse
common real problem hai aur iska root Chapter 1 ki samajh hai.

**Scenario 2 — "Galat server pe command maar di."** Aap ek saath 3 servers pe SSH se jude ho (3
terminal tabs). Aapko ek command sirf test-server pe chalani thi par galti se production pe maar di.
Bachne ka tareeka: **prompt padho** (1.11) — hostname dekho (`user@prod-server` vs `user@test-server`)
command chalane se *pehle*. Prompt padhne ki aadat bade nuksaan bachati hai.

**Scenario 3 — "Root pe galti se kuch delete kiya."** Prompt `#` dikha raha tha (root), aapne dhyan
nahi diya aur ek delete command chala di — system ka zaroori file udd gaya. Ab aap `$` vs `#` ka
farak jaante ho (1.11) — `#` dikhe toh har command double-check.

**Scenario 4 — "Docker image mein `bash: not found` aa gaya."** Aapne Dockerfile mein `RUN bash ...`
likha par image Alpine (chhota Linux) tha jisme bash hota hi nahi — sirf `sh`. Ab aap jaante ho
(1.7, 1.9) — Alpine pe `sh` use karo ya bash install karo. Yeh Chapter 15 (command-writing) mein
detail mein aayega, par samajh yahin se aayi.

**Scenario 5 — "Lamba training job terminal band karte hi ruk gaya."** Aapne ek ML training script
terminal mein chalaya, laptop band kiya, wapas aaye toh job ruk chuki thi. Ab aap jaante ho (1.12) —
terminal band = program ko hang-up signal. Solution: `nohup`, `tmux`, ya server pe background job
(Ch 13). Samajh Chapter 1 se.

**In sabka saar:** Chapter 1 koi command nahi sikhata — yeh **soch (mental model)** deta hai. Jab
aage commands aayenge, yeh model aapko bataega ki "yeh kahan, kis parat pe, kis shell mein ho raha
hai" — aur 80% confusion yahin khatam ho jaati hai.

[↑ Back to top](#top)

---

> **Chapter 01 khatam.** Ab tak: terminal (khidki), shell (dimaag), kernel (hardware-malik) ka farak;
> shell ke types (bash/zsh/sh) aur kab kaunsa; terminal ke types; apna shell pata karna; prompt
> padhna; aur real scenarios. **Agla chapter (jab aap approve karo):** filesystem aur navigation —
> `/`, `~`, `pwd`, `cd`, aur `ls` ka poora deep-dive (har flag: `-l -a -t -r -h`, aur `-ltr` kyun).

[↑ Back to top](#top)
