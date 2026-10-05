---
id: EXP-20261002-002
title: Duration-Aware STEP1 Extraction and Safe Reuse
date: 2026-10-02
hypothesis_status: VALIDATED
confidence: MEDIUM
components: [frame-extraction]
tags: [duration, fps, cache, regression]
related_decisions: [DEC-0009, DEC-0007]
related_failures: []
related_cases: []
---

# Experiment Record: EXP-20261002-002

## Objective and setup
Validate technical extraction density/cap, stable provenance, data protection and
policy-sensitive reuse. Windows/Python 3.10, FFmpeg/ffprobe, 71 normalized videos.
Config: frame_extraction sample_fps=2, max_frames_per_video=120, policy_version=2;
step1_extract trims=0. Same PNG/native dimensions and -q:v 2; fps round=up.

## Commands

```cmd
bat\01_extract_frames.bat --dry-run
bat\01_extract_frames.bat
py -3.10 -m unittest discover -s tests -q
```

Repeat STEP1 with identical config. No full STEP2 measurement command was run.

## Measured facts
71 successful videos; 2001 valid PNG frames; zero zero-frame videos or final failures.
Duration seconds min/median/max: 7.660998 / 13.372993 / 165.466667.
Frame count min/median/max/total: 15 / 27 / 120 / 2001.
The 165.467-second video uses approximately 0.725 FPS across the whole duration,
not the first 60 seconds. Its last output-grid timestamp exceeds 98% of duration.
Replay reused all 2001 frames, creating zero; metadata and current hashes match.
3550 historical frames retained with identical hashes/sizes/mtimes in archive.
71 source/copy SHA256 values and formal ID mapping match prior records. Alternate
58 images remain at their existing paths. Baseline SHA256 is unchanged.
Some initial nominal ceil-count checks failed by one; old frames were retained.
EOF rounding validation now accepts nominal count or one fewer, records actual
counts and rejects zeros, larger deficits and excess outputs. No frame padding.

## Tests and interpretation
Unit tests cover 3/10/30/100-second plans (6/20/60/120), cap effective FPS, invalid
durations, config/CLI precedence, policy mismatch, legacy metadata absence, corrupt
cache, explicit overwrite preservation, failed-generation retention, duration
failure continuation, EOF counts, naming and provenance. Existing configuration,
manifest and STEP2 metric tests remain. See docs/STEP1_RESULT.md for final totals.

Technical behavior is validated. Improved pose/expression coverage and downstream
quality are policy motivations, not visually measured outcomes. STEP2 needs a new
run for this frame generation; prior measurements are historical only.
