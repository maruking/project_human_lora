# STEP3 Revision A — upscale後の全件診断手順

正式動画フレーム1,893枚＋追加静止画58枚＝現行1,951枚が対象です。
これは正式metadataから確認した現在値で、コードの固定枚数ではありません。
正式STEP3のeligible 1枚だけに限定せず、公式Rejectも監査対象に含めます。
Rejectを対象へ含めることは、採用・復活を意味しません。

## 実行前の必要条件

- 現世代STEP1、STEP2、正式STEP3のCSVとsummaryが整合していること。
- `config/step3_revision_a.local.json` に追加静止画フォルダが指定されていること。
- `output/reports/step3_eligible_human_review.csv` が現世代の人間評価sidecarとして
  用意され、`dataset_generation_id`、STEP3 CSVの`source_sha256`、frame identityが
  現世代と一致していること。

今回整理時点では上記のHuman Review sidecarはactive reportsにありません。
現世代のレビュー資料・sidecarの準備が必要です。旧bkupの人間評価を同名画像へ
そのまま復元・適用しないでください。この整理ではレビュー生成や復元は行っていません。

## 実行担当・入口

前提が揃ってから★maruが [03_revision_a_diagnostics.bat](../bat/03_revision_a_diagnostics.bat)
を実行します。対応Pythonは
[step3_revision_a_diagnostics.py](../scripts/step3_revision_a_diagnostics.py) です。

```cmd
bat\03_revision_a_diagnostics.bat
```

入力数は開始時のformal / supplemental / total表示で確認します。
通常の全件処理は★maruが担当し、Codexはこの整理で実行していません。

## 出力と分類の意味

`output/reports/step3_revision_a/runs/<run_id>/` に全件diagnostics、summary、
`selection_groups.csv` と各A/B/C CSVを保存し、成功時のみlatestを更新します。

- A: 明示的に人間確認された主候補。
- B: 確認済みreserve、またはUNDECIDEDの暫定候補。
  未確認Bは人間確認まで採用不可。
- C: 人間Rejectを保持し、角度・構図不足で復活させない。

診断のNORMAL/OPENのみでAへ昇格しません。正式STEP3判定と選定状態は別管理です。
公式Gate・閾値・画像・人間評価履歴は変更せず、STEP4以降はこのBATで実行しません。
旧2,058枚手順・138枚部分実行結果は[docs索引](README.md)に記載したbkup内に保存済みです。
