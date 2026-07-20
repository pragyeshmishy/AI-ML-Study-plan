<a id="top"></a>
# Chapter 02 — Foundations: Big-O aur Problem ko Kaise Approach karein

Ab strategy clear hai (Ch 01), toh yeh chapter DSA ki **neev** deta — do cheezein jo har problem
mein kaam aati:
1. **Big-O** — kisi algorithm ki speed (time) aur memory (space) ko **naapne** ka tareeka. Yeh har
   interview mein bolna padta ("yeh O(n) hai"), toh yeh solid hona zaroori.
2. **Problem approach framework** — ek nayi (kabhi na dekhi) problem saamne aaye toh kaise sochna
   shuru karein — taaki blank na ho.

Yeh chapter theory-heavy hai par bahut examples ke saath. Isko samjhe bina aage ke patterns "ratta"
lagenge; iske saath woh "samajh" aayenge.

---

## Is chapter ka index

- [2.1 — Big-O kya hai (speed ko naapne ka tareeka)](#s2-1)
- [2.2 — Common complexities: O(1), O(n), O(n^2), O(log n), O(n log n)](#s2-2)
- [2.3 — Time complexity kaise nikalein (loops dekh ke)](#s2-3)
- [2.4 — Space complexity (memory kitni lagti)](#s2-4)
- [2.5 — Time vs Space tradeoff (ek badhake doosra ghatana)](#s2-5)
- [2.6 — Complexity cheat-table (kis structure pe kya operation kitna)](#s2-6)
- [2.7 — Nayi problem ko kaise approach karein (framework)](#s2-7)
- [2.8 — Nuances aur common galtiyan](#s2-8)
- [2.9 — Yaad rakhne wali baatein](#s2-9)

---

<a id="s2-1"></a>
## 2.1 — Big-O kya hai (speed ko naapne ka tareeka)

**Big-O** (bolte hain "big oh") ek tareeka hai yeh batane ka ki **jaise input bada hota jaye, ek
algorithm kitna slow (ya kitni memory) hota jaye**. Yeh actual seconds nahi naapta (woh machine pe
depend karta) — yeh **growth rate** naapta hai: "input 2x karo toh kaam kitna guna badhega?"

**Kyun zaroori:** interview mein har solution ke baad complexity bolna padta (Ch 1.7). Aur yeh
decide karta ki aapka solution "accept" hoga ya "too slow". Ek 1000-item input pe O(n) (~1000 steps)
aur O(n^2) (~1,000,000 steps) mein zameen-aasman ka farak.

**Intuition (misaal se):** socho aapke paas `n` logon ki list hai:
- **O(1)** — "pehle aadmi ka naam batao". Chahe list mein 10 log ho ya 10 lakh — 1 step. Input se
  farak nahi padta. (Constant.)
- **O(n)** — "sab logon ka naam padho". 10 log = 10 step, 10 lakh = 10 lakh step. Input ke barabar.
  (Linear.)
- **O(n^2)** — "har aadmi ko har doosre aadmi se milao (handshake)". 10 log = ~100, 10 lakh =
  ~10^12 (bahut zyada). Input ka square. (Quadratic.)

**Ek zaroori rule — sirf sabse bada term, constants ignore:** Big-O mein hum **sabse tezi se badhne
wala hissa** rakhte hain, baaki chhod dete:
- `3n + 5` → **O(n)** (5 constant ignore, 3 multiplier ignore — sirf `n` matter karta jab bada ho).
- `n^2 + n` → **O(n^2)** (bade n pe `n^2` `n` se bahut bada, `n` ignore).
- Kyun? Big-O **bade input** ka behaviour dikhata — chhote constants/terms tab matter nahi karte.

> **Yaad rakhne wali baat:** Big-O = "input badhne pe kaam kitna guna badhega" (growth rate, actual
> seconds nahi). Interview mein har solution pe bolna padta. Rule: sirf sabse bada term rakho,
> constants/multipliers ignore (`3n+5` -> O(n)). O(1) < O(log n) < O(n) < O(n log n) < O(n^2).

[↑ Back to top](#top)

---

<a id="s2-2"></a>
## 2.2 — Common complexities: O(1), O(n), O(n^2), O(log n), O(n log n)

Yeh 5-6 complexities 95% interview problems cover karti. Har ek ko example ke saath samjho — kyunki
aapko code dekh ke turant bolna aana chahiye "yeh kaunsi hai".

**O(1) — Constant ("input se farak nahi"):**
```
def get_first(arr):
    return arr[0]      # ek step, chahe arr mein 10 ho ya 10 lakh
```
- `arr` kitna bhi bada ho, `arr[0]` ek hi step. **O(1).** Array index-access, hash-map lookup,
  variable assign — sab O(1).

**O(n) — Linear ("input ke barabar"):**
```
def sum_all(arr):
    total = 0
    for x in arr:      # n baar chalega (n = len(arr))
        total += x
    return total
```
- Loop `n` baar chalta (har element ek baar). **O(n).** Input 2x → kaam 2x.

**O(n^2) — Quadratic ("nested loop"):**
```
def all_pairs(arr):
    for i in arr:          # n baar
        for j in arr:      # har i pe n baar => n*n
            print(i, j)
```
- Loop ke andar loop, dono `n` — total `n*n`. **O(n^2).** Input 2x → kaam 4x. Yeh aksar "brute
  force" hota; interview mein isse O(n) ya O(n log n) pe optimize karna hi asli kaam.

**O(log n) — Logarithmic ("har step mein aadha kaat do"):**
```
def binary_search(arr, target):   # arr sorted hai
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target: return mid
        elif arr[mid] < target: lo = mid + 1   # aadha (left) chhod diya
        else: hi = mid - 1                      # aadha (right) chhod diya
    return -1
```
- Har step mein search-space **aadha** ho jata (1000 → 500 → 250 → ...). ~10 step mein 1000 items.
  **O(log n).** Bahut fast. (Binary search Ch 11.) Jab bhi "aadha-aadha kaatna" ho, log n.

**O(n log n) — "sorting wali speed":**
```
sorted_arr = sorted(arr)     # Python ka sort O(n log n)
```
- Achhe sorting algorithms (merge sort, Python ka Timsort) **O(n log n)** hote. Yeh O(n) se thoda
  slow, O(n^2) se bahut fast. Jab bhi aap sort karte ho, ya "divide-and-conquer", yeh aata.

**Order (fast → slow, yaad rakho):** O(1) < O(log n) < O(n) < O(n log n) < O(n^2) < O(2^n).

> **Yaad rakhne wali baat:** O(1) (index/hashmap-lookup), O(n) (ek loop), O(n^2) (nested loop),
> O(log n) (aadha-aadha kaatna — binary search), O(n log n) (sorting). Code dekh ke turant pehchano.
> Order: 1 < log n < n < n log n < n^2. Brute-force aksar O(n^2) — use O(n)/O(n log n) pe optimize.

[↑ Back to top](#top)

---

<a id="s2-3"></a>
## 2.3 — Time complexity kaise nikalein (loops dekh ke)

Interview mein aapko apne code ki complexity **khud bolni** padti. Yeh kuch simple rules hain jinse
aap code dekh ke turant nikaal sakte ho. (Practice se yeh instant ho jata hai.)

**Rule 1 — Ek loop over n items = O(n):**
```
for x in arr:      # n baar
    print(x)       # O(1) kaam
# Total: n * O(1) = O(n)
```

**Rule 2 — Nested loop (loop ke andar loop) = multiply:**
```
for i in arr:          # n baar
    for j in arr:      # n baar (har i pe)
        print(i, j)    # O(1)
# Total: n * n * O(1) = O(n^2)
```
- Nested loops ko **multiply** karo. Do nested = n^2, teen = n^3.

**Rule 3 — Alag-alag (sequential) loops = add, phir bada rakho:**
```
for x in arr: print(x)       # O(n)
for y in arr: print(y)       # O(n)
# Total: O(n) + O(n) = O(2n) = O(n)   (constant 2 ignore)
```
- Ek ke baad ek (nested nahi) loops **add** hote, phir bada term rakhte. `O(n) + O(n) = O(n)`.

**Rule 4 — Loop jo aadha-aadha kaate = O(log n):**
```
while n > 1:
    n = n // 2      # n aadha har baar
# ~log2(n) baar chalega => O(log n)
```

**Rule 5 — Constants aur chhote terms ignore (2.1):** `O(3n + 5)` = `O(n)`. `O(n^2 + n)` = `O(n^2)`.

**Worked example — iski complexity kya?**
```
def has_duplicate(arr):
    for i in range(len(arr)):          # n baar
        for j in range(i+1, len(arr)): # ~n baar (har i pe)
            if arr[i] == arr[j]:
                return True
    return False
```
- **Analysis:** nested loop, dono ~n → **O(n^2)** time. (Inner loop average ~n/2 chalta par constant
  ignore → n.) Space: sirf i, j variables → **O(1)**. 
- **Interview mein bolna:** "yeh O(n^2) time hai kyunki nested loop, aur O(1) space. Main ise hashing
  se O(n) kar sakta hoon" (Ch 04). Yeh brute-force → optimize wali soch (Ch 1.7).

**Ek nuance — function calls:** agar loop ke andar aap koi function call karo jo khud O(n) hai, toh
woh bhi multiply hota. `for x in arr: sorted(other)` = n * O(m log m). Andar ki cheez ki complexity
bhi count karo.

> **Yaad rakhne wali baat:** Ek loop = O(n). Nested loop = multiply (n^2). Sequential loops = add
> phir bada (O(n)). Aadha-kaatna = O(log n). Constants ignore. Loop ke andar function-call ki
> complexity bhi count karo. Practice se instant ho jata.

[↑ Back to top](#top)

---

<a id="s2-4"></a>
## 2.4 — Space complexity (memory kitni lagti)

Time ke saath **space** (memory) bhi naapa jata — "algorithm kitni extra memory use karta jaise
input badhta". Interview mein dono bolna achha ("O(n) time, O(1) space").

**Rule — sirf EXTRA memory count karo (input ko nahi):** input array toh already diya hai; hum
**extra** memory naapte hain jo hum banate hain.

**O(1) space — constant extra (input se farak nahi):**
```
def sum_all(arr):
    total = 0          # ek variable — O(1) extra
    for x in arr:
        total += x
    return total
# Extra memory: sirf 'total' => O(1) space
```
- Chahe `arr` mein 10 ho ya 10 lakh, hum sirf ek `total` banate. **O(1) space.**

**O(n) space — input ke barabar extra:**
```
def double_all(arr):
    result = []              # naya array
    for x in arr:
        result.append(x * 2) # n items daalte
    return result
# 'result' mein n items => O(n) space
```
- Hum ek naya `result` array bana rahe jismein `n` items — **O(n) space.**

**Recursion mein space (dhyan — chhupa hua):** har recursive call "call stack" pe jagah leti. Agar
recursion `n` deep jati hai, toh **O(n) space** (chahe koi array na banaya ho). Yeh log bhoolte hain.
```
def factorial(n):
    if n <= 1: return 1
    return n * factorial(n - 1)   # n deep recursion => O(n) space (call stack)
```

**Common space values:**
- O(1) — kuch variables (counters, pointers).
- O(n) — ek naya array/hash-map/set jismein ~n items, ya n-deep recursion.
- O(n^2) — 2D array (n x n grid).

> **Yaad rakhne wali baat:** Space = EXTRA memory (input count nahi). O(1) = kuch variables; O(n) =
> naya array/hashmap/set with n items YA n-deep recursion (call stack — chhupa!); O(n^2) = n x n
> grid. Interview mein time+space dono bolo.

[↑ Back to top](#top)

---

<a id="s2-5"></a>
## 2.5 — Time vs Space tradeoff (ek badhake doosra ghatana)

DSA ka ek bada theme — aksar aap **zyada memory use karke time bacha sakte ho** (ya ulta). Yeh
"tradeoff" samajhna senior-level insight hai (Ch 1.8 — tradeoffs bolna green signal).

**Classic misaal — Two Sum (Ch 04 mein poora):**

**Problem:** array `nums` aur ek `target` diya. Do indices dhoondho jinke elements ka sum `target` ho.
```
Input:  nums=[2, 7, 11, 15], target=9
Output: [0, 1]    (kyunki nums[0]+nums[1] = 2+7 = 9)
```

**Approach 1 — Brute force (O(n^2) time, O(1) space):**
```
def two_sum_brute(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
```
- Har pair check. **O(n^2) time** (nested loop), **O(1) space** (koi extra memory nahi). Time slow,
  memory km.

**Approach 2 — Hashing (O(n) time, O(n) space):**
```
def two_sum_hash(nums, target):
    seen = {}                        # extra memory: hash-map
    for i, num in enumerate(nums):
        need = target - num          # isko dhoondhna hai
        if need in seen:             # O(1) lookup!
            return [seen[need], i]
        seen[num] = i
    return []
```
- Ek hash-map (`seen`) banaya — **O(n) space** (extra memory). Par ab ek hi pass, har lookup O(1) →
  **O(n) time.** Memory zyada di, time bacha liya. **Yeh tradeoff hai.**

**Dry-run (Approach 2, Input nums=[2,7,11,15], target=9):**
```
i=0, num=2:  need=9-2=7. seen={} mein 7 nahi. seen={2:0}
i=1, num=7:  need=9-7=2. seen={2:0} mein 2 HAI! return [seen[2], 1] = [0, 1]  ✓
```

**Senior insight:** interview mein aksar aap brute-force (O(n^2)) bolke shuru karte, phir "main space
use karke O(n) kar sakta hoon" — yeh tradeoff bolna maturity dikhata. Kabhi memory constraint ho toh
brute-force better; usually time zyada matter karta toh hashing. **Sahi tradeoff chunna = senior
skill.**

> **Yaad rakhne wali baat:** Time-space tradeoff = zyada memory use karke time bacha sakte (ya ulta).
> Two Sum: brute O(n^2) time/O(1) space vs hashing O(n) time/O(n) space. Interview: brute-force bolo,
> phir "space use karke optimize" — tradeoff bolna senior-signal. Sahi tradeoff chunna = skill.

[↑ Back to top](#top)

---

<a id="s2-6"></a>
## 2.6 — Complexity cheat-table (kis structure pe kya operation kitna)

Yeh table interview mein bahut kaam ka — har data structure pe common operations ki complexity. Yeh
yaad rakho (ya bookmark), taaki aap turant bol sako "hash-map lookup O(1) hai".

**Array / List (Python `list`):**
| Operation | Complexity | Note |
|---|---|---|
| Index access `arr[i]` | O(1) | direct jump |
| Append end `arr.append(x)` | O(1) | amortised (usually O(1)) |
| Insert/delete beech mein | O(n) | baaki shift karne padte |
| Search (unsorted) | O(n) | ek-ek dekhna |
| Search (sorted, binary) | O(log n) | Ch 11 |

**Hash Map / Set (Python `dict`/`set`):**
| Operation | Complexity | Note |
|---|---|---|
| Insert / lookup / delete | O(1) | average (yeh hashing ka superpower, Ch 04) |
| Worst case (rare) | O(n) | bahut collisions — practically O(1) maano |

**Stack / Queue (Ch 06):**
| Operation | Complexity |
|---|---|
| Push / pop (stack, list end) | O(1) |
| Enqueue / dequeue (`deque`) | O(1) |

**Heap (Ch 09):**
| Operation | Complexity |
|---|---|
| Push / pop-min | O(log n) |
| Peek min | O(1) |

**Tree / BST (Ch 08, balanced):**
| Operation | Complexity |
|---|---|
| Search/insert (balanced BST) | O(log n) |
| Traversal (sab nodes) | O(n) |

**Sorting:** O(n log n) (Python `sorted`/`.sort()`).

**Kaise use karein:** jab aap solution socho, poocho "mujhe kaunsa operation baar-baar chahiye?" Agar
"fast lookup" → hash-map (O(1)). Agar "min baar-baar nikaalna" → heap (O(log n)). Agar "sorted mein
dhoondhna" → binary search (O(log n)). Yeh table structure-choice guide karta.

> **Yaad rakhne wali baat:** Array: index O(1), search O(n), insert-middle O(n). Hash-map: lookup/
> insert O(1) (superpower). Heap: push/pop O(log n), peek O(1). Balanced BST: search O(log n).
> Sorting O(n log n). "Kaunsa operation baar-baar chahiye" se structure chuno.

[↑ Back to top](#top)

---

<a id="s2-7"></a>
## 2.7 — Nayi problem ko kaise approach karein (framework)

Interview mein ek nayi problem saamne aaye — kaise shuru karein taaki blank na ho? Yeh ek soch-ka-
framework hai (Ch 1.7 ke "bolke solve" ka andar-wala thought process).

**5-step problem-solving framework:**

**Step 1 — Samjho + examples banao:** problem padho, apne shabdon mein dohrao. Ek chhota input-output
example khud banao (jaise Two Sum: `[2,7,11], 9 → [0,1]`). Isse problem concrete ho jata, aur pattern
dikhne lagta.

**Step 2 — Brute-force socho (chahe slow):** "sabse seedha kya kar sakta hoon?" Usually nested loops
(O(n^2)) ya sab combinations try. Yeh baseline deta — kuch toh solve hua. Bolo ise (Ch 1.7 step 3).

**Step 3 — Pattern pehchano (yeh asli skill):** poocho "yeh kis pattern jaisa hai?" Signals:
- Sorted array / "pair dhoondho" → **two pointers** (Ch 03).
- "Contiguous subarray/substring" → **sliding window** (Ch 03).
- "Fast lookup / dekha hai kya" → **hashing** (Ch 04).
- "Top-K / sabse bade-chhote" → **heap** (Ch 09).
- "Sorted mein dhoondhna / answer-space" → **binary search** (Ch 11).
- "Tree/graph traversal" → **BFS/DFS** (Ch 08/10).
- "Choices + backtrack / all combinations" → **backtracking** (Ch 07).
- "Overlapping subproblems / optimal" → **DP** (Ch 12).
(Yeh signal→pattern mapping Ch 13 mein poora — yeh interview ki chaabi hai.)

**Step 4 — Optimize using pattern:** jo pattern pehchana, use apply karke brute-force se better karo.
Complexity bolo (O(n^2) → O(n)).

**Step 5 — Edge cases + dry-run:** empty input? single element? duplicates? negatives? Code ko ek
example pe trace karo (bug pakadne).

**Sabse zaroori — Step 3 (pattern):** 90% DSA problems ~15-20 patterns mein se ek hain. Aapka kaam
"naya algorithm invent karna" nahi — "yeh kaunsa jaana-pehchana pattern hai" pehchanna. Isliye yeh
guide patterns pe focus karta. Jitne patterns solid, utni jaldi aap Step 3 kar loge.

> **Yaad rakhne wali baat:** 5-step: (1) samjho+example banao, (2) brute-force socho, (3) PATTERN
> pehchano (signal→pattern: sorted/pair→two-pointer, subarray→sliding-window, lookup→hashing,
> top-K→heap...), (4) optimize, (5) edge-cases+dry-run. Step 3 = asli skill. 90% problems = ~15-20
> known patterns.

[↑ Back to top](#top)

---

<a id="s2-8"></a>
## 2.8 — Nuances aur common galtiyan

- **Constants matter karte real life mein, Big-O mein nahi:** O(n) "hamesha" O(n^2) se fast nahi —
  chhote input pe O(n^2) tez ho sakta (constants ki wajah se). Par interview/bade-input mein Big-O
  sahi guide hai. Chhote n pe over-optimize mat karo.

- **"Average" vs "worst" case:** hash-map lookup **average** O(1), worst O(n) (rare). Quicksort
  average O(n log n), worst O(n^2). Interview mein usually average bolte, par worst pata hona
  chahiye (interviewer pooch sakta).

- **Recursion ka hidden space (2.4):** log recursion ko O(1) space samajh lete kyunki koi array nahi
  banaya — par call stack O(depth) leta. n-deep recursion = O(n) space. Yeh yaad rakho.

- **`in` operator ki complexity (Python-specific):** `x in list` = **O(n)** (ek-ek dekhna!), par
  `x in set` / `x in dict` = **O(1)**. Log galti se list pe `in` loop mein use karke O(n^2) bana
  dete. Fast lookup chahiye toh set/dict.

- **String concatenation Python mein (chhupa O(n^2)):** loop mein `s += char` baar-baar naya string
  banata (strings immutable) → O(n^2). Iske bajaye list mein collect karke `"".join(list)` — O(n).
  (Ch 05 mein.)

- **`.append()` O(1), par `.insert(0, x)` O(n):** list ke end pe add O(1), par shuru/beech mein add
  O(n) (baaki shift). Front-add baar-baar chahiye toh `collections.deque` (O(1) both ends, Ch 06).

- **Log ignore karte "small" loop ko:** `for i in range(len(arr)): if arr[i] in arr[i+1:]` — yeh
  O(n^2) hai (`arr[i+1:]` slice + `in` dono O(n)). Chhota dikhne wala code bhi O(n^2) ho sakta —
  dhyan se count karo.

> **Yaad rakhne wali baat:** Big-O bade input ke liye (chhote pe constants matter). Average vs worst
> jaano (hashmap avg O(1)). Recursion = O(depth) hidden space. Python: `in list` O(n) BUT `in set/
> dict` O(1); `s += ` loop mein O(n^2) (use join); `insert(0)` O(n) (use deque). Chhota code bhi
> O(n^2) ho sakta.

[↑ Back to top](#top)

---

<a id="s2-9"></a>
## 2.9 — Yaad rakhne wali baatein

1. **Big-O = growth rate** (input badhne pe kaam kitna guna). Sirf bada term, constants ignore.
   Order: O(1) < O(log n) < O(n) < O(n log n) < O(n^2).
2. **Complexity nikalna:** ek loop O(n), nested multiply (n^2), sequential add, aadha-kaatna
   O(log n). Loop-andar function-call bhi count.
3. **Space = extra memory** (input nahi). O(1) variables, O(n) naya array/n-deep recursion.
4. **Time-space tradeoff:** zyada memory se time bacha sakte (Two Sum: brute O(n^2)/O(1) vs hash
   O(n)/O(n)). Tradeoff bolna senior-signal.
5. **Cheat-table:** array index O(1)/search O(n); hash-map O(1); heap O(log n); BST O(log n);
   sort O(n log n). "Kaunsa operation baar-baar" se structure chuno.
6. **Nayi problem framework (5-step):** samjho+example → brute-force → **pattern pehchano** →
   optimize → edge-cases+dry-run. Step 3 = asli skill.
7. **Python gotchas:** `in list` O(n) vs `in set` O(1); `s +=` loop O(n^2) (use join); recursion
   hidden O(depth) space.

> **Chapter ka mantra:** Big-O aapko batata "yeh solution kaafi fast hai ya nahi", aur framework
> batata "nayi problem pe kahan se shuru karun". Yeh do neev hain — inke saath aage ke patterns
> "samajh" aayenge, ratna nahi. Chalo ab pehla bada topic — arrays (sabse zyada aata).

[↑ Back to top](#top)

---

> **Chapter 02 khatam.** Ab tak: Big-O (growth rate, common complexities O(1) se O(n^2)); time
> complexity nikalna (loops); space complexity (+ recursion hidden); time-space tradeoff; complexity
> cheat-table; 5-step problem-approach framework (pattern pehchano); Python gotchas. **Agla chapter
> (03):** Arrays — two-pointer, sliding-window, prefix-sum, Kadane's, merge-intervals (sabse
> high-frequency topic).

[↑ Back to top](#top)
