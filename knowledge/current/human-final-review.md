---
topic: human-final-review
last_updated: 2026-10-07
status: ACTIVE
confidence: MEDIUM
related_decisions: [DEC-0028]
related_failures: []
related_cases: [CASE-0005]
---

# STEP8 Folder-Based Human Final Review

step8_folder_review_v3 is the implemented normal workflow, consuming complete
STEP7 v2.2 BASE+additional candidates. Source/frame/generation/feedback hashes stay
mandatory. Production preparation is deferred until STEP7 rerun and Chappy review.

Explorer surface: 00_ALL_RANKED; 01_BY_SHOT/CLOSE_UP,UPPER_BODY,FULL_BODY;
02_BY_POSE/FRONTAL,THREE_QUARTER_LEFT,THREE_QUARTER_RIGHT,PROFILE_LEFT,PROFILE_RIGHT;
03_BY_VERTICAL/LOOKING_UP,LEVEL,LOOKING_DOWN; 99_ACCEPT. All directories are created
including empty categories. NOT_EVALUABLE stays visible in ALL. Identical images
may appear across views. O-prefixed filenames preserve BEST descending order.
Copy desired image from any VIEW into99_ACCEPT with its original review filename;
only99_ACCEPT controls unique-frame acceptance. VIEW inventory is immutable during
collection. Config count35–45/target40 and soft guidance remain unchanged.

Nonempty99_ACCEPT and all legacy v2 reviews require explicit --reset-review for
rebuild; it archives prior sessions and choices. No migration/prepare ran now.
[Decision](../decisions/DEC-0028-step7-base-additive-step8-views.md),
[implementation](../../docs/STEP7_STEP8_REVIEW_REDESIGN.md).

Collection preserves every upstream row and all values. Candidate decisions are
STEP8_ACCEPT or STEP8_NOT_SELECTED; latter is not a bad-image Reject. Fatal/nonpool
rows remain non-applicable audit rows. Count shortages/excess require Human action;
soft guidance never overrides quality or chooses more images automatically.

Final source for downstream: validated step8_human_selection.csv + VALID summary,
STEP8_ACCEPT only. ACCEPT folders are not downstream SSOT. Identity stays diagnostic;
preferences are allowed only in ★maru's Human decisions. Review/stage/archive copies
are excluded from upstream source inventories. Do not edit folders during collection.

STEP9 handoff loader is implemented/tested, but normal legacy restoration route
STOPs after CSV validation because its directory input and full-face implementation
need a separate scoped revision. No STEP9+ execution/readiness claim. Legacy STEP8
code and old outputs remain history. Existing runner still STOPs afterSTEP5.

59 scoped synthetic/regression tests PASS; current STEP7 preflight-only PASS1951
rows. No production preparation/collection/STEP9. Old v2 evidence remains in
DEC-0026 and STEP8_FOLDER_REVIEW_IMPLEMENTATION.md.

Rare Profile amendment: STEP8 preflight permits explicit eligible RARE_PROFILE_REVIEW
rows outside guard, solely PROFILE_LEFT/RIGHT; no generic guard bypass. Source/feedback
proof and99_ACCEPT authority remain unchanged. Production prepare still deferred.

2026-10-07 collect robustness: VIEW extras with exactly the hash of an expected
candidate in the same VIEW are redundant presentation copies only. They do not
change candidate/accept counts. Record warning/path audit and pin their hashes.
Missing expected copies, edited/unknown/wrong-category extras and any unknown
99_ACCEPT filename still STOP. Existing review/choices untouched by this repair.
[Repair report](../../docs/STEP8_VIEW_COPY_COLLECTION_FIX.md).
