# STEP3 upscale recalibration audit

分析／校正検討のみ。CSV/metadataの読取りで作成。閾値・数式・画像・A/B/Cを変更していません。

## Observed data — 正式世代と比較可能性

- OLD: 2,001 frames / 71 videos; generation `fc2a37abc81e44e456891ac7d268c2dc622255d120c944ac377dbefd491833c2`.
- NEW: 1,893 frames / 67 videos; generation `bd72f194f62260fb728b77b26c75c5491b178908bff53393e197c11137bf9a40`.
- OLD matched67: 現在残る同じ67動画の1,893行。OLDから除外される旧動画: Sasha_v02, Sasha_v18, Sasha_v43, Sasha_v69。
- 追加静止画58枚は両世代の正式STEP3比較に含めません。
- 両STEP3 CSVのSHA256を各summaryと照合。summaryが指定するSTEP2 CSVも取得してSHA256・世代・全列継承を確認。
- 移行記録のoriginal/upscaled source hashを旧・現video manifestと照合。元filename/video ID、各動画の正式枚数、抽出policy/FPS、frame ID/temporal indexが共通群で一致。
- duration文字列表記が異なる動画数: 12。
- 安全に確認できるのは同じsource lineageとsampling scheduleに基づく比較群です。transcodeの厳密なPTS/frame内容同一性は証明していません。同名frameを同一pixel/timeと断定せず、共通動画群の分布比較を主証拠とします。
- CSV値は保存時の丸め済み値。欠測空欄を除外し、補完せず、各表にNと欠測数を明示。線形補間によるnumpy percentileを使用。

### 指標分布

| Metric | Cohort | N | Blank | min | P10 | P25 | P50 | P75 | P90 | P95 | P99 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| laplacian_score | OLD all | 2001 | 0 | 1.266 | 5.598 | 9.501 | 27.021 | 97.97 | 244.22 | 632.503 | 938.078 |
| laplacian_score | OLD matched67 | 1893 | 0 | 1.266 | 5.469 | 9.232 | 26.28 | 99.125 | 253.8568 | 669.4306 | 940.6976 |
| laplacian_score | NEW | 1893 | 0 | 0.499 | 1.9274 | 2.558 | 3.865 | 6.069 | 15.514 | 22.95 | 111.2798 |
| face_laplacian_score | OLD all | 1924 | 77 | 2.3 | 6.3791 | 8.6378 | 15.0265 | 31.576 | 60.6552 | 93.9269 | 169.6396 |
| face_laplacian_score | OLD matched67 | 1823 | 70 | 2.403 | 6.3172 | 8.4925 | 14.304 | 29.503 | 58.6526 | 92.7473 | 169.286 |
| face_laplacian_score | NEW | 1824 | 69 | 1.811 | 3.2 | 3.833 | 4.735 | 6.2165 | 8.6459 | 10.2657 | 19.2328 |
| eye_sharpness | OLD all | 1719 | 282 | 0 | 0 | 0 | 0 | 1.752 | 2.823 | 3.274 | 4.4507 |
| eye_sharpness | OLD matched67 | 1640 | 253 | 0 | 0 | 0 | 0 | 1.7125 | 2.735 | 3.1985 | 4.4947 |
| eye_sharpness | NEW | 1645 | 248 | 0 | 0 | 0 | 0 | 0.741 | 1.006 | 1.2116 | 1.6956 |
| skin_texture_score | OLD all | 1719 | 282 | 0.003 | 0.024 | 0.036 | 0.058 | 0.126 | 0.3272 | 0.6001 | 1.6923 |
| skin_texture_score | OLD matched67 | 1640 | 253 | 0.003 | 0.024 | 0.035 | 0.057 | 0.122 | 0.3161 | 0.585 | 1.6846 |
| skin_texture_score | NEW | 1645 | 248 | 0.001 | 0.012 | 0.016 | 0.022 | 0.033 | 0.051 | 0.0758 | 0.148 |
| plasticity_ratio | OLD all | 1719 | 282 | 0 | 0 | 0 | 0 | 26.1 | 49.54 | 65.52 | 108.646 |
| plasticity_ratio | OLD matched67 | 1640 | 253 | 0 | 0 | 0 | 0 | 25.85 | 49.5 | 65.51 | 107.854 |
| plasticity_ratio | NEW | 1645 | 248 | 0 | 0 | 0 | 0 | 29.4 | 46.52 | 58.18 | 97.616 |

### 現production閾値と百分位位置

位置は `100×count(value < threshold)/N / 100×count(value <= threshold)/N`。両値の幅は同値・丸めの影響です。
下限Gateでは左側が概ね失敗領域、plasticity上限Gateでは右側の100との差が超過領域。適用対象外や他Gateの評価順序は別扱いです。

| Metric / applicability | Threshold | OLD position % (< / <=) | OLD matched67 position % | NEW position % |
| --- | ---: | ---: | ---: | ---: |
| laplacian_score / all frames | 25 | 47.63 / 47.63 | 48.34 / 48.34 | 95.40 / 95.40 |
| face_laplacian_score / detected face; face blur branch | 50 | 85.60 / 85.60 | 86.73 / 86.73 | 99.95 / 99.95 |
| eye_sharpness / non-FULL_BODY; mesh/eye validity required | 1.6 | 70.62 / 70.62 | 71.83 / 71.83 | 98.66 / 98.66 |
| skin_texture_score / CLOSE_UP minimum | 0.05 | 41.88 / 43.57 | 43.05 / 44.70 | 89.60 / 89.79 |
| skin_texture_score / UPPER_BODY minimum | 0.035 | 23.33 / 24.78 | 24.15 / 25.61 | 77.26 / 78.66 |
| plasticity_ratio / CLOSE_UP / UPPER_BODY maximum | 45 | 87.67 / 87.73 | 87.93 / 87.99 | 89.12 / 89.12 |

上表のskin/plasticity位置は全非欠測値の位置であり、FULL_BODYを含む分布です。実Gateの適用範囲は次表で分離します。

### 適用範囲と構造的zero

eye_sharpnessとplasticity_ratioの0は、既存の眼存在Gateによる計算無効化を含みます。0を「実測された強いblur」と同一視しません。

| Cohort | eye actually measured | disabled eye-presence | missing landmarks | no face |
| --- | ---: | ---: | ---: | ---: |
| OLD all | 728 | 991 | 205 | 77 |
| OLD matched67 | 684 | 956 | 183 | 70 |
| NEW | 646 | 999 | 179 | 69 |

| Metric / measured eye only | Cohort | N | min | P10 | P25 | P50 | P75 | P90 | P95 | P99 | Threshold position % |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| eye_sharpness | OLD all | 728 | 0.753 | 1.228 | 1.4945 | 1.9885 | 2.7663 | 3.4086 | 3.9998 | 4.996 | 30.63 / 30.63 |
| eye_sharpness | OLD matched67 | 684 | 0.753 | 1.219 | 1.4572 | 1.9345 | 2.7062 | 3.3277 | 4.0236 | 5.037 | 32.46 / 32.46 |
| eye_sharpness | NEW | 646 | 0.325 | 0.559 | 0.6853 | 0.8295 | 1.0117 | 1.295 | 1.4825 | 1.8399 | 96.59 / 96.59 |
| plasticity_ratio | OLD all | 728 | 0.6 | 7.3 | 17.8 | 31.2 | 48.25 | 71.65 | 88.33 | 121.095 | 70.88 / 71.02 |
| plasticity_ratio | OLD matched67 | 684 | 0.6 | 6.96 | 18 | 31.3 | 48.5 | 71.85 | 88.005 | 120.255 | 71.05 / 71.20 |
| plasticity_ratio | NEW | 646 | 2.6 | 18.1 | 25.1 | 35.5 | 46.675 | 63.85 | 83.975 | 107.765 | 72.29 / 72.29 |

| Cohort | Shot | all N | skin numeric N | median skin | skin threshold | skin below % | plasticity >45 % | authoritative beauty reasons |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OLD all | CLOSE_UP | 325 | 325 | 0.045 | 0.05 | 57.85 | 9.23 | 191 |
| OLD all | UPPER_BODY | 792 | 782 | 0.051 | 0.035 | 26.60 | 15.86 | 268 |
| OLD all | FULL_BODY | 807 | 612 | 0.095 | N/A (skipped) | N/A | N/A | 0 |
| OLD matched67 | CLOSE_UP | 323 | 323 | 0.045 | 0.05 | 57.89 | 8.98 | 190 |
| OLD matched67 | UPPER_BODY | 752 | 743 | 0.05 | 0.035 | 27.46 | 15.61 | 258 |
| OLD matched67 | FULL_BODY | 748 | 574 | 0.0925 | N/A (skipped) | N/A | N/A | 0 |
| NEW | CLOSE_UP | 315 | 315 | 0.017 | 0.05 | 99.05 | 13.65 | 312 |
| NEW | UPPER_BODY | 759 | 749 | 0.021 | 0.035 | 83.18 | 12.42 | 627 |
| NEW | FULL_BODY | 750 | 581 | 0.031 | N/A (skipped) | N/A | N/A | 0 |

皮膚<閾値 OR plasticity>45がbeauty判定条件。FULL_BODYはbeauty rejection対象外。metricの空欄・shot未分類は分母から区別。保存時丸めからの分岐再構成は参考値で、最終拒否数はCSV reasonを正とします。

### 拒否・eligible率（全正式行を分母、重複理由を別々に数える）

| State | OLD all | OLD matched67 | NEW | NEW minus matched OLD (pp) |
| --- | ---: | ---: | ---: | ---: |
| global_blurry | 953/2001 (47.63%) | 915/1893 (48.34%) | 1806/1893 (95.40%) | +47.07 |
| face_blurry | 1691/2001 (84.51%) | 1622/1893 (85.68%) | 1823/1893 (96.30%) | +10.62 |
| beauty_filter_detected | 459/2001 (22.94%) | 448/1893 (23.67%) | 939/1893 (49.60%) | +25.94 |
| low_resolution_source | 281/2001 (14.04%) | 242/1893 (12.78%) | 0/1893 (0.00%) | -12.78 |
| face_too_small | 26/2001 (1.30%) | 17/1893 (0.90%) | 0/1893 (0.00%) | -0.90 |
| eligible | 62/2001 (3.10%) | 55/1893 (2.91%) | 1/1893 (0.05%) | -2.85 |

### ピクセルスケールと実装上の条件

- 同名抽出scheduleのmedian NEW/OLD width=2×、height=2×、顔bbox width=2.0158×、height=2.0153×。全動画が同じ倍率とは仮定しません。
- global/face Laplacian: native pixel grid上のLaplacian variance。固定pixel kernelを使用し、共通の顔解像度へ正規化しない。
- eye: Sobel gradientのP90 / (patch std + 1e-4)。contrast normalizationはspatial scale normalizationではない。
- skin: cheek radius=max(int(face min dimension×0.07),6)、Laplacian variance / max(mean brightness,10)。輝度正規化でありpixel-scale正規化ではない。
- plasticity: eye_sharpness / max(skin_texture_score,0.005)。分子・分母のscale changeが相殺/増幅し得る。
- face_blurryはnon-FULL_BODYでeye<1.6を先に評価し、elifでface Laplacian<50。FULL_BODYはeye基準を使わずface Laplacianを使う。reasonだけからeye/face寄与を独立に足せない。

## Inference — データからの解釈（因果・正解ラベルとは分離）

| Metric | Material scale change? | Threshold interpretation |
| --- | --- | --- |
| laplacian_score | YES: matched median 26.28→3.865; NEW/OLD 0.147× | 25は旧matched P48.34→新P95.40。coarse global Gateがほぼ上位4.6%だけを許可し、実効的に非常に厳しい。 |
| face_laplacian_score | YES: matched median 14.304→4.735; NEW/OLD 0.331× | 50は旧matched P86.73→新P99.95。測定顔1,824件のうちほぼ全件が基準未満。scale不整合の強い候補。 |
| skin_texture_score | YES: matched median 0.057→0.022; NEW/OLD 0.386× | 0.05/0.035は新CLOSE_UP/UPPER_BODYの測定値の99.05%/83.18%が閾値未満。beauty増加の主な数値要因である可能性が高い。 |
| eye_sharpness | YES: measured-only median 1.9345→0.8295 (0.429×). all-value median zeroはscale比較に不適 | 1.6は実測群でもより厳しくなる。眼存在Gate無効化との混同は禁止。 |
| plasticity_ratio | 単一倍率の大幅崩壊とは言えない。P75は少し増加、P90/P99は低下し、max45超過率は全非欠測値で12.27%→10.88% | 45の過剰厳格化がbeauty拒否増加の主因という証拠はない。優先的に引き上げる根拠なし。 |

- 4動画を除外したmatched cohortでも大幅なsharpness/texture低下が残るため、動画削除だけでは崩壊を説明できない。
- 固定pixel derivativeとupscale/補間/再圧縮によるspatial-frequency変化との不整合が有力。ただしupscaler固有のsmoothing、codec、detector/bbox/landmarkの変化も共変し、CSVだけで原因割合を確定できない。
- low_resolution_source/face_too_smallが0になったのはdimension Gateを満たした観測事実。元のidentity/眼/皮膚情報が回復した証拠ではない。旧結果も正解ラベルではなく、OLD eligible率を復元すること自体は品質目標にならない。
- 新beauty flagは加工の実使用の証明ではない。新たに939枚にbeauty加工が施されたと解釈しない。

## Recommended calibration targets — 検討候補のみ、採用・変更は禁止

優先順: face/global pixel scale対応、shot別skin texture、実測眼指標、plasticityの識別能力確認。
下表は同じOLD matched67の閾値CDF位置に対応するNEW quantileを示す統計アンカーであり、推奨production閾値ではありません。旧Gateの誤判定を継承するため、そのまま設定しないでください。

| Diagnostic review target | OLD current threshold | OLD matched below/equal percentile | NEW quantile anchor |
| --- | ---: | ---: | ---: |
| global | 25 | 48.34% | 3.775 |
| face | 50 | 86.73% | 7.852 |
| eyes actually measured | 1.6 | 32.46% | 0.7267 |
| skin CLOSE_UP | 0.05 | 59.44% | 0.02 |
| skin UPPER_BODY | 0.035 | 29.74% | 0.017 |

1. 人間が同じsourceのupscale前後で顔・眼・skin detailを確認する境界レビューを設計。数値の大小とLoRA適性を分け、shot別・native resolution別にgood/badのラベルを収集する。今回レビュー生成・画像判定は行っていません。
2. 将来の検討では、顔/眼/cheek評価のcanonical pixel scale、native source解像度での測定、複数scaleでの安定性を比較する。これは別のalgorithm/calibration revisionであり、今回はresize・再測定・formula変更をしない。
3. skin 0.05/0.035とface/global基準はpixel-scale dependenceを先に検証。眼はmeasured/disabled/missingを分離し、0を小さい新閾値で救済しない。
4. plasticity上限45は単独では優先変更しない。skin floor0.005とeyepresenceによる0、shot別適用範囲も含め、加工あり/なしラベルで識別能力を検証する。
5. cutoff校正の目標は人間ラベルに対するfalse reject/false acceptとidentity/detail保持。最終枚数・coverageを満たすためにGateを緩めることを校正目的にしない。

## Source artifacts and minimum validation

各source fingerprintは作成前後で同一を確認。CSV統計のみ、画像デコード・inferenceなし。min/percentileの単調性、unique frame identities、67動画cohort、counts/reason totals、閾値一致を確認。

- `config/config.yaml` — SHA256 `0ef51e4416382bbecfafa4cc95439f4f352bc8d0b0b7ff3f3336df54c5ef1388`
- `docs/bkup/pre_upscale_20261002_223607/STEP3_VERIFICATION.json` — SHA256 `3179776e198ef13eda64d7bcbdd0e53f290c195a2b45398b13ed5d46dc1f3c10`
- `output/reports/bkup/reports_archive_20261002_210730_647/step3_dataset_report.csv` — SHA256 `2589176c4a2eb22d098a1f97500654cde0e0ce6dfda0873cdeac25893f6b0051`
- `output/reports/bkup/reports_archive_20261002_210730_647/step3_summary.json` — SHA256 `49ea1a875ca5e14b7716119c827c4c1b512bcefc09cf321d6b700f141b72ec5a`
- `output/reports/bkup/step2_previous_20261002_210446_980/step2_dataset_report.csv` — SHA256 `a133656bf487f1d1c7f1add08e5943420254ca8270c499b3a87ce2a4b5602a63`
- `output/reports/bkup/step2_previous_20261002_210446_980/step2_summary.json` — SHA256 `32798c634e31c24ca62397644e3dd51dfa8218da2babe9ccc582cac7710803bc`
- `output/reports/step2_dataset_report.csv` — SHA256 `23115e15a8bd5869646c98b23422ac0c0f742f78f91bfcbb3bf7f4f13287d060`
- `output/reports/step2_summary.json` — SHA256 `cded36ee99d2773093f50376b02a9ae3537f498f4fbfa9b0f52dd6073560ac85`
- `output/reports/step3_dataset_report.csv` — SHA256 `de7d772bba8017fb4079698864539ab274452347db74ecf3e8624454d129523d`
- `output/reports/step3_summary.json` — SHA256 `286dc3ec86146cb03e7d4e40cb7460d13c812651202ef2e4684e197338f59099`
- `work/manifests/step1_summary.json` — SHA256 `209d695d14808a7a7c66e279d8f07ab351cba247de165ceda7493f75d9932c9c`
- `work/manifests/step1_upscale_transition.json` — SHA256 `2a2027932cc2b1c08eb79026cef56986b8c5ba98b6ef9694cacee3cbe89c0634`
- `work/manifests/video_extraction.csv` — SHA256 `23d3598e05641a331c4cb65d0d332a1871f237afe1d466db05cbef8cdd977f86`
- `work/manifests/video_manifest.csv` — SHA256 `eb1d98529d6508bb8f7f3eb61c764b8886c270f8bed9cf6f91f1894d5b5d4340`
- `work/videos_previous/upscale_92dd538644254cd898215d47a74bc02e/step1_summary.json` — SHA256 `329980bb1a93c9462347e3c23200f81e4d8aa0a539b13b7f9b1105124c2d2b1d`
- `work/videos_previous/upscale_92dd538644254cd898215d47a74bc02e/video_extraction.csv` — SHA256 `57a376fcd0c853c26e9b5539817e77a7268498c1e4a5fda126eb0257ffc516e9`
- `work/videos_previous/upscale_92dd538644254cd898215d47a74bc02e/video_manifest.csv` — SHA256 `7403d756038830417385e1bbf6a84e7245c65257442e813a6c6e187670c03e82`

Rules checked: AGENTS.md/.agents/AGENTS.md, PROJECT, pipeline/data-lineage rules, relevant current knowledge, DEC-0002/0003/0010 and failure/case/history evidence.
Data lineage preserved: YES (source mapping/digest validated). Full-row preservation: YES for analysis coverage of OLD2,001/NEW1,893; matched subset explicitly labeled, no CSV edits. Historical evidence preserved: YES. Config SSOT preserved: YES.
Only created: docs/STEP3_UPSCALE_RECALIBRATION_AUDIT.md. Documentation checked; no other documentation, Decisions or source artifacts updated by explicit analysis-only scope.
Not changed: config thresholds, STEP3 formulas/production code/CSV, Revision A, STEP4+, source images, Human Review/A/B/C. No production PASS beyond stored observed outputs claimed.
Full batch executed: NO. No commit/push.
