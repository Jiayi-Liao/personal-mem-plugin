# Personal Mem Plugin

Keep reusable plugin code in plugins/personal-mem/ and developer scripts/tests in scripts/ and tests/.
Private initialized memory lives in .local/memory/ and must never be packaged, committed or uploaded.
Build releases only with scripts/package.py; it includes the plugin folder only.
Use Python standard library for the local core. Preserve user data during init/import; no automatic deletion, sync or external upload.
Run python3 -m unittest discover -s tests before releasing changes to memory operations.
