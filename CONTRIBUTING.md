# Contributing to DocRoute

Thanks for helping make documentation easier to maintain. Small, reproducible changes
are welcome. You do not need to add an AI integration to contribute.

## Development

Use Python 3.10 or later and a virtual environment:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
docroute
python -m build
```

On Windows, activate with `.venv\Scripts\Activate.ps1` instead. Tests use temporary
directories and make no network requests. Symlink tests may skip when the operating
system does not allow creating symlinks.

## Bug reports and pull requests

1. Include your Python version, operating system, command, and a minimal Markdown example.
2. Explain expected and actual behavior, including the renderer if anchors differ.
3. For a fix, add a regression test and update documentation when behavior changes.
4. Keep each pull request focused. Do not include credentials, personal data, or generated environments.

Be respectful and constructive. Discuss the code and ideas, and welcome newcomers.
Contributions are licensed under the repository's [MIT license](LICENSE).
