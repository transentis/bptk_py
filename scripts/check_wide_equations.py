"""Find display equations that are wider than the text column of their page.

    just docs-serve          # in another terminal
    just docs-equations

A LaTeX equation does not wrap. Wider than the column, it runs over the page's right
edge, and nothing in the render says so - the HTML is valid, `docs-check` is green.
Only a browser knows how wide MathJax set it, so this measures there: every page of
the rendered site at a desktop width, each display equation against the width of
the main column. Exit status 1 if any is wider.

Needs `playwright` - `just docs-equations` brings it along with `uv run --with`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

MEASURE = """() => {
  const column = (document.querySelector('main') || document.body).getBoundingClientRect().width;
  return [...document.querySelectorAll('mjx-container[display="true"]')].map(m => {
    const inner = m.firstElementChild ? m.firstElementChild.getBoundingClientRect().width : 0;
    return [Math.round(Math.max(m.scrollWidth, inner)), Math.round(column),
            (m.textContent || '').replace(/\\s+/g, ' ').slice(0, 50)];
  });
}"""


def has_display_math(path: Path) -> bool:
    text = path.read_text(encoding="utf8", errors="replace")
    return "$$" in text or "\\begin{equation" in text or "\\[" in text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("site", nargs="?", default="website-tutorial/_output")
    parser.add_argument("--host", default="http://localhost:4201")
    parser.add_argument("--width", type=int, default=1280, help="viewport width in pixels")
    arguments = parser.parse_args()

    root = Path(arguments.site)
    pages = sorted(path.relative_to(root).as_posix() for path in root.rglob("*.html")
                   if "site_libs" not in path.parts and "marimo-islands" not in path.parts
                   and has_display_math(path))

    from playwright.sync_api import sync_playwright

    wide = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": arguments.width, "height": 900})
        for path in pages:
            page.goto(f"{arguments.host}/{path}", wait_until="load")
            # MathJax typesets after load; give it the time it takes.
            page.wait_for_timeout(2000)
            for width, column, text in page.evaluate(MEASURE):
                if width > column:
                    wide.append(f"{path}: {width} px in a column of {column} px - {text!r}")
        browser.close()

    print(f"Pages with equations:    {len(pages)}")
    print(f"Wider than the column:   {len(wide)}")
    for line in wide:
        print(f"  {line}")
    return 1 if wide else 0


if __name__ == "__main__":
    sys.exit(main())
