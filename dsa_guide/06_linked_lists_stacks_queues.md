<a id="top"></a>
# Chapter 06 — Linked Lists, Stacks, aur Queues

Yeh teen linear (line-mein) data structures hain — arrays ke "cousins", par alag properties ke saath.
Interview mein linked-list ke basics (reverse, cycle) aur stack/queue ke patterns (parentheses,
monotonic-stack, BFS) aate. Ch 1.4 — LL/stack/queue LOW-MEDIUM priority (basics zaroori, hard rare).

Clear examples + dry-run ke saath. (Yeh Ch 03 arrays + Ch 04 hashing ki neev pe.)

---

## Is chapter ka index

- [6.1 — Linked List kya hai (array se farak)](#s6-1)
- [6.2 — LL Pattern: Reversal (iterative + recursive)](#s6-2)
- [6.3 — LL Pattern: Fast-slow pointers (cycle, middle)](#s6-3)
- [6.4 — LL Pattern: Merge two sorted lists + dummy node](#s6-4)
- [6.5 — Stack kya hai (LIFO) + valid parentheses](#s6-5)
- [6.6 — Stack Pattern: Monotonic stack (next greater)](#s6-6)
- [6.7 — Queue kya hai (FIFO) + deque](#s6-7)
- [6.8 — Queue Pattern: Monotonic deque (sliding window max)](#s6-8)
- [6.9 — Nuances, kab kaunsa, edge cases](#s6-9)
- [6.10 — Yaad rakhne wali baatein](#s6-10)

---

<a id="s6-1"></a>
## 6.1 — Linked List kya hai (array se farak)

**Linked List** = nodes ki ek chain, jahan har **node** mein ek value hai aur **agle node ka pointer**
(`next`). Array mein elements ek continuous block mein hote (index se); linked-list mein woh bikhre
hote, aur `next` pointers se jude.

**Python mein node (standard interview definition — yeh yaad rakho):**
```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val        # is node ki value
        self.next = next      # agle node ka pointer (None = end)
```

**Ek linked list dikhti kaisi hai:**
```
[1|•] -> [2|•] -> [3|•] -> None
 val next  val next  val next
head                      (aakhri ka next = None)
```
- `head` = pehla node. Har node `next` se agle ko point karta. Aakhri ka `next = None` (end nishani).

**Array vs Linked List (farak — yaad rakho):**

| Cheez | Array (list) | Linked List |
|---|---|---|
| Memory | Continuous block | Bikhre nodes, pointers se jude |
| Index access `arr[i]` | O(1) (direct jump) | O(n) (chain follow karo) |
| Front pe insert/delete | O(n) (shift) | O(1) (pointer badlo) |
| Ek node ke aage-peeche | Index +/-1 | Sirf `next` (aage; single-LL mein peeche nahi) |

**Kab linked-list (kyun exist karta):** array mein front/beech pe insert-delete O(n) (shift), par LL
mein O(1) (bs pointer badlo). Isliye jab bahut insert/delete ho (beech mein), LL better. Par index-
access slow (O(n)). Interview mein LL usually pointer-manipulation skill test karta.

**Traverse karna (basic):**
```python
def print_list(head):
    curr = head
    while curr:              # jab tak node hai (None nahi)
        print(curr.val)
        curr = curr.next     # aage badho
```

> **Yaad rakhne wali baat:** Linked list = nodes ki chain, har node `{val, next}`, `next` agle ko
> point (aakhri None). Array se farak: index-access O(n) (chain follow) BUT front insert/delete O(1)
> (pointer badlo). `curr = curr.next` se traverse. Interview = pointer-manipulation skill.

[↑ Back to top](#top)

---

<a id="s6-2"></a>
## 6.2 — LL Pattern: Reversal (iterative + recursive)

Linked-list ko **ulta** karna (reverse) — sabse classic LL problem. Pointer-manipulation ka core
skill. Iterative (loop) aur recursive dono aane chahiye.

**Problem — Reverse Linked List:**

**Problem:** linked list ka order ulta karo (head aakhri ban jaye).
```
Input:  1 -> 2 -> 3 -> None
Output: 3 -> 2 -> 1 -> None
```

**Iterative solution (O(n) time, O(1) space — yeh yaad karo):**
```python
def reverse_list(head):
    prev = None                # pehle koi nahi
    curr = head
    while curr:
        next_node = curr.next  # agla yaad rakho (warna kho jayega)
        curr.next = prev       # pointer ULTA karo (curr ab prev ko point)
        prev = curr            # prev aage badho
        curr = next_node       # curr aage badho
    return prev                # prev ab naya head
```

**Logic kyun (yeh core — dhyan se, 3 pointers):** har node pe hum uska `next` pointer **ulta** karte
(agle ke bajaye pichhle ko point kare). 3 variables: `prev` (pichhla), `curr` (abhi), `next_node`
(agla — pehle yaad rakho warna link toot ke kho jaayega). Loop ke ant mein `prev` = naya head.
**O(n) time, O(1) space.**

**Dry-run (Input 1->2->3->None):**
```
prev=None, curr=1
step1: next_node=2. curr(1).next=None(prev). prev=1, curr=2.   List: None<-1  2->3
step2: next_node=3. curr(2).next=1(prev).    prev=2, curr=3.   None<-1<-2  3
step3: next_node=None. curr(3).next=2(prev). prev=3, curr=None. None<-1<-2<-3
curr=None -> loop end. return prev=3.  Result: 3->2->1->None  ✓
```

**Recursive solution (O(n) time, O(n) space — call stack):**
```python
def reverse_recursive(head):
    if not head or not head.next:      # base case: khaali ya ek node
        return head
    new_head = reverse_recursive(head.next)  # baaki ko reverse karo
    head.next.next = head              # agle node ko peeche point karao
    head.next = None                   # apna next None (naya end)
    return new_head
```
- Recursion se bhi hota (Ch 07 recursion). O(n) space (call stack, Ch 2.4). Iterative usually
  preferred (O(1) space), par dono aane chahiye.

> **Yaad rakhne wali baat:** Reverse LL iterative = 3 pointers (prev, curr, next_node): `next_node`
> yaad rakho → `curr.next=prev` (ulta) → dono aage. `prev` = naya head. O(n)/O(1). Recursive bhi
> (O(n) space). Classic pointer-manipulation — zaroor yaad.

[↑ Back to top](#top)

---

<a id="s6-3"></a>
## 6.3 — LL Pattern: Fast-slow pointers (cycle, middle)

Do pointers alag speed se chalao — ek **slow** (1 step) ek **fast** (2 step). Isse cycle detect karna
aur middle dhoondhna O(n)/O(1) mein hota. Yeh two-pointer (Ch 3.3) ka LL version.

**Kab pehchano (signal):** "cycle detect karo", "middle node", "kth from end".

**Sub-pattern A — Detect Cycle (Floyd's algorithm):**

**Problem:** kya linked list mein cycle hai (koi node peeche kisi node ko point karta, loop)?
```
Input:  1 -> 2 -> 3 -> 4 -> 2 (4 wapas 2 ko point)  -> Output: True (cycle)
Input:  1 -> 2 -> 3 -> None                          -> Output: False
```
```python
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next          # 1 step
        fast = fast.next.next     # 2 step
        if slow == fast:          # mil gaye -> cycle!
            return True
    return False                  # fast None tak pahuncha -> no cycle
```

**Logic kyun (yeh classic — dhyan se):** fast 2x speed se chalta. Agar cycle hai, fast aur slow
kabhi na kabhi **same node pe mil jaayenge** (jaise race-track pe tez daudne wala dheere wale ko lap
kar deta). Agar cycle nahi, fast `None` tak pahunch ke ruk jayega. **O(n) time, O(1) space** (koi
extra memory nahi — hashing se bhi ho sakta par O(n) space, yeh better).

**Dry-run (Input 1->2->3->4->2 cycle):**
```
slow=1, fast=1
step: slow=2, fast=3. alag.
step: slow=3, fast=2 (4->2 cycle). alag.
step: slow=4, fast=4. SAME! return True  ✓
```

**Sub-pattern B — Find Middle Node:**

**Problem:** linked list ka middle node dhoondho.
```
Input:  1 -> 2 -> 3 -> 4 -> 5  -> Output: node 3 (middle)
Input:  1 -> 2 -> 3 -> 4        -> Output: node 3 (do middle mein doosra)
```
```python
def find_middle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next          # 1 step
        fast = fast.next.next     # 2 step
    return slow                   # fast end pe -> slow middle pe
```
- Jab fast end pe pahunchta (2x speed), slow exactly **middle** pe hota. **O(n)/O(1).** Elegant.

> **Yaad rakhne wali baat:** Fast-slow pointers: slow 1-step, fast 2-step. Cycle detect (Floyd's):
> agar mil gaye toh cycle. Middle: fast end pe -> slow middle. O(n)/O(1) (hashing se better — no
> extra space). Signal: cycle/middle/kth-from-end.

[↑ Back to top](#top)

---

<a id="s6-4"></a>
## 6.4 — LL Pattern: Merge two sorted lists + dummy node

Do sorted linked lists ko ek sorted list mein merge karna — common, aur **dummy node** trick
sikhata (jo bahut LL problems mein kaam aata).

**Problem — Merge Two Sorted Lists:**

**Problem:** do sorted linked lists di. Ek sorted list mein merge karo.
```
Input:  l1: 1 -> 2 -> 4,  l2: 1 -> 3 -> 4
Output: 1 -> 1 -> 2 -> 3 -> 4 -> 4
```
```python
def merge_two_lists(l1, l2):
    dummy = ListNode(0)        # dummy: fake head (simplifies logic)
    tail = dummy               # tail: result ka aakhri node
    while l1 and l2:
        if l1.val <= l2.val:
            tail.next = l1     # chhota wala jodo
            l1 = l1.next
        else:
            tail.next = l2
            l2 = l2.next
        tail = tail.next       # tail aage
    tail.next = l1 or l2       # jo bacha (ek list khatam, doosri ka baaki)
    return dummy.next          # dummy.next = asli head
```

**Logic kyun (dummy node trick — yeh yaad rakho):** dono lists ke heads compare karo, chhota result
mein jodo, us list mein aage badho. **Dummy node** ek "fake" starting node hai — isse humein "pehla
node special-case" nahi karna padta (warna `if result is None` har baar). `tail` result ka aakhri
node track karta. Ant mein `dummy.next` = asli head. **O(n+m) time, O(1) space.**

**Dry-run (Input l1: 1->2->4, l2: 1->3->4):**
```
dummy->[]. tail=dummy
l1.val=1 <= l2.val=1: tail.next=l1(1), l1=2. tail=1.  Result: 1
l1.val=2 > l2.val=1: tail.next=l2(1), l2=3. tail=1.   Result: 1->1
l1.val=2 <= l2.val=3: tail.next=l1(2), l1=4. tail=2.  Result: 1->1->2
l1.val=4 > l2.val=3: tail.next=l2(3), l2=4. tail=3.   Result: 1->1->2->3
l1.val=4 <= l2.val=4: tail.next=l1(4), l1=None. tail=4. Result: 1->1->2->3->4
l1=None -> loop end. tail.next = l2 (4). Result: 1->1->2->3->4->4  ✓
```

**Dummy node kyun powerful:** bahut LL problems (merge, remove, insert) mein "head badal sakta hai"
ka special-case aata. Dummy node se aap hamesha `dummy.next` return karte — head-special-case gaya.
Yeh clean-code trick hai (Ch 1.8).

> **Yaad rakhne wali baat:** Merge sorted LLs: dono heads compare, chhota jodo, aage. **Dummy node**
> = fake head (head-special-case bachata, `dummy.next` return). `tail` aakhri track. `tail.next =
> l1 or l2` (bacha hua). O(n+m)/O(1). Dummy-node trick bahut LL problems mein.

[↑ Back to top](#top)

---

<a id="s6-5"></a>
## 6.5 — Stack kya hai (LIFO) + valid parentheses

**Stack** = ek dher (pile) jahan aap sirf **upar** se add/remove karte — **LIFO** (Last In First Out:
jo aakhri mein daala, woh pehle nikalta). Jaise plates ka dher — upar wali pehle uthao.

**Python mein stack = list (end pe push/pop):**
```python
stack = []
stack.append(5)      # push (upar daalo) — O(1)
stack.append(3)
top = stack[-1]      # peek (upar dekho, nikaalo nahi) — 3
x = stack.pop()      # pop (upar se nikaalo) — 3, O(1)
```
- `append` = push, `pop` = pop, `stack[-1]` = peek. Sab O(1) (end pe). LIFO.

**Kab pehchano (signal):** "matching/nesting" (brackets), "last-seen chahiye", "undo", "next
greater" (6.6), "reverse-order process".

**Classic problem — Valid Parentheses:**

**Problem:** string mein `()`, `[]`, `{}` hain. Kya sab sahi tarah matched aur nested hain?
```
Input:  s="()[]{}"  -> Output: True
Input:  s="([)]"    -> Output: False  (galat nesting)
Input:  s="(]"      -> Output: False
Input:  s="{[]}"    -> Output: True   (sahi nested)
```
```python
def is_valid(s):
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}   # closing -> opening
    for ch in s:
        if ch in pairs:                       # closing bracket
            if not stack or stack.pop() != pairs[ch]:
                return False                  # match nahi / stack khaali
        else:                                 # opening bracket
            stack.append(ch)                  # push
    return len(stack) == 0                     # sab matched? stack khaali hona chahiye
```

**Logic kyun (LIFO perfect for nesting):** opening bracket aaye toh stack pe push. Closing aaye toh
stack ke **top** (aakhri opening) se match karo — kyunki sahi nesting mein aakhri-khula pehle-band
hota (LIFO!). Match nahi ya stack khaali → invalid. Ant mein stack khaali hona chahiye (sab matched).
**O(n) time, O(n) space.**

**Dry-run (Input s="{[]}"):**
```
'{': opening -> push. stack=['{']
'[': opening -> push. stack=['{','[']
']': closing -> stack.pop()='[' == pairs[']']='[' ✓. stack=['{']
'}': closing -> stack.pop()='{' == pairs['}']='{' ✓. stack=[]
end: stack khaali -> return True  ✓
```

> **Yaad rakhne wali baat:** Stack = LIFO (last-in-first-out), Python `list` (`append`/`pop`/`[-1]`,
> O(1)). Valid-parens: opening push, closing top se match (LIFO = aakhri-khula pehle-band). Ant mein
> stack khaali. Signal: matching/nesting/last-seen/reverse-order. O(n).

[↑ Back to top](#top)

---

<a id="s6-6"></a>
## 6.6 — Stack Pattern: Monotonic stack (next greater)

**Monotonic stack** = ek stack jo hamesha ek order (increasing ya decreasing) mein rehta. Yeh "next
greater/smaller element" type problems mein O(n) deta — jo brute-force O(n^2) hoti. Thoda advanced
par common, isliye samajhna zaroori.

**Kab pehchano (signal):** "next greater/smaller element", "previous greater", "stock span", "daily
temperatures", "histogram".

**Classic problem — Next Greater Element:**

**Problem:** array `nums` diya. Har element ke liye, uske **daayen** pehla **bada** element dhoondho
(na ho toh -1).
```
Input:  nums=[2, 1, 2, 4, 3]
Output: [4, 2, 4, -1, -1]
        (2 ke aage pehla bada 4; 1 ke aage 2; 2 ke aage 4; 4 ke aage koi bada nahi -1; 3 ke -1)
```

**Brute force:** har element ke liye aage scan → O(n^2).

**Monotonic stack solution (O(n) time):**
```python
def next_greater(nums):
    result = [-1] * len(nums)     # default -1
    stack = []                    # indices, decreasing values (monotonic)
    for i in range(len(nums)):
        # jab tak stack ke top se current bada hai, unka answer current hai
        while stack and nums[i] > nums[stack[-1]]:
            idx = stack.pop()
            result[idx] = nums[i]  # idx ke liye next-greater = nums[i]
        stack.append(i)
    return result
```

**Logic kyun (yeh core — dhyan se):** stack mein hum **indices** rakhte hain jinka "next greater"
abhi tak nahi mila (decreasing values). Jab ek naya element aata jo stack-top se **bada** hai, toh
woh un sab ka "next greater" hai jo usse chhote hain — pop karke unka answer set karo. Har element
ek baar push, ek baar pop → **O(n) time.** Yeh "har element ke liye aage/peeche pehla bada/chhota"
ka standard tool.

**Dry-run (Input nums=[2,1,2,4,3]):**
```
i=0 (2): stack empty. push. stack=[0]
i=1 (1): 1 > nums[0]=2? No. push. stack=[0,1]
i=2 (2): 2 > nums[1]=1? Yes. pop 1, result[1]=2. 2 > nums[0]=2? No. push. stack=[0,2]. result=[-1,2,-1,-1,-1]
i=3 (4): 4 > nums[2]=2? Yes. pop 2, result[2]=4. 4 > nums[0]=2? Yes. pop 0, result[0]=4. push. stack=[3]. result=[4,2,4,-1,-1]
i=4 (3): 3 > nums[3]=4? No. push. stack=[3,4]
end. result=[4,2,4,-1,-1]  ✓
```

**Note (Ch 1.5):** monotonic stack medium-level hai, aate hain (daily-temperatures, next-greater),
par histogram-area jaise hard versions rare. Basic next-greater samajh lo — kaafi.

> **Yaad rakhne wali baat:** Monotonic stack = stack jismein indices ordered (inc/dec). Next-greater:
> jab current > stack-top, pop karke unka answer set. Har element ek push+pop = O(n) (brute O(n^2)).
> Signal: "next/previous greater/smaller", daily-temperatures, stock-span.

[↑ Back to top](#top)

---

<a id="s6-7"></a>
## 6.7 — Queue kya hai (FIFO) + deque

**Queue** = ek line (kataar) jahan aap **peeche** se add, **aage** se remove karte — **FIFO** (First
In First Out: jo pehle aaya, pehle nikalta). Jaise ticket-line — pehla aadmi pehle serve. Stack (LIFO)
ka ulta.

**Python mein queue = `collections.deque` (NOT list):**
```python
from collections import deque

q = deque()
q.append(5)          # peeche add (enqueue) — O(1)
q.append(3)
front = q[0]         # aage dekho — 5
x = q.popleft()      # aage se nikaalo (dequeue) — 5, O(1)
```
- **ZAROORI — `deque` use karo, list nahi:** list ka `pop(0)` (front se) **O(n)** hai (baaki shift,
  Ch 2.8)! `deque.popleft()` **O(1)**. Queue ke liye hamesha `deque`.

**Deque = double-ended queue (dono taraf O(1)):**
```python
dq = deque()
dq.append(1)         # right add
dq.appendleft(2)     # left add — O(1)
dq.pop()             # right remove — O(1)
dq.popleft()         # left remove — O(1)
```
- `deque` dono ends pe O(1) — isliye queue (FIFO) aur monotonic-deque (6.8) dono ke liye.

**Kab pehchano (signal):** "FIFO order", "BFS" (Ch 08/10 — level-by-level), "process in order",
"sliding window max" (6.8).

**Queue ka #1 use — BFS (Breadth-First Search):** trees/graphs mein level-by-level traverse (Ch
08/10). Queue mein nodes daalte, aage se nikaalke unke bachche peeche daalte — FIFO se level-order
hota. (Poora Ch 08/10 mein; abhi jaan lo queue = BFS ka engine.)

```python
# BFS ka skeleton (Ch 08/10 mein poora)
from collections import deque
def bfs(start):
    q = deque([start])
    while q:
        node = q.popleft()      # aage se (FIFO)
        # process node
        for neighbor in node.neighbors:
            q.append(neighbor)  # peeche add
```

> **Yaad rakhne wali baat:** Queue = FIFO (first-in-first-out), Python `collections.deque` (NOT
> list — list ka `pop(0)` O(n)!). `append` (peeche) / `popleft` (aage), O(1). Deque = dono ends O(1).
> #1 use: BFS (level-by-level, Ch 08/10). Signal: FIFO/BFS/in-order-process.

[↑ Back to top](#top)

---

<a id="s6-8"></a>
## 6.8 — Queue Pattern: Monotonic deque (sliding window max)

Monotonic deque (deque jo ordered rehta) ek specific powerful problem solve karta — **sliding window
maximum** — O(n) mein (brute O(n*k)). Yeh advanced-ish par classic hai.

**Problem — Sliding Window Maximum:**

**Problem:** array `nums` aur window-size `k`. Har size-k window ka **maximum** dhoondho.
```
Input:  nums=[1, 3, -1, -3, 5, 3, 6, 7], k=3
Output: [3, 3, 5, 5, 6, 7]
        (window [1,3,-1]max=3, [3,-1,-3]max=3, [-1,-3,5]max=5, ...)
```

**Brute force:** har window ka max nikaalo → O(n*k). Monotonic deque se O(n).

**Monotonic deque solution (O(n) time):**
```python
from collections import deque

def max_sliding_window(nums, k):
    dq = deque()              # indices, decreasing values (front = max)
    result = []
    for i in range(len(nums)):
        # 1. window se bahar wale indices hatao (front se)
        if dq and dq[0] < i - k + 1:
            dq.popleft()
        # 2. peeche se chhote elements hatao (yeh kabhi max nahi banenge)
        while dq and nums[dq[-1]] < nums[i]:
            dq.pop()
        dq.append(i)
        # 3. window bharne ke baad, front = current window ka max
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result
```

**Logic kyun (thoda advanced — samajhne ka try):** deque mein **indices** rakhte hain aise ki unki
values **decreasing** ho — toh `dq[0]` (front) hamesha current window ka **max**. Jab naya element
aaye, peeche se saare chhote hata dete (woh kabhi max nahi banenge jab tak bada hai). Aur window se
bahar nikal gaye index ko front se hata dete. Har index ek baar add+remove → **O(n).** (Yeh Ch 1.5
ka medium-hard hai — samajh lo, par agar mushkil lage toh basic queue/BFS zyada important hai.)

**Dry-run (Input nums=[1,3,-1,-3,5,3,6,7], k=3, pehle 3 windows):**
```
i=0(1): dq=[0]
i=1(3): nums[0]=1<3 pop. dq=[1]
i=2(-1): nums[1]=3<-1? no. dq=[1,2]. i>=2 -> result=[nums[1]]=[3]
i=3(-3): front 1 < 3-3+1=1? no. nums[2]=-1<-3? no. dq=[1,2,3]. front=1 out? 1<1 no. result=[3, nums[1]=3]
i=4(5): front 1 < 4-2=2? yes popleft. dq=[2,3]. nums[3]=-3<5 pop, nums[2]=-1<5 pop. dq=[4]. result=[3,3,5]
...
return [3,3,5,5,6,7]  ✓
```

> **Yaad rakhne wali baat:** Monotonic deque = deque with decreasing values (front=max). Sliding-
> window-max: naya aaye toh peeche-se-chhote hatao + window-bahar front hatao, front=max. Har index
> ek add+remove = O(n) (brute O(n*k)). Advanced — basic queue/BFS pehle solid karo.

[↑ Back to top](#top)

---

<a id="s6-9"></a>
## 6.9 — Nuances, kab kaunsa, edge cases

**Signal→pattern (is chapter ke):**

| Signal | Structure/Pattern | Section |
|---|---|---|
| LL reverse/rearrange | Linked list reversal (3 pointers) | 6.2 |
| Cycle / middle / kth-from-end | Fast-slow pointers | 6.3 |
| Merge/combine LLs | Merge + dummy node | 6.4 |
| Matching/nesting (brackets) | Stack (LIFO) | 6.5 |
| Next/previous greater/smaller | Monotonic stack | 6.6 |
| FIFO / BFS / level-order | Queue (deque) | 6.7 |
| Sliding window max/min | Monotonic deque | 6.8 |

**Stack vs Queue (kab kaunsa — yaad rakho):**
- **Stack (LIFO):** "last-seen chahiye", nesting/matching, reverse-order, next-greater, backtracking
  (Ch 07 recursion internally stack). "Aakhri pehle."
- **Queue (FIFO):** "order-mein process", BFS/level-order, "pehla pehle". "Pehla pehle."

**Edge cases (HAMESHA):**
- **Empty list/None head** — LL functions: `if not head`. Stack/queue: `if not stack` before pop
  (warna IndexError).
- **Single node** — reverse (same), cycle (fast.next None -> no cycle), middle (woh node).
- **Pop empty stack/queue** — `stack.pop()` on `[]` = IndexError. Pehle `if stack` check.
- **Cycle mein infinite loop** — LL traverse karte waqt cycle ho toh loop kabhi na ruke; fast-slow
  ya visited-set se detect.

**Python-specific (zaroori):**
- **Queue ke liye `deque`, list nahi** (6.7) — list `pop(0)` O(n), deque `popleft()` O(1).
- **Stack ke liye list theek** (`append`/`pop` end pe O(1)).
- **LL problems mein dummy node** (6.4) — head-special-case bachata, clean code.

**Kab yeh NAHI:** LL index-access chahiye (O(n) slow) → array better. Random-access zaroori → array.
LL sirf jab sequential + bahut insert/delete.

> **Yaad rakhne wali baat:** Stack (LIFO) = nesting/last-seen/next-greater; Queue (FIFO) = BFS/order.
> LL: reverse (3-pointer), fast-slow (cycle/middle), dummy-node (merge). Edge: empty/None/single, pop-
> empty (check pehle), cycle-infinite-loop. Python: queue=deque, stack=list.

[↑ Back to top](#top)

---

<a id="s6-10"></a>
## 6.10 — Yaad rakhne wali baatein (chapter recap)

1. **Linked list** (6.1): nodes chain (`{val, next}`), index O(n) but front-insert O(1). `curr=
   curr.next` traverse.
2. **Reversal** (6.2): 3 pointers (prev, curr, next_node), `curr.next=prev`. O(n)/O(1). Classic.
3. **Fast-slow** (6.3): slow 1-step + fast 2-step. Cycle (mil gaye), middle (fast end→slow middle).
   O(n)/O(1).
4. **Merge + dummy node** (6.4): compare heads, chhota jodo; dummy = head-special-case bachata.
5. **Stack (LIFO)** (6.5): `list` append/pop O(1). Valid-parens (opening push, closing top-match).
   Nesting/matching.
6. **Monotonic stack** (6.6): ordered indices, next-greater/smaller O(n) (brute O(n^2)).
7. **Queue (FIFO)** (6.7): `deque` (NOT list!) append/popleft O(1). BFS ka engine.
8. **Monotonic deque** (6.8): sliding-window-max O(n).

> **Chapter ka mantra:** LL = pointer-manipulation (reverse, fast-slow, dummy-node — inhe pakka
> karo, aate hain). Stack = LIFO (nesting, next-greater). Queue = FIFO (BFS — Ch 08/10 mein bahut
> aayega). Python: queue=deque, stack=list. Basics solid karo; monotonic-stack/deque medium — samajh
> lo par pehle basics.

[↑ Back to top](#top)

---

> **Chapter 06 khatam.** Ab tak: linked list (reversal, fast-slow cycle/middle, merge+dummy-node);
> stack LIFO (valid-parens, monotonic-stack/next-greater); queue FIFO (deque, BFS-engine, monotonic-
> deque/sliding-window-max); signal→pattern + stack-vs-queue + edge cases. **Agla chapter (07):**
> Recursion + Backtracking — base/recursive case, subsets, permutations, combinations, grid
> backtracking.

[↑ Back to top](#top)
