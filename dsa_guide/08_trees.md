<a id="top"></a>
# Chapter 08 — Trees: Traversals, BST, Tree Recursion, Trie

Trees Google/Microsoft ki **favourite** hain (Ch 1.4 — HIGH, ~12%). Ek tree = nodes ki hierarchy
(jaise family tree, folder structure). Yeh chapter tree traversals, BST (binary search tree), aur
tree-recursion patterns sikhata — recursion (Ch 07) ka seedha application.

Clear examples + tree-diagrams + dry-run ke saath.

---

## Is chapter ka index

- [8.1 — Tree kya hai (aur binary tree)](#s8-1)
- [8.2 — Traversals: DFS (pre/in/post-order)](#s8-2)
- [8.3 — Traversal: BFS / level-order](#s8-3)
- [8.4 — Tree recursion pattern (height, etc.)](#s8-4)
- [8.5 — BST (Binary Search Tree): search, insert, validate](#s8-5)
- [8.6 — Common tree problems (diameter, LCA, path-sum)](#s8-6)
- [8.7 — Trie (prefix tree) — short intro](#s8-7)
- [8.8 — Nuances, edge cases, kab kaunsa](#s8-8)
- [8.9 — Yaad rakhne wali baatein](#s8-9)

---

<a id="s8-1"></a>
## 8.1 — Tree kya hai (aur binary tree)

**Tree** = nodes ki ek hierarchy — ek **root** (sabse upar) se shuru, har node ke **children**
(bachche) hote, aur woh aage branch karte. Cycle nahi hoti (linked list branch-out, Ch 06). Jaise
family tree ya folder structure (Ch 2 filesystem — woh bhi tree tha!).

**Binary Tree** = har node ke **at most 2 children** (left aur right). Sabse common interview tree.

**Python mein node (standard — yaad rakho):**
```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val         # is node ki value
        self.left = left       # left child (ya None)
        self.right = right     # right child (ya None)
```

**Ek binary tree dikhta kaisa:**
```
        1          <- root
       / \
      2   3
     / \   \
    4   5   6      <- leaves (koi child nahi = 4,5,6)
```
- `root` = 1 (top). `1` ke children: 2 (left), 3 (right). `4,5,6` = **leaves** (no children).
  **Height** = root se sabse gehre leaf tak ka distance (yahan 2). **Depth** of a node = root se us
  node tak.

**Zaroori terms (yaad rakho):**
- **Root** — top node. **Leaf** — no-children node. **Parent/Child** — upar/neeche wala.
- **Subtree** — kisi node aur uske neeche sab (khud ek tree). Yeh recursion ki chaabi (8.4).
- **Height** — sabse lamba root-to-leaf path. **Balanced** — left/right heights ~barabar.

**Kyun trees recursion-friendly (yeh core insight):** ek tree ki definition khud recursive hai — "ek
node + left-subtree + right-subtree", aur subtrees bhi trees hain! Toh zyadatr tree problems
**recursion se natural** solve hote (Ch 07 trust): "node pe kaam karo + left-subtree recurse +
right-subtree recurse". Yeh pattern baar-baar aayega.

**Complexity:** tree ke saare n nodes visit = **O(n)**. Balanced tree ki height = **O(log n)**
(BST search fast). Skewed (ek taraf) tree height O(n).

> **Yaad rakhne wali baat:** Tree = nodes ki hierarchy (root top, children neeche, leaves no-child,
> no cycle). Binary tree = max 2 children (left/right). Node = `{val, left, right}`. Tree def khud
> recursive (node + 2 subtrees) → recursion-friendly. All-nodes visit O(n), balanced height O(log n).

[↑ Back to top](#top)

---

<a id="s8-2"></a>
## 8.2 — Traversals: DFS (pre/in/post-order)

**Traversal** = tree ke saare nodes ko ek order mein visit karna. **DFS** (Depth-First Search) — ek
branch mein **gehre** tak jaao, phir wapas. Teen orders (kab node ko "process" karte, uspe depend):

- **Pre-order:** **Node** → Left → Right (node pehle).
- **In-order:** Left → **Node** → Right (node beech mein).
- **Post-order:** Left → Right → **Node** (node aakhri mein).

**Recursive DFS (yeh yaad rakho — bahut simple, recursion Ch 07):**
```python
def preorder(node):
    if not node:                # base case: None -> ruko
        return
    print(node.val)             # NODE (pehle) — pre-order
    preorder(node.left)         # LEFT
    preorder(node.right)        # RIGHT

def inorder(node):
    if not node:
        return
    inorder(node.left)          # LEFT
    print(node.val)             # NODE (beech) — in-order
    inorder(node.right)         # RIGHT

def postorder(node):
    if not node:
        return
    postorder(node.left)        # LEFT
    postorder(node.right)       # RIGHT
    print(node.val)             # NODE (aakhri) — post-order
```

**Farak sirf `print(node.val)` ki JAGAH ka (yeh key insight):** teeno bilkul same, bs node ko kab
process karte — pehle (pre), beech (in), aakhri (post). Yaad rakhne ka tareeka: **naam batata node
kab** (pre=pehle, post=baad, in=beech).

**Dry-run (upar wala tree, pre-order):**
```
Tree:    1
        / \
       2   3
      / \   \
     4   5   6
Pre-order (Node-Left-Right): 1, 2, 4, 5, 3, 6
  (1 pehle -> left subtree: 2 pehle -> 4 -> 5 -> phir right subtree: 3 -> 6)
In-order (Left-Node-Right):  4, 2, 5, 1, 3, 6
Post-order (Left-Right-Node): 4, 5, 2, 6, 3, 1
```

**In-order ka special (BST ke liye — 8.5):** **BST** mein in-order traversal nodes ko **sorted order**
mein deta! Yeh bahut kaam ka property (BST validate, kth-smallest).

**Iterative DFS (stack se — jab recursion na chahiye):** recursion ke bajaye explicit **stack** (Ch
6.5) use karke bhi DFS hota. (Interview mein recursive usually kaafi; iterative pata hona achha.)
```python
def preorder_iterative(root):
    if not root: return []
    stack, result = [root], []
    while stack:
        node = stack.pop()
        result.append(node.val)
        if node.right: stack.append(node.right)  # right pehle push (stack LIFO)
        if node.left: stack.append(node.left)    # left baad -> left pehle process
    return result
```

> **Yaad rakhne wali baat:** DFS = gehre-tak-phir-wapas. 3 orders (node kab process): pre (Node-L-R),
> in (L-Node-R), post (L-R-Node) — farak sirf `process` ki jagah. Recursive simple (base None). BST
> mein IN-ORDER = sorted! Iterative = stack (LIFO).

[↑ Back to top](#top)

---

<a id="s8-3"></a>
## 8.3 — Traversal: BFS / level-order

**BFS** (Breadth-First Search) — tree ko **level-by-level** (upar se neeche, har level poora) traverse.
DFS gehre-tak jaata; BFS **chaudai** mein (ek level poora phir agla). Queue (Ch 6.7 — FIFO) ka #1 use.

**Kab pehchano (signal):** "level-by-level", "level order", "shortest path in tree", "right-side
view", "level ka max/sum".

**Level-order (BFS with queue — yeh yaad rakho):**
```python
from collections import deque

def level_order(root):
    if not root:
        return []
    result = []
    queue = deque([root])           # queue mein root
    while queue:
        level_size = len(queue)     # is level mein kitne nodes
        level = []
        for _ in range(level_size): # poora current level process
            node = queue.popleft()  # aage se (FIFO)
            level.append(node.val)
            if node.left: queue.append(node.left)    # bachche peeche add
            if node.right: queue.append(node.right)
        result.append(level)        # ek level done
    return result
```

**Logic kyun (queue = level-order engine):** queue mein root daalo. Har iteration mein **poora current
level** process karo (`level_size` = abhi queue mein jitne = current level ke nodes), unke bachche
peeche add karo. FIFO ki wajah se level-by-level order hota (parent pehle process, phir uske bachche
next level). `level_size` snapshot lena zaroori — taaki current level ke nodes hi process ho (naye
bachche agle level mein). **O(n) time.**

**Dry-run (upar wala tree, level-order):**
```
Tree:    1
        / \
       2   3
      / \   \
     4   5   6
queue=[1]. level_size=1: process 1, add 2,3. result=[[1]]. queue=[2,3]
level_size=2: process 2 (add 4,5), process 3 (add 6). result=[[1],[2,3]]. queue=[4,5,6]
level_size=3: process 4,5,6 (no children). result=[[1],[2,3],[4,5,6]]. queue=[]
return [[1], [2,3], [4,5,6]]  ✓ (level-by-level)
```

**DFS vs BFS (kab kaunsa — yaad rakho):**
- **DFS (recursion/stack):** "gehrai", path-related (root-to-leaf, height, path-sum), tree structure.
  Simple recursive.
- **BFS (queue):** "level-by-level", shortest-path (unweighted), level-wise info (level max/sum,
  right-side-view). Queue.

> **Yaad rakhne wali baat:** BFS = level-by-level (chaudai), queue (FIFO). `level_size = len(queue)`
> snapshot se poora current-level process, bachche peeche add. O(n). Signal: level-order/shortest-
> path/level-info. DFS (gehrai, recursion) vs BFS (level, queue).

[↑ Back to top](#top)

---

<a id="s8-4"></a>
## 8.4 — Tree recursion pattern (height, etc.)

Yeh tree problems ka **sabse important pattern** — recursion (Ch 07) ka natural application.
Zyadatr tree problems isi shape mein: "node pe kaam + left recurse + right recurse + combine".

**General tree-recursion shape (yeh template YAAD rakho):**
```python
def solve(node):
    if not node:                     # base case: None -> base value
        return base_value
    left = solve(node.left)          # left-subtree ka answer
    right = solve(node.right)        # right-subtree ka answer
    return combine(node.val, left, right)   # dono + node se apna answer
```

**Classic example — Height of tree:**

**Problem:** binary tree ki height (root se sabse gehre leaf tak edges/levels).
```
Input:    1          -> Output: 3 (levels: 1 -> 2 -> 4, teen levels)
         / \
        2   3
       /
      4
```
```python
def height(node):
    if not node:                     # base: empty tree, height 0
        return 0
    left_h = height(node.left)       # left subtree ki height
    right_h = height(node.right)     # right subtree ki height
    return 1 + max(left_h, right_h)  # apni height = 1 + bade child ki
```

**Logic kyun (trust the recursion, Ch 7.3):** hum **maan lete** ki `height(node.left)` left-subtree
ki sahi height dega (trust!). Toh current node ki height = `1 + max(left_height, right_height)` (1
apna, + jo bhi child taller). Base: None → 0. **Yeh "combine children's answers" pattern har tree
problem mein.**

**Dry-run (upar wala tree):**
```
height(1):
  height(2):
    height(4):
      height(None)=0, height(None)=0 -> 1+max(0,0)=1
    height(None)=0 -> 1+max(1,0)=2       (node 2 ki height 2)
  height(3):
    height(None)=0, height(None)=0 -> 1+max(0,0)=1
  -> 1 + max(2, 1) = 3                   (root height 3)  ✓
```

**Aur examples isi pattern se:**
```python
# Count total nodes
def count_nodes(node):
    if not node: return 0
    return 1 + count_nodes(node.left) + count_nodes(node.right)  # apna 1 + dono

# Sum of all values
def tree_sum(node):
    if not node: return 0
    return node.val + tree_sum(node.left) + tree_sum(node.right)

# Max value in tree
def tree_max(node):
    if not node: return float('-inf')
    return max(node.val, tree_max(node.left), tree_max(node.right))
```
- **Dekho — teeno same shape:** base (None → base value), recurse left+right, combine with node.
  Yeh recognize karo: **90% tree problems = yeh template + alag combine.**

> **Yaad rakhne wali baat:** Tree recursion template: base (None → base value) → `left=solve(node.
> left)`, `right=solve(node.right)` → `combine(node.val, left, right)`. Height = `1+max(L,R)`, count
> = `1+L+R`, sum = `val+L+R`. Trust recursion (Ch 7.3). 90% tree problems = yeh + alag combine.

[↑ Back to top](#top)

---

<a id="s8-5"></a>
## 8.5 — BST (Binary Search Tree): search, insert, validate

**BST** = ek binary tree with ek special property: har node ke liye, **left-subtree ke saare values
chhote**, **right-subtree ke saare values bade**. Yeh property search ko O(log n) (balanced) banati.

**BST property (yeh core):**
```
        5
       / \
      3   8       Har node: left < node < right
     / \   \      (3<5, 8>5; 1<3<4; 8<9)
    1   4   9
```
- Node 5: left-subtree (3,1,4) sab <5, right-subtree (8,9) sab >5. Yeh **har** node pe true.

**Search (O(log n) balanced — binary search Ch 11 jaisa):**
```python
def search_bst(node, target):
    if not node or node.val == target:   # mil gaya ya None
        return node
    if target < node.val:
        return search_bst(node.left, target)   # chhota -> left
    else:
        return search_bst(node.right, target)  # bada -> right
```
- BST property se: target chhota → sirf left dekho (right sab bade, bekaar). Bada → right. Har step
  **aadha** tree chhod dete (binary search!). Balanced BST → **O(log n)**. (Skewed → O(n).)

**Insert (similar logic):**
```python
def insert_bst(node, val):
    if not node:
        return TreeNode(val)             # jagah mili, naya node
    if val < node.val:
        node.left = insert_bst(node.left, val)   # left mein
    else:
        node.right = insert_bst(node.right, val) # right mein
    return node
```

**Validate BST (common problem — dhyan se):**

**Problem:** kya diya gaya tree valid BST hai?
```python
def is_valid_bst(node, low=float('-inf'), high=float('inf')):
    if not node:
        return True
    if not (low < node.val < high):      # node apni valid range mein hai?
        return False
    # left ke liye upper-bound = node.val; right ke liye lower-bound = node.val
    return (is_valid_bst(node.left, low, node.val) and
            is_valid_bst(node.right, node.val, high))
```
- **Logic kyun (range-check, common trap):** sirf `left < node < right` check karna **kaafi nahi** —
  poore left-subtree ke saare nodes chhote hone chahiye (sirf direct child nahi). Isliye har node ki
  ek **valid range** `(low, high)` pass karte — left mein jaate waqt `high = node.val`, right mein
  `low = node.val`. Yeh galti (sirf immediate children check) common hai — range-check sahi hai.
- **Alternative:** in-order traversal (8.2) — BST ka in-order **sorted** hota, toh in-order karke
  check karo strictly-increasing hai.

**Dry-run (validate, range-check):**
```
Tree valid? Root 5 (range -inf,inf): -inf<5<inf ok
  left 3 (range -inf,5): ok. right 8 (range 5,inf): ok
  ... har node apni tightening range mein -> True
```

> **Yaad rakhne wali baat:** BST = left<node<right (har node, poore subtree). Search/insert: chhota→
> left, bada→right (aadha chhodo, O(log n) balanced). Validate: **range-check** (low,high pass — left
> pe high=val, right pe low=val), NOT sirf immediate-children. BST in-order = sorted.

[↑ Back to top](#top)

---

<a id="s8-6"></a>
## 8.6 — Common tree problems (diameter, LCA, path-sum)

Kuch classic tree problems jo baar-baar aate — sab 8.4 wala "recurse + combine" pattern use karte,
bs combine alag.

**Problem 1 — Maximum Depth (height, 8.4 recap):** already dekha — `1 + max(left, right)`.

**Problem 2 — Diameter of Tree:**

**Problem:** tree ka diameter = kisi bhi do nodes ke beech sabse lamba path (edges mein).
```
Input:    1          -> Output: 3
         / \             (path 4->2->1->3, ya 5->2->1->3: 3 edges)
        2   3
       / \
      4   5
```
```python
def diameter(root):
    max_diameter = 0
    def height(node):
        nonlocal max_diameter
        if not node:
            return 0
        left = height(node.left)
        right = height(node.right)
        max_diameter = max(max_diameter, left + right)  # is node se guzarne wala path
        return 1 + max(left, right)                     # height (8.4)
    height(root)
    return max_diameter
```
- **Logic:** har node pe, us node se **guzarne wala** sabse lamba path = `left_height + right_height`
  (left ke gehre tak + right ke gehre tak). Overall max track. Height compute karte-karte (8.4)
  diameter bhi nikaal lete. **O(n).** (Trick: height-recursion ke andar diameter update.)

**Problem 3 — Lowest Common Ancestor (LCA):**

**Problem:** do nodes `p`, `q` ka lowest (sabse neeche) common ancestor dhoondho.
```
Input:    3          p=5, q=1  -> Output: 3  (5 aur 1 ka common ancestor 3)
         / \         p=5, q=4  -> Output: 5  (4, 5 ke neeche hai)
        5   1
       / \
      6   4
```
```python
def lca(root, p, q):
    if not root or root == p or root == q:  # base: mil gaya ya None
        return root
    left = lca(root.left, p, q)
    right = lca(root.right, p, q)
    if left and right:            # dono taraf mile -> yeh node LCA
        return root
    return left or right          # ek taraf mila -> woh (ya None)
```
- **Logic:** har node se poocho "p ya q neeche mile?". Agar `p`,`q` **alag-alag** subtrees mein
  (left aur right dono se kuch mila), toh yeh node LCA. Agar dono ek hi taraf, wahin aage. **O(n).**

**Problem 4 — Path Sum:**

**Problem:** kya koi root-to-leaf path hai jiska sum = target?
```python
def has_path_sum(node, target):
    if not node:
        return False
    if not node.left and not node.right:   # leaf
        return node.val == target
    remaining = target - node.val
    return (has_path_sum(node.left, remaining) or
            has_path_sum(node.right, remaining))
```
- **Logic:** target se node-value ghatte jaao, leaf pe check `remaining == leaf.val`. Koi path mile
  toh True. **O(n).**

> **Yaad rakhne wali baat:** Common tree problems (sab recurse+combine): diameter (`left_h+right_h`
> max, height ke andar), LCA (dono-taraf-mile → yeh LCA, warna jo-taraf-mila), path-sum (target
> ghatte, leaf pe check). Sab O(n). Pattern same (8.4), combine alag.

[↑ Back to top](#top)

---

<a id="s8-7"></a>
## 8.7 — Trie (prefix tree) — short intro

**Trie** (bolte "try", prefix tree) ek special tree hai **strings/prefixes** ke liye — jahan har node
ek character, aur root-se-path ek word/prefix banata. Autocomplete, spell-check, prefix-search mein
use. Interview mein kabhi aata (Ch 1.5 — brief, deep nahi).

**Kab pehchano (signal):** "prefix", "autocomplete", "dictionary of words", "starts-with".

**Basic Trie (insert + search + prefix):**
```python
class TrieNode:
    def __init__(self):
        self.children = {}       # char -> TrieNode
        self.is_end = False      # yahan koi word khatam hota?

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()   # naya char node
            node = node.children[ch]
        node.is_end = True       # word khatam yahan

    def search(self, word):      # poora word hai?
        node = self._find(word)
        return node is not None and node.is_end

    def starts_with(self, prefix):   # koi word is prefix se shuru?
        return self._find(prefix) is not None

    def _find(self, s):
        node = self.root
        for ch in s:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node
```

**Logic kyun (prefix sharing):** words ko character-by-character store karte, common prefixes **share**
hote (jaise "cat" aur "car" mein "ca" ek hi path). `is_end` batata kahan word khatam. Search/insert
= **O(word length)** (word ke chars ke barabar). Prefix-search fast — yeh trie ka fayda over hash-set
(jismein prefix-search O(n) hota).

**Example (insert "cat", "car", search):**
```
root -> c -> a -> t (is_end)
              \-> r (is_end)
insert("cat"), insert("car"): "ca" shared, phir t/r branch
search("cat") -> path mila + is_end -> True
search("ca")  -> path mila but is_end=False -> False (word nahi, prefix hai)
starts_with("ca") -> path mila -> True
```

**Note (Ch 1.5):** trie basics kaafi (insert/search/prefix). Advanced (delete, wildcard) rare. Aata
hai jab "prefix/autocomplete/dictionary" signal ho — tab yeh recognize karo.

> **Yaad rakhne wali baat:** Trie = prefix tree for strings. Node = `{children: char→node, is_end}`.
> Insert/search = O(word-length), prefix-search fast (hash-set se better). Common prefixes share.
> Signal: prefix/autocomplete/starts-with/dictionary. Basics kaafi (Ch 1.5).

[↑ Back to top](#top)

---

<a id="s8-8"></a>
## 8.8 — Nuances, edge cases, kab kaunsa

**Signal→pattern (trees):**

| Signal | Pattern | Section |
|---|---|---|
| Saare nodes visit / path-related | DFS (pre/in/post recursion) | 8.2 |
| Level-by-level / shortest / level-info | BFS (queue) | 8.3 |
| Height/count/sum/max/most tree problems | Tree recursion (recurse+combine) | 8.4 |
| Sorted tree / search-insert / kth-smallest | BST (left<node<right) | 8.5 |
| Diameter / LCA / path-sum | Tree recursion (specific combine) | 8.6 |
| Prefix / autocomplete / dictionary | Trie | 8.7 |

**Edge cases (HAMESHA — trees mein bahut common):**
- **Empty tree (None root)** — har function `if not node`. Sabse common tree edge case.
- **Single node** — root = leaf. Height 1 (ya 0, definition pe), traversal = [root].
- **Skewed tree** (ek taraf, jaise linked-list) — height O(n), recursion depth O(n) (stack-overflow
  risk bahut deep pe).
- **Unbalanced BST** — search O(n) (not O(log n)). BST guarantee sirf balanced pe.
- **Duplicate values** — BST mein duplicates ka rule problem-specific (left ya right?) — clarify.

**Recursion depth (Ch 7.9 recap):** deep/skewed tree → recursion depth O(n) → Python RecursionError
(~1000 default). Bahut bade trees pe iterative (stack/queue) safer. Interview mein usually recursive
kaafi.

**Kab kaunsa (DFS vs BFS — yaad rakho):**
- **DFS (recursion):** height, path-sum, diameter, "poora subtree ka kuch", validate. Default for
  most tree problems (simple recursion).
- **BFS (queue):** level-order, level-wise info (level max/sum/avg), shortest-path-in-tree,
  right-side-view. Jab "level" shabd aaye.

**Kab tree NAHI:** agar cycles ho sakti (node peeche point kare) → woh graph hai (Ch 10), tree nahi.
Tree = no cycle, ek root, har node ek parent.

> **Yaad rakhne wali baat:** Tree signals: traverse→DFS, level→BFS, height/count→recurse+combine,
> sorted/search→BST, prefix→trie. Edge: empty(None)/single/skewed(O(n) depth)/unbalanced-BST.
> DFS=most problems (recursion), BFS=level-info (queue). Cycle ho toh graph (Ch 10) na tree.

[↑ Back to top](#top)

---

<a id="s8-9"></a>
## 8.9 — Yaad rakhne wali baatein (chapter recap)

1. **Tree** (8.1): hierarchy (root/children/leaves, no cycle). Binary = max 2 children. Node =
   `{val, left, right}`. Recursion-friendly (node + 2 subtrees).
2. **DFS traversals** (8.2): pre (Node-L-R), in (L-Node-R), post (L-R-Node) — farak sirf process-
   jagah. Recursive simple. BST in-order = **sorted**.
3. **BFS/level-order** (8.3): queue (FIFO), `level_size` snapshot se level-by-level. O(n).
4. **Tree recursion template** (8.4): base(None) → left+right recurse → combine(node, L, R). Height
   `1+max(L,R)`, count `1+L+R`. **90% tree problems = yeh.**
5. **BST** (8.5): left<node<right. Search/insert chhota→left/bada→right (O(log n) balanced). Validate
   = range-check.
6. **Common problems** (8.6): diameter (L_h+R_h), LCA (dono-taraf→yeh), path-sum. Recurse+combine.
7. **Trie** (8.7): prefix tree, insert/search O(word-len), prefix-search fast.

> **Chapter ka mantra:** Trees = recursion (Ch 07). **"Node pe kaam + left recurse + right recurse +
> combine"** — yeh template 90% tree problems solve karta (bs combine badalta). Traversals (DFS 3
> orders, BFS level), BST (sorted property), aur recurse+combine solid karo. Google/MS favourite —
> LeetCode pe 5-6 tree problems.

[↑ Back to top](#top)

---

> **Chapter 08 khatam.** Ab tak: tree basics; DFS traversals (pre/in/post + iterative); BFS level-
> order (queue); tree-recursion template (height/count/sum); BST (search/insert/validate + in-order
> sorted); diameter/LCA/path-sum; trie (prefix tree). **Agla chapter (09):** Heaps + Priority Queues
> — top-K, k-frequent, two-heaps median, heapq.

[↑ Back to top](#top)