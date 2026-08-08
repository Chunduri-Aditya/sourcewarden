from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cleaner import clean_markdown, html_to_markdown


class CleanerTests(unittest.TestCase):
    def test_cleaner_preserves_headings_code_and_tables(self) -> None:
        html = """
        <html><body><nav>Noise</nav><main>
        <h1>Title</h1>
        <p>Intro</p>
        <pre><code>return items;</code></pre>
        <table><tr><th>Name</th><th>Value</th></tr><tr><td>A</td><td>B</td></tr></table>
        <div class="admonition warning"><p>Be careful</p></div>
        </main></body></html>
        """
        markdown = html_to_markdown(html)
        self.assertIn("# Title", markdown)
        self.assertIn("```text", markdown)
        self.assertIn("return items;", markdown)
        self.assertIn("|", markdown)
        self.assertIn("Be careful", markdown)
        self.assertNotIn("Noise", markdown)

    def test_markdown_input_is_preserved(self) -> None:
        markdown = clean_markdown("# Title\n\n```js\nreturn items;\n```\n\n| A | B |\n| - | - |")
        self.assertIn("# Title", markdown)
        self.assertIn("```js", markdown)
        self.assertIn("| A | B |", markdown)


if __name__ == "__main__":
    unittest.main()
