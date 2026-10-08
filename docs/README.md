# 現行資料 — STEP3 BEST v2.2

STEP5 v2 implementation: [contract, validation and production instructions](STEP5_DEDUP_V2_IMPLEMENTATION.md).
Full STEP5 production is pending ★maru. Its BAT generates the dedup summary and
representative pose/cluster HTML; these outputs are not pre-existing results.

2026-10-05：★maruよりSTEP3にChappy OKが出たとの申告。本作業は資料整理のみ。承認を理由とした再処理・採用状態の自動変更・STEP4実行はしていません。

## 今見る資料

- [Training ContractとSTEP10 preflight表示](TRAINING_CONTRACT_IMPLEMENTATION.md)：config内SSOT、trigger整合性確認。外部adapter YAML同期・Trainingは未実行。

- [STEP10 Caption V2実装・モデル確認](STEP10_CAPTION_V2_IMPLEMENTATION.md)：Qwen3-VL分割重み確認、1枚smokeまで。40枚生成は10_caption_v2_gpu.bat。

- [STEP10固有trigger・Training準備結果](STEP10_SASHA_RH_TRAINING_PREPARATION.md)：40件再Packaging・元画像不変、AI Toolkit Klein Base9B YAML確認済み。Trainingは未実行。

- [STEP4 Pose / Composition v3 実装・最小検証](STEP4_POSE_COMPOSITION_V3_IMPLEMENTATION.md)：既存buffalo_l推定へ変更。bat/04_classify_face_pose.bat実行後のSTEP4_POSE_COMPOSITION_SUMMARY.mdをChappyへ共有。STEP5+互換対応は別作業。
- [歴史資料：STEP4 v2](STEP4_POSE_COMPOSITION_IMPLEMENTATION.md)。
- [STEP5のSTEP4 v3入力対応](STEP5_STEP4_V3_COMPATIBILITY.md)：判定・閾値・代表選択は維持。正式05 BATのpreflightのみ確認、本番未実行。

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

- [STEP6 v2 implementation](STEP6_IDENTITY_V2_IMPLEMENTATION.md) and [reference-only audit](STEP6_REFERENCE_AUDIT.md).

- [STEP7 v2 implementation](STEP7_CANDIDATE_V2_IMPLEMENTATION.md): Chappy review before ★maru production; no STEP8 final decisions yet.

## STEP7 current-version Reject correction

[Eligibility patch report](STEP7_CURRENT_VERSION_REJECT_PATCH.md): authoritative same-version Human Reject exclusion; unchanged BEST/minima/identity and read-only correction audit.

- [STEP7 v2.1 implementation](STEP7_CANDIDATE_V21_IMPLEMENTATION.md): bounded quality guard/core and optional soft coverage, Chappy approval before ★maru production.

- [STEP8 folder-review implementation](STEP8_FOLDER_REVIEW_IMPLEMENTATION.md): Explorer copy selection, guarded ACCEPT, validated CSV handoff and user instructions.

- [STEP7/STEP8 review redesign](STEP7_STEP8_REVIEW_REDESIGN.md): immutable BASE70 + guard-bounded additions, multi-view99_ACCEPT; synthetic/preflight validation only, production07 pending; STEP8 prepare deferred.

- [STEP7 Rare Profile patch](STEP7_RARE_PROFILE_IMPLEMENTATION.md): profile-only BEST top-up from all eligible to3 choices per side; BASE/normal coverage unchanged; no production run.

- [STEP8 collect VIEW copy repair](STEP8_VIEW_COPY_COLLECTION_FIX.md): exact duplicate presentation copies ignored with audit;40 accepts verified read-only, production collect pending ★maru.

- [STEP9 diagnostic summary](STEP9_DIAGNOSTIC_SUMMARY.md):40 accepted images,30 protected/10 review due missing legacy eye metric; restoration/inference/image changes:NO.

- [STEP10 STEP9-SKIP input bridge](STEP10_STEP9_SKIP_IMPLEMENTATION.md): originalSTEP8_ACCEPT input40 verified/preflight-only; caption/16px unchanged; packaging not run.
