<a id="contents"></a>
# Area 12 — DSA Problem Bank & Timed Reps (Interview Prep)

Area 11 taught you to **recognise** which pattern a problem needs. This document gives you
the **practice problems** to build *speed* — because in a real interview you don't get credit
for recognising the pattern slowly. It maps a curated set of problems onto each Area 11
pattern, tells you how to do **timed reps**, and ends with **mock interview questions + full
answers**.

This is built so you don't need an outside problem list: each pattern lists the exact
problems to solve, in difficulty order, with *why* each one matters.

---

## Which company does this target?

> **The "grind" cluster — Google, Meta, Amazon — gate you on this.** You must be fast and
> hit the optimal solution. **Meta** is the most ruthless on speed (2 problems in ~40 min);
> **Google** uses the hardest problems and strictest complexity/clean-code; **Amazon** is
> mostly medium difficulty but weaves in behaviour (see Area 14).
>
> The "practical" cluster — **Anthropic, OpenAI, Netflix** — test this *less*, but a screening
> round may still include one or two. **Nvidia** may ask DSA in C++; the *patterns* here
> transfer, the language doesn't.
>
> **Bottom line:** if you're targeting Google/Meta/Amazon, this is your most important
> document. If you're targeting Anthropic/OpenAI/Netflix, skim it and spend more time on
> Areas 13–15.

---

## How to use this document (the timed-rep method)

**Why timed reps?** Recognising a pattern (Area 11) is step one. But interviews test whether
you can go from "blank screen" to "working optimal code" in **20–30 minutes while talking
out loud**. That only comes from *timed* practice, not from reading solutions.

**The method — for each problem:**

1. **Set a timer (25 min).** Read the problem; restate it in your own words (see Area 15 for
   why this matters).
2. **Spend the first 5 min on approach, NOT code.** Say out loud: "this looks like
   [pattern], because the signal is [keyword]." (This is the Area 11.30 reflex.)
3. **Code it.** Talk through what you're typing.
4. **Test on a tiny example + edge cases** (empty, one element, duplicates) *before* saying
   "done".
5. **If stuck >10 min, look at the hint, not the solution.** Then keep trying.
6. **After solving (or timing out), read the optimal solution and re-solve it from scratch
   the next day.** Spaced repetition is what builds speed.

> **Impact:** engineers who do ~150 timed problems this way typically go from "I can solve it
> in an hour" to "I can solve it in 20 minutes talking out loud" — which is the actual
> interview bar. Reading 500 solutions without timed reps does **not** build this; it builds
> false confidence. The single biggest mistake candidates make is passive reading.

**How many?** Aim for **~150 problems** total (roughly the list below), spread over 6–8 weeks.
Quality of reps beats quantity. Re-solving 100 problems twice beats solving 200 once.

---

## Contents

- [The 8-week study plan](#plan)
- [Problem bank by pattern](#bank)
  - [P1 — Arrays & Hashing (→ 11.1)](#p1)
  - [P2 — Two Pointers (→ 11.2)](#p2)
  - [P3 — Sliding Window (→ 11.3)](#p3)
  - [P4 — Binary Search (→ 11.5/11.6)](#p4)
  - [P5 — Stack / Monotonic (→ 11.10/11.11)](#p5)
  - [P6 — Heap / Top-K (→ 11.12)](#p6)
  - [P7 — Linked List (→ 11.8/11.9)](#p7)
  - [P8 — Trees (→ 11.13/11.14/11.15)](#p8)
  - [P9 — Graphs (→ 11.16/11.17/11.18/11.19)](#p9)
  - [P10 — Backtracking (→ 11.20)](#p10)
  - [P11 — Dynamic Programming (→ 11.21/11.22/11.23)](#p11)
  - [P12 — Greedy & Intervals (→ 11.7/11.24)](#p12)
- [Mock interview questions + full answers](#mock)

---

<a id="plan"></a>
## The 8-week study plan

**Why a plan?** Random grinding wastes time and leaves gaps. A pattern-by-pattern plan means
you build one reflex at a time, then mix them — which is how interviews actually feel (you
don't know the pattern in advance).

| Week | Focus | Target |
|---|---|---|
| 1 | P1 Arrays & Hashing, P2 Two Pointers | ~20 problems |
| 2 | P3 Sliding Window, P4 Binary Search | ~20 |
| 3 | P5 Stack, P6 Heap | ~18 |
| 4 | P7 Linked List, P8 Trees | ~22 |
| 5 | P9 Graphs | ~18 |
| 6 | P10 Backtracking, P11 DP (start) | ~20 |
| 7 | P11 DP (finish), P12 Greedy/Intervals | ~20 |
| 8 | **Mixed mode** — random problems, no pattern hint, full timed mocks | ~15 + 4 mocks |

> **The Week-8 "mixed mode" is the most important.** Solving 20 sliding-window problems in a
> row is easy — you *know* it's sliding window. The interview gives you a problem with **no
> label**. Week 8 simulates that: pick random problems, force yourself to identify the pattern
> first (Area 11.30), then solve. This is where recognition becomes real.

---

<a id="bank"></a>
## Problem bank by pattern

Each pattern below lists problems in **difficulty order** (Easy → Medium → Hard). Format:
**Problem — difficulty — why it matters — which company favours it.** Solve them on
LeetCode (free tier covers most). Do the Easy ones first to build the template, then Mediums
(the interview sweet spot), then 1–2 Hards for stretch.

---

<a id="p1"></a>
### P1 — Arrays & Hashing (→ pattern 11.1)

**The reflex:** "pair / duplicate / seen-before / count / group" → use a hash map/set for
O(1) lookup, turning O(n²) into O(n).

| Problem | Diff | Why it matters | Favoured by |
|---|---|---|---|
| Two Sum | Easy | *The* canonical hashing problem; write it in 3 min | All |
| Contains Duplicate | Easy | Set membership in one line; warm-up | All |
| Valid Anagram | Easy | Counter equality — "frequency = Counter" | Meta, Amazon |
| Group Anagrams | Med | Canonical-key grouping (`defaultdict`); very common | Meta, Google |
| Top K Frequent Elements | Med | Counter + heap combo (links P6); asked constantly | Meta, Amazon |
| Valid Sudoku | Med | Multiple sets tracking constraints; clean-code test | Google |
| Longest Consecutive Sequence | Med | Clever set use for O(n); separates strong candidates | Google, Meta |
| First Missing Positive | Hard | Index-as-hash trick, O(1) space; stretch | Google |

> **Practice tip:** Two Sum should become *muscle memory* — if you can't write it without
> thinking, you're not ready for the mediums. Re-solve until automatic, then never touch
> it again.

---

<a id="p2"></a>
### P2 — Two Pointers (→ pattern 11.2)

**The reflex:** input is **sorted**, or "pair from both ends", or "reverse/dedup/partition in
place" → two indices moving toward each other (O(1) space).

| Problem | Diff | Why it matters | Favoured by |
|---|---|---|---|
| Valid Palindrome | Easy | Converge-and-compare; warm-up template | Meta, Amazon |
| Two Sum II (sorted) | Easy | Shows two-pointers beats hashing on sorted input | All |
| 3Sum | Med | Sort + fix-one + two-pointer; *extremely* common | Meta, Google, Amazon |
| Container With Most Water | Med | Greedy two-pointer; teaches "move the limiting side" | Amazon, Google |
| Trapping Rain Water | Hard | Two-pointer or stack; classic hard, asked at all | Google, Amazon |
| Sort Colours (Dutch flag) | Med | In-place 3-way partition; O(1) space | Meta |

---

<a id="p3"></a>
### P3 — Sliding Window (→ pattern 11.3)

**The reflex:** "longest/shortest/max/min **contiguous** subarray/substring with a condition"
→ grow `right`, shrink `left` when invalid, update best.

| Problem | Diff | Why it matters | Favoured by |
|---|---|---|---|
| Best Time to Buy/Sell Stock | Easy | Simplest window (track min so far); warm-up | Amazon, all |
| Longest Substring Without Repeating | Med | *The* canonical variable window; near-guaranteed | Amazon, Meta, Google |
| Longest Repeating Char Replacement | Med | Window + frequency count; trickier shrink rule | Google |
| Minimum Window Substring | Hard | Hardest common window; need + have counts | Meta, Amazon |
| Permutation in String | Med | Fixed-size window + char counts | Meta |
| Sliding Window Maximum | Hard | Window + monotonic deque (links P5) | Amazon, Google |

> **Why these matter so much:** Longest Substring Without Repeating Characters is one of the
> single most-asked medium problems across Meta/Amazon/Google. If you can solve it cold in 15
> minutes, you've proven the whole sliding-window reflex.

---

<a id="p4"></a>
### P4 — Binary Search (→ patterns 11.5 / 11.6)

**The reflex:** "sorted" → binary search; "minimise the max / smallest feasible value" →
binary search **on the answer** (write a `feasible(x)` check).

| Problem | Diff | Why it matters | Favoured by |
|---|---|---|---|
| Binary Search | Easy | Get the boundary template exactly right; foundation | All |
| Search Insert Position | Easy | `bisect`-style left bound | All |
| Search in Rotated Sorted Array | Med | The classic twist; very common | Meta, Amazon, Google |
| Find Minimum in Rotated Array | Med | Boundary reasoning on rotation | Amazon |
| Koko Eating Bananas | Med | *Binary search on answer* — the key generalisation | Google, Meta |
| Median of Two Sorted Arrays | Hard | Hard binary search; partition reasoning | Google |
| Capacity to Ship Packages in D Days | Med | Binary-search-on-answer; feasibility check | Amazon, Google |

> **Boundary bugs are the #1 reason candidates fail binary search.** Drill the template
> (Area 11.5) until `<` vs `<=` and `mid±1` are automatic. Use `bisect` when the problem is a
> plain lookup.

---

<a id="p5"></a>
### P5 — Stack / Monotonic Stack & Deque (→ patterns 11.10 / 11.11)

**The reflex:** "matching brackets / next-greater / span / largest rectangle" → stack; "max
of every window" → monotonic deque.

| Problem | Diff | Why it matters | Favoured by |
|---|---|---|---|
| Valid Parentheses | Easy | Canonical stack; warm-up everyone expects | All |
| Min Stack | Easy | Stack with O(1) min; design-y | Amazon |
| Daily Temperatures | Med | Canonical monotonic stack (next-greater) | Meta, Amazon |
| Next Greater Element II | Med | Monotonic stack + circular array | Amazon |
| Largest Rectangle in Histogram | Hard | The hard monotonic-stack classic | Google, Amazon |
| Evaluate Reverse Polish Notation | Med | Stack for expression eval | Amazon |

---

<a id="p6"></a>
### P6 — Heap / Top-K / Merge-K (→ pattern 11.12)

**The reflex:** "kth largest / top-K / merge K sorted / running median / repeated extreme" →
heap (`heapq`); for top-K keep a **size-K** heap.

| Problem | Diff | Why it matters | Favoured by |
|---|---|---|---|
| Kth Largest Element in an Array | Med | Size-K heap (or quickselect); foundational | Amazon, Meta |
| Top K Frequent Elements | Med | Counter + heap; appears in P1 too | Meta, Amazon |
| K Closest Points to Origin | Med | Heap by distance; very common at Amazon | Amazon, Meta |
| Merge K Sorted Lists | Hard | Heap of heads; classic hard | Google, Amazon, Meta |
| Find Median from Data Stream | Hard | Two-heap design; senior-favourite | Google, Amazon |
| Task Scheduler | Med | Greedy + heap/counting | Amazon |

---

<a id="p7"></a>
### P7 — Linked List (→ patterns 11.8 / 11.9)

**The reflex:** "cycle / middle / nth-from-end" → fast & slow pointers; "reverse / merge /
reorder" → careful pointer rewiring (save `next` before overwriting; use a dummy head).

| Problem | Diff | Why it matters | Favoured by |
|---|---|---|---|
| Reverse Linked List | Easy | *The* foundational pointer-rewire; write it cold | All |
| Merge Two Sorted Lists | Easy | Dummy-head merge; building block | All |
| Linked List Cycle | Easy | Floyd's fast/slow; classic | Amazon, Meta |
| Remove Nth Node From End | Med | Two-pointer fixed gap | Meta, Amazon |
| Reorder List | Med | Compose: find middle + reverse + merge | Meta |
| LRU Cache | Med | Hash map + doubly linked list; *design-y*, very common | Amazon, Meta, Google |
| Merge K Sorted Lists | Hard | (also P6) heap + list rewiring | Google, Amazon |

> **LRU Cache is a must-do.** It combines a dict and a doubly linked list and shows up at
> Amazon/Meta/Google constantly — it sits between DSA and system design (links Area 2's caching
> and Area 13's design).

---

<a id="p8"></a>
### P8 — Trees (→ patterns 11.13 / 11.14 / 11.15)

**The reflex:** "process every node / depth / path" → DFS recursion; "level by level / min
depth" → BFS; "BST search/kth/validate" → use the ordering.

| Problem | Diff | Why it matters | Favoured by |
|---|---|---|---|
| Maximum Depth of Binary Tree | Easy | The DFS skeleton; warm-up | All |
| Invert Binary Tree | Easy | Famous; trivial recursion | Google, all |
| Same Tree / Symmetric Tree | Easy | Parallel recursion | Amazon |
| Binary Tree Level Order Traversal | Med | The BFS template (queue + size snapshot) | Amazon, Meta |
| Validate BST | Med | Pass-down range; the classic BST gotcha | Amazon, Google, Meta |
| Lowest Common Ancestor (BST + binary tree) | Med | Both versions asked; recursion | Meta, Amazon |
| Kth Smallest in a BST | Med | In-order = sorted | Google |
| Binary Tree Max Path Sum | Hard | Post-order with a global; senior-favourite | Meta, Google |
| Serialize/Deserialize Binary Tree | Hard | DFS/BFS encoding; common hard | Google, Meta, Amazon |

---

<a id="p9"></a>
### P9 — Graphs (→ patterns 11.16 / 11.17 / 11.18 / 11.19)

**The reflex:** "grid / islands / reachable / shortest unweighted" → BFS/DFS + visited;
"dependencies/order" → topological sort; "weighted shortest path" → Dijkstra; "dynamic
connectivity/components" → union-find.

| Problem | Diff | Why it matters | Favoured by |
|---|---|---|---|
| Number of Islands | Med | *The* canonical grid DFS/BFS; near-guaranteed | Amazon, Meta, Google |
| Flood Fill | Easy | Simplest grid traversal; warm-up | Amazon |
| Clone Graph | Med | BFS/DFS + hashmap copy | Meta, Google |
| Course Schedule I/II | Med | Topological sort + cycle detection; very common | Meta, Amazon, Google |
| Rotting Oranges | Med | Multi-source BFS | Amazon |
| Pacific Atlantic Water Flow | Med | Reverse BFS from edges | Google, Meta |
| Word Ladder | Hard | BFS shortest path on implicit graph | Amazon |
| Network Delay Time | Med | Dijkstra (weighted) | Google |
| Number of Connected Components / Redundant Connection | Med | Union-find | Google, Amazon |
| Alien Dictionary | Hard | Topo sort from ordering; senior-favourite | Meta, Google |

> **Number of Islands + Course Schedule are the two highest-yield graph problems.** Master
> grid BFS/DFS and topological sort and you cover the majority of graph questions asked.

---

<a id="p10"></a>
### P10 — Backtracking (→ pattern 11.20)

**The reflex:** "generate ALL / placements / partitions / constraint puzzle" → choose →
explore → un-choose, with pruning.

| Problem | Diff | Why it matters | Favoured by |
|---|---|---|---|
| Subsets | Med | The power-set template | Meta, Amazon |
| Permutations | Med | The ordering template | Meta, Amazon |
| Combination Sum | Med | Backtracking with reuse + pruning | Amazon, Google |
| Word Search | Med | Backtracking on a grid (links P9) | Amazon, Meta |
| Palindrome Partitioning | Med | Partition + check | Meta |
| Generate Parentheses | Med | Pruned generation; elegant | Google, Meta |
| N-Queens | Hard | The classic placement-with-pruning | Google |

---

<a id="p11"></a>
### P11 — Dynamic Programming (→ patterns 11.21 / 11.22 / 11.23)

**The reflex:** "count ways / min-max cost / can you make X" + overlapping subproblems →
define state + recurrence + base case; memoise or tabulate.

| Problem | Diff | Why it matters | Favoured by |
|---|---|---|---|
| Climbing Stairs | Easy | The "hello world" of DP; Fibonacci shape | All |
| House Robber (I/II) | Med | Decision DP, O(1) space; very common | Amazon, Meta |
| Coin Change | Med | Min-DP; the canonical "fewest coins" | Amazon, Google, Meta |
| Longest Increasing Subsequence | Med | Subsequence DP (and the O(n log n) twist) | Google, Meta |
| Word Break | Med | DP over a string + dictionary | Amazon, Meta |
| Unique Paths / Min Path Sum | Med | 2D grid DP template | Amazon, Google |
| Longest Common Subsequence | Med | The two-sequence (string) DP template | Google, Amazon |
| Edit Distance | Hard | The string-DP capstone; spell-check/diff | Google, Meta |
| Maximum Subarray (Kadane) | Med | Famous; DP or greedy view | Amazon, all |

> **DP is the most feared topic and the highest-leverage to drill.** Most candidates freeze on
> "what's the state?" Practising the 4-step recipe (state → recurrence → base → order) on
> Climbing Stairs → House Robber → Coin Change builds the reflex; everything else is variations.

---

<a id="p12"></a>
### P12 — Greedy & Intervals (→ patterns 11.7 / 11.24)

**The reflex:** "intervals/overlap/merge/meetings" → sort + sweep; "min number of / locally-best
works" → greedy (but justify it).

| Problem | Diff | Why it matters | Favoured by |
|---|---|---|---|
| Merge Intervals | Med | *The* canonical interval problem; sort-then-sweep | Google, Meta, Amazon |
| Insert Interval | Med | Three-phase sweep | Google, Amazon |
| Non-overlapping Intervals | Med | Greedy by end time (activity selection) | Meta, Google |
| Meeting Rooms I/II | Med | Sweep / min-heap of end times | Amazon, Meta, Google |
| Jump Game I/II | Med | Greedy reach | Amazon, Meta |
| Gas Station | Med | Greedy with a correctness argument | Amazon, Google |
| Minimum Number of Arrows | Med | Interval greedy | Google |

---

<a id="mock"></a>
## Mock interview questions + full answers

These are **complete worked mocks** — each shows the *interviewer's question*, then a model
answer written the way you'd actually speak and code in the room (restate → identify pattern →
brute force → optimise → code → test → complexity). Read the question, attempt it yourself with
a timer, *then* read the answer. The answers double as a template for how to communicate (the
real Area 15 skill, applied here).

> **Which company each mock targets is labelled.** The style (think-aloud, optimise from brute
> force, test your own code) is what Meta/Google/Amazon grade. Anthropic/OpenAI will care more
> that your final code is *correct and clean*; Netflix that your reasoning is sound.

---

### Mock 1 — "Two Sum" variant *(target: warm-up; all companies, esp. Meta/Amazon screen)*

**Interviewer:** *"Given an array of integers `nums` and an integer `target`, return the indices
of the two numbers that add up to the target. You may assume exactly one solution, and you may
not use the same element twice."*

**Model answer (spoken + coded):**

> "Let me restate: I'm looking for two **indices** `i, j` where `nums[i] + nums[j] == target`.
> Output is the indices, not the values. One guaranteed solution.
>
> The brute force is two nested loops — check every pair — that's **O(n²)**. Let me see if I can
> do better. For each number `x`, I really need to know: have I already seen `target - x`? That's
> a *lookup*, and a hash map gives me O(1) lookups — this is the hashing pattern. So I'll walk
> the array once, and for each number check a dict of values I've already seen."

```python
def two_sum(nums, target):
    seen = {}                          # value -> index of numbers already passed
    for i, x in enumerate(nums):
        need = target - x              # the complement that completes the pair
        if need in seen:               # O(1): have we seen it before?
            return [seen[need], i]
        seen[x] = i                    # store AFTER checking (avoids pairing x with itself)
    return []
```

> "Let me test on `nums=[2,7,11,15], target=9`: i=0 x=2, need=7, not seen, store {2:0}. i=1 x=7,
> need=2, **2 is seen at index 0** → return [0,1]. Correct.
>
> Edge cases: empty array → returns []. Duplicates like `[3,3], target=6` → i=0 store {3:0}, i=1
> need=3 seen at 0 → [0,1], correct (storing after checking is what makes this work).
>
> **Complexity: O(n) time, O(n) space** — one pass, the dict holds up to n entries. That's
> optimal; you can't do better than reading the array once."

> **What this demonstrates to an interviewer:** restating the problem, naming the brute force
> *and its complexity*, spotting the lookup→hashing optimisation, testing your own code, and
> stating final complexity. Even on an easy problem, *doing all of this out loud* is what
> separates a hire from a "solved it but said nothing."

---

### Mock 2 — "Longest substring without repeating characters" *(target: Meta, Amazon, Google — the single most-asked medium)*

**Interviewer:** *"Given a string `s`, find the length of the longest substring without
repeating characters. Example: `'abcabcbb'` → 3 (the answer is `'abc'`)."*

**Model answer (spoken + coded):**

> "Restating: I need the longest **contiguous** run of characters with no repeats, and I return
> its *length*, not the substring. 'Contiguous' + 'longest with a condition' is the **sliding
> window** signal.
>
> Brute force: check every substring, test each for uniqueness — that's O(n²) substrings × O(n)
> to check = O(n³). Too slow. With a window: I'll grow the right edge to include each new char;
> if that char is already in my window, I shrink from the left until it's gone. I track which
> chars are in the window with a set, and record the best length as I go.
>
> Why does each pointer only move forward, making it O(n)? Because `left` never goes backward —
> each char enters the set once and leaves once, so at most 2n operations."

```python
def length_of_longest(s):
    seen = set()                       # chars currently in the window
    left = best = 0
    for right, ch in enumerate(s):
        while ch in seen:              # window invalid (repeat) -> shrink from left
            seen.remove(s[left])
            left += 1
        seen.add(ch)                   # now valid: include the new char
        best = max(best, right - left + 1)   # window length = right - left + 1
    return best
```

> "Test on `'abcabcbb'`: window grows a,b,c (best=3); at the next 'a', 'a' is in seen → shrink
> (remove a, left=1); add a; continue. Best stays 3. Correct.
>
> Edge cases: empty string → loop doesn't run → returns 0, correct. All-same like `'bbbb'` →
> window never exceeds 1 → returns 1, correct. All-unique `'abcd'` → returns 4, correct.
>
> **Complexity: O(n) time** (each char added/removed at most once), **O(min(n, charset)) space**
> for the set. Optimal."

> **The trap to avoid out loud:** a beginner often re-scans the window to check for repeats —
> that's O(n²). Saying "I update the set incrementally so each step is O(1)" shows you
> understand *why* the window is fast, not just that it works.

**Follow-up the interviewer may add:** *"Now return the actual substring, not just its length."*
> "I track the best window's start/end alongside `best`: when I update `best`, also save
> `left`; at the end return `s[best_left : best_left + best]`."

---

### Mock 3 — "Number of Islands" *(target: Amazon, Meta, Google — the canonical graph question)*

**Interviewer:** *"Given a 2D grid of '1's (land) and '0's (water), count the number of islands.
An island is land connected horizontally or vertically. Example: a grid with two separate
clumps of 1s → 2."*

**Model answer (spoken + coded):**

> "Restating: count **connected components** of land cells, where connections are up/down/left/
> right. A grid is just a graph where each cell's neighbours are the adjacent cells — so this is
> **graph traversal (BFS/DFS) + a visited set**, the connected-components pattern.
>
> Plan: scan every cell. When I hit a '1' I haven't visited, that's a *new* island — I increment
> the count and then *flood* its whole connected region (DFS) so I don't count any of its cells
> again. The flood marks cells visited so we terminate (grids have cycles — neighbours point
> back)."

```python
def num_islands(grid):
    if not grid: return 0
    rows, cols, count = len(grid), len(grid[0]), 0
    def flood(r, c):
        if (r < 0 or r >= rows or c < 0 or c >= cols      # off the grid
                or grid[r][c] != "1"):                     # water or already-flooded
            return
        grid[r][c] = "0"                                   # MARK visited (sink the land)
        flood(r+1, c); flood(r-1, c); flood(r, c+1); flood(r, c-1)   # 4 neighbours
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":      # unvisited land -> a new island
                count += 1
                flood(r, c)            # flood its whole region
    return count
```

> "I mark visited by sinking land to '0' in place (O(1) space, no separate set — I'd mention I
> could use a `visited` set if mutating the input isn't allowed). Test: a 3×3 with two clumps →
> first clump flooded on first hit (count=1), second clump later (count=2). Correct.
>
> Edge cases: empty grid → 0. All water → 0. All land → 1 (one flood covers everything).
>
> **Complexity: O(rows×cols)** — each cell visited once. **Space: O(rows×cols)** worst case for
> the recursion stack (a grid that's all land); I'd switch to an explicit stack/BFS queue if
> stack depth is a concern on huge grids."

> **What earns points:** recognising "grid = graph", explicitly mentioning the visited set is
> *mandatory* (cycles), and noting the recursion-depth caveat for large grids (shows you think
> about limits, Area 11.28).

---

### Mock 4 — "Coin Change" *(target: Amazon, Google, Meta — the canonical DP question)*

**Interviewer:** *"You have coins of given denominations and an amount. Return the fewest coins
needed to make that amount, or -1 if it's impossible. Example: coins `[1,2,5]`, amount `11` →
3 (5+5+1)."*

**Model answer (spoken + coded):**

> "Restating: minimum number of coins summing to `amount`; -1 if no combination works. 'Minimum
> ... to make X' with choices that interact → this smells like **dynamic programming**. Let me
> check: a greedy 'take the biggest coin' is tempting but **wrong** in general — coins `[1,3,4]`,
> amount 6: greedy gives 4+1+1 (3 coins) but optimal is 3+3 (2 coins). So greedy fails; I need DP.
>
> **State:** `dp[a]` = fewest coins to make amount `a`. **Recurrence:** to make `a`, try each
> coin `c` and take `1 + dp[a-c]`, the best over all coins. **Base case:** `dp[0] = 0` (zero
> coins make zero). I fill `dp` from 1 up to `amount` so each `dp[a-c]` is already computed."

```python
def coin_change(coins, amount):
    INF = amount + 1                       # a sentinel "impossible" (more than any real answer)
    dp = [0] + [INF] * amount              # dp[0]=0; the rest start "impossible"
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a:
                dp[a] = min(dp[a], dp[a - c] + 1)   # use coin c -> 1 + best for the remainder
    return dp[amount] if dp[amount] != INF else -1   # never improved -> impossible
```

> "Test coins `[1,2,5]`, amount 11: dp builds up... dp[11] = min over using 1 (dp[10]+1), 2
> (dp[9]+1), 5 (dp[6]+1) → 3. Correct. Test amount 0 → dp[0]=0, returns 0. Test coins `[2]`,
> amount 3 → dp[3] stays INF → returns -1, correct.
>
> **Complexity: O(amount × number_of_coins) time, O(amount) space.** Much better than the
> exponential brute force of trying every combination."

> **What earns points:** *proving greedy is wrong with a counterexample* before reaching for DP
> (interviewers love this — it shows judgment, Area 11.24), then cleanly stating state →
> recurrence → base case. Freezing on "what's the state?" is the #1 DP failure; verbalising the
> 4-step recipe (Area 11.21) prevents it.

**Follow-up:** *"How many distinct ways to make the amount (not the minimum)?"*
> "Same DP shape but `dp[a] += dp[a-c]` (count), and iterate coins on the outside to avoid
> counting permutations as distinct — a classic variant worth knowing."

---

### Mock 5 — "Merge K Sorted Lists" *(target: Google, Amazon, Meta — a common Hard)*

**Interviewer:** *"You're given `k` sorted linked lists. Merge them into one sorted list."*

**Model answer (spoken + coded):**

> "Restating: `k` already-sorted lists → one sorted list. The naive approach: concatenate all
> nodes and sort — O(N log N) where N is total nodes, and it ignores that the lists are *already
> sorted*. Better: at each step I want the **smallest current head** among the k lists — that's
> 'repeatedly get the minimum among many', which is a **heap** (min-heap of the k heads).
>
> I push the head of each list into a min-heap. Then repeatedly pop the smallest, append it to
> the result, and push that node's `next`. The heap always surfaces the global minimum next."

```python
import heapq
def merge_k_lists(lists):
    heap = []
    for i, node in enumerate(lists):       # seed heap with each list's head
        if node:
            heapq.heappush(heap, (node.val, i, node))   # (value, index, node)
    dummy = tail = ListNode(0)             # dummy head simplifies the build (Area 11.9)
    while heap:
        val, i, node = heapq.heappop(heap) # the smallest current head
        tail.next = node; tail = node      # splice it onto the result
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))   # push its successor
    return dummy.next
```

> "The `i` (list index) in the tuple is a **tie-breaker** so the heap never tries to compare two
> `ListNode` objects when values are equal (they're not comparable → would crash). That's a
> subtle correctness point worth saying out loud.
>
> Test: lists `[1→4→5], [1→3→4], [2→6]` → heap surfaces 1,1,2,3,4,4,5,6 in order. Correct. Edge
> cases: empty input list `[]` → heap empty → returns None. Some lists empty → skipped at seeding.
>
> **Complexity: O(N log k)** — N total nodes, each pushed/popped once from a heap of size ≤ k.
> Beats the O(N log N) concatenate-and-sort, and uses O(k) heap space."

> **What earns points:** rejecting the naive sort by *using the sorted property*, the heap
> insight, and the tie-breaker tuple (a real bug that catches people). Stating O(N log k) vs
> O(N log N) shows you know *why* the heap is better, not just that it works.

---

## Final advice for the DSA rounds

- **Talk the whole time.** Silent solving, even if correct, reads as "can't communicate" — a
  red flag at Meta/Google especially (Area 15 covers this in depth).
- **Always state brute force + its complexity first**, then optimise. Jumping straight to the
  optimal solution can read as memorised; deriving it reads as capable.
- **Test your own code on a tiny example and edge cases** before saying "done" — interviewers
  notice who does this unprompted.
- **State final time & space complexity** every time, unprompted.
- **If stuck, think out loud about the brute force and what's repeated** — "I'm re-scanning, can
  I remember instead?" leads to hashing; "the input's sorted, can I avoid re-checking?" leads to
  two pointers. The Area 11.30 signal map is your recovery tool.

> **Company nuance recap:** **Meta** — speed + optimality, 2 problems/session. **Google** —
> hardest problems, cleanest code, strict complexity. **Amazon** — medium problems but pair each
> with a behavioural angle (Area 14). **Anthropic/OpenAI** — correctness and clean realistic code
> over puzzle difficulty. **Netflix** — sound reasoning at senior depth. **Nvidia** — same
> patterns, often in C++/CUDA.

[↑ Back to top](#contents)
