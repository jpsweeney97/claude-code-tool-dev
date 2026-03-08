# D4a Xfail Inventory

Tests marked `xfail(strict=True)` during D4a schema migration. Each will be resolved in D4b.

## test_pipeline.py — 18 tests

All tests that call `process_turn()` fail because `pipeline.py:120` accesses `request.context_claims` (removed from TurnRequest in 0.2.0).

| Test | Reason | D4b Task |
|------|--------|----------|
| `TestSchemaValidation::test_correct_schema_version_succeeds` | pipeline uses context_claims | Task 13a |
| `TestEntityExtraction::test_entities_extracted_from_focus_claims` | pipeline uses context_claims | Task 13a |
| `TestEntityExtraction::test_entities_extracted_from_focus_unresolved` | pipeline uses context_claims | Task 13a |
| `TestEntityExtraction::test_no_entities_when_no_text_references` | pipeline uses context_claims | Task 13a |
| `TestPathDecisions::test_file_path_entity_gets_path_decision` | pipeline uses context_claims | Task 13a |
| `TestPathDecisions::test_file_loc_entity_gets_path_decision` | pipeline uses context_claims | Task 13a |
| `TestPathDecisions::test_symbol_entity_no_path_decision` | pipeline uses context_claims | Task 13a |
| `TestPathDecisions::test_not_tracked_file_gets_not_tracked_status` | pipeline uses context_claims | Task 13a |
| `TestTemplateMatching::test_eligible_file_entity_gets_probe_template` | pipeline uses context_claims | Task 13a |
| `TestTemplateMatching::test_symbol_entity_gets_grep_template` | pipeline uses context_claims | Task 13a |
| `TestBudget::test_empty_history_full_budget` | pipeline uses context_claims | Task 13a |
| `TestStoreRecord::test_turn_request_stored` | pipeline uses context_claims | Task 13a |
| `TestStoreRecord::test_spec_registry_stored` | pipeline uses context_claims | Task 13a |
| `TestStoreRecord::test_duplicate_ref_raises_on_second_call` | pipeline uses context_claims | Task 13a |
| `TestEndToEnd::test_realistic_turn_request_produces_full_packet` | pipeline uses context_claims | Task 13a |
| `TestEndToEnd::test_empty_focus_produces_empty_success` | pipeline uses context_claims | Task 13a |
| `TestEndToEnd::test_multiple_entity_types_in_single_claim` | pipeline uses context_claims | Task 13a |
| `TestEndToEnd::test_entity_ids_are_unique` | pipeline uses context_claims | Task 13a |

**Not xfailed (pass correctly):**
- `TestErrorHandling::test_unexpected_exception_returns_internal_error` — mock throws before context_claims access
- `TestErrorHandling::test_error_packet_has_schema_version` — mock throws before context_claims access

## test_integration.py — 4 tests

All integration tests call `process_turn()` which accesses `request.context_claims`.

| Test | Reason | D4b Task |
|------|--------|----------|
| `test_contract_example_produces_valid_turn_packet` | pipeline uses context_claims | Task 13a |
| `test_grep_call1_call2_round_trip` | pipeline uses context_claims | Task 13a |
| `test_grep_no_matches_returns_success` | pipeline uses context_claims | Task 13a |
| `test_grep_denied_file_filtered` | pipeline uses context_claims | Task 13a |

## test_execute.py — 13 tests

Tests in `TestExecuteScout` that reach `execute.py:525` which accesses `record.turn_request.evidence_history` (removed from TurnRequest in 0.2.0).

| Test | Reason | D4b Task |
|------|--------|----------|
| `TestExecuteScout::test_valid_read_returns_success` | execute_scout uses evidence_history | Task 14 |
| `TestExecuteScout::test_already_used_returns_invalid` | execute_scout uses evidence_history | Task 14 |
| `TestExecuteScout::test_grep_happy_path` | execute_scout uses evidence_history | Task 14 |
| `TestExecuteScout::test_grep_no_matches` | execute_scout uses evidence_history | Task 14 |
| `TestExecuteScout::test_grep_rg_not_found` | execute_scout uses evidence_history | Task 14 |
| `TestExecuteScout::test_grep_timeout` | execute_scout uses evidence_history | Task 14 |
| `TestExecuteScout::test_grep_rg_execution_error` | execute_scout uses evidence_history | Task 14 |
| `TestExecuteScout::test_grep_all_files_filtered` | execute_scout uses evidence_history | Task 14 |
| `TestExecuteScout::test_grep_truncation_recomputes_metadata` | execute_scout uses evidence_history | Task 14 |
| `TestExecuteScout::test_grep_budget_success` | execute_scout uses evidence_history | Task 14 |
| `TestExecuteScout::test_grep_budget_failure` | execute_scout uses evidence_history | Task 14 |
| `TestExecuteScout::test_budget_with_evidence_history` | execute_scout uses evidence_history | Task 14 |
| `TestExecuteScout::test_all_success_fields_from_option_record` | execute_scout uses evidence_history | Task 14 |

**Not xfailed (pass correctly):**
- `TestExecuteScout::test_invalid_token_returns_invalid` — returns ScoutResultInvalid before evidence_history
- `TestExecuteScout::test_unknown_ref_returns_invalid` — returns ScoutResultInvalid before evidence_history

## Deleted Tests (No Xfail — Feature Removed)

Tests that tested features removed in 0.2.0. Cannot be xfailed because TurnRequest no longer accepts the fields they tested. D4b Task 13a provides equivalent coverage for the new data flow (cumulative claims from ConversationState).

| File | Test | What It Tested | D4b Replacement |
|------|------|----------------|-----------------|
| test_pipeline.py | `test_entities_extracted_from_context_claims` | Entity extraction from `context_claims` (in_focus=False) | Task 13a: `TestPipelineCumulativeClaims` |
| test_pipeline.py | `test_entities_from_all_three_sources_combined` | Combining focus.claims + focus.unresolved + context_claims | Task 13a: pipeline extracts from focus + prior claims |
| test_pipeline.py | `test_out_of_focus_entity_no_probe` | Out-of-focus entities from `context_claims` don't get probes | Task 13a: equivalent via ConversationState prior claims |
| test_pipeline.py | `test_history_reduces_remaining` | `evidence_history` reducing budget | Task 13a: budget from ConversationState evidence |
| test_pipeline.py | `test_exhausted_budget` | 5 evidence records exhausting budget | Task 13a: budget from ConversationState evidence |
| test_types.py | `test_optional_context_claims` | `context_claims` defaults to empty | Replaced by `TestTurnRequest020.test_context_claims_removed` |

## Summary

| File | Xfailed | Passing | Root Cause | D4b Task |
|------|---------|---------|------------|----------|
| test_pipeline.py | 18 | 2 | `pipeline.py` accesses `request.context_claims` | Task 13a |
| test_integration.py | 4 | 0 | `pipeline.py` accesses `request.context_claims` | Task 13a |
| test_execute.py | 13 | 2 | `execute.py` accesses `record.turn_request.evidence_history` | Task 14 |
| **Total** | **35** | **4** | | |
