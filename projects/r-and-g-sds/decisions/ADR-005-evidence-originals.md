# ADR-005 — Photo originals are immutable evidence; workbooks embed derived renders

**Status:** accepted · **Date:** 2026-08-25

## Context

SP0302 embeds four field photos totalling 13.2 MB in a 13.4 MB workbook; SP0348
embeds five totalling 14.1 MB in a 14.2 MB workbook. At 70 locations per
technician per week, that is roughly **1 GB of raw evidence per technician per
week** — about 50 GB per technician per year,
before any generated output.

This lands on hosting cost, backup windows, mobile upload behaviour on a jobsite,
the reviewer's download, and the per-technician component of the pricing model.

The photos are also *evidence*. They carry a GPS-camera overlay with timestamp,
coordinates, compass direction, address, county, altitude, and speed. If a
submission is ever disputed, the original is what matters.

## Decision

Two artifacts per photo:

| | Purpose |
|---|---|
| **original** | Full resolution, EXIF and overlay intact, write-once, content-addressed by SHA-256. Never modified. Retained while the project is active plus a contractual tail. |
| **render** | Downscaled to fit the target cell. Long edge configurable, default 2048 px (~600 KB). This is what gets embedded in the workbook. |

Both are stored in the object store, never in the database. Content addressing
means a re-uploaded photo deduplicates and a corrupted upload is detectable
rather than silently stored.

## Alternatives rejected

| Alternative | Why not |
|---|---|
| Embed originals | 14 MB workbooks: slow reviewer downloads, mail attachment limits, painful backups. No evidence the reviewer needs 12 megapixels. |
| Store only the render | Destroys the evidence of record. Non-recoverable if a submission is ever questioned. |
| Store photos in the database | Bloats every backup and restore with data that never needs transactional semantics. |

## Consequences

**Good.** Workbooks drop from ~14 MB to ~3 MB. Originals stay pristine.
Deduplication is free. Storage growth is predictable and can be quoted.

**Bad.** Two artifacts to manage, and a render pipeline to run. Retention policy
must be explicit, including what happens on cancellation — the customer gets a
full export of records, originals, and generated workbooks before anything is
removed.

**Watch.** `ASM-014`: 2048 px is a guess. If reviewers zoom in to read cable
labels off the photo, the setting goes up and the storage estimate goes with it.
That is one config value and a re-render, but it is worth asking before the
storage budget is quoted.
