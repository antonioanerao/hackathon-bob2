# PR Review — mp-ac/verifica-ai #57

**Title:** feat: adicionado verificacao de duplicidade também para áudio, vídeo e imagem  
**Risk:** MEDIUM | **Verdict:** ✅ ADVISORY — No blocking issues

---

## Summary

This PR refactors the duplicate-detection flow so the check runs **after** the LLM workflow using the normalized final-answer title (stripped of classification prefix) instead of the raw user query. This enables semantic deduplication for media content (audio, video, image) whose relevant text ends up in the answer title.

The core implementation is **sound**. The `explicit_attachments` parameter in `check_duplicate_analysis` is a skip-guard (non-empty → skip), not a data carrier, so passing `[]` is correct. The `None` query case is handled safely (returns `outcome='skipped'`). Four initial HIGH findings were **refuted** by direct code evidence.

Four advisory observations remain.

---

## Findings

### 🟡 MEDIUM — CODE-003: Ordering change closes early-exit path for duplicate submissions

**File:** [`src/jobs/analyze.py`](https://github.com/mp-ac/verifica-ai/blob/92f5a235c1f100e04e85a2d60ab36539f5755064/src/jobs/analyze.py)

The LLM workflow now always runs before the duplicate check. The previous ordering (check-then-workflow) could have been used as a cost-saving gate in the future. The current design makes the duplicate check strictly post-hoc and advisory.

> **Recommendation:** Document explicitly that duplicate checking is advisory-only and does not gate workflow execution. If future cost optimization requires short-circuiting, a lightweight pre-workflow title-based check would need to be added.

---

### 🟡 MEDIUM — ASYNC-003: Duplicate check at job end extends wall-clock time — RQ timeout risk

**File:** [`src/jobs/analyze.py`](https://github.com/mp-ac/verifica-ai/blob/92f5a235c1f100e04e85a2d60ab36539f5755064/src/jobs/analyze.py)

Previously, the duplicate check latency was paid before the LLM workflow. Now it's appended after, so total job duration = LLM time + Qdrant retrieval + optional LLM judge. If the RQ `job_timeout` was sized around the LLM workflow alone, the added tail latency may push jobs over the limit.

> **Recommendation:** Audit the configured `job_timeout` against the p95 combined latency (LLM workflow + duplicate check). Increase if the margin is insufficient.

---

### 🟡 MEDIUM — CODE-004: Verdict-only titles silently bypass duplicate check

**File:** [`src/similarity/query.py`](https://github.com/mp-ac/verifica-ai/blob/92f5a235c1f100e04e85a2d60ab36539f5755064/src/similarity/query.py)

When `final_answer.title` is only a classification prefix (e.g. `"FALSO:"`), `build_duplicate_check_query` returns `None` and `check_duplicate_analysis` returns `outcome='skipped'` — correctly. However, there is no log or metric to distinguish "skipped because title was empty after prefix stripping" from "skipped because semantic retriever is disabled." Titles that accidentally match a prefix pattern will silently bypass deduplication in production with no observable signal.

> **Recommendation:** Add a `logger.debug(...)` call in `build_duplicate_check_query` when a non-`None` `final_answer` produces a `None` result.

---

### 🔵 LOW — ASYNC-005: Duplicate result does not gate Qdrant persistence (advisory mode undocumented)

**File:** [`src/jobs/analyze.py`](https://github.com/mp-ac/verifica-ai/blob/92f5a235c1f100e04e85a2d60ab36539f5755064/src/jobs/analyze.py)

The duplicate check result (`outcome='exact_match'`, `'match'`, etc.) is returned in the job output but does not influence the `persist_to_qdrant` flag passed to `dispatch_completed_result`. This is correct for advisory mode, but it is not documented.

> **Recommendation:** Add a comment in `_process_analyze_job` explaining that duplicate checking is intentionally advisory and does not gate persistence.

---

### 🔵 LOW — CODE-005: None-query integration path not tested

**File:** [`tests/test_similarity_query.py`](https://github.com/mp-ac/verifica-ai/blob/92f5a235c1f100e04e85a2d60ab36539f5755064/tests/test_similarity_query.py)

Unit tests for `build_duplicate_check_query` are thorough in isolation but do not cover the integration path where `final_answer=None` flows through `run_duplicate_check` → `check_duplicate_analysis`. The path is safe, but the guarantee is untested.

> **Recommendation:** Add a mock-based test in `test_similarity_worker.py` asserting that `final_answer=None` produces `duplicate_check['outcome'] == 'skipped'`.

---

## Refuted Findings

| Finding | Claim | Refutation |
|---|---|---|
| CODE-001 | `[]` attachments = attachment dedup never runs | `explicit_attachments` is a **skip-guard**: non-empty → skip check. `[]` is correct. |
| CODE-002 | `None` query → unsafe call to `check_duplicate_analysis` | `(query or "").strip()` → `""` → early return `outcome='skipped'`. Safe. |
| ASYNC-001 | `dispatch_completed_result` runs before duplicate check | Actual order: `run_duplicate_check` → `dispatch_completed_result`. Premise was wrong. |
| ASYNC-004 | Same root cause as CODE-001 | Refuted by same evidence. |

---

## Positive Observations

- ✅ New `build_duplicate_check_query` is clean, focused, and well-named.
- ✅ Three unit tests cover the key paths for the new function.
- ✅ The semantic shift from raw query → normalized title is a correct improvement for media content.
- ✅ `run_duplicate_check` has comprehensive internal exception handling — failure cannot propagate to job failure.
- ✅ `check_duplicate_analysis` handles `None`/empty queries gracefully with `outcome='skipped'`.

---

*Generated by PR Guardian · Specialists: code-review, async-review · Verification: 4 findings refuted*
