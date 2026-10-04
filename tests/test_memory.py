import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HELPER = Path(__file__).resolve().parents[1] / "plugins/personal-mem/skills/personal-mem/scripts/mem.py"
spec = importlib.util.spec_from_file_location("personal_mem", HELPER)
mem = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mem)


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "我的 memory"
        mem.init_workspace(self.root, "Asia/Shanghai")

    def test_init_preserves_existing_user_content(self):
        file = self.root / "profile.md"
        file.write_text("用户自己写的内容", encoding="utf-8")
        mem.init_workspace(self.root, "UTC")
        self.assertEqual(file.read_text(), "用户自己写的内容")
        self.assertEqual(mem.status(self.root)["timezone"], "Asia/Shanghai")

    def test_binding_in_new_process(self):
        config = self.base / "binding.json"
        with mock.patch.dict(os.environ, {"PERSONAL_MEM_CONFIG": str(config)}):
            mem.init_workspace(self.root, bind=True)
            output = subprocess.check_output([sys.executable, str(HELPER), "status"], text=True)
        self.assertEqual(json.loads(output)["workspace"], str(self.root))

    def test_retry_is_idempotent_across_dates_and_rejects_different_body(self):
        first = mem.remember(self.root, "项目选择", "使用本地文件", operation_id="capture-1", date="2026-10-03")
        second = mem.remember(self.root, "项目选择", "使用本地文件", operation_id="capture-1", date="2026-10-04")
        self.assertFalse(second["created"])
        self.assertEqual(first["path"], second["path"])
        with self.assertRaises(ValueError):
            mem.remember(self.root, "项目选择", "改变内容", operation_id="capture-1")
        self.assertEqual(Path(first["path"]).read_text().count("## 项目选择"), 1)

    def test_preferences_need_scope(self):
        with self.assertRaises(ValueError):
            mem.remember(self.root, "偏好", "简短", kind="preference")
        mem.remember(self.root, "偏好", "保留原文判断", kind="preference", scope="文章编辑")
        hits = mem.search(self.root, "原文 判断")
        self.assertEqual(hits["total"], 1)
        self.assertIn("preferences.md", hits["results"][0]["path"])

    def test_writer_lock_preserves_file(self):
        with mem.write_lock(self.root):
            with self.assertRaises(ValueError):
                mem.remember(self.root, "不能并发覆盖", "内容")
        self.assertFalse((self.root / ".personal-mem/write.lock").exists())
        self.assertEqual(list((self.root / "daily").glob("*.md")), [])

    def test_write_failure_preserves_original_and_releases_lock(self):
        first = mem.remember(self.root, "原始内容", "不能丢失", date="2026-10-03")
        original = Path(first["path"]).read_bytes()
        with mock.patch.object(mem.os, "replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                mem.remember(self.root, "新内容", "应该失败", date="2026-10-03")
        self.assertEqual(Path(first["path"]).read_bytes(), original)
        self.assertFalse((self.root / ".personal-mem/write.lock").exists())

    def test_workspace_symlink_escape_rejected(self):
        outside = self.base / "outside.md"
        outside.write_text("不可更改", encoding="utf-8")
        (self.root / "daily/2026-10-03.md").symlink_to(outside)
        with self.assertRaises(ValueError):
            mem.remember(self.root, "x", "x", date="2026-10-03")
        self.assertEqual(outside.read_text(), "不可更改")

    def make_source(self):
        source = self.base / "old notes"
        (source / "daily").mkdir(parents=True)
        (source / "weekly").mkdir()
        (source / "artifacts").mkdir()
        (source / "2026-10-03.md").write_text("# 根目录\nJust in Time Memory", encoding="utf-8")
        (source / "daily/2026-10-03.md").write_text("# daily\n另一条独立记忆", encoding="utf-8")
        (source / "weekly/2026-W40.md").write_text("# 周回顾\n", encoding="utf-8")
        (source / "artifacts/report.md").write_text("![图](image.png)\n", encoding="utf-8")
        (source / "artifacts/image.png").write_bytes(b"test image bytes")
        (source / "AGENTS.md").write_text("Not imported", encoding="utf-8")
        (source / "scripts").mkdir()
        (source / "scripts/private.md").write_text("Not imported", encoding="utf-8")
        return source

    def test_import_is_lossless_idempotent_and_source_is_unchanged(self):
        source = self.make_source()
        before = {str(p): p.read_bytes() for p in source.rglob("*") if p.is_file()}
        preview = mem.import_notes(self.root, source, "old", include_assets=True, dry_run=True)
        self.assertEqual(preview["candidates"], 5)
        self.assertFalse((self.root / "library/old").exists())
        first = mem.import_notes(self.root, source, "old", include_assets=True)
        self.assertEqual(first["copied"], 5)
        second = mem.import_notes(self.root, source, "old", include_assets=True)
        self.assertEqual(second["unchanged"], 5)
        self.assertEqual(second["copied"], 0)
        self.assertEqual(before, {str(p): p.read_bytes() for p in source.rglob("*") if p.is_file()})
        for rel in ("2026-10-03.md", "daily/2026-10-03.md", "artifacts/image.png"):
            self.assertEqual((source / rel).read_bytes(), (self.root / "library/old" / rel).read_bytes())
        self.assertEqual(mem.search(self.root, "Just in Time")["total"], 1)
        ctx = mem.context(self.root)
        self.assertEqual(ctx["recent_dates"], ["2026-10-03"])
        self.assertEqual(ctx["latest_week"], "2026-W40")

    def test_import_conflicts_preserve_local_edits(self):
        source = self.make_source()
        mem.import_notes(self.root, source, "old")
        local = self.root / "library/old/2026-10-03.md"
        local.write_text("用户的新修正", encoding="utf-8")
        report = mem.import_notes(self.root, source, "old")
        self.assertEqual(report["conflicts"], ["2026-10-03.md"])
        self.assertEqual(local.read_text(), "用户的新修正")

    def test_import_rejects_overlapping_directories_and_source_symlinks(self):
        with self.assertRaises(ValueError):
            mem.import_notes(self.root, self.base, "bad")
        source = self.make_source()
        (source / "daily/secret.md").symlink_to(self.root / "profile.md")
        report = mem.import_notes(self.root, source, "old")
        self.assertEqual(report["candidates"], 4)
        self.assertFalse((self.root / "library/old/daily/secret.md").exists())

    def test_iso_week_crosses_calendar_year(self):
        mem.remember(self.root, "跨年", "记录", date="2025-12-29")
        info = mem.review_inputs(self.root, "2026-W01")
        self.assertEqual(info["start"], "2025-12-29")
        self.assertEqual(len(info["sources"]), 1)
        mem.save_review(self.root, "2026-W01", "# Review\n")
        with self.assertRaises(ValueError):
            mem.save_review(self.root, "2026-W01", "# Different\n")

    def test_unknown_schema_fails_closed(self):
        mem.write_json(self.root / mem.CONFIG_NAME, {"schema_version": 999})
        with self.assertRaises(ValueError):
            mem.remember(self.root, "x", "x")


if __name__ == "__main__":
    unittest.main()
