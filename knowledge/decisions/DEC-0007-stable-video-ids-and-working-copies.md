---
id: DEC-0007
title: Stable Video IDs with Manifest and Standalone Working Copies
status: ACCEPTED
date: 2026-10-02
confidence: MEDIUM
components: [video-organization, frame-extraction]
tags: [video-id, manifest, provenance, non-destructive]
supersedes: []
superseded_by: []
related_experiments: []
related_failures: []
related_cases: []
---

# Decision Record: DEC-0007 — Stable Video IDs

## Context / Problem
Download filenames may be long, random, nonportable or reordered. Using them
directly as downstream scene identifiers makes diagnosis and stable numbering
difficult. Replacing them in place loses provenance and risks irreplaceable media.

## Decision
Keep original downloaded files intact. Assign `{subject_name}_v{index:02d}` IDs
from config and create standalone byte-identical copies in `work/videos`.
Store original/normalized names and paths, size and SHA256 in a persistent CSV.
Initial natural ordering is deterministic, but existing manifest mappings always
win. Reserve normalized source IDs; append new originals after the maximum ID.
Keep missing-source mappings rather than reclaiming their indices.

Use atomic manifest checkpoints, OS advisory locking and exclusive publication
of verified temporary copies. Reject ambiguous/colliding/changed content rather
than overwrite destinations. Support dry-run and normalization-only execution.
Use per-video frame folders while preserving existing PNG filename grammar.

## Alternatives
- Rename raw inputs in place: rejected; needless risk to original media/provenance.
- Hardlink directly to originals: rejected as the default; edits to a working
  video could change the source because both names share the same data.
- Reassign all numbers by sort on every run: rejected; new downloads shift IDs.
- Use `frame_000001.jpg`: rejected here; changes established PNG filenames and
  downstream temporal parsing without a STEP1 requirement to do so.

## Facts / Evidence
The execution dataset has 71 supported videos totaling 233,751,151 bytes, and
ample free disk space for independent copies. Source names already have a
numeric ordering; natural sorting preserves that order while adding a configured
subject prefix. Unit tests verify manifest replay, append-after-71, copies that
do not share source inodes, interrupted-copy recovery and exact FFmpeg arguments.
The implementation does not download/load any AI model. Real run and integrity
verification results are reported separately in `docs/STEP1_RESULT.md`.

## Consequences
Additional video-copy storage and SHA256 I/O are accepted for safety (roughly
234 MB for this dataset). Manifest paths are local/private and ignored by Git;
move a project deliberately rather than silently remapping its absolute paths.
`--flat` conflicts with required video folders and now fails clearly.
Process all videos despite individual failures, but exit nonzero when failures
remain, as mandated by project rules. No downstream evaluation logic changes.

## Do not violate
Never overwrite/rename original media, lose original names, reassign existing
manifest IDs, hard-code a real subject in template code/config, replace the
successful sampling conditions, or bypass STEP BAT entrypoints. Changing subject
or working-video directory requires a separate manifest or deliberate migration.
