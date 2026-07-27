#!/usr/bin/env python3

import json
import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / ".codex" / "config.toml"
EXPECTED_TOOLS = {
    "archive_workflow",
    "create_workflow_from_code",
    "execute_workflow",
    "explore_node_resources",
    "get_node_types",
    "get_sdk_reference",
    "get_workflow",
    "get_workflow_best_practices",
    "list_credentials",
    "list_workflows",
    "prepare_test_pin_data",
    "publish_workflow",
    "search_nodes",
    "test_workflow",
    "unpublish_workflow",
    "update_workflow",
    "validate_node_config",
    "validate_workflow",
}
PROMPT_TOOLS = {
    "archive_workflow",
    "create_workflow_from_code",
    "execute_workflow",
    "publish_workflow",
    "test_workflow",
    "unpublish_workflow",
    "update_workflow",
}


def main() -> int:
    with CONFIG_PATH.open("rb") as handle:
        config = tomllib.load(handle)

    errors = []
    n8n = config.get("mcp_servers", {}).get("n8n")
    if not n8n:
        errors.append(
            "Active n8n MCP config is missing. Merge .codex/config.toml.example "
            "after replacing the example URL."
        )
    else:
        if n8n.get("url") in {None, "", "https://your-n8n-domain.example/mcp-server/http"}:
            errors.append("Configure the real instance-level n8n MCP URL.")
        if n8n.get("bearer_token_env_var") != "N8N_MCP_TOKEN":
            errors.append("Use the N8N_MCP_TOKEN environment reference; never store the token.")
        if n8n.get("required") is not True:
            errors.append("The n8n MCP server must be required.")
        if n8n.get("default_tools_approval_mode") != "writes":
            errors.append("n8n must prompt by default for write tools.")
        enabled_tools = set(n8n.get("enabled_tools", []))
        if enabled_tools != EXPECTED_TOOLS:
            errors.append(
                "Active n8n enabled_tools must exactly match the reviewed allowlist; "
                f"missing={sorted(EXPECTED_TOOLS - enabled_tools)}, "
                f"extra={sorted(enabled_tools - EXPECTED_TOOLS)}."
            )
        configured_tools = n8n.get("tools", {})
        for tool in PROMPT_TOOLS:
            if configured_tools.get(tool, {}).get("approval_mode") != "prompt":
                errors.append(f"n8n tool {tool} must use approval_mode=prompt.")

    try:
        listed = json.loads(
            subprocess.run(
                ["codex", "mcp", "list", "--json"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        )
        servers = listed if isinstance(listed, list) else listed.get("servers", [])
        enabled_server_names = {
            server.get("name")
            for server in servers
            if server.get("enabled") is True
        }
        if enabled_server_names != {"n8n"}:
            errors.append(
                "The active MCP surface must contain only enabled n8n; "
                f"observed={sorted(name for name in enabled_server_names if name)}."
            )
    except Exception as exc:
        errors.append(f"Could not inspect the active MCP surface: {exc}")

    print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
