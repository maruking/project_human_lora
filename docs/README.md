# 現行資料 — STEP3 BEST v2.2

STEP5 v2 implementation: [contract, validation and production instructions](STEP5_DEDUP_V2_IMPLEMENTATION.md).
Full STEP5 production is pending ★maru. Its BAT generates the dedup summary and
representative pose/cluster HTML; these outputs are not pre-existing results.

2026-10-05：★maruよりSTEP3にChappy OKが出たとの申告。本作業は資料整理のみ。承認を理由とした再処理・採用状態の自動変更・STEP4実行はしていません。

## 今見る資料

- [STEP4 Pose / Composition v2 実装・最小検証](STEP4_POSE_COMPOSITION_IMPLEMENTATION.md)：本番はbat/04_classify_face_pose.bat。実行後のSTEP4_POSE_COMPOSITION_SUMMARY.mdをChappyへ共有。

- [v2.2 Round1〜3 Chappy報告](STEP3_BEST_RANKING_V22_ROUND1_3_CHAPPY_REPORT.md)：135件レビュー、Human Reject4件。記録上PENDING131件。
- [Reject画像一覧](STEP3_BEST_RANKING_V22_ROUND1_3_REJECT_IMAGES.html)
- [v2.2実装・計算式](STEP3_BEST_RANKING_V22_IMPLEMENTATION.md)
- [v2.2検証記録](STEP3_BEST_RANKING_V22_VERIFICATION.json)
- [全体順位1〜90](../output/reports/step3_best_rank_001_090/index.html)
- [全体順位145〜200](../output/reports/step3_best_rank_145_200/index.html)
- [現行report案内](../output/reports/REPORTS_INDEX.md)

## STEP1/2と参照資料

- [STEP1現世代の抽出結果](STEP1_UPSCALED_EXTRACTION_RESULT.md)
- [STEP1 BAT統合](STEP1_UPSCALE_INTEGRATION.md)
- [STEP2追加静止画対応](STEP2_SUPPLEMENTAL_INPUT_FIX.md)
- [Agent Rules整理](AGENT_RULES_REVISION_RESULT.md)
- [Architecture](PIPELINE_ARCHITECTURE.md)

残した旧Gate・旧BEST実装資料はKnowledge/Decisionから参照される根拠資料です。現行BESTとは区別して参照してください。

## backup

- [今回の移動一覧と検証](../backup/step3_approved_20261005_a8f7c74c/README.md)
- [移動前後の全記録](../backup/step3_approved_20261005_a8f7c74c/MANIFEST.json)
- [以前のdocsバックアップ](bkup/)

元ファイルは削除せず移動。現行ランキング1,951行、STEP2/旧Gateの正式report、版別Human Review履歴、v2.2レビュー、原画像・現行動画・manifestは保持しています。
