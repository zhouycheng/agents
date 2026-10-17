#!/usr/bin/env python3
"""Shared work-delivery ledger. Remote writes are performed by the host's MCP tools."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import time
import uuid
import zipfile
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

CONFIG = Path.home() / ".config/work-delivery-log/config.json"
STATE = Path.home() / ".local/state/work-delivery-log"
LEASE_SECONDS = 1800
BATCH_SIZE = 10
UNKNOWN = "类别待确认"
FIELDS = ("name", "category", "action", "project", "sender", "summary")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def visible(path):
    return not path.name.startswith((".", "~$")) and not path.is_symlink()


def fingerprint(path):
    if path.is_file():
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    # shortcut: 成果目录比较一层文件内容和子目录元数据，深层改动须重新归档或打包。
    parts = []
    for child in sorted(path.iterdir()):
        if visible(child):
            stat = child.stat()
            parts.append([child.name, fingerprint(child) if child.is_file()
                          else [stat.st_size, stat.st_mtime_ns]])
    return digest(json.dumps(parts, ensure_ascii=False).encode())


def docx_text(path):
    with zipfile.ZipFile(path) as z:
        info = z.getinfo("word/document.xml")
        if info.file_size > 4 * 1024 * 1024:
            return "文档正文超过浅层读取上限"
        root = ElementTree.fromstring(z.read(info))
    return "\n".join(node.text or "" for node in root.iter()
                     if node.tag.endswith("}t"))[:16000]


def inspect_source(row):
    if row["kind"] == "supplement":
        return row["source"]
    path = Path(row.get("storage_path") or row["source"])
    texts = [path.name]
    try:
        if path.is_dir():
            texts += [child.name for child in sorted(path.iterdir()) if visible(child)][:100]
        elif path.suffix.lower() == ".docx":
            texts.append(docx_text(path))
        elif path.suffix.lower() in (".txt", ".md"):
            with path.open("r", encoding="utf-8", errors="replace") as f:
                texts.append(f.read(16000))
        elif path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as z:
                texts += [n for n in z.namelist() if len(Path(n).parts) <= 2
                          and not any(p.startswith((".", "__MACOSX")) for p in Path(n).parts)][:100]
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as e:
        texts.append("浅层读取失败：" + type(e).__name__)
    return "\n".join(texts)


def default_analysis(row):
    name = Path(row["source"]).stem if row["kind"] != "supplement" else "手动补充工作"
    category = UNKNOWN
    for term, value in (("实用新型", "实用新型专利"), ("发明", "发明专利"),
                        ("软著", "软件著作权"), ("软件著作权", "软件著作权"),
                        ("研发证明材料", "研发证明材料"), ("专利", "专利（类别待确认）"),
                        ("技术交底书", "专利（类别待确认）"), ("申请书", "专利（类别待确认）")):
        if term in name:
            category = value
            break
    if category == UNKNOWN:
        category = {".pptx": "演示文稿", ".mp4": "视频", ".psb": "设计文件",
                    ".stp": "三维模型", ".step": "三维模型"}.get(Path(row["source"]).suffix.lower(), UNKNOWN)
    action = "动作待确认"
    for term, value in (("修改补图", "修改/补图"), ("修改", "修改"),
                        ("改图", "补图"), ("补图", "补图"), ("撰写", "撰写")):
        if term in name:
            action = value
            break
    return dict(name=name, category=category, action=action, project="项目待确认",
                sender="派发人未知", summary="已归档成果：" + name)


class Ledger:
    def __init__(self, config_path=CONFIG, state=STATE, now=None):
        self.config = json.loads(Path(config_path).read_text(encoding="utf-8"))
        for key in ("archive_root", "archive_year", "project_id", "project_name", "time_zone"):
            if key not in self.config:
                raise ValueError("配置缺少字段：" + key)
        self.root = Path(self.config["archive_root"]).expanduser().resolve(strict=True)
        if not self.root.is_dir() or not isinstance(self.config["archive_year"], int):
            raise ValueError("归档根目录或年份无效")
        if not self.config["project_id"] or not self.config["project_name"]:
            raise ValueError("请先配置并核对目标清单")
        ZoneInfo(self.config["time_zone"])
        self.retention_days = self.config.get("retention_days", 7)
        if type(self.retention_days) is not int or self.retention_days < 1:
            raise ValueError("retention_days 须为正整数")
        history = Path(self.config.get("history_root", str(self.root / "历史归档"))).expanduser()
        self.history = history.resolve()
        if history.is_symlink() or self.history.parent != self.root or re.fullmatch(r"\d{4}(-\d{2}-\d{2})?", self.history.name):
            raise ValueError("历史归档须为根目录下独立的非日期目录")
        self.now = now or time.time
        self.state = Path(state)
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(str(self.state / "ledger.sqlite3"), timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY, work_date TEXT NOT NULL, source TEXT NOT NULL,
                kind TEXT NOT NULL, fingerprint TEXT NOT NULL, status TEXT NOT NULL,
                task_id TEXT, payload TEXT, synced_fingerprint TEXT);
            CREATE TABLE IF NOT EXISTS events (
                at REAL NOT NULL, event TEXT NOT NULL, entry_id TEXT, detail TEXT);
        """)
        identity = [str(self.root), self.config["project_id"]]
        self.db.execute("BEGIN IMMEDIATE")
        try:
            previous = self.get_meta("identity")
            if previous is not None and previous != identity:
                raise ValueError("根目录或清单已变化；请使用独立状态目录，保留原账本")
            self.set_meta("identity", identity)
            columns = {row[1] for row in self.db.execute("PRAGMA table_info(entries)")}
            if "storage_path" not in columns:
                self.db.execute("ALTER TABLE entries ADD COLUMN storage_path TEXT")
            self.db.execute("UPDATE entries SET storage_path=source WHERE storage_path IS NULL AND kind!='supplement'")
            self.db.execute("CREATE TABLE IF NOT EXISTS folders (source TEXT PRIMARY KEY, signature TEXT NOT NULL)")
            self.db.execute("""CREATE TABLE IF NOT EXISTS moves (
                id TEXT PRIMARY KEY, source TEXT NOT NULL, target TEXT NOT NULL,
                status TEXT NOT NULL, manifest TEXT NOT NULL)""")
            self.db.commit()
        except Exception:
            self.db.rollback()
            self.db.close()
            raise

    def get_meta(self, key):
        row = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def set_meta(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, json.dumps(value, ensure_ascii=False)))

    def event(self, name, entry_id=None, detail=None):
        self.db.execute("INSERT INTO events VALUES (?,?,?,?)", (self.now(), name, entry_id, detail))

    def require_lease(self, token):
        lease = self.get_meta("lease")
        if not lease or lease["token"] != token or lease["expires"] <= self.now():
            raise ValueError("执行租约无效或已过期，请停止远端写入")
        lease["expires"] = self.now() + LEASE_SECONDS
        self.set_meta("lease", lease)

    def entry(self, entry_id):
        row = self.db.execute("SELECT * FROM entries WHERE id=?", (entry_id,)).fetchone()
        if row is None:
            raise ValueError("成果标识不存在")
        return dict(row)

    def folder_date(self, name):
        old = self.get_meta("date:" + name)
        if old:
            return date.fromisoformat(old)
        if re.fullmatch(r"\d{4}", name):
            value = date(self.config["archive_year"], int(name[:2]), int(name[2:]))
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", name):
            value = date.fromisoformat(name)
        else:
            return None
        self.set_meta("date:" + name, value.isoformat())
        return value

    def today(self):
        return datetime.now(ZoneInfo(self.config["time_zone"])).date()

    def signature(self, folder):
        values = []
        for path in sorted(folder.iterdir()):
            stat = path.lstat()
            values.append([path.name, stat.st_mode, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns])
            if visible(path) and path.is_dir():
                for child in sorted(path.iterdir()):
                    stat = child.lstat()
                    values.append([path.name + "/" + child.name, stat.st_mode, stat.st_size,
                                   stat.st_mtime_ns, stat.st_ctime_ns])
        return digest(json.dumps(values, ensure_ascii=False).encode())

    def scan_folder(self, folder, work_date):
        signature = self.signature(folder)
        snapshots = []
        for path in sorted(folder.iterdir()):
            if visible(path) and (path.is_file() or path.is_dir()):
                entry_id = digest((str(self.root) + "\0" + work_date.isoformat() + "\0" + str(path.relative_to(self.root))).encode())
                snapshots.append((entry_id, work_date.isoformat(), str(path),
                                  "directory" if path.is_dir() else "file", fingerprint(path)))
        if signature != self.signature(folder):
            raise ValueError("扫描期间目录变化：" + folder.name)
        for entry_id, work_date, source, kind, fp in snapshots:
            old = self.db.execute("SELECT * FROM entries WHERE id=?", (entry_id,)).fetchone()
            if old is None:
                self.db.execute("INSERT INTO entries (id,work_date,source,kind,fingerprint,status,storage_path) VALUES (?,?,?,?,?,'pending',?)",
                                (entry_id, work_date, source, kind, fp, source))
                self.event("pending", entry_id)
            else:
                status = old["status"]
                if old["fingerprint"] != fp:
                    status = status if status in ("creating", "updating", "created") else "pending"
                    self.event("changed", entry_id)
                self.db.execute("UPDATE entries SET fingerprint=?,status=?,storage_path=? WHERE id=?",
                                (fp, status, source, entry_id))
        self.db.execute("INSERT OR REPLACE INTO folders VALUES (?,?)", (str(folder), signature))
        return [item[0] for item in snapshots]

    def scan(self, today, blocked=()):
        warnings = []
        for folder in sorted(self.root.iterdir()):
            if folder == self.history or str(folder) in blocked or not visible(folder) or not folder.is_dir():
                continue
            try:
                work_date = self.folder_date(folder.name)
            except ValueError:
                warnings.append("无效日期目录：" + folder.name)
                continue
            if work_date is None or work_date > today:
                continue
            previous = self.db.execute("SELECT signature FROM folders WHERE source=?", (str(folder),)).fetchone()
            prefix = str(folder) + "/"
            returned = self.db.execute("SELECT 1 FROM entries WHERE substr(source,1,?)=? AND storage_path!=source LIMIT 1",
                                       (len(prefix), prefix)).fetchone()
            if previous is None or returned or previous[0] != self.signature(folder):
                self.scan_folder(folder, work_date)
        if self.get_meta("baseline_at") is None:
            self.set_meta("baseline_at", today.isoformat())
        return warnings

    def begin(self, host, today=None):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            lease = self.get_meta("lease")
            if lease and lease["expires"] > self.now():
                raise ValueError("已有执行器持有租约：" + lease["host"])
            token = uuid.uuid4().hex
            self.set_meta("lease", dict(token=token, host=host, expires=self.now() + LEASE_SECONDS))
            recovery = self.recover_moves()
            warnings = self.scan(today or self.today(), recovery["blocked"])
            if self.get_meta("retention_migrated") is None:
                count = self.db.execute("UPDATE entries SET status='pending' WHERE status='baseline'").rowcount
                self.set_meta("retention_migrated", True)
                self.event("backfill", detail=str(count))
            self.event("begin", detail=host)
            self.db.commit()
            return dict(token=token, lease_seconds=LEASE_SECONDS, warnings=warnings + recovery["errors"], **self.status())
        except Exception:
            self.db.rollback()
            raise

    def preflight(self, host, today=None):
        result = self.begin(host, today)
        try:
            archived = self.archive(result["token"], today)
            result.update(archived)
            result["warnings"] += archived["errors"]
            result["needs_remote"] = result["remaining"] > 0
            result["idle"] = not (result["needs_remote"] or result["monthly_imports"]
                                  or result["warnings"] or result["unresolved_moves"])
            if result["idle"]:
                self.mutate(result["token"], "release")
                result["token"] = None
            return result
        except Exception:
            self.mutate(result["token"], "release")
            raise

    def next_action(self, row):
        entry_id, status = row["id"], row["status"]
        if status == "pending":
            command = "start" if row["payload"] and row["synced_fingerprint"] == row["fingerprint"] else "inspect"
            return dict(kind="local", command=command, arguments=dict(id=entry_id))
        if status == "creating":
            return dict(kind="reconcile", marker="work-delivery:" + entry_id,
                        project_id=self.config["project_id"])
        if status in ("created", "updating"):
            return dict(kind="remote", tool="get_task_by_id", arguments=dict(task_id=row["task_id"]),
                        after_read="update_then_verify" if status == "updating" else "verify")
        return None

    def status(self, exclude=()):
        rows = [dict(row) for row in self.db.execute("SELECT * FROM entries ORDER BY work_date,source")]
        pending = [row for row in rows if row["status"] not in ("baseline", "done")]
        moves = [dict(row) for row in self.db.execute("SELECT id,source,target,status FROM moves")]
        for row in pending:
            row["next_action"] = self.next_action(row)
        lease = self.get_meta("lease") or {}
        retries = self.get_meta("completion_retries") or {}
        failed = retries.get("entries", {}) if retries.get("token") == lease.get("token") else {}
        progress = dict(pending=len(pending), verified=sum(r["status"] == "done" for r in rows),
                        archived=sum(r["status"] == "done" and r["storage_path"] is not None
                                     and r["storage_path"] != r["source"] for r in rows),
                        exceptions=len(set(exclude) | {k for k, v in failed.items() if v >= 4})
                                   + sum(m["status"] == "prepared" for m in moves))
        return dict(project=dict(id=self.config["project_id"], name=self.config["project_name"]),
                    baseline_at=self.get_meta("baseline_at"), counts=dict(Counter(row["status"] for row in rows)),
                    retention_days=self.retention_days, history_root=str(self.history),
                    progress=progress, remaining=len(pending), entries=[row for row in pending if row["id"] not in exclude][:BATCH_SIZE],
                    monthly_imports=[dict(source=r["key"].removeprefix("monthly-import:"),
                                          month=v["month"], phase=v["phase"])
                                     for r in self.db.execute("SELECT * FROM meta WHERE key LIKE 'monthly-import:%'")
                                     for v in [json.loads(r["value"])] if v["phase"] != "done"],
                    archived_directories=sum(m["status"] == "done" and Path(m["source"]).parent == self.root for m in moves),
                    unresolved_moves=[m for m in moves if m["status"] == "prepared"])

    def recover_moves(self):
        errors, blocked = [], []
        for row in self.db.execute("SELECT * FROM moves WHERE status='prepared'").fetchall():
            source, target = Path(row["source"]), Path(row["target"])
            manifest = json.loads(row["manifest"])
            try:
                if (source.parent != self.root and source.parent.parent != self.history
                        or target.parent.parent != self.history and target.parent.parent.parent != self.history
                        or any(p.is_symlink() for p in (self.history, source.parent, target.parent, target.parent.parent))):
                    raise ValueError("移动路径或历史目录边界不匹配")
                if source.exists() == target.exists():
                    raise ValueError("来源与目标同时存在或同时缺失")
                actual = source if source.exists() else target
                stat = actual.lstat()
                if [stat.st_dev, stat.st_ino] != manifest["identity"] or actual.is_symlink():
                    raise ValueError("目录身份不匹配")
                if actual == source:
                    if self.signature(source) != manifest["signature"]:
                        self.db.execute("UPDATE moves SET status='cancelled' WHERE id=?", (row["id"],))
                        continue
                    if target.exists() or target.is_symlink():
                        raise ValueError("移动目标已存在")
                    source.rename(target)
                for item in manifest["entries"]:
                    self.db.execute("UPDATE entries SET storage_path=? WHERE id=? AND storage_path=?",
                                    (str(target / item["name"]), item["id"], str(source / item["name"])))
                self.db.execute("DELETE FROM folders WHERE source=?", (str(source),))
                self.db.execute("UPDATE moves SET status='done' WHERE id=?", (row["id"],))
                self.event("archived", detail=row["id"])
            except (OSError, ValueError) as e:
                errors.append(str(source) + "：" + str(e))
                blocked.append(str(source))
        return dict(errors=errors, blocked=blocked)

    def group_history(self, token):
        errors = []
        for old in self.db.execute("SELECT * FROM moves WHERE status='done'").fetchall():
            source = Path(old["target"])
            if (source.parent.parent != self.history or not source.exists()
                    or self.db.execute("SELECT 1 FROM moves WHERE source=? AND status='prepared'", (str(source),)).fetchone()):
                continue
            self.db.execute("BEGIN IMMEDIATE")
            try:
                self.require_lease(token)
                manifest = json.loads(old["manifest"])
                work_date = date.fromisoformat(self.entry(manifest["entries"][0]["id"])["work_date"])
                month = source.parent / f"{work_date.month}月"
                if any(p.is_symlink() for p in (self.history, source.parent, month, source)):
                    raise ValueError("历史目录不能是符号链接")
                month.mkdir(exist_ok=True)
                move_id = uuid.uuid4().hex
                target = month / source.name
                if target.exists() or target.is_symlink():
                    target = month / (source.name + "-" + move_id[:12])
                stat = source.lstat()
                if [stat.st_dev, stat.st_ino] != manifest["identity"]:
                    raise ValueError("历史目录身份不匹配")
                manifest["signature"] = self.signature(source)
                self.db.execute("INSERT INTO moves VALUES (?,?,?,'prepared',?)",
                                (move_id, str(source), str(target), json.dumps(manifest, ensure_ascii=False)))
                self.db.commit()
                self.db.execute("BEGIN IMMEDIATE")
                self.require_lease(token)
                errors.extend(self.recover_moves()["errors"])
                self.db.commit()
            except (OSError, ValueError, sqlite3.Error) as e:
                self.db.rollback()
                errors.append(str(source) + "：" + str(e))
        return errors

    def archive(self, token, today=None):
        cutoff = (today or self.today()) - timedelta(days=self.retention_days - 1)
        errors = []
        before = self.status()["archived_directories"]
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.require_lease(token)
            recovery = self.recover_moves()
            errors.extend(recovery["errors"])
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        errors.extend(self.group_history(token))
        for folder in sorted(self.root.iterdir()):
            if folder == self.history or str(folder) in recovery["blocked"] or not visible(folder) or not folder.is_dir():
                continue
            self.db.execute("BEGIN IMMEDIATE")
            try:
                self.require_lease(token)
                try:
                    work_date = self.folder_date(folder.name)
                except ValueError:
                    work_date = None
                if work_date is None or work_date >= cutoff:
                    self.db.commit()
                    continue
                rows = [dict(r) for r in self.db.execute("SELECT * FROM entries WHERE kind!='supplement'")
                        if Path(r["source"]).parent == folder and r["storage_path"] == r["source"]]
                if not rows or any(r["status"] != "done" or not r["task_id"] for r in rows):
                    self.db.commit()
                    continue
                ids = self.scan_folder(folder, work_date)
                rows = [self.entry(i) for i in ids]
                if not rows or any(r["status"] != "done" or r["synced_fingerprint"] != r["fingerprint"] for r in rows):
                    self.db.commit()
                    continue
                if self.history.is_symlink():
                    raise ValueError("历史归档不能是符号链接")
                self.history.mkdir(exist_ok=True)
                year = self.history / str(work_date.year)
                if year.is_symlink():
                    raise ValueError("历史年份目录不能是符号链接")
                year.mkdir(exist_ok=True)
                if year.is_symlink() or year.stat().st_dev != folder.stat().st_dev:
                    raise ValueError("历史目标须为同盘真实目录")
                month = year / f"{work_date.month}月"
                if month.is_symlink():
                    raise ValueError("历史月份目录不能是符号链接")
                month.mkdir(exist_ok=True)
                move_id = uuid.uuid4().hex
                target = month / folder.name
                if target.exists() or target.is_symlink():
                    target = month / (folder.name + "-" + move_id[:12])
                stat = folder.lstat()
                signature = self.db.execute("SELECT signature FROM folders WHERE source=?", (str(folder),)).fetchone()[0]
                if signature != self.signature(folder):
                    raise ValueError("移动前目录再次变化")
                manifest = dict(identity=[stat.st_dev, stat.st_ino], signature=signature,
                                entries=[dict(id=r["id"], name=Path(r["source"]).name, fingerprint=r["fingerprint"],
                                              task_id=r["task_id"]) for r in rows])
                self.db.execute("INSERT INTO moves VALUES (?,?,?,'prepared',?)",
                                (move_id, str(folder), str(target), json.dumps(manifest, ensure_ascii=False)))
                self.db.commit()
                self.db.execute("BEGIN IMMEDIATE")
                self.require_lease(token)
                outcome = self.recover_moves()
                errors.extend(outcome["errors"])
                self.db.commit()
            except (OSError, ValueError, sqlite3.Error) as e:
                self.db.rollback()
                errors.append(str(folder) + "：" + str(e))
        after = self.status()["archived_directories"]
        return dict(moved=after - before, errors=errors, **self.status())

    def mutate(self, token, operation, entry_id=None, data=None):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.require_lease(token)
            row = self.entry(entry_id) if entry_id else None
            result = {}
            if operation == "inspect":
                if row["status"] != "pending" or row["storage_path"] not in (None, row["source"]):
                    raise ValueError("仅待处理的活动成果可以读取")
                if row["kind"] != "supplement":
                    fp = fingerprint(Path(row["source"]))
                    self.db.execute("UPDATE entries SET fingerprint=? WHERE id=?", (fp, entry_id))
                    row["fingerprint"] = fp
                result = dict(entry=row, source_text=inspect_source(row), defaults=default_analysis(row))
            elif operation == "batch":
                result = self.status(data or ())
            elif operation == "backfill":
                count = self.db.execute("UPDATE entries SET status='pending' WHERE status='baseline'").rowcount
                result = dict(queued=count, **self.status())
            elif operation == "queue":
                if row["status"] != "baseline":
                    raise ValueError("仅基线条目需要显式补录")
                self.db.execute("UPDATE entries SET status='pending' WHERE id=?", (entry_id,))
            elif operation == "draft":
                if row["status"] != "pending":
                    raise ValueError("仅 pending 条目可以生成文案")
                analysis = default_analysis(row) if data is None else data
                if not isinstance(analysis, dict) or set(analysis) != set(FIELDS) or any(not isinstance(analysis[k], str) or not analysis[k].strip()
                                                       or len(analysis[k]) > 4000 for k in FIELDS):
                    raise ValueError("分析须包含六个非空文本字段：" + ",".join(FIELDS))
                analysis = dict(analysis)
                analysis["category"] = " ".join(analysis["category"].split())
                source_name = Path(row["source"]).name
                if row["kind"] != "supplement" and "研发证明材料" in source_name:
                    analysis["category"] = "研发证明材料"
                elif (row["kind"] != "supplement" and analysis["category"] in ("发明专利", "实用新型专利")
                      and (row["kind"] == "directory" or Path(source_name).suffix.lower() == ".zip")):
                    term = "发明" if analysis["category"] == "发明专利" else "实用新型"
                    if term not in source_name and analysis["category"] not in inspect_source(row):
                        analysis["category"] = "专利（类别待确认）"
                name = " ".join(analysis["name"].split())
                category = " ".join(analysis["category"].split())
                action = " ".join(analysis["action"].split())
                title = f'{row["work_date"]} · {category}/{action} · {name}'
                marker = "work-delivery:" + entry_id
                details = ["完整名称：" + analysis["name"], "归档日期：" + row["work_date"],
                           "成果类别：" + analysis["category"], "工作动作：" + analysis["action"],
                           "系统或项目：" + analysis["project"], "任务派发人：" + analysis["sender"],
                           "来源：" + row["source"], "说明：" + analysis["summary"],
                           "记录更新时间：" + datetime.now(ZoneInfo(self.config["time_zone"])).isoformat(timespec="seconds"), marker]
                start = datetime.fromisoformat(row["work_date"]).replace(tzinfo=ZoneInfo(self.config["time_zone"]))
                payload = dict(projectId=self.config["project_id"], title=title[:180], content="\n".join(details),
                               kind="TEXT", startDate=start.strftime("%Y-%m-%dT%H:%M:%S.000%z"),
                               isAllDay=True, timeZone=self.config["time_zone"])
                self.db.execute("UPDATE entries SET payload=?,synced_fingerprint=? WHERE id=?",
                                (json.dumps(payload, ensure_ascii=False), row["fingerprint"], entry_id))
                result = payload
            elif operation == "start":
                if row["status"] != "pending" or not row["payload"]:
                    raise ValueError("须先生成 pending 条目的文案；creating 条目必须对账")
                if row["synced_fingerprint"] != row["fingerprint"]:
                    raise ValueError("成果变化，请重新生成文案")
                if row["kind"] != "supplement" and fingerprint(Path(row["source"])) != row["synced_fingerprint"]:
                    raise ValueError("成果变化，请重新 inspect 并生成文案")
                status = "updating" if row["task_id"] else "creating"
                self.db.execute("UPDATE entries SET status=? WHERE id=?", (status, entry_id))
                result = dict(operation="update" if row["task_id"] else "create", task_id=row["task_id"],
                              payload=json.loads(row["payload"]))
            elif operation in ("created", "finish", "verify"):
                if row["status"] not in ("creating", "created", "updating") or not row["payload"]:
                    raise ValueError("该条目没有正在同步的任务")
                payload = json.loads(row["payload"])
                if (not isinstance(data, dict) or not isinstance(data.get("id"), str) or not data["id"]
                        or not isinstance(data.get("content"), str) or data.get("projectId") != self.config["project_id"]
                        or "work-delivery:" + entry_id not in data.get("content", "")
                        or (row["task_id"] and data["id"] != row["task_id"])):
                    raise ValueError("远端任务 ID、清单或同步标识不匹配")
                if operation in ("finish", "verify"):
                    if (operation == "finish" and data.get("status") != 2) or data.get("title") != payload["title"] or data.get("content", "").strip() != payload["content"].strip():
                        raise ValueError("须读回已完成且文案一致的远端任务")
                    raw_date = data.get("startDate")
                    if not isinstance(raw_date, str):
                        raise ValueError("远端任务缺少工作日期，请保存完整读回 JSON")
                    raw_date = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", raw_date.replace("Z", "+00:00"))
                    remote_date = datetime.fromisoformat(raw_date)
                    if (remote_date.tzinfo is None or data.get("isAllDay") is not True
                            or remote_date.astimezone(ZoneInfo(self.config["time_zone"])).date().isoformat() != row["work_date"]):
                        raise ValueError("远端工作日期或全天标识不匹配")
                    if operation == "verify" and data.get("status") != 2:
                        if data.get("status") != 0 or not row["task_id"]:
                            raise ValueError("完成重试须有已保存的任务 ID 和明确的未完成状态")
                        retries = self.get_meta("completion_retries") or {}
                        if retries.get("token") != token:
                            retries = dict(token=token, entries={})
                        attempts = retries["entries"].get(entry_id, 0)
                        if attempts >= 3:
                            retries["entries"][entry_id] = 4
                            self.set_meta("completion_retries", retries)
                            result = dict(action="defer", id=entry_id, reason="完成核验已达到本次重试上限")
                        else:
                            retries["entries"][entry_id] = attempts + 1
                            self.set_meta("completion_retries", retries)
                            result = dict(action="complete_then_read", attempt=attempts + 1,
                                          delay_seconds=(2, 5, 10)[attempts],
                                          tool="complete_task", arguments=dict(project_id=self.config["project_id"],
                                                                              task_id=row["task_id"]))
                        self.event("completion_retry", entry_id, json.dumps(result))
                        self.db.commit()
                        return result
                    if row["kind"] == "supplement":
                        current = digest(row["source"].encode())
                    elif row["storage_path"] != row["source"] and not Path(row["source"]).exists():
                        current = row["fingerprint"]
                    else:
                        current = fingerprint(Path(row["source"]))
                    status = "done" if current == row["synced_fingerprint"] else "pending"
                    self.db.execute("UPDATE entries SET task_id=?,status=?,fingerprint=? WHERE id=?",
                                    (data["id"], status, current, entry_id))
                    retries = self.get_meta("completion_retries") or {}
                    if retries.get("token") == token:
                        retries.get("entries", {}).pop(entry_id, None)
                        self.set_meta("completion_retries", retries)
                    result = dict(action=status, id=entry_id)
                else:
                    self.db.execute("UPDATE entries SET task_id=?,status='created' WHERE id=?", (data["id"], entry_id))
            elif operation == "supplement":
                work_date = date.fromisoformat(data["date"]).isoformat()
                text = data["text"].strip()
                if not text or len(text) > 16000:
                    raise ValueError("补充内容须为 1 至 16000 字符")
                entry_id = digest((str(self.root) + "\0supplement\0" + work_date + "\0" + text).encode())
                self.db.execute("INSERT OR IGNORE INTO entries (id,work_date,source,kind,fingerprint,status) VALUES (?,?,?,'supplement',?,'pending')",
                                (entry_id, work_date, text, digest(text.encode())))
                result = self.entry(entry_id)
            elif operation == "release":
                self.db.execute("DELETE FROM meta WHERE key='lease'")
            elif operation != "renew":
                raise ValueError("不支持的操作")
            self.event(operation, entry_id)
            self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=CONFIG)
    p.add_argument("--state", type=Path, default=STATE)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    for command in ("begin", "preflight"):
        begin = sub.add_parser(command)
        begin.add_argument("--host", choices=("codex", "workbuddy"), required=True)
    for command in ("inspect", "draft", "start", "created", "finish", "verify", "queue", "renew", "release", "supplement", "batch", "backfill", "archive"):
        child = sub.add_parser(command)
        child.add_argument("--token", required=True)
        if command in ("inspect", "draft", "start", "created", "finish", "verify", "queue"):
            child.add_argument("--id", required=True)
        if command in ("draft", "created", "finish", "verify"):
            child.add_argument("--json", type=Path, required=command != "draft")
        if command == "supplement":
            child.add_argument("--date", required=True)
            child.add_argument("--text-file", type=Path, required=True)
        if command == "batch":
            child.add_argument("--exclude", action="append", default=[])
    args = p.parse_args()
    ledger = None
    try:
        ledger = Ledger(args.config, args.state)
        if args.command in ("begin", "preflight"):
            result = getattr(ledger, args.command)(args.host)
        elif args.command == "status":
            result = ledger.status()
        elif args.command == "archive":
            result = ledger.archive(args.token)
        else:
            data = json.loads(args.json.read_text(encoding="utf-8")) if getattr(args, "json", None) else None
            if args.command == "supplement":
                data = dict(date=args.date, text=args.text_file.read_text(encoding="utf-8"))
            if args.command == "batch":
                data = args.exclude
            result = ledger.mutate(args.token, args.command, getattr(args, "id", None), data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, sqlite3.Error) as e:
        print(json.dumps(dict(error=str(e)), ensure_ascii=False), file=sys.stderr)
        return 1
    finally:
        if ledger:
            ledger.db.close()


if __name__ == "__main__":
    sys.exit(main())
