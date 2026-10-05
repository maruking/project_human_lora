# STEP4 Pose / Composition v2 — 実装・最小検証

2026-10-05。Chappy/★maruの追加指定により、[初回STOP報告](STEP4_POSE_COMPOSITION_PREFLIGHT_BLOCKERS.md)の顔面積比/高さ比の不一致を解消。旧STOP報告は当時の記録として保持。

## 実装結果と責務

Normal entry：`bat/04_classify_face_pose.bat` → `scripts/step4_pose_composition.py`
→ `scripts/common/pose_composition.py`。Version：step4_pose_composition_v2。

STEP4は保存済み測定値の記述・分類・集計のみ。STEP3 best_score/ranking_eligible/
global_rank・Human Review・画像を変更しない。品質順位、Reject、A/B/C、quota、
deduplication、identity、候補選択を導入しない。OpenCV/MediaPipe/body modelを
呼ばず、画像も読み込まない。旧STEP4のclassify_face_pose.pyは元の場所・内容で保持。

## 正式入力と行保持

Inputはstep3_best_ranking.csvとstep3_best_ranking_summary.json。
summaryとCSVのversion/count/SHA256、frame_id一意性、必須lineageを確認してから実行。
観測した現行入力は1,951行＝formal_video1,893＋supplemental_still58、eligible1,880、
non-ranking/fatal71。これらは観測値でありコードの固定件数ではない。

全行・STEP3列を保持し、STEP4属性を追加する。fatalは
NOT_APPLICABLE_STEP3_FATAL、欠測はNOT_EVALUABLE、整合しないbboxなどはERRORとして
行を残す。ERRORがあれば全行の診断reportを出した上でBATは非ゼロ終了する。
Human Review列は原文の監査情報として残るが分類・集計対象の選択に使用しない。

## 分類とgeometry

- Pose source：STEP3保存yaw/pitch/roll、pose_status=MEASUREDを確認。旧STEP4と
  common/best_pose.pyの計算関数AST一致を事前に確認済み。再推論なし。
- Yaw：既存SSOTの現値15/42。abs<=15 FRONTAL、15<abs<42 THREE_QUARTER、
  abs>=42 PROFILE。正yaw RIGHT／負yaw LEFTはRepository規約であり、鏡像に
  依存しない解剖学的左右を保証しない。raw値は変更しない。
- Pitch：既存SSOT現値-20/+20。<-20 LOOKING_UP、両端含む範囲LEVEL、>20 LOOKING_DOWN。
  extreme poseを拒否しない。Yawと独立属性。
- Roll：raw値のみ。roll_state=NOT_CLASSIFIED。新しい傾き閾値なし。
- face_scale_bin：顔面積比>=0.12 CLOSE_UP、0.04以上0.12未満UPPER_BODY、
  0.04未満FULL_BODY。閾値はstep3_face_gate SSOTの既存値を参照。shot_typeは同じ値のalias。
  これらは顔の相対サイズであり、胴体・脚の可視性を保証しない。
- bbox高さ/画像高さをface_height_ratioに保存。歴史的25%/10%分類は使わない。
- face_center_x_norm=(x+w/2)/image_width、face_center_y_norm=(y+h/2)/image_height。
  Stored area/short edgeを再利用し、bboxとの矛盾を確認。欠けていてbboxがある場合は
  同じgeometry式から補い、外に出たbboxを独断でclampしない。
- Edge：正規化bboxの各端が0/1に一致するexact contact。近接距離閾値なし。
  horizontal_position/vertical_positionはNOT_CLASSIFIED。欠測を0やLEVELにしない。

## 出力と再実行

本番BAT実行後、以下が作成される。今回Codexは本番出力を作成していない。

1. output/reports/step4_pose_composition.csv：STEP3の全行・元列＋属性。
2. output/reports/step4_pose_summary.json：全行status、eligibleのpose/vertical/
   face-scale/input-kind分布、pose×face-scale／pose×input-kind／face-scale×input-kind。
3. output/reports/step4_video_pose_summary.csv：video/sourceごとの全件・eligible・
   measured/missing/error、pose/face-scale件数、yaw中央値/最小/最大、既存BEST点の最大値。
4. docs/STEP4_POSE_COMPOSITION_SUMMARY.md：Chappy共有用の実分布。

Path設定は新しいstep4_pose_compositionセクション。既存の角度・顔面積閾値は変更せず
各元セクションがSSOT。CLI path overrides > local YAML > 文書化した標準path fallback。
必須角度/面積設定がない・矛盾する場合はguessせず停止する。

以前の新形式出力はreports/bkup配下へhash確認付きで保存してから再発行。
既存の旧step4_dataset_report.csvとは別名なので旧正式出力を上書きしない。
各ファイルはatomic replacement、複数ファイル一括transactionではない。
summaryを最後に書き、CSV・source-summary・Markdownのhashを記録して中断を照合できる。
STEP3/STEP4競合防止lockを取得する。

## 最小検証と限界

- STEP4 synthetic tests：19 PASS。
- 既存config tests：8 PASS。
- BAT --help：PASS。起動のみ、画像処理なし。
- 現行保存値6件だけのin-memory確認：動画・追加静止画・fatal・欠測pose・profile・
  edge contactを確認。ERRORなし。本番CSV/summary/画像コピー未作成。
- 19 testsで行保持、stills、fatal、重複画像も別行、raw angle/score不変、
  yaw15/42端点と符号、pitch端点、面積0.12/0.04端点、高さ比の非分類、
  Review状態の非依存、欠測、normalized center/edge、invalid geometry、
  schema/SSOT整合、temp-only CLI発行と旧出力保存を確認。

Execution status：実装・最小検証完了、本番は★maru未実行。
Algorithm validity：保存poseの実際の視覚精度、body visibility、LoRA適性は未保証。
Human calibration：本作業は新しい採用判定を作らない。
Unresolved：現行eligibleの182件は保存pose未測定。欠測を保持して実分布を確認する。
STEP5は旧step4_dataset_report.csv/pose_yaw等を参照するため、新形式統合は別タスク。
run_allはSTEP4後で停止し、古いreportを使った自動STEP5へ進まない。

## Changed / preserved

Changed：new scripts/common/pose_composition.py、scripts/step4_pose_composition.py、
tests/test_step4_pose_composition.py、bat/04_classify_face_pose.bat、bat/run_all.bat、
config/config.yaml・config.example.yaml・config.schema.json（新path/versionのみ）、
.gitignore（STEP4 lockのみ）、本報告、README/PROJECT/docs索引、DEC-0021・Decision索引・
Current Knowledgeの関連案内。

STEP3プログラム・採点式・report・Human Review履歴、旧STEP4コード、DEC-0005本文、
歴史的face-pose-quotaの各節、画像、STEP5以降のアルゴリズムは保存。
Knowledge Maintenance skillを適用し、既存Decision検索後に未使用ID DEC-0021を割当。
DEC-0005はSTEP7文脈も持つためglobal supersessionせず、STEP4の今回定義を新Decisionへ記録。

Rules checked：AGENTS.md、.agents/AGENTS.md、PROJECT.md、両Project Rules、関連Current
Knowledge/DEC-0005/DEC-0020/Failures/Cases/Experiments/History/current result。
Data lineage preserved：YES。Full-row preservation：YES（合成全行＋少数確認、本番未実行）。
Historical evidence preserved：YES。Config SSOT preserved：YES。Rule conflicts：解消済み。
Human Review dependency：NONE。Reject/quota introduced：NO。Full production executed：NO。

★maru：bat/04_classify_face_pose.batを実行し、生成された
docs/STEP4_POSE_COMPOSITION_SUMMARY.mdをChappyへ共有する。
実分布を確認した後にSTEP5 Deduplicationを設計する。
