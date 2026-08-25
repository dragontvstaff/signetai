# ADR-001 — Generate by patching a byte-preserved copy of the master

**Status:** accepted · **Date:** 2026-08-25

## Context

The deliverable is the exact workbook the reviewer already accepts. The master
carries parts that no spreadsheet library reproduces: `xl/richData/*` (in-cell
photos), `xl/metadata.xml`, seventeen cell comments with their VML anchors,
printer settings, three `customXml` items, web extension registration, twelve
defined names, and three hidden sheets.

The photos in particular use Excel's `_localImage` rich-value format. `openpyxl`
does not model `richData` at all: a load/save round-trip drops every photo
**while reporting success**. A LibreOffice PDF export of SP0302 produced 20
pages, 14 `#VALUE!` fallbacks, and zero rendered images.

## Decision

Generation copies the master's bytes and edits only a short, closed, asserted
list of parts:

```
xl/worksheets/sheet{1,3,4}.xml      cells we write
xl/media/image*.png                 appended photo bytes
xl/richData/*                       appended rich values and relationships
xl/metadata.xml                     appended metadata entries
[Content_Types].xml                 overrides for new parts
xl/_rels/workbook.xml.rels          relationships to richData parts
```

Everything else is copied verbatim and asserted byte-identical (`PKG-02`). Text
is written as inline strings so `xl/sharedStrings.xml` is never reindexed.
Formulas are never written, so `xl/calcChain.xml` stays valid.

## Alternatives rejected

| Alternative | Why not |
|---|---|
| Build the workbook with a library (`exceljs`, `openpyxl`, `SheetJS`) | Cannot reproduce rich values, comments, printer settings, or customXml. Produces a *similar* file, and the packet is explicit that a similar file is not the deliverable. |
| `openpyxl` load → modify → save | Silently destroys the photos. The most dangerous option precisely because it appears to work. |
| Template + LibreOffice headless conversion | Does not render the image format at all. |
| Floating drawings instead of in-cell images | A visibly different file. Kept only as the Milestone 0 fallback, and would require explicit customer acceptance. |

## Consequences

**Good.** The output is the customer's file with values in it. Every part nobody
thought to check is provably unchanged. Template updates do not require
regenerating any of this machinery.

**Bad.** A bespoke sheet-XML editor must be written and maintained: cells
inserted in ascending column order, rows in ascending row order, styles preserved,
merges and validations untouched. Roughly a day of work and the load-bearing
component of the product. It is the reason Milestone 0 exists as a go/no-go.

**Also.** Verification cannot be automated end to end. Microsoft Excel is the
only renderer that proves the file is right, so a human opens it. Automation
covers the package assertions and the binding round-trip; Excel covers what a
reviewer will actually see.
