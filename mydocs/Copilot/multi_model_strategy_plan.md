# Multi-Model Strategy: Per-Node Model Routing for Chat API & Auto-Summarization

> **Status:** DRAFT — Proposal pending final review before implementation.
> **Author:** Pragyesh Mishra
> **Date:** 2026-03-24

## Why We Need This

Today, every LLM call in the copilot — whether it's a simple "translate this sentence" or a complex "diagnose this equipment failure" — goes through the **same GPT-4o model**. That's like sending every package via overnight express when most could go standard shipping.

**The problem in plain terms:**
- A user types "Hola, necesito ayuda con la orden de trabajo" (Spanish). The translation node calls GPT-4o to translate it to English. GPT-4o takes ~800ms and costs ~$0.005 for this trivial task. GPT-4o-mini would do the same job in ~200ms for ~$0.0003.
- The intent classifier calls GPT-4o just to figure out if the user is saying "hello" vs "what's wrong with this pump?". Again, a simple categorization task that doesn't need the most powerful model.
- This repeats for every single chat request, across every node in the pipeline.

**The fix:** Let each node pick its own model. Simple tasks use GPT-4o-mini (fast, cheap). Complex tasks use GPT-4o (smart, thorough). Controlled via config — no code deploy needed to switch a node's model.

---

## Design Constraints

1. **Pre-resolved caching** — All LLM instances (both 4o and mini) are created once at app startup and cached. Model selection for each node is resolved once at request setup (in `build_config()`), not inside nodes. Nodes never do model lookups — they just use what they're given.

2. **Zero runtime overhead in nodes** — Nodes continue to do `cfg.get("llm")` or `cfg.get("llm_service")` exactly as today. No `if/else`, no routing logic, no model selection inside nodes. The model assignment happens upstream before the graph runs.

3. **Latency-optimized** — LLM instances are pre-warmed at startup. No lazy initialization, no first-request penalty. Per-node model resolution is a single dict lookup (O(1)) done once per request, not per node.

4. **Code consistency** — Nodes keep the exact same pattern (`cfg.get("llm")`). The only code that changes inside nodes is the key name they read. `build_config()` signature stays consistent with existing patterns. No new abstractions or patterns introduced.

---

## How This Achieves ~30% Latency Reduction

### Current Chat Pipeline Latency (all GPT-4o)

```
User Request
  → LanguageTranslation   ~800ms  (GPT-4o, non-streaming invoke)
  → ProfanityCheck        ~5ms    (local, no LLM)
  → ClassifyIntent        ~600ms  (GPT-4o, non-streaming invoke)
  → ContextGathering      ~300ms  (Snowflake + OpenSearch, no LLM)
  → IntentFanout          ~5ms    (routing logic, no LLM)
  → LLMInvoke             ~2000ms (GPT-4o, streaming)
  ─── parallel ───
  → Summarization         ~500ms  (GPT-4o, runs alongside CopilotFlow)

  TOTAL SEQUENTIAL: ~3710ms
```

### After Multi-Model (Translation + Classification + Summarization on GPT-4o-mini)

```
User Request
  → LanguageTranslation   ~200ms  (GPT-4o-mini, 4x faster for simple translation)
  → ProfanityCheck        ~5ms    (unchanged)
  → ClassifyIntent        ~150ms  (GPT-4o-mini, 4x faster for classification)
  → ContextGathering      ~300ms  (unchanged, no LLM)
  → IntentFanout          ~5ms    (unchanged)
  → LLMInvoke             ~2000ms (GPT-4o or GPT-4o-mini — configurable)
  ─── parallel ───
  → Summarization         ~150ms  (GPT-4o-mini, runs in parallel)

  TOTAL SEQUENTIAL: ~2660ms
  SAVINGS: ~1050ms = ~28% faster
```

If LLMInvoke is also switched to mini (the initial default): LLMInvoke drops from ~2000ms to ~800ms, total becomes ~1460ms — a **60% reduction**. We start with all-mini and only promote nodes back to 4o if quality suffers.

### Auto-Summary Endpoint Latency

```
Current:  GPT-4o invoke ~1500ms
With mini: GPT-4o-mini invoke ~500ms  (67% faster)
```

---

## Node Inventory — What Each Node Does & Why It Can Use a Smaller Model

| Node | What it does (plain English) | Current model | Recommended | Why |
|------|------------------------------|---------------|-------------|-----|
| **LanguageTranslationNode** | Translates user's non-English query to English | GPT-4o | GPT-4o-mini | Translation is a well-understood task. Mini handles it with same quality at 4x speed. |
| **ClassifyIntentNode** | Reads the user's query and picks a category like "diagnosis", "fix", "greetings" | GPT-4o | GPT-4o-mini | It's just picking from ~10 categories. Mini is accurate enough for classification. |
| **SummarizationNodeWrapper** | Compresses old conversation messages into a short summary | GPT-4o | GPT-4o-mini | Summarization of chat history is a routine task. Runs in parallel so even if slightly slower, no impact on user. |
| **LLMInvokeNode** | Generates the actual answer the user sees (streaming) | GPT-4o | Start with mini, evaluate | This is the most quality-sensitive node. Start with mini; if answers aren't good enough, switch back to 4o via config. |
| **AutoSummaryNode** | Generates a work order summary from technician notes | GPT-4o | Start with mini, evaluate | Structured summarization. Mini may suffice; test with real work orders. |

---

## Implementation Plan (Step-by-Step)

### Step 1: Add mini model config keys + model routing to config JSON

**What we're doing:** Adding two new deployment keys (`CHAT_MODEL_MINI`, `CHAT_MODEL_MINI_NAME`) and a `model_routing` map that says "for this node, use this model."

**Why:** So we can switch any node between GPT-4o and GPT-4o-mini by changing config — no code deploy needed.

**Impact (+):** Ops team can tune model assignments without engineering involvement. Full rollback by removing the config section.
**Impact (-):** Config JSON grows slightly. If `model_routing` has a typo in a node name, that node silently falls back to the default model (safe but could be confusing).

**File:** `.env.example`

**Example 1 — All nodes on mini (initial rollout):**
```json
{
  "openai": {
    "CHAT_MODEL": "gpt-4o-2024-11-20",
    "CHAT_MODEL_NAME": "gpt-4o",
    "CHAT_MODEL_MINI": "gpt-4o-mini",
    "CHAT_MODEL_MINI_NAME": "gpt-4o-mini",
    "CHAT_API_VERSION": "2024-05-01-preview",
    "AZURE_OPENAI_SECRET_NAME": "<your-openai-secret-arn>"
  },
  "model_routing": {
    "translation": "mini",
    "intent_classification": "mini",
    "summarization": "mini",
    "llm_invoke": "mini",
    "auto_summary": "mini"
  }
}
```

**Example 2 — LLM invoke promoted back to 4o after quality testing:**
```json
"model_routing": {
    "translation": "mini",
    "intent_classification": "mini",
    "summarization": "mini",
    "llm_invoke": "default",
    "auto_summary": "mini"
}
```

**Example 3 — No model_routing section (backward compatible, all 4o):**
```json
{
  "openai": { "CHAT_MODEL": "gpt-4o-2024-11-20", ... }
}
```
When `model_routing` is absent, every node automatically uses the existing GPT-4o. Zero behavior change from today.

---

### Step 2: Add `get_azure_openai_llm_mini()` function

**What we're doing:** Creating a second LLM factory function that produces a GPT-4o-mini instance, reusing the same Azure credentials and caching logic.

**Why:** Today `get_azure_openai_llm()` is hardcoded to `CHAT_MODEL`. We need a parallel function for `CHAT_MODEL_MINI` without duplicating credential-fetching code.

**Caching guarantee:** Both `get_azure_openai_llm()` and `get_azure_openai_llm_mini()` use the existing `_llm_cache` dict. Once created at startup, they're reused forever — zero recreation cost per request.

**Impact (+):** Mini model instances are cached just like the current ones — no extra overhead per request.
**Impact (-):** Two more cached LLM objects in memory at startup (negligible — each is ~1KB).

**File:** `common/util/llm.py`

**Example 1 — The refactored internal helper (DRY, no duplication):**
```python
def _create_azure_openai_llm(deployment_name, model_name, streaming=False):
    """Shared logic: fetch credentials, build AzureChatOpenAI, cache it.
    Called only at startup — result is cached in _llm_cache."""
    cache_key = f"llm_{deployment_name}_{streaming}"
    if cache_key in _llm_cache:
        return _llm_cache[cache_key]

    region_name = config.get("openai", "AWS_REGION", "us-east-1")
    secret_name = config.get("openai", "AZURE_OPENAI_SECRET_NAME")
    credentials = get_azure_openai_credentials(region_name, secret_name)

    language_model = AzureChatOpenAI(
        azure_endpoint=credentials["AZURE_OPENAI_ENDPOINT"],
        openai_api_key=credentials["AZURE_OPENAI_API_KEY"],
        deployment_name=deployment_name,
        model_name=model_name,
        openai_api_version=config.get("openai", "CHAT_API_VERSION"),
        openai_api_type="azure",
        timeout=90,
        max_retries=10,
        temperature=0,
        seed=123,
        max_tokens=config.get("llm", "MAX_TOKEN", 2048),
        streaming=streaming,
    )
    _llm_cache[cache_key] = language_model
    return language_model
```

**Example 2 — Existing function preserved (unchanged signature, unchanged behavior):**
```python
def get_azure_openai_llm(streaming=False):
    """Returns cached GPT-4o instance. Signature unchanged — no callers need to change."""
    deployment_name = config.get("openai", "CHAT_MODEL")
    model_name = config.get("openai", "CHAT_MODEL_NAME")
    return _create_azure_openai_llm(deployment_name, model_name, streaming)
```

**Example 3 — New mini function (same pattern, different deployment):**
```python
def get_azure_openai_llm_mini(streaming=False):
    """Returns cached GPT-4o-mini instance for lightweight tasks."""
    deployment_name = config.get("openai", "CHAT_MODEL_MINI")
    model_name = config.get("openai", "CHAT_MODEL_MINI_NAME")
    return _create_azure_openai_llm(deployment_name, model_name, streaming)
```

---

### Step 3: Extend `CopilotDependencies` with pre-resolved mini-model instances

**What we're doing:** Adding mini-model LLM fields to the dependency container. All model routing is resolved here at request setup time — nodes never see routing logic.

**Why:** The dependency container is the single source of truth for "which model does this node get?" Resolving it once here means zero overhead inside nodes.

**Key design: All 4 LLM instances (4o streaming, 4o non-streaming, mini streaming, mini non-streaming) are created at startup and held as fields. `get_llm_for_node()` / `get_llm_service_for_node()` do a single dict lookup + return — no object creation, no branching beyond one `if`.**

**Impact (+):** Single place to control all model routing. Nodes remain completely unaware of which model they're using.
**Impact (-):** `CopilotDependencies` class grows by ~4 fields and ~2 methods. Consistent with existing pattern (already has `llm_streaming` + `llm_non_streaming`).

**File:** `copilot/copilot_api/services/dependencies.py`

**Example 1 — New fields (same pattern as existing `llm_streaming`/`llm_non_streaming`):**
```python
@dataclass
class CopilotDependencies:
    # ...existing fields unchanged...

    # Mini-model LLM instances (same pattern as llm_streaming/llm_non_streaming above)
    llm_mini_streaming: Any
    llm_mini_non_streaming: Any
    llm_service_mini_streaming: LLMService
    llm_service_mini_non_streaming: LLMService

    # Model routing config — simple dict, read once from config at startup
    model_routing: Dict[str, str]
```

**Example 2 — Helper: one dict lookup, returns pre-cached instance (O(1)):**
```python
def get_llm_for_node(self, node_name: str, streaming: bool = False) -> Any:
    """Returns pre-cached LLM instance for a node. O(1) — one dict.get() + one if."""
    if self.model_routing.get(node_name) == "mini":
        return self.llm_mini_streaming if streaming else self.llm_mini_non_streaming
    return self.llm_streaming if streaming else self.llm_non_streaming
```

**Example 3 — Same for LLMService wrapper:**
```python
def get_llm_service_for_node(self, node_name: str, streaming: bool = False) -> LLMService:
    """Returns pre-cached LLMService for a node. O(1) — one dict.get() + one if."""
    if self.model_routing.get(node_name) == "mini":
        return self.llm_service_mini_streaming if streaming else self.llm_service_mini_non_streaming
    return self.llm_service_streaming if streaming else self.llm_service_non_streaming
```

---

### Step 4: Initialize mini-model instances at API startup (pre-warm everything)

**What we're doing:** Creating the GPT-4o-mini LLM instances when the FastAPI app boots, alongside the existing GPT-4o instances. Everything is warm and ready before the first request arrives.

**Why:** LLM instances are expensive to create (credential fetch, client setup). We create them once at startup. No lazy init, no first-request penalty.

**Impact (+):** Both models are ready to use immediately — zero cold-start penalty on any request.
**Impact (-):** Startup time increases by ~1-2 seconds (one more credential fetch + two more LLM object creations). Negligible for a server that runs for days.

**File:** `api/api.py` — `lifespan()` function

**Example 1 — Creating mini LLM instances (add right after existing LLM init on line 81):**
```python
shared_resources["llm_mini_streaming"] = get_azure_openai_llm_mini(streaming=True)
logger.info("✓ Azure OpenAI LLM Mini (streaming) initialized")
shared_resources["llm_mini_non_streaming"] = get_azure_openai_llm_mini(streaming=False)
logger.info("✓ Azure OpenAI LLM Mini (non-streaming) initialized")
```

**Example 2 — Reading model_routing config with graceful fallback:**
```python
model_routing = {}
try:
    model_routing = config.get_all("model_routing")
except KeyError:
    logger.info("No model_routing config found — all nodes will use primary model (GPT-4o)")
logger.info(f"✓ Model routing: {model_routing or 'all default'}")
```

**Example 3 — Passing to CopilotDependencies.create() (extends existing call):**
```python
deps = CopilotDependencies.create(
    config=config, logger=logger,
    snowflake_client_factory=SnowflakeClient.from_env_pool,
    opensearch_client=shared_resources["opensearch_client"],
    embedding_model=shared_resources["embedding_model"],
    checkpointer=checkpointer,
    llm_streaming=shared_resources["llm_streaming"],
    llm_non_streaming=shared_resources["llm_non_streaming"],
    llm_mini_streaming=shared_resources["llm_mini_streaming"],           # NEW
    llm_mini_non_streaming=shared_resources["llm_mini_non_streaming"],   # NEW
    model_routing=model_routing,                                          # NEW
)
```

---

### Step 5: Wire per-node LLMs into `build_config()` — resolved once per request, not per node

**What we're doing:** At request time (once, before the graph runs), we resolve which model each node should use and put it into the RunnableConfig. When the graph executes, each node just reads its pre-resolved LLM from config — no routing logic, no overhead.

**Why:** This is the key design decision for zero runtime overhead. Model selection happens in `chat_api_response.py` before `state_machine.stream()` is called. Inside the graph, nodes see a flat dict with their LLM already set.

**Impact (+):** Zero per-node overhead. Each `deps.get_llm_for_node()` call is O(1) and happens only once per request, not per node execution.
**Impact (-):** `build_config()` signature grows by 3 optional params — consistent with existing pattern.

**File:** `copilot/copilot_api/models/conversation_context.py`

**Example 1 — Updated method signature (3 new optional params):**
```python
def build_config(self, llm_service=None, profanity_checker=None,
                 llm_translation=None, llm_classification=None,
                 llm_service_summarization=None) -> dict:
```

**Example 2 — The returned config dict (new keys use same naming pattern):**
```python
return {
    "thread_id": self.session_id,
    "llm": self.llm,                                        # default (backward compat)
    "llm_service": llm_service,                              # for LLMInvokeNode
    "llm_translation": llm_translation or self.llm,          # for LanguageTranslationNode
    "llm_classification": llm_classification or self.llm,    # for ClassifyIntentNode
    "llm_service_summarization": llm_service_summarization or llm_service,  # for SummarizationNodeWrapper
    "profanity_checker": profanity_checker,
    "classify_intent_and_topic": classify_intent_and_topic,
    "context_retrieve": lambda ui, idx, aids: context_retrieve(...),
    "copilot_config": self.config,
    "prompt_templates": self.prompt_templates,
    "logger": self.logger,
}
```

**Example 3 — How `chat_api_response.py` calls it (all routing resolved here, once):**

**File:** `copilot/copilot_api/api/chat_api_response.py`

```python
# Model routing resolved ONCE here — nodes just read their key from config
config = context.build_config(
    llm_service=deps.get_llm_service_for_node("llm_invoke", streaming=True),
    profanity_checker=profanity,
    llm_translation=deps.get_llm_for_node("translation", streaming=False),
    llm_classification=deps.get_llm_for_node("intent_classification", streaming=False),
    llm_service_summarization=deps.get_llm_service_for_node("summarization", streaming=False),
)
```

Each `get_llm_for_node()` is one dict lookup + one `if` = nanoseconds. Total overhead for all 4 calls: effectively zero.

---

### Step 6: Update nodes to read their pre-resolved LLM key

**What we're doing:** Each node reads a different config key name. That's it. No routing logic, no conditionals, no model selection. The correct LLM is already sitting in the config dict waiting for them.

**Why:** This keeps nodes simple, consistent, and fast. A node doesn't know or care if it's using 4o or mini — it just calls `.invoke()` on whatever it gets.

**Impact (+):** Zero runtime overhead. Code consistency preserved — every node still does `cfg.get("key_name")`.
**Impact (-):** None. Each change is literally one key name change.

#### 6a. LanguageTranslationNode
**File:** `copilot/copilot_api/nodes/translation.py` — line 91

**Example 1 — Before (reads default LLM):**
```python
llm = cfg.get("llm")
```

**Example 2 — After (reads pre-resolved translation LLM — same pattern, different key):**
```python
llm = cfg.get("llm_translation") or cfg.get("llm")
```

**Example 3 — Why `or cfg.get("llm")`: If someone runs old config without the new keys, or during tests where only `"llm"` is set, the node still works. Zero breakage risk. The `or` short-circuits in nanoseconds — if `llm_translation` exists (the normal case), `cfg.get("llm")` is never called.**

#### 6b. ClassifyIntentNode
**File:** `copilot/copilot_api/nodes/input_processing.py` — line 84

**Example 1 — Before:**
```python
llm = cfg.get("llm")
```

**Example 2 — After:**
```python
llm = cfg.get("llm_classification") or cfg.get("llm")
```

**Example 3 — At runtime: intent classification now runs on mini, classifying "what's wrong with pump 42?" as "diagnosis" in ~150ms instead of ~600ms. The node code doesn't know the difference — it just got a faster LLM.**

#### 6c. SummarizationNodeWrapper
**File:** `copilot/copilot_api/nodes/summarization.py` — line 120

**Example 1 — Before:**
```python
llm_service = cfg.get("llm_service")
```

**Example 2 — After:**
```python
llm_service = cfg.get("llm_service_summarization") or cfg.get("llm_service")
```

**Example 3 — Cache invalidation for the class-level `_node`: Since `SummarizationNodeWrapper._node` is cached at class level, we need to detect if the underlying model changed (e.g., during config reload). Add a simple model identity check:**
```python
# Add class-level attribute:
_last_model_id: Optional[str] = None

# In _get_or_create_node(), before the existing if-check:
current_model_id = llm_service.llm.deployment_name
if SummarizationNodeWrapper._node is not None and SummarizationNodeWrapper._last_model_id != current_model_id:
    SummarizationNodeWrapper._node = None  # Force recreation
SummarizationNodeWrapper._last_model_id = current_model_id
```
This adds one string comparison per invocation — negligible cost, prevents stale cache.

#### 6d. LLMInvokeNode
**File:** `copilot/copilot_api/nodes/llm_nodes.py`

**No change needed.** This node reads `cfg.get("llm_service")` which is already set to the correct model in Step 5. The routing happened upstream — this node just uses it.

---

### Step 7: Update Auto-Summarization to use model routing

**What we're doing:** The auto-summary flow is separate from the chat graph. It receives its `llm_service` directly from `CopilotDependencies`. We change one line to use the routing helper instead of the hardcoded default.

**Why:** Auto-summarization is a structured task (turn technician notes into a summary). GPT-4o-mini can likely handle it at 67% less latency.

**Impact (+):** Summary generation drops from ~1500ms to ~500ms. Cost per summary drops ~15x.
**Impact (-):** If mini's summary quality is noticeably worse, switch back via config.

**File:** `copilot/copilot_api/auto_summary/core.py` — line 72

**Example 1 — Before:**
```python
llm_service=deps.llm_service_non_streaming,
```

**Example 2 — After:**
```python
llm_service=deps.get_llm_service_for_node("auto_summary", streaming=False),
```

**Example 3 — Downstream unchanged: `state_factory.py`, `dependency_manager.py`, and `llm_interface.py` all receive `llm_service` as a parameter and don't care which model backs it. No changes needed in those files.**

---

### Step 8: Update `.env.example`

**File:** `.env.example`

Add the new config keys to the JSON so developers know what's available. The existing structure stays the same — we just add keys to the existing `"openai"` section and a new `"model_routing"` section.

---

### Step 9: Update tests

**What we're doing:** Ensuring test fixtures include the new per-node config keys, and adding tests to verify fallback behavior.

**Files:**
- `tests/copilot/graph/conftest.py` — Add per-node LLM keys to test config fixtures
- `tests/copilot/graph/test_nodes.py` — Verify nodes fall back to default when per-node key absent
- `tests/configs/test_copilot_config.py` — Verify `model_routing` section is optional

**Example 1 — conftest.py fixture update (consistent with existing pattern):**
```python
config = {
    "llm": mock_llm,
    "llm_service": mock_llm_service,
    "llm_translation": mock_llm_mini,           # NEW — same mock pattern
    "llm_classification": mock_llm_mini,         # NEW
    "llm_service_summarization": mock_llm_service_mini,  # NEW
    ...existing keys unchanged...
}
```

**Example 2 — Fallback test:**
```python
def test_translation_node_falls_back_to_default_llm():
    """When llm_translation is not in config, node uses default llm."""
    config = {"configurable": {"llm": mock_llm}}  # no llm_translation key
    result = LanguageTranslationNode(logger)._execute(state, config)
    mock_llm.invoke.assert_called()  # used the fallback
```

**Example 3 — Model routing absent test:**
```python
def test_model_routing_absent_uses_defaults():
    """When model_routing section missing from config, all nodes get default model."""
    deps = CopilotDependencies.create(..., model_routing={})
    assert deps.get_llm_for_node("translation") is deps.llm_non_streaming
    assert deps.get_llm_for_node("llm_invoke") is deps.llm_non_streaming
```

---

## Performance Guarantee: Where Caching Happens

| What | When cached | Cache lifetime | Lookup cost per request |
|------|------------|----------------|------------------------|
| Azure OpenAI credentials | Startup | App lifetime (`_credentials_cache` dict) | 0 (never re-fetched) |
| GPT-4o LLM instance (streaming) | Startup | App lifetime (`_llm_cache` dict) | 0 |
| GPT-4o LLM instance (non-streaming) | Startup | App lifetime (`_llm_cache` dict) | 0 |
| GPT-4o-mini LLM instance (streaming) | Startup | App lifetime (`_llm_cache` dict) | 0 |
| GPT-4o-mini LLM instance (non-streaming) | Startup | App lifetime (`_llm_cache` dict) | 0 |
| LLMService wrappers (4 total) | Startup | App lifetime (`CopilotDependencies` fields) | 0 |
| Model routing config | Startup | App lifetime (`CopilotDependencies.model_routing` dict) | 0 |
| Per-node model resolution | Per request in `build_config()` | Request lifetime (in RunnableConfig) | 4 dict lookups total (~ns) |

**Bottom line:** After startup, every request does exactly 4 dict lookups to resolve all node models. Inside the graph, nodes do zero extra work compared to today.

---

## Files Modified (Summary)

| File | Change | Lines Changed (est.) |
|------|--------|---------------------|
| `common/util/llm.py` | Refactor into `_create_azure_openai_llm()` + add `get_azure_openai_llm_mini()` | ~30 |
| `copilot/copilot_api/services/dependencies.py` | Add mini LLM fields, `model_routing`, two helper methods | ~40 |
| `api/api.py` | Initialize mini LLM instances, read `model_routing` config | ~15 |
| `copilot/copilot_api/models/conversation_context.py` | Add per-node LLM params to `build_config()` | ~10 |
| `copilot/copilot_api/api/chat_api_response.py` | Wire per-node models via `deps.get_llm_for_node()` | ~5 |
| `copilot/copilot_api/nodes/translation.py` | 1-line change: read `llm_translation` with `or` fallback | 1 |
| `copilot/copilot_api/nodes/input_processing.py` | 1-line change: read `llm_classification` with `or` fallback | 1 |
| `copilot/copilot_api/nodes/summarization.py` | Read `llm_service_summarization` with fallback + cache identity check | ~10 |
| `copilot/copilot_api/auto_summary/core.py` | 1-line change: use `deps.get_llm_service_for_node()` | 1 |
| `.env.example` | Add `CHAT_MODEL_MINI`, `CHAT_MODEL_MINI_NAME`, `model_routing` | ~10 |
| `tests/copilot/graph/conftest.py` | Add per-node LLM keys to fixtures | ~10 |
| `tests/copilot/graph/test_nodes.py` | Add fallback behavior tests | ~30 |

**Total estimated: ~163 lines across 12 files.**

---

## Verification Plan

1. **Unit tests**: `pytest tests/copilot/graph/test_nodes.py -v`
2. **Config tests**: `pytest tests/configs/ -v`
3. **Full test suite**: `pytest -v`
4. **Local manual test**: Update `.env` with `model_routing` (all mini), run `uvicorn api.api:app --reload`, send chat + summary requests, verify logs show correct deployment name per node
5. **Quality comparison**: Run same 10 queries through both configurations, compare response quality side-by-side

---

## Rollback Strategy

- **Remove `model_routing` section from config** → all nodes automatically fall back to GPT-4o. Zero code changes.
- **Change one node back** → set `"llm_invoke": "default"` in config, restart. That node goes back to GPT-4o; others stay on mini.
- **Every node has `or cfg.get("llm")`** fallback, so even if the new config keys don't exist, behavior is identical to today.
