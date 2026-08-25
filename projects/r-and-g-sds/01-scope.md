# 1. Scope

## 1.1 The problem, stated precisely

Comcast requires an SDS workbook — "This document MUST be completed for each
location where fiber splicing occurred during construction" (`Splicing Record!N5`,
red text; Gabriel points at this line in the voice note) — for every enclosure
and every tap/terminal R&G touches.

The workbook is not a form. It is a 49-column, 909-merged-range spreadsheet with
five sheets, three of them hidden, whose photo slots use an Excel-only rich-value
image format. Filling one by hand means transcribing values that are identical
across every location on the job, retyping cable IDs from photos, and hand-drawing
a splitter routing diagram into unlabelled cells.

The cost is measured in unpaid evening hours:

- 50–70 locations per technician per week (Gabriel, voice note).
- Some maps carry 170–200 terminals.
- Current process: one photo folder per location, then one workbook at a time
  after the shift.
- At 70 locations/week, saving 10 minutes per workbook returns ~11.7 hours per
  technician per week; 15 minutes returns ~17.5 hours.

The active technician count is unconfirmed, so company-wide value is not
calculable yet. Do not calculate it.

## 1.2 Who this is for

| Role | Device | What they need |
|---|---|---|
| **Technician** | Phone, in the field, gloves on, connectivity unreliable | Capture a location in a few minutes without retyping project data, and leave the site knowing nothing is missing. |
| **Supervisor / reviewer** | Laptop | See what is complete, return what is wrong with a reason, approve, and hand off a package. |
| **Operator (Anses)** | Laptop | Update the template binding when Comcast changes the form, without redeploying, and without touching customer records. |

Gabriel is the buyer and the workflow authority. Comcast (possibly via Sammons
Construction — the delivery chain is unconfirmed) is the acceptance authority,
and **no acceptance evidence exists yet for anything**.

## 1.3 What success means

The product succeeds when a technician finishes a location on their phone before
leaving the site, and the file the reviewer receives is byte-compatible with
what they already accept today. Everything else is secondary.

Concretely, in priority order:

1. **The generated `.xlsx` opens in the reviewer's Microsoft Excel and looks
   right** — all photos render in-cell, hidden sheets, validations, and defined
   names intact. This is a hard gate, not a quality bar (see
   [`05-xlsx-generation.md`](./05-xlsx-generation.md)).
2. **Zero re-entry of project-level data.** Both filled references repeat seven
   identical project fields; those are entered once per job, forever.
3. **A location is finishable in the field.** Target: under 4 minutes of active
   entry for a simple splice location, offline-tolerant, photos included.
4. **Nothing incomplete reaches the reviewer.** Validation runs before
   finalization, not after rejection.
5. **The splitter case is not an afterthought.** SP0348 carries 35 splices, 13
   splitters, and 20 destination taps. A design that only handles SP0302 solves
   the easy half.

## 1.4 In scope for the pilot

- One project/job, imported or entered once, with confirmed defaults.
- Location list per job: import from a file, or add in the field.
- Location capture: enclosure identity, placement, GPS with editable canonical
  address, cable/equipment sections, fiber-level splice assignments, splitter
  routing, notes.
- Photo capture into named evidence buckets, with originals preserved.
- Conditional OTDR capture when the location says OTDR was performed.
- Offline draft capture and background sync.
- Completeness validation with configurable rules.
- Review workflow: submit → review → return with reason → approve.
- Deterministic `.xlsx` generation from a versioned template binding.
- Per-location download and per-job batch export.
- Data export for the customer at any time, including on cancellation.

## 1.5 Explicitly out of scope for the pilot

Each of these is out because the evidence to design it correctly does not exist
yet — not because it is unimportant.

| Out of scope | Why | Revisit when |
|---|---|---|
| PDF as the delivered artifact | Unknown whether Comcast wants XLSX, PDF, or both. The current print settings produce 20 letter pages with the wide form unreadable, and LibreOffice rendering drops every photo. | Delivery format is confirmed (Q5). |
| Comcast or Sammons system integration | No approved API or export contract has been seen. | An integration contract exists in writing. |
| OCR / vision auto-fill of cable IDs and routing | A wrong destination is an operational fault, not a typo. Assistive suggestion only, never authoritative. | Field accuracy is measured against real locations. |
| Automatic address from GPS without review | Photo overlays in a *single* workbook disagree on the street text for nearby coordinates. | Never — canonical address stays technician-confirmed. |
| Multi-tenant onboarding of other contractors | Platform is designed for it; selling it is a separate decision. | R&G pilot is accepted. |
| Unlimited template change absorption | Template maintenance is bounded in the commercial terms. | Change frequency is observed. |

## 1.6 Constraints that shape the design

1. **The exact accepted workbook is the deliverable.** Not a visually similar
   sidecar. This forces package-preserving generation and rules out any
   rebuild-from-scratch approach.
2. **Microsoft Excel is the only acceptance renderer.** LibreOffice produced 14
   `#VALUE!` fallbacks and zero rendered photos on SP0302. It cannot be used to
   verify anything user-visible.
3. **Field connectivity is unknown.** Capture must never block on the network.
4. **Almost every customer rule is unconfirmed.** Rules therefore live in
   configuration and in a labelled assumption registry, not in code branches.
5. **The underlying Comcast contract is unstable.** The platform must be
   reusable by the operator and exportable by the customer, with low upfront
   commitment. This is an architectural constraint, not just a pricing one.
6. **Photo payloads are large.** SP0302's four field photos total 13.2 MB in a
   13.4 MB workbook. At 70 locations/week/technician this is roughly 1 GB/week/technician
   of raw evidence. Storage strategy is a first-class design concern
   ([`06-system-architecture.md`](./06-system-architecture.md) §6.6).

## 1.7 Non-goals

- Not a generic form builder. The wedge is *this* workbook, filled correctly.
- Not a design/GIS system. R&G consumes maps; it does not author them.
- Not a crew scheduling, timesheet, or billing product.
- Not an attempt to "fix" R&G's data conventions unilaterally. The app proposes
  canonical values; the technician confirms; the reviewer decides.
