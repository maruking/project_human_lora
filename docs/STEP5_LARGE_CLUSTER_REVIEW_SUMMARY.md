# STEP5 — Largest / chain-risk 5-cluster review

REVIEW MATERIALIZATION ONLY. No clustering/hash/ranking rerun. Human judgments are blank.

[画像レビューを開く](STEP5_LARGE_CLUSTER_REVIEW.html)

Selection: cluster_size DESC, cluster_id ASC; top3 largest, then2 largest remaining chain warnings.

| Cluster ID | Size | Sources/videos | Representative | Chain warning | Selection reason |
| --- | ---: | --- | --- | --- | --- |
| DUP_9ce2fcf2d7a4d4fd7d457fcaaddf02321568670a99a8665229959ebe94c60117 | 32 | Sasha_v52 | Sasha_v52/Sasha_v52_001.png | true | TOP3_LARGEST |
| DUP_2e47ce9f72c3d35370639843773dbcc1da9c24b9ed25ea9b54550d93ffb5ff28 | 30 | Sasha_v22 | Sasha_v22/Sasha_v22_026.png | true | TOP3_LARGEST |
| DUP_ad7b106ecfa954ca385017ac676056243c2fba02103402b920084c35710697c3 | 26 | Sasha_v64 | Sasha_v64/Sasha_v64_006.png | true | TOP3_LARGEST |
| DUP_c2a12084e595f5ca8471645207776131c18a5bc0efa2e61836b788818c156f7d | 26 | Sasha_v03 | Sasha_v03/Sasha_v03_083.png | true | LARGE_CHAIN_WARNING |
| DUP_ed9137ea90f51ec18706f0a1ecfeb146931701bc333e9a9c66cae978fdf61e0a | 20 | Sasha_v68 | Sasha_v68/Sasha_v68_005.png | true | LARGE_CHAIN_WARNING |

Fallback non-warning slots: 0. LARGE_CHAIN_WARNING denotes the risk-selection slot; any fallback is disclosed here, not a fabricated warning.

Human Review: OK_CLUSTER / TOO_BROAD_CLUSTER / BAD_REPRESENTATIVE / UNSURE. No verdict assigned. HTML answers download separately; it never updates official STEP5 or the blank manifest automatically.

All5 OK: limited STEP5 sanity check is sufficient; proceed to STEP6 design/audit, not automatic inference. TOO_BROAD: STOP before STEP6 and inspect edge chaining, no immediate threshold change. BAD_REPRESENTATIVE alone: inspect selection separately, do not automatically invalidate cluster. UNSURE: retain uncertainty.

Input dataset SHA256: df761fd306d7a01949a0e8e98eaa3c1315b8b078bd00e89b12ea5efc96d70b37
All selected members/roles/ranks/representatives are copied from stored results. Source paths exist; no source pixels read/hashed/copied. Existing9 report/config files protected by unchanged SHA256.

Rules checked: AGENTS/.agents AGENTS, PROJECT, Pipeline/Data Lineage, current STEP5 Knowledge/DEC-0022. Data lineage preserved: YES. Full-row preservation: N/A for derived5-cluster subset; full1951-row official report unchanged. Historical evidence and Config SSOT preserved: YES. STEP5 algorithm/source images/STEP3/4/Human/A-B-C changed: NO. STEP6/full production executed: NO.
