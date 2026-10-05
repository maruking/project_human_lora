# STEP7 Candidate Selection v2.1 — Chappy実装報告

2026-10-05 / `step7_quality_coverage_v2.1`

## 結果と実行範囲

品質優先を明確にし、通常候補のBEST上位だけを対象とするQUALITY GUARDと、先に固定する品質コアを実装した。現行版Human Rejectの除外を維持している。Codexはunit/synthetic検証と現行データの読み取りシミュレーションのみ実施。本番STEP7公開・STEP8以降・画像推論は実施していない。現在の正式CSV/HTMLはv2のままで、Chappy確認後の★maruのBAT実行で更新する。

## 指定の報告項目

| 項目 | 実装・読み取りシミュレーション結果 |
|---|---|
| Version | step7_quality_coverage_v2.1 |
| Existing Reject Patch preserved | YES。版別履歴/feedback/画像hash/世代/現行ランキング根拠を検証 |
| Current-version Rejects excluded | 4枚。通常候補から除外、全行監査には保持 |
| Historical-only Rejects left eligible | 9枚。旧版Rejectのみでは除外しない |
| Quality guard | target×multiplierを切り上げ。既定70×2.0=140。今回実際140枚 |
| Guard score/rank bounds | 最低BEST49.75513992839904、最も低いglobal_rank232 |
| Core target | 60枚、純粋なBEST順。Coverageのために差し替えない |
| Coverage max | 10枚。不要な枠はBEST補充へ戻す |
| Final pool policy | min60/target70/max70。60〜69枚は品質維持の警告付き公開を許容。core不足・60未満は正式公開停止 |
| Pose desired coverage | FRONTAL15、3Q LEFT10、3Q RIGHT10、PROFILE LEFT2、PROFILE RIGHT2 |
| Other soft coverage | UP/DOWN各2、CLOSE_UP12、UPPER_BODY18、FULL_BODY12 |
| Coverage shortages from read-only simulation | PROFILE_LEFT：希望2、選定0、不足2 |
| Deepest selected global rank | 181 |
| Selection reason counts | BEST_QUALITY_CORE60 / COVERAGE_REPAIR0 / BEST_SCORE_FILL10 |
| Final simulated pool count | 70 |
| Identity weight | 0、変更なし |
| BEST changed | NO。保存値・global_rankをそのまま継承 |
| Semantic occlusion residual recorded | CASE-0005、Current Knowledge。検出器は未実装 |
| STEP3–6 changed | NO |
| Production executed | NO |

全上流1,951行を保存し、通常候補は現在1,075行。この件数は観測値でありコードの固定値ではない。

## 左PROFILEが不足する理由

品質範囲内には左PROFILEが2枚存在する。しかし品質コアを先に固定した時点で、その候補に適用される補足静止画集合の上限15枚に到達する。したがってsource capを緩めたり、高品質コアを差し替えたりせず、COVERAGE_SHORTAGEとして2枚不足を記録する。

このsoft不足だけではBLOCKEDにしない。source cap、品質コア、guardを優先する指定政策に従う。70枚内で良い左PROFILEが必ず確保できるという保証はしない。

## 選定順と品質の境界

1. 上流error/fatal/duplicate-memberと、正式に確認できた現行版REVIEW_REJECTを通常候補から除外する。
2. BEST降順/global_rank昇順/frame_id昇順で通常候補を並べ、QUALITY GUARDを作る。
3. 動画ごと6枚、補足静止画全体15枚、clusterごと1枚を守ってBESTコアを固定する。
4. 同じguardの残りから不足するsoft軸を最も多く補う候補を最大10枚追加する。同数ならBEST順。
5. 補完に使わなかった枠を同じguard内のBEST順で満たす。

guardは「global_rankが140以下」という意味ではない。重複などを除いた通常候補の上位140枚なので、今回のguard末尾はglobal_rank232となる。新しい物理画質閾値でもない。Coverageにはguard外の画像を復活させる権限がない。

PENDING、shown-only、旧版Reject、historical_review_reject単独、好み/favoriteは除外・加減点を行わない。Identityは診断のみ。STEP8が最終35〜45枚を判断する。

## 正式出力と公開安全性

通常BATの出力先は従来どおり全行CSV、選定候補CSV、JSON summary、STEP7_CANDIDATE_SUMMARY.md、STEP7_CANDIDATE_REVIEW.html。新しいsummaryにはguard要求数/実数/値・順位の境界、core/repair/fill件数、最も低い選定順位、soft希望/達成/不足、pool品質状態、現行Human Reject件数を追加する。

`current_version_human_reject_removed_from_pool`はguard作成前の通常候補資格から除外した数。前回正式70枚との差分数ではない。今回の入力では4。scopeもJSONに明示する。

HTML上部にQUALITY GUARD、品質コア/Coverage/BEST補充の件数、最も低い選定順位、soft不足を表示する。カードはPose→Face scale分類/BEST順、原画像リンク付き。Coverage候補への順位加点はしない。

正式公開時は前回成果物をhash検証付きarchiveへ保存し、個別ファイルatomic置換、summary最後、捕捉可能なエラー時rollbackを行う。既存共通publisherのarchive内部prefixはSTEP6名だが、manifestは正しいSTEP7元パス/hashを記録し、成果物のstep7_versionで版を識別できる。強制終了まで保証する複数ファイルtransactionではない。Partial/BLOCKEDは隔離auditのみで既存正式結果を上書きしない。

## 変更ファイルと旧版保存

- 新規：`scripts/common/candidate_selection_v21.py`、`scripts/step7_candidate_selection_v21.py`。
- 更新：`bat/07_score_lora_candidates.bat`をv2.1入口へ接続。
- 更新：`config/config.yaml`、`config/config.example.yaml`、`config/config.schema.json`。変更対象はSTEP7設定のみ。
- 新規：`config/step7_candidates_v2_legacy.json`。汎用exampleの旧STEP7設定を保存。
- 新規：`tests/test_step7_quality_coverage_v21.py`。旧v2テストの既定設定fixtureのみlegacy snapshotへ接続。
- 新規：DEC-0025、CASE-0005、本実装報告。
- 更新：DEC-0024のstatus/superseded_byと追記、Decision/Case/docs/Current索引、候補選定/設定/Pose Knowledge、README、PROJECT。

旧v2実装、現行版Reject検証コード、v2正式report、旧実装報告とReject patch報告は変更せず保存した。DEC-0024本文は履歴として残し、DEC-0025へ継承関係を示す。

## 検証と限界

- STEP7テスト65件PASS：旧版/Reject検証40件＋新規25件。指定23項目と正式公開/Partial隔離を検証。
- configテスト8件PASS。
- 通常BATのpreflight-only PASS：全1,951行、通常候補1,075行、同版Reject4件。選定/公開/画像推論なし。
- 現行データを読み取り、メモリ内で選定シミュレーション。正式成果物は生成していない。
- 上流report、版別履歴、原v2コード/正式成果物/報告のhash不変を確認。

品質guardは相対順位の境界であり、顔学習に必ず適する保証ではない。semantic hand/object occlusionはuser-reported residual。対象frame_idが提供されていないので、特定の画像に加工/遮蔽を断定しない。CASE-0005はLOW confidenceとし、hand-to-face overlap等の一般的な検証はpost-pipelineへ延期した。画像名/video名での例外は導入していない。

Rules checked：AGENTS.md、.agents/AGENTS.md、PROJECT.md、Pipeline/Data Lineage Rules、関連Knowledge/Decisions/Failures/Cases/History/Experiments。
Data lineage / Full-row preservation / Historical evidence / Config SSOT preserved：YES。
追加Failure/Experiment/History記録は不要。今回の新しいDecision/Caseと本報告で限定的な検証事実を保存する。

## ★maru

本実装報告をChappyへ渡す。Chappy確認後にだけ `bat/07_score_lora_candidates.bat` を実行する。実行後のSTEP7_CANDIDATE_SUMMARY.mdをChappyへ共有する。まだSTEP8の最終35〜45枚選択は開始しない。
