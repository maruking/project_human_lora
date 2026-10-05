# HIST-006 — STEP 0 Config SSOT

Date: 2026-10-02 (Asia/Tokyo)

## Before
Example YAML described a 30-image dataset, InsightFace, 40/40/20 quotas,
component masks and aspect buckets; actual scripts used DINO, a 65-image pool,
45-image initial review and fixed quota ranges. Settings were not connected.

## After / Changed files
`config/config.example.yaml`, `config/config.schema.json`, `requirements.txt`,
all ten processing scripts, `scripts/verify_environment.py`, standalone BAT files,
`README.md`, current/decision/history indexes and implementation-gap annotations.
Added shared config loader, frozen default fixture, unit tests, configuration
knowledge, DEC-0006, this record and `docs/STEP0_VERIFICATION.json`.

## Tests performed
- Example/schema, missing-local fallback, partial-local precedence, malformed YAML,
  missing explicit file, invalid numeric/device/bool/array/maps, Windows/Unicode
  paths and traversal protection.
- Real Step1–10 argument declarations, explicit CLI override, zero/False overrides,
  shared reports path override and frozen pre-SSOT constants.
- Synthetic Step2 metrics report bytes unchanged.
- Step7: 147 synthetic CSV rows; 65 selected; CSV bytes and all copied files equal.
- Step8: 45 initial selected files and normalized console output equal.
- Baseline content/hash unchanged; Python compilation succeeds.
- Environment preflight reports missing MediaPipe/imagehash in system Python 3.10,
  CPU-only Torch and zero references. Full inference was not run.

## Known remaining inconsistencies
Historical policy documents are intended standards, not proof of implementation.
Step9 full-body face restoration still differs from component-only policy;
Step10 aligns dimensions without buckets and preserves existing gendered captions.
Step7 retains existing profile-priority behavior even when it can exceed a small
CLI target; this algorithm limitation was deliberately not changed.
Step8's existing `populate_defaults` flag does not gate auto-population; preserved.
Fixed min/max quotas are not scaled for CLI target overrides; preserved.

## Deferred issues
- Step1 scene-aware extraction
- Step3 TikTok blink / mouth metrics
- Step4 body visibility
- Step6 DINO → InsightFace
- Step7 quota redesign
- Step8 HTML dashboard
- Step9 restoration redesign / component mask gap
- Step10 caption cleanup / aspect buckets
- Step11 trained LoRA evaluation

## Interpretation / confidence
MEDIUM confidence in configuration compatibility from frozen defaults and
synthetic comparisons; no inference-based validation beyond the unchanged
historical baseline is asserted. These records add implementation facts without
rewriting prior experimental results or superseding older algorithm decisions.
