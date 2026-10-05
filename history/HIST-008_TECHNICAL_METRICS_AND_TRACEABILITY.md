# HIST-008 — STEP2 Technical Metrics and Traceability

Date: 2026-10-02

STEP2 preserves the existing formulas and legacy CSV contract while adding
stable input-relative frame IDs, STEP1 video ID/count validation, dimensions,
measurement statuses, JSON distributions and a compact diagnostic outlier CSV.
Measurement, diagnosis and later quality decisions have separate responsibilities.
Natural numeric ordering and repeated atomic snapshot writes make replay stable.
Historical merge remains an explicit compatibility option; it was never a cache.

Root AGENTS.md replaces the misplaced .agents instruction file, preserving the
Knowledge Maintenance protocol and adding the required retrieval order and
accepted-decision/experiment requirement for converting diagnostics to gates.
CASE-0003 records the user's low-resolution/pixelation report without presenting
reported face measurements as new STEP2 evidence. DEC-0008 clarifies the historical
STEP2 gate descriptions without changing STEP3 or the validated baseline.

At execution the prior 3550 PNG files were absent. work/frames_raw instead held
58 other images in one untracked directory, while the STEP1 manifests still
reported 71 videos/3550 frames. Completeness correctly failed despite successful
measurement of those 58 images. The 71 normalized video copies remained.
Original and alternate images were retained, and unchanged STEP1 extraction was
rerun into a separate work/frames_step1 root selected in private config. Formal
manifest IDs were retained and extraction metadata updated to the actual location.
This is input recovery, not a sampling/codec or STEP3 algorithm change.
Evidence, regression, output hashes and limitations are in docs/STEP2_RESULT.md.
