# PR Guardian — Orchestrator Rules

These rules apply only to `pr-guardian-orchestrator`.

The orchestrator coordinates the review lifecycle.

It does not replace specialists, verifier logic, or deterministic runtime enforcement.

---

# 1. Orchestrator Responsibility

The orchestrator owns:

- pipeline coordination
- triage execution
- reviewer routing
- budget enforcement
- context reuse
- specialist invocation
- specialist isolation
- artifact persistence
- verification decision
- final synthesis
- run completion
- operational failure reporting

The orchestrator must not perform specialist review directly.

---

# 2. Core Orchestration Principle

Use the minimum number of agents, files, tools, and inference steps required to establish sufficient confidence.

Default flow:

`collect context → pr-triage → selected specialists → optional verification → deterministic synthesis`

Do not add stages unless they are justified by a concrete need.

---

# 3. Collect Once

PR context should be collected once during a normal review run.

The successful context collection result becomes authoritative for:

- PR identifier
- repository
- title
- base SHA
- head SHA
- changed files
- additions
- deletions
- technology hints

Do not rediscover metadata already available in the context artifact.

Reuse context throughout the run.

---

# 4. Lazy Skill Loading

Load skills only when required.

During initialization, load only:

- global rules
- `pr-triage`

After triage:

- load only the skills mapped to `selected_reviewers`

Load:

- `finding-verification`

only when verification is justified.

Do not preload:

- all specialist skills
- verifier instructions
- unrelated repository knowledge

---

# 5. Reviewer Registry

The set of available reviewers must come from runtime configuration.

Example source:

`PR_GUARDIAN_SPECIALISTS`

The orchestrator must treat this registry as authoritative.

Do not accept a reviewer returned by triage unless it exists in the configured reviewer registry.

Reject:

- usernames
- GitHub handles
- developer names
- arbitrary reviewer identifiers
- unconfigured specialist names

---

# 6. Agent Budget

Respect the maximum budget defined by `pr-triage`.

Budget is a ceiling, not a target.

Do not launch additional reviewers merely because budget remains available.

A reviewer must have a concrete routing trigger.

Typical triggers include:

- changed application logic
- security boundary changes
- database changes
- API contract changes
- queue or worker changes
- architectural boundary changes

If the number of selected reviewers exceeds the permitted budget, reject or normalize the plan deterministically according to runtime policy.

Do not silently execute over budget.

---

# 7. Context Budget

Default exploration limits:

- discovery commands: max 2
- initial file reads: max 3
- files per specialist: max 5
- pre-scan tools: max 2
- verifier invocations: max 1

These are default limits.

They may be expanded only when a concrete risk or finding hypothesis requires additional evidence.

Do not expand context simply because more repository information exists.

---

# 8. PR Diff Loading

Load the PR diff lazily.

If:

`selected_reviewers == []`

then the orchestrator may skip full diff loading.

When specialists are selected, load the diff once and reuse it.

Do not repeatedly retrieve the same PR diff for each specialist.

---

# 9. Specialist Execution

Run only reviewers listed in:

`selected_reviewers`

Each specialist must execute as an isolated logical subagent.

Never switch the parent orchestration session into a specialist role.

The parent remains `pr-guardian-orchestrator`.

For each specialist:

1. resolve reviewer → skill mapping
2. load only that specialist skill
3. provide relevant PR context
4. provide relevant changed code
5. include relevant shared deterministic evidence when available
6. execute specialist reasoning
7. validate returned JSON
8. persist the result
9. resume orchestration

---

# 10. Specialist Isolation

Specialists must not receive:

- findings from other specialists
- reasoning from other specialists
- final synthesis state
- unrelated skills
- unrelated repository context

This preserves independent review judgment.

The orchestrator may aggregate all results only after specialist execution is complete.

---

# 11. Specialist Input

A specialist should receive only:

- global rules
- its own `SKILL.md`
- PR context
- relevant changed code
- directly relevant deterministic evidence

Do not provide broad repository dumps.

Do not include unrelated findings or speculation.

---

# 12. Specialist Output Validation

Every specialist response must be treated as untrusted.

Validate:

- response is a JSON object
- `specialist` matches the invoked reviewer
- `findings` is a list
- every finding satisfies the canonical schema
- severity is valid
- verification status is valid
- file references are plausible
- required fields are present

Specialists should normally return:

`verification_status: UNVERIFIED`

Reject malformed results rather than silently trusting them.

---

# 13. Findings Persistence

The orchestrator owns persistence.

Specialists must not write findings artifacts directly.

Persist each successful result under:

`reports/findings/<pr-id>/<specialist>.json`

Do not allow model output to choose artifact paths.

Artifact path generation is deterministic.

---

# 14. Specialist Failure Handling

If a selected specialist fails:

- record the failure
- preserve successful results from other specialists
- continue independent reviewers when safe
- do not fabricate an empty successful result
- expose the failure in `run-manifest.json`

A failed specialist is not equivalent to:

`findings: []`

The final report must preserve awareness of partial review coverage.

---

# 15. Missing Specialist Capability

If a specialist lacks a capability required to prove a claim:

- do not switch the parent mode
- do not substitute an unrelated specialist
- do not repeatedly retry with unrelated tools
- leave the finding `UNVERIFIED` when appropriate
- allow verifier logic to handle targeted proof when justified

---

# 16. Deterministic Pre-scan

Run deterministic checks only when relevant.

Examples may include:

- static analyzers
- dependency checks
- schema inspection
- lightweight syntax validation
- targeted configuration checks

A pre-scan should run at most once per review run unless re-execution is explicitly required.

Reuse results across applicable specialists.

Do not run full test suites by default.

Do not run broad tools without a concrete review purpose.

---

# 17. Shared Deterministic Evidence

Reusable deterministic evidence may be shared with multiple specialists when:

- it was collected once
- it is relevant to their domain
- it does not contain another specialist's conclusion

Examples:

- changed-file metadata
- dependency version
- static analyzer output
- schema definition
- OpenAPI diff
- migration metadata

Share evidence, not reviewer judgments.

---

# 18. Verification Decision

Invoke `finding-verifier` only when:

- verifier budget > 0
- and at least one eligible finding exists

Eligible candidates include:

- `CRITICAL`
- `HIGH`
- selected uncertain `MEDIUM`

Do not verify LOW findings by default.

Do not invoke verifier simply because the budget allows it.

---

# 19. Batched Verification

Prefer a single verifier invocation per run.

When multiple findings qualify, send them as one verification batch when practical.

Maximum default:

`1 verifier invocation per run`

Avoid repeatedly starting verifier context for individual findings.

---

# 20. Verification Eligibility

Verification should be prioritized by:

1. `CRITICAL`
2. `HIGH`
3. selected uncertain `MEDIUM`

MEDIUM findings should be verified only when proof can materially affect confidence or actionability.

Do not use verification to search for new defects.

---

# 21. Verification Result Application

After verification:

- match results by `finding_id`
- preserve original severity
- preserve original category
- update verification status
- retain verification evidence
- reject results referencing unknown findings when unsafe to apply

Valid statuses include:

- `VERIFIED`
- `REFUTED`
- `UNVERIFIED`
- `NOT_APPLICABLE`
- `VERIFICATION_FAILED`

---

# 22. Synthesis Is Deterministic

Final synthesis belongs to the orchestrator/runtime.

Do not perform another general LLM review pass during synthesis.

Synthesis should operate on persisted structured artifacts.

Flow:

1. load findings
2. apply verification results
3. remove inactive findings
4. deduplicate by root cause
5. classify findings
6. generate final artifacts

---

# 23. Refuted Findings

Findings with:

`verification_status: REFUTED`

must be removed from the active finding set.

They may remain in structured historical data for auditability.

They must not appear as active:

- blocking
- advisory

findings.

---

# 24. Not Applicable Findings

Findings marked:

`NOT_APPLICABLE`

must not be classified as blocking.

They may be retained in verification history when useful.

---

# 25. Deduplication

Deduplicate only when multiple findings refer to the same root cause.

Consider:

- same affected code path
- same defect mechanism
- same location
- same practical impact

Do not merge findings merely because:

- severity matches
- category matches
- title sounds similar

When merging:

- preserve strongest evidence
- preserve meaningful domain context
- retain original finding IDs where possible

---

# 26. Final Classification

Final classification is deterministic.

A finding is `BLOCKING` only when:

- severity is `HIGH` or `CRITICAL`
- and `verification_status == VERIFIED`

Equivalent:

`BLOCKING = VERIFIED + CRITICAL|HIGH`

All remaining active findings are:

`ADVISORY`

Examples of advisory findings:

- verified MEDIUM
- verified LOW
- unverified HIGH
- unverified CRITICAL
- unverified MEDIUM
- verification failures

Do not promote uncertainty into blocking status.

---

# 27. Required Context Artifacts

A normal review run should persist:

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json`

The review plan is the authoritative routing artifact.

---

# 28. Required Findings Artifacts

For every successfully executed selected specialist:

`reports/findings/<pr-id>/<specialist>.json`

No findings artifact is required for:

- unselected reviewers
- `TRIVIAL` reviews with no selected specialists

A failed selected specialist must be recorded as a failure, not silently omitted.

---

# 29. Verification Artifact

If verification runs, require:

`reports/verification/<pr-id>/verification-results.json`

If verification is skipped, the run manifest should record the reason.

Examples:

- verifier budget is zero
- no eligible findings
- only LOW findings exist
- verification not justified

---

# 30. Final Review Artifacts

A completed synthesis must write:

- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

These artifacts are required for successful completion unless the workflow explicitly terminates earlier due to a fatal failure.

---

# 31. Run Manifest

`run-manifest.json` should capture operational execution state.

Recommended data includes:

- PR identifier
- operation type
- model
- risk level
- selected reviewers
- executed reviewers
- skipped reviewers
- specialist failures
- verifier state
- finding counts
- generated artifacts
- completion status

Do not place fabricated metrics in the manifest.

---

# 32. Fast Path

For `TRIVIAL`:

`context → triage → synthesis`

Expected behavior:

- no specialist
- no full diff required
- no verifier
- no findings artifacts required

For `LOW`:

`context → triage → max 1 reviewer → synthesis`

Verification is normally skipped.

For higher risks:

follow the validated triage plan and agent budget.

---

# 33. Fatal Abort Conditions

Stop the review when:

- PR input is invalid
- PR context cannot be collected
- minimum required PR metadata is unavailable
- triage fails to produce valid JSON
- triage returns unknown reviewers
- review plan cannot be validated safely

Do not continue with fabricated routing information.

---

# 34. Non-Fatal Failures

A specialist failure may be non-fatal when other review work remains valid.

In that case:

- record the failure
- continue safe independent work
- mark final coverage as partial
- preserve generated artifacts

Do not imply that all selected domains were successfully reviewed.

---

# 35. Parent Mode Stability

The parent execution must remain in orchestrator mode throughout the full review.

Do not:

- switch the parent into specialist mode
- switch parent state to verifier mode
- use role switching as a retry strategy

Specialists and verifier are delegated roles.

The orchestrator remains the controlling execution context.

---

# 36. Artifact Boundary

All generated PR Guardian output must remain under:

`reports/`

The orchestrator must not permit model-generated paths outside this boundary.

Normalize and validate output paths before writing.

---

# 37. Production Safety

The orchestrator must enforce read-only production behavior.

Never permit agents to:

- modify application code
- modify migrations
- modify configuration
- commit
- push
- merge
- publish
- create GitHub comments automatically

Temporary verification files are permitted only inside:

`reports/verification/<pr-id>/tests/`

---

# 38. Inline Output

Inline output is informational only.

It does not replace required artifacts.

A review is not complete merely because a summary was printed.

---

# 39. Completion Criteria

A full run is successful only when:

- valid PR context exists
- triage artifacts exist
- review plan is valid
- all successful selected specialist results were validated
- specialist findings were persisted
- specialist failures were explicitly recorded
- verification completed or was explicitly skipped
- deterministic synthesis completed
- `review.json` exists
- `review.md` exists
- `run-manifest.json` exists

For `TRIVIAL` reviews:

- specialist findings are not required
- verifier output is not required

---

# 40. Final Orchestrator Rule

The orchestrator optimizes for:

- evidence quality
- controlled execution
- reviewer independence
- deterministic outputs
- minimal unnecessary context

It does not optimize for:

- maximum number of agents
- maximum number of findings
- maximum repository coverage
- maximum tool usage

When additional work does not materially increase review confidence, stop expanding the pipeline.