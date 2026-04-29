#!/usr/bin/env python3
"""Compare two Codex App Server JSON Schema trees.

This script is a maintenance helper for compatibility evidence. It compares a
vendored schema fixture against a newly generated schema tree and writes a
machine-readable JSON report with method-surface, file-churn, selected payload,
and runtime-consumed shape summaries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]


DIRECT_RUNTIME_CONSUMED = [
    "v2/TurnStartResponse.json",
    "v2/ThreadReadResponse.json",
    "v2/ItemCompletedNotification.json",
    "v2/TurnCompletedNotification.json",
    "v2/TurnStartedNotification.json",
    "v2/ItemStartedNotification.json",
    "v2/ThreadStartedNotification.json",
]

THREAD_TURN_REQUESTS = [
    "v2/ThreadStartParams.json",
    "v2/TurnStartParams.json",
    "v2/ThreadResumeParams.json",
    "v2/ThreadForkParams.json",
]

THREAD_PERMISSION_RESPONSES = [
    "v2/ThreadStartResponse.json",
    "v2/ThreadResumeResponse.json",
    "v2/ThreadForkResponse.json",
]

SERVER_METHOD_FILES = {
    "item/commandExecution/requestApproval": (
        "CommandExecutionRequestApprovalParams.json",
        "CommandExecutionRequestApprovalResponse.json",
    ),
    "item/fileChange/requestApproval": (
        "FileChangeRequestApprovalParams.json",
        "FileChangeRequestApprovalResponse.json",
    ),
    "item/tool/requestUserInput": (
        "ToolRequestUserInputParams.json",
        "ToolRequestUserInputResponse.json",
    ),
    "mcpServer/elicitation/request": (
        "McpServerElicitationRequestParams.json",
        "McpServerElicitationRequestResponse.json",
    ),
    "item/permissions/requestApproval": (
        "PermissionsRequestApprovalParams.json",
        "PermissionsRequestApprovalResponse.json",
    ),
    "item/tool/call": (
        "DynamicToolCallParams.json",
        "DynamicToolCallResponse.json",
    ),
    "account/chatgptAuthTokens/refresh": (
        "ChatgptAuthTokensRefreshParams.json",
        "ChatgptAuthTokensRefreshResponse.json",
    ),
    "applyPatchApproval": (
        "ApplyPatchApprovalParams.json",
        "ApplyPatchApprovalResponse.json",
    ),
    "execCommandApproval": (
        "ExecCommandApprovalParams.json",
        "ExecCommandApprovalResponse.json",
    ),
}

CHECKED_EQUAL = [
    "ToolRequestUserInputResponse.json",
    "CommandExecutionRequestApprovalResponse.json",
    "FileChangeRequestApprovalResponse.json",
    "ToolRequestUserInputParams.json",
    "FileChangeRequestApprovalParams.json",
    "v1/InitializeParams.json",
    "v1/InitializeResponse.json",
    "v2/ThreadReadParams.json",
    "v2/TurnInterruptParams.json",
    "v2/TurnSteerParams.json",
]


def read_json(path: Path) -> Any:
    """Read JSON from a schema file."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(
            f"read schema failed: file not found. Got: {str(path)!r:.100}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"read schema failed: invalid JSON. Got: {str(path)!r:.100}"
        ) from exc


def schema_files(root: Path) -> dict[str, Path]:
    """Return schema JSON files by relative path, excluding derived manifests."""
    return {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*.json")
        if path.name != "required-methods.json"
    }


def canonical_tree_digest(root: Path, *, exclude_manifest: bool) -> JsonObject:
    """Compute a canonical digest for all JSON files in a schema tree."""
    digest = hashlib.sha256()
    count = 0
    for path in sorted(root.rglob("*.json")):
        if exclude_manifest and path.name == "required-methods.json":
            continue
        rel = path.relative_to(root).as_posix()
        canonical = json.dumps(
            read_json(path),
            sort_keys=True,
            separators=(",", ":"),
        )
        digest.update(rel.encode())
        digest.update(b"\0")
        digest.update(canonical.encode())
        digest.update(b"\0")
        count += 1
    return {"files": count, "sha256": digest.hexdigest()}


def extract_methods(root: Path, schema_name: str) -> list[str]:
    """Extract JSON-RPC method names from ClientRequest or ServerRequest."""
    data = read_json(root / schema_name)
    found: set[str] = set()
    for variant in data.get("oneOf", []):
        if not isinstance(variant, dict):
            continue
        method = variant.get("properties", {}).get("method", {})
        if isinstance(method, dict):
            found.update(method.get("enum", []))
    return sorted(found)


def enum_values(root: Path, schema_name: str, definition_name: str) -> list[str]:
    """Extract enum values from a schema definition."""
    data = read_json(root / schema_name)
    values = data.get("definitions", {}).get(definition_name, {}).get("enum", [])
    return sorted(values)


def property_keys(data: Any) -> set[str]:
    """Return top-level property keys for object schemas."""
    if not isinstance(data, dict):
        return set()
    props = data.get("properties", {})
    if not isinstance(props, dict):
        return set()
    return set(props)


def shape_summary(old_root: Path, new_root: Path, rel: str) -> JsonObject:
    """Compare top-level properties and required fields for one schema file."""
    old_data = read_json(old_root / rel)
    new_data = read_json(new_root / rel)
    old_props = property_keys(old_data)
    new_props = property_keys(new_data)
    return {
        "equal": old_data == new_data,
        "added_props": sorted(new_props - old_props),
        "removed_props": sorted(old_props - new_props),
        "required_old": old_data.get("required") if isinstance(old_data, dict) else None,
        "required_new": new_data.get("required") if isinstance(new_data, dict) else None,
    }


def permission_profile_summary(
    old_root: Path,
    new_root: Path,
    rel: str,
) -> JsonObject:
    """Summarize added fields and permissionProfile descriptions."""
    summary = shape_summary(old_root, new_root, rel)
    new_data = read_json(new_root / rel)
    permission_profile = {}
    if isinstance(new_data, dict):
        permission_profile = new_data.get("properties", {}).get("permissionProfile", {})
    summary["permissionProfile_description"] = (
        permission_profile.get("description")
        if isinstance(permission_profile, dict)
        else None
    )
    return summary


def thread_permission_response_summary(
    old_root: Path,
    new_root: Path,
    rel: str,
) -> JsonObject:
    """Summarize thread response permission-view fields."""
    summary = shape_summary(old_root, new_root, rel)
    new_data = read_json(new_root / rel)
    if isinstance(new_data, dict):
        props = new_data.get("properties", {})
        summary["permissionProfile_description"] = (
            props.get("permissionProfile", {}).get("description")
            if isinstance(props, dict)
            else None
        )
        summary["sandbox_description"] = (
            props.get("sandbox", {}).get("description")
            if isinstance(props, dict)
            else None
        )
    return summary


def command_action_variants(root: Path) -> dict[str, JsonObject]:
    """Summarize CommandAction variants by title."""
    data = read_json(root / "CommandExecutionRequestApprovalParams.json")
    variants = (
        data.get("definitions", {})
        .get("CommandAction", {})
        .get("oneOf", [])
    )
    result: dict[str, JsonObject] = {}
    for variant in variants:
        if not isinstance(variant, dict):
            continue
        title = variant.get("title")
        if not isinstance(title, str):
            continue
        props = variant.get("properties", {})
        path_prop = props.get("path") if isinstance(props, dict) else None
        result[title] = {
            "required": variant.get("required", []),
            "path": path_prop,
        }
    return result


def definition_property_summary(root: Path, definition_name: str) -> JsonObject:
    """Summarize one definition's properties."""
    data = read_json(root / "CommandExecutionRequestApprovalParams.json")
    definition = data.get("definitions", {}).get(definition_name, {})
    if not isinstance(definition, dict):
        return {"present": False, "properties": []}
    props = definition.get("properties", {})
    return {
        "present": True,
        "properties": sorted(props) if isinstance(props, dict) else [],
        "property_schemas": props if isinstance(props, dict) else {},
    }


def command_approval_details(old_root: Path, new_root: Path) -> JsonObject:
    """Summarize nested command-approval details called out by compatibility docs."""
    return {
        "top_level": shape_summary(
            old_root,
            new_root,
            "CommandExecutionRequestApprovalParams.json",
        ),
        "cwd": {
            "old": read_json(old_root / "CommandExecutionRequestApprovalParams.json")
            .get("properties", {})
            .get("cwd"),
            "new": read_json(new_root / "CommandExecutionRequestApprovalParams.json")
            .get("properties", {})
            .get("cwd"),
        },
        "command_action_variants": {
            "old": command_action_variants(old_root),
            "new": command_action_variants(new_root),
        },
        "additional_file_system_permissions": {
            "old": definition_property_summary(
                old_root,
                "AdditionalFileSystemPermissions",
            ),
            "new": definition_property_summary(
                new_root,
                "AdditionalFileSystemPermissions",
            ),
        },
        "additional_permission_profile": {
            "old": definition_property_summary(old_root, "AdditionalPermissionProfile"),
            "new": definition_property_summary(new_root, "AdditionalPermissionProfile"),
        },
        "macos_definition_names": {
            "old": sorted(
                name
                for name in read_json(
                    old_root / "CommandExecutionRequestApprovalParams.json"
                )
                .get("definitions", {})
                .keys()
                if "MacOs" in name
            ),
            "new": sorted(
                name
                for name in read_json(
                    new_root / "CommandExecutionRequestApprovalParams.json"
                )
                .get("definitions", {})
                .keys()
                if "MacOs" in name
            ),
        },
    }


def build_report(old_root: Path, new_root: Path) -> JsonObject:
    """Build the schema comparison report."""
    old_files = schema_files(old_root)
    new_files = schema_files(new_root)
    common_files = sorted(set(old_files) & set(new_files))
    added_files = sorted(set(new_files) - set(old_files))
    removed_files = sorted(set(old_files) - set(new_files))
    changed_files = [
        rel
        for rel in common_files
        if read_json(old_files[rel]) != read_json(new_files[rel])
    ]

    old_client_methods = extract_methods(old_root, "ClientRequest.json")
    new_client_methods = extract_methods(new_root, "ClientRequest.json")
    old_server_methods = extract_methods(old_root, "ServerRequest.json")
    new_server_methods = extract_methods(new_root, "ServerRequest.json")
    old_reviewers = enum_values(old_root, "ClientRequest.json", "ApprovalsReviewer")
    new_reviewers = enum_values(new_root, "ClientRequest.json", "ApprovalsReviewer")

    return {
        "roots": {
            "old": str(old_root),
            "new": str(new_root),
            "old_resolved": str(old_root.resolve()),
            "new_resolved": str(new_root.resolve()),
        },
        "digests": {
            "old_all_json": canonical_tree_digest(old_root, exclude_manifest=False),
            "old_schema_only": canonical_tree_digest(old_root, exclude_manifest=True),
            "new_schema_only": canonical_tree_digest(new_root, exclude_manifest=True),
        },
        "file_churn": {
            "old_schema_files": len(old_files),
            "new_schema_files": len(new_files),
            "common": len(common_files),
            "changed_common": len(changed_files),
            "added": len(added_files),
            "removed": len(removed_files),
            "added_files": added_files,
            "removed_files": removed_files,
            "changed_common_files": changed_files,
            "added_notification_files": [
                rel for rel in added_files if "Notification" in rel
            ],
            "removed_notification_files": [
                rel for rel in removed_files if "Notification" in rel
            ],
            "changed_common_notification_files": [
                rel for rel in changed_files if "Notification" in rel
            ],
        },
        "method_surfaces": {
            "ClientRequest": {
                "old_count": len(old_client_methods),
                "new_count": len(new_client_methods),
                "added": sorted(set(new_client_methods) - set(old_client_methods)),
                "removed": sorted(set(old_client_methods) - set(new_client_methods)),
            },
            "ServerRequest": {
                "old_count": len(old_server_methods),
                "new_count": len(new_server_methods),
                "added": sorted(set(new_server_methods) - set(old_server_methods)),
                "removed": sorted(set(old_server_methods) - set(new_server_methods)),
            },
        },
        "enum_changes": {
            "ApprovalsReviewer": {
                "old": old_reviewers,
                "new": new_reviewers,
                "added": sorted(set(new_reviewers) - set(old_reviewers)),
                "removed": sorted(set(old_reviewers) - set(new_reviewers)),
            },
        },
        "thread_turn_requests": {
            rel: permission_profile_summary(old_root, new_root, rel)
            for rel in THREAD_TURN_REQUESTS
        },
        "thread_permission_responses": {
            rel: thread_permission_response_summary(old_root, new_root, rel)
            for rel in THREAD_PERMISSION_RESPONSES
        },
        "direct_runtime_consumed": {
            rel: shape_summary(old_root, new_root, rel)
            for rel in DIRECT_RUNTIME_CONSUMED
        },
        "server_requests": {
            method: {
                "params_file": params_file,
                "response_file": response_file,
                "params": shape_summary(old_root, new_root, params_file),
                "response": shape_summary(old_root, new_root, response_file),
            }
            for method, (params_file, response_file) in SERVER_METHOD_FILES.items()
        },
        "command_approval_details": command_approval_details(old_root, new_root),
        "checked_equal": {
            rel: read_json(old_root / rel) == read_json(new_root / rel)
            for rel in CHECKED_EQUAL
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compare two Codex App Server JSON Schema trees.",
    )
    parser.add_argument("--old-root", required=True, type=Path)
    parser.add_argument("--new-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    """Run the schema comparison."""
    args = parse_args(argv)
    old_root = args.old_root
    new_root = args.new_root
    for label, root in [("old root", old_root), ("new root", new_root)]:
        if not root.is_dir():
            print(
                f"compare schemas failed: {label} is not a directory. "
                f"Got: {str(root)!r:.100}",
                file=sys.stderr,
            )
            return 1

    report = build_report(old_root, new_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
