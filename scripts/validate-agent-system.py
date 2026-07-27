#!/usr/bin/env python3

import json
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / ".codex" / "agents"

EXPECTED = {
    "supervisor": {
        "file": "supervisor.toml",
        "sandbox": "read-only",
        "approval": "never",
    },
    "skeleton_architect": {
        "file": "skeleton-architect.toml",
        "sandbox": "workspace-write",
        "approval": "on-request",
    },
    "module_builder": {
        "file": "module-builder.toml",
        "sandbox": "workspace-write",
        "approval": "on-request",
    },
    "deviation_monitor": {
        "file": "deviation-monitor.toml",
        "sandbox": "read-only",
        "approval": "never",
    },
    "eval_tuner": {
        "file": "eval-tuner.toml",
        "sandbox": "workspace-write",
        "approval": "on-request",
    },
    "security_firewall": {
        "file": "security-firewall.toml",
        "sandbox": "read-only",
        "approval": "never",
    },
}


def load_toml(path: Path):
    with path.open("rb") as handle:
        return tomllib.load(handle)


def main() -> int:
    errors = []
    parsed_agents = {}

    for expected_name, expected in EXPECTED.items():
        path = AGENTS_DIR / expected["file"]
        if not path.exists():
            errors.append(f"Missing agent file: {path.relative_to(ROOT)}")
            continue

        try:
            agent = load_toml(path)
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)} is invalid TOML: {exc}")
            continue

        parsed_agents[expected_name] = agent
        for field in ["name", "description", "developer_instructions"]:
            if not isinstance(agent.get(field), str) or not agent[field].strip():
                errors.append(f"{path.relative_to(ROOT)} is missing non-empty {field}.")

        if agent.get("name") != expected_name:
            errors.append(
                f"{path.relative_to(ROOT)} name is {agent.get('name')!r}, expected {expected_name!r}."
            )
        if agent.get("sandbox_mode") != expected["sandbox"]:
            errors.append(
                f"{expected_name} sandbox must be {expected['sandbox']}."
            )
        if agent.get("approval_policy") != expected["approval"]:
            errors.append(
                f"{expected_name} approval policy must be {expected['approval']}."
            )
        if agent.get("allow_login_shell") is not False:
            errors.append(f"{expected_name} must disable login shells.")
        if agent.get("web_search") != "disabled":
            errors.append(f"{expected_name} must disable web search.")
        n8n_agent_config = agent.get("mcp_servers", {}).get("n8n", {})
        if n8n_agent_config.get("enabled") is not False:
            errors.append(f"{expected_name} must disable inherited n8n MCP access.")
        if n8n_agent_config.get("url") != "http://127.0.0.1:9/disabled":
            errors.append(f"{expected_name} must override n8n with the disabled HTTP transport.")
        if n8n_agent_config.get("enabled_tools") != []:
            errors.append(f"{expected_name} n8n tool allowlist must be empty.")
        for feature in [
            "apps",
            "browser_use",
            "computer_use",
            "image_generation",
            "in_app_browser",
            "remote_plugin",
        ]:
            if agent.get("features", {}).get(feature) is not False:
                errors.append(f"{expected_name} must disable inherited feature {feature}.")
        node_repl_config = agent.get("mcp_servers", {}).get("node_repl", {})
        if (
            node_repl_config.get("enabled") is not False
            or node_repl_config.get("command") != "/usr/bin/false"
            or node_repl_config.get("enabled_tools") != []
        ):
            errors.append(f"{expected_name} must disable inherited node_repl access.")
        shell_policy = agent.get("shell_environment_policy", {})
        if shell_policy.get("inherit") not in {"core", "none"}:
            errors.append(f"{expected_name} must use a reduced shell environment.")
        if shell_policy.get("ignore_default_excludes") is not False:
            errors.append(f"{expected_name} must retain default secret-variable filtering.")
        excluded_environment = set(shell_policy.get("exclude", []))
        for pattern in {"N8N_*", "*TOKEN*", "*SECRET*", "*PASSWORD*", "*KEY*"}:
            if pattern not in excluded_environment:
                errors.append(f"{expected_name} shell policy is missing {pattern}.")

        if expected["sandbox"] == "workspace-write":
            network_access = (
                agent.get("sandbox_workspace_write", {}).get("network_access")
            )
            if network_access is not False:
                errors.append(f"{expected_name} must disable sandbox network access.")

    config_path = ROOT / ".codex" / "config.toml"
    try:
        config = load_toml(config_path)
    except Exception as exc:
        errors.append(f".codex/config.toml is invalid: {exc}")
        config = {}

    agents_config = config.get("agents", {})
    if agents_config.get("enabled") is not True:
        errors.append("Multi-agent support must be enabled.")
    if agents_config.get("max_concurrent_threads_per_session") != 3:
        errors.append("max_concurrent_threads_per_session must be 3.")
    if config.get("sandbox_mode") != "read-only":
        errors.append("The primary supervisor must default to a read-only sandbox.")
    if config.get("approval_policy") != "on-request":
        errors.append("The primary supervisor must retain interactive approvals.")
    if config.get("sandbox_workspace_write", {}).get("network_access") is not False:
        errors.append("The project workspace sandbox must deny network access by default.")
    if config.get("features", {}).get("hooks") is not True:
        errors.append("Project hooks must be enabled.")
    for feature in [
        "apps",
        "browser_use",
        "computer_use",
        "image_generation",
        "in_app_browser",
        "remote_plugin",
    ]:
        if config.get("features", {}).get(feature) is not False:
            errors.append(f"The primary supervisor must disable feature {feature}.")
    primary_node_repl = config.get("mcp_servers", {}).get("node_repl", {})
    if (
        primary_node_repl.get("enabled") is not False
        or primary_node_repl.get("command") != "/usr/bin/false"
        or primary_node_repl.get("enabled_tools") != []
    ):
        errors.append("The primary supervisor must disable node_repl.")

    orchestration_path = ROOT / "config" / "agent-orchestration.json"
    try:
        orchestration = json.loads(orchestration_path.read_text())
    except Exception as exc:
        errors.append(f"agent-orchestration.json is invalid: {exc}")
        orchestration = {}

    expected_roles = set(EXPECTED)
    configured_roles = set(orchestration.get("roles", []))
    if configured_roles != expected_roles:
        errors.append(
            f"Orchestration roles differ from agent files: {sorted(configured_roles ^ expected_roles)}"
        )
    if orchestration.get("primaryRole") != "supervisor":
        errors.append("The primary orchestration role must be supervisor.")
    if orchestration.get("maxConcurrentChildren") != 3:
        errors.append("Orchestration must cap child agents at 3.")

    module_write_stage = next(
        (
            stage
            for stage in orchestration.get("stages", [])
            if stage.get("name") == "module_write"
        ),
        None,
    )
    if not module_write_stage:
        errors.append("Missing module_write orchestration stage.")
    else:
        if module_write_stage.get("maxParallelModuleBuilders") != 1:
            errors.append("Only one module builder may write at a time.")
        if module_write_stage.get("agents") != ["module_builder"]:
            errors.append("module_write must run only the module builder.")

    stage_by_name = {
        stage.get("name"): stage for stage in orchestration.get("stages", [])
    }
    for writer, reviewer in [
        ("skeleton_write", "skeleton_review"),
        ("module_write", "module_review"),
        ("generalized_tuning_write", "generalized_tuning_review"),
    ]:
        if writer not in stage_by_name:
            errors.append(f"Missing {writer} stage.")
        review_stage = stage_by_name.get(reviewer)
        if not review_stage:
            errors.append(f"Missing {reviewer} stage.")
        else:
            if set(review_stage.get("agents", [])) != {
                "deviation_monitor",
                "security_firewall",
            }:
                errors.append(f"{reviewer} must run monitor and firewall only.")
            if review_stage.get("requiresFinalizedHandoffFrom") != writer:
                errors.append(f"{reviewer} must require a finalized {writer} handoff.")

    for stage in orchestration.get("stages", []):
        unknown = set(stage.get("agents", [])) - expected_roles
        if unknown:
            errors.append(f"Stage {stage.get('name')} references unknown roles: {sorted(unknown)}")
        if len(stage.get("agents", [])) > orchestration.get("maxConcurrentChildren", 0):
            errors.append(f"Stage {stage.get('name')} exceeds the child concurrency cap.")

    hooks_path = ROOT / ".codex" / "hooks.json"
    try:
        hooks = json.loads(hooks_path.read_text())
        stop_hooks = hooks.get("hooks", {}).get("Stop", [])
        command_text = json.dumps(stop_hooks)
        if ".codex/hooks/security-gate.mjs" not in command_text:
            errors.append("Stop hook must invoke the protected .codex security gate.")
        pre_tool_hooks = hooks.get("hooks", {}).get("PreToolUse", [])
        pre_tool_text = json.dumps(pre_tool_hooks)
        if ".codex/hooks/n8n-mutation-gate.mjs" not in pre_tool_text:
            errors.append("PreToolUse must invoke the protected n8n mutation gate.")
        for tool in [
            "create_workflow_from_code",
            "update_workflow",
            "test_workflow",
            "publish_workflow",
            "execute_workflow",
        ]:
            if tool not in pre_tool_text:
                errors.append(f"n8n mutation hook matcher is missing {tool}.")
    except Exception as exc:
        errors.append(f".codex/hooks.json is invalid: {exc}")

    agents_md = (ROOT / "AGENTS.md").read_text()
    if "the primary thread is the supervisor" not in agents_md:
        errors.append("AGENTS.md must bind the primary thread to the supervisor role.")
    if "run one writer, wait for its finalized handoff" not in agents_md:
        errors.append("AGENTS.md must separate writer and post-write review phases.")
    if "validate-agent-run.mjs" not in agents_md:
        errors.append("AGENTS.md must require the machine-validated run ledger.")
    if 'fork_turns = "none"' not in agents_md:
        errors.append("AGENTS.md must require no-history forks for selected custom roles.")

    config_example_path = ROOT / ".codex" / "config.toml.example"
    try:
        config_example = load_toml(config_example_path)
        n8n_config = config_example.get("mcp_servers", {}).get("n8n", {})
        enabled_tools = set(n8n_config.get("enabled_tools", []))
        expected_n8n_tools = {
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
        if enabled_tools != expected_n8n_tools:
            errors.append("Primary n8n example allowlist must exactly match the reviewed set.")
        for tool in [
            "archive_workflow",
            "create_workflow_from_code",
            "execute_workflow",
            "publish_workflow",
            "test_workflow",
            "unpublish_workflow",
            "update_workflow",
        ]:
            if n8n_config.get("tools", {}).get(tool, {}).get("approval_mode") != "prompt":
                errors.append(f"Primary n8n example must prompt for {tool}.")
    except Exception as exc:
        errors.append(f".codex/config.toml.example is invalid: {exc}")

    for required_path in [
        ROOT / ".codex" / "hooks" / "security-gate.mjs",
        ROOT / ".codex" / "hooks" / "grade-agent-eval.mjs",
        ROOT / ".codex" / "hooks" / "n8n-mutation-gate.mjs",
        ROOT / ".codex" / "hooks" / "validate-agent-run.mjs",
        ROOT / ".codex" / "hooks" / "validate-generalized-evals.mjs",
        ROOT / ".codex" / "security-control-hashes.json",
        ROOT / "scripts" / "validate-agent-run.mjs",
        ROOT / "scripts" / "validate-n8n-config.py",
    ]:
        if not required_path.exists():
            errors.append(f"Missing enforcement file: {required_path.relative_to(ROOT)}")

    result = {
        "valid": not errors,
        "agentCount": len(parsed_agents),
        "agents": sorted(parsed_agents),
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
