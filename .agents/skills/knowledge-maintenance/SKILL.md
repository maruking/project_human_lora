---
name: knowledge-maintenance
description: Systematic maintenance and retrieval of repository development memory, including decisions, experiments, failures, and counterexamples.
---

# Knowledge Maintenance Skill

Use this skill when tasked with recording, updating, auditing, or investigating architectural decisions, failure records, empirical experiments, or counterexamples in this repository.

---

## 1. Trigger Queries
Activate and follow this skill when handling instructions such as:
- *"この実験結果をKnowledge化して"* (Convert experiment results into Knowledge)
- *"今回の変更をDecision Recordに残して"* (Record this change in an ADR)
- *"Failureとして記録して"* (Record this as a Failure)
- *"Current Knowledgeを更新して"* (Update Current Knowledge)
- *"過去に似た失敗がないか調べて"* (Investigate past similar failures)
- *"この設計がなぜこうなっているか調べて"* (Trace why this design was chosen)
- *"このDecisionのhistoryを追って"* (Trace the lineage of a Decision)
- *"この実験からCounterexampleを作って"* (Extract a Counterexample from this experiment)

---

## 2. Core Workflow Protocol

### Step 1: Pre-Audit Existing Records (Never Duplicate)
Before creating any new file:
1. Search `knowledge/decisions/`, `knowledge/failures/`, and `knowledge/cases/` using keywords.
2. Check if a related Decision or Failure already exists.
3. If an existing record exists:
   - For an architectural shift: Mark the old decision as `SUPERSEDED` and link `supersedes: [OLD_ID]` in the new decision.
   - For supplementary evidence: Append the new experiment ID or case ID to the existing record's `related_experiments` / `related_cases` list.

### Step 2: Select the Appropriate Document Type & Template
Consult `knowledge/templates/` for standard structures:
- `DECISION_TEMPLATE.md` $\to$ Architectural or threshold decisions (`knowledge/decisions/DEC-xxxx.md`)
- `FAILURE_TEMPLATE.md` $\to$ Discarded hypotheses & anti-patterns (`knowledge/failures/FAIL-xxxx.md`)
- `CASE_TEMPLATE.md` $\to$ Edge cases & heuristic-breaking inputs (`knowledge/cases/CASE-xxxx.md`)
- `EXPERIMENT_TEMPLATE.md` $\to$ Empirical measurement logs (`experiments/EXP-YYYYMMDD-xxx.md`)
- `CURRENT_TEMPLATE.md` $\to$ High-level active policies (`knowledge/current/<topic>.md`)

### Step 3: Strict ID Assignment
- **Decisions**: `DEC-0001`, `DEC-0002`, ...
- **Failures**: `FAIL-0001`, `FAIL-0002`, ...
- **Cases**: `CASE-0001`, `CASE-0002`, ...
- **Experiments**: `EXP-YYYYMMDD-001`, `EXP-YYYYMMDD-002`, ...
*(Once assigned, an ID is permanent and must never be re-used).*

### Step 4: Separate Facts from Interpretation
- Record measured values (Laplacian, Tenengrad, IoU, cosine distance) as **Facts**.
- Record causal hypotheses and qualitative assessments under explicit **Interpretation** sections.

### Step 5: Specify "Do Not Retry Unless"
When authoring a Failure Record (`FAIL-xxxx`), the `Do Not Retry Unless` clause is **mandatory**. Clearly state the exact technological or environmental prerequisite required before this idea can be revisited.

### Step 6: Synchronize Current Knowledge
If an ACCEPTED Decision alters standard operating policy, update the corresponding summary file in `knowledge/current/` with minimal diffs, linking to the new `DEC-xxxx`.
