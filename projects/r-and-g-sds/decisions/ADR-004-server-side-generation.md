# ADR-004 — Generation runs on the server

**Status:** accepted · **Date:** 2026-08-25

## Context

XLSX generation could plausibly run in the browser: the master is 812 KB, and the
surgery is zip manipulation plus XML editing, both of which work client-side. That
would let a technician download the workbook without a round trip.

## Decision

Generation runs on the VPS, in a Bun worker, triggered on approval.

## Reasons

1. **Profiles must update instantly for everyone.** A client-side generator ships
   the binding to every installed PWA; a template fix would wait on cache
   expiry and app updates across every phone in the field.
2. **Photo originals live server-side.** A 14 MB workbook assembled on a phone
   means downloading every original back to the phone first.
3. **Reproducibility.** Generation is recorded with a generator version and an
   output hash. A regression is attributable to a build, not to whichever browser
   happened to run it.
4. **Verification belongs where generation happens.** Package assertions gate
   delivery; a client that can generate can also bypass them.
5. **Approval is a server-side event anyway.** Generation on approval keeps the
   billing event, the audit entry, and the artifact in one transaction.

## Alternatives rejected

| Alternative | Why not |
|---|---|
| Client-side generation | Above. Also puts the most delicate code in the least controlled environment. |
| Generate on submission rather than approval | Produces artifacts for records that may be returned, and blurs the billing boundary. |
| External queue (Redis, RabbitMQ) | Generation takes seconds and the volume is tens per day. A queue table and a worker loop are sufficient; a broker is another thing to run and back up. |

## Consequences

**Good.** One place to fix, one place to verify, one place to audit. Phones stay
light. Template changes take effect on the next generation.

**Bad.** A technician cannot produce a workbook offline. This is acceptable —
generation happens after supervisor approval, which is a desk activity, not a
field one.

**Watch.** Generation is CPU- and IO-bound for a few seconds per workbook with
multi-megabyte photo processing. It runs in a separate process so it never blocks
the API. If batch export of a 200-location job becomes common, it needs its own
concurrency limit and progress reporting.
