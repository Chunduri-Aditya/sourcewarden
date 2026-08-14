from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAG_ROOT = REPO_ROOT / "n8n_rag_system"

# Matches scripts/retrieve-rag-context.py's sys.path pattern: make both the
# repo root (for self_improvement) and n8n_rag_system (for src.*) importable
# before any web module reaches into either package.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(RAG_ROOT) not in sys.path:
    sys.path.insert(0, str(RAG_ROOT))

EVALS_RESULTS_DIR = REPO_ROOT / "evals" / "results"
TUNING_PROPOSALS_DIR = REPO_ROOT / "tuning" / "proposals"
MODULE_MANIFEST_PATH = REPO_ROOT / "config" / "module-manifest.json"
SECURITY_HASHES_PATH = REPO_ROOT / ".codex" / "security-control-hashes.json"
