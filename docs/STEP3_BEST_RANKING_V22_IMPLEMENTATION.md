# STEP3 BEST Ranking v2.2 — implementation result

2026-10-05。local working treeを正として実装。★maruによる本番実行は未実施。

## Changed / Ranking version

Ranking version：**best_rank_v2.2**。

コード／BAT／config：

- `scripts/common/best_ranking.py`：現行v2.2への入口。
- `scripts/common/best_ranking_v21.py`：変更前v2.1コードをバイト同一で保存。旧v1/v2と旧eye helperは変更なし。
- `scripts/common/best_ranking_v22.py`：balanced score・face-size／contrast／illuminationの改善。
- `scripts/common/best_quality_v22.py`：目・信頼性・global/local detailの汎用因子。
- `scripts/common/best_review.py`：active版の候補／Reject二重配置解消。
- `scripts/step3_best_ranking.py`：v2.1成果物の安全なarchive互換、v2.2の式・因子summary。
- `bat/03_face_quality_gate.bat`、`bat/03_best_review_round.bat`：版表示変更。既存の`03_step3_best_ranking.bat`呼出経路を継続。
- `config/config.yaml`、`config/config.example.yaml`、`config/config.schema.json`：ranking_versionのみ更新。既存の閾値・数値設定は変更なし。

検証／資料：新規v2.2テスト・9例fixture、旧版／現行契約テストの参照分離、比較JSON、保護ハッシュ、本報告、DEC-0020、Decision索引、Current Knowledgeのface-quality／configuration、README／PROJECTの現行入口。

公式STEP3 Gate、STEP2、STEP4+、元画像、Human Review判断、A/B/C、歴史的レポートは変更なし。

## Root causes addressed / Balanced critical quality

旧式：absolute＋relative−soft penalties。目の問題が他の大きな加点で補われ、global blurがlocalの強いエッジで過小評価される構造を修正。

```text
base_quality = absolute_quality_total + relative_quality_bonus
critical_face_quality = geometric_mean(eye, blur, exposure, reliability)
BEST_SCORE = base_quality * critical_face_quality - remaining_geometry_penalty
```

4軸は0〜1、等重み。新しい強度係数なし。critical factorが0でもranking_eligibleは変えず、binary Hard Rejectを追加しない。

代案`100*sqrt(base/100*critical)-geometry`も9例で比較したが、低いcritical qualityを再び持ち上げるため単純積を採用。v19_024では採用45.149／代案67.193。名前・Human Reject・目標順位に合わせた係数調整はしない。[数値比較JSON](STEP3_BEST_RANKING_V22_REGRESSION.json)。新しいglobal_rankは計算していない。

## Eye aggregation / Eye measurement reliability

左右眼を独立に評価。既存yaw／実測ROI投影によるexpected eyeを維持し、profile far eyeはNOT_EXPECTED_BY_POSE。弱いexpected eyeの開きを用い、平均で隠さない。OPEN正常、HALF/BORDERLINE低下、CLOSED/BLINKはさらに低下する。

presence単独では遮蔽判定しない。同じexpected eyeのpresence＋detail不足の合意を遮蔽疑いとして扱う。失敗はocclusionにせず、`ROI_INVALID`／`LANDMARK_MISSING`／`DETAIL_UNAVAILABLE`／`MEASUREMENT_UNAVAILABLE`／`INCONSISTENT`として信頼性へ反映する。

出力：左右`*_eye_measurement_status`／`*_eye_landmark_availability`／opening_quality／obstruction_concern、eye_measurement_reliability、eye_quality_factor。

profileでは既存open境界に対する連続比を使い、僅かな比率低下に固定の半開状態減点を付ける段差を避ける。実際の眼形状／閉眼の検出精度は未検証。v08_004の保存状態BORDERLINEを、人間説明に合わせてCLOSEDへ書き換えていない。

### v05_003 audit — STOPした部分

保存済み：face bbox687,1887,740,740、face短辺740、mesh MEASURED、yaw18.522、左右openness0.347673／0.300961、asymmetry1.155209、presence0.018620／0.084481、detail1.603560／1.123438、ROI180×144／217×174、両ROI MEASURED、警告なし。

測定コードはeye corners33/133と263/362からspanとcenterを求め、span×1.5／1.2のpatchを取り、同じkernelでdetailを測定している。空／3px未満patchはUNAVAILABLE、値は欠損のまま残す。

**不足証拠：実際の左右ROI座標・保存ランドマーク座標・眼別ランドマーク可用性／信頼度・眼がROI内に正しく対応しているかの記録。** 保存CSVのwhole-mesh statusは眼別検証の粗いproxyにすぎない。これだけで「眼を測れていない」と断定できず、今回新しい推論を行って補完していない。v2.2診断VALIDは保存情報の整合性であり、真の眼ROIの正しさを認定する意味ではない。この例は66.085→66.555で、強制的に順位を落としていない。

## Blur aggregation

global_detail_quality：canonical192 LaplacianとTenengradを、既存positive P95参照に対する飽和比で正規化し、geometric mean。

local_detail_quality：expected眼とmouthの同じ飽和比のmedian。1領域だけ弱い場合に全体blurを過大にしない。

blur_quality_factor＝global×local。localが1でも弱いglobalは回復しない。旧pair-product不足度が小さくなる問題を解消。

**P95参照は既存の比較品質尺度であり、物理的blurの新しい絶対閾値ではない。** 新しいTenengrad／mouthのabsolute defect cutoffは未承認のため追加していない。`blur_scaling_state=COMPARATIVE_P95_QUALITY_NOT_CALIBRATED_PHYSICAL_BLUR_THRESHOLD`。値・世代分布への感度と実際のblurの一致にはHuman Calibrationが必要。blur_evidence_strengthはこの比較品質低下の診断であり、blurの断定ではない。

## Exposure/haze

既存brightness／clip／contrast／dynamic-rangeの情報損失モデル・数値境界を維持。shadow ratioはcontext＋測定coverageとして保存し、暗さ単独で問題にしない。tiny clippingにslackを維持。露出欠点はexposure factorへ集約。

視覚的なv19 hazeはbrightness約159、contrast約70、dynamic range102、clip0ではモデル上成立しない。**視覚的hazeへの新しい採点はSTOP／未解決**。根拠のない閾値を追加しない。exposure_evidence_statusに未解決状態を明示。blur改善は独立に実装。

## Double counting / contribution audit

| family | positive effect | critical effect | explicit penalty |
| --- | --- | --- | --- |
| Eye opening／obstruction | usabilityによる旧eye加点縮小を解除 | eye factorのみ | 0 |
| Eye／metric failure | missing値の加点欠損は既存coverageで可視 | reliability factor | 0 |
| Exposure loss | 情報が測定済みなら露出基本加点は正常値を使う | exposure factorのみ | 0 |
| Facial detail | 既存positive sharpnessは維持 | detail因子で無関係な加点の補償を抑制 | 0 |
| Contrast | useful informationの飽和加点 | exposureで同じ情報損失が作用する場合あり | 0 |
| Geometric/detection visibility | raw geometryの加点を維持 | criticalには追加しない | 既存geometry penalty |

Detailのpositiveとcriticalは同じ測定を使う意図的な2経路。前者は鮮明さの良さ、後者は他軸の過大補償を制限する。欠損値も加点coverageと信頼性の両方へ作用するため、その影響は隠さない。第三の直接blur／eye／exposure penaltyは削除。旧deductionは`v21_evidence_deduction_*`へ監査保存する。

`*_critical_quality_effect`は他軸を正常とした単独因子の影響を示す非加算値。総損失はcritical_quality_score_effectで確認し、軸ごとの差を単純加算しない。

欠損factorは空欄。集約時のneutral placeholderは観測値1を意味せず、別の測定coverage信頼性を下げる。全expected眼が利用不能の場合は眼factorを捏造せず信頼性を0にする。observed0とmissingの状態／保存値は区別する。

## Face-size / Contrast / Good-image protection

- Face-sizeは既存`min_face_dim_upper_body`を比較品質の飽和参照として再利用。超えても加点が増えず、追加relative size bonusも付けない。新しいfatal条件なし。
- Contrastは既存normal span15でlocal contrast／dynamic rangeの情報量を飽和評価。high contrastほど無制限に高評価しない。既存小さなrelative contrast bonus（最大1.5点）は維持。
- `asymmetric_eye_brightness`の旧visibility25点低下をranking上のみ差し戻す。照明差を遮蔽に変換せず、他のgeometry/detection signalsは保持。raw face_visibility_scoreは変更しない。
- 汎用profile比率・飽和face-size／contrast・照明補正で110146を保護。画像名条件なし。良質参照4枚は高スコアを維持。ただし他の良質画像全体の保護は未検証。

## Known counterexamples v2.1 → v2.2

| Stored sample | v2.1 | v2.2 estimate | critical | eye | blur | exposure | reliability |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v08_011 | 63.886 | 56.208 | .645 | .232 | .746 | 1 | 1 |
| v08_004 | 62.801 | 60.255 | .729 | .396 | .713 | 1 | 1 |
| v05_003 | 66.085 | 66.555 | .850 | 1 | .521 | 1 | 1 |
| v19_024 | 58.484 | 45.149 | .592 | .899 | .137 | 1 | 1 |
| 110146 | 45.620 | 70.458 | .834 | .905 | .534 | 1 | 1 |
| reference jpg 652794808… | 88.409 | 94.205 | 1 | 1 | 1 | 1 | 1 |
| 111733 | 90.758 | 91.819 | .996 | 1 | .983 | 1 | 1 |
| 110609 | 89.705 | 92.322 | 1 | 1 | 1 | 1 | 1 |
| 105148 | 89.449 | 94.058 | 1 | 1 | 1 | 1 | 1 |

9例だけscore_rowを計算。positive references／bonus poolsは互換な保存済み全件測定値を読み取りでfitし、全1,951画像のscore_row／rank_rowsは実行していない。旧rankを入力特徴量にしない。JSONのold_global_rankは旧版監査値。新順位・レビュー候補からの脱落は保証しない。

## Review materialization duplication fix / versioning

future active-v2.2 feedbackでパス／image hashを確認し、Rejectを優先。両コピーがある場合は判断を履歴に保存してから余分なcandidate copyを除去。保存Rejectがcandidateへ戻されていれば同一review subtree内でatomic rename。再実行可能。

元画像・旧版判断・旧版copiesは変更しない。今回存在するv2.1のv19_024二重copyも実行して解消していない。両コピーが欠ける場合はMISSINGを明示し、元画像から勝手に再配置しない。複数ファイル全体のtransactionは保証しない。

v2.2はRound1から開始。旧v1/v2/v2.1履歴は読み取り回帰証拠で、BEST_SCOREにもcandidate exclusionにも使用しない。

## Minimum validation / unresolved items / scope

BEST unit/synthetic suite：111 tests PASS。Config：8 tests PASS。BAT --help PASS。19要求のgeneral properties、same metrics／different identity、review-state無関係、profile far eye、global弱点をlocal edgeが回復しないこと、no triple deduction、旧v2.1 archive／history不変、Review duplicate reconciliationを検証。

一時フォルダの小さなmock/synthetic ranking・review extractionのみ。実データ本番copiesなし。保護ハッシュで既存report／history／feedback不変、v2.1 scoringのbyte-preservation、numeric config不変を確認する。

未解決：v05眼ROI真値の監査、視覚的haze、profile eyeの真の可視性、P95比較detailと物理blurの校正、顔サイズ参照の全shot有効性、全体rankingのHuman精度。十分な証拠を得るまで、特定画像を下げるための係数・blacklistを追加しない。

Human Review used as runtime feature：NO。
Filename/source/video blacklist used：NO。
Full production executed：NO。

Rules checked：AGENTS.md、.agents/AGENTS.md、PROJECT.md、両Project Rules、関連Knowledge／Decision／Failures／Cases／History。Knowledge Maintenance適用。Data lineage preserved：YES。Full-row preservation：YES（現在1,951行は変更なし、9行derived comparison／synthetic pathsを検証）。Historical evidence preserved：YES。Config SSOT preserved：YES。Rule conflictなし。STEP4 readiness／全体品質PASSとはしていない。

## ★maru

`bat/03_step3_best_ranking.bat`でbest_rank_v2.2の本番ランキングを実行してください。summaryを確認後、`bat/03_best_review_round.bat 1`でbest_rank_v2.2 Round1を生成しHuman Reviewを再開始してください。旧v1/v2/v2.1は履歴として保持し、現行score／除外には使用しません。
