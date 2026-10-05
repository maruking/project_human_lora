# STEP8 Folder-Based Human Final Review — 実装報告・操作手順

2026-10-05 / step8_folder_review_v2

## 完了報告

| 指定項目 | 結果 |
|---|---|
| STEP8 version | step8_folder_review_v2 |
| Input candidate count | 現行STEP7 v2.1 COMPLETEの70枚。上流全体は1,951行 |
| Pose review folders | 下記6フォルダ。stored pose_binで分類 |
| Guidance ranges | Pose/Scale/Verticalは目安。合計35〜45枚のみhard件数 |
| Review materialization | 実装済み。各候補をFULLへ1回だけコピー、ACCEPTは空 |
| ACCEPT protection | 非空なら通常prepare停止。明示reset時も旧選択をarchive保存 |
| Final count validation | <35 NEED_MORE_SELECTION、35〜45 VALID、>45 TOO_MANY_SELECTED |
| Summary outputs | Manifest、準備metadata、全行選択CSV、JSON、Markdown |
| STEP9 handoff | 検証済みCSVのSTEP8_ACCEPT行だけを返すloader実装。旧STEP9はガードで停止 |
| Tests | STEP8 25件PASS、config8件PASS、共通review保護27件PASS、両BAT preflight-only PASS |
| Production folder preparation executed | **NO** |

Codexは一時フォルダの合成画像で配置/選択/集計を検証した。実画像の本番コピーや★maruの採用判断は実施していない。STEP3〜7正式成果物・履歴・原画像は変更していない。

## ★maruの操作

1. STEP7のcurrent-version Reject patchが正式に反映されていることを確認する。現状はv2.1、候補70枚、Reject4枚を除外した正式成果物があり、STEP8事前検証もPASS。添付指定どおりSTEP7を再実行する場合は `bat/07_score_lora_candidates.bat` を先に実行する。
2. `bat/08_prepare_folder_review.bat` を実行する。
3. Explorerで `work/step8_review/` を開く。
4. 各PoseのFULLを見て、採用したい画像だけ同じPoseのACCEPTへ**コピー**する。名前を変えず、FULLから削除しない。
5. 全体35〜45枚（約40枚）を選ぶ。選択理由を記載する必要はない。
6. `bat/08_collect_folder_review.bat` を実行する。
7. 生成された `docs/STEP8_SELECTION_SUMMARY.md` をChappyへ渡す。STEP9はまだ実行しない。

コピー作業を終えてから集計BATを実行する。実行中はACCEPTを変更しない。件数が範囲外でも画像は自動調整しない。summaryに不足/超過を出力し、終了コードを非zeroにして後段進行を止める。これは選択を変更して再集計するための状態。

## フォルダと目安

各フォルダにFULL/とACCEPT/を作る。Face scaleを別のフォルダ軸にしないので同じ画像を重複配置しない。

| Pose folder | 採用目安 |
|---|---:|
| 01_FRONTAL__ACCEPT_12-17 | 12〜17 |
| 02_THREE_QUARTER_LEFT__ACCEPT_7-10 | 7〜10 |
| 03_THREE_QUARTER_RIGHT__ACCEPT_7-10 | 7〜10 |
| 04_PROFILE_LEFT__ACCEPT_1-3 | 1〜3 |
| 05_PROFILE_RIGHT__ACCEPT_1-3 | 1〜3 |
| 06_NOT_EVALUABLE__ACCEPT_0-2 | 0〜2 |

設定値は `config.step8_folder_review` がSSOT。画像品質を優先する。現行STEP7では左PROFILE候補0枚なので、そのFULLは空になる。目安を埋めるための復活/低品質候補追加はしない。

Face scale目安：CLOSE_UP8〜12、UPPER_BODY16〜24、FULL_BODY6〜12。上下は良い素材があればLOOKING_UP/DOWN各1枚以上。いずれも警告のみで、合計35〜45がVALIDならそれだけでfinalizationを拒まない。FULL_BODYは上流の顔面積区分で、全身可視性の認定ではない。

## 名前と正式Identity

`R{global_rank:04d}_B{best_score:05.1f}_{vertical_pose}_{face_scale_bin}__{original_basename}`。
順位・BEST・上下・ScaleをExplorer上で読める。補足静止画も同じ形式。長すぎる/衝突する名前のみframe_id由来のsuffixを付ける。正式frame_id、BEST、global_rank、source/hash/generationは変更しない。

名前は操作用表示でありpipeline identityではない。Manifestが正しいframe_idへ戻す。Poseはstored STEP4 pose_binを利用し、再推論しない。画像のsource bytesとFULLコピーのhashを確認する。

## ACCEPT保護と再準備

通常prepareはACCEPTに1件でもあれば停止する。意図的に選択をリセットするときだけ、別操作として `08_prepare_folder_review.bat --reset-review` を実行する。既存review全体（ACCEPTの選択を含む）を `work/bkup/step8_folder_review_v2_<id>/` へ保存し、新しいACCEPTを空にする。旧選択を無断削除しない。

通常再準備でも既存の空ACCEPT/FULLを持つ旧sessionはarchiveする。未知フォルダ/ファイル、sourceとの重複、リンク/junction等は停止して検査を要求する。新sessionのmanifest/preparation hashにより、旧STEP8のfinal CSVは再集計まで利用できない。

## 成果物と監査

準備時：

- `output/reports/step8_review_manifest.csv`：候補70枚の名前→frame/source mapping、BEST/pose/scale/dedup/identity、FULL/ACCEPTパス。
- `output/reports/step8_review_preparation.json`：入力hash、session、Manifest hash、設定。

集計時：

- `output/reports/step8_human_selection.csv`：上流全1,951行・全列を保持。候補にはSTEP8_ACCEPT/STEP8_NOT_SELECTEDを付与。候補外はNOT_APPLICABLE_NOT_IN_REVIEW_POOL。
- `output/reports/step8_selection_summary.json`：合計状態、Pose/Vertical/Scale/Identity、source分布、BEST min/median/max・順位範囲、目安との不足/超過、入力・成果物hash。
- `docs/STEP8_SELECTION_SUMMARY.md`：Chappy共有用の集計。

STEP8_NOT_SELECTEDは今回の学習集合に不要という意味で、悪い画像のRejectではない。Identity状態だけでHuman採用を取り消さない。好み・表情・服装・加工・遮蔽等は★maruが判断してよい。

集計は未知ファイル、同一frameの重複採用、Pose違いの配置、FULL欠落、画像改変、現行版Reject、古い世代/session/reportを停止する。現行Rejectをgeneric historical/shown列から推定せず、正式版別history/feedbackで確認する。

## STEP9境界

正規入力は検証済み `step8_human_selection.csv` とVALID summary。`load_step9_selection`はSTEP8_ACCEPTだけを返し、元画像のIdentity/hashを検証する。ACCEPTフォルダの中身を後段のSSOTにはしない。集計後に操作用コピーを破棄しても、正式CSVと元画像が有効なら引き渡しを読める。

既存STEP9はwork/selectedの直接走査と旧full-face復元を実装しており、新しいCSV入力およびcomponent-only方針に整合しない。通常 `09_selective_restoration_gpu.bat` はCSV検証後にSTOPし、旧復元を起動しない。旧BATは `bat/legacy/09_selective_restoration_gpu_legacy.bat` に同内容を保存、復元Python自体は変更していない。STEP9へのCSV入力adapter/component-mask整合は別の作業。今回、STEP9を実行したり対応完了としたりしない。

## 変更ファイル

- 新規Python：`scripts/step8_folder_review.py`、`scripts/common/folder_review.py`。
- 新規BAT：`bat/08_prepare_folder_review.bat`、`bat/08_collect_folder_review.bat`。
- 更新：config/local/example/schemaに独立step8_folder_review設定を追加。旧step8_reviewは保存。
- 更新：`scripts/common/step3_review.py`にSTEP8 interaction/stage/archiveの入力禁止登録を追加。STEP3〜7の計算・成果物は変更なし。
- 更新：`.gitignore`にSTEP8 copies/stage/lockを追加。
- 更新：通常STEP9 BATに停止ガード。旧BAT保存。
- 新規：STEP8テスト、DEC-0026、Current Knowledge、本報告。更新：README/PROJECT/docs・Knowledge索引/設定Knowledge。
- 保存：旧STEP8 BAT/Python、旧review履歴/outputs、STEP3〜7の正式成果物・BEST値。

## 検証と限界

依頼18項目を含む25テストPASS。合成ファイルのFULL配置、空ACCEPT、保護/明示archive reset、改変/unknown/重複停止、件数35〜45、soft警告、全行/列継承、CSV handoff、レビューinput禁止を検証。config8件と共通review保護27件もPASS。Prepare/Collect両BATのpreflight-onlyは現行1,951行/70候補/4除外RejectにPASS。

ディレクトリswapとreport公開はprocess-crashを含む一括transactionではない。session/hash不整合は停止する。公開時は既存report archive、個別atomic置換、marker最後、捕捉可能なエラー時のrollbackを再利用する。旧共通publisherのarchive内部prefixにはSTEP6名が残るが、manifestは正しい元パス/hashを保持する。

Rules checked：AGENTS.md、.agents/AGENTS.md、PROJECT.md、Pipeline/Data Lineage Rules、関連Knowledge/Decisions/Failures/Cases/History/Experiments。
Data lineage / Full-row preservation / Historical evidence / Config SSOT preserved：YES。
新規Decision26とCurrent Knowledgeを追加。新規Failure/Case/Experiment/History記録は不要。原画像を変更する処理はなく、本番reviewコピーはCodex未作成。

**Production folder preparation executed: NO**
