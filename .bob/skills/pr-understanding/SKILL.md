---
name: pr-understanding
description: >
  DEPRECATED — use pr-triage instead.
---

# PR Understanding — Deprecated

Do not load this skill.

Use:

`pr-triage`

It already performs PR understanding, impact analysis, and routing, producing:

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json`

Loading this skill separately adds redundant context and LLM cycles.