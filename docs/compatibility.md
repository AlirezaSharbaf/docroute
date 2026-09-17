# Compatibility and output contract

## Markdown dialect

DocRoute uses markdown-it-py in CommonMark mode, with tables and strikethrough enabled.
It recognizes `.md` and `.markdown` files, case-insensitively. Files are decoded as UTF-8
with an optional byte-order mark. YAML front matter is ignored if the first line is
`---` and a closing `---` or `...` line exists.

Raw HTML is inspected only for `id` attributes and `<a name="...">` anchors. HTML links,
JSX/MDX expressions, template variables, and extensions such as footnotes are not checked.
Only references that the Markdown parser resolves into links are checked.

## Heading anchors

The slug comes from rendered inline text (including inline code and image alt text).
It is lowercased; Unicode letters, numbers, and combining marks are retained, along
with spaces, hyphens, and underscores. Other characters are removed. Each space becomes
a hyphen. Repeated slugs receive `-1`, `-2`, and so on, avoiding previously generated IDs.
ATX and Setext headings are supported. Explicit HTML anchors remain case-sensitive.

This is a documented approximation of GitHub heading IDs, not full renderer parity.
Emoji shortcodes, unusual Unicode symbols, HTML headings, and custom heading attributes
may need explicit HTML anchors or a different checker configured for your renderer.

## Path rules

- Relative destinations resolve from the file containing the link.
- A single leading slash means the repository root, not the filesystem root.
- Any URL scheme or network location is skipped without a request.
- URL-encoded paths and fragments are decoded once; query strings are ignored.
- An empty destination or bare fragment refers to the current file.
- Existing directories are valid destinations. Their fragments are not checked.
- Fragments in non-Markdown files are not checked, including code line references.
- Symlinks may point within the root; links that resolve outside it are findings.
- Directory symlinks are not traversed when discovering source files.
- Filename case sensitivity follows the host filesystem. Linux CI is recommended to
  catch case mismatches that a default macOS or Windows filesystem may accept.

Default discovery skips `.git`, `.venv`, `venv`, `node_modules`, `__pycache__`, `dist`,
and `build` directories. It does not read `.gitignore`. Exclusions use Python `fnmatch`
against root-relative POSIX paths; `*` can match `/`. Use `--exclude 'vendor'` to prune
a directory or `--exclude 'vendor/*'` to exclude its contents. Exclusions affect source
discovery only: a link into an excluded Markdown file still has its anchor checked.

## Diagnostics

Source lines are one-based. Ordinary links use their inline source line; links whose
own syntax spans multiple lines, and complex nested blocks, may point to the start of
the containing inline block. Suggestions are hints, never automatic rewrites.

The JSON report has `schema_version: 1`, `files_checked`, `links_checked`,
`links_skipped`, and `issues`. Each issue contains `file`, `line`, `target`, `code`,
`message`, and nullable `suggestion`. Files are root-relative with `/` separators.

Issue codes: `missing-file`, `missing-anchor`, `outside-root`, `invalid-url`,
`invalid-path`, `unreadable-file`, and `unreadable-target`. Invalid invocation inputs
produce a JSON object containing `schema_version` and `error`, with exit code 2.

Output order is deterministic for a fixed filesystem and parser version. Findings
follow source-file order, then link order within the file. Target documents are cached
for one invocation. Every local link occurrence is counted, including duplicate links.

Return to the [README](../README.md).
