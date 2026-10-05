# HIST-009 — STEP1 Revision 2: Duration-Aware Extraction

Date: 2026-10-02; DEC-0009 supersedes DEC-0001's sampling policy only.

Initial STEP1 normalized working copies and stable IDs, then extracted 50 frames
per video (71 videos, 3550 frames). STEP2 measured that historical set. The user
identified inconsistent temporal density: shorter videos were oversampled while
longer clips were sparse. The current policy uses 2 FPS with a 120-frame cap, reducing
effective FPS across the full duration when needed. No artificial minimum is used.

ffprobe duration, requested/effective FPS, nominal budget and actual count are
recorded. Initial real validation required nominal ceil(duration*FPS) exactly;
some containers/video end timestamps produced one fewer fps-filter output. Those
attempts failed safely and retained old folders. Validation was corrected to the
explicit one-frame EOF rounding envelope without padding images. Actual counts
are authoritative, and larger deficits or zero-frame output remain failures.

Policy/source/frame fingerprints replace existence-only reuse. Old generations
are archived after staged new output passes PNG/count validation. 3550 old frames
were retained with unchanged SHA256/size/mtime. Final result: 71 videos, 2001 new
frames, per-video min/median/max 15/27/120; duration min/median/max approximately
7.661/13.373/165.467 seconds. Replay reused all 2001, creating none. Video IDs and
all original/copy hashes remain unchanged. Alternate 58 images remain untouched.

Old STEP2 outputs were preserved in the private revision audit and removed from
active output paths. STEP2 full technical measurement was not rerun. Its input
reader was checked against actual STEP1 counts, with no 3550 runtime assumption.
See docs/STEP1_RESULT.md for revision-2 evidence; revision-1 result is retained.
Historical extraction experiments and docs/VALIDATED_BASELINE.md remain preserved.
