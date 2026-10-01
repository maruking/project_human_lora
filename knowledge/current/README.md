# Current Knowledge Index

This directory contains the **currently active policies and operating boundaries** across each stage of the pipeline.  
Developers and AI coding agents should consult these files first to understand current production logic.

---

## Active Policy Documents

| Topic | File | Scope | Status | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| **Face Quality & Filter Rejection** | [`face-quality.md`](file:///./face-quality.md) | Step 02 & 03: Blur, face sharpness, occlusion, and beauty-filter plasticity | ACTIVE | HIGH |
| **Face Pose & Quota Distribution** | [`face-pose-quota.md`](file:///./face-pose-quota.md) | Step 04 & 07: Head angles (Yaw/Pitch) and shot-type quotas (Close/Med/Full) | ACTIVE | HIGH |
| **Identity Verification** | [`identity-evaluation.md`](file:///./identity-evaluation.md) | Step 06: InsightFace embedding similarity and imposter exclusion | ACTIVE | HIGH |
| **Selective Face Restoration** | [`selective-restoration.md`](file:///./selective-restoration.md) | Step 09: Component-only neural restoration and 100% camera skin preservation | ACTIVE | HIGH |
| **FLUX LoRA Dataset Packaging** | [`lora-dataset-flux.md`](file:///./lora-dataset-flux.md) | Step 10: Multi-aspect bucketing, prompt captioning, and trigger strategy | ACTIVE | HIGH |
