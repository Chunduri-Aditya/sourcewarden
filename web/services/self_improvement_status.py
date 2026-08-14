from __future__ import annotations

from typing import Any

from self_improvement.core import RUN_ID_RE, ContractError, status_for_run
from web.paths import EVALS_RESULTS_DIR, REPO_ROOT, TUNING_PROPOSALS_DIR


def discover_run_ids() -> list[str]:
    """Union of run-id-shaped subdirectory names under evals/results/ and
    tuning/proposals/. Either directory may be absent; both absent returns
    an empty list.
    """
    run_ids: set[str] = set()
    for directory in (EVALS_RESULTS_DIR, TUNING_PROPOSALS_DIR):
        if not directory.is_dir():
            continue
        for entry in directory.iterdir():
            if entry.is_dir() and RUN_ID_RE.fullmatch(entry.name):
                run_ids.add(entry.name)
    return sorted(run_ids)


def status_for_all_runs() -> list[dict[str, Any]]:
    """Read-only status for every discovered run.

    Each entry is `{"run_id": ..., "ok": True, "data": ...}` on success or
    `{"run_id": ..., "ok": False, "error": ...}` when self_improvement.core's
    contract checks reject that one run. A per-run ContractError never
    aborts the rest of the batch. Zero discovered runs returns an empty
    list, not an exception.
    """
    results: list[dict[str, Any]] = []
    for run_id in discover_run_ids():
        try:
            data = status_for_run(REPO_ROOT, run_id)
        except ContractError as error:
            results.append(
                {"run_id": run_id, "ok": False, "error": f"{error.code}: {error.detail}"}
            )
        else:
            results.append({"run_id": run_id, "ok": True, "data": data})
    return results
