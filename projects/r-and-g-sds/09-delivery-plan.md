# 9. Delivery plan

The owner's direction is explicit: additional discovery with Gabriel is not
available, so build a working end-to-end demo from the evidence that exists and
use the demo itself to run discovery. This plan is ordered by **risk retired per
day**, not by feature value.

## 9.1 Milestone 0 — prove the file (the go/no-go)

**Nothing else is worth building until this works.**

Deliverable: a command-line tool that takes a JSON domain object plus the blank
master and emits a workbook whose values and photos match SP0302, with every
package assertion passing and every photo rendering in-cell in Microsoft Excel.

| Step | Done when |
|---|---|
| Package-preserving copy | Output differs from the master only in the declared touched-parts list |
| Sheet-XML editor | Cells written in order, styles preserved, merges and validations untouched |
| Rich-value image injection | `Pictures!B20` renders a photo in Excel, not `#VALUE!` |
| Append-not-replace | The master's pre-existing `_error` rich value still resolves |
| `PKG-01`…`PKG-10` | All pass on both fixtures |
| Excel verification | Manual checklist passes on a real Excel install |

**Exit gate:** a human opens the generated SP0302 in Microsoft Excel next to the
original and cannot tell them apart. If this cannot be achieved, the product
premise changes and the plan stops here for a conversation — that is the correct
outcome, not a failure.

Risk if skipped: every other milestone builds on an assumption that the exact
accepted workbook can be produced at all.

## 9.2 Milestone 1 — the splitter case

Deliverable: SP0348 generated from a domain object, including 13 splitters, 35
splices, 20 destinations, and 5 photos.

This is separated from Milestone 0 because it exercises everything the simple
case does not: the staircase routing layout, the aligned-pair fiber assignments,
row-capacity limits, and the section-ordering constraint that makes the diagonal
read correctly.

**Exit gate:** both golden fixtures generate and verify; the routing rendering is
reviewed against the SP0348 reference and every intentional difference (§4.6) is
written down for Gabriel.

## 9.3 Milestone 2 — capture

Deliverable: the PWA, offline-first, generating real records.

- Auth, projects, project defaults with explicit confirmation
- Location list and job board
- Enclosure capture with GPS and editable address
- Sections with type-driven forms and controlled vocabularies
- Fiber picker in TIA-598 order
- Splitter cascade builder
- Photo buckets with local-first capture
- Conditional OTDR
- IndexedDB drafts, outbox, resumable uploads
- Validation rules running client-side

**Exit gate:** a location captured on a phone in airplane mode, submitted on
reconnect, generates a workbook identical to the Milestone 1 output.

## 9.4 Milestone 3 — review and delivery

- Review queue, return with per-field reasons, approve
- Generation on approval with package assertions gating delivery
- Per-location download and per-job ZIP export
- Audit trail
- Idempotent billing event on first approval
- Customer data export

**Exit gate:** the full lifecycle runs end to end, including a returned location
corrected in the field and re-approved, billing exactly once.

## 9.5 Milestone 4 — operate

- Docker compose deployment on the VPS with Caddy and TLS
- Backups configured **and a restore rehearsed**
- Monitoring on health, generation failures, outbox age, disk headroom
- Template profile admin: upload master, diff, preview against fixtures, publish
- Rule override admin

**Exit gate:** the operator can publish a new template profile and roll it back
without a deploy.

## 9.6 Milestone 5 — the demo run

Not a phase of engineering; a phase of evidence gathering.

1. Load the real `avalon ridge sec 1` project.
2. Capture SP0302 and SP0348 as if in the field.
3. Generate both, verify in Excel, compare to the originals.
4. Anses runs the whole flow before Gabriel sees it, logging defects separately
   from unresolved business rules.
5. Gabriel runs it on his own phone, on a real location.
6. Use the run to close the open questions in
   [`10-open-questions.md`](./10-open-questions.md).

**Exit gate:** Gabriel has generated a workbook he would actually submit, and the
open-question list has real answers with named sources.

Only after that: production scope, deployment posture, and pricing.

## 9.7 Acceptance tests

Written before the code, run on every build.

| ID | Test |
|---|---|
| `A-01` | SP0302 fixture → workbook matching the reference cell-for-cell in bound cells |
| `A-02` | SP0348 fixture → workbook matching the reference, routing differences documented |
| `A-03` | All package assertions pass on both |
| `A-04` | Generated workbook decodes back to the source domain object |
| `A-05` | Master's untouched parts byte-identical in both outputs |
| `A-06` | Generation refuses to run against a master whose hash does not match the profile |
| `A-07` | Offline capture → reconnect → identical output to online capture |
| `A-08` | Returned → corrected → re-approved → regenerated bills exactly once |
| `A-09` | Voided location never bills and never delivers |
| `A-10` | A location exceeding row capacity fails validation with the required count, never truncates |
| `A-11` | Every organisation-scoped query is scoped; a cross-org read is impossible |
| `A-12` | Profile change → fixture diff is reviewable and explains every changed cell |

## 9.8 Risks

| Risk | Impact | Response |
|---|---|---|
| **Rich-value images cannot be generated reliably** | Fatal to the premise | Milestone 0 is first and is a go/no-go. Fallback: floating drawings anchored to the same cells, which is a *visibly different file* and needs customer acceptance |
| **The reviewer rejects the generated file for a reason we cannot see** | Pilot stalls | Golden fixtures reproduce accepted-looking files; get one real submission reviewed as early as possible |
| **Neither sample was ever accepted** | The whole reference basis is wrong | Q1 is the first question asked. Until answered, no claim of Comcast acceptance appears anywhere |
| **The template changes mid-pilot** | Rework | Profiles are data; §4.10 makes the update path a bounded operation |
| **Row capacity is genuinely insufficient for real splitter locations** | Some locations cannot be filed at all | `R-10` surfaces it explicitly rather than truncating; likely forces Q4 (one workbook per what?) |
| **Photo volume overwhelms the VPS or the technician's data plan** | Operational failure | Downscaled renders, content-addressed storage, resumable chunked upload, disk alerting |
| **Comcast requires PDF** | New rendering surface with real cost | Out of pilot scope; §5.8 documents the path and its cost |
| **R&G loses the Comcast contract** | Revenue disappears | Low upfront, cancellable, customer exports everything, operator keeps the platform |
| **Offline sync corrupts or loses field data** | Trust destroyed on day one | Content-addressed photos, outbox never drops unsynced evidence, `A-07` |
| **Building against one technician's habits** | The app encodes one person's conventions | Every convention is a named strategy with an `ASM-` id and a config key |

## 9.9 What is explicitly not promised

Carried forward from the packet's field-audit checklist, and repeated here
because a working demo makes over-promising easy:

- Perfect automatic addresses from GPS.
- Customer-system integration before an approved API or export contract exists.
- Full offline synchronisation guarantees before field connectivity is tested.
- Unlimited absorption of Comcast template changes under a flat fee.
- A fixed price before output acceptance rules and real accepted examples are
  inspected.
- **Comcast acceptance of anything.** No output, format, or workflow may be
  described as accepted until direct evidence exists.
