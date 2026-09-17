"""Parse Markdown and validate repository-local destinations without network I/O."""

from dataclasses import asdict, dataclass, field
from difflib import get_close_matches
from fnmatch import fnmatch
from html.parser import HTMLParser
import os
from pathlib import Path
import unicodedata
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

MARKDOWN = {".md", ".markdown"}
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build"}


@dataclass(frozen=True)
class Link:
    target: str
    line: int


@dataclass
class Document:
    links: list[Link] = field(default_factory=list)
    anchors: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Issue:
    file: str
    line: int
    target: str
    code: str
    message: str
    suggestion: str | None = None


@dataclass
class Report:
    files_checked: int = 0
    links_checked: int = 0
    links_skipped: int = 0
    issues: list[Issue] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"schema_version": 1, **asdict(self)}


class _HTMLAnchors(HTMLParser):
    def __init__(self, anchors: set[str]):
        super().__init__()
        self.anchors = anchors

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value and (key == "id" or (tag == "a" and key == "name")):
                self.anchors.add(value)


def _plain(tokens) -> str:
    return "".join(
        _plain(t.children) if t.type == "image" and t.children else
        t.content if t.type in {"text", "code_inline", "image"} else
        " " if t.type in {"softbreak", "hardbreak"} else ""
        for t in tokens
    )


def slug(text: str) -> str:
    """GitHub-style anchors for common headings; see compatibility documentation."""
    return "".join(
        c for c in text.lower()
        if c in " -_" or unicodedata.category(c)[0] in "LNM"
    ).replace(" ", "-")


def parse_document(text: str) -> Document:
    # Ignore YAML front matter while preserving original source line numbers.
    lines = text.splitlines(keepends=True)
    if lines and lines[0].strip() == "---":
        for end in range(1, len(lines)):
            if lines[end].strip() in {"---", "..."}:
                lines[:end + 1] = ["\n"] * (end + 1)
                break
    tokens = MarkdownIt("commonmark").enable(["table", "strikethrough"]).parse("".join(lines))
    doc = Document()
    used: set[str] = set()
    html = _HTMLAnchors(doc.anchors)
    for index, token in enumerate(tokens):
        if token.type == "heading_open":
            base = slug(_plain(tokens[index + 1].children or []))
            anchor, suffix = base, 0
            while anchor in used:
                suffix += 1
                anchor = f"{base}-{suffix}"
            used.add(anchor)
            doc.anchors.add(anchor)
        if token.type == "html_block":
            html.feed(token.content)
        if token.type != "inline":
            continue
        line = (token.map[0] + 1) if token.map else 1
        for child in token.children or []:
            if child.type in {"softbreak", "hardbreak"}:
                line += 1
            elif child.type in {"link_open", "image"}:
                doc.links.append(Link(child.attrGet("href" if child.type == "link_open" else "src") or "", line))
            elif child.type == "html_inline":
                html.feed(child.content)
    return doc


def _inside(path: Path, root: Path) -> bool:
    return path.is_relative_to(root)


def discover(root: Path, inputs: list[str], excludes: list[str]) -> list[Path]:
    found: set[Path] = set()

    def excluded(path: Path) -> bool:
        rel = path.relative_to(root).as_posix()
        return any(fnmatch(rel, pattern) for pattern in excludes)

    def add(path: Path):
        if path.suffix.lower() in MARKDOWN and not excluded(path):
            if not _inside(path.resolve(), root):
                raise ValueError(f"Source escapes repository root: {path}")
            found.add(path)

    def walk_error(error):
        raise error

    for value in inputs or ["."]:
        source = root / value
        source = Path(os.path.abspath(source))
        if not _inside(source, root) or not _inside(source.resolve(), root):
            raise ValueError(f"Input escapes repository root: {value}")
        if not source.exists():
            raise ValueError(f"Input does not exist: {value}")
        if source.is_file():
            add(source)
        else:
            for directory, dirs, files in os.walk(source, onerror=walk_error, followlinks=False):
                parent = Path(directory)
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS
                                 and not (parent / d).is_symlink() and not excluded(parent / d))
                for name in sorted(files):
                    add(parent / name)
    return sorted(found)


def check(root: Path, inputs: list[str] | None = None, excludes: list[str] | None = None) -> Report:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Repository root is not a directory: {root}")
    sources = discover(root, inputs or [], excludes or [])
    if not sources:
        raise ValueError("No Markdown files found; check the input paths and exclusions")
    cache: dict[Path, Document] = {}

    def read(path: Path) -> Document:
        if path not in cache:
            cache[path] = parse_document(path.read_text(encoding="utf-8-sig"))
        return cache[path]

    report = Report(files_checked=len(sources))
    for source in sources:
        name = source.relative_to(root).as_posix()
        try:
            document = read(source)
        except (OSError, UnicodeError) as exc:
            report.issues.append(Issue(name, 1, "", "unreadable-file", str(exc)))
            continue
        for link in document.links:
            def fail(code, message, suggestion=None):
                report.issues.append(Issue(name, link.line, link.target, code, message, suggestion))

            try:
                url = urlsplit(link.target)
            except ValueError:
                report.links_checked += 1
                fail("invalid-url", "Cannot parse link destination")
                continue
            if url.scheme or url.netloc or link.target.startswith("//"):
                report.links_skipped += 1
                continue
            report.links_checked += 1
            path, anchor = unquote(url.path), unquote(url.fragment)
            if "\x00" in path or "\\" in path:
                fail("invalid-path", "Use a portable path without NUL or backslash characters")
                continue
            target = (root / path.lstrip("/") if path.startswith("/") else
                      source.parent / path if path else source)
            try:
                target = target.resolve()
                if not _inside(target, root):
                    fail("outside-root", "Destination escapes the repository root")
                    continue
                if not target.exists():
                    candidates = sorted(p.name for p in target.parent.iterdir()) if target.parent.is_dir() else []
                    matches = get_close_matches(target.name, candidates, n=1, cutoff=0.65)
                    fail("missing-file", "Destination does not exist", matches[0] if matches else None)
                    continue
                if anchor and target.is_file() and target.suffix.lower() in MARKDOWN:
                    anchors = read(target).anchors
                    if anchor not in anchors:
                        matches = get_close_matches(anchor, sorted(anchors), n=1, cutoff=0.6)
                        fail("missing-anchor", f"Heading or HTML anchor #{anchor} does not exist",
                             "#" + matches[0] if matches else None)
            except (OSError, UnicodeError, RuntimeError) as exc:
                fail("unreadable-target", str(exc))
    return report
