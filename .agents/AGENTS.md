# Agent Operating Guidelines (AGENTS.md)

This repository incorporates a structured **Development Memory & Knowledge System**.  
As an AI coding agent or human developer working here, you must operate according to these systematic guidelines to avoid repeating past failures.

---

## 1. Core Operating Philosophy: "Do Not Repeat Past Failures"

In computer vision, face detection, and LoRA training, optimal parameters and algorithms shift with resolution, lighting, and compression.  
**Recording only the currently successful steps causes developers to repeat the exact same trial-and-error whenever conditions change.**

This repository preserves:
- **Current Knowledge**: What is currently validated and recommended.
- **Decisions (ADRs)**: Why specific approaches were adopted or superseded.
- **Failures**: What was tried, why it failed, and explicit "Do Not Retry Unless" conditions.
- **Cases / Counterexamples**: Concrete inputs that broke existing heuristics.
- **Experiments**: Empirical observations separated from subjective interpretations.

---

## 2. Information Retrieval Hierarchy

When tasked with investigating, modifying, or extending code, traverse documents in this exact order:

```text
1. knowledge/current/         (What is currently the active standard)
2. knowledge/decisions/       (ACCEPTED decisions and architectural context)
3. knowledge/cases/           (Edge cases and counterexamples that shaped rules)
4. knowledge/failures/        (Failed attempts - CHECK BEFORE PROPOSING CHANGES)
5. experiments/               (Raw empirical data and observed metrics)
6. SUPERSEDED Decisions       (Historic context only - DO NOT use as active specs)
```

---

## 3. Workflow Protocol

### Phase 1: Before Implementation
1. **Check Current Knowledge**: Read the relevant file in `knowledge/current/`.
2. **Search Past Failures**: Grep or review `knowledge/failures/`.
   - *Example*: Before suggesting "Let's run CodeFormer on all selected images to improve sharpness", you will find `FAIL-0001`, which proves whole-face CodeFormer destroys natural skin pores and causes plastic overfitting.
3. **Inspect Counterexamples**: Check `knowledge/cases/` to understand known edge cases.
4. **Verify Boundary Conditions**: Confirm whether the user's current input conditions match the validated envelope.

### Phase 2: During Implementation
1. Maintain **fact vs. interpretation separation**:
   - `Fact`: "Image `Sash_v5_013` had a Tenengrad score of 185.0 and skin texture score of 4.2."
   - `Interpretation`: "Aggressive beauty-smoothing algorithm destroyed mid-frequency pores while sharp edge filters artificially inflated gradient metrics."
2. Tag new observations as potential Counterexamples or Failure Modes.
3. Never use magic numbers without linking to a Decision (`DEC-xxxx`) or documenting the rationale.

### Phase 3: After Implementation or Experiment
Evaluate whether the Knowledge System requires updating:
- **Update Required When**:
  - A new architectural or threshold decision was accepted (`knowledge/decisions/`).
  - An existing decision was superseded (`supersedes:` tag).
  - A new failure mode or edge case was discovered (`knowledge/failures/` or `knowledge/cases/`).
  - Empirical validation bounds shifted (`knowledge/current/`).
- **Do NOT Update When**:
  - Trivial refactoring, formatting, comment edits, or cosmetic adjustments.

---

## 4. Confidence Ratings

Assign appropriate confidence levels to all recorded insights:
- **HIGH**: Validated across hundreds/thousands of real samples across multiple video sources.
- **MEDIUM**: Observed and verified across multiple test samples with consistent behavior.
- **LOW**: Observed on single isolated edge case or theoretical hypothesis awaiting wider validation.

---

## 5. Skills Integration
Use the specialized skill `.agents/skills/knowledge-maintenance/SKILL.md` when asked to:
- Document new experiment findings
- Author architectural decision records (ADRs)
- Catalog failure modes and counterexamples
- Synchronize current policy documents
