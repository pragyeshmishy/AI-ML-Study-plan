<a id="top"></a>
# Chapter 05 — Strings: Sliding Window, Anagrams, Palindrome, Parsing

Strings interview mein bahut common hain (Ch 1.4 — HIGH, ~8%). Achhi baat — string patterns
zyadatr **arrays (Ch 03) aur hashing (Ch 04) jaise hi** hain (string = characters ka array). Toh
yeh chapter un patterns ko strings pe apply karta, plus kuch string-specific cheezein (palindrome,
parsing, Python string gotchas).

Clear examples aur dry-run ke saath, taaki yeh patterns yaad ho jaayein.

---

## Is chapter ka index

- [5.1 — String basics + Python gotchas (immutability, join)](#s5-1)
- [5.2 — Pattern: Anagram check (frequency)](#s5-2)
- [5.3 — Pattern: Sliding window on strings (longest substring)](#s5-3)
- [5.4 — Pattern: Palindrome (two-pointer + expand-around-center)](#s5-4)
- [5.5 — Pattern: Character frequency + hashing (recap on strings)](#s5-5)
- [5.6 — Basic parsing / string building](#s5-6)
- [5.7 — Nuances, edge cases, aur kab kaunsa](#s5-7)
- [5.8 — Yaad rakhne wali baatein](#s5-8)

---

<a id="s5-1"></a>
## 5.1 — String basics + Python gotchas (immutability, join)

**String** = characters ki sequence (jaise `"hello"`). Python mein yeh ek `str` hai — array jaisa
index-access, par ek **bada farak: strings IMMUTABLE hain** (badle nahi ja sakte).

```python
s = "hello"
print(s[0])       # 'h'  (index access, array jaisa, O(1))
print(s[-1])      # 'o'  (aakhri)
print(len(s))     # 5
print(s[1:4])     # 'ell'  (slice)
for ch in s:      # iterate characters
    print(ch)
```

**GOTCHA 1 — Immutability (yeh sabse zaroori):** aap string ka ek character **badal nahi sakte**:
```python
s = "hello"
s[0] = "H"        # ERROR! strings immutable hain
```
- Badalna ho toh **naya** string banao (ya list mein convert karo):
```python
s = "H" + s[1:]           # naya string "Hello"
# ya:
chars = list(s)           # ['h','e','l','l','o'] — ab mutable
chars[0] = "H"
s = "".join(chars)        # wapas string "Hello"
```

**GOTCHA 2 — `+=` in loop = O(n^2) (Ch 2.8 recap, bahut important):**
```python
# GALAT (slow) — har += naya string banata (immutable!)
result = ""
for ch in s:
    result += ch          # O(n) har baar -> total O(n^2)!

# SAHI — list mein collect, phir join
parts = []
for ch in s:
    parts.append(ch)      # O(1) har baar
result = "".join(parts)   # O(n) ek baar -> total O(n)
```
- **Kyun:** strings immutable — `result += ch` har baar poora naya string banata (O(n)), loop mein
  O(n^2). List `append` O(1), phir ek `join` O(n). **String banane ke liye hamesha list+join.** Yeh
  interview mein clean-code signal (Ch 1.8).

**Useful string methods:**
```python
s.lower() / s.upper()     # case
s.strip()                 # aage-peeche whitespace hatao
s.split(",")              # comma pe todo -> list
",".join(list)            # list ko string mein jodo
s.replace("a", "b")       # replace
s.isalpha() / s.isdigit() # check
```

> **Yaad rakhne wali baat:** String = char sequence, array jaisa index-access (O(1)), PAR IMMUTABLE
> (char badal nahi sakte — naya banao). GOTCHA: `s += ch` loop mein O(n^2) — use `list + "".join()`
> (O(n)). Methods: split/join/strip/lower. String = character array, patterns array/hashing jaise.

[↑ Back to top](#top)

---

<a id="s5-2"></a>
## 5.2 — Pattern: Anagram check (frequency)

Anagram (Ch 4.6 recap — same letters, alag order) check karna common. Frequency-count (Ch 4.5) ka
seedha application.

**Kab pehchano (signal):** "anagram hai kya", "same characters", "rearrange to equal".

**Problem — Valid Anagram:**

**Problem:** do strings `s` aur `t` diye. Kya `t`, `s` ka anagram hai (same letters, same count)?
```
Input:  s="anagram", t="nagaram"  -> Output: True   (same letters)
Input:  s="rat", t="car"          -> Output: False  (alag letters)
Input:  s="ab", t="a"             -> Output: False  (alag length)
```

**Solution 1 — Frequency count (O(n) time):**
```python
from collections import Counter

def is_anagram(s, t):
    if len(s) != len(t):        # alag length -> anagram nahi (quick check)
        return False
    return Counter(s) == Counter(t)   # dono ki frequency same?
```
- `Counter(s) == Counter(t)` — dono strings ki character-frequencies same hain kya? Anagram ka matlab
  exactly yehi. **O(n) time.** Ek line mein.

**Solution 2 — Sorting (O(n log n), simpler soch):**
```python
def is_anagram_sort(s, t):
    return sorted(s) == sorted(t)   # sorted letters same -> anagram
```
- Anagrams ka sorted-form same hota (Ch 4.6). Simple par O(n log n) (sort slow than count).

**Dry-run (Input s="anagram", t="nagaram"):**
```
len same (7 == 7) -> aage
Counter("anagram") = {'a':3, 'n':1, 'g':1, 'r':1, 'm':1}
Counter("nagaram") = {'a':3, 'n':1, 'g':1, 'r':1, 'm':1}
Same! -> return True  ✓
```

**Interview mein bolna:** "frequency-count se O(n), ya sorting se O(n log n) — main frequency use
karunga kyunki fast". Yeh dono approach + tradeoff bolna senior-signal (Ch 1.7).

> **Yaad rakhne wali baat:** Anagram = same letters same count. Check: `Counter(s)==Counter(t)` (O(n),
> best) ya `sorted(s)==sorted(t)` (O(n log n), simpler). Pehle length-check (alag length = jaldi
> False). Frequency (Ch 4.5) ka application.

[↑ Back to top](#top)

---

<a id="s5-3"></a>
## 5.3 — Pattern: Sliding window on strings (longest substring)

Sliding-window (Ch 3.4/3.5) strings pe bahut aata — substring (contiguous characters) problems. Yeh
Ch 3.5 (variable window) ka string version — wahan "longest unique substring" dekha tha, ab aur.

**Kab pehchano (signal):** "longest/shortest substring with [condition]", "window of characters".

**Problem — Longest Substring Without Repeating Characters (Ch 3.5 recap, string focus):**

**Problem:** string `s` diya. Sabse lambi substring (contiguous) ki length jismein koi char repeat na
ho.
```
Input:  s="abcabcbb"  -> Output: 3   ("abc")
Input:  s="bbbbb"     -> Output: 1   ("b")
Input:  s="pwwkew"    -> Output: 3   ("wke")
```
```python
def longest_unique(s):
    seen = set()
    left = 0
    max_len = 0
    for right in range(len(s)):
        while s[right] in seen:        # repeat -> shrink
            seen.remove(s[left])
            left += 1
        seen.add(s[right])
        max_len = max(max_len, right - left + 1)
    return max_len
```
- Yeh Ch 3.5 wala hi hai (variable window: right grow, left shrink-when-repeat). String pe same
  logic. **O(n).**

**Naya example — Longest Substring with At Most K Distinct Characters:**

**Problem:** string `s` aur `k` diya. Sabse lambi substring jismein **at most k alag** characters ho.
```
Input:  s="eceba", k=2  -> Output: 3   ("ece" — 2 distinct: e,c)
Input:  s="aa", k=1     -> Output: 2   ("aa")
```
```python
def longest_k_distinct(s, k):
    freq = {}                          # window mein har char ki count
    left = 0
    max_len = 0
    for right in range(len(s)):
        freq[s[right]] = freq.get(s[right], 0) + 1   # add right char
        while len(freq) > k:           # zyada distinct -> shrink
            freq[s[left]] -= 1
            if freq[s[left]] == 0:
                del freq[s[left]]      # count 0 -> distinct kam karo
            left += 1
        max_len = max(max_len, right - left + 1)
    return max_len
```

**Logic kyun (variable window + freq map):** window mein characters ka count `freq` map mein.
`len(freq)` = kitne **distinct** chars. Jab distinct `> k` ho jaye (invalid), left se shrink karo
(count ghatao, 0 ho toh distinct kam). Yeh Ch 3.5 template + hashing (Ch 04) ka combo. **O(n).**

**Dry-run (Input s="eceba", k=2):**
```
right=0 'e': freq={e:1}, distinct=1<=2. max=1
right=1 'c': freq={e:1,c:1}, distinct=2<=2. max=2
right=2 'e': freq={e:2,c:1}, distinct=2<=2. max=3  ("ece")
right=3 'b': freq={e:2,c:1,b:1}, distinct=3>2! shrink: remove s[0]='e'(freq e:1), left=1. distinct=3 still>2. remove s[1]='c'(freq c:0,del), left=2. distinct=2. window "eb". max=3
right=4 'a': freq={e:1,b:1,a:1}, distinct=3>2! shrink... left moves. max stays 3
return 3  ✓
```

> **Yaad rakhne wali baat:** Sliding-window on strings = Ch 3.5 template (right grow, left shrink-
> when-invalid) + hashing for char-tracking. "Longest substring without repeat" (seen-set),
> "at-most-k-distinct" (freq map, len>k shrink). O(n). Signal: "longest/shortest substring with
> condition".

[↑ Back to top](#top)

---

<a id="s5-4"></a>
## 5.4 — Pattern: Palindrome (two-pointer + expand-around-center)

**Palindrome** = jo aage-peeche same padha jaye (jaise "racecar", "madam"). Do sub-patterns: **check**
karna (two-pointer, Ch 3.2) aur **dhoondhna** (expand-around-center).

**Kab pehchano (signal):** "palindrome", "same forwards/backwards", "symmetric".

**Sub-pattern A — Palindrome CHECK (two-pointer, Ch 3.2 recap):**

**Problem:** string `s` palindrome hai? (sirf alphanumeric, case ignore)
```
Input:  s="A man a plan a canal Panama"  -> Output: True  (spaces/case ignore ke baad palindrome)
Input:  s="race a car"                    -> Output: False
```
```python
def is_palindrome(s):
    # sirf alphanumeric rakho, lowercase
    cleaned = [c.lower() for c in s if c.isalnum()]
    left, right = 0, len(cleaned) - 1
    while left < right:
        if cleaned[left] != cleaned[right]:
            return False
        left += 1
        right -= 1
    return True
```
- Two-pointer opposite-ends (Ch 3.2) — dono taraf se compare. Pehle clean (alphanumeric, lowercase).
  **O(n).**

**Sub-pattern B — Longest Palindromic Substring (expand-around-center):**

**Problem:** string `s` mein sabse lambi palindrome substring dhoondho.
```
Input:  s="babad"  -> Output: "bab"  (ya "aba", dono length 3)
Input:  s="cbbd"   -> Output: "bb"
```
```python
def longest_palindrome(s):
    if not s:
        return ""
    start, max_len = 0, 1

    def expand(left, right):           # center se dono taraf failao
        while left >= 0 and right < len(s) and s[left] == s[right]:
            left -= 1
            right += 1
        return left + 1, right - 1     # palindrome ki boundaries

    for i in range(len(s)):
        # odd-length palindrome (center = i)
        l1, r1 = expand(i, i)
        if r1 - l1 + 1 > max_len:
            start, max_len = l1, r1 - l1 + 1
        # even-length palindrome (center = i, i+1)
        l2, r2 = expand(i, i + 1)
        if r2 - l2 + 1 > max_len:
            start, max_len = l2, r2 - l2 + 1

    return s[start:start + max_len]
```

**Logic kyun (expand-around-center — yeh core idea):** har palindrome ka ek **center** hota. Hum har
possible center pe khade hoke **dono taraf failte** hain jab tak characters match karen. Odd-length
palindrome ka center ek char (`i`); even-length ka center do chars ke beech (`i, i+1`) — isliye
dono try. Har center O(n) expand, n centers → **O(n^2) time** (par simple aur interview-acceptable;
faster Manacher's rare, Ch 1.5 skip).

**Dry-run (Input s="babad", center expand):**
```
i=0 'b': expand(0,0) -> "b" (len 1). expand(0,1) 'b'vs'a' no -> len 0
i=1 'a': expand(1,1) -> s[0]='b'==s[2]='b'? yes -> "bab" (len 3)! start=0, max_len=3
i=2 'b': expand(2,2) -> s[1]='a'==s[3]='a'? yes -> "aba" (len 3, but max_len already 3)
...
return s[0:3] = "bab"  ✓
```

> **Yaad rakhne wali baat:** Palindrome CHECK = two-pointer opposite-ends (Ch 3.2), O(n). Longest
> palindrome SUBSTRING = expand-around-center: har center se dono taraf failao (odd: `i,i`; even:
> `i,i+1`), O(n^2). Signal: "palindrome/symmetric". Center-expand = key idea.

[↑ Back to top](#top)

---

<a id="s5-5"></a>
## 5.5 — Pattern: Character frequency + hashing (recap on strings)

Frequency-count (Ch 4.5) strings pe bahut aata — kyunki strings characters ka collection hain. Yeh
short recap + ek string-specific example, taaki pattern strings pe pakka ho.

**Problem — Find All Anagrams in a String (sliding-window + frequency combo):**

**Problem:** string `s` aur `p` diye. `s` mein `p` ke saare anagrams ke start-indices dhoondho.
```
Input:  s="cbaebabacd", p="abc"  -> Output: [0, 6]
        (index 0 "cba" = anagram of "abc"; index 6 "bac" = anagram)
Input:  s="abab", p="ab"          -> Output: [0, 1, 2]
```
```python
from collections import Counter

def find_anagrams(s, p):
    if len(p) > len(s):
        return []
    p_count = Counter(p)               # p ki frequency
    window = Counter(s[:len(p)])       # pehli window
    result = []
    if window == p_count:
        result.append(0)
    for i in range(len(p), len(s)):    # window slide (Ch 3.4 fixed)
        window[s[i]] += 1              # naya char add (right)
        left_char = s[i - len(p)]
        window[left_char] -= 1         # purana remove (left)
        if window[left_char] == 0:
            del window[left_char]      # count 0 -> hatao (taaki == kaam kare)
        if window == p_count:          # frequency match = anagram!
            result.append(i - len(p) + 1)
    return result
```

**Logic kyun (fixed-window + frequency):** `p` ke length ka **fixed window** `s` pe slide karo (Ch
3.4). Har window ki frequency `p` ki frequency se match kare toh woh anagram hai. Window slide: naya
char add, purana remove (count 0 ho toh delete taaki `==` sahi ho). **O(n) time.** Yeh sliding-window
(Ch 3.4) + frequency (Ch 4.5) ka clean combo — patterns aksar combine hote (Ch 3.10).

**Dry-run (Input s="cbaebabacd", p="abc"):**
```
p_count = {a:1, b:1, c:1}
window (s[0:3]="cba") = {c:1,b:1,a:1} == p_count! result=[0]
slide... eventually i pe window "bac" (index 6) = {b:1,a:1,c:1} == p_count! result=[0,6]
return [0, 6]  ✓
```

> **Yaad rakhne wali baat:** Char-frequency (Ch 4.5) strings pe common. Find-anagrams = fixed
> sliding-window (Ch 3.4) + frequency-match: window ki Counter == p ki Counter toh anagram. Slide:
> add-right, remove-left (0 ho toh del). O(n). Patterns combine (window + frequency).

[↑ Back to top](#top)

---

<a id="s5-6"></a>
## 5.6 — Basic parsing / string building

Kabhi problem mein string ko **parse** (tod ke samajhna) ya **build** (banana) karna padta — jaise
words ginna, tokens nikaalna, ya result string banana. Simple par common.

**Example 1 — Reverse Words in a String:**

**Problem:** string ke words ka order ulta karo (extra spaces handle karo).
```
Input:  s="  the sky  is blue  "  -> Output: "blue is sky the"
```
```python
def reverse_words(s):
    words = s.split()          # split() extra spaces handle karta -> ["the","sky","is","blue"]
    return " ".join(reversed(words))   # ulta karke join
```
- `s.split()` (bina argument) — multiple/leading/trailing spaces automatically handle (khaali tokens
  nahi). `reversed` + `join` — clean. **O(n).** (Split/join — Ch 5.1 methods.)

**Example 2 — Valid Palindrome after cleaning (parsing example, 5.4 recap):**
```python
# alphanumeric nikaalna ek parsing hai:
cleaned = [c.lower() for c in s if c.isalnum()]   # sirf letters/digits, lowercase
```
- `c.isalnum()` — character letter ya digit hai kya? Isse punctuation/spaces filter. Parsing ka
  common step.

**String building (Ch 5.1 gotcha recap — bahut important):**
```python
# GALAT: loop mein += (O(n^2))
result = ""
for word in words:
    result += word + " "

# SAHI: list + join (O(n))
parts = []
for word in words:
    parts.append(word)
result = " ".join(parts)
```
- Dohra raha hoon kyunki yeh #1 string galti hai — **build karne ke liye list + join, `+=` nahi.**

**Common parsing tools:**
- `s.split(delim)` — todo (delim ya whitespace pe). `s.strip()` — trim. `s.isalnum()/.isdigit()/
  .isalpha()` — check. `"".join(list)` — build. `ord(c)/chr(n)` — char<->number (kabhi useful).

> **Yaad rakhne wali baat:** Parsing: `split()` (todo, extra-space-safe), `strip()` (trim), `isalnum`
> (filter). Building: **list + `join`** (O(n)), NEVER `+=` loop (O(n^2)). `ord/chr` char<->number.
> Simple string manipulation ke tools.

[↑ Back to top](#top)

---

<a id="s5-7"></a>
## 5.7 — Nuances, edge cases, aur kab kaunsa

**Signal→pattern (strings):**

| Signal | Pattern | Section |
|---|---|---|
| Anagram / same letters | Frequency (Counter) ya sort | 5.2 |
| Longest/shortest substring with condition | Sliding window (variable) | 5.3 |
| Palindrome check | Two-pointer opposite-ends | 5.4 |
| Longest palindrome substring | Expand-around-center | 5.4 |
| Substring anagram / char-window | Fixed window + frequency | 5.5 |
| Words/tokens process | split/join parsing | 5.6 |

**Edge cases (HAMESHA):**
- **Empty string** `""` — loop nahi chalega, sahi default (`""`, 0, True/False)?
- **Single char** `"a"` — palindrome (True), unique (len 1).
- **Spaces/case/punctuation** — clean karna hai? (`strip`, `lower`, `isalnum`). Problem padho dhyan se.
- **All same** `"aaaa"` — window/frequency logic sahi?
- **Unicode/non-ASCII** — interview mein usually ASCII maano (jab tak na bola jaye).

**Python-specific (Ch 5.1 recap — yaad rakho):**
- **Immutable** — char badalne ke liye `list(s)` → modify → `"".join()`.
- **`+=` loop = O(n^2)** — use list + join.
- **`in` on string** = O(n) (substring search) — `"abc" in s` poora scan.

**Kab yeh patterns NAHI:**
- **String matching deep (KMP/Z-algorithm)** — SR ML mein rare (Ch 1.5 skip). Simple `in`/`find`
  kaafi zyadatr.
- **Regex** — kabhi parsing mein, par DSA rounds mein usually manual logic expected (regex mention
  kar sakte, par implement manual).

> **Yaad rakhne wali baat:** String signals: anagram→frequency, substring-condition→sliding-window,
> palindrome→two-pointer/expand-center, substring-anagram→window+freq. Edge: empty/single/spaces-
> case/all-same. Python: immutable (list+join to modify), `+=` loop O(n^2). KMP/regex skip (rare).

[↑ Back to top](#top)

---

<a id="s5-8"></a>
## 5.8 — Yaad rakhne wali baatein (chapter recap)

Strings = character arrays; patterns arrays (Ch 03) + hashing (Ch 04) jaise:

1. **Basics + gotchas** (5.1): index-access O(1), IMMUTABLE (char badalne ko list+join). `+=` loop
   O(n^2) — use `"".join(list)`. split/strip/lower methods.
2. **Anagram** (5.2): `Counter(s)==Counter(t)` (O(n)) ya `sorted` (O(n log n)). Length-check pehle.
3. **Sliding window** (5.3): longest/shortest substring with condition (Ch 3.5 template + hashing).
   Unique-substring, at-most-k-distinct.
4. **Palindrome** (5.4): check = two-pointer (O(n)); longest-substring = expand-around-center (odd
   `i,i` + even `i,i+1`, O(n^2)).
5. **Char-frequency + window** (5.5): find-anagrams = fixed-window + Counter-match. Combo pattern.
6. **Parsing/building** (5.6): split/join/strip/isalnum. Build with list+join.

> **Chapter ka mantra:** String = character array — toh arrays (two-pointer, sliding-window) aur
> hashing (frequency) ke patterns yahan bhi. Extra: palindrome (expand-center), Python immutability
> (list+join). Signal dekho → pattern (5.7 table). LeetCode pe 3-4 string problems practice.

[↑ Back to top](#top)

---

> **Chapter 05 khatam.** Ab tak: string basics + Python gotchas (immutable, `+=` O(n^2), join);
> anagram (frequency), sliding-window on strings (unique/k-distinct), palindrome (two-pointer +
> expand-around-center), char-frequency+window (find-anagrams), parsing (split/join). **Agla chapter
> (06):** Linked Lists + Stacks + Queues — fast-slow, reversal, monotonic stack, valid-parentheses,
> BFS-queue, monotonic-deque.

[↑ Back to top](#top)
