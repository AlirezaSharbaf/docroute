# Roadmap

DocRoute 0.1 is a small offline tool with an intentionally limited scope. These are
proposed improvements, not implemented features or delivery promises.

## Next candidates

- Build a larger compatibility fixture corpus from real-world Markdown edge cases.
- Add optional configuration in `pyproject.toml` after the CLI interface stabilizes.
- Improve exact source positions for multiline and deeply nested links.
- Investigate opt-in raw HTML link checking and renderer-specific heading strategies.
- Evaluate publishing to PyPI once packaging and compatibility have broader testing.

## Useful first contributions

Add a failing fixture for an anchor or filename edge case, clarify a confusing
diagnostic, or document a reproducible difference between a renderer and DocRoute.
Open an issue describing the expected behavior before implementing a large feature.

See [contribution instructions](../CONTRIBUTING.md).
