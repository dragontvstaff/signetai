# R&G / Comcast SDS field-operations app — project design

Design package for a phone-first field-capture service that generates the
Comcast SDS ("As-Built Fiber Splicing Sheet") workbook for every splice
location, from data and photos a technician captures once, in the field.

**Status:** design only. Nothing here has been built, deployed, quoted, or
shown to the customer. No Comcast acceptance evidence exists for any output
format described in this package.

**Source of truth for the problem:** the takeover packet
`R-and-G-Comcast-Agent-Takeover-Packet-2026-08-18` (relay, README, field audit
checklist, sample comparison, blank master workbook, two filled references, and
Gabriel's voice note). This package does not restate the packet; it adds the
engineering design and the cell-level findings the packet asked for.

## Customer boundary

This project is **R&G / Comcast only**. R&G/Comcast and Colonial/Brightspeed
are unrelated customers. No Colonial data, contacts, rules, paths, or
deliverables may be reused, merged, inferred, or cross-referenced here. Shared
fiber-splicing *software patterns* may inform implementation; operational facts
may not.

## Note on repository location

This is a design package for a **separate product** from Signet. It lives in
`projects/` rather than `docs/` so it is not mistaken for Signet product
documentation, and so it can be lifted into its own repository unchanged. It
adds no code, dependencies, or build steps to the Signet workspace.

## How to read this package

| # | Document | Answers |
|---|---|---|
| — | [`01-scope.md`](./01-scope.md) | What are we building, for whom, and what are we deliberately not building? |
| — | [`02-evidence.md`](./02-evidence.md) | What do the supplied files actually prove, cell by cell? |
| — | [`03-domain-model.md`](./03-domain-model.md) | What is the canonical data model behind the workbook? |
| — | [`04-template-binding.md`](./04-template-binding.md) | How does that model map onto the real workbook cells? |
| — | [`05-xlsx-generation.md`](./05-xlsx-generation.md) | How do we produce a file Excel and the reviewer accept? |
| — | [`06-system-architecture.md`](./06-system-architecture.md) | How is the service built, hosted, and operated? |
| — | [`07-ux-flows.md`](./07-ux-flows.md) | What does the technician and the supervisor actually do? |
| — | [`08-validation.md`](./08-validation.md) | What must be true before a location can be finalized? |
| — | [`09-delivery-plan.md`](./09-delivery-plan.md) | What gets built in what order, and how is each step proven? |
| — | [`10-open-questions.md`](./10-open-questions.md) | What is still unknown, and why is it not blocking the build? |
| — | [`assumptions.md`](./assumptions.md) | Every inferred rule, labelled, with its config key and blast radius. |
| — | [`decisions/`](./decisions/) | The five decisions that shape everything else. |

## Generated specification

`spec/` is **generated, never hand-written**. Every cell reference in the design
is extracted from the real workbook package so the binding cannot drift from
the evidence.

```bash
cd projects/r-and-g-sds/tools
python3 extract_template_spec.py <packet>/source-documents ../spec
```

| File | Contents |
|---|---|
| `spec/template-profile.rg-flat.json` | The workbook binding: every field, its label cell, value cell, merge range, master prefill, and the instruction recovered from the cell comment. |
| `spec/vocabularies.json` | Controlled lists recovered from the hidden `Lists` sheet, the workbook's defined names, and the one surviving inline validation. |
| `spec/observed-fills.json` | Both filled references decoded *through* the binding — the proof that the binding round-trips against real evidence. |
| `spec/rich-value-images.json` | The Excel image-in-cell package parts that any generator must reproduce. |

The extractor reads the OOXML package directly with the Python standard library
and never writes to the source workbooks.

**Redaction.** Personal names, street addresses, and precise coordinates are
redacted from generated output by default — the takeover packet requires contact
details and operational addresses to stay in the protected sources rather than
in derived analyses. The *shape* of each value survives redaction
(`N dd.dddd W dd.dddd`), because the shape is what the design reasons about.
`--raw` emits unredacted output for local inspection and must never be
committed.

## The one-line version

Comcast requires one workbook per splice location. A technician does 50–70
locations a week and fills the workbooks at home, at night, unpaid. The
workbook is a wide, merged, mostly free-form spreadsheet whose photos use an
Excel-only in-cell image format that most tooling silently destroys. The
product is: capture once in the field, generate the exact workbook the
reviewer already accepts, and never retype a project default again.
