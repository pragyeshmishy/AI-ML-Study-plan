# Plan: Extend Auto Summary to Support All Work Order Source Types

## Context

Auto Summary currently only works for asset-based work orders. The source resolver (`source_resolver.py`) was created to detect source types via a priority cascade, but it reads **flat fields** (`SourceSiteName`, `SourceSiteNo`, etc.) for site/location detection.

**Client confirmed:** `SourceSites` and `SourceLocations` are **ARRAYS of nested objects** — identical in structure to `SourceAssets`. The flat-field approach does not match real AE payloads.

### What's already done (on dev, 44/44 tests pass):
- `data_access.py` — SourceAssets validation gate removed; only tenant ID check remains
- `constants.py` — `NO_ASSETS_ERROR` removed
- `core.py` — calls `resolve_source_contexts()` correctly, `NO_ASSETS_ERROR` block removed
- `source_resolver.py` — exists with SourceType enum, SourceContext dataclass, correct `_resolve_assets()` path
- `context_builder.py` — accepts `List[SourceContext]`, uses dynamic labels (`ctx.label`)
- `Summarization.yaml` — prompt updated with "(if applicable)"
- Tests — 44 passing (6 resolver + 2 node-level + existing)

### What's wrong: `_resolve_site()` and `_resolve_location()` read flat fields instead of arrays

---

## Source Type Rules (from client)

1. **Source types are mutually exclusive** — only ONE of `SourceAssets[]`, `SourceLocations[]`, or `SourceSites[]` is populated per work order
2. **Source is mandatory** — AE enforces a work source. If all three arrays are missing/empty, return an error: *"No source found: work order must have at least one of SourceAssets, SourceSites, or SourceLocations."*
3. **Priority cascade:** `SourceAssets` > `SourceLocations` > `SourceSites`
4. **Not all nested fields guaranteed** — some may be null, code must handle gracefully
5. **Site/Location on assets belong to the asset**, not the WO — WO-level site/location are null when assets are present
6. **Locations are always tied to a Site** — `SiteId`/`SiteName` inside `SourceLocations[]` objects are reliably populated (not just optional). Use them confidently for the location string.
7. **API reference:** https://assetessentials.dudesolutions.com/Documents/APIDocuments.html

### 5 Cases:
1. **Asset + Site + Location on asset:** `SourceAssets[].SiteName`, `SourceAssets[].LocationName` populated
2. **Asset + Site (no location):** `SourceAssets[].SiteName` populated, `LocationName` null
3. **Global asset (no site/location):** `SourceAssets[]` present but site/location fields null
4. **Location with parent site:** `SourceLocations[].SiteName` carries parent site info (always present)
5. **Site only:** `SourceSites[]` populated, no assets or locations
6. **No source — Error:** No source arrays populated → return error message

---

## Payload Shapes (from client)

**`SourceAssets[]`** (already handled correctly):
```json
[{
  "AssetId": 1001, "Name": "Chiller Unit A", "AssetNo": "A-001",
  "SiteId": 10, "SiteNo": "S01", "SiteName": "Building A",
  "LocationId": 100, "LocationNo": "R101", "LocationName": "Mech Room",
  "RegionName": "Northeast"
}]
```

**`SourceSites[]`:**
```json
[{
  "SiteId": 500, "SiteNo": "MSA-45", "SiteName": "Kentucky Arts",
  "RegionId": 50, "RegionName": "Southeast", "Description": "..."
}]
```

**`SourceLocations[]`:**
```json
[{
  "LocationId": 300, "LocationNo": "LOC-001", "LocationName": "Building A",
  "SiteId": 10, "SiteName": "Main Campus", "SiteNo": "S01",
  "RegionName": "Northeast", "Path": "Main Campus > Building A",
  "ParentLocationId": null, "ParentLocationName": null
}]
```

**Labels per type:**
- Assets: `Asset Name/No 1: Chiller Unit A (No: A-001)` + `Location 1: Building A, Northeast`
- Sites: `Site Name/No 1: Kentucky Arts (MSA-45)` + `Location 1: Southeast`
- Locations: `Location Name/No 1: Building A (LOC-001)` + `Location 1: Main Campus, Northeast`

`WorkOrderItem` in `api/schemas.py` has `extra: "allow"`, so all arrays pass through without new Pydantic models.

---

## Remaining Changes (4 files)

### 1. Add `NO_SOURCE_ERROR` constant — `copilot/copilot_api/auto_summary_node/constants.py`

```python
NO_SOURCE_ERROR = "No source found: work order must have at least one of SourceAssets, SourceSites, or SourceLocations."
```

### 2. Add no-source error handling — `copilot/copilot_api/auto_summary_node/core.py`

After `resolve_source_contexts()` call, check if it returned `None`. If so, return error (same pattern as `MISSING_DEPENDENCIES_ERROR`):

```python
source_contexts = resolve_source_contexts(...)
if source_contexts is None:
    logger.warning(f"No source type found for work order ID={workorder_id}")
    if streaming:
        state["response_generator"] = iter([NO_SOURCE_ERROR])
    else:
        state["response"] = NO_SOURCE_ERROR
    return state
```

### 3. Rework `source_resolver.py` — `copilot/copilot_api/auto_summary_node/source_resolver.py`

**Keep unchanged:** `SourceType`, `SourceContext`, `_resolve_assets()`

**Change detection logic** in `resolve_source_contexts()`:

```python
# BEFORE (flat fields — WRONG):
if work_order_payload.get("SourceSiteName") or work_order_payload.get("SourceSiteId"):
    return _resolve_site(work_order_payload)
if work_order_payload.get("SourceLocationName") or work_order_payload.get("SourceLocationId"):
    return _resolve_location(work_order_payload)

# AFTER (arrays — CORRECT, note priority change: Location > Site):
raw_locations = work_order_payload.get("SourceLocations") or []
if raw_locations:
    return _resolve_locations(raw_locations)

raw_sites = work_order_payload.get("SourceSites") or []
if raw_sites:
    return _resolve_sites(raw_sites)
```

**Change "no source" fallback** — return `None` instead of `[]`:
```python
# BEFORE:
return []

# AFTER:
logger.warning("No source type detected — all three source arrays are missing/empty")
return None
```

Update return type from `List[SourceContext]` to `Optional[List[SourceContext]]`.

**Replace `_resolve_site(payload)` → `_resolve_sites(raw_sites: List[Dict])`:**
- Iterate `SourceSites[]` array
- Per site: `name_id = f"{SiteName} ({SiteNo})"`, `location = RegionName or DEFAULT_VALUE`
- Return one `SourceContext(SITE, "Site Name/No", ...)` per entry

**Replace `_resolve_location(payload)` → `_resolve_locations(raw_locations: List[Dict])`:**
- Iterate `SourceLocations[]` array
- Per location: `name_id = f"{LocationName} ({LocationNo})"`, `location = SiteName, RegionName`
- Location carries parent site info (`SiteName`/`SiteNo` nested in each object)
- Return one `SourceContext(LOCATION, "Location Name/No", ...)` per entry

### 4. Rework tests — `tests/copilot/summary_response/test_summary_api.py`

**Rework existing tests to use array payloads:**

| Test | Current (flat fields) | New (arrays) |
|------|----------------------|--------------|
| `test_source_resolver_site` | `SourceSiteName`, `SourceSiteNo` flat fields | `SourceSites: [{SiteId, SiteNo, SiteName, RegionName}]` |
| `test_source_resolver_location` | `SourceLocationName`, `SourceLocationNo` flat fields | `SourceLocations: [{LocationId, LocationNo, LocationName, SiteName, RegionName}]` |
| `test_priority_cascade_site_over_location` | Both flat fields | Both arrays → location wins (new priority) |
| `test_priority_cascade_asset_wins` | `SourceSiteName` + `SourceAssets` | `SourceSites` array + `SourceAssets` → asset wins |
| `test_site_based_work_order` (node) | Flat `SourceSiteName` etc. | `SourceSites: [...]` array |
| `test_location_based_work_order` (node) | Flat `SourceLocationName` etc. | `SourceLocations: [...]` array |

**Add new tests:**
- `test_source_resolver_multiple_sites` — 2 entries in `SourceSites` → 2 SourceContext objects
- `test_source_resolver_multiple_locations` — 2 entries in `SourceLocations` → 2 SourceContext objects
- `test_source_resolver_location_with_parent_site` — location has `SiteName`/`SiteNo` → location field includes parent site
- `test_source_resolver_site_null_fields` — site with only `SiteName` (no `SiteNo`, no `RegionName`) → handles gracefully
- `test_source_resolver_location_null_fields` — location with only `LocationName` → handles gracefully
- `test_source_resolver_no_source_error` — all three arrays missing/empty → returns `None`
- `test_no_source_work_order` (node-level) — no source arrays → node returns `NO_SOURCE_ERROR` message

---

## Files Modified

| File | Change |
|------|--------|
| `copilot/copilot_api/auto_summary_node/constants.py` | Add `NO_SOURCE_ERROR` constant |
| `copilot/copilot_api/auto_summary_node/core.py` | Add no-source error check after `resolve_source_contexts()`, import `NO_SOURCE_ERROR` |
| `copilot/copilot_api/auto_summary_node/source_resolver.py` | Rework `_resolve_site` → `_resolve_sites(raw_sites)`, `_resolve_location` → `_resolve_locations(raw_locations)`, fix priority to Asset > Location > Site, read from arrays, return `None` when no source |
| `tests/copilot/summary_response/test_summary_api.py` | Rework 6 existing resolver/node tests to use array payloads, add 7 new edge-case tests |

## Files NOT Modified (already correct on dev)

- `context_builder.py` — accepts `List[SourceContext]`, dynamic labels
- `Summarization.yaml` — prompt already updated
- `api/schemas.py` — `WorkOrderItem` has `extra: "allow"`, arrays pass through
- `data_access.py` — SourceAssets gate already removed
- `models.py` — `WorkOrderData.from_ae_item()` source-agnostic
- `dependency_manager.py` — no source logic
- `asset_parser.py` — reused by resolver for asset path

---

## Verification

1. `pytest tests/copilot/summary_response/test_summary_api.py -v` — all reworked + new tests pass
2. `pytest` — full suite, no regressions (15 pre-existing failures from unrelated import chain issue expected)
3. Spot-check: payload with `SourceSites: [{"SiteId": 500, "SiteName": "Test"}]` → LLM prompt contains `"Site Name/No 1: Test"`
4. Spot-check: payload with `SourceLocations: [{"LocationName": "Bldg A", "SiteName": "Campus"}]` → LLM prompt contains `"Location Name/No 1: Bldg A"` and `"Location 1: Campus"`
