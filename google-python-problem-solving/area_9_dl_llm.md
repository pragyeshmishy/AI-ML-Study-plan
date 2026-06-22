# Area 9 — DL & LLM Tributary

Deep learning and LLM work has its own recurring failure modes — shape mismatches, GPU
memory limits, NaN losses, and the LLM-specific realities of tokens, chunking, and
parsing model output. This area is a *tributary*, not the main river: it assumes the
broad-ML foundations of Area 8 and focuses on what's distinct about training neural nets
and building on language models. The recurring theme: the framework gives a cryptic error
(or silently wrong output), and the skill is recognising the small set of causes behind
most of them.

---

<a id="contents"></a>
## Contents

- [9.1 — "RuntimeError: shapes (32,10) and (64,10) cannot be multiplied" → tensor shapes & broadcasting](#9.1)
- [9.2 — "My batch has sentences of different lengths and won't form a tensor" → padding & masking](#9.2)
- [9.3 — "CUDA out of memory" → fitting training into GPU memory](#9.3)
- [9.4 — "Training loss exploded to NaN (or flatlined and won't learn)" → exploding/vanishing gradients](#9.4)
- [9.5 — "I saved the model but resuming training gives different results" → checkpoints (model + optimizer)](#9.5)
- [9.6 — "My expensive GPU sits idle waiting for data" → workers & prefetch](#9.6)
- [9.7 — "My model gives different predictions each call, and inference is slow + OOMs" → eval mode & no_grad](#9.7)
- [9.8 — "My LLM call failed: too many tokens" → tokens & context budgets](#9.8)
- [9.9 — "Retrieval returns half a sentence or a whole irrelevant chapter" → chunking strategy](#9.9)
- [9.10 — "I asked the LLM for JSON and json.loads crashed" → parsing LLM output safely](#9.10)
- [9.11 — "The JSON parsed fine but 'age' was -5 and the category was made up" → validating structured output](#9.11)
- [9.12 — "Every run re-embeds the same 1M documents and re-bills me" → embedding cache](#9.12)
- [9.13 — "The user stares at a blank screen for 20 seconds while the LLM thinks" → streaming responses](#9.13)
- [9.14 — "How does the system find the 'relevant' chunks for a question?" → vector similarity](#9.14)
- [9.15 — "Our LLM bill is huge and p99 latency is awful, but which calls?" → tracking LLM cost & latency](#9.15)

---


<a id="9.1"></a>
## 9.1 — "RuntimeError: shapes (32,10) and (64,10) cannot be multiplied" → tensor shapes & broadcasting

### The situation

You're wiring up a model and get a wall of shape errors that all look like this:

```python
# a batch of 32 samples, each a 784-vector; a layer expecting 256 inputs
x = torch.randn(32, 784)               # shape: (batch=32, features=784)
layer = nn.Linear(256, 10)             # expects inputs of size 256, not 784
out = layer(x)                          # RuntimeError: mat1 and mat2 shapes cannot be multiplied
                                        # (32x784 and 256x10)
```

The numbers in the error (`32x784`, `256x10`) mean nothing until you realise they're
**tensor shapes** that don't line up. Most deep-learning bugs, especially early on, are
shape mismatches — and the error messages describe the symptom, not which line or
dimension is actually wrong.

### What's really going on

A **tensor** is an n-dimensional array (the generalisation of vectors/matrices to any
number of dimensions), and every operation has **shape rules** about how dimensions must
align. A matrix multiply `(a, b) @ (b, c) → (a, c)` requires the inner dimensions to
match; a `Linear(in, out)` layer requires its input's last dimension to equal `in`. When
they don't, you get the cryptic error. The fix is almost always to **print the shapes**
and find where a dimension is wrong — usually a layer size, a forgotten batch dimension,
or a transpose.

A second, subtler mechanic is **broadcasting**: NumPy/PyTorch let you combine tensors of
*different but compatible* shapes by automatically stretching size-1 dimensions. This is
powerful (add a `(10,)` bias to a `(32, 10)` batch without a loop) but a frequent source
of silent bugs — shapes that broadcast when you didn't intend them to, producing
wrong-but-not-erroring results.

> **Tensor** = n-dimensional array; **shape** = the size of each dimension, e.g.
> `(batch, features)`. **Broadcasting** = automatic stretching of size-1 (or missing)
> dimensions so tensors of compatible shapes can be combined element-wise. The two skills:
> read shape errors by checking which dimensions must align, and watch for *unintended*
> broadcasting that silently gives wrong results.

### The move

**Print shapes at each step** to locate the mismatch, then fix the offending dimension;
and be explicit about broadcasting:

```python
print(x.shape)                          # (32, 784) — the first thing to check, always
layer = nn.Linear(784, 10)              # match in_features to the input's last dim
print(layer(x).shape)                   # (32, 10) — confirm the output shape is what you expect
```

### Why it works

Shape errors are positional: the operation tells you the two shapes it couldn't combine,
and matching them to *your* tensors reveals which dimension is wrong. Printing
`.shape` (or asserting it) at each step turns "somewhere a shape is wrong" into "the input
is 784 but the layer expects 256 — fix the layer." It's the deep-learning version of
"measure before guessing" (Area 2). For broadcasting, knowing the rule (dimensions align
from the right; each must be equal or one of them 1) lets you predict whether two tensors
combine as intended — and add explicit `unsqueeze`/`reshape` to control it rather than
relying on accidental alignment.

### The code, every line explained

```python
import torch
import torch.nn as nn

# --- read the shape error: match dims to YOUR tensors -------------------
x = torch.randn(32, 784)               # (batch=32, features=784)
# layer = nn.Linear(256, 10)           # WRONG: expects last dim 256, got 784
layer = nn.Linear(784, 10)             # FIX: in_features must equal x's last dim (784)
out = layer(x)                         # (32, 10): 32 samples, 10 outputs each
print(x.shape, "->", out.shape)        # PRINT shapes to confirm at every step

# --- the universal debugging move: assert/print shapes ------------------
def forward(x):
    print("in:", x.shape)              # (32, 784)
    x = layer1(x);  print("h1:", x.shape)   # catch the mismatch at the EXACT layer
    x = layer2(x);  print("h2:", x.shape)
    return x
# or assert the contract so a wrong shape fails loudly (7.2):
assert x.shape[-1] == 784, f"expected 784 features, got {x.shape[-1]}"

# --- broadcasting: powerful, and a silent-bug source --------------------
batch = torch.randn(32, 10)            # (32, 10)
bias  = torch.randn(10)                # (10,) -> broadcasts to (32, 10): adds bias per column
out = batch + bias                     # OK, INTENDED: each row gets the same 10-bias

a = torch.randn(32, 1)                 # (32, 1)
b = torch.randn(1, 10)                 # (1, 10)
c = a + b                              # broadcasts to (32, 10) — maybe NOT what you meant!
# Rule: align shapes from the RIGHT; each dim must be EQUAL or one of them == 1.
# (32,1) + (1,10) -> (32,10): a silent outer-sum. If you expected an error, you got a bug.

# --- control broadcasting explicitly ------------------------------------
v = torch.randn(10)                    # (10,)
v.unsqueeze(0).shape                   # (1, 10) — add a leading dim (e.g. a batch axis)
v.unsqueeze(1).shape                   # (10, 1) — add a trailing dim
x.reshape(32, -1).shape                # (32, 784) — -1 = "infer this dim"; flatten safely
x.view(-1).shape                       # (25088,) — flatten everything (contiguous tensors)

# --- the most common shape bugs -----------------------------------------
# - forgot the BATCH dimension: model expects (batch, features), you passed (features,)
#   -> x.unsqueeze(0) to add batch dim of 1
# - wrong layer size: Linear(in, out) with `in` != input's last dim (the example above)
# - need a transpose: (seq, batch, dim) vs (batch, seq, dim) — check the API's expected order
# - channels order: images as (N, C, H, W) [PyTorch] vs (N, H, W, C) [TF] — don't mix
```

### Impact

- **Fast debugging:** printing/asserting shapes turns cryptic multi-line errors into "this
  dimension is wrong here," often the difference between minutes and hours of confusion.
- **Catches silent broadcasting bugs:** understanding the rule prevents wrong-but-not-
  erroring results (the dangerous kind) from unintended dimension stretching.
- **Confident model wiring:** knowing each layer's expected input/output shape lets you
  assemble and modify architectures without trial-and-error.

### Pros & cons / when NOT to

This is foundational DL debugging, not an optional technique:

- **Always print/assert shapes when wiring or debugging a model** — it's the single most
  effective habit for the most common class of DL bug.
- **Treat unintended broadcasting as a real risk** — if two shapes "happen to" combine,
  confirm that's what you meant; add `assert x.shape == (...)` on critical tensors so a
  wrong shape fails loudly (7.2) instead of silently broadcasting.
- **Mind framework conventions** — image channel order (NCHW vs NHWC), sequence order
  (batch-first vs seq-first) differ by framework/API; mixing them is a classic shape bug.
- **Don't leave debug prints in training loops** — they flood logs and slow training;
  remove or gate them once the shapes are confirmed (use asserts, which are cheap, or
  proper logging, 7.13).

### Where this shows up

- **Real work — every model you build or modify:** wiring layers, adding a batch
  dimension, reshaping between conv and linear layers — shape-checking is constant.
- **Real work — debugging "it won't run":** the first move on a shape `RuntimeError` is to
  print shapes layer by layer and find the mismatch.
- **Real work — batching for inference (8.10) and padding (9.2):** getting the batch and
  sequence dimensions right is exactly this skill.
- **Pattern mapping (secondary):** broadcasting is the vectorisation idea from 6.10/2.12
  (operate on whole arrays, no loops); shape-reasoning is the array-dimension bookkeeping
  underlying matrix/grid problems (Area 11).
[↑ Back to top](#contents)

---

<a id="9.2"></a>
## 9.2 — "My batch has sentences of different lengths and won't form a tensor" → padding & masking

### The situation

You're batching text (or any variable-length sequences) for a model. Each sentence
tokenises to a different length, and stacking them into one tensor fails:

```python
batch = [
    [5, 12, 9],            # "the cat sat"       -> 3 tokens
    [5, 8, 21, 3, 17],     # "a dog ran very far"-> 5 tokens
    [5, 12],               # "the cat"           -> 2 tokens
]
X = torch.tensor(batch)    # ValueError: expected a rectangular tensor — rows differ in length
```

A tensor must be **rectangular** — every row the same length — but real sequences vary. You
need them the same length to batch them, *without* corrupting the model's understanding of
where the real tokens end.

### What's really going on

Models process **fixed-shape batches** (9.1), but sequences (sentences, time series, audio)
have **variable length**. The standard solution is **padding**: extend every sequence to
the same length (the longest in the batch, or a fixed max) by appending a special **pad
token** (usually `0`). Now they form a rectangle and stack into a tensor.

But padding introduces a new problem: those pad tokens are *fake* — they're not real data,
and if the model attends to them or counts them in the loss, they corrupt the result. So
padding must come with a **mask**: a parallel 0/1 tensor marking which positions are real
(1) vs padding (0), so the model (attention, pooling, loss) **ignores** the padded
positions.

> **Padding** = appending a special pad token (usually 0) to make all sequences in a batch
> the same length, so they form a rectangular tensor. A **mask** = a 0/1 tensor of the same
> shape marking real (1) vs pad (0) positions, so the model ignores padding in attention,
> pooling, and loss. Pad *and* mask — padding without masking silently teaches the model
> from fake tokens.

### The move

Pad sequences to a common length and build an attention mask; let the tokenizer/utilities
do both:

```python
from torch.nn.utils.rnn import pad_sequence
seqs = [torch.tensor(s) for s in batch]
X = pad_sequence(seqs, batch_first=True, padding_value=0)   # (3, 5) rectangle, 0-padded
mask = (X != 0).long()                                       # 1 where real, 0 where padded
```

### Why it works

`pad_sequence` finds the longest sequence and pads the shorter ones with `padding_value=0`
to match, producing a rectangular `(batch, max_len)` tensor that stacks cleanly (9.1). The
`mask = (X != 0)` marks every real token 1 and every pad 0, so downstream operations can
**exclude** padded positions: attention layers add `-inf` to masked scores (so padding gets
~zero attention weight), pooling averages only real tokens, and the loss ignores pad
positions. The model therefore learns *only* from real tokens — padding makes the batch
the right shape without polluting what the model learns. Hugging Face tokenizers return the
`input_ids` *and* the `attention_mask` together for exactly this reason.

### The code, every line explained

```python
import torch
from torch.nn.utils.rnn import pad_sequence

# --- pad a batch to a rectangle -----------------------------------------
batch = [[5, 12, 9], [5, 8, 21, 3, 17], [5, 12]]
seqs = [torch.tensor(s) for s in batch]
X = pad_sequence(seqs, batch_first=True, padding_value=0)
# X = [[ 5, 12,  9,  0,  0],     <- padded to length 5 (the longest)
#      [ 5,  8, 21,  3, 17],
#      [ 5, 12,  0,  0,  0]]     batch_first=True -> shape (batch, seq) = (3, 5)

# --- build the mask: 1 = real token, 0 = padding ------------------------
mask = (X != 0).long()
# mask = [[1,1,1,0,0],
#         [1,1,1,1,1],
#         [1,1,0,0,0]]           the model uses this to IGNORE padded positions

# --- Hugging Face does padding + mask for you ---------------------------
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("bert-base-uncased")
enc = tok(["the cat sat", "a dog ran very far"],
          padding=True, truncation=True, return_tensors="pt")
enc["input_ids"]        # padded token ids, rectangular
enc["attention_mask"]   # the mask — PASS THIS to the model so it ignores pad tokens
out = model(**enc)      # model uses attention_mask internally; padding contributes nothing

# --- using the mask in a loss (ignore pad positions) --------------------
import torch.nn.functional as F
# for token-level loss, tell the loss to skip the pad id:
loss = F.cross_entropy(logits.view(-1, V), targets.view(-1), ignore_index=0)
#                                                            └ pad id 0 excluded from loss

# --- the silent bug: pad WITHOUT a mask ---------------------------------
# If you pad but DON'T pass the mask, the model attends to / pools / trains on the 0s
# as if they were real tokens -> degraded, hard-to-spot performance loss. Always mask.

# --- truncation: the other side of padding -----------------------------
# Sequences LONGER than the model's max length must be truncated (or chunked, 9.9):
# tok(..., truncation=True, max_length=512)  -> cut to fit the model's context (9.8)
```

### Impact

- **Variable-length data becomes batchable:** padding makes a rectangular tensor so the
  model can process the batch at all (9.1), unlocking efficient batched training/inference
  (8.10).
- **Correct learning/inference:** the mask ensures the model ignores fake pad tokens, so
  padding doesn't degrade attention, pooling, or loss — the difference between a model that
  works and one quietly trained on noise.
- **Standard, reusable:** tokenizers emit ids+mask together, so once you pass the mask
  through, the whole pipeline handles variable lengths correctly.

### Pros & cons / when NOT to

**Pad and mask when:** batching any variable-length sequences — text, time series, audio,
events — for a model.

**Watch out / when NOT to:**
- **Never pad without masking.** It's the central bug here — pad tokens treated as real
  corrupt attention/pooling/loss silently. Always pass the `attention_mask` and use
  `ignore_index` in token losses.
- **Pad to the batch max, not a global max, when you can.** Padding every batch to a huge
  fixed length wastes compute/memory on mostly-padding tensors; dynamic per-batch padding
  is cheaper. (Sorting similar-length sequences into the same batch — "bucketing" — reduces
  padding further.)
- **Truncate over-long sequences deliberately** — inputs beyond the model's context (9.8)
  must be cut or chunked (9.9); silent truncation can drop important content.
- **Pad value must match the model's pad id** — using `0` when the model's pad token isn't
  `0` mis-masks; use the tokenizer's `pad_token_id`.
- **Left vs right padding matters for generation** — decoder/generation models often need
  *left* padding; check the model's expectation.

### Where this shows up

- **Real work — every NLP/transformer pipeline:** tokenize → pad → mask is the standard
  input prep; the `attention_mask` flows through training and inference (LLMs, BERT-style
  models).
- **Real work — RNNs/time series:** padding variable-length sequences (with `pack_padded_
  sequence` to skip pads efficiently) for recurrent models.
- **Real work — batched LLM inference:** padding a batch of prompts of different lengths
  and masking so generation isn't polluted (ties to 8.10 batch inference, 9.8 context).
- **Pattern mapping (secondary):** padding-to-rectangular is shape normalisation (9.1);
  masking is the "ignore these positions" idea that recurs in matrix problems and
  variable-length processing.
[↑ Back to top](#contents)

---

<a id="9.3"></a>
## 9.3 — "CUDA out of memory" → fitting training into GPU memory

### The situation

Training crashes partway through with the most common GPU error in deep learning:

```python
model = BigModel().cuda()
for batch in loader:                   # batch_size=64
    out = model(batch.cuda())          # RuntimeError: CUDA out of memory.
                                        # Tried to allocate 2.5 GiB ... GPU has 0 bytes free
```

The GPU has, say, 16 GB of memory (VRAM), and your model + batch + the intermediate values
needed for training exceed it. The model is correct; it just doesn't *fit*.

### What's really going on

A GPU has a **fixed, limited memory** (VRAM — much smaller than system RAM), and training
must hold several things in it at once: the **model weights**, the **gradients** (one per
weight), the **optimiser state** (e.g. Adam keeps two extra values per weight), and — the
usually-dominant part — the **activations** (every intermediate output saved during the
forward pass so gradients can be computed in the backward pass). Activation memory scales
with **batch size** and **sequence length**, so a too-large batch is the most common cause
of OOM.

The levers, cheapest first:

- **Smaller batch size** — the simplest fix; directly cuts activation memory.
- **Gradient accumulation** (9.x) — keep a small batch but accumulate gradients over
  several batches before updating, simulating a large *effective* batch without its
  memory.
- **Mixed precision** — store activations in 16-bit instead of 32-bit floats, roughly
  halving activation memory and speeding up compute.
- **Gradient checkpointing** — trade compute for memory by *recomputing* activations in
  the backward pass instead of storing them all.

> **VRAM** = the GPU's dedicated memory; training must fit weights + gradients + optimiser
> state + **activations** in it. **Activations** (saved forward-pass intermediates) usually
> dominate and scale with batch size × sequence length — so **reducing batch size** is the
> first OOM fix, followed by gradient accumulation, mixed precision, and checkpointing.

### The move

Reduce activation memory — start by lowering batch size, then add mixed precision and (if
needed) gradient accumulation to keep the effective batch large:

```python
batch_size = 16                         # was 64 -> ~4x less activation memory
scaler = torch.cuda.amp.GradScaler()    # mixed precision (16-bit activations)
```

### Why it works

Cutting the batch size from 64 to 16 cuts activation memory ~4× (activations scale with
batch size), which usually clears the OOM directly. **Mixed precision** stores activations
and does matmuls in 16-bit floats — roughly halving activation memory and often speeding up
compute on modern GPUs — while keeping a 32-bit master copy of weights for stability.
**Gradient accumulation** lets you recover the large *effective* batch a small physical
batch lost: run several small batches, sum their gradients, and only then step the
optimiser — so the optimiser sees the average of (say) 64 samples while memory only ever
holds 16. **Gradient checkpointing** goes furthest: it discards most activations and
recomputes them during the backward pass, trading ~30% more compute for a large memory
saving — the lever for models that otherwise won't fit at any reasonable batch size.

### The code, every line explained

```python
import torch

# --- 1) smallest fix: reduce batch size ---------------------------------
loader = DataLoader(ds, batch_size=16)   # was 64; activation memory scales with batch (9.6)

# --- 2) mixed precision: ~half the activation memory, faster ------------
scaler = torch.cuda.amp.GradScaler()     # scales loss to keep 16-bit gradients stable
for batch in loader:
    optimizer.zero_grad()
    with torch.cuda.amp.autocast():      # run forward in 16-bit where safe
        out = model(batch.cuda())
        loss = criterion(out, target)
    scaler.scale(loss).backward()        # scaled backward (avoids 16-bit underflow)
    scaler.step(optimizer); scaler.update()

# --- 3) gradient accumulation: large EFFECTIVE batch, small memory ------
ACCUM = 4                                 # effective batch = 16 * 4 = 64
optimizer.zero_grad()
for i, batch in enumerate(loader):        # physical batch stays 16 in memory
    loss = criterion(model(batch.cuda()), target) / ACCUM   # scale so sum ≈ average
    loss.backward()                       # gradients ACCUMULATE across iterations
    if (i + 1) % ACCUM == 0:              # only step every ACCUM batches
        optimizer.step(); optimizer.zero_grad()
# Optimiser sees the gradient of ~64 samples, but VRAM only held 16 at a time.

# --- 4) gradient checkpointing: recompute activations to save memory ----
from torch.utils.checkpoint import checkpoint
# wrap expensive blocks so their activations are NOT stored, but recomputed in backward:
out = checkpoint(expensive_block, x)      # ~30% more compute, big activation-memory saving
# (or model.gradient_checkpointing_enable() for HF transformers)

# --- diagnosing & freeing -----------------------------------------------
torch.cuda.memory_summary()               # what's using VRAM
torch.cuda.empty_cache()                  # frees CACHED (unused) memory — does NOT fix a
                                          # genuine over-allocation; only helps fragmentation
# common leak: accumulating tensors that still hold the graph across iterations ->
# use loss.item() / .detach() when storing metrics, or the graph (and its memory) piles up.
```

### Impact

- **Training fits and runs:** the right combination of these levers takes a model from
  "won't start" to training on the GPU you have — often without renting a bigger one.
- **Bigger effective batches:** gradient accumulation gives large-batch training dynamics
  on small VRAM, useful when batch size affects convergence.
- **Speed + memory together:** mixed precision usually *both* halves activation memory and
  speeds up compute on modern GPUs — a near-free win.

### Pros & cons / when NOT to

**Apply these when:** you hit CUDA OOM, or want to train larger models/batches on limited
VRAM.

**Watch out / when NOT to:**
- **Reduce batch size first** — it's the simplest, most reliable fix. Reach for
  accumulation/checkpointing when a small batch alone hurts convergence or still won't fit.
- **Very small batches can destabilise training** (noisy gradients, batch-norm issues) —
  use gradient accumulation to keep the *effective* batch reasonable.
- **Mixed precision can introduce NaNs/underflow** (8.11) — use the framework's loss
  scaler (`GradScaler`/`autocast`), and keep stability-sensitive ops in 32-bit; don't
  hand-roll fp16.
- **Gradient checkpointing trades compute for memory** (~20–40% slower) — use it only when
  you need the memory, not by default.
- **`empty_cache()` is not an OOM fix** — it frees *cached* memory, not memory you're
  actually using; a genuine over-allocation needs a real reduction. And watch for the
  classic leak: storing loss/metric tensors without `.item()`/`.detach()` keeps the whole
  graph alive (Area 2 memory leaks).

### Where this shows up

- **Real work — training/fine-tuning any non-trivial model:** OOM is a routine gate;
  batch-size + mixed precision + accumulation is the standard toolkit to get under VRAM.
- **Real work — LLM fine-tuning:** long sequences make activations huge; checkpointing,
  mixed precision, and accumulation (plus parameter-efficient methods like LoRA) are how
  large models train on modest GPUs.
- **Real work — inference at scale:** batch size bounded by VRAM (8.10) — the inference
  side of the same constraint.
- **Pattern mapping (secondary):** no DSA analogue; it's a memory-vs-compute trade-off
  (the GPU sibling of Area 2's memory management) — reduce the working set, or recompute
  instead of store.
[↑ Back to top](#contents)

---

<a id="9.4"></a>
## 9.4 — "Training loss exploded to NaN (or flatlined and won't learn)" → exploding/vanishing gradients

### The situation

Two opposite training failures, same root area. Either the loss blows up:

```python
# epoch 1: loss 2.3 -> 1.8 -> 5.1 -> 9999.0 -> nan   (exploding)
```

or it refuses to move:

```python
# epoch 1..50: loss 2.30 -> 2.30 -> 2.30   (flat; the model isn't learning at all)
```

The model architecture is reasonable, but training either diverges into `NaN` (8.11) or
makes no progress. Both are symptoms of the gradients — the signal that drives learning —
being the wrong size.

### What's really going on

Neural nets learn by **gradient descent**: compute the gradient of the loss with respect
to each weight, then nudge weights in the direction that lowers the loss, scaled by the
**learning rate**. Training breaks when those gradients become pathological:

- **Exploding gradients:** gradients grow huge (often in deep/recurrent nets or with a
  too-high learning rate), weights take enormous steps, the loss overshoots and diverges to
  `inf`/`NaN` (8.11).
- **Vanishing gradients:** gradients shrink toward zero as they propagate back through many
  layers, so early layers get almost no update signal and the model barely learns.

The usual levers:

- **Learning rate** — the single most impactful knob. Too high → explode/diverge; too low →
  crawl. Tuning it fixes a large fraction of training failures.
- **Gradient clipping** — cap the gradient magnitude so a spike can't blow up the weights
  (the standard exploding-gradient fix).
- **Normalisation layers** (BatchNorm/LayerNorm) and **good initialisation/activations**
  (ReLU, residual connections) — keep gradients well-scaled through depth, addressing
  vanishing.

> Training is **gradient descent**: `weight -= learning_rate * gradient`. **Exploding
> gradients** (too large → divergence/NaN) and **vanishing gradients** (too small → no
> learning) are the two failure modes. First lever: the **learning rate**. Then: gradient
> **clipping** (for exploding) and normalisation/better architecture (for vanishing).

### The move

Tune the learning rate first; add gradient clipping to stop explosions; use normalisation
and good architecture for vanishing:

```python
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)   # start moderate; tune this knob first

for batch in loader:
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)   # cap gradient size
    optimizer.step()
```

### Why it works

The learning rate scales every weight update, so it directly governs both failure modes:
lowering it stops the overshoot that causes divergence, while raising it (or using a
schedule/warmup) unsticks a model that's barely moving. **Gradient clipping** rescales the
gradient whenever its overall magnitude exceeds `max_norm`, so a sudden spike can't push
weights to `inf` — it turns "one bad batch destroys the run" into "the step is capped and
training continues." For vanishing gradients, **normalisation layers** keep each layer's
inputs well-scaled so gradients neither shrink nor blow up through depth, and architectural
choices (ReLU activations, **residual/skip connections**) provide gradient "shortcuts" that
let signal reach early layers — which is precisely what made very deep networks trainable.

### The code, every line explained

```python
import torch

# --- learning rate: the first and most impactful knob -------------------
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
# loss diverges/NaN -> LR too high: try 1e-4, 1e-5...
# loss flat/won't move -> LR too low (or vanishing gradients): try 1e-3, add warmup/schedule
scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=1e-3, total_steps=steps)
# a SCHEDULE (warmup then decay) is standard for stable training of deep nets/transformers.

# --- gradient clipping: the exploding-gradient fix ----------------------
for batch in loader:
    optimizer.zero_grad()
    loss = criterion(model(batch.x), batch.y)
    loss.backward()                                  # compute gradients
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    #   rescales ALL gradients so their combined norm <= 1.0 -> a spike can't blow up
    optimizer.step()

# --- diagnose: watch the gradient norm ----------------------------------
total_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1e9)  # measure, don't clip
print("grad norm:", total_norm.item())
# huge & growing -> exploding (lower LR / clip).  ~0 in early layers -> vanishing.

# --- vanishing gradients: architecture + normalisation ------------------
# - use ReLU/GELU (not sigmoid/tanh in deep stacks — they saturate, killing gradients)
# - add normalisation: nn.BatchNorm / nn.LayerNorm between layers
# - use residual (skip) connections: out = x + block(x) -> gradient shortcut to early layers
# - sensible weight init (Kaiming/Xavier) so signal neither shrinks nor grows through depth

# --- NaN loss is often this + numerical instability (8.11) --------------
torch.autograd.set_detect_anomaly(True)   # (debug) pinpoints the op that produced a NaN
# and use stable losses (8.11): BCEWithLogitsLoss, log_softmax — not hand-rolled log()s.

# --- the diagnostic flow ------------------------------------------------
# loss -> NaN/inf:   lower LR, add grad clipping, check for unstable ops (8.11), check data
# loss -> flat:      raise LR / add warmup, check vanishing (grad norms), check architecture
# loss -> noisy:     LR slightly high or batch too small (9.3 accumulation)
```

### Impact

- **Training converges:** the right learning rate (plus clipping) turns a diverging or
  stuck run into one that actually learns — often the single biggest unblock in DL.
- **Robust to spikes:** gradient clipping makes training resilient to the occasional bad
  batch that would otherwise blow the run to `NaN`.
- **Deep nets become trainable:** normalisation + residual connections keep gradients
  healthy through many layers, which is what enables very deep/large models.

### Pros & cons / when NOT to

**Reach for these when:** training diverges to NaN, won't learn, or is unstable — i.e. most
DL training-debugging sessions.

**Watch out / when NOT to:**
- **Tune the learning rate before anything else** — it's the highest-leverage knob and
  fixes a large share of both failure modes. Use an LR-finder or a schedule with warmup.
- **NaN loss is often LR + numerical instability together** — pair LR/clipping with stable
  losses and epsilon guards (8.11); check the *input data* for NaNs too (3.23) before
  blaming gradients.
- **Clipping treats the symptom, not always the cause** — if you must clip aggressively to
  survive, the LR is probably too high or the architecture/init is off; clipping is a
  safety net, not a substitute for a sane setup.
- **Vanishing gradients are usually architectural** — sigmoid/tanh in deep stacks, no
  normalisation, no residuals. Modern architectures (ReLU/GELU, LayerNorm, residuals)
  largely prevent it; reach for those rather than just cranking the LR.
- **Don't thrash randomly** — diagnose with the gradient norm and loss curve shape (NaN vs
  flat vs noisy) to pick the right lever, instead of changing five things at once.

### Where this shows up

- **Real work — every training run that won't converge:** the first checks are LR and
  gradient norms; clipping is standard in RNN/transformer training.
- **Real work — RNNs/transformers:** especially prone to exploding gradients over long
  sequences — `clip_grad_norm_` and LR warmup are routine.
- **Real work — debugging a NaN loss:** this scenario + numerical stability (8.11) +
  checking inputs (3.23) form the standard NaN-hunt.
- **Pattern mapping (secondary):** no DSA analogue; it's the optimisation-dynamics
  knowledge specific to training neural nets, tightly coupled to numerical stability
  (8.11).
[↑ Back to top](#contents)

---

<a id="9.5"></a>
## 9.5 — "I saved the model but resuming training gives different results" → checkpoints (model + optimizer)

### The situation

You checkpoint a training run (7.6) so it can resume after interruption. You save the
model's weights, reload them, and continue — but the resumed run trains *differently* than
an uninterrupted one would:

```python
torch.save(model.state_dict(), "ckpt.pt")    # saved ONLY the weights
# ...crash, restart...
model.load_state_dict(torch.load("ckpt.pt"))  # weights restored
# resume training -> loss behaves oddly; it's NOT continuing where it left off
```

The weights are back, but the resumed optimiser starts "cold" — it lost the momentum and
adaptive learning-rate state it had built up, and the learning-rate schedule restarted from
step 0. So the model takes different steps than it would have, and resuming isn't truly
seamless.

### What's really going on

This is checkpointing (7.6) specialised to neural-net training, where "the state needed to
resume" is **more than the weights**. Optimisers like Adam keep **per-parameter state**
(running averages of gradients — the "momentum" and variance estimates) that shape every
update; the **learning-rate scheduler** tracks the current step; and you need the **epoch/
step counter** and ideally the **RNG state** (8.7) to reproduce the data order. Save only
`model.state_dict()` and you lose all of that — resuming is a *cold restart of the
optimiser on warm weights*, which trains differently.

A correct checkpoint bundles **everything needed to continue identically**: model weights,
optimiser state, scheduler state, epoch, and RNG/seed state — exactly the "save all state
required to resume" principle from 7.6, with neural-net specifics.

> A neural-net **checkpoint** must capture: `model.state_dict()` (weights) **+**
> `optimizer.state_dict()` (momentum/adaptive state) **+** scheduler state **+** epoch/step
> **+** RNG state. Saving weights alone gives a cold-optimiser resume that diverges from
> uninterrupted training. (This is 7.6 applied to DL; save it *atomically*, 7.8, and
> version it, 8.9.)

### The move

Checkpoint the full training state — model, optimiser, scheduler, epoch — and restore all
of it on resume:

```python
torch.save({
    "model": model.state_dict(),
    "optimizer": optimizer.state_dict(),   # momentum/adaptive state — the part people forget
    "scheduler": scheduler.state_dict(),
    "epoch": epoch,
}, "ckpt.pt")
```

### Why it works

Bundling the optimiser's `state_dict` preserves Adam's running gradient/variance averages,
so on resume it keeps stepping with the momentum it had built up — not from zero. Saving
the scheduler state means the learning rate continues along its schedule instead of
resetting to the warmup value. Restoring the epoch/step counter resumes the loop at the
right place, and restoring RNG state (8.7) reproduces the data shuffling order. With all of
it restored, the resumed run takes the *same* steps it would have taken without
interruption — true seamless resumption, the neural-net realisation of 7.6/7.7. For serving
(as opposed to resuming training), you only need the weights — which is why "save the state
dict" (not a pickled module, 8.9) is also the robust way to deploy.

### The code, every line explained

```python
import torch, os, tempfile

# --- SAVE: the full training state (resume-complete) --------------------
def save_checkpoint(path, model, optimizer, scheduler, epoch):
    state = {
        "model": model.state_dict(),          # weights
        "optimizer": optimizer.state_dict(),   # momentum / adaptive LR state (Adam etc.)
        "scheduler": scheduler.state_dict(),   # current LR-schedule position
        "epoch": epoch,                         # where to resume the loop
        "rng": torch.get_rng_state(),           # reproduce data order (8.7)
    }
    # atomic write (7.8): temp + rename so a crash mid-save keeps the last good ckpt
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".")
    torch.save(state, tmp); os.replace(tmp, path)

# --- LOAD: restore EVERYTHING, resume seamlessly ------------------------
def load_checkpoint(path, model, optimizer, scheduler):
    ckpt = torch.load(path, map_location="cpu")   # map_location: load GPU ckpt on CPU safely
    model.load_state_dict(ckpt["model"])
    optimizer.load_state_dict(ckpt["optimizer"])   # <- the step that makes resume SEAMLESS
    scheduler.load_state_dict(ckpt["scheduler"])
    torch.set_rng_state(ckpt["rng"])
    return ckpt["epoch"]                            # resume the loop from here

# --- resume-aware training loop -----------------------------------------
start = load_checkpoint("ckpt.pt", model, optimizer, scheduler) if os.path.exists("ckpt.pt") else 0
for epoch in range(start, num_epochs):
    train_one_epoch(...)
    save_checkpoint("ckpt.pt", model, optimizer, scheduler, epoch + 1)   # every epoch (7.6)

# --- for SERVING (not resuming): weights are enough ---------------------
torch.save(model.state_dict(), "weights.pt")     # state_dict = portable across code refactors
model.load_state_dict(torch.load("weights.pt")); model.eval()   # eval mode for inference (9.7)
# NOTE: prefer state_dict over torch.save(model) — a pickled MODULE breaks if your class
# definition changes (8.9); the state_dict is just tensors, robust to refactors.

# --- keep multiple checkpoints + save the BEST --------------------------
# rotate last N (so a crash mid-save doesn't lose everything, 7.6) AND keep best-by-val-metric
if val_metric > best: best = val_metric; save_checkpoint("best.pt", ...)
```

### Impact

- **Truly seamless resume:** restoring optimiser+scheduler+RNG means the resumed run
  continues exactly as if uninterrupted — essential for long/interrupted training (7.7).
- **No wasted GPU-hours:** combined with frequent checkpoints (7.6) and atomic writes
  (7.8), an interruption (crash, spot-instance reclaim) costs one epoch, not the whole run.
- **Robust deployment artifacts:** saving the state dict (not a pickled module) gives
  weights that load across code changes and serve correctly (8.9).

### Pros & cons / when NOT to

**Checkpoint the full state when:** training any model long enough that you'd resume after
an interruption — i.e. essentially all real DL training.

**Watch out / when NOT to:**
- **Saving only `model.state_dict()` breaks seamless resume** — the optimiser/scheduler
  state is what people forget, and its absence makes resumed training diverge. Bundle all
  of it.
- **Prefer `state_dict` over pickling the whole module** (8.9) — a pickled `nn.Module`
  breaks when your class definition changes; the state dict is portable tensors.
- **Write atomically and keep more than one** (7.6/7.8) — a crash *during* a save can
  corrupt the only checkpoint; temp-then-rename and rotate the last N.
- **Match devices on load** — use `map_location` to load a GPU checkpoint on CPU (or a
  different GPU) without errors.
- **Serving needs only weights** — don't ship the optimiser state to production; that's for
  resuming training, not inference.

### Where this shows up

- **Real work — long/interrupted training:** the standard resume mechanism for multi-hour/
  day training and spot-instance/preemptible compute (7.6/7.7 applied to DL).
- **Real work — best-model selection:** checkpointing the best-by-validation model
  separately from the latest, so you keep the best even if later epochs overfit.
- **Real work — deployment:** exporting the trained weights (state dict / safetensors,
  8.9) as the serving artifact, loaded in `eval()` mode (9.7).
- **Pattern mapping (secondary):** no DSA analogue; it's checkpointing (7.6) + atomic
  writes (7.8) + serialization/versioning (8.9) specialised to neural-net training state.
[↑ Back to top](#contents)

---

<a id="9.6"></a>
## 9.6 — "My expensive GPU sits idle waiting for data" → workers & prefetch

### The situation

You're training on a fast GPU, but `nvidia-smi` shows GPU utilisation bouncing between 0%
and 100% — it's idle half the time. Training is slow not because the GPU is weak, but
because it keeps **waiting for the next batch** to be loaded and preprocessed:

```python
loader = DataLoader(dataset, batch_size=64)          # num_workers defaults to 0!
for batch in loader:                                  # data loaded on the MAIN process,
    out = model(batch.cuda())                          # GPU WAITS while the CPU reads+decodes
```

With `num_workers=0`, each batch is loaded and preprocessed on the main process *between*
GPU steps — so the GPU does a fast forward/backward pass, then sits idle while the CPU
prepares the next batch. The most expensive resource in the system is starved by the
cheapest.

### What's really going on

Training is a two-stage pipeline (5.7): **load+preprocess a batch** (CPU/disk, I/O-bound)
then **forward+backward** (GPU, compute). Run them serially on one process and they
alternate — GPU idle during loading, CPU idle during compute. The fix is to **overlap**
them: load the *next* batch on background workers *while* the GPU trains on the current one,
so a prepared batch is always ready when the GPU finishes.

`DataLoader`'s `num_workers` spins up background processes (6.2) that load and preprocess
batches in parallel, and `prefetch_factor` has them stage batches ahead. This is the
data-loading (8.13) and producer/consumer (5.6) ideas applied to keep the GPU fed.

> **`num_workers`** = background processes that load/preprocess batches in parallel, so the
> GPU isn't blocked on data. **Prefetching** = preparing upcoming batches ahead of time.
> Together they overlap the CPU/disk data stage with the GPU compute stage (5.7), keeping
> GPU utilisation high. The symptom of getting this wrong is a fast GPU at low utilisation.

### The move

Set `num_workers` to load batches in parallel, plus pinned memory and prefetch for fast
transfer:

```python
loader = DataLoader(dataset, batch_size=64,
                    num_workers=8,        # background processes load/preprocess in parallel
                    pin_memory=True,       # faster CPU->GPU copy
                    prefetch_factor=2)     # each worker stages 2 batches ahead
```

### Why it works

The `num_workers` background processes load and preprocess upcoming batches *while* the GPU
trains on the current one — so when the GPU finishes a step, the next batch is already
prepared and waiting, eliminating the idle gap. `prefetch_factor` keeps a small buffer of
ready batches so a momentarily slow disk read doesn't stall the GPU. `pin_memory=True` puts
batches in page-locked memory that transfers to the GPU faster (and can overlap with
compute). The net effect is the load and compute stages run *concurrently* (5.7) instead of
alternating, so GPU utilisation rises toward 100% and wall-clock training time drops — often
dramatically when preprocessing is heavy (image decode/augment, tokenisation).

### The code, every line explained

```python
from torch.utils.data import DataLoader

# --- the fix: parallel loading + prefetch + pinned memory ---------------
loader = DataLoader(
    dataset,
    batch_size=64,
    num_workers=8,        # 8 background processes prepare batches in parallel (6.2)
    pin_memory=True,       # page-locked host memory -> faster, async CPU->GPU transfer
    prefetch_factor=2,     # each worker keeps 2 batches ready ahead of time
    persistent_workers=True,  # don't tear down workers every epoch (avoids re-spawn cost)
)
for batch in loader:
    out = model(batch.cuda(non_blocking=True))   # non_blocking pairs with pin_memory for overlap

# --- diagnose first: is data loading the bottleneck? --------------------
# watch `nvidia-smi` (or torch profiler): GPU util oscillating low <-> high while the CPU
# is busy = data-starved. GPU pinned near 100% = compute-bound (this won't help; 9.3).
# Time a pure data pass vs a pure compute pass to see which dominates.

# --- tuning num_workers -------------------------------------------------
# too few (0/1): GPU starves waiting on data (the original problem)
# too many: CPU/RAM contention, worker spawn overhead, even slower; also more shared-mem use
# rule of thumb: start ~ number of CPU cores, then tune by watching GPU utilisation.

# --- pitfalls -----------------------------------------------------------
# - workers re-import your module (6.2): keep Dataset code importable, no unpicklable state
# - heavy AUGMENTATION in __getitem__ is fine (it's parallelised) — that's the point
# - on Windows/notebooks, num_workers>0 needs the __main__ guard / can be finicky
# - if preprocessing is the REAL cost, move it off the hot path: precompute & cache (2.8),
#   or store a preprocessed/tokenised dataset on disk so loading is cheap

# --- when MORE workers won't help: you're compute-bound -----------------
# if the GPU is already ~100% utilised, the bottleneck is the model, not data loading ->
# this scenario doesn't apply; look at 9.3 (memory), mixed precision, or a bigger GPU.
```

### Impact

- **High GPU utilisation:** overlapping data loading with compute keeps the expensive GPU
  busy, often cutting wall-clock training time substantially when preprocessing is heavy.
- **Cost efficiency:** a GPU idling on data is money wasted; feeding it well gets the
  throughput you're paying for.
- **Scales preprocessing:** parallel workers absorb expensive per-sample transforms (image
  decode/augment, tokenise) without bottlenecking training.

### Pros & cons / when NOT to

**Tune workers/prefetch when:** GPU utilisation is low and oscillating (data-starved), or
preprocessing per sample is non-trivial.

**Watch out / when NOT to:**
- **Diagnose first — this only helps if you're data-bound.** If the GPU is already ~100%
  utilised you're *compute*-bound; more workers do nothing (look at 9.3, mixed precision,
  or model size instead).
- **More workers isn't always better** — too many cause CPU/RAM contention and spawn
  overhead, sometimes slowing things down. Tune by watching utilisation; start near core
  count.
- **Workers are separate processes** (6.2) — `Dataset` code must be importable and
  picklable, no open handles/unpicklable state; on Windows/notebooks `num_workers>0` is
  finicky (needs `__main__` guard).
- **If preprocessing is the real cost, move it off the hot path** — precompute and cache
  (2.8), or store a tokenised/preprocessed dataset, rather than re-doing heavy work every
  epoch on workers.
- **`pin_memory` only helps GPU training** — it's pointless (and uses page-locked RAM) for
  CPU-only runs.

### Where this shows up

- **Real work — image/video training:** decode + augment per sample is heavy; parallel
  workers are essential to keep the GPU fed (the classic data-starvation case).
- **Real work — LLM/NLP training:** parallel tokenisation/loading, or precomputing a
  tokenised dataset so the GPU isn't waiting on text processing.
- **Real work — cloud GPU cost control:** maximising GPU utilisation directly reduces the
  cost of expensive accelerator time.
- **Pattern mapping (secondary):** it's the producer/consumer pipeline (5.6/5.7) and
  parallel loading (6.2) applied to training — overlap the slow I/O stage with the fast
  compute stage so neither waits.
[↑ Back to top](#contents)

---

<a id="9.7"></a>
## 9.7 — "My model gives different predictions each call, and inference is slow + OOMs" → eval mode & no_grad

### The situation

You deploy a trained model for inference and hit three odd problems at once:

```python
model = load_model()
pred1 = model(x)                       # 0.83
pred2 = model(x)                       # 0.79 (!) — SAME input, DIFFERENT output
# also: inference is slower than expected and uses lots of memory, sometimes OOMs (9.3)
```

The same input gives different predictions run to run, inference is sluggish, and memory
balloons — all because the model is still in **training mode** and is **tracking gradients**
during inference, neither of which you want when just predicting.

### What's really going on

Neural nets behave **differently in training vs inference**, and two switches control it:

1. **Train vs eval mode (`model.train()` / `model.eval()`).** Some layers behave
   differently in each mode. **Dropout** randomly zeroes activations during training (for
   regularisation) — if left on at inference, predictions become *random*, hence the
   different outputs. **BatchNorm** uses batch statistics during training but stored running
   statistics at inference — using batch stats at serve time gives wrong, batch-dependent
   results. `model.eval()` switches these layers to inference behaviour.

2. **Gradient tracking (`torch.no_grad()`).** By default, the framework builds a
   computation graph and stores intermediates so it can compute gradients — necessary for
   *training*, pure waste for *inference*. It makes inference slower and uses far more
   memory (storing activations, 9.3). `torch.no_grad()` turns it off.

> For inference: call **`model.eval()`** (so dropout/BatchNorm behave correctly — fixes the
> random/wrong predictions) **and** wrap prediction in **`torch.no_grad()`** (so no gradient
> graph is built — faster, much less memory). Forgetting `eval()` gives wrong/random
> outputs; forgetting `no_grad()` wastes speed and memory.

### The move

Switch to eval mode once, and wrap inference in `no_grad` (or `inference_mode`):

```python
model.eval()                            # dropout off, BatchNorm uses running stats
with torch.no_grad():                   # no gradient graph -> faster, less memory
    pred = model(x)
```

### Why it works

`model.eval()` flips every dropout layer off (so activations are deterministic — same input
gives the same output) and tells BatchNorm to use its stored running statistics instead of
the current batch's — both required for correct, stable inference. `torch.no_grad()` tells
the framework not to record operations for backpropagation, so it doesn't build the
computation graph or retain activations — that's where the speed-up and the large memory
reduction (9.3) come from. Together they configure the model for *prediction* rather than
*learning*. (Remember to call `model.train()` again if you resume training — eval mode
persists until you switch back.)

### The code, every line explained

```python
import torch

# --- the correct inference pattern --------------------------------------
model.eval()                             # set INFERENCE behaviour for dropout/BatchNorm
with torch.no_grad():                    # disable gradient tracking for everything inside
    for batch in loader:                 # (batched inference, 8.10)
        preds = model(batch.cuda())      # deterministic, fast, low-memory
# eval() persists -> call model.train() before resuming training, or BatchNorm/dropout
# stay in inference mode and training silently misbehaves.

# --- torch.inference_mode(): an even faster no_grad (PyTorch 1.9+) ------
with torch.inference_mode():             # like no_grad but with extra optimisations
    preds = model(x)                     # use for pure inference (can't use results in autograd)

# --- what each switch fixes ---------------------------------------------
# WITHOUT model.eval():
#   - Dropout stays ON -> randomly zeros activations -> DIFFERENT output each call (the bug)
#   - BatchNorm uses the CURRENT batch's stats -> predictions depend on what else is in the
#     batch (a single sample vs a batch gives different results) -> wrong + unstable
# WITHOUT torch.no_grad():
#   - the autograd graph + activations are stored every call -> slower and high memory (9.3),
#     can OOM on large inputs even though no training is happening

# --- the training/eval toggle in a train loop ---------------------------
for epoch in range(epochs):
    model.train()                        # TRAINING mode: dropout on, BatchNorm uses batch stats
    for batch in train_loader:
        ...                               # forward/backward WITH gradients
    model.eval()                          # switch to EVAL for validation
    with torch.no_grad():
        for batch in val_loader:          # validate without dropout/grad
            ...
# Forgetting to toggle back to train() after validation is a classic, silent bug.

# --- serving checklist --------------------------------------------------
# [ ] model.eval() called?         (correct dropout/BatchNorm)
# [ ] inference under no_grad/inference_mode?  (fast, low memory)
# [ ] weights loaded from state_dict (9.5/8.9), preprocessing via the saved pipeline (8.16)?
```

### Impact

- **Correct, deterministic predictions:** `eval()` stops dropout/BatchNorm from randomising
  or distorting outputs, so the same input reliably gives the same answer — essential for
  serving and evaluation.
- **Faster, lighter inference:** `no_grad`/`inference_mode` skip the gradient graph and
  activation storage, cutting latency and memory (often the fix for inference-time OOM,
  9.3).
- **Trustworthy validation:** evaluating in eval mode means your val/test metrics reflect
  real inference behaviour, not a dropout-randomised version.

### Pros & cons / when NOT to

**Always set eval() + no_grad() when:** running inference or validation — serving,
evaluation, embedding extraction, any forward pass where you're not training.

**Watch out / when NOT to:**
- **Forgetting `eval()` is a silent correctness bug** — outputs become random (dropout) or
  batch-dependent (BatchNorm), and nothing errors; you just get worse, unstable
  predictions. It's the first thing to check when "predictions vary for the same input."
- **Remember to toggle back to `train()`** before resuming training (e.g. after a
  validation loop) — leaving the model in eval mode silently disables dropout/correct
  BatchNorm during training.
- **`no_grad`/`inference_mode` results can't be used in further autograd** — they're for
  pure inference; don't wrap a forward pass you intend to backprop through.
- **eval() doesn't change the weights or preprocessing** — for correct serving you still
  need the right weights (9.5) and the saved preprocessing pipeline (8.16); eval mode is
  one part of the serving checklist.

### Where this shows up

- **Real work — every model deployment:** `model.eval()` + `no_grad()` is the standard,
  required inference setup; omitting it is one of the most common serving bugs.
- **Real work — validation/evaluation loops:** switching to eval mode for the val pass so
  metrics (8.5) reflect true inference behaviour, then back to train.
- **Real work — embedding/feature extraction:** running a model forward to get embeddings
  under `no_grad` for speed and memory (feeds 9.9/9.14, RAG).
- **Pattern mapping (secondary):** no DSA analogue; it's the train-vs-inference mode
  discipline specific to neural nets, and a key item on the serving checklist alongside
  serialization (8.9) and skew (8.16).
[↑ Back to top](#contents)

---

<a id="9.8"></a>
## 9.8 — "My LLM call failed: too many tokens" → tokens & context budgets

### The situation

You build a prompt by concatenating a system instruction, some retrieved documents, and the
user's question, and the API rejects it:

```python
prompt = system + "\n".join(retrieved_docs) + user_question
response = llm(prompt)     # Error: maximum context length is 8192 tokens, your input has 11403
```

Or it *succeeds* but the model's reply is truncated, because the input ate so much of the
budget there was no room left for the output. You were thinking in characters or words; the
model thinks in **tokens**, and there's a hard ceiling on how many it can handle at once.

### What's really going on

LLMs don't read characters or words — they read **tokens**: sub-word chunks produced by a
**tokenizer**. Roughly, 1 token ≈ 4 characters ≈ ¾ of a word in English, but it varies by
text (code, rare words, and other languages tokenise into more tokens). Every model has a
**context window**: a maximum number of tokens it can process in one call, *shared between
the input (prompt) and the output (completion)*. Exceed it and the call errors; come close
and the output gets squeezed.

So you must **budget tokens**: count the prompt's tokens, reserve enough for the desired
output, and keep `input + output ≤ context_limit`. This means measuring with the *model's
own tokenizer* (not a character estimate), and trimming/chunking (9.9) input that won't fit.

> A **token** is the unit an LLM processes (a sub-word piece from its **tokenizer**);
> ~4 chars/token in English but variable. The **context window** caps total tokens per call,
> shared by **input + output** — so you must count input tokens and *reserve* output budget.
> Count with the model's tokenizer (e.g. `tiktoken`), never by character length, or you'll
> mis-budget and hit "too many tokens".

### The move

Count tokens with the model's tokenizer, reserve output budget, and trim input to fit:

```python
import tiktoken
enc = tiktoken.encoding_for_model("gpt-4")     # the MODEL'S tokenizer, not a char estimate

def n_tokens(text): return len(enc.encode(text))

CONTEXT = 8192; RESERVE_OUTPUT = 1000
budget_for_input = CONTEXT - RESERVE_OUTPUT     # leave room for the model to respond
```

### Why it works

Encoding with the model's *own* tokenizer gives the exact token count the API will see, so
your budget matches reality instead of a character guess that's off for code/non-English
text. Subtracting a reserved output allowance (`RESERVE_OUTPUT`) enforces `input + output ≤
context`, so the model always has room to produce a complete answer rather than getting cut
off. With a measured input size and a known budget, you can deterministically decide whether
to send as-is, trim the least-important content, or chunk it (9.9) — turning "hope it fits"
into "know it fits." This is the foundation for RAG context assembly: fit the most relevant
retrieved chunks into the input budget.

### The code, every line explained

```python
import tiktoken

enc = tiktoken.encoding_for_model("gpt-4")   # exact tokenizer for the target model
def n_tokens(text):
    return len(enc.encode(text))             # encode -> list of token ids -> count them

# --- budget: keep input + output within the context window --------------
CONTEXT = 8192               # the model's max tokens per call (check the model's docs)
RESERVE_OUTPUT = 1000        # tokens you want available for the RESPONSE
input_budget = CONTEXT - RESERVE_OUTPUT      # = 7192 tokens for the whole prompt

# --- measure the prompt parts -------------------------------------------
sys_tokens = n_tokens(system)
q_tokens   = n_tokens(user_question)
remaining  = input_budget - sys_tokens - q_tokens   # tokens left for retrieved docs

# --- fit retrieved docs into the remaining budget (RAG context assembly) -
context, used = [], 0
for doc in retrieved_docs:                   # assumed ordered by relevance (9.14)
    t = n_tokens(doc)
    if used + t > remaining:
        break                                # stop before overflowing; keep the top docs
    context.append(doc); used += t
prompt = system + "\n".join(context) + user_question
assert n_tokens(prompt) <= input_budget      # fail loud if budgeting is wrong (7.2)

# --- char-count estimate is WRONG (why you must tokenize) ---------------
# len(text)//4 is a rough English guess; code, JSON, and other languages tokenize into
# MORE tokens per char, so a char estimate silently under-counts and you overflow.

# --- trimming a single over-long text -----------------------------------
ids = enc.encode(long_text)
if len(ids) > input_budget:
    long_text = enc.decode(ids[:input_budget])   # truncate by TOKENS (decode back to text)
    # better than truncating chars: lands on a valid token boundary and a known count.
# For long documents you usually CHUNK rather than truncate (9.9) to avoid losing content.
```

### Impact

- **No "too many tokens" failures:** budgeting against the real token count prevents the
  call from being rejected, and reserving output prevents truncated replies.
- **Predictable cost:** tokens drive both limits *and* billing (5.20), so counting them lets
  you estimate and control spend, not just avoid errors.
- **Better RAG:** fitting the most-relevant chunks into the input budget (9.14) maximises
  useful context without overflow — the core of context assembly.

### Pros & cons / when NOT to

**Count and budget tokens when:** building prompts programmatically, doing RAG, or sending
variable/large input to an LLM — i.e. essentially all LLM application code.

**Watch out / when NOT to:**
- **Never estimate by characters/words for budgeting** — use the model's tokenizer.
  Char-based guesses under-count code/JSON/non-English and cause overflow.
- **Input and output share the window** — reserve output budget, or a big prompt leaves no
  room for the answer and the response gets cut off.
- **Use the *right* tokenizer per model** — different model families tokenize differently;
  counting with the wrong one mis-budgets. (For non-OpenAI models, use that provider's
  tokenizer / count endpoint.)
- **Truncation loses content silently** — trimming to fit drops information; for long
  documents prefer chunking + retrieval (9.9/9.14) so you keep the relevant parts.
- **Token limits change by model** — a 8k vs 128k context model changes the whole budget;
  don't hard-code one limit across models.

### Where this shows up

- **Real work — RAG context assembly:** fitting retrieved chunks (9.9/9.14) plus the
  question into the input budget is the daily LLM-engineering task.
- **Real work — cost control:** token counting feeds usage/cost accounting (5.20) — tokens
  are the billing unit, so budgeting tokens is budgeting money.
- **Real work — long-document handling:** deciding when to chunk vs truncate vs summarise
  based on measured token counts.
- **Pattern mapping (secondary):** the "fit items into a fixed budget by value" assembly is
  a greedy knapsack-style packing (Area 11) — take the highest-relevance chunks until the
  budget is full.
[↑ Back to top](#contents)

---

<a id="9.9"></a>
## 9.9 — "Retrieval returns half a sentence or a whole irrelevant chapter" → chunking strategy

### The situation

You're building RAG: split documents into pieces, embed each, and retrieve the relevant
ones for a question. Your naive split hurts retrieval quality:

```python
# fixed-size split by characters, ignoring meaning:
chunks = [doc[i:i+500] for i in range(0, len(doc), 500)]   # cut every 500 chars
# chunk boundaries fall MID-SENTENCE: "...the refund policy is" | "30 days for unopened..."
# now neither chunk contains the full fact -> retrieval finds a fragment, answer is wrong
```

Chunks that are too big retrieve a whole chapter when you needed one paragraph (diluting
relevance and wasting context budget, 9.8); too small lose the surrounding context that
makes a fact meaningful; and arbitrary boundaries split sentences/ideas in half so no single
chunk holds a complete thought.

### What's really going on

Retrieval quality depends heavily on **how you chunk**. The chunk is the unit that gets
embedded (9.14) and retrieved, so a chunk should ideally contain **one coherent, complete
idea** — big enough to be self-contained, small enough to be specific. Three levers:

- **Chunk size** — balance completeness (enough context to stand alone) against specificity
  (not so big it dilutes relevance or blows the token budget, 9.8). Often sized in tokens,
  not characters.
- **Boundaries** — split on **semantic** boundaries (paragraphs, sentences, headings), not
  arbitrary character counts, so a chunk doesn't cut an idea in half.
- **Overlap** — let consecutive chunks share some text at the edges, so a fact spanning a
  boundary still appears whole in at least one chunk.

> **Chunking** = splitting documents into the units that get embedded and retrieved. Good
> chunks are **semantically coherent** (split on sentence/paragraph boundaries, not raw
> char counts), **right-sized** (self-contained but specific, measured in tokens, 9.8), and
> **overlapping** (shared edges so boundary-spanning facts aren't lost). Bad chunking is one
> of the biggest, most overlooked causes of poor RAG quality.

### The move

Split on semantic boundaries into token-sized chunks with overlap (a recursive splitter
handles this well):

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50,          # ~500-token chunks, 50-token overlap
    separators=["\n\n", "\n", ". ", " "],       # prefer paragraph > line > sentence > word
)
chunks = splitter.split_text(document)
```

### Why it works

A recursive splitter tries the *biggest* semantic separator first (paragraph breaks), only
falling back to finer ones (lines, sentences, words) when a piece is still too large — so it
keeps coherent units together and avoids cutting mid-sentence wherever possible. `chunk_
size` keeps each piece self-contained yet specific, and sizing it in tokens (9.8) makes it
fit the embedding model and the eventual context budget. `chunk_overlap` repeats a little
text at each boundary, so a fact that straddles two chunks ("...refund policy is | 30 days
for unopened...") appears intact in at least one of them — the single most effective fix for
the "retrieved a fragment" problem. Better chunks mean the embedding (9.14) captures one
clear idea, so retrieval returns relevant, complete context.

### The code, every line explained

```python
# --- recommended: recursive, semantic-boundary splitting with overlap ---
from langchain.text_splitter import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,            # target chunk size (use a TOKEN-based splitter to size in tokens, 9.8)
    chunk_overlap=50,           # consecutive chunks share ~50 units -> boundary facts survive
    separators=["\n\n", "\n", ". ", " ", ""],   # try paragraph, then line, sentence, word
)
chunks = splitter.split_text(document)   # coherent, overlapping, right-sized pieces

# --- token-aware sizing (so chunks fit the embedding/model budget, 9.8) -
import tiktoken
enc = tiktoken.get_encoding("cl100k_base")
def token_len(text): return len(enc.encode(text))
# many splitters accept a length_function=token_len so chunk_size is in TOKENS, not chars.

# --- the naive version and why it fails ---------------------------------
# bad = [doc[i:i+500] for i in range(0, len(doc), 500)]   # cuts mid-sentence, no overlap
#   -> a fact split across the boundary appears WHOLE in neither chunk -> retrieval misses it

# --- structure-aware chunking is even better when you have it -----------
# - Markdown/HTML: split by headings so each chunk is a coherent section (keep the heading
#   as context in the chunk).
# - Code: split by function/class, not arbitrary lines.
# - Tables/CSV: keep rows + header together; don't split a row from its column names.
# Match the boundary to the document's STRUCTURE, not just punctuation.

# --- attach metadata to each chunk (improves retrieval & citations) -----
chunk_records = [{"text": c, "source": doc_id, "section": heading, "pos": i}
                 for i, c in enumerate(chunks)]
# metadata lets you cite sources, filter by document, and reassemble order later.

# --- there is no universal best size — evaluate it ----------------------
# chunk_size/overlap are HYPERPARAMETERS: try a few (e.g. 256/512/1024 tokens, 0–20% overlap)
# and measure retrieval quality on real questions (8.5/8.14). Optimal depends on your docs.
```

### Impact

- **Better retrieval, better answers:** coherent, overlapping chunks mean the retriever
  finds complete, relevant context — often the highest-leverage fix for a mediocre RAG
  system.
- **No lost boundary facts:** overlap ensures information spanning a split still appears
  whole somewhere, eliminating the "retrieved half a sentence" failure.
- **Efficient context use:** right-sized chunks pack the most relevant information into the
  token budget (9.8) without diluting it with irrelevant text.

### Pros & cons / when NOT to

**Chunk thoughtfully when:** building any retrieval/RAG system over documents — chunking
quality directly bounds retrieval quality.

**Watch out / when NOT to:**
- **Never split by raw character count alone** — it cuts ideas mid-sentence. Split on
  semantic boundaries (paragraphs/sentences/structure) and add overlap.
- **Size in tokens, not characters** (9.8) — so chunks fit the embedding model and the
  downstream context budget, and to keep cost predictable.
- **Match boundaries to document structure** — headings for docs, functions for code,
  rows+header for tables; punctuation-only splitting ignores meaningful structure.
- **Chunk size/overlap are hyperparameters** — there's no universal best; evaluate
  retrieval quality on real queries (8.14) and tune. Too-small loses context; too-big
  dilutes relevance and wastes budget.
- **Carry metadata** (source, section, position) — needed for citations, filtering, and
  reconstructing order; chunks without provenance are hard to trust or debug.

### Where this shows up

- **Real work — RAG ingestion:** chunking is the first, quality-determining step of the
  embed→store→retrieve pipeline (feeds 9.12/9.14); poor chunking caps the whole system.
- **Real work — long-document QA/summarisation:** splitting documents that exceed the
  context window (9.8) into processable, coherent pieces.
- **Real work — code/knowledge-base search:** structure-aware chunking (by function,
  heading) for searching codebases and docs.
- **Pattern mapping (secondary):** it's text segmentation (Area 4) with overlap — a
  sliding-window-style split (Area 11) over a document, where window size and stride
  (overlap) are tuned for coherence.
[↑ Back to top](#contents)

---

<a id="9.10"></a>
## 9.10 — "I asked the LLM for JSON and json.loads crashed" → parsing LLM output safely

### The situation

You prompt an LLM to return JSON so your code can use its output programmatically, and
parsing it blows up:

```python
resp = llm("Extract name and age as JSON: " + text)
data = json.loads(resp)        # JSONDecodeError!
# the model returned:  Here's the JSON you requested:\n```json\n{"name": "Alice", "age": 30}\n```
# ...so resp isn't pure JSON — it has prose, a markdown fence, maybe a trailing comma
```

LLMs are *text* generators, not JSON APIs. Even when asked for JSON, they may wrap it in
explanatory prose, markdown code fences, add trailing commas, use single quotes, or
occasionally produce malformed/partial JSON. A bare `json.loads` on raw model output is
fragile and will crash in production on the first quirk.

### What's really going on

Model output is **untrusted, free-form text** that only *usually* matches the format you
asked for — so you must treat parsing it as a **boundary** (7.1) that can fail, not as a
reliable structured response. Robust handling has layers:

1. **Constrain the output** at the source — use the provider's **structured-output / JSON
   mode** or function/tool calling, which forces valid JSON, rather than hoping the prompt
   is obeyed.
2. **Extract then parse** — strip markdown fences and surrounding prose before `json.loads`.
3. **Validate the shape** — even valid JSON might miss fields or have wrong types; validate
   against a schema (pydantic, 3.6/7.1).
4. **Handle failure** — on a parse/validation error, retry (possibly asking the model to
   fix it) or fail gracefully (7.2) — don't let one bad response crash the job.

> LLM output is **free-form text**, not guaranteed JSON. Treat it as an untrusted boundary
> (7.1): prefer the provider's **structured-output mode** to force valid JSON; otherwise
> **extract** (strip fences/prose) → **parse** → **validate against a schema** (3.6) →
> **handle errors** (retry/fallback). Never `json.loads` raw model text and assume success.

### The move

Prefer the provider's structured-output mode; otherwise extract → parse → validate, with a
retry on failure:

```python
# best: force valid JSON at the source (OpenAI-style)
resp = client.chat.completions.create(model=..., messages=[...],
                                       response_format={"type": "json_object"})
data = json.loads(resp.choices[0].message.content)   # guaranteed parseable JSON
```

### Why it works

Structured-output / JSON mode constrains the model's decoding so the output is *always*
syntactically valid JSON — eliminating the fence/prose/trailing-comma quirks at the source,
which is far more reliable than cleaning up free text after the fact. When that mode isn't
available, treating the response as an untrusted boundary (7.1) — extract the JSON
substring, parse it, then validate the *shape* against a schema (3.6) — catches both
syntactic and semantic problems (missing fields, wrong types) before your code trusts the
data. Wrapping the whole thing in a retry (5.9) means a one-off malformed response is
recovered (often by asking the model to fix its own output) instead of crashing the job
(7.2). Each layer handles a different failure the previous one can't.

### The code, every line explained

```python
import json, re
from pydantic import BaseModel, ValidationError

# --- LAYER 1 (best): provider structured output / function calling ------
resp = client.chat.completions.create(
    model="gpt-4o", messages=[...],
    response_format={"type": "json_object"},   # model is FORCED to emit valid JSON
)
data = json.loads(resp.choices[0].message.content)   # parseable by construction
# (function/tool calling goes further: the args arrive as a validated object.)

# --- LAYER 2: extract JSON from messy free text (when mode unavailable) -
def extract_json(text):
    # strip a ```json ... ``` fence if present, else grab the outermost {...}
    fenced = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    brace = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)   # first {...} or [...]
    return brace.group(1) if brace else text

# --- LAYER 3: parse + VALIDATE the shape (3.6/7.1) ----------------------
class Person(BaseModel):
    name: str
    age: int                       # validates type; missing/wrong field -> ValidationError

def parse_llm(text):
    raw = extract_json(text)
    obj = json.loads(raw)          # may raise JSONDecodeError
    return Person(**obj)           # may raise ValidationError (wrong/missing fields)

# --- LAYER 4: handle failure — retry asking the model to fix it ---------
def robust_extract(prompt, attempts=3):
    for i in range(attempts):
        resp = llm(prompt)
        try:
            return parse_llm(resp)            # success -> validated object
        except (json.JSONDecodeError, ValidationError) as e:
            prompt = (prompt + f"\n\nYour previous reply was invalid JSON: {e}. "
                              f"Return ONLY valid JSON matching the schema.")   # self-correct
    raise ValueError("LLM failed to produce valid JSON after retries")          # fail loud (7.2)

# --- the anti-pattern ---------------------------------------------------
# data = json.loads(llm(prompt))   # crashes on the first fence/prose/trailing comma.
# Treat model output as UNTRUSTED text (7.1), not a reliable JSON API.
```

### Impact

- **Reliable structured data from a text model:** the layered approach turns flaky
  free-text output into validated objects your code can depend on — no crashes on the first
  quirk.
- **Catches semantic errors too:** schema validation (3.6) rejects JSON that parses but has
  missing/wrong fields, so downstream code isn't fed plausible-but-wrong data.
- **Self-healing:** retrying with the error fed back lets the model correct its own
  malformed output, recovering automatically from occasional failures.

### Pros & cons / when NOT to

**Parse defensively when:** you consume LLM output programmatically as structured data —
extraction, classification, tool/agent outputs, any "return JSON" prompt.

**Watch out / when NOT to:**
- **Use structured-output/JSON mode or function calling when available** — it's far more
  reliable than prompt-and-clean; don't hand-roll extraction if the API can guarantee valid
  JSON.
- **Always validate the shape, not just parse** (3.6/7.1) — valid JSON with a missing field
  or wrong type is a silent bug; a schema catches it.
- **Treat output as untrusted** (7.1) — beyond format, never `eval()` model output or run it
  unsanitised; for agents that emit code/commands, sandbox and review (security boundary).
- **Bound retries** (5.9) — self-correction loops can run forever and cost tokens (5.20);
  cap attempts and fail loud (7.2) if the model can't comply.
- **Lower temperature for structured tasks** — high randomness increases format deviations;
  a low/zero temperature makes valid-format output more consistent.

### Where this shows up

- **Real work — extraction & classification:** asking an LLM to pull fields/labels as JSON
  for downstream code — the most common "LLM as a structured function" pattern.
- **Real work — agents & tool use:** parsing/validating the tool calls and arguments an
  agent emits before executing them (with the security caveat above).
- **Real work — pipelines feeding databases:** validating LLM-produced records (3.6) before
  inserting, so malformed output is dead-lettered (7.9), not stored.
- **Pattern mapping (secondary):** it's boundary validation (7.1) + schema validation (3.6)
  + retries (5.9) applied to model output — treat the LLM as an unreliable external source,
  not a trusted API.
[↑ Back to top](#contents)

---

<a id="9.11"></a>
## 9.11 — "The JSON parsed fine but 'age' was -5 and the category was made up" → validating structured output

### The situation

You fixed parsing (9.10), so the LLM's JSON now loads cleanly. But the *content* is still
wrong in ways that pass `json.loads`:

```python
data = json.loads(resp)        # parses fine
# {"age": -5, "category": "Sportz", "email": "not-an-email", "priority": "URGENT!!!"}
# age is negative; "category" isn't one of your allowed values; email is malformed;
# priority should be one of {low, medium, high} but the model invented "URGENT!!!"
```

Syntactically valid JSON is not *semantically* valid data. The model can hallucinate
category values, return out-of-range numbers, miss required fields, or use the wrong type —
and if your code trusts it, that garbage flows downstream exactly like the leakage of bad
data in 7.1.

### What's really going on

Parsing (9.10) only guarantees the output is *well-formed JSON*; it says nothing about
whether the *values* obey your rules. LLMs frequently produce plausible-but-invalid content:
values outside an allowed set (a hallucinated `category`), out-of-range numbers, wrong
types, or missing fields. You need to **validate the parsed object against a schema that
encodes your actual constraints** — allowed values (enums), ranges, formats, required
fields — and reject or repair anything that violates them.

This is schema validation (3.6) / boundary validation (7.1) applied to model output, with an
LLM-specific twist: when validation fails, you can often **ask the model to repair** its
output by feeding the validation error back (a self-correction loop, 9.10/5.9). The schema
does double duty: it can be sent to the model to *constrain* generation, and it *enforces*
correctness after.

> Parsing checks **syntax**; validation checks **meaning**. Define a schema (pydantic, 3.6)
> with enums, ranges, and required fields that encode your real constraints, validate the
> parsed output against it, and on failure **reject or repair** (feed the error back to the
> model). Valid JSON ≠ valid data — the model hallucinates *content*, not just format.

### The move

Define a constraint-rich schema (enums, ranges, formats) and validate the parsed output
against it; repair on failure:

```python
from enum import Enum
from pydantic import BaseModel, Field, EmailStr

class Priority(str, Enum): low="low"; medium="medium"; high="high"   # allowed values only

class Ticket(BaseModel):
    category: str = Field(pattern="^(Sports|Tech|Music)$")   # must match an allowed set
    age: int = Field(ge=0, le=120)                            # range-checked
    email: EmailStr                                           # format-checked
    priority: Priority                                        # enum: rejects "URGENT!!!"
```

### Why it works

The schema encodes your *real* constraints, so `Ticket(**parsed)` rejects the model's
invented `category`, the negative `age`, the malformed `email`, and the off-enum
`priority` — turning "plausible garbage" into a precise `ValidationError` that names exactly
what's wrong. That error is actionable two ways: you can **reject** the output (dead-letter
it, 7.9) or **repair** it by sending the error back to the model and asking it to fix only
the invalid fields (self-correction, 9.10/5.9). Sending the same schema *to* the model (many
APIs accept a JSON schema for structured output) also *constrains* generation up front, so
fewer repairs are needed — the schema both prevents and catches bad content. Downstream code
then receives a `Ticket` it can fully trust.

### The code, every line explained

```python
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, ValidationError

# --- schema that encodes REAL constraints, not just types ---------------
class Priority(str, Enum):
    low = "low"; medium = "medium"; high = "high"     # ONLY these are valid

class Ticket(BaseModel):
    category: str = Field(pattern="^(Sports|Tech|Music)$")  # allowed-set check (rejects "Sportz")
    age: int = Field(ge=0, le=120)                           # ge/le = range bounds
    email: EmailStr                                          # validates email FORMAT
    priority: Priority                                       # enum -> "URGENT!!!" is rejected

# --- validate the PARSED output (9.10 got us valid JSON) ----------------
def validate_ticket(parsed: dict) -> Ticket:
    return Ticket(**parsed)        # raises ValidationError listing EVERY violation

# --- repair loop: feed the error back to the model ----------------------
def extract_validated(prompt, attempts=3):
    for _ in range(attempts):
        parsed = parse_llm(llm(prompt))          # parse (9.10)
        try:
            return validate_ticket(parsed)        # validate CONTENT (this scenario)
        except ValidationError as e:
            prompt += (f"\n\nYour output failed validation:\n{e}\n"
                       f"Fix ONLY the invalid fields and return valid JSON.")   # self-correct
    raise ValueError("LLM could not produce valid data")   # reject -> dead-letter (7.9), fail loud (7.2)

# --- constrain generation up front: send the schema to the model --------
schema = Ticket.model_json_schema()    # pydantic -> JSON schema
# pass `schema` to the provider's structured-output API (or include in the prompt) so the
# model is GUIDED to produce conforming content -> fewer repair round-trips.

# --- syntax vs meaning, side by side ------------------------------------
# json.loads(resp)        -> checks SYNTAX only: {"priority": "URGENT!!!"} passes
# Ticket(**parsed)         -> checks MEANING: "URGENT!!!" not in enum -> ValidationError
# You need BOTH layers (9.10 + 9.11): parseable AND conforming.
```

### Impact

- **Trustworthy structured output:** downstream code receives data that obeys your real
  constraints (allowed values, ranges, formats), not plausible hallucinations — the content
  analogue of fixing parsing (9.10).
- **Precise, actionable failures:** a `ValidationError` pinpoints every bad field, enabling
  targeted repair or clean rejection (7.9) instead of silent corruption.
- **Fewer bad outputs at the source:** sending the schema to constrain generation reduces
  invalid content up front, cutting repair round-trips and token cost (5.20).

### Pros & cons / when NOT to

**Validate content when:** LLM output feeds code/databases/decisions — extraction,
classification, agent arguments, structured generation. (Always, alongside parsing, 9.10.)

**Watch out / when NOT to:**
- **Parsing ≠ validation** — `json.loads` succeeding tells you nothing about correctness.
  Always validate the *values* against a constraint-rich schema (enums, ranges, formats),
  not just types.
- **Encode real constraints, not just types** — `age: int` allows `-5`; use `ge/le`, enums,
  and patterns so the schema actually rejects nonsense.
- **Bound the repair loop** (5.9/9.10) — self-correction can loop and burn tokens (5.20);
  cap attempts and reject/dead-letter (7.9) on persistent failure (fail loud, 7.2).
- **Use the schema to constrain generation too** — sending it to the model up front prevents
  more than it catches; validation is the backstop, not the only line of defence.
- **Don't trust validated content blindly for actions** — a value can be schema-valid yet
  wrong/harmful (a valid-looking but incorrect category, or an agent command that's
  well-formed but dangerous); apply business rules and, for actions, a security boundary
  (7.1).

### Where this shows up

- **Real work — LLM extraction into databases:** validating extracted records against a
  schema (3.6) before insert, dead-lettering (7.9) the ones that fail — the content-quality
  gate of an LLM pipeline.
- **Real work — agents/tool calling:** validating that tool arguments obey allowed
  values/ranges before executing the tool (with a security check for actions).
- **Real work — structured generation products:** constraining + validating model output
  so a user-facing feature can't emit invalid categories/fields.
- **Pattern mapping (secondary):** it's schema/boundary validation (3.6/7.1) plus a
  retry-repair loop (5.9) — the semantic layer on top of parsing (9.10), enforcing meaning
  the way validation enforces data integrity throughout the guide.
[↑ Back to top](#contents)

---

<a id="9.12"></a>
## 9.12 — "Every run re-embeds the same 1M documents and re-bills me" → embedding cache

### The situation

Your RAG pipeline embeds documents (9.9→9.14). You run it repeatedly — to re-index, to
debug, after a code change — and each run re-embeds *everything*, costing time and money:

```python
for doc in documents:                  # 1,000,000 docs, most UNCHANGED since last run
    vec = embedding_api(doc.text)      # paid API call PER doc, EVERY run
    store(doc.id, vec)
# re-running (or re-processing unchanged docs) re-embeds all 1M -> hours + a repeated bill
```

Embeddings are **deterministic** — the same text and model always produce the same vector —
so re-embedding unchanged text is pure waste: you pay the API again for an answer you
already had.

### What's really going on

Embedding a piece of text is a **pure, expensive, deterministic** operation — exactly the
profile that benefits from **caching** (memoization, 1.13 / persistent caching, Area 2/7).
The same text → the same vector, so you should compute it **once**, store it keyed by the
text (or its hash, 4.4), and on any future request **look it up** instead of re-calling the
API. Because the cache must survive across runs and processes (not just in-memory, 1.13), it
needs to be **persistent** — a disk store, database, or the vector store itself.

Keying on a **content hash** (4.4) also gives you free incremental behaviour: unchanged docs
hit the cache; only *new or edited* docs (whose hash changed) get embedded. This is the
LLM-cost-control sibling of the manifest/skip-done pattern (7.5) and persistent caching
(2.14).

> Embeddings are **deterministic and paid**, so cache them: compute once, store keyed by a
> **content hash** (4.4) in a **persistent** cache (disk/DB/vector store), and look up on
> repeat. Re-embedding unchanged text is wasted money and time; a content-hash key also
> means only new/changed text is re-embedded (incremental, like the skip-done manifest, 7.5).

### The move

Key embeddings by a content hash in a persistent cache; embed only on a cache miss, and
batch the misses (5.14):

```python
import hashlib, json
def key(text, model): return hashlib.sha256(f"{model}:{text}".encode()).hexdigest()  # (4.4)

def get_embedding(text, model, cache):
    k = key(text, model)
    if k in cache:                 # persistent store (disk/DB) -> survives runs (2.14/7.5)
        return cache[k]            # HIT: free, instant
    vec = embedding_api(text, model)   # MISS: pay once
    cache[k] = vec
    return vec
```

### Why it works

The hash key (4.4) maps each unique `(model, text)` to its vector, so a repeat run finds the
key already present and returns the stored vector with **zero** API calls — the deterministic
nature of embeddings makes the cached value always correct. Including the **model name** in
the key means switching embedding models doesn't return stale vectors from the old one.
Because the cache is **persistent** (disk/DB, not in-memory, 1.13/2.14), the savings carry
across runs, restarts, and processes — exactly when re-embedding hurts. And since the key is
a *content* hash, an *edited* document produces a new key and is correctly re-embedded, while
the millions of unchanged docs are skipped (incremental, 7.5) — you only ever pay for new or
changed text.

### The code, every line explained

```python
import hashlib

def emb_key(text, model):
    # include MODEL in the key: different models give different vectors for the same text
    return hashlib.sha256(f"{model}::{text}".encode("utf-8")).hexdigest()   # (4.4)

# --- persistent cache: survives across runs/processes -------------------
import shelve   # simple disk-backed dict; or use sqlite/Redis/the vector store itself
def embed_cached(texts, model, cache_path="emb_cache.db"):
    with shelve.open(cache_path) as cache:        # persistent key->vector store
        results, to_compute = {}, []
        for t in texts:
            k = emb_key(t, model)
            if k in cache:
                results[t] = cache[k]              # HIT: reuse stored vector (free)
            else:
                to_compute.append(t)               # MISS: collect for a BATCH call
        # batch the misses in ONE API call (5.14) instead of one-per-text:
        if to_compute:
            vecs = embedding_api_batch(to_compute, model)   # pay once for all misses
            for t, v in zip(to_compute, vecs):
                cache[emb_key(t, model)] = v        # store for next time
                results[t] = v
        return [results[t] for t in texts]          # preserve input order
# First run: embeds all (misses). Re-run / unchanged docs: all hits -> ~0 cost.

# --- incremental: only new/CHANGED text is re-embedded ------------------
# Because the key is a content hash, editing a doc changes its key -> it's a miss ->
# re-embedded; the millions of unchanged docs stay hits. (Same idea as skip-done, 7.5.)

# --- functools.lru_cache is NOT enough here -----------------------------
# @lru_cache (1.13) is IN-MEMORY and per-process -> lost on restart, not shared across
# workers. For embeddings you need a PERSISTENT cache (disk/DB) to actually save money.

# --- cache invalidation note --------------------------------------------
# Keyed by content+model, the cache is naturally correct: it only returns a vector for the
# exact text+model that produced it. If you UPGRADE the model, the new model name -> new
# keys -> re-embed (old vectors simply go unused; prune them if storage matters).
```

### Impact

- **Direct cost savings:** unchanged text is never re-embedded, so re-runs and incremental
  updates cost a fraction of a full re-embed — often the biggest line-item saving in a RAG
  pipeline (ties to usage accounting, 5.20).
- **Faster iteration:** debugging and re-indexing don't pay the full embedding time each
  cycle — cache hits are instant.
- **Incremental by construction:** content-hash keys mean only new/edited documents are
  embedded on each run, the same efficiency as a skip-done manifest (7.5).

### Pros & cons / when NOT to

**Cache embeddings when:** you embed text that repeats across runs or where most documents
are unchanged between updates — i.e. essentially every production RAG/embedding pipeline.

**Watch out / when NOT to:**
- **Use a *persistent* cache, not `lru_cache`** — in-memory caching (1.13) is lost on
  restart and not shared across workers, so it doesn't save the cross-run cost that matters.
- **Include the model (and key params) in the key** — a vector is only valid for the model
  that produced it; omit the model and a model switch returns stale vectors.
- **Key on content, not just an id** — keying on `doc.id` alone means an *edited* doc keeps
  its stale embedding; a content hash (4.4) re-embeds changed text automatically.
- **Batch the cache misses** (5.14) — don't make one API call per miss; collect misses and
  embed them in one batched call for both speed and cost.
- **Mind cache storage growth** — millions of vectors take real space; prune unused keys
  (e.g. after a model upgrade) or store vectors in the vector DB you're already using.
- **Caching only helps repeats** — a one-shot embed of all-new text gets no benefit (every
  call is a miss); the win is on re-runs and incremental updates.

### Where this shows up

- **Real work — RAG ingestion & re-indexing:** caching embeddings so re-running the pipeline
  (or adding a few new docs) doesn't re-embed and re-bill the whole corpus (9.9→9.14).
- **Real work — LLM/embedding cost control:** a core tactic alongside batching (5.14) and
  usage accounting (5.20) to keep API spend down.
- **Real work — incremental data sync:** content-hash keying to embed only changed records,
  the same pattern as skip-done manifests (7.5) for embeddings.
- **Pattern mapping (secondary):** it's memoization (1.13) made persistent (2.14) and keyed
  by content hash (4.4) — the same "compute once, reuse" principle as caching and skip-done
  (7.5), applied to a paid deterministic operation.
[↑ Back to top](#contents)

---

<a id="9.13"></a>
## 9.13 — "The user stares at a blank screen for 20 seconds while the LLM thinks" → streaming responses

### The situation

Your chatbot calls an LLM and waits for the full answer before showing anything:

```python
response = llm(prompt)          # blocks ~20s while the model generates the ENTIRE answer
display(response)                # only NOW does the user see anything
```

A long answer takes the model ~20 seconds to generate fully. With this code the user sees a
blank screen the whole time, then the complete answer appears at once. It *feels* broken or
slow — even though the model started producing words within a fraction of a second.

### What's really going on

LLMs generate text **one token at a time** (autoregressively) — they produce the first word
almost immediately and the rest progressively. Waiting for the *complete* response throws
away that property: you hold back tokens the model has already produced. **Streaming** sends
each token to the user **as it's generated**, so the answer appears progressively (like a
person typing), and **time-to-first-token** drops from ~20s to ~100ms.

This is the LLM application of streamed responses (5.19): instead of buffering the whole
body, you consume it incrementally as it arrives. The model output is a *stream of tokens*;
you iterate it and render/forward each chunk immediately.

> LLMs emit tokens **incrementally**; **streaming** delivers each to the user as it's
> produced rather than waiting for the full completion. It transforms *perceived* latency —
> first words in ~100ms vs a ~20s blank wait — without changing total generation time. It's
> the token-level case of streamed HTTP responses (5.19); enable `stream=True` and iterate
> the chunks.

### The move

Request a streamed response and render each token chunk as it arrives:

```python
stream = client.chat.completions.create(model=..., messages=[...], stream=True)  # stream=True
for chunk in stream:                       # yields tokens as the model produces them
    piece = chunk.choices[0].delta.content or ""
    print(piece, end="", flush=True)        # show IMMEDIATELY (flush! — see 5.19/7.13)
```

### Why it works

`stream=True` makes the API send each token (or small group) the instant the model produces
it, instead of buffering the whole completion server-side. Your loop receives those deltas
as a stream (5.19) and renders each immediately, so the user sees the answer build up
word-by-word starting in ~100ms — total generation time is unchanged, but *perceived*
latency collapses because feedback is immediate. The `flush=True` (or equivalent flush in a
web framework) is essential: without it, output sits in a buffer and you lose the streaming
effect (the same buffering caveat as 5.19/7.13). In a web app, you forward each chunk to the
client over Server-Sent Events (5.19) or a websocket so the browser renders progressively.

### The code, every line explained

```python
# --- streaming an LLM completion (OpenAI-style) -------------------------
stream = client.chat.completions.create(
    model="gpt-4o", messages=[{"role": "user", "content": prompt}],
    stream=True,                           # <- request incremental tokens, not one blob
)
full = []
for chunk in stream:                       # iterate as tokens arrive
    delta = chunk.choices[0].delta.content or ""   # this chunk's new text ("" on non-text chunks)
    print(delta, end="", flush=True)        # render NOW; flush so it isn't buffered (5.19)
    full.append(delta)                      # also accumulate, if you need the final string
answer = "".join(full)                      # the complete response, reassembled

# --- in a web service: forward chunks via SSE (5.19) --------------------
from fastapi.responses import StreamingResponse
def token_stream():
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield f"data: {delta}\n\n"      # SSE frame per token -> browser renders live
@app.post("/chat")
def chat():
    return StreamingResponse(token_stream(), media_type="text/event-stream")

# --- the trade-off: streaming complicates parsing/validation (9.10/9.11) -
# If you need STRUCTURED output (JSON), streaming gives PARTIAL JSON mid-stream that
# isn't valid until complete -> you usually buffer the full text first, THEN parse/validate.
# Stream for human-readable chat; buffer-then-parse for machine-consumed structured output.

# --- the anti-pattern ---------------------------------------------------
# response = llm(prompt); display(response)   # 20s blank wait, then everything at once.
# For interactive UX, that's the wrong default — stream it.
```

### Impact

- **Dramatically better perceived latency:** first words in ~100ms instead of a ~20s blank
  wait — the difference between an app that feels responsive and one that feels broken.
- **Natural UX:** progressive, typewriter-style output matches how users expect a chat
  assistant to behave, and lets them start reading before generation finishes.
- **Early cancellation:** because output streams, a user can stop a wrong/overlong answer
  mid-generation, saving tokens (5.20) and time.

### Pros & cons / when NOT to

**Stream when:** output is shown to a human in real time — chat UIs, assistants, live
generation. Interactive UX is the main case.

**Watch out / when NOT to:**
- **Don't stream when you need structured output** (9.10/9.11) — partial JSON mid-stream
  isn't parseable/validatable; for machine-consumed JSON, buffer the full response then
  parse. Stream human text, buffer structured data.
- **Flush, or there's no streaming** — buffered output (no `flush=True`, or a framework
  that buffers) defeats the point (same caveat as 5.19/7.13).
- **Total time is unchanged** — streaming improves *perceived* latency, not throughput;
  it's a UX win, not a speed-up of generation.
- **Error handling mid-stream is trickier** — a failure can occur after partial output is
  shown; handle stream interruptions and timeouts (5.8) so a dropped stream degrades
  gracefully (7.2).
- **Holds a connection open** for the whole generation (5.19) — at high concurrency that
  ties up connections; size accordingly.

### Where this shows up

- **Real work — every chat/assistant UI:** streaming is the standard for LLM chat
  interfaces; it's why assistants render text progressively.
- **Real work — long-form generation:** showing a long answer/summary as it's written so
  the user isn't left waiting on a blank screen.
- **Real work — agent step traces:** streaming intermediate reasoning/steps to the user for
  transparency during a long agent run.
- **Pattern mapping (secondary):** it's streamed responses (5.19) at the token level —
  consume-as-produced rather than buffer-then-show — the same lazy/incremental principle as
  generators (1.2).
[↑ Back to top](#contents)

---

<a id="9.14"></a>
## 9.14 — "How does the system find the 'relevant' chunks for a question?" → vector similarity

### The situation

You've chunked (9.9) and embedded (9.12) your documents. Now a user asks a question, and you
need to find the chunks most relevant to it — but the question rarely shares exact keywords
with the answer:

```python
question = "How do I get my money back?"
# the relevant chunk says: "Refunds are processed within 30 days of return."
# keyword search for "money back" finds NOTHING — the words don't overlap,
# even though the chunk is exactly what the user needs
```

Literal keyword matching fails because natural language expresses the same meaning with
different words ("money back" vs "refunds"). You need to retrieve by **meaning**, not
spelling.

### What's really going on

An **embedding** turns text into a **vector** — a list of numbers — positioned in a
high-dimensional space such that *semantically similar* texts land *close together*, even
with no shared words. "How do I get my money back?" and "Refunds are processed..." map to
nearby vectors because they mean similar things. So "find relevant chunks" becomes "find the
vectors **nearest** to the question's vector" — a **nearest-neighbour search** in embedding
space.

Closeness is measured by a **similarity metric**, almost always **cosine similarity**: the
cosine of the angle between two vectors (1.0 = same direction/meaning, 0 = unrelated). You
embed the question with the *same model* as the documents (or retrieval breaks), score it
against the stored chunk vectors, and return the top-k most similar — which then go into the
LLM's context (9.8). At scale you don't compare against every vector by brute force; a
**vector database** uses an **ANN** (approximate nearest neighbour) index for fast search.

> **Embeddings** place text as **vectors** where semantic similarity = geometric closeness.
> Retrieval = **nearest-neighbour search**: embed the query (same model, 9.12), score
> against stored vectors by **cosine similarity**, return the **top-k**. This is *semantic*
> search — it matches meaning, not keywords. A **vector DB** (FAISS, Pinecone, pgvector)
> does this fast at scale via approximate NN; the top-k chunks feed the LLM context (9.8).

### The move

Embed the query with the same model, score by cosine similarity against stored vectors, take
the top-k (a vector DB does this at scale):

```python
import numpy as np
def cosine(a, b):
    return a @ b / (np.linalg.norm(a) * np.linalg.norm(b))   # 1.0 = identical meaning

q = embed(question, model)                       # SAME model as the chunks (9.12)
scored = [(cosine(q, c.vector), c) for c in chunks]
top_k = [c for _, c in sorted(scored, reverse=True)[:5]]      # 5 most similar chunks
```

### Why it works

Because the embedding model places similar *meanings* near each other, the question's vector
sits close to the answer chunk's vector even with zero shared words — so ranking chunks by
cosine similarity surfaces the *semantically* relevant ones that keyword search misses.
Cosine measures direction (meaning) rather than magnitude, which is why it's the standard
metric for text embeddings. Sorting by score and taking the top-k (the heap/top-N pattern,
3.17/Area 11) gives the handful of most-relevant chunks to drop into the LLM's context (9.8).
The brute-force scan shown is fine for thousands of vectors; for millions, a **vector
database** builds an ANN index so search is sub-linear instead of comparing against every
vector — the same "don't scan everything" instinct as choosing O(1)/indexed lookups (2.9).

### The code, every line explained

```python
import numpy as np

# --- cosine similarity: the standard text-embedding metric --------------
def cosine(a, b):
    return a @ b / (np.linalg.norm(a) * np.linalg.norm(b))
#          │        └ product of the vectors' lengths (normalises out magnitude)
#          └ dot product; with normalisation -> cosine of the angle between them
# 1.0 = same direction (same meaning); ~0 = unrelated; works despite different words.

# --- retrieval: embed query (SAME model), score, take top-k -------------
q = embed(question, model)                        # MUST match the docs' embedding model (9.12)
scored = [(cosine(q, c.vector), c) for c in chunks]
top_k = [c for _, c in sorted(scored, reverse=True)[:5]]   # top-5 by similarity (3.17)
context = "\n".join(c.text for c in top_k)         # assemble into the LLM context (9.8 budget!)

# --- tip: normalise vectors once, then cosine == dot product ------------
# If all vectors are unit-length (norm 1), cosine(a,b) == a @ b -> faster scoring.
# Many embedding APIs already return normalised vectors.

# --- at scale: a vector DB does ANN search (don't brute-force millions) -
# brute force = O(n) per query (compare to EVERY vector). For millions of chunks use a
# vector database (FAISS / pgvector / Pinecone / Chroma): it builds an APPROXIMATE
# nearest-neighbour (ANN) index -> sub-linear search, slight accuracy trade-off.
# import faiss; index = faiss.IndexFlatIP(dim); index.add(vectors)
# D, I = index.search(q.reshape(1, -1), k=5)   # returns indices of the top-5 nearest

# --- hybrid & re-ranking (quality boosts) -------------------------------
# - HYBRID search: combine semantic (vector) with keyword (BM25) — catches exact terms
#   (names, codes, IDs) that pure embeddings can miss.
# - RE-RANK: retrieve top-50 by vector similarity, then re-score with a cross-encoder for
#   precision before taking the final top-5. Cheap recall first, expensive precision second.

# --- the failure this fixes ---------------------------------------------
# keyword search("money back") -> misses "refunds are processed..." (no shared words).
# vector search -> finds it, because the MEANINGS are close. That's the whole point.
```

### Impact

- **Meaning-based retrieval:** finds relevant chunks despite different wording — the core
  capability that makes RAG work where keyword search fails.
- **The retrieval half of RAG:** top-k semantic search is what selects the context the LLM
  reasons over (9.8); retrieval quality bounds answer quality (alongside chunking, 9.9).
- **Scales with a vector DB:** ANN indexing keeps search fast over millions of chunks, so
  retrieval stays sub-second at production scale.

### Pros & cons / when NOT to

**Use vector similarity when:** retrieving by meaning over text — RAG, semantic search,
deduplication-by-meaning, recommendation over embeddings.

**Watch out / when NOT to:**
- **Query and documents must use the same embedding model** — mixing models puts them in
  incompatible spaces and retrieval returns garbage. (Same caveat as the cache key, 9.12.)
- **Semantic search misses exact tokens** — IDs, codes, rare names, exact phrases. Use
  **hybrid** search (vector + keyword/BM25) when exact matches matter.
- **Brute force is O(n) per query** — fine for thousands, far too slow for millions. Use a
  vector DB with ANN indexing at scale (2.9's "don't scan everything").
- **Top-k similarity ≠ correctness** — retrieved chunks are *similar*, not guaranteed
  *relevant* or *sufficient*; consider re-ranking, and evaluate retrieval quality on real
  questions (8.5/8.14).
- **Embeddings encode the training distribution** — domain-specific jargon may embed poorly
  with a general model; a domain-tuned embedding model can help.
- **Mind the context budget** (9.8) — retrieving more chunks isn't always better; too many
  dilute relevance and blow the token budget.

### Where this shows up

- **Real work — RAG retrieval:** embed query → ANN search a vector DB → top-k chunks → LLM
  context (9.8); the heart of every retrieval-augmented system (chunking 9.9 + embedding
  cache 9.12 feed it).
- **Real work — semantic search products:** "find similar documents/tickets/products" by
  meaning rather than keywords.
- **Real work — dedup & clustering by meaning:** grouping near-duplicate or related content
  via embedding similarity (cousin of near-dup detection, 4.5).
- **Pattern mapping (secondary):** it's top-N selection (3.17/heap, Area 11) over a
  similarity score, and the "use an index instead of scanning" principle (2.9) realised as
  ANN — nearest-neighbour search is itself a classic algorithmic problem.
[↑ Back to top](#contents)

---

<a id="9.15"></a>
## 9.15 — "Our LLM bill is huge and p99 latency is awful, but which calls?" → tracking LLM cost & latency

### The situation

Your LLM-powered feature works, but two operational problems surface and you can't pinpoint
either:

```python
answer = llm(prompt)           # works — but how many tokens? how much did it cost? how slow?
# month-end: a large bill with no breakdown by feature/user.
# user complaints: "it's slow sometimes" — but which calls? how slow? why?
```

You're flying blind: no per-call record of tokens, cost, or latency, so you can't tell which
feature or prompt drives spend, which calls are slow, or whether a change made things better
or worse.

### What's really going on

LLM calls have two operational dimensions you must **measure to manage**: **cost** (driven
by tokens, 9.8) and **latency** (often seconds, and highly variable). This is the
LLM-specific application of usage accounting (5.20) and metrics/observability (7.x): wrap
every call to record, per request, the **token counts** (input/output), the **computed
cost**, the **latency**, and **context tags** (which feature, model, user) — then aggregate.

With that data you can answer the questions you currently can't: which feature dominates the
bill, which prompts are slow, what your p50/p95/p99 latency is, and whether an optimisation
(a smaller model, a shorter prompt, caching 9.12) actually helped. Without it, cost and
latency are anecdotes.

> Track every LLM call's **tokens** (input/output, 9.8), **cost** (tokens × price), and
> **latency**, tagged with **feature/model/user**, then aggregate. It's usage accounting
> (5.20) + latency metrics (7.x) for LLMs — the instrumentation that turns "the bill is big
> and it's slow sometimes" into "feature X spends 60%, and these prompts have p99 = 9s."
> Report latency as **percentiles** (p50/p95/p99), not just the average — tail latency is
> what users feel.

### The move

Wrap every LLM call to record tokens, cost, latency, and tags through one choke point:

```python
import time
def tracked_llm(prompt, *, feature, model="gpt-4o"):
    t0 = time.monotonic()
    resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}])
    latency = time.monotonic() - t0
    u = resp.usage                                  # the API returns token counts (5.20)
    record(feature=feature, model=model, in_tok=u.prompt_tokens,
           out_tok=u.completion_tokens, cost=cost(u, model), latency=latency)
    return resp.choices[0].message.content
```

### Why it works

Routing every call through one wrapper means *no* call escapes measurement — the same
single-choke-point discipline that makes usage accounting reliable (5.20). Each call records
the API-reported token counts (so cost is exact, not estimated), the wall-clock latency
(`time.monotonic`, the right clock for durations), and tags (feature/model/user) that let
you slice the aggregates. Once that per-call data lands in logs/a metrics store, aggregation
answers the operational questions: group by feature → which dominates spend; percentiles of
latency → what users actually experience (the average hides the slow tail); compare before/
after a change → did it help. Measurement is the precondition for optimisation — you can't
improve cost or latency you don't track.

### The code, every line explained

```python
import time

PRICE = {"gpt-4o": (2.50/1e6, 10.0/1e6)}   # (input $/token, output $/token) — keep in config (5.20)

def cost(usage, model):
    pin, pout = PRICE[model]
    return usage.prompt_tokens * pin + usage.completion_tokens * pout

# --- one wrapper ALL calls go through -----------------------------------
def tracked_llm(prompt, *, feature, model="gpt-4o"):
    t0 = time.monotonic()                          # monotonic clock for durations (not wall time)
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
    )
    latency = time.monotonic() - t0
    u = resp.usage                                  # exact token counts from the API
    log.info("llm call", extra={                    # structured log (7.13) -> aggregatable
        "feature": feature, "model": model,
        "in_tok": u.prompt_tokens, "out_tok": u.completion_tokens,
        "cost_usd": cost(u, model), "latency_s": round(latency, 3),
    })
    # also push to a metrics system (Prometheus/Datadog) for live dashboards + alerts:
    # metrics.observe("llm_latency_s", latency, tags={"feature": feature, "model": model})
    # metrics.increment("llm_cost_usd", cost(u, model), tags={"feature": feature})
    return resp.choices[0].message.content

# --- aggregate to answer the real questions -----------------------------
# from the logged records (load into pandas, or query the metrics store):
# - cost by feature:   df.groupby("feature").cost_usd.sum()   -> what dominates the bill
# - latency tail:      df.latency_s.quantile([0.5, 0.95, 0.99])  -> p50/p95/p99 (NOT mean)
# - slow prompts:      df.sort_values("latency_s").tail(20)    -> investigate the worst
# - did caching help?  compare cost/latency before vs after (9.12) — measured, not guessed

# --- why percentiles, not the average -----------------------------------
# mean latency 1.2s can hide a p99 of 9s — 1% of users wait 9 seconds. The average is
# dominated by the common case; PERCENTILES reveal the tail users actually complain about.

# --- streaming changes the latency metric (9.13) -----------------------
# for streamed responses, TIME-TO-FIRST-TOKEN matters more than total time — track both.
```

### Impact

- **Cost attribution & control:** per-feature/user cost breakdowns show where the bill goes,
  so you optimise the expensive 20% (smaller model, shorter prompts, caching 9.12) instead of
  guessing (extends 5.20).
- **Latency visibility:** p50/p95/p99 per feature reveals the slow tail users actually feel,
  pinpointing which calls/prompts to fix.
- **Measured optimisation:** before/after data proves whether a change helped, turning
  "it feels faster/cheaper" into evidence (the metric-driven rigor of 8.14/2.1).

### Pros & cons / when NOT to

**Track cost & latency when:** running LLM features in production or at any meaningful
volume — i.e. essentially any real LLM application.

**Watch out / when NOT to:**
- **Track at a single choke point** — calls that bypass the wrapper are invisible; route all
  LLM traffic (including retries, 5.9, and agent sub-calls) through it, or you undercount
  exactly where overspend hides (5.20).
- **Report latency as percentiles, not the mean** — the average hides the tail; p95/p99 is
  what users experience and what SLAs are written against.
- **Use a monotonic clock for latency** (`time.monotonic`), not wall-clock time, which can
  jump; and for streaming (9.13) track time-to-first-token separately from total time.
- **Keep prices in config and update them** (5.20) — hard-coded prices drift from the real
  bill; recompute cost from current rates.
- **Don't log prompt/response content blindly** — it may contain PII/secrets (7.13/7.14);
  log token *counts* and tags, redact or omit raw text unless you've handled privacy.
- **Tracking is necessary, not sufficient** — it tells you *where* the problem is; fixing it
  uses the other tools (caching 9.12, smaller models, prompt/token reduction 9.8, batching
  5.14).

### Where this shows up

- **Real work — LLM product operations:** cost dashboards by feature/customer and latency
  SLOs are standard for any deployed LLM feature (the LLM face of 5.20 + 7.x metrics).
- **Real work — cost optimisation:** the data identifies the expensive prompts/features to
  target with caching (9.12), a cheaper model, or shorter prompts (9.8).
- **Real work — performance debugging:** p99 latency and per-prompt timing locate the slow
  calls behind "it's slow sometimes."
- **Pattern mapping (secondary):** no DSA analogue; it's observability — usage accounting
  (5.20) + latency metrics/percentiles (7.x) applied to LLM calls — the measure-before-you-
  optimise principle (2.1) for cost and speed.

[↑ Back to top](#contents)

