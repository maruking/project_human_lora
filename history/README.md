# Pipeline Validation History (試行錯誤と変遷の全記録)

このディレクトリには、本パイプラインが完成に至るまでに**「実際にどのような課題に直面し、何を試し、何に失敗し、どのように解決へ至ったか」**という**時系列の開発・検証の歴史（History）**を記録しています。

---

## Knowledge と History の違い

- **`knowledge/`（現在と設計判断の体系）**:  
  将来のエンジニアやAIが「今どう実装すべきか」「何が確定仕様か」「何をしてはならないか」を即座に参照するための**抽象化・ルール化された知識**。
- **`history/`（生々しい試行錯誤の軌跡）**:  
  「プロジェクト初期の仮説から最終的な成功に至るまでの泥臭い試行錯誤、現場で発生した想定外のトラブル、ユーザーとの対話で判明した事実、失敗の経緯」を**時系列で振り返るための開発史**。別プロジェクトでゼロから立ち上げる際や、前提が覆った際の根本的な振り返りに使用します。

---

## History 一覧（検証クロニクル）

| ID | タイトル | 発生した課題と経緯の要約 |
| :--- | :--- | :--- |
| **`HIST-001`** | [動画からのフレーム抽出手法の変遷](HIST-001_FRAME_EXTRACTION_AND_DENSITY.md) | 全フレーム抽出による3万枚爆発から、固定FPS方式の不均一性を経て、1動画50等分抽出へ辿り着いた経緯。 |
| **`HIST-002`** | [全体ブラー評価の限界と顔局所判定の発見](HIST-002_GLOBAL_BLUR_LIMITATION.md) | 背景レンガ壁に引っ張られて顔ピンボケフレームを合格にしてしまった事件と、顔切り出しTenengrad導入の歴史。 |
| **`HIST-003`** | [美顔フィルター・プラスチック肌問題と除外の道のり](HIST-003_BEAUTY_FILTER_AND_PLASTIC_SKIN.md) | 「絵画のようになっている」という目視指摘から発覚した、スマホ美顔フィルターによるエッジ過剰＆毛穴消失の解明と749枚除外の実測記録。 |
| **`HIST-004`** | [顔復元AI（CodeFormer）の罠と生肌保持のブレークスルー](HIST-004_CODEFORMER_RESTORATION_DILEMMA.md) | 顔全体に復元をかけるとAIイラスト肌化するディレンマから、目・唇のみ選択的復元＋カメラ生肌100%保持に行き着いた葛藤の記録。 |
| **`HIST-005`** | [アングル固定バグの激闘と構図クォータの確立](HIST-005_FLUX_LORA_ANGLE_LOCK_CHRONICLE.md) | スコア上位だけで選定すると30枚中28枚が正面アップになり横顔や全身が出なくなった問題と、40:40:20クォータ制定の経緯。 |
| **`HIST-006`** | [STEP 0 Config SSOT](HIST-006_CONFIG_SSOT.md) | 実装の既存値を共通設定へ移し、比較検証と未実装仕様を記録。 |
| **`HIST-007`** | [STEP1 Video ID and Manifest](HIST-007_VIDEO_ID_AND_MANIFEST.md) | 元動画保持、安定ID、対応Manifest、動画別Frame出力を導入。 |

- [HIST-008 — Technical metrics and traceability](HIST-008_TECHNICAL_METRICS_AND_TRACEABILITY.md).

- [HIST-009 — STEP1 Revision 2 duration-aware extraction](HIST-009_DURATION_AWARE_EXTRACTION.md).

- [HIST-010 — Current-generation technical metrics](HIST-010_CURRENT_GENERATION_TECHNICAL_METRICS.md).

- [HIST-011 — STEP2 Report Revision](HIST-011_STEP2_REPORT_REVISION.md).

- [HIST-012 — Agent Rules and Data Lineage](HIST-012_AGENT_RULES_AND_DATA_LINEAGE.md).

- [HIST-013 — STEP3 full frame audit](HIST-013_STEP3_FULL_FRAME_AUDIT.md).

- [HIST-014 — STEP3 Calibration Review](HIST-014_STEP3_CALIBRATION_REVIEW.md).

- [HIST-015 — STEP3 REJECT Boundary Review](HIST-015_STEP3_REJECT_BOUNDARY_REVIEW.md).

- [HIST-016 — STEP3 Revision A diagnostics](HIST-016_STEP3_REVISION_A_DIAGNOSTICS.md).

- [HIST-017 — STEP3 4K to BEST Ranking v2.2](HIST-017_STEP3_4K_TO_BEST_RANKING.md): native metric domain shift, canonical measurement, failed Gate/percentile interpretations, ranking evolution and bounded Human Review baseline.
