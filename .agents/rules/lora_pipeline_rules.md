# Real Human LoRA Pipeline — Core Project Rules

ACTIVE means a required governance policy, not proof of runtime enforcement.
PLANNED means implementation/validation is outstanding; HISTORICAL records earlier
specifications/evidence. Known differences are in
[Agent Rules Revision Result](../../docs/AGENT_RULES_REVISION_RESULT.md).
Read [PROJECT](../../PROJECT.md) and [Data Lineage Rules](data_lineage_rules.md).
Do not repair algorithms during documentation cleanup.

## Rule 1 — Pipeline Architecture and Compatibility (ACTIVE)

Keep STEP00-10 BAT entrypoints independently executable; retain the runner's calls
and nonzero failure propagation. Do not remove/combine the individual entrypoints.
GPU-intensive entrypoints retain _gpu naming. Preserve compatible source IDs,
filename grammar, CSV columns and CLI/config behavior unless a scoped change
explicitly authorizes migration. Multi-subject reusable design is required; no
current subject name, observed count or source-specific pattern becomes generic code.
Each STEP must remain within its responsibility: STEP2 technical measurement,
STEP3 face quality, STEP4 pose/composition, STEP5 duplicates, STEP6 identity,
STEP7 candidates, STEP8 human decision, STEP9 selective restoration, STEP10 export.

## Rule 2 — Real Skin and Restoration (ACTIVE policy; legacy gap)

Preserve natural skin and real source pixels. Face-quality/beauty-filter decisions
belong to STEP3, not STEP2 diagnostics. Existing STEP3 Gates remain configuration,
not new empirically validated thresholds in this revision.
Whole-face neural restoration is prohibited by the accepted component-only policy;
only anatomically scoped eyes/pupils/eyebrows/lips may be restored, preserving
cheeks/forehead/neck. [DEC-0004](../../knowledge/decisions/DEC-0004-raw-skin-preservation.md)
and [FAIL-0001](../../knowledge/failures/FAIL-0001-whole-face-codeformer.md) provide rationale.
PLANNED enforcement: existing STEP9 code uses full-body face-crop restoration with
feathering/rollback, not component masks. Do not claim raw-skin guarantees are
already enforced; document and resolve that mismatch in scoped STEP9 work.

## Rule 3 — Diversity and Quotas (ACTIVE principle; HISTORICAL numeric target)

Avoid frontal-only/close-up-only candidate pools; preserve angle and shot diversity
according to accepted evaluation policy and configured selection/review settings.
HISTORICAL: the previous rule/DEC-0005 described 40/40/20 close-up/upper/full-body.
That specification is not the current runtime allocator. Current STEP7 uses fixed
config shot/pose min/max maps; STEP8 has a separate configured review target.
No independent active quota values are defined in this rule. Read config SSOT and
[configuration knowledge](../../knowledge/current/configuration.md); defer any
quota-policy resolution to explicit STEP7/8 work, preserving historical evidence.

## Rule 4 — Human Review Gateway (ACTIVE; existing bypass documented)

STEP7 writes candidate material; STEP8 prepares/reviews the human-selected subset.
Current STEP7 output is configured candidates, not directly work/selected. STEP8
handles selected material. Keep the normal runner's review pause before STEP9/10.
Existing --skip-pause bypasses the pause; it does not prove human review or authorize
unreviewed changes. Human decision persistence and bypass policy enforcement are
PLANNED audit work. Do not silently delete source/audit rows during manual curation.

## Rule 5 — Privacy and Portability (ACTIVE)

Never publish private media, model weights, local subject identifiers or machine
absolute paths as generic template configuration/code. Resolve paths from project
root/config; external absolute sources belong in ignored local configuration.
Keep .gitignore protection and distribute config/config.example.yaml. Local audited
artifacts may identify their actual source; generic rules do not fix that subject.

## Rule 6 — Windows/Shell Safety (ACTIVE)

Keep UTF-8 chcp 65001 in BAT entrypoints. Escape CMD command separators such as
unquoted ampersands; use one shell for verified file operations. Resolve targets
before destructive operations and preserve original media/historical generations.

## Rule 7 — Config SSOT (ACTIVE)

Explicit CLI > local config > internal fallback, using the shared config loader.
The example is used when local config is absent; partial local files do not merge
all example values. Runtime paths, Gates, quotas/model settings have one config
source; Python constants are documented safety/compatibility fallbacks.
Do not independently define active settings in BAT, README or Knowledge. Docs must
identify quoted values as current defaults from config; kernels/formulas remain
algorithm code. [DEC-0006](../../knowledge/decisions/DEC-0006-config-single-source-of-truth.md).

## Rule 8 — Measurement, Lineage and Evidence (ACTIVE)

STEP2 whole-frame gradients/exposure/ranks are diagnostics, never face/identity/
selection truth. No diagnostic becomes a hard quality Gate without accepted
Decision plus supporting experiment. Preserve full-frame audit rows and reasons,
current-generation coverage and regenerable derived reports as specified exclusively
in [Data Lineage Rules](data_lineage_rules.md). Generation changes archive prior
universes; they do not justify stale-row merging. Preserve baseline/Decision/
Experiment/Failure/History evidence with explicit historical/superseded labels.
Keep dataset evaluation independent of training adapters. Additional adapters,
universal subject/generation schema and master audit remain PLANNED, not implemented
by documenting them. Review mismatches before extending legacy STEP3-10 code.
