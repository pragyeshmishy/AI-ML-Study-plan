<a id="top"></a>
# Chapter 07 — Recursion aur Backtracking

**Recursion** (ek function jo khud ko call kare) DSA ki ek foundational technique hai — aur trees
(Ch 08), graphs (Ch 10), DP (Ch 12) sab isi pe khade. **Backtracking** recursion ka ek roop hai jo
"saare possibilities try karo" type problems (subsets, permutations) solve karta. Ch 1.4 — MEDIUM,
par yeh baaki topics ka base hai, isliye solid hona zaroori.

Yeh chapter recursion ko basics se, clear examples + recursion-tree + dry-run ke saath.

---

## Is chapter ka index

- [7.1 — Recursion kya hai (function khud ko call kare)](#s7-1)
- [7.2 — Base case + recursive case (recursion ke do hisse)](#s7-2)
- [7.3 — Recursion ko "trust" karna (recursion tree)](#s7-3)
- [7.4 — Backtracking kya hai (try -> explore -> undo)](#s7-4)
- [7.5 — Backtracking: Subsets](#s7-5)
- [7.6 — Backtracking: Permutations](#s7-6)
- [7.7 — Backtracking: Combinations / Combination Sum](#s7-7)
- [7.8 — Backtracking: Grid (example)](#s7-8)
- [7.9 — Nuances, pruning, edge cases](#s7-9)
- [7.10 — Yaad rakhne wali baatein](#s7-10)

---

<a id="s7-1"></a>
## 7.1 — Recursion kya hai (function khud ko call kare)

**Recursion** = ek function jo apne aap ko (chhote input pe) call karta hai, jab tak ek simple case
(base case) na aa jaye. Idea: ek badi problem ko **chhoti same-type problem** mein todo, jab tak
woh itni chhoti ho ki seedha answer pata ho.

**Analogy (misaal):** socho aap ek line mein khade ho aur jaanna chahte "main kaunse number pe hoon?"
Aap aage wale se poochte ho "tum kaunse pe ho?" Woh apne aage wale se — jab tak pehla banda na kahe
"main 1 pe hoon" (base case). Phir jawab peeche aata: 1 → 2 → 3 → aap. Har banda "khud jaisa chhota
sawaal" aage bhejta — yeh recursion.

**Simplest example — Factorial:**

**Problem:** `n!` = n × (n-1) × ... × 1. Recursively.
```
Input:  n=4  -> Output: 24   (4*3*2*1)
Input:  n=0  -> Output: 1     (0! = 1, base case)
```
```python
def factorial(n):
    if n <= 1:              # BASE CASE: itna chhota ki seedha pata
        return 1
    return n * factorial(n - 1)   # RECURSIVE CASE: chhoti problem
```

**Logic kyun:** `factorial(4)` = `4 * factorial(3)` = `4 * 3 * factorial(2)` = ... jab `factorial(1)`
aata, woh base-case se `1` return karta, phir sab wapas multiply hoke aata. Har call chhota input
(`n-1`), jab tak base (`n<=1`).

**Dry-run (Input n=4):**
```
factorial(4) = 4 * factorial(3)
             = 4 * (3 * factorial(2))
             = 4 * (3 * (2 * factorial(1)))
             = 4 * (3 * (2 * 1))          <- factorial(1) base case = 1
             = 4 * 3 * 2 * 1 = 24  ✓
```

**Har recursion ke do hisse (yeh MUST, 7.2 mein poora):**
1. **Base case** — kab rukna (chhota case, seedha answer). Bina iske infinite recursion (crash).
2. **Recursive case** — problem ko chhota karke khud ko call.

**Complexity (Ch 2.4 recap):** recursion depth = call-stack space. `factorial(n)` = n-deep = **O(n)
space** (chahe koi array na ho — hidden call-stack).

> **Yaad rakhne wali baat:** Recursion = function khud ko chhote input pe call kare jab tak base-case.
> Do hisse: base-case (kab ruko, seedha answer) + recursive-case (chhoti problem). `factorial(n) =
> n*factorial(n-1)`, base `n<=1`. Recursion depth = O(n) call-stack space.

[↑ Back to top](#top)

---

<a id="s7-2"></a>
## 7.2 — Base case + recursive case (recursion ke do hisse)

Har recursive function mein yeh do cheezein honi ZAROORI hain. Inhe sahi likhna hi recursion ki
poori kala hai.

**1. Base case — "kab rukna":**
- Sabse chhota input jiska answer aap **bina recursion ke** jaante ho.
- **Bina base-case = infinite recursion = crash** (RecursionError / stack overflow). Yeh #1
  recursion galti.
- Example: `factorial` mein `n<=1 -> return 1`. Aur chhota nahi kar sakte.

**2. Recursive case — "problem ko chhota karke khud ko call":**
- Problem ko aise todo ki woh **base-case ki taraf** badhe (chhoti hoti jaye).
- Example: `factorial` mein `n * factorial(n-1)` — `n-1` chhota hai, base ki taraf.
- **ZAROORI — progress:** har recursive call input ko **chhota** karna chahiye (base ki taraf), warna
  kabhi base nahi aayega = infinite. `factorial(n-1)` chhota; agar galti se `factorial(n)` call
  karte, infinite.

**Ek aur example — Sum of array (recursively):**

**Problem:** array ka sum, recursively.
```
Input:  [1, 2, 3, 4]  -> Output: 10
Input:  []            -> Output: 0   (empty = base case)
```
```python
def array_sum(arr):
    if not arr:                    # BASE CASE: empty array, sum 0
        return 0
    return arr[0] + array_sum(arr[1:])   # RECURSIVE: pehla + baaki ka sum
```
- Base: empty → 0. Recursive: `arr[0]` (pehla) + `array_sum(arr[1:])` (baaki, chhota). Baaki har baar
  chhota (`arr[1:]`), jab tak empty.

**Dry-run (Input [1,2,3]):**
```
array_sum([1,2,3]) = 1 + array_sum([2,3])
                   = 1 + (2 + array_sum([3]))
                   = 1 + (2 + (3 + array_sum([])))
                   = 1 + (2 + (3 + 0))       <- base case
                   = 6  ✓
```

**Recursion likhne ka framework (yeh yaad rakho):**
1. **Base case pehle socho:** "sabse chhota input kya, uska answer kya?" — woh likho.
2. **Recursive case:** "problem ko chhota kaise karun, aur chhote answer se poora kaise banega?"
3. **Progress check:** "kya har call base ki taraf badh raha?" (warna infinite).

> **Yaad rakhne wali baat:** Recursion = base-case (kab ruko — sabse chhota, seedha answer; bina iske
> infinite crash) + recursive-case (problem chhota karke khud call, base ki taraf). Har call input
> CHHOTA karna chahiye (progress). Framework: base pehle, phir recursive, phir progress-check.

[↑ Back to top](#top)

---

<a id="s7-3"></a>
## 7.3 — Recursion ko "trust" karna (recursion tree)

Recursion samajhne ki sabse badi trick — **"leap of faith" (bharosa)**. Aapko poora recursion "dimaag
mein trace" nahi karna — bs yeh maano ki recursive call **sahi answer de dega** chhote input ke liye,
aur usse aapka answer kaise banega woh socho.

**"Trust" ka matlab (yeh mindset badalta hai):** `factorial(n) = n * factorial(n-1)` likhte waqt,
aap yeh nahi sochte "factorial(n-1) andar-andar kya karega". Aap **maan lete** ki "factorial(n-1) mujhe
(n-1)! de dega (sahi)". Phir bs `n * woh` = n!. Base-case + "chhota-answer-sahi-hai" ka trust — bas.

**Recursion tree (visualize karne ka tareeka):** recursion ko ek "tree" ki tarah dekho — har call
apne se chhote calls ko branch karta.
```
              factorial(4)
                  |
              4 * factorial(3)
                      |
                  3 * factorial(2)
                          |
                      2 * factorial(1)
                              |
                          1  (base case)
```
- Neeche tak jaao (base tak), phir wapas upar answers build hote. Yeh "tree" recursion ki shape hai.
  Trees (Ch 08) aur backtracking (7.4) mein yeh tree branch-out karta (ek call se kai calls).

**Fibonacci — branching recursion (do calls):**

**Problem:** `fib(n) = fib(n-1) + fib(n-2)`, `fib(0)=0`, `fib(1)=1`.
```
Input:  n=5  -> Output: 5   (0,1,1,2,3,5)
```
```python
def fib(n):
    if n <= 1:                  # base: fib(0)=0, fib(1)=1
        return n
    return fib(n - 1) + fib(n - 2)   # do recursive calls
```
- Yahan har call **do** calls karta — recursion tree branch-out karta. (Note: yeh O(2^n) — slow,
  kyunki same values baar-baar. DP se O(n) — Ch 12. Abhi recursion samajhne ko.)

**Recursion tree (fib(4), branching dekho):**
```
                fib(4)
              /        \
          fib(3)        fib(2)
          /    \        /    \
     fib(2)  fib(1)  fib(1) fib(0)
     /    \
  fib(1) fib(0)
```
- Ek call se do branches → tree failta. (Yahan repeated fib(2), fib(1) — isliye slow; DP yeh fix
  karta Ch 12.)

**Kyun "trust" zaroori:** agar aap har recursion ko poora dimaag mein trace karne ki koshish karoge,
toh confuse ho jaoge (khaaskar branching mein). Trust: "base sahi + recursive-call chhote-input pe
sahi + main unhe sahi combine kar raha" — bs yeh 3 verify karo, poora tree nahi.

> **Yaad rakhne wali baat:** Recursion "trust" — maano recursive-call chhote input ka SAHI answer
> dega, phir usse apna banao (poora trace mat karo). Recursion tree = calls ki branching shape
> (factorial linear, fib branching). Verify: base sahi + recursive-call-trust + sahi combine. Yeh
> mindset recursion aasaan karta.

[↑ Back to top](#top)

---

<a id="s7-4"></a>
## 7.4 — Backtracking kya hai (try -> explore -> undo)

**Backtracking** recursion ka ek roop hai jahan hum **saari possibilities** systematically try karte:
ek choice lo → aage explore karo → phir **undo** (backtrack) karke agli choice try karo. "Saare
combinations/arrangements dhoondho" type problems ka tool.

**Kab pehchano (signal):** "all subsets/permutations/combinations", "saare possible ways", "generate
all", "N-queens / sudoku", "choices with constraints".

**Backtracking ka core pattern (yeh template YAAD rakho):**
```python
def backtrack(current, choices):
    if (goal reached):              # base case: ek complete answer bana
        result.append(current[:])   # copy save karo (current[:] — important!)
        return
    for choice in choices:
        current.append(choice)      # 1. CHOICE lo (try)
        backtrack(current, ...)     # 2. EXPLORE (recurse aage)
        current.pop()               # 3. UNDO (backtrack — choice wapas lo)
```

**Teen steps (yeh backtracking ka dil):**
1. **Choose (choice lo):** ek option pick karo, current-path mein add.
2. **Explore (aage badho):** us choice ke saath recurse — aage ki choices try.
3. **Un-choose (undo/backtrack):** choice wapas lo (`pop`), taaki agli choice fresh try ho.

**Analogy (bhoolbhulaiya/maze):** ek maze mein raste dhoondhna — ek raste pe jaao (choose), aage
explore karo, dead-end aaye toh **wapas aao** (backtrack) aur doosra rasta try karo. Saare raste is
tarah cover.

**Kyun `current[:]` (copy — important gotcha):** jab answer save karo, `current` ki **copy**
(`current[:]`) daalo, `current` khud nahi — kyunki `current` aage backtrack mein badalta rahega, aur
reference save kiya toh saved answer bhi badal jaayega (bug). Copy = snapshot.

**Complexity:** backtracking aksar exponential (O(2^n) subsets, O(n!) permutations) — kyunki saare
possibilities generate karte. Yeh expected hai (problem hi "sab dhoondho" hai). Pruning (7.9) se kabhi
km.

> **Yaad rakhne wali baat:** Backtracking = saari possibilities try: **choose → explore → undo
> (backtrack)**. Template: base-case pe `result.append(current[:])` (COPY!), phir loop: append →
> recurse → pop. Signal: "all subsets/permutations/combinations/ways". Exponential (expected). Maze
> analogy.

[↑ Back to top](#top)

---

<a id="s7-5"></a>
## 7.5 — Backtracking: Subsets

**Subsets** (saare possible subsets — powerset) backtracking ka simplest classic. Har element ke liye
"lo ya na lo" — saari combinations.

**Problem — Subsets:**

**Problem:** unique numbers ka array `nums` diya. Saare possible subsets return karo.
```
Input:  nums=[1, 2, 3]
Output: [[], [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]]
        (8 subsets — 2^3, har element lo/na-lo)
```
```python
def subsets(nums):
    result = []
    def backtrack(start, current):
        result.append(current[:])       # har state ek valid subset (COPY)
        for i in range(start, len(nums)):
            current.append(nums[i])     # 1. CHOOSE nums[i]
            backtrack(i + 1, current)   # 2. EXPLORE (i+1 se, aage wale)
            current.pop()               # 3. UNDO
    backtrack(0, [])
    return result
```

**Logic kyun (yeh core):** har call pe current-subset save karo (har intermediate state bhi valid
subset hai — `[]`, `[1]`, `[1,2]`...). Phir har aage-wale element ko "lo" (append), explore, phir
"na lo" (pop). `start` isliye ki hum sirf aage-wale elements consider karen (taaki `[1,2]` aur
`[2,1]` duplicate na ho — subsets mein order nahi). **O(2^n)** subsets (har element lo/na-lo).

**Dry-run (Input nums=[1,2,3], tree):**
```
backtrack(0, []): save []
  i=0: choose 1, current=[1]
    backtrack(1, [1]): save [1]
      i=1: choose 2, current=[1,2]
        backtrack(2, [1,2]): save [1,2]
          i=2: choose 3, [1,2,3]: save [1,2,3], pop -> [1,2]
        pop -> [1]
      i=2: choose 3, [1,3]: save [1,3], pop -> [1]
    pop -> []
  i=1: choose 2, [2]: save [2] ... aur aage
  ...
Result: [[], [1], [1,2], [1,2,3], [1,3], [2], [2,3], [3]]  ✓ (8 subsets)
```

> **Yaad rakhne wali baat:** Subsets = backtracking, har state save (copy). `start` se loop (aage-
> wale only, duplicate order bachata): choose (append) → explore (`i+1`) → undo (pop). O(2^n) (har
> element lo/na-lo). Simplest backtracking classic.

[↑ Back to top](#top)

---

<a id="s7-6"></a>
## 7.6 — Backtracking: Permutations

**Permutations** = saare possible **arrangements** (order matter karta). Subsets se farak: yahan order
matter karta (`[1,2]` aur `[2,1]` alag), aur har permutation mein saare elements hote.

**Problem — Permutations:**

**Problem:** unique numbers ka array `nums` diya. Saare permutations (arrangements) return karo.
```
Input:  nums=[1, 2, 3]
Output: [[1,2,3], [1,3,2], [2,1,3], [2,3,1], [3,1,2], [3,2,1]]
        (6 permutations = 3! — order matter karta)
```
```python
def permutations(nums):
    result = []
    def backtrack(current, remaining):
        if not remaining:               # base: koi element bacha nahi -> complete
            result.append(current[:])   # COPY save
            return
        for i in range(len(remaining)):
            current.append(remaining[i])            # 1. CHOOSE
            backtrack(current, remaining[:i] + remaining[i+1:])  # 2. EXPLORE (baaki, yeh hataya)
            current.pop()                           # 3. UNDO
    backtrack([], nums)
    return result
```

**Logic kyun (subsets se farak):** yahan har step pe **koi bhi bacha hua** element choose kar sakte
(subsets mein sirf aage-wale). Kyunki order matter karta — `[1,2]` aur `[2,1]` dono chahiye. `remaining`
= jo abhi tak use nahi hue. Base: `remaining` khaali = ek complete permutation. **O(n!)** permutations
(n choices, phir n-1, ...).

**Dry-run (Input nums=[1,2,3], partial tree):**
```
backtrack([], [1,2,3]):
  choose 1, current=[1], remaining=[2,3]
    choose 2, [1,2], remaining=[3]
      choose 3, [1,2,3], remaining=[] -> save [1,2,3]
    choose 3, [1,3], remaining=[2]
      choose 2, [1,3,2] -> save [1,3,2]
  choose 2, [2], remaining=[1,3] ... -> [2,1,3], [2,3,1]
  choose 3, [3], remaining=[1,2] ... -> [3,1,2], [3,2,1]
Result: 6 permutations  ✓
```

**Subsets vs Permutations (farak yaad rakho):**
- **Subsets:** order nahi matter (`start` se aage-only), har size (chhote-bade), O(2^n).
- **Permutations:** order matter (koi-bhi-remaining choose), saare full-length, O(n!).

> **Yaad rakhne wali baat:** Permutations = saare arrangements (order matter, `[1,2]≠[2,1]`). Har
> step koi-bhi-remaining choose (subsets mein sirf aage-only). Base: remaining khaali. O(n!). Subsets
> (order-no, O(2^n)) se farak.

[↑ Back to top](#top)

---

<a id="s7-7"></a>
## 7.7 — Backtracking: Combinations / Combination Sum

**Combinations** = fixed-size subsets (order nahi matter). **Combination Sum** = numbers chuno jinka
sum target ho. Dono subsets-jaise par ek constraint ke saath.

**Problem — Combination Sum:**

**Problem:** distinct numbers `candidates` aur `target` diya. Saare combinations dhoondho jinka sum
`target` ho. Ek number **baar-baar** use kar sakte.
```
Input:  candidates=[2, 3, 6, 7], target=7
Output: [[2,2,3], [7]]
        (2+2+3=7, aur 7=7. Note: 2 baar-baar use hua)
```
```python
def combination_sum(candidates, target):
    result = []
    def backtrack(start, current, remaining):
        if remaining == 0:              # base: target exactly reach
            result.append(current[:])   # COPY
            return
        if remaining < 0:               # base: overshoot -> dead end
            return
        for i in range(start, len(candidates)):
            current.append(candidates[i])          # 1. CHOOSE
            backtrack(i, current, remaining - candidates[i])  # 2. EXPLORE (i, na i+1 — reuse allowed)
            current.pop()                          # 3. UNDO
    backtrack(0, [], target)
    return result
```

**Logic kyun (do base cases + reuse):** `remaining` = kitna aur chahiye (target se ghatte jaao).
`remaining == 0` → perfect combination. `remaining < 0` → overshoot, dead-end (backtrack). Loop
`backtrack(i, ...)` — `i` (na `i+1`) isliye ki same number **dobara** use kar sakte (problem
allows). `start` se isliye ki duplicates (order) na ho. **Exponential** (par pruning se `<0` pe
ruk jata).

**Dry-run (Input candidates=[2,3,6,7], target=7, partial):**
```
backtrack(0, [], 7):
  choose 2, remaining=5:
    choose 2, remaining=3:
      choose 2, remaining=1:
        choose 2, remaining=-1 -> dead (<0)
        choose 3, remaining=-2 -> dead
      choose 3, remaining=0 -> save [2,2,3]!
    ...
  choose 7, remaining=0 -> save [7]!
Result: [[2,2,3], [7]]  ✓
```

**Combinations (fixed size k) — chhota variation:**
```python
# "n mein se k choose" — sirf size-k combinations
def combine(n, k):
    result = []
    def backtrack(start, current):
        if len(current) == k:           # base: size k reach
            result.append(current[:])
            return
        for i in range(start, n + 1):
            current.append(i)
            backtrack(i + 1, current)   # i+1 — reuse nahi (distinct)
            current.pop()
    backtrack(1, [])
    return result
```

> **Yaad rakhne wali baat:** Combination-sum: `remaining` ghatte jaao, `==0` save / `<0` dead-end.
> `backtrack(i)` (reuse) vs `backtrack(i+1)` (no-reuse). `start` = duplicate-order bachata.
> Combinations = fixed-size subsets (`len==k` base). Subsets-family with constraint.

[↑ Back to top](#top)

---

<a id="s7-8"></a>
## 7.8 — Backtracking: Grid (example)

Backtracking grids (2D arrays) pe bhi aata — jaise word-search, path-finding. Yeh trees/graphs (Ch
08/10) se bhi juda (grid = graph). Ek representative example.

**Problem — Word Search:**

**Problem:** ek 2D grid of characters aur ek `word` diya. Kya word grid mein banta hai (adjacent
cells — up/down/left/right, ek cell ek baar)?
```
Input:  board = [["A","B","C"],
                 ["S","F","C"],
                 ["A","D","E"]],  word="ABF"
Output: True   (A(0,0)->B(0,1)->F(1,1), adjacent path)
```
```python
def exist(board, word):
    rows, cols = len(board), len(board[0])

    def backtrack(r, c, idx):
        if idx == len(word):              # base: poora word mil gaya
            return True
        # out of bounds ya char match nahi ya visited
        if r < 0 or r >= rows or c < 0 or c >= cols or board[r][c] != word[idx]:
            return False
        temp = board[r][c]
        board[r][c] = "#"                 # 1. CHOOSE (mark visited)
        # 2. EXPLORE 4 directions
        found = (backtrack(r+1, c, idx+1) or backtrack(r-1, c, idx+1) or
                 backtrack(r, c+1, idx+1) or backtrack(r, c-1, idx+1))
        board[r][c] = temp                # 3. UNDO (unmark)
        return found

    for r in range(rows):
        for c in range(cols):
            if backtrack(r, c, 0):
                return True
        return False
```

**Logic kyun (grid backtracking):** har cell se try karo word banana. Current cell char match kare
toh use "visited" mark karo (`#`), phir 4 directions mein aage (next char). Dead-end (mismatch/out-
of-bounds) → False. **Undo** (`board[r][c]=temp`) — taaki doosre path mein yeh cell fir use ho sake.
Yeh choose-explore-undo grids pe.

**Note (Ch 1.5):** N-queens, sudoku bhi grid-backtracking classics hain — par word-search jaisa ek
representative kaafi hai. Pattern same: choose-explore-undo on grid. Hard versions rare in SR ML.

> **Yaad rakhne wali baat:** Grid backtracking: har cell se choose (mark visited `#`) → explore (4
> directions) → undo (unmark). Word-search, N-queens, sudoku same pattern. Grid = graph (Ch 10).
> Choose-explore-undo har jagah.

[↑ Back to top](#top)

---

<a id="s7-9"></a>
## 7.9 — Nuances, pruning, edge cases

**Signal→pattern:**

| Signal | Pattern | Section |
|---|---|---|
| Chhoti-same-type problem, "compute recursively" | Plain recursion | 7.1-7.3 |
| All subsets / powerset | Backtracking (start, lo/na-lo) | 7.5 |
| All permutations / arrangements | Backtracking (remaining, order-matter) | 7.6 |
| Combinations / combination-sum | Backtracking (start + constraint) | 7.7 |
| Grid all-paths / word-search / N-queens | Grid backtracking (mark/unmark) | 7.8 |

**Pruning (backtracking ko fast karna):** "pruning" = ek branch ko jaldi chhod dena jab pata chal
jaye woh answer nahi de sakta — taaki poora explore na karna pade. Example: combination-sum mein
`remaining < 0` pe turant return (aage jaane ka fayda nahi, 7.7). Ya sorted-input pe "agar current
already bada hai toh aage sab bade — break". Pruning se exponential km hota (par worst-case abhi
exponential). Interview mein pruning bolna smart-signal.

**Edge cases (HAMESHA):**
- **Empty input** `[]` — subsets `[[]]` (empty subset), permutations `[[]]`. Base-case handle.
- **Base case sahi/pehle** — bina base = infinite recursion (RecursionError). Base case #1 priority.
- **`current[:]` copy** (7.4) — save karte waqt copy, reference nahi (warna baad ke backtrack se
  saved answer badal jaata). Bahut common bug.
- **Undo (pop) match karo choose se** — har `append` ka ek `pop`. Miss karo toh state corrupt.
- **Recursion depth** — bahut deep (jaise n=10000) → RecursionError (Python default ~1000 limit).
  Tab iterative/DP socho (Ch 12).

**Kab recursion NAHI (iterative better):**
- **Simple loop kaafi ho** — factorial/sum loop se bhi (O(1) space, recursion O(n) stack). Recursion
  jab problem naturally recursive (trees, backtracking).
- **Overlapping subproblems** (jaise fib repeated calls, 7.3) → **DP** (memoization, Ch 12) — plain
  recursion O(2^n) slow.
- **Bahut deep** — stack-overflow risk; iterative safer.

> **Yaad rakhne wali baat:** Backtracking signals: subsets/permutations/combinations/grid-paths.
> Pruning = branch jaldi chhodo jab answer impossible (`remaining<0`) — fast. Edge: empty (`[[]]`),
> base-case-pehle (infinite bachaao), `current[:]` copy, pop-match-append. Overlapping subproblems →
> DP (Ch 12) na plain recursion.

[↑ Back to top](#top)

---

<a id="s7-10"></a>
## 7.10 — Yaad rakhne wali baatein (chapter recap)

1. **Recursion** (7.1-7.2): function khud ko chhote input pe call. **Base-case** (kab ruko, seedha
   answer — bina iske infinite) + **recursive-case** (chhoti problem, base ki taraf).
2. **Trust** (7.3): maano recursive-call chhote input ka sahi answer dega, phir apna banao (poora
   trace mat karo). Recursion tree = calls ki branching.
3. **Backtracking** (7.4): saari possibilities — **choose → explore → undo**. Template: base pe
   `result.append(current[:])` (COPY), loop: append→recurse→pop.
4. **Subsets** (7.5): har element lo/na-lo, `start` se aage-only. O(2^n).
5. **Permutations** (7.6): saare arrangements (order matter), koi-bhi-remaining. O(n!).
6. **Combination sum** (7.7): `remaining` ghatte, `==0` save / `<0` dead. `i` (reuse) vs `i+1`.
7. **Grid backtracking** (7.8): mark-visited → explore-4-dir → unmark. Word-search/N-queens.

> **Chapter ka mantra:** Recursion = base + recursive (trust the recursion). Backtracking = choose-
> explore-undo (saari possibilities). Yeh trees (Ch 08), graphs (Ch 10), DP (Ch 12) ka base hai —
> isliye solid karo. Subsets/permutations/combinations templates yaad, `current[:]` copy mat bhoolo.
> LeetCode pe 3-4 backtracking problems.

[↑ Back to top](#top)

---

> **Chapter 07 khatam.** Ab tak: recursion (base+recursive case, trust, recursion-tree); backtracking
> (choose-explore-undo template); subsets, permutations, combination-sum, grid backtracking (word-
> search); pruning + edge cases (copy, base-case, depth). **Agla chapter (08):** Trees — traversals
> (pre/in/post/level), BST, tree recursion (height/diameter/LCA), trie.

[↑ Back to top](#top)
