# STEP2 supplemental input correction — 2026-10-02

## Cause and correction

`02_technical_metrics.bat` invokes `scripts/score_blur.py`. The previous preflight
treated every supported image under raw input as a STEP1 video frame. The current
STEP1 metadata records 1,893 frames from 67 videos, while raw input also contains
58 user-supplied stills in `Sash_high_identity-img`. Comparing 1,951 images against
the formal 1,893-frame generation therefore stopped measurement before scoring.

The local SSOT config now explicitly declares that still subtree via
`step2_blur.supplemental_dir`. Only this declared subtree is measured as additional
stills; formal STEP1 video counts, filenames, hashes and extraction metadata remain
strictly validated. Generic code contains no subject names or fixed dataset counts.
Missing or empty declared still input is an error. Both inventories are checked
again before publication. Existing metric formulas and thresholds are unchanged.

## Normal execution and outputs

The existing `bat/02_technical_metrics.bat` remains the entry point and requires no
BAT change. It reads the configured still path automatically. Expected successful
outputs for the inspected, unchanged input:

| Output under output/reports | Universe | Expected rows |
| --- | --- | ---: |
| step2_dataset_report.csv | Formal STEP1 video frames | 1,893 |
| step2_supplemental_report.csv | Explicit supplemental stills | 58 |
| step2_all_images_report.csv | Both input kinds | 1,951 |

The formal CSV keeps its original schema and video-only global/per-video ranks.
Supplemental and combined CSVs add `input_kind` and `image_sha256`. Supplemental
rows have no inferred video ID, temporal index, extraction policy or video ranks.
Their global ranks cover stills only; combined global ranks cover all images using
the existing formulas. Combined video rows retain their original per-video ranks.
The JSON summary records formal and supplemental generations/counts separately and
the combined total. Formal outliers and existing derived human reports remain
video-only. Additional still integration into STEP3 is deferred.

Any decoding failure makes the run FAIL, retaining error rows in failed audit
outputs without replacing previous successful reports. Publication exceptions roll
back the complete set of five outputs. Current-input snapshots never merge stale
rows. Previously archived reports were not restored or moved by this correction.

## Minimum validation

- `python -m unittest discover -s tests -p test_image_metrics.py`: 29 tests PASS,
  using temporary tiny images. Includes metric regression, separate/combined rows,
  repeatability, formal count mismatch, failed still decoding, and five-file rollback.
- `cmd /c bat\02_technical_metrics.bat --help`: exit 0; environment initialization,
  local config loading and CLI argument forwarding verified. This command displays
  help only; the BAT's existing success message does not imply dataset measurement.
- No real-input measurement, full batch, STEP2 report regeneration or STEP3 run.
- Full batch executed: **NO**. Normal production execution belongs to **★maru**.

## Scope and rule compliance

Rules checked: `AGENTS.md`, `.agents/AGENTS.md`, `PROJECT.md`, pipeline hard rules,
data-lineage hard rules, relevant current knowledge and accepted decisions/failures.

- Data lineage preserved: YES; formal STEP1 lineage unchanged, still hashes separate.
- Full-row preservation: YES in synthetic verification; each input appears once in
  its own report and once in combined output, including error rows in failed audit.
  Actual production coverage is pending ★maru execution.
- Historical evidence preserved: YES; no existing report/frame moves or deletions.
- Config SSOT preserved: YES; optional generic schema, explicit local input setting.
- No rule conflict. STEP3/downstream behavior and thresholds unchanged.

Changed files:

- `scripts/score_blur.py`
- `scripts/common/step2_inputs.py` (new)
- `config/config.yaml` (local SSOT)
- `config/config.schema.json`
- `config/config.example.yaml`
- `tests/test_image_metrics.py`
- `knowledge/current/technical-image-metrics.md`
- `docs/STEP2_SUPPLEMENTAL_INPUT_FIX.md` (this result)

Documentation checked: existing decisions, failures, cases, experiments and history
remain historical evidence; no new acceptance decision or production PASS recorded.
