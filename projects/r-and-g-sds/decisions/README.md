# Decisions

Five decisions that shape everything else in this design. Each records the
context, the choice, the alternatives rejected, and the consequences — including
the bad ones.

| ADR | Decision |
|---|---|
| [001](./ADR-001-preserve-master-package.md) | Generate by patching a byte-preserved copy of the customer master, never by rebuilding |
| [002](./ADR-002-offline-first-capture.md) | Capture is offline-first; the network is never on the critical path |
| [003](./ADR-003-layout-profiles.md) | The workbook binding is versioned data, not code |
| [004](./ADR-004-server-side-generation.md) | Generation runs on the server, not in the browser |
| [005](./ADR-005-evidence-originals.md) | Photo originals are immutable evidence; workbooks embed derived renders |
