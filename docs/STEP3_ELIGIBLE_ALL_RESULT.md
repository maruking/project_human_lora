# STEP3 All Eligible Review

All62 current machine-eligible frames across15 videos are displayed, with exact
source identity coverage. [Open full review](STEP3_ELIGIBLE_ALL_REVIEW.html).
Full copies/plain face crops and recorded threshold cards are provided for every
frame. This list preserves automatic eligibility, not final human/training adoption.

User explicitly judged Sasha_v63/Sasha_v63_020.png and Sasha_v69/Sasha_v69_014.png
unacceptable due to blur. These are human observations, saved in a separate
output/reports/step3_eligible_human_review.csv with generation/source hashes and
production_label_applied=false. Both remain in the machine-OK list and are clearly
marked human REJECT. Other frames have no recorded human decision.

v69 is provisionally FULL_BODY, where current code does not reject on eye sharpness,
eye presence, skin texture or plasticity. This explains its four inactive cards;
it does not establish human quality. v63 is UPPER_BODY and recorded faceLaplacian
66.080/threshold50, eyeSharpness1.812/threshold1.6. No thresholds are changed in
response to these observations.

New derived outputs: eligible_all_review HTML/JSON/CSV/summary,62 full copies/62
plain crops, human-feedback sidecar and eligible_all_audit. Source production CSV,
Gate formulas/config,2,001 raw frames and prior25/10-frame review bytes are preserved.
No browser label storage is read/written, no human decision is auto-applied, and
no STEP4+ work is performed. User-reported completion of the25-frame review does
not imply that its browser labels have been imported or analyzed here.

Verification: exact current eligible identity set/62 unique frame IDs;62 full
copies match originals and62 plain crops match existing logic; all62 page navigation
and human-reject markers verified using a synthetic DOM. Protected hashes match.
Browser visual QA not performed because file access is blocked by browser policy.

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md,
.agents/rules/lora_pipeline_rules.md, .agents/rules/data_lineage_rules.md and relevant
Current/accepted Decisions/Failures/Cases/STEP results/History previously read.
Data lineage preserved: YES. Full-row preservation: YES (2,001 source;62 derived).
Historical evidence preserved: YES. Config SSOT preserved: YES.
README, Current Knowledge, Decisions, Failures, Cases, Experiments and History
checked: Documentation checked; no update required beyond this scoped result.
No new architecture/threshold Decision or unrelated optimization. Ready only for
human inspection of machine-OK frames; accuracy/tuning/automatic application deferred.
