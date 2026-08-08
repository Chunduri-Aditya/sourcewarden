from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .schema import Source
from .utils import PROJECT_ROOT, load_yaml_config


class SourceRegistry:
    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path = Path(config_path or PROJECT_ROOT / "config" / "sources.yaml")

    def load_sources(self, enabled_only: bool = True) -> list[Source]:
        data = load_yaml_config(self.config_path)
        if not isinstance(data, dict):
            raise ValueError(f"source config must be a mapping: {self.config_path}")

        sources: list[Source] = []
        errors: list[str] = []
        for category, entries in data.items():
            if entries is None:
                continue
            if not isinstance(entries, list):
                errors.append(f"{category}: expected a list of sources")
                continue
            for index, entry in enumerate(entries, start=1):
                if not isinstance(entry, dict):
                    errors.append(f"{category}[{index}]: expected a mapping")
                    continue
                payload = dict(entry)
                payload.setdefault("category", category)
                try:
                    source = Source.model_validate(payload)
                except Exception as exc:
                    errors.append(f"{category}[{index}]: {exc}")
                    continue
                if enabled_only and not source.enabled:
                    continue
                sources.append(source)

        if errors:
            raise ValueError("invalid sources.yaml:\n" + "\n".join(errors))
        return sources

    def duplicate_urls(self, enabled_only: bool = True) -> dict[str, list[Source]]:
        grouped: dict[str, list[Source]] = {}
        for source in self.load_sources(enabled_only=enabled_only):
            grouped.setdefault(normalize_source_url(source.url), []).append(source)
        return {url: sources for url, sources in grouped.items() if len(sources) > 1}

    def assert_no_duplicate_urls(self, enabled_only: bool = True) -> None:
        duplicates = self.duplicate_urls(enabled_only=enabled_only)
        if not duplicates:
            return
        lines: list[str] = []
        for url, sources in sorted(duplicates.items()):
            titles = ", ".join(f"{source.category}/{source.title}" for source in sources)
            lines.append(f"{url}: {titles}")
        raise ValueError("duplicate source URLs found:\n" + "\n".join(lines))

    def by_rag(self, enabled_only: bool = True) -> dict[str, list[Source]]:
        grouped: dict[str, list[Source]] = {}
        for source in self.load_sources(enabled_only=enabled_only):
            grouped.setdefault(source.rag_target, []).append(source)
        return grouped

    def categories(self) -> list[str]:
        data = load_yaml_config(self.config_path)
        if not isinstance(data, dict):
            return []
        return list(data.keys())


def normalize_source_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))
