#!/usr/bin/env python3
"""Extract the SDS workbook binding spec straight from the source .xlsx files.

The spec files under ../spec/ are generated, never hand-written: every cell
reference in the design is derived from the real workbook package so the
binding cannot drift from the evidence.

Usage:
    python3 extract_template_spec.py <source-documents-dir> <spec-out-dir> [--raw]

Personal names, street addresses, and precise coordinates are redacted from the
generated spec by default, because the takeover packet requires contact details
and operational addresses to stay in the protected sources rather than in derived
analyses. Pass --raw for local inspection only; never commit --raw output.

<source-documents-dir> must contain the packet layout:
    SDS-Template.xlsx
    email-intake/2026-08-10-sds-sample/SDS AVALON R SEC 1 SP0302.xlsx
    email-intake/2026-08-10-splitter-sp0348/SDS Template SP0348.xlsx

Reads the OOXML package directly (stdlib only). Never writes to the sources.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RELS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"m": MAIN, "r": RELS}

CELL_RE = re.compile(r"([A-Z]+)(\d+)")


def col_to_index(col: str) -> int:
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n


def index_to_col(idx: int) -> str:
    out = ""
    while idx:
        idx, rem = divmod(idx - 1, 26)
        out = chr(65 + rem) + out
    return out


def split_ref(ref: str) -> tuple[str, int]:
    m = CELL_RE.match(ref)
    if not m:
        raise ValueError(f"bad cell ref: {ref}")
    return m.group(1), int(m.group(2))


class Workbook:
    def __init__(self, path: Path):
        self.path = path
        self.zip = zipfile.ZipFile(path)
        self.sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        self._sst = self._shared_strings()
        self.sheets = self._sheets()

    def _shared_strings(self) -> list[str]:
        try:
            raw = self.zip.read("xl/sharedStrings.xml")
        except KeyError:
            return []
        root = ET.fromstring(raw)
        return [
            "".join(t.text or "" for t in si.iter(f"{{{MAIN}}}t"))
            for si in root.findall("m:si", NS)
        ]

    def _sheets(self) -> list[dict]:
        wb = ET.fromstring(self.zip.read("xl/workbook.xml"))
        rels = ET.fromstring(self.zip.read("xl/_rels/workbook.xml.rels"))
        targets = {r.get("Id"): r.get("Target") for r in rels}
        out = []
        for s in wb.find("m:sheets", NS):
            target = targets[s.get(f"{{{RELS}}}id")]
            if not target.startswith("xl/"):
                target = "xl/" + target.lstrip("/")
            out.append(
                {"name": s.get("name"), "state": s.get("state", "visible"), "part": target}
            )
        return out

    def part_of(self, sheet: str) -> str:
        for s in self.sheets:
            if s["name"] == sheet:
                return s["part"]
        raise KeyError(sheet)

    def cells(self, sheet: str) -> dict[str, dict]:
        root = ET.fromstring(self.zip.read(self.part_of(sheet)))
        out: dict[str, dict] = {}
        for c in root.iter(f"{{{MAIN}}}c"):
            ref = c.get("r")
            v = c.find("m:v", NS)
            f = c.find("m:f", NS)
            inline = c.find("m:is", NS)
            value = None
            if c.get("t") == "s" and v is not None:
                value = self._sst[int(v.text)]
            elif inline is not None:
                value = "".join(t.text or "" for t in inline.iter(f"{{{MAIN}}}t"))
            elif v is not None:
                value = v.text
            if f is not None and value is None:
                value = "=" + (f.text or "")
            vm = c.get("vm")
            if value is not None or vm:
                out[ref] = {"value": value, "type": c.get("t"), "vm": int(vm) if vm else None}
        return out

    def merges(self, sheet: str) -> list[str]:
        root = ET.fromstring(self.zip.read(self.part_of(sheet)))
        mc = root.find("m:mergeCells", NS)
        return [] if mc is None else [m.get("ref") for m in mc]

    def defined_names(self) -> dict[str, str]:
        wb = ET.fromstring(self.zip.read("xl/workbook.xml"))
        dn = wb.find("m:definedNames", NS)
        return {} if dn is None else {d.get("name"): (d.text or "") for d in dn}

    def validations(self, sheet: str) -> list[dict]:
        raw = self.zip.read(self.part_of(sheet)).decode("utf-8")
        out = []
        for m in re.finditer(r"<dataValidation\b[^>]*>.*?</dataValidation>|<dataValidation\b[^>]*/>", raw, re.S):
            blob = m.group(0)
            sqref = re.search(r'sqref="([^"]+)"', blob)
            f1 = re.search(r"<formula1>(.*?)</formula1>", blob, re.S)
            out.append(
                {
                    "sqref": sqref.group(1) if sqref else None,
                    "kind": (re.search(r'type="([^"]+)"', blob) or [None, None])[1]
                    if re.search(r'type="([^"]+)"', blob)
                    else None,
                    "formula1": html.unescape(f1.group(1)) if f1 else None,
                }
            )
        return out

    def comments(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for name in self.zip.namelist():
            if not re.fullmatch(r"xl/comments\d+\.xml", name):
                continue
            root = ET.fromstring(self.zip.read(name))
            for c in root.iter(f"{{{MAIN}}}comment"):
                text = " ".join(
                    (t.text or "").strip() for t in c.iter(f"{{{MAIN}}}t") if (t.text or "").strip()
                )
                # First run is the author prefix in some files; keep full text.
                out[c.get("ref")] = html.unescape(re.sub(r"\s+", " ", text)).strip()
        return out

    def parts(self) -> list[dict]:
        return [{"part": i.filename, "bytes": i.file_size} for i in self.zip.infolist()]


def merge_index(merges: list[str]) -> dict[str, str]:
    """Map every merge anchor (top-left ref) to its full range."""
    return {rng.split(":")[0]: rng for rng in merges}


def block_widths(merges: list[str], row: int) -> list[dict]:
    """Return the merged blocks on `row`, left to right, as anchor/range pairs."""
    blocks = []
    for rng in merges:
        start, _, end = rng.partition(":")
        col, r = split_ref(start)
        if r != row or not end:
            continue
        ecol, erow = split_ref(end)
        if erow != row:
            continue
        blocks.append({"anchor": start, "range": rng, "col": col, "span": col_to_index(ecol) - col_to_index(col) + 1})
    return sorted(blocks, key=lambda b: col_to_index(b["col"]))


# --- Splicing Record binding -------------------------------------------------

SINGLE_FIELDS = [
    # (field id, label cell, value cell, note)
    ("form_date", "C3", "C4", "Header date. Both samples carry a date one day after the photo EXIF date."),
    ("technician", "E3", "E4", "Prefilled in the blank master with a stale name."),
    ("business_partner", "H3", "H4", "Prefilled in the blank master ('Sammons Construction')."),
    ("job_number", "C7", "C8", None),
    ("job_name", "E7", "E8", None),
    ("job_type", "H7", "H8", "Prefilled in the blank master ('SDU')."),
    ("hub_headend", "K7", "K8", None),
    ("enclosure_name", "C11", "C12", None),
    ("enclosure_alt_name", "F11", "F12", None),
    ("enclosure_manufacturer", "H11", "H12", "Only surviving dropdown on this sheet."),
    ("enclosure_type", "J11", "J12", "Prefilled in the blank master ('OTE'); both samples overwrite with '450-D'."),
    ("location_address", "C13", "C14", None),
    ("lat_long", "G13", "G14", "Free text; samples use two different formats."),
    ("placement_class", "J13", "J14", "Aerial / Underground / ISP. Label cell reads 'UG' in the blank master."),
    ("pole_tag", "K13", "K14", None),
    ("connected_sheaths", "C15", "C16", None),
    ("total_couplers", "E15", "E16", None),
    ("splices_performed", "G15", "G16", None),
    ("property_class", "I15", "I16", "Private Property or ROW."),
    ("otdr_performed", "K15", "K16", "Yes / No. Gates the OTDR Shots sheet."),
]

NOTES_ROWS = [11, 12, 13, 14, 15, 16]
NOTES_COL = "N"

SECTION_ROWS = {
    "section_header": 19,
    "role": 20,
    "cable_manufacturer": 21,
    "cable_date": 22,
    "cable_footage": 23,
    "cable_id": 24,
    "cable_count": 25,
}
FREEFORM_PAIR_ROWS = list(range(26, 33))  # label col + value col, no printed labels
RACK_SHELF_PORT_ROW = 33
WORK_PERFORMED_ROW = 35
FREEFORM_GRID_ROWS = list(range(36, 53))  # full-width per-section cells


def build_section_grid(merges: list[str]) -> list[dict]:
    header = block_widths(merges, SECTION_ROWS["section_header"])
    pairs = merge_index(merges)
    sections = []
    for i, blk in enumerate(header, start=1):
        anchor = blk["col"]
        value_col = index_to_col(col_to_index(anchor) + 1)
        value_range = pairs.get(f"{value_col}21")
        sections.append(
            {
                "index": i,
                "label_col": anchor,
                "value_col": value_col,
                "block_range_row19": blk["range"],
                "value_merge_row21": value_range,
                "block_span": blk["span"],
            }
        )
    return sections


def extract_pictures(wb: Workbook) -> dict:
    merges = wb.merges("Pictures")
    cells = wb.cells("Pictures")
    idx = merge_index(merges)

    def slot(label_ref: str, image_ref: str, group: str, slot_id: str) -> dict:
        return {
            "id": slot_id,
            "group": group,
            "caption": (cells.get(label_ref) or {}).get("value"),
            "caption_cell": idx.get(label_ref, label_ref),
            "image_cell": image_ref,
            "image_range": idx.get(image_ref, image_ref),
        }

    return {
        "sheet": "Pictures",
        "slots": [
            slot("B4", "B5", "enclosure", "enclosure_location"),
            slot("G4", "G5", "enclosure", "enclosure_before"),
            slot("L4", "L5", "enclosure", "enclosure_after"),
            slot("B19", "B20", "splicing", "splicing_1"),
            slot("G19", "G20", "splicing", "splicing_2"),
            slot("L19", "L20", "splicing", "splicing_3"),
            slot("B32", "B33", "splicing", "splicing_4"),
            slot("G32", "G33", "splicing", "splicing_5"),
            slot("L32", "L33", "splicing", "splicing_6"),
        ],
    }


def extract_otdr(wb: Workbook) -> dict:
    merges = wb.merges("OTDR Shots")
    cells = wb.cells("OTDR Shots")
    idx = merge_index(merges)
    return {
        "sheet": "OTDR Shots",
        "state": next(s["state"] for s in wb.sheets if s["name"] == "OTDR Shots"),
        "slots": [
            {
                "id": "hub_to_endsite_forward",
                "caption": (cells.get("B3") or {}).get("value"),
                "caption_cell": idx.get("B3", "B3"),
                "fiber_label_cell": idx.get("F3", "F3"),
                "fiber_value_cell": "G3",
                "image_cell": "B4",
                "image_range": idx.get("B4", "B4"),
            },
            {
                "id": "hub_to_endsite_return",
                "caption": (cells.get("J3") or {}).get("value"),
                "caption_cell": idx.get("J3", "J3"),
                "fiber_label_cell": idx.get("N3", "N3"),
                "fiber_value_cell": "O3",
                "image_cell": "J4",
                "image_range": idx.get("J4", "J4"),
            },
        ],
        "note": (
            "The blank master exposes one forward/return pair. The hidden Example sheet "
            "shows two pairs (hub-to-endsite and endsite-to-hub), so multi-direction OTDR "
            "capacity is an open template question."
        ),
    }


def extract_vocabularies(wb: Workbook) -> dict:
    cells = wb.cells("Lists")
    names = wb.defined_names()

    def read_range(ref: str) -> list[str]:
        m = re.fullmatch(r"Lists!\$([A-Z]+)\$(\d+)(?::\$([A-Z]+)\$(\d+))?", ref)
        if not m:
            return []
        c1, r1, c2, r2 = m.group(1), int(m.group(2)), m.group(3) or m.group(1), int(m.group(4) or m.group(2))
        out = []
        for ci in range(col_to_index(c1), col_to_index(c2) + 1):
            for r in range(r1, r2 + 1):
                cell = cells.get(f"{index_to_col(ci)}{r}")
                if cell and cell["value"] not in (None, ""):
                    out.append(str(cell["value"]))
        return out

    vocab = {name: {"defined_name": ref, "values": read_range(ref)} for name, ref in sorted(names.items())}

    # Equipment categories and their per-type field lists (Lists!A/B).
    categories: dict[str, list[str]] = {}
    for r in range(2, 60):
        cat = (cells.get(f"A{r}") or {}).get("value")
        field = (cells.get(f"B{r}") or {}).get("value")
        if not cat:
            continue
        categories.setdefault(str(cat), [])
        if field and str(field) not in categories[str(cat)]:
            categories[str(cat)].append(str(field))

    inline = wb.validations("Splicing Record")
    return {
        "defined_names": vocab,
        "equipment_categories": categories,
        "inline_validations": inline,
    }


# Fields carrying personal names, street addresses, or precise coordinates.
# Redacted from generated output unless --raw is passed. The *shape* of each
# value is preserved, because the shape is what the design reasons about.
REDACTED_FIELDS = {"technician", "location_address", "lat_long"}


def redact(fid: str, value: object) -> object:
    if value in (None, ""):
        return value
    text = str(value)
    if fid == "lat_long":
        return "".join("d" if ch.isdigit() else ch for ch in text)
    return f"<redacted:{fid}:{len(text)} chars>"


def decode_sample(
    master: Workbook, sample: Workbook, sections: list[dict], raw: bool
) -> dict:
    """Read a filled sample through the binding and report what landed where."""
    cells = sample.cells("Splicing Record")
    header = {}
    for fid, label_ref, value_ref, _ in SINGLE_FIELDS:
        cell = cells.get(value_ref)
        value = None if cell is None else cell["value"]
        header[fid] = value if raw or fid not in REDACTED_FIELDS else redact(fid, value)

    notes = [
        (cells.get(f"{NOTES_COL}{r}") or {}).get("value") for r in NOTES_ROWS
    ]
    if not raw:
        notes = [None if n in (None, "") else "<redacted:note>" for n in notes]

    section_data = []
    for sec in sections:
        lab, val = sec["label_col"], sec["value_col"]
        fields = {}
        for fid, row in SECTION_ROWS.items():
            ref = f"{lab if row in (19, 20) else val}{row}"
            cell = cells.get(ref)
            if cell and cell["value"] not in (None, ""):
                fields[fid] = cell["value"]
        pairs = []
        for row in FREEFORM_PAIR_ROWS:
            l = (cells.get(f"{lab}{row}") or {}).get("value")
            v = (cells.get(f"{val}{row}") or {}).get("value")
            if l not in (None, "") or v not in (None, ""):
                pairs.append({"row": row, "label_cell_value": l, "value_cell_value": v})
        grid = []
        for row in FREEFORM_GRID_ROWS:
            v = (cells.get(f"{lab}{row}") or {}).get("value")
            if v not in (None, ""):
                grid.append({"row": row, "value": v})
        rack = (cells.get(f"{lab}{RACK_SHELF_PORT_ROW}") or {}).get("value")
        work = (cells.get(f"{lab}{WORK_PERFORMED_ROW}") or {}).get("value")
        if fields or pairs or grid or rack or work:
            section_data.append(
                {
                    "index": sec["index"],
                    "label_col": lab,
                    "value_col": val,
                    "fields": fields,
                    "freeform_pairs_rows26_32": pairs,
                    "freeform_grid_rows36_52": grid,
                    "rack_shelf_port": rack,
                    "work_performed": work,
                }
            )

    pic = sample.cells("Pictures")
    filled_slots = sorted(ref for ref, c in pic.items() if c["vm"])
    return {
        "file": sample.path.name,
        "sha256": sample.sha256,
        "header": header,
        "notes_n11_n16": notes,
        "sections": section_data,
        "picture_cells_with_rich_value_images": filled_slots,
        "media_parts": [p for p in sample.parts() if p["part"].startswith("xl/media/")],
    }


def rich_value_report(sample: Workbook) -> dict:
    names = set(sample.zip.namelist())
    wanted = [
        "xl/metadata.xml",
        "xl/richData/rdrichvalue.xml",
        "xl/richData/rdrichvaluestructure.xml",
        "xl/richData/rdRichValueTypes.xml",
        "xl/richData/richValueRel.xml",
        "xl/richData/_rels/richValueRel.xml.rels",
    ]
    rels = []
    if "xl/richData/_rels/richValueRel.xml.rels" in names:
        root = ET.fromstring(sample.zip.read("xl/richData/_rels/richValueRel.xml.rels"))
        rels = sorted(
            ({"id": r.get("Id"), "target": r.get("Target")} for r in root),
            key=lambda r: r["id"],
        )
    structures = []
    if "xl/richData/rdrichvaluestructure.xml" in names:
        root = ET.fromstring(sample.zip.read("xl/richData/rdrichvaluestructure.xml"))
        structures = [s.get("t") for s in root]
    return {
        "present_parts": [p for p in wanted if p in names],
        "missing_parts": [p for p in wanted if p not in names],
        "rich_value_structures": structures,
        "image_relationships": rels,
    }


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    raw = "--raw" in sys.argv[1:]
    if len(args) != 2:
        print(__doc__)
        return 2
    src = Path(args[0])
    out = Path(args[1])
    out.mkdir(parents=True, exist_ok=True)

    master = Workbook(src / "SDS-Template.xlsx")
    sp0302 = Workbook(src / "email-intake/2026-08-10-sds-sample/SDS AVALON R SEC 1 SP0302.xlsx")
    sp0348 = Workbook(src / "email-intake/2026-08-10-splitter-sp0348/SDS Template SP0348.xlsx")

    merges = master.merges("Splicing Record")
    sections = build_section_grid(merges)
    labels = master.cells("Splicing Record")
    comments = master.comments()

    profile = {
        "profile_id": "rg-flat-2026-08",
        "description": (
            "Binding for the flattened Splicing Record variant that R&G actually files. "
            "Generated from the supplied blank master; do not hand-edit."
        ),
        "master": {"file": master.path.name, "sha256": master.sha256},
        "sheets": master.sheets,
        "splicing_record": {
            "sheet": "Splicing Record",
            "single_fields": [
                {
                    "id": fid,
                    "label_cell": lab,
                    "label_text": (labels.get(lab) or {}).get("value"),
                    "value_cell": val,
                    "value_merge": merge_index(merges).get(val, val),
                    "master_prefill": (labels.get(val) or {}).get("value")
                    if raw or fid not in REDACTED_FIELDS
                    else redact(fid, (labels.get(val) or {}).get("value")),
                    "instruction": comments.get(lab),
                    "note": note,
                }
                for fid, lab, val, note in SINGLE_FIELDS
            ],
            "notes_block": {
                "header_cell": "N10",
                "line_cells": [f"{NOTES_COL}{r}" for r in NOTES_ROWS],
                "line_merges": [merge_index(merges).get(f"{NOTES_COL}{r}") for r in NOTES_ROWS],
            },
            "section_grid": {
                "count": len(sections),
                "rows": SECTION_ROWS,
                "rack_shelf_port_row": RACK_SHELF_PORT_ROW,
                "work_performed_row": WORK_PERFORMED_ROW,
                "freeform_pair_rows": FREEFORM_PAIR_ROWS,
                "freeform_grid_rows": FREEFORM_GRID_ROWS,
                "row_labels": {
                    str(row): (labels.get(f"C{row}") or {}).get("value")
                    for row in sorted(set(list(SECTION_ROWS.values()) + [RACK_SHELF_PORT_ROW, WORK_PERFORMED_ROW]))
                },
                "sections": sections,
            },
        },
        "pictures": extract_pictures(master),
        "otdr": extract_otdr(master),
        "master_prefill_warnings": [
            {
                "cell": val,
                "field": fid,
                "value": (labels.get(val) or {}).get("value")
                if raw or fid not in REDACTED_FIELDS
                else redact(fid, (labels.get(val) or {}).get("value")),
            }
            for fid, lab, val, _ in SINGLE_FIELDS
            if (labels.get(val) or {}).get("value") not in (None, "")
        ],
        "master_stray_values": [
            {"cell": ref, "value": c["value"]}
            for ref, c in labels.items()
            if ref == "F44"
        ],
    }

    (out / "template-profile.rg-flat.json").write_text(json.dumps(profile, indent=2) + "\n")
    (out / "vocabularies.json").write_text(json.dumps(extract_vocabularies(master), indent=2) + "\n")
    (out / "observed-fills.json").write_text(
        json.dumps(
            {
                "profile_id": profile["profile_id"],
                "redacted": not raw,
                "samples": [
                    decode_sample(master, sp0302, sections, raw),
                    decode_sample(master, sp0348, sections, raw),
                ],
            },
            indent=2,
        )
        + "\n"
    )
    (out / "rich-value-images.json").write_text(
        json.dumps(
            {
                "mechanism": "Excel 'image in cell' (_localImage rich value)",
                "master": rich_value_report(master),
                "sp0302": rich_value_report(sp0302),
                "sp0348": rich_value_report(sp0348),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"wrote 4 spec files to {out}" + ("" if raw else " (redacted)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
