# ADR-002 — Capture is offline-first

**Status:** accepted · **Date:** 2026-08-25

## Context

Field connectivity is unknown (Q14) and cannot be resolved without observing
technicians at work. The work happens in vaults, pedestals, and on poles. A
technician does 50–70 locations a week; losing one location's data to a failed
upload destroys trust in the product permanently, and the alternative — filling
the workbook at home — is exactly the problem being solved.

## Decision

Capture never touches the network.

- Every field change writes to IndexedDB immediately. There is no save button.
- Photos are stored as local blobs; thumbnails render from local data.
- Validation runs client-side against the same rule definitions the server uses.
- Submission is a local state change; an outbox delivers it when possible.
- Photo uploads are chunked, resumable, and content-addressed by SHA-256.
- The client evicts an original only after the server confirms its hash.
- Conflict policy: server wins on lifecycle state, client wins on field data,
  and the reviewer's return reasons surface on next open.

## Alternatives rejected

| Alternative | Why not |
|---|---|
| Online-only, retry on failure | Guarantees data loss on the first dead zone, and there is no evidence dead zones are rare. |
| Native app for offline | A PWA reaches every phone the crew already carries, installs from a link, and updates without a store. Offline is a browser capability, not a native one. |
| Optimistic sync without local persistence | Survives a network blip, not a closed tab or a dead battery. |

## Consequences

**Good.** Field connectivity stops being a project risk. The demo works in
airplane mode, which is itself persuasive. Validation feedback is instant.

**Bad.** Real engineering cost in Milestone 2: a local store, an outbox, resumable
uploads, conflict handling, and storage-pressure management. Rule definitions must
be shared between client and server as data, not duplicated as code.

**Watch.** Local storage fills up. Photos are 2–5 MB each and a technician may
capture 300 in a week. The client warns before the quota is reached and refuses
to silently drop unsynced evidence — dropping evidence quietly would be worse
than refusing to capture more.
