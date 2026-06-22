# Area 11 — LeetCode / DSA Patterns

A standalone pillar: the algorithmic **patterns** behind coding-interview and competitive
problems. Unlike the rest of the guide, this area is **not** ML-biased — it's general
computer science. The goal is the same reflex, applied to algorithms: *"this problem has
shape X → reach for pattern Y."* Each scenario teaches a pattern by the **trigger that
signals it** (what in the problem statement tells you to use it), the **core idea**, a
worked example with complexity, and the traps. Master the triggers and most interview
problems become "which of these ~15 patterns is this?" — which is exactly scenario 11.30.

---

<a id="contents"></a>
## Contents

- [11.1 — "Find pairs/duplicates/complements fast" → arrays + hashing](#11.1)
- [11.2 — "Scan a sorted array from both ends" → two pointers](#11.2)
- [11.3 — "Longest/shortest/best contiguous subarray or substring" → sliding window](#11.3)
- [11.4 — "Sum of a range, asked over and over" → prefix sums](#11.4)
- [11.5 — "Search a sorted space" → binary search](#11.5)
- [11.6 — "Minimise the maximum / find the smallest feasible value" → binary search on the answer](#11.6)
- [11.7 — "Overlapping ranges — merge them, or count conflicts" → interval problems](#11.7)
- [11.8 — "Detect a cycle, or find the middle, in one pass with no extra memory" → fast & slow pointers](#11.8)
- [11.9 — "Reverse or reorder a linked list in place" → pointer manipulation](#11.9)
- [11.10 — "For each element, find the next greater/smaller one" → monotonic stack](#11.10)
- [11.11 — "Maximum (or minimum) of every sliding window" → monotonic deque](#11.11)
- [11.12 — "Kth largest, top-K, or merge K sorted things" → heaps](#11.12)
- [11.13 — "Visit every node in a tree" → depth-first search (DFS)](#11.13)
- [11.14 — "Process a tree level by level" → breadth-first search (BFS)](#11.14)
- [11.15 — "Search or insert in an ordered tree" → BST operations](#11.15)
- [11.16 — "Explore a grid, map, or network of connections" → graph BFS/DFS](#11.16)
- [11.17 — "Order tasks with dependencies" → topological sort](#11.17)
- [11.18 — "Cheapest path when edges have different costs" → Dijkstra](#11.18)
- [11.19 — "Group connected things / are these two in the same group?" → union-find](#11.19)
- [11.20 — "Generate all valid combinations, with pruning" → backtracking](#11.20)
- [11.21 — "Count the ways / find the optimum over overlapping subproblems" → dynamic programming (1D)](#11.21)
- [11.22 — "Optimum over a grid or two interacting dimensions" → 2D dynamic programming](#11.22)
- [11.23 — "Compare or align two sequences" → string DP (edit distance, LCS)](#11.23)
- [11.24 — "A locally-best choice is globally optimal" → greedy (and how to know it's safe)](#11.24)
- [11.25 — "Prefix lookups, autocomplete, many-words matching" → tries](#11.25)
- [11.26 — "Flip, test, or combine bits / track a set of flags compactly" → bit manipulation](#11.26)
- [11.27 — "Walk or transform a matrix in a specific pattern" → matrix traversal](#11.27)
- [11.28 — "Break a problem into a smaller version of itself" → recursion fundamentals](#11.28)
- [11.29 — "Generate all subsets / permutations / combinations" → combinatorial enumeration](#11.29)
- [11.30 — "I've read the problem — now which pattern is it?" → reading a problem to pick the approach](#11.30)

---


<a id="11.1"></a>
## 11.1 — "Find pairs/duplicates/complements fast" → arrays + hashing

### The situation

A classic problem: *given an array of numbers and a target, return indices of the two numbers
that add up to the target* ("Two Sum"). The brute-force solution is the first thing everyone
writes:

```python
def two_sum(nums, target):
    for i in range(len(nums)):              # for each number...
        for j in range(i + 1, len(nums)):   # ...check every later number
            if nums[i] + nums[j] == target:
                return [i, j]
# correct, but O(n²): on 100,000 elements that's ~5 billion comparisons -> too slow
```

The nested loop checks every pair — O(n²) (2.2). For a large array, or an interview, that's
the *wrong* answer even though it's correct: there's a linear-time solution hiding in the
problem.

### What's really going on

The problem is secretly a **lookup**: for each number `x`, you're asking "have I already seen
`target - x`?" (its **complement**). Re-scanning the array to answer that is O(n) per element,
giving O(n²) — but a **hash table** (dict/set) answers "have I seen this value?" in O(1)
(this is the core idea from Area 1's 1.1 and Area 3's 3.13, applied to algorithms).

So the pattern: **as you walk the array once, store what you've seen in a dict; for each new
element, check the dict for the value that would complete the answer.** This converts
"check every pair" (O(n²)) into "one pass with O(1) lookups" (O(n)) — trading O(n) extra
memory for the speed-up.

> **Trigger:** "find a pair / duplicate / complement / 'have I seen X?' in an array,"
> especially when the brute force is a nested-loop O(n²). **Pattern:** one pass, storing seen
> values (and their indices) in a **hash map/set**, checking O(1) for the value that completes
> the answer. **Result:** O(n²) → O(n), at the cost of O(n) memory. This hashing instinct
> underlies a huge fraction of "easy/medium" array problems.

### The move

Walk once, keeping a dict of values seen so far; for each element look up its complement:

```python
def two_sum(nums, target):
    seen = {}                               # value -> index, of elements already passed
    for i, x in enumerate(nums):            # one pass (enumerate, 1.5)
        if target - x in seen:              # O(1): have we seen the complement?
            return [seen[target - x], i]    # yes -> answer found
        seen[x] = i                          # record this value's index for future lookups
```

### Why it works

Each element is processed once. When you reach `x`, every earlier element is already in
`seen`, so `target - x in seen` checks in O(1) whether a previous number pairs with `x` to hit
the target — no re-scanning. If found, `seen` also holds that number's index, so you return
both. Storing `x` *after* the check ensures you don't pair an element with itself. Total work
is n elements × O(1) lookup = **O(n)** time and **O(n)** space — the hash map is what removes
the inner loop. The same "store seen, look up the completing value" structure solves a whole
family of problems, not just Two Sum.

### The code, every line explained

```python
# --- Two Sum: the canonical example -------------------------------------
def two_sum(nums, target):
    seen = {}                               # maps value -> its index
    for i, x in enumerate(nums):
        need = target - x                    # the complement that would complete the pair
        if need in seen:                     # O(1) lookup (vs O(n) re-scan in brute force)
            return [seen[need], i]
        seen[x] = i                          # store AFTER checking -> no self-pairing
    return []                                # no pair found

# --- the same hashing instinct, other problems --------------------------
# contains duplicate: "is any value repeated?" -> a SET (3.13)
def has_dup(nums):
    seen = set()
    for x in nums:
        if x in seen: return True            # O(1) "seen before?"
        seen.add(x)
    return False

# group anagrams: key by a canonical form -> defaultdict buckets (3.15 + 4.x)
from collections import defaultdict
def group_anagrams(words):
    groups = defaultdict(list)
    for w in words:
        groups["".join(sorted(w))].append(w)   # sorted letters = same for all anagrams
    return list(groups.values())

# count frequencies / "top K" -> Counter (3.14), often + a heap (11.12)
from collections import Counter
def first_unique(s):
    counts = Counter(s)
    for i, ch in enumerate(s):
        if counts[ch] == 1: return i          # first char that appears exactly once
    return -1

# --- when NOT to reach for hashing --------------------------------------
# - input is SORTED and you want a pair summing to target -> TWO POINTERS (11.2) is O(1)
#   space (no hash map needed) — sorted input is the signal to consider that instead.
# - you need RANGE queries / order -> hashing loses order; consider sorting/prefix sums (11.4).
```

### Impact

- **O(n²) → O(n):** the defining win — replacing a re-scan with an O(1) hash lookup turns the
  brute force into a single pass, the difference between "too slow" and instant on large
  inputs (and between a rejected and accepted interview answer).
- **Broad applicability:** the "store seen / look up the completing value" shape solves pairs,
  duplicates, complements, anagram grouping, frequency, and first-unique — a large slice of
  array/string problems.
- **Simple to reason about:** one pass, one dict — easy to write correctly and explain
  (11.30).

### Pros & cons / when NOT to

**Reach for arrays + hashing when:** the problem asks about pairs, duplicates, complements, "
have I seen X?", grouping by a key, or frequencies — and the naive solution is a nested-loop
O(n²).

**Watch out / when NOT to:**
- **Costs O(n) memory** — you trade space for time. Usually worth it, but if memory is tight
  or the input is already sorted, **two pointers** (11.2) may solve a pair-sum in O(1) extra
  space.
- **Hashing loses order and range structure** — for "sum of a range", "k-th smallest", or
  ordered queries, use prefix sums (11.4), sorting, or a heap (11.12) instead.
- **Keys must be hashable** — to bucket lists/sequences, convert to a tuple or a canonical
  string (the anagram `"".join(sorted(w))` trick); unhashable keys raise (1.1).
- **Watch self-pairing and duplicates** — store after checking (as above); for problems with
  repeated values, decide whether you want indices, counts, or unique values (set vs Counter).
- **Order-of-operations matters for indices** — return the stored index *then* the current
  one; mixing them up is a common off-by-one.

### Where this shows up

- **Interview classics:** Two Sum, Contains Duplicate, Group Anagrams, First Unique Character,
  Valid Anagram, Subarray Sum Equals K (hashing prefix sums, 11.4), Longest Consecutive
  Sequence — all hashing at their core.
- **Real work (the crossover):** this *is* the dedup/Counter/groupby/dict-join toolkit from
  Area 3 (3.13–3.16) — the same instinct that makes data-wrangling fast is what cracks these
  problems.
- **Pattern mapping:** the foundational pattern; many other patterns (sliding window 11.3,
  prefix sums 11.4) combine hashing with another idea.
[↑ Back to top](#contents)

---

<a id="11.2"></a>
## 11.2 — "Scan a sorted array from both ends" → two pointers

### The situation

*Given a **sorted** array, find two numbers that sum to a target.* You could hash (11.1), but
the array being sorted unlocks a cheaper approach — and some problems (reversing, removing
duplicates in place, partitioning) need O(1) extra space that hashing can't give:

```python
# brute force: O(n²) pairs; hashing: O(n) time + O(n) space.
# but the array is SORTED — can we do O(n) time AND O(1) space?
nums = [2, 7, 11, 15]; target = 9     # sorted!
```

### What's really going on

When data is **sorted** (or you process from both ends, or compare adjacent elements), you can
often use **two pointers**: one at each end (or two moving in tandem), moving them toward each
other based on a comparison, so each element is visited once — O(n) time, O(1) space.

For the sorted pair-sum: put `lo` at the start, `hi` at the end. If `nums[lo] + nums[hi]` is
*too small*, the only way to grow the sum is to move `lo` right (to a bigger number); if *too
big*, move `hi` left. Each step eliminates one element, so it's O(n) — and uses no extra
memory, unlike hashing.

> **Trigger:** the input is **sorted**, or the problem is "pair from both ends," "reverse in
> place," "remove/partition in place," or "compare elements converging from two sides."
> **Pattern:** two indices moving toward each other (or in tandem), advanced by a comparison.
> **Result:** O(n) time, **O(1)** space — the space win over hashing (11.1) when the input is
> sorted, and the in-place tool when you can't allocate.

### The move

Put one pointer at each end; move the one that brings you closer to the goal:

```python
def two_sum_sorted(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        s = nums[lo] + nums[hi]
        if s == target:   return [lo, hi]
        if s < target:    lo += 1          # too small -> need a bigger number -> move lo right
        else:             hi -= 1          # too big   -> need a smaller number -> move hi left
```

### Why it works

Because the array is sorted, the comparison tells you *which* pointer to move: if the sum is
too small, every pair using `hi` with an index ≤ `lo` is also too small, so `lo` can never be
the answer with the current `hi` — advance `lo`. Symmetrically for too big, retreat `hi`. Each
step permanently discards one element from consideration, so the pointers meet after at most n
steps — **O(n) time** — using only two index variables — **O(1) space**. That sortedness is
the key: it's what makes "move this pointer" provably correct, which is why two pointers and
sorting so often go together.

### The code, every line explained

```python
# --- converging pointers: sorted pair-sum -------------------------------
def two_sum_sorted(nums, target):
    lo, hi = 0, len(nums) - 1               # start at both ends
    while lo < hi:                           # until they meet
        s = nums[lo] + nums[hi]
        if s == target:  return [lo, hi]
        elif s < target: lo += 1             # increase the sum (sorted -> bigger to the right)
        else:            hi -= 1             # decrease the sum
    return []

# --- in-place reverse: pointers swap from both ends (O(1) space) --------
def reverse(a):
    lo, hi = 0, len(a) - 1
    while lo < hi:
        a[lo], a[hi] = a[hi], a[lo]          # swap (1.6) — no extra array allocated
        lo += 1; hi -= 1

# --- tandem (slow/fast) pointers: remove duplicates from a SORTED array --
def dedup_sorted(a):
    if not a: return 0
    slow = 0                                 # slow = last unique position written
    for fast in range(1, len(a)):            # fast scans ahead
        if a[fast] != a[slow]:               # found a new value
            slow += 1
            a[slow] = a[fast]                # write it just after the last unique
    return slow + 1                          # length of the deduped prefix (in place, O(1) space)

# --- palindrome check: converge and compare ----------------------------
def is_palindrome(s):
    lo, hi = 0, len(s) - 1
    while lo < hi:
        if s[lo] != s[hi]: return False
        lo += 1; hi -= 1
    return True

# --- 3Sum: sort, then fix one element and two-point the rest ------------
def three_sum(nums):
    nums.sort(); res = []                     # sorting (O(n log n)) ENABLES two pointers
    for i in range(len(nums) - 2):
        if i and nums[i] == nums[i-1]: continue        # skip duplicates for `i`
        lo, hi = i + 1, len(nums) - 1
        while lo < hi:
            s = nums[i] + nums[lo] + nums[hi]
            if s < 0: lo += 1
            elif s > 0: hi -= 1
            else:
                res.append([nums[i], nums[lo], nums[hi]])
                lo += 1; hi -= 1
                while lo < hi and nums[lo] == nums[lo-1]: lo += 1   # skip dup answers
    return res
```

### Impact

- **O(1) space:** unlike hashing (11.1), two pointers solve sorted pair-problems and in-place
  rearrangements without extra memory — the key advantage when the input is sorted or memory
  is constrained.
- **O(n) scans:** converging/tandem pointers visit each element once, turning many O(n²)
  brute forces into linear passes.
- **In-place transforms:** reversing, deduping, and partitioning happen *within* the array,
  no allocation — essential for memory-bound or "modify in place" requirements.

### Pros & cons / when NOT to

**Reach for two pointers when:** the array is **sorted** (pair/triple sums, closest pair), or
the task is reverse/dedup/partition **in place**, or you compare elements **converging from
both ends** (palindrome).

**Watch out / when NOT to:**
- **Usually needs sorted input** — for an unsorted pair-sum where you only need *a* pair,
  hashing (11.1) is O(n) without sorting; sorting first costs O(n log n). Sort when the
  problem is *already* sorted, needs order anyway (3Sum), or when O(1) space matters.
- **Off-by-one and termination** — `while lo < hi` (not `<=`) for pairs so you don't pair an
  element with itself; advance the right pointer each branch or you loop forever.
- **Duplicate handling** in problems like 3Sum requires explicit skip-the-duplicate steps, or
  you emit repeated answers — a classic bug.
- **Doesn't apply to unsorted "which pointer to move?" problems** — if a comparison can't tell
  you which side to advance, two pointers won't work; reach for hashing or sorting first.

### Where this shows up

- **Interview classics:** Two Sum II (sorted), 3Sum / 4Sum, Container With Most Water, Valid
  Palindrome, Remove Duplicates from Sorted Array, Move Zeroes, Sort Colours (Dutch flag
  partition), Trapping Rain Water.
- **Real work (the crossover):** merging two **sorted** streams/files (the merge step of merge
  sort, and `heapq.merge`, Area 3), in-place array compaction, and comparing sorted sequences
  — the same converging-pointer logic.
- **Pattern mapping:** closely related to **sliding window** (11.3, two pointers moving the
  same direction over a window), **fast/slow pointers** (11.8, on linked lists), and the merge
  step that sorting and many other algorithms rely on.
[↑ Back to top](#contents)

---

<a id="11.3"></a>
## 11.3 — "Longest/shortest/best contiguous subarray or substring" → sliding window

### The situation

*Find the length of the longest substring without repeating characters.* Or *the maximum sum
of any contiguous subarray of size k.* The brute force checks every subarray:

```python
def longest_unique(s):
    best = 0
    for i in range(len(s)):
        for j in range(i, len(s)):          # every (i, j) substring -> O(n²) substrings
            if len(set(s[i:j+1])) == j - i + 1:   # ...and O(n) to check each -> O(n³)!
                best = max(best, j - i + 1)
    return best
```

Re-examining every contiguous range is O(n²) or worse. But the answer is always a *contiguous*
window, and as the window moves, most of it overlaps the previous one — so recomputing from
scratch is wasted work.

### What's really going on

When the problem asks for the best/longest/shortest **contiguous** subarray or substring
satisfying some condition, you can use a **sliding window**: two pointers (`left`, `right`)
bounding a contiguous range that you **grow and shrink** instead of recomputing. You extend
`right` to include new elements; when the window violates the condition, you advance `left` to
shrink it back to validity. Each pointer only ever moves *forward*, so across the whole array
they take at most 2n steps — **O(n)**.

The key insight: as the window slides by one, you **update** the running state (a sum, a count,
a set of seen chars) incrementally — add the entering element, remove the leaving one — rather
than recomputing over the whole window. That incremental update is what collapses O(n²) into
O(n).

> **Trigger:** "longest / shortest / maximum / minimum **contiguous** subarray or substring
> satisfying a condition" (sum ≤ k, no repeats, at most K distinct, etc.). **Pattern:** a
> window `[left, right]` that grows by advancing `right` and shrinks by advancing `left` when
> the condition breaks, **incrementally** updating running state. **Result:** O(n) — each
> pointer moves forward only. (Fixed-size window: slide a constant-width window; variable-size:
> grow/shrink to satisfy the condition.)

### The move

Expand `right` to include each element; shrink `left` while the window is invalid; track the
best valid window:

```python
def longest_unique(s):
    seen = set(); left = best = 0
    for right, ch in enumerate(s):
        while ch in seen:                    # window invalid (repeat) -> shrink from the left
            seen.remove(s[left]); left += 1
        seen.add(ch)                          # now valid: include the new char
        best = max(best, right - left + 1)    # update best window length
    return best
```

### Why it works

`right` sweeps the array once, pulling each element into the window. When adding `ch` would
break the "no repeats" condition, the `while` advances `left`, removing elements until the
window is valid again. Crucially, `left` never moves backward — so although there's a nested
`while`, each index is added once and removed at most once, giving at most 2n pointer moves
total: **O(n)**, not O(n²). The running state (`seen`) is updated **incrementally** — add the
entering char, remove the leaving ones — so checking validity is O(1) per step instead of
re-scanning the window. The window always represents the best *valid* range ending at `right`,
so tracking its size finds the global best.

### The code, every line explained

```python
# --- VARIABLE-size window: longest substring without repeats ------------
def longest_unique(s):
    seen = set()                              # chars currently IN the window
    left = best = 0
    for right, ch in enumerate(s):            # right grows the window (1.5)
        while ch in seen:                      # condition broken -> shrink from left
            seen.remove(s[left]); left += 1    # remove leaving char, advance left
        seen.add(ch)                           # add entering char -> window valid again
        best = max(best, right - left + 1)     # window size = right - left + 1
    return best

# --- FIXED-size window: max sum of any k-length subarray ----------------
def max_sum_k(nums, k):
    window = sum(nums[:k])                    # first window's sum (compute ONCE)
    best = window
    for right in range(k, len(nums)):
        window += nums[right] - nums[right-k]  # INCREMENTAL: add entering, drop leaving (O(1))
        best = max(best, window)               # not re-summing the whole window each step
    return best

# --- variable window with a CONSTRAINT: smallest subarray with sum >= target
def min_subarray_len(target, nums):
    left = total = 0; best = float("inf")
    for right, x in enumerate(nums):
        total += x                             # grow
        while total >= target:                 # shrink while STILL valid -> find minimal
            best = min(best, right - left + 1)
            total -= nums[left]; left += 1
    return best if best != float("inf") else 0

# --- "at most K distinct" — window + a Counter (3.14) -------------------
from collections import Counter
def longest_k_distinct(s, k):
    count = Counter(); left = best = 0
    for right, ch in enumerate(s):
        count[ch] += 1
        while len(count) > k:                  # too many distinct -> shrink
            count[s[left]] -= 1
            if count[s[left]] == 0: del count[s[left]]
            left += 1
        best = max(best, right - left + 1)
    return best

# --- the giveaway vs the trap -------------------------------------------
# CONTIGUOUS subarray/substring + best/longest/shortest -> sliding window.
# But NON-contiguous (subSEQUENCE, any subset) is NOT a window -> usually DP (11.21+).
# And negative numbers break "shrink while >= target" monotonicity -> window may not apply.
```

### Impact

- **O(n²)/O(n³) → O(n):** the incremental window update removes the repeated re-scanning of
  overlapping ranges — often the decisive speed-up for substring/subarray problems.
- **O(1) or O(k) space:** the window keeps only running state (a sum, a small Counter/set), not
  every subarray — memory-light.
- **One reusable template:** grow-right / shrink-left-while-invalid / update-best covers a
  large family of problems with small variations.

### Pros & cons / when NOT to

**Reach for sliding window when:** the answer is a **contiguous** subarray/substring and you
want the longest/shortest/max/min satisfying a condition, or a fixed-size window statistic
(moving average/sum).

**Watch out / when NOT to:**
- **Must be contiguous.** A subSEQUENCE (non-contiguous, pick any subset preserving order) is
  *not* a window — that's usually dynamic programming (11.21+). Misreading "subsequence" as
  "subarray" is a classic trap.
- **Needs monotonic shrink logic.** The window works when growing/shrinking changes validity
  predictably. **Negative numbers** can break "shrink while sum ≥ target" (adding can decrease
  the sum), so some sum-condition problems need prefix sums (11.4) + hashing instead.
- **Update state incrementally, not by recomputing** — the whole point is O(1) per step; if you
  `sum(window)` or `set(window)` each move, you're back to O(n²). Add the entering element,
  remove the leaving one.
- **Fixed vs variable** — fixed-size slides a constant width (compute the first window, then
  add-one/drop-one); variable-size grows/shrinks to meet a condition. Pick the right shape.
- **Off-by-one in window size** — it's `right - left + 1`; getting the inclusive bounds wrong
  is the common bug.

### Where this shows up

- **Interview classics:** Longest Substring Without Repeating Characters, Minimum Size Subarray
  Sum, Longest Substring with At Most K Distinct, Permutation in String, Max Consecutive Ones,
  Sliding Window Maximum (window + a monotonic deque, 11.11).
- **Real work (the crossover):** moving averages / rolling sums over a time series, "events in
  the last N seconds," rate calculations over a window, and fixed-window aggregates — the same
  add-one/drop-one incremental update (ties to Area 3 time-series and Area 9 token windows).
- **Pattern mapping:** a same-direction specialisation of two pointers (11.2); pairs with
  Counter/set (11.1) for state, prefix sums (11.4) when windows don't fit, and a monotonic
  deque (11.11) for window min/max.
[↑ Back to top](#contents)

---

<a id="11.4"></a>
## 11.4 — "Sum of a range, asked over and over" → prefix sums

### The situation

*Given an array, answer many queries of the form "what's the sum of elements from index i to
j?"* The naive answer re-sums the range each time:

```python
def range_sum(nums, i, j):
    return sum(nums[i:j+1])          # O(n) per query
# with Q queries that's O(Q × n) — for many queries on a big array, far too slow
```

Each query re-adds the same elements; across many overlapping queries that's enormous repeated
work.

### What's really going on

When you need **repeated range-sum (or range-aggregate) queries** over a static array,
precompute a **prefix sum** array once: `prefix[k]` = sum of the first `k` elements. Then the
sum of any range `[i, j]` is `prefix[j+1] - prefix[i]` — an **O(1)** subtraction, no
re-summing. You pay O(n) once to build it, then answer each query in O(1).

The deeper idea: `prefix[j+1] - prefix[i]` cancels the shared prefix, leaving exactly the
range. This "difference of running totals" trick extends to a powerful variant: combine prefix
sums with a **hash map** (11.1) to count/locate subarrays with a given sum in O(n) — the key to
problems like "number of subarrays summing to k" where sliding window (11.3) fails on negative
numbers.

> **Trigger:** many **range-sum / range-aggregate** queries on a static array, or "subarray
> summing to k / divisible by k." **Pattern:** precompute running totals (`prefix`) once;
> `range_sum(i,j) = prefix[j+1] - prefix[i]` in **O(1)**. With a **hash map of prefix sums
> seen**, count subarrays with a target sum in **O(n)** — works with negatives where windows
> (11.3) don't. **Cost:** O(n) precompute + O(n) space, then O(1) per query.

### The move

Build a running-total array once; answer each range query by subtracting two prefix values:

```python
def build_prefix(nums):
    prefix = [0]                            # prefix[0] = 0 (sum of zero elements)
    for x in nums:
        prefix.append(prefix[-1] + x)       # prefix[k] = sum of first k elements
    return prefix

def range_sum(prefix, i, j):                # inclusive sum of nums[i..j]
    return prefix[j+1] - prefix[i]          # O(1): cancels the shared prefix
```

### Why it works

`prefix[k]` holds the total of the first `k` elements, so `prefix[j+1]` is "everything up to
and including `j`" and `prefix[i]` is "everything before `i`." Subtracting removes the shared
front portion, leaving exactly the range `[i, j]` — one subtraction, **O(1)**, regardless of
range size. The leading `prefix[0] = 0` sentinel makes the formula work uniformly (including
ranges starting at index 0) without special cases. For the subarray-sum-equals-k variant, note
that a subarray `[i+1, j]` sums to `k` exactly when `prefix[j+1] - prefix[i] = k`, i.e.
`prefix[i] = prefix[j+1] - k` — so as you compute prefixes left to right, a hash map of "prefix
sums seen so far" lets you count, in O(1) per step, how many earlier prefixes complete a
`k`-sum (the hashing pattern, 11.1, applied to running totals) — O(n) total, and correct even
with negative numbers.

### The code, every line explained

```python
# --- prefix sums: O(n) build, O(1) range queries ------------------------
def build_prefix(nums):
    prefix = [0]                            # sentinel: sum of first 0 elements
    for x in nums:
        prefix.append(prefix[-1] + x)
    return prefix                            # len = len(nums) + 1

prefix = build_prefix([3, 1, 4, 1, 5])      # -> [0, 3, 4, 8, 9, 14]
def range_sum(i, j):
    return prefix[j+1] - prefix[i]
range_sum(1, 3)                              # nums[1..3] = 1+4+1 = 6  -> prefix[4]-prefix[1] = 9-3

# --- the powerful variant: count subarrays summing to k (hashing, 11.1) -
from collections import defaultdict
def subarray_sum_k(nums, k):
    count = 0
    running = 0
    seen = defaultdict(int); seen[0] = 1     # one empty prefix (sum 0) seen before we start
    for x in nums:
        running += x                          # prefix sum up to here
        count += seen[running - k]            # how many earlier prefixes give a k-sum here
        seen[running] += 1                     # record this prefix sum
    return count
# O(n) time, O(n) space — and CORRECT WITH NEGATIVES, where sliding window (11.3) fails.

# --- 2D prefix sums: O(1) rectangle-sum queries on a grid ---------------
# pre[r+1][c+1] = sum of the sub-rectangle from (0,0) to (r,c); a rectangle sum is then
# pre[r2+1][c2+1] - pre[r1][c2+1] - pre[r2+1][c1] + pre[r1][c1]  (inclusion-exclusion).

# --- difference array: the INVERSE (many range UPDATES, one read) -------
# to add `v` to every element in [i, j] for MANY ranges, then read the final array:
#   diff[i] += v; diff[j+1] -= v   (O(1) per update); prefix-sum diff at the end -> result.
# prefix sums answer range QUERIES; difference arrays batch range UPDATES.

# --- when a window is enough --------------------------------------------
# for a SINGLE pass / one moving window with non-negative values, sliding window (11.3) is
# O(1) space. Prefix sums shine for MANY queries, or sum-condition counting with negatives.
```

### Impact

- **O(n) per query → O(1):** repeated range sums become constant-time after one O(n)
  precompute — decisive when there are many queries (Q×n → Q + n).
- **Unlocks negative-number subarray problems:** prefix-sum + hashing counts subarrays with a
  target sum in O(n) even with negatives, where sliding window's monotonic shrink breaks
  (11.3).
- **Generalises:** extends to 2D rectangle sums (inclusion–exclusion) and, inverted as a
  difference array, to batching many range *updates*.

### Pros & cons / when NOT to

**Reach for prefix sums when:** answering **many** range-sum/aggregate queries on a static
array, or counting subarrays with a sum condition (= k, divisible by k) — especially with
negative values.

**Watch out / when NOT to:**
- **The array must be static** (or rarely updated). If elements change between queries, a plain
  prefix array is stale after each update; use a **Fenwick/BIT** or **segment tree** for O(log
  n) updates *and* queries instead.
- **Mind the off-by-one** — the `prefix[0]=0` sentinel and the `prefix[j+1]-prefix[i]` indexing
  are the classic bug source. Keep `len(prefix) = n+1` and derive the formula carefully.
- **Single window? prefer sliding window (11.3)** — for one pass / one moving window with
  non-negative values, a window is O(1) space; prefix sums pay off for *many* queries or
  negative-number counting.
- **O(n) (or O(n·m) in 2D) extra space** — usually fine, but note the memory for very large
  inputs.
- **For min/max/gcd over ranges, not sum**, a plain prefix doesn't invert (you can't "subtract"
  a max) — use a sparse table or segment tree.

### Where this shows up

- **Interview classics:** Range Sum Query – Immutable, Subarray Sum Equals K, Continuous
  Subarray Sum (divisible by k), Subarray Sums Divisible by K, Maximum Size Subarray Sum Equals
  k, 2D Range Sum (Matrix).
- **Real work (the crossover):** cumulative sums / running totals over time series, "total in
  date range" analytics queries, and the cumulative-aggregate columns you build in
  pandas/SQL (the data-wrangling cousin in Area 3) — same precompute-then-subtract idea.
- **Pattern mapping:** combines with hashing (11.1) for sum-condition counting; the static-data
  counterpart to segment trees/Fenwick (dynamic ranges); inverse of the difference-array update
  trick.
[↑ Back to top](#contents)

---

<a id="11.5"></a>
## 11.5 — "Search a sorted space" → binary search

### The situation

*Find the index of a target value in a **sorted** array.* The obvious scan checks every
element:

```python
def find(nums, target):
    for i, x in enumerate(nums):     # O(n): checks up to all n elements
        if x == target: return i
    return -1
```

On a sorted array of a billion elements that's a billion comparisons in the worst case — but
the sortedness means you can discard *half* the remaining candidates with a single comparison.

### What's really going on

When the search space is **sorted** (or otherwise **monotonic** — see 11.6), **binary search**
finds the answer in **O(log n)** by repeatedly halving the range. Look at the middle element:
if it's the target, done; if the target is smaller, it can only be in the left half (discard
the right); if larger, the right half (discard the left). Each comparison eliminates half the
remaining candidates, so a billion elements take ~30 steps, not a billion.

The mechanism is "maintain a `[lo, hi]` range known to contain the answer, and shrink it by
half each step." Binary search is conceptually simple but **notoriously easy to get wrong** —
the bugs are in the boundaries (`<` vs `<=`), the midpoint, and how you move `lo`/`hi`. For
plain "find in sorted list," prefer Python's **`bisect`** module (the same tool from Area 3,
3.20) rather than hand-rolling.

> **Trigger:** searching a **sorted** array, or any space where a condition is **monotonic**
> (false…false, true…true). **Pattern:** keep a `[lo, hi]` range containing the answer; check
> the midpoint; discard the half that can't contain it. **Result:** **O(log n)**. Use
> **`bisect`** (3.20) for plain lookups/insertion points; hand-roll only for variants. The
> generalisation — "binary search on the *answer*" — is 11.6.

### The move

Maintain `[lo, hi]`, compare the midpoint, halve the range each step:

```python
def binary_search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:                          # inclusive range [lo, hi]
        mid = (lo + hi) // 2
        if nums[mid] == target: return mid
        elif nums[mid] < target: lo = mid + 1   # target is in the right half
        else:                    hi = mid - 1   # target is in the left half
    return -1                                 # not found
```

### Why it works

The invariant is "if the target is present, it lies within `[lo, hi]`." Each iteration checks
the midpoint and, using sortedness, discards the half that provably can't hold the target —
shrinking the range by ~half. Because the range halves each step, it reaches size 1 in
`log₂(n)` steps: **O(log n)**. The boundary details are what make it correct: `while lo <= hi`
with an *inclusive* range, `lo = mid + 1` / `hi = mid - 1` to always make progress (never
leave `mid` in the range, or you can loop forever), and `mid = (lo + hi) // 2`. Getting any of
these subtly wrong causes infinite loops or off-by-one misses — which is exactly why
`bisect` exists for the common cases.

### The code, every line explained

```python
import bisect

# --- PREFER bisect for standard lookups / insertion points (3.20) -------
i = bisect.bisect_left(nums, target)         # leftmost index where target could insert
found = i < len(nums) and nums[i] == target  # present iff that slot holds target
# bisect_left / bisect_right also give "first >= x" / "first > x" — count in a range, etc.

# --- hand-rolled exact search (know this, but use bisect when you can) --
def binary_search(nums, target):
    lo, hi = 0, len(nums) - 1                # INCLUSIVE range
    while lo <= hi:                           # <= because hi is a valid index
        mid = (lo + hi) // 2                  # midpoint (Python ints don't overflow; in
                                              # other languages use lo + (hi-lo)//2)
        if nums[mid] == target: return mid
        elif nums[mid] < target: lo = mid + 1 # discard left half incl. mid
        else:                    hi = mid - 1 # discard right half incl. mid
    return -1

# --- find the FIRST index satisfying a condition (left-bound template) --
def first_true(nums, pred):
    lo, hi = 0, len(nums)                     # HALF-OPEN [lo, hi); hi = len (not len-1)
    while lo < hi:                            # < for half-open
        mid = (lo + hi) // 2
        if pred(nums[mid]): hi = mid          # condition holds -> answer is mid or left
        else:               lo = mid + 1      # doesn't hold -> answer is right of mid
    return lo                                 # first index where pred is True (or len)
# e.g. first element >= x:  first_true(nums, lambda v: v >= x)

# --- search in a ROTATED sorted array (a common twist) ------------------
def search_rotated(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target: return mid
        if nums[lo] <= nums[mid]:             # left half is sorted
            if nums[lo] <= target < nums[mid]: hi = mid - 1
            else: lo = mid + 1
        else:                                 # right half is sorted
            if nums[mid] < target <= nums[hi]: lo = mid + 1
            else: hi = mid - 1
    return -1

# --- the bug sources (why bisect is preferred) --------------------------
# - <= vs < must MATCH the range convention (inclusive [lo,hi] -> <= ; half-open [lo,hi) -> <)
# - always move past mid (mid+1 / mid-1, or set hi=mid in half-open) or you INFINITE-LOOP
# - pick ONE template (inclusive or half-open) and use it consistently; don't mix them
```

### Impact

- **O(n) → O(log n):** halving the search space each step turns a billion-element scan into
  ~30 comparisons — the canonical logarithmic speed-up on sorted data.
- **O(1) space:** just two indices; no extra structure (unlike hashing, 11.1).
- **Foundation for more:** the same halving logic powers insertion points (`bisect`, 3.20),
  "first/last satisfying a condition," rotated-array search, and binary-search-on-answer
  (11.6).

### Pros & cons / when NOT to

**Reach for binary search when:** the data is **sorted**, or a predicate over the search space
is **monotonic** (all-false then all-true), and you want O(log n) instead of O(n).

**Watch out / when NOT to:**
- **Requires sorted/monotonic input.** On unsorted data, binary search is wrong; either sort
  first (O(n log n) — worth it only if you'll search many times) or use hashing (11.1) for O(1)
  membership without order.
- **Boundary bugs are the norm, not the exception** — `<` vs `<=`, the midpoint, and
  `mid±1` vs `mid` must match your range convention. Pick one template (inclusive `[lo,hi]` or
  half-open `[lo,hi)`) and never mix them. **Prefer `bisect`** for standard lookups/insertion.
- **Always make progress past `mid`** — failing to (e.g. `lo = mid` in an inclusive range) is
  the classic infinite loop.
- **For a single lookup on unsorted data, don't sort just to binary-search** — a linear scan
  or a set is simpler and often faster overall.
- **Duplicates** — for "first/last occurrence" or counts, use the left/right-bound templates
  (`bisect_left`/`bisect_right`), not the exact-match version.

### Where this shows up

- **Interview classics:** Binary Search, Search Insert Position, First/Last Position of Element,
  Search in Rotated Sorted Array, Find Minimum in Rotated Array, Find Peak Element, Search a 2D
  Matrix.
- **Real work (the crossover):** `bisect` for insertion points and range counts on sorted data
  (3.20), looking up a value in a sorted index/log by timestamp, and the search step inside
  many algorithms and databases (B-tree lookups are binary search's cousin).
- **Pattern mapping:** the basis for binary-search-on-answer (11.6); pairs with sorting (which
  *enables* it) and `bisect` (the library realisation, 3.20).
[↑ Back to top](#contents)

---

<a id="11.6"></a>
## 11.6 — "Minimise the maximum / find the smallest feasible value" → binary search on the answer

### The situation

*You must ship all packages within `D` days; each day you load a contiguous run of packages up
to the ship's capacity. Find the **minimum capacity** that lets you finish in `D` days.* There's
no array to search — the answer is a *number* (a capacity) you're solving for:

```python
# brute force: try capacity = 1, 2, 3, ... and check feasibility for each -> O(answer_range × n)
# the answer range can be huge (sum of all weights) -> too slow
```

It doesn't look like a search problem — there's no sorted list. But the *space of candidate
answers* has hidden structure.

### What's really going on

Many optimisation problems — "minimise the maximum," "maximise the minimum," "smallest/largest
value that works" — have a **monotonic feasibility**: if capacity `X` works, every capacity
`> X` also works; if `X` fails, every `< X` fails too. That's a false…false…**true**…true
pattern over the candidate answers — exactly what binary search (11.5) needs. So you **binary
search on the answer**: guess a capacity, write a `feasible(capacity)` check, and use its
true/false result to halve the range of candidate answers.

The leap is realising the *thing you're searching* isn't the input array but the **range of
possible answers** `[lo, hi]`, and the "comparison" is a feasibility function you write. Each
check costs O(n), and you do O(log(range)) checks → O(n log(range)), vs trying every candidate.

> **Trigger:** "minimise the maximum," "maximise the minimum," "smallest/largest value such
> that a condition holds," where checking a *specific* value is easy but trying all is slow —
> **and feasibility is monotonic** (works for X ⇒ works for all larger/smaller X). **Pattern:**
> binary search over the **answer range** `[lo, hi]` using a `feasible(x)` predicate (11.5's
> monotonic search). **Result:** O(n · log(range)).

### The move

Write a `feasible(x)` check, then binary-search the answer range for the smallest `x` that
passes:

```python
def min_capacity(weights, days):
    def feasible(cap):                       # can we ship within `days` at this capacity?
        d, load = 1, 0
        for w in weights:
            if load + w > cap: d += 1; load = 0    # start a new day
            load += w
        return d <= days
    lo, hi = max(weights), sum(weights)      # answer range: must hold biggest item .. all in 1 day
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid): hi = mid           # works -> try smaller
        else:             lo = mid + 1       # fails -> need bigger
    return lo
```

### Why it works

Feasibility is monotonic: if capacity `mid` lets you finish in ≤ `days`, any larger capacity
trivially does too (false…false…true…true over capacities). So the candidate answers behave
exactly like a sorted boolean array, and the left-bound binary search (11.5) finds the
*smallest* `mid` where `feasible` flips to true. The range is bounded below by `max(weights)`
(you must fit the heaviest single package) and above by `sum(weights)` (everything in one day),
so `[lo, hi]` is well-defined. Each `feasible` check is an O(n) greedy simulation, and binary
search does O(log(sum)) of them → **O(n · log(sum))**, vastly better than testing every
capacity. The whole trick is recognising the answer space is monotonic and that *checking* a
guess is easy even when *finding* the answer directly is not.

### The code, every line explained

```python
# --- "minimise the maximum": ship packages in D days -------------------
def min_capacity(weights, days):
    def feasible(cap):                       # PREDICATE: is capacity `cap` enough?
        days_used, load = 1, 0
        for w in weights:
            if load + w > cap:               # current day full -> open a new day
                days_used += 1; load = 0
            load += w
        return days_used <= days             # monotonic: bigger cap -> fewer days -> stays True
    lo, hi = max(weights), sum(weights)      # tightest possible .. loosest possible answer
    while lo < hi:                           # left-bound search (11.5) for smallest feasible
        mid = (lo + hi) // 2
        if feasible(mid): hi = mid           # feasible -> answer is mid or smaller
        else:             lo = mid + 1       # infeasible -> answer is larger
    return lo                                # smallest capacity that works

# --- "maximise the minimum": same idea, flipped ------------------------
# e.g. place k cows in stalls to MAXIMISE the minimum distance between them:
#   feasible(d) = "can we place all k cows at least d apart?" -> monotonic (smaller d easier).
#   binary search the LARGEST d that's feasible (mirror the bound moves).

# --- the template ------------------------------------------------------
# 1. identify the ANSWER is a number, and feasibility is MONOTONIC in it
# 2. write feasible(x) -> bool  (often a greedy O(n) check)
# 3. set [lo, hi] to the answer's possible range
# 4. binary search (11.5) for the boundary where feasible flips
# Examples of feasible(): "fits in <= D days", "can split into <= k parts each <= x",
#                         "can finish all tasks in <= t time at this speed", etc.

# --- real-numbered answers (rates, not integers) ------------------------
# if the answer is a FLOAT (e.g. minimum speed), binary-search on reals: iterate a fixed
# number of times (e.g. 100) or until hi-lo < epsilon, instead of lo < hi.

# --- the giveaway -------------------------------------------------------
# "minimum largest ___", "maximum smallest ___", "least X such that Y is possible" + checking
# a candidate is straightforward -> binary search on the answer. (NOT searching the input!)
```

### Impact

- **Turns optimisation into search:** "find the best value" becomes "binary search a monotonic
  predicate" — O(n log(range)) instead of trying every candidate (O(range · n)) or a complex
  direct formula.
- **Reuses an easy check:** you only need a *feasibility* function (often a simple greedy
  simulation), which is far easier to write correctly than solving for the optimum directly.
- **Broadly applicable:** the same template cracks capacity/speed/split/distance optimisation
  problems that look unrelated on the surface.

### Pros & cons / when NOT to

**Reach for binary-search-on-answer when:** the answer is a numeric value, you can *check* a
candidate easily, trying all candidates is too slow, **and feasibility is monotonic** in the
answer.

**Watch out / when NOT to:**
- **Feasibility MUST be monotonic** — "works for X ⇒ works for all larger (or all smaller) X."
  If it isn't (works for some values but not others, non-monotonically), binary search gives a
  wrong answer; you need a different approach (DP, 11.21; greedy; or full search).
- **Get the answer range right** — `lo`/`hi` must bracket the true answer (e.g.
  `max(weights)..sum(weights)`); too narrow misses it, and a wrong bound is a silent bug.
- **Match the boundary template to "smallest" vs "largest"** — minimise uses the left-bound
  search (shrink `hi` on feasible); maximise mirrors it. Mixing them up returns the wrong side
  (11.5's boundary discipline).
- **Float answers need epsilon/iteration-count termination**, not `lo < hi` on integers.
- **Don't force it** — if checking a candidate is itself as hard as solving the problem, this
  doesn't help; the win depends on `feasible(x)` being cheap (usually O(n)).

### Where this shows up

- **Interview classics:** Capacity to Ship Packages in D Days, Split Array Largest Sum, Koko
  Eating Bananas, Minimum Number of Days to Make Bouquets, Aggressive Cows / Magnetic Force,
  Minimise Max Distance to Gas Station.
- **Real work (the crossover):** capacity/throughput planning ("smallest cluster size that
  meets the SLA"), rate/threshold tuning where you can *simulate* a candidate cheaply, and
  scheduling/packing decisions — the "find the smallest resource that satisfies a constraint"
  shape.
- **Pattern mapping:** it *is* binary search (11.5) applied to an abstract monotonic predicate
  instead of an array; the feasibility check is often a **greedy** (11.24) simulation.
[↑ Back to top](#contents)

---

<a id="11.7"></a>
## 11.7 — "Overlapping ranges — merge them, or count conflicts" → interval problems

### The situation

*Given a list of intervals `[start, end]`, merge all overlapping ones.* Or *given meeting
times, find the minimum number of rooms needed.* The intervals arrive in arbitrary order:

```python
intervals = [[1, 3], [8, 10], [2, 6], [15, 18]]
# want merged: [[1, 6], [8, 10], [15, 18]]   ([1,3] and [2,6] overlap -> [1,6])
# checking every pair for overlap is O(n²); and in random order you can't tell what merges
```

Comparing every pair is O(n²), and the random order hides which intervals are adjacent.

### What's really going on

Almost every interval problem starts the same way: **sort the intervals by start time.** Once
sorted, overlapping intervals are *adjacent*, so you can resolve everything in a single linear
pass — comparing each interval only to the current "active" one, not to all others. Sorting is
the key that converts an O(n²) all-pairs comparison into O(n log n) sort + O(n) sweep.

For **merging**: walk the sorted intervals; if the next one starts before the current merged
interval ends, they overlap — extend the current end; otherwise, close the current interval and
start a new one. For **counting overlaps / rooms needed**: a **sweep line** processes
start/end events in time order, incrementing a counter on a start and decrementing on an end,
tracking the running maximum (often using a heap, 11.12, of end times).

> **Trigger:** problems about **intervals/ranges** — merge overlapping, insert an interval,
> count overlaps, "minimum meeting rooms," "can attend all meetings," free-time gaps.
> **Pattern:** **sort by start** (sometimes by end), then a single **linear sweep** comparing
> each interval to the current/active one — overlap means "next.start ≤ current.end."
> **Result:** O(n log n) (dominated by the sort). Sorting is the move that makes intervals
> tractable.

### The move

Sort by start, then sweep once, merging or counting as you go:

```python
def merge(intervals):
    intervals.sort(key=lambda x: x[0])       # sort by start (1.15) — overlaps become adjacent
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:           # overlaps the current merged interval
            merged[-1][1] = max(merged[-1][1], end)   # extend its end
        else:
            merged.append([start, end])      # no overlap -> start a new interval
    return merged
```

### Why it works

After sorting by start, any interval that overlaps the current merged one must start *at or
before* its end (`start <= merged[-1][1]`) — and because starts are non-decreasing, you only
ever need to compare against the *last* merged interval, never all previous ones. That's what
turns the O(n²) all-pairs overlap check into a single O(n) pass. When they overlap you extend
the end (taking the `max`, since the next interval might end earlier *or* later); when they
don't, the sorted order guarantees no later interval can overlap this one either, so you safely
close it and open a new one. The sort dominates at **O(n log n)**; the sweep is O(n). For "how
many overlap at once" (rooms), the same sorted structure feeds a sweep-line or a min-heap of
end times (11.12).

### The code, every line explained

```python
# --- MERGE overlapping intervals ----------------------------------------
def merge(intervals):
    intervals.sort(key=lambda x: x[0])       # STEP 1 (always): sort by start
    merged = [intervals[0]]
    for start, end in intervals[1:]:         # STEP 2: single sweep
        if start <= merged[-1][1]:           # overlap: next starts before current ends
            merged[-1][1] = max(merged[-1][1], end)   # max: next may end sooner OR later
        else:
            merged.append([start, end])      # disjoint: begin a new merged interval
    return merged

# --- MIN MEETING ROOMS: min-heap of end times (sweep, 11.12) ------------
import heapq
def min_rooms(intervals):
    intervals.sort(key=lambda x: x[0])       # sort by start
    heap = []                                # holds END times of rooms in use
    for start, end in intervals:
        if heap and heap[0] <= start:        # the earliest-ending room is free by `start`
            heapq.heappop(heap)              # reuse it
        heapq.heappush(heap, end)            # occupy a room until `end`
    return len(heap)                         # rooms still needed at peak = answer

# --- "can attend ALL meetings?" (any overlap at all?) -------------------
def can_attend_all(intervals):
    intervals.sort(key=lambda x: x[0])
    return all(intervals[i][0] >= intervals[i-1][1] for i in range(1, len(intervals)))

# --- INSERT an interval into a sorted, non-overlapping list -------------
def insert(intervals, new):
    res, i, n = [], 0, len(intervals)
    while i < n and intervals[i][1] < new[0]:     # intervals entirely BEFORE new
        res.append(intervals[i]); i += 1
    while i < n and intervals[i][0] <= new[1]:    # intervals overlapping new -> merge
        new = [min(new[0], intervals[i][0]), max(new[1], intervals[i][1])]; i += 1
    res.append(new)
    res.extend(intervals[i:])                     # intervals entirely AFTER new
    return res

# --- sweep line (events): general overlap counting ----------------------
# turn each interval into (+1 at start, -1 at end), sort events by time, run a counter;
# the running max counter = maximum simultaneous overlaps. (Mind start/end tie-breaking:
# does an interval ending at t conflict with one starting at t? define it explicitly.)

# --- which key to sort by ----------------------------------------------
# merge / most problems -> sort by START. greedy "max non-overlapping intervals" -> sort by
# END (11.24, activity selection). Choosing the sort key IS the design decision.
```

### Impact

- **O(n²) → O(n log n):** sorting makes overlaps adjacent, so a single linear sweep replaces
  all-pairs comparison — the standard, expected solution for interval problems.
- **One mental template:** "sort, then sweep comparing to the active interval" covers merge,
  insert, attend-all, free-gaps, and (with a heap) rooms/max-overlap.
- **Clear, debuggable logic:** comparing only to the last/active interval is simple to reason
  about and explain (11.30).

### Pros & cons / when NOT to

**Reach for interval techniques when:** the input is ranges with start/end and you must merge,
insert, detect/count overlaps, schedule, or find gaps.

**Watch out / when NOT to:**
- **Almost always sort first** — forgetting to sort (or sorting by the wrong key) is the #1
  bug. Merge/most → sort by **start**; max non-overlapping selection → sort by **end** (greedy,
  11.24). Choosing the key is the real decision.
- **Define boundary touching explicitly** — does `[1,2]` overlap `[2,3]`? Whether the endpoint
  is inclusive changes `<=` vs `<` in your overlap test; get this from the problem, and be
  consistent.
- **Use `max` when extending the end** — the merging interval may end *before* the current one
  (`[1,9]` then `[2,3]`); `merged[-1][1] = end` (without max) is a classic bug that shrinks the
  interval.
- **Counting max overlap needs a sweep/heap, not just merging** — merging tells you the union,
  not how many are simultaneously active; use end-time events or a min-heap (11.12) for "rooms."
- **Sweep-line tie-breaking** — when starts and ends share a timestamp, decide the event order
  (process ends before starts, or vice versa) per the problem's definition of overlap.

### Where this shows up

- **Interview classics:** Merge Intervals, Insert Interval, Meeting Rooms I/II, Non-overlapping
  Intervals, Minimum Arrows to Burst Balloons, Employee Free Time, Interval List
  Intersections.
- **Real work (the crossover):** calendar/scheduling and resource allocation (rooms, machines),
  merging time ranges in logs/sessions, detecting overlapping bookings, coalescing date ranges
  — the same sort-then-sweep, and the sort-key choice ties back to 1.15/Area 3.
- **Pattern mapping:** built on sorting (the enabler) + a linear sweep; rooms/max-overlap use a
  **heap** (11.12); "max non-overlapping" is a classic **greedy** (11.24).
[↑ Back to top](#contents)

---

<a id="11.8"></a>
## 11.8 — "Detect a cycle, or find the middle, in one pass with no extra memory" → fast & slow pointers

### The situation

*Does a linked list have a cycle?* (a node's `next` eventually points back into the list,
creating an infinite loop). Or *find the middle node in one pass.* The obvious cycle check
stores every node seen:

```python
def has_cycle(head):
    seen = set()
    node = head
    while node:
        if node in seen: return True     # revisited -> cycle
        seen.add(node); node = node.next
    return False                          # O(n) time but O(n) SPACE
```

It works, but uses O(n) extra memory to remember every node — and for "find the middle" you'd
otherwise need two passes (count length, then walk halfway).

### What's really going on

When traversing a **linked list** (or any "follow the next pointer" sequence), two pointers
moving at **different speeds** reveal structure with **O(1) space**. The classic is **Floyd's
cycle detection** ("tortoise and hare"): a `slow` pointer moves one step, a `fast` pointer two
steps. If there's a cycle, `fast` eventually laps `slow` and they **meet**; if `fast` reaches
the end (`None`), there's no cycle. Same idea finds the **middle**: when `fast` reaches the
end, `slow` is at the midpoint (it went half as far).

The insight: relative speed encodes position. Because `fast` gains one step on `slow` each
iteration, in a cycle of length `c` they must coincide within `c` steps — so you detect a loop
without remembering any nodes. This is the linked-list cousin of two pointers (11.2), but the
pointers move *the same direction at different speeds* rather than converging.

> **Trigger:** linked-list (or "follow next") problems — **detect a cycle**, find the **middle**,
> find the **cycle start**, or "nth from the end" — especially when O(1) space is wanted.
> **Pattern:** **fast & slow** pointers (hare moves 2, tortoise moves 1). Cycle ⇒ they meet;
> no cycle ⇒ fast hits the end. Middle ⇒ slow is halfway when fast finishes. **Result:** O(n)
> time, **O(1)** space (vs the O(n)-space "store seen nodes" approach).

### The move

Advance `slow` by 1 and `fast` by 2; their meeting (or `fast` hitting the end) answers the
question:

```python
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next            # tortoise: 1 step
        fast = fast.next.next       # hare: 2 steps
        if slow is fast:            # they met -> a cycle exists
            return True
    return False                    # fast reached the end -> no cycle
```

### Why it works

Each iteration, `fast` gains exactly one step on `slow`. If the list ends, `fast` (moving
twice as fast) reaches `None` first — proving no cycle, in ≤ n/2 iterations. If there *is* a
cycle, once both pointers are inside the loop the gap between them shrinks by one each step, so
`fast` is guaranteed to land on `slow` within one loop-length — they **meet**, with no need to
record any nodes (hence O(1) space). The identity check is `is` (1.9) — comparing node
*identity*, not value, since values can repeat. The same speed difference places `slow` at the
**middle** when `fast` finishes (it travelled half as far), and a neat follow-up (reset one
pointer to head after they meet, then advance both by 1) finds the **cycle's start** — a
classic result of the step arithmetic.

### The code, every line explained

```python
# --- cycle detection (Floyd's tortoise & hare), O(1) space --------------
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:        # need fast AND fast.next to take 2 steps safely
        slow = slow.next             # 1 step
        fast = fast.next.next        # 2 steps
        if slow is fast:             # identity (1.9), not ==; they occupy the SAME node
            return True
    return False                     # fast fell off the end -> acyclic

# --- find the MIDDLE node in one pass -----------------------------------
def middle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next; fast = fast.next.next
    return slow                      # fast at end -> slow at midpoint (even len -> 2nd middle)

# --- find the START of the cycle (Floyd, phase 2) -----------------------
def cycle_start(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next; fast = fast.next.next
        if slow is fast:             # meeting point inside the loop
            p = head
            while p is not slow:     # reset one to head; advance BOTH by 1; they meet at start
                p = p.next; slow = slow.next
            return p                 # the node where the cycle begins
    return None                      # no cycle

# --- nth node from the END: a fixed GAP between two pointers ------------
def nth_from_end(head, n):
    fast = slow = head
    for _ in range(n): fast = fast.next      # advance fast n steps ahead -> gap of n
    while fast:                               # move both until fast hits the end
        fast = fast.next; slow = slow.next
    return slow                               # slow is now n from the end (one pass)

# --- also works beyond linked lists: "happy number" -------------------
# iterate x -> sum of squares of digits; a fast/slow run detects the cycle (loops forever)
# vs reaching 1 (no cycle) — the "follow a deterministic next-step" structure is the same.

# --- the trap -----------------------------------------------------------
# guard `while fast and fast.next:` — calling fast.next.next when fast.next is None CRASHES
# (AttributeError on None, 1.9/1.17). The two-condition guard is essential.
```

### Impact

- **O(1) space cycle detection:** finds loops without recording every node — the memory win
  over the hash-set approach, which matters on long lists or constrained memory.
- **One-pass middle / nth-from-end:** the speed/gap trick answers positional questions in a
  single traversal, no length-counting pre-pass.
- **Elegant cycle-start result:** the reset-and-walk phase locates where a loop begins with
  pure pointer arithmetic — a frequently-tested, memorable technique.

### Pros & cons / when NOT to

**Reach for fast & slow pointers when:** traversing a linked list (or any deterministic
"follow next" sequence) for cycle detection, the middle, the cycle's start, or a fixed offset
from the end — especially when O(1) space is required.

**Watch out / when NOT to:**
- **Guard the fast pointer** — `while fast and fast.next:` before `fast.next.next`, or you
  dereference `None` and crash (1.9/1.17). The two-part condition is mandatory.
- **Compare identity, not value** (`is`, 1.9) — nodes can hold equal values; a cycle means the
  *same node object* is revisited.
- **If O(n) space is fine and clarity matters, a `set` of seen nodes is simpler** — Floyd's is
  for the O(1)-space requirement or when it's the expected interview answer; don't reach for the
  trickier version when the simple one suffices.
- **Even vs odd length changes "the middle"** — for even length, `fast and fast.next` lands
  `slow` on the *second* middle; adjust the loop condition if you need the first.
- **It's specific to "follow a single deterministic next"** — it doesn't generalise to trees/
  graphs with branching (those need BFS/DFS + a visited set, 11.13/11.16).

### Where this shows up

- **Interview classics:** Linked List Cycle I/II, Middle of the Linked List, Remove Nth Node
  From End, Happy Number, Find the Duplicate Number (Floyd on the index-mapping "linked list"),
  Palindrome Linked List (find middle + reverse, 11.9).
- **Real work (the crossover):** detecting cycles in "follow the pointer/reference" structures
  (linked data, parent chains, state machines that might loop), and any "is this iteration
  going to terminate or loop forever?" check — the cycle-detection instinct.
- **Pattern mapping:** the linked-list sibling of two pointers (11.2) — same-direction, different
  speeds; contrasts with hashing (11.1, the O(n)-space alternative) and underpins several
  linked-list manipulations (11.9).
[↑ Back to top](#contents)

---

<a id="11.9"></a>
## 11.9 — "Reverse or reorder a linked list in place" → pointer manipulation

### The situation

*Reverse a singly linked list.* Each node knows only its `next`; you must flip every arrow so
the list runs backwards — ideally in place, O(1) extra space:

```python
# 1 -> 2 -> 3 -> None      becomes      3 -> 2 -> 1 -> None
# the tempting "just use a list" approach copies values out and back -> O(n) space, and many
# interview variants forbid it / want true pointer surgery
```

The trap is losing the rest of the list the moment you overwrite a `next` pointer — flip
`1.next` to `None` and you've orphaned `2 -> 3`.

### What's really going on

Linked-list problems are about **carefully rewiring `next` pointers**, and the universal
technique is to walk the list maintaining a few pointers — typically `prev`, `curr`, and a
saved `next` — rewiring one node at a time. The critical discipline: **save the next pointer
*before* you overwrite it**, or you lose access to the remainder of the list.

For reversal: keep `prev` (the part already reversed) and `curr` (the node to process). Each
step: remember `curr.next`, point `curr.next` back to `prev`, then advance both forward. When
`curr` falls off the end, `prev` is the new head. The same "track a few pointers, save-before-
overwrite" mechanic handles reorder, swap-in-pairs, merge two lists, and rotate — they're all
pointer surgery.

A **dummy/sentinel head** node often simplifies these: a fake node before the real head means
you never special-case "modifying the head," because there's always a node before the one you
care about.

> **Trigger:** reverse / reorder / merge / swap / rotate a **linked list**, in place.
> **Pattern:** walk with a few pointers (`prev`, `curr`, saved `next`), rewiring one `next` per
> step — **always save `next` before overwriting it**. A **dummy head** node avoids head-edge
> special cases. **Result:** O(n) time, **O(1)** space. The whole skill is not losing the rest
> of the list while you relink.

### The move

Walk with `prev`/`curr`, saving `next` before flipping each pointer:

```python
def reverse(head):
    prev, curr = None, head
    while curr:
        nxt = curr.next        # 1. SAVE next before we overwrite it
        curr.next = prev       # 2. reverse this node's pointer
        prev = curr            # 3. advance prev
        curr = nxt             # 4. advance curr (using the saved next)
    return prev                # prev is the new head
```

### Why it works

The four-step dance is the whole trick. Step 1 saves `curr.next` into `nxt` *before* step 2
overwrites `curr.next` — without that save, flipping the pointer would orphan the rest of the
list (the bug everyone hits first). Step 2 reverses the current arrow to point at the
already-reversed portion (`prev`). Steps 3–4 slide both pointers forward, using the saved
`nxt` to keep traversing. Each node is visited once and rewired in O(1), so it's **O(n) time,
O(1) space** — no copying values to an array. When `curr` becomes `None`, every arrow has been
flipped and `prev` points at what was the last node — the new head. The same save-before-
overwrite discipline (plus a dummy head to dodge head edge cases) generalises to merging,
swapping pairs, and reordering.

### The code, every line explained

```python
# --- reverse a linked list (the template move) --------------------------
def reverse(head):
    prev, curr = None, head
    while curr:
        nxt = curr.next        # SAVE — lose this and you lose the rest of the list
        curr.next = prev       # rewire: point backward
        prev, curr = curr, nxt # advance both (tuple swap, 1.6)
    return prev                # new head

# --- DUMMY HEAD: avoid special-casing the head --------------------------
def remove_value(head, val):
    dummy = ListNode(0, head)            # fake node BEFORE head -> head is never a special case
    prev = dummy
    while prev.next:
        if prev.next.val == val:
            prev.next = prev.next.next   # unlink — works uniformly even if it's the head
        else:
            prev = prev.next
    return dummy.next                    # real head (may have changed) — why dummy helps

# --- merge two SORTED lists (pointer surgery + two pointers, 11.2) ------
def merge_two(a, b):
    dummy = ListNode(0); tail = dummy
    while a and b:
        if a.val <= b.val: tail.next = a; a = a.next   # splice the smaller node
        else:              tail.next = b; b = b.next
        tail = tail.next
    tail.next = a or b                   # attach whatever remains (one list is exhausted)
    return dummy.next

# --- swap nodes in PAIRS: relink, don't swap values ---------------------
def swap_pairs(head):
    dummy = ListNode(0, head); prev = dummy
    while prev.next and prev.next.next:
        a, b = prev.next, prev.next.next
        a.next = b.next; b.next = a; prev.next = b   # rewire prev -> b -> a -> rest
        prev = a
    return dummy.next

# --- reorder = compose smaller moves (11.8 + reverse + merge) -----------
# "reorder L0->L1->...->Ln to L0->Ln->L1->Ln-1...": find MIDDLE (11.8 slow/fast),
# REVERSE the second half (above), then MERGE the two halves alternately. Composition!

# --- the cardinal rule & a debugging tip --------------------------------
# ALWAYS save `next` before overwriting it. When stuck, DRAW the nodes and arrows on paper
# and trace pointer by pointer — linked-list bugs are almost always a lost/dangling pointer.
```

### Impact

- **In-place, O(1) space:** rewiring pointers avoids copying the list's values to an array,
  the memory win and the usual interview requirement.
- **One reusable discipline:** "track a few pointers, save-before-overwrite, use a dummy head"
  solves reverse, merge, swap-pairs, remove, and rotate — and composes into bigger operations
  (reorder = middle + reverse + merge).
- **Builds pointer fluency:** the careful relinking is foundational for trees/graphs too, where
  you manipulate `left`/`right`/neighbour references.

### Pros & cons / when NOT to

**Reach for pointer manipulation when:** you must restructure a **linked list** in place —
reverse, merge, swap, reorder, rotate, remove — especially with an O(1)-space constraint.

**Watch out / when NOT to:**
- **Save `next` before overwriting it** — the single most common linked-list bug is orphaning
  the remainder of the list by flipping a pointer too early. This rule is non-negotiable.
- **Use a dummy head** whenever the head node might change or be removed — it eliminates the
  fiddly "is this the head?" special case and a class of null-pointer bugs.
- **Guard for `None`** at every dereference (`while curr`, `prev.next and prev.next.next`,
  1.9/1.17) — linked lists end in `None`, and stepping past it crashes.
- **Relink nodes, don't swap values, when the problem is about node structure** — value-
  swapping is sometimes a shortcut but defeats problems that test pointer manipulation (and
  fails when nodes carry more than a value).
- **If recursion is clearer and depth is bounded, it's fine** — reverse/merge have neat
  recursive forms, but mind the O(n) call-stack space (and recursion limits) on long lists vs
  the O(1) iterative version.
- **Draw it.** When the rewiring gets confusing, sketch nodes and arrows and trace each step —
  far faster than guessing.

### Where this shows up

- **Interview classics:** Reverse Linked List (I/II), Merge Two/K Sorted Lists, Swap Nodes in
  Pairs, Reorder List, Rotate List, Remove Nth From End, Odd-Even Linked List, Add Two Numbers.
- **Real work (the crossover):** maintaining linked structures — LRU cache eviction lists,
  free-lists, adjacency lists, undo/redo chains — anywhere you splice/unsplice nodes; and the
  merge step here is the same as merging sorted streams (11.2 / `heapq.merge`, Area 3).
- **Pattern mapping:** uses two/fast-slow pointers (11.2/11.8) to locate split points; composes
  primitives (reverse + merge) into bigger operations; the relinking discipline carries over to
  tree/graph pointer work (11.13–11.16).
[↑ Back to top](#contents)

---

<a id="11.10"></a>
## 11.10 — "For each element, find the next greater/smaller one" → monotonic stack

### The situation

*For each day's temperature, how many days until a warmer day?* (Next Greater Element.) The
brute force scans forward from each element:

```python
def days_until_warmer(temps):
    res = [0] * len(temps)
    for i in range(len(temps)):
        for j in range(i + 1, len(temps)):     # scan forward for the next warmer day
            if temps[j] > temps[i]:
                res[i] = j - i; break
    return res                                  # O(n²) — re-scans for every element
```

Each element re-scans the rest of the array — O(n²). But there's structure: once you've passed
an element looking for something bigger, you can *remember* it efficiently instead of
re-scanning.

### What's really going on

"For each element, find the **next** (or **previous**) element that is **greater/smaller**"
is the signature of a **monotonic stack** — a stack kept in sorted (increasing or decreasing)
order. You walk the array once, pushing indices; before pushing the current element, you **pop**
everything that the current element "resolves." For *next greater*: maintain a decreasing
stack; when the current value is bigger than the value at the top, it *is* the next-greater for
that top — pop and record it. Each element is pushed and popped **at most once**, so the whole
thing is **O(n)** despite the inner `while`.

The insight: the stack holds "elements still waiting for their answer," kept monotonic so the
current element resolves a whole run of them in amortised O(1). It turns the O(n²) "look ahead
for each" into a single linear pass.

> **Trigger:** "for each element, find the **next/previous greater/smaller** element" (or its
> distance/index), and span/area problems built on that — daily temperatures, stock span,
> largest rectangle in a histogram. **Pattern:** a **monotonic stack** of indices; pop elements
> the current one resolves before pushing it. **Result:** **O(n)** (each element pushed/popped
> once), vs the O(n²) look-ahead. Decreasing stack → next greater; increasing → next smaller.

### The move

Keep a stack of indices in monotonic order; before pushing the current index, pop everything it
resolves:

```python
def days_until_warmer(temps):
    res = [0] * len(temps)
    stack = []                               # indices of days still WAITING for a warmer day
    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:    # current day is warmer than the top
            j = stack.pop()                      # -> resolves day j
            res[j] = i - j                       # distance to the warmer day
        stack.append(i)
    return res                               # days never resolved stay 0
```

### Why it works

The stack holds indices of days that haven't yet found a warmer day, kept so their temperatures
are **decreasing** from bottom to top. When a warmer day `i` arrives, it is the answer for every
waiting day on top whose temperature is lower — so you pop them and record `i - j`. Those days
are now resolved and never reconsidered. Each index is pushed exactly once and popped at most
once, so even with the inner `while`, the *total* number of operations across the whole loop is
≤ 2n — **amortised O(n)**, not O(n²). The monotonic invariant is what guarantees the top is
always the nearest unresolved candidate, so the current element resolves a contiguous run of
them cheaply.

### The code, every line explained

```python
# --- NEXT GREATER (distance): daily temperatures ------------------------
def days_until_warmer(temps):
    res = [0] * len(temps)
    stack = []                               # decreasing stack of INDICES (store index, not value)
    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:    # t resolves everything smaller on top
            j = stack.pop()
            res[j] = i - j                       # i is the next-warmer day for j
        stack.append(i)                          # i now waits for ITS warmer day
    return res

# --- NEXT GREATER ELEMENT (value, with wraparound via %) ----------------
def next_greater(nums):
    n = len(nums); res = [-1] * n; stack = []
    for i in range(2 * n):                       # 2n pass handles circular arrays
        x = nums[i % n]
        while stack and nums[stack[-1]] < x:
            res[stack.pop()] = x                 # x is the next greater for the popped index
        if i < n: stack.append(i)
    return res

# --- PREVIOUS smaller? flip the comparison & read the stack -------------
# increasing stack -> the element BELOW the current top is its "previous smaller".
# next SMALLER -> use `>` in the while (pop bigger elements). The comparison direction
# selects greater/smaller; the side you read (push vs pop time) selects next vs previous.

# --- LARGEST RECTANGLE IN HISTOGRAM (the hard, classic application) -----
def largest_rectangle(heights):
    heights.append(0)                            # sentinel forces all bars to flush at the end
    stack = []; best = 0                         # increasing stack of indices
    for i, h in enumerate(heights):
        while stack and heights[stack[-1]] > h:  # bar h ends the rectangle of taller bars
            height = heights[stack.pop()]
            left = stack[-1] if stack else -1    # width spans to the previous smaller bar
            best = max(best, height * (i - left - 1))
        stack.append(i)
    heights.pop()                                # restore input
    return best

# --- the giveaway -------------------------------------------------------
# "next/previous greater/smaller", "how far until a bigger value", "span", "largest rectangle
# / max area under bars" -> monotonic stack. Store INDICES (so you can compute distances).
```

### Impact

- **O(n²) → O(n):** the amortised single push/pop per element removes the per-element
  look-ahead — the decisive speed-up for next-greater/smaller and span/area problems.
- **One structure, many problems:** the same monotonic-stack skeleton (flip the comparison,
  choose push-time vs pop-time reads) solves next/previous greater/smaller, stock span, and
  histogram area.
- **Indices unlock distances/widths:** storing indices (not values) lets you compute "how many
  days" or rectangle widths directly.

### Pros & cons / when NOT to

**Reach for a monotonic stack when:** each element needs its **next/previous greater/smaller**
neighbour (or the distance to it), or for span/area problems (histogram rectangle, trapping
water can also be done this way) where that relationship is the core.

**Watch out / when NOT to:**
- **Store indices, not values**, when you need distances or widths — `i - j` and rectangle
  widths require positions; value-only stacks lose that.
- **Get the comparison direction right** — `<` vs `>` in the `while` selects greater vs smaller,
  and *when* you read the stack (at push vs at pop) selects next vs previous. Mixing these is
  the main bug; reason through one concrete example.
- **It's amortised O(n), and that can be non-obvious** — the inner `while` looks like it could
  be O(n²), but the push-once/pop-once accounting makes it linear; don't "optimise" it away or
  add a redundant scan.
- **Use a sentinel to flush** — appending a 0 (histogram) or doing a 2n pass (circular) ensures
  elements left on the stack get resolved; forgetting this leaves answers unset.
- **Not for "any larger element anywhere"** — it finds the *nearest* next/previous; "is there a
  larger element at all" is a simple max/scan, and "kth larger" is a heap (11.12).

### Where this shows up

- **Interview classics:** Daily Temperatures, Next Greater Element I/II, Largest Rectangle in
  Histogram, Maximal Rectangle, Trapping Rain Water, Stock Span, Remove K Digits / Remove
  Duplicate Letters (monotonic stack for lexicographically smallest result).
- **Real work (the crossover):** "time/distance until the next higher value" over a series
  (next price above current, next spike), and span calculations in time-series/finance — the
  same next-greater logic; stacks themselves are everywhere (parsing, undo, call frames).
- **Pattern mapping:** a specialised use of a **stack**; complements the **monotonic deque**
  (11.11) for sliding-window max/min (a window, not "next greater"); contrasts with heaps
  (11.12) for "kth/extreme overall" rather than "nearest greater".
[↑ Back to top](#contents)

---

<a id="11.11"></a>
## 11.11 — "Maximum (or minimum) of every sliding window" → monotonic deque

### The situation

*Given an array and a window size `k`, return the maximum of each window as it slides.* The
brute force recomputes the max of every window:

```python
def max_sliding_window(nums, k):
    res = []
    for i in range(len(nums) - k + 1):
        res.append(max(nums[i:i+k]))     # O(k) per window x n windows -> O(n·k)
    return res
```

Recomputing `max` over each window is O(n·k). A sliding window (11.3) handles sums by add/drop,
but **max can't be maintained that way** — when the current max *leaves* the window, you don't
know the new max without rescanning.

### What's really going on

Maintaining the **max (or min) of a sliding window** in O(1) amortised per step needs a
**monotonic deque** — a double-ended queue (`collections.deque`) holding indices in decreasing
(for max) order of value. The front always holds the index of the current window's maximum. Two
operations per step keep it valid: (1) **pop from the back** any indices whose values are ≤ the
incoming element (they can never be the max while it's around — the monotonic-stack idea, 11.10,
applied to a window), and (2) **pop from the front** the index if it has slid out of the window.

The deque thus holds "candidates that could still be the window max, in decreasing order," so
the answer is always at the front in O(1). Because each index is added once and removed once,
the whole sweep is **O(n)** — the right tool that the plain sliding-window-sum trick (11.3)
can't provide for max/min.

> **Trigger:** "**maximum/minimum of every window** of size k" (or a variable window's
> extreme) — where a running sum-style update (11.3) fails because a leaving element might be
> the extreme. **Pattern:** a **monotonic deque of indices**: pop smaller (for max) values from
> the back before adding; pop out-of-window indices from the front; the front is the window
> extreme. **Result:** **O(n)**, vs O(n·k) recomputation.

### The move

Keep a decreasing deque of indices; evict out-of-window from the front and smaller values from
the back; the front is the window max:

```python
from collections import deque
def max_sliding_window(nums, k):
    dq, res = deque(), []                 # dq holds INDICES, values decreasing front->back
    for i, x in enumerate(nums):
        while dq and dq[0] <= i - k:      # front index slid out of the window
            dq.popleft()
        while dq and nums[dq[-1]] <= x:   # back values <= x can never be max again -> drop
            dq.pop()
        dq.append(i)
        if i >= k - 1:                     # window is full -> record the front (the max)
            res.append(nums[dq[0]])
    return res
```

### Why it works

Two evictions keep the deque exactly equal to "indices that could still be the max of the
current window, in decreasing value order." The back-eviction (`nums[dq[-1]] <= x`) drops any
element no larger than the incoming one: while `x` is in the window, those can never be the max,
so they're useless — this is the monotonic idea (11.10) confined to a window. The front-eviction
(`dq[0] <= i - k`) discards the max once it has slid out of range. Because the deque stays
decreasing, `dq[0]` is always the index of the current window's maximum — readable in O(1). Each
index is appended once and popped once across the whole array, so it's **O(n)** total. This is
precisely the piece the add/drop sliding-window-sum (11.3) can't do: sums are reversible, but
"which is the max after the max leaves?" requires remembering the runner-up candidates — which
the deque does.

### The code, every line explained

```python
from collections import deque

# --- sliding window MAXIMUM ---------------------------------------------
def max_sliding_window(nums, k):
    dq = deque()                          # indices; nums[dq] strictly... non-increasing
    res = []
    for i, x in enumerate(nums):
        if dq and dq[0] <= i - k:         # the index at the front is now OUTSIDE the window
            dq.popleft()                  # (use `while`/`if`: at most one can expire per step)
        while dq and nums[dq[-1]] <= x:   # maintain DECREASING: drop smaller-or-equal tails
            dq.pop()
        dq.append(i)                      # x is a new candidate
        if i >= k - 1:                    # first full window starts at index k-1
            res.append(nums[dq[0]])       # front = current window's MAX, O(1)
    return res

# --- sliding window MINIMUM: flip the comparison ------------------------
# while dq and nums[dq[-1]] >= x: dq.pop()   # INCREASING deque -> front is the min

# --- why store INDICES, not values --------------------------------------
# you need the index to know when an element EXPIRES from the window (dq[0] <= i - k).
# a value-only deque can't tell you whether the front has slid out of range.

# --- deque vs heap for window max (11.12) -------------------------------
# a max-HEAP also gives window max, but removing the element that LEFT the window is O(n)
# or needs lazy deletion (pop stale entries when seen at top). The monotonic deque is the
# clean O(n) tool BECAUSE the window is contiguous and indices expire in order.

# --- the giveaway -------------------------------------------------------
# "max/min of EVERY window of size k", "longest window where max-min <= limit" (two deques),
# "shortest subarray with sum >= k" (monotonic deque on prefix sums) -> monotonic deque.
```

### Impact

- **O(n·k) → O(n):** maintaining candidates in a deque removes the per-window rescan — the
  decisive win for window-extreme problems on large arrays.
- **Does what sliding-window-sum can't:** provides O(1) window max/min, where add/drop (11.3)
  only works for reversible aggregates like sum/count.
- **Reusable for related problems:** two deques (one increasing, one decreasing) track window
  max *and* min together (e.g. "longest window with max−min ≤ limit").

### Pros & cons / when NOT to

**Reach for a monotonic deque when:** you need the **max or min of every sliding window** (fixed
or variable), or a window constraint involving the window's extreme (max−min ≤ limit).

**Watch out / when NOT to:**
- **Store indices, not values** — you must detect expiry (`dq[0] <= i - k`), which needs
  positions; a value deque can't tell when the front leaves the window.
- **Two evictions, correct order** — front-evict the expired index, back-evict smaller/equal
  values *before* appending. Forgetting either (or flipping the comparison) breaks it; min vs
  max is just `>=` vs `<=`.
- **For window max/min specifically, prefer the deque over a heap** (11.12) — a heap gives the
  extreme but removing the *expired* element is O(n) or needs lazy deletion; the deque is the
  clean O(n) fit because window elements expire in index order.
- **It's for contiguous windows** — for "kth largest in a stream" or "top-k overall" (not a
  sliding window), use a heap (11.12); for "next greater element" (not a window), use a
  monotonic stack (11.10).
- **Record only once the window is full** (`i >= k-1`) — emitting earlier yields answers for
  partial windows.

### Where this shows up

- **Interview classics:** Sliding Window Maximum, Shortest Subarray with Sum at Least K
  (monotonic deque over prefix sums), Longest Continuous Subarray with Absolute Diff ≤ Limit
  (two deques), Constrained Subsequence Sum (deque + DP, 11.21).
- **Real work (the crossover):** rolling max/min over a time series (peak load in the last N
  minutes, rolling high/low in finance), and streaming window statistics where you need the
  extreme, not just the sum — the operational cousin of the sliding window (11.3).
- **Pattern mapping:** the windowed sibling of the **monotonic stack** (11.10), built on a
  **deque** (`collections.deque`, Area 3); complements sliding window (11.3, sums) and heaps
  (11.12, top-k / non-windowed extremes).
[↑ Back to top](#contents)

---

<a id="11.12"></a>
## 11.12 — "Kth largest, top-K, or merge K sorted things" → heaps

### The situation

*Find the Kth largest element in an array*, or *the K most frequent*, or *merge K sorted
lists*. The naive approach sorts everything:

```python
def kth_largest(nums, k):
    return sorted(nums, reverse=True)[k-1]    # O(n log n) to sort ALL n, to read ONE element
```

Sorting the whole array is O(n log n) when you only need the top K — and for a *stream* (data
arriving over time) you can't sort "everything" at all, because it doesn't all exist yet.

### What's really going on

When you need the **K smallest/largest**, the **Kth** element, **top-K by some score**, or to
repeatedly pull the **current extreme**, the tool is a **heap** (priority queue) —
`heapq`, the same structure from Area 3 (3.17). A heap keeps its smallest element instantly
accessible at the front and supports push/pop in O(log size). The key trick for top-K: maintain
a **size-K heap**, not a heap of everything — so you use O(K) memory and O(n log K) time, which
beats sorting (O(n log n)) and works on unbounded streams.

For "K largest," keep a **min-heap of size K**: the smallest of your current top-K sits at the
front, so when a bigger element arrives you pop that smallest and push the newcomer — the heap
always holds the K largest seen so far. For "merge K sorted lists," a heap of the K list-heads
always surfaces the global minimum next. The heap is the right structure whenever "what's the
next smallest/largest among many?" is asked **repeatedly**.

> **Trigger:** "**Kth** largest/smallest," "**top-K**," "**K most frequent**," "**merge K**
> sorted lists," "repeatedly get/remove the min/max," or a **stream** where you can't sort
> everything. **Pattern:** a **heap** (`heapq`); for top-K keep a **size-K** heap. **Result:**
> O(n log K) and O(K) space (beats O(n log n) full sort); works on streams. (Area 3's 3.17 is
> the data-wrangling face of this.)

### The move

Keep a size-K min-heap; push each element and pop the smallest whenever the heap exceeds K — the
front is the Kth largest:

```python
import heapq
def kth_largest(nums, k):
    heap = []                          # min-heap; will hold the K LARGEST seen so far
    for x in nums:
        heapq.heappush(heap, x)
        if len(heap) > k:
            heapq.heappop(heap)        # drop the smallest -> heap keeps the top-K
    return heap[0]                     # the smallest of the top-K = the Kth largest
```

### Why it works

`heapq` is a **min-heap**: `heap[0]` is always the smallest element, and push/pop are O(log
size). By capping the heap at size K, after processing all `n` elements it contains exactly the
K largest — and its front (`heap[0]`), the smallest of those K, is by definition the Kth
largest. Each element costs one O(log K) push (and maybe a pop), so total time is **O(n log K)**
with **O(K) space** — better than sorting all n (O(n log n), O(n) space) and, crucially, it
processes elements one at a time so it works on a **stream** that never fully materialises. For
merging K sorted lists, a heap of the current heads always yields the global minimum next in
O(log K), giving O(N log K) to merge N total elements. The heap is the answer whenever you
repeatedly need "the next extreme among many."

### The code, every line explained

```python
import heapq

# --- Kth largest: size-K MIN-heap ---------------------------------------
def kth_largest(nums, k):
    heap = []
    for x in nums:
        heapq.heappush(heap, x)        # O(log k)
        if len(heap) > k:
            heapq.heappop(heap)        # evict the smallest -> only the top-K survive
    return heap[0]                     # smallest of the K largest = Kth largest
# (one-shot shortcut when not streaming: heapq.nlargest(k, nums)[-1] — 3.17)

# --- top-K FREQUENT: Counter (11.1/3.14) + heap -------------------------
from collections import Counter
def top_k_frequent(nums, k):
    counts = Counter(nums)
    return heapq.nlargest(k, counts.keys(), key=counts.get)   # K keys with the highest counts

# --- MERGE K sorted lists: heap of (value, which_list, index) -----------
def merge_k(lists):
    heap = [(lst[0], i, 0) for i, lst in enumerate(lists) if lst]   # seed with each head
    heapq.heapify(heap)                # O(K) to build
    out = []
    while heap:
        val, li, idx = heapq.heappop(heap)     # global min among the K heads
        out.append(val)
        if idx + 1 < len(lists[li]):           # push the next element from that list
            heapq.heappush(heap, (lists[li][idx+1], li, idx+1))
    return out                                 # O(N log K) total
# (heapq.merge(*lists) does this lazily for iterables — Area 3.)

# --- MAX-heap: negate values (heapq is min-only) ------------------------
heapq.heappush(heap, -x)               # push negatives...
largest = -heapq.heappop(heap)         # ...negate back on pop -> behaves as a max-heap

# --- tie-breaking: make entries comparable ------------------------------
# push tuples like (priority, tiebreak_id, item) so Python never compares the `item`
# objects (which may be unhashable/incomparable) when priorities tie. (3.17 noted this.)

# --- "median from a data stream": TWO heaps -----------------------------
# a max-heap of the lower half + a min-heap of the upper half, kept balanced -> the median
# is at the heap tops in O(log n) per insert. The classic two-heap design.

# --- the giveaway: K vs ordering ----------------------------------------
# need the FULL sorted order -> just sort. need TOP-K / Kth / repeated-extreme / a STREAM
# -> heap (size-K). need the NEAREST greater (not extreme) -> monotonic stack (11.10).
```

### Impact

- **O(n log n) → O(n log K):** a size-K heap reads the top-K without fully sorting — a real win
  when K ≪ n, and the only option for streams that don't fully exist in memory.
- **O(K) space on streams:** processes elements one at a time holding only K, so "top-K of a
  billion events" runs in bounded memory.
- **Repeated-extreme engine:** powers merge-K, priority scheduling, Dijkstra (11.18), and
  two-heap median — anywhere "give me the next smallest/largest" is asked over and over.

### Pros & cons / when NOT to

**Reach for a heap when:** you need Kth/top-K/K-most-frequent, to merge K sorted sources, the
running median, or to repeatedly extract the min/max (priority queue) — especially on streams.

**Watch out / when NOT to:**
- **If you need everything fully sorted, just sort** — a heap shines for top-K or repeated
  extraction, not for producing a complete ordering (that's O(n log n) either way, and `sorted`
  is simpler).
- **`heapq` is min-only** — for a max-heap, negate values (or use tuples with negated keys);
  forgetting to negate back on pop is a classic bug.
- **Make tuples comparable** — push `(priority, tiebreak, item)` so Python never has to compare
  the payload objects when priorities tie (they may be unorderable) — same caveat as 3.17.
- **For sliding-window max/min, prefer a monotonic deque (11.11)** — removing the *expired*
  element from a heap is O(n) or needs lazy deletion; the deque is the clean O(n) fit there.
- **Heap gives the extreme, not the *nearest* greater** — "next greater element" is a monotonic
  stack (11.10), not a heap.
- **Size-K vs full heap** — for top-K keep the heap at size K (O(n log K)); a heap of all n is
  O(n log n) and misses the point.

### Where this shows up

- **Interview classics:** Kth Largest Element (array & stream), Top K Frequent Elements, Merge K
  Sorted Lists, Find Median from Data Stream, K Closest Points to Origin, Task Scheduler,
  Reorganise String.
- **Real work (the crossover):** this *is* the `heapq` top-N / `heapq.merge` toolkit from Area 3
  (3.17) — "top N customers by revenue," "slowest K requests," merging sorted daily exports —
  and the priority-queue behind schedulers and worker pools (Area 5/6).
- **Pattern mapping:** the priority-queue backbone of **Dijkstra** (11.18) and many greedy
  algorithms (11.24); contrasts with monotonic stack/deque (11.10/11.11) for *nearest*/*window*
  extremes rather than *global* top-K.
[↑ Back to top](#contents)

---

<a id="11.13"></a>
## 11.13 — "Visit every node in a tree" → depth-first search (DFS)

### The situation

*Compute the maximum depth of a binary tree*, or *sum all node values*, or *check if two trees
are identical.* You have a tree — nodes with `left`/`right` children — and need to process
every node:

```python
# tree:        1
#             / \
#            2   3
#           / \
#          4   5
# how do you systematically visit 1,2,3,4,5 — and combine results from children up to the root?
```

There's no array to loop over; the structure branches, and each node's answer often depends on
its children's answers.

### What's really going on

A **tree** is a recursive structure — each node has subtrees that are themselves trees — so the
natural way to process it is **recursion**, and the natural traversal is **depth-first search
(DFS)**: go as deep as possible down one branch before backtracking. DFS *is* recursion applied
to a tree: handle the current node, recurse into each child, combine. The recursion's **base
case** is the empty subtree (`None`); the **recursive case** combines results from `left` and
`right`.

The three DFS *orders* differ only in **when you process the node relative to its children**:
**pre-order** (node, then children), **in-order** (left, node, right — yields a BST's values
sorted, 11.15), **post-order** (children, then node — needed when a node's result depends on its
children, like height or subtree sums). Choosing the order is the main design decision; the
skeleton is always "base case → recurse children → combine."

> **Trigger:** process **every node of a tree** / compute something over a tree (depth, sum,
> path, validate, compare) — anything where a node's answer combines its children's.
> **Pattern:** **DFS via recursion** — base case `None`, recurse left & right, combine.
> Order: **pre** (top-down), **in** (sorted for BSTs, 11.15), **post** (bottom-up, when you need
> children's results first). **Result:** O(n) time, O(h) stack space (h = height).

### The move

Recurse: handle the empty base case, recurse into both children, combine their results:

```python
def max_depth(root):
    if not root:                       # base case: empty subtree has depth 0
        return 0
    return 1 + max(max_depth(root.left),     # recurse children, combine (post-order:
                   max_depth(root.right))    # use children's results, then add this node)
```

### Why it works

The recursion mirrors the tree's own structure: `max_depth` of a node is "1 + the deeper of its
two subtrees' depths," and each subtree is solved by the *same* function — the definition of a
recursive solution (11.28). The base case `if not root: return 0` stops the recursion at empty
subtrees and gives the combine step concrete numbers to work with; without it the recursion
never terminates. This is **post-order**: the node's answer is computed *after* its children's
(you need both child depths before you can take their max), which is exactly when post-order is
the right choice. Every node is visited once → **O(n)** time; the call stack goes as deep as the
tree → **O(h)** space (O(log n) for balanced, O(n) for a degenerate/skewed tree). Swap the order
of "process node" vs "recurse children" and you get pre/in/post-order for different needs.

### The code, every line explained

```python
# --- the DFS skeleton (memorise this shape) -----------------------------
def dfs(node):
    if not node:            # BASE CASE: empty subtree -> stop (prevents infinite recursion)
        return ...          # identity value (0 for sums/depth, True for "all valid", etc.)
    left  = dfs(node.left)  # recurse into children
    right = dfs(node.right)
    return combine(node.val, left, right)   # combine — WHERE this happens sets the "order"

# --- post-order (bottom-up): max depth, subtree sum ---------------------
def max_depth(root):
    if not root: return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))

# --- in-order on a BST yields SORTED values (11.15) ---------------------
def inorder(root, out):
    if not root: return
    inorder(root.left, out)     # left subtree first...
    out.append(root.val)        # ...then THIS node (so values come out ascending in a BST)
    inorder(root.right, out)    # ...then right subtree

# --- pre-order (top-down): pass info DOWN, e.g. validate a BST ----------
def is_bst(node, lo=float("-inf"), hi=float("inf")):
    if not node: return True
    if not (lo < node.val < hi): return False        # node must fit its allowed range
    return (is_bst(node.left, lo, node.val) and       # left: upper bound tightens to node.val
            is_bst(node.right, node.val, hi))         # right: lower bound tightens to node.val

# --- compare two trees (parallel recursion) -----------------------------
def same(p, q):
    if not p and not q: return True          # both empty -> identical here
    if not p or not q or p.val != q.val: return False   # one empty, or values differ
    return same(p.left, q.left) and same(p.right, q.right)

# --- ITERATIVE DFS with an explicit stack (avoid deep recursion, 11.28) -
def preorder_iter(root):
    if not root: return []
    out, stack = [], [root]
    while stack:
        node = stack.pop()                    # a STACK gives DFS (LIFO); a queue would give BFS
        out.append(node.val)
        if node.right: stack.append(node.right)   # push right first so left is processed first
        if node.left:  stack.append(node.left)
    return out

# --- the choices that matter --------------------------------------------
# base case = None (or leaf) — ALWAYS handle it first, or you recurse into None and crash.
# order: need children's results to compute the node's? -> POST. passing constraints down? ->
#        PRE. want sorted output from a BST? -> IN. picking the order IS the design.
```

### Impact

- **Natural fit for tree problems:** recursion mirrors the tree's structure, so the code is
  short and directly expresses "combine children's answers" — far cleaner than manual
  bookkeeping.
- **O(n), one visit per node:** every node processed exactly once; the only space is the O(h)
  call stack.
- **One skeleton, many problems:** depth, sum, validate, compare, path-sum, lowest-common-
  ancestor all instantiate "base case → recurse children → combine" with a different combine
  step and order.

### Pros & cons / when NOT to

**Reach for tree DFS when:** you must process every node, and a node's result depends on its
subtrees (depth, sums, validation, paths, comparisons) — i.e. most tree problems.

**Watch out / when NOT to:**
- **Always handle the base case first** (`if not node`) — recursing into `None` and accessing
  `.left`/`.val` crashes (1.9/1.17); the base case both terminates the recursion and seeds the
  combine step.
- **Pick the order deliberately** — post-order when the node needs children's results
  (height/sum), pre-order to pass constraints downward (BST validation), in-order for sorted BST
  output (11.15). The wrong order gives wrong answers.
- **Mind stack depth on skewed/deep trees** — recursion uses O(h) stack; a degenerate tree (h =
  n) can hit Python's recursion limit (~1000). Use the iterative explicit-stack form for very
  deep trees (11.28).
- **For shortest-path / level-by-level, use BFS (11.14), not DFS** — DFS finds *a* path and is
  natural for "process the whole subtree"; BFS finds the *shortest* in an unweighted graph and
  processes level by level.
- **Trees don't need a visited-set; general graphs do (11.16)** — a tree has no cycles, so plain
  recursion is safe; reusing tree-DFS on a graph without tracking visited nodes loops forever.

### Where this shows up

- **Interview classics:** Maximum Depth, Same Tree, Invert Binary Tree, Path Sum, Validate BST,
  Lowest Common Ancestor, Diameter of Binary Tree, Binary Tree Maximum Path Sum, Serialize/
  Deserialize.
- **Real work (the crossover):** walking any nested/recursive structure — nested JSON/config
  (the Area 3 "walk a tree" scenario), file-system directories, the DOM/AST, org charts — the
  same base-case-then-recurse-children skeleton.
- **Pattern mapping:** DFS is **recursion** (11.28) applied to a tree; the iterative form uses an
  explicit **stack**; contrasts with **BFS** (11.14, level-order via a queue); in-order on a BST
  ties to 11.15; generalises to graphs with a visited set (11.16).
[↑ Back to top](#contents)

---

<a id="11.14"></a>
## 11.14 — "Process a tree level by level" → breadth-first search (BFS)

### The situation

*Return a binary tree's values grouped by level* (level-order traversal), or *find the
right-side view*, or *the minimum depth.* DFS (11.13) goes deep down one branch first — but here
you need to process all nodes at depth 0, then all at depth 1, then depth 2:

```python
# tree:        1            want level-order: [[1], [2, 3], [4, 5]]
#             / \           DFS visits 1,2,4,5,3 — wrong order for "by level"
#            2   3
#           / \
#          4   5
```

DFS's depth-first order doesn't naturally give you "everything at this level together," and for
*shortest*-path questions DFS can wander down a long branch before finding a near answer.

### What's really going on

When you need to process a tree (or graph) **level by level**, or find the **shortest path /
minimum depth** in an unweighted structure, use **breadth-first search (BFS)**: visit nodes in
order of distance from the root — all of depth 0, then depth 1, and so on. BFS uses a **queue**
(FIFO): dequeue a node, enqueue its children. The FIFO order is what guarantees you finish a
whole level before the next begins.

The key trick for *grouping by level*: at the start of each loop iteration, record the current
queue size — that's exactly how many nodes are on this level — then process precisely that many
before moving on. Because BFS expands outward by distance, the **first time** it reaches a
target node it has done so by the **shortest** path — which is why BFS, not DFS, answers
"minimum depth" and "fewest steps" in unweighted graphs (11.16).

> **Trigger:** process a tree/graph **level by level**, "level-order," "right/left side view,"
> **minimum depth**, or **shortest path in an unweighted** structure. **Pattern:** **BFS with a
> queue** (`collections.deque`); snapshot the queue size to delimit each level. **Result:** O(n)
> time, O(width) space. First-reach = shortest path (unweighted). Contrast: **DFS uses a stack/
> recursion and goes deep; BFS uses a queue and goes wide.**

### The move

Use a queue; each iteration, process exactly the nodes currently on this level, enqueuing their
children for the next:

```python
from collections import deque
def level_order(root):
    if not root: return []
    out, q = [], deque([root])
    while q:
        level = []
        for _ in range(len(q)):        # SNAPSHOT size = nodes on THIS level
            node = q.popleft()
            level.append(node.val)
            if node.left:  q.append(node.left)    # children go to the NEXT level
            if node.right: q.append(node.right)
        out.append(level)
    return out
```

### Why it works

A FIFO queue dequeues nodes in the order they were enqueued, and since each node enqueues its
children, the queue always drains an entire level before any of the next level's nodes are
reached — that's why BFS proceeds strictly by distance from the root. The `for _ in
range(len(q))` snapshot captures how many nodes are on the current level *before* you start
adding the next level's children, so you process exactly this level, group its values, then move
on — giving the `[[1],[2,3],[4,5]]` grouping DFS can't produce naturally. Every node is enqueued
and dequeued once → **O(n)** time; the queue holds at most one level → **O(width)** space. And
because BFS reaches nodes in increasing distance order, the *first* time it touches a target,
that's the shortest path — the property that makes BFS the tool for minimum-depth and
fewest-steps problems (11.16).

### The code, every line explained

```python
from collections import deque

# --- level-order traversal (the template) -------------------------------
def level_order(root):
    if not root: return []
    out, q = [], deque([root])              # deque = O(1) popleft (a list's pop(0) is O(n)!)
    while q:
        level = []
        for _ in range(len(q)):             # len(q) NOW = exactly this level's node count
            node = q.popleft()              # FIFO: dequeue front
            level.append(node.val)
            if node.left:  q.append(node.left)    # enqueue children -> next level
            if node.right: q.append(node.right)
        out.append(level)                    # one list per level
    return out

# --- minimum depth: BFS stops at the FIRST leaf (shortest) --------------
def min_depth(root):
    if not root: return 0
    q = deque([(root, 1)])                   # (node, depth)
    while q:
        node, d = q.popleft()
        if not node.left and not node.right: # first leaf reached = MINIMUM depth (BFS!)
            return d
        if node.left:  q.append((node.left, d+1))
        if node.right: q.append((node.right, d+1))
# DFS would have to explore ALL branches to be sure of the min; BFS returns on first leaf.

# --- right-side view: last node of each level ---------------------------
def right_view(root):
    if not root: return []
    out, q = [], deque([root])
    while q:
        n = len(q)
        for i in range(n):
            node = q.popleft()
            if i == n - 1: out.append(node.val)   # last node in this level = rightmost
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
    return out

# --- DFS vs BFS, in one line each ---------------------------------------
# DFS: stack/recursion, goes DEEP, natural for "whole subtree" & path problems (11.13)
# BFS: queue, goes WIDE, natural for "by level" & SHORTEST path in unweighted graphs (11.16)

# --- the must-not bugs --------------------------------------------------
# - use collections.deque, NOT a list: list.pop(0) is O(n) -> BFS becomes O(n²)
# - SNAPSHOT len(q) before the inner loop; reading it as the queue grows mixes levels
```

### Impact

- **Level-grouped processing:** the size-snapshot gives exact per-level groups that DFS's
  depth-first order can't produce — directly answering level-order, side-views, and per-level
  aggregates.
- **Shortest path / minimum depth:** first-reach-is-shortest makes BFS the correct (and often
  much faster) tool for "fewest steps" in unweighted structures, where DFS would over-explore.
- **O(n) with bounded memory:** one visit per node, queue holds at most one level (O(width)).

### Pros & cons / when NOT to

**Reach for BFS when:** you need level-by-level processing, level-order/side-views, **minimum
depth**, or **shortest path in an unweighted** tree/graph (11.16).

**Watch out / when NOT to:**
- **Use `collections.deque`, never a list as a queue** — `list.pop(0)` is O(n), turning BFS into
  O(n²); `deque.popleft()` is O(1). This is the single most common BFS performance bug.
- **Snapshot `len(q)` before the inner loop** — to group by level you must capture the count
  *before* enqueuing children, or the loop reads a growing queue and merges levels.
- **BFS for shortest path only in UNWEIGHTED graphs** — with edge weights, first-reach isn't
  cheapest; use Dijkstra (11.18). BFS = uniform step cost.
- **For "explore the whole subtree," depth, sums, or path problems, DFS (11.13) is more
  natural** — BFS shines specifically for level/shortest questions.
- **In general graphs, track visited (11.16)** — trees are cycle-free so plain BFS is safe, but
  a graph BFS without a visited set revisits nodes and can loop.
- **Memory can spike on wide trees** — BFS holds a whole level; a very wide level is O(width)
  memory, which can exceed DFS's O(height) for bushy structures.

### Where this shows up

- **Interview classics:** Binary Tree Level-Order Traversal, Right Side View, Minimum Depth,
  Zigzag Level Order, Average of Levels, Connect Level-Order Siblings — and (as graph BFS, 11.16)
  shortest path in a grid/maze, word ladder, rotten oranges.
- **Real work (the crossover):** "nearest/fewest-hops" queries — shortest path in unweighted
  networks, crawling by distance from a seed, processing a hierarchy tier by tier — and BFS's
  queue is the same FIFO that coordinates producer/consumer pipelines (5.6).
- **Pattern mapping:** the breadth-first counterpart to **DFS** (11.13) — queue vs stack, wide vs
  deep; the foundation of unweighted **shortest path** and the basis for graph BFS (11.16) and
  (with a priority queue) Dijkstra (11.18).
[↑ Back to top](#contents)

---

<a id="11.15"></a>
## 11.15 — "Search or insert in an ordered tree" → BST operations

### The situation

*Search for a value in a binary search tree*, or *insert one*, or *find the kth smallest.* A
**binary search tree (BST)** is a binary tree with an ordering invariant — but you have to
*exploit* that invariant rather than treating it like any tree:

```python
# BST:        8           the invariant: for EVERY node,
#            / \          all values in its LEFT subtree  < node.val
#           3   10        all values in its RIGHT subtree > node.val
#          / \    \
#         1   6    14     searching for 6: from 8 go LEFT (6<8), from 3 go RIGHT (6>3) -> found
```

If you ignore the ordering and DFS the whole tree (11.13) to find a value, you've thrown away
the very property that makes a BST fast.

### What's really going on

A **BST** maintains the invariant *left subtree < node < right subtree* at every node, which
means at each step a comparison tells you **which single subtree** can contain your target — so
you discard the other half. That's **binary search (11.5) on a tree**: search, insert, and
delete all run in **O(h)** (h = height), which is O(log n) for a balanced tree. The other
defining BST fact: an **in-order traversal (11.13) yields values in sorted order**, which makes
"kth smallest," "validate BST," and "range queries" natural.

The catch: O(log n) holds **only if the tree is balanced**. Insert sorted data into a naive BST
and it degenerates into a linked list — height n, operations O(n). Real systems use
**self-balancing** BSTs (red-black, AVL) to keep height ~log n; in interviews you usually assume
balance or are tested on the rebalancing/operations themselves. In practice, Python's `dict`/
`set` (hashing, 11.1) give O(1) average lookup and are preferred unless you specifically need
*ordered* operations (sorted iteration, range queries, floor/ceiling) — which is exactly when a
BST (or `sortedcontainers`) earns its place.

> **Trigger:** search/insert/delete by value, **kth smallest**, validate, or **range / ordered**
> queries on a **BST**. **Pattern:** use the invariant — compare at each node and recurse into
> the *one* subtree that can contain the answer (binary search on a tree, O(h)); **in-order**
> gives sorted values. **Caveat:** O(log n) only if **balanced** (sorted inserts → O(n)
> degenerate list). For unordered lookup, a hash set/dict (11.1) beats a BST.

### The move

At each node, compare with the target and go left or right — never both:

```python
def search(root, target):
    node = root
    while node:
        if target == node.val: return node
        node = node.left if target < node.val else node.right   # use the invariant: ONE side
    return None
```

### Why it works

The invariant guarantees that if `target < node.val`, the target (if present) can only be in the
**left** subtree — everything on the right is larger — so you safely discard the right subtree
and recurse left (and vice versa). Each step eliminates one subtree, so you descend a single
root-to-leaf path: **O(h)** comparisons, O(log n) when balanced — the tree-shaped form of binary
search (11.5). Insert works the same way: walk down as if searching until you fall off the tree,
then attach the new node where the search would have continued, which automatically preserves the
ordering. And because left < node < right everywhere, an **in-order** DFS (left, node, right —
11.13) emits values in ascending order, so the kth smallest is the kth node produced — no full
sort needed.

### The code, every line explained

```python
# --- SEARCH: O(h), discard one subtree per step -------------------------
def search(root, target):
    node = root
    while node:
        if target == node.val: return node
        node = node.left if target < node.val else node.right   # the invariant picks the side
    return None

# --- INSERT: walk to the leaf position, attach ---------------------------
def insert(root, val):
    if not root: return TreeNode(val)            # found the empty slot -> place the node
    if val < root.val: root.left  = insert(root.left, val)   # belongs in the left subtree
    else:              root.right = insert(root.right, val)  # ...or the right
    return root                                  # ordering preserved automatically

# --- IN-ORDER = sorted; kth smallest -----------------------------------
def kth_smallest(root, k):
    stack, node = [], root
    while stack or node:
        while node:                              # go as far LEFT as possible
            stack.append(node); node = node.left
        node = stack.pop()                       # smallest unvisited node
        k -= 1
        if k == 0: return node.val               # the kth in ascending order
        node = node.right                        # then the right subtree
# in-order visits nodes in increasing value -> the kth popped is the kth smallest.

# --- VALIDATE a BST: pass down the allowed range (pre-order, 11.13) -----
def is_valid_bst(node, lo=float("-inf"), hi=float("inf")):
    if not node: return True
    if not (lo < node.val < hi): return False
    return (is_valid_bst(node.left, lo, node.val) and        # left values must be < node.val
            is_valid_bst(node.right, node.val, hi))          # right values must be > node.val
# NOTE: checking only node vs its immediate children is WRONG — a deep descendant can violate
# the global order. You must thread the (lo, hi) RANGE down the recursion.

# --- the balance caveat, made concrete ----------------------------------
# inserting 1,2,3,4,5 in order -> a right-leaning chain (height 5) -> search is O(n), not O(log n).
# self-balancing trees (red-black/AVL) fix this; Python's stdlib has no balanced BST, so in
# practice use `dict`/`set` (11.1) for lookups, or `sortedcontainers.SortedList` for ordered ops.

# --- BST vs hash set: pick by what you need -----------------------------
# unordered membership/lookup -> dict/set (O(1) avg, 11.1)  <- usually the right Python choice
# need SORTED iteration / range / floor-ceiling / kth -> BST or SortedList (ordered ops)
```

### Impact

- **O(h) search/insert/delete:** the ordering invariant turns "scan the whole tree" into a
  single root-to-leaf descent — O(log n) when balanced, the tree analogue of binary search.
- **Sorted order for free:** in-order traversal yields values ascending, making kth-smallest,
  range queries, and validation natural without sorting.
- **Ordered operations a hash table can't do:** range queries, floor/ceiling, predecessor/
  successor, and sorted iteration — the reason to choose a BST when order matters.

### Pros & cons / when NOT to

**Reach for a BST when:** you need **ordered** operations — sorted iteration, range queries,
kth-smallest, floor/ceiling — or you're implementing/validating one in an interview.

**Watch out / when NOT to:**
- **O(log n) requires balance** — a naive BST fed sorted data degenerates to an O(n) chain. Use a
  self-balancing tree (red-black/AVL) for guarantees; in Python, `sortedcontainers.SortedList`
  for ordered ops, since the stdlib has no balanced BST.
- **For unordered lookup, prefer `dict`/`set` (11.1)** — O(1) average vs O(log n), and simpler.
  Only choose a BST when you specifically need *order*; using one for plain membership is
  over-engineering.
- **Validate with a propagated range, not local checks** — comparing each node only to its
  direct children misses violations by deep descendants; thread `(lo, hi)` down the recursion.
- **Use the invariant — don't DFS the whole tree to search** — going into both subtrees is O(n)
  and discards the BST's entire advantage.
- **Deletion is the fiddly operation** — removing a node with two children requires replacing it
  with its in-order successor/predecessor; get this exactly right or you break the invariant.

### Where this shows up

- **Interview classics:** Validate BST, Search/Insert/Delete in a BST, Kth Smallest in a BST,
  Lowest Common Ancestor of a BST (use the invariant to pick a direction), Convert Sorted Array
  to BST, Range Sum of BST.
- **Real work (the crossover):** ordered/range data structures — database **B-tree indexes**
  (a balanced search tree generalisation) powering range scans and sorted lookups, and
  `sortedcontainers` for keeping data sorted with fast inserts; for plain key lookup, the hash
  `dict`/`set` (11.1, Area 3) is the everyday choice.
- **Pattern mapping:** **binary search (11.5)** realised on a tree; relies on **DFS** (11.13,
  in-order for sorted output); contrasts with **hashing** (11.1) — ordered O(log n) vs unordered
  O(1); balanced variants underpin database indexing.
[↑ Back to top](#contents)

---

<a id="11.16"></a>
## 11.16 — "Explore a grid, map, or network of connections" → graph BFS/DFS

### The situation

*Count the number of islands in a grid of land/water cells*, or *find the shortest path through
a maze*, or *can you get from node A to node B in a network?* You have nodes connected by edges
(a grid where cells connect to neighbours, a map of cities and roads, a social network):

```python
grid = [["1","1","0"],     # 1 = land, 0 = water
        ["1","0","0"],     # connected land cells form one "island"
        ["0","0","1"]]     # count the islands -> 2
```

It's not a tree (which has no cycles and one path between nodes); it's a general **graph** where
nodes can connect in loops and have many paths — so naive recursion (11.13) would revisit nodes
forever.

### What's really going on

Exploring a **graph** — reachability, connected components, shortest path, flood fill — uses the
same **BFS (11.14)** and **DFS (11.13)** as trees, with **one critical addition: a `visited`
set.** Graphs have **cycles** and **multiple paths** to a node, so without marking nodes visited
you loop infinitely or do exponential redundant work. The visited set is the entire difference
between tree traversal and graph traversal.

Choose by the question: **DFS** (recursion or a stack) for "explore everything reachable / count
components / is there *a* path" — it goes deep and floods a region. **BFS** (a queue) for
"**shortest** path / fewest steps in an unweighted graph" — first-reach-is-shortest (11.14). A
**grid is just a graph** where each cell's neighbours are the adjacent cells; "number of islands"
is "count connected components," solved by running DFS/BFS from each unvisited land cell and
flooding its whole island.

> **Trigger:** anything about **connections** — grids/mazes, maps, networks, "islands"/connected
> components, reachability, **shortest path (unweighted)**, flood fill, "can A reach B." **Pattern:**
> **BFS or DFS + a `visited` set** (the set is mandatory — graphs have cycles). DFS (stack/
> recursion) for explore/components/any-path; **BFS (queue) for shortest path**. **Result:** O(V +
> E). A grid = implicit graph (neighbours = adjacent cells).

### The move

Traverse with BFS/DFS, marking nodes visited so you never process one twice:

```python
def num_islands(grid):
    rows, cols, count = len(grid), len(grid[0]), 0
    visited = set()
    def dfs(r, c):
        if (r < 0 or r >= rows or c < 0 or c >= cols      # off the grid
                or grid[r][c] == "0" or (r, c) in visited):  # water, or already seen
            return
        visited.add((r, c))                                # MARK before recursing -> no loops
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):         # 4 neighbours
            dfs(r + dr, c + dc)
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1" and (r, c) not in visited:
                count += 1; dfs(r, c)                      # new component -> flood it, count it
    return count
```

### Why it works

`dfs(r,c)` floods one island: it marks the cell visited, then recurses into its four neighbours,
which recurse into theirs — so the whole connected region of land gets marked in one call. The
**`visited` set is what makes this terminate**: a grid cell's neighbours point back at it
(cycles), so without marking-before-recursing you'd bounce between adjacent cells forever. The
outer double loop starts a fresh flood only from land cells not yet visited — each such start is
a *new* island, so the count equals the number of connected components. Every cell is visited
once and its edges examined once → **O(V + E)** (here O(rows·cols)). Swap the recursion for a
queue and you get BFS, which additionally gives shortest path because it expands by distance
(11.14).

### The code, every line explained

```python
from collections import deque

# --- explicit graph as an adjacency list (dict: node -> neighbours) -----
graph = {0: [1, 2], 1: [0, 3], 2: [0], 3: [1]}    # built via defaultdict(list) (3.15)

# --- DFS: reachability / components / "any path" ------------------------
def dfs(node, graph, visited):
    if node in visited: return          # ALREADY seen -> stop (this guard prevents cycles)
    visited.add(node)                    # MARK on entry, before exploring neighbours
    for nb in graph[node]:
        dfs(nb, graph, visited)
# visited at the end = all nodes reachable from the start.

# --- BFS: SHORTEST path in an unweighted graph (11.14) ------------------
def shortest_path(graph, start, target):
    q = deque([(start, 0)]); visited = {start}    # mark on ENQUEUE (not dequeue) to avoid dups
    while q:
        node, dist = q.popleft()
        if node == target: return dist            # first reach = fewest edges = shortest
        for nb in graph[node]:
            if nb not in visited:
                visited.add(nb); q.append((nb, dist + 1))
    return -1                                      # unreachable

# --- GRID as an implicit graph: count connected components (islands) ----
def num_islands(grid):
    R, C = len(grid), len(grid[0]); seen = set(); count = 0
    def flood(r, c):
        stack = [(r, c)]                           # iterative DFS (avoids deep recursion, 11.28)
        while stack:
            x, y = stack.pop()
            if not (0 <= x < R and 0 <= y < C) or grid[x][y] == "0" or (x, y) in seen:
                continue
            seen.add((x, y))
            stack += [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]   # 4-directional neighbours
    for r in range(R):
        for c in range(C):
            if grid[r][c] == "1" and (r, c) not in seen:
                count += 1; flood(r, c)            # each new flood = one island
    return count

# --- the non-negotiable rule --------------------------------------------
# ALWAYS keep a `visited` set for GRAPHS. Trees (11.13/11.14) skip it because they have no
# cycles; a graph without `visited` loops forever or explodes exponentially.

# --- DFS vs BFS for graphs ----------------------------------------------
# DFS: reachability, connected components, cycle detection, "a path", topological sort (11.17)
# BFS: SHORTEST path / fewest steps in UNWEIGHTED graphs (weighted -> Dijkstra, 11.18)
```

### Impact

- **One toolkit for all connection problems:** islands, mazes, reachability, networks, flood
  fill — all are BFS/DFS + visited over an explicit or implicit graph, in O(V + E).
- **Correct termination on cyclic data:** the visited set is what lets you traverse real graphs
  (with loops and multiple paths) at all, not just trees.
- **Shortest path for free (unweighted):** choosing BFS gives fewest-steps answers without extra
  machinery (11.14).

### Pros & cons / when NOT to

**Reach for graph BFS/DFS when:** the problem is about **connectivity/reachability**, connected
components ("islands"), **shortest path in an unweighted** graph, flood fill, or exploring any
network/grid/map.

**Watch out / when NOT to:**
- **The `visited` set is mandatory for graphs** — omit it and cycles make you loop forever or do
  exponential work. (Trees, 11.13/11.14, skip it only because they're acyclic.)
- **Mark visited at the right moment** — for BFS, mark on **enqueue**, not dequeue, or the same
  node gets queued multiple times before it's processed (a subtle blow-up).
- **BFS for shortest path only when unweighted** — with edge weights, fewest-edges ≠ cheapest;
  use **Dijkstra** (11.18). BFS assumes every step costs the same.
- **Deep recursion can overflow** — recursive DFS on a large/long graph can hit Python's
  recursion limit; use an explicit stack (iterative DFS) for big inputs (11.28).
- **Build the graph representation first** — explicit graphs are usually an adjacency list
  (`defaultdict(list)`, 3.15); for grids, neighbours are computed (adjacent cells), not stored.
  Getting the neighbour function / bounds right is half the bug surface.
- **For weighted shortest path, MST, or strongly-connected-components, use the specialised
  algorithm** (Dijkstra 11.18, union-find 11.19, etc.) — plain BFS/DFS won't give optimal
  weighted results.

### Where this shows up

- **Interview classics:** Number of Islands, Flood Fill, Rotting Oranges (multi-source BFS),
  Word Ladder, Clone Graph, Course Schedule (cycle detection / topo sort, 11.17), Pacific
  Atlantic Water Flow, shortest path in a binary matrix.
- **Real work (the crossover):** reachability and shortest hops in real networks (dependency
  graphs, social/recommendation graphs, service maps), flood-fill in image/region processing,
  and traversing any connected structure — the same BFS/DFS + visited; adjacency lists are the
  `defaultdict(list)` from Area 3 (3.15).
- **Pattern mapping:** generalises tree **DFS/BFS** (11.13/11.14) with a visited set; the basis
  for **topological sort** (11.17), and **Dijkstra** (11.18) is BFS upgraded with a priority
  queue (11.12) for weights; **union-find** (11.19) is an alternative for connectivity/components.
[↑ Back to top](#contents)

---

<a id="11.17"></a>
## 11.17 — "Order tasks with dependencies" → topological sort

### The situation

*You have courses where some require prerequisites first; find a valid order to take them all.*
Or build steps, or task dependencies — each item must come *after* the things it depends on:

```python
prereqs = {"calc2": ["calc1"], "calc1": [], "ml": ["calc2", "linalg"], "linalg": []}
# valid order: calc1, linalg, calc2, ml  (every course after its prerequisites)
# also: can it even be done? if A needs B and B needs A, there's NO valid order (a cycle)
```

You need an ordering that respects every "must come before" constraint — and to detect when no
such ordering exists (a circular dependency).

### What's really going on

Dependencies form a **directed graph**: an edge A→B means "A must come before B." A valid
ordering where every node precedes its dependents is a **topological sort**, and it exists
**iff the graph has no cycle** (a cycle = a circular dependency = impossible to order). This is
exactly the dependency-direction problem from design (10.7), now as an algorithm.

The standard method is **Kahn's algorithm (BFS-based)**: compute each node's **in-degree** (how
many things must come before it); start with the in-degree-0 nodes (no prerequisites); repeatedly
output one, and decrement its dependents' in-degrees, adding any that reach 0. If you output all
nodes, that's a valid order; if some never reach in-degree 0, they're stuck in a **cycle** — so
the same algorithm **detects cycles** for free. (DFS-based topo sort also exists: post-order
finish times, reversed.)

> **Trigger:** "find a valid **order** respecting **dependencies/prerequisites**," "can all tasks
> be completed," scheduling with "X before Y," or **detect a cycle** in a directed graph.
> **Pattern:** model as a directed graph; **Kahn's algorithm** — repeatedly remove in-degree-0
> nodes (a BFS, 11.14, over a queue). Output count < node count ⇒ a **cycle** (no valid order).
> **Result:** O(V + E).

### The move

Count in-degrees, queue the zero-in-degree nodes, and peel them off, decrementing dependents:

```python
from collections import deque, defaultdict
def topo_sort(nodes, edges):                 # edges: list of (before, after)
    graph = defaultdict(list); indeg = {n: 0 for n in nodes}
    for before, after in edges:
        graph[before].append(after); indeg[after] += 1     # after depends on before
    q = deque([n for n in nodes if indeg[n] == 0])         # no prerequisites -> ready
    order = []
    while q:
        n = q.popleft(); order.append(n)
        for m in graph[n]:                    # n is done -> relax its dependents
            indeg[m] -= 1
            if indeg[m] == 0: q.append(m)      # all of m's prereqs done -> ready
    return order if len(order) == len(nodes) else []        # incomplete -> cycle
```

### Why it works

A node's **in-degree** is the number of prerequisites it still has; in-degree 0 means "nothing
blocks it, it's safe to do now." Starting from those and, each time you complete a node,
decrementing its dependents' in-degrees, exactly mimics resolving dependencies in order — a
dependent becomes ready precisely when its *last* prerequisite is finished (reaches 0). Because
you only ever emit a node after everything pointing to it, the output respects all "before"
constraints. The cycle detection is elegant: nodes inside a cycle each depend on another node in
the cycle, so none ever reaches in-degree 0 — they're never enqueued, so `len(order) <
len(nodes)` signals "no valid ordering exists." It's a BFS (11.14) over the dependency graph, so
**O(V + E)**.

### The code, every line explained

```python
from collections import deque, defaultdict

# --- Course Schedule II: return a valid order, or [] if impossible ------
def find_order(num_courses, prerequisites):   # prerequisites: [[course, prereq], ...]
    graph = defaultdict(list)
    indeg = [0] * num_courses
    for course, prereq in prerequisites:
        graph[prereq].append(course)           # edge prereq -> course (prereq before course)
        indeg[course] += 1                      # course has one more prerequisite

    q = deque([c for c in range(num_courses) if indeg[c] == 0])   # ready: no prereqs
    order = []
    while q:
        c = q.popleft()                         # take a ready course
        order.append(c)
        for nxt in graph[c]:                    # courses that depended on c
            indeg[nxt] -= 1                      # one prerequisite satisfied
            if indeg[nxt] == 0:                  # all prereqs done -> now ready
                q.append(nxt)
    return order if len(order) == num_courses else []   # all placed? else a CYCLE exists

# --- Course Schedule I: just "is it POSSIBLE?" (cycle detection) --------
def can_finish(num_courses, prerequisites):
    return len(find_order(num_courses, prerequisites)) == num_courses

# --- why len(order) < n means a cycle -----------------------------------
# A -> B -> A : both A and B always have in-degree >= 1 (each waits on the other), so
# NEITHER is ever enqueued -> they never enter `order` -> len(order) < n -> impossible.

# --- DFS-based alternative (post-order, then reverse) -------------------
# dfs(node): mark "in progress"; recurse unvisited neighbours; on the way OUT append to a list;
# finally reverse it. A node seen while still "in progress" -> back edge -> CYCLE.
# Kahn's (BFS) is usually easier to reason about and detects cycles via the count.

# --- the giveaway -------------------------------------------------------
# "valid order given prerequisites / dependencies", "can all tasks be done", "build order",
# "X must come before Y" -> topological sort. The "impossible if circular" hint = cycle check.
```

### Impact

- **Produces a valid dependency order** (or proves none exists) in O(V + E) — the standard,
  efficient answer for prerequisite/scheduling/build-order problems.
- **Free cycle detection:** the same algorithm that orders also reports circular dependencies —
  exactly the "no valid order" case.
- **Models real dependency systems:** the algorithm behind build tools, task schedulers, and
  course planners.

### Pros & cons / when NOT to

**Reach for topological sort when:** you must order items under "X before Y" dependencies, check
if all tasks can complete, find a build/execution order, or detect cycles in a **directed**
graph.

**Watch out / when NOT to:**
- **Only works on a DAG** — a directed graph **with a cycle has no topological order**. Always
  check `len(order) == n`; a smaller count means a cycle (don't return a partial order as if
  valid).
- **Get the edge direction right** — "B is a prerequisite of A" means edge **B→A** and A's
  in-degree increases. Reversing this silently produces a wrong (or reversed) order — a classic
  bug.
- **The order usually isn't unique** — multiple valid orderings exist; any that respects
  dependencies is correct (don't assume one specific output).
- **Undirected graphs aren't topologically sortable** — this is for *directed* dependencies; for
  undirected connectivity use BFS/DFS (11.16) or union-find (11.19).
- **Mark "in progress" vs "done" if using DFS** — DFS cycle detection needs three states (white/
  gray/black); a plain visited set can't distinguish a back edge (cycle) from a cross edge.

### Where this shows up

- **Interview classics:** Course Schedule I/II, Alien Dictionary (derive letter order from
  sorted words), Parallel Courses, Minimum Height Trees, Sequence Reconstruction, Build Order.
- **Real work (the crossover):** build systems (Make/Bazel) and task runners ordering steps by
  dependency, package/dependency managers resolving install order, data-pipeline DAGs (Airflow),
  and spreadsheet cell recomputation — and it's literally the **module dependency-direction /
  no-cycles** rule from design (10.7).
- **Pattern mapping:** a directed-graph algorithm built on **BFS** (11.14, Kahn's) or **DFS**
  (11.13, post-order); the cycle check overlaps graph traversal (11.16); the dependency-DAG idea
  is the same one underpinning 10.7.
[↑ Back to top](#contents)

---

<a id="11.18"></a>
## 11.18 — "Cheapest path when edges have different costs" → Dijkstra

### The situation

*Find the cheapest route from city A to city B, where roads have different distances/costs.* BFS
(11.14/11.16) finds the path with the **fewest edges**, but here edges have **weights**, and
fewest-hops isn't cheapest:

```python
# A --1--> B --1--> C      two hops, total cost 2
# A --5--------> C         one hop, total cost 5
# BFS picks the 1-hop path (cost 5); the CHEAPEST is A->B->C (cost 2). Hops != cost.
```

When steps cost different amounts, "fewest steps" and "lowest total cost" diverge — so plain BFS
gives the wrong answer.

### What's really going on

For **shortest path in a weighted graph with non-negative edge weights**, the algorithm is
**Dijkstra**. It's BFS upgraded: instead of a plain FIFO queue (which expands by number of hops),
it uses a **min-heap (priority queue, 11.12)** keyed by **total cost so far**, so it always
expands the **cheapest-reachable** node next. The first time it finalises a node, it has the
minimum cost to reach it — the weighted analogue of BFS's first-reach-is-shortest.

The mechanism is **greedy** (11.24): repeatedly pop the lowest-cost unfinalised node, and
**relax** its edges (if going through it reaches a neighbour more cheaply, record the cheaper
cost and push it). Using a heap, each node/edge is processed efficiently → **O(E log V)**.
Crucially, Dijkstra **requires non-negative weights** — its greedy "the cheapest popped node is
final" logic breaks if a later negative edge could undercut it; for negative weights you need
Bellman-Ford instead.

> **Trigger:** **shortest/cheapest path** (or min cost to reach all nodes) in a graph with
> **weighted, non-negative** edges — "minimum cost," "shortest time," "cheapest flights within K
> stops." **Pattern:** **Dijkstra** = BFS with a **min-heap by total cost** (11.12); pop the
> cheapest node, **relax** its edges. First finalisation = optimal cost. **Result:** O(E log V).
> **Non-negative weights only** (else Bellman-Ford). Unweighted? plain BFS (11.14/11.16).

### The move

Run BFS with a min-heap keyed by cumulative cost; pop the cheapest node and relax its edges:

```python
import heapq
def dijkstra(graph, start):                  # graph: node -> [(neighbour, weight), ...]
    dist = {start: 0}
    heap = [(0, start)]                       # (cost_so_far, node) — min-heap by cost
    while heap:
        d, node = heapq.heappop(heap)         # the cheapest-reachable unfinalised node
        if d > dist.get(node, float("inf")):  # stale entry (we already found cheaper) -> skip
            continue
        for nb, w in graph[node]:
            nd = d + w                         # cost to reach nb via node
            if nd < dist.get(nb, float("inf")):   # relax: found a cheaper route to nb
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))
    return dist                               # cheapest cost from start to every reachable node
```

### Why it works

The min-heap always hands you the unfinalised node with the **smallest total cost so far**.
Because all edge weights are **non-negative**, no path through a not-yet-finalised (more
expensive) node could reach this one more cheaply — so the first time a node is popped, its
recorded distance is provably optimal and final. **Relaxing** each edge ("is going through
`node` cheaper for `nb` than what I had?") propagates improvements outward, and pushing the new
cost re-queues `nb` at its better priority. Old, now-superseded heap entries are skipped by the
`d > dist[node]` staleness check (cheaper than deleting from a heap). Each edge triggers at most
one useful push → **O(E log V)**. The non-negativity is load-bearing: a negative edge could make
a path through an "expensive" node suddenly cheap, violating the "first pop is final" guarantee —
which is why negative weights need Bellman-Ford.

### The code, every line explained

```python
import heapq
from collections import defaultdict

# --- Dijkstra: cheapest cost from start to all nodes --------------------
def dijkstra(graph, start):
    dist = {start: 0}                         # best known cost to each node
    heap = [(0, start)]                       # min-heap ordered by cost (11.12)
    while heap:
        d, node = heapq.heappop(heap)         # GREEDY: take the globally cheapest frontier node
        if d > dist.get(node, float("inf")):  # a stale, superseded entry -> ignore
            continue                           # (lazy deletion instead of removing from heap)
        for nb, w in graph[node]:             # examine neighbours
            nd = d + w
            if nd < dist.get(nb, float("inf")):   # RELAX: cheaper route found
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))    # enqueue nb at its improved cost
    return dist

# --- Network Delay Time: time for a signal to reach ALL nodes -----------
def network_delay(times, n, k):               # times: [(u, v, w)], k = source
    graph = defaultdict(list)
    for u, v, w in times: graph[u].append((v, w))
    dist = dijkstra(graph, k)
    return max(dist.values()) if len(dist) == n else -1   # -1 if some node unreachable

# --- variant with a CONSTRAINT: cheapest flight within K stops ----------
# push (cost, node, stops_left); only relax/push a neighbour if stops_left > 0. The extra
# state in the heap entry handles the "at most K stops" twist (state-augmented Dijkstra).

# --- which algorithm, by graph type -------------------------------------
# unweighted graph        -> BFS (11.14/11.16): fewest edges = shortest
# non-negative weights     -> Dijkstra (this): min-heap by cost
# NEGATIVE weights         -> Bellman-Ford: O(V·E), handles negatives, detects negative cycles
# all-pairs shortest paths -> Floyd-Warshall: O(V³)

# --- the trap -----------------------------------------------------------
# Dijkstra is WRONG with negative edges: a node popped as "final" might later be reachable
# more cheaply via a negative edge. If weights can be negative, use Bellman-Ford, not this.
```

### Impact

- **Optimal weighted shortest paths:** correctly handles different edge costs where BFS's
  fewest-hops answer would be wrong — the standard tool for routing/min-cost problems.
- **Efficient at scale:** the heap makes it O(E log V), practical on large road/flight/network
  graphs.
- **Extensible:** augmenting the heap state (stops left, fuel, etc.) adapts it to constrained
  shortest-path variants without changing the core idea.

### Pros & cons / when NOT to

**Reach for Dijkstra when:** finding the cheapest/shortest path (or min cost to all nodes) in a
graph with **weighted, non-negative** edges.

**Watch out / when NOT to:**
- **Non-negative weights only** — Dijkstra is **incorrect** with negative edges (the "first pop
  is final" guarantee breaks). Use **Bellman-Ford** for negatives (and to detect negative
  cycles).
- **Unweighted graph? use plain BFS (11.14/11.16)** — Dijkstra's heap is unnecessary overhead
  when every edge costs the same; BFS already gives the shortest path.
- **Handle stale heap entries** — `heapq` can't update a key, so you push duplicates and **skip
  outdated pops** (`if d > dist[node]: continue`); forgetting this still works but wastes time,
  and using the stale distance is a correctness bug.
- **Make heap entries comparable** — push `(cost, node)` so ties compare on `node`; if `node` is
  unorderable, add a tiebreaker (same caveat as 11.12).
- **For all-pairs shortest paths, Floyd-Warshall** (O(V³)) may be simpler than running Dijkstra
  from every source on dense graphs.
- **A* is Dijkstra + a heuristic** — if you have a good distance estimate to the target (e.g.
  grid coordinates), A* explores far less; Dijkstra is A* with a zero heuristic.

### Where this shows up

- **Interview classics:** Network Delay Time, Cheapest Flights Within K Stops, Path with Minimum
  Effort, Swim in Rising Water, Path with Maximum Probability, shortest path in a weighted grid.
- **Real work (the crossover):** routing and navigation (maps, networks), least-cost path
  problems (latency-aware routing, cost-optimal pipelines), and any "minimum total cost to get
  from here to there" over a weighted graph — the priority queue is the same `heapq` from
  11.12/Area 3.
- **Pattern mapping:** **BFS** (11.14/11.16) generalised to weights via a **min-heap** (11.12);
  it's a **greedy** algorithm (11.24); contrasts with Bellman-Ford (negative weights) and
  Floyd-Warshall (all-pairs), and specialises to **A*** with a heuristic.
[↑ Back to top](#contents)

---

<a id="11.19"></a>
## 11.19 — "Group connected things / are these two in the same group?" → union-find

### The situation

*You're given pairs of connected items and must answer "are A and B in the same group?" — with
new connections arriving over time.* Or count how many groups remain as you merge:

```python
# friendships arrive one by one: (0,1), (1,2), (3,4)
# queries interleave: "are 0 and 2 connected?" (yes, via 1)  "0 and 3?" (no)
# re-running BFS/DFS (11.16) for EACH query, as edges keep being added, is wasteful
```

You *could* DFS/BFS for each query, but with connections being added incrementally and many
"same group?" queries, repeatedly re-traversing is expensive.

### What's really going on

For **dynamic connectivity** — incrementally merging groups and asking "same group?" — the right
tool is **union-find (disjoint set union, DSU)**. It maintains a forest where each group is a
tree with a **representative root**; two operations: **`find(x)`** returns x's root (which group
it's in), and **`union(a,b)`** merges two groups by linking one root under the other. "Are A and
B connected?" is just `find(A) == find(B)` — near-O(1).

Two optimisations make it nearly constant time: **path compression** (during `find`, point nodes
directly at the root, flattening the tree) and **union by rank/size** (attach the smaller tree
under the larger). Together they give an **inverse-Ackermann** amortised cost — effectively O(1)
per operation. Union-find shines where BFS/DFS struggles: *incremental* merging and *repeated*
connectivity queries, counting connected components, and cycle detection in an *undirected*
graph (an edge whose endpoints already share a root closes a cycle).

> **Trigger:** **dynamic connectivity** — merge groups and repeatedly ask "**are A and B in the
> same group?**", count connected components as edges are added, or detect a cycle in an
> **undirected** graph. **Pattern:** **union-find / DSU** — `find` (with path compression) +
> `union` (by rank/size). Same group ⇔ same root. **Result:** ~O(1) amortised per op (α, inverse
> Ackermann). Prefer over BFS/DFS (11.16) when connections are *incremental* or queries are many.

### The move

Keep a `parent` array; `find` walks to the root (compressing the path), `union` links two roots:

```python
class DSU:
    def __init__(self, n):
        self.parent = list(range(n))          # each node starts as its own root (own group)
        self.rank = [0] * n                    # tree heights, for union by rank
    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]   # path compression (halving)
            x = self.parent[x]
        return x                               # the group's representative root
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return False              # already same group (an edge here = a CYCLE)
        if self.rank[ra] < self.rank[rb]: ra, rb = rb, ra   # attach smaller under larger
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]: self.rank[ra] += 1
        return True                            # a real merge happened
```

### Why it works

Each group is a tree identified by its root, so "same group?" reduces to "same root?" —
`find(a) == find(b)`. `union` merges by pointing one root at the other, instantly combining two
groups in O(1) (plus the `find`s). The two optimisations keep the trees flat so `find` stays
fast: **path compression** rewires nodes directly toward the root as it walks (so future `find`s
are short), and **union by rank** always hangs the shorter tree under the taller one (so trees
never get needlessly deep). Together they bound the amortised cost at the inverse-Ackermann
function α(n) — ≤ 4 for any realistic n, i.e. effectively constant. Cycle detection falls out:
if `union(a,b)` finds `a` and `b` already share a root, the edge connects two already-connected
nodes — a cycle in an undirected graph.

### The code, every line explained

```python
class DSU:
    def __init__(self, n):
        self.parent = list(range(n))           # parent[i] = i -> n singleton groups
        self.rank = [0] * n
        self.count = n                          # number of groups (decrements on each real union)
    def find(self, x):
        while self.parent[x] != x:              # walk up to the root
            self.parent[x] = self.parent[self.parent[x]]   # PATH COMPRESSION: skip a level
            x = self.parent[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return False               # same group already -> no merge (cycle edge)
        if self.rank[ra] < self.rank[rb]: ra, rb = rb, ra   # UNION BY RANK
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]: self.rank[ra] += 1
        self.count -= 1                          # two groups became one
        return True
    def connected(self, a, b):
        return self.find(a) == self.find(b)      # the "same group?" query, ~O(1)

# --- count connected components (after adding all edges) ----------------
def count_components(n, edges):
    dsu = DSU(n)
    for a, b in edges: dsu.union(a, b)
    return dsu.count                             # groups remaining

# --- cycle detection in an UNDIRECTED graph -----------------------------
def has_cycle(n, edges):
    dsu = DSU(n)
    for a, b in edges:
        if not dsu.union(a, b):                  # endpoints already connected -> CYCLE
            return True
    return False

# --- where it beats BFS/DFS: edges arrive ONLINE, many queries ----------
# BFS/DFS (11.16) recomputes connectivity from scratch each query. DSU updates incrementally
# in ~O(1) per union/query -> ideal when connections are added over time and you query often.

# --- the giveaway -------------------------------------------------------
# "are X and Y connected?", "how many groups?", "merge accounts/regions", "redundant edge /
# cycle in an undirected graph", Kruskal's MST -> union-find.
```

### Impact

- **~O(1) dynamic connectivity:** merge and "same group?" queries are effectively constant time
  with compression + rank — far better than re-running BFS/DFS per query as edges accumulate.
- **Natural for incremental/online problems:** handles connections arriving over time, where
  traversal-based approaches would recompute from scratch.
- **Components & undirected cycles for free:** counting groups and detecting redundant edges
  (cycles) fall directly out of the structure.

### Pros & cons / when NOT to

**Reach for union-find when:** connectivity is **dynamic** (edges added over time), you have
**many "same group?" queries**, you need to **count components**, detect **undirected cycles**,
or build a **minimum spanning tree** (Kruskal's).

**Watch out / when NOT to:**
- **Apply both optimisations** — path compression *and* union by rank/size. Without them, trees
  can degenerate to O(n)-deep chains and `find` becomes O(n); together they're ~O(1).
- **Union-find doesn't give paths** — it answers "connected?" and "which group?", not the *route*
  between two nodes. For an actual path/shortest path, use BFS/DFS (11.16) or Dijkstra (11.18).
- **It's for undirected connectivity / grouping** — cycle detection here is for *undirected*
  graphs; *directed* cycle detection / ordering is topological sort (11.17).
- **No efficient "un-union"** — standard DSU only merges; it can't split groups (removing edges
  needs different techniques). It's add-only connectivity.
- **For a one-shot, static "count components once," BFS/DFS (11.16) is just as good** — DSU's
  edge is *incremental* updates and *repeated* queries; don't add it where a single traversal
  suffices.

### Where this shows up

- **Interview classics:** Number of Connected Components, Graph Valid Tree, Redundant Connection
  (find the cycle-closing edge), Accounts Merge, Number of Islands II (online), Kruskal's MST,
  Most Stones Removed.
- **Real work (the crossover):** grouping/clustering by transitive relationships — merging
  duplicate accounts/records (entity resolution), connected regions in image segmentation,
  network/cluster membership, and incremental "are these two in the same partition?" checks
  over streaming connections.
- **Pattern mapping:** an alternative to **BFS/DFS** (11.16) for connectivity, optimal when
  *dynamic*; the engine of **Kruskal's MST** (a greedy algorithm, 11.24); contrasts with
  **topological sort** (11.17, which is for *directed* dependency cycles/ordering).
[↑ Back to top](#contents)

---

<a id="11.20"></a>
## 11.20 — "Generate all valid combinations, with pruning" → backtracking

### The situation

*Generate all permutations of `[1,2,3]`*, or *all subsets*, or *place N queens so none attack
each other*, or *solve a Sudoku.* You need to explore *all* ways to build something, abandoning
partial attempts that can't lead to a valid result:

```python
# all permutations of [1,2,3]: [1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]
# N-Queens: try placing a queen per row; if a placement is attacked, that branch is DEAD —
#           don't keep exploring it. but how do you systematically try all, and back out?
```

A pile of nested loops can't express "build up a partial solution, and when it goes wrong,
*undo the last choice and try the next*." That undo-and-retry is the heart of it.

### What's really going on

**Backtracking** is systematic, exhaustive search that builds a solution **incrementally** and
**abandons** ("backtracks" from) a partial candidate the moment it can't possibly succeed. It's
DFS (11.13) over the tree of *choices*: at each step you **choose** an option, **recurse** to
extend the solution, then **un-choose** (undo) to try the next option. The undo is what makes it
backtracking rather than plain recursion.

The universal template is **choose → explore → un-choose**. **Pruning** is the key optimisation:
the sooner you detect a partial solution is invalid (a queen is attacked, a sum already exceeds
target), the sooner you cut that whole branch — turning a hopeless exponential search into a
tractable one. Backtracking is inherently **exponential** in the worst case (there are
exponentially many subsets/permutations), so it's for problems where the answer space is
genuinely combinatorial and pruning keeps it manageable.

> **Trigger:** "**generate all** / find **all** valid ___" — permutations, combinations, subsets,
> partitions, placements (N-Queens), constraint puzzles (Sudoku), word search. **Pattern:**
> **backtracking** = DFS over choices with **choose → explore → un-choose**, plus **pruning**
> (abandon invalid partials early). **Result:** exponential worst case (the answer space is), but
> pruning makes real instances feasible.

### The move

Recurse building a partial solution; at each step choose an option, recurse, then undo it:

```python
def permutations(nums):
    res, path, used = [], [], [False] * len(nums)
    def backtrack():
        if len(path) == len(nums):            # base case: a complete solution
            res.append(path[:]); return        # append a COPY (path is mutated below)
        for i, x in enumerate(nums):
            if used[i]: continue               # PRUNE: skip already-used elements
            used[i] = True; path.append(x)     # CHOOSE
            backtrack()                         # EXPLORE
            used[i] = False; path.pop()         # UN-CHOOSE (the backtrack step)
    backtrack()
    return res
```

### Why it works

The recursion explores the tree of choices: each level picks the next element of the permutation,
and the `for` loop tries every still-available option at that level. The three-step rhythm is the
engine — **choose** (mark `x` used, add to `path`), **explore** (recurse to fill the rest), then
**un-choose** (unmark, pop) so the loop can try the *next* option from the same state. That undo
is what lets one mutable `path`/`used` be reused across the whole search instead of copying state
everywhere. The base case (`len(path) == len(nums)`) records a finished solution — copied with
`path[:]` because `path` keeps mutating. `used[i]` is a prune: it cuts branches that would repeat
an element. For harder problems (N-Queens), the prune is a validity check ("is this square
attacked?") that abandons doomed branches early, which is what keeps an exponential search
tractable.

### The code, every line explained

```python
# --- the BACKTRACKING TEMPLATE ------------------------------------------
def backtrack(state, choices):
    if is_complete(state):
        record(state); return              # base case: a full valid solution
    for choice in choices:
        if not valid(state, choice):       # PRUNE: skip choices that can't lead to a solution
            continue
        make(state, choice)                # CHOOSE
        backtrack(state, choices)          # EXPLORE (recurse deeper)
        undo(state, choice)                # UN-CHOOSE (restore state, try next)

# --- SUBSETS: include or exclude each element ---------------------------
def subsets(nums):
    res, path = [], []
    def bt(start):
        res.append(path[:])                # every node is a valid subset
        for i in range(start, len(nums)):
            path.append(nums[i])           # CHOOSE nums[i]
            bt(i + 1)                       # EXPLORE with later elements (start=i+1 avoids dups)
            path.pop()                      # UN-CHOOSE
    bt(0); return res

# --- COMBINATION SUM: prune when the running sum exceeds target ---------
def combination_sum(candidates, target):
    res, path = [], []
    def bt(start, remaining):
        if remaining == 0: res.append(path[:]); return
        for i in range(start, len(candidates)):
            if candidates[i] > remaining: continue      # PRUNE: would overshoot
            path.append(candidates[i])
            bt(i, remaining - candidates[i])             # i (not i+1): allow reuse
            path.pop()
    bt(0, target); return res

# --- N-QUEENS: prune attacked squares (the prune is the whole game) -----
def solve_n_queens(n):
    res, cols, diag, anti = [], set(), set(), set()      # track attacked columns/diagonals
    def bt(row, placement):
        if row == n: res.append(placement[:]); return
        for c in range(n):
            if c in cols or (row-c) in diag or (row+c) in anti:
                continue                                  # PRUNE: this square is attacked
            cols.add(c); diag.add(row-c); anti.add(row+c); placement.append(c)   # CHOOSE
            bt(row + 1, placement)                        # EXPLORE
            cols.remove(c); diag.remove(row-c); anti.remove(row+c); placement.pop()  # UNDO
    bt(0, []); return res

# --- the two cardinal rules ---------------------------------------------
# 1. ALWAYS undo your choice after exploring (or state leaks across branches -> wrong results)
# 2. record a COPY of the solution (path[:]), not the mutable path itself, or all results
#    end up pointing at the same (now-empty) list.
```

### Impact

- **Exhaustively and correctly generates all solutions:** the choose/explore/undo structure
  systematically covers the entire answer space without missing or duplicating candidates.
- **Pruning makes the intractable tractable:** abandoning doomed partials early cuts huge swaths
  of the exponential search tree — the difference between N-Queens/Sudoku solving in milliseconds
  vs not at all.
- **One template, many problems:** permutations, combinations, subsets, partitions, placements,
  and constraint puzzles are all the same skeleton with a different "valid"/"complete"/"choices".

### Pros & cons / when NOT to

**Reach for backtracking when:** the problem asks to **generate/find all** valid configurations,
or to find *one* satisfying complex constraints (N-Queens, Sudoku, word search) — combinatorial
search problems.

**Watch out / when NOT to:**
- **Always undo the choice** after recursing — forgetting the un-choose leaks state into sibling
  branches and produces wrong results. The undo *is* the backtrack.
- **Record a copy** (`path[:]`), not the live mutable `path` — appending the same list object
  means every saved solution ends up identical (and empty) as `path` keeps changing. A classic,
  baffling bug.
- **Prune as early as possible** — the whole point is cutting dead branches; a check done one
  level too late still explores exponentially. Push validity checks to the moment of choosing.
- **It's exponential — bound the input** — backtracking is for small/medium combinatorial spaces.
  If the input is large and you only need a *count* or an *optimum* (not all solutions), it's
  often a **DP** problem (11.21) instead.
- **Avoid duplicate solutions deliberately** — for combinations/subsets, the `start` index (or
  sorting + skip-equal) prevents permutations of the same set; without it you over-generate.

### Where this shows up

- **Interview classics:** Permutations, Subsets, Combination Sum, Combinations, Palindrome
  Partitioning, N-Queens, Sudoku Solver, Word Search, Generate Parentheses, Letter Combinations
  of a Phone Number.
- **Real work (the crossover):** constraint-satisfaction and configuration search — generating
  valid layouts/schedules, exhaustive test-case/parameter enumeration, parsing with backtracking
  grammars, and small combinatorial optimisation where you must try all options with pruning.
- **Pattern mapping:** backtracking is **DFS (11.13)** over a *choice tree* with state undo;
  built on **recursion** (11.28); when the goal is a count/optimum over overlapping subproblems
  rather than enumerating all, it becomes **dynamic programming** (11.21–11.23).
[↑ Back to top](#contents)

---

<a id="11.21"></a>
## 11.21 — "Count the ways / find the optimum over overlapping subproblems" → dynamic programming (1D)

### The situation

*How many distinct ways can you climb `n` stairs taking 1 or 2 steps at a time?* The natural
recursion re-solves the same subproblems exponentially many times:

```python
def climb(n):
    if n <= 2: return n
    return climb(n-1) + climb(n-2)        # ways(n) = ways(n-1) + ways(n-2)
# correct, but climb(n-2) is computed by BOTH climb(n) and climb(n-1)... -> O(2^n), exponential
# climb(50) recomputes the same values BILLIONS of times
```

The recurrence is right, but it recomputes `climb(k)` for the same `k` over and over — an
exponential blow-up from **overlapping subproblems**.

### What's really going on

**Dynamic programming (DP)** applies when a problem has (1) **optimal substructure** — the answer
is built from answers to smaller subproblems — and (2) **overlapping subproblems** — those
smaller problems recur many times. The fix is to **solve each subproblem once and store the
result**, so it's never recomputed.

Two equivalent styles: **top-down (memoization)** — keep the recursion but cache results
(literally `@lru_cache`, 1.13, on the recursive function); and **bottom-up (tabulation)** — fill
a table from the base cases upward. The art is identifying the **state** (what defines a
subproblem — here, "number of stairs left") and the **recurrence** (how a state's answer combines
smaller states' answers — here `f(n) = f(n-1) + f(n-2)`). Once you have those, DP is mechanical:
each of O(n) states is computed once in O(1), so the exponential recursion collapses to **O(n)**.

> **Trigger:** "**count the ways**," "**min/max** cost/length," "**can you reach/make** X" — where
> the answer builds from smaller subproblems that **recur**, and greedy doesn't work because
> choices interact. **Pattern:** define **state** + **recurrence** + **base case**; solve each
> state once via **memoization** (top-down, `@lru_cache`, 1.13) or **tabulation** (bottom-up
> table). **Result:** O(states × work-per-state) — collapses exponential recursion to polynomial.

### The move

Identify the state and recurrence, then either memoize the recursion or fill a table bottom-up:

```python
from functools import lru_cache

# top-down: same recursion + a cache (1.13) -> each state computed once
@lru_cache(maxsize=None)
def climb(n):
    if n <= 2: return n
    return climb(n-1) + climb(n-2)        # now O(n): each climb(k) computed ONCE

# bottom-up: fill a table from the base cases up
def climb_tab(n):
    if n <= 2: return n
    a, b = 1, 2                            # f(1), f(2)
    for _ in range(3, n+1):
        a, b = b, a + b                    # f(k) = f(k-1) + f(k-2); keep only the last two
    return b                               # O(n) time, O(1) space
```

### Why it works

The exponential cost came purely from recomputing the same subproblems. **Memoization** caches
each `climb(k)` the first time it's computed (1.13), so every later call is an O(1) lookup —
turning the branching recursion into O(n) computations. **Tabulation** does the same work in the
opposite direction: it fills `f(1), f(2), f(3), …` in order, each from already-computed
predecessors, so every state is produced exactly once. They're equivalent in complexity; the
recurrence and base cases are identical — only the bookkeeping differs. The further win
(`climb_tab`) is recognising that `f(k)` only needs the *last two* values, so you keep two
variables instead of a whole table — **O(1) space**. The entire skill is naming the **state**
(here, "n stairs remaining") and the **recurrence** (`f(n)=f(n-1)+f(n-2)`); once those are right,
DP is mechanical.

### The code, every line explained

```python
from functools import lru_cache

# --- COIN CHANGE: fewest coins to make `amount` (min-DP) ----------------
def coin_change(coins, amount):
    INF = amount + 1
    dp = [0] + [INF] * amount              # dp[a] = fewest coins to make `a`; dp[0]=0 (base)
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a:
                dp[a] = min(dp[a], dp[a-c] + 1)   # recurrence: use coin c, +1 coin
    return dp[amount] if dp[amount] != INF else -1   # INF -> impossible

# --- HOUSE ROBBER: max sum, no two adjacent (decision DP) ---------------
def rob(nums):
    prev, curr = 0, 0                      # best for first i-1 / i houses
    for x in nums:
        prev, curr = curr, max(curr, prev + x)   # rob this (prev+x) or skip (curr)
    return curr                            # O(n) time, O(1) space

# --- LONGEST INCREASING SUBSEQUENCE (O(n^2) DP form) --------------------
def lis(nums):
    if not nums: return 0
    dp = [1] * len(nums)                   # dp[i] = LIS ending at i
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)   # extend a smaller-ending subsequence
    return max(dp)

# --- the 4-step DP recipe -----------------------------------------------
# 1. STATE: what defines a subproblem? (n stairs left / amount a / houses up to i)
# 2. RECURRENCE: how does a state's answer use smaller states? (f(n)=f(n-1)+f(n-2))
# 3. BASE CASES: the smallest states' answers (f(1)=1, dp[0]=0)
# 4. ORDER/CACHE: memoize the recursion (top-down) OR fill a table bottom-up
# then OPTIMISE SPACE if a state only needs the last few values (rolling variables).

# --- DP vs the others ---------------------------------------------------
# overlapping subproblems + optimal substructure -> DP (count/optimum, NOT all solutions)
# need ALL solutions enumerated -> backtracking (11.20)
# a locally-best choice is provably globally optimal -> greedy (11.24, simpler than DP)
```

### Impact

- **Exponential → polynomial:** caching/tabulating overlapping subproblems collapses O(2^n)
  recursion to O(n) (or O(n·m)) — the defining DP win, the difference between feasible and not.
- **Often O(1) space:** when a state depends only on the last few, rolling variables replace the
  whole table (Fibonacci/stairs/house-robber).
- **One recipe, vast coverage:** state + recurrence + base case + order solves a huge class of
  count/optimise problems that have no greedy shortcut.

### Pros & cons / when NOT to

**Reach for DP when:** the problem asks to **count ways** or find a **min/max/optimum**, the
answer builds from **smaller subproblems that overlap**, and a greedy choice isn't safe (choices
interact).

**Watch out / when NOT to:**
- **No overlapping subproblems? It's not DP.** If subproblems don't recur, memoization saves
  nothing — it's just recursion (11.28) or divide-and-conquer. DP's whole value is reusing
  repeated subproblems.
- **If a locally-optimal choice is provably globally optimal, use greedy (11.24)** — it's simpler
  and faster. DP is for when you must consider combinations of choices because they interact.
- **Getting the state/recurrence wrong is the real difficulty** — an incomplete state (missing a
  dimension the answer depends on) gives wrong results. Define exactly what determines a
  subproblem before coding.
- **Watch base cases and iteration order (bottom-up)** — a state must be computed *before* the
  states that use it; wrong order reads uninitialised entries. Memoization sidesteps ordering
  but uses call-stack/recursion-limit (11.28).
- **Mind memory** — a full table can be large; collapse to rolling variables when only the last
  few states are needed. For *enumerating* solutions (not counting/optimising), use backtracking
  (11.20), not DP.

### Where this shows up

- **Interview classics:** Climbing Stairs, Coin Change, House Robber, Longest Increasing
  Subsequence, Maximum Subarray (Kadane's), Word Break, Decode Ways, Partition Equal Subset Sum,
  Jump Game.
- **Real work (the crossover):** the memoization instinct is the everyday `@lru_cache` (1.13) —
  caching expensive recursive/repeated computations; and optimisation DPs underlie sequence
  alignment in bioinformatics, **edit distance** in spell-check/diff (11.23), and resource-
  allocation/scheduling optimisation.
- **Pattern mapping:** top-down DP *is* recursion (11.28) + memoization (1.13); it generalises to
  **2D DP** (11.22) and **string DP** (11.23); contrasts with **backtracking** (11.20, enumerate
  all) and **greedy** (11.24, when local choices suffice).
[↑ Back to top](#contents)

---

<a id="11.22"></a>
## 11.22 — "Optimum over a grid or two interacting dimensions" → 2D dynamic programming

### The situation

*Count the unique paths from top-left to bottom-right of an m×n grid, moving only right or down.*
Or *min-cost path through a cost grid.* The state now depends on **two** coordinates, not one:

```python
# 3x3 grid, move right/down only: how many distinct paths corner-to-corner?  -> 6
# paths(r,c) = paths(r-1,c) + paths(r,c-1)   (arrive from above OR from the left)
# naive recursion recomputes paths(r,c) for the same (r,c) exponentially -> too slow
```

It's still DP (11.21) — overlapping subproblems, optimal substructure — but a subproblem is now
identified by a **pair** `(row, col)`, so the table is two-dimensional.

### What's really going on

**2D dynamic programming** is 1D DP (11.21) with a **two-part state** — typically a position in a
grid `(r, c)`, or an index into *two* sequences `(i, j)` (which is string DP, 11.23). The same
recipe applies: define the state, the recurrence (how `(r,c)` builds from neighbouring states),
and base cases (the first row/column, or empty prefixes); then fill a 2D table — usually row by
row so each cell's dependencies (`dp[r-1][c]`, `dp[r][c-1]`) are already computed.

For unique paths: `dp[r][c] = dp[r-1][c] + dp[r][c-1]` (you reach a cell from above or from the
left), with the first row/column all 1 (only one way along an edge). The complexity is
**O(m×n)** — one computation per cell — versus exponential recursion. As in 1D, you can often
**reduce space**: if each row depends only on the row above, keep a single rolling row (O(n)
space instead of O(m×n)).

> **Trigger:** optimum / count over a **grid** (paths, min-cost path, max square) or over **two
> sequences/indices** (edit distance, LCS — 11.23). **Pattern:** **2D DP** — state `(r,c)` or
> `(i,j)`, recurrence from adjacent cells, base cases on the first row/column (or empty prefixes);
> fill a 2D table in dependency order. **Result:** O(m×n); often reducible to O(n) space with a
> rolling row.

### The move

Build a 2D table; initialise the first row/column, then fill each cell from its already-computed
neighbours:

```python
def unique_paths(m, n):
    dp = [[1] * n for _ in range(m)]          # first row & column = 1 (one way along an edge)
    for r in range(1, m):
        for c in range(1, n):
            dp[r][c] = dp[r-1][c] + dp[r][c-1]   # from above + from the left
    return dp[m-1][n-1]
```

### Why it works

Each cell's answer combines its neighbours' answers (`from above + from the left`), and by
filling the table **row by row, left to right**, both `dp[r-1][c]` and `dp[r][c-1]` are already
computed when you reach `dp[r][c]` — so every cell is solved exactly once. The first row and
column are the base cases: along the top edge or left edge there's only one path, so they're all
1. This is identical in spirit to 1D DP (11.21) — overlapping subproblems solved once — only the
state is a coordinate *pair*, so the table is a grid. The exponential recursion (which recomputes
`(r,c)` many times) becomes **O(m×n)**, one pass over the grid. Because each row only reads the
row directly above (and the current row to its left), you can keep a single rolling row and drop
to **O(n) space**.

### The code, every line explained

```python
# --- UNIQUE PATHS: count paths corner to corner -------------------------
def unique_paths(m, n):
    dp = [[1] * n for _ in range(m)]          # base: first row/col have exactly 1 path
    for r in range(1, m):
        for c in range(1, n):
            dp[r][c] = dp[r-1][c] + dp[r][c-1]   # arrive from above OR from the left
    return dp[m-1][n-1]

# --- MIN PATH SUM: cheapest top-left to bottom-right --------------------
def min_path_sum(grid):
    m, n = len(grid), len(grid[0])
    dp = [[0]*n for _ in range(m)]
    dp[0][0] = grid[0][0]
    for r in range(m):
        for c in range(n):
            if r == 0 and c == 0: continue
            up   = dp[r-1][c] if r else float("inf")    # cost coming from above
            left = dp[r][c-1] if c else float("inf")    # cost coming from the left
            dp[r][c] = grid[r][c] + min(up, left)        # cheapest way to reach (r,c)
    return dp[m-1][n-1]

# --- MAXIMAL SQUARE: largest all-1s square in a binary matrix -----------
def maximal_square(matrix):
    m, n = len(matrix), len(matrix[0]); best = 0
    dp = [[0]*(n+1) for _ in range(m+1)]      # dp[r][c] = side of largest square ending at (r-1,c-1)
    for r in range(1, m+1):
        for c in range(1, n+1):
            if matrix[r-1][c-1] == "1":
                dp[r][c] = min(dp[r-1][c], dp[r][c-1], dp[r-1][c-1]) + 1   # limited by 3 neighbours
                best = max(best, dp[r][c])
    return best * best

# --- SPACE REDUCTION: keep one rolling row (O(n) instead of O(m*n)) -----
def unique_paths_1d(m, n):
    row = [1] * n
    for _ in range(1, m):
        for c in range(1, n):
            row[c] += row[c-1]                # row[c] (old = from above) + row[c-1] (from left)
    return row[-1]

# --- the recipe (same as 11.21, two-part state) -------------------------
# STATE (r,c) or (i,j) -> RECURRENCE from adjacent cells -> BASE first row/col (or empty prefix)
# -> FILL in dependency order (usually row by row) -> optionally collapse to a rolling row.
```

### Impact

- **Exponential → O(m×n):** filling the grid once, each cell from solved neighbours, eliminates
  the repeated recomputation of the naive recursion — the standard efficient grid/two-sequence
  solution.
- **O(n) space when rows roll:** since a row depends only on the previous one, a single rolling
  array replaces the full table on many problems.
- **Unifies grid and dual-sequence problems:** the same 2D template covers path counting/costing,
  maximal-square, and (with `(i,j)` over two strings) the entire edit-distance/LCS family (11.23).

### Pros & cons / when NOT to

**Reach for 2D DP when:** the optimum/count is over a **grid** or over **two indices/sequences**,
with overlapping subproblems and optimal substructure (the DP preconditions, 11.21).

**Watch out / when NOT to:**
- **Get the fill order right** — a cell must be computed *after* the cells it depends on. Row-by-
  row left-to-right works when dependencies are up/left; a different recurrence may need a
  different order (or memoization, which sidesteps ordering).
- **Initialise base cases (first row/column) correctly** — off-by-one or wrong edge values are
  the most common 2D-DP bug; many solutions use an extra padding row/column (size `n+1`) to
  avoid boundary special-cases (as in maximal-square).
- **Watch memory on large grids** — an m×n table can be big; collapse to a rolling row (O(n))
  when each row only reads the previous one.
- **If the state needs *more* than two dimensions, you need a higher-dimensional DP** — don't
  force a 2D table when the answer genuinely depends on three things (add the dimension, or
  reconsider the state).
- **It's still DP** — if there's no overlap or a greedy/closed-form works, don't build a table
  (11.21's caveats apply).

### Where this shows up

- **Interview classics:** Unique Paths (I/II), Minimum Path Sum, Maximal Square, Dungeon Game,
  Longest Common Subsequence & Edit Distance (11.23), Triangle, Cherry Pickup.
- **Real work (the crossover):** grid/matrix cost-optimisation, image processing (largest region/
  square), and — via the two-sequence form — **sequence alignment** (bioinformatics) and **diff/
  edit-distance** in version control, search, and spell-check (11.23).
- **Pattern mapping:** **1D DP** (11.21) extended to a two-part state; the two-sequence case *is*
  **string DP** (11.23); shares the memoization/tabulation machinery (1.13) and contrasts with
  greedy (11.24) and backtracking (11.20) as in 11.21.
[↑ Back to top](#contents)

---

<a id="11.23"></a>
## 11.23 — "Compare or align two sequences" → string DP (edit distance, LCS)

### The situation

*What's the minimum number of edits (insert, delete, replace) to turn word A into word B?*
(edit/Levenshtein distance — the engine behind spell-check and diff.) Or *the longest
subsequence common to two strings?*

```python
# "kitten" -> "sitting":  k→s (replace), e→i (replace), insert g  -> 3 edits
# comparing the strings character by character with branching choices (match? insert? delete?
# replace?) re-explores the same prefix pairs exponentially -> too slow
```

You're comparing **two** sequences, and at each position you have several choices whose
consequences overlap heavily across prefixes.

### What's really going on

Problems that **compare or align two sequences** — edit distance, longest common subsequence
(LCS), longest common substring, sequence alignment — are **2D DP (11.22)** where the state is a
pair of **prefix lengths** `(i, j)`: "the answer considering the first `i` characters of A and the
first `j` of B." The recurrence compares `A[i-1]` and `B[j-1]`: if they **match**, extend the
diagonal subproblem `(i-1, j-1)`; if not, take the best of the neighbouring subproblems (which
correspond to insert / delete / replace).

For **edit distance**: `dp[i][j]` = min edits to turn A's first `i` chars into B's first `j`. If
the characters match, no edit is needed → `dp[i-1][j-1]`; otherwise `1 + min(insert, delete,
replace)` = `1 + min(dp[i][j-1], dp[i-1][j], dp[i-1][j-1])`. Base cases: turning a length-`i`
string into "" takes `i` deletes (first column = `i`), and "" into length-`j` takes `j` inserts
(first row = `j`). It's a 2D table of size `(len(A)+1) × (len(B)+1)`, filled in O(m·n).

> **Trigger:** **compare/align/transform two sequences** — edit distance, LCS, longest common
> substring, "min operations to make A == B," diff. **Pattern:** **2D string DP** with state
> `(i, j)` = prefix lengths; recurrence branches on `A[i-1] == B[j-1]` (match → diagonal; mismatch
> → best of insert/delete/replace neighbours); base cases on empty prefixes (first row/column).
> **Result:** O(m·n) time, reducible to O(min(m,n)) space.

### The move

Build a `(m+1)×(n+1)` table over prefix lengths; branch on whether the current characters match:

```python
def edit_distance(a, b):
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(m+1): dp[i][0] = i          # base: a[:i] -> "" needs i deletes
    for j in range(n+1): dp[0][j] = j          # base: "" -> b[:j] needs j inserts
    for i in range(1, m+1):
        for j in range(1, n+1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1]         # match -> no edit, take the diagonal
            else:
                dp[i][j] = 1 + min(dp[i-1][j],      # delete from a
                                   dp[i][j-1],      # insert into a
                                   dp[i-1][j-1])    # replace
    return dp[m][n]
```

### Why it works

`dp[i][j]` answers a self-contained subproblem — "min edits between `a`'s first `i` and `b`'s
first `j` chars" — and the recurrence expresses every way to resolve the *last* position. If the
current characters match, that position costs nothing and the answer is the diagonal subproblem
`dp[i-1][j-1]`. If they differ, one edit fixes it, and the three neighbouring states correspond
exactly to the three operations: `dp[i-1][j]` (delete a char from `a`), `dp[i][j-1]` (insert
b's char), `dp[i-1][j-1]` (replace) — take the cheapest and add 1. The base cases are the empty-
prefix rows/columns (turning a string into "" is all deletes; "" into a string is all inserts).
Because every `(i,j)` pair is filled once from earlier cells, the exponentially-overlapping
character-comparison recursion collapses to **O(m·n)**. LCS is the same table shape with a
maximising recurrence instead of minimising.

### The code, every line explained

```python
# --- EDIT (Levenshtein) DISTANCE ----------------------------------------
def edit_distance(a, b):
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]       # dp[i][j] over PREFIX LENGTHS i, j
    for i in range(m+1): dp[i][0] = i          # a[:i] -> "" : i deletions
    for j in range(n+1): dp[0][j] = j          # "" -> b[:j] : j insertions
    for i in range(1, m+1):
        for j in range(1, n+1):
            if a[i-1] == b[j-1]:               # NOTE: a[i-1] is the i-th char (0-indexed)
                dp[i][j] = dp[i-1][j-1]        # characters match -> free, inherit diagonal
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])  # del / ins / replace
    return dp[m][n]                            # full strings = bottom-right cell

# --- LONGEST COMMON SUBSEQUENCE: same shape, MAXimise -------------------
def lcs(a, b):
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]       # base row/col 0 (empty prefix -> LCS 0)
    for i in range(1, m+1):
        for j in range(1, n+1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1    # match extends the common subsequence
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])   # drop one char from a or from b
    return dp[m][n]

# --- subsequence vs substring (a common confusion) ----------------------
# SUBSEQUENCE: keep relative order, chars need NOT be contiguous ("ace" in "abcde") -> the DP above
# SUBSTRING: contiguous run -> reset dp[i][j]=0 on mismatch, track the max (different recurrence)

# --- the index off-by-one (the #1 string-DP bug) ------------------------
# table is (m+1)x(n+1); dp[i][j] uses CHARACTERS a[i-1] and b[j-1] (1-indexed table, 0-indexed
# strings). Mixing these up is the classic mistake — keep "dp index = prefix LENGTH" in mind.

# --- space reduction: two rows -----------------------------------------
# each row depends only on the previous row -> keep two 1D arrays (prev, curr) -> O(min(m,n)) space.

# --- when it's NOT 2D string DP -----------------------------------------
# comparing for EXACT equality / substring search -> just == or str methods / KMP (no DP needed).
# "are they anagrams?" -> Counter (11.1), not alignment. DP is for ALIGNMENT/transformation cost.
```

### Impact

- **Exponential → O(m·n):** the prefix-pair table solves the heavily-overlapping alignment
  recursion once per `(i,j)` — making edit distance / LCS practical on real strings.
- **One template, the whole family:** edit distance, LCS, longest common substring, and sequence
  alignment are the same 2D prefix-pair DP with a match-vs-mismatch recurrence — learn it once.
- **Underpins real tools:** it's the literal algorithm behind spell-check suggestions, fuzzy
  matching, `diff`, and bioinformatics alignment.

### Pros & cons / when NOT to

**Reach for string DP when:** you must **align, compare, or transform two sequences** with a
cost/length objective — edit distance, LCS, alignment, "min ops to make equal."

**Watch out / when NOT to:**
- **Mind the index convention** — the table is indexed by **prefix length** (`dp[i][j]` over
  `a[:i]`, `b[:j]`), so the current characters are `a[i-1]`/`b[j-1]`. Mixing length-index with
  char-index is the single most common bug; keep them straight.
- **Subsequence ≠ substring** — subsequence keeps order but allows gaps (the `max` recurrence
  above); substring needs contiguity (reset to 0 on mismatch). Misreading the problem gives the
  wrong recurrence.
- **Initialise the base row/column** — the empty-prefix cases (`i` deletes / `j` inserts, or 0
  for LCS) are essential; forgetting them yields wrong answers.
- **For exact equality / plain substring search, don't use DP** — `==`, `in`, or KMP suffice;
  for "are they anagrams?" use a Counter (11.1). String DP is for *alignment/transformation cost*,
  not exact matching.
- **O(m·n) can be large for very long strings** — reduce to two rows (O(min(m,n)) space); for
  enormous inputs, specialised/banded alignment may be needed.

### Where this shows up

- **Interview classics:** Edit Distance, Longest Common Subsequence, Longest Common Substring,
  Delete Operation for Two Strings, Distinct Subsequences, Interleaving String, Regular
  Expression / Wildcard Matching.
- **Real work (the crossover):** spell-check & fuzzy matching, `diff`/version-control change
  detection, DNA/protein **sequence alignment** in bioinformatics, and record/entity matching by
  string similarity — the same edit-distance DP behind the fuzzy-similarity scenario in Area 4
  (4.6).
- **Pattern mapping:** a specialisation of **2D DP** (11.22) where the two dimensions are prefix
  lengths of two sequences; shares all the DP machinery (state/recurrence/base, 11.21) and the
  memoization tooling (1.13).
[↑ Back to top](#contents)

---

<a id="11.24"></a>
## 11.24 — "A locally-best choice is globally optimal" → greedy (and how to know it's safe)

### The situation

*Given activities with start/end times, select the maximum number that don't overlap.* DP
(11.21) could solve it, but there's a simpler rule — and the danger is *assuming* a simple rule
works when it doesn't:

```python
# activities: pick the most non-overlapping ones.
# greedy rule: always pick the activity that ENDS earliest among those still compatible.
# vs a tempting-but-WRONG greedy: "pick the shortest activity first" -> can be suboptimal!
# how do you know which greedy choice is actually correct?
```

The appeal of greedy is its simplicity; the trap is that an intuitive locally-best choice is
often *not* globally optimal, and a wrong greedy quietly returns suboptimal answers that pass
small examples.

### What's really going on

A **greedy algorithm** builds the answer by always taking the **locally-best choice** and never
reconsidering. It's simpler and faster than DP (11.21) — but it's only *correct* when the problem
has the **greedy-choice property**: a locally-optimal choice is guaranteed to lead to a globally-
optimal solution. When that holds, greedy beats DP; when it doesn't, greedy gives wrong answers,
and you need DP (which considers combinations of choices) instead.

For activity selection, the correct greedy is "**always pick the activity that ends earliest**
(among compatible ones)" — provably optimal, because finishing earliest leaves the most room for
the rest. The two skills are (1) *finding* the right greedy choice (often after **sorting** by
the right key, 1.15), and (2) *justifying* it — via an **exchange argument** (show any optimal
solution can be transformed to use the greedy choice without getting worse) or by finding a
**counterexample** that proves a candidate greedy wrong.

> **Trigger:** optimisation where a simple "always pick the best-looking option now" rule plausibly
> works — interval scheduling, Huffman coding, some coin systems, "minimum number of ___."
> **Pattern:** **greedy** — sort by the right key (1.15), then make the locally-optimal choice
> repeatedly. **Crucial:** it's correct **only** if the **greedy-choice property** holds — prove
> it (exchange argument) or disprove it (counterexample). If not, use **DP** (11.21). **Result:**
> usually O(n log n) (the sort).

### The move

Sort by the key that makes the locally-optimal choice safe, then greedily take compatible items:

```python
def max_activities(intervals):
    intervals.sort(key=lambda x: x[1])        # sort by END time (the correct greedy key)
    count, last_end = 0, float("-inf")
    for start, end in intervals:
        if start >= last_end:                  # compatible with what we've chosen
            count += 1; last_end = end          # take it; it ends earliest -> leaves most room
    return count
```

### Why it works

Sorting by **end time** and always taking the next compatible activity is provably optimal by an
**exchange argument**: consider any optimal selection; its first activity ends no earlier than the
greedy's first (which ends earliest of all), so swapping in the greedy choice can't reduce how
many fit afterwards — repeat the swap and you transform *any* optimum into the greedy solution
without losing count. That's the proof obligation greedy always carries: you must show the local
choice never forecloses a better global outcome. The "sort by *end*" detail is load-bearing —
the intuitive "pick the shortest" or "pick the earliest start" greedies have easy
counterexamples. Once the right key is found, the algorithm is a single O(n) sweep after an
O(n log n) sort; the hard part was never the code, it was *choosing and justifying* the greedy
rule.

### The code, every line explained

```python
# --- ACTIVITY SELECTION: max non-overlapping intervals ------------------
def max_activities(intervals):
    intervals.sort(key=lambda x: x[1])         # sort by END (proven-correct key, 1.15/11.7)
    count, last_end = 0, float("-inf")
    for start, end in intervals:
        if start >= last_end:                   # doesn't overlap the last chosen one
            count += 1; last_end = end           # greedily take it
    return count

# --- JUMP GAME: can you reach the last index? (greedy reach) ------------
def can_jump(nums):
    reach = 0
    for i, n in enumerate(nums):
        if i > reach: return False              # a gap we can't cross
        reach = max(reach, i + n)               # greedily extend the farthest reachable index
    return True

# --- the COIN-CHANGE caution: greedy ISN'T always right -----------------
# greedy "take the largest coin <= remaining" works for {1,5,10,25} (canonical systems)...
# ...but FAILS for coins {1,3,4}, amount 6: greedy -> 4+1+1 (3 coins); optimal -> 3+3 (2 coins).
# So coin change in GENERAL needs DP (11.21), NOT greedy. Always verify the greedy property!

# --- how to JUSTIFY (or kill) a greedy choice ---------------------------
# PROVE (exchange argument): show any optimal solution can be modified to include the greedy
#   choice without becoming worse -> greedy is safe.
# DISPROVE (counterexample): find ONE input where the locally-best choice loses -> greedy is
#   wrong; fall back to DP (11.21). Try small adversarial inputs before trusting a greedy.

# --- greedy vs DP, decided -------------------------------------------- 
# locally-optimal provably -> globally-optimal  -> GREEDY (simpler, faster: O(n log n))
# choices INTERACT; a local best can hurt later -> DP (11.21, considers combinations)
```

### Impact

- **Simpler and faster than DP when valid:** a sort + linear sweep (O(n log n)) replaces a DP
  table — the lighter solution whenever the greedy-choice property holds.
- **The justification skill matters more than the code:** knowing *why* a greedy is correct (or
  finding the counterexample that kills it) is what separates a right answer from a plausible
  wrong one — and is exactly what interviewers probe.
- **Underlies key algorithms:** Huffman coding, Kruskal's/Prim's MST, Dijkstra (11.18), and
  interval scheduling are all greedy at heart.

### Pros & cons / when NOT to

**Reach for greedy when:** an optimisation problem has a *provable* greedy-choice property —
interval scheduling, "minimum number of X to cover Y," Huffman/MST, reach/coverage problems.

**Watch out / when NOT to:**
- **Greedy is wrong unless the greedy-choice property holds** — this is the cardinal caveat.
  Always *prove* it (exchange argument) or *test* it against small adversarial inputs before
  trusting it; the general coin-change counterexample ({1,3,4}, 6) shows how a natural greedy
  silently fails.
- **If local choices interact (a good choice now can force a bad outcome later), use DP (11.21)**
  — greedy can't reconsider, so it loses when the optimum requires a non-locally-best step.
- **Choosing the right key is the whole problem** — activity selection works sorting by *end*,
  not *start* or *length*. The wrong sort key (1.15) gives a wrong greedy; this is where most
  greedy bugs live.
- **"It passes the examples" isn't a proof** — greedy bugs hide because small cases often work.
  Demand a justification or a stress-test against brute force before shipping a greedy.
- **Some problems blend both** — the feasibility check inside binary-search-on-answer (11.6) is
  often a greedy simulation; and Dijkstra (11.18) is greedy + a heap.

### Where this shows up

- **Interview classics:** Activity Selection / Non-overlapping Intervals (11.7), Jump Game I/II,
  Gas Station, Task Scheduler, Partition Labels, Minimum Number of Arrows, Huffman/Merge Stones.
- **Real work (the crossover):** scheduling and resource allocation (pick the next-finishing job,
  pack greedily), the greedy *feasibility checks* inside binary-search-on-answer planning (11.6),
  Dijkstra-based routing (11.18), and MST for network design — plus the everyday instinct to
  sort by the right key first (1.15/11.7).
- **Pattern mapping:** the simpler alternative to **DP** (11.21) when local optimality suffices;
  it powers **Dijkstra** (11.18) and **Kruskal's MST** (with union-find, 11.19); almost always
  preceded by **sorting** (1.15) and common in **interval** problems (11.7).
[↑ Back to top](#contents)

---

<a id="11.25"></a>
## 11.25 — "Prefix lookups, autocomplete, many-words matching" → tries

### The situation

*Build an autocomplete: given a typed prefix, find all stored words starting with it.* Or *check
many words against a dictionary efficiently.* A set (11.1) gives O(1) *exact* lookup but can't
answer *prefix* questions:

```python
words = {"car", "card", "care", "dog"}
# "is 'card' a word?" -> set handles this in O(1)
# "which words start with 'car'?" -> a set CAN'T do this without scanning ALL words (O(n·len))
```

Prefix queries — "starts with", "all completions of", "is any prefix of X a stored word" — are
what a hash set fundamentally can't do, because hashing destroys the shared-prefix structure.

### What's really going on

A **trie** (prefix tree) stores strings by **sharing common prefixes**: each node represents a
character, and a path from the root spells a prefix; words that share a prefix share the same
path until they diverge. This makes **prefix operations** natural and fast: searching for a
prefix is just walking down the tree character by character — **O(L)** where L is the prefix
length, *independent of how many words are stored*. From the node where a prefix ends, every word
in that subtree is a completion (autocomplete).

Each node holds a map of `child character → child node` and a flag marking whether a complete
word ends there. The trie's superpower is exactly what a hash set lacks: it preserves and
exploits **shared prefix structure**, so "all words starting with X," "is any stored word a
prefix of X," and "match many patterns at once" become tree walks rather than full scans.

> **Trigger:** **prefix**-based operations — autocomplete / "starts with," storing a dictionary
> for many prefix/word lookups, "is any prefix of X in the set," matching many words/patterns at
> once (word search, replace-words). **Pattern:** a **trie** (prefix tree) — nodes = characters,
> paths = prefixes, shared prefixes shared. **Result:** insert/search **O(L)** (word length),
> independent of the number of words — which a hash set (11.1) can't do for *prefix* queries.

### The move

Build a tree of `char → child` maps; insert/search by walking it character by character:

```python
class Trie:
    def __init__(self):
        self.root = {}                          # nested dicts; "$" marks end-of-word
    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})      # descend, creating the child if absent (1.20)
        node["$"] = True                         # mark a complete word ends here
    def search(self, word):
        node = self._walk(word)
        return node is not None and "$" in node  # exists AND a word ends exactly here
    def starts_with(self, prefix):
        return self._walk(prefix) is not None    # the prefix PATH exists -> some word has it
    def _walk(self, s):
        node = self.root
        for ch in s:
            if ch not in node: return None       # path breaks -> not present
            node = node[ch]
        return node
```

### Why it works

Insertion walks down from the root, reusing existing nodes for shared prefixes and creating new
ones only where words diverge — so "car", "card", "care" share the `c→a→r` path and branch after.
The `"$"` end-of-word marker distinguishes a *stored word* from a mere *prefix*: "car" being a
word and "card" extending it both coexist on the same path. **`search`** walks the path and checks
for `"$"` at the end (the exact word exists); **`starts_with`** just checks the path exists (some
word has that prefix) — the operation a hash set can't do, because hashing scatters the words and
loses the shared structure. Every operation costs **O(L)** in the query length, *not* O(number of
words), because you only traverse one root-to-node path. From a prefix's end node, a DFS (11.13)
of the subtree enumerates all completions — that's autocomplete.

### The code, every line explained

```python
# --- a compact dict-based trie (idiomatic Python) -----------------------
class Trie:
    def __init__(self):
        self.root = {}
    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})       # 1.20: get child, create {} if missing
        node["$"] = True                          # sentinel: a word ENDS here
    def search(self, word):                       # EXACT word present?
        node = self._walk(word)
        return node is not None and "$" in node
    def starts_with(self, prefix):                # any word with this PREFIX?
        return self._walk(prefix) is not None
    def _walk(self, s):
        node = self.root
        for ch in s:
            if ch not in node: return None        # prefix path doesn't exist
            node = node[ch]
        return node

# --- AUTOCOMPLETE: walk to the prefix, then DFS the subtree (11.13) -----
def completions(trie, prefix):
    node = trie._walk(prefix)
    if node is None: return []
    out = []
    def dfs(node, path):
        if "$" in node: out.append(prefix + path)     # a full word -> record it
        for ch, child in node.items():
            if ch != "$": dfs(child, path + ch)
    dfs(node, "")
    return out

# --- when a SET beats a trie --------------------------------------------
# EXACT membership only ("is X a word?") -> a set/dict (11.1) is O(1) and simpler.
# reach for a trie ONLY when you need PREFIX queries / autocomplete / many-pattern matching;
# a trie for plain exact lookup is over-engineering (and uses more memory).

# --- memory note --------------------------------------------------------
# a trie can use lots of memory (a node per character per branch). for huge dictionaries,
# compressed tries (radix trees) or other structures trade some simplicity for space.
```

### Impact

- **Fast prefix queries a hash set can't do:** "starts with," autocomplete completions, and
  "any prefix of X stored?" become O(L) tree walks, independent of dictionary size.
- **Shared-prefix efficiency:** common prefixes are stored once, and matching many words against
  text can be done in a single pass over the trie.
- **Natural autocomplete/spell structures:** the subtree-from-prefix DFS directly yields all
  completions — the backbone of search suggestions.

### Pros & cons / when NOT to

**Reach for a trie when:** you need **prefix** operations — autocomplete, "starts with," storing
a dictionary for repeated prefix/word queries, "is any prefix of X present," or matching many
words/patterns against text.

**Watch out / when NOT to:**
- **For exact membership only, use a set/dict (11.1)** — it's O(1) and far simpler; a trie's
  advantage is *prefix* structure. Using a trie for plain "is X in the set?" is over-engineering.
- **Tries use significant memory** — potentially a node per character per branch. For very large
  dictionaries, consider a compressed trie (radix tree) or accept the space cost deliberately.
- **Mark end-of-words explicitly** (the `"$"` sentinel) — without it you can't tell a stored word
  from a prefix of a longer word ("car" vs the "car" inside "card"); forgetting the marker is the
  classic trie bug.
- **It's for string/sequence prefixes** — not a general-purpose ordered structure; for ordered
  numeric ranges use a BST/sorted structure (11.15), for exact keys a hash map (11.1).
- **Don't hand-roll when a library/regex suffices** — for a one-off "does text contain any of
  these words," a set of words or a regex may be simpler than building a trie; reach for the trie
  when prefix queries or many-pattern matching are the *repeated* core need.

### Where this shows up

- **Interview classics:** Implement Trie (Prefix Tree), Word Search II (trie + DFS over a grid,
  11.16/11.20), Add and Search Word (wildcards), Replace Words, Longest Word in Dictionary,
  Maximum XOR of Two Numbers (a *bit* trie, 11.26).
- **Real work (the crossover):** autocomplete and search suggestions, spell-checkers and fuzzy
  prefix matching, IP routing tables (longest-prefix match), and multi-keyword/pattern matching
  in text (the prefix-structure cousin of the exact-match hashing in 11.1/Area 3).
- **Pattern mapping:** a tree (so DFS/BFS, 11.13/11.14, traverse it) specialised for string
  prefixes; the prefix-query alternative to **hashing** (11.1, exact only); built with the
  `setdefault`/nested-dict idiom (1.20).
[↑ Back to top](#contents)

---

<a id="11.26"></a>
## 11.26 — "Flip, test, or combine bits / track a set of flags compactly" → bit manipulation

### The situation

*In an array where every number appears twice except one, find the single number — in O(1)
space.* Or *track which of N items are selected using a single integer.* The obvious solutions
use extra memory:

```python
def single_number(nums):
    counts = Counter(nums)              # O(n) extra space (11.1)
    return next(x for x, c in counts.items() if c == 1)
# works, but there's an O(1)-SPACE trick using XOR — and a whole class of problems hinges on it
```

A hash/Counter solves it but uses O(n) space; certain problems specifically want O(1) space or
have a clean bitwise structure that a value-level approach misses.

### What's really going on

**Bit manipulation** operates on the binary representation of integers directly, using bitwise
operators. The key ones: **AND `&`**, **OR `|`**, **XOR `^`**, **NOT `~`**, and shifts **`<<` /
`>>`**. A few identities unlock a class of problems:

- **XOR**: `x ^ x = 0`, `x ^ 0 = x`, and it's commutative — so XOR-ing *all* numbers cancels the
  pairs and leaves the unique one (the "single number" trick, O(1) space).
- **A bitmask as a set of flags**: each bit position is a boolean; one integer compactly stores N
  on/off flags. Set bit i: `mask | (1 << i)`; test bit i: `mask & (1 << i)`; clear bit i:
  `mask & ~(1 << i)`. This is how **bitmask DP** represents "which subset is visited."
- **Handy tricks**: `n & (n-1)` clears the lowest set bit (count set bits, or test power-of-two);
  `n & 1` tests odd/even.

The trigger is recognising binary structure: "appears twice except one," "subsets via a mask,"
"count/toggle bits," "power of two." It's niche but, when it applies, gives O(1)-space or elegant
solutions that value-level code can't.

> **Trigger:** problems with **binary structure** — "every element twice except one" (XOR),
> tracking a **set of flags/subset in one int** (bitmask, incl. bitmask DP), counting/toggling
> bits, power-of-two checks. **Pattern:** bitwise ops — **XOR** to cancel pairs, **`1<<i`** masks
> to set/test/clear flags, **`n&(n-1)`** to strip the lowest bit. **Result:** often **O(1) space**
> or O(1)/O(bits) operations where a value-level approach needs more.

### The move

Use the bitwise identity that matches the structure — e.g. XOR everything to cancel pairs:

```python
def single_number(nums):
    result = 0
    for x in nums:
        result ^= x            # pairs cancel (x ^ x = 0); the lone number survives
    return result              # O(n) time, O(1) SPACE — no Counter needed
```

### Why it works

XOR has two properties that make this exact: `x ^ x = 0` (a value XOR'd with itself vanishes) and
`x ^ 0 = x`, and it's order-independent. So XOR-ing the whole array pairs up every duplicated
value into 0s, and the single un-paired number XOR'd against all those 0s is left standing — in a
single pass with **one integer of state** (O(1) space), beating the Counter's O(n) space. The
bitmask techniques work because an integer *is* a vector of bits: `1 << i` is a mask with only bit
`i` set, so OR-ing sets that flag, AND-ing tests it, and AND-with-complement clears it — letting
one `int` stand in for an array of N booleans (the representation behind bitmask DP, where the
"state" is *which subset has been visited*). The whole pattern is recognising that the problem's
structure lives in the bits, then reaching for the operator that manipulates them directly.

### The code, every line explained

```python
# --- XOR: find the unique number (pairs cancel) -------------------------
def single_number(nums):
    result = 0
    for x in nums:
        result ^= x                  # x ^ x = 0 -> duplicates cancel; the single one remains
    return result

# --- BITMASK as a set of flags ------------------------------------------
mask = 0
mask |= (1 << 3)                     # SET bit 3  (turn flag 3 on)
on   = bool(mask & (1 << 3))         # TEST bit 3 (is flag 3 set?)
mask &= ~(1 << 3)                    # CLEAR bit 3 (turn flag 3 off)
mask ^= (1 << 3)                     # TOGGLE bit 3
# one int now compactly stores up to ~word-size boolean flags.

# --- count set bits & power-of-two (the n&(n-1) trick) ------------------
def count_bits(n):
    c = 0
    while n:
        n &= n - 1                   # clears the LOWEST set bit each iteration
        c += 1                       # ...so loops exactly (number of set bits) times
    return c
def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0   # powers of two have exactly ONE set bit
# (Python also has int.bit_count() / bin(n).count("1") for counting set bits.)

# --- BITMASK DP: "which subset is visited" as the state (e.g. TSP) ------
# dp[mask][i] = best cost having visited the set `mask`, currently at node i.
# transition: dp[mask | (1<<j)][j] = min(..., dp[mask][i] + dist[i][j])  for j not in mask.
# the integer `mask` IS the subset -> 2^n subsets enumerated compactly. (Niche but powerful.)

# --- common gotchas -----------------------------------------------------
# - Python ints are ARBITRARY precision and `~x` = -(x+1) (two's complement, no fixed width).
#   For fixed-width behaviour (e.g. 32-bit), mask explicitly: x & 0xFFFFFFFF.
# - operator precedence: & | ^ bind LOOSELY -> parenthesise: (mask & (1<<i)) == 0, not
#   mask & (1<<i) == 0 (which parses as mask & ((1<<i)==0)). A classic silent bug.

# --- when NOT to reach for bits -----------------------------------------
# if a Counter/set (11.1) solves it clearly and space isn't constrained, prefer that —
# bit tricks are LESS READABLE. Use them when O(1) space, subset-state, or bit structure
# is genuinely the point, not to show off.
```

### Impact

- **O(1)-space solutions:** XOR-style cancellation solves "unique among pairs" with a single
  variable, where hashing needs O(n) — the canonical bit-trick win.
- **Compact state:** a bitmask packs N booleans (or a visited-subset) into one integer, enabling
  bitmask DP over 2ⁿ subsets that an explicit set couldn't represent as cheaply.
- **Fast bit-level ops:** `n & (n-1)`, shifts, and masks give O(1)/O(bits) building blocks for
  counting, toggling, and power-of-two checks.

### Pros & cons / when NOT to

**Reach for bit manipulation when:** the problem has genuine binary structure — XOR
cancellation ("twice except one"), subset/flag state in one integer (bitmask DP), bit counting/
toggling, or power-of-two/parity checks.

**Watch out / when NOT to:**
- **Readability cost** — bit tricks are terse and easy to misread. If a `set`/`Counter` (11.1)
  solves it clearly and space isn't tight, prefer that; reach for bits when O(1) space or
  subset-state is the actual requirement, not to be clever.
- **Operator precedence bites** — `&`/`|`/`^` bind *looser* than `==`; always parenthesise
  (`(mask & bit) == 0`). This is a classic silent bug.
- **Python ints are arbitrary-precision** — `~x` is `-(x+1)`, not a fixed-width complement; for
  32/64-bit semantics, mask explicitly (`& 0xFFFFFFFF`). Don't assume C-style overflow.
- **Bitmask DP is exponential in the number of bits** (2ⁿ subsets) — only viable for small n
  (~≤ 20). For larger, the subset-state approach is infeasible; rethink the problem.
- **Use built-ins when they're clearer** — `int.bit_count()`, `bin(n).count("1")`, `x & 1` for
  parity — don't hand-roll what the language gives you.

### Where this shows up

- **Interview classics:** Single Number (I/II/III), Number of 1 Bits, Counting Bits, Power of
  Two, Missing Number (XOR), Sum of Two Integers (no `+`), Maximum XOR (bit trie, 11.25),
  Subsets via bitmask, Travelling Salesman / bitmask DP.
- **Real work (the crossover):** compact flag sets and permission bitfields, feature toggles
  packed into an integer, fast set operations on small universes, hashing/checksums, and
  low-level/systems code — niche in day-to-day ML/data work, but the XOR and mask idioms appear
  in serialization, dedup fingerprints, and bit-packed storage.
- **Pattern mapping:** mostly standalone bit-level tricks; the bitmask-as-set powers **bitmask
  DP** (a 11.21 variant) and the bit **trie** (11.25); contrasts with hashing (11.1) as the
  O(1)-space / compact-state alternative for specific structures.
[↑ Back to top](#contents)

---

<a id="11.27"></a>
## 11.27 — "Walk or transform a matrix in a specific pattern" → matrix traversal

### The situation

*Return the elements of an m×n matrix in spiral order.* Or *rotate an n×n image 90° in place.*
These aren't algorithmically deep — they're about **carefully managing 2D indices** without
going out of bounds or losing track of direction:

```python
matrix = [[1,2,3],
          [4,5,6],     # spiral order: 1,2,3,6,9,8,7,4,5
          [7,8,9]]
# the difficulty is purely INDEX bookkeeping: when to turn, where the boundaries are, off-by-one
```

The trap is index errors — off-by-one boundaries, wrong turn conditions, double-visiting the
centre — not any clever algorithm.

### What's really going on

**Matrix/grid traversal** problems test disciplined **2D index management**: visiting cells in a
prescribed order (spiral, diagonal), transforming positions (rotate, transpose, reflect), or
moving in directions (the neighbour-stepping that graph/grid BFS-DFS, 11.16, also uses). There's
rarely a deep "pattern" — the skill is choosing a clean representation of position and direction
so the bookkeeping stays correct.

Two reusable techniques tame the index soup: (1) **boundary shrinking** for spirals — track
`top/bottom/left/right` edges and move them inward as you complete each side; (2) **direction
vectors** for movement — a list of `(dr, dc)` deltas you cycle through, so "turn" is just
"advance to the next delta" instead of four hard-coded branches. For in-place transforms like
rotate, the trick is a **decomposition** into simpler steps (rotate 90° = transpose, then reverse
each row).

> **Trigger:** traverse/transform a **2D matrix in a specific pattern** — spiral order, diagonal
> traversal, rotate/transpose/reflect, set-matrix-zeroes, search a sorted matrix. **Pattern:**
> disciplined index management — **boundary shrinking** (spiral), **direction vectors `(dr,dc)`**
> (movement/turning), or **decompose a transform** (rotate = transpose + reverse rows).
> **Result:** O(m·n) (visit each cell once); the challenge is correctness, not complexity.

### The move

Track shrinking boundaries (spiral) or decompose the transform into simple steps (rotate):

```python
def spiral_order(matrix):
    if not matrix: return []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    res = []
    while top <= bottom and left <= right:
        for c in range(left, right + 1): res.append(matrix[top][c])     # → top row
        top += 1
        for r in range(top, bottom + 1): res.append(matrix[r][right])   # ↓ right col
        right -= 1
        if top <= bottom:                                                # guard: row left?
            for c in range(right, left - 1, -1): res.append(matrix[bottom][c])  # ← bottom row
            bottom -= 1
        if left <= right:                                                # guard: col left?
            for r in range(bottom, top - 1, -1): res.append(matrix[r][left])    # ↑ left col
            left += 1
    return res
```

### Why it works

The four boundaries (`top/bottom/left/right`) delimit the unvisited rectangle. Each pass traces
one side — top row left-to-right, right column top-to-bottom, bottom row right-to-left, left
column bottom-to-top — then **shrinks** that boundary inward, so the rectangle gets smaller each
loop and the spiral converges to the centre. The two `if` guards before the bottom row and left
column are essential: in a single remaining row or column, the first two passes already consumed
it, and without the guard you'd re-traverse cells (the classic spiral double-visit bug). The
`while top <= bottom and left <= right` stops exactly when the rectangle is empty. For rotation,
the insight is **decomposition**: rotating 90° clockwise equals transposing (swap `m[i][j]` with
`m[j][i]`) then reversing each row — two simple, individually-correct steps compose into the
transform, far less error-prone than computing rotated indices directly.

### The code, every line explained

```python
# --- ROTATE an n×n matrix 90° clockwise, IN PLACE -----------------------
def rotate(matrix):
    n = len(matrix)
    for i in range(n):                       # STEP 1: transpose (reflect over the diagonal)
        for j in range(i + 1, n):            # j > i so each pair swapped ONCE (not back again)
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    for row in matrix:                       # STEP 2: reverse each row
        row.reverse()
    # transpose + reverse-rows == rotate 90° clockwise. Decomposition beats index arithmetic.

# --- DIRECTION VECTORS: clean movement / turning ------------------------
DIRS = [(0,1),(1,0),(0,-1),(-1,0)]           # right, down, left, up (clockwise)
def walk(matrix):                            # generic pattern: step, turn by cycling dirs
    r = c = d = 0
    for _ in range(len(matrix) * len(matrix[0])):
        # ... use matrix[r][c] ...
        nr, nc = r + DIRS[d][0], c + DIRS[d][1]
        if not (0 <= nr < len(matrix) and 0 <= nc < len(matrix[0])) or visited(nr, nc):
            d = (d + 1) % 4                  # TURN = advance to the next direction vector
            nr, nc = r + DIRS[d][0], c + DIRS[d][1]
        r, c = nr, nc
# the same DIRS trick drives grid BFS/DFS neighbour-stepping (11.16).

# --- SET MATRIX ZEROES in place: use first row/col as markers -----------
# naive: O(m·n) extra space to remember which rows/cols to zero. trick: use row 0 and col 0
# themselves as the marker storage -> O(1) extra space. (a representation choice, not an algo.)

# --- the bug sources (this whole pattern is bug-avoidance) --------------
# - off-by-one in range bounds (right+1, left-1) — trace a 1xN and Nx1 matrix by hand
# - spiral DOUBLE-VISIT: forgetting the `if top<=bottom` / `if left<=right` guards on a single
#   leftover row/column
# - transpose: loop j from i+1 (not 0) or you swap every pair twice and undo the transpose
# - confusing matrix[row][col] order, and (rows, cols) = (len(m), len(m[0]))

# --- when it's actually a GRAPH problem ---------------------------------
# "shortest path / connected regions / flood fill in a grid" is NOT this pattern — that's grid
# BFS/DFS (11.16). This scenario is fixed-PATTERN traversal/transform, not search.
```

### Impact

- **Correct, off-by-one-free 2D code:** boundary shrinking and direction vectors turn fiddly
  index juggling into a disciplined, debuggable structure — the actual challenge in these
  problems.
- **In-place transforms via decomposition:** expressing rotate as transpose + reverse (or
  reflect) gives O(1)-space, easy-to-verify steps instead of brittle rotated-index formulas.
- **Reusable movement toolkit:** the `(dr,dc)` direction-vector idiom serves both pattern
  traversal here and neighbour-stepping in grid BFS/DFS (11.16).

### Pros & cons / when NOT to

**Reach for matrix-traversal techniques when:** you must visit/transform a 2D array in a
prescribed pattern — spiral/diagonal order, rotate/transpose/reflect, in-place marker tricks.

**Watch out / when NOT to:**
- **This is bug-avoidance, not algorithm design** — the difficulty is purely index correctness.
  Trace small/edge shapes (1×N, N×1, 1×1, empty) by hand; that's where off-by-one and
  double-visit bugs hide.
- **Spiral needs the single-row/column guards** — without `if top <= bottom` / `if left <=
  right`, a lone leftover row or column gets traversed twice. The #1 spiral bug.
- **Transpose only the upper triangle** (`j` from `i+1`) — looping all `j` swaps each pair twice
  and undoes the transpose.
- **Decompose transforms** — rotate = transpose + reverse rows; reflect/transpose are simpler
  than direct rotated-index math and far less error-prone. Don't compute `new[i][j] = old[...]`
  by hand if a decomposition exists.
- **If it's search/connectivity in a grid, it's a graph problem (11.16), not this** — flood
  fill, shortest path, islands use BFS/DFS + visited; this scenario is fixed-pattern
  traversal/transform.
- **Mind `(rows, cols)` vs `(x, y)`** — keep `matrix[row][col]` straight and derive bounds as
  `len(matrix)` / `len(matrix[0])`; transposed indexing is a constant source of confusion.

### Where this shows up

- **Interview classics:** Spiral Matrix (I/II), Rotate Image, Set Matrix Zeroes, Diagonal
  Traverse, Transpose Matrix, Search a 2D Matrix (binary search, 11.5), Game of Life (in-place
  state update).
- **Real work (the crossover):** image/grid transforms (rotate/flip/transpose) in graphics and
  data preprocessing, working with 2D arrays/tensors (the shape/index discipline overlaps tensor
  reshaping, 9.1), and any tabular/grid layout manipulation — the careful index management
  carries over.
- **Pattern mapping:** mostly standalone index discipline; shares the **direction-vector**
  neighbour-stepping with grid **BFS/DFS** (11.16), uses **binary search** (11.5) for sorted
  matrices, and the index-bookkeeping mindset mirrors tensor-shape reasoning (9.1).
[↑ Back to top](#contents)

---

<a id="11.28"></a>
## 11.28 — "Break a problem into a smaller version of itself" → recursion fundamentals

### The situation

Recursion underlies half this area — DFS (11.13), backtracking (11.20), DP (11.21), divide-and-
conquer — yet it's where beginners most often get stuck: either the function never stops, or it
"feels like magic" and they can't reason about it:

```python
def factorial(n):
    return n * factorial(n - 1)        # BUG: no base case -> recurses forever -> RecursionError
# the fix and the whole mental model hinge on TWO things every recursion needs
```

Without a clear mental model, recursive code is written by trial and error and debugged by hope.

### What's really going on

**Recursion** is solving a problem by **calling the function on a smaller version of itself**,
until the problem is small enough to answer directly. Every correct recursion has exactly two
parts: a **base case** (the smallest input, answered without recursing — this *stops* the
recursion) and a **recursive case** (reduce the problem toward the base case and combine).
Factorial: base `factorial(0) = 1`; recursive `n * factorial(n-1)`.

The mental model that dissolves the "magic": **trust that the recursive call returns the correct
answer for the smaller input** (the "recursive leap of faith"), and just specify how to combine
it. You don't trace every level in your head — you verify the base case is correct and the
combine step is correct, and induction does the rest. Two practical realities: each call uses a
**stack frame**, so deep recursion costs O(depth) memory and can hit Python's **recursion limit**
(~1000); and recursion with **overlapping** subproblems needs memoization to avoid exponential
recompute (that's DP, 11.21).

> **Trigger:** the problem **decomposes into a smaller instance of itself** — trees/graphs
> (11.13/11.16), divide-and-conquer (merge/quick sort), backtracking (11.20), DP (11.21), nested
> structures. **Pattern:** a **base case** (stops recursion) + a **recursive case** (shrink toward
> the base and combine), trusting the recursive call is correct. **Watch:** O(depth) stack (limit
> ~1000); memoize overlapping calls (→ DP). It's the foundation under most of Area 11.

### The move

Write the base case first (when to stop), then the recursive case (shrink and combine):

```python
def factorial(n):
    if n <= 1:                 # BASE CASE: smallest input, answer directly -> STOPS recursion
        return 1
    return n * factorial(n - 1)  # RECURSIVE CASE: reduce toward base, combine the smaller answer
```

### Why it works

The base case (`n <= 1 → 1`) is the floor the recursion descends to, and it's what makes the
recursion *terminate* — every recursive call (`factorial(n-1)`) moves strictly toward it, so the
chain `n, n-1, …, 1` is finite. The recursive case assumes `factorial(n-1)` already returns the
correct answer for the smaller problem (the leap of faith) and just specifies the combine
(`n × that`). You verify correctness by induction: the base case is right, and *if* the smaller
call is right *then* the combine is right — so all of them are right. You never have to mentally
unfold all the levels. Under the hood, each call pushes a **stack frame** holding its local
state; when the base case returns, the frames unwind, each completing its combine — which is why
recursion costs O(depth) memory and why a missing/unreachable base case blows the stack.

### The code, every line explained

```python
# --- the recursion skeleton (every recursive function) ------------------
def recurse(problem):
    if is_base_case(problem):          # 1. BASE CASE first — when to STOP (no recursion)
        return base_answer
    smaller = reduce(problem)          # 2. shrink toward the base case
    return combine(recurse(smaller))   # 3. trust the recursive call; combine its result

# --- DIVIDE & CONQUER: split, solve halves, merge (merge sort) ----------
def merge_sort(a):
    if len(a) <= 1:                    # base: 0 or 1 element is already sorted
        return a
    mid = len(a) // 2
    left  = merge_sort(a[:mid])        # solve each HALF (smaller subproblems)
    right = merge_sort(a[mid:])
    return merge(left, right)          # combine: merge two sorted halves (two pointers, 11.2)
# O(n log n): log n levels of splitting, O(n) merge work per level.

# --- recursion vs ITERATION: the same loop, two forms -------------------
def sum_list(a):
    if not a: return 0                 # base: empty list sums to 0
    return a[0] + sum_list(a[1:])      # recursive — but O(n) STACK frames + O(n) slicing!
# a simple loop is better here: sum(a) / a for-loop -> O(1) stack. Use recursion when the
# problem is genuinely recursive (trees, branching), not for plain linear iteration.

# --- DEEP recursion: Python's limit (~1000) -----------------------------
import sys
# sys.setrecursionlimit(10000)         # can raise it, but risks a real stack overflow/crash
# better: convert to ITERATIVE with an explicit stack (the technique used in 11.13/11.16)
def factorial_iter(n):
    result = 1
    for i in range(2, n + 1): result *= i   # no recursion -> no stack-depth limit
    return result

# --- OVERLAPPING subproblems -> memoize (this becomes DP, 11.21) --------
from functools import lru_cache
@lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n-1) + fib(n-2)   # without @lru_cache this is O(2^n) (11.21)

# --- the two cardinal rules ---------------------------------------------
# 1. ALWAYS have a reachable base case, and ensure each call moves TOWARD it (or infinite
#    recursion -> RecursionError). this is the #1 recursion bug.
# 2. trust the recursive call ("leap of faith"): verify base + combine, don't trace every level.
```

### Impact

- **Expresses recursive problems directly:** trees, divide-and-conquer, backtracking, and nested
  structures map onto base-case + recursive-case far more cleanly than manual iteration —
  shorter, clearer code.
- **The mental model unblocks the rest of Area 11:** DFS (11.13), backtracking (11.20), and DP
  (11.21) are all "recursion + something"; getting base-case/recursive-case fluent makes them
  approachable instead of magic.
- **Composes with memoization:** adding a cache (1.13) to a recursion turns exponential into
  polynomial — the bridge from naive recursion to DP.

### Pros & cons / when NOT to

**Reach for recursion when:** the problem genuinely decomposes into smaller instances of itself —
trees/graphs (11.13/11.16), divide-and-conquer, backtracking (11.20), DP (11.21), nested/
hierarchical data (Area 3's "walk nested JSON").

**Watch out / when NOT to:**
- **Always have a reachable base case, and shrink toward it** — the #1 recursion bug is a missing
  or never-reached base case → infinite recursion → `RecursionError`. Check it first.
- **Mind the stack-depth limit (~1000 in Python)** — deep/linear recursion overflows; convert to
  an **iterative** form with an explicit stack (as in 11.13/11.16) for large depths, or use
  iteration for plain linear loops.
- **Don't recurse for simple linear iteration** — `sum_list` via recursion is O(n) stack + slicing
  overhead; a loop is O(1) stack. Recursion earns its keep on *branching*/recursive structure,
  not flat sequences.
- **Memoize overlapping subproblems** — naive recursion with repeated subproblems is exponential
  (11.21); add `@lru_cache` (1.13) or you'll TLE. If there's no overlap, no memoization needed.
- **Trust the recursive call** — reason by base + combine (induction), don't try to trace every
  level in your head; over-tracing is how recursion *feels* hard when it isn't.

### Where this shows up

- **Interview classics:** factorial/Fibonacci, merge sort & quick sort, all tree problems
  (11.13/11.14), backtracking (11.20), top-down DP (11.21), Tower of Hanoi, generating
  permutations/subsets, parsing nested expressions.
- **Real work (the crossover):** walking nested/recursive structures — nested JSON/config, file
  systems, the DOM/ASTs (Area 3's recursion scenario) — and divide-and-conquer in libraries
  (sorting, parsers); the memoization habit is the everyday `@lru_cache` (1.13).
- **Pattern mapping:** the foundation beneath **DFS** (11.13/11.16), **backtracking** (11.20),
  **DP** (11.21–11.23), and divide-and-conquer; pairs with memoization (1.13) to become DP; its
  iterative form uses an explicit **stack** (11.10/11.13).
[↑ Back to top](#contents)

---

<a id="11.29"></a>
## 11.29 — "Generate all subsets / permutations / combinations" → combinatorial enumeration

### The situation

You need to produce *every* arrangement or selection: *all subsets of a set*, *all permutations
of a list*, *all k-combinations*, *the cartesian product of several lists*. It's easy to confuse
which is which, and to reinvent generation logic that the standard library already provides:

```python
# subsets of [1,2,3]:        [], [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]   (2^3 = 8)
# permutations of [1,2,3]:   [1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]   (3! = 6)
# combinations of 2 from 3:  [1,2],[1,3],[2,3]                                 (C(3,2) = 3)
# these are DIFFERENT counts and shapes — picking the wrong one is a common bug
```

The trap is muddling subsets vs permutations vs combinations (order matters? size fixed?
repetition?), and hand-rolling generation that `itertools` does correctly and efficiently.

### What's really going on

**Combinatorial enumeration** generates structured arrangements, and the first job is naming
which structure you need — the distinctions are precise:

- **Subsets (power set)**: every possible selection, any size — `2ⁿ` of them; order doesn't
  matter.
- **Permutations**: all orderings of the elements — `n!`; order *does* matter.
- **Combinations**: all selections of a *fixed size* k — `C(n,k)`; order doesn't matter.
- **Cartesian product**: pick one from each of several lists — `∏ lengths`.

You can generate each by **backtracking** (11.20) — and should understand that — but Python's
**`itertools`** (1.12) provides `combinations`, `permutations`, `product`, and
`combinations_with_replacement` ready-made: correct, lazy, and efficient. Know the hand-rolled
backtracking form for when you need *custom pruning* or to build solutions incrementally; reach
for `itertools` for plain generation. Either way, these spaces are **exponential/factorial**, so
enumeration is only viable for small inputs (and is often a sign DP/greedy is the real intended
solution for large ones).

> **Trigger:** "generate **all** subsets / permutations / combinations / the cartesian product."
> **Pattern:** first identify the structure (order? fixed size? repetition?) — subsets (2ⁿ),
> permutations (n!), combinations (C(n,k)), product (∏). **Generate** via `itertools` (1.12) for
> plain cases, or **backtracking** (11.20) when you need pruning/custom build. **Caveat:**
> exponential/factorial — small inputs only.

### The move

Use `itertools` for plain generation; reach for backtracking (11.20) when you need custom
pruning:

```python
from itertools import combinations, permutations, product, chain

nums = [1, 2, 3]
list(permutations(nums))            # all orderings (n!): (1,2,3),(1,3,2),...
list(combinations(nums, 2))         # all size-2 selections: (1,2),(1,3),(2,3)
list(product([0,1], repeat=3))      # cartesian product: (0,0,0),(0,0,1),...,(1,1,1)
# power set (all subsets) = combinations of every size:
subsets = list(chain.from_iterable(combinations(nums, r) for r in range(len(nums)+1)))
```

### Why it works

`itertools` implements each structure correctly and lazily: `permutations` yields every ordering,
`combinations(nums, r)` yields every size-`r` selection (order-independent, no repeats),
`product(..., repeat=k)` yields one-from-each (the nested-loops cartesian product), and
`combinations_with_replacement` allows repeats. The **power set** is just the union of
combinations of all sizes 0..n — hence the `chain.from_iterable` over every `r`. These are lazy
generators (1.2/1.12), so they don't build the whole (possibly huge) list in memory unless you
ask. Knowing the *counts* (2ⁿ, n!, C(n,k)) both tells you which structure the problem wants and
warns you when enumeration is infeasible. The backtracking form (11.20) produces the same sets
but lets you *prune* mid-generation (abandon partial selections that can't be valid) — which
`itertools` can't, since it generates blindly.

### The code, every line explained

```python
from itertools import combinations, permutations, product, combinations_with_replacement, chain

nums = [1, 2, 3]

# --- the four structures, by what they mean -----------------------------
list(permutations(nums))                 # ORDER matters, use ALL -> n! arrangements
list(permutations(nums, 2))              # ordered selections of size 2 (n!/(n-k)!)
list(combinations(nums, 2))              # ORDER doesn't matter, fixed size 2 -> C(n,2)
list(combinations_with_replacement(nums, 2))  # combinations allowing repeats: (1,1),(1,2),...
list(product([0,1], [0,1]))              # one from each list -> (0,0),(0,1),(1,0),(1,1)
list(product([0,1], repeat=3))           # product of a list with itself 3x (all 3-bit strings)

# --- POWER SET (all subsets) = combinations of EVERY size 0..n ----------
def power_set(items):
    return list(chain.from_iterable(combinations(items, r) for r in range(len(items)+1)))
# also: each subset maps to an n-bit number -> bitmask enumeration (11.26):
def power_set_bits(items):
    n = len(items)
    return [[items[i] for i in range(n) if mask & (1 << i)] for mask in range(1 << n)]

# --- BACKTRACKING form: when you need PRUNING / custom build (11.20) ----
def subsets(nums):
    res, path = [], []
    def bt(start):
        res.append(path[:])
        for i in range(start, len(nums)):
            # could PRUNE here (e.g. skip if path-sum exceeds a target) — itertools can't
            path.append(nums[i]); bt(i + 1); path.pop()
    bt(0); return res

# --- which one? a decision checklist ------------------------------------
# order matters & use all      -> permutations         (n!)
# order matters & choose k     -> permutations(_, k)
# order doesn't matter, size k -> combinations         (C(n,k))
# any size, order doesn't      -> power set / subsets  (2^n)
# one from each of several sets-> product              (prod of lengths)
# repeats allowed              -> *_with_replacement / product(repeat=)

# --- the scale warning --------------------------------------------------
# permutations of 12 items = 479 MILLION; subsets of 30 = a billion. ENUMERATION is only for
# SMALL inputs. if n is large and you need a COUNT or OPTIMUM (not every arrangement), it's
# almost certainly a DP (11.21) or combinatorial-formula problem, NOT enumeration.
```

### Impact

- **Correct, ready-made generation:** `itertools` gives bug-free, lazy enumeration of each
  structure — no hand-rolled (and easily wrong) generation logic.
- **Clear structure choice:** naming subsets vs permutations vs combinations (and their counts)
  prevents the classic "generated the wrong thing" bug and sets expectations on feasibility.
- **Pruning when needed:** the backtracking form (11.20) generates the same spaces but can abandon
  invalid partials early — essential when most arrangements are invalid.

### Pros & cons / when NOT to

**Reach for combinatorial enumeration when:** you must produce *all* arrangements/selections of a
**small** input — subsets, permutations, combinations, cartesian products.

**Watch out / when NOT to:**
- **Pick the right structure** — order vs no-order, fixed size vs any size, repeats vs not. The
  most common bug is generating permutations when you wanted combinations (or subsets). Use the
  decision checklist.
- **Use `itertools` for plain generation** (1.12) — it's correct, lazy, and efficient; hand-rolled
  generation is error-prone. Reach for backtracking (11.20) only when you need *custom pruning* or
  to build solutions incrementally.
- **These spaces explode** — n! and 2ⁿ grow astronomically (12! ≈ 479M). Enumeration is viable
  only for small n. If n is large, you almost certainly want a **count formula** or **DP** (11.21),
  not to enumerate.
- **Generate lazily; don't `list()` a huge space** — iterate the generator (1.2) and process/prune
  on the fly; materialising billions of tuples OOMs.
- **Watch duplicates with repeated input elements** — `permutations([1,1,2])` yields duplicate
  tuples; dedupe (a set, 11.1) or use sorted + skip-equal in backtracking if distinct results are
  required.

### Where this shows up

- **Interview classics:** Subsets (I/II), Permutations (I/II), Combinations, Combination Sum,
  Letter Combinations of a Phone Number, Generate Parentheses, Cartesian-product / grid
  enumeration.
- **Real work (the crossover):** generating parameter grids for hyperparameter search
  (`product` over value lists — the Area 8 sweep), enumerating test-case combinations, feature
  subset exploration, and any "try all configurations of a small set" — `itertools.product`/
  `combinations` are the everyday tools.
- **Pattern mapping:** generated by **backtracking** (11.20) or **`itertools`** (1.12); subsets
  map to **bitmasks** (11.26); when the goal is a count/optimum over these spaces rather than
  listing them, it's **DP** (11.21) — enumeration is the brute-force baseline patterns improve on.
[↑ Back to top](#contents)

---

<a id="11.30"></a>
## 11.30 — "I've read the problem — now which pattern is it?" → reading a problem to pick the approach

### The situation

You face an unfamiliar problem in an interview or at work. You know the ~20 patterns from this
area, but the real skill — the one this whole pillar builds toward — is **mapping a fresh problem
to the right pattern** quickly, instead of staring blankly or jumping to brute force:

```python
# "Find the longest substring with at most K distinct characters."
# "Return the kth smallest element in a sorted matrix."
# "Can these courses be finished given prerequisites?"
# each is a near-instant pattern match ONCE you know the keyword-to-pattern map.
```

Knowing the patterns isn't enough; recognising *which* applies, from the problem's wording and
structure, is what turns "stuck" into "I have a plan."

### What's really going on

Strong problem-solvers don't invent algorithms from scratch under pressure — they **recognise the
shape** and recall the matching pattern. Problem statements leak strong **signals**: keywords
("contiguous," "sorted," "shortest path," "all combinations," "minimum/maximum," "kth"), the
input structure (array? linked list? tree? grid? two sequences?), and constraints (the input
size hints at the required complexity — n ≤ 20 suggests exponential/backtracking is fine; n ≤ 10⁵
demands O(n log n) or better; n ≤ 10⁹ demands O(log n) or O(1)).

The method: **read carefully → identify the signals → match to a pattern → and only then code.**
This scenario is the **decision tree** over the whole area — a lookup from "what the problem says"
to "which of 11.1–11.29 to reach for." It's also a humility check: most problems are a known
pattern (or a small composition of two), so the question is rarely "what novel algorithm?" but
"which pattern, possibly combined?"

> **Trigger:** *any* new problem — this is the meta-skill the area builds to. **Pattern:** read →
> extract **signals** (keywords, input structure, constraints/size) → **map to a known pattern**
> (the decision tree below) → verify with a tiny example → code. **Result:** "stuck" becomes
> "candidate approach in seconds." Most problems are a known pattern or a composition of two —
> recognise, don't reinvent.

### The move

Match the problem's signals to a pattern using the keyword/structure decision map, then confirm
on a tiny example before coding.

### Why it works

Patterns have **distinctive fingerprints** in how problems are phrased and shaped, so a short
checklist of signals reliably narrows ~20 patterns to one or two candidates. Checking the
**constraints** prunes further — the input size dictates the allowed complexity, which often
eliminates whole categories (n ≤ 20 → backtracking is fine; n = 10⁵ → you need O(n log n), so
brute force is out before you write it). Verifying the candidate on a tiny example catches a
mis-match cheaply, *before* you've sunk time into the wrong approach. The method works because
interview/competitive problems are overwhelmingly *applications* of known patterns (or simple
compositions), so disciplined recognition beats from-scratch invention almost every time.

### The decision map (signal → pattern)

```text
# === BY KEYWORD / PHRASING =============================================
# "pair / duplicate / complement / seen before / count of each / group by"
#       -> HASHING (11.1) ; counts -> Counter ; group -> defaultdict ; join -> dict (Area 3)
# "sorted array" + "pair/triple" , "in place reverse/dedup/partition"
#       -> TWO POINTERS (11.2)
# "longest/shortest/max/min CONTIGUOUS subarray/substring with <condition>"
#       -> SLIDING WINDOW (11.3)   (subSEQUENCE, not contiguous -> DP, 11.21)
# "range sum asked repeatedly" , "subarray sums to k" (esp. with negatives)
#       -> PREFIX SUMS (11.4) (+ hashing for the count variant)
# "search a SORTED thing" , "find position/insert point"
#       -> BINARY SEARCH (11.5)
# "minimise the maximum / maximise the minimum / smallest value such that feasible"
#       -> BINARY SEARCH ON THE ANSWER (11.6)
# "intervals / overlapping ranges / meetings / merge"
#       -> SORT + SWEEP / INTERVALS (11.7)
# "linked list" + "cycle / middle / nth from end"  -> FAST & SLOW POINTERS (11.8)
# "linked list" + "reverse / reorder / merge / swap" -> POINTER MANIPULATION (11.9)
# "next/previous greater/smaller element" , "span" , "largest rectangle"
#       -> MONOTONIC STACK (11.10)
# "max/min of every window of size k"  -> MONOTONIC DEQUE (11.11)
# "kth largest/smallest / top-K / K most frequent / merge K / running median"
#       -> HEAP (11.12)
# "tree" + "depth/sum/path/validate/compare"   -> TREE DFS (11.13)
# "tree" + "level by level / minimum depth"     -> TREE BFS (11.14)
# "BST" + "search/insert/kth/validate/range"    -> BST OPS (11.15)
# "grid / maze / islands / connected / reachable / shortest steps (unweighted)"
#       -> GRAPH BFS/DFS + visited (11.16)   (shortest -> BFS)
# "order with dependencies / prerequisites / can finish / build order"
#       -> TOPOLOGICAL SORT (11.17)
# "cheapest/shortest path with WEIGHTS (non-negative)"  -> DIJKSTRA (11.18)
# "are X and Y connected / number of groups / connections added over time"
#       -> UNION-FIND (11.19)
# "generate ALL ... / placements / Sudoku / N-Queens"   -> BACKTRACKING (11.20)
# "count the ways / min-max cost / can you make X" + choices interact + overlap
#       -> DP (11.21) ; grid/two coords -> 2D DP (11.22) ; two strings -> STRING DP (11.23)
# "locally-best obviously works / min number of ___ / scheduling"
#       -> GREEDY (11.24)   (but PROVE the greedy choice, or counterexample it!)
# "prefix / autocomplete / starts-with / dictionary of words"  -> TRIE (11.25)
# "every element twice except one / subset-as-state / count bits / power of two"
#       -> BIT MANIPULATION (11.26)
# "spiral / rotate / transpose a matrix in a pattern"  -> MATRIX TRAVERSAL (11.27)
# "all subsets/permutations/combinations/product"      -> ENUMERATION (11.29 / itertools)

# === BY CONSTRAINTS (size dictates complexity) =========================
# n <= ~20            -> exponential ok: BACKTRACKING (11.20) / bitmask DP (11.26)
# n <= ~2000          -> O(n^2) ok: many DP (11.21/11.22)
# n <= ~10^5 / 10^6   -> need O(n log n) or O(n): sort+sweep, sliding window, hashing, heap
# n <= ~10^9 or "huge"-> need O(log n) or O(1): BINARY SEARCH (11.5/11.6), math/formula
# the constraint is a HINT at the intended complexity -> it prunes the candidate patterns.

# === THE PROCESS ========================================================
# 1. READ twice; restate the problem in your own words; note input type & constraints.
# 2. Work a TINY example by hand -> reveals the structure and edge cases.
# 3. Match SIGNALS -> candidate pattern(s) above. Often it's a COMPOSITION (e.g. top-K
#    frequent = Counter (11.1) + heap (11.12); reorder list = fast/slow (11.8) + reverse (11.9)).
# 4. Start from BRUTE FORCE, then ask which pattern removes the repeated work (hashing? sorting?
#    two pointers? DP?) -> that's usually the optimisation (mirrors Area 2's "make it work, then
#    fast").
# 5. VERIFY on the tiny example + EDGE CASES (empty, one element, duplicates, all same,
#    negatives, boundaries — 1.17) BEFORE and AFTER coding.
```

### Impact

- **Turns "stuck" into a plan:** the signal→pattern map produces a candidate approach in seconds,
  the difference between freezing and making progress under pressure.
- **Avoids wasted effort:** matching (and constraint-checking) *before* coding stops you sinking
  time into a doomed brute force or the wrong pattern.
- **Reveals compositions:** seeing problems as known patterns (often two combined) is how
  "hard"-looking problems become tractable — recognise, don't reinvent.

### Pros & cons / when NOT to

**Apply this meta-process to every problem** — it's the capstone skill the whole area exists to
build.

**Watch out / when NOT to:**
- **Don't pattern-match prematurely** — read carefully and work a tiny example first; forcing the
  wrong pattern onto a misread problem is worse than thinking from brute force. Recognition
  follows understanding.
- **Check constraints early** — the input size eliminates whole categories (an O(n²) DP on n=10⁶
  is a non-starter); let it prune your candidates before you commit.
- **Many problems are COMPOSITIONS** — top-K frequent = Counter + heap; sliding window often +
  hashing; reorder list = fast/slow + reverse. Don't expect exactly one pattern; expect one or
  two combined.
- **Some problems genuinely need novel reasoning** — not everything is a textbook pattern;
  recognition gets you most of the way, then problem-specific insight finishes it. Treat the map
  as a strong prior, not a guarantee.
- **Always verify on edge cases** — empty/one-element/duplicates/negatives/boundaries (1.17/
  10.8); a pattern that's right on the happy path can still be wrong at the edges.

### Where this shows up

- **Interview practice (the whole point):** this is *the* skill coding interviews test — quickly
  classifying a problem and choosing an approach out loud; the signal map is what you internalise
  by solving many problems.
- **Real work (the crossover):** the same "recognise the shape, reach for the known tool" reflex
  the entire guide trains — diagnosing whether a slow job is I/O- vs CPU-bound (Area 5/6), whether
  data work is a dedup/group/join (Area 3), or whether a slowdown is an accidental O(n²) (Area 2).
  Problem-recognition is domain-general.
- **Pattern mapping:** the meta-pattern over 11.1–11.29 — and over the whole field guide:
  *feel the symptom → name the real problem → reach for the matching move.* That reflex, across
  craft, data, systems, ML, and algorithms, is what the guide set out to build.

[↑ Back to top](#contents)

