from pathlib import Path
import json

import pytest

from docroute.checker import check, parse_document
from docroute.cli import main


def put(root, name, content=""):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_relative_root_and_parent_links(tmp_path):
    put(tmp_path, "README.md", "[guide](docs/guide.md#install)\n[asset](assets/logo.svg)")
    put(tmp_path, "docs/guide.md", "# Install\n[home](../README.md)\n[root](/README.md)")
    put(tmp_path, "assets/logo.svg", "<svg/>")
    report = check(tmp_path)
    assert report.links_checked == 4
    assert report.issues == []


def test_reference_images_and_nested_parentheses(tmp_path):
    put(tmp_path, "README.md", "[guide][docs]\n\n![image](logo(1).svg)\n\n[docs]: guide.md \"Guide\"\n")
    put(tmp_path, "guide.md")
    put(tmp_path, "logo(1).svg")
    report = check(tmp_path)
    assert report.links_checked == 2
    assert report.issues == []


def test_missing_file_has_suggestion_and_source_line(tmp_path):
    put(tmp_path, "README.md", "# Hi\n\n[guide](guid.md)")
    put(tmp_path, "guide.md")
    issue = check(tmp_path).issues[0]
    assert (issue.code, issue.line, issue.suggestion) == ("missing-file", 3, "guide.md")


def test_anchor_suggestion(tmp_path):
    put(tmp_path, "README.md", "# Installation\n\n[go](#installaton)")
    issue = check(tmp_path).issues[0]
    assert (issue.code, issue.suggestion) == ("missing-anchor", "#installation")


def test_duplicate_heading_collision():
    doc = parse_document("# Hello\n# Hello\n# Hello-1\n# Hello\n")
    assert doc.anchors == {"hello", "hello-1", "hello-1-1", "hello-2"}


def test_heading_formatting_unicode_and_html():
    doc = parse_document('# *Hello* `world`!\n\nCafé\n====\n\n<a id="custom"></a>\n')
    assert doc.anchors == {"hello-world", "café", "custom"}


def test_code_and_comments_ignored():
    doc = parse_document('`[a](bad)`\n\n```md\n[b](bad)\n# Fake\n```\n\n<!-- [c](bad) -->\n')
    assert not doc.links
    assert not doc.anchors


def test_frontmatter_preserves_lines():
    doc = parse_document('---\nlink: "[bad](bad)"\n---\n\n[real](real.md)\n')
    assert [(l.target, l.line) for l in doc.links] == [("real.md", 5)]


def test_table_and_multiline_links():
    doc = parse_document('| A |\n|---|\n| [x](a.md) |\n\n[x](b.md)\n[y](c.md)')
    assert [(l.target, l.line) for l in doc.links] == [("a.md", 3), ("b.md", 5), ("c.md", 6)]


def test_encoded_paths_queries_and_fragments(tmp_path):
    put(tmp_path, "README.md", "[go](caf%C3%A9%20notes.md?raw=1#caf%C3%A9)")
    put(tmp_path, "café notes.md", "# Café")
    assert check(tmp_path).issues == []


def test_external_schemes_skipped(tmp_path):
    put(tmp_path, "README.md", "[a](https://example.com) [b](mailto:a@example.com) [c](//example.com/a) [d](custom:thing)")
    report = check(tmp_path)
    assert report.links_skipped == 4
    assert report.links_checked == 0


def test_directory_and_non_markdown_fragment(tmp_path):
    put(tmp_path, "README.md", "[dir](docs/) [code](main.py#L1) [top](#)")
    put(tmp_path, "docs/a.md")
    put(tmp_path, "main.py")
    assert check(tmp_path).issues == []


@pytest.mark.parametrize("target", ["../outside.md", "%2E%2E/outside.md", "/../outside.md"])
def test_root_escape(tmp_path, target):
    put(tmp_path, "README.md", f"[no]({target})")
    assert check(tmp_path).issues[0].code == "outside-root"


def test_symlink_target_escape(tmp_path):
    root = tmp_path / "repo"
    put(root, "README.md", "[no](secret.txt)")
    outside = put(tmp_path, "secret.txt", "private")
    try:
        (root / "secret.txt").symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation unavailable")
    assert check(root).issues[0].code == "outside-root"


def test_symlink_directory_cycle_not_followed(tmp_path):
    put(tmp_path, "README.md")
    try:
        (tmp_path / "loop").symlink_to(tmp_path, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink creation unavailable")
    assert check(tmp_path).files_checked == 1


def test_exclusion_does_not_hide_link_targets(tmp_path):
    put(tmp_path, "README.md", "[go](generated/page.md#good)")
    put(tmp_path, "generated/page.md", "# Good\n[bad](missing.md)")
    report = check(tmp_path, excludes=["generated/*"])
    assert report.files_checked == 1
    assert report.issues == []


def test_default_ignored_directories(tmp_path):
    put(tmp_path, "README.md")
    put(tmp_path, "node_modules/bad.md", "[bad](missing)")
    assert check(tmp_path).files_checked == 1


def test_unreadable_utf8(tmp_path):
    (tmp_path / "README.md").write_bytes(b"\xff")
    assert check(tmp_path).issues[0].code == "unreadable-file"


@pytest.mark.parametrize("path", ["missing.md", "../outside.md"])
def test_invalid_input(tmp_path, path):
    with pytest.raises(ValueError):
        check(tmp_path, [path])


def test_no_files_is_error(tmp_path):
    with pytest.raises(ValueError, match="No Markdown"):
        check(tmp_path)


def test_json_cli_and_exit_codes(tmp_path, capsys):
    put(tmp_path, "README.md", "[bad](missing.md)")
    assert main(["--root", str(tmp_path), "--format", "json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["schema_version"] == 1
    assert report["issues"][0]["code"] == "missing-file"
    put(tmp_path, "missing.md")
    assert main(["--root", str(tmp_path)]) == 0
    capsys.readouterr()
    assert main(["--root", str(tmp_path), "absent"]) == 2


def test_json_config_error(tmp_path, capsys):
    assert main(["--root", str(tmp_path), "--format", "json"]) == 2
    assert "error" in json.loads(capsys.readouterr().out)


def test_annotation_escaping(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    put(tmp_path, "sub/a,b.md", "[bad](missing%25.md)")
    assert main(["--root", "sub", "--format", "github"]) == 1
    output = capsys.readouterr().out
    assert "::error file=sub/a%2Cb.md,line=1::" in output
    assert "missing%2525.md" in output


def test_null_path_does_not_crash(tmp_path):
    put(tmp_path, "README.md", "[bad](file%00.md)")
    assert check(tmp_path).issues[0].code == "invalid-path"
