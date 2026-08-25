# ADR-003 — The workbook binding is versioned data, not code

**Status:** accepted · **Date:** 2026-08-25

## Context

Three facts make a hardcoded binding untenable:

1. **The master will change.** Comcast owns the template and has already changed
   it once — the supplied master is a flattened derivative of the schema still
   visible in its own hidden `Example` sheet.
2. **The conventions are unconfirmed and mutually inconsistent.** Two workbooks
   filled by the same technician on the same day for the same job disagree about
   what rows 19 and 20 mean.
3. **Template maintenance is a bounded commercial commitment.** If absorbing a
   template change requires a code release, the commitment is not bounded.

## Decision

A **template profile** is a versioned JSON document, generated from a real master
by `tools/extract_template_spec.py`, containing:

- the master's SHA-256 (generation refuses to run against a mismatch)
- every field's label cell, value cell, merge range, and type
- the section grid geometry
- picture and OTDR slot maps
- controlled vocabularies
- named **strategies** for the regions the template does not define:
  `headerRole`, `fiberAssignment`, `routing`, `pictures`, `latLongFormat`,
  `spliceOverflow`
- the filename pattern

Every `Submission` records the profile id and version it used, so regenerating a
location months later reproduces the file that was actually filed.

## Alternatives rejected

| Alternative | Why not |
|---|---|
| Hardcode cell addresses | A template change becomes a code release; every unconfirmed convention becomes a branch nobody can find later. |
| Infer the layout at generation time | The layout is genuinely ambiguous — two samples, two conventions. Inference would silently pick one and produce inconsistent output across locations. |
| One profile, no strategies | Would force a choice between reproducing SP0302's convention and SP0348's. Neither is known to be right. |

## Consequences

**Good.** Template updates are an operational task: obtain the master, extract,
diff, adjust strategies, verify in Excel, publish. No deploy. Every convention has
a name, an owner, and an entry in the assumption registry. Historical
regeneration is exact.

**Bad.** Indirection. Reading the generator does not tell you which cell a field
lands in — you read the profile. Mitigated by generating the profile from the real
file, so it cannot drift from the evidence.

**Also.** Strategies must be finite and named. "Configurable" must not become
"scriptable"; a profile that can execute arbitrary layout logic is code with
worse tooling.
