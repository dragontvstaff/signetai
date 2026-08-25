# 2. What the supplied files actually prove

Everything below was extracted from the packet's workbooks by
`tools/extract_template_spec.py`, which reads the OOXML package directly. Cell
references are reproducible; nothing here is transcribed by hand.

Sources:

| File | SHA-256 (first 16) |
|---|---|
| `SDS-Template.xlsx` (blank master) | `f675b11fca3ea415` |
| `SDS AVALON R SEC 1 SP0302.xlsx` | recorded in `spec/observed-fills.json` |
| `SDS Template SP0348.xlsx` | `27d682c84ec57b52` |

## 2.1 The workbook is five sheets, three hidden

| Sheet | State | Role |
|---|---|---|
| `Splicing Record` | visible | The form. 909 merged ranges, 15 equipment sections, a large unlabelled free-form region. |
| `Pictures` | visible | Nine photo slots: three enclosure, six splicing. |
| `Lists` | **hidden** | Controlled vocabularies and the dynamic label machinery. |
| `OTDR Shots` | **hidden** | Forward/return trace images and fiber numbers. |
| `Example` | **hidden** | A completed sample carrying the *original* field schema. |

The hidden sheets are not decoration. `Lists` backs twelve defined names that the
workbook's validations reference; `Example` is the only surviving description of
what the form was designed to collect.

## 2.2 Finding 1 — the blank master is a flattened derivative, not the original

This is the most consequential finding in the packet, and it is not recorded
anywhere in the takeover documents.

The hidden `Example` sheet and the visible `Splicing Record` describe **two
different schemas** for the same region:

| | Hidden `Example` (original design) | Visible `Splicing Record` (what R&G files) |
|---|---|---|
| Section header row | Equipment-type dropdown | Literal numbers `1`…`15` |
| Field labels | Type-driven: `Sheath` → Name, Reel #, Sheath Mfr., Mfg. Date, Fiber Count, Buffer Size, Buffer Type, Ribbon, Case Footage, Span Footage, Splice Type | Fixed five: `Cable Manufacture`, `Cable Date`, `Cable Footage`, `Cable ID`, `Cable Count` |
| Other types | `Mux/Coupler`, `Fiber Tap/Tail`, `Node Cable`, `Demark`, each with its own field list | none |
| Validations | Driven from `Lists` via defined names | **one** survives (`H12:I12`, enclosure manufacturer) |

Three independent pieces of evidence confirm the visible sheet was edited down
from the original:

1. **The cell comments still describe the original.** `Splicing Record!C19`
   carries the instruction *"Using the drop down options, choose the equipment
   types that splicing occurred for. Each option will provide a list of required
   information."* That comment is anchored to a cell that now contains the
   literal `1`.
2. **Two comments are orphaned.** `B53` ("Enter the fiber number where the OTDR
   was performed…") and `B91` ("Provide photos of the enclosure location, from
   ground level…") point at rows that are empty on `Splicing Record` but hold
   `OTDR Examples` and `Picture Examples` on the `Example` sheet.
3. **The machinery is intact but disconnected.** `Lists` still holds the
   category → field → options tables and the array formulas that fed the dynamic
   labels; twelve defined names still resolve; nothing on `Splicing Record`
   references them any more.

The master also carries editing residue: a stray `fdssd` at `Splicing Record!F44`,
and nine prefilled values sitting in cells that should be per-location:

| Cell | Field | Stale value |
|---|---|---|
| `E4` | technician | `<stale technician name>` |
| `H4` | business partner | `Sammons Construction` |
| `H8` | job type | `SDU` |
| `H12` | enclosure manufacturer | `CommScope` |
| `J12` | enclosure type | `OTE` |
| `J14` | placement | `Underground` |
| `K14` | pole tag | `N/A` |
| `I16` | private property / ROW | `ROW` |
| `K16` | OTDR? | `No` |

Both filled samples inherited five of these unchanged. Whether that was a
deliberate choice or an unnoticed default is Q11 in the packet and remains open.

**Design consequence.** There are two candidate schemas, and only one of them is
what the reviewer has actually seen. The generator therefore binds to a named,
versioned *template profile* rather than to "the SDS format"
([ADR-003](./decisions/ADR-003-layout-profiles.md)). The flattened profile
(`rg-flat-2026-08`) is what ships; the original type-driven schema is a second
profile to build only if the customer confirms it.

## 2.3 Finding 2 — the section grid is a clean, regular binding

Fifteen equipment sections run left to right across `Splicing Record`. Each has a
**label column** and a **value column**:

| Section | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Label col | C | F | I | L | P | S | V | Y | AB | AE | AH | AK | AN | AQ | AT |
| Value col | D | G | J | M | Q | T | W | Z | AC | AF | AI | AL | AO | AR | AU |

Section 4 spans four columns (`L19:O19`) rather than three, because column N is
consumed by the Notes block above. Every other section spans three. The full
per-section geometry is in `spec/template-profile.rg-flat.json`.

Row meanings:

| Row | Column used | Content |
|---|---|---|
| 19 | label | Section header (master: `1`…`15`) |
| 20 | label | `Input` / `Output` (master fills sections 1–2 only) |
| 21–25 | value | Cable Manufacture, Cable Date, Cable Footage, Cable ID, Cable Count |
| 26–32 | **both** | **Unlabelled.** Label and value cells are separately addressable. |
| 33 | label | Rack/Shelf/Port (ISP) |
| 35 | label | Work Performed |
| 36–52 | label (full-width merge) | **Unlabelled.** One merged cell per section per row. |

Rows 21–25 bind cleanly and both samples round-trip through them without
ambiguity. Rows 26–32 and 36–52 are where the design breaks down.

## 2.4 Finding 3 — the free-form regions carry real data under invented conventions

The two filled references were completed by the *same technician* on the *same
day* for the *same job* — and they use **different conventions** in the same
cells.

### Row 19/20 disagree between samples

| | SP0302 | SP0348 |
|---|---|---|
| Section 1 row 19 | `24CT` (fiber count) | `IMPUT` (role, misspelled) |
| Section 1 row 20 | `Input` (master default, untouched) | `48CT` (fiber count) |
| Section 2 row 19 | `288CT` | `OUT` |
| Section 2 row 20 | `Output` (untouched) | `1X16` (splitter ratio) |

SP0302 puts fiber count in the header row and leaves the role labels alone.
SP0348 puts role in the header row and count/ratio in the role row. Both are
readable by a human; neither is machine-parseable; a generator must pick one.

### Rows 26–32 carry fiber-level splice assignments

SP0302, section 1 row 27: label `PORT`, value `19`. Section 2 row 27: label `BR`,
value `WH`. Decoded: *the 24CT cable at port 19 is spliced to the 288CT cable,
brown buffer tube, white fiber.* One splice — matching `Splices Performed = 1`.

SP0348, section 3 rows 28–31: `BL`/`BL`, `BL`/`OR`, `BL`/`GR`, `BL`/`BR` —
blue buffer tube, fibers blue, orange, green, brown. Aligned on the same rows,
section 2's value column holds `1`, `2`, `3`, `4`: the 1×16 splitter's output
ports 1–4.

**The row is the relationship.** Two cells on the same row in adjacent sections
are the two ends of one splice. That is the entire fiber-assignment schema, and
it is expressed purely by vertical alignment.

### Rows 36–52 are a hand-drawn routing diagram on a diagonal

SP0348 records 13 splitters and 20 destination taps in this region. Row 36 holds
one ratio per section: sections 3–14 carry `1X2` ×11 and `1X4` ×1; section 2
carries the `1X16` (in row 20).

The layout follows a decodable rule:

```
splitter in section N  →  its COM marker sits at row 34 + N
                          its k-th output sits at row (34 + N) + 1 + k
```

Verified against every splitter in SP0348:

| Section | Ratio | COM row | Output rows | Destinations |
|---|---|---|---|---|
| 3 | 1X2 | 37 | 39, 40 | NP0017, NP0018 |
| 4 | 1X2 | 38 | 40, 41 | NP0010, NP0011 |
| 5 | 1X2 | 39 | 41, 42 | NP0020, NP0022 |
| 6 | 1X2 | 40 | 42, 43 | NP0023, NP0024 |
| 7 | 1X2 | 41 | 43, 44 | NP0025, NP0026 |
| 8 | 1X2 | 42 | 44, 45 | NP0028, NP0016 |
| 9 | 1X2 | 43 | 45, 46 | NP0015, NP0014 |
| 10 | 1X2 | 44 | 46, 47 | NP0013, NP0012 |
| 11 | 1X2 | 45 | 47 | NP0019 *(one leg only)* |
| 12 | 1X4 | 46 | 48, 49, 50 | NP0008, NP0021, NP0027 *(three legs)* |
| 13 | 1X2 | 47 | — | *(none recorded)* |
| 14 | 1X2 | 48 | — | *(none recorded)* |

The diagonal is not decoration: **section 2's output list aligns with it.**
Section 2 (the 1×16) lists ports `5`…`14` down rows 37–46, and section N's COM
sits on exactly the row carrying the 1×16 port that feeds it. Port 5 → splitter
in section 3, port 6 → section 4, and so on. The technician drew a cascade
diagram: a 1×16 feeding twelve downstream splitters, each fanning out to taps.

Two caveats, both important:

- **The port→splitter alignment is an inference**, not a stated rule. It is
  consistent across all ten aligned rows, which is strong, but it is not
  confirmed. Registered as `ASM-012`.
- **Section 2 breaks its own convention.** Ports 1–4 are in the *value* column at
  rows 28–31 (aligned with section 3's fiber colours), while ports 5–14 are in the
  *label* column at rows 37–46. Two placements for one splitter's port list.

### The data disagrees with itself

`Total Couplers = 3` on SP0348, but the routing region shows 13 splitters. Either
"couplers" means something narrower than "splitters", or the count is wrong. It
is exactly the class of error a cross-field check catches before submission
([`08-validation.md`](./08-validation.md), rule `X-02`).

Spelling drift is visible too: `IMPUT` for input, `COMPSCOPE` for CommScope
(twice), `AFL` where the controlled list says `AFL Tel`, `450-D` where the
`Example` sheet says `450D`.

**Design consequence.** None of these free-form regions can be treated as text
boxes to be echoed. The app must own a real model — cables, fibers, splitters,
ports, destinations — and *render* it into these cells under a named layout
strategy. That is [`03-domain-model.md`](./03-domain-model.md) and
[`04-template-binding.md`](./04-template-binding.md).

## 2.5 Finding 4 — the photos use Excel's in-cell rich-value format

The field photos are **not** floating drawings. They are `_localImage` rich
values referenced from the cell's `vm` attribute. The full mechanism, present in
both filled samples and absent from the blank master:

```
Pictures!B20   <c r="B20" t="e" vm="2"><v>#VALUE!</v></c>
                            │
xl/metadata.xml             └─→ valueMetadata[2] → XLRICHVALUE bk → rvb i="1"
                                     │
xl/richData/rdrichvalue.xml          └─→ <rv s="1"><v>0</v><v>5</v></rv>
                                              │        │
xl/richData/rdrichvaluestructure.xml    s=1 = └─ _localImage { _rvRel:LocalImageIdentifier, CalcOrigin }
                                                       │
xl/richData/richValueRel.xml                   index 0 └─→ <rel r:id="rId1"/>
                                                                    │
xl/richData/_rels/richValueRel.xml.rels                             └─→ ../media/image1.png
```

Consequences, all of them hard:

- **Non-Microsoft parsers see `#VALUE!`.** The image bytes are present and
  correctly related; the reader simply does not implement the format. A
  LibreOffice PDF export of SP0302 produced 20 pages, 14 `#VALUE!` fallbacks,
  and zero rendered photos.
- **`openpyxl` load/save will not round-trip this.** It does not model
  `richData`, so a naive read-modify-write silently drops every photo while
  reporting success. This is the single most likely way to ship a broken file.
- **The blank master already contains a rich value.** Its
  `rdrichvaluestructure.xml` declares one `_error` structure (backing the spilled
  array `#VALUE!` cells on `Lists`). A generator must *append* to the existing
  rich-value tables, not replace them — index 0 is already taken.
- **Verification requires Microsoft Excel.** There is no substitute.

Photo slot usage in the two samples, which is itself a finding:

| Slot | Cell | SP0302 | SP0348 |
|---|---|---|---|
| Enclosure — Location | `B5` | *empty* | *empty* |
| Enclosure — Before | `G5` | *empty* | *empty* |
| Enclosure — After | `L5` | *empty* | *empty* |
| Splicing 1 | `B20` | photo | photo |
| Splicing 2 | `G20` | photo | photo |
| Splicing 3 | `L20` | photo | photo |
| Splicing 4 | `B33` | photo | photo |
| Splicing 5 | `G33` | — | photo |
| Splicing 6 | `L33` | — | — |

**Every photo went into the splicing slots; the three enclosure slots were never
filled in either sample** — even though the workbook's own instruction (`B91`
comment) asks for ground-level location, before, and after shots. Either the
reviewer does not enforce the enclosure slots, or both samples are
non-compliant. Unresolved (Q2 in the SP0302 intake); registered as `ASM-008`.

## 2.6 Finding 5 — project data repeats, location data does not

Seven fields are byte-identical across both samples:

`form_date` `2026-08-07` · `technician` *(same person)* ·
`business_partner` `Sammons Construction` · `job_number` `2541631` ·
`job_name` `avalon ridge sec 1` · `job_type` `SDU` · `hub_headend` `TXWS`

Plus four defaults inherited from the master: enclosure manufacturer `CommScope`,
placement `Underground`, property class `ROW`, OTDR `No`. Enclosure type `450-D`
is identical in both but differs from the master's `OTE`, so it is a job-level
choice, not a template default.

This is the single clearest product signal in the evidence: **eleven of twenty
header fields never change within a job.** They belong on a Project record,
entered once, inherited with explicit confirmation.

## 2.7 Finding 6 — file naming is already inconsistent

`SDS AVALON R SEC 1 SP0302.xlsx` and `SDS Template SP0348.xlsx` — two files, same
job, same day, same technician, two conventions. The second still carries the
word "Template" from the file it was copied from. Naming must be generated from a
configurable pattern (`ASM-009`), not left to the technician.

## 2.8 Finding 7 — payload size is a cost driver

SP0302 embeds four field photos totalling 13.2 MB in a 13.4 MB workbook; SP0348
embeds five totalling 14.1 MB in a 14.2 MB workbook. Extrapolated at 70
locations/week/technician, that is roughly
**1 GB of raw evidence per technician per week** — ~50 GB/year/technician before
any generated output.

This lands directly on hosting cost, backup windows, mobile upload behaviour on
a jobsite, and the per-technician component of the pricing model. It also argues
for storing a full-resolution original once and embedding a downscaled derivative
sized to the target cell ([ADR-005](./decisions/ADR-005-evidence-originals.md)).

## 2.9 Controlled vocabularies recovered

From `Lists` and the workbook's defined names — usable immediately as app
dropdowns, and the basis for correcting `COMPSCOPE`-class drift:

| Vocabulary | Values |
|---|---|
| `Sheath_Manufacturer` | AFL Tel, Amphenol, CommScope, Corning, Draka, Prysmian |
| `Mux_Splitter_Manufacturer` | AFL Tel, All Systems, Amphenol, Arris, Aurora, Cisco, CommScope, Corning, Finisar, II-VI Photonics, Infinera, Lumentum, Motorola, Net Tech, PPC, Radiant, TE Conn, TFC Amphenol, Times Fiber, Tyco |
| `Mux_Splitter_Type` | CWDM, DWDM, BWDM, Splitter |
| `Port_Config` | 1x2, 1x3, 1x4, 1x8, 1x16, 1x24, 1x32, 1x64, 4ch, 8ch, 12ch, 16ch, 20ch |
| `Splice_Type` | Butt Splice, Ring Cut |
| `Ribbon` | Yes, No |
| `Tail_Length` | 100, 250, 500, 750, 1000, 1500, 1750, 2000, 2500 |
| `Location` | Exterior, Interior |
| `Node_Cable_Manufacturer` | Amphenol |
| Enclosure manufacturer *(inline validation on `H12:I12`)* | 3M, ADC Tel, AFL Tel, AllSystems, Arris, Channel, Clearfield, CommScope, Corning, Fiberdyne, Fons, Keptel, Multilink, Raychem, TE, TVC, Tyco, Other |

Equipment categories and their per-type field lists (`Lists!A:B`) are in
`spec/vocabularies.json`. Note `Port_Config` contains `1x16`, and SP0348 wrote
`1X16` — case normalisation is needed, and the app should propose the canonical
casing rather than accept either.

## 2.10 Instructions recovered from cell comments

The blank master carries seventeen cell comments that no printed copy shows.
They are the closest thing to a written specification the customer has provided:

- **`C13` Location** — "Street address or nearest cross streets. If using cross
  streets, include direction location (ex NE corner of)"
- **`G13` Lat/Long** — "Latitude and longitude as shown in the field"
- **`J13` placement** — "Drop down options: Aerial, underground or inside plant location"
- **`K13` Pole Tag** — "If aerial, document the pole tag of the nearest pole"
- **`C15`** — "Enter the total count of sheaths connected to the enclosure"
- **`E15`** — "Enter total count of mux's/splitters in the enclosure"
- **`G15`** — "Enter the total amount of splices performed during work visit"
- **`I15`** — "Enclosure is located in private property or in the right of way"
- **`K15`** — "Was an OTDR performed here?"
- **`B53`** — "Enter the fiber number where the OTDR was performed for each
  location and a clear image for each OTDR test that was performed."
- **`B91`** — "Provide photos of the enclosure location, from ground level.
  Provide the pole/vault/ped interior before and after. Provide photos of the
  tray(s) where the splicing occurred for each splice post-splicing."

`E15` resolves the `Total Couplers` ambiguity from §2.4: it means *mux's/splitters
in the enclosure*, which makes SP0348's `3` inconsistent with 13 splitters drawn.
`B91` establishes the intended photo set, which neither sample satisfies. These
comments become the in-app help text verbatim — the customer's own words are the
safest available guidance.
