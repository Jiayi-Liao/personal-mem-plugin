#!/usr/bin/env python3
"""Package only distributable plugin files; never include the personal workspace."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def package(output=None):
    plugin = ROOT / "plugins/personal-mem"
    version = json.loads((plugin / "plugin.json").read_text())["version"]
    output = Path(output) if output else ROOT / "artifacts" / ("personal-mem-" + version + ".zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(plugin.rglob("*")):
            relative = file.relative_to(plugin)
            if file.is_symlink():
                raise ValueError("Do not package symlinks: " + str(relative))
            if not file.is_file() or "__pycache__" in relative.parts or file.suffix == ".pyc":
                continue
            if relative.parts[0] not in {"plugin.json", ".codex-plugin", "skills", "assets"}:
                raise ValueError("Unexpected plugin file: " + str(relative))
            archive.writestr(str(relative), file.read_bytes())
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".zip.sha256").write_text(checksum + "  " + output.name + "\n")
    return {"path": str(output), "sha256": checksum}


if __name__ == "__main__":
    print(json.dumps(package(), indent=2))
