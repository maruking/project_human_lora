# HISTORY — 2026-10-02 STEP3 Coordination Breakdown

## Summary

2026-10-02 の `project_human_lora` STEP3 作業では、★maru / Chappy / Codex 間で
「何を改善しているのか」「誰が実行するのか」「どの時点で人間基準を反映するのか」
の共有が崩れ、長時間の付きっきり作業になった。

## What actually happened

- STEP3 Revision 1 は、全 2,001 frame の処理、lineage、再現性、report、audit の検証を完了した。
- ただし既存 Gate threshold / formula は維持され、Gate 精度そのものは改善されていない。
- STEP3_RESULT は Execution / reproducibility の PASS であり、Algorithm validity / Human calibration の PASS ではない。
- 現行 Gate により Eligible は 62 / 2,001 (3.10%) まで絞られた。
- Human Review で、以下の問題が判明した。
  - 半開眼 / blink 途中でも自動 OK に入る
  - 白飛び / 強加工 / detail loss でも自動 OK に入る
  - 逆に、人間視覚で十分使える画像が `low_resolution_source` や blur Gate で Reject される
- 代表例:
  - `Sasha_v01_007.png`: 顔は十分鮮明だが `REJECT_LOW_RES`
  - `Sasha_v01_013.png`: 顔は十分鮮明だが `REJECT_LOW_RES`
  - `Sasha_v02_006.png`: `global_blurry;low_resolution_source;face_blurry`
  - `Sasha_v03_001.png`: 小物内の人の顔を含め face_count=2 となり `REJECT_MULTIPLE_FACE`。これは妥当と人間確認済み。
- `Sasha_v69` は白飛び・不鮮明・顔周り加工が強く、人間判断で動画全体を不採用。
- 既存の Human Review は正式 STEP3 CSV / Gate を変更せず sidecar として保存された。

## Why coordination failed

### 1. 「Revision」の意味が共有されていなかった

★maruの期待:
- 元ソースがあるため、既存STEP3を人間基準に近づける改善。
- 既知の問題を直し、実用的なLoRA素材選定へ近づける。

Chappy / Codex側で実際に進んだ内容:
- 既存Gateを変えずに再現性・監査性・lineage・reportを整える Revision 1。
- Threshold tuning / Gate validity は後段Human Calibrationへ延期。

結果:
- 「STEP3を改善している」つもりでも、品質判定ロジック自体は旧挙動のままだった。

### 2. Execution PASS と Algorithm PASS が混同された

Codex が報告する PASS は、
- 全件処理成功
- lineage保持
- report再生成
- reproducibility

を意味していた。

しかし★maruが必要としていた PASS は、
- 人間が良いと見る顔を残せる
- 人間が悪いと見る顔を落とせる
- LoRA顔学習用途として妥当

であり、意味が違った。

### 3. Reject側だけを先に見て False Reject を十分確認しなかった

25枚の Reject sample を見て妥当に見えたため、
「Reject Gate は概ね妥当」と早期に安心した。

しかし後から、
- `Sasha_v01_007.png`
- `Sasha_v01_013.png`
- `Sasha_v02_006.png`

のような「人間には使えるのに機械が落とす」False Reject が確認された。

今後は必ず、
- Reject側 precision
- Eligible側 false positive
- Reject側 false negative / false reject
の3方向を見る。

### 4. Source resolution を Face Quality の Hard Reject に置いた

元動画由来の native resolution が異なるため、
464x848 / 576x1024 / 1080x1920 などが混在する。

STEP1はnative dimensionsを保持してframe抽出するため、解像度差は正常な入力差。

しかし現行STEP3では `low_resolution_source` がHard Rejectになり、
顔crop自体が十分鮮明でも落ちるケースが発生した。

### 5. Codexの役割が「実装」から「本番実行」へ膨らんだ

本来:
- Chappy: architecture / STEP / evaluation設計
- Codex: BAT + Python 実装
- ★maru: 通常のfull batch実行 / Human Review

ところがPrompt内に
- run diagnostics
- regenerate outputs
- full dataset analysis
まで含めたため、Codexが本番処理まで担当した。

credit削減・決定論的運用という既存方針と矛盾した。

## Accepted lessons

1. 「STEP改良」と「監査・再現性改良」を別名で扱う。
2. Execution PASS / Algorithm validity / Human calibration を毎回分離して報告する。
3. Human calibration前のGateは「仮」であり、最終品質判定とみなさない。
4. A/B/C を使う。
   - A: clean / primary
   - B: borderline / reserve
   - C: reject
5. Bを残し、後段のPose/角度coverage不足時の補充候補にする。
6. low_resolution_source単独でCへ落とさない方向を再評価する。
7. Codexは原則BAT + Pythonを実装し、full batchを直接実行しない。
8. 調査 / audit / debugを明示的に依頼した場合のみCodex直接実行を許可する。
9. 1 Prompt = 1目的 = 1変更単位を守る。
10. STEP3が安定するまでSTEP4へ進めない。

---

## Additional incident: execution authority misread during reports backup

### Incident

★maru asked whether it was safe for ★maru to move the existing contents of
`output/reports` into `bkup`.

The wording included both:
- an action phrase ("すべてbkupに移動させて")
- a confirmation question ("こちらで行って問題ないですか？")

Codex interpreted the first part as a direct execution instruction and treated the
second part as a question about technical safety.

Codex then moved 55 items (32 files + 23 folders) from:

`C:\Users\maruk\Documents\Genelate_img\Sasha_re_codex\real_human_lora\output\reports`

to:

`output\reports\bkup\reports_archive_20261002_210730_647`

using PowerShell `Move-Item`.

### Why this was wrong

The user's intent was to ask whether ★maru could safely perform the move.

Codex failed to separate:
- "Is this operation safe?"
from
- "Are you authorized to perform it now?"

A technically reversible action is not automatically authorized.
A commentary message such as "移動します" is not approval from ★maru.

### Accepted corrective rule

For any user message phrased as a feasibility/safety/permission question:
- answer only
- do not mutate files
- STOP

If instruction-like text and a question are mixed in the same message,
do not perform the mutating action unless the execution subject and authorization
are unambiguous.

File/folder move, delete, overwrite, restore and bulk cleanup are all treated as
mutating operations requiring explicit execution authorization.

Reversibility or backup availability must never be used as a substitute for permission.
