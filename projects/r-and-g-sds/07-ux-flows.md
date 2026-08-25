# 7. UX flows

## 7.1 The design target

A technician standing at an open vault, phone in one hand, gloves on, sun on the
screen, patchy signal. Target: **under four minutes of active entry** for a
simple splice location, photos included, with nothing left to finish at home.

Three rules follow from that and drive every screen:

1. **Never ask twice.** Eleven header fields are constant within a job. They are
   inherited, shown, and confirmed once — not retyped per location.
2. **Never block on the network.** Every screen works offline. Sync is a status
   indicator, not a step.
3. **Never make them type what they can pick.** Cable manufacturers, fiber
   colours, split ratios, and enclosure types all come from the workbook's own
   vocabularies. `COMPSCOPE` should not be typeable.

## 7.2 Technician: capture a location

```
Jobs ──▶ Job board ──▶ Location ──▶ Sections ──▶ Splices ──▶ Photos ──▶ Review ──▶ Submit
                          │            │            │           │
                          └── GPS      └── cables   └── fiber   └── buckets
                              address      splitters    picker
```

### Job board

The list of locations for the active job, grouped by state, with a persistent
progress line — *"48 of 170 complete"*. This is where a 200-terminal map stops
being terrifying. Filters: mine, unstarted, drafts, returned, submitted.

A returned location is visually distinct and sorts to the top, carrying the
supervisor's reason.

### Location: identity and placement

Opens with project defaults already filled and visibly marked as inherited. The
technician confirms them **once per location** with a single action, and the
confirmation is recorded — because the blank master ships with a stale technician
name and five other stale defaults that both filed samples inherited unexamined.

- **GPS** is captured on arrival with accuracy shown. One tap to re-capture.
- **Address** is reverse-geocoded as a *suggestion*, always editable, and the app
  records whether it was geocoded, edited, or typed. The workbook's own
  instruction is shown inline: *"Street address or nearest cross streets. If
  using cross streets, include direction location (ex NE corner of)."*
- **Placement** drives the form: choosing `aerial` reveals Pole Tag and makes it
  required. Choosing `isp` reveals Rack/Shelf/Port on the sections.
- **OTDR?** gates the whole OTDR step later. Off by default, matching both
  references.

Every field carries the customer's own comment text as help. Those seventeen cell
comments are the only written specification anyone has; putting them in front of
the technician at the moment of entry is free accuracy.

### Sections: cables, splitters, taps

A horizontal strip of up to fifteen slots, mirroring the workbook, but the
technician picks a **type** first — cable, splitter, or tap — and the form
follows. That is the type-driven behaviour the original template intended before
it was flattened, restored in the app without changing the file.

- **Cable**: manufacturer (picker, canonical casing), manufacture date, footage,
  cable ID, fiber count. Footage and fiber count are numeric with sane bounds.
- **Splitter**: ratio (picker: 1x2 … 1x64). Choosing `1x16` creates sixteen
  output ports the routing step can assign.
- **Tap**: tap identifier, validated for shape.

Recently used values within the job are offered first. On a 170-terminal map, the
same two cable manufacturers appear constantly.

### Splices: the fiber picker

The step that saves the most time and prevents the most rejections.

```
   from                     to
 ┌──────────────┐        ┌──────────────┐
 │ Section 1    │        │ Section 2    │
 │ 24CT AFL     │   ⟷    │ 288CT Corning│
 │ ● PORT 19    │        │ ● BR / WH    │
 └──────────────┘        └──────────────┘
        [ + next fiber ]      [ done: 1 splice ]
```

- Pick the two sections once; the app keeps them and advances fiber by fiber.
- Fibers advance in TIA-598 order (BL · OR · GR · BR · SL · WH · RD · BK · YL ·
  VI · RS · AQ), so recording SP0348's four-fiber run is four taps, not sixteen.
- Skipping a fiber is allowed but flagged, because a jump from GR to WH is either
  deliberate or a mistake and only the technician knows which.
- A running splice count is always visible and reconciles against the
  `Splices Performed` header field before submission.

### Routing: the splitter cascade

For splitter locations, a visual tree rather than a grid:

```
48CT input
  └── 1x16  (section 2)
        ├── port 1..4  →  24CT Corning, blue tube, BL OR GR BR
        ├── port 5     →  1x2 (section 3) ── NP0017
        │                                 └─ NP0018
        ├── port 6     →  1x2 (section 4) ── NP0010
        │                                 └─ NP0011
        └── …
```

The technician assigns ports by picking a destination — an existing tap, another
splitter, or a new tap ID. Unassigned legs stay visible as empty slots, which is
how the two unassigned splitters in SP0348 would have been caught at the time
rather than discovered later.

The app renders this tree into the workbook's staircase layout
([`04-template-binding.md`](./04-template-binding.md) §4.6). The technician never
sees a cell address.

### Photos: named buckets

Six required-by-default buckets, each a large tap target with a thumbnail once
filled:

```
[ Location ]  [ Before ]  [ After ]
[ Tray 1   ]  [ Tray 2  ]  [ Closed ]
```

- Capture goes straight to the local blob store; the thumbnail renders from local
  data, so it appears instantly with no signal.
- GPS and timestamp are captured **structurally** by the app alongside the image,
  not read from a pixel overlay.
- The existing GPS-camera app remains usable — its overlay is preserved in the
  original. Whether that app is mandatory is Q9; the design works either way.
- Required buckets are configurable, because both filed samples left the three
  enclosure slots empty despite the template asking for them.

### OTDR (conditional)

Appears only when the location says OTDR was performed. Fiber number plus trace
image per test, with direction and forward/return. Hidden entirely otherwise —
which is both references' behaviour.

### Review and submit

A single scrollable summary: every field, every splice, every photo, every route,
with problems pinned to the top and each one tappable straight to its field.

- **Errors** block submission. **Warnings** require an explicit acknowledgement
  that is recorded in the audit trail.
- Submission is local and instant. The outbox shows delivery status afterwards.
- A technician can leave a location in draft indefinitely; drafts are never lost
  to a failed upload.

## 7.3 Supervisor: review

Desktop, because this happens at a laptop.

**Queue.** Everything submitted, oldest first, with job, location, technician,
splice count, photo count, and any warnings the technician acknowledged.

**Review view.** The captured record side by side with a preview of what will be
generated. Photos at full resolution. Every inherited default marked as such, so
a wrong project default is visible rather than buried.

**Return.** Reasons attach to specific fields. The technician sees them pinned on
the location, on their phone, in the field. A returned location goes back to
draft without losing anything.

**Approve.** Generates the workbook, runs the package assertions, records the
hash, and fires the single idempotent billing event. If any assertion fails, the
approval is blocked with the specific failure — never a partially valid file
delivered quietly.

**Export.** Per location, or per job as a ZIP with the configured naming pattern.

## 7.4 Operator: template profiles

Rarely used, and the reason support stays bounded.

- Upload a new master workbook; the extractor produces a candidate profile and a
  diff against the current one.
- Adjust strategies (§4.4–§4.7) and preview against both golden fixtures.
- Verify in Microsoft Excel — the gate that cannot be automated.
- Publish. New generations use it; existing submissions keep theirs.

## 7.5 Field realities the design accounts for

| Reality | Response |
|---|---|
| Gloves, sunlight, one hand | Large targets, high contrast, no hover, no drag |
| No signal in a vault | Everything offline; sync is ambient |
| Battery | No polling, no background location, photos compressed on-device |
| Interruptions | Every field saves on change; there is no "save" button to forget |
| 170–200 locations on one map | Progress count always visible; recently-used values offered first |
| Wrong data is worse than slow data | Vocabularies over free text; confirmation over inheritance; warnings recorded, not swallowed |
