# Twelve long-horizon task specifications

This document defines the binding final task requirements. Domain-specific
implementations now extend the shared resource graph, but their existence does
not establish full acceptance. V2_COMPLETION_AUDIT.md and V2_PROGRESS.md separate
current engine/browser/video evidence from still-unverified requirements.
The specifications below are not a blanket claim of verified completion.

## Common episode contract

The agent sees an ordinary desktop, a project-specific outcome request and
three demonstration videos. Each video uses different project resources but
the same operating convention. The recorder sees a private brief before the
desktop opens. No checklist, answer locations, reference actions, convention ID
or next-operation hint is shown in the evaluation desktop.

Task complexity must come from causally dependent work and observable artifacts.
Use normal concepts (projects, versions, backups, dependencies, permissions,
devices, schedules). The agent should be able to explain the workflow without
mentioning arbitrary parity, colors, shapes or invented file extensions.

Conventions are coherent practices, such as keeping originals with a review
directory versus using versioned snapshots, producing an archive versus a
folder handoff, or validating before a scheduled release versus immediately
after an interactive build. They must be operationally meaningful and support
equivalent valid action orders. Cosmetic names alone cannot define a context.

Each template needs an explicit dependency DAG and multiple valid reference
plans. Record at least one branch-triggering and one branch-free demonstration
per context. At least 25 meaningful mutations is a minimum sanity gate; it
does not replace a complexity review. Final counts are measured from actual
UI runs and exclude no-op configuration, clicks, navigation and failed attempts.

## OS-LH-01 Research handoff

Inspect a project brief and source inventory; collect approved data and notes
from multiple folders; reconcile duplicate revisions; create working copies;
edit a handoff index referencing the chosen versions; validate the inventory;
produce the requested handoff layout; verify it; deliver the bundle and receipt.

The demonstration teaches the directory layout, revision preservation practice,
index format and verification placement. The query changes filenames and
revision histories. A locked source requires identifying its owner before
retrying; a draft must remain outside the handoff.

Evidence: chosen revisions, preserved drafts/originals, accurate index, packaged
membership, checksum receipt, final delivery destination. Not just six job labels.

## OS-LH-02 Release preparation

Inspect installed tools and project configuration; repair a missing processing
dependency; organize source and assets; edit release notes; create a build task;
inspect its log; fix a configuration problem if present; rebuild; stage the
matching build output and notes; package; verify; create the release delivery.

The context teaches tool/profile selection, version naming and release gates.
At least one demonstration shows a failed build followed by log-based repair.
Queries vary the failing dependency and existing release version.

Evidence: tool configuration, repaired project file, successful build artifact,
notes matching the release, preservation of the previous release, verified bundle.

## OS-LH-03 Backup and recovery

Inventory the source tree; configure scope and retention; create a backup;
inspect its manifest; restore into an empty test directory; compare restored
contents; repair one omitted or conflicting resource according to the learned
policy; rerun the comparison; preserve the original; deliver a recovery report.

Contexts vary full versus selected-scope backup, version preservation and restore
conflict handling. The query introduces a different conflict and file ordering.

Evidence: immutable backup snapshot, actual restored files, scope coverage,
content comparison, retained original revisions, recovery receipt.

## OS-LH-04 Media ingest

Connect a camera; inspect media and sidecar metadata; import selected takes;
organize them by session; align captions with clip IDs; configure preview output;
create preview tasks; inspect failures; recover a missing sidecar; generate a
catalogue; verify source-to-preview correspondence; deliver the collection.

The context teaches ingest organization, sidecar pairing and naming practices.
Media remains virtual; the benchmark evaluates correspondence and workflow,
not a real codec. Queries vary takes, caption matches and camera availability.

Evidence: connected source, imported assets, correct metadata pairs, preview
provenance, catalogue membership and verified delivery.

## OS-LH-05 Print production

Open a document packet and printer capabilities; assemble approved sections;
edit the packet cover/index; configure paper, duplex and output order; create
a proof job; inspect page warnings; repair layout; generate a revised proof;
submit the final packet; inspect queue state; save the print receipt.

The context teaches compatible print settings and proof-before-submit practice,
not arbitrary mappings from symbols to buttons. Queries change packet sections,
printer capability and which page fails validation.

Evidence: actual layout metadata, repaired document, compatible device settings,
proof and submission referring to the same revision, final print receipt.

## OS-LH-06 Offline field kit

Inspect a field assignment; obtain its map, contacts and guide; resolve a failed
transfer; verify download revisions; arrange working resources; edit local
references; configure offline availability; build the cache; disconnect network;
test resource access; recover an uncached item; repeat the test; deliver the kit.

The context teaches cache scope, local path organization and network transition
order. A successful download alone cannot count as an offline-ready kit.

Evidence: cached bytes, local references, successful access with network offline,
all required resources, retained downloaded originals and verification receipt.

## OS-LH-07 Workspace migration

Inspect a source workspace manifest and installed tools; create the destination;
copy approved resources; rewrite manifest paths; migrate app settings; resolve
a path collision; run validation against the destination; launch the migrated
workspace; inspect its logs; compare source/destination; deliver a migration report.

The context teaches path rewrite and collision preservation policies. Query
paths differ and include nested resources; copying four files without fixing
references must fail.

Evidence: manifest resolves to new resources, configuration migration, usable
destination, content comparison and untouched source workspace.

## OS-LH-08 Failed build recovery

Inspect the failed task and log; identify a process locking the source; pause
the owner safely; preserve existing output; repair project configuration; retry
the build; inspect and address a second-stage error; run tests; package the
verified build; restore the owner's prior state; deliver the replacement.

The context teaches a diagnostic/recovery workflow and safe preservation order.
The affected file, owner and failure stage vary between episodes.

Evidence: diagnosed lock, repaired config, recovered build, passing test output,
preserved previous bundle and restored process state.

## OS-LH-09 Evidence archive

Inspect incident notifications and event logs; export the relevant time window;
collect matching source records; preserve originals; create redacted copies;
check that personal values are absent while event IDs remain; edit the incident
timeline; package evidence; verify provenance; deliver the archive and audit trail.

Contexts vary log organization, personal-field treatment and audit-record placement.
Treatment is a legitimate practice: A masks values while retaining the schema,
B removes personal fields, and C uses stable synthetic pseudonyms to retain
cross-channel links. Filtering scope follows the visible incident's sensitive
field list, not an arbitrary hidden preference. This clarifies the earlier
"redaction scope" design: the learned choice is the treatment method; omitting
required fields from filtering is always unsafe and requires repair.
All three safe treatments are accepted by tools regardless of context; the
final evaluator checks delivered bytes against the demonstrated practice.
Pseudonyms are deterministic truncated hashes of synthetic field/value pairs,
not a claim of cryptographic anonymity or production data protection.
The query changes event times and sensitive fields. Renaming files without
redacting their contents cannot succeed.

Evidence: selected time window, original integrity, absence of sensitive fields
in delivered copies, accurate timeline and traceable archive membership.

## OS-LH-10 Scheduled distribution

Inspect recipient/destination information; connect the correct share; stage a
release; configure destination access and scheduling conditions; create a
dependent distribution task; run a dry check; resolve an unavailable share;
verify staged bytes; schedule delivery; inspect the scheduled configuration;
preserve a receipt without launching premature delivery.

The context teaches destination layout, trigger/condition settings and dry-run
practice. Query destinations and availability differ from demonstrations.

Evidence: correct recipient, exact distribution membership, validated access,
dependency gates and persisted schedule; immediate execution may be incorrect.

## OS-LH-11 Storage maintenance

Inspect disk usage and owning processes; identify regenerable cache separately
from project data; back up the project; verify the snapshot; stop cache owners;
remove only safe cache entries; compact working data; compare retained content;
restore services; check space accounting; deliver the maintenance report.

The context teaches backup-before-cleanup and classification by provenance.
Queries vary cache paths and active owners; deleting the largest file is not
a valid learned procedure.

Evidence: verified pre-cleanup backup, precise deletion scope, actual virtual
space reduction, content preservation, services restored and audit report.

## OS-LH-12 Project restoration

Inspect the available snapshot versions and manifest; retrieve the appropriate
snapshot; validate it; extract into a recovery workspace; resolve version/name
conflicts; repair local references; compare recovered content; reopen the
project; restore its scheduled tasks; verify the restored configuration;
deliver a restoration receipt while preserving existing user edits.

The context teaches snapshot selection, conflict preservation and reactivation
order. Queries change snapshot versions, local edits and missing tasks.

Evidence: correct snapshot, real recovered resources, usable references,
preserved edits, restored task configuration and verification receipt.

## Required implementation review

Reject a task whose solution is merely the shared copy/rename/index/settings/six
jobs scaffold. Each task must implement its domain-specific evidence and at
least one causally necessary branch. Compare actual action/resource graphs,
not task titles. Do not publish the 12-template release until this review passes.
