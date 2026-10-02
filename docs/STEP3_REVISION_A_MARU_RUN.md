# STEP3 Revision A — 全件A/B/C / maru実行待ち

実行担当はmaru。CodexはBAT・Pythonを準備し、この修正版の診断・テスト実行は行っていません。

運用方針の正式参照先は [Codex Execution Policy](../.agents/AGENTS.md#codex-execution-policy) です。
必要最小限の実装動作確認はCodexに許可されますが、通常の全件診断・再生成は★maruが実行します。
明示的な調査・監査依頼による実行も、その依頼範囲に限定します。

## 対象

正式STEP1の全2,001枚＋追加静止画57枚＝現在想定2,058枚。
自動OK62枚のみには限定しません。既存公式Rejectも全件入力に含めます。
枚数はコードに固定せず、STEP1正式metadataと追加画像inventoryから取得・照合します。

## maruが実行するファイル

[bat/03_revision_a_diagnostics.bat](../bat/03_revision_a_diagnostics.bat) を実行してください。
対応Pythonは [scripts/step3_revision_a_diagnostics.py](../scripts/step3_revision_a_diagnostics.py) です。
既にローカル設定に追加静止画フォルダが指定されています。

```cmd
bat\03_revision_a_diagnostics.bat
```

開始時に formal / supplemental / total を表示します。現在の想定は2,001 / 57 / 2,058です。
全件測定・全件A/B/C記録・重複なしを確認してから、新規runに出力します。

## 出力

`output/reports/step3_revision_a/runs/<run_id>/` に以下を保存します。

- `selection_groups.csv`: 全画像のA/B/C・根拠・人間確認状態。
- `selection_A.csv`, `selection_B.csv`, `selection_C.csv`: 各群の一覧。全件CSVと同じ分類で、群間の重複なし。
- `diagnostics.csv`, `diagnostics.json`: 全件の目・露出・顔ディテール測定と公式判定の参照情報。
- `summary.json`, `REPORT.md`: 対象数、各群数、診断結果、設定と来歴。

成功時だけ `output/reports/step3_revision_a/latest.json` を新しいrunへ更新します。
今のlatestはCodexが実行した旧138枚の部分結果です。maruによる全件実行が成功するまでは全件結果ではありません。

## A/B/Cの確定と暫定を区別

- A: 明示的な人間確認済みの主候補。
- B: 人間確認済みのReserve、または確認不足の暫定B。`selection_review_status`でCONFIRMED / UNDECIDEDを区別します。
- C: 既知の明示Human Rejectを保持。

新しい診断閾値だけでA/Cを確定しません。既存公式Rejectを入力に含めることは、その画像の復活・使用許可を意味しません。公式拒否理由は別欄に保存し、暫定Bは人間確認まで使用不可です。
公式STEP3判定、閾値、画像、人間評価履歴は変更しません。最終選定・STEP4以降は実施しません。

## 現在の検証状態

入力フィルタ撤去、全件件数チェック、A/B/C分割出力をソース確認しました。
修正後の実測数・各群数・BAT動作・再現性はmaru実行待ちです。旧123テストPASSと138枚実行の記録は修正版全件実行の成功証拠にはしません。

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md, applicable rules and previously consulted Knowledge.
Data lineage preserved: YES (structure retained; corrected run pending).
Full-row preservation: PLANNED ALL formal + supplemental; runtime verification pending.
Historical evidence preserved: YES. Config SSOT preserved: YES.
