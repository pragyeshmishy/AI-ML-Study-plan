<a id="top"></a>
# Chapter 03 — Arrays: Two Pointers, Sliding Window, Prefix Sum, aur more

Yeh **sabse high-frequency topic** hai (Ch 1.4 — ~18%, har interview mein lagbhag). Array (ek line
mein rakhe elements ki list) pe kaam karne ke kuch **patterns** hain jo baar-baar aate. Yeh chapter
un saare zaroori patterns ko basics se sikhata — bahut examples ke saath, clear Input→Output, aur
dry-run.

Agar aap sirf ek chapter solid kar sakte ho, toh yeh — kyunki array patterns (khaaskar two-pointer
aur sliding-window) baaki topics mein bhi baar-baar aate.

---

## Is chapter ka index

- [3.1 — Array basics + Python list (quick recap)](#s3-1)
- [3.2 — Two Pointers, Pattern 1: Opposite ends (dono taraf se)](#s3-2)
- [3.3 — Two Pointers, Pattern 2: Same direction (fast-slow)](#s3-3)
- [3.4 — Sliding Window, Pattern 1: Fixed size](#s3-4)
- [3.5 — Sliding Window, Pattern 2: Variable size](#s3-5)
- [3.6 — Prefix Sum (range-sum jaldi nikaalna)](#s3-6)
- [3.7 — Kadane's Algorithm (max subarray sum)](#s3-7)
- [3.8 — Merge Intervals (overlapping ranges)](#s3-8)
- [3.9 — In-place reverse / rotate](#s3-9)
- [3.10 — Nuances, edge cases, aur kab kaunsa pattern](#s3-10)
- [3.11 — Yaad rakhne wali baatein](#s3-11)

---

<a id="s3-1"></a>
## 3.1 — Array basics + Python list (quick recap)

**Array** = ek line mein, index (position number) se rakhe elements. Python mein hum `list` use karte
(`[]`). Index `0` se shuru: `arr[0]` pehla, `arr[1]` doosra.

```python
arr = [10, 20, 30, 40]
#       0   1   2   3      <- index (0 se shuru)
print(arr[0])      # 10  (pehla)
print(arr[-1])     # 40  (Python: -1 = aakhri)
print(len(arr))    # 4   (kitne elements)
print(arr[1:3])    # [20, 30]  (slice: index 1 se 3 se pehle tak)
```

**Zaroori operations aur unki complexity (Ch 2.6 recap):**
- `arr[i]` — index access — **O(1)** (direct jump).
- `arr.append(x)` — end pe add — **O(1)**.
- `arr.insert(0, x)` / `del arr[0]` — shuru/beech mein — **O(n)** (baaki shift).
- `x in arr` — search (unsorted) — **O(n)** (ek-ek dekhna).

**Kyun arrays interview mein itne common:** simple structure, par bahut patterns fit hote. Aur real
data (numbers, scores, prices) aksar array/list mein aata — toh "is list pe yeh nikaalo" natural
interview question hai.

**Iss chapter ke patterns ek nazar mein (pattern-recognition, Ch 2.7):**
- "Sorted array + pair/target dhoondho" → **two pointers opposite ends** (3.2).
- "Cycle / middle / in-place partition" → **two pointers same-direction** (3.3).
- "Contiguous subarray/window of size k" → **sliding window fixed** (3.4).
- "Longest/shortest subarray with condition" → **sliding window variable** (3.5).
- "Range sum baar-baar" → **prefix sum** (3.6).
- "Max sum contiguous subarray" → **Kadane's** (3.7).
- "Overlapping intervals/ranges" → **merge intervals** (3.8).

> **Yaad rakhne wali baat:** Array = index-based list (Python `list`, 0-indexed). `arr[i]` O(1),
> `append` O(1), `insert(0)`/search O(n). Sabse common interview topic. Patterns: two-pointer,
> sliding-window, prefix-sum, Kadane's, merge-intervals — problem ke signal se pehchano.

[↑ Back to top](#top)

---

<a id="s3-2"></a>
## 3.2 — Two Pointers, Pattern 1: Opposite ends (dono taraf se)

**Two pointers** = do index-variables (pointers) jo array mein ghumte hain. **Pattern 1:** ek pointer
shuru se (`left`), ek aakhir se (`right`), dono ek doosre ki taraf aate. Yeh **sorted array** pe
"pair dhoondho" type problems mein magic karta.

**Kab pehchano (signal):** "sorted array", "do elements ka sum/pair", "palindrome check", "dono
taraf se compare".

**Classic problem — Two Sum on SORTED array:**

**Problem:** ek **sorted** array `nums` aur `target` diya. Do indices dhoondho jinke elements ka sum
`target` ho.
```
Input:  nums=[2, 7, 11, 15], target=9
Output: [0, 1]    (kyunki nums[0]+nums[1] = 2+7 = 9)

Input:  nums=[1, 3, 4, 5, 7], target=12
Output: [3, 4]    (kyunki 5+7 = 12)
```

**Brute force (baseline):** har pair check → O(n^2). (Ch 2.5 wala.)

**Two-pointer solution (O(n) time, O(1) space):**
```python
def two_sum_sorted(nums, target):
    left, right = 0, len(nums) - 1     # ek shuru se, ek aakhir se
    while left < right:
        curr = nums[left] + nums[right]
        if curr == target:
            return [left, right]        # mil gaya!
        elif curr < target:
            left += 1                   # sum chhota -> bada element chahiye -> left aage
        else:
            right -= 1                  # sum bada -> chhota element chahiye -> right peeche
    return []
```

**Logic kyun kaam karta (yeh samjho):** array **sorted** hai. Agar current sum `target` se **chhota**
hai, humein bada sum chahiye — toh `left` ko aage badhao (bade element ki taraf). Agar sum **bada**
hai, chhota chahiye — `right` peeche. Har step mein ek pointer move, toh O(n). Sorted hone ki wajah
se yeh "decision" possible hai.

**Dry-run (Input nums=[2,7,11,15], target=9):**
```
left=0, right=3:  nums[0]+nums[3] = 2+15 = 17. 17 > 9 -> right=2
left=0, right=2:  nums[0]+nums[2] = 2+11 = 13. 13 > 9 -> right=1
left=0, right=1:  nums[0]+nums[1] = 2+7  =  9. 9 == 9 -> return [0, 1]  ✓
```

**Doosra example — Palindrome check (opposite ends):**

**Problem:** string `s` palindrome hai? (aage-peeche same padha jaye)
```
Input:  s="racecar"  -> Output: True
Input:  s="hello"    -> Output: False
```
```python
def is_palindrome(s):
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return False        # match nahi -> palindrome nahi
        left += 1
        right -= 1
    return True
```
- Dono taraf se compare — mismatch mila toh `False`. Sab match toh `True`. **O(n) time, O(1) space.**

> **Yaad rakhne wali baat:** Two-pointer opposite-ends: `left=0`, `right=n-1`, ek doosre ki taraf.
> Signal: SORTED array + pair/sum, ya palindrome. Sorted hone se "sum chhota -> left++, sum bada ->
> right--" decision possible. O(n) time, O(1) space (brute O(n^2) se behtar).

[↑ Back to top](#top)

---

<a id="s3-3"></a>
## 3.3 — Two Pointers, Pattern 2: Same direction (slow-fast)

Doosra two-pointer flavour — dono pointers **ek hi taraf** chalte, par alag speed/role se. Ek "slow"
(jahan tak sahi answer bana), ek "fast" (aage explore karta). Yeh **in-place** (bina extra array)
array modify karne mein bahut kaam ka.

**Kab pehchano (signal):** "in-place remove/move elements", "duplicates hatao", "array ko rearrange".

**Classic problem — Remove Duplicates from Sorted Array (in-place):**

**Problem:** ek **sorted** array `nums` diya. Duplicates in-place hatao (extra array nahi), aur unique
elements ki count return karo. (Array ke shuru mein unique elements aa jaayein.)
```
Input:  nums=[1, 1, 2, 2, 3]
Output: 3    (aur nums ke pehle 3 elements = [1, 2, 3, ...])

Input:  nums=[0, 0, 1, 1, 1, 2]
Output: 3    (pehle 3 = [0, 1, 2, ...])
```

**Two-pointer (same direction) solution:**
```python
def remove_duplicates(nums):
    if not nums:              # edge case: empty array
        return 0
    slow = 0                  # slow: aakhri unique element ki position
    for fast in range(1, len(nums)):   # fast: aage explore
        if nums[fast] != nums[slow]:   # naya unique mila
            slow += 1
            nums[slow] = nums[fast]    # use slow ki agli jagah pe rakho
    return slow + 1           # count = index + 1
```

**Logic kyun (yeh samjho):** `slow` batata "ab tak jitne unique mile, unki aakhri position". `fast`
aage badhta rehta. Jab `fast` pe koi **naya** element (jo `slow` wale se alag) mile, hum `slow` aage
badhake wahan naya rakh dete. Sorted hone se same elements saath hote — toh `!=` check kaafi. **O(n)
time, O(1) space** (in-place, koi extra array nahi).

**Dry-run (Input nums=[1,1,2,2,3]):**
```
slow=0 (nums[0]=1)
fast=1: nums[1]=1 == nums[0]=1 -> skip
fast=2: nums[2]=2 != nums[0]=1 -> slow=1, nums[1]=2. Array ab [1,2,2,2,3]
fast=3: nums[3]=2 == nums[1]=2 -> skip
fast=4: nums[4]=3 != nums[1]=2 -> slow=2, nums[2]=3. Array ab [1,2,3,2,3]
return slow+1 = 3.  Pehle 3 elements = [1,2,3]  ✓
```

**Doosra example — Move Zeroes (in-place):**

**Problem:** array ke saare `0` end mein le jao, baaki elements ka order same rahe. In-place.
```
Input:  nums=[0, 1, 0, 3, 12]
Output: [1, 3, 12, 0, 0]
```
```python
def move_zeroes(nums):
    slow = 0                          # slow: agli non-zero rakhne ki jagah
    for fast in range(len(nums)):
        if nums[fast] != 0:           # non-zero mila
            nums[slow], nums[fast] = nums[fast], nums[slow]  # swap
            slow += 1
```
- `slow` non-zero elements ko aage pack karta; `0` apne aap peeche chale jate. **O(n) time, O(1)
  space.** Dry-run: `[0,1,0,3,12]` → swap se non-zeros aage → `[1,3,12,0,0]`.

**Do two-pointer patterns ka farak (yaad rakho):**
- **Opposite ends (3.2):** `left=0`, `right=n-1`, ek doosre ki taraf. Sorted-pair/palindrome.
- **Same direction (3.3):** dono aage, slow-fast, alag role. In-place modify/dedup/rearrange.

> **Yaad rakhne wali baat:** Two-pointer same-direction: slow (jahan tak answer bana) + fast (aage
> explore), dono aage. Signal: in-place remove/dedup/rearrange. Remove-duplicates, move-zeroes.
> O(n) time, O(1) space. Opposite-ends (sorted pair) se alag pattern.

[↑ Back to top](#top)

---

<a id="s3-4"></a>
## 3.4 — Sliding Window, Pattern 1: Fixed size

**Sliding window** = ek "khidki" (window = continuous elements ka ek tukda) jo array pe **slide**
(sarkti) karti. **Pattern 1 (fixed):** window ka size fixed hai (`k`), aur woh ek-ek step aage
sarkti hai. Yeh "size-k ke contiguous subarray" problems mein O(n) deta (brute O(n*k) ke bajaye).

**Kab pehchano (signal):** "contiguous subarray/substring of size k", "har k-size window ka sum/avg/
max".

**Classic problem — Max Sum of Subarray of Size K:**

**Problem:** array `nums` aur number `k` diya. Size-`k` ke **contiguous** (lagatar) subarray ka max
sum dhoondho.
```
Input:  nums=[2, 1, 5, 1, 3, 2], k=3
Output: 9    (subarray [5,1,3] ka sum = 9, sabse zyada)

Input:  nums=[1, 2, 3, 4, 5], k=2
Output: 9    (subarray [4,5] = 9)
```

**Brute force (baseline):** har size-k window ka sum alag se nikaalo → har window k elements jodo, n
windows → O(n*k). Slow.

**Sliding window solution (O(n) time):**
```python
def max_sum_subarray(nums, k):
    if len(nums) < k:                  # edge case
        return None
    window_sum = sum(nums[:k])         # pehli window (index 0..k-1) ka sum
    max_sum = window_sum
    for i in range(k, len(nums)):      # window ko slide karo
        window_sum += nums[i]          # naya element (right) add
        window_sum -= nums[i - k]      # purana element (left) remove
        max_sum = max(max_sum, window_sum)
    return max_sum
```

**Logic kyun (yeh core insight):** har baar poori window ka sum dobara nikaalne (O(k)) ke bajaye, hum
**pichhli window ka sum reuse** karte — sirf ek naya element add (right) aur ek purana remove (left).
Yeh "sarkna" O(1) per step, toh total O(n). Yeh sliding-window ki asli power hai — repeated kaam
bachana.

**Dry-run (Input nums=[2,1,5,1,3,2], k=3):**
```
Pehli window [2,1,5]: window_sum = 8, max_sum = 8
i=3 (nums[3]=1): +1 -nums[0]=2 -> window_sum = 8+1-2 = 7. window [1,5,1]. max=8
i=4 (nums[4]=3): +3 -nums[1]=1 -> window_sum = 7+3-1 = 9. window [5,1,3]. max=9
i=5 (nums[5]=2): +2 -nums[2]=5 -> window_sum = 9+2-5 = 6. window [1,3,2]. max=9
return max_sum = 9  ✓
```

> **Yaad rakhne wali baat:** Sliding-window fixed: size-k window ko slide karo — har step ek element
> add (right) + ek remove (left), sum reuse karo (poora dobara nahi). Signal: "size-k contiguous
> subarray ka sum/avg/max". O(n) time (brute O(n*k) se behtar). Core: repeated kaam bachana.

[↑ Back to top](#top)

---

<a id="s3-5"></a>
## 3.5 — Sliding Window, Pattern 2: Variable size

Yeh sliding-window ka zyada powerful (aur zyada common) roop. Yahan window ka size **fix nahi** —
woh badhti aur ghatti hai ek condition ke hisaab se. `right` window ko badhata (grow), `left` use
chhota karta (shrink) jab condition toot jaye.

**Kab pehchano (signal):** "longest/shortest subarray/substring jismein [koi condition]", "at most K
distinct", "sum >= target wali shortest".

**Classic problem — Longest Substring Without Repeating Characters:**

**Problem:** string `s` diya. Sabse lambi substring (contiguous) ki length dhoondho jismein koi
character repeat na ho.
```
Input:  s="abcabcbb"  -> Output: 3   ("abc" — length 3, koi repeat nahi)
Input:  s="bbbbb"     -> Output: 1   ("b" — ek hi)
Input:  s="pwwkew"    -> Output: 3   ("wke")
```

**Variable sliding-window solution (O(n) time):**
```python
def longest_unique_substring(s):
    seen = set()              # abhi window mein kaunse chars hain
    left = 0                  # window ka left edge
    max_len = 0
    for right in range(len(s)):        # right window ko grow karta
        while s[right] in seen:        # repeat mila -> window shrink karo
            seen.remove(s[left])       # left wala char nikaalo
            left += 1                  # left aage
        seen.add(s[right])             # ab naya char add
        max_len = max(max_len, right - left + 1)   # window size = right-left+1
    return max_len
```

**Logic kyun (yeh core — dhyan se):** `right` har baar aage badhta (window grow). Jab `s[right]`
window mein **already hai** (repeat), toh window invalid ho gayi — hum `left` ko aage badhake
(shrink) tab tak chalte jab tak repeat hat na jaye. Har point pe window "valid" (no-repeat) rehti,
aur hum uski max length track karte. `left` aur `right` dono sirf aage jate (kabhi peeche nahi) →
total O(n).

**Dry-run (Input s="abcabcbb"):**
```
right=0 'a': seen={} -> add 'a'. window "a", len=1, max=1
right=1 'b': add 'b'. window "ab", len=2, max=2
right=2 'c': add 'c'. window "abc", len=3, max=3
right=3 'a': 'a' in seen! shrink: remove s[0]='a', left=1. add 'a'. window "bca", len=3, max=3
right=4 'b': 'b' in seen! shrink: remove s[1]='b', left=2. add 'b'. window "cab", len=3, max=3
... (aage bhi max 3 rehta)
return max_len = 3  ✓
```

**Fixed vs Variable window (farak yaad rakho):**
- **Fixed (3.4):** size hamesha `k`. Ek add + ek remove har step.
- **Variable (3.5):** size condition pe badalta. `right` grow, `left` shrink-when-invalid. "longest/
  shortest with condition".

**Template (variable window ka general shape — yeh yaad rakho):**
```python
left = 0
for right in range(len(arr)):
    # 1. arr[right] ko window mein add karo
    while (window invalid hai):        # condition tootI
        # 2. arr[left] ko remove karo, left += 1  (shrink)
    # 3. ab window valid -> answer update karo (jaise max_len)
```

> **Yaad rakhne wali baat:** Sliding-window variable: `right` grow karta, `left` shrink karta jab
> window invalid ho. Signal: "longest/shortest subarray/substring with condition". Template: add
> right -> while-invalid shrink left -> update answer. left/right dono sirf aage -> O(n).

[↑ Back to top](#top)

---

<a id="s3-6"></a>
## 3.6 — Prefix Sum (range-sum jaldi nikaalna)

**Prefix sum** = ek pehle se banaya hua array jismein har position pe "shuru se yahan tak ka sum"
rakha hota. Isse aap kisi bhi **range (i se j tak) ka sum O(1)** mein nikaal sakte ho — baar-baar
jodne ke bajaye.

**Kab pehchano (signal):** "range sum baar-baar poocha jaye", "subarray sum", "sum between index i
and j".

**Problem — Range Sum Query (baar-baar):**

**Problem:** array `nums` diya. Bahut saari queries: "index `i` se `j` tak ka sum kya hai?" Har query
fast (O(1)) chahiye.
```
Input:  nums=[3, 1, 4, 1, 5], queries: sum(1,3), sum(0,2)
Output: sum(1,3) = 1+4+1 = 6;  sum(0,2) = 3+1+4 = 8
```

**Brute force:** har query pe i se j jodo → O(n) per query. Bahut queries pe slow.

**Prefix-sum solution (build O(n) once, phir har query O(1)):**
```python
def build_prefix(nums):
    prefix = [0] * (len(nums) + 1)     # prefix[0]=0, size n+1
    for i in range(len(nums)):
        prefix[i + 1] = prefix[i] + nums[i]   # shuru se (i) tak ka sum
    return prefix

def range_sum(prefix, i, j):           # sum from index i to j (dono include)
    return prefix[j + 1] - prefix[i]
```

**Logic kyun (yeh core insight):** `prefix[k]` = "index 0 se k-1 tak ka total sum". Toh `i` se `j`
tak ka sum = (0 se j tak) minus (0 se i-1 tak) = `prefix[j+1] - prefix[i]`. Ek subtraction — O(1)!
Ek baar prefix bana lo (O(n)), phir har range-query O(1). Yeh "pehle se compute karke baad mein
reuse" ka pattern.

**Dry-run (Input nums=[3,1,4,1,5]):**
```
prefix banao: [0, 3, 4, 8, 9, 14]
              (prefix[1]=3, prefix[2]=3+1=4, prefix[3]=4+4=8, prefix[4]=8+1=9, prefix[5]=9+5=14)

range_sum(1,3): prefix[4] - prefix[1] = 9 - 3 = 6   (nums[1]+nums[2]+nums[3]=1+4+1=6)  ✓
range_sum(0,2): prefix[3] - prefix[0] = 8 - 0 = 8   (3+1+4=8)  ✓
```

**Bahut common combo — Prefix sum + Hashmap (subarray-sum = k):** "kitne subarrays ka sum exactly k
hai" — yeh prefix-sum + hash-map se O(n) mein hota (Ch 04 mein poora, kyunki hashing wahan). Abhi
jaan lo: prefix-sum sirf range-query nahi, subarray-sum problems ka bhi base hai.

> **Yaad rakhne wali baat:** Prefix sum: `prefix[k]` = 0 se k-1 tak ka sum. Range i..j ka sum =
> `prefix[j+1]-prefix[i]` (O(1)!). Build O(n) once, phir har range-query O(1). Signal: baar-baar
> range-sum / subarray-sum. Hashmap ke saath subarray-sum=k (Ch 04).

[↑ Back to top](#top)

---

<a id="s3-7"></a>
## 3.7 — Kadane's Algorithm (max subarray sum)

**Kadane's** ek famous, must-know algorithm hai ek specific problem ke liye: **max sum wala
contiguous subarray**. Yeh ek simple loop mein O(n) mein hota — aur interview mein bahut aata.

**Kab pehchano (signal):** "maximum sum of a contiguous subarray", "best consecutive stretch"
(jaise max profit wale consecutive din).

**Problem — Maximum Subarray:**

**Problem:** array `nums` (positive+negative numbers) diya. Woh **contiguous** (lagatar) subarray
dhoondho jiska sum sabse zyada ho — aur woh max sum return karo.
```
Input:  nums=[-2, 1, -3, 4, -1, 2, 1, -5, 4]  -> Output: 6   (subarray [4,-1,2,1] = 6)
Input:  nums=[1, 2, 3, -2, 5]                 -> Output: 9   ([1,2,3,-2,5] = 9)
Input:  nums=[-1, -2, -3]                      -> Output: -1  (sabse km bura, akela -1)
```

**Brute force:** har possible subarray ka sum → O(n^2). Kadane's isse O(n) karta.

**Kadane's solution (O(n) time, O(1) space):**
```python
def max_subarray(nums):
    current = nums[0]         # yahan tak (is index pe khatam hone wala) best sum
    best = nums[0]            # ab tak ka overall best
    for i in range(1, len(nums)):
        # choice: naya element akela shuru karun, ya pichhle ke saath jodun?
        current = max(nums[i], current + nums[i])
        best = max(best, current)
    return best
```

**Logic kyun (yeh core insight — bahut elegant):** har position pe ek **choice** hai — "is element se
naya subarray shuru karun (`nums[i]`), ya pichhle running-sum ke saath jodun (`current + nums[i]`)?"
Hum jo bada de woh lete. Kyun? Agar pichhla `current` **negative** ho gaya, toh use aage le jaana
nuksaan hai — behtar naya shuru karo. `best` overall maximum yaad rakhta. Ek pass, O(n).

**Dry-run (Input nums=[-2,1,-3,4,-1,2,1,-5,4]):**
```
current=-2, best=-2
i=1 (1):   max(1, -2+1=-1) = 1.    current=1, best=1
i=2 (-3):  max(-3, 1-3=-2) = -2.   current=-2, best=1
i=3 (4):   max(4, -2+4=2) = 4.     current=4, best=4   (naya shuru — pichhla negative tha)
i=4 (-1):  max(-1, 4-1=3) = 3.     current=3, best=4
i=5 (2):   max(2, 3+2=5) = 5.      current=5, best=5
i=6 (1):   max(1, 5+1=6) = 6.      current=6, best=6
i=7 (-5):  max(-5, 6-5=1) = 1.     current=1, best=6
i=8 (4):   max(4, 1+4=5) = 5.      current=5, best=6
return best = 6  ✓   (subarray [4,-1,2,1])
```

**Edge case (all negative):** `[-1,-2,-3]` → answer `-1` (sabse km bura single element). Kadane's
ise handle karta kyunki hum `nums[0]` se shuru karte, `0` se nahi. (Agar `0` se shuru karte toh
galat `0` de deta — yeh common bug.)

> **Yaad rakhne wali baat:** Kadane's = max-sum contiguous subarray, O(n). Har element pe choice:
> `current = max(nums[i], current + nums[i])` (naya shuru ya jodna), `best` track. Logic: pichhla
> negative ho toh naya shuru. `nums[0]` se init (0 se nahi — all-negative edge case).

[↑ Back to top](#top)

---

<a id="s3-8"></a>
## 3.8 — Merge Intervals (overlapping ranges)

**Intervals** = ranges jaise `[start, end]` (jaise meeting timings `[9, 11]`). Ek bahut common
problem — **overlapping intervals ko merge** karna. Yeh pattern real-world (calendars, bookings)
mein bhi aata.

**Kab pehchano (signal):** "intervals/ranges", "overlapping", "merge", "meeting rooms", "[start,end]
pairs".

**Problem — Merge Intervals:**

**Problem:** intervals ki list di (`[start, end]`). Overlapping (jo ek doosre ko cross karte) ko
merge karke ek bana do. Non-overlapping alag rahein.
```
Input:  [[1,3], [2,6], [8,10], [15,18]]
Output: [[1,6], [8,10], [15,18]]
        ([1,3] aur [2,6] overlap karte (2 <= 3) -> merge -> [1,6])

Input:  [[1,4], [4,5]]
Output: [[1,5]]    (4 pe touch karte -> merge)
```

**Solution (sort + merge, O(n log n) time):**
```python
def merge_intervals(intervals):
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])     # start ke hisaab se sort (ZAROORI)
    merged = [intervals[0]]                # pehla interval daalo
    for start, end in intervals[1:]:
        last_end = merged[-1][1]           # aakhri merged interval ka end
        if start <= last_end:              # overlap! (current start <= pichhla end)
            merged[-1][1] = max(last_end, end)  # end ko extend karo
        else:
            merged.append([start, end])    # no overlap -> naya interval
    return merged
```

**Logic kyun (yeh core — sort pehle kyun):** pehle **start ke hisaab se sort** karte — taaki
overlapping intervals **saath-saath** aa jayein. Phir ek pass: har interval ka `start` pichhle merged
ke `end` se compare. Agar `start <= last_end` → overlap → `end` ko `max` se extend. Warna naya
interval. Sort O(n log n) dominant, phir pass O(n) → **O(n log n) total.** Sort ke bina yeh problem
mushkil — sorting "unlock" karta hai (Ch 2.7 signal).

**Dry-run (Input [[1,3],[2,6],[8,10],[15,18]]):**
```
Sort (already sorted): [[1,3],[2,6],[8,10],[15,18]]
merged=[[1,3]]
[2,6]:  start=2 <= last_end=3 -> overlap. merged[-1][1]=max(3,6)=6. merged=[[1,6]]
[8,10]: start=8 <= 6? NAHI -> naya. merged=[[1,6],[8,10]]
[15,18]:start=15 <= 10? NAHI -> naya. merged=[[1,6],[8,10],[15,18]]
return [[1,6],[8,10],[15,18]]  ✓
```

**Edge case:** touch-karte intervals `[1,4],[4,5]` → `4 <= 4` True → merge → `[1,5]`. (`<=` use kiya
`<` nahi, taaki touching bhi merge ho — problem ke hisaab se decide.)

> **Yaad rakhne wali baat:** Merge intervals: pehle **start se sort** (overlapping saath aa jaye),
> phir pass — `start <= last_end` toh overlap (end ko max se extend), warna naya interval. O(n log n)
> (sort dominant). Signal: intervals/ranges/overlapping/meetings. Sort "unlock" karta.

[↑ Back to top](#top)

---

<a id="s3-9"></a>
## 3.9 — In-place reverse / rotate

Do simple par common array-manipulation patterns — **reverse** (ulta karna) aur **rotate** (ghumana)
— in-place (bina extra array). Yeh basics hain par interview mein building-block ki tarah aate.

**Reverse in-place (two-pointer, 3.2 wala):**

**Problem:** array ko in-place ulta karo.
```
Input:  [1, 2, 3, 4, 5]  -> Output: [5, 4, 3, 2, 1]
```
```python
def reverse(nums):
    left, right = 0, len(nums) - 1
    while left < right:
        nums[left], nums[right] = nums[right], nums[left]  # swap
        left += 1
        right -= 1
```
- Two-pointer opposite-ends (3.2) — dono taraf se swap. **O(n) time, O(1) space.**

**Rotate array by k (right rotation):**

**Problem:** array ko `k` positions right rotate karo.
```
Input:  nums=[1,2,3,4,5], k=2  -> Output: [4,5,1,2,3]
        (aakhri 2 elements aage aa gaye)
```
**Clever trick (reverse teen baar — yeh yaad rakho):**
```python
def rotate(nums, k):
    n = len(nums)
    k = k % n                    # k > n ho sakta, isliye mod
    reverse_part(nums, 0, n - 1) # poora reverse: [5,4,3,2,1]
    reverse_part(nums, 0, k - 1) # pehle k reverse: [4,5,3,2,1]
    reverse_part(nums, k, n - 1) # baaki reverse:   [4,5,1,2,3]

def reverse_part(nums, left, right):
    while left < right:
        nums[left], nums[right] = nums[right], nums[left]
        left += 1
        right -= 1
```
- **Logic:** poora reverse karo, phir pehle `k` aur baaki alag-alag reverse — magically rotate ho
  jata. **O(n) time, O(1) space.** (`k % n` isliye ki agar `k` array se bada ho.)

**Dry-run (nums=[1,2,3,4,5], k=2):**
```
k = 2 % 5 = 2
poora reverse:      [5,4,3,2,1]
pehle 2 reverse:    [4,5,3,2,1]
baaki (index 2..4): [4,5,1,2,3]  ✓
```

**Edge case:** `k % n` zaroori — `k=7, n=5` → `7%5=2` (7 rotation = 2 rotation effectively). Bina
mod ke index-error.

> **Yaad rakhne wali baat:** Reverse = two-pointer opposite-ends swap (O(n)/O(1)). Rotate-by-k =
> teen reverse (poora -> pehle k -> baaki), O(n)/O(1). `k % n` zaroori (k bada ho sakta). Yeh
> building-block patterns — baaki problems mein use hote.

[↑ Back to top](#top)

---

<a id="s3-10"></a>
## 3.10 — Nuances, edge cases, aur kab kaunsa pattern

**Kaunsa pattern kab (pattern-recognition — yeh table interview mein sona):**

| Problem ka signal | Pattern | Section |
|---|---|---|
| Sorted array + pair/sum dhoondho | Two pointers (opposite ends) | 3.2 |
| Palindrome / dono taraf se compare | Two pointers (opposite ends) | 3.2 |
| In-place dedup/remove/rearrange | Two pointers (same direction) | 3.3 |
| Size-k contiguous subarray ka sum/max | Sliding window (fixed) | 3.4 |
| Longest/shortest subarray with condition | Sliding window (variable) | 3.5 |
| Baar-baar range-sum / subarray-sum | Prefix sum | 3.6 |
| Max-sum contiguous subarray | Kadane's | 3.7 |
| Overlapping intervals/ranges/meetings | Merge intervals (sort first) | 3.8 |

**Common edge cases (HAMESHA check karo — Ch 1.7/1.8, senior-signal):**
- **Empty array** `[]` — kya code crash karta? (jaise `nums[0]` index-error). Pehle `if not nums`.
- **Single element** `[5]` — loops chalenge? two-pointer `left < right` (single pe loop nahi chalta,
  theek).
- **All same / duplicates** `[2,2,2]` — dedup, window logic sahi?
- **All negative** `[-1,-2]` — Kadane's mein `nums[0]` se init (3.7 wala bug).
- **k > len(array)** — sliding-window/rotate mein `k % n` ya length-check (3.4/3.9).
- **Negative numbers** — sorting/comparison sahi? two-pointer sum logic negatives pe bhi chalta.

**Kab yeh patterns NAHI (galat use se bacho):**
- **Sliding window sirf CONTIGUOUS pe** — agar subarray contiguous nahi hona (koi bhi elements), toh
  sliding-window nahi (shayad DP ya subset, Ch 07/12).
- **Two-pointer opposite-ends usually SORTED pe** — unsorted pe pair dhoondhna ho toh hashing (Ch 04)
  behtar. (Sort karke two-pointer bhi kar sakte, par sort O(n log n) add.)
- **Prefix-sum sirf jab baar-baar range-query** — ek hi query ke liye seedha sum kaafi (prefix build
  ka overhead bekaar).

**Ek senior-tip:** in patterns ko **combine** bhi karte hain — jaise "sorted array" na ho toh pehle
`sort` karke phir two-pointer (sort O(n log n) + two-pointer O(n) = O(n log n), still brute O(n^2) se
behtar). Interview mein yeh bolna maturity dikhata.

> **Yaad rakhne wali baat:** Signal→pattern table yaad rakho (sorted-pair→two-pointer, k-subarray→
> fixed-window, longest-with-condition→variable-window, range-sum→prefix, max-subarray→Kadane,
> intervals→merge). Edge cases HAMESHA: empty/single/duplicates/all-negative/k>n/negatives. Sliding-
> window sirf contiguous. Patterns combine bhi hote (sort + two-pointer).

[↑ Back to top](#top)

---

<a id="s3-11"></a>
## 3.11 — Yaad rakhne wali baatein (chapter recap)

Arrays sabse high-frequency topic — yeh patterns pakke karo:

1. **Two pointers — opposite ends** (3.2): `left=0`,`right=n-1` ek doosre ki taraf. Sorted-pair,
   palindrome. O(n)/O(1).
2. **Two pointers — same direction** (3.3): slow-fast dono aage. In-place dedup/rearrange. O(n)/O(1).
3. **Sliding window — fixed** (3.4): size-k window slide, add-right+remove-left, sum reuse. O(n).
4. **Sliding window — variable** (3.5): right grow, left shrink-when-invalid. Longest/shortest-with-
   condition. O(n). (Template yaad rakho.)
5. **Prefix sum** (3.6): `prefix[k]`=0..k-1 sum; range = `prefix[j+1]-prefix[i]` O(1). Baar-baar
   range/subarray-sum.
6. **Kadane's** (3.7): max-sum contiguous subarray, `current=max(nums[i], current+nums[i])`. O(n).
7. **Merge intervals** (3.8): start-se-sort phir merge (`start<=last_end`). O(n log n).
8. **Reverse/rotate** (3.9): two-pointer swap; rotate = 3 reverses.

**Sabse zaroori — pattern pehchanna:** problem ka signal (sorted? contiguous? range-sum? intervals?)
dekh ke pattern chuno (3.10 table). Brute-force (O(n^2)) se shuru, phir pattern se optimize (O(n)/
O(n log n)) — aur bolke (Ch 1.7). Yeh in patterns ki practice LeetCode pe zaroor karo (padhna kaafi
nahi).

> **Chapter ka mantra:** Array problems = ~7-8 patterns. Signal dekho → pattern pehchano → apply.
> Two-pointer aur sliding-window sabse zyada aate (aur baaki topics mein bhi) — yeh do sabse solid
> karo. Har pattern ka template + ek classic problem yaad, aur LeetCode pe 3-4 practice.

[↑ Back to top](#top)

---

> **Chapter 03 khatam.** Ab tak: two-pointer (opposite-ends + same-direction), sliding-window (fixed
> + variable + template), prefix-sum, Kadane's (max subarray), merge-intervals, reverse/rotate,
> aur signal→pattern table + edge cases. **Agla chapter (04):** Hashing — hash-map/set se O(1)
> lookup, two-sum (unsorted), frequency counting, group-anagrams, subarray-sum=k.

[↑ Back to top](#top)
