# 8. Validation

## 8.1 Principle

Every rule below is a **prototype assumption until the customer confirms it**. No
rule is hardcoded as a branch; each is a declared rule with a severity that the
operator can change per project without a code release. Rules that came from the
customer's own workbook comments are marked `[evidence]`; rules inferred from the
two samples are marked `[inferred]` and carry an `ASM-` id.

Severities:

| Severity | Effect |
|---|---|
| `error` | Blocks submission and blocks approval. |
| `warn` | Requires explicit technician acknowledgement, recorded in the audit trail. |
| `info` | Shown, never blocking. |

The same rule definitions run client-side (offline, during capture) and
server-side (at submission and again at approval). One source of truth; the
client is a fast path, never the authority.

## 8.2 Header and enclosure

| ID | Rule | Default | Source |
|---|---|---|---|
| `H-01` | All twenty header fields present | `error` | `[evidence]` — both samples fill all twenty |
| `H-02` | Every inherited project default explicitly confirmed on first open | `error` | `[inferred]` `ASM-003` — the master ships stale values in six of these cells |
| `H-03` | `technician` is the signed-in technician, not a template leftover | `error` | `[evidence]` — master carries `<stale technician name>` |
| `H-04` | `enclosure_name` matches the project's location-id pattern | `warn` | `[inferred]` `ASM-010` |
| `H-05` | `pole_tag` required when `placement == aerial`, `N/A` otherwise | `error` | `[evidence]` — `K13` comment |
| `H-06` | `lat_long` within the project's plausible bounding box | `warn` | `[inferred]` `ASM-006` |
| `H-07` | GPS accuracy better than 25 m, else re-capture prompt | `warn` | `[inferred]` |
| `H-08` | `location_address` non-empty and technician-confirmed | `error` | `[evidence]` — `C13` comment |
| `H-09` | `connected_sheaths` ≥ 1, integer, ≤ 15 | `error` | `[inferred]` — 15 is the section-grid capacity |
| `H-10` | `form_date` follows the project's date rule | `warn` | `[inferred]` `ASM-002` — both samples carry a date one day after the photos |

## 8.3 Sections

| ID | Rule | Default | Source |
|---|---|---|---|
| `S-01` | At least one section populated | `error` | `[evidence]` |
| `S-02` | Exactly one section has `role == input` | `warn` | `[inferred]` `ASM-011` — SP0302 and SP0348 each have one |
| `S-03` | Cable manufacturer resolves to a controlled vocabulary entry | `warn` | `[evidence]` — `Sheath_Manufacturer`; catches `COMPSCOPE` |
| `S-04` | Cable manufacturer casing normalised to canonical | `info` | `[evidence]` — `AFL` vs `AFL Tel` |
| `S-05` | `fiberCount` ∈ {12, 24, 48, 72, 96, 144, 288, 432, 864} | `warn` | `[inferred]` — observed values only |
| `S-06` | `footage` > 0 and < 100 000 | `error` | `[inferred]` — bounds check |
| `S-07` | `cableId` non-empty for every cable section | `error` | `[evidence]` |
| `S-08` | `manufacturedOn` not in the future, not before 2000 | `error` | `[inferred]` |
| `S-09` | Split ratio resolves to `Port_Config`, canonical casing | `error` | `[evidence]` — catches `1X16` → `1x16` |
| `S-10` | `rackShelfPort` required when `placement == isp` | `warn` | `[evidence]` — label reads "(ISP)" |
| `S-11` | Section slots are contiguous from 1 | `info` | `[inferred]` — readability |

## 8.4 Splices and routing

| ID | Rule | Default | Source |
|---|---|---|---|
| `R-01` | Both endpoints of every splice resolve to a populated section | `error` | `[inferred]` |
| `R-02` | Port endpoint within the section's port count | `error` | `[inferred]` — port 19 of a 16-port splitter is impossible |
| `R-03` | Fiber endpoint within the cable's fiber count | `error` | `[inferred]` |
| `R-04` | No fiber appears in two splices | `error` | `[inferred]` — physically impossible |
| `R-05` | Fiber sequence has no unexplained gaps | `warn` | `[inferred]` — GR→WH is deliberate or a mistake |
| `R-06` | Every splitter output either assigned or explicitly marked spare | `warn` | `[inferred]` `ASM-013` — SP0348 leaves two splitters entirely unassigned |
| `R-07` | Destination identifiers match the configured pattern (default `^NP\d{4}$`) | `warn` | `[inferred]` `ASM-012` — meaning unconfirmed, shape observed |
| `R-08` | No destination identifier appears twice at one location | `error` | `[inferred]` |
| `R-09` | Routing graph is acyclic and rooted at the input | `error` | `[inferred]` |
| `R-10` | Splice and route counts fit the profile's row capacity | `error` | `[evidence]` — 7 pair rows, 17 grid rows |

## 8.5 Cross-field consistency

These exist because the evidence contains a real contradiction, and it is exactly
what a submission check should have caught.

| ID | Rule | Default | Source |
|---|---|---|---|
| `X-01` | `splices_performed` equals the number of recorded splices | `warn` | `[evidence]` — `G15`: "total amount of splices performed during work visit" |
| `X-02` | `total_couplers` equals the number of splitter/mux sections | `warn` | `[evidence]` — `E15`: "total count of mux's/splitters in the enclosure". **SP0348 declares 3 against 13 splitters drawn.** |
| `X-03` | `connected_sheaths` equals the number of cable sections | `warn` | `[evidence]` — `C15` |
| `X-04` | `otdr_performed == true` ⇒ at least one OTDR test recorded | `error` | `[evidence]` — `B53` comment |
| `X-05` | `otdr_performed == false` ⇒ no OTDR images | `error` | `[inferred]` |
| `X-06` | Photo capture timestamps within 24 h of `workDate` | `warn` | `[inferred]` `ASM-002` |
| `X-07` | Photo GPS within 200 m of the location fix | `warn` | `[inferred]` — catches a photo from the previous site |

`X-01` through `X-03` are `warn`, not `error`, on purpose. The customer's counts
and the customer's drawings disagree in the evidence we have, and the app is not
entitled to decide which is right — only to make the disagreement visible before
it reaches a reviewer.

## 8.6 Evidence

| ID | Rule | Default | Source |
|---|---|---|---|
| `E-01` | At least four photos | `error` | `[inferred]` `ASM-008` — SP0302 has 4, SP0348 has 5 |
| `E-02` | Buckets `enclosure_location`, `enclosure_before`, `enclosure_after` filled | `warn` | `[evidence]` `ASM-008` — `B91` requires them; **neither sample provides them** |
| `E-03` | One tray photo per splice group | `warn` | `[evidence]` — `B91`: "photos of the tray(s) where the splicing occurred for each splice" |
| `E-04` | `closed_condition` photo present | `warn` | `[inferred]` — SP0348 has one, SP0302 does not |
| `E-05` | Every photo ≥ 1 megapixel after processing | `error` | `[inferred]` — an unreadable label fails the purpose |
| `E-06` | Total workbook payload under the configured ceiling (default 20 MB) | `warn` | `[inferred]` `ASM-014` — SP0348 is 14.2 MB |
| `E-07` | No two photos in a location are byte-identical | `warn` | `[inferred]` — catches a double-tap |

`E-02` is the single most likely rule to change after one conversation with
Gabriel. If the reviewer enforces the enclosure slots, it becomes `error` and the
default picture strategy flips to `as-instructed`. If the reviewer does not, it
drops to `info`. One question, two config lines.

## 8.7 Generation gates

Package assertions `PKG-01` … `PKG-10` from
[`05-xlsx-generation.md`](./05-xlsx-generation.md) §5.6 run on every generated
file and are all `error`. A file that fails any of them is never delivered and
never billed. Approval is blocked with the specific assertion, not a generic
failure.

## 8.8 Rule configuration

```jsonc
{
  "projectId": "…",
  "ruleOverrides": {
    "E-02": { "severity": "error" },      // reviewer confirmed enclosure photos
    "R-07": { "pattern": "^(NP|MP)\\d{4}$" },
    "X-02": { "severity": "info" }        // "couplers" means something narrower
  }
}
```

Overrides are per project, versioned, and audited. A rule change never requires a
deploy — which is the whole point, because most of these rules are guesses until
someone with authority says otherwise.
