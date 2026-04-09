# T8 T4 Live Smoke Log

Fill one row per T4 live branch after running the temporary smoke setup and agent flow.

| branch_id | scenario_id | preconditions | execution_kind | prompt_or_tool_input | expected_result | observed_result | evidence_paths | telemetry_row | pass_fail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| scope_file_create | scope_file_create |  |  |  |  |  |  |  |  |
| scope_file_remove | scope_file_remove |  |  |  |  |  |  |  |  |
| read_allow_anchor | read_allow_anchor |  |  |  |  |  |  |  |  |
| read_allow_scope_directory | read_allow_scope_directory |  |  |  |  |  |  |  |  |
| read_deny_out_of_scope | read_deny_out_of_scope |  |  |  |  |  |  |  |  |
| grep_rewrite_path_targeted | grep_rewrite_path_targeted |  |  |  |  |  |  |  |  |
| glob_rewrite_path_targeted | glob_rewrite_path_targeted |  |  |  |  |  |  |  |  |
| grep_pathless_deny | grep_pathless_deny |  |  |  |  |  |  |  |  |
| glob_pathless_deny | glob_pathless_deny |  |  |  |  |  |  |  |  |
| main_thread_passthrough | main_thread_passthrough |  |  |  |  |  |  |  |  |
| no_active_run_passthrough | no_active_run_passthrough |  |  |  |  |  |  |  |  |
| agent_id_mismatch_passthrough | agent_id_mismatch_passthrough |  |  |  |  |  |  |  |  |
| poll_success | poll_success |  |  |  |  |  |  |  |  |
| poll_timeout_deny | poll_timeout_deny |  |  |  |  |  |  |  |  |
