"""Gated, offline self-improvement proposal tooling."""

from .core import (
    ContractError,
    prepare_baseline,
    record_feedback,
    status_for_run,
    validate_candidate,
)

__all__ = [
    "ContractError",
    "prepare_baseline",
    "record_feedback",
    "status_for_run",
    "validate_candidate",
]

