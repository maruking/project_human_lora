# STEP7 Candidate Selection v2 — 実装報告

2026-10-05 / `step7_quality_coverage_v2`

## 目的と実行範囲

STEP7はSTEP8で人間が確認する約70枚の候補を作る。最終35〜45枚の採用はSTEP8の★maruの判断に委ねる。今回Codexが実施したのは実装、合成データのテスト、既存reportの読み取り検証のみ。本番STEP7、STEP8以降、画像推論、候補画像コピーは実行していない。

## STEP7 version / Legacy STEP7 audit

通常の `bat/07_score_lora_candidates.bat` を新規 `scripts/step7_candidate_selection_v2.py` へ接続した。選定本体は `scripts/common/candidate_selection_v2.py`。

旧 `score_lora_candidates.py` はIdentity 35%等を含む別品質スコアとIdentity通過条件を持つため、通常BATから利用しない。旧 `select_revision_b.py`、`common/revision_b.py`、DEC-0012、DEC-0013、A/B/C sidecar、Human Review履歴は保持した。DEC-0013はDEC-0024によりSUPERSEDEDとし、旧本文は保存した。

## Primary quality authority / Identity selection weight

`selection_quality_score = best_score`。STEP3の保存値を変更せず継承する。順序はBEST降順、global_rank昇順、frame_id昇順。新しい複合品質スコア、Pose加点、人間の好みは導入しない。

Identityの選定重みは0。IDENTITY_REJECT、REVIEW、NOT_EVALUABLEおよびidentity_passed=falseだけを理由に除外しない。状態・類似度・cluster_identity_fallback_neededは診断として表示する。LOW_MEASURED_IDENTITYは別人という断定ではない。重複メンバーを自動昇格させない。

## Candidate universe / target / Coverage minima / Source caps

通常候補はranking_eligible=trueかつUNIQUEまたはREPRESENTATIVE。DUPLICATE_MEMBER、STEP3 fatal、upstream ERRORは通常候補外とするが、全行監査には保持する。

現在の読み取り検証では全体1,951行、通常候補1,079行。これは入力の件数であり、本番選定結果ではない。コードに現在の件数や動画名を固定していない。

configの新しい `step7_candidates_v2` がSSOT。目標70、設定可能な範囲60〜80。旧STEP7設定は履歴として保持する。

| 軸 | レビュー候補の最低選択肢数 |
|---|---|
| Pose | FRONTAL 15、THREE_QUARTER_LEFT 10、THREE_QUARTER_RIGHT 10、PROFILE_LEFT 4、PROFILE_RIGHT 4 |
| Vertical | LOOKING_UP 2、LOOKING_DOWN 2 |
| Face scale | CLOSE_UP 12、UPPER_BODY 18、FULL_BODY 12 |

これらは最終学習枚数・比率ではない。FULL_BODYは顔の面積区分で、脚や全身が見える証拠ではない。

formal_videoは動画ごとに最大6、supplemental_stillは集合全体で最大15、同一dedup clusterから最大1。上限は自動緩和しない。

## Selection algorithm

Phase Aは不足するPose / Vertical / Face scaleの軸を最も多く満たす候補から選ぶ。同数ならBEST順。COVERAGE_OPTIONとその時点の不足軸を記録する。Phase Bは残り枠をBEST順で満たし、BEST_SCORE_FILLを記録する。表示順step7_pool_orderもBEST順であり、Coverage候補に品質加点しない。

Phase Aも設定された目標枚数を枠上限とする。最低選択肢数が同時に満たせない場合は不足・競合を報告し、目標枚数やsource capを無断変更しない。SOURCE_CAP_COVERAGE_CONFLICT等の競合はBLOCKEDとして隔離し、Chappyの方針確認を要求する。利用可能なカテゴリ自体が不足する場合は不足を明示し、架空候補やduplicate昇格で埋めない。

## Full-row preservation / Preflight / Publication

STEP3 best_rank_v2.2、STEP4 step4_pose_composition_v2、STEP5 step5_dedup_v2、STEP6 step6_identity_v2を指定reportから検証する。STEP6 COMPLETE、CSV hash、全行ID、世代、継承列、状態件数、保存された上流hash、クラスタ整合性、BEST値・順位、画像ファイルの存在を確認する。最新reportへの自動fallbackはない。

現行STEP3/4 summaryには文字通りのCOMPLETEフィールドがない。そのため既存の全行ID・件数と固定hashの契約で構造的な完了を検証する。上流metadataを変更したり完了状態を捏造したりしない。STEP5/6は明示的なCOMPLETEを要求する。

全行と全STEP3〜6列を保存し、STEP7列を追加する。非選定はNOT_NEEDED_FOR_REVIEW_POOLであり、新しい画像品質Rejectではない。

公開処理は既存STEP6の共通化可能な処理を再利用し、前回成果物のarchive、個別ファイルのatomic置換、summaryの最後の公開、検出エラー時のrollbackを行う。プロセス強制終了まで保証する複数ファイル一括transactionではない。共通archiveの内部ディレクトリ名にSTEP6 prefixが残るが、保存manifestは各STEP7元パスを記録する。Partial / test / BLOCKED成果物は隔離auditへ出力し、正式成果物を上書きしない。

## Review HTML / 本番BATが生成する成果物

- `output/reports/step7_candidate_selection.csv`：全行監査
- `output/reports/step7_review_candidates.csv`：選定されたレビュー候補のみ
- `output/reports/step7_candidate_summary.json`
- `docs/STEP7_CANDIDATE_SUMMARY.md`
- `docs/STEP7_CANDIDATE_REVIEW.html`

HTMLはPose→Face scaleで分類し、各区分をBEST順に表示する。原画像へリンクし、画像クリックで開ける。BEST・順位、Pose/yaw/pitch、Vertical/Scale、dedup role/cluster size、Identity診断、source、選定理由を表示する。概要には分布、品質範囲、不足、source cap競合を表示する。今回、本番HTMLや候補CSVは生成していない。

## Tests / Minimum validation

- STEP7 unit / synthetic / tiny-fixture：28件PASS。依頼の24項目に加え、上限競合、非選定の意味、fatal/error除外、加点なしの表示順を検証。
- config/schema：8件PASS。
- 通常BATの `--preflight-only`：PASS。全1,951行と通常候補1,079行の入力検証のみ。選定・成果物公開・画像推論なし。
- 保護対象の旧実装、STEP3〜6 report、STEP6 docsの変更がないことをhashで確認。

## Decision / Knowledge / Unresolved shortages

DEC-0024を新設し、現行Knowledge `candidate-selection.md`、設定・Pose Knowledge、索引、PROJECT、READMEを現在の責務に整合させた。Failure / Case / Experiment / History索引を確認し、今回新規記録が必要な事実はない。

読み取り検証では各カテゴリの候補数と独立したsource cap上限は要求数以上。ただしこれは複数軸を同時に満たす70枚の選定成功を証明しない。実際の選定枚数・同時充足・不足は未測定で、本番実行後のsummaryで確認する。STEP3〜6の数式、threshold、出力、Human Review履歴、画像は変更していない。

**Full production executed: NO**

## ★maru の次の操作

まず本実装報告をChappyに共有する。Chappy確認後、★maruが `bat/07_score_lora_candidates.bat` を実行する。生成されたSTEP7_CANDIDATE_SUMMARY.mdとSTEP7_CANDIDATE_REVIEW.htmlをChappyへ共有する。この段階では最終35〜45枚を選ばず、候補構成を確認する。
