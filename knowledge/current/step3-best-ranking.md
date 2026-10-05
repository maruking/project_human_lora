---
topic: step3-best-ranking
last_updated: 2026-10-05
confidence: MEDIUM
status: ACTIVE
related_decisions:
  - DEC-0016
  - DEC-0017
  - DEC-0018
  - DEC-0019
  - DEC-0020
---

# Current Knowledge: STEP3 BEST Ranking

## 現在の責務と適用範囲

STEP3の現行baselineは **best_rank_v2.2**。最小限のfatal exclusionを残し、良い候補を優先する品質順位を作る。すべての不良画像を完全な二値Rejectで取り除く工程とは扱わない。STEP4 pose/composition、STEP5重複、STEP6 identity、STEP7候補選定、STEP8 Human Reviewには、それぞれ独立した責務が残る。ランキング可能、レビュー表示、最終LoRA採用は別の状態である。

[DEC-0020](../decisions/DEC-0020-balanced-critical-quality-best-v22.md)が現行設計、[実装報告](../../docs/STEP3_BEST_RANKING_V22_IMPLEMENTATION.md)が実装時の限定検証、[本番レビュー報告](../../docs/STEP3_BEST_RANKING_V22_ROUND1_3_CHAPPY_REPORT.md)がその後の実行証拠。実装報告の「本番未実施」は当時の事実として保存する。MEDIUMは、設計の受容と限定的な検証を表し、全画像の画質精度を保証しない。

## 測定尺度と品質判断

4K移行ではnative global Laplacian、face Laplacian、実測eye sharpness、skin textureの分布が大きく変わった。解像度、upscale、resampling、source domainを変えた後に旧pixel-space閾値をそのまま移さない。可能な範囲でcanonical化し、metric version・測定尺度・resize/ROI条件・世代を保存し、分布を再確認する。[4K監査](../../docs/STEP3_UPSCALE_RECALIBRATION_AUDIT.md)

canonical face短辺192は旧/新比較で尺度の安定化に役立ったが、domain shiftはゼロになっていない。安定したLaplacianだけでmotion blur、眼の使用可能性、白い霞、意味的な遮蔽まで判定できるわけではない。**測定安定性と知覚的な妥当性を別々に検証する。** [canonical比較](../../docs/STEP3_CANONICAL_SHARPNESS_RESULT.md)、[歴史的閾値移送の限界](../../docs/STEP3_CANONICAL192_THRESHOLD_TRANSFER.md)

閾値中心のGateで経験した失敗を繰り返さない。`one_eye_occluded`というheuristic名は実際の遮蔽の証明ではない。閉眼、外部遮蔽物、poseで見えない眼、測定失敗を分け、missingを観測値0に変換しない。FULL_BODY等のshot labelだけで、実際に測れる顔特徴を対象外にしない。一つの弱いheuristicだけでLoRA適性を決めず、個別被写体の例を汎用ルールにしない。[眼の適用範囲](../decisions/DEC-0015-eye-applicability-review-outputs.md)、[汎用眼評価](../decisions/DEC-0019-general-eye-quality-best-v21.md)

## スコアの使い方

現行設計の概念式は次のとおり。実際の数値設定はConfig SSOT、詳細式は現行実装とDEC-0020を参照する。

```text
base_quality = absolute_quality_total + relative_quality_bonus
critical_face_quality = geometric_mean(eye, facial_detail, exposure, reliability)
BEST_SCORE = base_quality * critical_face_quality - remaining_geometry_penalty
```

criticalの4軸は等重み。強いsharpness/contrastの加点だけで重要な顔品質軸の弱さを埋め合わせにくくする、現在受容した構造である。普遍的な数学的最適解ではなく、重大な欠点が必ず下位になる保証もない。factor低下は新しいbinary Hard Rejectを作らない。[因子・二重作用の監査](../../docs/STEP3_BEST_RANKING_V22_IMPLEMENTATION.md)

`absolute_quality`は共通の比較尺度という名称であり、独立に校正された物理品質単位ではない。多くのpositive尺度は世代の共通P5/P95参照を使う。small relative bonusはinput kind内のpositive比較に用いる。[v2の尺度設計](../../docs/STEP3_BEST_RANKING_V2_IMPLEMENTATION.md)

**percentile/rankはpositive順位、分布分析、比較bonusに使えても、そのまま欠点の強さにはできない。** 下位percentileだけでblur、遮蔽、clipping、shadow、blinkを断定しない。defect concernには実際の画像由来の測定証拠と適用条件が必要である。v2.2のP95 detail因子も比較品質であり、物理的blurの認定ではない。[DEC-0017](../decisions/DEC-0017-best-ranking-evidence-penalties.md)

## 眼・顔detail・露出の境界

- **眼**：左右を独立に評価し、期待される眼の弱い側を平均で隠さない。openness、obstruction concern、measurement reliabilityは別概念。poseでfar-side profile eyeが見えない場合は期待対象から外す。presenceだけで遮蔽を決めず、同じ眼のdetail不足との整合を見る。missingは0でも自動遮蔽でもない。ROI/landmark不整合は測定失敗として明示する。真の眼ROIやprofile期待眼の正しさは十分に検証されていない。[v2.1](../../docs/STEP3_BEST_RANKING_V21_IMPLEMENTATION.md)、[v2.2眼監査](../../docs/STEP3_BEST_RANKING_V22_IMPLEMENTATION.md)
- **blur/detail**：画像全体のsharpnessは背景等の影響を受け、顔品質を代用できない。v2.2は顔全体のcanonical Laplacian/Tenengrad品質と、期待眼・mouthのlocal品質を組み合わせる。global face detailとlocal medianの積により、強い局所edgeだけで弱い顔全体のdetailを回復させない。P95参照は比較品質正規化で、校正済みmotion-blur閾値ではない。[実装のBlur aggregation](../../docs/STEP3_BEST_RANKING_V22_IMPLEMENTATION.md)、[背景sharpnessの失敗](../failures/FAIL-0002-global-blur-only-selection.md)
- **露出**：underexposure、clipping、white hazeを分ける。tiny clippingは自動的な不良ではなく、白い霞もclippingと同義ではない。既存のbrightness/contrast/dynamic-range/clipによる情報損失モデルでは説明できない視覚的hazeが残る。一例を落とすための任意閾値を追加しない。[Exposure/hazeの未解決部分](../../docs/STEP3_BEST_RANKING_V22_IMPLEMENTATION.md)

## 入力・Human Review・版の扱い

正式video framesと宣言済みsupplemental stillsを共通candidate universeと監査schemaに含める。input_kind、source identity、provenance、世代と分布を保持する。互換なcanonical測定は共通品質尺度で比較し、独立したkind内percentileだけで実際の品質差を消さない。全auditにはfatalを含む全行を残す。レビューcopiesは入力でも正式監査の代替でもない。[v2入力/比較設計](../../docs/STEP3_BEST_RANKING_V2_IMPLEMENTATION.md)、[Data Lineage Rules](../../.agents/rules/data_lineage_rules.md)

**Human Reviewをruntime ranking featureにしない。** filename/video/source blacklistや以前のHuman RejectをBEST_SCOREに使わない。人間判断は回帰証拠、反例発見、一般的な採点ロジックの検証に使う。別の人物・動画でも同じ測定上の弱点が評価されるべきであり、既知の画像名だから低順位にしてはいけない。[DEC-0019](../decisions/DEC-0019-general-eye-quality-best-v21.md)

式が大きく変われば候補順も変わるため、review historyはranking version単位で分離する。新しい版はRound1から再開始でき、旧判断は不変の歴史として残す。旧版の表示済み/Human Rejectは新しい版のshown除外に使わない。同じ版では既に表示したframeを後Roundに再表示しない。[DEC-0018](../decisions/DEC-0018-version-scoped-best-review.md)

レビューには動画ごとのsoft capとsupplemental stillの最低希望枚数がある。これらは表示の多様性確保で、training quotaやスコアの補正ではない。動画capはRoundごとに適用し、枠不足なら必要最小限の緩和を記録する。このためRound3はglobal top45ではなく、top135より下のframeも表示され得る。低global rankの表示だけで採点失敗と判断せず、まずsampling理由を確認する。[レビュー設計](../../docs/STEP3_BEST_RANKING_V2_IMPLEMENTATION.md)

## 2026-10-05の検証snapshotと現在の判断

`gpt6.1`のSTEP3保存baseline（commit `db488cb16779a142d62d0614ba82284f76c5aa1b`）の[本番報告](../../docs/STEP3_BEST_RANKING_V22_ROUND1_3_CHAPPY_REPORT.md)による。この世代の値であり汎用定数ではない。

| 項目 | 観測値 |
| --- | ---: |
| 全candidate universe | 1,951（正式1,893＋静止画58） |
| ranking eligible / fatal | 1,880 / 71 |
| Human Review表示 | 3 rounds × 45 = 135、同版frame重複なし |
| Human Reject | 4（Round1/2は0、Round3は4） |
| Reject画像のglobal rank | 85、129、146、150 |
| 残る履歴状態 | 131 PENDING |

動画capはこのsnapshotでは4/動画/Round、緩和なし。Round3の未表示stillsは8枚しかなく、最低希望10枚には2枚不足した。4/135は表示された集合のReject率で、全datasetのprecisionではない。131 PENDINGをACCEPT/A/最終LoRA素材へ自動昇格させない。根拠は[summary](../../output/reports/step3_best_ranking_summary.json)、[version別履歴](../../output/reports/step3_best_review_history_by_version.json)、[feedback](../../output/reports/step3_best_review_reject_feedback_best_rank_v2.2.csv)。

★maru/Chappyは現時点でv2.2を実用的なSTEP3 baselineとしてfreezeし、STEP4へ進めると判断した（本Knowledge作成依頼と、★maruのSTEP3承認報告に基づくproject judgement）。これは報告当時の「次段階判断待ち」に対する後続判断であり、機械精度認定ではない。実装時の[verification](../../docs/STEP3_BEST_RANKING_V22_VERIFICATION.json)が「本番未実施」を記録することとも矛盾しない。実装時記録は変更しない。

## 未解決事項と古い資料の読み方

眼ROI/真の眼測定（v05型反例）、視覚的white haze、profile眼可視性、比較detail尺度と物理blurの一致は未解決。final LoRA適性には後段と最終Human Reviewが必要である。個別反例へのblacklistや根拠のない閾値で限界を隠さない。

[face-quality.md](face-quality.md)の旧Gate節、[旧Human Calibration/Execution記録](KNOWLEDGE_STEP3_HUMAN_CALIBRATION_AND_EXECUTION.md)の2,001枚・eligible62等は以前の世代/設計の記録。実行ownershipの原則は有効だが、その旧数値・Gateや未実施記述を現行v2.2状態に使わない。旧DEC/実装資料の説明は記録時点に属し、現行状態は本書と後続本番証拠を参照する。経緯は[HIST-017](../../history/HIST-017_STEP3_4K_TO_BEST_RANKING.md)に分離する。
