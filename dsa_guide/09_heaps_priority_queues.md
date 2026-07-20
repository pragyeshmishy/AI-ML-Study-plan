<a id="top"></a>
# Chapter 09 — Heaps aur Priority Queues

**Heap** ek special tree-based structure hai jo **min ya max element turant (O(1))** deta, aur
push/pop O(log n) mein. Iska #1 use: **top-K** problems (sabse bade/chhote K elements) — jo ML mein
bhi aata (top-K recommendations, streaming). Ch 1.4 — MEDIUM, ~7%.

Clear examples + dry-run + Python `heapq` ke saath.

---

## Is chapter ka index

- [9.1 — Heap kya hai (min-heap / max-heap)](#s9-1)
- [9.2 — Python heapq (min-heap) + gotchas](#s9-2)
- [9.3 — Pattern: Top-K elements](#s9-3)
- [9.4 — Pattern: K most frequent](#s9-4)
- [9.5 — Pattern: K-way merge](#s9-5)
- [9.6 — Pattern: Two heaps (running median)](#s9-6)
- [9.7 — Heap vs Sorting vs Quickselect (kab kaunsa)](#s9-7)
- [9.8 — Nuances, edge cases](#s9-8)
- [9.9 — Yaad rakhne wali baatein](#s9-9)

---

<a id="s9-1"></a>
## 9.1 — Heap kya hai (min-heap / max-heap)

**Heap** = ek binary tree jismein ek property: **min-heap** mein har parent apne children se **chhota**
(toh root = sabse chhota); **max-heap** mein parent bada (root = sabse bada). Isse **min/max element
turant (O(1))** milta (root pe), aur add/remove O(log n).

**Do types:**
- **Min-heap:** root = **sabse chhota**. Parent < children. "Sabse chhota jaldi chahiye."
- **Max-heap:** root = **sabse bada**. Parent > children. "Sabse bada jaldi chahiye."

**Min-heap dikhta kaisa:**
```
        1          <- root = sabse chhota (min-heap)
       / \
      3   2        Har parent < children (1<3, 1<2, 3<5, 3<4)
     / \
    5   4
```
- Root (1) = minimum. **Note:** heap fully sorted NAHI — sirf parent-child property. Par root hamesha
  min (min-heap) — yeh kaafi hai top-K ke liye.

**Kyun heap (kya problem solve karta):** socho aapko baar-baar "sabse chhota (ya bada) element
nikaalna" hai (aur naye add karne hai). List mein: min dhoondhna O(n) har baar. Sorted rakhna: insert
O(n). **Heap:** min O(1) peek, pop O(log n), push O(log n) — bahut better jab baar-baar min/max
chahiye. Yeh top-K, median, scheduling mein aata.

**Complexity (yaad rakho):**
- **Peek** (min/max dekho, nikaalo nahi) — **O(1)** (root pe).
- **Push** (add) — **O(log n)** (tree mein sahi jagah "bubble up").
- **Pop** (min/max nikaalo) — **O(log n)** ("re-heapify").
- **Build heap** from n items — **O(n)**.

**"Priority Queue" = heap ka doosra naam:** priority queue ek abstract idea hai — "highest/lowest
priority wala pehle nikalo". Heap uska common implementation hai. Interview mein dono words same
maano.

> **Yaad rakhne wali baat:** Heap = tree jahan root = min (min-heap) ya max (max-heap); parent-child
> property (fully sorted nahi). Min/max peek O(1), push/pop O(log n). Kab: baar-baar min/max chahiye
> (top-K, median). Priority-queue = heap ka doosra naam.

[↑ Back to top](#top)

---

<a id="s9-2"></a>
## 9.2 — Python heapq (min-heap) + gotchas

Python mein heap `heapq` module se — par ek **bada gotcha: `heapq` sirf MIN-heap hai** (max-heap ke
liye trick chahiye). Yeh yaad rakhna zaroori.

**Basic heapq (min-heap):**
```python
import heapq

heap = []
heapq.heappush(heap, 5)      # add — O(log n)
heapq.heappush(heap, 1)
heapq.heappush(heap, 3)
print(heap[0])               # 1  — peek min (root), O(1)
smallest = heapq.heappop(heap)  # 1 — pop min, O(log n)

# List ko heap banao (in-place, O(n))
nums = [5, 1, 3, 2]
heapq.heapify(nums)          # ab nums ek min-heap — O(n)
print(nums[0])               # 1 (min)
```
- `heappush` (add), `heappop` (min nikaalo), `heap[0]` (peek min), `heapify` (list→heap). Sab min-
  heap.

**GOTCHA 1 — Max-heap ke liye negate karo (yeh yaad rakho):** `heapq` sirf min. Max-heap chahiye toh
**values ko negative** karke push karo (sabse bada → sabse chhota-negative → root), pop pe wapas
negate:
```python
max_heap = []
heapq.heappush(max_heap, -5)     # -5 (actual 5)
heapq.heappush(max_heap, -1)     # -1 (actual 1)
largest = -heapq.heappop(max_heap)  # -(-5) = 5 (actual max)
```
- Negate trick: `-value` push, `-pop` = actual max. Yeh interview mein bahut use hota (max-heap
  simulate).

**GOTCHA 2 — Tuples for priority (sort by first element):** items ko `(priority, value)` tuple ke
roop mein push karo — heap first element se sort karta:
```python
heapq.heappush(heap, (2, "task_b"))   # priority 2
heapq.heappush(heap, (1, "task_a"))   # priority 1
p, task = heapq.heappop(heap)         # (1, "task_a") — lowest priority pehle
```
- **Gotcha within gotcha:** agar priorities same ho, heap **second element** se compare karega —
  agar woh comparable na ho (jaise custom object) toh error. Tab `(priority, index, item)` (unique
  index tie-break) use karo.

**GOTCHA 3 — heapify O(n), sorting O(n log n):** poore list ko heap banana `heapify` O(n) hai (sort
O(n log n) se fast) — yeh top-K mein kaam aata (9.3).

> **Yaad rakhne wali baat:** Python `heapq` = **MIN-heap only**. `heappush`/`heappop`/`heap[0]`(peek)/
> `heapify`(O(n)). MAX-heap: values NEGATE karo (`-x` push, `-pop`). Priority: `(priority, value)`
> tuples (same-priority pe `(pri, idx, item)` tie-break). heapify O(n).

[↑ Back to top](#top)

---

<a id="s9-3"></a>
## 9.3 — Pattern: Top-K elements

Heap ka **#1 use** — "sabse bade/chhote K elements" (poora sort kiye bina). ML mein bhi aata (top-K
predictions). Yeh pattern zaroor yaad.

**Kab pehchano (signal):** "top K", "K largest/smallest", "K closest", "Kth largest".

**Problem — K Largest Elements:**

**Problem:** array `nums` aur `k` diya. K sabse bade elements dhoondho.
```
Input:  nums=[3, 1, 5, 12, 2, 11], k=3   -> Output: [11, 12, 5] (ya kisi order mein, 3 sabse bade)
```

**Approach — Min-heap of size K (yeh clever, O(n log k)):**
```python
import heapq

def k_largest(nums, k):
    min_heap = []
    for num in nums:
        heapq.heappush(min_heap, num)     # add
        if len(min_heap) > k:             # size K se zyada?
            heapq.heappop(min_heap)        # sabse chhota nikaalo (min-heap root)
    return min_heap                        # bache hue K = K largest
```

**Logic kyun (yeh core insight — dhyan se):** hum ek **size-K min-heap** rakhte hain. Har element add
karte, par size K se zyada ho toh **min (sabse chhota) nikaal dete**. Toh heap mein hamesha "ab tak
ke K sabse bade" bache rehte (chhote nikal gaye). Ant mein heap = K largest. Kyun min-heap for
K-**largest**? Kyunki hum sabse chhote ko baar-baar hatana chahte (taaki bade bachen) — min-heap root
= sabse chhota, jaldi nikaal do. **O(n log k)** (n elements, har push/pop O(log k) — heap size K).

**Kyun O(n log k) achha (sorting se better jab k chhota):** poora sort O(n log n). Par sirf top-K
chahiye toh size-K heap O(n log k) — jab k << n (jaise top-10 of a million), yeh bahut fast. Yeh
tradeoff bolna interview mein achha (Ch 1.7).

**Dry-run (Input nums=[3,1,5,12,2,11], k=3):**
```
push 3: heap=[3]
push 1: heap=[1,3]
push 5: heap=[1,3,5] (size 3)
push 12: heap=[1,3,5,12], size>3 -> pop min 1. heap=[3,12,5]
push 2: heap=[2,3,5,12], size>3 -> pop min 2. heap=[3,12,5]
push 11: heap=[3,11,5,12], size>3 -> pop min 3. heap=[5,11,12]
return [5,11,12] = 3 largest  ✓
```

**Kth largest (chhota variation):** same size-K min-heap, phir `heap[0]` (root) = **Kth largest**
(K bade mein sabse chhota = Kth). Common problem.

> **Yaad rakhne wali baat:** Top-K largest = **size-K MIN-heap** (chhote nikaalte jaao, bade bachen),
> heap = K largest, `heap[0]` = Kth largest. O(n log k) — sorting O(n log n) se better jab k<<n.
> (K-smallest = size-K MAX-heap, ulta.) Signal: top-K/K-largest/Kth.

[↑ Back to top](#top)

---

<a id="s9-4"></a>
## 9.4 — Pattern: K most frequent

Top-K ka ek common variation — "K sabse frequent elements". Yeh hashing (Ch 04 frequency) + heap
(top-K) ka combo — do patterns saath.

**Problem — Top K Frequent Elements:**

**Problem:** array `nums` aur `k` diya. K sabse zyada frequent (baar-baar aane wale) elements dhoondho.
```
Input:  nums=[1, 1, 1, 2, 2, 3], k=2   -> Output: [1, 2]
        (1 teen baar, 2 do baar — top 2 frequent)
```
```python
import heapq
from collections import Counter

def top_k_frequent(nums, k):
    freq = Counter(nums)              # step 1: frequency count (Ch 4.5) — O(n)
    # step 2: size-K min-heap by frequency
    min_heap = []
    for num, count in freq.items():
        heapq.heappush(min_heap, (count, num))   # (frequency, number)
        if len(min_heap) > k:
            heapq.heappop(min_heap)   # sabse km frequent nikaalo
    return [num for count, num in min_heap]   # bache = K most frequent
```

**Logic kyun (frequency + top-K combo):** pehle `Counter` se har element ki frequency (Ch 4.5). Phir
size-K min-heap, par **frequency ke hisaab se** (tuple `(count, num)` — heap first-element/count se
sort, Ch 9.2). Km-frequent nikaalte jaao, K most-frequent bachen. **O(n log k).** Yeh Ch 04 (hashing)
+ Ch 09 (heap) ka clean combo — patterns combine (Ch 3.10).

**Dry-run (Input nums=[1,1,1,2,2,3], k=2):**
```
Counter: {1:3, 2:2, 3:1}
push (3,1): heap=[(3,1)]
push (2,2): heap=[(2,2),(3,1)]  (size 2)
push (1,3): heap=[(1,3),(3,1),(2,2)], size>2 -> pop min (1,3). heap=[(2,2),(3,1)]
return [2, 1] (numbers)  ✓  (top 2 frequent: 1 aur 2)
```

**Alternative (bucket sort, O(n)):** frequencies bounded hain (0 se n), toh "bucket by frequency"
se O(n) bhi hota — par heap approach simpler aur interview-acceptable. (Bucket Ch 11 mein zikr.)

> **Yaad rakhne wali baat:** K-most-frequent = frequency-count (Counter, Ch 4.5) + size-K min-heap
> by count (`(count, num)` tuples). Km-frequent nikaalo, K bachen. O(n log k). Hashing + heap combo.
> Signal: "K most/least frequent".

[↑ Back to top](#top)

---

<a id="s9-5"></a>
## 9.5 — Pattern: K-way merge

Heap se **kai sorted lists** ko efficiently merge kar sakte — har list ka current-smallest heap mein
rakhke. "K sorted lists merge" ya "merge K sorted arrays" mein.

**Problem — Merge K Sorted Lists:**

**Problem:** K sorted lists di. Ek sorted list mein merge karo.
```
Input:  lists = [[1,4,5], [1,3,4], [2,6]]
Output: [1, 1, 2, 3, 4, 4, 5, 6]
```
```python
import heapq

def merge_k_sorted(lists):
    min_heap = []
    # step 1: har list ka pehla element heap mein (value, list-index, element-index)
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(min_heap, (lst[0], i, 0))
    result = []
    while min_heap:
        val, list_idx, elem_idx = heapq.heappop(min_heap)   # sabse chhota abhi
        result.append(val)
        # us list ka agla element heap mein daalo
        if elem_idx + 1 < len(lists[list_idx]):
            next_val = lists[list_idx][elem_idx + 1]
            heapq.heappush(min_heap, (next_val, list_idx, elem_idx + 1))
    return result
```

**Logic kyun (yeh core):** heap mein har list ka **current smallest** rakhte hain. Sabse chhota pop
karo (yeh overall smallest hai — kyunki har list sorted, aur hum sabke fronts compare kar rahe),
result mein daalo, aur us list ka **agla** element heap mein. Repeat. Heap size ~K (K lists), total
N elements → **O(N log k).** Tuple `(value, list_idx, elem_idx)` — value se sort, baaki tracking +
tie-break (Ch 9.2 gotcha).

**Dry-run (Input [[1,4,5],[1,3,4],[2,6]]):**
```
heap init: (1,0,0), (1,1,0), (2,2,0)   [har list ka pehla]
pop (1,0,0): result=[1]. list 0 ka agla 4 -> push (4,0,1)
pop (1,1,0): result=[1,1]. list 1 ka agla 3 -> push (3,1,1)
pop (2,2,0): result=[1,1,2]. list 2 ka agla 6 -> push (6,2,1)
pop (3,1,1): result=[1,1,2,3]. push (4,1,2)
... continues -> [1,1,2,3,4,4,5,6]  ✓
```

> **Yaad rakhne wali baat:** K-way merge = heap mein har list ka current-smallest, pop-smallest →
> result → us list ka agla push. Tuple `(value, list_idx, elem_idx)`. O(N log k). Signal: "merge K
> sorted lists/arrays".

[↑ Back to top](#top)

---

<a id="s9-6"></a>
## 9.6 — Pattern: Two heaps (running median)

Ek clever pattern — **do heaps** (ek max, ek min) use karke ek stream ka **running median** (beech
ka element) O(log n) per element mein. Yeh advanced-ish par classic.

**Median kya:** sorted data ka beech ka element (odd count) ya do-beech ka average (even count).
Stream mein "ab tak ka median" baar-baar chahiye.

**Problem — Find Median from Data Stream:**

**Problem:** numbers stream mein aa rahe. Har baar "ab tak ka median" chahiye.
```
addNum(1), addNum(2): median = 1.5 (average of 1,2)
addNum(3): median = 2 (beech ka)
```
```python
import heapq

class MedianFinder:
    def __init__(self):
        self.small = []   # max-heap (chhoti half) — negated values
        self.large = []   # min-heap (badi half)

    def add_num(self, num):
        heapq.heappush(self.small, -num)          # pehle small (max-heap) mein
        # balance: small ka max, large ke min se bada na ho
        if self.small and self.large and (-self.small[0] > self.large[0]):
            heapq.heappush(self.large, -heapq.heappop(self.small))
        # sizes balance (difference <= 1)
        if len(self.small) > len(self.large) + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        elif len(self.large) > len(self.small) + 1:
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def find_median(self):
        if len(self.small) > len(self.large):
            return -self.small[0]                 # small mein zyada -> uska top
        elif len(self.large) > len(self.small):
            return self.large[0]
        else:
            return (-self.small[0] + self.large[0]) / 2   # dono barabar -> average
```

**Logic kyun (do heaps — dhyan se):** data ko **do halves** mein baant do — **`small`** (chhoti aadhi,
max-heap taaki uska sabse bada top pe) aur **`large`** (badi aadhi, min-heap taaki uska sabse chhota
top pe). Median = beech mein, jo in dono halves ki boundary pe hai (`small` ka max ya `large` ka min,
ya dono ka average). Heaps balanced rakhte (sizes ~barabar). Add O(log n), median O(1). **Yeh
"beech-ka-element baar-baar" ka clever tool.**

**Note (Ch 1.5):** two-heaps medium-hard hai, aata hai (running median classic). Samajh lo — par
top-K (9.3) zyada common, pehle woh solid.

> **Yaad rakhne wali baat:** Two-heaps (running median): `small` = max-heap (chhoti half), `large` =
> min-heap (badi half), balanced. Median = boundary pe (top of one, ya average). Add O(log n), median
> O(1). Signal: "running/stream median". Advanced — top-K pehle.

[↑ Back to top](#top)

---

<a id="s9-7"></a>
## 9.7 — Heap vs Sorting vs Quickselect (kab kaunsa)

Top-K type problems teen tareeke se ho sakte — heap, sorting, ya quickselect. Kab kaunsa, yeh
tradeoff samajhna interview mein achha (Ch 1.7).

**Teen approaches for "top K largest":**

| Approach | Complexity | Kab best |
|---|---|---|
| **Sorting** | O(n log n) | Simple, ya jab poora sorted chahiye. K bade ho toh theek. |
| **Heap (size K)** | O(n log k) | K << n (jaise top-10 of million). Streaming/online. |
| **Quickselect** | O(n) average | Sabse fast average, par worst O(n^2); ek-baar top-K (streaming nahi) |

**Logic (kab kya):**
- **Sorting** — sabse simple, likhne mein aasaan. Agar `k` bada hai (~n ke paas) ya aapko poora order
  chahiye, sorting theek. O(n log n).
- **Heap** — jab **k chhota** (k << n) — O(n log k) sorting se better. Aur **streaming** (elements ek-
  ek aa rahe, sab ek saath nahi) mein heap best — size-K heap maintain karte raho (9.3). ML top-K
  streaming mein yeh.
- **Quickselect** — O(n) average (fastest) jab ek baar top-K nikaalna (sorting/heap se fast). Par
  worst O(n^2), aur streaming mein nahi chalta. (Quickselect Ch 11 mein — quicksort ka partition
  idea.)

**Interview mein bolna:** "main heap use karunga, O(n log k) — kyunki k chhota hai. Agar poora sort
chahiye toh sorting, ya ek-baar top-K ke liye quickselect O(n) average." Yeh teen tradeoffs bolna
maturity dikhata (Ch 1.8).

**Simple rule:** streaming/small-k → **heap**. One-shot fastest → **quickselect**. Simple/poora-order
→ **sorting**. Interview mein heap sabse "safe" (clear, common).

> **Yaad rakhne wali baat:** Top-K: sorting O(n log n) (simple/large-k), heap O(n log k) (small-k/
> streaming — best default), quickselect O(n) avg (one-shot fastest, worst O(n^2)). Streaming→heap,
> one-shot-fast→quickselect, simple→sort. Tradeoff bolna interview-signal.

[↑ Back to top](#top)

---

<a id="s9-8"></a>
## 9.8 — Nuances, edge cases

**Signal→pattern (heaps):**

| Signal | Pattern | Section |
|---|---|---|
| Top K / K largest-smallest / Kth | Size-K heap | 9.3 |
| K most/least frequent | Frequency + heap | 9.4 |
| Merge K sorted lists | K-way merge (heap) | 9.5 |
| Running/stream median | Two heaps | 9.6 |
| "Baar-baar min/max nikaalna + add" | Heap (general) | 9.1 |

**Edge cases (HAMESHA):**
- **k > len(array)** — saare elements return (heap mein sab). Check ya handle.
- **k = 0** — khaali return.
- **Empty array** — khaali heap, sahi default.
- **Duplicates** — heap duplicates handle karta (frequency mein bhi theek).
- **k = 1** — sirf min/max (heap overkill; simple `min()`/`max()` bhi).

**Python `heapq` gotchas (Ch 9.2 recap — zaroori):**
- **Min-heap only** — max ke liye NEGATE (`-x`).
- **Tuples for priority** — `(priority, value)`, same-priority pe `(pri, idx, item)` tie-break (warna
  comparison error non-comparable items pe).
- **`heapify` O(n)** — poora list heap banana fast (sort se).
- **`heap[0]` peek** — pop nahi, sirf dekho (O(1)).

**Kab heap NAHI:**
- **Sirf ek baar min/max** — `min()`/`max()` O(n) simpler (heap ka O(n) build + overhead bekaar for
  one query).
- **Poora sorted chahiye** — sorting (O(n log n)) better than n pops (n log n same, par sort simpler).
- **k ~ n** (top-K where K bada) — sorting simpler.

> **Yaad rakhne wali baat:** Heap signals: top-K/Kth (size-K heap), K-frequent (freq+heap), K-merge,
> median (two-heaps). Edge: k>n/k=0/empty/duplicates. Python: min-heap-only (negate for max), tuples-
> for-priority (tie-break idx), heapify O(n). NAHI: one-shot min/max (use min/max), full-sort needed.

[↑ Back to top](#top)

---

<a id="s9-9"></a>
## 9.9 — Yaad rakhne wali baatein (chapter recap)

1. **Heap** (9.1): tree, root = min (min-heap) ya max (max-heap). Peek O(1), push/pop O(log n).
   Kab: baar-baar min/max + add. = Priority queue.
2. **Python heapq** (9.2): MIN-heap only (`heappush`/`heappop`/`heap[0]`/`heapify`-O(n)). Max: NEGATE
   values. Priority: tuples `(pri, value)`, tie-break `(pri, idx, item)`.
3. **Top-K** (9.3): size-K min-heap (K-largest — chhote nikaalo, bade bachen), `heap[0]`=Kth. O(n log
   k). **#1 use, zaroor yaad.**
4. **K most frequent** (9.4): Counter + size-K heap by count. Hashing+heap combo.
5. **K-way merge** (9.5): heap mein har list ka current-smallest, pop→next. O(N log k).
6. **Two heaps** (9.6): running median (max-heap small + min-heap large, balanced). Advanced.
7. **Heap vs sort vs quickselect** (9.7): streaming/small-k→heap, one-shot→quickselect, simple→sort.

> **Chapter ka mantra:** Heap = "min/max turant + baar-baar". Sabse zyada aata **top-K** (size-K
> heap, O(n log k)) — yeh pakka karo, ML mein bhi (top-K predictions). Python min-heap-only (negate
> for max) yaad rakho. Two-heaps/k-merge medium — samajh lo, top-K pehle. LeetCode pe 3-4 heap
> problems.

[↑ Back to top](#top)

---

> **Chapter 09 khatam.** Ab tak: heap (min/max, O(1) peek, O(log n) push/pop); Python heapq (min-only,
> negate for max, tuples); top-K (size-K heap), K-frequent, K-way merge, two-heaps median; heap vs
> sort vs quickselect. **Agla chapter (10):** Graphs — BFS/DFS, connected components, islands,
> topological sort, union-find.

[↑ Back to top](#top)