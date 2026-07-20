<a id="top"></a>
# Chapter 11 — Binary Search aur Sorting

**Binary search** = sorted data mein "aadha-aadha kaat ke" O(log n) mein dhoondhna — bahut fast, aur
interview mein common (Ch 1.4 — MEDIUM, ~8%). **Sorting** samajhna (kaunsa algo, kab) bhi zaroori.
Yeh chapter binary-search ke variants (jo asli skill hai) aur sorting-overview sikhata.

Clear examples + dry-run ke saath.

---

## Is chapter ka index

- [11.1 — Binary Search basics (classic)](#s11-1)
- [11.2 — Boundary search (leftmost / rightmost)](#s11-2)
- [11.3 — Binary search on answer-space (yeh powerful)](#s11-3)
- [11.4 — Rotated sorted array search](#s11-4)
- [11.5 — Sorting overview (kaunsa algo kab)](#s11-5)
- [11.6 — Quickselect (Kth element, O(n) avg)](#s11-6)
- [11.7 — Custom sort (Python key)](#s11-7)
- [11.8 — Nuances, edge cases](#s11-8)
- [11.9 — Yaad rakhne wali baatein](#s11-9)

---

<a id="s11-1"></a>
## 11.1 — Binary Search basics (classic)

**Binary search** = ek **sorted** array mein target dhoondhna, har step mein search-space **aadha**
kaat ke. O(log n) — bahut fast (Ch 2.2). Sirf **sorted** pe kaam karta (yeh zaroori condition).

**Kab pehchano (signal):** "sorted array", "dhoondho", "log n chahiye", "answer-space mein search"
(11.3).

**Classic binary search (yeh template YAAD rakho):**
```python
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1        # search range: [lo, hi]
    while lo <= hi:
        mid = (lo + hi) // 2         # beech
        if arr[mid] == target:
            return mid               # mil gaya!
        elif arr[mid] < target:
            lo = mid + 1             # target bada -> right half (mid chhod do)
        else:
            hi = mid - 1             # target chhota -> left half
    return -1                        # nahi mila
```

**Logic kyun (aadha-aadha):** array sorted hai. `mid` dekho — target `mid` se bada hai toh woh
**right half** mein hoga (left half + mid chhod do, `lo = mid+1`); chhota toh **left half**
(`hi = mid-1`). Har step mein aadha search-space gaya → ~log2(n) steps → **O(log n).** (1 million
items ~20 steps!)

**Dry-run (Input arr=[1,3,5,7,9,11], target=7):**
```
lo=0, hi=5: mid=2, arr[2]=5 < 7 -> lo=3
lo=3, hi=5: mid=4, arr[4]=9 > 7 -> hi=3
lo=3, hi=3: mid=3, arr[3]=7 == 7 -> return 3  ✓
```

**Do common bugs (dhyan se):**
1. **`lo <= hi` (not `<`):** loop condition `<=` — warna single-element range miss. Yaad rakho `<=`.
2. **`mid = (lo + hi) // 2`:** integer overflow bade numbers pe (kuch languages) — Python mein theek,
   par `lo + (hi-lo)//2` safe convention.
3. **Infinite loop:** `lo`/`hi` update galat (jaise `lo = mid` bina +1) → kabhi na ruke. `mid+1`/
   `mid-1` zaroori.

> **Yaad rakhne wali baat:** Binary search = SORTED array, aadha-aadha kaat, O(log n). Template:
> `lo,hi=0,n-1; while lo<=hi: mid; ==return; <lo=mid+1; else hi=mid-1`. Bugs: `<=` (not `<`), `mid+1/
> mid-1` (infinite bachaao). Sirf sorted pe.

[↑ Back to top](#top)

---

<a id="s11-2"></a>
## 11.2 — Boundary search (leftmost / rightmost)

Kabhi target multiple baar hota, aur aapko **pehla (leftmost)** ya **aakhri (rightmost)** occurrence
chahiye. Ya "target se bada pehla element" (insert position). Yeh binary-search ka variant — bahut
aata.

**Kab pehchano (signal):** "first/last occurrence", "insert position", "smallest element >= target",
"count of target".

**Leftmost (first occurrence / insert position):**

**Problem:** sorted array mein `target` ka **pehla** index (ya jahan insert karna, agar nahi hai).
```
Input:  arr=[1, 2, 2, 2, 3], target=2  -> Output: 1  (pehla 2, index 1)
Input:  arr=[1, 3, 5], target=4        -> Output: 2  (4 nahi, insert at index 2)
```
```python
def left_bound(arr, target):
    lo, hi = 0, len(arr)             # note: hi = len (not len-1)
    while lo < hi:                   # note: < (not <=)
        mid = (lo + hi) // 2
        if arr[mid] < target:
            lo = mid + 1             # target right mein
        else:
            hi = mid                 # arr[mid] >= target -> yeh candidate, left mein aur dekho
    return lo                        # leftmost position
```

**Logic kyun (boundary variant — thoda alag):** yahan hum "exact match" pe ruk nahi jate — hum
**leftmost** dhoondhte hain jahan condition (`>= target`) pehli baar true ho. Jab `arr[mid] >=
target`, woh candidate hai par aur left mein bhi ho sakta — toh `hi = mid` (mid ko rakho, aur left
dekho). `< target` toh right (`lo = mid+1`). `lo == hi` pe boundary. **O(log n).** (Yeh
`bisect_left` — Python `bisect` module isi ko deta.)

**Dry-run (Input arr=[1,2,2,2,3], target=2):**
```
lo=0, hi=5: mid=2, arr[2]=2 >= 2 -> hi=2
lo=0, hi=2: mid=1, arr[1]=2 >= 2 -> hi=1
lo=0, hi=1: mid=0, arr[0]=1 < 2 -> lo=1
lo=1, hi=1: loop end. return 1  ✓  (pehla 2)
```

**Python shortcut (`bisect`):** Python mein `bisect.bisect_left(arr, target)` (leftmost) aur
`bisect.bisect_right(arr, target)` (rightmost+1) ready hain — interview mein use kar sakte (ya manual
likho, dono theek). Count of target = `bisect_right - bisect_left`.

> **Yaad rakhne wali baat:** Boundary search (leftmost/rightmost): exact-match pe mat ruko, condition
> pehli-baar-true dhoondho. Leftmost: `hi=len; while lo<hi; >=target hi=mid, <target lo=mid+1`. O(log
> n). Python `bisect_left/right`. Signal: first/last occurrence, insert-position, count.

[↑ Back to top](#top)

---

<a id="s11-3"></a>
## 11.3 — Binary search on answer-space (yeh powerful)

Yeh binary-search ka sabse powerful (aur "aha!") use — jab aap **answer ki value pe** binary-search
karte ho, array pe nahi. Jab problem "minimum/maximum X dhoondho jismein condition satisfy ho" ho,
aur X badhne pe condition monotonic (ek taraf true, doosri false) ho.

**Kab pehchano (signal):** "minimum/maximum value such that [condition]", "smallest capacity/speed/
size jismein possible", "can we do it in X?" jahan X badhane se easier hota.

**Problem — Koko Eating Bananas (classic answer-space):**

**Problem:** `piles` (banana piles), `h` hours. Koko ek speed `k` (bananas/hour) chunti. Minimum `k`
dhoondho jismein woh saare bananas `h` hours mein kha le.
```
Input:  piles=[3, 6, 7, 11], h=8  -> Output: 4
        (speed 4 se: pile 3->1hr, 6->2hr, 7->2hr, 11->3hr = 8 hrs. speed 3 se zyada lagega)
```
```python
def min_eating_speed(piles, h):
    import math
    def hours_needed(k):              # speed k pe kitne hours
        return sum(math.ceil(pile / k) for pile in piles)

    lo, hi = 1, max(piles)            # answer-space: speed 1 se max-pile tak
    while lo < hi:
        mid = (lo + hi) // 2          # try speed mid
        if hours_needed(mid) <= h:    # is speed se ho jaata?
            hi = mid                  # haan -> aur km speed try (left)
        else:
            lo = mid + 1              # nahi -> zyada speed chahiye (right)
    return lo                         # minimum valid speed
```

**Logic kyun (yeh core "aha" — dhyan se):** hum **speed `k` ki value pe** binary-search kar rahe (na
ki piles array pe). Answer-space = 1 se max-pile (possible speeds). Har `mid` (speed) pe check karo
"kya is speed se `h` hours mein ho jaata?" (monotonic: zyada speed → km hours, toh ek point ke baad
sab valid). Valid speed pe aur km try (left), invalid pe zyada (right). Boundary = minimum valid.
**O(n log(max-pile))** — log answer-space × O(n) check.

**Dry-run (Input piles=[3,6,7,11], h=8):**
```
lo=1, hi=11: mid=6, hours(6)=1+1+2+2=6 <= 8 -> hi=6
lo=1, hi=6: mid=3, hours(3)=1+2+3+4=10 > 8 -> lo=4
lo=4, hi=6: mid=5, hours(5)=1+2+2+3=8 <= 8 -> hi=5
lo=4, hi=5: mid=4, hours(4)=1+2+2+3=8 <= 8 -> hi=4
lo=4, hi=4: end. return 4  ✓
```

**Yeh recognize karna skill hai:** "minimum/maximum X such that condition" + "X badhane se
monotonic" → **binary-search on answer-space**. Examples: min-speed, min-capacity (ship packages),
min-largest-sum (split array), min-days. Yeh aata hai aur log ise miss karte (brute-force try
karte). Signal pakdna = senior skill.

> **Yaad rakhne wali baat:** Binary-search on answer-space: **value pe search** (array pe nahi), jab
> "min/max X such that condition" + monotonic (X badhane se ek-taraf-valid). Range = possible answers,
> `mid`=try-value, `check(mid)` valid? → left/right. O(n log(range)). Signal: "minimum/maximum X
> jismein possible". Powerful, recognize karo.

[↑ Back to top](#top)

---

<a id="s11-4"></a>
## 11.4 — Rotated sorted array search

Ek classic binary-search variant — sorted array jo ek point pe "rotate" (ghuma) ho gaya. Isme
target dhoondhna O(log n) mein (binary-search adapt karke).

**Rotated array kya:** `[4,5,6,7,0,1,2]` — yeh `[0,1,2,4,5,6,7]` tha jo rotate hua. Ek "pivot" ke
aage-peeche do sorted parts.

**Problem — Search in Rotated Sorted Array:**

**Problem:** rotated sorted array mein `target` ka index (ya -1).
```
Input:  arr=[4,5,6,7,0,1,2], target=0  -> Output: 4
Input:  arr=[4,5,6,7,0,1,2], target=3  -> Output: -1
```
```python
def search_rotated(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        # kaunsa half sorted hai?
        if arr[lo] <= arr[mid]:          # LEFT half sorted
            if arr[lo] <= target < arr[mid]:
                hi = mid - 1             # target left-sorted-half mein
            else:
                lo = mid + 1
        else:                            # RIGHT half sorted
            if arr[mid] < target <= arr[hi]:
                lo = mid + 1             # target right-sorted-half mein
            else:
                hi = mid - 1
    return -1
```

**Logic kyun (thoda tricky — dhyan se):** rotated array mein `mid` ke ek taraf **hamesha sorted**
hota (dono nahi ho sakte un-sorted). Pehle pata karo kaunsa half sorted (`arr[lo] <= arr[mid]` →
left sorted). Phir check karo target us **sorted half ke range** mein hai kya — hai toh wahan jaao,
warna doosre half. Isse har step aadha kaat dete (binary-search adapt). **O(log n).**

**Dry-run (Input arr=[4,5,6,7,0,1,2], target=0):**
```
lo=0,hi=6: mid=3, arr[3]=7 != 0. arr[0]=4<=arr[3]=7 (left sorted). 4<=0<7? no -> lo=4
lo=4,hi=6: mid=5, arr[5]=1 != 0. arr[4]=0<=arr[5]=1 (left sorted). 0<=0<1? yes -> hi=4
lo=4,hi=4: mid=4, arr[4]=0 == 0 -> return 4  ✓
```

> **Yaad rakhne wali baat:** Rotated-sorted-array search = binary-search adapt: `mid` ke ek taraf
> hamesha sorted. Pata karo kaunsa half sorted (`arr[lo]<=arr[mid]`), target us range mein hai toh
> wahan jaao. O(log n). Signal: "rotated sorted array + search".

[↑ Back to top](#top)

---

<a id="s11-5"></a>
## 11.5 — Sorting overview (kaunsa algo kab)

Interview mein aapko har sorting-algorithm khud implement karna rarely padta — par **kaunsa kab, aur
unki complexity** samajhna zaroori (aur Python ka `sorted` use karna). Yeh overview.

**Common sorting algorithms (samajhne ko):**

| Algorithm | Time (avg) | Space | Note |
|---|---|---|---|
| **Merge sort** | O(n log n) | O(n) | Stable, guaranteed n log n (divide-and-conquer) |
| **Quick sort** | O(n log n) avg | O(log n) | Fast in practice, worst O(n^2) (bad pivot) |
| **Heap sort** | O(n log n) | O(1) | In-place, heap se (Ch 09) |
| **Bubble/Insertion** | O(n^2) | O(1) | Slow, sirf chhote/nearly-sorted mein |
| **Python `sorted`** | O(n log n) | O(n) | Timsort (merge+insertion), stable — YEH USE KARO |

**Merge sort intuition (divide-and-conquer):** array ko aadha-aadha todo (jab tak single elements),
phir sorted halves ko merge karo (Ch 6.4 merge jaisa). Guaranteed O(n log n), stable. Recursion (Ch
07).

**Quick sort intuition (partition):** ek "pivot" chuno, array ko partition karo (pivot se chhote
left, bade right), phir dono halves recursively sort. Avg O(n log n), par bad pivot pe O(n^2).
Quickselect (11.6) isi ka rishtedar.

**Interview mein (practical):**
- **99% baar `sorted(arr)` ya `arr.sort()` use karo** — Python ka Timsort O(n log n), stable,
  optimized. Khud implement karne ki zaroorat nahi (jab tak specifically na poocha jaye).
- **Complexity jaano** — "sorting O(n log n) hai" bolna. Aur "sorting se yeh problem unlock hoti"
  (jaise merge-intervals Ch 3.8, two-pointer-after-sort).
- **`sort()` vs `sorted()`:** `arr.sort()` in-place (arr badalta), `sorted(arr)` naya list (arr
  same). Chuno kya chahiye.

**Stable sort kya (kabhi matter karta):** stable = equal elements ka original order preserve. Python
`sorted` stable. Jab aap multiple keys pe sort karo (pehle ek, phir doosre), stability matter
karti.

> **Yaad rakhne wali baat:** Sorting: merge (O(n log n), stable, O(n) space), quick (O(n log n) avg,
> O(n^2) worst), heap (O(n log n), O(1)). Interview: **`sorted(arr)`/`arr.sort()` use karo** (Timsort,
> O(n log n), stable) — khud mat likho. Jaano: complexity + "sorting unlocks problem". `sort()`
> in-place vs `sorted()` naya.

[↑ Back to top](#top)

---

<a id="s11-6"></a>
## 11.6 — Quickselect (Kth element, O(n) avg)

**Quickselect** = quicksort ka partition-idea use karke **Kth smallest/largest** element O(n) average
mein dhoondhna (poora sort O(n log n) ke bina). Top-K (Ch 9.3) ka ek alternative.

**Kab pehchano (signal):** "Kth largest/smallest", "median" (Kth), one-shot top-K (streaming nahi).

**Quickselect (Kth largest):**
```python
import random

def quickselect(nums, k):        # kth LARGEST
    k = len(nums) - k            # kth largest = (n-k)th smallest (0-indexed)
    def partition(lo, hi):
        pivot = nums[hi]         # pivot (aakhri)
        i = lo
        for j in range(lo, hi):
            if nums[j] <= pivot:
                nums[i], nums[j] = nums[j], nums[i]
                i += 1
            nums[i], nums[hi] = nums[hi], nums[i]
        return i                 # pivot ki final position
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        p = partition(lo, hi)
        if p == k:
            return nums[p]       # Kth element mil gaya
        elif p < k:
            lo = p + 1           # right half
        else:
            hi = p - 1           # left half
```

**Logic kyun (partition + binary-search jaisa):** quicksort mein partition ek pivot ko uski **final
sorted position** pe rakh deta (chhote left, bade right). Agar woh position = k (jo humein chahiye),
mil gaya! Warna sirf ek half mein aage dhoondho (binary-search jaisa — doosra half chhod do). Kyunki
sirf **ek** half recurse (dono nahi, jaise quicksort), avg **O(n)** (n + n/2 + n/4 + ... = 2n).
Worst O(n^2) (bad pivot — random pivot se avoid).

**Quickselect vs Heap (Ch 9.7 recap):**
- **Quickselect:** O(n) avg, **one-shot** (array pe ek baar), fastest. Worst O(n^2). Array modify
  karta.
- **Heap (size-K):** O(n log k), **streaming** OK, stable. Slightly slower par safe.
- One-shot fastest → quickselect. Streaming/safe → heap.

> **Yaad rakhne wali baat:** Quickselect = quicksort-partition se Kth-element, O(n) avg (worst
> O(n^2)). Partition pivot ko final-position pe rakhta; agar =k mila, warna ek-half recurse (binary-
> search jaisa). One-shot Kth fastest. Heap alternative (streaming/safe). Signal: Kth largest/smallest.

[↑ Back to top](#top)

---

<a id="s11-7"></a>
## 11.7 — Custom sort (Python key)

Interview mein aksar "custom order" mein sort karna padta — jaise objects ko kisi field pe, ya
multiple criteria pe. Python ka `key` parameter yeh aasaan karta.

**Basic custom sort (`key`):**
```python
# strings ko length ke hisaab se
words = ["banana", "apple", "cherry"]
words.sort(key=len)               # ['apple', 'cherry', 'banana'] (length se)

# tuples ko doosre element se
pairs = [(1, 3), (2, 1), (3, 2)]
pairs.sort(key=lambda x: x[1])    # [(2,1), (3,2), (1,3)] (second element se)

# descending (reverse)
nums = [3, 1, 2]
nums.sort(reverse=True)           # [3, 2, 1]
```
- **`key=function`** — har element pe function laga ke, us result pe sort. `key=len` (length),
  `key=lambda x: x[1]` (custom field). `reverse=True` (descending). Yeh 99% custom-sort cover karta.

**Multiple criteria (tuple key — yeh yaad rakho):**
```python
# pehle age se, phir name se (age same ho toh name)
people = [("Amit", 30), ("Bhavna", 25), ("Chetan", 30)]
people.sort(key=lambda x: (x[1], x[0]))   # (age, name) tuple key
# [("Bhavna",25), ("Amit",30), ("Chetan",30)]  (age pehle, tie pe name)
```
- **Tuple key** = multiple criteria: pehle tuple ke first pe sort, tie ho toh second pe, etc. Bahut
  powerful — "pehle X se phir Y se" ek line mein.

**Mixed ascending/descending:** ek field ascending, doosra descending — negate karo (numbers pe):
`key=lambda x: (x[1], -x[0])` (age ascending, tie pe id descending).

**Interview use:** custom sort aksar ek problem ka **first step** hota (jaise merge-intervals Ch 3.8
mein `sort(key=lambda x: x[0])`). Sorting se problems "unlock" hoti (Ch 11.5) — sahi key chunna
skill.

> **Yaad rakhne wali baat:** Custom sort: `arr.sort(key=func)` — `key=len`, `key=lambda x: x[1]`
> (field). `reverse=True` (descending). Multiple criteria = **tuple key** `(x[1], x[0])` (pehle x[1]
> tie pe x[0]). Mixed asc/desc = negate. Sorting aksar problem ka first-step.

[↑ Back to top](#top)

---

<a id="s11-8"></a>
## 11.8 — Nuances, edge cases

**Signal→pattern:**

| Signal | Pattern | Section |
|---|---|---|
| Sorted array + dhoondho | Classic binary search | 11.1 |
| First/last occurrence, insert-pos, count | Boundary search (leftmost/rightmost) | 11.2 |
| "Min/max X such that condition" + monotonic | Binary search on answer-space | 11.3 |
| Rotated sorted array + search | Rotated binary search | 11.4 |
| Kth largest/smallest (one-shot) | Quickselect | 11.6 |
| Custom order / multi-criteria | `sort(key=...)` | 11.7 |

**Binary search edge cases (HAMESHA — bug-prone):**
- **Empty array** — `lo > hi` turant, return -1. Handle.
- **Single element** — `lo == hi`, ek check. `<=` condition zaroori (11.1).
- **Target not present** — classic returns -1; boundary returns insert-position.
- **Duplicates** — classic koi ek index deta; leftmost/rightmost (11.2) specific chahiye toh boundary.
- **Overflow** (`(lo+hi)//2`) — Python theek, par `lo + (hi-lo)//2` safe habit.
- **Infinite loop** — `lo`/`hi` update mein `mid+1`/`mid-1` (classic) ya `hi=mid`/`lo=mid+1`
  (boundary) — galat mix = infinite. Template yaad rakho.

**Sorting edge cases:**
- **Empty / single** — sorted (no-op).
- **Already sorted / reverse** — Timsort already-sorted pe fast (O(n)).
- **Stability** — equal elements order matter kare toh stable (Python `sorted` stable).

**Kab binary search NAHI:** array **unsorted** ho aur sort karne ka cost justify na ho (binary
search sorted maangta). Ek-baar search unsorted mein = linear O(n) (sort O(n log n) se sasta agar
sirf ek query). Baar-baar search → sort once + binary search.

> **Yaad rakhne wali baat:** BS signals: sorted-search (classic), first/last (boundary), min/max-X
> (answer-space), rotated (adapt), Kth (quickselect). Edge: empty/single/duplicates/`<=`/infinite-
> loop (template yaad). Custom sort = key/tuple-key. BS sirf sorted; unsorted+one-query = linear.

[↑ Back to top](#top)

---

<a id="s11-9"></a>
## 11.9 — Yaad rakhne wali baatein (chapter recap)

1. **Binary search classic** (11.1): SORTED array, aadha-kaat, O(log n). `lo<=hi`, `mid+1/mid-1`.
   Bugs: `<=`, infinite-loop.
2. **Boundary search** (11.2): leftmost/rightmost occurrence, insert-pos. `hi=len`, `lo<hi`, condition
   pe hi=mid/lo=mid+1. Python `bisect`.
3. **Answer-space** (11.3): value pe search (not array) — "min/max X such that condition" + monotonic.
   Powerful, recognize karo (Koko, ship-capacity).
4. **Rotated array** (11.4): `mid` ke ek taraf sorted, target range-check. O(log n).
5. **Sorting overview** (11.5): merge/quick/heap O(n log n). Interview: `sorted()` use karo (Timsort,
   stable). Complexity jaano.
6. **Quickselect** (11.6): Kth element O(n) avg (partition + one-half recurse). One-shot fastest.
7. **Custom sort** (11.7): `sort(key=...)`, tuple-key multi-criteria, reverse.

> **Chapter ka mantra:** Binary search = "sorted + aadha-kaat, O(log n)". Asli skill = **variants**:
> boundary (first/last), aur **answer-space** (min/max-X — yeh recognize karna sabse valuable). Sorting
> khud mat likho (`sorted()`), par complexity + "sorting unlocks problem" jaano. LeetCode pe 3-4
> binary-search problems (khaaskar answer-space).

[↑ Back to top](#top)

---

> **Chapter 11 khatam.** Ab tak: binary search (classic, boundary/leftmost-rightmost, answer-space,
> rotated); sorting overview (merge/quick/heap, use `sorted`); quickselect (Kth, O(n) avg); custom
> sort (key/tuple-key). **Agla chapter (12):** Dynamic Programming + Greedy — memoization→tabulation,
> 1D/2D DP, knapsack, LCS, greedy-vs-DP.

[↑ Back to top](#top)