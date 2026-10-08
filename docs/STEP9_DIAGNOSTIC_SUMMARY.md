# STEP9 Diagnostic Summary

STEP8_ACCEPT対象: **40枚**

RESTORATION_NOT_NEEDED: **30枚**

REVIEW_RECOMMENDED: **10枚**

## 判定の範囲

既存STEP9のFULL_BODY限定条件を使用。顔短辺 < 190.0px または旧eye_sharpness < 2.0。境界値は未満比較。CLOSE_UP/UPPER_BODYは既存のraw保護対象です。

face_min_dimensionは既存値、または保存済bbox幅・高さのmin（既存STEP3と同じ式）。再検出はありません。旧eye_sharpnessが無い場合は左右眼local_detailで代用しません。FULL_BODYの旧眼評価が欠ける場合、修復不要と断定できないためREVIEW_RECOMMENDED。これは修復指示ではありません。

canonical Laplacian/Tenengrad、左右眼/detail/blur診断、face_scale、BEST/rankをCSVにそのまま記録。STEP9にはcanonical値用の既存閾値がないため、この値へ新しいcutoffを適用しません。BESTの順位・スコアやSTEP8採用は変更しません。RESTORATION_NOT_NEEDEDは既存STEP9対象条件による判定で、画像の完全な品質保証ではありません。

- face_min_dimension: measured 40/40, min 229.0, max 1325.0
- face_laplacian_canonical_192: measured 40/40, min 21.75522105447555, max 527.6668723416917
- face_tenengrad_canonical_192: measured 40/40, min 2423.5738932291665, max 11525.453070746527

## REVIEW_RECOMMENDED一覧

| global rank | 画像 | scale | 顔短辺 | canonical Laplacian | 理由 |
|---:|---|---|---:|---:|---|
| 9 | [Sash_high_identity-img/スクリーンショット 2026-09-30 111838.png](file:///C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/work/frames_raw/Sash_high_identity-img/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88%202026-09-30%20111838.png) | FULL_BODY | 333.0 | 97.88403516934243 | EXISTING_STEP9_EYE_METRIC_UNAVAILABLE |
| 13 | [Sash_high_identity-img/SaveTik.co_7543503138088537379_2.jpeg](file:///C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/work/frames_raw/Sash_high_identity-img/SaveTik.co_7543503138088537379_2.jpeg) | FULL_BODY | 307.0 | 195.4417095353574 | EXISTING_STEP9_EYE_METRIC_UNAVAILABLE |
| 19 | [Sash_high_identity-img/スクリーンショット 2026-09-30 111248.png](file:///C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/work/frames_raw/Sash_high_identity-img/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88%202026-09-30%20111248.png) | FULL_BODY | 417.0 | 107.76348954365577 | EXISTING_STEP9_EYE_METRIC_UNAVAILABLE |
| 46 | [Sash_high_identity-img/スクリーンショット 2026-09-30 111857.png](file:///C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/work/frames_raw/Sash_high_identity-img/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88%202026-09-30%20111857.png) | FULL_BODY | 367.0 | 63.362626746941714 | EXISTING_STEP9_EYE_METRIC_UNAVAILABLE |
| 49 | [Sash_high_identity-img/スクリーンショット 2026-09-30 105518.png](file:///C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/work/frames_raw/Sash_high_identity-img/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88%202026-09-30%20105518.png) | FULL_BODY | 324.0 | 337.249480491803 | EXISTING_STEP9_EYE_METRIC_UNAVAILABLE |
| 50 | [Sasha_v05/Sasha_v05_021.png](file:///C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/work/frames_raw/Sasha_v05/Sasha_v05_021.png) | FULL_BODY | 470.0 | 46.4193657298147 | EXISTING_STEP9_EYE_METRIC_UNAVAILABLE |
| 63 | [Sash_high_identity-img/スクリーンショット 2026-09-30 110039.png](file:///C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/work/frames_raw/Sash_high_identity-img/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88%202026-09-30%20110039.png) | FULL_BODY | 320.0 | 39.41460492213567 | EXISTING_STEP9_EYE_METRIC_UNAVAILABLE |
| 66 | [Sash_high_identity-img/スクリーンショット 2026-09-30 110146.png](file:///C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/work/frames_raw/Sash_high_identity-img/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88%202026-09-30%20110146.png) | FULL_BODY | 266.0 | 33.449468751012546 | EXISTING_STEP9_EYE_METRIC_UNAVAILABLE |
| 97 | [Sash_high_identity-img/スクリーンショット 2026-09-30 110956.png](file:///C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/work/frames_raw/Sash_high_identity-img/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88%202026-09-30%20110956.png) | FULL_BODY | 229.0 | 21.75522105447555 | EXISTING_STEP9_EYE_METRIC_UNAVAILABLE |
| 125 | [Sash_high_identity-img/スクリーンショット 2026-09-30 110056.png](file:///C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/work/frames_raw/Sash_high_identity-img/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88%202026-09-30%20110056.png) | FULL_BODY | 310.0 | 29.34100450115439 | EXISTING_STEP9_EYE_METRIC_UNAVAILABLE |

## Evidence / execution boundary

Derived subset only: STEP8 full audit unchanged; all accepted frame IDs retained. No full-generation STEP9 audit replacement.

```json
{
  "accepted_total": 40,
  "diagnostic_rows": 40,
  "subset": "STEP8_ACCEPT only",
  "step8_session_id": "0aee90574e714fb5b6d50709136243fa",
  "input_sha256": {
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\output\\reports\\step8_human_selection.csv": "36caa6f5b9ff374a8c8219f7e5a3443bab80c57e05683b713440af32f98e2fbb",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\output\\reports\\step8_selection_summary.json": "3ab73659e3333b27262e07b789662f77c3debf83986850edc36f3905ee1c57b8",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\output\\reports\\step8_review_manifest.csv": "fcb0bc2058ea0edee23e1d746c896ca653e985e9abbae75cf5a446ac171c56b8",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\output\\reports\\step8_review_preparation.json": "30fda83a331d73cabb6160b4cc2ea2b00eee050a3d9014a1e1aaf0d2ffdc07ad",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110631.png": "6ffe9d03f9da2515801fad6dfb9f8cf045d65c4b9afff09930e42745a586d558",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 105042.png": "b00b7424e495a3008ed527dad58967eb5ec58d47c7126c9388c29d4821b1a608",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\652794808_18008722232838431_6335316425841053458_n.jpg": "7e79954866df79ee93eb2603785c36d6dc37308bb7965c8f72d004fc1da683f1",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 111838.png": "8ad01e4df7a74e7d3c853f1976fff086c8607af47f79d8bf0c4212b7f367932a",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 105148.png": "42d1c0835c99d8c65838be3837379c1b787341efd5be8282aa94540a17ba85a5",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\SaveTik.co_7543503138088537379_2.jpeg": "eec26220770cc91fb2d77dc2718a6f4c6752ccb07e02fe03b31dab942f3c9094",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\654025529_18101141824898533_326058541450589604_n.jpg": "914f8228e99602a9d71ae2f4f9796ddcc5122a5011fc49b05dd4a079bea8b5b7",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 105344.png": "4dbced93c1e4d05b516c65feef30da7cc9bfa6917f24e4e54927dfdd2e592a85",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110644.png": "c4ddd636159cacc32e7d0fab42fd6069d8c5aba60b930399c5f2d3ea49bf2e5e",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sasha_v23\\Sasha_v23_001.png": "8d189f91cdfbb280fe60fd325a5f5bc8a4888e2060de851791df8694c7b147b2",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 111248.png": "9d0903274b427c66e064f12ca61d2902ec4177fc3c665aa9917ebadf66c973f6",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 111038.png": "82329e6ebf99d44898b69126cd292a9b8a604eaf6df70247fdbbea04ecb551c8",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 111214.png": "8eddea217ac67630f87aa72c7322ab5c14f654135e0a7c2102687c4a173b1086",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 111403.png": "58c342a9abcf28674abf22911d8e2425fadcb8fa603bb677ab6b5cb4dc61e082",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 112018.png": "ce96ca9f1169a10beac00bc5e098f956629374b3d62bd63f6d3fbfd03de1b6fe",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110609.png": "a0187e624e4d50d20edcb5cd1acc1e6c644a896dae14b98fdc748d2daa502645",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110439.png": "16bb9d481f23ed13e9e856fbe29858cf11db3a1f314dcac577aed1066e270119",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110314.png": "8a0196bb5640a5fba0510741f1cdb5f6faaa258ae90716a61349945c95a035ec",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110734.png": "0eada9a3cf06146442f336116d5d12c367c7a9eff1948b7c58e6c467749e0a9b",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 111314.png": "eccda1ac898b0071e7a7e5e555b6a5950d377ddba1bd62d84c5dcbb4de5bec42",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 111340.png": "4dcea64e759071488186391c35a7cca65df7deafc8386a2adcc3db30a5476efb",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 111946.png": "da9f2740e721b0ee72b797b2b74cb69a24c4171736edb29eb07eeac6a2a726ca",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110933.png": "039598d8883d320f0faf23e0a92e89930e7c8f4431dc8e385b759b5862aaab20",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 111857.png": "e08a6b7a2c2c68f6a312a5d6edadd218afdb9c13197e19148413e123c322c05b",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 105518.png": "ca5b6f723dff330e6dcaa087927cc16683eff75cae8019b43c04386117c9c931",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sasha_v05\\Sasha_v05_021.png": "62833f8c8ab82df9d18b3fa299130e152fbe8e52505141860f8babece139ff68",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110409.png": "572862e0937b5ab122f78853f6db2b5d3acdc3b1b2bc2662762e086a03b5107a",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110424.png": "2a1b6fa8f24cc5ea4a658d6851c65c5f986488949ccb7d07c7d09d4e390151cd",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110504.png": "6a6adfe01ab3f532088b9fddfff186e13aebcf6f76b944ba93e3b05bb1858b0a",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110039.png": "2144136bb1d9e3e9bd4b1b132b88c224f8c54962ba06dfdbe6b597572002482d",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110146.png": "8fc91b287245c84dacf198e8926168a23dafec8e757c6fb4d124a44895af10fb",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sasha_v22\\Sasha_v22_020.png": "1e87833fca47593501ecae97a6a74ad983a2ec6c6de93cb990bbb92f4c57c0f7",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sasha_v41\\Sasha_v41_005.png": "8337064d693533ddb8392c91635f121b67b677f0aa36633db0c8a7d20c5ffbc3",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sasha_v22\\Sasha_v22_035.png": "abe38c9fd5c7b35edc1f0b7e8dbe833cbcf3189f2ec3185347fc8dcfd855ac0e",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110956.png": "39f50451c23a76c75723bfcbf9b8ca3bdf2d6932d66b2be28894cbe17f5c3da1",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sasha_v08\\Sasha_v08_020.png": "7e45e25d4167d081f6ce47feecf7886ee22b16df17d3ae6f37508a44ca57f637",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sasha_v23\\Sasha_v23_002.png": "b5f5e30559ee45f282c75c1000aadbf1b739957702e5dbd4ab5d190340553967",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sasha_v16\\Sasha_v16_001.png": "b01e3f8a3ce27b2d1be0a0753a31834599bd7407481c896e3ad1c40863e27b63",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sasha_v11\\Sasha_v11_001.png": "9b6a2b5d770299175ac638289faba78f6f4c1fede746704fd6c58b9b44c44c71",
    "C:\\Users\\maruk\\Documents\\Genelate_img\\Sasha_re_codex\\real_human_lora\\work\\frames_raw\\Sash_high_identity-img\\スクリーンショット 2026-09-30 110056.png": "860c29b3669de73f5dd4c370b3fc068de4a68c99d64d343dca4f27cac079addf"
  },
  "existing_step9_settings": {
    "restoration_face_dim_threshold": 190.0,
    "restoration_eye_threshold": 2.0
  },
  "source_legacy_predicate": "FULL_BODY and (face_min_dimension < configured threshold or eye_sharpness < configured threshold)",
  "thresholds_changed": false,
  "new_score": false
}
```

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, pipeline/lineage rules. Data lineage preserved:YES. Full-row preservation:YES within accepted subset; official STEP8 full audit unchanged. Historical evidence preserved:YES. Config SSOT:YES.

Restoration executed:NO. New AI inference:NO. Image change/copy:NO. STEP8 changed:NO. STEP10 executed:NO.

★maru: このSummaryをChappyへ共有してください。上記画像のみ目視確認してください。REVIEW_RECOMMENDEDは修復必須・自動修復の意味ではありません。 STEP10は実行していません。

## Implementation / minimum validation

Changed: scripts/step9_diagnostic.py, bat/09_diagnose_selected.bat;
config/config.yaml,config/config.example.yaml,config/config.schema.json
(output paths only); tests/test_step9_diagnostic.py; README.md,PROJECT.md,
docs/README.md; knowledge/current/selective-restoration.md,configuration.md.
Legacy selective_restoration.py and09_selective_restoration_gpu.bat unchanged.

18 tests PASS (10 diagnostic +8 config): strict existing boundaries, protected shots,
missing/disabled legacy eye handling, no proxy/canonical cutoff, accepted-only scope,
unchanged source fields. Diagnostic executed:YES,40 accepted rows only. Model/inference
production batch:NO. All selected source hashes and authoritative STEP8 evidence
were checked before/after publication. Source pixels and official STEP8 rows unchanged.
Current/Decisions/Failures/Cases/History/Experiments reviewed; no new architecture
Decision/Failure/Case/Experiment needed. No restoration mask readiness implied.

Legacy eye_sharpness available:0/40 in authoritative selected rows. Expected-eye
local_detail is present but is a different metric; not compared against the old
2.0 threshold.10 FULL_BODY rows therefore need Human review due evidence uncertainty,
not a demonstrated blur defect.30 protected CLOSE_UP/UPPER_BODY rows are outside
legacy restoration scope. No blanket photographic-quality claim or STEP10 execution.
