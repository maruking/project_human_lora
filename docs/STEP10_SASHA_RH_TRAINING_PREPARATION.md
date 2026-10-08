# STEP10 sasha_rh Dataset / AI Toolkit Training準備

実施日: 2026-10-07。★maruの指示によりSTEP10だけ再Packaging。
Trainingは開始していません。

## Chappyへ共有するファイル

- Training YAML: `C:\Users\maruk\Documents\makeLora\ai-toolkit\config\sasha_realhuman_flux2_klein9b.yaml`
- STEP10 audit: [step10_dataset_report.csv](../output/reports/step10_dataset_report.csv)
- 検証記録: [step10_sasha_rh_packaging_verification.json](../output/reports/step10_sasha_rh_packaging_verification.json)
- Dataset: `C:\Users\maruk\Documents\Genelate_img\Sasha_re_codex\real_human_lora\output\dataset_flux`

## 実施結果 — observed

| 確認項目 | 結果 |
| --- | --- |
| local config `project.trigger_word` | character → sasha_rh |
| STEP10 preflight | PASS、STEP8_ACCEPT 40枚、STEP8_ORIGINAL |
| 正式BAT | bat/10_package_flux_dataset_gpu.bat、exit 0 |
| PNG / paired TXT / metadata / audit | 各40件 |
| captionにsasha_rh | 40/40、各1回 |
| captionにcharacter | 0/40 |
| 旧Packagingとのcaption差分 | trigger置換のみ |
| 確定frame_id集合・順序 | 不変 |
| 元画像40枚のSHA256 | 不変 |
| 旧Packagingとの出力PNGのSHA256 | 40/40一致、画像内容不変 |
| STEP1〜9の既存report類 | 36ファイルのSHA256不変 |
| 16px alignment | 全40枚PASS、既存処理を維持 |
| restoration_status | SKIPPED_NOT_NEEDED、全40件 |

旧Dataset・旧STEP10 CSV・実施前のhash記録を以下に保存しました。

`output/bkup/step10_before_sasha_rh_20261007_200327/`

元画像・STEP8選定・Human Reviewを変更していません。
STEP1〜9の実行、Restoration、Trainingは行っていません。

## Training YAML — 現在のrepo実装に基づく設定

AI Toolkit root: `C:\Users\maruk\Documents\makeLora\ai-toolkit`

確認したHEAD: `ecee894ed2b1f3716d9d7326693061ec1a3105bb`。
既存 `config/examples/train_lora_flux_24gb.yaml` を参考に作成。

| 設定 | 値 |
| --- | --- |
| Base Model | black-forest-labs/FLUX.2-klein-base-9B |
| model.arch | flux2_klein_9b |
| device | cuda:0 |
| 本体 / Text Encoder | quantize=true / quantize_te=true、qfloat8 |
| low_vram | true |
| LoRA rank / alpha | 16 / 16 |
| batch / accumulation | 1 / 1 |
| steps / lr / optimizer | 2000 / 1e-4 / adamw8bit |
| train dtype / gradient checkpointing | bf16 / true |
| Text Encoder training | false |
| Dataset resolutions | 512 / 768 / 1024 |
| latent / text embedding cache | 有効 |
| caption dropout / shuffle | 0 / false |
| save interval / retained saves | 250 / 4 |
| sample interval / steps / guidance | 250 / 25 / 4.0 |

Klein用のarchitectureを指定し、FLUX.1用の `is_flux: true` は付けていません。
現在の `toolkit/models/registry.py` と
`extensions_built_in/diffusion_models/flux2/flux2_klein_model.py` にある
Klein Base 9B登録・実装と一致しています。

### trigger_wordの扱い

現在の `toolkit/prompt_utils.py` の `inject_trigger_into_prompt` は、
placeholder置換と、trigger未存在時の追加を行います。
`toolkit/dataloader_mixins.py` のcaption読み込みもこの関数を使用します。
既にliteral `sasha_rh` を含むため、このYAMLではprocessにもdatasetにも
`trigger_word` を設定していません。`[trigger]` placeholderも使いません。
sample promptにもliteral `sasha_rh` を直接記載。
caption dropout=0とし、学習captionからtriggerを落とさない設定です。

### 最小確認と未確認範囲

AI Toolkit既存venvで、`toolkit.config.get_config` による読み込み、
ModelConfig / TrainConfig / DatasetConfig / NetworkConfig / SaveConfig /
SampleConfig生成、`validate_configs` を実行してPASS。
Base Model / architecture / dataset path / trigger未設定もassertで確認しました。
Training jobの生成・モデルweight読み込み・ダウンロードは実行していません。

24GB向けの量子化・cache・checkpointing設定を用意しましたが、
実学習時のVRAM使用量・OOMの有無・学習品質は未検証です。
2000 steps等は参考exampleに基づく初期設定であり、最適値の実験結果ではありません。
AI Toolkitの既存ignoreによりこの個別YAMLはlocal config扱いです。

## 変更範囲・Rules

今回の設定変更はREAL_HUMAN_LORAの `config/config.yaml` のtriggerだけ。
新規Training YAML、STEP10再生成物、検証JSON、本報告とSTEP10資料案内を更新。
既存Python / BAT / caption生成ロジックを変更していません。

Rules checked: AGENTS.md、.agents/AGENTS.md、PROJECT.md、
.agents/rules/lora_pipeline_rules.md、data_lineage_rules.md、関連STEP10 Knowledge / DEC-0029。
AI Toolkit内と関連ancestorに追加AGENTS.mdなし。

- Data lineage preserved: YES
- Full-row preservation: YES、STEP10確定40件。既存全体auditは変更なし
- Historical evidence preserved: YES
- Config SSOT preserved: YES
- STEP1〜9 changed / executed: NO
- Training executed: NO
- Rule conflicts: none

新しい設計Decisionは不要。既存DEC-0029の承認済み入力経路を使用。
旧preflight-only実装記録は履歴として保存し、今回の本Packaging結果と区別します。

## ★maruがやること

完成したTraining YAMLと本報告・STEP10 audit CSVをChappyへ共有してください。
まだTrainingは実行しません。
