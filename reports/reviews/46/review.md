# PR Review — mp-ac/verifica-ai #46

**Title:** fix: resolvido erro ao passar conteúdo extraído do youtube para o agente de buscas  
**Risk:** LOW  
**Verdict:** ✅ Approved with Advisory Notes

---

## Summary

The PR correctly fixes the reported bug. The full extracted YouTube content was previously passed verbatim as research context, which could overwhelm the search agent. The fix introduces a compact formatter (`format_research_context`) that selects up to 3 segment summaries, each truncated to 400 characters, stores the result in a new `youtube_research_context` state field, and removes the brittle `media_contexts` list lookup from both the main and reanalysis graph paths.

**Core logic is correct:**
- `break` placement in `format_research_context` is correct — empty segments do not consume a cap slot.
- `state.get("youtube_research_context", "")` fallback is safe at both call sites.
- `format_youtube_research_query` conditional context inclusion is correct.
- `NotRequired[str]` field additions are consistent across `RouterState` and `ReanalysisState`.
- Test updates are on-point for the reanalysis path.

---

## Blocking Findings

_None._

---

## Advisory Findings

### 🟡 MEDIUM — CR-001: All-empty relevance segments not tested
**Location:** [`src/agents/youtube_agent/formatting.py`](src/agents/youtube_agent/formatting.py)

If every segment in `analysis.relevant_segments` has an empty `relevance` string, `format_research_context` returns `""` silently. The downstream guard in `format_youtube_research_query` handles this gracefully (the context block is omitted), so there is no crash. However, this edge case is untested and could mask data-quality regressions.

**Suggestion:** Add a test asserting the empty-string return for all-empty segments. Optionally emit a `logging.warning` to surface data-quality issues in production.

---

### 🔵 LOW — CR-003: Unicode ellipsis (U+2026) in truncation
**Location:** [`src/agents/youtube_agent/formatting.py`](src/agents/youtube_agent/formatting.py)

`_compact_summary` appends `…` (U+2026) when truncating. Python 3 and LLM APIs generally handle UTF-8 cleanly, but ASCII-only serialisers or log sinks may produce a replacement character or raise `UnicodeEncodeError`.

**Suggestion:** Use `...` (three ASCII dots) or confirm the full pipeline is UTF-8 throughout.

---

### 🔵 LOW — CR-004: Off-by-one in truncation slice
**Location:** [`src/agents/youtube_agent/formatting.py`](src/agents/youtube_agent/formatting.py)

```python
return f"{summary[:MAX_RESEARCH_SUMMARY_CHARS - 1].rstrip()}…"
```

`MAX_RESEARCH_SUMMARY_CHARS - 1 = 399`. With the ellipsis appended the total is 400 characters, so the result is consistent with "total ≤ 400 chars". However, if the intent was "400 chars of content plus the ellipsis" the slice is one character short. The constant should be commented to clarify which interpretation is correct.

**Suggestion:** Add a comment to `MAX_RESEARCH_SUMMARY_CHARS` clarifying whether it is a total-length cap (current behaviour) or a content-length cap.

---

### 🔵 LOW — CR-005: Removal of explicit no-context fallback changes prompt structure
**Location:** [`src/graph/nodes.py`](src/graph/nodes.py), [`src/reanalysis/graph/nodes.py`](src/reanalysis/graph/nodes.py)

Before, when no YouTube context was available the LLM received:

> "Contexto do vídeo diretamente relacionado à alegação: Nenhum contexto adicional foi extraído."

Now it receives nothing. The prompt is shorter when `youtube_research_context` is absent, which changes model behaviour for non-YouTube inputs or state-miss scenarios. This is likely an improvement but was not explicitly evaluated.

**Suggestion:** Evaluate prompt quality with and without the phrase. If the explicit no-context signal was load-bearing, restore it as a default: `state.get("youtube_research_context") or "Nenhum contexto adicional foi extraído."`.

---

### 🔵 LOW — CR-006: Test assertions for truncation not fully visible
**Location:** [`tests/test_youtube_agent.py`](tests/test_youtube_agent.py)

The patch shows that `format_research_context(analysis).splitlines()` is called but the assertions are cut off. It cannot be confirmed that the tests assert:
1. Exactly 3 lines when 4 segments are given.
2. Each truncated line is ≤ 400 characters (including ellipsis).
3. Each line starts with `- `.
4. An empty string is returned for 0 segments.

**Suggestion:** Verify (or add) assertions for all four properties above.

---

### ℹ️ INFO — CR-007: LangGraph state propagation for `youtube_research_context` not verified
**Location:** [`src/reanalysis/graph/state.py`](src/reanalysis/graph/state.py)

`NotRequired[str]` fields without an explicit reducer may not propagate correctly in branched or resumed LangGraph executions. The `.get()` empty-string fallback is safe for the current call sites, but the intent should be documented.

**Suggestion:** Confirm no custom reducer is needed and add a brief comment documenting the empty-string-fallback as intentional for resumed/replayed graphs.

---

## Reviewers

| Specialist | Status |
|---|---|
| code-review-specialist | ✅ Completed |
| security-review-specialist | ⏭ Skipped (no security surfaces) |
| database-review-specialist | ⏭ Skipped (no DB changes) |
| api-review-specialist | ⏭ Skipped (no HTTP/API changes) |
| async-review-specialist | ⏭ Skipped (no queue/worker changes) |
| architecture-review-specialist | ⏭ Skipped (no structural boundary changes) |

## Verification

Skipped — risk level LOW, no CRITICAL/HIGH findings.
