# STEP3 人間レビューの現状とChappy相談資料

状態：**ChappyのLoRA顔学習適性の判断待ち**。この出力では次工程へ進めていません。
目的は写真としての見栄えだけではなく、実人物の顔・目・肌をLoRAが学習する素材として問題がないかの確認です。

## 現在の状態

- 自動OK：62枚（正式CSVの判定は維持）。
- ユーザー拒否：自動OK中8枚。
- Chappy判断待ち：3枚。
- その他：51枚は個別の採否が未記録。人間OKとは扱っていません。
- Sasha_v69：現世代の26枚すべてユーザー拒否。このうち自動OKは7枚。
- 既存のSasha_v63/Sasha_v63_020.pngへの拒否も維持。

ユーザーの指摘は人間評価として記録しています。白飛び・加工・目の半開は、ここで新たに機械判定して確定した結果ではありません。

## Chappyへの確認事項

1. 以下3枚の半開の目は自然な表情としてLoRAの顔学習に許容できるか。瞬き途中・目の形の学習への悪影響として除外すべきか。
2. Sasha_v69の白飛び・不鮮明・顔周りの加工について、顔の特徴や自然な肌の学習に問題があるか。動画全体の除外判断を維持すべきか。
3. 各画像について「許容／不可／判断困難」と、その理由を返してください。FULL_BODYで自動判定が省略されている目・肌の項目も、画像から確認してください。

**ChappyがLoRAの顔学習に問題ないと判断する場合に限り、継続可否を検討します。現在はChappyの回答がありません。**

## 半開の目：判断待ち3枚

### OK006 · Sasha_v05/Sasha_v05_012.png · FULL_BODY

ユーザー評価：目が半開。Chappy判断待ち。

![全体](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK006_full.png)

![顔crop](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK006_face.png)

### OK007 · Sasha_v05/Sasha_v05_013.png · FULL_BODY

ユーザー評価：目が半開。Chappy判断待ち。

![全体](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK007_full.png)

![顔crop](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK007_face.png)

### OK021 · Sasha_v08/Sasha_v08_005.png · UPPER_BODY

ユーザー評価：目が半開。Chappy判断待ち。

![全体](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK021_full.png)

![顔crop](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK021_face.png)

## Sasha_v69：全26枚をユーザー拒否（以下は自動OKだった7枚）

理由：白飛び・不鮮明・顔周りに加工あり。OK056の004、OK058の015もこの動画全体の拒否に含みます。

### OK056 · Sasha_v69/Sasha_v69_004.png · FULL_BODY

ユーザー評価：拒否。

![全体](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK056_full.png)

![顔crop](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK056_face.png)

### OK057 · Sasha_v69/Sasha_v69_014.png · FULL_BODY

ユーザー評価：拒否。

![全体](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK057_full.png)

![顔crop](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK057_face.png)

### OK058 · Sasha_v69/Sasha_v69_015.png · FULL_BODY

ユーザー評価：拒否。

![全体](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK058_full.png)

![顔crop](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK058_face.png)

### OK059 · Sasha_v69/Sasha_v69_017.png · FULL_BODY

ユーザー評価：拒否。

![全体](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK059_full.png)

![顔crop](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK059_face.png)

### OK060 · Sasha_v69/Sasha_v69_018.png · FULL_BODY

ユーザー評価：拒否。

![全体](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK060_full.png)

![顔crop](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK060_face.png)

### OK061 · Sasha_v69/Sasha_v69_022.png · FULL_BODY

ユーザー評価：拒否。

![全体](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK061_full.png)

![顔crop](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK061_face.png)

### OK062 · Sasha_v69/Sasha_v69_024.png · FULL_BODY

ユーザー評価：拒否。

![全体](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK062_full.png)

![顔crop](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK062_face.png)

## 既存の拒否も維持

Sasha_v63/Sasha_v63_020.png：ブレ度が高く許容できない。

![顔crop](C:/Users/maruk/Documents/Genelate_img/Sasha_re_codex/real_human_lora/output/reports/step3_chappy_handoff/assets/OK055_face.png)


## 記録と検証範囲

正式STEP3 CSV・Gate閾値/数式・元画像・STEP4+は変更していません。
人間評価はgeneration/frame identity付きsidecarに保存し、自動判定へ適用していません。
旧評価状態はstep3_eligible_all_audit/review_state_historyに保存しています。
62行の状態、8拒否/3判断待ち、v69全26枚拒否、22画像の相談ZIPと参照整合性を検証済み。
ブラウザでの目視QAはfileアクセス制限により未実施。合否や加工の判断はユーザーの申告です。

Rules checked: AGENTS.md, .agents/AGENTS.md, PROJECT.md,
.agents/rules/lora_pipeline_rules.md, .agents/rules/data_lineage_rules.md;
関連Current/Decisions/Failures/Cases/STEP3 results/Historyは本セッションで確認済み。
Data lineage preserved: YES. Full-row preservation: YES (2,001 source;62 eligible state rows).
Historical evidence preserved: YES. Config SSOT preserved: YES.
README/Current/Decisions/Failures/Cases/Experiments/History checked:
Documentation checked; no update required beyond this human-review-state output.
学習適性の専門判断、閾値変更、人間ラベルの自動適用、STEP4+は未実施。
