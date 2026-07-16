<a id="top"></a>
# Shell / Unix / Linux Scripting — Complete Guide (Hinglish)

Yeh ek **poora study guide** hai shell scripting ka — bilkul zero se (terminal kya hai) advanced tak
(production-grade scripts, Dockerfile commands). Yeh notes nahi, ek **proper tutorial** hai — har
cheez scratch se, layman language mein, har jargon (technical shabd) ka matlab bracket mein, aur
bahut saare examples ke saath.

**Language:** Hinglish (Hindi + English, Roman script) — taaki padhte waqt aisa lage jaise koi senior
aapke saath baith ke samjha raha ho. Technical terms English mein (industry mein aise hi bolte).

**Kiske liye:** aap jo terminal se thoda darte ho, ya commands "ratte" ho bina samjhe, ya production/
Docker/servers pe kaam karte ho aur "kyun aisa" samajhna chahte ho.

---

## Yeh guide kaise padhein

- **Bilkul naye ho?** → Chapter 1 se seedha, ek-ek karke. Har chapter pichhle pe khada hai.
- **Kuch aata hai?** → jo topic chahiye us chapter pe jao (neeche index). Har chapter khud-mukammal
  hai (par cross-references dete hain).
- **Jaldi lookup?** → Chapter 16 ka decision cheat-sheet ("yeh chahiye → yeh command").
- **Har chapter mein:** apna index (upar), theory (scratch se), examples (khoob), nuances/caveats
  (bareek baatein), real-life scenarios (kahan kaam aata), aur har section ke neeche "[↑ Back to
  top]".

**Sabse zaroori aadat:** commands ratna nahi — **samajhna** (har symbol/flag ka matlab), aur
`--help`/`man`/`tldr` (Ch 3.10) se khud pata karna. Yeh guide woh soch deta hai.

---

## Chapters (poora index)

**Neev (foundation) — yahan se shuru:**
- [Chapter 01 — Terminal, Shell, Kernel](01_terminal_aur_shell.md) — yeh sab hai kya, shell types
  (bash/zsh/sh), terminal types, prompt padhna
- [Chapter 02 — Filesystem aur Navigation](02_filesystem_navigation.md) — `/`, `~`, `.`, `..`, path
  (absolute/relative), `pwd`/`cd`/`ls`, `ls -ltr` deep-dive
- [Chapter 03 — Command ki Anatomy](03_command_anatomy.md) — command/flag/argument, `-` vs `--`,
  flags jodna, `--help`/`man`, `which`/PATH

**Roz ke kaam:**
- [Chapter 04 — File/Folder Operations](04_file_folder_operations.md) — `touch`/`mkdir`/`cp`/`mv`/`rm`
  (aur `rm -rf` khatra), `cat`/`less`/`head`/`tail -f`, `find`
- [Chapter 05 — `$` ka raaz aur Variables](05_dollar_aur_variables.md) — `$var`, `${}`, `$(...)`,
  `$?`/`$1`, environment/`export`, `echo`/`printf`, quotes (`'` vs `"`)
- [Chapter 06 — Pipes, Redirects, Unix Philosophy](06_pipes_redirects.md) — stdin/stdout/stderr, `|`,
  `>`/`>>`, `2>`/`&>`, `/dev/null`, `tee`, pipeline banana
- [Chapter 07 — Permissions aur Ownership](07_permissions.md) — `rwx`, owner/group/others, `chmod`
  (`+x`, `755`/`644`), `./script.sh` ka kaaran, `chown`, `sudo`
- [Chapter 08 — Terminal se File Editing](08_terminal_se_file_editing.md) — nano, VIM (modes,
  emergency escape), `.zshrc`/`.bashrc` edit + `source`

**Scripting:**
- [Chapter 09 — Scripts aur Conditions](09_scripts_aur_conditions.md) — shebang, chalane ke tareeke,
  `set -euo pipefail`, `if/else`, `[ ]` vs `[[ ]]`, `&&`/`||`, `case`
- [Chapter 10 — Loops aur Functions](10_loops_aur_functions.md) — `for`/`while`/`until`, `break`/
  `continue`, `while read` (file lines), functions (args, return)
- [Chapter 11 — Input aur Arguments](11_input_aur_arguments.md) — `$1..$9`, `$@`/`$#`, `shift`,
  validation, `read` (`-rsp`), `getopts`
- [Chapter 12 — Text Processing](12_text_processing.md) — `grep` (regex, flags), `sed` (`s///g`,
  `-i`), `awk` (columns, calculations), pipe se jodna

**Production aur beyond:**
- [Chapter 13 — Processes aur Jobs](13_processes_aur_jobs.md) — `ps`/`top`, `kill` (`-9`), background
  (`&`, `Ctrl+Z`, `bg`/`fg`), `nohup`, `;` vs `&&` vs `&`
- [Chapter 14 — Error Handling aur Robust Scripts](14_error_handling.md) — `set -e/-u/-o pipefail`,
  `trap`, defensive scripting, debugging (`bash -x`)
- [Chapter 15 — Production/Dockerfile Commands](15_production_dockerfile_commands.md) — `RUN` chaining
  (`&&`), `\`, non-interactive (`-y`), cleanup, idempotent, pinning
- [Chapter 16 — Handy Tools aur Cheat-Sheet](16_handy_tools_cheatsheet.md) — `tar`/`curl`/`ssh`/
  `rsync`/`tmux`, aliases, history (`Ctrl+R`), `cron`, decision cheat-sheet
- [Chapter 17 — Common Galtiyan aur Anti-patterns](17_common_gotchas.md) — woh traps jo baar-baar
  aaye, ek jagah — quotes, `rm -rf`, `cd`-fail, "mere machine pe chala", aur asool

---

## Poore guide ke asli sabak (baar-baar aaye)

Agar sirf 5 cheezein yaad rakhni ho:
1. **Har variable `"$var"` (double quotes) mein** — word-splitting bugs se bacho (Ch 5.10). #1 rule.
2. **Har script `#!/bin/bash` + `set -euo pipefail`** — strict mode, galtiyon pe ruko (Ch 9.2, 14.5).
3. **`rm -rf`/`>`/`cd` dhyan se** — permanent/overwrite/fail, pehle check (`pwd`/`ls`, Ch 4/14).
4. **Chhote tools pipe se jodo** — Unix philosophy (Ch 6.2). Problem ko steps mein todo.
5. **Ratna nahi, samajhna** — har symbol/flag ka matlab, aur `--help`/`man`/`tldr` se khud seekho
   (Ch 3.10).

> **Shuru karo:** [Chapter 01 se](01_terminal_aur_shell.md). Ant tak, aap terminal se darte nahi —
> use *chalate* ho, samajh ke, production mein bhi. 🎯

[↑ Back to top](#top)
