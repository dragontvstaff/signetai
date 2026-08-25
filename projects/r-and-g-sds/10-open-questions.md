# 10. Open questions

The packet lists fifteen blocking unknowns. Discovery with Gabriel is not
currently available, and the owner's direction is to build anyway. This document
records, for each question: what the evidence now says, what the design does in
the meantime, and what changes when the real answer arrives.

**No question below blocks Milestone 0 or 1.** Every one is absorbed by a config
value, a named strategy, or a rule severity.

## Status key

- 🔴 **Open** — no evidence, pure assumption
- 🟡 **Inferred** — evidence supports an answer, unconfirmed
- 🟢 **Resolved from evidence** — the files answer it

---

### Q1 🔴 Were SP0302 and SP0348 actually submitted and accepted? By whom?

Nothing in the packet indicates acceptance. Both are internal filled examples as
far as the evidence goes.

**Design response:** the golden fixtures reproduce these files because they are
the best available reference, not because they are known-good. Every document in
this package states acceptance is unconfirmed. No output is described as
Comcast-accepted anywhere in the product or its marketing.

**On answer:** if accepted → they become the acceptance baseline. If *not* → the
reference basis is wrong and Milestone 5 must obtain a genuinely accepted example
before the pilot proceeds. This is the highest-value question in the list.

---

### Q2 🔴 What is the exact R&G → Sammons → Comcast submission chain?

`Business Partner = Sammons Construction` in both samples; photo overlays are
Xfinity-branded. Direction of flow unknown.

**Design response:** `businessPartner` is a project field, and delivery is manual
(download / ZIP export). No submission channel is automated.

**On answer:** determines whether a delivery integration is worth building and
who the "reviewer" role actually represents.

---

### Q3 🔴 How many active technicians, and what is the real volume distribution?

Gabriel says 50–70 locations per technician per week and "several" technicians.

**Design response:** the system is multi-technician from the start; nothing
assumes a count. No company-wide value or price is calculated in this package.

**On answer:** sizes the VPS, the storage budget, and the per-technician pricing
component. Until then, per-technician figures only.

---

### Q4 🟡 One workbook per terminal, enclosure, splice point, or other unit?

**Evidence:** `Splicing Record!N5`, red: *"This document MUST be completed for
each location where fiber splicing occurred during construction."* Gabriel's
voice note: *"para cada enclosure y para cada OT."* SP0302 and SP0348 are each one
enclosure.

**Design response:** one `Location` → one workbook. Both taps and enclosures are
Locations distinguished by enclosure type.

**Still open:** what happens when one location's routing exceeds the workbook's
17 grid rows. Rule `R-10` fails validation with the required count rather than
truncating, which turns the question into a visible, answerable event instead of
a silent data loss.

---

### Q5 🔴 Required final package: XLSX, PDF, both, ZIP? Naming convention? Channel?

Two filed samples, two naming conventions — one of them (`SDS Template SP0348`)
plainly accidental.

**Design response:** XLSX only. Naming is a per-project pattern (§4.9). Export is
per-location download or per-job ZIP. PDF is documented as out of scope with its
cost (§5.8).

**On answer:** naming becomes one config string. PDF, if required, adds a
rendering surface that needs Microsoft Excel or a commercial renderer — a real
cost that must be priced, not absorbed.

---

### Q6 🔴 What project/map/cable/routing data exists before dispatch, in what format?

Unknown. Gabriel mentions maps with 170–200 terminals.

**Design response:** locations can be imported from CSV/XLSX *or* created in the
field. The import mapper is deliberately generic because the source format is
unknown.

**On answer:** potentially the single largest time saving left. If tap IDs,
cable IDs, and design routing arrive in a structured file, the technician
confirms rather than types, and capture time drops again.

---

### Q7 🔴 Which fields are field-observed, looked up, copied from design, or calculated?

**Design response:** the app records the *provenance* of the values it can —
`GeoFix.addressSource`, inherited-vs-confirmed defaults, derived-vs-entered
splice counts. That provenance is the raw material for answering this question
from real usage rather than from an interview.

**On answer:** fields that come from design move into import; fields that are
calculated stop being typed.

---

### Q8 🟡 What do `COM`, `NP####`, `1X2`, `1X4` mean?

**Evidence:** `1X2`/`1X4`/`1X16` map to the workbook's own `Port_Config`
vocabulary (`1x2`, `1x4`, `1x16`) — casing differs, meaning is certain. `COM` is
the splitter's common/input port, consistent across all 13 splitters in SP0348.
`NP####` are downstream destinations; Gabriel's voice note describes feeding "la
MP 009 … que viene siendo una tapa" — a tap. So `NP/MP####` is almost certainly a
tap/terminal identifier.

**Design response:** ratios are canonicalised against `Port_Config`. `COM` is
modelled as the splitter's input port. `NP####` is an opaque identifier validated
by shape (`R-07`, pattern configurable).

**On answer:** if the identifiers reference records that exist before dispatch,
they become a picker instead of a text field — and `R-07` becomes referential
rather than syntactic.

---

### Q9 🟡 Required photo sequence and slot meaning? Is the GPS-camera app mandatory?

**Evidence:** comment `B91` states the intent — ground-level location, pole/vault/
ped interior before and after, tray photos per splice. **Both samples ignore it**,
putting every photo into the splicing slots and leaving all three enclosure slots
empty.

**Design response:** buckets are named by content; bucket→slot mapping is a
strategy defaulting to `as-filed` (what the reviewer has seen) rather than
`as-instructed` (what the template says). `E-02` is a warning, not an error.

**On answer:** one strategy value and one rule severity. Roughly two lines of
config, and it is the change most likely to be needed.

---

### Q10 🟡 What date does the form carry?

**Evidence:** both samples carry `2026-08-07`, one day after the visible photo
date, and both were sent on 2026-08-10.

**Design response:** `formDateRule` ∈ `work_date` (default) | `work_date_plus_1` |
`submission_date`. `H-10` warns on divergence; `X-06` warns when photo timestamps
fall outside 24 h of the work date.

**On answer:** one config value.

---

### Q11 🟡 Which blank-template defaults must be actively confirmed?

**Evidence:** the master ships nine prefilled values, including a stale technician
name (`<stale technician name>`) and a stray `fdssd`. Both samples inherited five unchanged.

**Design response:** treat *all* of them as requiring explicit confirmation
(`H-02`, `error`). The confirmation is recorded, so a reviewer can distinguish
"chosen" from "not looked at" — which is impossible in the current files.

**On answer:** severity may relax for genuinely constant fields. Confirming is
cheap; inheriting a wrong technician name onto fifty workbooks is not.

---

### Q12 🔴 OTDR applicability, fiber labels, screenshots — and an accepted example

Neither sample performed an OTDR. The blank master exposes one forward/return
pair; the hidden `Example` sheet shows two pairs (hub-to-endsite and
endsite-to-hub).

**Design response:** OTDR capture is conditional and gated on the header flag.
The profile declares only the slots the master actually has. A location recording
more tests than the profile can hold fails validation with the count rather than
dropping traces.

**On answer:** may require a second profile exposing the four-slot layout. This
is the largest unexercised area of the design and needs one accepted OTDR
workbook to close.

---

### Q13 🔴 Rejection/correction workflow, and an example rejected SDS

Unknown. No rejected example supplied.

**Design response:** a full return-with-reasons cycle exists
([`07-ux-flows.md`](./07-ux-flows.md) §7.3) with per-field reasons and an audit
trail. It is modelled on ordinary review workflow, not on R&G's actual process.

**On answer:** likely adds required metadata to a resubmission (a revision marker,
a reviewer name, a correction note). The audit trail already carries the data;
the workbook binding may need somewhere to put it.

---

### Q14 🔴 Field connectivity and offline requirements

Unknown.

**Design response:** removed from the critical path. Capture is offline-first by
construction; sync is ambient. This costs real engineering in Milestone 2 and is
worth it, because the alternative is discovering the answer through lost field
data.

**On answer:** if connectivity is good everywhere, the offline path becomes
insurance. If it is bad, it was the product.

---

### Q15 🔴 Which Excel version and device is used to complete, review, and submit?

Unknown. Rich-value in-cell images require a reasonably modern Excel; older
versions and Excel for Mac render them inconsistently.

**Design response:** verification layer 3 specifies "the same Microsoft Excel
environment used by R&G/reviewer" precisely because this is unknown.

**On answer:** if any participant runs an Excel that cannot render in-cell images,
the photo mechanism itself must change — and that is a Milestone 0 fallback
decision, not a late tweak. Worth asking early despite sitting last on the list.

---

## Summary

| | Count | Questions |
|---|---|---|
| 🟢 Resolved from evidence | 0 | — |
| 🟡 Inferred, unconfirmed | 5 | Q4, Q8, Q9, Q10, Q11 |
| 🔴 Open | 10 | Q1, Q2, Q3, Q5, Q6, Q7, Q12, Q13, Q14, Q15 |

**Highest value to close first:** Q1 (is the reference basis real?), Q15 (does the
photo mechanism work in their Excel?), Q9 (which photos does the reviewer
enforce?). All three are answerable in a single short conversation, and the first
two can invalidate work if answered late.
