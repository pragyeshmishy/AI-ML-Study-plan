<a id="top"></a>
# Chapter 04 — Hashing: Hash Map/Set se O(1) Lookup ka Superpower

Hashing DSA ka sabse zyada kaam aane wala tool hai (Ch 1.4 — HIGH priority, ~12%). Iska ek
superpower hai: **kisi cheez ko O(1) mein dhoondh lena** (ek-ek dekhne ki O(n) ke bajaye). Bahut
saari O(n^2) brute-force problems hashing se O(n) ho jaati — isliye interview mein baar-baar aata.

Yeh chapter hash-map/set kaise kaam karta, aur uske core patterns (two-sum, frequency, dedup,
subarray-sum) sikhata — clear examples aur dry-run ke saath.

---

## Is chapter ka index

- [4.1 — Hash map/set kya hai (aur O(1) kaise)](#s4-1)
- [4.2 — Python mein dict aur set (basics)](#s4-2)
- [4.3 — Pattern 1: Seen-set (dekha hai kya?)](#s4-3)
- [4.4 — Pattern 2: Two Sum (unsorted array)](#s4-4)
- [4.5 — Pattern 3: Frequency counting](#s4-5)
- [4.6 — Pattern 4: Group anagrams (key banana)](#s4-6)
- [4.7 — Pattern 5: Prefix-sum + hashmap (subarray sum = k)](#s4-7)
- [4.8 — Nuances, edge cases, aur kab hashing NAHI](#s4-8)
- [4.9 — Yaad rakhne wali baatein](#s4-9)

---

<a id="s4-1"></a>
## 4.1 — Hash map/set kya hai (aur O(1) kaise)

**Hash map** (Python mein `dict`) = key→value ka store, jahan aap ek **key** se uski **value** turant
(O(1)) nikaal sakte ho. **Hash set** (Python `set`) = sirf keys ka store (values nahi) — "yeh cheez
hai ya nahi" O(1) mein batata.

**O(1) kaise (thoda intuition):** hash map ek "hash function" use karta jo key ko ek number (memory
address/bucket) mein badal deta. Toh key dete hi woh seedha us bucket pe jaata — dhoondhna nahi
padta (ek-ek dekhne wali O(n) nahi). Yeh "seedha jump" hi O(1) deta. (Deep internals interview mein
zaroori nahi — bs "average O(1) lookup" yaad rakho.)

**Analogy:** socho ek dictionary (shabdkosh) — aap "apple" shabd seedha 'A' section mein dhoondhte ho,
poori book nahi padhte. Hash map waisa hi — key se seedha jagah pe pahunchta.

**Kyun itna powerful (yeh core insight):** bahut problems mein aapko "kya yeh element pehle dekha
hai?" ya "is cheez ki value kya hai?" baar-baar poochna padta. List mein yeh O(n) (ek-ek dekho),
par hash-map/set mein **O(1)**. Isse ek nested-loop (O(n^2)) aksar single-loop (O(n)) ban jata. Yeh
DSA ka sabse common "optimize" trick hai (Ch 2.5 time-space tradeoff — memory de ke time bachaya).

**Complexity (Ch 2.6 recap):**
- Insert / lookup / delete — **O(1) average** (superpower).
- Extra space — **O(n)** (n items store karne padte).

> **Yaad rakhne wali baat:** Hash map (`dict`) = key→value, O(1) lookup. Hash set (`set`) = "hai ya
> nahi" O(1). Superpower: "dekha hai kya / value kya" ko O(n) list-search se O(1) banata — nested
> loop (O(n^2)) ko single (O(n)). Cost: O(n) extra memory (time-space tradeoff).

[↑ Back to top](#top)

---

<a id="s4-2"></a>
## 4.2 — Python mein dict aur set (basics)

Interview Python mein hota, toh `dict`/`set` fluently aana chahiye. Quick recap:

**dict (hash map) — key→value:**
```python
d = {}                    # khaali dict
d["apple"] = 5            # key "apple" -> value 5
d["banana"] = 3
print(d["apple"])         # 5  (O(1) lookup)
print("apple" in d)       # True  (key hai kya? O(1))
print(d.get("mango", 0))  # 0  (mango nahi hai -> default 0, KeyError nahi)
del d["banana"]           # delete
for key, val in d.items(): # iterate
    print(key, val)
```

**set (hash set) — sirf keys, unique:**
```python
s = set()                 # khaali set
s.add(5)                  # add
s.add(5)                  # dobara 5 -> kuch nahi (unique)
print(5 in s)             # True  (O(1))
s.remove(5)               # delete
print(len(s))             # kitne unique
```

**Do bahut kaam ke tools (`collections` se):**
```python
from collections import Counter, defaultdict

# Counter: frequency count ek line mein (4.5)
c = Counter("aabbbc")     # Counter({'b':3, 'a':2, 'c':1})
print(c["b"])             # 3

# defaultdict: missing key pe default value (KeyError nahi)
dd = defaultdict(int)     # missing key -> 0
dd["x"] += 1              # "x" nahi tha -> 0, phir +1 = 1  (KeyError nahi!)
dd_list = defaultdict(list)  # missing key -> []
dd_list["y"].append(3)    # "y" nahi tha -> [], phir append
```

**Zaroori — `dict.get()` aur `defaultdict` kyun:** normal `d["missing"]` **KeyError** deta (crash).
`d.get(key, default)` ya `defaultdict` se safe — missing key pe default. Yeh frequency/grouping
patterns mein bahut kaam aata (aage), aur bug bachata.

**Ek gotcha (Ch 2.8 recap):** `x in list` = O(n), par `x in set/dict` = O(1). Fast lookup chahiye toh
list nahi, set/dict use karo. Yeh common mistake hai jo O(n^2) bana deta.

> **Yaad rakhne wali baat:** `dict` = key→value (`d[k]`, `d.get(k, default)` safe), `set` = unique
> membership (`x in s` O(1)). `Counter` = frequency ek line mein, `defaultdict(int/list)` = missing
> key pe default (KeyError bachata). `in set/dict` O(1), `in list` O(n) — set/dict use karo.

[↑ Back to top](#top)

---

<a id="s4-3"></a>
## 4.3 — Pattern 1: Seen-set (dekha hai kya?)

Sabse simple hashing pattern — ek **set** mein "jo dekha woh yaad rakho", aur har naye element pe
poocho "pehle dekha hai kya?". Duplicates, cycles, ya "pehle aa chuka" type problems mein.

**Kab pehchano (signal):** "duplicate hai kya", "pehle dekha", "unique elements".

**Classic problem — Contains Duplicate:**

**Problem:** array `nums` diya. Kya koi element **do baar** aata hai? True/False.
```
Input:  nums=[1, 2, 3, 1]  -> Output: True   (1 do baar hai)
Input:  nums=[1, 2, 3, 4]  -> Output: False  (sab unique)
Input:  nums=[]            -> Output: False  (empty)
```

**Brute force:** har pair check → O(n^2). (Ch 2.3 wala `has_duplicate`.)

**Seen-set solution (O(n) time):**
```python
def contains_duplicate(nums):
    seen = set()                # jo dekha
    for num in nums:
        if num in seen:         # pehle dekha? O(1)
            return True         # duplicate mila!
        seen.add(num)           # ab yaad rakho
    return False
```

**Logic kyun:** har element pe pehle poocho "seen mein hai?" (O(1)). Hai → duplicate, return True.
Nahi → add karo. Ek pass, har check O(1) → **O(n) time, O(n) space** (set). Brute O(n^2) se behtar —
classic time-space tradeoff (Ch 2.5).

**Dry-run (Input nums=[1,2,3,1]):**
```
num=1: seen={} mein 1 nahi. seen={1}
num=2: 2 nahi. seen={1,2}
num=3: 3 nahi. seen={1,2,3}
num=1: 1 HAI seen mein! return True  ✓
```

> **Yaad rakhne wali baat:** Seen-set: ek set mein "jo dekha yaad rakho", har naye pe "dekha hai
> kya?" (O(1)). Signal: duplicate/pehle-dekha/unique. O(n) time+space (brute O(n^2) se behtar). Sabse
> simple hashing pattern.

[↑ Back to top](#top)

---

<a id="s4-4"></a>
## 4.4 — Pattern 2: Two Sum (unsorted array)

Yeh **the** classic hashing problem — har interview prep mein aata. Ch 02/03 mein sorted-array pe
two-pointer dekha; yahan **unsorted** array pe hashing se O(n).

**Kab pehchano (signal):** "do elements ka sum = target", "pair dhoondho", unsorted array.

**Problem — Two Sum:**

**Problem:** array `nums` (unsorted) aur `target` diya. Do indices dhoondho jinke elements ka sum
`target` ho. (Exactly ek answer hai.)
```
Input:  nums=[2, 7, 11, 15], target=9   -> Output: [0, 1]   (2+7=9)
Input:  nums=[3, 2, 4], target=6        -> Output: [1, 2]   (2+4=6)
Input:  nums=[3, 3], target=6           -> Output: [0, 1]   (3+3=6)
```

**Brute force:** har pair → O(n^2).

**Hashing solution (O(n) time — yeh yaad karo, bahut aata):**
```python
def two_sum(nums, target):
    seen = {}                        # value -> index
    for i, num in enumerate(nums):
        need = target - num          # is num ke saath kya chahiye?
        if need in seen:             # woh 'need' pehle dekha? O(1)
            return [seen[need], i]   # dono indices
        seen[num] = i                # ab is num ko yaad rakho (value->index)
    return []
```

**Logic kyun (yeh core — dhyan se):** har `num` pe hum sochte "iske saath sum banane ke liye kya
chahiye?" = `need = target - num`. Agar woh `need` **pehle dekha** hai (seen mein), toh pair mil
gaya! Warna current `num` ko yaad rakho (aage kisi ke `need` ke liye). Ek pass, har lookup O(1) →
**O(n) time, O(n) space.** Yeh Ch 2.5 wala hi hai, ab poore context mein.

**Dry-run (Input nums=[2,7,11,15], target=9):**
```
i=0, num=2:  need=9-2=7. seen={} mein 7 nahi. seen={2:0}
i=1, num=7:  need=9-7=2. seen={2:0} mein 2 HAI! return [seen[2], 1] = [0, 1]  ✓
```

**Kyun value→index (naam yaad rakhna):** hum value ko **key** banate (taaki `need in seen` O(1) ho),
aur uska index **value** rakhte (taaki answer mein index de saken). Ulta (index→value) karte toh
lookup O(n) ho jata — galat.

> **Yaad rakhne wali baat:** Two Sum (unsorted) = hashing O(n). Har num pe `need=target-num`, agar
> `need in seen` toh pair mila, warna `seen[num]=i`. Value→index store (lookup O(1)). Sorted array
> ho toh two-pointer bhi (Ch 3.2); unsorted pe hashing best. Classic — zaroor yaad.

[↑ Back to top](#top)

---

<a id="s4-5"></a>
## 4.5 — Pattern 3: Frequency counting

Bahut problems mein aapko "kaunsa element kitni baar aata" chahiye — **frequency count**. Hash-map
(ya `Counter`) se O(n) mein. Yeh anagram, top-K, majority type problems ka base hai.

**Kab pehchano (signal):** "kitni baar", "most/least frequent", "count of each", "anagram".

**Problem — First Unique Character:**

**Problem:** string `s` diya. Pehla character jo **sirf ek baar** aata hai, uska index return karo.
Koi na ho toh -1.
```
Input:  s="leetcode"   -> Output: 0   ('l' pehla unique, index 0)
Input:  s="aabb"       -> Output: -1  (koi unique nahi)
Input:  s="loveleet"   -> Output: 2   ('v' pehla unique)
```

**Solution (frequency count, O(n) time):**
```python
from collections import Counter

def first_unique_char(s):
    freq = Counter(s)              # har char ki frequency, O(n)
    for i, ch in enumerate(s):     # order mein dekho
        if freq[ch] == 1:          # frequency 1 = unique
            return i
    return -1
```

**Logic kyun:** pehle ek pass mein saari frequencies count karo (`Counter` — O(n)). Phir doosre pass
mein, string ke order mein, pehla char dhoondho jiski frequency 1 ho. Do pass, dono O(n) → **O(n)
total.** `Counter` ne frequency counting ek line mein kar di (warna manual dict loop).

**Manual dict version (Counter ke bina, samajhne ko):**
```python
def first_unique_char_manual(s):
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1   # get(ch,0) = missing pe 0 (4.2)
    for i, ch in enumerate(s):
        if freq[ch] == 1:
            return i
    return -1
```
- `freq.get(ch, 0) + 1` = "abhi tak jitni baar, +1". `get(ch, 0)` missing key pe 0 (KeyError bachata,
  4.2). `Counter` isi ka shortcut hai.

**Dry-run (Input s="leetcode"):**
```
Counter: {'l':1, 'e':3, 't':1, 'c':1, 'o':1, 'd':1}
i=0 'l': freq=1 -> unique! return 0  ✓
```

> **Yaad rakhne wali baat:** Frequency counting: `Counter(s)` (ya manual `freq[x]=freq.get(x,0)+1`)
> se har element ki count O(n). Signal: "kitni baar/most-frequent/anagram/unique". Aksar do pass
> (count phir use). Anagram, top-K, majority ka base.

[↑ Back to top](#top)

---

<a id="s4-6"></a>
## 4.6 — Pattern 4: Group anagrams (key banana)

Yeh pattern ek clever idea sikhata — **cheezon ko group karne ke liye ek "key" banao**, aur same-key
wali cheezein ek group mein daalo (hash-map of key→list). Anagram grouping classic hai.

**Anagram kya:** do words jo same letters se bane (bs order alag). Jaise "eat" aur "tea" (dono e,a,t).

**Kab pehchano (signal):** "group karo", "same [kuch] wale saath", "anagrams".

**Problem — Group Anagrams:**

**Problem:** words ki list di. Anagrams ko ek saath group karo.
```
Input:  ["eat", "tea", "tan", "ate", "nat", "bat"]
Output: [["eat","tea","ate"], ["tan","nat"], ["bat"]]
        (eat/tea/ate same letters; tan/nat same; bat akela)
```

**Solution (sorted-string as key, O(n * k log k)):**
```python
from collections import defaultdict

def group_anagrams(words):
    groups = defaultdict(list)        # key -> list of words
    for word in words:
        key = "".join(sorted(word))   # sorted letters = anagram key
        groups[key].append(word)      # same key wale saath
    return list(groups.values())
```

**Logic kyun (yeh core idea):** anagrams ka ek common property — **sorted letters same hote**. "eat"
aur "tea" dono sorted = "aet". Toh sorted-string ko **key** banaya, aur same-key wale words ek list
mein group kiye (`defaultdict(list)` — missing key pe khaali list, 4.2). Har word: sort (O(k log k),
k=word length) + O(1) group-add. Total **O(n * k log k)** (n words).

**Dry-run (Input ["eat","tea","tan","ate","nat","bat"]):**
```
"eat" -> sorted "aet" -> groups={"aet":["eat"]}
"tea" -> sorted "aet" -> groups={"aet":["eat","tea"]}
"tan" -> sorted "ant" -> groups={"aet":["eat","tea"], "ant":["tan"]}
"ate" -> sorted "aet" -> groups={"aet":["eat","tea","ate"], "ant":["tan"]}
"nat" -> sorted "ant" -> groups={..., "ant":["tan","nat"]}
"bat" -> sorted "abt" -> groups={..., "abt":["bat"]}
return [["eat","tea","ate"], ["tan","nat"], ["bat"]]  ✓
```

**Key-banane ka general idea:** grouping problems mein socho "kya common property hai jo group decide
karti?" — usse key banao. Anagram → sorted-letters. Kabhi frequency-tuple, kabhi kuch aur. Yeh
"canonical key" idea kaam ka hai.

> **Yaad rakhne wali baat:** Group-by-key: same group wali cheezon ka ek common "key" banao,
> `defaultdict(list)` mein key→list group karo. Anagram: key = sorted-letters (anagrams ka sorted
> same). O(n*k log k). Signal: "group karo / same-X wale saath". Common property se key banao.

[↑ Back to top](#top)

---

<a id="s4-7"></a>
## 4.7 — Pattern 5: Prefix-sum + hashmap (subarray sum = k)

Yeh ek powerful combo — prefix-sum (Ch 3.6) + hashmap. "Kitne subarrays ka sum exactly k hai" type
problems mein O(n) deta. Thoda advanced par bahut aata, isliye samajhna zaroori.

**Kab pehchano (signal):** "subarray with sum = k", "count of subarrays summing to X", "continuous
subarray sum".

**Problem — Subarray Sum Equals K:**

**Problem:** array `nums` aur `k` diya. Kitne **contiguous** subarrays ka sum exactly `k` hai?
```
Input:  nums=[1, 1, 1], k=2   -> Output: 2   (subarrays [1,1](index 0-1) aur [1,1](index 1-2))
Input:  nums=[1, 2, 3], k=3   -> Output: 2   ([1,2] aur [3])
```

**Brute force:** har subarray ka sum → O(n^2). Hashing se O(n).

**Prefix-sum + hashmap solution (O(n) time):**
```python
def subarray_sum(nums, k):
    count = 0
    prefix_sum = 0
    seen = {0: 1}                    # prefix_sum -> kitni baar dekha. {0:1} start
    for num in nums:
        prefix_sum += num            # ab tak ka running sum
        need = prefix_sum - k        # agar yeh prefix pehle dekha, toh beech ka subarray = k
        if need in seen:
            count += seen[need]      # utne subarrays
        seen[prefix_sum] = seen.get(prefix_sum, 0) + 1
    return count
```

**Logic kyun (yeh thoda dimaag lagta — dhyan se):** running `prefix_sum` rakhte hain (0 se yahan tak
ka sum). Agar current `prefix_sum` aur koi pehla `prefix_sum` ka **farak = k**, toh un dono ke beech
ka subarray ka sum = k! Toh hum `need = prefix_sum - k` dhoondhte hain seen mein — agar mila, matlab
utne subarrays end yahan. `seen` mein har prefix_sum ki count rakhte. `{0:1}` start isliye ki agar
prefix_sum khud k ho (shuru se subarray). **O(n) time, O(n) space.**

**Dry-run (Input nums=[1,1,1], k=2):**
```
seen={0:1}, prefix_sum=0, count=0
num=1: prefix_sum=1. need=1-2=-1. seen mein -1 nahi. seen={0:1, 1:1}
num=1: prefix_sum=2. need=2-2=0.  seen mein 0 HAI (count 1). count += 1 = 1. seen={0:1,1:1,2:1}
num=1: prefix_sum=3. need=3-2=1.  seen mein 1 HAI (count 1). count += 1 = 2. seen={...,3:1}
return count = 2  ✓
```

**Yeh Ch 3.6 se juda:** prefix-sum akela range-sum deta tha; hashmap ke saath yeh "count subarrays
with sum k" O(n) mein karta (brute O(n^2) se behtar). Prefix-sum + hashmap ek recurring combo hai —
jab bhi "subarray sum = k / count" dikhe, yeh socho.

> **Yaad rakhne wali baat:** Subarray-sum=k: prefix-sum + hashmap. Running `prefix_sum`, `need =
> prefix_sum - k`, agar `need in seen` toh utne subarrays. `seen` mein prefix_sum→count, `{0:1}`
> start. O(n) (brute O(n^2) se behtar). Signal: "count/find subarray with sum k".

[↑ Back to top](#top)

---

<a id="s4-8"></a>
## 4.8 — Nuances, edge cases, aur kab hashing NAHI

**Signal→pattern (hashing ke andar):**

| Problem ka signal | Pattern | Section |
|---|---|---|
| Duplicate/pehle-dekha/unique | Seen-set | 4.3 |
| Do elements ka sum=target (unsorted) | Two Sum (value→index map) | 4.4 |
| Kitni baar / most-frequent | Frequency count (Counter) | 4.5 |
| Group same-X wale / anagrams | Key banao + group (defaultdict) | 4.6 |
| Subarray/continuous sum = k | Prefix-sum + hashmap | 4.7 |

**Edge cases (HAMESHA check):**
- **Empty input** `[]` / `""` — loop chalega hi nahi, sahi default return (jaise 0, [], False)?
- **Single element** — two-sum single pe koi pair nahi (theek).
- **Duplicates** — two-sum mein same value do baar (jaise `[3,3]`) — value→index map latest overwrite
  karta, par hum pehle lookup karte toh theek. Dhyan se.
- **Negative numbers / zero** — prefix-sum mein negatives/zero se bhi chalta (subarray-sum=k works).
- **`get(key, default)` use karo** — direct `d[key]` missing pe KeyError (crash). `get` ya
  `defaultdict` (4.2).

**Kab hashing NAHI (galat use se bacho):**
- **Jab order matter kare aur aap sirf set use karo** — set order nahi rakhta (Python 3.7+ dict
  insertion-order rakhta, par set nahi guaranteed conceptually). Order chahiye toh list + set combo.
- **Jab memory constraint ho** — hashing O(n) extra space leta. Agar "O(1) space" required, toh
  two-pointer/sorting socho (jaise sorted array pe two-pointer, Ch 3.2 — O(1) space).
- **Chhota fixed range** — jaise sirf lowercase letters (26) — tab array `[0]*26` set/dict se fast+
  simple ho sakta (index = char). Micro-optimization, interview mein optional.
- **Sorted array pe pair** — two-pointer (Ch 3.2) O(1) space deta; hashing O(n) space. Sorted ho toh
  two-pointer consider karo.

**Ek zaroori baat — hashing "average O(1)":** worst case O(n) (bahut collisions) par practically O(1)
maano. Interview mein "average O(1)" bolna safe.

> **Yaad rakhne wali baat:** Hashing signals: duplicate→seen-set, pair-sum→two-sum-map, count→
> frequency, group→key+defaultdict, subarray-sum→prefix+hashmap. Edge: empty/single/duplicates/
> negatives, `get()` use karo. NAHI: O(1)-space required (two-pointer/sort), order-critical, sorted
> array (two-pointer). Average O(1).

[↑ Back to top](#top)

---

<a id="s4-9"></a>
## 4.9 — Yaad rakhne wali baatein (chapter recap)

Hashing sabse zyada kaam aane wala optimize-tool:

1. **Hash map/set = O(1) lookup** (superpower). Nested-loop (O(n^2)) ko single (O(n)) banata. Cost:
   O(n) memory (time-space tradeoff).
2. **Python:** `dict` (key→value), `set` (membership), `Counter` (frequency), `defaultdict` (missing
   pe default). `get(k, default)` KeyError bachata. `in set/dict` O(1), `in list` O(n).
3. **Seen-set** (4.3): "dekha hai kya?" — duplicate/unique. O(n).
4. **Two Sum** (4.4): `need=target-num`, `need in seen`? — value→index map. O(n). Classic, zaroor
   yaad.
5. **Frequency count** (4.5): `Counter` — "kitni baar/unique/anagram". O(n).
6. **Group by key** (4.6): common property se key (anagram=sorted-letters), `defaultdict(list)` mein
   group.
7. **Prefix-sum + hashmap** (4.7): subarray-sum=k, `need=prefix_sum-k`. O(n).

> **Chapter ka mantra:** Jab bhi "dhoondhna / count / dekha-hai-kya / pair / group / subarray-sum"
> dikhe — **hashing socho**. Yeh brute-force O(n^2) ko O(n) banane ka #1 tool hai. Two-sum aur
> frequency-count sabse zyada aate — inhe pakka karo. LeetCode pe 4-5 hashing problems practice.

[↑ Back to top](#top)

---

> **Chapter 04 khatam.** Ab tak: hash-map/set O(1) lookup (superpower); Python dict/set/Counter/
> defaultdict; seen-set, two-sum (unsorted), frequency-count, group-anagrams, prefix-sum+hashmap;
> signal→pattern + edge cases + kab-NAHI. **Agla chapter (05):** Strings — sliding-window on strings,
> anagrams, palindrome (expand-around-center), parsing, Python string gotchas.

[↑ Back to top](#top)
