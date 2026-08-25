# 4. Template binding

The binding is the only place in the system that knows cell addresses. It is
**data, not code** ([ADR-003](./decisions/ADR-003-layout-profiles.md)): a
versioned JSON profile, generated from a real workbook, that maps the domain
model onto a specific master file.

## 4.1 Profile identity

```
profile_id : rg-flat-2026-08
master     : SDS-Template.xlsx
sha256     : f675b11fca3ea415f9c2e1c730d7a5e60bc44264a7241c266c51ddea92efcb4a
```

A profile is bound to one master file by hash. If the master changes — and it
will, because Comcast owns it — a new profile is issued with a new id. Every
`Submission` records the profile id and version it was generated under, so a
regeneration months later reproduces the file that was actually filed, not
whatever the current template happens to be.

The generator refuses to run if the master's hash does not match the profile.
Silently generating against an unexpected template is the failure mode that
produces a hundred wrong workbooks before anyone notices.

## 4.2 Header and enclosure fields

Direct one-to-one bindings. Full detail, including each cell's merge range and
the instruction recovered from its comment, is in
`spec/template-profile.rg-flat.json`.

| Field | Label | Value cell | Merge | Master prefill |
|---|---|---|---|---|
| `form_date` | `C3` | `C4` | `C4:D4` | — |
| `technician` | `E3` | `E4` | `E4:G4` | ⚠ `<stale technician name>` |
| `business_partner` | `H3` | `H4` | `H4:L4` | ⚠ `Sammons Construction` |
| `job_number` | `C7` | `C8` | `C8:D8` | — |
| `job_name` | `E7` | `E8` | `E8:G8` | — |
| `job_type` | `H7` | `H8` | `H8:J8` | ⚠ `SDU` |
| `hub_headend` | `K7` | `K8` | `K8:L8` | — |
| `enclosure_name` | `C11` | `C12` | `C12:E12` | — |
| `enclosure_alt_name` | `F11` | `F12` | `F12:G12` | — |
| `enclosure_manufacturer` | `H11` | `H12` | `H12:I12` | ⚠ `CommScope` *(only surviving dropdown)* |
| `enclosure_type` | `J11` | `J12` | `J12:L12` | ⚠ `OTE` |
| `location_address` | `C13` | `C14` | `C14:F14` | — |
| `lat_long` | `G13` | `G14` | `G14:I14` | — |
| `placement_class` | `J13` | `J14` | *(unmerged)* | ⚠ `Underground` |
| `pole_tag` | `K13` | `K14` | `K14:L14` | ⚠ `N/A` |
| `connected_sheaths` | `C15` | `C16` | `C16:D16` | — |
| `total_couplers` | `E15` | `E16` | `E16:F16` | — |
| `splices_performed` | `G15` | `G16` | `G16:H16` | — |
| `property_class` | `I15` | `I16` | `I16:J16` | ⚠ `ROW` |
| `otdr_performed` | `K15` | `K16` | `K16:L16` | ⚠ `No` |

⚠ marks a cell that arrives pre-populated in the blank master. The generator
**always writes all twenty**, including when the value matches the prefill. A
field that is merely "not overwritten" is indistinguishable from a field nobody
looked at, and five of these were inherited unexamined into both filed samples.

Notes block: `N10` header, six free-text lines `N11`…`N16`, each merged to `AV`.

### Value formatting

| Field | Written as |
|---|---|
| `form_date` | Excel date serial, preserving the master's `style_id` (samples: `46241` = 2026-08-07) |
| `connected_sheaths`, `total_couplers`, `splices_performed` | Numbers |
| `lat_long` | Text, format from profile (`ASM-006`) |
| everything else | Inline strings — see [`05-xlsx-generation.md`](./05-xlsx-generation.md) §5.4 |

`lat_long` has no agreed format: SP0302 wrote `N dd.dddddd W dd.dddddd`, SP0348
wrote `N dd.dddd W dd.dddd` (four decimals vs six), and the hidden `Example`
sheet shows a signed comma-separated pair. The profile carries a
`latLongFormat` strategy; default matches the samples' hemisphere-prefixed form
at six decimals.

## 4.3 The section grid

Fifteen sections, each with a label column and a value column:

| Section | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Label | C | F | I | L | P | S | V | Y | AB | AE | AH | AK | AN | AQ | AT |
| Value | D | G | J | M | Q | T | W | Z | AC | AF | AI | AL | AO | AR | AU |
| Span | 3 | 3 | 3 | **4** | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |

Section 4 is four columns wide because column N carries the Notes block.

| Row | Column | Domain field |
|---|---|---|
| 19 | label | Section header — **strategy-dependent**, see §4.4 |
| 20 | label | Role — **strategy-dependent**, see §4.4 |
| 21 | value | `cable.manufacturer` |
| 22 | value | `cable.manufacturedOn` (date serial) |
| 23 | value | `cable.footage` |
| 24 | value | `cable.cableId` |
| 25 | value | `cable.fiberCount` |
| 26–32 | label + value | Fiber assignments — §4.5 |
| 33 | label | `section.rackShelfPort` |
| 35 | label | `section.workPerformed` |
| 36–52 | label (full-width) | Splitter routing — §4.6 |

Unused sections are left exactly as the master ships them (the residual numbers
`3`…`15` in row 19). Both filed samples do this, so it matches what the reviewer
already accepts.

## 4.4 Strategy: the header/role rows

The two filed samples disagree about what rows 19 and 20 mean (§2.4). The profile
resolves this with a named strategy rather than a coin flip:

| Strategy | Row 19 | Row 20 | Matches |
|---|---|---|---|
| `count-in-header` | fiber count (`24CT`) | master default untouched (`Input`/`Output`) | SP0302 |
| `role-in-header` **(default)** | role (`INPUT`/`OUT`) | fiber count or split ratio (`48CT`, `1X16`) | SP0348 |

`role-in-header` is the default for three reasons: it is the newer sample; it is
the only one of the two that can express a splitter at all (SP0302 has no
splitter to express); and it leaves row 19 carrying information rather than
duplicating row 25's fiber count.

The app corrects `IMPUT` → `INPUT` on the way out. It does not correct historical
files.

## 4.5 Strategy: fiber assignments, rows 26–32

Seven rows, each with independently addressable label and value cells. The
observed encoding is **positional**: two cells on the same row in adjacent
sections are the two ends of one splice.

Rendering a `SpliceLink`, under the `aligned-pairs` strategy:

```
for each splice, in fiber order:
  row := next free row in 26..32
  write endpoint A into section A's cells on `row`
  write endpoint B into section B's cells on `row`

endpoint of kind 'port':  label ← "PORT", value ← port number
endpoint of kind 'fiber': label ← buffer colour, value ← fiber colour
```

Reproducing SP0302 exactly: one splice, `{ port 19 on section 1 }` ↔
`{ BR/WH on section 2 }` → `C27="PORT"`, `D27=19`, `F27="BR"`, `G27="WH"`.

Reproducing SP0348's section 3: four splices from the 1×16's ports 1–4 to the
24CT's blue tube → rows 28–31 carry `G28..G31 = 1,2,3,4` and
`I28..I31 = "BL"` with `J28..J31 = BL, OR, GR, BR`.

**Seven rows is a hard capacity limit.** A location with more than seven splices
per section pair cannot be expressed here. SP0348 has 35 splices and only fits
because most are represented in the routing region instead. The overflow policy
is a profile setting (`spliceOverflow`): `warn` (default), `truncate-with-note`,
or `spill-to-notes`. Resolving this properly needs Q4 and Q8 answered — a
technician who routinely exceeds seven splices per pair is telling us the
template does not fit the work.

## 4.6 Strategy: splitter routing, rows 36–52

The decoded convention from §2.4, expressed as a rendering rule:

```
staircase strategy
──────────────────
row 36                      ← splitter ratio, in each splitter section's cell
COM row for section N       ← 34 + N
k-th output of section N    ← (34 + N) + 1 + k     (k is 1-based)
```

Rendering `RouteLink`s under this strategy:

1. Assign each splitter a section slot. Order matters: the diagonal only reads
   correctly if downstream splitters occupy *increasing* slots, because section
   N's COM must land on the row carrying the upstream port that feeds it.
2. Write the ratio into row 36 of each splitter's section.
3. For each splitter, write `COM` at row `34 + N`.
4. For each assigned output port `k`, write the destination at row `34 + N + 1 + k`.
5. For the head splitter (the one fed from outside, section 2 in SP0348), write
   its port list down its own column so each port lands on the row of the
   splitter it feeds.

Verified against every splitter in SP0348 (table in §2.4).

**Two things this strategy deliberately changes:**

- SP0348 splits its 1×16's port list across two places — ports 1–4 in the value
  column at rows 28–31, ports 5–14 in the label column at rows 37–46. The
  strategy renders the whole list in one place. This is a visible difference from
  the reference file and must be shown to Gabriel before it ships (`ASM-013`).
- Sections 13 and 14 in SP0348 have a `COM` and a ratio but no destinations. The
  app can express that (an unassigned splitter) but flags it as a warning, not an
  error — it may be a spare leg, or it may be an omission.

**Capacity.** Rows 36–52 give seventeen rows. The staircase consumes one row per
splitter plus one per output, so a location with a 1×16 fully populated by 1×2s
(16 splitters × 2 outputs = 48 rows) does not fit. SP0348 fits because only 12
splitters and 20 destinations were recorded. The generator computes required rows
before writing and fails validation with a specific message rather than
truncating. Whether Comcast expects multiple workbooks for such a location is
Q4, and it is the single most likely reason the pilot needs a second workbook
per location.

## 4.7 Pictures

Nine slots, all merged blocks on the `Pictures` sheet:

| Bucket | Caption cell | Caption | Image cell | Image block |
|---|---|---|---|---|
| `enclosure_location` | `B4:F4` | Location (Requires Point of Reference/Landmark) | `B5` | `B5:F16` |
| `enclosure_before` | `G4:K4` | Before | `G5` | `G5:K16` |
| `enclosure_after` | `L4:P4` | After | `L5` | `L5:P16` |
| `splicing_1` | `B19:F19` | 1 | `B20` | `B20:F31` |
| `splicing_2` | `G19:K19` | 2 | `G20` | `G20:K31` |
| `splicing_3` | `L19:P19` | 3 | `L20` | `L20:P31` |
| `splicing_4` | `B32:F32` | 4 | `B33` | `B33:F44` |
| `splicing_5` | `G32:K32` | 5 | `G33` | `G33:K44` |
| `splicing_6` | `L32:P32` | 6 | `L33` | `L33:P44` |

Bucket → slot mapping is a profile setting because the evidence contradicts the
instructions. The workbook's own `B91` comment asks for ground-level location,
before, and after — but **both filed samples left all three enclosure slots empty
and filled the splicing slots instead**. Two strategies:

| Strategy | Behaviour |
|---|---|
| `as-filed` **(default)** | Everything into `splicing_1..6` in capture order. Matches both references. |
| `as-instructed` | `enclosure_location/before/after` into their named slots; tray and closed-condition shots into `splicing_1..6`. Matches the workbook's written instruction. |

Default is `as-filed` because matching what the reviewer has already seen beats
matching what the template says, until someone confirms which one the reviewer
actually wants (`ASM-008`, Q9).

## 4.8 OTDR

Hidden sheet, gated on `enclosure.otdrPerformed`. The blank master exposes one
forward/return pair:

| Slot | Caption | Fiber # | Image block |
|---|---|---|---|
| `hub_to_endsite_forward` | `B3:E3` | `F3:I3` → `G3` | `B4:I19` |
| `hub_to_endsite_return` | `J3:M3` | `N3:Q3` → `O3` | `J4:Q19` |

The hidden `Example` sheet shows **two** pairs — hub-to-endsite and
endsite-to-hub, four images and four fiber numbers. The blank master exposes only
the first pair. Neither filed sample performed an OTDR, so there is no evidence
which is correct. The profile declares the slots it has; when a location records
more OTDR tests than the profile can hold, validation fails with the count rather
than dropping traces. This is Q12 and needs one accepted OTDR workbook to close.

## 4.9 Filename generation

Observed: `SDS AVALON R SEC 1 SP0302.xlsx` and `SDS Template SP0348.xlsx` — the
second still carrying the word "Template" from whatever it was copied from.

Profile setting `namingPattern`, default:

```
SDS {jobName|upper} {locationName|upper}.xlsx
→ "SDS AVALON RIDGE SEC 1 SP0348.xlsx"
```

This reproduces neither sample exactly: SP0302's `AVALON R SEC 1` is an
abbreviation of `avalon ridge sec 1` with no derivable rule, and SP0348's name is
an accident. The pattern is per-project and editable, so an abbreviation can be
set as a project-level display name once Gabriel confirms the convention
(`ASM-009`, Q5).

## 4.10 What a profile contains

```
profile
├── id, version, masterSha256
├── singleFields[]        cell + merge + type + master prefill
├── notesBlock            header cell, six line cells
├── sectionGrid           15 × { labelCol, valueCol, span }, row map
├── strategies
│   ├── headerRole        count-in-header | role-in-header
│   ├── fiberAssignment   aligned-pairs
│   ├── routing           staircase
│   ├── pictures          as-filed | as-instructed
│   ├── latLongFormat
│   └── spliceOverflow    warn | truncate-with-note | spill-to-notes
├── pictureSlots[]        bucket → cell + block
├── otdrSlots[]
├── vocabularies          defined names + inline validations
└── namingPattern
```

Profiles are versioned, reviewable, and deployable without a code release. When
Comcast changes the form, the work is: obtain the new master, run
`extract_template_spec.py`, diff, adjust strategies, verify in Excel, publish.
That is the bounded "template maintenance" the commercial terms promise, and it
is bounded precisely because it never requires touching the generator.
