from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str, max_length: int = 80) -> str:
    value = value.lower().strip()
    value = re.sub(r"https?://", "", value)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:max_length].strip("-") or "source"


def stable_id(*parts: str, length: int = 16) -> str:
    joined = "||".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:length]


def approx_token_count(text: str) -> int:
    # A lightweight approximation that is good enough for chunk boundaries.
    return max(1, len(re.findall(r"\S+", text)))


def compact_blank_lines(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_dotenv(path: str | Path | None = None) -> None:
    path = Path(path or PROJECT_ROOT / ".env")
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def read_json(path: str | Path, default: Any = None) -> Any:
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            rows.append(json.loads(stripped))
    return rows


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def load_yaml_config(path: str | Path) -> Any:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except Exception:
        pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return _simple_yaml_load(text)


def _simple_yaml_load(text: str) -> dict[str, Any]:
    """Small YAML subset parser used when PyYAML is not installed.

    It supports the config style used in this package: top-level mappings,
    lists of scalar values, and lists of flat dictionaries.
    """

    result: dict[str, Any] = {}
    current_key: str | None = None
    current_item: dict[str, Any] | None = None

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if indent == 0 and ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            parsed_value = _parse_scalar(value)
            result[current_key] = parsed_value
            current_item = None
            continue

        if current_key is None:
            continue

        if indent == 2 and line.startswith("- "):
            if not isinstance(result.get(current_key), list):
                result[current_key] = []
            rest = line[2:].strip()
            if ":" in rest:
                item_key, item_value = rest.split(":", 1)
                current_item = {item_key.strip(): _parse_scalar(item_value)}
                result[current_key].append(current_item)
            else:
                result[current_key].append(_parse_scalar(rest))
                current_item = None
            continue

        if indent >= 4 and current_item is not None and ":" in line:
            item_key, item_value = line.split(":", 1)
            current_item[item_key.strip()] = _parse_scalar(item_value)
            continue

        if indent == 2 and ":" in line:
            if not isinstance(result.get(current_key), dict):
                result[current_key] = {}
            child_key, child_value = line.split(":", 1)
            result[current_key][child_key.strip()] = _parse_scalar(child_value)

    return result


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    lowered = value.lower()
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def strip_front_matter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) == 3:
        return parts[2].lstrip()
    return text

