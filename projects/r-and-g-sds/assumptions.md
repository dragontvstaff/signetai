# Assumption registry

Every rule in this design that is inferred rather than stated by the customer.
Each has an id, the evidence behind it, the config key that changes it, and what
breaks if it is wrong.

The registry exists so that a demo can be shown to Gabriel with an honest answer
to "why does it do that?" for every behaviour — and so that no assumption is
discovered only by a reviewer rejecting a file.

**Blast radius** is what has to change when the assumption turns out wrong:
`config` (a value), `strategy` (a named rendering rule), `schema` (data model),
or `premise` (the product changes).

| ID | Assumption | Evidence | Config key | Blast radius |
|---|---|---|---|---|
| `ASM-001` | The flattened `Splicing Record` schema — not the hidden `Example` schema — is what the reviewer expects | Both filed samples use it; the `Example` sheet's type-driven labels are unreachable from the visible sheet | `templateProfileId` | **strategy** — a second profile |
| `ASM-002` | The form date is the field-work date | Both samples carry a date one day after the photo date; both were sent three days later | `formDateRule` | config |
| `ASM-003` | Every inherited project default must be explicitly confirmed per location | The master ships nine prefills including a stale technician name; both samples inherited five unexamined | rule `H-02` severity | config |
| `ASM-004` | One workbook per location (enclosure or tap) | `N5` red text; Gabriel: "para cada enclosure y para cada OT" | — | **premise** if wrong |
| `ASM-005` | XLSX is the delivered artifact; PDF is not required | Both samples are XLSX; no PDF in evidence; LibreOffice rendering is unusable | `deliveryFormats` | **premise** — PDF needs a new rendering surface |
| `ASM-006` | Lat/long format is hemisphere-prefixed decimal, six places | SP0302 uses `N dd.dddddd W dd.dddddd` (six places); SP0348 uses four places; `Example` uses signed decimal | `latLongFormat` | config |
| `ASM-007` | Unused sections keep the master's residual numbers | Both samples leave `3`…`15` untouched in row 19 | `unusedSectionPolicy` | config |
| `ASM-008` | Photos go into the six splicing slots; the three enclosure slots may stay empty | **Both** samples fill only splicing slots, despite comment `B91` requiring location/before/after | `pictures` strategy + rule `E-02` | strategy |
| `ASM-009` | Filenames follow `SDS {JOB} {LOCATION}.xlsx` | SP0302 matches with an abbreviated job name; SP0348 is `SDS Template SP0348.xlsx`, plainly accidental | `namingPattern` | config |
| `ASM-010` | Location names follow the job's own pattern (`SP####`) | `sp0302`, `sp0348` in both name and alternate-name cells | rule `H-04` pattern | config |
| `ASM-011` | Exactly one section is the input; the rest are outputs | SP0302 uses the master's `Input`/`Output` labels; SP0348 writes `IMPUT`/`OUT` in row 19 | rule `S-02` severity | config |
| `ASM-012` | In the routing region, splitter section N's `COM` sits at row 34+N, and that row carries the upstream port feeding it | Holds for all 12 splitters in SP0348, and section 2's port list aligns with it across all ten rows | `routing` strategy | strategy |
| `ASM-013` | A splitter's port list renders in one contiguous place | SP0348 splits its 1×16 list across two regions (ports 1–4 at rows 28–31, ports 5–14 at rows 37–46) | `routing` strategy | strategy — **visible difference from the reference** |
| `ASM-014` | A 2048px long-edge render is sufficient for the reviewer | SP0302's originals are 2.3–4.7 MB each; nobody has confirmed whether reviewers zoom to read labels | `renderLongEdge` | config |
| `ASM-015` | Destination identifiers match `^NP\d{4}$` | 20 occurrences in SP0348, all conforming; Gabriel's voice note says "MP 009", suggesting an `MP` variant exists | rule `R-07` pattern | config |
| `ASM-016` | Splice counts should reconcile with the header count | Comment `G15` says "total amount of splices performed during work visit"; SP0302 declares 1 and records 1 | rule `X-01` severity | config |
| `ASM-017` | "Total Couplers" means mux/splitter count | Comment `E15`: "total count of mux's/splitters in the enclosure" — but SP0348 declares 3 against 13 splitters drawn | rule `X-02` severity | config |
| `ASM-018` | Fibers are assigned in TIA-598 order | SP0348 section 3 walks BL, OR, GR, BR — the first four of the blue tube, in order | `fiberOrder` | config |
| `ASM-019` | The app's PWA camera may replace the GPS-stamped camera app | Overlays are informational; the app captures GPS structurally. Unconfirmed whether the overlay itself is required evidence | `requireStampedPhotos` | strategy — could force using the external camera |
| `ASM-020` | Row capacity (7 pair rows, 17 grid rows) is sufficient for real locations | SP0348 fits at 13 splitters and 20 destinations; larger locations exist on 200-terminal maps | rule `R-10` | **premise** — may force multiple workbooks per location |

## Reading the registry

**Five assumptions have a blast radius beyond config.** Those are the ones worth
a direct question:

- `ASM-004` and `ASM-020` together decide whether "one location, one workbook"
  survives contact with a 200-terminal map.
- `ASM-005` decides whether a rendering surface must exist at all.
- `ASM-012` and `ASM-013` decide whether generated splitter workbooks look like
  the ones the reviewer has seen.
- `ASM-019` decides whether the app owns photo capture or defers to an external
  camera — which changes the field flow substantially.

Everything else is a value in a JSON document, changeable per project, without a
deploy.
