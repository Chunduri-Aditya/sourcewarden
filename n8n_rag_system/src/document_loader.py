from __future__ import annotations

from dataclasses import dataclass
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .schema import Source, schema_to_dict
from .utils import ensure_dir, slugify, utc_now_iso, write_json, write_jsonl


DEFAULT_USER_AGENT = "n8n-rag-system/0.2 (+local official docs ingestion)"


@dataclass
class DownloadResult:
    source_title: str
    url: str
    status: str
    raw_path: str | None = None
    metadata_path: str | None = None
    error: str | None = None
    attempts: int = 0
    status_code: int | None = None


class DocumentLoader:
    def __init__(self, raw_dir: str | Path) -> None:
        self.raw_dir = ensure_dir(raw_dir)
        self.failure_log_path = self.raw_dir / "source_failures.jsonl"
        self.status_report_path = self.raw_dir / "source_status.json"

    def fetch_source(
        self,
        source: Source,
        force: bool = False,
        timeout: int = 25,
        retries: int = 2,
        retry_delay: float = 1.0,
        user_agent: str = DEFAULT_USER_AGENT,
        dry_run: bool = False,
    ) -> DownloadResult:
        stem = slugify(f"{source.category}-{source.title}")
        raw_path = self.raw_dir / f"{stem}{extension_for_url(source.url)}"
        metadata_path = self.raw_dir / f"{stem}.metadata.json"

        if dry_run:
            return DownloadResult(
                source_title=source.title,
                url=source.url,
                status="dry_run",
                raw_path=str(raw_path),
                metadata_path=str(metadata_path),
            )

        if raw_path.exists() and metadata_path.exists() and not force:
            metadata = schema_to_dict(source)
            metadata.update(
                {
                    "last_seen_at": utc_now_iso(),
                    "raw_path": str(raw_path),
                    "status": "skipped_existing",
                }
            )
            write_json(metadata_path, metadata)
            return DownloadResult(
                source_title=source.title,
                url=source.url,
                status="skipped_existing",
                raw_path=str(raw_path),
                metadata_path=str(metadata_path),
            )

        attempts = max(1, retries + 1)
        last_error: str | None = None
        for attempt in range(1, attempts + 1):
            try:
                request = Request(
                    source.url,
                    headers={
                        "User-Agent": user_agent,
                        "Accept": "text/markdown, text/html, text/plain;q=0.9,*/*;q=0.8",
                    },
                )
                with urlopen(request, timeout=timeout) as response:
                    body = response.read()
                    content_type = response.headers.get("content-type", "")
                    status_code = getattr(response, "status", 200)
                text = body.decode("utf-8", errors="replace")
                raw_path.write_text(text, encoding="utf-8")
                metadata = schema_to_dict(source)
                metadata.update(
                    {
                        "fetched_at": utc_now_iso(),
                        "content_type": content_type,
                        "status_code": status_code,
                        "raw_path": str(raw_path),
                        "attempts": attempt,
                        "status": "downloaded",
                    }
                )
                write_json(metadata_path, metadata)
                return DownloadResult(
                    source_title=source.title,
                    url=source.url,
                    status="downloaded",
                    raw_path=str(raw_path),
                    metadata_path=str(metadata_path),
                    attempts=attempt,
                    status_code=status_code,
                )
            except HTTPError as exc:
                last_error = f"HTTP {exc.code}: {exc.reason}"
                if 400 <= exc.code < 500 and exc.code != 429:
                    break
            except (OSError, TimeoutError, URLError) as exc:
                last_error = str(exc)
            if attempt < attempts:
                time.sleep(retry_delay)

        failure_metadata = schema_to_dict(source)
        failure_metadata.update(
            {
                "fetched_at": utc_now_iso(),
                "raw_path": str(raw_path),
                "attempts": attempts,
                "status": "failed",
                "error": last_error,
            }
        )
        write_json(metadata_path, failure_metadata)
        return DownloadResult(
            source_title=source.title,
            url=source.url,
            status="failed",
            raw_path=str(raw_path),
            metadata_path=str(metadata_path),
            error=last_error,
            attempts=attempts,
        )

    def fetch_all(
        self,
        sources: list[Source],
        force: bool = False,
        timeout: int = 25,
        retries: int = 2,
        user_agent: str = DEFAULT_USER_AGENT,
        dry_run: bool = False,
    ) -> list[DownloadResult]:
        results = [
            self.fetch_source(
                source,
                force=force,
                timeout=timeout,
                retries=retries,
                user_agent=user_agent,
                dry_run=dry_run,
            )
            for source in sources
        ]
        self.write_status_report(results)
        return results

    def write_status_report(self, results: list[DownloadResult]) -> None:
        rows = [
            {
                "source_title": result.source_title,
                "url": result.url,
                "status": result.status,
                "raw_path": result.raw_path,
                "metadata_path": result.metadata_path,
                "error": result.error,
                "attempts": result.attempts,
                "status_code": result.status_code,
                "reported_at": utc_now_iso(),
            }
            for result in results
        ]
        write_json(self.status_report_path, rows)
        failures = [row for row in rows if row["status"] == "failed"]
        write_jsonl(self.failure_log_path, failures)


def extension_for_url(url: str) -> str:
    lowered = url.lower().split("?", 1)[0]
    if lowered.endswith(".md") or lowered.endswith(".markdown"):
        return ".md"
    if lowered.endswith(".txt"):
        return ".txt"
    return ".html"
