---
name: change-impact
description: >
  DEPRECATED — use pr-triage instead.
---

# Change Impact — Deprecated

Do not load this skill.

Use:

`pr-triage`

It already performs change-impact analysis and produces:

- `reports/context/<pr-id>/impact-map.json`
- `reports/context/<pr-id>/pr-context.json`
- `reports/plans/<pr-id>/review-plan.json`

Loading this skill separately adds redundant context and reasoning cycles.

> Collect once. Reuse everywhere.