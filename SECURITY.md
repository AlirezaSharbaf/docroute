# Security policy

DocRoute is an early-stage local CLI. The latest version on the default branch is
the supported development version.

## Reporting

For a suspected vulnerability, use GitHub's private vulnerability reporting feature
if enabled on this repository. Otherwise open an issue asking for a private reporting
channel without including exploit details or sensitive data. Do not post credentials
or private repository contents in public issues.

## Behavior

The checker makes no network requests, executes no repository code, and does not
modify checked files. Installation still uses your package manager's network access.
It resolves symlinks and rejects link targets outside the configured root before
reading target Markdown. This is a path check, not an operating-system sandbox;
run against a stable checkout you control. Concurrent filesystem changes, extremely
large documents, and resource exhaustion are outside the current protection scope.

GitHub annotation output escapes workflow-command metacharacters. Run untrusted
pull requests with read-only permissions and without secrets.
