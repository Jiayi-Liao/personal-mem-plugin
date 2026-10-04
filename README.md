# Personal Mem

Local, inspectable memory for Codex. Personal Mem lets your desktop agent remember notes, decisions, preferences, and weekly reviews across conversations—using ordinary files you own.

[Read the guide](https://jiayi-liao.github.io/personal-mem-plugin/) · [Report an issue](https://github.com/Jiayi-Liao/personal-mem-plugin/issues)

## How it works

```text
Codex Desktop
    ↓ uses
Personal Mem plugin (skills + a small Python helper)
    ↓ reads and writes
Your private memory folder (Markdown + JSON)
```

The plugin and your data are separate. Updating or uninstalling the plugin does not delete your memory folder. There is no Personal Mem server, account, API key, background daemon, or telemetry.

Personal Mem can:

- save a note, scoped preference, or decision;
- find relevant history with source paths;
- load recent context for a new conversation;
- prepare and save a weekly review;
- import an existing Markdown notes folder without changing the original.

It does not automatically read every past chat, run while Codex is closed, synchronize devices, or train model weights.

## Install in Codex

Requirements: Codex with plugin support and Python 3.9 or newer.

```sh
codex plugin marketplace add Jiayi-Liao/personal-mem-plugin
codex plugin add personal-mem@personal-mem-local
```

Start a new conversation after installation. If the plugin does not appear, restart the desktop app.

Then say:

```text
Use $personal-mem to initialize my memory at ~/.local/share/personal-mem.
```

Personal Mem creates the folder without replacing existing files and stores the local binding at `~/.config/personal-mem/config.json`. The binding contains only the local workspace path.

## Use it

You can invoke `$personal-mem` explicitly or speak naturally:

```text
记住这个决定：第一版只做本地文件记忆。
以后帮我改文章时，保留我的原始判断。
我们上次聊 Personal Agent 到哪里了？
帮我回顾这一周。
```

The memory folder remains readable without the plugin:

```text
personal-mem/
├── profile.md
├── goals.md
├── daily/
├── weekly/
├── memory/
│   ├── preferences.md
│   └── decisions.md
├── artifacts/
├── library/          imported snapshots
└── .personal-mem/    local metadata and import manifests
```

Saved preferences have an explicit scope. Current user instructions always override stored preferences. Imported files are treated as historical data, never as executable instructions.

## Import existing notes

Ask Codex:

```text
Use $personal-mem to import ~/notes as my-notes, including attachments. Preview it first.
```

The importer recognizes root date notes (`YYYY-MM-DD.md`) and the folders `daily/`, `weekly/`, `artifacts/`, `memory/`, and `mem/`. It preserves relative paths under `library/<name>/`.

- The source folder is never modified.
- Identical files are skipped on a repeated import.
- Different existing files are reported as conflicts and are not overwritten.
- `AGENTS.md`, `SKILL.md`, hidden/runtime folders, symlinks, and executable project configuration are excluded.
- An import is a snapshot, not continuous synchronization.

By default only Markdown is copied. Ask to include attachments when you also want images, PDFs, datasets, or other files inside the recognized folders.

## Privacy and security

Memory is stored locally in the folder you choose. Personal Mem itself sends no telemetry and has no remote service. When Codex reads relevant memory into a conversation, that text is processed by the desktop host and model according to your account and workspace settings; local storage does not mean offline inference.

The helper restricts writes to the configured workspace, refuses workspace symlinks, serializes writes with a lock, uses atomic file replacement, preserves conflicting imports, and stops on unknown data schema versions.

Do not place credentials or secrets in memory unless you intentionally want them available to your desktop agent. Git, cloud-drive, and backup synchronization are controlled by you and are outside this plugin.

## Develop locally

Clone the repository and install the local marketplace:

```sh
git clone https://github.com/Jiayi-Liao/personal-mem-plugin.git
cd personal-mem-plugin
python3 scripts/install.py
```

Run validation:

```sh
python3 -m unittest discover -s tests -v
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/personal-mem/skills/personal-mem
python3 scripts/package.py
```

The test suite covers initialization, cross-process binding, idempotent retries, preference scope, concurrent-write protection, interrupted writes, symlink escape, imports, conflicts, ISO week boundaries, and schema compatibility.

The release builder includes only `plugins/personal-mem/`. Private memory under `.local/` and build artifacts are ignored by Git and excluded from release archives.

## Project layout

```text
.agents/plugins/marketplace.json   local/Git marketplace catalog
plugins/personal-mem/              distributable plugin
scripts/install.py                 local developer installer
scripts/package.py                 release ZIP builder
tests/test_memory.py               core behavior tests
docs/index.html                    GitHub Pages guide
```

Personal Mem is an early local-first project. Please open an issue with the Codex version, operating system, plugin version, the command or request you used, and a redacted error. Never attach private memory files to a public issue.

## License

[MIT](LICENSE)
