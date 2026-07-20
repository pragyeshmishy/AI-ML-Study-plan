<a id="top"></a>
# Chapter 12 — Dynamic Programming (DP) aur Greedy

**DP** sabse "daravna" topic lagta hai, par senior interviews mein aksar **medium** DP aata (Ch 1.4 —
~10%, hardest versions rare). Iska core idea simple: "same chhoti problem baar-baar mat solve karo —
answer yaad rakho (memoize)". **Greedy** ek related technique hai. Yeh chapter DP ko basics se,
step-by-step, clear examples ke saath — taaki "dar" khatam ho.

Clear examples + dry-run ke saath.

---

## Is chapter ka index

- [12.1 — DP kya hai (overlapping subproblems)](#s12-1)
- [12.2 — Memoization (top-down) vs Tabulation (bottom-up)](#s12-2)
- [12.3 — DP problem kaise pehchano + state design](#s12-3)
- [12.4 — 1D DP: Climbing Stairs, House Robber](#s12-4)
- [12.5 — 2D DP: Grid paths, LCS](#s12-5)
- [12.6 — Knapsack (0/1) + Coin Change](#s12-6)
- [12.7 — Greedy: kab greedy vs DP](#s12-7)
- [12.8 — Bit manipulation (XOR trick)](#s12-8)
- [12.9 — Nuances, edge cases](#s12-9)
- [12.10 — Yaad rakhne wali baatein](#s12-10)

---

<a id="s12-1"></a>
## 12.1 — DP kya hai (overlapping subproblems)

**Dynamic Programming (DP)** = ek technique jahan aap ek badi problem ko chhoti subproblems mein
todte ho, aur **same subproblem baar-baar solve karne ke bajaye uska answer yaad (store) rakhte** ho.
Yeh recursion (Ch 07) + "yaad rakhna" (memory) hai.

**Do conditions (DP tab lagta jab dono ho):**
1. **Overlapping subproblems** — same chhoti problem baar-baar aati (yaad rakhne ka fayda).
2. **Optimal substructure** — badi problem ka answer chhoti problems ke answers se banta.

**Fibonacci se dekho (Ch 7.3 recap — kyun plain recursion slow):**
```python
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)
```
- `fib(5)` compute karne mein `fib(3)` **kai baar** compute hota (recursion tree, Ch 7.3). Same
  subproblem baar-baar → **O(2^n)** (exponential, bahut slow). Yeh "overlapping subproblems" — DP ka
  perfect case.

**DP fix — answer yaad rakho (memoization):**
```python
def fib_dp(n, memo={}):
    if n <= 1: return n
    if n in memo:                # pehle compute kiya? yaad hai?
        return memo[n]           # dobara mat karo, stored do
    memo[n] = fib_dp(n-1, memo) + fib_dp(n-2, memo)
    return memo[n]
```
- Ab har `fib(k)` sirf **ek baar** compute hota (baaki stored se) → **O(n)**! Exponential se linear.
  Yeh DP ki poori taakat — "repeated kaam bachana" (Ch 3.4 sliding-window jaisa spirit, par recursion
  pe).

**Analogy:** socho ek bada math homework jismein ek hi sub-calculation (jaise `7×8`) baar-baar aata.
Har baar dobara karne ke bajaye, aap use ek kaagaz pe likh lete (memoize), aur agli baar wahin se
padh lete. DP = "kaam ka answer yaad rakho, dobara mat karo".

> **Yaad rakhne wali baat:** DP = recursion + "answer yaad rakho" (memoize), jab (1) overlapping
> subproblems (same chhoti problem baar-baar) + (2) optimal substructure (bade ka answer chhote se).
> Fibonacci: plain recursion O(2^n), DP O(n) — repeated kaam bachaya. Core: dobara compute mat karo.

[↑ Back to top](#top)

---

<a id="s12-2"></a>
## 12.2 — Memoization (top-down) vs Tabulation (bottom-up)

DP do tareeke se likha jata — **memoization** (top-down, recursion + cache) aur **tabulation**
(bottom-up, loop + table). Dono same answer, alag style. Dono aane chahiye.

**1. Memoization (Top-down) — recursion + cache:**
```python
def fib_memo(n, memo={}):
    if n <= 1: return n
    if n in memo: return memo[n]     # cache check
    memo[n] = fib_memo(n-1) + fib_memo(n-2)   # compute + store
    return memo[n]
```
- **Top-down:** badi problem se shuru (`fib(n)`), recursion se chhoti mein jaao, answers cache
  (`memo`) mein store. "Jab zaroorat ho tab compute (lazy) + yaad rakho." Recursion (12.1 wala).
  Natural (recursion se seedha), par recursion-depth (Ch 2.4) risk.

**2. Tabulation (Bottom-up) — loop + table:**
```python
def fib_tab(n):
    if n <= 1: return n
    dp = [0] * (n + 1)               # table
    dp[0], dp[1] = 0, 1              # base cases
    for i in range(2, n + 1):        # chhote se bade
        dp[i] = dp[i-1] + dp[i-2]    # pichhle answers se
    return dp[n]
```
- **Bottom-up:** sabse chhoti problem se shuru (`dp[0]`, `dp[1]`), loop se bade banao, table (`dp`)
  mein store. "Pehle sab chhote solve, phir bade." No recursion (loop) — no depth-risk, aksar thoda
  fast.

**Dono ka farak (yaad rakho):**

| | Memoization (top-down) | Tabulation (bottom-up) |
|---|---|---|
| Style | Recursion + cache | Loop + table |
| Direction | Bada → chhota (lazy) | Chhota → bada |
| Recursion depth risk | Haan (deep pe) | Nahi (loop) |
| Likhne mein | Natural (recursion se) | Thoda sochna (order) |

**Kaunsa use:** dono theek. **Memoization** aksar likhne mein aasaan (recursion se seedha — pehle
brute-force recursion likho, phir `memo` add). **Tabulation** deep-recursion se bachata + space-
optimize (aage) easier. Interview mein memoization se shuru karna aksar natural (Ch 1.7 — brute-force
recursion → add memo).

**Space optimization (tabulation ka bonus):** fib mein sirf pichhle 2 values chahiye — poora `dp`
array nahi, sirf do variables:
```python
def fib_optimized(n):
    if n <= 1: return n
    prev, curr = 0, 1
    for _ in range(2, n + 1):
        prev, curr = curr, prev + curr
    return curr
# O(n) time, O(1) space!
```
- Sirf zaroori pichhle values rakho → O(1) space. Yeh "space-optimized DP" — interview mein bolna
  achha (Ch 1.8 tradeoff).

> **Yaad rakhne wali baat:** DP do style: **memoization** (top-down, recursion+cache, natural — brute
> recursion + `memo`), **tabulation** (bottom-up, loop+table, no depth-risk). Dono same answer. Start
> with memoization (aasaan), tabulation space-optimize easier (sirf zaroori values → O(1) space).

[↑ Back to top](#top)

---

<a id="s12-3"></a>
## 12.3 — DP problem kaise pehchano + state design

DP ka sabse mushkil hissa — **pehchanna** (yeh DP hai kya?) aur **state design** (dp[i] ka matlab
kya?). Yeh framework har DP problem pe lagao.

**DP kab pehchano (signals):**
- "Number of ways" (kitne tareeke) — count problems.
- "Minimum/maximum" cost/path/value with **choices**.
- "Can we reach/make X?" (subset-sum, coin-change).
- Choices at each step + **overlapping** (same subproblem baar-baar).
- Aksar array/string/grid pe "optimal" ya "count".
- **NOT** DP: agar greedy chalta (12.7), ya sirf ek path (no overlap).

**State design (yeh DP ka dil — 3 sawaal):**
1. **State kya hai?** `dp[i]` (ya `dp[i][j]`) ka **exact matlab** kya? (Jaise "dp[i] = index i tak ka
   best answer".) Yeh clearly define karo — poora DP isi pe khada.
2. **Transition (recurrence) kya?** `dp[i]` ko chhote states (`dp[i-1]`, etc.) se kaise banaya? Yeh
   "choice" reflect karta.
3. **Base case kya?** Sabse chhota state ka answer (jaise `dp[0]`).

**Example — state design of Climbing Stairs (12.4 preview):**
- **State:** `dp[i]` = i-th stair tak pahunchne ke kitne tareeke.
- **Transition:** `dp[i] = dp[i-1] + dp[i-2]` (i pe ya toh 1-step se (i-1 se) ya 2-step se (i-2 se)).
- **Base:** `dp[0]=1` (ground, ek tareeka), `dp[1]=1`.

**Framework (har DP pe — yaad rakho):**
1. **Pehchano** DP hai (signals upar).
2. **State define karo** — `dp[i]` ka clear matlab (sabse zaroori step).
3. **Transition likho** — `dp[i]` = chhote states se (choices).
4. **Base case** — sabse chhota.
5. **Order** — tabulation mein chhote se bade (jaise `dp[i-1]` pehle ready ho).
6. **Answer** — usually `dp[n]` ya `max/min(dp)`.

**Sabse zaroori — state clearly define karo:** 80% DP struggle "dp[i] ka matlab kya" clear na hone
se. Agar aap ek line mein bol sako "dp[i] = ...", toh transition aur base aksar apne aap aa jate.
Interview mein state bolna (Ch 1.7) — "main dp[i] ko yeh define kar raha hoon" — clarity dikhata.

> **Yaad rakhne wali baat:** DP signals: count-ways/min-max-with-choices/can-reach/overlapping. State
> design (dil): (1) `dp[i]` ka EXACT matlab, (2) transition (chhote states se, choices), (3) base
> case. Framework: pehchano→state→transition→base→order→answer. State clearly define karna = 80% DP.

[↑ Back to top](#top)

---

<a id="s12-4"></a>
## 12.4 — 1D DP: Climbing Stairs, House Robber

**1D DP** = state ek index (`dp[i]`). Sabse simple DP — yahin se start. Do classic problems.

**Problem 1 — Climbing Stairs:**

**Problem:** `n` stairs. Ek baar mein 1 ya 2 step chadh sakte. Kitne alag tareeke top (n) tak?
```
Input:  n=3  -> Output: 3   (ways: 1+1+1, 1+2, 2+1)
Input:  n=4  -> Output: 5
```
```python
def climb_stairs(n):
    if n <= 2:
        return n
    dp = [0] * (n + 1)
    dp[1], dp[2] = 1, 2              # base: 1 stair=1 way, 2 stairs=2 ways
    for i in range(3, n + 1):
        dp[i] = dp[i-1] + dp[i-2]    # i pe: (i-1 se 1-step) + (i-2 se 2-step)
    return dp[n]
```
- **State:** `dp[i]` = i-th stair tak ke tareeke. **Transition:** `dp[i] = dp[i-1] + dp[i-2]` (i pe
  pahunchne ke do raste: i-1 se ek step, ya i-2 se do step). **Base:** dp[1]=1, dp[2]=2. (Yeh
  fibonacci hi hai! 12.1) **O(n) time, O(n) space** (ya O(1) optimized, 12.2).

**Dry-run (Input n=4):**
```
dp[1]=1, dp[2]=2
dp[3] = dp[2]+dp[1] = 2+1 = 3
dp[4] = dp[3]+dp[2] = 3+2 = 5
return 5  ✓
```

**Problem 2 — House Robber:**

**Problem:** houses ki line, har mein paisa. Adjacent houses nahi loot sakte (alarm). Maximum paisa?
```
Input:  nums=[2, 7, 9, 3, 1]  -> Output: 12  (house 0,2,4: 2+9+1=12)
Input:  nums=[2, 1, 1, 2]     -> Output: 4   (house 0,3: 2+2=4)
```
```python
def rob(nums):
    if not nums: return 0
    if len(nums) == 1: return nums[0]
    dp = [0] * len(nums)
    dp[0] = nums[0]
    dp[1] = max(nums[0], nums[1])
    for i in range(2, len(nums)):
        # choice: is house ko loot (nums[i] + dp[i-2]) ya na loot (dp[i-1])
        dp[i] = max(dp[i-1], nums[i] + dp[i-2])
    return dp[-1]
```
- **State:** `dp[i]` = house 0..i tak max loot. **Transition (choice — DP ka dil):** house `i` pe do
  choice — **loot** (`nums[i] + dp[i-2]`, kyunki i-1 skip karna pada) ya **na loot** (`dp[i-1]`, i
  chhod ke pichhla best). Bada lo. **Base:** dp[0], dp[1]. **O(n).**

**Dry-run (Input nums=[2,7,9,3,1]):**
```
dp[0]=2, dp[1]=max(2,7)=7
dp[2]=max(dp[1]=7, nums[2]+dp[0]=9+2=11) = 11
dp[3]=max(dp[2]=11, nums[3]+dp[1]=3+7=10) = 11
dp[4]=max(dp[3]=11, nums[4]+dp[2]=1+11=12) = 12
return 12  ✓
```

**1D DP ka pattern (yaad rakho):** `dp[i]` = i tak ka answer, transition = pichhle 1-2 states se
(choice: include/exclude). Climbing (ways), house-robber (max with skip). Yeh sabse common DP shape.

> **Yaad rakhne wali baat:** 1D DP: `dp[i]` = i tak answer, transition pichhle states se (choice
> include/exclude). Climbing-stairs `dp[i]=dp[i-1]+dp[i-2]` (fibonacci). House-robber `dp[i]=max(dp
> [i-1], nums[i]+dp[i-2])` (loot ya na-loot). O(n). Simplest DP — yahin se start.

[↑ Back to top](#top)

---

<a id="s12-5"></a>
## 12.5 — 2D DP: Grid paths, LCS

**2D DP** = state do indices (`dp[i][j]`) — grids ya do strings/arrays pe. Thoda zyada, par same
framework (12.3).

**Problem 1 — Unique Paths (grid):**

**Problem:** `m x n` grid. Top-left se bottom-right tak jaana, sirf right ya down move. Kitne unique
paths?
```
Input:  m=3, n=3  -> Output: 6   (6 alag raste top-left se bottom-right)
```
```python
def unique_paths(m, n):
    dp = [[1] * n for _ in range(m)]     # pehli row/col = 1 (ek hi rasta)
    for i in range(1, m):
        for j in range(1, n):
            dp[i][j] = dp[i-1][j] + dp[i][j-1]   # upar se + left se
    return dp[m-1][n-1]
```
- **State:** `dp[i][j]` = (i,j) cell tak ke unique paths. **Transition:** `dp[i][j] = dp[i-1][j]
  (upar se) + dp[i][j-1] (left se)` — kyunki (i,j) pe sirf upar ya left se aa sakte. **Base:** pehli
  row/col = 1 (ek hi rasta — sidha). **O(m×n).**

**Dry-run (m=3, n=3, dp grid banta):**
```
Start (row/col 1):  [[1,1,1],
                     [1,_,_],
                     [1,_,_]]
dp[1][1]=dp[0][1]+dp[1][0]=1+1=2
dp[1][2]=dp[0][2]+dp[1][1]=1+2=3
dp[2][1]=dp[1][1]+dp[2][0]=2+1=3
dp[2][2]=dp[1][2]+dp[2][1]=3+3=6
return dp[2][2]=6  ✓
```

**Problem 2 — Longest Common Subsequence (LCS):**

**Problem:** do strings `s1`, `s2`. Sabse lambi common subsequence (order-preserving, contiguous
zaroori nahi) ki length.
```
Input:  s1="abcde", s2="ace"  -> Output: 3   ("ace" — common subsequence)
Input:  s1="abc", s2="def"    -> Output: 0
```
```python
def lcs(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]   # dp[i][j] = s1[:i], s2[:j] ka LCS
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:               # chars match
                dp[i][j] = dp[i-1][j-1] + 1      # diagonal + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])  # ek char skip, bada lo
    return dp[m][n]
```
- **State:** `dp[i][j]` = `s1` ke pehle i chars aur `s2` ke pehle j chars ka LCS. **Transition:**
  chars match (`s1[i-1]==s2[j-1]`) → `dp[i-1][j-1] + 1` (diagonal, dono se ek char liya). Match nahi
  → `max(dp[i-1][j], dp[i][j-1])` (ek string se ek char skip, bada). **Base:** dp[0][*]=dp[*][0]=0
  (khaali string). **O(m×n).**

**2D DP pattern (yaad rakho):** `dp[i][j]` = do dimensions tak ka answer. Grid (upar+left), strings
(match→diagonal+1, else max-skip). Edit-distance bhi similar (2 strings). Framework same (12.3), bs
state 2D.

> **Yaad rakhne wali baat:** 2D DP: `dp[i][j]` = do-index tak answer. Grid-paths `dp[i][j]=dp[i-1][j]
> +dp[i][j-1]` (upar+left). LCS: match→`dp[i-1][j-1]+1` (diagonal), else `max(dp[i-1][j],dp[i][j-1])`.
> O(m×n). Framework same, state 2D. Strings/grids.

[↑ Back to top](#top)

---

<a id="s12-6"></a>
## 12.6 — Knapsack (0/1) + Coin Change

Do aur classic DP — **knapsack** (items chuno with weight limit) aur **coin change** (min coins for
amount). Choice-based DP ke representative.

**Problem 1 — Coin Change (min coins):**

**Problem:** coins ki denominations aur ek `amount`. Minimum coins jinse `amount` bane (na bane toh
-1). Har coin baar-baar use kar sakte.
```
Input:  coins=[1, 2, 5], amount=11  -> Output: 3   (5+5+1 = 11, 3 coins)
Input:  coins=[2], amount=3         -> Output: -1  (2 se 3 nahi banta)
```
```python
def coin_change(coins, amount):
    dp = [float('inf')] * (amount + 1)   # dp[x] = x banane ke min coins
    dp[0] = 0                            # 0 banane ke liye 0 coins
    for x in range(1, amount + 1):
        for coin in coins:
            if coin <= x:
                dp[x] = min(dp[x], dp[x - coin] + 1)   # is coin ko use karo
    return dp[amount] if dp[amount] != float('inf') else -1
```
- **State:** `dp[x]` = amount `x` banane ke min coins. **Transition:** har coin ke liye, `dp[x] =
  min(dp[x], dp[x-coin] + 1)` (agar yeh coin use karen, toh `x-coin` ke min coins + 1). **Base:**
  `dp[0]=0`. **O(amount × coins).**

**Dry-run (Input coins=[1,2,5], amount=11, partial):**
```
dp[0]=0
dp[1]=min(inf, dp[0]+1)=1  (coin 1)
dp[2]=min(dp[1]+1=2, dp[0]+1=1)=1  (coin 2)
...
dp[11]: min via coin 5 (dp[6]+1), coin 2 (dp[9]+1), coin 1 (dp[10]+1) = 3
return 3  ✓
```

**Problem 2 — 0/1 Knapsack:**

**Problem:** items with weights aur values, ek weight `capacity`. Max value jo utha sakte (har item
ek baar — 0 ya 1).
```
Input:  weights=[1,3,4], values=[15,20,30], capacity=4
Output: 35   (item 0 (w1,v15) + item 2... nahi: item1(w3,v20)+item0(w1,v15)=35, weight 4)
```
```python
def knapsack(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            # choice: item (i-1) na lo (dp[i-1][w]) ya lo (value + dp[i-1][w-weight])
            dp[i][w] = dp[i-1][w]                      # na lo
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w],
                               values[i-1] + dp[i-1][w - weights[i-1]])  # lo
    return dp[n][capacity]
```
- **State:** `dp[i][w]` = pehle i items, capacity w mein max value. **Transition (choice):** item
  (i-1) ko **na lo** (`dp[i-1][w]`) ya **lo** (`value + dp[i-1][w-weight]`, agar fit). Bada lo.
  **Base:** dp[0][*]=0. **O(n × capacity).**

**Knapsack pattern (yaad rakho):** "items chuno with constraint (weight/capacity), max/min value" —
har item pe include/exclude choice. Subset-sum, partition bhi similar. Yeh choice-DP ka core.

> **Yaad rakhne wali baat:** Coin-change: `dp[x]` = min coins for x, `dp[x]=min(dp[x], dp[x-coin]+1)`.
> Knapsack 0/1: `dp[i][w]` = i items/capacity w max value, choice include (`val+dp[i-1][w-wt]`) vs
> exclude (`dp[i-1][w]`). Choice-based DP. O(n × capacity/amount).

[↑ Back to top](#top)

---

<a id="s12-7"></a>
## 12.7 — Greedy: kab greedy vs DP

**Greedy** = har step pe **abhi ka best choice** lo (locally optimal), yeh ummeed karke ki woh
overall best dega. DP se simpler/faster jab kaam kare — par **hamesha nahi karta**. Kab greedy vs DP
samajhna zaroori.

**Kab pehchano (signal):** "maximum/minimum" jahan har step ka obvious best choice ho, "intervals",
"scheduling", "jab local-best = global-best".

**Greedy example — Jump Game:**

**Problem:** array jahan har `nums[i]` = us index se max jump. Kya last index tak pahunch sakte?
```
Input:  nums=[2, 3, 1, 1, 4]  -> Output: True   (0->1->4 ya 0->2->3->4)
Input:  nums=[3, 2, 1, 0, 4]  -> Output: False  (index 3 pe 0, aage nahi ja sakte)
```
```python
def can_jump(nums):
    max_reach = 0                    # ab tak kahan tak pahunch sakte
    for i in range(len(nums)):
        if i > max_reach:            # is index tak pahunch hi nahi sakte
            return False
        max_reach = max(max_reach, i + nums[i])   # greedy: max reach update
    return True
```
- **Greedy logic:** har index pe "max reach" track karo (abhi ka best). Agar kisi index tak pahunch
  hi nahi sakte (`i > max_reach`), False. Yeh greedy — har step best-reach, DP ki zaroorat nahi.
  **O(n).** (DP se bhi hota par greedy O(n) simpler.)

**Greedy example 2 — Interval Scheduling (max non-overlapping):**

**Problem:** intervals, max kitne non-overlapping select kar sakte?
```python
def max_intervals(intervals):
    intervals.sort(key=lambda x: x[1])   # END time se sort (greedy key!)
    count = 0
    last_end = float('-inf')
    for start, end in intervals:
        if start >= last_end:            # overlap nahi
            count += 1
            last_end = end
    return count
```
- **Greedy insight:** **earliest-end** wale pehle chuno (end se sort) — isse aage ke liye max jagah
  bachti. Yeh greedy choice provably optimal. **O(n log n)** (sort).

**Greedy vs DP (kab kaunsa — yeh zaroori):**
- **Greedy:** jab **local best = global best** (greedy choice provably optimal). Simpler, faster
  (aksar O(n) ya O(n log n)). Par **prove karna** padta ki greedy kaam karega.
- **DP:** jab greedy fail kare — jab abhi ka best choice aage nuksaan de sakta, aur **saari
  possibilities** consider karni paden (overlapping subproblems). Slower par correct.
- **Test:** coin-change [1,2,5] amount 11 — greedy (bada coin pehle: 5+5+1=3) kaam karta. Par coins
  [1,3,4] amount 6 — greedy (4+1+1=3) galat, DP (3+3=2) sahi! Toh coin-change **DP** (greedy fail).
  Jump-game greedy kaam karta. **Jab doubt, DP safe (correct); greedy sirf jab prove kar sako.**

> **Yaad rakhne wali baat:** Greedy = har step abhi-ka-best (local optimal), simpler/faster — par
> sirf jab local-best=global-best (prove karna padta). Jump-game (max-reach), intervals (earliest-end
> sort). DP jab greedy fail (saari possibilities chahiye). Doubt → DP safe. Coin[1,3,4]: greedy fail,
> DP sahi.

[↑ Back to top](#top)

---

<a id="s12-8"></a>
## 12.8 — Bit manipulation (XOR trick)

Bit manipulation (numbers ko binary bits pe operate) kabhi aata — sabse common **XOR trick**. Ek-do
classic patterns kaafi (Ch 1.5 — deep bit-DP rare).

**XOR (`^`) ki key properties (yeh yaad rakho):**
- `a ^ a = 0` (same cheez XOR = 0).
- `a ^ 0 = a` (0 ke saath XOR = wahi).
- XOR commutative/associative (order matter nahi).

**Classic problem — Single Number:**

**Problem:** array jahan har element **do baar** aata sivay ek ke (jo ek baar). Woh single dhoondho.
```
Input:  nums=[4, 1, 2, 1, 2]  -> Output: 4   (baaki sab do baar, 4 ek baar)
Input:  nums=[2, 2, 1]        -> Output: 1
```
```python
def single_number(nums):
    result = 0
    for num in nums:
        result ^= num            # sab XOR
    return result
```
- **Logic kyun (XOR magic):** saare numbers XOR karo. Jo do baar aaye woh **cancel** ho jate (`a^a=
  0`), aur single number bacha rehta (`x^0=x`). Ek pass, **O(n) time, O(1) space** — hashing (O(n)
  space) se better! Elegant.

**Dry-run (Input nums=[4,1,2,1,2]):**
```
result=0
0^4=4, 4^1=5, 5^2=7, 7^1=6, 6^2=4
(pairs cancel: 1^1=0, 2^2=0, sirf 4 bacha)
return 4  ✓
```

**Doosre common bit tricks (jaan-ne bhar):**
- `n & 1` — last bit (odd/even check: `n & 1 == 1` odd).
- `n >> 1` — right shift (divide by 2). `n << 1` — left shift (multiply by 2).
- `n & (n-1)` — lowest set-bit hatta (count-set-bits mein use).
- **Note:** bit-manipulation SR ML mein kabhi aata (single-number common), par deep bit-DP/bitmask
  rare (Ch 1.5 skip). XOR single-number samajh lo — kaafi.

> **Yaad rakhne wali baat:** XOR (`^`): `a^a=0`, `a^0=a` — same cancel. Single-number (baaki do-baar,
> ek ek-baar): sab XOR → pairs cancel → single bacha. O(n)/O(1) (hashing se better). Bit tricks:
> `n&1` (odd/even), `>>`/`<<` (÷2/×2). Deep bit-DP skip (rare).

[↑ Back to top](#top)

---

<a id="s12-9"></a>
## 12.9 — Nuances, edge cases

**Signal→pattern (DP/greedy):**

| Signal | Pattern | Section |
|---|---|---|
| Count ways / min-max with choices (1 index) | 1D DP | 12.4 |
| Grid paths / 2 strings (LCS/edit) | 2D DP | 12.5 |
| Items with constraint / coin / subset-sum | Knapsack-style DP | 12.6 |
| Local-best = global-best (provable) | Greedy | 12.7 |
| "X do baar sivay ek" / bits | XOR / bit trick | 12.8 |

**DP edge cases (HAMESHA):**
- **Empty input / n=0** — base case (dp[0], khaali). Handle.
- **Base case galat** — DP ka #1 bug. dp[0], dp[1] sahi set karo (12.4 house-robber base dhyan se).
- **Order (tabulation)** — `dp[i]` compute karne se pehle `dp[i-1]` ready ho (chhote-se-bade loop).
- **Impossible case** — coin-change `-1` (na bane), `float('inf')` init + final check.
- **Off-by-one** — array size `n+1` (0 se n), indices dhyan se. Common bug.

**Greedy caveat:** greedy **prove** karo kaam karega — warna galat answer. Doubt ho toh DP (safe,
correct). Interview mein greedy bolne se pehle "kya local-best global-best hai?" socho.

**Kab DP NAHI:**
- **No overlapping subproblems** — agar har subproblem unique (repeat nahi), DP ka fayda nahi (plain
  recursion/divide-conquer).
- **Greedy chalta ho** — simpler, use greedy (jab prove ho).
- **Interview mein DP-dar:** medium DP (1D/2D, knapsack, LCS) aata — hardest (interval-DP, bitmask)
  rare (Ch 1.5). Basics + state-design solid karo, kaafi.

> **Yaad rakhne wali baat:** DP signals: count-ways/min-max-choices (1D), grid/2-strings (2D), items-
> constraint (knapsack). Edge: base-case (#1 bug), order (chhote pehle), impossible (`inf`+-1),
> off-by-one (`n+1`). Greedy: prove karo (doubt→DP). Deep-DP skip; medium aata.

[↑ Back to top](#top)

---

<a id="s12-10"></a>
## 12.10 — Yaad rakhne wali baatein (chapter recap)

1. **DP** (12.1): recursion + "answer yaad rakho" (memoize), jab overlapping subproblems + optimal
   substructure. Fib: O(2^n) → O(n).
2. **Memoization vs Tabulation** (12.2): top-down (recursion+cache) vs bottom-up (loop+table). Dono
   same. Tabulation space-optimize easier (O(1)).
3. **State design** (12.3): (1) `dp[i]` ka EXACT matlab, (2) transition (choices), (3) base. State
   clearly define = 80% DP.
4. **1D DP** (12.4): climbing-stairs (`dp[i]=dp[i-1]+dp[i-2]`), house-robber (`max(skip, take+dp[i-
   2])`).
5. **2D DP** (12.5): grid-paths (`dp[i-1][j]+dp[i][j-1]`), LCS (match→diagonal+1, else max-skip).
6. **Knapsack/coin** (12.6): choice include/exclude with constraint. Coin `dp[x]=min(dp[x],dp[x-coin]
   +1)`.
7. **Greedy** (12.7): local-best (jab provably global). Jump-game, intervals. Doubt→DP.
8. **XOR** (12.8): single-number (pairs cancel), O(n)/O(1).

> **Chapter ka mantra:** DP = "repeated kaam mat karo, yaad rakho" — recursion + memo. Sabse zaroori
> **state design** (dp[i] ka matlab). Senior interviews mein **medium DP** (1D/2D, knapsack, LCS) —
> hardest rare (Ch 1.5). Dar mat, framework (12.3) lagao. Greedy jab prove ho (warna DP). LeetCode pe
> 5-6 DP problems (climbing, house-robber, coin, LCS, unique-paths).

[↑ Back to top](#top)

---

> **Chapter 12 khatam.** Ab tak: DP (overlapping subproblems, memoize); memoization vs tabulation;
> state-design framework; 1D DP (climbing/house-robber), 2D DP (grid/LCS), knapsack/coin-change;
> greedy (vs DP); XOR/bit-tricks. **Agla chapter (13):** Review + master pattern cheat-sheet
> (signal→pattern) + honest self-assessment (yeh docs kaafi hain ya nahi).

[↑ Back to top](#top)