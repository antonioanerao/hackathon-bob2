---
name: review-synthesis
description: >
  Consolidates all specialist findings and verification results into the final
  review artifacts: review.json, review.md, and run-manifest.json. Removes
  REFUTED findings, groups by root cause, deduplicates, classifies blocking
  vs advisory, and calculates metrics including agent efficiency. Normally
  executed directly by the orchestrator. The review-synthesizer mode is
  spawned only for high-volume or complex runs.
---

# Review Synthesis

## Purpose

Transform raw, independently-produced findings and verification results into
a clean, deduplicated, actionable review with full metrics and audit trail.

## Core Principle

> The final review must contain only what has been proven or credibly evidenced —
> stripped of noise, duplicates, and refuted hypotheses.

## Execution Model

By default, the orchestrator executes this skill **directly in its own context**
without spawning the `review-synthesizer` subagent.

Spawn `review-synthesizer` as a subagent only when:
- More than 3 specialists contributed findings
- Total initial findings exceed 15
- Deduplication complexity is high (many overlapping findings)
- Orchestrator context capacity is a constraint

## When to Use

Activated by the orchestrator after `finding-verifier` has completed (or after
the specialist phase, if verification was skipped). This is the final stage of
every PR Guardian run.

## Inputs

- `reports/findings/<pr-id>/*.json` (all specialist findings)
- `reports/verification/<pr-id>/verification-results.json`
- `reports/context/<pr-id>/pr-context.json`
- `reports/plans/<pr-id>/review-plan.json`

## Phases

### Phase 1: Finding Collection

Load all findings from all specialist output files.

Count total findings across all files:
```
initial_findings = sum(len(file.findings) for all specialist files)
```

### Phase 2: Verification Status Enrichment

For each finding, look up its `finding_id` in `verification-results.json`.
Update `verification_status` to the verified result.

If a finding has no verification result entry:
- Keep `verification_status: "UNVERIFIED"`

### Phase 3: REFUTED Finding Removal

Remove all findings where `verification_status == "REFUTED"`.

Record count as `refuted_findings`.

These findings appear ONLY in:
- The "Refuted Findings" section of `review.md`
- The `verification_summary.refuted` counter in `review.json`
- The `findings.refuted` counter in `run-manifest.json`

They do NOT appear in the active findings list.

### Phase 4: Root-Cause Deduplication

Group findings that are symptoms of the same underlying defect.

Deduplication algorithm:
1. Look for findings that share the same `metadata.root_cause` value
2. Look for findings that reference the same symbols in `metadata.related_symbols`
3. Look for findings across different reviewers that describe the same
   observable consequence from different perspectives

For each deduplication group:
- Select the finding with the highest severity as the primary
- Merge all evidence arrays into the primary finding's evidence
- Set `metadata.related_symbols` to all symbols from merged findings
- Record original finding IDs in `metadata.related_finding_ids`
- Increment `duplicates_removed` by (group_size - 1)

### Phase 5: Blocking vs Advisory Classification

Apply classification rules:

```
BLOCKING:
  verification_status == VERIFIED AND severity in (CRITICAL, HIGH)

ADVISORY:
  verification_status == VERIFIED AND severity in (MEDIUM, LOW, INFO)
  OR verification_status == UNVERIFIED (any severity)
  OR verification_status == NOT_APPLICABLE
```

ADVISORY findings must be clearly annotated with their verification status
in all outputs.

### Phase 6: Metric Calculation

```python
# Counts
initial_findings     = total from all specialist files before any filtering
verified_findings    = count where verification_status == VERIFIED
refuted_findings     = count where verification_status == REFUTED
unverified_findings  = count where verification_status == UNVERIFIED
not_applicable       = count where verification_status == NOT_APPLICABLE
verification_failed  = count where verification_status == VERIFICATION_FAILED
duplicates_removed   = sum of (group_size - 1) for each dedup group

final_findings       = initial_findings - refuted_findings - duplicates_removed

# Rates
routing_discard_rate = skipped_reviewers / 7

if initial_findings > 0:
    noise_reduction_rate = (initial_findings - final_findings) / initial_findings
else:
    noise_reduction_rate = 0.0

# Agent efficiency (available_agents = 9: 7 specialists + verifier + synthesizer)
executed_agents      = len(selected_reviewers) + (1 if verifier_invoked else 0) + (1 if synthesizer_spawned else 0)
agent_execution_rate = executed_agents / 9
agent_avoidance_rate = 1 - agent_execution_rate
```

### Phase 7: JSON Report Generation

Write `reports/reviews/<pr-id>/review.json` conforming to the schema defined
in `rules-pr-guardian-orchestrator/04-artifact-contracts.md`.

### Phase 8: Markdown Report Generation

Write `reports/reviews/<pr-id>/review.md` with the following structure:

```markdown
# PR Guardian Review
**PR:** #<id> — <title>
**Base:** <base_sha> → **Head:** <head_sha>
**Generated:** <timestamp>

---

## Executive Summary
<2-3 sentence summary: how many blocking findings, advisory, noise reduction>

---

## Pull Request Intent
<intent from pr-context.json>

---

## Impact Analysis
<indirect_impact_summary from impact-map.json>

---

## Review Routing

### Selected Reviewers
| Reviewer | Reason | Triggers |
|---|---|---|
<rows from review-plan.json selected_reviewers>

### Skipped Reviewers
| Reviewer | Reason |
|---|---|
<rows from review-plan.json skipped_reviewers>

**Routing Discard Rate:** <routing_discard_rate>

---

## Blocking Findings
<for each BLOCKING finding>
### [<severity>] <id>: <title>
**File:** `<file>:<line>`
**Reviewer:** <reviewer>
**Verification:** <status> via <method>

<description>

**Evidence:**
- <evidence item>

**Impact:** <impact>
**Recommendation:** <recommendation>

---

## Advisory Findings
<for each ADVISORY finding, same format, annotated with verification status>

---

## Refuted Findings
<list of refuted finding IDs and titles — no detailed content>

---

## Verification Summary
| Status | Count |
|---|---|
| VERIFIED | <n> |
| UNVERIFIED | <n> |
| NOT_APPLICABLE | <n> |
| VERIFICATION_FAILED | <n> |
| REFUTED | <n> |

---

## Noise Reduction
| Stage | Count |
|---|---|
| Initial findings | <n> |
| Refuted | <n> |
| Duplicates removed | <n> |
| Final findings | <n> |

**Noise Reduction Rate:** <noise_reduction_rate>

---

## Review Metrics
| Metric | Value |
|---|---|
| Reviewers available | 7 |
| Reviewers selected | <n> |
| Reviewers skipped | <n> |
| Routing discard rate | <rate> |
| Initial findings | <n> |
| Verified | <n> |
| Refuted | <n> |
| Unverified | <n> |
| Not applicable | <n> |
| Verification failures | <n> |
| Duplicates removed | <n> |
| Final findings | <n> |
| Noise reduction rate | <rate> |
```

### Phase 9: Run Manifest Generation

Write `reports/runs/<pr-id>/run-manifest.json` with stage statuses and
all metrics per the schema in `04-artifact-contracts.md`.

Include `agent_efficiency` and `context_reuse` fields:
```json
{
  "agent_efficiency": {
    "available_agents": 9,
    "executed_agents": "<integer>",
    "skipped_agents": "<integer>",
    "agent_execution_rate": "<float>",
    "agent_avoidance_rate": "<float>"
  },
  "context_reuse": {
    "context_package_generated": true,
    "reviewers_using_shared_context": "<integer>",
    "duplicate_discovery_avoided": true
  }
}
```

Include `verification_invoked` (boolean) and `synthesis_mode`
(`"ORCHESTRATOR_INLINE"` or `"SYNTHESIZER_SUBAGENT"`).

## Canonical Output

```
reports/reviews/<pr-id>/review.json
reports/reviews/<pr-id>/review.md
reports/runs/<pr-id>/run-manifest.json
```

## Failure Modes

| Failure | Correct Response |
|---------|-----------------|
| Specialist findings file missing | Note missing file; count as 0 findings for that reviewer |
| verification-results.json missing | Mark all findings UNVERIFIED; record in run-manifest |
| initial_findings == 0 | Set noise_reduction_rate = 0.0; record "No findings produced" |
| verification skipped | Set verification_invoked=false; all statuses remain UNVERIFIED |

## What This Skill Must Not Do

- Create new findings or search for new bugs
- Re-run any specialist reviewer
- Modify production code or test files
- Elevate or downgrade verified finding severities
- Include REFUTED findings in the active findings list

## Completion Criteria

- All specialist findings have been loaded and verification statuses applied
- REFUTED findings have been removed from the active set
- Root-cause deduplication has been performed
- BLOCKING and ADVISORY classification is complete
- All metrics are correctly calculated
- `review.json`, `review.md`, and `run-manifest.json` are written and schema-valid
