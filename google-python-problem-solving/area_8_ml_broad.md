# Area 8 — ML Scenarios (Broad)

These are the failure modes and judgement calls that show up across *classical* machine
learning — not deep learning or LLMs specifically (those are Area 9), but the everyday
tabular/feature work an ML engineer does constantly. The recurring theme: the code runs
fine and produces a number, but the *number is wrong or misleading* — and the skill is
recognising the silent traps (leakage, bad metrics, non-determinism) before they reach
production.

---

<a id="contents"></a>
## Contents

- [8.1 — "My model scored 0.98 in testing and 0.61 in production" → data leakage](#8.1)
- [8.2 — "My model thinks 'red' is bigger than 'blue'" → categorical encoding](#8.2)
- [8.3 — "One feature in rupees swamps another in years" → feature scaling](#8.3)
- [8.4 — "99% accuracy but it never catches a single fraud" → imbalanced data](#8.4)
- [8.5 — "We optimised the metric and the product got worse" → choosing the right metric](#8.5)
- [8.6 — "My model scored 0.88, but a re-split gave 0.79" → cross-validation](#8.6)
- [8.7 — "I trained the same model twice and got different results" → seeds & determinism](#8.7)
- [8.8 — "I can't recreate the model that's running in production" → reproducible pipelines](#8.8)
- [8.9 — "The saved model loads but predicts garbage in production" → serialization & versioning](#8.9)
- [8.10 — "Scoring 10 million rows one at a time takes all night" → batch inference](#8.10)
- [8.11 — "My loss became NaN and the whole model is ruined" → numerical stability](#8.11)
- [8.12 — "I imputed missing values before splitting and the test set cheated" → fit transforms on train only](#8.12)
- [8.13 — "Loading the whole training set into memory OOMs" → data loaders & batching](#8.13)
- [8.14 — "Model B scored 0.2% higher, so we shipped it — was that real?" → comparing models fairly](#8.14)
- [8.15 — "Which hyperparameters gave last Tuesday's best result?" → experiment tracking](#8.15)
- [8.16 — "Great offline scores, bad live predictions" → train/serve skew](#8.16)

---


<a id="8.1"></a>
## 8.1 — "My model scored 0.98 in testing and 0.61 in production" → data leakage

### The situation

You build a churn model. Cross-validation says 98% accuracy — fantastic. You ship it,
and on real new customers it scores 61% — barely better than guessing. The model that
looked brilliant in testing is nearly useless live:

```python
# scaling the WHOLE dataset before splitting:
X_scaled = StandardScaler().fit_transform(X)   # fit uses ALL rows, incl. the test rows
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y)
model.fit(X_train, y_train)
print(model.score(X_test, y_test))             # 0.98 — but the test set was "contaminated"
```

The test score is a lie: it doesn't reflect performance on truly unseen data, so you had
no real warning before production exposed the truth.

### What's really going on

This is **data leakage**: information from outside the training data (specifically, from
the test set or the future) sneaks into the model during training, so the test score is
inflated and doesn't predict real-world performance. The model effectively "saw the
answers" during its exam.

In the example, `StandardScaler().fit_transform(X)` computes the mean and standard
deviation over the **entire** dataset — *including the test rows* — then scales
everything with those statistics. So the training data was transformed using knowledge of
the test set's distribution. The test set is no longer truly "unseen", and its score is
optimistic.

> **Data leakage** = the training process gains access to information it won't have at
> prediction time (test-set statistics, future values, target-derived features). The
> result is a test score that's too good and collapses in production. The fix is to keep
> a strict wall: *anything learned from data — scaling stats, encodings, feature
> selection, imputation values — must be computed on the **training set only**, then
> applied to the test set.*

Leakage is insidious because nothing errors and the metrics look *great* — the better
the score, the more you should suspect it. It's the single most common reason "it worked
in the notebook" fails in production.

### The move

**Split first, then fit every data-derived transform on the training set only** — and
wrap the whole sequence in a `Pipeline` so it's enforced automatically:

```python
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

X_train, X_test, y_train, y_test = train_test_split(X, y)   # split BEFORE any fitting
pipe = make_pipeline(StandardScaler(), model)               # scaler fits on train only
pipe.fit(X_train, y_train)                                   # .fit learns scaling from train
print(pipe.score(X_test, y_test))                            # honest estimate on unseen data
```

### Why it works

Splitting *before* any transform means the test rows never influence anything the model
learns. A `Pipeline` enforces this correctly by construction: when you call `pipe.fit(
X_train, ...)`, the scaler's `.fit` sees **only** the training rows and stores *their*
mean/std; when you later call `pipe.score(X_test, ...)`, the scaler **transforms** the
test rows using those stored training statistics — it never re-fits on test data. So the
test set stays genuinely unseen, and its score is an honest estimate of production
performance. The pipeline also guarantees the *same* transform is applied at serving
time, eliminating a whole class of train/serve mismatch (8.16).

### The code, every line explained

```python
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

# --- WRONG: fit transforms on all data -> leakage -----------------------
X_scaled = StandardScaler().fit_transform(X)   # mean/std computed over TEST rows too
Xtr, Xte, ytr, yte = train_test_split(X_scaled, y)
# test score is inflated; production will be worse.

# --- RIGHT: split first, transforms inside a pipeline -------------------
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
#                                                          └ fixed split for reproducibility (8.7)
pipe = make_pipeline(
    StandardScaler(),        # .fit() will learn mean/std from TRAIN only
    model,                   # e.g. LogisticRegression()
)
pipe.fit(Xtr, ytr)           # scaler fits on train; model trains on scaled train
print(pipe.score(Xte, yte))  # scaler TRANSFORMS test with train stats -> honest score

# --- and with cross-validation: the pipeline keeps each fold honest -----
scores = cross_val_score(pipe, X, y, cv=5)   # for EACH fold, the scaler re-fits on that
                                             # fold's TRAIN portion only -> no fold leakage
# Without the pipeline, scaling X once before cross_val_score leaks across folds.

# --- other common leakage sources (same rule: train-only) --------------
# - imputation: fill missing values with the TRAIN mean/median, not the full-data one
# - encoding:   fit target/category encoders on train only (3.x, 8.2)
# - feature selection: select features using train only, not the whole set
# - TIME leakage: using future info to predict the past — split by TIME for time series,
#   never random-split temporal data (a future row must never train a past prediction)
# - target leakage: a feature that's a proxy for the label (e.g. "account_closed_date"
#   predicting churn) — drop features unavailable at real prediction time
```

### Impact

- **Honest evaluation:** the test/CV score actually predicts production performance, so
  you catch a weak model *before* shipping instead of after.
- **No nasty surprises:** removes the "0.98 in the notebook, 0.61 live" collapse — the
  most common and damaging ML-to-production failure.
- **Correct serving behaviour:** the pipeline applies identical transforms at train and
  serve time, preventing train/serve skew (8.16).

### Pros & cons / when NOT to

**Guard against leakage always** — it's not optional; an unguarded evaluation is worse
than no evaluation because it gives false confidence.

**Watch out / when NOT to:**
- **Suspect a *too-good* score.** Near-perfect accuracy on a hard problem almost always
  means leakage (or a target-proxy feature), not a great model. Investigate before
  celebrating.
- **Use `Pipeline` for every data-derived step** (scaling, imputation, encoding, feature
  selection) so fitting-on-train is enforced, not remembered by hand. Manual transforms
  before the split are the classic leak.
- **Time-series needs time-based splits**, not random ones — a random split lets future
  rows train a model evaluated on the past. Use `TimeSeriesSplit` / split by date.
- **Watch target-proxy features** — a column that encodes the answer (computed *after*
  the event you're predicting) gives perfect scores and zero real value. Only use
  features available at true prediction time.
- **Even "harmless" global stats leak** — dataset-wide normalisation, dedup, or
  outlier-removal done before splitting all contaminate the test set.

### Where this shows up

- **Real work — every supervised model:** the first thing to audit when a model's offline
  metrics look implausibly good or don't survive production.
- **Real work — feature engineering pipelines:** scaling/encoding/imputation must be
  fit-on-train; the `Pipeline` + `cross_val_score` pattern is the standard safeguard.
- **Real work — time-series/forecasting:** temporal leakage (training on the future) is
  rampant and requires time-aware splits and feature lagging.
- **Pattern mapping (secondary):** no DSA analogue; it's the foundational evaluation-
  integrity principle, and it underpins trustworthy cross-validation (8.6), metric choice
  (8.5), and train/serve consistency (8.12/8.16).
[↑ Back to top](#contents)

---

<a id="8.2"></a>
## 8.2 — "My model thinks 'red' is bigger than 'blue'" → categorical encoding

### The situation

Your dataset has a `colour` column with values `"red"`, `"green"`, `"blue"`, and a
`city` column with 500 distinct values. You map them to numbers so the model can use
them:

```python
df["colour"] = df["colour"].map({"red": 0, "green": 1, "blue": 2})   # label encoding
model.fit(df[["colour", "city_code", ...]], y)
```

The model trains fine — but it now treats `blue (2)` as **twice** `green (1)` and
**greater than** `red (0)`, as if colours had a numeric order. They don't. The model
learns a meaningless ordering, and predictions suffer in subtle, hard-to-spot ways.

### What's really going on

Models work on numbers, but **categorical** values (colours, cities, product types) have
**no inherent numeric meaning or order**. Naively mapping them to `0, 1, 2…` (**label
encoding**) injects a false ordinal relationship — the model assumes the integers carry
magnitude and order, which for unordered categories is simply wrong.

The fix depends on the category's nature:

- **Nominal (no order)** → **one-hot encoding**: create a separate 0/1 column per
  category, so no false ordering exists. `colour` becomes `colour_red`, `colour_green`,
  `colour_blue`.
- **Ordinal (real order)** → label/ordinal encoding is *correct* — `small/medium/large`
  → `0/1/2` genuinely encodes order.
- **High-cardinality** (500 cities) → one-hot explodes into 500 columns; use **target
  encoding** (replace each category with the mean target for that category) or
  embeddings instead.

> **One-hot encoding** = one binary column per category (exactly one is 1 per row).
> **Label/ordinal encoding** = map categories to integers (only valid when order is
> real). **Target encoding** = replace a category with a statistic of the target for
> that category (compact for high-cardinality, but leakage-prone, 8.1). Choosing wrong
> either invents false structure or wastes the signal.

### The move

Pick the encoder by the category's nature, and fit it inside the pipeline (8.1) so it's
applied identically at serve time:

```python
from sklearn.preprocessing import OneHotEncoder

# nominal (no order): one column per category, no false ordering
enc = OneHotEncoder(handle_unknown="ignore")   # unseen categories at serve -> all-zeros, no crash
```

### Why it works

One-hot gives each category its own independent 0/1 dimension, so the model sees
`colour_red`, `colour_green`, `colour_blue` as **unrelated** features — there's no
numeric magnitude to misread as "blue > red". The model learns a separate weight per
category, which is exactly right for unordered data. Fitting the encoder inside a
`Pipeline` means the *set of categories* is learned on the training data and the same
columns are produced at serving time; `handle_unknown="ignore"` makes a category never
seen in training encode as all-zeros instead of crashing — essential for production where
new values appear.

### The code, every line explained

```python
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.pipeline import Pipeline

# --- WRONG: label-encode a NOMINAL column -> invents an order -----------
df["colour"] = df["colour"].map({"red": 0, "green": 1, "blue": 2})
# model now believes blue(2) > green(1) > red(0). False structure.

# --- RIGHT: one-hot for nominal, ordinal for truly-ordered --------------
preprocess = ColumnTransformer([
    # nominal categories -> one binary column each, unknowns ignored at serve
    ("colour", OneHotEncoder(handle_unknown="ignore"), ["colour"]),
    # genuinely ORDERED categories -> ordinal encoding IS correct here
    ("size", OrdinalEncoder(categories=[["small", "medium", "large"]]), ["size"]),
    # numeric columns -> scale (8.3); fit on train via the pipeline (8.1)
    ("nums", StandardScaler(), ["age", "income"]),
])
pipe = Pipeline([("prep", preprocess), ("model", model)])
pipe.fit(X_train, y_train)        # encoders learn categories from TRAIN only (no leakage)
pipe.predict(X_new)               # same encoding applied automatically at serve time

# --- HIGH-CARDINALITY (500 cities): one-hot would make 500 columns ------
# Option A: target encoding — replace city with mean(target) for that city.
#   MUST be fit inside CV folds / on train only, or it leaks the target (8.1)!
from category_encoders import TargetEncoder        # (3rd-party)
# Option B: group rare categories into "other"; keep only the top-K frequent ones.
# Option C: learned EMBEDDINGS (a small dense vector per category) — common in DL (Area 9).

# --- the decision rule --------------------------------------------------
# unordered + few categories     -> one-hot
# genuinely ordered              -> ordinal/label (order is meaningful)
# unordered + MANY categories    -> target encoding (careful w/ leakage) or embeddings
# tree models (RandomForest/XGB) -> tolerate label encoding better than linear models,
#                                   but one-hot/target is still usually safer for nominal
```

### Impact

- **No invented structure:** the model stops misreading category codes as ordered
  magnitudes, so it learns the real per-category effect.
- **Production-safe:** `handle_unknown="ignore"` and pipeline-fitted encoders mean unseen
  categories at serve time don't crash and encoding stays consistent (8.16).
- **Right tool for cardinality:** matching the encoder to the number of categories avoids
  both the false-order trap (label) and the column explosion (one-hot on 500 values).

### Pros & cons / when NOT to

**Choose the encoder deliberately when:** features are categorical — which is almost
every real tabular dataset.

**Watch out / when NOT to:**
- **Never label-encode nominal categories for linear/distance-based models** — it injects
  a false order they take literally. (Tree models are more tolerant but one-hot/target is
  still safer.)
- **One-hot explodes on high cardinality** — 500 cities → 500 sparse columns, bloating
  memory and hurting many models. Use target encoding, top-K + "other", or embeddings.
- **Target encoding leaks the label if naive** — fit it on training folds only (8.1), and
  prefer smoothed/cross-fold variants, or your CV score is fantasy.
- **Fit encoders on train only, inside a pipeline** — fitting on the full dataset leaks
  (8.1), and hand-encoding outside the pipeline causes train/serve mismatch (8.16).
- **Handle unseen categories explicitly** — a category present at serve but absent in
  training will crash a naive encoder; `handle_unknown="ignore"` or an "other" bucket is
  required for production.

### Where this shows up

- **Real work — every tabular model:** encoding categorical features (colours, regions,
  product types, device) is a routine, unavoidable preprocessing step.
- **Real work — high-cardinality features:** user/product/city ids handled via target
  encoding or embeddings rather than thousands of one-hot columns.
- **Real work — recommender/CTR systems:** categorical embeddings for huge id spaces are
  the standard, bridging to the DL approaches in Area 9.
- **Pattern mapping (secondary):** no DSA analogue; it's a representation choice — mapping
  discrete values into a numeric space without distorting their relationships, akin to
  choosing the right data structure (Area 3) for the meaning of the data.
[↑ Back to top](#contents)

---

<a id="8.3"></a>
## 8.3 — "One feature in rupees swamps another in years" → feature scaling

### The situation

Your model has two features: `age` (range ~18–80) and `annual_income` (range
~200,000–5,000,000). You train a distance-based or gradient-based model and it behaves as
if `age` barely matters:

```python
# income values are ~50,000x larger than age values
model = KNeighborsClassifier()          # uses DISTANCE between points
model.fit(X[["age", "annual_income"]], y)
# distance is dominated by income; age contributes almost nothing
```

The model isn't ignoring age because age is unimportant — it's because income's *numeric
magnitude* is tens of thousands of times larger, so any calculation involving distances
or weighted sums is overwhelmed by income before age gets a say.

### What's really going on

Many algorithms combine features by **magnitude** — distances (KNN, K-means, SVM with
RBF), gradient steps (linear/logistic regression, neural nets), and regularisation
penalties all treat a feature's raw scale as its importance. When one feature spans
millions and another spans tens, the large-scale feature dominates the geometry purely
because of its units, not its predictive value.

**Feature scaling** puts all features on a comparable range so each contributes on its
merits:

- **Standardisation** (`StandardScaler`): subtract the mean, divide by the standard
  deviation → each feature has mean 0, std 1 ("z-score"). The default for most models.
- **Min-max normalisation** (`MinMaxScaler`): rescale to a fixed range, usually [0, 1].
  Good when you need bounded inputs (e.g. some neural nets, image pixels).
- **Robust scaling** (`RobustScaler`): centre/scale using median and interquartile range
  → resistant to outliers.

> **Scaling/normalisation** = transforming features so their numeric ranges are
> comparable, so magnitude no longer masquerades as importance. It must be **fit on the
> training set only** (8.1) and applied via a pipeline so the same transform runs at
> serve time (8.16).

### The move

Scale features inside the pipeline so the model sees comparable ranges and the transform
is fit on train only:

```python
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

pipe = make_pipeline(StandardScaler(), KNeighborsClassifier())
pipe.fit(X_train, y_train)        # scaler learns mean/std from train (8.1)
```

### Why it works

`StandardScaler` rescales each feature to mean 0 and std 1, so after scaling `age` and
`annual_income` both span roughly the same numeric range (typically about −3 to +3). Now
a distance or a weighted sum gives each feature a fair chance — income's units no longer
dominate, and the model weights features by their actual predictive value, not their
scale. Fitting inside the pipeline means the scaler stores the **training** mean/std and
applies those same numbers to test and production data, so evaluation is honest (8.1) and
serving matches training (8.16).

### The code, every line explained

```python
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

# --- standardisation: the default choice --------------------------------
pipe = make_pipeline(StandardScaler(), model)   # each feature -> mean 0, std 1
pipe.fit(X_train, y_train)                       # mean/std learned from TRAIN only (8.1)
pipe.score(X_test, y_test)                        # scaler transforms test w/ train stats

# what StandardScaler does to one feature:  z = (x - mean_train) / std_train
# age 18..80 and income 2e5..5e6 both end up roughly in [-3, +3] -> comparable.

# --- alternatives, by situation -----------------------------------------
MinMaxScaler()      # -> [0, 1]; use when you need BOUNDED inputs (e.g. some NNs, pixels)
RobustScaler()      # centres on median, scales by IQR; use when OUTLIERS skew mean/std
# StandardScaler is the safe default for linear models, SVM, KNN, K-means, NNs.

# --- which models NEED scaling vs DON'T ---------------------------------
# NEED scaling (magnitude-sensitive):
#   - distance-based: KNN, K-means, SVM (RBF)
#   - gradient-based: linear/logistic regression, neural nets (also speeds convergence)
#   - anything with L1/L2 regularisation (penalty depends on coefficient scale)
# DON'T need scaling (split on thresholds, scale-invariant):
#   - tree-based: decision trees, RandomForest, gradient boosting (XGBoost/LightGBM)
#     -> scaling these is harmless but pointless.

# --- the leakage trap (same as 8.1) -------------------------------------
# WRONG: StandardScaler().fit_transform(X) BEFORE the split -> test stats leak in.
# RIGHT: fit the scaler inside the pipeline AFTER splitting, or it re-fits per CV fold.
```

### Impact

- **Fair feature contribution:** features influence the model by predictive value, not by
  the accident of their units — often a real accuracy gain for distance/gradient models.
- **Faster, more stable training:** gradient-based models converge faster and more
  reliably when features are on similar scales (smoother loss surface).
- **Consistent serving:** pipeline-fit scaling applies identical transforms at train and
  serve time, avoiding skew (8.16).

### Pros & cons / when NOT to

**Scale features when:** using distance-based, gradient-based, or regularised models —
KNN, K-means, SVM, linear/logistic regression, neural nets.

**Watch out / when NOT to:**
- **Tree-based models don't need it** — they split on thresholds, so they're
  scale-invariant. Scaling RandomForest/XGBoost inputs is harmless but adds no value.
- **Fit on train only, inside a pipeline** — the single most common scaling bug is
  `fit_transform(X)` before the split, which leaks test statistics (8.1).
- **Pick the scaler for the data** — `RobustScaler` when outliers would distort
  mean/std; `MinMaxScaler` when the model needs bounded inputs; `StandardScaler`
  otherwise.
- **Scale targets only when appropriate** — for regression, scaling the *target* can help
  some models but means inverse-transforming predictions; be deliberate.
- **Don't scale already-comparable features needlessly** — if all features share a sane
  range (e.g. all probabilities in [0,1]), scaling adds little.

### Where this shows up

- **Real work — any tabular model with mixed-unit features:** age + income + counts +
  ratios — scaling is a routine preprocessing step in the pipeline (8.1).
- **Real work — clustering & nearest-neighbour:** K-means/KNN results are meaningless
  without scaling, because they're pure distance.
- **Real work — neural network inputs:** normalising/standardising inputs (and pixels to
  [0,1], 1.1) is standard for stable, fast training (Area 9).
- **Pattern mapping (secondary):** no DSA analogue; it's a numeric-normalisation step so
  that combined quantities are comparable — the same spirit as normalising units before
  arithmetic.
[↑ Back to top](#contents)

---

<a id="8.4"></a>
## 8.4 — "99% accuracy but it never catches a single fraud" → imbalanced data

### The situation

You build a fraud detector. 99.2% accuracy — you're thrilled. Then you check what it
actually predicts:

```python
# dataset: 1,000,000 transactions, 8,000 fraudulent (0.8%)
model.fit(X_train, y_train)
print(accuracy_score(y_test, model.predict(X_test)))   # 0.992 — looks great!
# ...but the model predicts "not fraud" for EVERYTHING.
# It catches 0 of the frauds. Accuracy is high only because fraud is rare.
```

A model that labels *every* transaction "not fraud" is 99.2% accurate (because 99.2% of
transactions really aren't fraud) and **completely useless** — it never flags the thing
you built it to catch.

### What's really going on

The classes are **imbalanced**: one class (fraud, churn, disease, defect) is far rarer
than the other. With a 99.2% / 0.8% split, **accuracy is a trap** — predicting the
majority class for everything scores 99.2% while having zero value. The metric rewards
ignoring the rare class, which is exactly the class you care about.

Two things must change:

1. **Stop using accuracy.** Measure performance on the rare class directly — **precision**
   (of those flagged fraud, how many really are), **recall** (of all real frauds, how many
   you caught), their combination **F1**, or threshold-independent **ROC-AUC / PR-AUC**.
2. **Help the model attend to the rare class** — via class weights, resampling
   (oversample the minority / undersample the majority), or threshold tuning.

> **Class imbalance** = one target class is much rarer than the other(s). It breaks
> accuracy as a metric (the majority-class baseline looks great) and biases models toward
> the majority. Fixes: rare-class metrics (precision/recall/F1/PR-AUC) + techniques that
> rebalance the model's attention (class weights, resampling, threshold tuning).

### The move

Measure with rare-class metrics, and tell the model the rare class matters via class
weights (the simplest, leakage-free fix):

```python
model = LogisticRegression(class_weight="balanced")   # penalise rare-class mistakes more
# evaluate on the RARE class, not accuracy:
from sklearn.metrics import classification_report
print(classification_report(y_test, model.predict(X_test)))  # precision/recall/F1 per class
```

### Why it works

`class_weight="balanced"` makes the model treat each fraud example as worth many "normal"
examples when computing its loss — so misclassifying a fraud is penalised heavily, and
the model can no longer minimise error by ignoring the rare class. It now has an
incentive to actually find frauds. And `classification_report` shows **precision and
recall per class**, so "catches 0 frauds" is glaringly visible (recall = 0.00 for the
fraud class) where accuracy hid it. You optimise and report the number that reflects the
real goal — catching the rare event — instead of the misleading aggregate.

### The code, every line explained

```python
from sklearn.metrics import classification_report, confusion_matrix, average_precision_score
from sklearn.linear_model import LogisticRegression

# --- 1) fix the METRIC: never trust accuracy on imbalanced data ---------
model = LogisticRegression(class_weight="balanced").fit(X_train, y_train)
pred  = model.predict(X_test)
print(classification_report(y_test, pred))   # per-class precision, recall, F1
#   precision = TP / (TP + FP)  -> of flagged frauds, how many were real
#   recall    = TP / (TP + FN)  -> of all real frauds, how many we caught  (KEY here)
#   F1        = harmonic mean of precision & recall (one balanced number)
print(confusion_matrix(y_test, pred))         # see the actual TP/FP/FN/TN counts

# PR-AUC (area under precision-recall curve) suits rare positives better than ROC-AUC:
proba = model.predict_proba(X_test)[:, 1]
print("PR-AUC:", average_precision_score(y_test, proba))

# --- 2) fix the MODEL's attention: pick ONE approach --------------------
# (a) class weights — simplest, no resampling, no leakage risk:
LogisticRegression(class_weight="balanced")
RandomForestClassifier(class_weight="balanced")

# (b) resampling — oversample the minority (SMOTE) or undersample majority:
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
pipe = ImbPipeline([("smote", SMOTE()), ("model", model)])
# CRITICAL: resample INSIDE the CV pipeline, on TRAIN folds only. Oversampling the
# whole dataset before splitting leaks duplicates into the test set (8.1).

# (c) threshold tuning — the default 0.5 cutoff is often wrong for imbalance:
proba = model.predict_proba(X_test)[:, 1]
pred  = (proba > 0.2).astype(int)   # lower threshold -> catch more frauds (higher recall,
                                    # lower precision). Choose the threshold from the
                                    # precision/recall trade-off your problem needs.

# --- the business trade-off decides the threshold -----------------------
# Fraud / disease: missing a positive (false negative) is costly -> favour RECALL.
# Spam filter: flagging a real email (false positive) annoys users -> favour PRECISION.
# There is no universal "best" — pick the operating point from the cost of each error.
```

### Impact

- **The model becomes useful:** instead of a 99% "always says no", it actually catches a
  meaningful fraction of the rare events you built it for.
- **Honest evaluation:** rare-class metrics expose the failure that accuracy concealed,
  so you can't ship a useless-but-high-accuracy model by mistake.
- **Tunable to the business:** the precision/recall trade-off (via class weights or
  threshold) lets you match the model to the real cost of false positives vs false
  negatives.

### Pros & cons / when NOT to

**Treat imbalance explicitly when:** the positive class is rare and is the one you care
about — fraud, churn, disease, defects, anomalies, rare-event prediction.

**Watch out / when NOT to:**
- **Never report accuracy alone on imbalanced data** — it's the trap. Lead with
  precision/recall/F1 or PR-AUC for the rare class.
- **Resample on training folds only** — SMOTE/oversampling before the split duplicates
  minority rows into the test set, leaking (8.1) and inflating scores. Use `imblearn`'s
  pipeline so it happens per fold.
- **The 0.5 threshold is rarely right** — tune it from the precision/recall curve to your
  cost trade-off; don't accept the default cutoff.
- **Prefer class weights first** — they're simple and leakage-free; reach for SMOTE/
  resampling when weights aren't enough, and validate it actually helps (it can add noise).
- **Don't chase recall blindly** — flagging everything gives 100% recall and 0 precision
  (useless alerts). Balance both for the actual decision the model drives.

### Where this shows up

- **Real work — fraud / anomaly / defect detection:** the canonical imbalanced problem;
  recall on the rare class is the metric that matters, never accuracy.
- **Real work — churn / disease / rare-event prediction:** same pattern — the rare
  positive is the point, so class weights + precision/recall drive everything.
- **Real work — alerting systems:** threshold tuning to balance "catch real incidents"
  (recall) against "don't drown ops in false alarms" (precision).
- **Pattern mapping (secondary):** no DSA analogue; it's the evaluation-and-objective
  alignment principle — measure (and optimise) the thing you actually care about, tightly
  linked to metric choice (8.5).
[↑ Back to top](#contents)

---

<a id="8.5"></a>
## 8.5 — "We optimised the metric and the product got worse" → choosing the right metric

### The situation

You're told to "improve the model." You optimise accuracy, ship it, and the business
outcome *worsens* — or two teammates report different "scores" for the same model and
argue about which is right:

```python
print(accuracy_score(y_test, pred))    # 0.91 — but is accuracy even the right question?
# The model that maximises accuracy might recommend the same popular item to everyone,
# or miss every rare-but-critical case — "better metric, worse product."
```

The number went up; the thing you actually cared about went down. The metric and the
goal were misaligned.

### What's really going on

A **metric is a proxy for the real objective**, and choosing the wrong proxy means you
optimise the wrong thing. Each metric answers a *different question*, and the right one
depends entirely on **what decision the model drives and what each kind of error costs**.
Optimising a convenient default (accuracy, or RMSE) instead of the metric that reflects
the business goal is how "the score improved but the product regressed" happens.

The job is to **pick the metric that matches the cost structure of your problem** before
optimising anything:

- **Classification:** accuracy (only if balanced, 8.4), precision vs recall (which error
  is costlier?), F1 (balance), ROC-AUC (ranking, balanced), PR-AUC (ranking, rare
  positives).
- **Regression:** MAE (robust, interpretable in units), RMSE (punishes large errors
  more), MAPE (percentage error), R² (variance explained) — and they can disagree about
  which model is "best".
- **Ranking/recommendation:** precision@k, recall@k, NDCG — "is the *top* of the list
  good?", not overall accuracy.

> A **metric** is a single number standing in for "is the model good *for our purpose*?"
> Different metrics encode different priorities; the skill is choosing the one whose
> definition matches the real-world cost of being wrong — *before* you tune to it,
> because you will get exactly what you optimise.

### The move

Choose the metric from the *cost of each error type* for your specific decision, and fix
it before tuning:

```python
# Fraud: a missed fraud (false negative) costs money; a false alarm is cheap to review
#   -> optimise RECALL (and watch precision). Accuracy is irrelevant (8.4).
# Forecasting spend where big misses hurt disproportionately -> RMSE (punishes large errors).
```

### Why it works

Picking the metric from the **error costs** aligns the optimisation target with the
real-world goal, so "the number went up" actually means "the product got better". If
missing a positive is expensive (fraud, disease), recall is the right proxy and tuning to
it catches more of what matters; if large errors are disproportionately bad (forecasting),
RMSE's squaring penalises them more than MAE, so the model avoids big misses. Because a
model becomes *whatever its metric rewards*, choosing the metric that encodes your
priorities is what makes optimisation move the product in the intended direction.

### The code, every line explained

```python
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, average_precision_score,
                             mean_absolute_error, mean_squared_error, r2_score)

# --- CLASSIFICATION: pick by which error costs more ---------------------
recall_score(y, pred)       # of real positives, how many caught — use when MISSES costly
precision_score(y, pred)    # of flagged positives, how many right — use when FALSE ALARMS costly
f1_score(y, pred)           # balance of the two — when both errors matter
roc_auc_score(y, proba)     # ranking quality, threshold-free — good for BALANCED data
average_precision_score(y, proba)  # PR-AUC — better than ROC-AUC for RARE positives (8.4)
# accuracy_score: ONLY meaningful when classes are roughly balanced.

# --- REGRESSION: metrics can DISAGREE on the best model -----------------
mean_absolute_error(y, pred)              # MAE: avg |error|, in the target's units, robust
mean_squared_error(y, pred, squared=False)# RMSE: punishes LARGE errors more (squares them)
r2_score(y, pred)                          # fraction of variance explained (0..1, can be <0)
# A model with low MAE but a few huge misses can have worse RMSE than a steadier model —
# choose MAE if all errors are equally bad, RMSE if big errors are disproportionately bad.

# --- RANKING / RECOMMENDATION: only the TOP matters ---------------------
# precision@k / recall@k / NDCG — "are the top-k recommendations good?", not overall
# accuracy. A recommender judged on accuracy may just predict the popular item for all.

# --- align the metric with optimisation (don't tune to the wrong one) ---
from sklearn.model_selection import GridSearchCV
GridSearchCV(model, params, scoring="recall")   # tune TOWARD the metric you actually want
# GridSearchCV(..., scoring="accuracy") on imbalanced data would tune toward uselessness.

# --- the guarding question ----------------------------------------------
# "What does a false positive cost us? What does a false negative cost us?"
#  -> that answer picks the metric. If you can't answer it, you can't choose a metric.
```

### Impact

- **Optimisation moves the real goal:** tuning improves the outcome you care about, not a
  proxy that diverges from it — no more "metric up, product down".
- **Shared, unambiguous evaluation:** everyone reports the same purpose-fit metric, ending
  "my accuracy vs your F1" arguments.
- **Right model selected:** when regression metrics disagree, choosing by error-cost picks
  the model that's actually best for the use case.

### Pros & cons / when NOT to

**Choose the metric deliberately when:** *always, before optimising* — the metric defines
what "better" means, so getting it wrong wastes all subsequent effort.

**Watch out / when NOT to:**
- **Don't default to accuracy/RMSE out of habit** — they're right only for specific
  situations (balanced classes; errors equally costly). Start from the cost of each error.
- **Tune toward the metric you'll be judged on** — optimising accuracy then reporting F1
  (or vice versa) means your search optimised the wrong target.
- **One headline metric, but watch the others** — optimising recall to 100% can crater
  precision (8.4); track the trade-off, don't tunnel on a single number.
- **Beware Goodhart's law** — "when a measure becomes a target, it ceases to be a good
  measure." A metric can be gamed in ways that hurt the real goal (e.g. clickbait
  maximising CTR); sanity-check against the actual outcome.
- **Offline metric ≠ business outcome** — a great offline score doesn't guarantee a better
  product; validate with an A/B test or the real KPI where possible.

### Where this shows up

- **Real work — model selection & tuning:** the `scoring=` you pass to CV/grid search *is*
  your definition of better; choosing it correctly is step zero of any modelling task.
- **Real work — imbalanced problems:** metric choice and imbalance (8.4) are inseparable —
  precision/recall/PR-AUC over accuracy.
- **Real work — forecasting/regression:** picking MAE vs RMSE vs MAPE based on whether big
  errors or percentage errors hurt most.
- **Pattern mapping (secondary):** no DSA analogue; it's the objective-definition
  principle — be precise about what you're optimising, the evaluation cousin of
  understanding the problem before coding (Area 11's "read the problem first").
[↑ Back to top](#contents)

---

<a id="8.6"></a>
## 8.6 — "My model scored 0.88, but a re-split gave 0.79" → cross-validation

### The situation

You evaluate with a single train/test split, get a great score, and make decisions on
it — then notice the score swings depending on *which* split you happened to use:

```python
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1)
model.fit(X_train, y_train)
print(model.score(X_test, y_test))     # 0.88
# change random_state to 2 -> 0.79.  Which number is the truth?
```

A single split means your reported score depends on the luck of which rows landed in the
test set. With a small or noisy dataset, that luck can swing the number by several
points — so you can't tell whether model A really beats model B, or you just got a
favourable split.

### What's really going on

One train/test split gives **one** estimate of performance, computed on **one** arbitrary
subset — a high-variance, luck-dependent number. You can't trust it for model selection,
because the difference between two models might be smaller than the noise between two
splits.

**Cross-validation** removes the luck by averaging over *multiple* splits. **k-fold CV**
divides the data into k equal parts ("folds"); it trains on k−1 folds and tests on the
held-out fold, rotating so **every** row is in the test set exactly once. You get k
scores; their **mean** is a stable performance estimate and their **spread** (std) tells
you how reliable it is.

> **Cross-validation (k-fold)** = split data into k folds, train/test k times rotating
> the held-out fold, average the k scores. It gives a **lower-variance estimate** of
> performance (and a variance *measurement*) than a single split, so model comparisons
> are trustworthy. Variants: **StratifiedKFold** (preserves class balance per fold —
> essential for imbalance, 8.4), **TimeSeriesSplit** (respects time order — no future
> leakage, 8.1), **GroupKFold** (keeps related rows together).

### The move

Use k-fold cross-validation and report the mean ± std, with a pipeline so each fold is
leakage-free:

```python
from sklearn.model_selection import cross_val_score

scores = cross_val_score(pipe, X, y, cv=5, scoring="f1")   # 5 folds; pipe = transforms+model (8.1)
print(f"{scores.mean():.3f} ± {scores.std():.3f}")          # stable estimate + reliability
```

### Why it works

By training and testing five times on different fold assignments, CV averages out the
luck of any single split — the mean is far more stable than one number, and the std tells
you how much the score wobbles (so you know whether a 0.88-vs-0.85 difference is real or
noise). Passing the **pipeline** (not pre-transformed data) means each fold re-fits its
scaler/encoder/imputer on *that fold's training portion only*, so there's no leakage
across folds (8.1) — every fold's test score is honest. The `scoring=` makes CV evaluate
the metric you actually care about (8.5), and `StratifiedKFold` (the default for
classifiers) keeps the class ratio steady per fold so imbalance (8.4) doesn't distort
individual folds.

### The code, every line explained

```python
from sklearn.model_selection import cross_val_score, StratifiedKFold, TimeSeriesSplit, GridSearchCV

# --- basic k-fold: mean ± std, leakage-free via the pipeline ------------
scores = cross_val_score(pipe, X, y, cv=5, scoring="f1")
#                        │    │     │  └ the metric you care about (8.5)
#                        │    │     └ 5 folds: train on 4, test on 1, rotate
#                        │    └ full data — CV does the splitting internally
#                        └ a PIPELINE so transforms re-fit per fold (no leakage, 8.1)
print(scores)                       # e.g. [0.82, 0.79, 0.85, 0.80, 0.83]
print(f"{scores.mean():.3f} ± {scores.std():.3f}")   # 0.818 ± 0.021 -> stable + reliable

# --- stratified (default for classifiers): keep class balance per fold --
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)  # reproducible (8.7)
cross_val_score(pipe, X, y, cv=cv, scoring="average_precision")  # PR-AUC for imbalance (8.4)

# --- time series: NEVER random-fold temporal data (future leakage, 8.1) -
tscv = TimeSeriesSplit(n_splits=5)   # each fold trains on PAST, tests on the next chunk
cross_val_score(pipe, X, y, cv=tscv)

# --- CV is also how you tune hyperparameters honestly -------------------
grid = GridSearchCV(pipe, {"model__C": [0.1, 1, 10]}, cv=5, scoring="f1")
grid.fit(X, y)                       # each candidate evaluated by CV, not one lucky split
print(grid.best_params_, grid.best_score_)

# --- the nested-CV subtlety (for unbiased tuned-model estimates) --------
# If you tune hyperparameters with CV AND report that same CV score, the score is
# slightly optimistic (you selected for it). For a truly unbiased estimate, use NESTED
# CV: an outer CV for evaluation wrapping an inner CV for tuning. Often overkill, but
# know it exists when the final number must be trustworthy.
```

### Impact

- **Trustworthy comparisons:** the mean±std tells you whether model A genuinely beats
  model B or just won the split lottery — the basis of sound model selection.
- **Uses all the data:** every row serves as both train and test (across folds), giving a
  better estimate than holding out one fixed chunk — valuable on small datasets.
- **Honest tuning:** CV-based hyperparameter search avoids overfitting to one split's
  quirks.

### Pros & cons / when NOT to

**Use cross-validation when:** comparing models/hyperparameters, or whenever a single
split's score would be too noisy to trust — i.e. most modelling, especially smaller data.

**Watch out / when NOT to:**
- **Pass a pipeline, not pre-transformed data** — CV's anti-leakage benefit only holds if
  transforms re-fit per fold (8.1). Scaling/encoding the whole X before CV leaks across
  folds.
- **Stratify for imbalanced classes** (`StratifiedKFold`) so each fold keeps the rare
  class; a random fold might get zero positives and a meaningless score (8.4).
- **Respect structure** — time series needs `TimeSeriesSplit` (no future in training);
  grouped data (multiple rows per user) needs `GroupKFold` so the same group isn't in
  both train and test (a leakage source).
- **CV costs k× the compute** — for very large datasets or expensive models, a single
  large held-out set (or fewer folds) may be pragmatic; CV shines most on small/medium
  data.
- **Tuning + reporting on the same CV is optimistic** — use nested CV when an unbiased
  final estimate matters.

### Where this shows up

- **Real work — every model-selection decision:** "is this model/feature/hyperparameter
  actually better?" is answered with CV mean±std, not a single split.
- **Real work — hyperparameter search:** `GridSearchCV`/`RandomizedSearchCV` use CV under
  the hood to evaluate each candidate honestly.
- **Real work — small/noisy datasets:** where one split is far too unreliable, CV (or
  repeated CV) is essential to get a stable read.
- **Pattern mapping (secondary):** no DSA analogue; it's the variance-reduction-by-
  resampling principle for trustworthy estimates — the evaluation backbone that makes
  leakage avoidance (8.1) and metric choice (8.5) actionable.
[↑ Back to top](#contents)

---

<a id="8.7"></a>
## 8.7 — "I trained the same model twice and got different results" → seeds & determinism

### The situation

You train a model, get 0.84. You run the *exact same code* again and get 0.81. A
teammate runs it and gets 0.86. Nothing changed — yet the numbers won't sit still:

```python
model = RandomForestClassifier()       # randomness in bootstrap sampling + feature picks
model.fit(X_train, y_train)            # different random choices each run -> different model
# run 1: 0.84, run 2: 0.81, colleague: 0.86 — which is "the" score?
```

You can't tell if a change you made *actually* improved the model or if you just got a
luckier random initialisation — and your colleague can't reproduce your result to verify
it.

### What's really going on

Many ML operations use **randomness**: train/test splitting, RandomForest's bootstrap
sampling and feature selection, neural-net weight initialisation and shuffling, K-means
centroid starts, SMOTE, dropout. By default that randomness is seeded from the system
clock, so every run differs. The result is **non-reproducible** — you can't compare runs,
debug, or let anyone verify your numbers.

The fix is to **set the random seed** so the "random" choices are the *same* every run.
Computers use **pseudo-random** number generators: given the same starting **seed**, they
produce the identical sequence of "random" numbers. Fix the seed → fix the randomness →
identical results across runs and machines.

> A **seed** is the starting value for a pseudo-random number generator; the same seed
> reproduces the same sequence, making randomised operations **deterministic** (same
> output every run). You must set it in *every* library that introduces randomness
> (Python's `random`, NumPy, the ML framework) — and pass `random_state=` to scikit-learn
> estimators/splitters — or some component stays random.

### The move

Set seeds everywhere randomness enters, and pass `random_state` to every estimator and
splitter:

```python
import random, numpy as np
random.seed(42); np.random.seed(42)          # Python + NumPy RNGs
model = RandomForestClassifier(random_state=42)   # the estimator's own randomness
X_tr, X_te, y_tr, y_te = train_test_split(X, y, random_state=42)   # the split
```

### Why it works

With a fixed seed, every pseudo-random draw — which rows go to test, which samples each
tree bootstraps, which features it considers — replays the *identical* sequence on every
run and every machine. So "train twice, get the same number" holds, and a score change
now genuinely reflects *your code change*, not random luck. Reproducibility also lets a
colleague rerun your script and get your exact result, which is the basis of trust,
debugging, and code review for ML. The catch is **coverage**: every independent source of
randomness needs its own seed, so you set Python's `random`, NumPy, the framework, *and*
each estimator's `random_state` — miss one and that component still wanders.

### The code, every line explained

```python
import random, os
import numpy as np

# --- a reusable seed-everything function (call once at the top) ---------
def set_seed(seed=42):
    random.seed(seed)                  # Python's built-in random module
    np.random.seed(seed)               # NumPy (used by pandas, sklearn internals)
    os.environ["PYTHONHASHSEED"] = str(seed)   # stabilise hash-based ordering
    # for deep learning, also:
    # torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)  (Area 9)
    # tf.random.set_seed(seed)

set_seed(42)

# --- pass random_state to EVERY sklearn component that takes it ---------
from sklearn.model_selection import train_test_split, StratifiedKFold
X_tr, X_te, y_tr, y_te = train_test_split(X, y, random_state=42)   # reproducible split (8.6)
model = RandomForestClassifier(random_state=42)                     # reproducible trees
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)     # reproducible folds
# Miss random_state on ANY of these and that step stays non-deterministic.

# --- when you WANT to measure randomness: vary the seed deliberately ----
seeds = [0, 1, 2, 3, 4]
scores = [train_and_eval(seed=s) for s in seeds]
print(f"{np.mean(scores):.3f} ± {np.std(scores):.3f}")
# Reporting mean±std over several seeds shows how much the result depends on luck —
# more honest than a single seeded number that could be cherry-picked.

# --- GPU determinism is harder (Area 9 preview) -------------------------
# Some GPU ops are non-deterministic even with seeds set (parallel float reductions).
# Full determinism may need torch.use_deterministic_algorithms(True) and can cost speed —
# a trade-off you opt into when exact reproducibility matters.
```

### Impact

- **Reproducible results:** the same code yields the same number every run and on every
  machine — so you (and reviewers) can trust and verify outcomes.
- **Valid comparisons:** a score change reflects your *actual* change, not random
  variation, so you can tell whether an improvement is real (complements CV, 8.6).
- **Debuggable:** a deterministic run can be re-run to reproduce a bug or odd result,
  instead of it vanishing on the next execution.

### Pros & cons / when NOT to

**Set seeds when:** doing any ML/experiment work — training, splitting, sampling,
initialisation — i.e. essentially always.

**Watch out / when NOT to:**
- **Seed *every* source.** Missing one library or one estimator's `random_state` leaves
  that component random and breaks reproducibility — and the failure is silent (numbers
  just won't match).
- **A single fixed seed can mislead.** One seed's score might be lucky; for an *honest*
  read, report mean±std over several seeds (or use CV, 8.6) — don't cherry-pick the seed
  that looks best.
- **Determinism ≠ better.** Seeding makes results *repeatable*, not *more accurate*; it's
  for reproducibility, not performance.
- **GPU/parallel ops may stay non-deterministic** even with seeds (float reduction order);
  full determinism needs extra flags and can slow training (Area 9) — opt in only when
  exact reproducibility is required.
- **Don't reuse the same seed to fake stability** — if results swing wildly across seeds,
  that variance is real information (a fragile model), not something to hide behind one
  seed.

### Where this shows up

- **Real work — every experiment & training run:** seeding is the baseline for trustworthy
  ML work; combined with pinned dependencies (7.15), it makes runs fully reproducible.
- **Real work — A/B of model changes:** to attribute a score change to your change, the
  randomness must be held fixed (or averaged over seeds).
- **Real work — paper/result reproduction:** sharing seeds (and a lockfile, 7.15) is what
  lets others reproduce your reported numbers.
- **Pattern mapping (secondary):** no DSA analogue; it's the determinism/reproducibility
  discipline — the experiment-level sibling of reproducible environments (7.15) and a
  precondition for reproducible pipelines (8.8).
[↑ Back to top](#contents)

---

<a id="8.8"></a>
## 8.8 — "I can't recreate the model that's running in production" → reproducible pipelines

### The situation

Three months ago you trained the model now serving production. A stakeholder asks "why
did it predict X?" or "retrain it with the new data" — and you discover you *can't
recreate it*:

```python
# the notebook that made it (run interactively, cells out of order):
df = pd.read_csv("data_v?.csv")        # which data file? what version?
df = df.dropna()                        # ...and some manual cleaning you don't fully recall
# ...20 cells of ad-hoc transforms...
model = train(df)                       # what hyperparameters? what seed? what code commit?
joblib.dump(model, "model.pkl")         # only the OUTPUT was saved — not HOW it was made
```

You have the model file but not a reliable way to *reproduce* it: the exact data, code,
preprocessing, hyperparameters, and environment that produced it are scattered, partly in
your memory, and partly lost.

### What's really going on

A model is the output of a **pipeline**: `data + code + preprocessing + hyperparameters +
environment + randomness → model`. If any of those inputs isn't captured, the result
isn't reproducible — you can't retrain identically, debug a prediction, audit a decision,
or roll back. Reproducibility here means **all the inputs are recorded and the whole
process is automated**, not run by hand in a notebook.

This pulls together threads from across the guide into one discipline:

- **Code**: committed and version-tagged (which git commit produced this model?).
- **Data**: versioned/snapshotted (which exact dataset? — tools like DVC, or an immutable
  data path).
- **Preprocessing**: codified as a saved `Pipeline` (8.1), not ad-hoc notebook cells, so
  the *same* transforms run at train and serve (8.16).
- **Hyperparameters & seed**: recorded (8.7) so the run is deterministic.
- **Environment**: pinned (7.15) so library versions match.
- **Tracked**: logged to an experiment tracker (8.15) linking all of the above to the
  resulting metrics and artifact.

> A **reproducible pipeline** = the end-to-end, automated process that turns versioned
> data + committed code + recorded config into a model, such that re-running it yields the
> same model. The opposite — an interactive notebook with unsaved steps — produces a model
> nobody can recreate.

### The move

Codify the whole train flow as a script/pipeline driven by a recorded config, and log
every input alongside the output:

```python
# train.py — one command, all inputs explicit, nothing interactive
def train(config):
    df = load_versioned(config["data_version"])     # exact data
    pipe = build_pipeline(config)                     # preprocessing + model, as code (8.1)
    set_seed(config["seed"])                          # determinism (8.7)
    pipe.fit(df[features], df[target])
    log_run(config, git_commit(), metrics, artifact=pipe)   # track everything (8.15)
    return pipe
```

### Why it works

Every input that determines the model is **explicit and recorded**: the data version, the
preprocessing-and-model as a single saved `Pipeline` object, the seed, the config, and the
git commit — all logged together. Re-running `train(config)` with the same config and the
pinned environment (7.15) regenerates the same model, because nothing is left to memory or
out-of-order cells. Saving the *whole pipeline* (not just the model) means the exact
preprocessing travels with it, so serving applies identical transforms (8.16) and you can
answer "why did it predict X?" by replaying the recorded inputs. The experiment log (8.15)
ties model → metrics → data → code, giving you audit, debug, and rollback.

### The code, every line explained

```python
# --- config-driven training script (not an interactive notebook) --------
config = {                              # ALL knobs in one recorded place
    "data_version": "2026-03-15",       # exact data snapshot (DVC tag / immutable path)
    "features": ["age", "income", "city"],
    "target": "churn",
    "model": "RandomForest",
    "hyperparams": {"n_estimators": 200, "max_depth": 8},
    "seed": 42,                         # determinism (8.7)
}

def train(config):
    set_seed(config["seed"])                              # reproducible randomness (8.7)
    df = load_versioned(config["data_version"])           # exact, versioned data
    pipe = build_pipeline(config)        # ColumnTransformer + model, ALL preprocessing
                                         # captured as code (8.1) — no notebook cells
    pipe.fit(df[config["features"]], df[config["target"]])
    return pipe

# --- save the WHOLE pipeline (preprocessing + model), not just the model -
import joblib
joblib.dump(pipe, "model.pkl")          # includes scalers/encoders -> serve applies the
                                        # SAME transforms (avoids train/serve skew, 8.16)

# --- record what produced it (experiment tracking, 8.15) ----------------
import mlflow
with mlflow.start_run():
    mlflow.log_params(config["hyperparams"] | {"data_version": config["data_version"],
                                               "git_commit": git_commit(), "seed": config["seed"]})
    mlflow.log_metrics({"f1": f1, "pr_auc": pr_auc})
    mlflow.sklearn.log_model(pipe, "model")   # artifact linked to its inputs+metrics
# Now: model <-> data version <-> code commit <-> config <-> metrics, all linked.

# --- the reproducibility checklist --------------------------------------
# [ ] data versioned/snapshotted?        (which exact rows?)         DVC / immutable path
# [ ] code committed + commit recorded?   (which exact code?)        git
# [ ] preprocessing saved as a pipeline?  (same transforms at serve) 8.1 / 8.16
# [ ] seed set + recorded?                (deterministic)            8.7
# [ ] environment pinned?                 (same lib versions)        7.15
# [ ] run logged (params/metrics/artifact)?(linked + auditable)      8.15
# All six -> the model can be recreated, audited, debugged, and rolled back.
```

### Impact

- **Recreatable models:** re-running the pipeline regenerates the production model
  exactly — so you can retrain, audit, and roll back with confidence.
- **Debuggable predictions:** because inputs are recorded, you can replay why the model
  behaves as it does and trace a bad prediction to its cause.
- **Team-scalable & compliant:** anyone can reproduce a result; regulated domains can
  audit how a model was built — impossible with a one-off notebook.

### Pros & cons / when NOT to

**Build reproducible pipelines when:** a model will run in production, be retrained, be
shared, or ever need auditing — i.e. any model that matters beyond a quick experiment.

**Watch out / when NOT to:**
- **Notebooks are for exploration, not production training.** Out-of-order cells and
  unsaved transforms are the classic "can't reproduce it" trap. Graduate the flow to a
  script/pipeline before it produces a model anyone depends on.
- **Save the whole pipeline, not just the model.** Pickling only the estimator loses the
  preprocessing, causing train/serve skew (8.16) and breaking reproducibility.
- **All six inputs must be captured** (data, code, preprocessing, seed, env, tracking) —
  missing any one breaks reproducibility silently. Use the checklist.
- **Data versioning is the hardest part** — code is easy to commit; "the exact data" needs
  a snapshot/version (DVC, immutable storage), not a mutable `data.csv` that changes under
  you.
- **Don't over-engineer throwaway experiments** — a quick what-if doesn't need the full
  apparatus; apply it once an experiment becomes a model you'll keep.

### Where this shows up

- **Real work — production model lifecycle:** the standard for any served model —
  retraining, rollback, and "why did it predict that?" all depend on reproducibility.
- **Real work — regulated/audited ML:** finance, healthcare, hiring — you must show
  exactly how a model was built and on what data.
- **Real work — team collaboration:** reproducible pipelines + tracking (8.15) let a team
  build on each other's runs instead of each owning an unrepeatable notebook.
- **Pattern mapping (secondary):** no DSA analogue; it's the end-to-end reproducibility
  discipline that *composes* seeds (8.7), pinned environments (7.15), pipelines/no-leakage
  (8.1), and tracking (8.15) into a recreatable whole.
[↑ Back to top](#contents)

---

<a id="8.9"></a>
## 8.9 — "The saved model loads but predicts garbage in production" → serialization & versioning

### The situation

You train, save, and later load a model to serve it — and it either fails to load or
produces nonsense:

```python
# training environment: scikit-learn 1.3, and you saved ONLY the model
joblib.dump(model, "model.pkl")

# serving environment (weeks later): scikit-learn 1.5, different code
model = joblib.load("model.pkl")        # warns about version mismatch, or breaks subtly
pred = model.predict(raw_input)          # raw_input ISN'T preprocessed -> garbage out
```

Two failures: the **library version** differs between save and load (pickled models are
version-sensitive), and you saved only the *estimator*, so the **preprocessing** that
training applied (scaling, encoding) isn't there at serve time — the model gets raw,
untransformed inputs and predicts rubbish.

### What's really going on

Saving a model is **serialization** — turning the in-memory object into bytes on disk
(8.x / Area 6's pickling) — and reloading it has requirements people miss:

1. **The whole pipeline must be saved, not just the model.** The fitted scalers/encoders
   (8.1/8.3) are part of how inputs become predictions; without them, serving feeds raw
   data to a model trained on transformed data (train/serve skew, 8.16).
2. **The environment must match.** Pickled scikit-learn/PyTorch objects are tied to the
   library version that created them — load under a different version and you get warnings,
   errors, or silently wrong behaviour. Pin versions (7.15) and record them with the
   artifact.
3. **Artifacts must be versioned.** "model.pkl" overwritten in place means you can't roll
   back to the previous model or know which one is deployed. Version the files
   (`model_v3_2026-03-15.pkl`) and link them to the run that produced them (8.8/8.15).

> **Model serialization** = persisting a trained model (and its preprocessing) to disk so
> it can be loaded and served later. `joblib`/`pickle` are standard for scikit-learn;
> frameworks have their own (`torch.save`, SavedModel). The pitfalls: save the *pipeline*
> not just the estimator, match the *environment*, and *version* the artifact.

### The move

Save the **whole fitted pipeline** with its version metadata, to a **versioned** path:

```python
import joblib, sklearn
artifact = {"pipeline": pipe,                     # preprocessing + model together (8.1)
            "sklearn_version": sklearn.__version__, # so the loader can check compatibility
            "trained_at": "2026-03-15", "git_commit": git_commit()}
joblib.dump(artifact, "models/model_v3_2026-03-15.pkl")   # versioned filename, not overwrite
```

### Why it works

Saving the **pipeline** means the fitted scalers/encoders travel with the model, so at
serve time the same transforms turn raw input into the representation the model expects —
no skew (8.16). Bundling the **library version** lets the loader detect a mismatch and
fail loudly (7.2) instead of predicting silently-wrong values. A **versioned filename**
(plus the git commit and date) means you never overwrite the live model, can roll back to
a previous version instantly, and can trace any served model back to the run that built it
(8.8). Pinning the environment (7.15) so load-time versions match save-time is the final
guarantee that the reloaded object behaves identically.

### The code, every line explained

```python
import joblib, sklearn

# --- save the WHOLE pipeline + metadata, to a VERSIONED path ------------
artifact = {
    "pipeline": pipe,                       # ColumnTransformer + model (NOT just the model)
    "sklearn_version": sklearn.__version__, # record env so load can verify (7.15)
    "feature_names": list(X.columns),       # so serving validates input columns (8.16)
    "trained_at": "2026-03-15",
    "git_commit": git_commit(),             # link back to the producing code (8.8)
}
joblib.dump(artifact, "models/churn_v3_2026-03-15.pkl")   # versioned -> rollback possible

# --- load defensively: check the environment matches -------------------
loaded = joblib.load("models/churn_v3_2026-03-15.pkl")
if loaded["sklearn_version"] != sklearn.__version__:
    log.warning("sklearn mismatch: trained %s, serving %s",
                loaded["sklearn_version"], sklearn.__version__)   # fail loud-ish (7.2)
pipe = loaded["pipeline"]
pred = pipe.predict(raw_input)              # pipeline preprocesses raw_input correctly

# --- framework-specific serialization -----------------------------------
# PyTorch: save the STATE DICT (weights), not the whole pickled module (Area 9, 9.5):
#   torch.save(model.state_dict(), "weights_v3.pt")   # robust across code changes
#   model.load_state_dict(torch.load("weights_v3.pt")); model.eval()
# TensorFlow/Keras: model.save("saved_model/")  (SavedModel format, portable)

# --- SECURITY: pickle executes code on load -----------------------------
# joblib/pickle can run ARBITRARY code when loading -> NEVER load a .pkl from an
# untrusted source. For untrusted/portable models prefer safe formats: ONNX, or
# safetensors (weights-only, no code execution) for neural nets.

# --- the anti-patterns --------------------------------------------------
# joblib.dump(model, "model.pkl")     # saved only the estimator -> serve gets raw input
# (overwriting the same path)         # no versioning -> can't roll back, can't tell which
```

### Impact

- **Correct serving:** the pipeline reproduces training-time preprocessing, so predictions
  on raw production input are valid (eliminates the "loads but predicts garbage" failure).
- **Safe upgrades & rollback:** versioned artifacts with recorded environments let you
  detect mismatches and revert to a known-good model instantly.
- **Traceability:** metadata links the artifact to its data/code/run (8.8), so a deployed
  model is auditable and debuggable.

### Pros & cons / when NOT to

**Serialize carefully when:** a trained model leaves the training process to be served,
shared, or stored — i.e. any model used beyond the session that made it.

**Watch out / when NOT to:**
- **Save the pipeline, not just the estimator** — the #1 serving bug is reloading a bare
  model and feeding it raw, unpreprocessed input (8.16).
- **Match the environment** — pickled models are version-sensitive; pin libraries (7.15)
  and record the version with the artifact so a mismatch fails loudly, not silently.
- **Version artifacts; never overwrite in place** — versioned filenames + metadata enable
  rollback and tell you which model is live (ties to 8.8/8.15).
- **`pickle`/`joblib` execute code on load — never unpickle untrusted files.** For
  portability/safety use ONNX or safetensors; treat a `.pkl` like executable code (Area 7
  trust boundaries).
- **For neural nets, save the state dict, not the whole pickled object** — weights are
  portable across code refactors; a pickled module breaks if your class definition
  changes (9.5).

### Where this shows up

- **Real work — model deployment:** every served model is a saved pipeline loaded by a
  service; getting serialization right is what makes offline training usable online.
- **Real work — model registries:** MLflow/SageMaker registries version artifacts with
  metadata and environment — the productionised form of this scenario (8.8/8.15).
- **Real work — neural net checkpoints:** `state_dict` save/load for resuming training and
  serving (9.5), and safetensors for safe weight sharing.
- **Pattern mapping (secondary):** it's serialization (Area 6's pickling) plus versioning
  and trust-boundary care (Area 7) applied to models — persist *everything needed to use
  the artifact correctly*, safely, and reversibly.
[↑ Back to top](#contents)

---

<a id="8.10"></a>
## 8.10 — "Scoring 10 million rows one at a time takes all night" → batch inference

### The situation

You need predictions for 10 million records. You loop and predict one row at a time:

```python
preds = []
for row in records:                    # 10,000,000 iterations
    preds.append(model.predict([row])[0])   # one tiny predict() call PER row
```

It crawls. Each `model.predict([row])` has fixed Python/framework **overhead** — input
validation, array setup, a function call into the model — that dwarfs the microseconds of
actual maths for one row. Multiplied by 10 million, that overhead *is* the runtime.

### What's really going on

ML models — especially vectorised ones (NumPy-backed sklearn, neural nets) — are built to
score **many rows at once** in a single call. A one-row-at-a-time loop pays the per-call
overhead 10 million times and forfeits the **vectorisation** (6.10) that makes the maths
fast: passing a whole array lets the library do the work in optimised C/BLAS (or one GPU
forward pass) over all rows together.

The fix is **batch inference**: predict on arrays/chunks of rows, not single rows.
`model.predict(X_array)` over 10,000 rows is one call doing 10,000 predictions in a tight
vectorised loop — overhead paid once per batch, not per row. For data bigger than memory,
process in chunks (1.2/6.5); for very large or latency-sensitive workloads, parallelise
the batches across cores (6.2) or run them on a GPU.

> **Batch inference** = running predictions on many rows per call (a 2-D array / chunk)
> rather than one row at a time, to amortise per-call overhead and exploit vectorisation
> (6.10). It's the inference cousin of batching API calls (5.14) and the opposite of the
> row-by-row Python loop that kills throughput (2.12).

### The move

Predict on whole arrays; for huge data, stream in chunks:

```python
# the whole array at once (if it fits in memory):
preds = model.predict(X)               # ONE vectorised call -> all 10M predictions

# bigger than memory: chunk it (1.2 / 6.5)
from itertools import batched
for chunk in batched(records, 10_000):           # 10k rows per predict() call
    write(model.predict(np.array(chunk)))
```

### Why it works

`model.predict(X)` hands the model a 2-D array and lets it score every row inside one
vectorised routine — the per-call overhead is paid once instead of 10 million times, and
the maths runs in compiled C/BLAS (or a single GPU pass) over the whole array, which is
where the real speed comes from (6.10). Chunking keeps memory bounded (you hold one batch,
not all 10M, 1.2) while still getting near-full batch efficiency, so the same approach
scales to data larger than RAM. Batch size becomes a tunable knob: bigger batches amortise
overhead better but use more memory (and on a GPU, must fit in VRAM, 9.3).

### The code, every line explained

```python
import numpy as np
from itertools import batched

# --- SLOW: one row per call -> overhead x 10M ---------------------------
preds = [model.predict([row])[0] for row in records]   # 10M tiny calls; mostly overhead

# --- FAST: whole array in one vectorised call ---------------------------
X = np.array(records)                  # shape (10_000_000, n_features)
preds = model.predict(X)               # ONE call; vectorised over all rows (6.10)

# --- bigger than memory: chunked batch inference ------------------------
def batch_predict(records, batch_size=10_000):
    for chunk in batched(records, batch_size):     # (1.12) groups rows into batches
        X = np.array(chunk)
        yield from model.predict(X)                 # stream predictions (1.2), O(1) memory
for pred in batch_predict(records):
    write(pred)

# --- parallel batch inference across cores (CPU model) ------------------
from concurrent.futures import ProcessPoolExecutor
chunks = [np.array(c) for c in batched(records, 50_000)]
with ProcessPoolExecutor() as pool:                # (6.2) load model per worker (6.11)
    for preds in pool.map(score_chunk, chunks):    # batches scored on different cores
        write(preds)

# --- GPU / neural-net batching (Area 9) ---------------------------------
# model.eval()                          # inference mode (no dropout) (9.7)
# with torch.no_grad():                 # don't build the gradient graph -> faster, less memory
#     for batch in dataloader:          # DataLoader yields batches (9.6)
#         preds = model(batch.to(device))   # one forward pass scores the whole batch
# Bigger batch -> better GPU utilisation, but must fit in VRAM (9.3).

# --- choosing batch size ------------------------------------------------
# bigger = less overhead, better hardware use — until it doesn't fit in RAM/VRAM.
# Start ~1k–10k (CPU) or as large as VRAM allows (GPU); tune empirically.
```

### Impact

- **Order-of-magnitude speed-up:** amortising per-call overhead and using vectorised/GPU
  math turns an all-night row-by-row job into minutes — often 10–100×.
- **Scales to any size:** chunked batch inference holds memory flat (1.2), so 10M or 10B
  rows process in a constant footprint.
- **Hardware utilisation:** large batches keep CPU SIMD/BLAS or the GPU busy, which is
  where modern models get their throughput.

### Pros & cons / when NOT to

**Use batch inference when:** scoring many rows offline — bulk predictions, nightly
scoring, embedding/featurising a corpus, evaluating on a large test set.

**Watch out / when NOT to:**
- **Online/low-latency serving is different.** A live request needs *one* prediction
  *now*; you can't always wait to fill a batch. There, the trade-off is latency vs
  throughput — some servers do *dynamic batching* (briefly grouping concurrent requests),
  but a single real-time prediction is legitimately one-at-a-time.
- **Batch size is bounded by memory/VRAM** — too large OOMs (9.3 on GPU). Tune it;
  bigger isn't always feasible.
- **Chunk data bigger than RAM** (1.2/6.5) — don't `np.array(all_10M_rows)` if it won't
  fit; stream batches.
- **Preprocess in batch too** — apply the pipeline's transforms (8.1) to the whole array,
  not per row, or you reintroduce the overhead you removed.
- **Order/identity** — when streaming/parallel batches, keep predictions aligned to their
  input ids (6.9), or you'll mislabel results.

### Where this shows up

- **Real work — offline scoring jobs:** nightly "score every customer/transaction" runs —
  batch inference is the standard, often combined with multiprocessing (6.2) or a GPU.
- **Real work — embedding a corpus:** running an embedding model over millions of texts in
  batches (5.14/9.x) for a vector store.
- **Real work — model evaluation:** predicting on a large test/validation set in one or a
  few vectorised calls rather than looping.
- **Pattern mapping (secondary):** it's vectorisation (6.10/2.12) + batching (5.14) +
  chunked streaming (1.2/6.5) applied to model prediction — process many items per call
  to amortise fixed cost.
[↑ Back to top](#contents)

---

<a id="8.11"></a>
## 8.11 — "My loss became NaN and the whole model is ruined" → numerical stability

### The situation

Training is going fine, then the loss prints `nan` and every prediction afterwards is
`nan` too — the model is dead:

```python
# a hand-written cross-entropy loss:
loss = -(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()
# when the model outputs p = 0.0 (or exactly 1.0), np.log(0) = -inf -> loss = nan
# OR a feature normalisation:
z = (x - x.mean()) / x.std()          # if x.std() == 0 (constant column) -> divide by 0 -> nan/inf
```

Once a `nan` ("not a number") or `inf` (infinity) appears, it **propagates**: any
arithmetic involving it yields `nan`, so one bad value silently poisons gradients,
weights, and every subsequent output. The model doesn't error — it just quietly turns to
garbage.

### What's really going on

Computers represent numbers with **finite-precision floating point**, and certain
operations produce the special values `inf` (overflow / divide-by-zero) and `nan`
(undefined results like `log(0)`, `0/0`, `inf - inf`). These then **contaminate
everything** they touch — `nan + anything = nan` — so a single unstable operation can
wreck an entire training run. Common culprits: `log(0)`, division by a zero/near-zero
denominator, `exp()` of a large number (overflow), and subtracting nearly-equal large
numbers (catastrophic cancellation).

**Numerical stability** means writing computations so they avoid these danger zones:

- **Clamp/epsilon**: never `log(p)` directly — use `log(p + ε)` or clip `p` into
  `[ε, 1−ε]`; guard divisions with a small `ε` in the denominator.
- **Use stable library implementations**: framework losses (e.g. `BCEWithLogitsLoss`,
  `log_softmax`) are written to be numerically stable — don't hand-roll them.
- **Detect early**: check for `nan`/`inf` in inputs and gradients so you catch the source,
  not just the downstream wreckage.

> **Numerical stability** = arranging floating-point computations to avoid `inf`/`nan`
> (from `log(0)`, divide-by-zero, overflow) and precision loss. `nan` propagates through
> all arithmetic, so one unstable step silently corrupts the whole result — prevention
> (epsilons, stable library functions) beats debugging after the fact.

### The move

Guard danger-zone operations with an epsilon, prefer stable library implementations, and
detect `nan`/`inf` at the source:

```python
EPS = 1e-7
loss = -(y * np.log(p + EPS) + (1 - y) * np.log(1 - p + EPS)).mean()  # no log(0)
z = (x - x.mean()) / (x.std() + EPS)                                  # no divide-by-zero
```

### Why it works

Adding a tiny `EPS` keeps arguments out of the undefined regions: `log(p + EPS)` is finite
even when `p = 0`, and `/ (std + EPS)` can't divide by zero on a constant column — so no
`inf`/`nan` is created to propagate. Framework loss functions go further: `log_softmax`
and `BCEWithLogitsLoss` combine the exp/log steps using identities (like the
log-sum-exp trick) that stay stable even for extreme inputs, which a naive
`log(softmax(x))` does not — that's why you use the library version rather than composing
it yourself. And checking for `nan`/`inf` on inputs/gradients catches the *first* bad
value, so you fix the cause (a constant feature, an exploding gradient, 9.4) instead of
chasing a model that's already all `nan`.

### The code, every line explained

```python
import numpy as np

# --- guard log and division with an epsilon -----------------------------
EPS = 1e-7
loss = -(y * np.log(p + EPS) + (1 - y) * np.log(1 - p + EPS)).mean()   # never log(0)
# better: clip p into a safe range so it's bounded on BOTH ends:
p = np.clip(p, EPS, 1 - EPS)                          # now log(p) and log(1-p) are finite
z = (x - x.mean()) / (x.std() + EPS)                  # constant column -> std 0 -> guarded

# --- prefer STABLE library implementations (don't hand-roll) ------------
# Unstable: log(softmax(x)) — softmax can underflow to 0, then log(0) = -inf
# Stable:   log_softmax(x)  — combined op uses the log-sum-exp trick internally
# Unstable: BCE on sigmoid(logits)   Stable: BCEWithLogitsLoss(logits, y) (PyTorch)
# These library losses are written for numerical stability — use them.

# --- detect nan/inf at the SOURCE, not after it spreads -----------------
assert np.isfinite(x).all(), "non-finite values in input features"     # catch bad inputs
if not np.isfinite(loss):
    raise FloatingPointError("loss became non-finite — check inputs/lr/gradients")
# in PyTorch: torch.isnan(t).any(), or torch.autograd.set_detect_anomaly(True) to find
# the exact op that produced a nan in the backward pass.

# --- make numpy RAISE on the operation that creates nan/inf -------------
np.seterr(divide="raise", invalid="raise")   # turns silent nan/inf into a loud exception
# now `1/0` or `log(-1)` raises AT THE SOURCE line, instead of propagating silently (7.2/7.3)

# --- common causes + fixes (quick map) ----------------------------------
# loss = nan        -> log(0)/div-by-0 (add EPS); learning rate too high (lower it, 9.4)
# inf               -> exp() overflow (subtract max before exp; use stable softmax)
# gradients nan     -> exploding gradients (gradient clipping, 9.4)
# normalisation nan -> constant feature, std=0 (EPS in denominator, or drop the column)
```

### Impact

- **Training survives:** guarded operations don't emit `nan`/`inf`, so a single edge
  value (a zero probability, a constant column) can't silently destroy the whole run.
- **Bugs caught at the source:** `np.seterr`/finite-checks turn silent contamination into
  a loud failure at the exact operation (7.2/7.3), so you fix the cause fast.
- **Correct results:** stable library losses give accurate values across the full input
  range, where naive hand-rolled versions quietly lose precision or blow up.

### Pros & cons / when NOT to

**Mind numerical stability when:** writing math directly — custom losses/metrics,
normalisation, probability calculations, anything with `log`, `exp`, or division.

**Watch out / when NOT to:**
- **Don't hand-roll losses/softmax** when a stable library version exists
  (`log_softmax`, `BCEWithLogitsLoss`, `logsumexp`) — they're written specifically to
  avoid these traps.
- **Guard both ends.** `log(p + EPS)` fixes `p=0` but not `p=1` in `log(1-p)`; clip into
  `[EPS, 1-EPS]` to cover both.
- **`nan` propagates silently** — turn on `np.seterr(...)`/finite-asserts during
  development so it fails loudly (7.2) at the source instead of surfacing as all-`nan`
  predictions later.
- **Epsilon size matters** — too small doesn't help precision; too large biases the
  result. `1e-7`/`1e-8` are typical for float32; match it to your dtype.
- **Distinguish "data has NaNs" from "math made NaNs"** — missing-value NaNs in inputs
  are a data problem (handle with fillna/dropna, 3.23) *before* the math; this scenario
  is about computations *creating* non-finite values.

### Where this shows up

- **Real work — custom losses/metrics:** any hand-written log-likelihood, cross-entropy,
  or ratio metric needs epsilon guards or a stable library equivalent.
- **Real work — feature normalisation:** constant or near-constant columns produce
  divide-by-zero in standardisation (8.3) — guard with EPS or drop them (3.12).
- **Real work — neural net training:** `nan` loss from a too-high learning rate or
  exploding gradients is a daily DL debugging task (9.4), fixed with stable losses,
  clipping, and lower LR.
- **Pattern mapping (secondary):** no DSA analogue; it's the floating-point-correctness
  discipline — arrange computations to avoid undefined/overflow regions, akin to handling
  edge cases (empty/zero/boundary) before they break an algorithm.
[↑ Back to top](#contents)

---

<a id="8.12"></a>
## 8.12 — "I imputed missing values before splitting and the test set cheated" → fit transforms on train only

### The situation

You handle missing values and scaling before modelling — sensibly, you think — by
processing the full dataset first, *then* splitting:

```python
df["income"] = df["income"].fillna(df["income"].median())   # median over ALL rows
X = StandardScaler().fit_transform(df[features])             # mean/std over ALL rows
X_train, X_test, y_train, y_test = train_test_split(X, y)    # split AFTER transforming
```

The median used to fill missing income, and the mean/std used to scale, were computed
over the **entire** dataset — *including the rows that become the test set*. The test set
has influenced the transforms applied to training, so your evaluation is contaminated.
This is the same leakage as 8.1, but it's worth its own scenario because **imputation,
encoding, feature selection, and any "learn a statistic from data" step** all leak the
same way, and the fix — a fitted pipeline — is the daily mechanic.

### What's really going on

Any transform that **learns a parameter from data** — the median for imputation, the
mean/std for scaling, category frequencies for encoding, which columns survive feature
selection — must learn it from the **training set only**. Computing it over all rows lets
information from the test set (and, in production, the future) flow into how training data
is prepared, inflating the test score (data leakage, 8.1).

The reliable mechanic is a scikit-learn **`Pipeline`**: it chains transforms + model into
one object whose `.fit()` learns every transform's parameters from the data it's given,
and whose `.transform()`/`.predict()` *applies* those learned parameters without
re-learning. Pass the *pipeline* to `train_test_split`-derived `.fit(X_train)` (or to
cross-validation, 8.6), and each transform automatically fits on train (or the fold's
train portion) only — leakage becomes impossible by construction.

> The rule: **`fit` on train, `transform` test.** A `Pipeline` enforces this for the whole
> chain — `.fit()` learns from training data, then the *same* learned parameters transform
> any new data. Doing transforms manually before the split is the classic leak; the
> pipeline is the fix you use every day.

### The move

Put every data-learned transform inside a `Pipeline`, split first, then fit the pipeline
on train:

```python
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

pipe = Pipeline([
    ("impute", SimpleImputer(strategy="median")),   # median learned from TRAIN only
    ("scale", StandardScaler()),                      # mean/std learned from TRAIN only
    ("model", model),
])
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)  # split FIRST
pipe.fit(X_train, y_train)                                                   # fit on train
pipe.score(X_test, y_test)                                                   # honest score
```

### Why it works

When you call `pipe.fit(X_train, ...)`, the imputer computes its median and the scaler its
mean/std **from the training rows only**, and stores them. When you call `pipe.score(
X_test, ...)`, those *stored* training parameters are *applied* to the test rows — the
imputer and scaler do **not** re-learn from test data. So the test set never influences how
training data was prepared, and its score honestly reflects unseen data. Used inside
`cross_val_score`/`GridSearchCV` (8.6), the pipeline re-fits its transforms on each fold's
training portion, keeping every fold leakage-free — something you cannot achieve by
transforming `X` once up front.

### The code, every line explained

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split, cross_val_score

# --- WRONG: learn transform parameters from ALL rows -> leakage ---------
df["income"] = df["income"].fillna(df["income"].median())   # median includes test rows
X = StandardScaler().fit_transform(df[num_cols])             # mean/std include test rows
Xtr, Xte, ytr, yte = train_test_split(X, y)                  # too late — already leaked

# --- RIGHT: split first, transforms fit inside the pipeline -------------
num = Pipeline([("impute", SimpleImputer(strategy="median")),  # fit on train fold only
                ("scale", StandardScaler())])
cat = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore"))])   # (8.2)
prep = ColumnTransformer([("num", num, num_cols), ("cat", cat, cat_cols)])
pipe = Pipeline([("prep", prep), ("model", model)])

Xtr, Xte, ytr, yte = train_test_split(X, y, random_state=42)  # SPLIT before any fitting
pipe.fit(Xtr, ytr)            # every transform learns its params from TRAIN only
print(pipe.score(Xte, yte))   # transforms APPLY train params to test -> honest

# --- and leakage-free cross-validation comes for free -------------------
scores = cross_val_score(pipe, X, y, cv=5)   # each fold re-fits transforms on its train
# (Transforming X once before cross_val_score would leak across folds — 8.1/8.6.)

# --- the same artifact serves correctly (8.9/8.16) ----------------------
joblib.dump(pipe, "model.pkl")   # imputer+scaler+encoder+model travel together ->
                                 # production applies identical transforms to raw input
```

### Impact

- **Honest evaluation:** transforms never see test data, so the score predicts production
  performance — the concrete daily mechanic behind avoiding leakage (8.1).
- **Leakage-free CV & tuning:** passing the pipeline keeps every fold and every
  hyperparameter trial clean (8.6), so comparisons are trustworthy.
- **Train/serve consistency:** the fitted pipeline applies the *same* learned transforms
  at serving time, eliminating skew (8.16) and making the saved artifact correct (8.9).

### Pros & cons / when NOT to

**Use a fitted pipeline when:** any preprocessing learns parameters from data —
imputation, scaling, encoding, feature selection, dimensionality reduction. I.e. almost
every real model.

**Watch out / when NOT to:**
- **The leak is silent and looks like success** — a too-good score is the symptom (8.1).
  If transforms run before the split, assume leakage until proven otherwise.
- **Every data-learned step belongs in the pipeline**, not just scaling — imputers,
  encoders, feature selectors, PCA all leak if fit on the full set. `ColumnTransformer`
  handles mixed column types in one pipeline.
- **Stateless transforms are exempt** — operations that don't learn from data (e.g.
  `log1p`, a fixed unit conversion) can be applied anytime; only *fitted* transforms leak.
- **Target transforms need care** — transforming `y` (e.g. log-target) must be inverted
  for predictions and kept out of feature leakage; use `TransformedTargetRegressor`.
- **Pandas-then-sklearn mismatch** — doing `fillna` in pandas on the whole frame *before*
  the split is the most common accidental leak; move it into the pipeline.

### Where this shows up

- **Real work — every tabular ML workflow:** the `Pipeline`/`ColumnTransformer` pattern is
  the standard, correct way to preprocess — it's how 8.1's "no leakage" rule is actually
  implemented in code.
- **Real work — cross-validation & hyperparameter search:** pipelines are what make
  `cross_val_score`/`GridSearchCV` leakage-free (8.6).
- **Real work — deployment:** the fitted pipeline is the deployable artifact (8.9), so
  serving preprocesses raw input exactly as training did (8.16).
- **Pattern mapping (secondary):** no DSA analogue; it's the fit-on-train/transform-test
  discipline — the operational core of evaluation integrity (8.1) and reproducible
  pipelines (8.8).
[↑ Back to top](#contents)

---

<a id="8.13"></a>
## 8.13 — "Loading the whole training set into memory OOMs" → data loaders & batching

### The situation

Your training set is 200 GB of images (or rows). You try to load it all, then train:

```python
X = load_all_images(paths)        # 200 GB -> MemoryError before training even starts
y = load_all_labels()
model.fit(X, y)                   # never reached
```

Even if it fit, you'd want to feed the model in **batches** (8.10) and **shuffle** the
order each epoch — none of which "load everything then fit" supports. You need a way to
stream training examples in shuffled, model-sized batches without holding the full dataset
in memory.

### What's really going on

Training doesn't need the whole dataset in memory at once — it processes **one batch at a
time** (8.10). So you want a component that **lazily** loads, transforms, shuffles, and
batches examples on demand, ideally **prefetching** the next batch (often on background
workers) while the model trains on the current one. That component is a **data loader**.

This is the ML-specific application of generators/streaming (1.2) and chunking (6.5):
instead of materialising 200 GB, you yield batches as the trainer asks for them. Every
framework provides one — PyTorch's `Dataset` + `DataLoader`, TensorFlow's `tf.data` — and
for classical sklearn there's `partial_fit` (incremental learning) for models that
support it.

> A **data loader** = an object that yields training data in **batches**, loading each
> example **lazily** from disk/stream (so the full dataset never sits in RAM), with
> **shuffling** (random order per epoch, important for training, 8.7) and often
> **parallel prefetching** (background workers prepare the next batch to keep the
> GPU/CPU fed). A **`Dataset`** says *how to get one example*; the **`DataLoader`** wraps
> it to batch, shuffle, and prefetch.

### The move

Define a `Dataset` that loads one example lazily, wrap it in a `DataLoader` that batches,
shuffles, and prefetches:

```python
from torch.utils.data import Dataset, DataLoader

class ImageDataset(Dataset):
    def __init__(self, paths, labels): self.paths, self.labels = paths, labels
    def __len__(self):  return len(self.paths)            # how many examples (1.14)
    def __getitem__(self, i):                              # load ONE example, on demand
        return transform(load_image(self.paths[i])), self.labels[i]

loader = DataLoader(ImageDataset(paths, labels),
                    batch_size=32, shuffle=True, num_workers=4)   # batch + shuffle + prefetch
```

### Why it works

`__getitem__` loads a *single* example only when asked, so the 200 GB is never all in
memory — the `DataLoader` pulls 32 indices, gets their examples, stacks them into one
batch, and hands it to the trainer; the rest stay on disk (lazy, 1.2). `shuffle=True`
randomises order each epoch (important so the model doesn't learn the data's ordering, and
for stable training, 8.7). `num_workers=4` runs the loading/transforming on background
processes (6.2) that **prefetch** the next batches while the model trains on the current
one — so the expensive GPU isn't left idle waiting for disk I/O (a 5.7-style pipeline of
load → train). The `Dataset`/`DataLoader` split (1.14's `__len__`/`__getitem__` dunders)
cleanly separates "how to fetch one item" from "how to batch/shuffle/prefetch them."

### The code, every line explained

```python
from torch.utils.data import Dataset, DataLoader

# --- Dataset: defines how to get ONE example (lazy) ---------------------
class ImageDataset(Dataset):
    def __init__(self, paths, labels):
        self.paths, self.labels = paths, labels   # store references, NOT the data itself
    def __len__(self):
        return len(self.paths)                     # total examples (DataLoader needs this)
    def __getitem__(self, i):                      # called per example, on demand
        img = transform(load_image(self.paths[i])) # load+preprocess ONE image now
        return img, self.labels[i]                 # (features, label) for index i

# --- DataLoader: batches + shuffles + prefetches ------------------------
loader = DataLoader(
    ImageDataset(paths, labels),
    batch_size=32,        # examples per batch (8.10) — bounded by memory/VRAM (9.3)
    shuffle=True,         # reshuffle order each epoch (don't shuffle the VAL/TEST loader)
    num_workers=4,        # background processes prefetch batches -> GPU stays fed
    pin_memory=True,      # faster CPU->GPU transfer (GPU training)
)

# --- the training loop consumes batches ---------------------------------
for epoch in range(epochs):
    for X_batch, y_batch in loader:        # each iteration = ONE batch, loaded lazily
        loss = train_step(model, X_batch, y_batch)   # only 32 examples in memory at a time

# --- tf.data equivalent (TensorFlow) ------------------------------------
# ds = (tf.data.Dataset.from_tensor_slices((paths, labels))
#         .map(load_and_preprocess, num_parallel_calls=tf.data.AUTOTUNE)  # parallel load
#         .shuffle(1000).batch(32).prefetch(tf.data.AUTOTUNE))            # shuffle+batch+prefetch

# --- classical sklearn: incremental learning for out-of-core ------------
# Models with partial_fit (SGDClassifier, etc.) can train on chunks (6.5) without
# loading all data: for chunk in read_chunks(...): model.partial_fit(Xc, yc, classes=...)

# --- common pitfalls -----------------------------------------------------
# - shuffle=True on TRAIN only; NEVER shuffle the test loader (you'd scramble eval order)
# - num_workers too high -> CPU/memory contention; too low -> GPU starves waiting on data
# - heavy per-item work in __getitem__ is fine (it's parallelised), but keep it deterministic
```

### Impact

- **Trains on data bigger than RAM:** lazy per-example loading means dataset size is bound
  by disk, not memory — 200 GB (or more) trains in a small footprint (1.2/6.5).
- **Keeps expensive hardware busy:** parallel prefetching overlaps data loading with
  compute, so the GPU isn't idling on disk I/O (5.7-style pipeline) — often a large
  throughput win.
- **Correct training dynamics:** per-epoch shuffling and proper batching (8.10) give the
  model well-formed, randomised input, which matters for convergence.

### Pros & cons / when NOT to

**Use a data loader when:** training on data too large for memory, or whenever you need
batching + shuffling + parallel loading — essentially all non-trivial DL training, and
out-of-core classical ML.

**Watch out / when NOT to:**
- **Shuffle train, not test.** `shuffle=True` belongs on the training loader only;
  shuffling the eval loader scrambles the order you align predictions to (and is
  pointless).
- **Tune `num_workers`.** Too few starves the GPU (it waits on data); too many causes
  CPU/RAM contention. Match to cores and the cost of `__getitem__` (6.x).
- **`__getitem__` should be deterministic given an index** (apart from intended
  augmentation randomness, which should be seeded, 8.7) — hidden state across calls causes
  subtle, irreproducible bugs.
- **Small datasets that fit in memory don't need this** — loading once and indexing arrays
  is simpler; data loaders earn their keep at scale or when streaming.
- **Worker processes re-import your module** (6.2) — keep dataset code importable and avoid
  non-picklable state in the `Dataset`.

### Where this shows up

- **Real work — deep learning training:** `Dataset`+`DataLoader` (PyTorch) / `tf.data` is
  the standard input pipeline for training on large image/text/audio datasets (Area 9).
- **Real work — out-of-core classical ML:** `partial_fit` over chunks (6.5) for datasets
  too big for `model.fit(X, y)`.
- **Real work — keeping GPUs utilised:** prefetching + parallel loading to ensure
  expensive accelerators aren't bottlenecked on disk (ties to 5.7 pipelines, 9.6).
- **Pattern mapping (secondary):** it's lazy streaming (1.2) + chunking (6.5) + a
  producer/consumer prefetch pipeline (5.6/5.7), packaged for ML training — the
  `__len__`/`__getitem__` interface is the container dunders from 1.14.
[↑ Back to top](#contents)

---

<a id="8.14"></a>
## 8.14 — "Model B scored 0.2% higher, so we shipped it — was that real?" → comparing models fairly

### The situation

You compare two models and pick the "winner" — but the comparison is subtly unfair, so the
decision might be noise:

```python
# Model A on one split:
A = RandomForest().fit(X_train_v1, y_train).score(X_test_v1, y_test)   # 0.851
# Model B on a DIFFERENT split (and you tuned B on the test set while iterating):
B = XGBoost().fit(X_train_v2, y_train).score(X_test_v2, y_test)        # 0.853
# ship B because 0.853 > 0.851?  -> the 0.2% could be split luck, or test-set overfitting
```

Three problems hide here: A and B were evaluated on **different splits** (8.6), B was
**tuned by repeatedly checking the test set** (so the test set leaked into model
selection), and **0.2% may be within noise** — smaller than the variation between splits.
The "winner" might not actually be better.

### What's really going on

A fair comparison requires holding **everything except the model constant** and accounting
for **noise**. Three disciplines make a comparison trustworthy:

1. **Same data, same evaluation.** Compare models on the *same* CV folds / the *same*
   held-out set, with the *same* metric (8.5) and preprocessing — otherwise you're
   comparing splits, not models.
2. **A held-out test set used once.** If you tune and select against the test set
   repeatedly, you **overfit to it** — the test score stops predicting reality. Keep a
   final test set untouched until the very end; do all selection/tuning on
   train/validation (or CV, 8.6).
3. **Account for variance.** A difference smaller than the score's std across folds/seeds
   (8.6/8.7) is probably noise. Compare mean±std, and for important calls use a
   significance test or, ultimately, an A/B test on the real metric.

> **Fair model comparison** = same data + same metric + same untouched test set + noise
> awareness. The traps: different splits, tuning on the test set (selection leakage), and
> over-reading a difference that's within run-to-run variance. The gold standard for "does
> it actually help the product?" is an **A/B test** on the live KPI, not an offline delta.

### The move

Evaluate every candidate on the *same* CV folds with the *same* metric, compare mean±std,
and reserve a final test set used exactly once:

```python
from sklearn.model_selection import cross_val_score, StratifiedKFold

cv = StratifiedKFold(5, shuffle=True, random_state=42)        # SAME folds for all models
a = cross_val_score(pipe_A, X_dev, y_dev, cv=cv, scoring="f1")  # same metric, same data
b = cross_val_score(pipe_B, X_dev, y_dev, cv=cv, scoring="f1")
print(f"A {a.mean():.3f}±{a.std():.3f}  B {b.mean():.3f}±{b.std():.3f}")  # noise-aware
```

### Why it works

Fixing the same `cv` object (and seed, 8.7) means both models are scored on **identical**
fold assignments, so the comparison reflects the *model*, not which rows landed where. The
same `scoring` and pipelines hold the metric and preprocessing constant. Reporting
mean±std makes noise visible: if B's mean is within A's std, the "win" is likely luck, not
a real improvement. And doing all of this on a **development** set (`X_dev`) while a
separate **test** set stays untouched until the final decision prevents selection leakage —
the test score remains an honest, never-optimised-against estimate. For a true
product-level verdict, an online A/B test measures the real KPI, which offline metrics only
approximate (8.5).

### The code, every line explained

```python
from sklearn.model_selection import cross_val_score, StratifiedKFold
from scipy.stats import ttest_rel
import numpy as np

# --- compare on the SAME folds, SAME metric -----------------------------
cv = StratifiedKFold(5, shuffle=True, random_state=42)   # fixed -> identical folds for all
a = cross_val_score(pipe_A, X_dev, y_dev, cv=cv, scoring="f1")   # pipelines (8.12) = no leak
b = cross_val_score(pipe_B, X_dev, y_dev, cv=cv, scoring="f1")
print(f"A: {a.mean():.4f} ± {a.std():.4f}")
print(f"B: {b.mean():.4f} ± {b.std():.4f}")

# --- is the difference within NOISE? ------------------------------------
if abs(a.mean() - b.mean()) < max(a.std(), b.std()):
    print("difference is within run-to-run noise — NOT a clear win")
# paired t-test across folds (same folds -> paired) for a significance signal:
t, p = ttest_rel(a, b)
print(f"paired t-test p={p:.3f}")        # p > 0.05 -> can't conclude B differs from A

# --- the held-out test set: used ONCE, at the very end ------------------
# Split THREE ways up front:
#   train  -> fit models
#   dev/val (or CV on train) -> ALL model selection & hyperparameter tuning
#   test   -> LOCKED until the final decision; touch it once to report final performance
# Repeatedly checking `test` while iterating = overfitting to it (selection leakage, 8.1).

# --- account for fairness beyond the score ------------------------------
# also compare: inference latency, memory, training cost, interpretability, maintenance.
# A 0.2% F1 gain from a 10x-slower, harder-to-debug model is often NOT worth shipping.

# --- the ultimate test: online A/B --------------------------------------
# Offline metric improvement ≠ product improvement (8.5/Goodhart). For decisions that
# matter, ship B to a fraction of traffic and measure the REAL KPI vs A (10.12 rollout).
```

### Impact

- **Decisions reflect reality:** you ship a model because it's *genuinely* better, not
  because it won a split or you overfit to the test set — avoiding regressions disguised
  as wins.
- **Noise-aware judgement:** mean±std (and a significance test) stop you from chasing
  fractional differences that won't reproduce in production.
- **Honest final estimate:** an untouched test set (or A/B test) gives a number you can
  actually trust and report.

### Pros & cons / when NOT to

**Compare fairly when:** choosing between models, features, or hyperparameters — any "is
this better?" decision, which is most of modelling.

**Watch out / when NOT to:**
- **Don't compare across different splits** — same folds/test set, same metric (8.5), same
  preprocessing, or you're measuring split luck, not the model.
- **Never tune against the test set.** Repeatedly peeking overfits selection to it; keep a
  locked test set and do all iteration on dev/CV (8.6) — this is selection leakage (8.1).
- **A tiny delta within std is not a win** — report mean±std and, for important calls, a
  significance test; reproduce across seeds (8.7) before believing it.
- **Offline ≠ online** — a better offline metric may not improve the product (8.5,
  Goodhart). For high-stakes decisions, validate with an A/B test (10.12).
- **Weigh non-accuracy costs** — latency, memory, training cost, interpretability,
  maintainability. The "best" score isn't automatically the best choice to ship.

### Where this shows up

- **Real work — model/feature selection:** every "A vs B" decision in a project should use
  shared folds, mean±std, and a locked test set — this is how 8.6 is applied to *choices*.
- **Real work — hyperparameter tuning:** `GridSearchCV` compares candidates on the same CV
  folds; the final pick is then confirmed on the untouched test set.
- **Real work — shipping decisions:** offline comparison to shortlist, then an online A/B
  test on the real KPI to make the call (10.12).
- **Pattern mapping (secondary):** no DSA analogue; it's controlled experimentation —
  hold everything constant but the variable under test, and separate signal from noise —
  the evaluation-rigor capstone of 8.1/8.5/8.6/8.7.
[↑ Back to top](#contents)

---

<a id="8.15"></a>
## 8.15 — "Which hyperparameters gave last Tuesday's best result?" → experiment tracking

### The situation

You run dozens of experiments — different features, models, hyperparameters — tweaking
code and noting scores in your head or a scratch file. Then you need last week's best run
and can't reconstruct it:

```python
# Monday:    n_estimators=200, max_depth=8  -> f1 0.84   (noted... somewhere?)
# Tuesday:   added a feature, lr=0.05        -> f1 0.87   (best! but what was the EXACT config?)
# Wednesday: changed code, didn't write it down -> 0.85
# Friday: "use Tuesday's model" -> which features? which params? which data? which commit?
```

Each run's inputs (params, features, data version, code) and outputs (metrics, the model
artifact) lived only in your memory or transient cell output. You can't compare runs
systematically, can't reproduce the best one (8.8), and can't tell *why* one beat another.

### What's really going on

ML is **empirical** — you try many configurations and keep the best — which only works if
every run is **recorded**: its parameters, metrics, the data/code version, and the
resulting artifact, all linked. Without that, experiments are unrepeatable and
incomparable, and "the best model" is whatever you happen to remember.

**Experiment tracking** logs each run to a persistent store so you can compare, sort,
filter, and reproduce them. Tools like **MLflow**, **Weights & Biases**, or even a
disciplined CSV/DB capture: **params** (hyperparameters, feature set, data version),
**metrics** (your chosen metric, 8.5, ideally CV mean±std, 8.6), and **artifacts** (the
saved pipeline, 8.9; plots; the git commit, 8.8). It's the system of record that turns ad
hoc tinkering into a comparable, reproducible experiment history.

> **Experiment tracking** = automatically logging each run's inputs (params, data/code
> version) and outputs (metrics, artifacts) to a queryable store, so runs can be compared,
> the best reproduced (8.8), and decisions audited. It's the bookkeeping layer that makes
> empirical ML systematic instead of a memory game.

### The move

Log every run's params, metrics, and artifact to a tracker (MLflow shown):

```python
import mlflow
with mlflow.start_run():
    mlflow.log_params({"n_estimators": 200, "max_depth": 8,
                       "features": feature_set, "data_version": "2026-03-15",
                       "git_commit": git_commit()})        # inputs
    mlflow.log_metrics({"cv_f1_mean": scores.mean(), "cv_f1_std": scores.std()})  # outputs (8.6)
    mlflow.sklearn.log_model(pipe, "model")               # the artifact (8.9)
```

### Why it works

Each `start_run()` creates a persistent record tying that run's **params** to its
**metrics** and its **artifact** — so the tracker can later show all runs in a sortable
table, let you filter ("show runs with the new feature"), and identify the best by your
metric. Because the data version and git commit are logged alongside, the best run is
**reproducible** (8.8): you know exactly which data, code, and config produced it. The
logging is a few lines wrapped around training you already do, so the cost is tiny and the
payoff — comparable history, no lost results, auditable decisions — is large. Crucially,
the *model artifact* is stored *with* its metrics, so "use Tuesday's model" resolves to a
concrete, retrievable object, not a memory.

### The code, every line explained

```python
import mlflow

# --- log one run: inputs + outputs + artifact, all linked ---------------
with mlflow.start_run(run_name="rf_v3_newfeature"):
    params = {"n_estimators": 200, "max_depth": 8,
              "features": ",".join(feature_set),   # WHAT features (data lineage)
              "data_version": "2026-03-15",         # WHICH data (8.8)
              "git_commit": git_commit(), "seed": 42}  # WHICH code + determinism (8.7)
    mlflow.log_params(params)                       # the inputs that define the run

    scores = cross_val_score(pipe, X, y, cv=5, scoring="f1")  # honest eval (8.6)
    mlflow.log_metric("cv_f1_mean", scores.mean())  # the OUTCOME you compare on (8.5)
    mlflow.log_metric("cv_f1_std", scores.std())     # noise, for fair comparison (8.14)

    mlflow.sklearn.log_model(pipe, "model")          # the ARTIFACT (whole pipeline, 8.9)
    mlflow.log_artifact("confusion_matrix.png")       # any extra files (plots, reports)
# Later: query/sort runs by cv_f1_mean, see each one's exact params, load the best model.

# --- the lightweight version (no infra): append to a CSV/JSONL ----------
import json, datetime
def log_run(params, metrics):
    with open("runs.jsonl", "a") as f:               # append one JSON record per run (3.2)
        f.write(json.dumps({"ts": str(datetime.datetime.now()),  # (pass time in, 7.x)
                            **params, **metrics}) + "\n")
# Even this beats memory: you can later load runs.jsonl into pandas and sort/filter.

# --- what to log (the checklist) ----------------------------------------
# params : hyperparameters, FEATURE SET, data version, git commit, seed
# metrics: your chosen metric (8.5), as CV mean±std (8.6), + secondary metrics
# artifacts: the saved pipeline (8.9), plots, the run's config file
# -> enough to COMPARE runs and REPRODUCE (8.8) any of them.

# --- don't log secrets/PII ----------------------------------------------
# log params/metrics/paths, not raw data, credentials, or personal info (7.13/7.14).
```

### Impact

- **No lost results:** every run's config and score are recorded, so "last Tuesday's best"
  is a query, not a memory test.
- **Systematic comparison:** sort/filter runs by metric to see what actually helped —
  turning trial-and-error into a readable experiment history (supports fair comparison,
  8.14).
- **Reproducible & auditable:** params + data version + git commit + artifact mean the
  best run can be recreated (8.8) and its provenance explained.

### Pros & cons / when NOT to

**Track experiments when:** you run more than a handful of experiments, work on a team, or
any model might reach production — i.e. essentially all real ML projects.

**Watch out / when NOT to:**
- **Log enough to *reproduce*, not just the score.** A metric without its params, data
  version, and code commit (8.8) tells you a run was good but not how to recreate it.
- **Automate the logging.** Manual notes drift and get forgotten; wrap training in the
  tracker so every run is captured without discipline. The unlogged run is the one you'll
  need.
- **Don't log secrets/PII or huge raw data** — log params, metrics, paths/versions, and
  the artifact; keep credentials (7.14) and personal data out (7.13).
- **A heavyweight tracker is overkill for a quick one-off** — a CSV/JSONL append is fine
  to start; adopt MLflow/W&B when the experiment volume or team size warrants it.
- **Tracking ≠ reproducibility on its own** — it records *what* happened; you still need
  pinned environments (7.15) and seeds (8.7) for the recorded run to actually re-run
  identically (8.8).

### Where this shows up

- **Real work — model development:** the standard way teams run and compare dozens/hundreds
  of experiments (MLflow/W&B dashboards) instead of losing results in notebooks.
- **Real work — hyperparameter sweeps:** logging every trial's params+metrics so the sweep
  is analysable and the winner reproducible.
- **Real work — model governance:** the run record (params, data, code, metrics, artifact)
  is the audit trail for *how* a production model was chosen (8.8).
- **Pattern mapping (secondary):** no DSA analogue; it's the observability/bookkeeping
  practice (the experiment-level sibling of logging, 7.13) that makes empirical ML
  systematic and feeds reproducible pipelines (8.8).
[↑ Back to top](#contents)

---

<a id="8.16"></a>
## 8.16 — "Great offline scores, bad live predictions" → train/serve skew

### The situation

Your model evaluated brilliantly offline, but in production its predictions are worse —
even though the model file is correct:

```python
# TRAINING (in a notebook/pipeline):
df["age"] = df["age"].fillna(df["age"].median())     # filled with median 34
df["income"] = np.log1p(df["income"])                # log-transformed
X = scaler.fit_transform(df[features])
model.fit(X, y)

# SERVING (a separate API service, written weeks later by someone else):
features = {"age": req.age, "income": req.income}    # raw! no median fill, no log1p, no scaling
pred = model.predict([list(features.values())])      # model gets DIFFERENT inputs than it trained on
```

The serving code reimplemented preprocessing — and got it subtly different (forgot the
`log1p`, used a different median, skipped scaling). The model receives inputs in a
*different distribution* than it trained on, so it predicts poorly despite being a good
model.

### What's really going on

**Train/serve skew** is any difference between how features are computed at **training**
time versus **serving** time. The model learned a mapping from *training-time-preprocessed*
inputs to outputs; if serving feeds it differently-preprocessed inputs, that mapping no
longer applies. Causes: preprocessing reimplemented (and diverging) in two codebases,
different feature definitions, different data sources, or features that depend on
time/state that differ live.

The root fix is **share one preprocessing path** between train and serve — don't write it
twice. Save the *fitted pipeline* (8.9/8.12) so the exact transforms (medians, scalers,
encoders learned at training, 8.1) are *applied* at serving, not re-derived. Then the same
code computes features in both places, so skew is impossible by construction.

> **Train/serve skew** = features are computed differently at training vs serving, so the
> model sees a distribution it wasn't trained on and underperforms despite being correct.
> The fix: a single shared preprocessing artifact (the fitted `Pipeline`, 8.12) used in
> both — plus monitoring for *data drift* (the live data itself changing over time, a
> related but distinct problem).

### The move

Bake preprocessing into the saved pipeline so serving calls **one** object that transforms
raw input exactly as training did:

```python
# TRAIN: fit transforms + model as ONE pipeline, save it whole (8.9/8.12)
pipe = Pipeline([("prep", preprocessing), ("model", model)]).fit(X_train_raw, y_train)
joblib.dump(pipe, "model.pkl")

# SERVE: load the SAME pipeline; feed it RAW input — it preprocesses identically
pipe = joblib.load("model.pkl")
pred = pipe.predict(raw_input_df)        # median fill, log1p, scaling all applied for you
```

### Why it works

Because the imputer, transforms, and scaler are *inside* the fitted pipeline, serving
doesn't reimplement preprocessing — it calls `pipe.predict(raw)` and the pipeline applies
the **exact** learned parameters (the training median, the training scaler's mean/std, the
fitted encoder, 8.1/8.12) to raw input. There's only one preprocessing implementation, so
train and serve can't diverge. The model always receives inputs in the distribution it
trained on, so offline performance carries over to production. Skew from *reimplementation*
is eliminated; what remains to watch is genuine **data drift** (the world changing), which
you detect by monitoring live feature distributions against training.

### The code, every line explained

```python
from sklearn.pipeline import Pipeline
import joblib

# --- TRAIN: everything in one fitted pipeline ---------------------------
pipe = Pipeline([
    ("prep", preprocessing),     # imputers + log1p + scaler + encoders (8.12), fit on TRAIN
    ("model", model),
])
pipe.fit(X_train_raw, y_train)   # learns medians/means/encodings AND trains the model
joblib.dump(pipe, "model.pkl")   # the artifact carries preprocessing + model together (8.9)

# --- SERVE: one call, raw input, identical preprocessing ----------------
pipe = joblib.load("model.pkl")
def predict(raw_request: dict):
    df = pd.DataFrame([raw_request])      # raw features, same SHAPE/columns as training
    return pipe.predict(df)[0]            # pipeline applies the SAME transforms -> no skew
# No fillna/log1p/scale reimplemented here -> nothing to get subtly wrong.

# --- guard the input contract (boundary validation, 7.1) ----------------
EXPECTED = ["age", "income", "city"]      # the columns/order the pipeline expects
def predict_safe(raw):
    df = pd.DataFrame([raw])
    missing = set(EXPECTED) - set(df.columns)
    if missing:
        raise ValueError(f"missing features at serve: {missing}")   # fail loud (7.2)
    return pipe.predict(df[EXPECTED])[0]   # fix column ORDER too — a common skew source

# --- detect DATA DRIFT (distinct from skew): monitor live vs train ------
# Log serving feature stats and compare to training stats over time:
#   if live_mean_income drifts far from train_mean_income -> the WORLD changed, not the code.
#   Drift -> retrain on fresh data (8.8 reproducible pipeline makes this safe/cheap).

# --- the anti-pattern ---------------------------------------------------
# Two codebases each implementing preprocessing -> they WILL diverge over time.
# Save only the model (not the pipeline) -> serving must reimplement transforms -> skew.
```

### Impact

- **Offline performance transfers to production:** the model sees identically-prepared
  inputs live, so the good test score (achieved honestly via 8.1/8.6) actually holds in
  production.
- **Single source of truth for features:** one preprocessing implementation means no
  drift between two codebases — the most common cause of "great offline, bad online".
- **Safe retraining on drift:** with a reproducible pipeline (8.8) and monitoring, you can
  detect data drift and retrain on fresh data without reintroducing skew.

### Pros & cons / when NOT to

**Guard against train/serve skew when:** a model is deployed and serving predictions —
i.e. any model that leaves the notebook.

**Watch out / when NOT to:**
- **Never reimplement preprocessing at serve time** — save and reuse the fitted pipeline
  (8.9/8.12). Two implementations diverge; one can't.
- **Match the input contract exactly** — column names, order, and types at serve must
  match training. Validate at the boundary (7.1) and fail loud (7.2) on mismatch; a
  reordered column silently skews predictions.
- **Distinguish skew from drift.** Skew = *your code* differs train vs serve (fixable by
  sharing the pipeline). Drift = *the data* changes over time (fixable by monitoring +
  retraining). Both degrade live performance; the fixes differ.
- **Time/stateful features are skew-prone** — a feature like "avg spend last 30 days"
  computed differently in the batch training job vs the live service is a classic skew;
  define such features once, ideally in a feature store.
- **Monitor live performance**, don't assume — even with no skew, drift erodes models;
  track the live metric and feature distributions.

### Where this shows up

- **Real work — every deployed model:** sharing the fitted pipeline between training and a
  serving API is the standard defence; it's why 8.9/8.12 insist on saving the whole
  pipeline.
- **Real work — feature stores:** centralising feature definitions so batch (training) and
  online (serving) compute them identically — purpose-built skew prevention.
- **Real work — model monitoring/retraining:** detecting data drift in production and
  retraining via a reproducible pipeline (8.8) when live distributions move.
- **Pattern mapping (secondary):** no DSA analogue; it's the consistency principle —
  the same computation must run in both places — closing the loop from leakage-free
  training (8.1) through serialization (8.9) to correct serving.

[↑ Back to top](#contents)

