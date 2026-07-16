<a id="top"></a>
# Chapter 16 — Handy Tools aur Cheat-Sheet (roz kaam aane wale)

Yeh chapter woh **extra tools** cover karta jo roz kaam aate par ab tak nahi aaye — files zip karna
(`tar`), internet se cheezein laana (`curl`/`wget`), doosre server se judna (`ssh`), files sync karna
(`rsync`), aur apne shell ko customize karna (aliases, `.bashrc`). Aakhir mein ek **decision
cheat-sheet** — "yeh chahiye toh yeh command".

Yeh reference-style chapter hai — har tool ka core + kab use. Poora Ch 1-15 ki neev pe.

---

## Is chapter ka index

- [16.1 — `tar` — files ko ek bundle mein (zip/archive)](#s16-1)
- [16.2 — `curl` aur `wget` — internet se cheezein laana](#s16-2)
- [16.3 — `ssh` — doosre computer/server se judna](#s16-3)
- [16.4 — `scp` aur `rsync` — files transfer/sync karna](#s16-4)
- [16.5 — `tmux` — session jo terminal band pe bhi zinda](#s16-5)
- [16.6 — Aliases — chhote naam badi command ke liye](#s16-6)
- [16.7 — History aur shortcuts (`!!`, `Ctrl+R`, arrow)](#s16-7)
- [16.8 — `cron` — commands ko schedule karna](#s16-8)
- [16.9 — Decision cheat-sheet ("yeh chahiye → yeh command")](#s16-9)
- [16.10 — Nuances aur caveats](#s16-10)
- [16.11 — Real-life scenarios](#s16-11)

---

<a id="s16-1"></a>
## 16.1 — `tar` — files ko ek bundle mein (zip/archive)

**`tar`** = "**t**ape **ar**chive" (purana naam, jab tapes pe backup hote the). Yeh kai files/folders
ko **ek single file** mein bundle karta (aur aksar compress bhi) — jaise ek suitcase mein saara saaman.
Backup, transfer, aur download mein bahut use hota (`.tar.gz` files).

**Bundle banana (compress) — `-czf`:**
```
tar -czf backup.tar.gz myfolder/
```
- **`-czf`** = teen flags jude (Ch 3.6): **c** (create — banao), **z** (gzip — compress karo), **f**
  (file — is naam ki file mein). Toh: `myfolder/` ko compress karke `backup.tar.gz` banao.
- **`f` aakhri kyun** (Ch 3.7): `f` value leta hai (`backup.tar.gz`) — isliye `-czf` mein `f` aakhri,
  uske turant baad file-naam.

**Bundle kholna (extract) — `-xzf`:**
```
tar -xzf backup.tar.gz
```
- **`-xzf`** = **x** (extract — kholo), **z** (gzip decompress), **f** (file). `backup.tar.gz` ko
  wapas folder/files mein khol do.

**Dekhna (kya hai andar) — `-tzf`:**
```
tar -tzf backup.tar.gz
```
- **`t`** = list (bina khole andar ki files dekho). Extract se pehle "kya-kya hai" dekhne ko.

**Yaad rakhne ka tareeka (c/x/t):** **c**reate (banao), e**x**tract (kholo), **t** = list (dekho) —
teen main kaam. Baaki flags saath: `z` (gzip compress), `f` (file), `v` (verbose — kya ho raha dikhao,
Ch 3.8). Toh common: `tar -czvf` (banao+dikhao), `tar -xzvf` (kholo+dikhao).

> **Yaad rakhne wali baat:** `tar -czf out.tar.gz folder/` = bundle banao (c=create, z=gzip, f=file).
> `tar -xzf file.tar.gz` = kholo (x=extract). `tar -tzf` = andar dekho (t=list). `f` aakhri (value
> leta). `v` add karo dikhane ko. Backup/transfer ka standard.

[↑ Back to top](#top)

---

<a id="s16-2"></a>
## 16.2 — `curl` aur `wget` — internet se cheezein laana

Do tools jo internet se data laate — **`curl`** (flexible, API/data) aur **`wget`** (simple file
download). Dono URL se cheezein fetch karte.

**`curl` — URL se data (default screen pe):**
```
curl https://api.example.com/data
```
- URL ka content screen pe (stdout) daal deta. API se JSON, ek webpage, kuch bhi. Default: dikhata
  hai (save nahi).

**`curl` ke kaam ke flags:**
```
curl -o output.json https://api.example.com/data     # -o = file mein save
curl -O https://example.com/file.zip                 # -O = same naam se save
curl -s https://... | jq .                           # -s = silent (progress nahi), pipe to jq
curl -f https://...                                  # -f = HTTP error (404) pe fail (Ch 15.7)
curl -L https://...                                  # -L = redirects follow karo
```
- `-o file` (is naam se save), `-O` (URL ka naam), `-s` (silent — script mein, Ch 15.7), `-f` (error
  pe fail — Ch 15.7 wala), `-L` (redirect follow). `curl` API/scripting mein zyada — flexible.

**`wget` — simple file download:**
```
wget https://example.com/file.zip
```
- Seedha file download karke save (default same naam se). Progress bar dikhata. `curl` se simpler jab
  bs file download karni ho.

**`curl` vs `wget` (kab kaunsa):**
- **`curl`** — API calls, data screen pe/pipe mein, flexible (POST, headers). Scripting mein zyada.
  Default: dikhata (save ko `-o`).
- **`wget`** — bs file download (save), recursive download (poori site), simple. Default: save karta.
- Overlap hai; dono se download hota. API/pipe → curl; simple file save → wget. (curl zyada universal,
  har jagah hota.)

> **Yaad rakhne wali baat:** `curl URL` (data screen pe — API/scripting; `-o` save, `-s` silent, `-f`
> fail-on-error, `-L` redirect). `wget URL` (file seedha download/save — simple). API/pipe = curl;
> simple file = wget. Dono internet se laate.

[↑ Back to top](#top)

---

<a id="s16-3"></a>
## 16.3 — `ssh` — doosre computer/server se judna

**`ssh`** = "**s**ecure **sh**ell" — yeh aapko ek **doosre computer (server) pe** ek terminal deta,
jaise aap wahan baithe ho. Yeh production ka dil hai — aap apne laptop se remote servers pe kaam
karte ho via ssh. (Ch 1 wala "remote server pe terminal" — yeh woh tool hai.)

**Basic connect:**
```
ssh username@server-address
```
- **`username`** = us server pe aapka user, **`@`** = "at" (kis server pe), **`server-address`** =
  server ka IP ya naam (jaise `192.168.1.5` ya `prod.example.com`).
- Connect hote hi aapko us server ka shell prompt milta (Ch 1.11 — ab prompt mein server ka hostname
  dikhega). Ab jo command chalao, woh **us server pe** chalti (aapke laptop pe nahi). `exit` se wapas.

**Port batana (agar default 22 nahi) — `-p`:**
```
ssh -p 2222 username@server
```
- **`-p 2222`** = port 2222 pe judo (default ssh port 22 hai; kuch servers alag use karte).

**Key se login (password ke bajaye) — `-i`:**
```
ssh -i ~/.ssh/mykey.pem username@server
```
- **`-i keyfile`** = **i**dentity file (private key) se login (password nahi). Cloud servers (AWS
  etc.) aksar key-based — woh `.pem`/`.key` file `-i` se dete. Zyada secure than password.

**Ek command chala ke turant wapas (bina "andar" jaaye):**
```
ssh username@server "df -h"
```
- Server pe sirf `df -h` (disk space) chalao aur result laake wapas — poore session mein "ghuse"
  bina. Quick remote-check ke liye. (Command quotes mein — Ch 5.10.)

**Yeh Ch 8 se juda:** yaad karo Ch 8 (file editing) — "server pe GUI nahi, sirf terminal". Woh
terminal aksar `ssh` se milta. `ssh` se jude, phir `nano`/`vim` (Ch 8) se files edit, `tail -f` (Ch
4.9) se logs — sab remote.

> **Yaad rakhne wali baat:** `ssh user@server` = remote server pe terminal (jaise wahan baithe). Jo
> command chalao woh *us server* pe. `-p` (port), `-i keyfile` (key login, cloud), `ssh user@server
> "cmd"` (ek command chala ke wapas). `exit` se wapas. Production ka dil.

[↑ Back to top](#top)

---

<a id="s16-4"></a>
## 16.4 — `scp` aur `rsync` — files transfer/sync karna

`ssh` remote pe terminal deta; par files **transfer** karne (laptop<->server) ke liye do tools —
`scp` (simple copy) aur `rsync` (smart sync).

**`scp` = "**s**ecure **c**o**p**y" — ssh ke upar file copy:**
```
scp file.txt username@server:/remote/path/       # laptop -> server
scp username@server:/remote/file.txt ./          # server -> laptop
```
- `cp` (Ch 4.3) jaisa, par network ke paar (ssh se secure). Structure: `scp <source> <dest>`, jahan
  remote ko `user@server:/path` se likhte (`:` ke baad remote path). Direction badlo — source/dest
  swap.
- **Folder ke liye `-r`** (Ch 4.3 wala): `scp -r myfolder/ user@server:/path/`.

**`rsync` — smart sync (sirf farak bhejta):**
```
rsync -av myfolder/ username@server:/remote/path/
```
- **`rsync`** `scp` se smart — yeh sirf woh files bhejta jo **badli/nayi** hain (jo already same hain
  woh skip). Bade folders/dobara-sync mein bahut fast (sab dobara nahi bhejta).
- **`-av`** = **a** (archive — sab kuch, permissions/structure samet) + **v** (verbose, Ch 3.8 — kya
  ho raha dikhao). Common combo.
- **`--delete`** (dhyan se): destination se woh files bhi hatao jo source mein nahi (poora mirror).
  Powerful par khatarnak (galat use = files gayab). Pehle `--dry-run` (sirf dikhao, karo mat) se test.

**`scp` vs `rsync` (kab kaunsa):**
- **`scp`** — ek-do files, simple, ek baar. Seedha copy.
- **`rsync`** — bade folders, baar-baar sync, resume (toota toh wahin se), sirf-farak-bhejna. Backup/
  deploy mein zyada. "Bada ya repeated" → rsync.

**Trailing slash `/` ka farak `rsync` mein (Ch 4.12 wala, yahan aur zaroori):** `rsync folder/`
(slash) = "folder ke *andar* ka content bhejo"; `rsync folder` (bina slash) = "folder khud bhejo".
Yeh chhota farak `rsync` mein bada asar — dhyan se.

> **Yaad rakhne wali baat:** `scp source user@server:/path` = network pe file copy (ssh-secure,
> simple, `-r` folder). `rsync -av src dst` = smart sync (sirf farak bhejta, bade/repeated ke liye
> fast; `--delete` mirror — dhyan se, `--dry-run` test). Ek-do file = scp; bada/repeated = rsync.

[↑ Back to top](#top)

---

<a id="s16-5"></a>
## 16.5 — `tmux` — session jo terminal band pe bhi zinda

**`tmux`** = "**t**erminal **mu**ltiplexer" — yeh ek "session" banata jo terminal band/SSH toot jane
pe bhi **zinda rehta**, aur aap baad mein wapas **jude** sakte ho (jaise chhod ke gaye the). Yeh Ch
13.8 (`nohup`) ka behtar bhai — lambe/interactive remote kaam ke liye zaroori.

**Problem (Ch 1.12, 13.8 wala):** SSH se server pe lamba kaam chala rahe ho, SSH toot gaya (network)
— kaam gaya. `nohup` (13.8) background mein bachata par aap us kaam se "wapas jude" nahi sakte (sirf
log dekh sakte). `tmux` se aap poore session se wapas jud sakte ho.

**Basic use:**
```
tmux                    # naya session shuru
# ... apna kaam karo (commands, editor, kuch bhi) ...
# Ctrl+B phir D         # "detach" — session se niklo (par woh zinda rehta)
```
- `tmux` se naya session. Andar aap normal kaam karo. **`Ctrl+B` phir `D`** = "detach" — session se
  nikal jao, par woh (aur uske andar chal raha kaam) **background mein zinda** rehta. SSH toot jaye
  toh bhi.

**Wapas judna (reattach):**
```
tmux attach            # wapas us session mein
tmux ls                # kaunse sessions hain (list)
tmux attach -t 0       # specific session (number 0) se judo
```
- `tmux attach` = wapas us zinda session mein (jaise kabhi gaye hi nahi — sab waisa hi). Yeh `nohup`
  se bada fayda — poora session wapas, na sirf log.

**Kyun kaam ka (production):** SSH se server pe lamba kaam (training, migration, build) — `tmux` mein
chalao, detach karo, SSH toot jaye/laptop band karo, baad mein `tmux attach` se wapas — kaam chalta
mila. Server pe lamba-kaam karne walon ke liye tmux (ya `screen`, purana bhai) essential.

**Bonus — split panes:** `tmux` ek window ko kai "panes" (hisson) mein baant sakta (jaise iTerm ki
split, Ch 1.8) — ek mein log dekho, ek mein command chalao. `Ctrl+B` phir `%` (vertical split) ya
`"` (horizontal). Yeh productivity feature hai.

> **Yaad rakhne wali baat:** `tmux` = session jo detach karo (`Ctrl+B` `D`) toh bhi zinda; `tmux
> attach` se wapas judo (poora session, na sirf log — `nohup` se bada). SSH-toota/laptop-band pe
> lamba kaam bachata. Server pe lambe kaam ke liye essential.

[↑ Back to top](#top)

---

<a id="s16-6"></a>
## 16.6 — Aliases — chhote naam badi command ke liye

**Alias** = ek badi/baar-baar wali command ko ek **chhota naam** de dena. Ch 8.9 mein chhua tha (jab
`.zshrc` edit kiya) — ab poora. Roz ki typing bachata.

**Banana:**
```
alias ll='ls -ltr'
alias gs='git status'
alias ..='cd ..'
```
- **`alias chhota_naam='poori command'`** — ab `ll` type karo, woh `ls -ltr` (Ch 2.10) chala dega.
  `gs` = `git status`. `..` = `cd ..`. Badi command ka chhota shortcut.
- **`=` ke aas-paas space nahi** (Ch 5.2 wala — assignment jaisa). Command quotes mein (space wali).

**Permanent banane ke liye `.zshrc`/`.bashrc` mein (Ch 8.9):** terminal mein `alias` likhna sirf us
session ke liye — band karo, gaya. Hamesha ke liye, aliases ko `~/.zshrc` (ya `.bashrc`) mein daalo
aur `source ~/.zshrc` (Ch 8.9). Ab har naye terminal mein woh alias.

**Common useful aliases:**
```
alias ll='ls -ltr'              # detailed, latest neeche (Ch 2.10)
alias la='ls -la'               # hidden bhi (Ch 2.9)
alias ..='cd ..'                # ek folder upar
alias ...='cd ../..'            # do folder upar
alias grep='grep --color=auto'  # grep ka output colorful
alias df='df -h'                # disk space human-readable
```

**Dekhna aur hatana:**
```
alias                  # saare aliases dekho
unalias ll             # ll alias hatao
```

**Ek dhyan — aliases scripts mein nahi chalte:** aliases sirf interactive shell mein (jab aap type
karte). Scripts (Ch 9) mein aliases by-default kaam nahi karte — wahan poori command ya function (Ch
10.8) use karo. Aliases "aapki personal typing-convenience" hain, script-logic nahi.

> **Yaad rakhne wali baat:** `alias ll='ls -ltr'` = badi command ko chhota naam (typing bachata).
> `=` pe space nahi, command quotes mein. Permanent ke liye `.zshrc` mein (Ch 8.9) + `source`.
> `alias` (dekho), `unalias` (hatao). Scripts mein nahi chalte (wahan function/poori command).

[↑ Back to top](#top)

---

<a id="s16-7"></a>
## 16.7 — History aur shortcuts (`!!`, `Ctrl+R`, arrow)

Shell aapki chalayi commands yaad rakhta (**history**). In shortcuts se aap purani commands jaldi
dobara chala sakte — bahut typing bachti.

**Arrow keys — pichhli commands:**
- **Up arrow (↑)** = pichhli command (dobara dabao = usse pehle wali). Sabse basic — abhi-abhi wali
  command dobara chalani ho toh ↑ + Enter.
- **Down arrow (↓)** = aage (recent ki taraf).

**`history` — saari purani commands:**
```
history
```
- Ab tak ki commands ki numbered list. `history | grep git` (Ch 6) se koi purani command dhoondho.

**`!!` — pichhli command dobara (khaaskar `sudo` ke saath):**
```
apt-get install nginx
# "Permission denied" — sudo bhool gaye!
sudo !!
```
- **`!!`** = "pichhli poori command". `sudo !!` = "pichhli command sudo ke saath dobara" (Ch 7.9).
  Yeh sabse kaam ka — command chalayi, permission-denied aaya, `sudo !!` se turant sudo ke saath.

**`!$` — pichhli command ka aakhri argument:**
```
mkdir /app/data/logs
cd !$              # cd /app/data/logs (pichhla aakhri argument)
```
- **`!$`** = "pichhli command ka aakhri shabd". Folder banaya, phir `cd !$` se usmen jao (dobara path
  na likhna pade).

**`Ctrl+R` — history mein search (bahut powerful):**
- **`Ctrl+R`** dabao, phir kuch akshar type karo — shell purani commands mein woh dhoondhta hai
  (reverse search). Jaise `Ctrl+R` phir `docker` = pichhli `docker` wali command mil jayegi. `Enter`
  se chalao, ya `Ctrl+R` phir se (agla match). Lambi command dobara dhoondhne ka best tareeka.

**Line-editing shortcuts (bonus):**
- **`Ctrl+A`** = line ke shuru, **`Ctrl+E`** = line ke ant. **`Ctrl+U`** = cursor se pehle sab mitao,
  **`Ctrl+K`** = cursor se aage sab mitao. **`Ctrl+C`** = command cancel (Ch 1). Yeh terminal
  navigation fast karte.

> **Yaad rakhne wali baat:** History: ↑/↓ (pichhli commands), `history` (list), `!!` (pichhli poori —
> `sudo !!`), `!$` (pichhla aakhri argument — `cd !$`), **`Ctrl+R`** (search — sabse powerful, lambi
> command dhoondho). `Ctrl+A/E` (line shuru/ant). Bahut typing bachti.

[↑ Back to top](#top)

---

<a id="s16-8"></a>
## 16.8 — `cron` — commands ko schedule karna

**`cron`** ek background service hai jo commands ko **schedule** pe chalati hai — jaise "roz raat 2
baje backup chalao", "har ghante check karo". Automate/production mein bahut kaam ka — bina insaan ke
regular kaam.

**`crontab -e` — apni scheduled jobs edit karo:**
```
crontab -e
```
- **`crontab`** = "cron table" (schedule ki list). **`-e`** = edit (editor khulta, Ch 8 — nano/vim).
  Ismein aap jobs likhte ho.

**Ek cron line ka format (5 numbers + command):**
```
0 2 * * *  /home/user/backup.sh
```
- Paanch cheezein (space se), phir command:
  ```
  ┌─ minute (0-59)
  │ ┌─ hour (0-23)
  │ │ ┌─ day of month (1-31)
  │ │ │ ┌─ month (1-12)
  │ │ │ │ ┌─ day of week (0-6, 0=Sunday)
  │ │ │ │ │
  0 2 * * *  command
  ```
- **`0 2 * * *`** = "minute 0, hour 2, har din, har month, har weekday" = **roz raat 2:00 baje**.
  **`*`** = "koi bhi/har" (Ch 4.11 wildcard jaisa — "har value"). Toh yeh command roz 2 baje chalega.

**Common schedules:**
```
0 2 * * *      # roz 2:00 AM
*/15 * * * *   # har 15 minute (*/15 = "har 15")
0 * * * *      # har ghante (minute 0 pe)
0 9 * * 1      # har Monday 9:00 AM (1 = Monday)
0 0 1 * *      # har month ki 1st tareekh
```

**`crontab -l` — apni jobs dekho:**
```
crontab -l
```
- Saari scheduled jobs list.

**ZAROORI — cron ka environment alag/minimal (common trap):** cron jobs ek alag, minimal environment
mein chalti — aapka `.zshrc`, `PATH` (Ch 3.11), aliases wahan nahi hote. Isliye cron mein: (1)
**absolute paths** use karo (Ch 2.4 — `/home/user/backup.sh`, na `./backup.sh`), (2) zaroori env vars
khud set karo, (3) output redirect karo (`>> /var/log/backup.log 2>&1`, Ch 6.6) taaki pata chale kya
hua. Cron jobs "mere terminal pe chala par cron mein nahi" — iska kaaran yehi minimal environment.

> **Yaad rakhne wali baat:** `cron` = commands schedule pe chalao. `crontab -e` (edit), `-l` (dekho).
> Format: `min hour day month weekday command` (`*` = har). `0 2 * * *` = roz 2 AM. TRAP: cron
> minimal environment — absolute paths, output redirect (Ch 6.6), env khud set.

[↑ Back to top](#top)

---

<a id="s16-9"></a>
## 16.9 — Decision cheat-sheet ("yeh chahiye → yeh command")

Poore guide ka quick-reference. "Mujhe yeh karna hai → yeh command" (chapter ref ke saath):

**Navigation aur files:**
| Chahiye | Command | Ch |
|---|---|---|
| Main kahan hoon | `pwd` | 2 |
| Folder badlo | `cd path` (`cd ..` upar, `cd -` pichhla) | 2 |
| Kya hai yahan | `ls -ltr` (latest neeche) | 2 |
| File dhoondho | `find . -name "*.log"` | 4 |
| Text dhoondho (file mein) | `grep -rn "text" .` | 12 |
| File banao/dekho | `touch`, `cat`, `less`, `tail -f` | 4 |
| Copy/move/delete | `cp -r`, `mv`, `rm -rf` (dhyan!) | 4 |

**Text aur data:**
| Chahiye | Command | Ch |
|---|---|---|
| Lines filter | `grep "pattern"` | 12 |
| Find-replace | `sed 's/old/new/g'` | 12 |
| Column nikaalo | `awk '{print $2}'` ya `cut -d',' -f2` | 12/6 |
| Lines gino | `wc -l` | 4 |
| Sort/unique | `sort`, `uniq -c` | 6 |

**Process aur jobs:**
| Chahiye | Command | Ch |
|---|---|---|
| Chalti processes | `ps aux \| grep name`, `top` | 13 |
| Process roko | `kill PID` (phir `-9`) | 13 |
| Background mein | `command &`, `nohup ... &` | 13 |
| Session zinda rakho | `tmux` | 16 |

**Network aur transfer:**
| Chahiye | Command | Ch |
|---|---|---|
| Remote server | `ssh user@server` | 16 |
| File transfer | `scp`, `rsync -av` | 16 |
| Download | `curl -O`, `wget` | 16 |
| Bundle/zip | `tar -czf out.tar.gz folder/` | 16 |

**Scripting:**
| Chahiye | Command | Ch |
|---|---|---|
| Variable | `x=5`, use `"$x"` | 5 |
| Command ka output | `$(command)` | 5 |
| Condition | `if [ -f file ]; then ...; fi` | 9 |
| Loop (files) | `for f in *.txt; do ... "$f"; done` | 10 |
| Loop (lines) | `while IFS= read -r l; do ...; done < file` | 10 |
| Function | `name() { ...; }` | 10 |
| Script safety | `set -euo pipefail` | 14 |

> **Yaad rakhne wali baat:** Yeh cheat-sheet quick-lookup ke liye — "yeh chahiye → yeh command → Ch
> ref". Bookmark karo. Detail ke liye us chapter pe jao. Guide ka nichod ek table mein.

[↑ Back to top](#top)

---

<a id="s16-10"></a>
## 16.10 — Nuances aur caveats

- **`tar` ke flags order (`f` aakhri):** `tar -czf out.tar.gz folder` — `f` ke turant baad file-naam
  (Ch 3.7). `tar -cfz` (galat order) confuse karega. Yaad: `czf` (create) / `xzf` (extract), `f`
  aakhri.

- **`ssh` key permissions (common error):** private key file (`.pem`) ki permissions `600` honi
  chahiye (sirf owner read/write, Ch 7.6) — warna ssh mana kar deta ("permissions too open"). `chmod
  600 mykey.pem` (Ch 7.5).

- **`rsync` trailing slash (dohra — bada asar):** `rsync src/ dst` (content) vs `rsync src dst`
  (folder khud). Ch 4.12/16.4. Galat slash = files galat jagah. Dhyan se.

- **`rsync --delete` khatarnak:** destination se files hatata (mirror). Galat source/path = data
  gaya. Hamesha pehle `--dry-run` (sirf dikhao) se test (16.4).

- **`curl | bash` (URL se script chalana) — security risk:** `curl url | bash` internet se code
  seedha chala deta — agar URL compromised, aapke system pe koi bhi code chal jayega. Trusted sources
  se hi, aur behtar: pehle download karo, padho, phir chalao. (Ch 15.7 mein pipefail bhi.)

- **`cron` minimal environment (dohra — #1 cron trap):** cron mein `.zshrc`/PATH/aliases nahi. Absolute
  paths, output redirect, env khud set (16.8). "Terminal pe chala cron mein nahi" = yeh.

- **Aliases scripts mein nahi (16.6):** aliases interactive-only. Scripts mein function ya poori
  command. Alias ko script mein use karke expect karna = bug.

- **`history` mein secrets:** agar aap password/token command mein type karo (`mysql -pSECRET`), woh
  history mein save ho jata (baad mein koi `history` se padh le). Secrets command-line pe mat do —
  env var ya prompt (`read -s`, Ch 11.7) se.

[↑ Back to top](#top)

---

<a id="s16-11"></a>
## 16.11 — Real-life scenarios

**Scenario 1 — "Server pe lamba training chalana, laptop le jaana hai."** SSH se server pe jude (16.3),
`tmux` (16.5) shuru, `python train.py` chalaya, `Ctrl+B D` (detach), laptop band. Baad mein SSH +
`tmux attach` — training chalta mila. `tmux` + `ssh` = remote long-jobs ka combo.

**Scenario 2 — "Logs laptop pe laane hain analyze karne ko."** Server ke logs chahiye: `rsync -av
user@server:/var/log/app/ ./logs/` (16.4) — sirf naye/badle logs aaye (fast). Ya ek file: `scp
user@server:/var/log/app.log ./`. Phir local `grep`/`awk` (Ch 12) se analyze.

**Scenario 3 — "Roz ka automatic backup."** `crontab -e` (16.8), line: `0 2 * * * /home/user/
backup.sh >> /var/log/backup.log 2>&1` — roz 2 AM backup, output log mein (Ch 6.6). Absolute path
(cron trap, 16.10). Bina insaan ke regular backup.

**Scenario 4 — "Lambi command dobara chalani, yaad nahi poori."** Aapne kal ek lamba `docker run
...` chalaya tha. Aaj `Ctrl+R` (16.7), type `docker run` — woh command mil gayi, Enter. Poori dobara
type nahi karni padi. `Ctrl+R` roz bachata.

**Scenario 5 — "Command permission-denied, sudo bhool gaye."** `apt-get install nginx` → "Permission
denied". Turant `sudo !!` (16.7) — pichhli command sudo ke saath dobara. Ek-do second mein fix, poori
command dobara nahi likhni.

**Saar:** Chapter 16 ke tools roz kaam aate — `tar` (bundle), `curl`/`wget` (download), `ssh` (remote),
`scp`/`rsync` (transfer), `tmux` (session zinda), aliases (typing bachao), history/`Ctrl+R` (dobara
chalao), `cron` (schedule). Aur decision cheat-sheet (16.9) — poore guide ka quick-lookup. Sabse
practical: `ssh`+`tmux` (remote long-jobs), `rsync` (smart transfer), `Ctrl+R` (history), `cron`
(automate — absolute paths yaad rakho).

[↑ Back to top](#top)

---

> **Chapter 16 khatam.** Ab tak: `tar` (bundle -czf/-xzf), `curl`/`wget` (download), `ssh` (remote
> terminal), `scp`/`rsync` (transfer/sync), `tmux` (session zinda), aliases (`.zshrc`), history
> (`!!`, `!$`, `Ctrl+R`), `cron` (schedule + minimal-env trap), aur decision cheat-sheet. **Agla
> chapter (aakhri):** common galtiyan aur anti-patterns — woh traps jo is guide mein baar-baar aaye,
> ek jagah, taaki inse bacho.

[↑ Back to top](#top)