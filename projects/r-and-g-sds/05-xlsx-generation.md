# 5. XLSX generation

This is the highest-risk component in the system and the one to prototype first.
If it does not work, nothing else matters; if it does, the rest is ordinary web
engineering.

## 5.1 The constraint

The deliverable is **the exact workbook the reviewer already accepts** — not a
visually similar file. That rules out generating a spreadsheet from scratch with
any library, because the master carries parts no library reproduces:

```
xl/richData/*              image-in-cell rich values
xl/metadata.xml            the cell → rich value indirection
xl/comments1.xml           17 instruction comments
xl/drawings/vmlDrawing1.vml comment anchors
xl/printerSettings/*.bin   print configuration
customXml/item{1,2,3}.xml  document metadata
xl/webextensions/*         task pane registration
defined names ×12          Lists-backed vocabularies
hidden sheets ×3           Lists, OTDR Shots, Example
```

It also rules out a load/save round-trip through `openpyxl` or any similar
library: they do not model `richData`, so they drop every photo while reporting
success ([ADR-001](./decisions/ADR-001-preserve-master-package.md)).

## 5.2 The approach: package surgery

Copy the master's bytes, then edit only the parts that must change. The exact
delta is known, because it can be measured: diffing the blank master against
SP0302 shows precisely what Excel itself did when the technician pasted four
photos in.

**Parts SP0302 adds that the master does not have — the complete list:**

```
xl/richData/richValueRel.xml
xl/richData/_rels/richValueRel.xml.rels
xl/media/image{1..4}.png                   (the four field photos)
```

Plus one `[Content_Types].xml` override (`/xl/richData/richValueRel.xml`) and one
workbook relationship (`richData/richValueRel.xml`). **Nothing else.** No part
present in the master is absent from the filled file.

Everything else the photos need — `xl/metadata.xml`, `rdrichvalue.xml`,
`rdrichvaluestructure.xml`, `rdRichValueTypes.xml` and their workbook
relationships and content-type overrides — **already exists in the blank master**,
because the master's `Lists` sheet has spilled-array `#VALUE!` cells that use the
same rich-value machinery. They are edited in place, not created.

That reduces generation to:

```
1. verify        master sha256 == profile.masterSha256          (else refuse)
2. open          the master as a zip; stream every entry forward
3. rewrite       xl/worksheets/sheet1.xml   Splicing Record cells
                 xl/worksheets/sheet4.xml   Pictures cells (vm refs)
                 xl/worksheets/sheet3.xml   OTDR Shots (when applicable)
4. edit in place xl/richData/rdrichvaluestructure.xml   add the _localImage structure
                 xl/richData/rdrichvalue.xml            append one <rv> per photo
                 xl/metadata.xml                        append futureMetadata + valueMetadata
                 [Content_Types].xml                    add the richValueRel override
                 xl/_rels/workbook.xml.rels             add the richValueRel relationship
5. create        xl/richData/richValueRel.xml
                 xl/richData/_rels/richValueRel.xml.rels
                 xl/media/image{N}.png                  one per photo
6. copy          every other entry byte-for-byte, unchanged
7. hash          record the output sha256 in the Submission
```

`[Content_Types].xml` already declares `<Default Extension="png"
ContentType="image/png"/>`, so media parts need no per-file override — verified
against the master, not assumed.

Everything not in steps 3–5 is copied verbatim. The list of touched parts is
short, closed, and asserted in tests (`PKG-02`) — a generator that touches a part
outside this list fails the build.

## 5.3 Injecting an in-cell image

The mechanism decoded in §2.5, run in reverse. Critically, the blank master
**already contains one rich value**: `rdrichvalue.xml` declares `count="1"` with a
single `_error` at index 0, and `rdrichvaluestructure.xml` declares `count="1"`
with only the `_error` structure. New entries append; index 0 is taken, and the
`_localImage` structure must be *added* at index 1 rather than assumed present.

```
given: master already has R rich values and S structures

1. append the image bytes as xl/media/image{N}.png
   ([Content_Types].xml already declares a png Default — verify, do not assume)

2. xl/richData/rdrichvaluestructure.xml
   ensure a _localImage structure exists:
     <s t="_localImage">
       <k n="_rvRel:LocalImageIdentifier" t="i"/>
       <k n="CalcOrigin" t="i"/>
     </s>
   remember its index Simg

3. xl/richData/_rels/richValueRel.xml.rels
   append <Relationship Id="rId{L+1}" Type=".../image" Target="../media/image{N}.png"/>

4. xl/richData/richValueRel.xml
   append <rel r:id="rId{L+1}"/>            → local image identifier = L (0-based)

5. xl/richData/rdrichvalue.xml
   append <rv s="{Simg}"><v>{L}</v><v>5</v></rv>   → rich value index = R
   bump count

6. xl/metadata.xml
   append to futureMetadata name="XLRICHVALUE":
     <bk><extLst><ext uri="{3e2802c4-a4d2-4d8b-9148-e3be6c30e623}">
       <xlrd:rvb i="{R}"/></ext></extLst></bk>
   append to valueMetadata:
     <bk><rc t="{XLRICHVALUE type index}" v="{R}"/></bk>
   → the cell's vm attribute is the 1-based index of this valueMetadata entry

7. the worksheet cell becomes
     <c r="B20" s="{existing style}" t="e" vm="{vmIndex}"><v>#VALUE!</v></c>
```

Two details that are easy to get wrong and expensive to discover late:

- **`vm` is 1-based into `valueMetadata`; `rvb i` is 0-based into `rdrichvalue`.**
  Confirmed against SP0302: `Pictures!B20` has `vm="2"` → `valueMetadata[1]` →
  `rvb i="1"` → `rdrichvalue[1]` → local image 0 → `rId1` → `image1.png`.
- **The `t="{n}"` in `<rc>` is the index into `metadataTypes`,** not a literal.
  The master declares `XLDAPR` then `XLRICHVALUE`, so `t="2"`. Read it from the
  master; do not hardcode.

The `#VALUE!` text is the *fallback*, and it is what non-Microsoft readers show.
This is correct and expected — SP0302 and SP0348 both behave this way. It is not
a defect to be fixed and must not be treated as one during testing.

## 5.4 Writing cell values without touching shared strings

Text is written as **inline strings**:

```xml
<c r="C14" s="203" t="inlineStr"><is><t>NE corner Waters Rd &amp; Lone Oak Pkwy</t></is></c>
```

This avoids editing `xl/sharedStrings.xml` and therefore avoids reindexing every
existing `t="s"` cell in the workbook — a class of corruption that is easy to
introduce and hard to see. It costs a few bytes per cell and buys the guarantee
that no untouched cell changes meaning.

Numbers and dates are written as bare values with the master's existing style id
preserved, so date formatting, alignment, borders, and fills are inherited from
the template rather than reconstructed:

```xml
<c r="C4" s="203"><v>46241</v></c>
```

Formulas are never written, so `xl/calcChain.xml` stays valid and is copied
unchanged.

## 5.5 The sheet-XML editor

`Splicing Record` is 110 KB of XML with 909 merged ranges. The editor must:

- Insert a `<c>` into an existing `<row>` in **ascending column order**, since
  Excel rejects out-of-order cells.
- Insert a `<row>` in ascending row order when the target row does not exist.
- Preserve the `s` (style) attribute of any cell it replaces, and inherit from
  the row/column default when creating a cell.
- Leave `dimension`, `mergeCells`, `dataValidations`, `extLst`, and every other
  child element untouched and in place.
- Never reorder or reformat anything it does not write.

Implementation: a targeted streaming editor over the sheet XML, not a DOM
round-trip. A round-trip through a generic XML parser reorders attributes and
normalises namespaces, which produces a file that opens but no longer
byte-matches the master in the parts nobody inspected. Writing the editor is
roughly a day's work and it is the load-bearing component of the product.

## 5.6 Verification

Three layers, run on every generated file.

### Layer 1 — package assertions (automatic, every generation)

Fail the generation, not the review, when any of these break:

| Check | Assertion |
|---|---|
| `PKG-01` | Every part present in the master is present in the output. |
| `PKG-02` | Every part **not** on the touched-parts list is byte-identical to the master. |
| `PKG-03` | Every `xl/media/*` entry in the master survives; new entries only appended. |
| `PKG-04` | `rdrichvalue` count == `valueMetadata` count == `richValueRel` count + pre-existing non-image rich values. |
| `PKG-05` | Every `vm` on a worksheet resolves through metadata → rich value → relationship → an existing media part. |
| `PKG-06` | Every defined name still resolves to a range on an existing sheet. |
| `PKG-07` | Sheet visibility states match the master (three hidden). |
| `PKG-08` | Every cell written by the profile is present with the expected type. |
| `PKG-09` | No cell outside the profile's writable set differs from the master. |
| `PKG-10` | Output opens as a valid zip with `[Content_Types].xml` first. |

### Layer 2 — round-trip through the binding (automatic)

Read the generated workbook back with `extract_template_spec.py`'s decoder and
assert it reproduces the source domain object. This is the same code path that
decoded SP0302 and SP0348 in `spec/observed-fills.json`, so it is already known
to work against real files.

### Layer 3 — Microsoft Excel (manual, gated)

**No output ships to a customer until it has been opened in the same Microsoft
Excel environment R&G and the reviewer use.** LibreOffice is not a substitute and
must not appear in any acceptance path. The manual checklist:

1. Open in Excel. No repair prompt.
2. Every photo renders **in-cell**, not as `#VALUE!`.
3. Photos are in the expected slots and correctly oriented.
4. The enclosure-manufacturer dropdown on `H12` still works.
5. Hidden sheets remain hidden; unhiding shows `Lists`, `OTDR Shots`, `Example`
   intact.
6. Cell comments still appear on hover.
7. Print preview matches the master's behaviour.
8. Side-by-side against the reference sample: every value where expected.

Recorded per generation as a `VerificationResult`. Layers 1 and 2 gate delivery
automatically; layer 3 gates the *profile*, and is re-run whenever a profile or
the generator changes — not on every workbook.

## 5.7 Fixtures and regression suite

Two golden fixtures, derived from the packet's references:

| Fixture | Exercises |
|---|---|
| `sp0302-simple` | 2 cable sections, 1 splice, 4 photos, no OTDR, no routing |
| `sp0348-splitter` | 4 populated sections, 13 splitters, 35 splices, 20 routes, 5 photos |

Each fixture is a domain object plus the expected cell map. The test asserts the
generator produces exactly those cells, and the package assertions pass. When a
profile strategy changes, the expected cell map changes with it and the diff is
reviewable — which is the point.

The source workbooks stay read-only. Generated outputs go to a separate
directory. Nothing in the test suite writes to the packet.

## 5.8 PDF

Out of scope for the pilot, and worth stating why in one place. LibreOffice
conversion of SP0302 produced 20 letter pages, 14 `#VALUE!` fallbacks, and zero
photos — it does not render the format at all. Any PDF path therefore requires
Microsoft Excel or a rendering engine that implements rich-value images, which
means either a Windows/Office host in the deployment or a commercial rendering
service. That is a real cost and a real operational surface, and it should not be
taken on until someone confirms Comcast wants a PDF (Q5).

If PDF turns out to be required, the design does not change — a rendering step is
added after generation, and the same three verification layers apply to it.
