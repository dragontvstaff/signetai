# 3. Domain model

## 3.1 The central decision

The workbook's free-form regions tempt an obvious shortcut: model the app as a
grid of cells and let technicians type into it. That reproduces today's problem
in a nicer font — it cannot validate, cannot reuse, cannot catch `IMPUT`, and
cannot tell a supervisor whether a splitter leg is unassigned.

The app therefore owns a **real fiber model**, and the workbook is one rendering
of it. Cables, fibers, splitters, ports, and destinations are first-class; cell
addresses appear nowhere outside the binding layer
([`04-template-binding.md`](./04-template-binding.md)).

This also future-proofs the only certainty in the project: **the template will
change.** When it does, the model survives and the profile is re-issued.

## 3.2 Model overview

```
Organisation
└── Project (a job: 2541631 "avalon ridge sec 1")
    ├── ProjectDefaults      ← the 11 fields that never change within a job
    ├── Technician[]         ← assignment
    └── Location[]           ← one per enclosure / tap; one workbook each
        ├── Enclosure        ← identity, placement, GPS, counts, notes
        ├── Section[]        ← up to 15: cables, splitters, taps
        │   └── SectionKind  ← discriminated: cable | splitter | tap | unused
        ├── SpliceLink[]     ← fiber-level: (section, port|fiber) ↔ (section, port|fiber)
        ├── RouteLink[]      ← splitter port → downstream destination
        ├── Evidence[]       ← photos in named buckets; originals immutable
        ├── OtdrTest[]       ← conditional on enclosure.otdrPerformed
        └── Submission[]     ← lifecycle, generated packages, audit trail
```

Two relationship types rather than one, because the evidence shows two distinct
things: `SpliceLink` is a physical splice between two fibers (SP0302's single
`PORT 19` ↔ `BR/WH`); `RouteLink` is a logical downstream assignment of a
splitter output to a tap (`NP0017`). SP0348 has 35 of the former and 20 of the
latter, and they render into different regions of the workbook.

## 3.3 Types

Written to the repository's TypeScript conventions: no `enum`, no `any`,
discriminated unions over optional-property bags, `readonly` throughout.

```ts
// ---------- identity ----------

type Id<T extends string> = string & { readonly __brand: T }

type ProjectId  = Id<'project'>
type LocationId = Id<'location'>
type SectionId  = Id<'section'>

// ---------- project ----------

interface Project {
  readonly id: ProjectId
  readonly jobNumber: string          // 2541631
  readonly jobName: string            // "avalon ridge sec 1"
  readonly defaults: ProjectDefaults
  readonly templateProfileId: string  // e.g. "rg-flat-2026-08"
  readonly namingPattern: string      // ASM-009
  readonly status: 'active' | 'archived'
}

/**
 * The eleven header fields that were byte-identical across both filled
 * references. Inherited into every location; each one still requires explicit
 * technician confirmation the first time a location is opened (ASM-003),
 * because the blank master ships with stale values in these same cells.
 */
interface ProjectDefaults {
  readonly businessPartner: string      // "Sammons Construction"
  readonly jobType: string              // "SDU"
  readonly hubHeadend: string           // "TXWS"
  readonly enclosureManufacturer: string
  readonly enclosureType: string        // "450-D"
  readonly placement: Placement
  readonly propertyClass: PropertyClass
  readonly otdrPerformed: boolean
  readonly poleTag: string | null
}

type Placement     = 'aerial' | 'underground' | 'isp'
type PropertyClass = 'private' | 'row'

// ---------- location ----------

interface Location {
  readonly id: LocationId
  readonly projectId: ProjectId
  readonly name: string                 // "SP0348" — enclosure name from design maps
  readonly alternateName: string | null
  readonly enclosure: Enclosure
  readonly sections: readonly Section[]
  readonly splices: readonly SpliceLink[]
  readonly routes: readonly RouteLink[]
  readonly evidence: readonly Evidence[]
  readonly otdr: readonly OtdrTest[]
  readonly state: LocationState
  readonly workDate: string             // ISO date of the field visit
  readonly assignedTechnicianId: string
}

interface Enclosure {
  readonly manufacturer: string
  readonly type: string
  readonly placement: Placement
  readonly poleTag: string | null       // required when placement === 'aerial'
  readonly propertyClass: PropertyClass
  readonly otdrPerformed: boolean
  readonly location: GeoFix
  readonly connectedSheaths: number
  readonly totalCouplers: number        // "mux's/splitters in the enclosure"
  readonly splicesPerformed: number     // derived, technician-confirmable
  readonly notes: readonly string[]     // up to 6 lines → N11:N16
}

/**
 * GPS is captured structurally by the app. `address` is technician-confirmed and
 * never overwritten by reverse geocoding, because photo overlays inside a single
 * workbook disagree on the street text for near-identical coordinates.
 */
interface GeoFix {
  readonly latitude: number             // decimal degrees, -90..90
  readonly longitude: number            // decimal degrees, -180..180
  readonly accuracyMetres: number | null
  readonly capturedAt: string           // ISO 8601
  readonly address: string              // canonical, technician-confirmed
  readonly addressSource: 'geocoded' | 'edited' | 'manual'
}

// ---------- sections ----------

/**
 * One of the 15 columns on the Splicing Record. `slot` is the workbook column
 * index (1..15) and is assigned by the binding layer, not chosen by the user.
 */
interface Section {
  readonly id: SectionId
  readonly slot: number                 // 1..15
  readonly role: 'input' | 'output'
  readonly kind: SectionKind
  readonly rackShelfPort: string | null // ISP locations only
  readonly workPerformed: string | null
}

type SectionKind =
  | { readonly type: 'cable';    readonly cable: Cable }
  | { readonly type: 'splitter'; readonly splitter: Splitter }
  | { readonly type: 'tap';      readonly tap: Tap }
  | { readonly type: 'unused' }

interface Cable {
  readonly manufacturer: string         // canonical, from Sheath_Manufacturer
  readonly manufacturedOn: string | null
  readonly footage: number              // stored as a number; unit rendered separately
  readonly cableId: string
  readonly fiberCount: number           // 24, 48, 288 …
  readonly bufferSize: number | null
  readonly ribbon: boolean | null
  readonly spliceType: 'butt' | 'ring-cut' | null
}

interface Splitter {
  readonly ratio: SplitRatio            // canonical casing: "1x16"
  readonly manufacturer: string | null
  readonly outputs: number              // derived from ratio; 16 for 1x16
}

type SplitRatio = '1x2' | '1x3' | '1x4' | '1x8' | '1x16' | '1x24' | '1x32' | '1x64'

interface Tap {
  readonly tapId: string                // "NP0017"
  readonly ports: number | null
  readonly tailLength: number | null
}

// ---------- relationships ----------

/**
 * One physical splice. Both endpoints must resolve to a section on this
 * location. SP0302's single splice is
 *   { a: { section: 1, port: 19 }, b: { section: 2, buffer: 'BR', fiber: 'WH' } }
 */
interface SpliceLink {
  readonly a: FiberRef
  readonly b: FiberRef
}

type FiberRef =
  | { readonly kind: 'fiber'; readonly sectionId: SectionId; readonly buffer: FiberColour; readonly fiber: FiberColour }
  | { readonly kind: 'port';  readonly sectionId: SectionId; readonly port: number }

/** TIA-598 order. Stored canonically; rendered with the customer's abbreviations. */
type FiberColour =
  | 'BL' | 'OR' | 'GR' | 'BR' | 'SL' | 'WH'
  | 'RD' | 'BK' | 'YL' | 'VI' | 'RS' | 'AQ'

/**
 * A splitter output assigned to a downstream destination. `destination` is a tap
 * or terminal identifier ("NP0017"); Gabriel's voice note calls these "tapas"
 * and refers to them as MP/NP numbers. Meaning unconfirmed (Q8) — treated as an
 * opaque, validated identifier.
 */
interface RouteLink {
  readonly sourceSectionId: SectionId
  readonly sourcePort: number           // 1-based within the splitter
  readonly destination: string
  readonly destinationKind: 'tap' | 'splitter' | 'other'
  readonly downstreamSectionId: SectionId | null  // when it feeds another section
}

// ---------- evidence ----------

interface Evidence {
  readonly id: string
  readonly bucket: EvidenceBucket
  readonly originalKey: string          // immutable object-store key, full resolution
  readonly renderKey: string            // downscaled derivative embedded in the workbook
  readonly capturedAt: string
  readonly fix: GeoFix | null           // structured, from the device
  readonly bytes: number
  readonly sha256: string
}

/**
 * Buckets are named by what the photo shows, not by which cell it lands in.
 * The bucket → cell mapping lives in the template profile, because both filled
 * references put every photo in the splicing slots and left the three enclosure
 * slots empty (ASM-008).
 */
type EvidenceBucket =
  | 'enclosure_location'
  | 'enclosure_before'
  | 'enclosure_after'
  | 'splice_tray'
  | 'closed_condition'
  | 'other'

interface OtdrTest {
  readonly direction: 'hub_to_endsite' | 'endsite_to_hub'
  readonly trace: 'forward' | 'return'
  readonly fiberNumber: string
  readonly imageKey: string
}

// ---------- lifecycle ----------

type LocationState =
  | 'draft'        // technician editing; may be offline-only
  | 'submitted'    // complete, queued for review
  | 'in_review'
  | 'returned'     // sent back with reasons; editable again
  | 'approved'     // billable event fires here, once, idempotently
  | 'void'         // test/abandoned; never billable, never delivered

interface Submission {
  readonly locationId: LocationId
  readonly state: LocationState
  readonly templateProfileId: string
  readonly profileVersion: string
  readonly generatedPackages: readonly GeneratedPackage[]
  readonly events: readonly AuditEvent[]
}

interface GeneratedPackage {
  readonly filename: string
  readonly objectKey: string
  readonly sha256: string
  readonly generatedAt: string
  readonly generatorVersion: string
  readonly verification: VerificationResult
}

interface AuditEvent {
  readonly at: string
  readonly actorId: string
  readonly kind: 'created' | 'submitted' | 'returned' | 'approved' | 'voided' | 'regenerated'
  readonly reason: string | null
}
```

## 3.4 Why these particular shapes

**`SectionKind` is a discriminated union, not a bag of optional fields.** The
hidden `Lists` sheet proves the original template was type-driven: `Sheath`,
`Mux/Coupler`, `Fiber Tap/Tail`, `Node Cable`, `Demark`, each with its own
required fields. The flattened profile collapsed that into five generic cable
fields, but the underlying reality did not change — SP0348's section 2 is a
splitter, not a cable, and forcing it through cable fields is exactly why `1X16`
ended up in the `Input/Output` row. Modelling the type restores validation and
makes a future type-driven profile a rendering change, not a migration.

**`SpliceLink` endpoints are `FiberRef`, not strings.** The whole point is to
refuse a splice that references a fiber on a cable that does not exist, or port
19 of a 16-port splitter.

**`RouteLink.destination` is an opaque validated string.** `NP####` semantics are
unconfirmed (Q8). Modelling it as a typed reference now would encode a guess into
the schema; validating its *shape* while keeping it opaque costs nothing and
survives whatever the answer turns out to be.

**`splicesPerformed` is derived but stored.** It equals `splices.length` under the
app's model, but SP0348's `Total Couplers = 3` against 13 splitters shows the
customer's counts do not always agree with the drawing. Store what is filed,
compute what is true, and warn on divergence rather than silently overwriting the
technician.

**`Evidence` carries two keys.** The original is immutable evidence with its GPS
overlay intact; the render is a downscaled derivative sized for the target cell.
13.2 MB of photos in one workbook is a hosting bill, a mobile upload failure, and
a reviewer waiting on a download ([ADR-005](./decisions/ADR-005-evidence-originals.md)).

**`GeoFix.address` has a source.** Reverse geocoding is a suggestion; the field
records which it was, so a reviewer can see whether a human confirmed the street.

## 3.5 Fiber ordering

Standard TIA-598 order is used for both buffer tubes and fibers within a tube:

`BL · OR · GR · BR · SL · WH · RD · BK · YL · VI · RS · AQ`

SP0348's section 3 walks `BL/BL`, `BL/OR`, `BL/GR`, `BL/BR` — the first four
fibers of the blue tube, in order. This lets the app offer "next fiber" as a
single tap during capture, which is the difference between a four-minute
location and a fifteen-minute one, and it makes gaps visible: a jump from `GR` to
`WH` is either a mistake or a deliberate skip worth confirming.
