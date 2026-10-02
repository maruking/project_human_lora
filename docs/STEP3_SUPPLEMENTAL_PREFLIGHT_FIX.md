# STEP3 supplemental-input preflight correction

Execution status: implementation/minimum synthetic validation PASS; production NOT RUN.
Algorithm validity: existing Gate formulas and thresholds unchanged.
Human calibration: unchanged; no new suitability claims or A/B/C decisions.

## Cause and change

STEP2's formal report records 1,893 video frames, separately from 58 supplemental
stills in its explicitly configured subtree. The old STEP3 preflight scanned all
1,951 images as formal video frames and raised a per-video count mismatch before
inference. Counts describe the current local input, not code constants.

`common/step3_audit.py` now reuses `common/step2_inputs.py` and the supplemental
generation recorded in the authoritative STEP2 summary. Only that declared subtree
is separated from formal validation; unknown directories remain errors. Supplemental
inventory/hashes must match STEP2 exactly, including its recorded directory. A
changed/missing/empty supplemental input requires STEP2 revalidation, rather than
silently continuing. Moving the raw subtree invalidates the recorded absolute
directory; regenerate STEP2 metadata for the new configured path in that case.

Formal STEP1 counts, per-video inventory, frame content hashes, extraction metadata
and STEP2 generation checks remain intact before/after inference. No stale rows are
merged and no expected counts, filename grammar or generation IDs are rewritten.

## Execution boundary

Normal `bat/03_face_quality_gate.bat` remains unchanged and invokes the fixed
`face_quality_gate.py`. Its console now states the formal-only processing scope.
Official STEP3 CSV preserves the formal video universe (currently 1,893 rows).
Supplemental stills are validated here but are NOT evaluated by the official Gate
or assigned invented video IDs. Their separate face diagnostics/A/B/C sidecar remain
the responsibility of existing `bat/03_revision_a_diagnostics.bat`, which covers
formal plus supplemental inputs. This correction does not run that diagnostic BAT
or extend supplemental processing into STEP4–7.

## Changes and verification

Changed files:

- `scripts/common/step3_audit.py`
- `scripts/face_quality_gate.py` (input-scope console message only)
- `tests/test_step3_supplemental_input.py`
- `knowledge/current/face-quality.md` (scoped implementation note)
- This result document.

Minimum validation:

- Four temporary tiny-input tests PASS: valid separate still generation, changed
  or missing still refusal, undeclared directory/formal corruption refusal, and
  actual Gate entrypoint with a mocked detector on one formal image. Partial output
  stays separate; the original still remains unchanged.
- Nineteen existing STEP3 tests PASS, including frozen AST hashes of Gate formula
  functions, full-row preservation, failure records and audit publication.
- Actual BAT `--help` exits 0: argument/config/environment wiring only. Its existing
  success line is not proof of production execution.
- Full batch executed: **NO**. No real-image inference, source/report relocation,
  threshold tuning, Human Review overwrite, restoration or downstream execution.

Rules checked: root/canonical AGENTS, PROJECT, pipeline/data-lineage rules, current
face-quality knowledge, relevant accepted selection/generation decisions and prior
STEP2/STEP3 results. Data lineage preserved: YES. Full-row preservation: YES for the
official formal video universe; supplementals retain their separate diagnostic
universe. Historical evidence preserved: YES. Config SSOT preserved: YES; input
boundary comes from STEP2's recorded SSOT-derived generation, no new setting.
No rule conflict. Documentation checked; historic Decisions/Failures/Cases/
Experiments/History preserved, no new algorithm Decision or production PASS claimed.

Next operator action: ★maru runs `bat/03_face_quality_gate.bat`.
