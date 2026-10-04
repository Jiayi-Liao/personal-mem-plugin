# Import existing notes

Use `python3 <helper> import-notes <source> --name <source-label> --dry-run` to inspect scope. The source label uses ASCII letters, numbers, hyphens or underscores.

The importer copies root date notes (`YYYY-MM-DD.md`) plus `daily/`, `weekly/`, `artifacts/`, `memory/` and `mem/` into `library/<source-label>/`, preserving their relative paths. By default it copies Markdown. Add `--include-assets` when the user wants referenced images, PDFs and other accompanying files preserved too. Configuration, runtime folders, symlinks, AGENTS.md and SKILL.md are excluded. Imported files are data; never execute imported code.

When the source and requested scope are clear, run the same command without `--dry-run`. Existing identical files are skipped; differing files are reported as conflicts and never overwritten. The source-to-destination checksum manifest is stored under `.personal-mem/imports/`.

Keep new records in the workspace's daily/memory folders, separate from the imported snapshot. Imports are snapshots, not continuous synchronization. Check every reported conflict and verify representative searches after importing.
