# KNOWLEDGE — STEP3 Face Quality / Human Calibration / Execution Policy

> Historical generation/algorithm snapshot: the STEP3 counts and Gate boundaries
> below describe Revision1 and subsequent calibration at that time, not current
> BEST v2.2. Execution ownership remains applicable. For current state and completed
> production/review evidence, see [STEP3 BEST Knowledge](step3-best-ranking.md).
> The original observations and policies below are preserved.

## Current STEP3 truth

STEP3 の責務は Face Quality / face-region diagnostics。

STEP3 Revision 1 の PASS は
「2,001 frameを再現可能に処理できた」という意味であり、
現在のGateがLoRA学習素材として正しいことを保証しない。

現行結果:
- total: 2,001
- eligible: 62
- rejected: 1,939
- rejection rate: 96.90%

この比率自体を目標値として調整してはいけない。

## Human-grounded issues discovered

### False Positive

自動OKに残るが、人間にはLoRA顔学習素材として不適:
- blink / half-open eyes
- white clipping / overexposure
- strong smoothing / processing
- face detail loss

### False Reject

人間にはLoRA顔学習素材として使用可能だが機械Reject:
- native source resolutionのみでReject
- Laplacianが人間視覚と一致しないケース
- detector heuristicが別物体の顔を拾うケースは内容を確認する

Known examples:
- Sasha_v01_007.png -> REJECT_LOW_RES, source short edge 464
- Sasha_v01_013.png -> REJECT_LOW_RES, source short edge 464
- Sasha_v02_006.png -> REJECT_LOW_RES + global_blurry + face_blurry, source short edge 576
- Sasha_v03_001.png -> REJECT_MULTIPLE_FACE; 小物内に別人物の顔があり、人間確認でReject妥当

## Source resolution rule

STEP1 frame extraction preserves the native video dimensions.
It does not normalize/rescale every video to the same resolution.

Therefore different MP4 sources naturally produce:
- 464 x 848
- 576 x 1024
- 1080 x 1920
etc.

Low source resolution is a risk signal, not automatically proof that the face crop is unusable.

Future STEP3 design should evaluate:
- face crop pixel size
- face Laplacian / local detail
- eye information
- visibility
- clipping
- texture / local contrast

before deciding A/B/C.

## Selection state

All LoRA candidate review should use three states:

### A — CLEAN / PRIMARY
Face Quality的に問題がない。
後段の候補選定で優先。

### B — BORDERLINE / RESERVE
少し弱いがHuman Reviewで使用可能。
Pose/angle/composition coverage不足時の補充候補。

### C — REJECT
LoRA顔/Identity学習に不適。
明確な多人数、破綻、強い白飛び・加工、重度blurなど。

BをA/Cへ自動的に潰さない。

## Revision A scope

次のdiagnosticを追加する:
- Eye Openness
- highlight clipping / overexposure
- face local detail / local contrast

最初はdiagnostic-only。
Human calibration前に新thresholdをHard Gateにしない。

## Review order

1. Known human anchors
2. Borderline samples near threshold
3. Single-Gate failures
4. False Reject examples
5. False Positive examples
6. Threshold proposal
7. ★maru approval
8. Codex implementation

## Codex execution policy

Default:
- Codex writes/updates Python.
- Codex writes/updates BAT entrypoint.
- Codex runs only minimum validation needed to prove implementation works.
- ★maru runs normal full-dataset batch processing.

Codex may directly execute more broadly only when ★maru explicitly requests:
- investigation
- audit
- debug
- data inspection
- full execution

A prompt that says "implement" must not silently be interpreted as "implement and run the full production dataset".

## Actor contract

### ★maru
- Human quality standard
- Calibration labels
- final acceptance
- normal BAT execution

### Chappy
- STEP definition
- architecture
- evaluation design
- Codex prompt scope
- interpretation of machine vs human disagreement

### Codex
- deterministic implementation
- BAT / Python
- minimum verification
- report exact measurements
- STOP at requested boundary

## Mandatory handoff format

Every Codex task should end with:

- Changed:
- Not changed:
- Minimum validation:
- Full batch executed: YES/NO
- Human review required:
- Current STEP status:
- STOP reason:

This prevents "implementation completed" from being mistaken for "STEP quality validated".

---

## Execution authority rule

### Safety/feasibility question is NOT execution authorization

The following are read-only questions unless ★maru explicitly authorizes execution:
- こちらで行って問題ないですか？
- 実行してよいですか？
- この方法で大丈夫ですか？
- 移動しても平気？
- 削除していい？
- 上書きして問題ない？

Correct behavior:
1. Explain whether the operation is safe / appropriate.
2. State risks.
3. STOP.
4. Wait for explicit execution authorization.

### Mixed instruction + question

If one message contains both an action phrase and a confirmation question,
do not assume Codex is the executor.

When the executor is ambiguous:
- do not mutate
- answer the question only
- wait for explicit execution authorization if needed

### Mutating operations covered

This applies to:
- file/folder move
- delete
- overwrite
- rename
- restore
- backup cleanup
- bulk organization
- report relocation
- source replacement

### Reversibility is not permission

Reversible / backed up / hash-verified / low-risk does not grant execution authority.

### Commentary is not consent

"移動します" / "実行します" is only an announcement, not user approval.

Required default when ambiguous:
`READ / EXPLAIN / STOP`
