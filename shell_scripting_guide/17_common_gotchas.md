<a id="top"></a>
# Chapter 17 — Common Galtiyan aur Anti-patterns (jo bar-bar log karte hain)

Yeh aakhri chapter — poore guide mein jo traps aur galtiyan baar-baar aayi, unhe **ek jagah** rakh
diya, taaki aap inse bach sako. Yeh "anti-patterns" hain — matlab woh tareeke jo galat/khatarnak
hain, aur inke sahi vikalp (alternatives). Ise ek "kya-nahi-karna" checklist ki tarah use karo.

Har galti ke saath: **kyun bura**, **kya hota hai**, aur **sahi tareeka** (chapter ref ke saath).

---

## Is chapter ka index

- [17.1 — Quotes na lagana (`$var` vs `"$var"`)](#s17-1)
- [17.2 — `=` ke aas-paas space (variable mein)](#s17-2)
- [17.3 — `rm -rf` ka laprvaah use](#s17-3)
- [17.4 — `>` se galti se overwrite](#s17-4)
- [17.5 — `cd` ke fail hone ko ignore karna](#s17-5)
- [17.6 — "Mere machine pe chala" (shell/version farak)](#s17-6)
- [17.7 — `[ ]` mein spaces bhoolna](#s17-7)
- [17.8 — Useless use of `cat` (aur doosre chhote](#s17-8)
- [17.9 — Numbers aur strings ka comparison mix](#s17-9)
- [17.10 — Error ko ignore karna (no error handling)](#s17-10)
- [17.11 — Aakhri salah: achhi shell scripting ke asool](#s17-11)

---

<a id="s17-1"></a>
## 17.1 — Quotes na lagana (`$var` vs `"$var"`)

**Galti:** variables ko quotes ke bina use karna — `rm $file`, `cd $dir`.

**Kyun bura:** agar variable ki value mein **space** ho (jaise `my report.txt`), toh shell use kai
tokens mein tod deta (Ch 3.9, 5.10). `rm $file` jahan `$file="my report.txt"` → `rm my report.txt`
(do alag files!) → galat file delete ya error.

**Kya hota:**
```
file="my report.txt"
rm $file          # GALAT: rm ko "my" aur "report.txt" do samjhe
```

**Sahi tareeka — hamesha `"$var"` (double quotes):**
```
rm "$file"        # SAHI: "my report.txt" ek hi rehta
```
- Yeh guide ka sabse bada rule (Ch 5.10, 5.12). **Har variable use `"$var"` mein** — 90% space/word-
  splitting bugs yahin ruk jaate. Loop mein bhi (`"$f"`, Ch 10.3), condition mein bhi (`[ -f "$x" ]`,
  Ch 9.7).

> **Yaad rakhne wali baat:** GALTI: `rm $file` (bina quotes — space wali value todti). SAHI: `rm
> "$file"` (double quotes). Har variable `"$var"` mein — guide ka #1 rule. Ch 5.10/5.12.

[↑ Back to top](#top)

---

<a id="s17-2"></a>
## 17.2 — `=` ke aas-paas space (variable mein)

**Galti:** `x = 5` (spaces ke saath) — variable banane mein.

**Kyun bura:** shell space ko separator maanta (Ch 3.9). `x = 5` = teen tokens: `x` (command!), `=`,
`5`. Shell `x` naam ki command dhoondhta → `command not found`.

**Kya hota:**
```
name = Pragyesh        # GALAT: "command not found: name"
```

**Sahi tareeka — `=` chipka hua:**
```
name=Pragyesh          # SAHI (Ch 5.2)
name="Pragyesh Mishra" # value mein space ho toh quotes
```
- Assignment mein `=` ke dono taraf space bilkul nahi (Ch 5.2). (Yaad rakho — comparison `[ "$x" =
  "5" ]` mein spaces hote hain, par woh alag cheez hai — Ch 9.9.)

> **Yaad rakhne wali baat:** GALTI: `x = 5` (space — "command not found"). SAHI: `x=5` (chipka).
> Assignment mein `=` pe space nahi; comparison `[ "$x" = "5" ]` mein hota (alag). Ch 5.2.

[↑ Back to top](#top)

---

<a id="s17-3"></a>
## 17.3 — `rm -rf` ka laprvaah use

**Galti:** `rm -rf` bina soche/check kiye chalana — galat folder, `*` ke saath, ya variable ke saath.

**Kyun bura:** `rm -rf` permanent hai (Trash nahi, Ch 4.5), recursive (poora tree) + force (bina
pooche). Ek typo = tabahi:
- `rm -rf $dir/` jahan `$dir` khaali (undefined, Ch 14.3) → `rm -rf /` (poora system!).
- `rm -rf project /tmp` (galti se space) → `project` AUR `/tmp` dono.
- Galat folder mein `rm -rf *` → sab gaya.

**Sahi tareeka — safety layers (Ch 4.5, 14):**
```
# 1. Pehle dekho kahan ho aur kya jayega
pwd
ls target_folder/
# 2. Variable use ho toh check karo khaali toh nahi
[ -z "$dir" ] && { echo "dir khaali!"; exit 1; }
# 3. Quotes + trailing slash care
rm -rf "$dir"
# 4. set -u (undefined variable pe ruko, Ch 14.3)
```
- Niyam: `rm -rf` se pehle `pwd`+`ls` (Ch 4.13), variable `"$var"` + khaali-check (Ch 14.3), `set -u`
  (Ch 14.3). Aur `rm -rf /` ya `~` **kabhi nahi**. Important jagah `-i` (Ch 4.5 — poochega).

> **Yaad rakhne wali baat:** GALTI: `rm -rf` bina soche (permanent, ek typo = tabahi — khaali
> variable → `rm -rf /`). SAHI: pehle `pwd`+`ls`, `"$var"`+khaali-check, `set -u`, `rm -rf /` kabhi
> nahi. Ch 4.5/14.3.

[↑ Back to top](#top)

---

<a id="s17-4"></a>
## 17.4 — `>` se galti se overwrite

**Galti:** `>` (redirect) ka dhyan bina use — zaroori file overwrite ho jati.

**Kyun bura:** `>` file ka poora content **mita ke** naya likhta (Ch 6.4), bina warning. `command >
important.txt` — `important.txt` ka purana sab gaya. Aur loop mein `>` (Ch 6.11) — har baar reset,
sirf aakhri bacha.

**Kya hota:**
```
echo "line1" > data.txt
echo "line2" > data.txt     # GALAT: line1 MIT gaya (overwrite)
```

**Sahi tareeka:**
```
echo "line1" > data.txt      # naya banao (ya reset — jaan-boojh ke)
echo "line2" >> data.txt     # JODo (append, Ch 6.4) — purana rehta
```
- Jodna ho toh `>>` (append), reset karna ho tabhi `>`. Loop mein hamesha `>>` (ya redirect loop ke
  bahar, Ch 6.11). Zaroori file pe `>` se pehle socho. (`set -o noclobber` overwrite rok sakta —
  advanced.)

> **Yaad rakhne wali baat:** GALTI: `>` zaroori file pe (poora content mita deta, chup-chaap). SAHI:
> jodna = `>>` (append), reset = `>` (soch ke). Loop mein `>>` ya bahar redirect (Ch 6.11). Ch 6.4.

[↑ Back to top](#top)

---

<a id="s17-5"></a>
## 17.5 — `cd` ke fail hone ko ignore karna

**Galti:** `cd somedir` ke baad seedha kaam, bina check kiye `cd` safal hua ya nahi.

**Kyun bura:** agar `cd` fail ho (folder nahi, typo, permission), aur script aage badhe — toh aap
**galat folder** mein kaam kar rahe (Ch 14.1 wala disaster). `cd /app/data; rm -rf *` — `cd` fail →
`rm` galat jagah (home/`/`) mein.

**Sahi tareeka (do options):**
```
# Option 1 — && se (safal ho toh hi aage, Ch 9.10/13.9)
cd /app/data && rm -rf ./*

# Option 2 — set -e (fail pe ruko, Ch 14.2)
set -e
cd /app/data
rm -rf ./*

# Option 3 — explicit check
cd /app/data || { echo "cd fail"; exit 1; }
```
- `cd` ko kabhi "maan ke" mat chalo ki safal hua. `&&`, `set -e`, ya `|| exit` se ensure karo. Yeh
  guide ka baar-baar aaya sabak (Ch 9.10, 14.1, 14.2).

> **Yaad rakhne wali baat:** GALTI: `cd dir` phir seedha kaam (cd fail hua toh galat jagah — disaster).
> SAHI: `cd dir && kaam`, ya `set -e`, ya `cd dir || exit 1`. cd ko safal maan ke mat chalo. Ch
> 14.1/14.2.

[↑ Back to top](#top)

---

<a id="s17-6"></a>
## 17.6 — "Mere machine pe chala" (shell/version farak)

**Galti:** Mac (zsh) pe script likhi, bash-specific ya version-specific cheezein use ki, phir server
(bash/sh) pe fail.

**Kyun bura:** shell alag (bash/zsh/sh — Ch 1.7), versions alag (Ch 1.12), Mac vs Linux flags alag
(Ch 3.12) — ek jagah chala doosri pe nahi. Poore guide mein yeh baar-baar aaya:
- `[[ ]]` bash-only, `sh` (Alpine) mein nahi (Ch 9.8).
- `sed -i` Mac vs Linux alag (Ch 12.6, 12.10).
- `{1..5}` bash-only (Ch 10.11).
- Mac ka purana bash 3.2 (Ch 1.12).

**Sahi tareeka:**
```
#!/bin/bash              # 1. Shebang — sahi shell force (Ch 9.2)
set -euo pipefail        # 2. Strict mode (Ch 14.5)
```
- (1) **Shebang** (Ch 9.2) — `#!/bin/bash` (ya `#!/bin/sh` portable). (2) Jaan lo target kaunsa shell
  (server bash? Alpine sh?) aur uske hisaab se syntax. (3) Portable chahiye toh POSIX `sh` syntax
  ([ ] na [[ ]], `seq` na `{1..5}`). (4) Mac pe likhi script server (Linux) pe **test** karo. Ch
  1.7/1.9/1.13.

> **Yaad rakhne wali baat:** GALTI: Mac (zsh) pe likhi, server (bash/sh) pe fail (shell/version/flag
> farak). SAHI: shebang `#!/bin/bash`, target-shell jaano, portable ho toh POSIX `sh`, aur target pe
> test. Ch 1.7/9.2. Guide ka baar-baar aaya theme.

[↑ Back to top](#top)

---

<a id="s17-7"></a>
## 17.7 — `[ ]` mein spaces bhoolna

**Galti:** `[ ]` (condition, Ch 9.7) ke andar spaces na dena — `[-f file]` ya `[ -f file]`.

**Kyun bura:** `[` asal mein ek **command** hai (test ka roop, Ch 9.7). Command ke baad space chahiye
(Ch 3.1). `[-f` ko shell ek ajeeb command samajhta → error. `]` se pehle bhi space chahiye.

**Kya hota:**
```
if [-f file]; then      # GALAT: "[-f: command not found"
```

**Sahi tareeka — dono taraf space:**
```
if [ -f file ]; then    # SAHI: [ ke baad space, ] se pehle space
```
- `[` ke baad space, `]` se pehle space (Ch 9.7). Yeh sabse common condition-galti hai. `[[ ]]` mein
  bhi yehi (spaces zaroori).

> **Yaad rakhne wali baat:** GALTI: `[-f file]` (spaces nahi — "[-f: command not found"). SAHI: `[ -f
> file ]` (dono taraf space — `[` ek command hai). Ch 9.7. Sabse common condition-galti.

[↑ Back to top](#top)

---

<a id="s17-8"></a>
## 17.8 — Useless use of `cat` (aur doosre chhote inefficiencies)

**Galti:** `cat file | grep "x"` — jab `grep "x" file` seedha ho sakta.

**Kyun (halka) bura:** `cat file | grep` mein `cat` bekaar hai — `grep` khud file padh sakta (`grep
"x" file`). Extra process, extra pipe, bina fayde. Ise "useless use of cat" kehte hain (famous
chhoti galti). Kaam toh karta, par saaf/efficient nahi.

**Sahi tareeka:**
```
cat file.txt | grep "error"     # bekaar cat
grep "error" file.txt           # SAHI — grep khud padhta (Ch 12.2)
```
- Zyadatr text-tools (grep/sed/awk/sort) file-naam seedha lete (argument). `cat |` ki zaroorat nahi
  jab ek hi file ho. (`cat` tab theek jab kai files jodni ho — Ch 4.7 — ya pipe ka asli source koi
  command ho.)

**Doosri chhoti inefficiencies (jaan-ne bhar):**
- `grep "x" file | wc -l` → `grep -c "x" file` (grep khud gin sakta, Ch 12.3).
- `cat file | head` → `head file`.
- Loop mein ek-ek line process karke jo `awk`/`sed` ek command mein kar de — tool use karo (Ch 12).
- Yeh "premature" chinta nahi — bs saaf-simple likho, extra steps na daalo. (Ch 6.2 Unix philosophy —
  right tool, minimal.)

> **Yaad rakhne wali baat:** GALTI: `cat file | grep x` (bekaar cat). SAHI: `grep x file` (grep khud
> padhta). Text-tools file seedha lete — `cat |` ki zaroorat nahi (ek file pe). `grep -c` (gino),
> `head file`. Saaf-simple, extra steps nahi.

[↑ Back to top](#top)

---

<a id="s17-9"></a>
## 17.9 — Numbers aur strings ka comparison mix

**Galti:** number compare karne ko `=`/`>` use karna, ya string ko `-eq` — galat operator.

**Kyun bura:** shell mein number aur string comparison ke **alag** operators hain (Ch 9.7, 9.9):
- Numbers: `-eq -ne -gt -lt` (word se).
- Strings: `=`, `!=`.
- Mix karo toh galat result ya error. Aur `[ ]` mein `>`/`<` ko shell **redirect** (Ch 6) samajh
  leta — disaster (`[ $a > $b ]` ek file `b` bana deta!).

**Kya hota:**
```
[ "$count" > 5 ]         # GALAT: > redirect samjha, file "5" ban gayi!
[ "$count" = 5 ]         # theek chalega par STRING compare ("10" != "10.0")
```

**Sahi tareeka:**
```
[ "$count" -gt 5 ]       # SAHI: number compare (-gt = greater than, Ch 9.7)
[ "$name" = "Pragyesh" ] # SAHI: string compare (= , Ch 9.9)
```
- Number? → `-eq -gt -lt` etc. String? → `=`. `[ ]` mein `>`/`<` **kabhi nahi** (redirect ban jata).
  ([[ ]] mein `>`/`<` string ke liye chalta, par `[ ]` mein nahi — Ch 9.8.)

> **Yaad rakhne wali baat:** GALTI: number pe `=`/`>` ya string pe `-eq` (galat result; `>` toh
> redirect ban jata — file bana deta!). SAHI: number = `-gt -lt -eq` (Ch 9.7), string = `=` (Ch
> 9.9). `[ ]` mein `>`/`<` kabhi nahi.

[↑ Back to top](#top)

---

<a id="s17-10"></a>
## 17.10 — Error ko ignore karna (no error handling)

**Galti:** script bina error handling — koi command fail ho toh script aage chalta rahe (Ch 14.1).

**Kyun bura:** shell ka default (Ch 14.1) — fail pe rukta nahi. Toh: `cd` fail → `rm` galat jagah;
download fail → aadhe data pe process; ek step fail → aage sab galat. "Chup-chaap galat" — sabse bura
production mein.

**Sahi tareeka — har script ka standard (Ch 14):**
```
#!/bin/bash
set -euo pipefail        # fail-ruko + undefined-error + pipe-fail (Ch 14.5)

# defensive checks (Ch 14.8)
[ $# -lt 1 ] && { echo "Usage: $0 <file>" >&2; exit 1; }
[ -f "$1" ] || { echo "File nahi mili" >&2; exit 1; }

# cleanup (Ch 14.6)
trap 'rm -f /tmp/temp_$$' EXIT

# ... asli kaam ...
```
- (1) `set -euo pipefail` (Ch 14.5 — strict mode). (2) Defensive checks shuru mein (Ch 14.8). (3)
  `trap` cleanup (Ch 14.6). Yeh teen har production script mein. "Chup-chaap galat" → "ruk ke batao".

> **Yaad rakhne wali baat:** GALTI: no error handling (fail pe script aage — chup-chaap galat). SAHI:
> `set -euo pipefail` (Ch 14.5) + defensive checks (Ch 14.8) + `trap cleanup` (Ch 14.6). Har
> production script ka standard. Ch 14.

[↑ Back to top](#top)

---

<a id="s17-11"></a>
## 17.11 — Aakhri salah: achhi shell scripting ke asool

Poore guide ka nichod — kuch asool (principles) jo achhi, safe, maintainable shell scripting banate.
Yeh yaad rakho, baaki detail aap chapters mein dhoondh sakte ho.

**Safety (sabse zaroori):**
- Har variable `"$var"` (double quotes) — word-splitting bugs se bacho (Ch 5.10). #1 rule.
- Har script `#!/bin/bash` + `set -euo pipefail` (Ch 9.2, 14.5). Strict mode.
- `rm -rf`, `>`, `cd` — dhyan se (permanent/overwrite/fail). Pehle check (`pwd`/`ls`/`-z`).
- Destructive commands se pehle backup ya `-i` (Ch 4).

**Clarity (padhne-layak):**
- Long commands `\` se todo, `&&` se jodo (Ch 15.3). Readable = maintainable.
- Comments (`#`) jahan "kyun" non-obvious (Ch 9.4).
- Achhe variable/function naam. `getopts`/usage-message (Ch 11).
- Long flags scripts mein (`--verbose` > `-v` for clarity, Ch 3.5).

**Correctness (sahi kaam):**
- Input validate karo (arguments, files, tools — Ch 11.5, 14.8) shuru mein.
- Sahi operators (number `-gt`, string `=` — Ch 9). `[ ]` mein spaces.
- Exit codes do (`exit 0`/`1`, Ch 5.6/14.7). Errors `>&2`.
- Idempotent banao (dobara-safe, Ch 15.6) — production retry-safe.

**Unix soch (Ch 6.2):**
- Chhote tools pipe se jodo (grep/sed/awk/sort) — ek "sab-karne-wala" nahi.
- Right tool: simple pe simple (cut vs awk), zaroorat pe powerful.
- Problem ko chhote steps mein todo, har step ek tool.

**Aur sabse zaroori — seekhte raho:**
- `--help`/`man`/`tldr` (Ch 3.10) — flags ratne ki zaroorat nahi, khud pata karo.
- Test karo (khaaskar destructive/production se pehle) — `--dry-run`, chhote pe try.
- "Mere machine pe chala" se bacho — target pe test (Ch 1.13).

> **Poore guide ka ant — ek line:** Shell scripting = **chhote tools + soch se jodna**, aur **safety
> (quotes, strict mode, dhyan) + clarity (readable) + correctness (validate, sahi operators)**. Ratna
> nahi — samajhna, aur `--help` se khud seekhna. Ab aap terminal se darte nahi, use *chalate* ho. 🎯

[↑ Back to top](#top)