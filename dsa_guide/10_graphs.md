<a id="top"></a>
# Chapter 10 — Graphs: BFS, DFS, Islands, Topological Sort, Union-Find

Graphs Google/Microsoft mein bahut common hain (Ch 1.4 — HIGH, ~12%), khaaskar **grid problems**
(islands). Graph = nodes + connections (edges) — trees ka general roop (jo cycles allow karta). Yeh
chapter core graph patterns sikhata — BFS/DFS pe khada (Ch 08 se juda).

Clear examples + diagrams + dry-run ke saath.

---

## Is chapter ka index

- [10.1 — Graph kya hai (representation)](#s10-1)
- [10.2 — DFS on graph (with visited-set)](#s10-2)
- [10.3 — BFS on graph (shortest path unweighted)](#s10-3)
- [10.4 — Grid as graph: Number of Islands](#s10-4)
- [10.5 — Connected components + cycle detection](#s10-5)
- [10.6 — Topological Sort (dependency order)](#s10-6)
- [10.7 — Union-Find (Disjoint Set)](#s10-7)
- [10.8 — Nuances, kab kaunsa, edge cases](#s10-8)
- [10.9 — Yaad rakhne wali baatein](#s10-9)

---

<a id="s10-1"></a>
## 10.1 — Graph kya hai (representation)

**Graph** = **nodes** (vertices — points) + **edges** (connections — inhe jodne wali lines). Tree ek
special graph tha (no cycle, ek root); general graph mein cycles ho sakti, koi root nahi zaroori.
Real-world: social network (log = nodes, friendship = edges), map (cities + roads), dependencies.

**Do types:**
- **Directed** — edges ki direction (A→B, ek taraf). Jaise Twitter follow (A follows B, ulta zaroori
  nahi).
- **Undirected** — edges dono taraf (A-B = B-A). Jaise Facebook friendship (mutual).

**Representation (Python mein — adjacency list, most common):**
```python
# adjacency list: har node -> uske neighbors ki list
graph = {
    0: [1, 2],       # node 0 juda 1, 2 se
    1: [0, 3],       # node 1 juda 0, 3 se
    2: [0],
    3: [1]
}
```
- **Adjacency list** = dict/list jahan har node ke neighbors listed. Space O(V + E) (V=vertices,
  E=edges). Sabse common (interview mein yehi). (Adjacency matrix — 2D array — bhi hota, par dense
  graphs ke liye; list zyada common.)

**Ek graph dikhta kaisa:**
```
    0 --- 1
    |     |
    2     3
graph = {0:[1,2], 1:[0,3], 2:[0], 3:[1]}  (undirected)
```

**Graph vs Tree (farak):** tree = connected, no cycle, ek root, V-1 edges. Graph = cycles allowed,
disconnected ho sakta, koi root nahi. Toh graph mein **visited-set** ZAROORI (cycle mein infinite
loop na ho — 10.2). Tree mein nahi chahiye tha (no cycle).

**Do core traversals (Ch 08 se juda):** graph bhi DFS (gehrai) aur BFS (level/chaudai) se traverse
hota — par **visited-set** ke saath (cycle handle). Yeh do (BFS/DFS) 80% graph problems ka base.

> **Yaad rakhne wali baat:** Graph = nodes + edges (connections). Directed (A→B) ya undirected (A-B).
> Adjacency list (`{node: [neighbors]}`) most common, O(V+E) space. Tree se farak: cycles allowed,
> no root → **visited-set zaroori** (infinite-loop bachaao). Core: BFS + DFS.

[↑ Back to top](#top)

---

<a id="s10-2"></a>
## 10.2 — DFS on graph (with visited-set)

**DFS** graph pe = ek neighbor mein **gehre** tak jaao, phir wapas (Ch 08 tree-DFS jaisa), par
**visited-set** ke saath (taaki cycle mein baar-baar na ghumen).

**DFS recursive (yeh template YAAD rakho):**
```python
def dfs(graph, node, visited):
    if node in visited:          # already dekha -> ruko (cycle-safe)
        return
    visited.add(node)            # mark visited
    print(node)                  # process
    for neighbor in graph[node]:
        dfs(graph, neighbor, visited)   # har neighbor mein gehre jaao
```

**Logic kyun (visited-set = graph vs tree ka farak):** graph mein cycle ho sakti (A→B→A), toh bina
visited-set DFS infinite loop mein ghusega. `visited` set mein "jo dekha" rakhte, aur already-dekha
node skip. Har node ek baar visit → **O(V + E)** (V nodes + E edges). Yeh Ch 08 tree-DFS + visited
= graph DFS.

**DFS iterative (stack, Ch 6.5 — jab recursion na chahiye):**
```python
def dfs_iterative(graph, start):
    visited = set()
    stack = [start]
    while stack:
        node = stack.pop()       # LIFO (DFS)
        if node in visited:
            continue
        visited.add(node)
        print(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                stack.append(neighbor)
```

**Dry-run (graph {0:[1,2], 1:[0,3], 2:[0], 3:[1]}, DFS from 0):**
```
dfs(0): visited={0}, process 0. neighbors 1,2
  dfs(1): visited={0,1}, process 1. neighbors 0(visited),3
    dfs(0): visited -> ruko
    dfs(3): visited={0,1,3}, process 3. neighbor 1(visited)
  dfs(2): visited={0,1,3,2}, process 2. neighbor 0(visited)
Visited order: 0, 1, 3, 2  (gehre pehle)
```

**Kab DFS (signal):** "connected hai kya", "path exist karta", "cycle detect", "explore all reachable",
"islands" (10.4), backtracking-on-graph. Gehrai/reachability.

> **Yaad rakhne wali baat:** Graph DFS = gehre-tak (Ch 08 tree-DFS + **visited-set** — cycle-safe,
> infinite-loop bachaao). Recursive: `if node in visited return; visited.add; recurse neighbors`.
> O(V+E). Iterative = stack. Signal: connected/path/cycle/reachable/islands.

[↑ Back to top](#top)

---

<a id="s10-3"></a>
## 10.3 — BFS on graph (shortest path unweighted)

**BFS** graph pe = level-by-level (Ch 8.3 tree-BFS jaisa), queue se, visited-set ke saath. Iska
**superpower: unweighted graph mein shortest path** (km-se-km edges).

**BFS (queue + visited — yeh template YAAD rakho):**
```python
from collections import deque

def bfs(graph, start):
    visited = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()       # FIFO
        print(node)                  # process
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
```

**BFS for shortest path (unweighted — yeh key use):**
```python
def shortest_path(graph, start, target):
    visited = {start}
    queue = deque([(start, 0)])      # (node, distance)
    while queue:
        node, dist = queue.popleft()
        if node == target:
            return dist              # pehli baar mila = shortest!
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))
    return -1                        # nahi mila
```

**Logic kyun (BFS = shortest in unweighted):** BFS level-by-level failta — pehle 1-edge-door sab,
phir 2-edge-door sab. Toh jab target **pehli baar** milta, woh **minimum edges** (shortest path) se
mila hai. Yeh BFS ka superpower — unweighted shortest path. (Weighted ke liye Dijkstra — Ch 1.5 skip,
rare.) **O(V + E).**

**DFS vs BFS on graph (kab kaunsa — yaad rakho):**
- **DFS:** connected?/path-exist/cycle/explore-all. Gehrai. Recursion simple, km memory (aksar).
- **BFS:** **shortest path (unweighted)**, level-wise, "minimum steps". Queue.
- Signal "shortest/minimum steps/fewest" → **BFS**. "Exists/reachable/all" → DFS (dono chal jate).

**Dry-run (shortest 0 to 3, graph {0:[1,2],1:[0,3],2:[0],3:[1]}):**
```
queue=[(0,0)]. pop (0,0). neighbors 1,2 -> queue=[(1,1),(2,1)]
pop (1,1). 1==3? no. neighbor 3 -> queue=[(2,1),(3,2)]
pop (2,1). neighbors 0(visited)
pop (3,2). 3==3! return 2  ✓  (0->1->3, 2 edges)
```

> **Yaad rakhne wali baat:** Graph BFS = level-by-level (Ch 8.3 + visited), queue. Superpower:
> **unweighted shortest path** (pehli baar mila = minimum edges). `(node, dist)` track. O(V+E).
> Signal "shortest/minimum-steps" → BFS; "exists/all" → DFS.

[↑ Back to top](#top)

---

<a id="s10-4"></a>
## 10.4 — Grid as graph: Number of Islands

**Grid problems** (2D array) graphs mein sabse common interview type. Ek grid = graph jahan har cell
ek node, aur adjacent cells (up/down/left/right) edges. "Number of Islands" classic.

**Problem — Number of Islands:**

**Problem:** 2D grid of `'1'` (land) aur `'0'` (water). Kitne islands (connected land groups)?
```
Input:  grid = [["1","1","0","0"],
                ["1","1","0","0"],
                ["0","0","1","0"],
                ["0","0","0","1"]]
Output: 3   (top-left 4 cells = 1 island, middle 1 = 2nd, bottom-right 1 = 3rd)
```
```python
def num_islands(grid):
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])
    count = 0

    def dfs(r, c):
        # out of bounds ya water ya visited -> ruko
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != "1":
            return
        grid[r][c] = "0"             # mark visited (land -> water, taaki dobara na)
        dfs(r + 1, c)                # 4 directions
        dfs(r - 1, c)
        dfs(r, c + 1)
        dfs(r, c - 1)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":    # naya island mila
                count += 1
                dfs(r, c)            # poora island "sink" kar do (visited mark)
    return count
```

**Logic kyun (yeh core — grid = graph):** har cell scan karo. Jab ek `'1'` (land) mile jo abhi visited
nahi, woh ek **naya island** — count++. Phir DFS se us island ke **saare connected land** ko visited
mark karo (`'1'`→`'0'`, taaki dobara na gino). DFS 4 directions (up/down/left/right = grid mein
"neighbors/edges"). **O(rows × cols)** — har cell ek baar. Yeh "grid ko graph samajh ke DFS/BFS" ka
sabse common pattern (flood-fill).

**Dry-run (upar wala grid, high-level):**
```
Scan cells:
(0,0)='1' -> naya island! count=1. DFS sinks (0,0),(0,1),(1,0),(1,1) -> sab '0'
... (aage ke cells jo island the woh ab '0', skip)
(2,2)='1' -> naya! count=2. DFS sinks (2,2)
(3,3)='1' -> naya! count=3. DFS sinks (3,3)
return 3  ✓
```

**Related (same pattern):** flood-fill (paint), max-area-of-island, surrounded-regions — sab "grid
DFS/BFS + visited mark". Ek baar yeh pattern samajh liya, saari grid problems similar.

> **Yaad rakhne wali baat:** Grid = graph (cell=node, adjacent=edges). Islands: scan cells, naya '1'
> mile → count++ + DFS-sink poora island (visited mark '1'→'0'). DFS 4 directions. O(rows×cols).
> Flood-fill/max-area same pattern. Sabse common graph interview type.

[↑ Back to top](#top)

---

<a id="s10-5"></a>
## 10.5 — Connected components + cycle detection

Do common graph tasks — **connected components** (kitne alag-alag jude groups) aur **cycle detection**
(loop hai kya). Dono DFS/BFS + visited pe.

**Connected Components:**

**Problem:** undirected graph mein kitne alag connected groups hain?
```
Input:  n=5 nodes, edges = [[0,1], [1,2], [3,4]]
Output: 2   ({0,1,2} ek group, {3,4} doosra)
```
```python
def count_components(n, edges):
    graph = {i: [] for i in range(n)}
    for a, b in edges:                    # adjacency list banao
        graph[a].append(b)
        graph[b].append(a)                # undirected -> dono taraf
    visited = set()
    count = 0

    def dfs(node):
        visited.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                dfs(neighbor)

    for node in range(n):
        if node not in visited:           # naya component mila
            count += 1
            dfs(node)                     # poora component visit
    return count
```
- **Logic:** islands (10.4) jaisa hi! Har un-visited node = naya component (count++), DFS se poora
  component mark. Islands = grid version; yeh general-graph version. **O(V+E).**

**Cycle Detection (undirected — DFS with parent):**

**Problem:** undirected graph mein cycle hai kya?
```python
def has_cycle_undirected(n, edges):
    graph = {i: [] for i in range(n)}
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    visited = set()

    def dfs(node, parent):
        visited.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                if dfs(neighbor, node):
                    return True
            elif neighbor != parent:      # visited AND parent nahi -> cycle!
                return True
        return False

    for node in range(n):
        if node not in visited:
            if dfs(node, -1):
                return True
    return False
```
- **Logic (undirected cycle):** DFS karte waqt, agar ek **visited** neighbor mile jo current node ka
  **parent nahi** hai, toh cycle (kisi aur raste se pehle is node tak pahunche the). Parent-check
  isliye ki undirected mein A-B edge se B ko A "visited neighbor" dikhega, par woh parent hai (cycle
  nahi). **O(V+E).**
- (Directed graph cycle detection thoda alag — "recursion stack" track — 10.6 topo-sort se juda.)

> **Yaad rakhne wali baat:** Connected components = islands (10.4) ka general-graph version — un-
> visited node se DFS, count++. Cycle (undirected) = DFS mein visited-neighbor-jo-parent-nahi → cycle
> (parent-check). Dono O(V+E). Signal: "kitne groups", "cycle/loop hai kya".

[↑ Back to top](#top)

---

<a id="s10-6"></a>
## 10.6 — Topological Sort (dependency order)

**Topological sort** = directed graph ke nodes ko aise order mein lagana ki har edge A→B mein A, B
se **pehle** aaye. "Dependencies pehle" — jaise course prerequisites, build order, task scheduling.

**Kab pehchano (signal):** "order/sequence with dependencies", "prerequisites", "build order",
"course schedule", "kaunsa pehle karna".

**Problem — Course Schedule (order):**

**Problem:** `n` courses, prerequisites `[a, b]` (a karne se pehle b zaroori). Valid order dhoondho
(ya empty agar cycle — impossible).
```
Input:  n=4, prerequisites=[[1,0], [2,0], [3,1], [3,2]]
Output: [0, 1, 2, 3]  (0 pehle, phir 1,2, phir 3 — dependencies respect)
```

**Kahn's Algorithm (BFS-based topo-sort — yeh yaad rakho):**
```python
from collections import deque

def topo_sort(n, prerequisites):
    graph = {i: [] for i in range(n)}
    in_degree = [0] * n                   # har node pe kitni incoming edges
    for course, prereq in prerequisites:
        graph[prereq].append(course)      # prereq -> course
        in_degree[course] += 1
    # start: 0 in-degree wale (koi dependency nahi)
    queue = deque([i for i in range(n) if in_degree[i] == 0])
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:      # is node ko "remove" karo
            in_degree[neighbor] -= 1      # neighbors ki dependency ghati
            if in_degree[neighbor] == 0:  # ab koi dependency nahi -> ready
                queue.append(neighbor)
    return order if len(order) == n else []  # sab aaye? warna cycle (impossible)
```

**Logic kyun (Kahn's — in-degree):** **in-degree** = ek node pe kitni incoming edges (kitni
dependencies). "0 dependency" wale pehle process kar sakte (unka koi prerequisite nahi). Process
karne ke baad, unke neighbors ki dependency ghatao (ek prerequisite pura hua); jinki 0 ho gayi woh
ready. BFS se yeh order banta. **Agar sab n nodes order mein nahi aaye → cycle** (circular
dependency, impossible). **O(V+E).**

**Dry-run (Input n=4, prereqs=[[1,0],[2,0],[3,1],[3,2]]):**
```
graph: 0->[1,2], 1->[3], 2->[3]. in_degree: [0,1,1,2]
queue=[0] (in_degree 0). 
pop 0: order=[0]. neighbors 1,2 -> in_degree[1]=0, in_degree[2]=0 -> queue=[1,2]
pop 1: order=[0,1]. neighbor 3 -> in_degree[3]=1
pop 2: order=[0,1,2]. neighbor 3 -> in_degree[3]=0 -> queue=[3]
pop 3: order=[0,1,2,3]
len(order)==4 -> return [0,1,2,3]  ✓
```

**Cycle detect via topo:** agar order mein saare nodes nahi aaye (kuch ki in-degree kabhi 0 nahi hui),
toh cycle hai — jaise course-schedule "possible?" (True/False) problems.

> **Yaad rakhne wali baat:** Topological sort = directed graph, dependencies-pehle order. Kahn's
> (BFS): in-degree (incoming count), 0-in-degree se start, process karke neighbors ki in-degree
> ghatao, 0 hote hi ready. Sab na aaye = cycle. O(V+E). Signal: prerequisites/build-order/schedule.

[↑ Back to top](#top)

---

<a id="s10-7"></a>
## 10.7 — Union-Find (Disjoint Set)

**Union-Find** (Disjoint Set Union, DSU) ek structure hai jo "kaunse elements ek group mein hain" fast
track karta — do main operations: **union** (do groups jodo) aur **find** (kis group mein hai). Cycle
detection, connected-components mein alternative to DFS.

**Kab pehchano (signal):** "connected/same-group hai kya", "groups merge", "cycle in undirected",
"number of provinces/components".

**Basic Union-Find (with path-compression):**
```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))      # har node apna khud ka parent (start)

    def find(self, x):                    # x kis group ka (root)?
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])   # path compression
        return self.parent[x]

    def union(self, x, y):                # x, y ke groups jodo
        root_x, root_y = self.find(x), self.find(y)
        if root_x != root_y:
            self.parent[root_x] = root_y  # ek root ko doosre se jodo
            return True                   # jude (alag the)
        return False                      # already same group (union nahi hua)
```

**Logic kyun (yeh core):** har group ka ek "root/representative". `find(x)` = x ka root dhoondho
(chain follow). `union(x,y)` = dono ke roots jodo (ek ko doosre ka child). **Path compression**
(`find` mein `parent[x] = root`) — chain flatten, future finds fast. Union/find ~**O(1) amortised**
(almost). Yeh "same group?" ko super-fast banata.

**Use — Cycle detection / components:**
```python
def has_cycle(n, edges):
    uf = UnionFind(n)
    for a, b in edges:
        if not uf.union(a, b):        # union False = already same group = cycle!
            return True
    return False
```
- **Logic:** har edge pe union karo. Agar dono nodes **pehle se same group** mein (union False), toh
  yeh edge ek cycle banata (dono already jude the). Elegant cycle-detect.

**Dry-run (cycle detect, n=3, edges=[[0,1],[1,2],[0,2]]):**
```
uf: parent=[0,1,2]
union(0,1): roots 0,1 alag -> join. parent=[1,1,2]. True
union(1,2): roots find(1)=1, find(2)=2 alag -> join. parent=[1,2,2]. True
union(0,2): find(0)=find(1)=2, find(2)=2. SAME! union False -> cycle! return True  ✓
```

**Union-Find vs DFS (kab):** connected-components/cycle dono se hote. Union-Find better jab **edges
ek-ek aate** (dynamic — "ab yeh jude, ab woh") ya "same-group?" queries baar-baar. DFS better jab
poora graph pehle se hai aur ek baar traverse. Dono valid; union-find "grouping" mein elegant.

> **Yaad rakhne wali baat:** Union-Find (DSU): `find(x)` (x ka root/group), `union(x,y)` (groups
> jodo). Path-compression → ~O(1) amortised. Cycle: union False (already same group) = cycle.
> Signal: same-group?/merge-groups/components/undirected-cycle. DFS alternative (dynamic edges pe
> better).

[↑ Back to top](#top)

---
<a id="s10-8"></a>
## 10.8 — Nuances, kab kaunsa, edge cases

**Signal to pattern (graphs):**

| Signal | Pattern | Section |
|---|---|---|
| Explore all / path-exists / reachable | DFS | 10.2 |
| Shortest path (unweighted) / min-steps | BFS | 10.3 |
| Grid land/water/regions | Grid DFS/BFS (flood-fill) | 10.4 |
| Kitne groups / connected | Components (DFS ya union-find) | 10.5 |
| Cycle / loop | DFS (parent-check) ya union-find | 10.5/10.7 |
| Dependencies / prerequisites / order | Topological sort (Kahn's) | 10.6 |
| Same-group? / merge / dynamic-connect | Union-Find | 10.7 |

**Edge cases (HAMESHA - graphs mein bahut):**
- **Disconnected graph** - sab nodes ek group mein nahi. Loop over ALL nodes (jo un-visited, DFS
  fresh) - warna kuch components miss (10.5).
- **Empty graph / single node** - 0 ya 1 handle.
- **Cycle** - bina visited-set infinite loop (10.1). Visited ZAROORI.
- **Self-loop / duplicate edges** - kabhi input mein; visited-set handle karta.
- **Directed vs undirected** - undirected mein edge dono taraf add (`graph[a].append(b)` AND
  `graph[b].append(a)`). Directed mein sirf ek taraf. Galti common.

**Visited-set placement (common bug):** BFS mein neighbor ko **queue mein daalte waqt** visited mark
karo (pop pe nahi) - warna ek node multiple baar queue mein aa sakta (duplicate processing). DFS mein
entry pe mark.

**Kab kaunsa (BFS vs DFS vs Union-Find - yaad rakho):**
- **Shortest path (unweighted)** -> BFS (level-by-level).
- **Just explore / path-exists / islands** -> DFS (simple recursion) ya BFS (dono chal jate).
- **Dependencies/order** -> Topological sort.
- **Dynamic grouping / same-group queries** -> Union-Find.

**SKIP (Ch 1.5 - rare in SR ML):** Dijkstra deep (weighted shortest - intuition kaafi), MST
(Kruskal/Prim), max-flow, bipartite matching, Tarjan/SCC. Inka one-line pata ho, deep nahi.

> **Yaad rakhne wali baat:** Graph signals: explore->DFS, shortest->BFS, grid->flood-fill, groups->
> components/union-find, order->topo-sort, same-group->union-find. Edge: disconnected (loop ALL
> nodes), visited-set-zaroori (cycle), directed-vs-undirected (edge dono/ek taraf). BFS mark-on-
> enqueue. SKIP: Dijkstra-deep/MST/flow.

[↑ Back to top](#top)

---

<a id="s10-9"></a>
## 10.9 — Yaad rakhne wali baatein (chapter recap)

1. **Graph** (10.1): nodes+edges (directed/undirected), adjacency-list (`{node:[neighbors]}`). Tree
   se farak: cycles -> **visited-set zaroori**.
2. **DFS** (10.2): gehre-tak + visited-set. Recursive (`if visited return; add; recurse`) ya stack.
   O(V+E). Explore/path/reachable.
3. **BFS** (10.3): level-by-level, queue + visited. **Unweighted shortest path** (pehli baar mila =
   min edges). O(V+E).
4. **Grid = graph** (10.4): islands/flood-fill - scan, naya land -> count + DFS-sink. 4 directions.
   Sabse common.
5. **Components + cycle** (10.5): un-visited se DFS (components), visited-neighbor-not-parent (cycle).
6. **Topological sort** (10.6): Kahn's - in-degree, 0-in-degree start, process->ghatao. Dependencies/
   order. Sab na aaye = cycle.
7. **Union-Find** (10.7): find/union, path-compression ~O(1). Same-group/merge/cycle.

> **Chapter ka mantra:** Graphs = **BFS + DFS** (visited-set ke saath - cycle-safe). Grid-islands
> (flood-fill) sabse common, zaroor pakka. BFS = shortest (unweighted), DFS = explore. Topo-sort
> (dependencies), union-find (grouping) - bhi aate. Google/MS favourite - LeetCode pe 5-6 graph
> problems (islands, BFS/DFS, topo-sort).

[↑ Back to top](#top)

---

> **Chapter 10 khatam.** Ab tak: graph (adjacency-list, visited-set); DFS + BFS (BFS=unweighted
> shortest); grid-islands/flood-fill; connected-components + cycle-detection; topological-sort
> (Kahn's); union-find (DSU). **Agla chapter (11):** Binary Search + Sorting - binary-search
> variants, on-answer-space, rotated-array, sorting overview, quickselect.

[↑ Back to top](#top)
