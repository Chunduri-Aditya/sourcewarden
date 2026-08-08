from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from .utils import compact_blank_lines, ensure_dir, read_json, utc_now_iso, write_json


class _HTMLToMarkdownParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0
        self.heading_level: int | None = None
        self.in_pre = False
        self.in_link_href: str | None = None
        self.in_table_row = False
        self.in_admonition = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg", "header", "footer", "nav", "aside"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        attrs_dict = {key: value for key, value in attrs}
        classes = " ".join(
            value for key, value in attrs if key == "class" and value
        ).lower()
        if any(name in classes for name in ["admonition", "warning", "note", "caution", "tip", "danger"]):
            self._newline(2)
            self.parts.append("> ")
            self.in_admonition = True
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._newline(2)
            self.heading_level = int(tag[1])
            self.parts.append("#" * self.heading_level + " ")
        elif tag in {"p", "section", "article", "div"}:
            self._newline(1)
        elif tag == "br":
            self.parts.append("\n")
        elif tag == "li":
            self._newline(1)
            self.parts.append("- ")
        elif tag == "pre":
            self._newline(2)
            self.parts.append("```text\n")
            self.in_pre = True
        elif tag == "code" and not self.in_pre:
            self.parts.append("`")
        elif tag == "a":
            self.in_link_href = attrs_dict.get("href")
        elif tag in {"tr"}:
            self._newline(1)
            self.parts.append("|")
            self.in_table_row = True
        elif tag in {"td", "th"}:
            if not self.in_table_row:
                self.parts.append("|")
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg", "header", "footer", "nav", "aside"}:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_level = None
            self._newline(2)
        elif tag in {"p", "section", "article", "div", "ul", "ol", "li", "table"}:
            self._newline(1)
            if tag in {"div", "section"}:
                self.in_admonition = False
        elif tag == "pre":
            self.parts.append("\n```\n")
            self.in_pre = False
        elif tag == "code" and not self.in_pre:
            self.parts.append("`")
        elif tag == "a":
            if self.in_link_href:
                self.parts.append(f" ({self.in_link_href})")
            self.in_link_href = None
        elif tag in {"td", "th"}:
            self.parts.append(" |")
        elif tag == "tr":
            self.in_table_row = False
            self._newline(1)

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.in_pre:
            self.parts.append(data)
        else:
            cleaned = re.sub(r"\s+", " ", data)
            if cleaned.strip():
                self.parts.append(cleaned)

    def markdown(self) -> str:
        return compact_blank_lines(html.unescape("".join(self.parts)))

    def _newline(self, count: int) -> None:
        current = "".join(self.parts[-3:])
        needed = "\n" * count
        if not current.endswith(needed):
            self.parts.append(needed)


def html_to_markdown(raw_html: str) -> str:
    try:
        from bs4 import BeautifulSoup  # type: ignore

        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "aside"]):
            tag.decompose()
        for tag in soup.find_all(class_=re.compile(r"(md-sidebar|toc|navigation|breadcrumbs|footer|header)", re.I)):
            tag.decompose()
        main = soup.find("main") or soup.find("article") or soup.body or soup
        parser = _HTMLToMarkdownParser()
        parser.feed(str(main))
        return parser.markdown()
    except Exception:
        parser = _HTMLToMarkdownParser()
        parser.feed(raw_html)
        return parser.markdown()


def is_markdown_input(raw_path: Path, metadata: dict[str, Any], raw_text: str) -> bool:
    content_type = str(metadata.get("content_type", "")).lower()
    source_url = str(metadata.get("url") or metadata.get("source_url") or "").lower()
    return (
        raw_path.suffix.lower() in {".md", ".markdown", ".txt"}
        or source_url.endswith((".md", ".markdown", ".txt"))
        or "markdown" in content_type
        or raw_text.lstrip().startswith("#")
    )


def clean_markdown(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return compact_blank_lines(text)


def extract_html_title_and_canonical(raw_html: str, fallback_url: str = "") -> tuple[str | None, str | None]:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, flags=re.I | re.S)
    title = html.unescape(re.sub(r"\s+", " ", title_match.group(1)).strip()) if title_match else None
    canonical_match = re.search(
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
        raw_html,
        flags=re.I,
    )
    canonical = urljoin(fallback_url, canonical_match.group(1)) if canonical_match else None
    return title, canonical


def clean_raw_file(raw_path: str | Path, processed_dir: str | Path, force: bool = False) -> dict[str, Any]:
    raw_path = Path(raw_path)
    processed_dir = ensure_dir(processed_dir)
    metadata_path = raw_path.with_suffix(".metadata.json")
    if not metadata_path.exists():
        metadata_path = raw_path.with_name(raw_path.stem + ".metadata.json")
    metadata = read_json(metadata_path, default={}) or {}

    output_path = processed_dir / f"{raw_path.stem}.md"
    output_metadata_path = processed_dir / f"{raw_path.stem}.metadata.json"
    if output_path.exists() and output_metadata_path.exists() and not force:
        return {
            "status": "skipped_existing",
            "processed_path": str(output_path),
            "metadata_path": str(output_metadata_path),
        }

    raw_text = raw_path.read_text(encoding="utf-8", errors="replace")
    source_url = metadata.get("url") or metadata.get("source_url") or ""
    if is_markdown_input(raw_path, metadata, raw_text):
        cleaned = clean_markdown(raw_text)
        title = metadata.get("title") or metadata.get("source_title") or raw_path.stem
        canonical_url = source_url
    else:
        html_title, canonical_url = extract_html_title_and_canonical(raw_text, fallback_url=source_url)
        cleaned = html_to_markdown(raw_text)
        title = metadata.get("title") or metadata.get("source_title") or html_title or raw_path.stem
    if title and not cleaned.lstrip().startswith("#"):
        cleaned = f"# {title}\n\n{cleaned}"

    cleaned_metadata = {
        "source_title": metadata.get("title") or metadata.get("source_title") or title,
        "source_url": canonical_url or source_url,
        "category": metadata.get("category") or "",
        "rag_target": metadata.get("rag_target") or "",
        "priority": metadata.get("priority") or "medium",
        "cleaned_at": utc_now_iso(),
        "raw_path": str(raw_path),
        "source_type": metadata.get("source_type") or "",
        "page_title": title,
        "canonical_url": canonical_url or source_url,
    }

    front_matter = "\n".join(
        [
            "---",
            f"source_title: {cleaned_metadata['source_title']}",
            f"source_url: {cleaned_metadata['source_url']}",
            f"category: {cleaned_metadata['category']}",
            f"rag_target: {cleaned_metadata['rag_target']}",
            f"priority: {cleaned_metadata['priority']}",
            f"cleaned_at: {cleaned_metadata['cleaned_at']}",
            f"canonical_url: {cleaned_metadata['canonical_url']}",
            "---",
            "",
        ]
    )
    output_path.write_text(front_matter + compact_blank_lines(cleaned) + "\n", encoding="utf-8")
    write_json(output_metadata_path, cleaned_metadata)
    return {
        "status": "cleaned",
        "processed_path": str(output_path),
        "metadata_path": str(output_metadata_path),
    }


def clean_all(raw_dir: str | Path, processed_dir: str | Path, force: bool = False) -> list[dict[str, Any]]:
    raw_dir = Path(raw_dir)
    results: list[dict[str, Any]] = []
    raw_paths = [
        path
        for pattern in ("*.html", "*.md", "*.markdown", "*.txt")
        for path in raw_dir.glob(pattern)
        if not path.name.endswith(".metadata.json")
    ]
    for raw_path in sorted(set(raw_paths)):
        try:
            results.append(clean_raw_file(raw_path, processed_dir=processed_dir, force=force))
        except Exception as exc:
            results.append({"status": "failed", "raw_path": str(raw_path), "error": str(exc)})
    return results
