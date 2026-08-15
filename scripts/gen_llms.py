"""Generate llms.txt and llms-full.txt for the built site.

Adapted from django-div's scripts/llms.py. Zensical has no plugin API yet and
no llms.txt support, so this runs as a post-build step.

Awesome Django is a single long page: README.md is the source of truth and
docs/README.md is a symlink to it, so neither the GitHub README nor the site
can drift from what this reads. Everything else -- name, summary, URL -- comes
from zensical.toml.

  llms.txt       an index: an H1, a blockquote summary, then the category
                 headings from the README as links to their on-site anchors.
  llms-full.txt  the complete text of the list, verbatim.

See https://llmstxt.org/ for the format.

Usage: python scripts/gen_llms.py [site_dir]
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "zensical.toml"
README = ROOT / "README.md"

# Headings that structure the page but are not categories to link to.
SKIP_HEADINGS = {"Contents", "Footnotes"}


def config() -> dict:
    return tomllib.loads(CONFIG.read_text())["project"]


def slugify(text: str) -> str:
    """Anchor id for a heading, matching python-markdown's toc extension:
    lowercase, strip everything but word chars/space/hyphen, spaces -> hyphens.
    """
    slug = text.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    return re.sub(r"[\s]+", "-", slug)


def readme_body() -> str:
    """The README with its doctoc-generated TOC block removed.

    The TOC is navigation doctoc rewrites on every build; the headings it
    points at are the real content, so keeping both would just duplicate the
    category list.
    """
    body = README.read_text()
    return re.sub(
        r"<!-- START doctoc.*?<!-- END doctoc[^>]*-->\n?",
        "",
        body,
        flags=re.DOTALL,
    )


def headings(body: str) -> list[tuple[int, str]]:
    """(level, text) for each ``##``/``###`` heading, TOC/footnotes aside.

    Fenced code blocks are skipped so a ``#`` comment inside one is never
    mistaken for a heading.
    """
    found = []
    in_fence = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^(#{2,3})\s+(.*)$", line)
        if not match:
            continue
        text = match.group(2).strip()
        if text in SKIP_HEADINGS:
            continue
        found.append((len(match.group(1)), text))
    return found


def build_llms_txt(project: dict, body: str) -> str:
    base_url = project.get("site_url", "").rstrip("/")
    lines = [
        f"# {project['site_name']}",
        "",
        f"> {project['site_description']}.",
        "",
        f"- The complete list is available as text at {base_url}/llms-full.txt.",
        "",
        "## Categories",
        "",
    ]
    seen: dict[str, int] = {}
    for level, text in headings(body):
        # python-markdown disambiguates a repeated heading id with _1, _2, ...
        slug = slugify(text)
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        anchor = slug if count == 0 else f"{slug}_{count}"
        indent = "  " * (level - 2)  # ## flush left, ### indented one step
        lines.append(f"{indent}- [{text}]({base_url}/#{anchor})")

    lines += [
        "",
        "## Optional",
        "",
        f"- [Source]({project['repo_url']}): the repository and"
        " contribution guidelines.",
    ]
    return "\n".join(lines) + "\n"


def build_llms_full_txt(project: dict, body: str) -> str:
    base_url = project.get("site_url", "").rstrip("/")
    header = [
        f"# {project['site_name']} - Full Text",
        "",
        f"> {project['site_description']}.",
        "",
        f"- An index of links is available at {base_url}/llms.txt.",
        f"- Source: {project['repo_url']}",
        "",
        "---",
        "",
    ]
    return "\n".join(header) + body.strip() + "\n"


def main() -> int:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
    if not site.is_dir():
        print(f"error: {site} does not exist -- build the site first", file=sys.stderr)
        return 1

    project = config()
    body = readme_body()

    for name, text in (
        ("llms.txt", build_llms_txt(project, body)),
        ("llms-full.txt", build_llms_full_txt(project, body)),
    ):
        target = site / name
        target.write_text(text, encoding="utf-8")
        print(f"wrote {target} ({target.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
