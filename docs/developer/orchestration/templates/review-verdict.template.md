# Review Verdict

WO: `WO-XXX-short-title`
Reviewer role: `spec_reviewer | quality_reviewer | release_validator`
Review mode: `full | owned_finding_recheck`
Date: `<timestamp>`

Use this interface for every reviewer. Repeat `finding` and `evidence` blocks as needed. Use an empty findings list for a pass.

```text
verdict: pass | changes_required | blocked

finding:
  id: <stable id>
  issue_class: <stable class>
  severity: <critical | important | minor>
  reference: <exact path, line, artifact, or gate>
  required_change: <smallest change that closes the issue>
  status: open | fixed | accepted_risk | blocked

evidence:
  source: static_review | synthetic_test | tracked_fixture | generated_artifact | api_e2e | ui_behavior | runtime_smoke | full_validation_epoch | manual | n/a
  target_scope: local | exact_candidate | deployed_environment | provider | physical_device | current_origin | brain_origin | ru_origin
  freshness: current_candidate | current_environment | retained_current | historical_stale
  attribution: wo_owned | wave_integration | pre_existing | unrelated | blocked_by_access
  result: <observed result or truthful manual label>
  reference: <reproducible summary or retained artifact>

next_action: execute | owned_finding_recheck | fresh_final_review | release_validation | problem_class_analysis | wait_for_access | close
```

Do not hide a skip, attestation, stale artifact, unrelated failure, or access blocker inside a passing summary. Explain scope and limitations in the result or reference.
