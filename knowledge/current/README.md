# Current Knowledge Index

This directory contains the **currently active policies and operating boundaries** across each stage of the pipeline.  
Developers and AI coding agents should consult these files first to understand current production logic.

---

## Active Policy Documents

| Topic | File | Scope | Status | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| **STEP3 BEST Ranking / current practice** | [step3-best-ranking.md](step3-best-ranking.md) | v2.2 baseline, measurement/semantic boundaries, versioned review and dated production evidence | ACTIVE; production/review completed, limited quality validation | MEDIUM |
| **Face-quality architecture and historical Gates** | [`face-quality.md`](face-quality.md) | Current v2.2 overview; earlier Gates and generation results retained as historical evidence | ACTIVE; see current BEST Knowledge | MEDIUM |
| **Deduplication / representatives** | [deduplication.md](deduplication.md) | STEP5 v2 full-row source-aware clusters, BEST representatives, pose/cluster review | ACTIVE; production pending | MEDIUM |
| **Face Pose & Quota Distribution** | [`face-pose-quota.md`](face-pose-quota.md) | STEP4 v2 stored pose/face-scale descriptors; STEP7 quotas separate | ACTIVE; STEP4 production pending | MEDIUM |
| **Identity Verification** | [`identity-evaluation.md`](identity-evaluation.md) | Step 06: InsightFace embedding similarity and imposter exclusion | ACTIVE | HIGH |
| **Selective Face Restoration** | [`selective-restoration.md`](selective-restoration.md) | Step 09: Component-only neural restoration and 100% camera skin preservation | ACTIVE | HIGH |
| **FLUX LoRA Dataset Packaging** | [`lora-dataset-flux.md`](lora-dataset-flux.md) | Step 10: Multi-aspect bucketing, prompt captioning, and trigger strategy | ACTIVE | HIGH |
| **Configuration SSOT** | [configuration.md](configuration.md) | Step00–10 runtime configuration and actual implementation gaps | ACTIVE | MEDIUM |
| **Video / Frame Organization** | [video-frame-organization.md](video-frame-organization.md) | Step1 stable IDs, original provenance, copies and per-video frames | ACTIVE | MEDIUM |

- [Technical image metrics](technical-image-metrics.md): STEP2 measurement, provenance and diagnostic boundaries (DEC-0008).

- [Project governance](project-governance.md): mandatory Rules entry, full-frame lineage and planned implementation boundaries.
