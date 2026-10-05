# Chappy報告：best_rank_v2.2 Round 1〜3 Human Review

作成日：2026-10-05。現在のlocal working treeのランキング・summary・version別履歴・feedback・画像フォルダを読み取り確認。★maruが実行した結果の報告であり、本報告作成時にCodexは再ランキング・推論・feedback BATを実行していない。

## 結果とユーザー確認

Round 1〜3の計135枚をレビューし、**Human Rejectは4枚**。ユーザーの初報は「Round3 reject3枚」だったが、記録／フォルダでは4枚だったため確認し、★maruから「4枚すべてRejectで正しい」と回答を受けた。判断を書き換えず、確認済み4枚として報告する。

| Round | 表示枚数 | 動画 | 追加静止画 | Human Reject | Reject未指定／履歴PENDING |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 45 | 8 | 37 | 0 | 45 |
| 2 | 45 | 33 | 12 | 0 | 45 |
| 3 | 45 | 37 | 8 | 4 | 41 |
| 合計 | 135 | 78 | 57 | 4 | 131 |

Reject率は4/135＝2.96%。選抜レビュー集合の値であり、全1,951枚の品質精度やReject率ではない。Round1／2は★maruがRejectなしと明示。残り131枚は機械履歴PENDINGであり、正式ACCEPT・A群・最終LoRA採用の自動確定ではない。

## 正式データ・実行状態

- best_rank_v2.2、全1,951行＝正式動画1,893＋追加静止画58。
- ranking_eligible1,880、fatal71（no_face70／multiple_faces1）。
- 3Roundともpublication_status=COMPLETE、各45枚、表示frame_id重複なし。
- 動画上限4枚／Roundの緩和なし。上限は3Round通算ではない。
- Round3の未表示追加静止画は8枚だけなので、最低希望10枚には2枚不足。8枚＋動画37枚で45枚を確保。
- ランキング可能な静止画57枚は全て表示済み。残り1枚はfatal。
- next_review_round=null。Round4はこの運用に存在しない。
- Execution status：★maruによるv2.2本番出力とRound1〜3発行・Reject反映を確認。
- Algorithm validity：一般化した画質順位／目検出の正しさ／LoRA適性は未確定。
- Human calibration：選抜135枚のHuman Reject確認。個別の今回Reject理由はまだ未記入。

## Human Reject画像と因子

[画像付き一覧を開く](STEP3_BEST_RANKING_V22_ROUND1_3_REJECT_IMAGES.html)。画像クリックで原画像を開く。

| frame_id | 全体順位 | BEST | critical | eye | blur/detail | exposure | reliability | 今回の人間理由 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Sasha_v05/Sasha_v05_003.png | 85 | 66.555 | 0.850 | 1.000 | 0.521 | 1.000 | 1.000 | 未記入 |
| Sasha_v08/Sasha_v08_004.png | 129 | 60.255 | 0.729 | 0.396 | 0.713 | 1.000 | 1.000 | 未記入 |
| Sasha_v08/Sasha_v08_018.png | 146 | 57.351 | 0.716 | 0.427 | 0.616 | 1.000 | 1.000 | 未記入 |
| Sasha_v08/Sasha_v08_008.png | 150 | 56.571 | 0.732 | 0.455 | 0.630 | 1.000 | 1.000 | 未記入 |

4枚ともRound3の正式Reject。v05_003はeye=1、reliability=1であり、保存情報の整合性診断は問題を表現していない。真の眼ROIが正しく測れていることの証明ではない。v08の3枚には目品質の低下があるが、候補に残りHuman Rejectされた。profileのv08_004ではexpected eyeはleftのみ、他2枚はboth eyes。

機械の因子値を今回の人間の拒否理由に置き換えない。以前の観測ではv05_003の眼測定に疑義、v08_004には閉眼／髪の遮蔽疑義があったが、今回の理由として改めて確認されたものではない。v08_018の具体理由も未記入。

## 旧v2.1 Human Rejectの現行結果

以下は★maruが実行した現行ランキングの実順位。実装時の少数例推定から順位を創作したものではない。

| 旧Reject画像 | v2.1点 | v2.2点 | 全体順位 v2.1 → v2.2 | v2.2レビュー状態 |
| --- | ---: | ---: | --- | --- |
| Sasha_v08/Sasha_v08_011.png | 63.886 | 56.208 | 99 → 156 | NOT_SHOWN |
| Sasha_v08/Sasha_v08_004.png | 62.801 | 60.255 | 104 → 129 | REVIEW_REJECT |
| Sasha_v05/Sasha_v05_003.png | 66.085 | 66.555 | 92 → 85 | REVIEW_REJECT |
| Sasha_v19/Sasha_v19_024.png | 58.484 | 45.149 | 134 → 321 | NOT_SHOWN |

観測：v08_011・v19_024は低順位へ移り、今回の135枚には出ていない。v08_004は下がったが再登場してReject。v05_003は僅かにスコアが上がり、再登場してReject。v08_008はv2でRejectだった画像で、v2.2でも再登場しReject。v08_018は旧v1/v2/v2.1の表示記録にない新しい反例。

推論：顔ディテール／critical aggregationの変更は一部の旧反例のレビュー再登場を抑えた。一方、目の測定真値とprofile期待眼、criticalとbaseの補償構造には不一致が残る。今回のReject件数はv2.1と同じ4件なので「Rejectが減った」「全体品質が改善した」とは結論しない。表示集合や静止画のRound分布も変わっている。

旧版のHuman Rejectはv2.2のスコア・候補除外に使われないため、版をまたぐ再登場は設計どおり。同じ版内の同一frame再表示は確認されていない。動画単位の一律Reject・画像名blacklistは導入していない。

## Chappyへ依頼する判断

1. 今回4枚の具体的なReject理由を★maruが提示し、目の開き／遮蔽／ROI不整合／blurなどを区別する。保存値だけで人間理由を補完しない。
2. v05_003は眼ROI座標と眼別ランドマーク証拠が不足。測定不具合かどうかを解明するための小規模監査要件を定義する。重み増加で隠さない。
3. v08_004のprofile期待眼と連続開き比率、v08_018／008の開き診断とcritical構造を比較する。source名／Human Rejectをruntime featureにしない。
4. v19_024が今回未表示になったことは視覚的hazeの検出成功を意味しない。hazeは依然未解決。
5. 131件を正式ACCEPTやAに自動昇格させず、必要な採用／保留の記録と次段階の検証範囲を決める。最終35〜45枚やSTEP4+へ自動移行しない。

## 照合と今回の変更範囲

- 全件ランキングの件数・一意frame_id数とも1,951。STEP2正式＋静止画の件数とidentity集合が一致。
- 履歴135件のframe_id重複なし。summary／履歴／feedbackのReject4件が一致。
- 現行コピー：Round1 candidates45／Reject0、Round2 45／0、Round3 41／4。画像欠落・候補とRejectの二重配置なし。
- ランキングSHA256はsummaryと一致：`6400f2a09d30b0a99488872c435c0fae039644cbc27619d90b09a31e0d7126ca`。
- 元画像リンク4件を存在確認。全画像の再目視・推論・全コピーの内容ハッシュ監査はしていない。
- v1／v2／v2.1の歴史的判断は保持。既存の公式STEP3 Gateレポートと現行BESTを同一判定として扱わない。

根拠：[現行ranking](../output/reports/step3_best_ranking.csv)、[summary](../output/reports/step3_best_ranking_summary.json)、[版別履歴](../output/reports/step3_best_review_history_by_version.json)、[v2.2 feedback](../output/reports/step3_best_review_reject_feedback_best_rank_v2.2.csv)、[実装と限界](STEP3_BEST_RANKING_V22_IMPLEMENTATION.md)、[DEC-0020](../knowledge/decisions/DEC-0020-balanced-critical-quality-best-v22.md)。

Changed：本報告Markdownと画像一覧HTMLのみ。コード／BAT／config／閾値／ranking／Human Review履歴／A/B/C／元画像／STEP4+は変更していない。

Rules checked：AGENTS.md、.agents/AGENTS.md、PROJECT.md、両Project Rules、関連Current Knowledge／DEC-0020／Failures／Cases／History／実装結果。Data lineage preserved：YES。Full-row preservation：YES（既存1,951行は読み取りのみ、報告集合135件）。Historical evidence preserved：YES。Config SSOT preserved：YES。Rule conflicts：なし。Documentation checked; no update required（他の既存資料は当時の記録として保持し、この報告に実行後の事実を記録）。

Full production executed by Codex for this report：NO。
