# HIST-017 — STEP3: 4K移行からBEST Ranking v2.2へ

記録日：2026-10-05。アルゴリズムと測定尺度の変遷を記録する。現在の実務は[STEP3 BEST Knowledge](../knowledge/current/step3-best-ranking.md)。旧Decision・実験・判断を成功に見えるよう書き換えない。以下の数値・画像名は各時点の証拠で、汎用処理の定数/例外ではない。

## 1. 旧STEP3：絶対閾値を中心としたGate

旧native global Laplacian25、face Laplacian50、eye sharpness1.6、skin minima .050/.035、plasticity maximum45を使う設計は、技術的な測定と拒否理由を出す前提になっていた。旧2,001枚ではeligible62だった。[HIST-013](HIST-013_STEP3_FULL_FRAME_AUDIT.md)が検証したのは全行保持、旧判定との一致、再現性であり、LoRA適性のラベル精度ではない。

以前の素材に値が適していると見えた背景には既存処理結果と過去の画質仮説があった。しかし既存値で動くことや一部Reject例の納得だけでは妥当性を立証できなかった。[HIST-014](HIST-014_STEP3_CALIBRATION_REVIEW.md)・[HIST-015](HIST-015_STEP3_REJECT_BOUNDARY_REVIEW.md)は人間の許容境界を別工程として扱い、[HIST-016](HIST-016_STEP3_REVISION_A_DIAGNOSTICS.md)はA/B/C診断の部分実行と実行ownership訂正も保存している。当時の「有効」とする強い表現を、現在の検証済み精度と読み替えない。

## 2. 4K移行：尺度が変わり旧Gateが崩れた

[4K監査](../docs/STEP3_UPSCALE_RECALIBRATION_AUDIT.md)では旧71動画/2,001枚と新67動画/1,893枚を分け、共通67動画の旧1,893行を比較群とした。source lineageとsampling scheduleを照合したが、transcode前後の厳密なPTS/pixel一致までは証明しなかった。

共通群のnative global Laplacian medianは26.28→3.865、face Laplacianは14.304→4.735。実測眼のmedianは1.9345→0.8295、skin textureは0.057→0.022。native face50の位置は旧86.73%から新99.95%へ移り、正式eligibleは新世代で1/1,893になった。global_blurry1,806、face_blurry1,823、beauty_filter_detected939に対し、resolution/face-size理由は0になった。

観測は「native derivative尺度と拒否率が変わった」。解釈は「旧絶対閾値の移送が不適切」であり、数値低下だけから新画像の知覚品質悪化を断定しない。画像が見やすくなっていてもpixel尺度の変更で勾配値は下がり得る。upscaleが元にない顔情報を復元したとの証明もない。

## 3. canonical sharpness実験と歴史的severity移送

[canonical実験](../docs/STEP3_CANONICAL_SHARPNESS_RESULT.md)は原動画hashに一致する旧recipe再抽出を使い、保存native値との一致を確認した。旧PNG byteそのものの回収ではなく、同じsource/sample scheduleからの再構成である。global短辺720/1080、顔192/256/320を比較した。

顔canonical192ではLaplacianのNEW/OLD median比1.1374、Tenengrad1.0641となり、native比0.3303/0.1983より分布が近づいた。比較尺度の安定候補として192を選んだが、ROI/detection driftと残る分布差は消えなかった。

[閾値移送](../docs/STEP3_CANONICAL192_THRESHOLD_TRANSFER.md)は旧native50未満の1581/1823＝86.725178%を旧canonical分布へ移し、36.9013920732を導いた。Human labelでfitした値ではなく、歴史的なscalar拒否severityの移送である。旧/新の最終eligible数、同じframe判定、知覚的正しさを保存する方法ではない。

[DEC-0014](../knowledge/decisions/DEC-0014-canonical192-face-gate.md)と[canonical実装](../docs/STEP3_CANONICAL192_IMPLEMENTATION.md)ではnative blur/eye/skin/beautyを診断へ移しcanonical face Gateを採用した。当時の「本番未実施」は当時の記録として残る。

## 4. Human Review：尺度安定化だけでは意味的な判定を直せなかった

[DEC-0015](../knowledge/decisions/DEC-0015-eye-applicability-review-outputs.md)と[review gaps修正](../docs/STEP3_REVIEW_GAPS_IMPLEMENTATION.md)は、FULL_BODY labelだけで大きな実測顔の眼を評価対象外にする問題を修正した。別の診断BORDERLINEを追加し、公式eligibility/A-B-Cと分離した。その後の[Gate summary](../docs/STEP3_FACE_QUALITY_SUMMARY.md)は正式1,893行、eligible139、PASS51/BORDERLINE88/REJECT1754を記録する。これは後のBEST1,951行とは異なる出力である。

人間観測では使用可能な眼がheuristicで落ちる一方、眼の開き/髪の遮蔽、motion blur、暗さや白い霞と保存数値の不一致が残った。後の[DEC-0019](../knowledge/decisions/DEC-0019-general-eye-quality-best-v21.md)・[DEC-0020](../knowledge/decisions/DEC-0020-balanced-critical-quality-best-v22.md)が反例を具体的に記録する。`one_eye_occluded`や測定VALIDという名称を意味的な真値とみなす誤りが問題になった。

画像例への人間疑義と原因確定は分ける。v05_003には眼測定疑義があるが、真の眼ROI座標等がなく測定不具合と断定できない。v08の眼/髪 concernとv19の視覚的hazeも、機械因子を人間の拒否理由に置き換えられない。尺度の安定化だけでは「不良を完全に二値Rejectする」目的を達成できず、ランキングへ責務を移した。

## 5. BEST candidate rankingへの転換

[DEC-0016](../knowledge/decisions/DEC-0016-best-candidate-ranking.md)は複雑なReject設計から、最小fatalとBEST候補順位へ転換した。後段pose、重複、identity、選定、Human Reviewを残すことで、STEP3にあらゆる欠点の完全検出を背負わせない。正式動画と追加静止画を共通監査に含め、レビューを独立した表示工程にした。

これは「再現可能なRejectを増やす」から「良い候補を上位に並べ、後段と人間で吟味する」への設計変更であり、単なるインフラ改善ではない。

## 6. best_rank_v1：relative percentileを欠点へ変換した失敗

v1はkindごとのrelative scoringを使ったが、percentileの低さからblur/遮蔽/clipping等の強さを作り、品質の高い追加静止画にも根拠のない減点を与えた。[DEC-0017](../knowledge/decisions/DEC-0017-best-ranking-evidence-penalties.md)と[v2実装の比較](../docs/STEP3_BEST_RANKING_V2_IMPLEMENTATION.md)には、参照静止画652794808…のv1 score41.002473、減点23.853765が残る。

同kindの他画像より低い値は、実際の欠点を意味しない。kindごとのpercentileだけではvideo/still間の実際の品質差も失われる。この二つを修正対象とした。

## 7. best_rank_v2：共通quality、positive bonus、実測evidence

v2は共通positive尺度＋小さなkind内relative bonusと、実測条件に根拠を持つsoft penaltiesへ変更した。参照静止画の少数例計算は88.436829、penalty0となったが、新global rankや全体品質改善の証明ではなかった。[v2実装](../docs/STEP3_BEST_RANKING_V2_IMPLEMENTATION.md)

review restartには途中訂正があった。DEC-0017の初期履歴方針を[DEC-0018](../knowledge/decisions/DEC-0018-version-scoped-best-review.md)が置換し、旧v1 Round1/2 shownで新v2候補を除外せず、新版Round1から再開することを確定した。旧判断は回帰証拠として保持し、新スコアのfeatureにしない。レビューcapやstill最低希望はtraining quotaではない。

## 8. best_rank_v2.1：generic eye qualityと残る補償問題

[v2.1実装](../docs/STEP3_BEST_RANKING_V21_IMPLEMENTATION.md)と[DEC-0019](../knowledge/decisions/DEC-0019-general-eye-quality-best-v21.md)は左右眼を分離し、openness/obstruction/reliabilityを区別、期待眼の弱い側を用いた。profile far eyeの除外も導入したが、ROI投影による期待眼は未検証のheuristicだった。Human Reject、filename、sourceをruntimeに入れなかった。

残った問題は、additiveなsharpness/contrast等の加点がcriticalな眼/blur弱点を補償する構造である。眼状態の測定自体、v05 ROI、v19 hazeも未解決で、無根拠の新Tenengrad/mouth/haze境界を作らずSTOPした。測定が不十分な反例を重みだけで押し下げる解法にはしなかった。

## 9. best_rank_v2.2：balanced critical quality

[DEC-0020](../knowledge/decisions/DEC-0020-balanced-critical-quality-best-v22.md)と[v2.2実装](../docs/STEP3_BEST_RANKING_V22_IMPLEMENTATION.md)はbase qualityにeye/detail/exposure/reliabilityの等重みgeometric meanを掛け、残るgeometry concernを引く構造を採用した。critical品質を持ち上げるsqrt代案は少数比較で退けた。global face detail×local medianとし、局所edgeだけで弱い顔全体を救済させない。

良い画像の不必要な減点を避けるため、顔サイズ/有用contrastを飽和させ、照明非対称をvisibility損失へ変換する旧経路をranking上で訂正した。raw値、旧版コード、Human判断は残した。画像名によるboost/blacklistはない。少数9例とsynthetic111＋config8 tests等が[実装時verification](../docs/STEP3_BEST_RANKING_V22_VERIFICATION.json)の範囲であり、本番実行証拠とは別である。[回帰比較JSON](../docs/STEP3_BEST_RANKING_V22_REGRESSION.json)

P95 detail scalingは比較品質で物理blur閾値ではない。visual hazeの解決、眼ROI真値の立証は実装しなかった。これらをv2.2の成功として記録しない。

## 10. 本番Human Reviewとbaseline freeze

[2026-10-05 Chappy報告](../docs/STEP3_BEST_RANKING_V22_ROUND1_3_CHAPPY_REPORT.md)は★maruによる本番結果を確認した。全1,951＝正式1,893＋静止画58、ranking eligible1,880、fatal71。3 rounds×45＝135、同版frame重複なし。Round1/2 Reject0、Round3 Reject4であり、初報の3枚との差は★maruが「4枚すべてReject」と確認した。

| Human Reject | global rank | 今回の理由記録 |
| --- | ---: | --- |
| Sasha_v05/Sasha_v05_003.png | 85 | 未記入 |
| Sasha_v08/Sasha_v08_004.png | 129 | 未記入 |
| Sasha_v08/Sasha_v08_018.png | 146 | 未記入 |
| Sasha_v08/Sasha_v08_008.png | 150 | 未記入 |

動画soft capは4/動画/**Round**で緩和なし。表示集合はglobal top135ではなく、Round3ではglobal rank146/150も含んだ。Round3のstillsは残る8枚を使い最低希望10に2枚不足した。samplingと順位品質を分けて解釈する。135枚中4Rejectは全1,951枚のprecisionを表さず、残り131履歴PENDINGも正式ACCEPT/Aではない。

旧v2.1反例v08_011は99→156、v19_024は134→321へ移り未表示、v08_004は104→129で再Reject、v05_003は92→85で再Rejectだった。4件という件数はv2.1と同じで、「Rejectが減った」とは言えない。v19の順位低下もhaze検出成功ではない。

本番報告時点には次の判断をChappyへ依頼していた。その後★maruがChappyのSTEP3 OKを報告し、今回のKnowledge化依頼も「v2.2を実用baselineとしてfreezeしSTEP4へ進む」と明示した。この後続project judgementを現在状態として記録する。rank85の一例を落とすため際限なく調整せず、既知限界を残して後段へ進む判断であり、全体精度認定や最終採用ではない。実装時DEC-0020の本番pending文も、本番報告の当時の判断待ちも書き換えない。

## 11. 別の被写体にも引き継ぐ教訓

- 再現性はアルゴリズムの妥当性を証明しない。canonical測定安定性も知覚的真値を証明しない。
- percentileは比較に使い、実際の欠点のseverityへ自動変換しない。native閾値はdomain変更後に再検討する。
- Human反例から一般的な測定/aggregationを直す。名前・動画・過去Rejectのblacklistでgeneric pipelineを最適化しない。
- 残る反例の順位、レビューsampling、後段の検証範囲を踏まえて実用baselineをfreezeする。単一の低順位例に合わせた無根拠の閾値を加えない。
- 眼ROI、profile可視性、white haze、物理blur校正など、未解決事項を隠さず後続要件へ渡す。最終LoRA適性は後段とHuman Reviewに残す。

実行主体/Revision意味の共有失敗は別の[Coordination History](HISTORY_2026-10-02_STEP3_COORDINATION_BREAKDOWN.md)に保存されている。本書ではその時系列を重複させない。
