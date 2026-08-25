# 6. System architecture

## 6.1 Shape

```
┌─────────────────────────────────────────────────────────────┐
│  Phone (PWA, installed to home screen)                      │
│  ├── capture UI            Svelte 5 + Tailwind              │
│  ├── local store           IndexedDB: drafts + photo blobs  │
│  ├── sync engine           outbox queue, resumable uploads  │
│  └── service worker        app shell + offline routing      │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS, token auth
┌───────────────────────────▼─────────────────────────────────┐
│  VPS (single host, docker compose)                          │
│  ├── Caddy                 TLS, static PWA, reverse proxy   │
│  ├── API                   Bun + Hono                       │
│  │   ├── projects/locations/evidence                        │
│  │   ├── review + lifecycle                                 │
│  │   └── generation queue                                   │
│  ├── generator worker      package surgery + verification   │
│  ├── PostgreSQL            records, lifecycle, audit        │
│  └── object storage        photo originals, renders, output │
└─────────────────────────────────────────────────────────────┘
```

One host, one compose file, one backup job. The operational surface is
deliberately small because the commercial model bounds support hours, and
because a contractor's field app that is down at 7am is worse than no app.

## 6.2 Stack, and why

| Layer | Choice | Reasoning |
|---|---|---|
| Client | **SvelteKit + Svelte 5, Tailwind v4** | PWA-first, small bundle on a jobsite connection, and the stack the operator already runs day to day. |
| API | **Bun + Hono** | Same runtime as the generator, fast cold start, trivial to containerise. |
| Database | **PostgreSQL** | The commercial model is multi-tenant from day one. Starting on SQLite and migrating later is a tax paid at the worst moment. |
| Object storage | **S3-compatible** (MinIO on the VPS, or a managed bucket) | Photo payloads are ~1 GB/week/technician. They do not belong in the database or in the backup of the database. |
| Generation | **Bun worker, in-process queue** | Generation is CPU- and IO-bound for seconds, not minutes. A queue table plus a worker loop is enough; no broker. |
| TLS / static | **Caddy** | Automatic certificates, one config file. |
| Auth | **Session cookie + device-bound refresh token** | Technicians stay signed in for weeks on one phone; supervisors use a browser. |

**On reusing the Signet stack:** the operator builds and runs Bun/Hono/Svelte
systems already. Reusing that stack is a legitimate efficiency — one set of build
tooling, one deployment idiom, one debugging skill set. What must *not* be reused
is anything customer-specific. This service has its own database, its own object
store, its own host, and its own backups.

## 6.3 Offline-first capture

Field connectivity is an unresolved unknown (Q14). The design removes the
question from the critical path: **capture never touches the network.**

```
capture → IndexedDB draft (immediately, on every field change)
        → photo blob stored locally, thumbnail rendered from local blob
        → outbox entry queued
                │
                ├── online  → upload resumes, draft syncs, server acknowledges
                └── offline → nothing happens; the technician keeps working
```

Rules:

- A draft is complete and validatable **entirely offline**. Validation rules run
  client-side against the same rule definitions the server uses.
- Photos upload independently of the record, in chunks, resumable. A failed
  upload never loses the photo — it stays in IndexedDB until the server confirms
  the hash.
- Submission is a *local* state change. The outbox delivers it when it can.
- Conflict policy: a location is owned by one technician at a time. A draft
  edited offline while the same location was returned by a supervisor resolves as
  *server-wins on lifecycle state, client-wins on field data*, and surfaces the
  reviewer's return reasons on the next open.
- Storage pressure: photos are the risk. The client evicts uploaded originals
  once the server confirms the hash, keeping only thumbnails. It warns before
  local storage fills and refuses to silently drop unsynced evidence.

## 6.4 Data model in the database

```
organisations
technicians          (org, name, role, active)
projects             (org, job_number, job_name, template_profile_id, naming_pattern)
project_defaults     (project, the 11 inherited fields)
locations            (project, name, alt_name, state, work_date, assigned_technician)
enclosures           (location, placement, gps, counts, notes[])
sections             (location, slot 1..15, role, kind, payload jsonb)
splice_links         (location, endpoint_a jsonb, endpoint_b jsonb)
route_links          (location, source_section, source_port, destination, kind)
evidence             (location, bucket, original_key, render_key, sha256, bytes, fix jsonb)
otdr_tests           (location, direction, trace, fiber_number, image_key)
submissions          (location, state, profile_id, profile_version)
generated_packages   (submission, filename, object_key, sha256, generator_version, verification jsonb)
audit_events         (location, actor, kind, reason, at)
billing_events       (org, project, location, kind, at)   -- unique (location, 'finalized')
template_profiles    (id, version, master_sha256, document jsonb, published_at)
```

Notes on the shape:

- `sections.payload` is `jsonb` because `SectionKind` is a union whose arms have
  genuinely different fields. The discriminator is a real column; the arm-specific
  data is not worth five sparse tables.
- `splice_links` and `route_links` are separate tables, not one polymorphic
  table, because they render into different workbook regions and have different
  validation rules.
- `template_profiles.document` stores the whole profile so a regeneration months
  later reproduces the file that was filed, byte for byte.
- Every query that reads customer data is scoped by `organisation_id` at the
  repository layer, not by convention in each handler.

## 6.5 Lifecycle and the billing event

```
   draft ──submit──▶ submitted ──open──▶ in_review
     ▲                                      │
     │                                      ├──return──▶ returned ──edit──▶ draft
     └──────────────────────────────────────┤
                                            └──approve─▶ approved
   any state ──void──▶ void
```

The commercial posture requires: charge per successfully finalised SDS package;
corrections and regenerations of the same location do not create duplicate
charges; drafts, tests, and voids never count.

That maps to exactly one rule:

```
on transition → approved:
    insert billing_events (org, project, location, 'finalized')
    on conflict (location, kind) do nothing
```

A unique index on `(location_id, kind)` makes it idempotent by construction. A
location returned, corrected, re-approved, and regenerated eleven times bills
once. Voided locations never reach `approved`, so they never bill. This is a
database constraint rather than application logic because the pricing promise is
easier to keep than to remember.

## 6.6 Evidence storage

The numbers from §2.8: ~13–14 MB of photos per location, ~1 GB/week/technician,
~50 GB/year/technician before generated output.

```
original   full resolution, EXIF and GPS overlay intact, write-once
           → the evidence of record; never modified, never deleted while the
             project is active
render     downscaled to fit the target cell, long edge configurable
           (default 2048px, ~600 KB) → embedded in the workbook
```

A 2048px render puts a five-photo workbook near 3 MB instead of 14 MB, which
matters for the reviewer's download, the mail attachment limit, and the backup
window. The long edge is a profile setting because nobody has confirmed whether
reviewers zoom into these photos to read cable labels — if they do, the setting
goes up (`ASM-014`).

Object keys are content-addressed (`sha256`) so a re-uploaded photo deduplicates
and a corrupted upload is detectable rather than silently stored.

Retention: originals live as long as the project is active plus a contractual
tail. On cancellation the customer gets a full export — records as JSON/CSV plus
every original and every generated workbook — before anything is removed.

## 6.7 Authentication and authorisation

| Role | Can |
|---|---|
| `technician` | Read assigned projects; create and edit own drafts; submit; view own history |
| `supervisor` | Everything a technician can, plus review, return, approve, export, and edit any location in the org |
| `operator` | Manage projects, technicians, and template profiles; no access to other organisations |

- Mutation and admin endpoints check permission explicitly at the handler, not
  via middleware inference.
- Rate limits on the abuse-prone paths: photo upload, generation, and export.
- Generation is authorised per location, and the returned download URL is a
  short-lived signed link scoped to one object.
- Every lifecycle transition writes an `audit_event` with actor and reason.

## 6.8 Deployment and operations

```
docker compose: caddy · api · generator · postgres · minio
```

- **Backups.** Nightly `pg_dump` plus object-store snapshot to off-host storage.
  Restore is rehearsed before the pilot starts, not after the first incident.
- **Monitoring.** Uptime check on `/health`; alerts on generation failure rate,
  outbox backlog age, and disk headroom. Disk is the one that will actually fire.
- **Template profile updates.** Published through the admin surface, versioned,
  and applied to *new* generations only. Existing submissions keep their profile.
- **Releases.** The generator is versioned and recorded on every package, so a
  regression is attributable to a specific build.
- **Support boundary.** Bounded hours, as the commercial terms specify. The
  design keeps the surface small so that boundary is realistic: one host, one
  database, one worker, one storage bucket.

## 6.9 What is deliberately absent

- No message broker. A queue table and a worker loop handle this volume.
- No Kubernetes. One VPS, one compose file.
- No microservices. The generator is a separate process only because it is
  CPU-bound and should not block the API.
- No client-side XLSX generation. Profiles must be updatable without shipping a
  new client, and phones should not download multi-megabyte masters
  ([ADR-004](./decisions/ADR-004-server-side-generation.md)).
- No custom auth provider. Sessions and refresh tokens, done carefully.
