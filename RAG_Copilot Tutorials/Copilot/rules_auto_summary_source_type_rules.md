# Auto Summary — Work Order Source Type Rules

## The Golden Rule

Every work order **must** have exactly one source type. It will always be one of:

- **Assets** (`SourceAssets` array)
- **Locations** (`SourceLocations` array)
- **Sites** (`SourceSites` array)

These are **mutually exclusive at the work order level** — if assets are present, the WO-level site and location will be null, and vice versa.

---

## The Six Cases

### Case 1: Asset with Site and Location

The asset itself has a site and location, but these belong to the **asset**, not the work order.

- `SourceAssets` = populated (with `SiteId`, `SiteName`, `LocationId`, `LocationName` inside each asset)
- `SourceSites` = null
- `SourceLocations` = null
- WO-level site/location = null

**Think of it as:** "This work order is about an asset. That asset happens to live at a site and location, but the WO only cares about the asset."

### Case 2: Asset with Site only (no Location)

Same as Case 1, but the asset has a site but no location assigned.

- `SourceAssets` = populated (with `SiteId`/`SiteName` inside, `LocationId`/`LocationName` = null)
- `SourceSites` = null
- `SourceLocations` = null

### Case 3: Global Asset (no Site, no Location)

The asset is "global" — not tied to any site or location.

- `SourceAssets` = populated (`SiteId`, `SiteName`, `LocationId`, `LocationName` all null inside the asset)
- `SourceSites` = null
- `SourceLocations` = null

### Case 4: Location-based (no Asset)

The work order is about a location, not an asset. The location carries its parent site info within it.

- `SourceAssets` = null
- `SourceLocations` = populated (with `SiteId`/`SiteName` inside each location object)
- `SourceSites` = null
- WO-level asset = null

**Key insight:** A location is **always tied to a site** — `SiteId` and `SiteName` inside `SourceLocations[]` objects are reliably populated (not optional). Use them confidently for the location string.

### Case 5: Site-only (no Asset, no Location)

The work order is about a site directly. No asset or location involved.

- `SourceAssets` = null
- `SourceSites` = populated
- `SourceLocations` = null

### Case 6: No Source — Error

If all three source arrays are missing or empty, the work order is incomplete. AE enforces a work source, so this shouldn't happen under normal circumstances.

- `SourceAssets` = null or empty
- `SourceSites` = null or empty
- `SourceLocations` = null or empty

**Our code returns an error:** `resolve_source_contexts()` returns `None`, and `core.py` responds with: *"No source found: work order must have at least one of SourceAssets, SourceSites, or SourceLocations."*

---

## Payload Structure

All three source types come as **arrays**, not flat fields:

| Source Type | Payload Key | Type |
|-------------|-------------|------|
| Assets | `SourceAssets` | Array of asset objects |
| Sites | `SourceSites` | Array of site objects |
| Locations | `SourceLocations` | Array of location objects |

### Not all nested fields are guaranteed

Each array object has many possible fields, but **not all will be present every time**. Code must handle missing/null fields gracefully.

### Key fields per source type

**SourceAssets[]** — fields we use for summary context:
- `AssetId`, `Name`, `AssetNo`
- `SiteId`, `SiteNo`, `SiteName` (belongs to the asset, may be null for global assets)
- `LocationId`, `LocationNo`, `LocationName` (belongs to the asset, may be null)
- `RegionName`

**SourceSites[]** — fields we use for summary context:
- `SiteId`, `SiteNo`, `SiteName`
- `RegionId`, `RegionName`

**SourceLocations[]** — fields we use for summary context:
- `LocationId`, `LocationNo`, `LocationName`
- `SiteId`, `SiteName`, `SiteNo` (parent site, nested inside the location object)
- `RegionName`
- `Path` (e.g., "Area de Chillers > Area de Chillers CTE51ACH0007")

---

## Priority Cascade for Detection

```
if SourceAssets is non-empty  → use Asset path (Cases 1, 2, 3)
elif SourceLocations is non-empty → use Location path (Case 4)
elif SourceSites is non-empty     → use Site path (Case 5)
else                              → no source (Case 6 — unknown/empty)
```

A source is mandatory (AE enforces it). If none of the three arrays are populated, the resolver returns an error: *"No source found: work order must have at least one of SourceAssets, SourceSites, or SourceLocations."*

**API Reference:** https://assetessentials.dudesolutions.com/Documents/APIDocuments.html

---

## Sample Payloads — All Cases

Every example below shows the **full work order payload shape** that our `/summary` API receives. The three source arrays (`SourceAssets`, `SourceSites`, `SourceLocations`) sit alongside the standard WO metadata fields. Only one source array is populated per work order — the others are `null`.

> **Note:** Fields like `WorkOrderId`, `Title`, `WorkRequested`, etc. are always present. The examples below focus on the source arrays but include the surrounding WO fields for completeness.

---

### Case 1 — Asset with Site + Location

A technician is fixing a chiller. The chiller (an asset) is installed at a specific site and location. The site/location info lives **inside the asset object** — it describes where the asset physically sits, not the WO itself.

```json
{
  "WorkOrderId": 50001,
  "WorkOrderNo": "WO-50001",
  "Title": "Chiller compressor failure",
  "WorkRequested": "Compressor not cycling, unit overheating",
  "Origin": "NONPM",
  "CreatedDate": "2026-04-01T08:00:00Z",
  "CompletedDate": "2026-04-01T14:30:00Z",

  "SourceAssets": [
    {
      "AssetId": 175530,
      "Name": "Chiller Unit A",
      "AssetNo": "0000147217",
      "SiteId": 144,
      "SiteNo": "MSA-79",
      "SiteName": "Panama",
      "LocationId": 38642,
      "LocationNo": "L-101",
      "LocationName": "Area de Chillers",
      "RegionName": "Liston-Reller"
    }
  ],
  "SourceSites": null,
  "SourceLocations": null
}
```

**What our code extracts:**
- Asset Name/No 1: Chiller Unit A (0000147217)
- Location 1: Panama > Area de Chillers, Liston-Reller

**Layman:** "This WO is about the chiller. The chiller happens to be at the Panama site in the Area de Chillers room."

---

### Case 2 — Asset with Site only (no Location)

Same as Case 1, but the asset has a site but no specific room/location assigned to it.

```json
{
  "WorkOrderId": 50002,
  "WorkOrderNo": "WO-50002",
  "Title": "Generator annual inspection",
  "WorkRequested": "Scheduled annual inspection for backup generator",
  "Origin": "PM",
  "CreatedDate": "2026-04-05T09:00:00Z",
  "CompletedDate": "2026-04-05T11:00:00Z",

  "SourceAssets": [
    {
      "AssetId": 22010,
      "Name": "Backup Generator B",
      "AssetNo": "GEN-042",
      "SiteId": 200,
      "SiteNo": "FAC-12",
      "SiteName": "North Campus",
      "LocationId": null,
      "LocationNo": null,
      "LocationName": null,
      "RegionName": "Midwest"
    }
  ],
  "SourceSites": null,
  "SourceLocations": null
}
```

**What our code extracts:**
- Asset Name/No 1: Backup Generator B (GEN-042)
- Location 1: North Campus, Midwest

**Layman:** "This WO is about the generator. It's at the North Campus site but no specific room — maybe it's an outdoor unit."

---

### Case 3 — Global Asset (no Site, no Location)

The asset is "global" — not tied to any physical site or location. Think of a laptop, a fleet vehicle, or a shared tool.

```json
{
  "WorkOrderId": 50003,
  "WorkOrderNo": "WO-50003",
  "Title": "Laptop screen replacement",
  "WorkRequested": "Cracked screen on shared department laptop",
  "Origin": "NONPM",
  "CreatedDate": "2026-04-10T13:00:00Z",
  "CompletedDate": "2026-04-10T15:00:00Z",

  "SourceAssets": [
    {
      "AssetId": 99001,
      "Name": "Dell Latitude 5520",
      "AssetNo": "IT-LAP-330",
      "SiteId": null,
      "SiteNo": null,
      "SiteName": null,
      "LocationId": null,
      "LocationNo": null,
      "LocationName": null,
      "RegionName": null
    }
  ],
  "SourceSites": null,
  "SourceLocations": null
}
```

**What our code extracts:**
- Asset Name/No 1: Dell Latitude 5520 (IT-LAP-330)
- Location 1: Not captured in technician notes.

**Layman:** "This WO is about a laptop that isn't assigned to any building. We just know the asset name and number."

---

### Case 4 — Location-based (no Asset)

The WO is about a **location** (a room, floor, area) — not a specific piece of equipment. The location always carries its parent site info inside the object.

```json
{
  "WorkOrderId": 50004,
  "WorkOrderNo": "WO-50004",
  "Title": "Restroom plumbing leak",
  "WorkRequested": "Water pooling under sink in west restrooms",
  "Origin": "NONPM",
  "CreatedDate": "2026-04-12T07:00:00Z",
  "CompletedDate": "2026-04-12T09:30:00Z",

  "SourceAssets": null,
  "SourceSites": null,
  "SourceLocations": [
    {
      "LocationId": 2343,
      "LocationNo": "LOC-445",
      "LocationName": "West Restrooms",
      "SiteId": 2431,
      "SiteNo": "CC-01",
      "SiteName": "Convention Center",
      "RegionName": "Southeast",
      "Path": "Building B > West Restrooms",
      "ParentLocationId": null,
      "ParentLocationName": null
    }
  ]
}
```

**What our code extracts:**
- Location Name/No 1: West Restrooms (LOC-445)
- Location 1: Convention Center, Southeast

**Layman:** "This WO is about the West Restrooms area at the Convention Center. No specific asset — it's the room itself that needs fixing."

---

### Case 5 — Site-only (no Asset, no Location)

The WO is about an **entire site** — not a specific room or piece of equipment. Think of grounds maintenance, event setup, or a site-wide inspection.

```json
{
  "WorkOrderId": 50005,
  "WorkOrderNo": "WO-50005",
  "Title": "Annual grounds maintenance",
  "WorkRequested": "Full site landscaping, tree trimming, parking lot sweep",
  "Origin": "PM",
  "CreatedDate": "2026-04-15T06:00:00Z",
  "CompletedDate": "2026-04-15T18:00:00Z",

  "SourceAssets": null,
  "SourceLocations": null,
  "SourceSites": [
    {
      "SiteId": 500,
      "SiteNo": "MSA-45",
      "SiteName": "Kentucky Arts Center",
      "RegionId": 61,
      "RegionName": "Southeast",
      "Description": "Main arts and cultural center campus"
    }
  ]
}
```

**What our code extracts:**
- Site Name/No 1: Kentucky Arts Center (MSA-45)
- Location 1: Southeast

**Layman:** "This WO is about the entire Kentucky Arts Center site. No specific room or piece of equipment — the whole campus."

---

### Case 6 — No Source (Error)

All three source arrays are missing or empty. This shouldn't happen normally (AE enforces a source), but our code must handle it. We return an error.

```json
{
  "WorkOrderId": 50006,
  "WorkOrderNo": "WO-50006",
  "Title": "Unclassified request",
  "WorkRequested": "Submitted via automated workflow",
  "Origin": "NONPM",
  "CreatedDate": "2026-04-20T10:00:00Z",
  "CompletedDate": null,

  "SourceAssets": null,
  "SourceSites": null,
  "SourceLocations": null
}
```

**What our code does:**
- Returns error: *"No source found: work order must have at least one of SourceAssets, SourceSites, or SourceLocations."*

**Layman:** "This WO came through a workflow but nobody picked what it's about yet — no asset, no site, no location. We can't summarize it."

---

### Case 7 — Multiple Assets on one WO (Cases 1+2+3 combined)

A single WO covers three assets: one with full site+location, one with site only, and one global. This is common for batch maintenance — a tech visits multiple pieces of equipment on one work order.

```json
{
  "WorkOrderId": 50007,
  "WorkOrderNo": "WO-50007",
  "Title": "Quarterly HVAC check - multiple units",
  "WorkRequested": "Inspect and service all assigned HVAC units",
  "Origin": "PM",
  "CreatedDate": "2026-04-22T08:00:00Z",
  "CompletedDate": "2026-04-22T16:00:00Z",

  "SourceAssets": [
    {
      "AssetId": 334,
      "Name": "Rooftop AHU-1",
      "AssetNo": "HVAC-001",
      "SiteId": 2431,
      "SiteNo": "FAC-12",
      "SiteName": "North Campus",
      "LocationId": 2343,
      "LocationNo": "RM-201",
      "LocationName": "Floor 2 Mechanical",
      "RegionName": "Midwest"
    },
    {
      "AssetId": 335,
      "Name": "Rooftop AHU-2",
      "AssetNo": "HVAC-002",
      "SiteId": 2431,
      "SiteNo": "FAC-12",
      "SiteName": "North Campus",
      "LocationId": null,
      "LocationNo": null,
      "LocationName": null,
      "RegionName": "Midwest"
    },
    {
      "AssetId": 336,
      "Name": "Portable AC Unit",
      "AssetNo": "HVAC-003",
      "SiteId": null,
      "SiteNo": null,
      "SiteName": null,
      "LocationId": null,
      "LocationNo": null,
      "LocationName": null,
      "RegionName": null
    }
  ],
  "SourceSites": null,
  "SourceLocations": null
}
```

**What our code extracts:**
- Asset Name/No 1: Rooftop AHU-1 (HVAC-001) — Location 1: North Campus > Floor 2 Mechanical, Midwest
- Asset Name/No 2: Rooftop AHU-2 (HVAC-002) — Location 2: North Campus, Midwest
- Asset Name/No 3: Portable AC Unit (HVAC-003) — Location 3: Not captured in technician notes.

**Layman:** "One WO, three HVAC units. First one is in a specific room, second is on the same campus but no room, third is a portable unit not tied to any building."

---

### Case 8 — Multiple Locations on one WO

A single WO covers work across multiple locations at the same site (e.g., a plumber fixing leaks on different floors).

```json
{
  "WorkOrderId": 50008,
  "WorkOrderNo": "WO-50008",
  "Title": "Multi-floor plumbing repairs",
  "WorkRequested": "Fix reported leaks on floors 1 and 3",
  "Origin": "NONPM",
  "CreatedDate": "2026-04-23T07:00:00Z",
  "CompletedDate": "2026-04-23T12:00:00Z",

  "SourceAssets": null,
  "SourceSites": null,
  "SourceLocations": [
    {
      "LocationId": 3001,
      "LocationNo": "LOC-F1",
      "LocationName": "Floor 1 Restrooms",
      "SiteId": 2431,
      "SiteNo": "CC-01",
      "SiteName": "Convention Center",
      "RegionName": "Southeast",
      "Path": "Convention Center > Floor 1 Restrooms",
      "ParentLocationId": null,
      "ParentLocationName": null
    },
    {
      "LocationId": 3003,
      "LocationNo": "LOC-F3",
      "LocationName": "Floor 3 Kitchen",
      "SiteId": 2431,
      "SiteNo": "CC-01",
      "SiteName": "Convention Center",
      "RegionName": "Southeast",
      "Path": "Convention Center > Floor 3 Kitchen",
      "ParentLocationId": null,
      "ParentLocationName": null
    }
  ]
}
```

**What our code extracts:**
- Location Name/No 1: Floor 1 Restrooms (LOC-F1) — Location 1: Convention Center, Southeast
- Location Name/No 2: Floor 3 Kitchen (LOC-F3) — Location 2: Convention Center, Southeast

**Layman:** "One WO, two locations at the same Convention Center. The plumber is fixing the first floor restrooms and the third floor kitchen."

---

### Case 9 — Multiple Sites on one WO

A single WO covers work across multiple sites (e.g., a regional inspector visiting several campuses).

```json
{
  "WorkOrderId": 50009,
  "WorkOrderNo": "WO-50009",
  "Title": "Regional fire safety audit",
  "WorkRequested": "Annual fire extinguisher and alarm inspection across sites",
  "Origin": "PM",
  "CreatedDate": "2026-04-25T06:00:00Z",
  "CompletedDate": "2026-04-25T17:00:00Z",

  "SourceAssets": null,
  "SourceLocations": null,
  "SourceSites": [
    {
      "SiteId": 500,
      "SiteNo": "MSA-45",
      "SiteName": "Kentucky Arts Center",
      "RegionId": 61,
      "RegionName": "Southeast",
      "Description": "Main arts campus"
    },
    {
      "SiteId": 501,
      "SiteNo": "MSA-46",
      "SiteName": "Louisville Branch Office",
      "RegionId": 61,
      "RegionName": "Southeast",
      "Description": "Administrative office"
    }
  ]
}
```

**What our code extracts:**
- Site Name/No 1: Kentucky Arts Center (MSA-45) — Location 1: Southeast
- Site Name/No 2: Louisville Branch Office (MSA-46) — Location 2: Southeast

**Layman:** "One WO, two sites. The inspector visits both the arts center and the branch office for fire safety checks."

---

### Case 10 — Sparse/Null Fields (Location with minimal data)

Not all fields are guaranteed. Here a location only has `LocationName` — no `LocationNo`, no `RegionName`. Our code must handle this without crashing.

```json
{
  "WorkOrderId": 50010,
  "WorkOrderNo": "WO-50010",
  "Title": "Light fixture replacement",
  "WorkRequested": "Broken ceiling light in lobby",
  "Origin": "NONPM",
  "CreatedDate": "2026-04-26T14:00:00Z",
  "CompletedDate": "2026-04-26T15:00:00Z",

  "SourceAssets": null,
  "SourceSites": null,
  "SourceLocations": [
    {
      "LocationId": 7700,
      "LocationNo": null,
      "LocationName": "Main Lobby",
      "SiteId": 100,
      "SiteNo": null,
      "SiteName": "Downtown Office",
      "RegionName": null,
      "Path": null,
      "ParentLocationId": null,
      "ParentLocationName": null
    }
  ]
}
```

**What our code extracts:**
- Location Name/No 1: Main Lobby *(no LocationNo, so just the name — no parentheses)*
- Location 1: Downtown Office *(no RegionName, so just the site name)*

**Layman:** "The location only has a name and its parent site. Everything else is blank. Our code just uses what's available and doesn't crash."

---

## What Changes From Our Current Implementation

Our current `source_resolver.py` reads **flat fields** (`SourceSiteName`, `SourceSiteNo`) on the work order item. The actual payload uses **arrays** (`SourceSites[]`, `SourceLocations[]`) with nested objects — identical in structure to `SourceAssets[]`.

Changes needed:
1. Read from `SourceSites` array (not flat `SourceSiteName` fields)
2. Read from `SourceLocations` array (not flat `SourceLocationName` fields)
3. Handle null/missing nested fields gracefully — not all sub-fields are guaranteed
4. Return an error when all three source arrays are missing/empty — at least one is required
5. Locations always carry parent site info (`SiteName`/`SiteNo` inside each location object) — use confidently
