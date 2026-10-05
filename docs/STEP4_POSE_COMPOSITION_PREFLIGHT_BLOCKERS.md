# STEP4 Pose / Composition — 実装前の不一致確認

2026-10-05。現在のlocal working treeとSTEP3 best_rank_v2.2を読み取り調査。添付依頼の18節「shot_type has multiple conflicting definitions」に該当するため、定義を独断で選ばず実装を停止した。

## 観測した現行入力

- [BESTランキング](../output/reports/step3_best_ranking.csv)：1,951行。formal_video 1,893、supplemental_still 58。これらは観測値でありコードへ固定しない。
- ranking_eligible=true 1,880行、false 71行。
- eligible内でpose_status=MEASUREDは1,698行、UNAVAILABLEは182行。欠測を0度やFRONTALと扱ってはいけない。
- frame_id、filename、input_kind、source_id、video_id、dataset_generation_id、image_sha256、yaw/pitch/roll、face_area_ratio、face_short_edge_pxは存在する。
- **shot_type列はBESTランキングに存在しない。**
- [旧正式Face Gate report](../output/reports/step3_dataset_report.csv)は1,893行。shot_typeはCLOSE_UP 315、UPPER_BODY 759、FULL_BODY 750、空欄69。追加静止画58枚のshot_typeをこのreportから取得できない。旧Gateの値をBESTへ安全にjoinできるかの世代・bbox照合は未実施。
- reports直下に既存step4出力は見つからなかった。過去のSTEP4が一度も実行されていないことまでは断定しない。

## Poseは再利用可能

[旧STEP4](../scripts/classify_face_pose.py)のestimate_head_poseと[STEP3共通helper](../scripts/common/best_pose.py)の同名関数は、位置情報を除いたASTが一致した。solvePnPのモデル、ランドマーク、Euler角、pitch補正は同一。別式で再推論する必要はない。

[現行SSOT](../config/config.yaml)のstep4_pose：front_yaw_max=15、three_quarter_yaw_max=42、profile_yaw_min=42、pitch_looking_min=-20、pitch_looking_max=20。角度境界を新しく作る必要はない。

既存コードのラベル規約は正yaw→RIGHT、負yaw→LEFT。正pitch>20→LOOKING_DOWN、負pitch<-20→LOOKING_UP。これは保存値とコードのラベル規約であり、鏡像入力を含む画像上の左右／人物の解剖学的左右を目視で検証した結果ではない。新実装ではraw signed angleと規約を明記する必要がある。

旧STEP4はpitch/rollの絶対値35超をEXTREME_POSEにまとめ、pitch binをyaw binより優先する。今回依頼はyaw・vertical_poseを独立属性として要求するため、角度は再利用しつつラベルの出力構造を変える必要がある。これはRejectやquotaの追加を意味しない。

## STOPとなるshot_type定義の不一致

| 根拠 | 分類に使う量 | 境界 |
| --- | --- | --- |
| [現行Face Gateのclassify_shot_type](../scripts/face_quality_gate.py)、step3_face_gate SSOT | bbox面積 / 画像面積 | 0.12以上CLOSE_UP、0.04以上0.12未満UPPER_BODY、それ未満FULL_BODY |
| [Current Knowledge face-pose-quota](../knowledge/current/face-pose-quota.md)、[ACCEPTED DEC-0005](../knowledge/decisions/DEC-0005-pose-composition-quotas.md) | 顔高さ / 画像高さ | 25%超Close-up、10〜25%Medium、10%未満Full-body/Wide |

高さ比と面積比は別の量であり、その閾値を置き換えたり換算して同じ定義と見なすことはできない。Current Knowledgeには過去のquota説明もあるが、shot分類の高さ比説明をsupersededと明示する別の決定は今回の参照資料では確認できなかった。

旧STEP4は独自のshot測定をしておらず、入力rowのshot_typeを使用し、欠ければUPPER_BODYを代入する。この欠測時の代入は今回の「Missing != zero / 不明を捏造しない」方針に使えない。BESTには列自体がないため、従来STEP4をそのままBATから実行しても今回要件は満たさない。

## Chappyに明示してもらう選択

推奨案：現行SSOTの**面積比0.12/0.04方式を、今回はface-scale由来のshot記述として正式に再利用**する。BESTの保存bbox/面積比から分類し、旧Knowledge/DECの高さ比を今回STEP4の基準には使わないと明示する。FULL_BODY等は顔の相対サイズによる記述であり、脚まで写っていることの保証ではない。

別案：高さ比方式を正式なshot分類に採用する場合は、現行Face Gateと異なる定義であること、正式SSOT境界・端点の扱い・旧shotとの関係を先に指定する。今回は新しい分類を独断で導入しない。

どちらの場合も品質順位・Reject・quota・Human Reviewをshot決定に利用しない。顔中心の正規化とbbox端接触は保存geometryから算出可能。位置binの既存SSOTがない場合は座標のみ保存し、左右上下の区分境界を創作しない。

## 今回の変更と検証

Changed：この調査報告のみ。STEP4の新コード・config/schema・BAT・Knowledge/Decisionは未変更。既存STEP4コードも保存されている。

STEP4 version：未実装（予定step4_pose_composition_v2）。Input universe：現行BESTの全行。Rows preserved：YES、読み取りのみ1,951行。Pose source：STEP3保存角度、計算関数一致を静的確認。Shot type source：未決定。STEP3 dependency：保存ランキング/測定値のみを使用する予定。Human Review dependency：NONE。Reject/quota introduced：NO。Summary outputs：未作成。

Tests：入力の列・件数・種類・eligibility・pose欠測状態を集計、pose関数AST一致を確認。画像推論・本番STEP4・unit test再実行はしていない。

Rules checked：AGENTS.md、.agents/AGENTS.md、PROJECT.md、pipeline/data lineage rules、関連Current Knowledge/DEC-0005/DEC-0020/Failures/Cases/History、現行STEP3結果。Data lineage preserved：YES。Full-row preservation：YES。Historical evidence preserved：YES。Config SSOT preserved：YES。その他文書の意味や過去Decisionは書き換えていない。

Unresolved items：今回STEP4で採用するshot_type定義の明示。Full production executed：NO。STEP5+未実行。

STOP：新STEP4がまだ実装されていないため、この状態で本番BATの実行は案内しない。
