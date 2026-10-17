import json
from datetime import date
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from delivery import Ledger, default_analysis, fingerprint, inspect_source
from monthly_import import members, run as import_month


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "archive"
        self.root.mkdir()
        self.config = self.base / "config.json"
        self.config.write_text(json.dumps(dict(archive_root=str(self.root), archive_year=2026,
                                              project_id="work", project_name="Work", time_zone="Asia/Shanghai")))
        self.clock = [100.0]
        self.ledger = Ledger(self.config, self.base / "state", now=lambda: self.clock[0])

    def tearDown(self):
        self.ledger.db.close()
        self.temp.cleanup()

    def file(self, folder, name, content="delivered"):
        path = self.root / folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def begin(self, host="codex", day=date(2026, 10, 11)):
        return self.ledger.begin(host, day)

    def sync(self, token, row, remote_id="task-1"):
        self.ledger.mutate(token, "draft", row["id"])
        started = self.ledger.mutate(token, "start", row["id"])
        remote = dict(started["payload"], id=remote_id, status=0)
        self.ledger.mutate(token, "created", row["id"], remote)
        remote["status"] = 2
        self.ledger.mutate(token, "finish", row["id"], remote)
        return remote

    def test_preflight_empty_replay_skips_content_and_releases(self):
        self.file("1010", "recent.txt")
        first = self.begin()
        self.assertEqual(first["entries"][0]["next_action"]["command"], "inspect")
        self.sync(first["token"], first["entries"][0])
        self.ledger.mutate(first["token"], "release")
        with patch("delivery.fingerprint", side_effect=AssertionError("unchanged content read")):
            result = self.ledger.preflight("workbuddy", date(2026, 10, 11))
        self.assertTrue(result["idle"])
        self.assertFalse(result["needs_remote"])
        self.assertIsNone(result["token"])
        self.assertIsNone(self.ledger.get_meta("lease"))
        self.assertEqual(result["progress"], dict(pending=0, verified=1, archived=0, exceptions=0))
        self.file("1010", "recent.txt", "new")
        changed = self.ledger.preflight("codex", date(2026, 10, 11))
        self.assertTrue(changed["needs_remote"])
        self.assertEqual(changed["entries"][0]["task_id"], "task-1")

    def test_preflight_archives_before_idle_and_reports_warnings(self):
        self.file("1004", "expired.txt")
        first = self.begin()
        self.sync(first["token"], first["entries"][0])
        self.ledger.mutate(first["token"], "release")
        result = self.ledger.preflight("codex", date(2026, 10, 11))
        self.assertTrue(result["idle"])
        self.assertEqual(result["moved"], 1)
        self.assertEqual(result["progress"]["archived"], 1)
        self.file("0230", "invalid.txt")
        result = self.ledger.preflight("workbuddy", date(2026, 10, 11))
        self.assertFalse(result["idle"])
        self.assertTrue(result["warnings"])

    def test_completion_retry_budget_identity_and_recovery(self):
        self.file("1010", "recent.txt")
        first = self.begin()
        token, row = first["token"], first["entries"][0]
        self.ledger.mutate(token, "draft", row["id"])
        self.assertEqual(self.ledger.status()["entries"][0]["next_action"]["command"], "start")
        started = self.ledger.mutate(token, "start", row["id"])
        self.assertEqual(self.ledger.status()["entries"][0]["next_action"]["kind"], "reconcile")
        remote = dict(started["payload"], id="original-id", status=0)
        self.ledger.mutate(token, "created", row["id"], remote)
        with self.assertRaises(ValueError):
            self.ledger.mutate(token, "verify", row["id"], dict(remote, id="wrong"))
        with self.assertRaises(ValueError):
            self.ledger.mutate(token, "verify", row["id"], dict(remote, title="wrong"))
        for attempt, delay in enumerate((2, 5, 10), 1):
            result = self.ledger.mutate(token, "verify", row["id"], remote)
            self.assertEqual((result["attempt"], result["delay_seconds"]), (attempt, delay))
            self.assertEqual(result["arguments"]["task_id"], "original-id")
            self.assertEqual(self.ledger.status()["progress"]["exceptions"], 0)
        self.assertEqual(self.ledger.mutate(token, "verify", row["id"], remote)["action"], "defer")
        self.assertEqual(self.ledger.status()["progress"]["exceptions"], 1)
        self.assertEqual(self.ledger.entry(row["id"])["status"], "created")
        self.ledger.mutate(token, "release")
        token = self.begin("workbuddy")["token"]
        self.assertEqual(self.ledger.mutate(token, "verify", row["id"], remote)["attempt"], 1)
        result = self.ledger.mutate(token, "verify", row["id"], dict(remote, status=2))
        self.assertEqual(result["action"], "done")
        self.assertEqual(self.ledger.status()["progress"]["exceptions"], 0)

    def test_history_catch_up_and_invalid_future_dates(self):
        self.file("1010", "past.txt")
        self.file("1011", "today.txt")
        self.file("1012", "future.txt")
        self.file("0230", "bad.txt")
        self.file("PSB", "unscoped.txt")
        first = self.begin()
        self.assertEqual(first["counts"], {"pending": 2})
        self.assertEqual(len(first["warnings"]), 1)
        self.ledger.mutate(first["token"], "release")
        self.file("1010", "late.txt")
        second = self.begin("workbuddy", date(2026, 10, 13))
        self.assertEqual(second["counts"], {"pending": 4})
        self.assertEqual({r["work_date"] for r in second["entries"]}, {"2026-10-10", "2026-10-11", "2026-10-12"})

    def test_each_direct_file_archive_and_directory_is_one(self):
        self.file("1011", "patent.docx")
        self.file("1011", ".DS_Store")
        self.file("1011", "~$patent.docx")
        self.file("1011/system", "one.txt")
        self.file("1011/system/deep", "two.txt")
        self.file("1011", "outside.txt").unlink()
        (self.root / "1011/outside.txt").symlink_to(self.config)
        with zipfile.ZipFile(self.root / "1011/delivery.zip", "w") as z:
            z.writestr("one.docx", "one")
            z.writestr("two.docx", "two")
        result = self.begin()
        self.assertEqual(len(result["entries"]), 3)
        self.assertEqual({r["kind"] for r in result["entries"]}, {"file", "directory"})
        for row in result["entries"]:
            if row["kind"] == "directory":
                self.assertNotIn("two.txt", inspect_source(row))
                old = fingerprint(Path(row["source"]))
                self.file("1011/system", "one.txt", "new contents")
                self.assertNotEqual(old, fingerprint(Path(row["source"])))

    def test_cross_host_replay_and_same_path_update(self):
        self.file("1011", "修改 宠物项圈.txt")
        first = self.begin()
        row = first["entries"][0]
        remote = self.sync(first["token"], row)
        self.ledger.mutate(first["token"], "release")
        second = self.begin("workbuddy")
        self.assertEqual(second["entries"], [])
        self.ledger.mutate(second["token"], "release")
        self.file("1011", "修改 宠物项圈.txt", "changed")
        third = self.begin("workbuddy")
        self.assertEqual(third["entries"][0]["id"], row["id"])
        self.ledger.mutate(third["token"], "draft", row["id"])
        updated = self.ledger.mutate(third["token"], "start", row["id"])
        self.assertEqual((updated["operation"], updated["task_id"]), ("update", remote["id"]))

    def test_different_day_is_new_work_even_with_identical_bytes(self):
        self.file("1011", "宠物项圈.txt")
        self.file("1012", "宠物项圈.txt")
        result = self.begin(day=date(2026, 10, 12))
        rows = self.ledger.db.execute("SELECT * FROM entries").fetchall()
        self.assertEqual(len({r["id"] for r in rows}), 2)
        self.assertEqual(len({r["fingerprint"] for r in rows}), 1)

    def test_lease_exclusion_expiration_and_unknown_creation(self):
        self.file("1011", "work.txt")
        first = self.begin()
        with self.assertRaisesRegex(ValueError, "持有租约"):
            self.begin("workbuddy")
        row = first["entries"][0]
        self.ledger.mutate(first["token"], "draft", row["id"])
        started = self.ledger.mutate(first["token"], "start", row["id"])
        self.clock[0] += 1801
        second = self.begin("workbuddy")
        self.assertEqual(second["entries"][0]["status"], "creating")
        with self.assertRaisesRegex(ValueError, "租约无效"):
            self.ledger.mutate(first["token"], "renew")
        with self.assertRaisesRegex(ValueError, "必须对账"):
            self.ledger.mutate(second["token"], "start", row["id"])
        remote = dict(started["payload"], id="remote-after-timeout", status=0)
        self.ledger.mutate(second["token"], "created", row["id"], remote)
        self.ledger.mutate(second["token"], "release")
        third = self.begin()
        self.assertEqual(third["entries"][0]["task_id"], remote["id"])
        remote["status"] = 2
        self.ledger.mutate(third["token"], "finish", row["id"], remote)
        self.assertEqual(self.ledger.entry(row["id"])["status"], "done")

    def test_remote_validation_and_changes_during_sync(self):
        self.file("1011", "work.txt")
        result = self.begin()
        token, row = result["token"], result["entries"][0]
        payload = self.ledger.mutate(token, "draft", row["id"])
        self.ledger.mutate(token, "start", row["id"])
        remote = dict(payload, id="id", status=2)
        for wrong in (dict(remote, projectId="other"), dict(remote, content="wrong"),
                      dict(remote, title="wrong"), dict(remote, status=0),
                      dict(remote, startDate="2026-10-12T00:00:00+0800"), dict(remote, isAllDay=False),
                      dict(remote, isAllDay="true")):
            with self.assertRaises(ValueError):
                self.ledger.mutate(token, "finish", row["id"], wrong)
        self.file("1011", "work.txt", "new version")
        self.ledger.mutate(token, "finish", row["id"], remote)
        updated = self.ledger.entry(row["id"])
        self.assertEqual(updated["status"], "pending")
        self.assertEqual(updated["task_id"], "id")

    def test_analysis_validation_unknowns_and_persistent_supplement(self):
        self.file("1011", "mystery.zip")
        result = self.begin()
        token, row = result["token"], result["entries"][0]
        defaults = default_analysis(row)
        self.assertEqual(defaults["category"], "类别待确认")
        self.assertEqual(defaults["sender"], "派发人未知")
        for invalid in ({"name": "only name"}, {}, [], "text"):
            with self.assertRaises(ValueError):
                self.ledger.mutate(token, "draft", row["id"], invalid)
        data = dict(date="2026-10-10", text="老板 A 安排的旅游系统修改已完成")
        supplement = self.ledger.mutate(token, "supplement", data=data)
        duplicate = self.ledger.mutate(token, "supplement", data=data)
        self.assertEqual(supplement["id"], duplicate["id"])
        self.ledger.mutate(token, "release")
        second = self.begin("workbuddy")
        self.assertIn(supplement["id"], [r["id"] for r in second["entries"]])

    def test_year_mapping_is_frozen_and_target_change_is_rejected(self):
        self.file("1011", "work.txt")
        result = self.begin()
        self.ledger.mutate(result["token"], "release")
        data = json.loads(self.config.read_text())
        data["archive_year"] = 2027
        self.config.write_text(json.dumps(data))
        other = Ledger(self.config, self.base / "state")
        try:
            result = other.begin("workbuddy", date(2027, 10, 11))
            self.assertEqual(result["entries"][0]["work_date"], "2026-10-11")
            other.mutate(result["token"], "release")
        finally:
            other.db.close()
        data["project_id"] = "other-project"
        self.config.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "清单已变化"):
            Ledger(self.config, self.base / "state")

    def test_failed_scan_does_not_commit_partial_baseline(self):
        self.file("1011", "work.txt")
        with patch("delivery.fingerprint", side_effect=OSError("unreadable")):
            with self.assertRaises(OSError):
                self.begin()
        self.assertIsNone(self.ledger.get_meta("baseline_at"))
        self.assertIsNone(self.ledger.get_meta("lease"))
        self.assertEqual(self.ledger.status()["counts"], {})

    def test_separate_host_connections_share_lease_and_ledger(self):
        self.file("1011", "发明专利 修改申请书.txt")
        first = self.begin()
        second = Ledger(self.config, self.base / "state", now=lambda: self.clock[0])
        try:
            with self.assertRaisesRegex(ValueError, "持有租约"):
                second.begin("workbuddy", date(2026, 10, 11))
            row = first["entries"][0]
            remote = self.sync(first["token"], row)
            self.ledger.mutate(first["token"], "release")
            resumed = second.begin("workbuddy", date(2026, 10, 11))
            self.assertEqual(resumed["counts"], {"done": 1})
            self.assertEqual(resumed["entries"], [])
            self.assertEqual(second.entry(row["id"])["task_id"], remote["id"])
            second.mutate(resumed["token"], "release")
        finally:
            second.db.close()

    def test_golden_record_fields_and_long_title(self):
        self.file("1011", "撰写 发明专利申请书.txt")
        result = self.begin()
        token, row = result["token"], result["entries"][0]
        payload = self.ledger.mutate(token, "draft", row["id"])
        self.assertEqual(payload["title"], "2026-10-11 · 发明专利/撰写 · 撰写 发明专利申请书")
        self.assertEqual(payload["startDate"], "2026-10-11T00:00:00.000+0800")
        self.assertTrue(payload["isAllDay"])
        for text in ("归档日期：2026-10-11", "成果类别：发明专利", "工作动作：撰写",
                     "任务派发人：派发人未知", "系统或项目：项目待确认", "work-delivery:" + row["id"]):
            self.assertIn(text, payload["content"])
        analysis = default_analysis(row)
        analysis["name"] = "完整名称" * 100
        payload = self.ledger.mutate(token, "draft", row["id"], analysis)
        self.assertEqual(len(payload["title"]), 180)
        self.assertIn(analysis["name"], payload["content"])

    def test_legacy_schema_and_baselines_migrate_without_changing_ids(self):
        self.file("1001", "old.txt")
        first = self.begin()
        row = first["entries"][0]
        remote = self.sync(first["token"], row)
        self.ledger.mutate(first["token"], "release")
        self.file("1002", "unrecorded.txt")
        second = self.begin()
        pending = second["entries"][0]
        self.ledger.mutate(second["token"], "release")
        self.ledger.db.execute("UPDATE entries SET status='baseline' WHERE id=?", (pending["id"],))
        self.ledger.db.execute("DELETE FROM meta WHERE key='retention_migrated'")
        self.ledger.db.commit()
        self.ledger.db.close()
        path = self.base / "state/ledger.sqlite3"
        db = sqlite3.connect(str(path))
        db.execute("ALTER TABLE entries RENAME TO previous_entries")
        db.execute("""CREATE TABLE entries (id TEXT PRIMARY KEY,work_date TEXT,source TEXT,kind TEXT,
                   fingerprint TEXT,status TEXT,task_id TEXT,payload TEXT,synced_fingerprint TEXT)""")
        db.execute("INSERT INTO entries SELECT id,work_date,source,kind,fingerprint,status,task_id,payload,synced_fingerprint FROM previous_entries")
        db.execute("DROP TABLE previous_entries")
        db.commit()
        db.close()
        self.ledger = Ledger(self.config, self.base / "state", now=lambda: self.clock[0])
        result = self.begin("workbuddy")
        self.assertEqual(result["counts"], {"done": 1, "pending": 1})
        self.assertEqual(self.ledger.entry(row["id"])["task_id"], remote["id"])
        self.assertEqual(result["entries"][0]["id"], pending["id"])

    def test_retention_boundary_and_cold_files_are_not_read(self):
        old = self.file("1004", "old.txt")
        self.file("1004", ".metadata")
        self.file("1005", "recent.txt")
        first = self.begin()
        for i, row in enumerate(first["entries"]): self.sync(first["token"], row, str(i))
        result = self.ledger.archive(first["token"], date(2026, 10, 11))
        self.assertEqual(result["moved"], 1)
        cold = self.root / "历史归档/2026/10月/1004"
        self.assertFalse(old.exists())
        self.assertTrue((cold / "old.txt").exists())
        self.assertTrue((cold / ".metadata").exists())
        self.assertTrue((self.root / "1005").exists())
        old_row = self.ledger.db.execute("SELECT * FROM entries WHERE source=?", (str(old),)).fetchone()
        self.assertEqual(old_row["storage_path"], str(cold / "old.txt"))
        with self.assertRaisesRegex(ValueError, "活动成果"):
            self.ledger.mutate(first["token"], "inspect", old_row["id"])
        self.ledger.mutate(first["token"], "release")
        with patch("delivery.fingerprint", wraps=fingerprint) as reads, patch("delivery.inspect_source") as ai_reads:
            result = self.begin("workbuddy")
            self.assertEqual(result["entries"], [])
            self.assertTrue(all("历史归档" not in str(c.args[0]) for c in reads.call_args_list))
            ai_reads.assert_not_called()

    def test_existing_history_month_grouping_keeps_ids_and_reads_no_content(self):
        self.file("0930", "old.txt")
        first = self.begin()
        row = first["entries"][0]
        self.sync(first["token"], row, "keep-id")
        self.ledger.archive(first["token"], date(2026, 10, 11))
        current = self.root / "历史归档/2026/9月/0930"
        legacy = current.parent.parent / current.name
        current.rename(legacy)
        self.ledger.db.execute("UPDATE moves SET target=?", (str(legacy),))
        self.ledger.db.execute("UPDATE entries SET storage_path=?", (str(legacy / "old.txt"),))
        self.ledger.db.commit()
        with patch("delivery.fingerprint", side_effect=AssertionError("cold read")):
            self.assertEqual(self.ledger.group_history(first["token"]), [])
        updated = self.ledger.entry(row["id"])
        self.assertEqual(updated["task_id"], "keep-id")
        self.assertEqual(updated["source"], row["source"])
        self.assertEqual(updated["storage_path"], str(current / "old.txt"))
        self.assertEqual(self.ledger.group_history(first["token"]), [])

    def test_archived_metadata_update_finishes_without_reading_history(self):
        self.file("0930", "old.txt")
        first = self.begin()
        row = first["entries"][0]
        remote = self.sync(first["token"], row, "keep-id")
        self.ledger.archive(first["token"], date(2026, 10, 11))
        remote["content"] = remote["content"].replace("派发人未知", "岸达")
        self.ledger.db.execute("UPDATE entries SET status='updating',payload=? WHERE id=?",
                               (json.dumps(remote), row["id"]))
        self.ledger.db.commit()
        with patch("delivery.fingerprint", side_effect=AssertionError("cold read")):
            self.ledger.mutate(first["token"], "finish", row["id"], remote)
        self.assertEqual(self.ledger.entry(row["id"])["status"], "done")
        self.assertEqual(self.ledger.entry(row["id"])["task_id"], "keep-id")

    def test_monthly_zip_import_replay_and_original_preservation(self):
        source = self.root / "7 月.zip"
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("7月/260720｜2撰写/a.txt", "a")
            archive.writestr("7月/260720｜2撰写/package/b.txt", "b")
            archive.writestr("7月/CHANGLOG.md", "日报")
            archive.writestr("__MACOSX/._7月", "metadata")
        first = self.begin()
        token = first["token"]
        record = import_month(self.ledger, token, source, 7)
        self.assertEqual(record["phase"], "imported")
        self.assertEqual(self.ledger.status()["remaining"], 2)
        import_month(self.ledger, token, source, 7)
        with self.assertRaisesRegex(ValueError, "尚未全部"):
            import_month(self.ledger, token, source, 7, True)
        for row in self.ledger.status()["entries"]:
            self.sync(token, row, row["id"])
        self.ledger.archive(token, date(2026, 10, 11))
        import_month(self.ledger, token, source, 7)
        finished = import_month(self.ledger, token, source, 7, True)
        self.assertTrue(Path(finished["target"]).exists())
        self.assertFalse(source.exists())
        self.assertFalse(Path(record["stage"]).exists())
        self.assertEqual(import_month(self.ledger, token, source, 7, True)["phase"], "done")

    def test_monthly_zip_rejects_traversal_month_mismatch_and_existing_dates(self):
        source = self.root / "monthly.zip"
        for name in ("../escape.txt", "7月/260820/a.txt"):
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(name, "a")
            with zipfile.ZipFile(source) as archive, self.assertRaises(ValueError):
                members(archive, 7)
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("7月/260720/a.txt", "a")
        self.file("2026-07-20", "existing.txt")
        first = self.begin()
        with self.assertRaisesRegex(ValueError, "已存在"):
            import_month(self.ledger, first["token"], source, 7)
        self.assertEqual((self.root / "2026-07-20/existing.txt").read_text(), "delivered")

    def test_monthly_publish_and_original_move_resume_after_interruption(self):
        source = self.root / "7.zip"
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("7月/260720/a.txt", "a")
        first = self.begin()
        token = first["token"]
        rename = Path.rename
        def interrupted(source, target):
            rename(source, target)
            raise OSError("interrupted after rename")
        with patch.object(Path, "rename", interrupted), self.assertRaises(OSError):
            import_month(self.ledger, token, source, 7)
        import_month(self.ledger, token, source, 7)
        row = self.ledger.status()["entries"][0]
        self.sync(token, row)
        self.ledger.archive(token, date(2026, 10, 11))
        with patch.object(Path, "rename", interrupted), self.assertRaises(OSError):
            import_month(self.ledger, token, source, 7, True)
        result = import_month(self.ledger, token, source, 7, True)
        self.assertEqual(result["phase"], "done")
        self.assertTrue(Path(result["target"]).exists())
        self.assertEqual(self.ledger.entry(row["id"])["task_id"], "task-1")

    def test_expired_pending_folders_skip_content_scan_until_changed(self):
        self.file("1001", "old.txt")
        first = self.begin()
        self.ledger.mutate(first["token"], "release")
        with patch("delivery.fingerprint", side_effect=AssertionError("unexpected read")):
            second = self.begin()
        self.ledger.mutate(second["token"], "release")
        self.file("1001", "late.txt")
        third = self.begin()
        self.assertEqual(third["counts"], {"pending": 2})

    def test_expired_pending_unknown_creation_and_changed_sources_stay_active(self):
        path = self.file("1001", "old.txt")
        first = self.begin()
        row = first["entries"][0]
        self.ledger.mutate(first["token"], "draft", row["id"])
        started = self.ledger.mutate(first["token"], "start", row["id"])
        self.assertEqual(self.ledger.archive(first["token"], date(2026, 10, 11))["moved"], 0)
        remote = dict(started["payload"], id="known", status=2)
        self.ledger.mutate(first["token"], "finish", row["id"], remote)
        path.write_text("late change")
        result = self.ledger.archive(first["token"], date(2026, 10, 11))
        self.assertEqual(result["moved"], 0)
        self.assertEqual(self.ledger.entry(row["id"])["status"], "pending")
        self.assertTrue(path.exists())

    def test_move_interruption_recovers_without_reading_archived_contents(self):
        self.file("1001", "old.txt")
        first = self.begin()
        self.sync(first["token"], first["entries"][0])
        rename = Path.rename
        def interrupted(source, target):
            rename(source, target)
            raise OSError("interrupted after rename")
        with patch.object(Path, "rename", interrupted):
            result = self.ledger.archive(first["token"], date(2026, 10, 11))
        self.assertEqual(len(result["unresolved_moves"]), 1)
        self.ledger.mutate(first["token"], "release")
        with patch("delivery.fingerprint", side_effect=AssertionError("cold content read")):
            resumed = self.begin("workbuddy")
        self.assertEqual(resumed["unresolved_moves"], [])
        self.assertEqual(resumed["archived_directories"], 1)
        self.assertEqual(resumed["entries"], [])

    def test_move_failure_before_rename_and_ambiguous_paths(self):
        self.file("1001", "old.txt")
        first = self.begin()
        self.sync(first["token"], first["entries"][0])
        with patch.object(Path, "rename", side_effect=OSError("permission denied")):
            result = self.ledger.archive(first["token"], date(2026, 10, 11))
        move = result["unresolved_moves"][0]
        Path(move["target"]).mkdir()
        (Path(move["target"]) / "external.txt").write_text("preserve")
        self.ledger.mutate(first["token"], "release")
        result = self.begin("workbuddy")
        self.assertEqual(len(result["warnings"]), 1)
        self.assertTrue((self.root / "1001/old.txt").exists())
        self.assertEqual((Path(move["target"]) / "external.txt").read_text(), "preserve")

    def test_returned_old_path_updates_same_task_and_preserves_previous_archive(self):
        path = self.file("1001", "old.txt")
        first = self.begin()
        row = first["entries"][0]
        self.sync(first["token"], row, "original-task")
        self.ledger.archive(first["token"], date(2026, 10, 11))
        self.ledger.mutate(first["token"], "release")
        old_cold = self.root / "历史归档/2026/10月/1001/old.txt"
        self.file("1001", "old.txt", "revised")
        second = self.begin("workbuddy")
        returned = second["entries"][0]
        self.assertEqual(returned["id"], row["id"])
        self.assertEqual(returned["task_id"], "original-task")
        self.sync(second["token"], returned, "original-task")
        result = self.ledger.archive(second["token"], date(2026, 10, 11))
        self.assertEqual(result["moved"], 1)
        self.assertEqual(old_cold.read_text(), "delivered")
        actual = Path(self.ledger.entry(row["id"])["storage_path"])
        self.assertEqual(actual.read_text(), "revised")
        self.assertFalse(path.exists())

    def test_batch_limit_exclusion_and_year_boundary(self):
        for i in range(13): self.file("2025-12-31", str(i) + ".txt")
        self.file("2026-01-01", "new-year.txt")
        self.file("2026-01-02", "recent.txt")
        first = self.begin(day=date(2026, 1, 8))
        self.assertEqual(first["remaining"], 15)
        self.assertEqual(len(first["entries"]), 10)
        excluded = [r["id"] for r in first["entries"]]
        second = self.ledger.mutate(first["token"], "batch", data=excluded)
        self.assertEqual(len(second["entries"]), 5)
        for r in first["entries"] + second["entries"]: self.sync(first["token"], r, r["id"])
        result = self.ledger.archive(first["token"], date(2026, 1, 8))
        self.assertEqual(result["moved"], 2)
        self.assertTrue((self.root / "历史归档/2025/12月/2025-12-31").exists())
        self.assertTrue((self.root / "2026-01-02/recent.txt").exists())

    def test_shallow_packages_require_explicit_patent_type_and_keep_delivery_category(self):
        for name in ("系统及方法.zip", "发明专利.zip", "修改补图_研发证明材料.zip"):
            path = self.root / "1010" / name
            path.parent.mkdir(exist_ok=True)
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("申请书.docx", "unread contents")
        self.file("1010", "成果目录/申请书.docx")
        expected = {"系统及方法.zip": "专利（类别待确认）", "发明专利.zip": "发明专利",
                    "成果目录": "专利（类别待确认）", "修改补图_研发证明材料.zip": "研发证明材料"}
        for host in ("codex", "workbuddy"):
            result = self.begin(host)
            for row in result["entries"]:
                analysis = default_analysis(row)
                analysis["category"] = " 发明专利 "
                payload = self.ledger.mutate(result["token"], "draft", row["id"], analysis)
                category = expected[Path(row["source"]).name]
                self.assertIn("成果类别：" + category, payload["content"])
                self.assertIn(" · " + category + "/", payload["title"])
            self.ledger.mutate(result["token"], "release")


if __name__ == "__main__":
    unittest.main()
