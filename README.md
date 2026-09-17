# DocRoute

**Keep your documentation connected.** Catch broken local Markdown links and heading anchors before they reach your readers.

[![CI](https://github.com/AlirezaSharbaf/docroute/actions/workflows/ci.yml/badge.svg)](https://github.com/AlirezaSharbaf/docroute/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

Renaming a guide or changing a heading can quietly break links across a repository.
DocRoute checks those connections locally, with no API key, network requests, or hosted service.
It is an early-stage project focused on documentation stored alongside code.

```text
docs/start.md:12: missing-anchor: Heading or HTML anchor #installaton does not exist (#installaton); did you mean #installation?
4 file(s), 18 local link(s), 3 external link(s) skipped, 1 issue(s)
```

The output above is illustrative. Run the included [demo](examples/demo/README.md) for a passing example.

## What it checks

- Relative links, repository-root links, images, and reference-style links.
- Heading fragments across Markdown files, including repeated headings.
- Explicit HTML `id` and anchor `name` destinations inside Markdown.
- Percent-encoded filenames, Unicode headings, and paths containing parentheses.
- Missing files and anchors, with close-match suggestions when available.
- Destinations outside the repository root, including resolved symlinks.

Code blocks, inline code, comments, and YAML front matter are ignored. External URLs
are counted and skipped. Checks use a Markdown parser, not a regex over source text.

## Quick start

Requires Python 3.10 or later. Installation downloads dependencies; running the checker is offline.
The project is distributed from this repository and is **not published to PyPI**.

```sh
git clone https://github.com/AlirezaSharbaf/docroute.git
cd docroute
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install .
docroute
```

Check another repository or selected files:

```sh
docroute --root /path/to/your/repository
docroute --root /path/to/your/repository README.md docs
docroute --exclude 'generated/*' --exclude 'vendor/*'
docroute --format json
docroute --format github
```

All input paths and exclusion patterns are relative to `--root`. Without `--root`, the
current directory is the root. Quote glob patterns so your shell does not expand them.

Exit codes: **0** means no findings, **1** means broken links or unreadable Markdown,
and **2** means an input/configuration error (including finding no Markdown files).

## GitHub Actions

Add this job to a workflow in the repository you want to check. For reproducible use,
replace `main` in the install URL with a reviewed commit SHA.

```yaml
name: Documentation links
on: [push, pull_request]
permissions:
  contents: read
jobs:
  links:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python -m pip install 'git+https://github.com/AlirezaSharbaf/docroute.git@main'
      - run: docroute --format github
```

The GitHub format emits escaped error annotations and returns a failing exit code for
broken links. No write token or pull-request comments are needed.

## Pre-commit

Use the hook in [.pre-commit-hooks.yaml](.pre-commit-hooks.yaml) with a reviewed commit SHA
as the `rev` in your pre-commit configuration. The hook scans the whole repository so a
heading change can catch a broken link in a different file. It also runs when non-Markdown
files change, since those files may be link destinations.

## Scope and compatibility

DocRoute checks source repositories, not rendered websites. It does not check HTTP status,
site-generator routes, MDX, raw HTML `href`/`src` links, or fragments in non-Markdown files.
Undefined Markdown references are plain text under CommonMark and are not reported.
Directory links pass when the directory exists; DocRoute does not assume an index file.

Heading IDs use GitHub-style rules for common headings. Unusual punctuation, emoji
shortcodes, raw HTML headings, and renderer-specific extensions can differ from GitHub
or your site generator. See [compatibility details](docs/compatibility.md).

## Contributing

Bug reports with a small Markdown example are especially useful. See
[CONTRIBUTING.md](CONTRIBUTING.md), the [roadmap](docs/roadmap.md), and the
[security policy](SECURITY.md).

```sh
python -m pip install -e '.[dev]'
python -m pytest -q
docroute
```

Maintained by [Alireza Sharbafchi](https://github.com/AlirezaSharbaf). Licensed under [MIT](LICENSE).
