#!/usr/bin/env python3
"""Import an explicitly supplied monthly delivery ZIP into the shared ledger."""
import argparse
from datetime import date
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import uuid
import zipfile

from delivery import Ledger, fingerprint


def members(archive, month):
    result, dates, seen = [], {}, set()
    for info in archive.infolist():
        name = info.filename
        if not info.flag_bits & 0x800:
            try:
                name = name.encode("cp437").decode("utf-8")
            except UnicodeError:
                pass
        path = PurePosixPath(name)
        mode = info.external_attr >> 16
        if (path.is_absolute() or ".." in path.parts or "\\" in name
                or stat.S_ISLNK(mode) or info.flag_bits & 1):
            raise ValueError("ZIP 包含不安全路径、符号链接或加密成员")
        if any(p.startswith((".", "__MACOSX", "~$")) for p in path.parts):
            continue
        if not path.parts or path in seen:
            raise ValueError("ZIP 成员路径重复或为空")
        seen.add(path)
        if len(path.parts) >= 2 and (len(path.parts) > 2 or info.is_dir()):
            match = re.match(r"^(\d{2})(\d{2})(\d{2})(?:\D|$)", path.parts[1])
            if not match:
                raise ValueError("无法识别日期目录：" + path.parts[1])
            day = date(2000 + int(match[1]), int(match[2]), int(match[3]))
            if day.month != month:
                raise ValueError("ZIP 日期与指定月份不一致")
            original = "/".join(path.parts[:2])
            if day.isoformat() in dates.values() and dates.get(original) != day.isoformat():
                raise ValueError("同一天包含多个顶层日期目录")
            dates[original] = day.isoformat()
        result.append((info, path))
    if not dates:
        raise ValueError("ZIP 中没有可导入的日期目录")
    return result, dates


def run(ledger, token, source, month, finish=False):
    source = Path(source).absolute()
    if source.parent != ledger.root or source.is_symlink():
        raise ValueError("月度 ZIP 须为归档根目录下的真实文件")
    key = "monthly-import:" + str(source)
    ledger.db.execute("BEGIN IMMEDIATE")
    try:
        ledger.require_lease(token)
        record = ledger.get_meta(key)
        if record and record["month"] != month:
            raise ValueError("已保存导入月份与参数不一致")
        if record is None:
            with zipfile.ZipFile(source) as archive:
                _, dates = members(archive, month)
            if any((ledger.root / day).exists() or (ledger.root / day).is_symlink() for day in dates.values()):
                raise ValueError("处理区日期目录已存在，停止以免覆盖")
            if len({day[:4] for day in dates.values()}) != 1:
                raise ValueError("月度 ZIP 包含多个年份")
            stage = ledger.state / ("monthly-" + uuid.uuid4().hex)
            record = dict(month=month, year=next(iter(dates.values()))[:4], stage=str(stage),
                          fingerprint=fingerprint(source), dates=dates, phase="extracting", folders={})
            ledger.set_meta(key, record)
        ledger.db.commit()
    except Exception:
        ledger.db.rollback()
        raise
    if record["phase"] == "done":
        return record
    stage = Path(record["stage"])
    if stage.parent != ledger.state or not stage.name.startswith("monthly-") or stage.is_symlink():
        raise ValueError("解压暂存位置异常")
    if not finish:
        if fingerprint(source) != record["fingerprint"]:
            raise ValueError("原始 ZIP 已变化")
        if record["phase"] == "extracting":
            if stage.exists():
                shutil.rmtree(stage)
            stage.mkdir(mode=0o700)
            with zipfile.ZipFile(source) as archive:
                checked, dates = members(archive, month)
                if dates != record["dates"]:
                    raise ValueError("ZIP 日期目录已变化")
                for info, path in checked:
                    target = stage.joinpath(*path.parts)
                    if info.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with archive.open(info) as incoming, target.open("xb") as output:
                            shutil.copyfileobj(incoming, output)
            record["folders"] = {name: [p.stat().st_dev, p.stat().st_ino]
                                 for name in dates for p in [stage / name]}
            record["phase"] = "publishing"
            ledger.set_meta(key, record)
            ledger.db.commit()
        for name, day in record["dates"].items():
            ledger.mutate(token, "renew")
            incoming, target = stage / name, ledger.root / day
            if incoming.exists() == target.exists():
                if not incoming.exists() and record["phase"] == "imported":
                    continue
                raise ValueError("发布来源和目标位置不明确：" + day)
            actual = incoming if incoming.exists() else target
            if actual.is_symlink() or [actual.stat().st_dev, actual.stat().st_ino] != record["folders"][name]:
                raise ValueError("发布目录身份不匹配：" + day)
            if incoming.exists():
                incoming.rename(target)
        ledger.db.execute("BEGIN IMMEDIATE")
        try:
            ledger.require_lease(token)
            for day in record["dates"].values():
                folder = ledger.root / day
                if folder.exists():
                    ledger.scan_folder(folder, date.fromisoformat(day))
            record["phase"] = "imported"
            ledger.set_meta(key, record)
            ledger.db.commit()
        except Exception:
            ledger.db.rollback()
            raise
    else:
        ledger.mutate(token, "renew")
        if record["phase"] not in ("imported", "finishing"):
            raise ValueError("请先完成解压导入")
        rows = [dict(r) for r in ledger.db.execute("SELECT * FROM entries")
                if Path(r["source"]).parent.name in record["dates"].values()]
        if not rows or any(r["status"] != "done" or r["storage_path"] == r["source"] for r in rows):
            raise ValueError("成果尚未全部完成核验并移动")
        destination = ledger.history / record["year"] / f"{month}月" / "原始打包"
        if any(p.is_symlink() for p in (ledger.history, destination.parent.parent, destination.parent, destination)):
            raise ValueError("原始打包目录不能是符号链接")
        destination.mkdir(parents=True, exist_ok=True)
        if record["phase"] == "imported":
            target = destination / source.name
            if target.exists() or target.is_symlink():
                target = destination / (source.stem + "-" + stage.name + source.suffix)
            record.update(phase="finishing", target=str(target))
            ledger.set_meta(key, record)
            ledger.db.commit()
        target = Path(record["target"])
        if source.exists() == target.exists() or target.parent != destination:
            raise ValueError("原始 ZIP 来源与目标位置不明确")
        actual = source if source.exists() else target
        if actual.is_symlink() or fingerprint(actual) != record["fingerprint"]:
            raise ValueError("原始 ZIP 内容已变化")
        if source.exists():
            source.rename(target)
        if stage.exists():
            shutil.rmtree(stage)
        record["phase"] = "done"
        ledger.set_meta(key, record)
        ledger.db.commit()
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token", required=True)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--month", type=int, required=True)
    parser.add_argument("--finish", action="store_true")
    args = parser.parse_args()
    ledger = Ledger()
    try:
        print(json.dumps(run(ledger, args.token, args.zip, args.month, args.finish), ensure_ascii=False))
    finally:
        ledger.db.close()
