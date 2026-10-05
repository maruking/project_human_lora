# STEP3 complete image listing — supplemental omission correction

User pointed out that the previously requested supplemental still directory was absent from the current STEP3 list. Observed:STEP2 recorded/measured58 supplemental images, but normal STEP3 processed only1893 formal video frames. The prior implementation routed still face diagnostics to Revision A and therefore omitted them from normal STEP3 review/report outputs. This did not satisfy the requested complete listing.

Correction executed: bat/03_build_all_images_review.bat / scripts/build_step3_all_images_report.py builds a separate consolidated review listing from the current successful formal STEP3 results plus authoritative STEP2 supplemental receipt/report. output/reports/step3_all_images_report.csv contains1951 unique images:1893 formal results plus all58 declared stills. Supplemental filenames retain the original directory; image_path and clickable image_open are included.

The58 stills have no current STEP3 face evaluation. They are explicitly NOT_EVALUATED / step3_not_evaluated with blank face_eligible, not silently accepted/rejected or labeled A/B/C. Their recorded STEP2 metrics and separate generation/hash remain visible. Existing formal STEP3 result/hash/counts and passed/borderline/reject copies were not rewritten. Clarification is pending on whether to extend normal STEP3 to evaluate supplemental images with the same approved Gate; no such inference or production rerun was performed in this correction.

Validation: current CSV/summary hashes and formal STEP2/STEP3 generation/identity match; all58 current supplemental source bytes match STEP2 recorded hashes; combined1951 unique-row count and58 pending still rows verified;3 synthetic tests PASS (preserved formal metrics, explicit pending state, source/link safety, no A/B/C). Existing formal STEP3 CSV still matches its summary hash.

Changed:scripts/build_step3_all_images_report.py, bat/03_build_all_images_review.bat, tests/test_step3_all_images_report.py, output/reports/step3_all_images_report.csv, output/reports/step3_all_images_summary.json, docs/STEP3_ALL_IMAGES_LIST_RESULT.md, docs/README.md, knowledge/current/face-quality.md.

Rules checked:AGENTS.md/.agents/AGENTS.md, PROJECT.md, Pipeline/Data Lineage rules, relevant Current Knowledge/Decisions/Failure/Case/prior result/history. Data lineage preserved:YES. Full-row preservation:YES (1951-image derived list; formal1893-row authoritative report unchanged). Historical evidence preserved:YES. Config SSOT preserved:YES. No new threshold/selection policy, experiment or accuracy claim; documentation/memory reviewed, no new Decision/Failure record required.

Full STEP3/Revision A/downstream production batch executed:NO. Only report/list generation was executed under the user's request to include the missing images.
