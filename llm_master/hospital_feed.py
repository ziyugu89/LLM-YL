# -*- coding: utf-8 -*-
"""读取医院导入的号源、排队和检查报告。没有文件或文件为空时不编造记录。"""
import json
import os

_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hospital_feed", "feed.json")
_MAX_BYTES = 2_000_000
_KINDS = ("slots", "queue", "reports")
_JSON_KEY = {"slots": "slots", "queue": "queues", "reports": "reports"}
_TITLES = {"slots": "号源", "queue": "排队", "reports": "报告"}
_EMPTY = "尚未导入医院号源、排队和检查报告。请把资料写入 hospital_feed/feed.json 后再查询。"


def title_of(kind):
    return _TITLES.get(kind, "")


def hospital_kinds(query):
    text = query or ""
    kinds = []
    if any(word in text for word in ("号源", "还有号", "余号", "可预约", "排班")):
        kinds.append("slots")
    if any(word in text for word in ("排队", "候诊", "叫号")):
        kinds.append("queue")
    if any(word in text for word in ("检查报告", "化验", "检验报告", "报告单", "检查结果")):
        kinds.append("reports")
    return kinds


def _text(value, limit):
    return str(value or "").replace("\n", " ").strip()[:limit]


def _line(fields):
    return "；".join(f"{name}：{value}" for name, value in fields if value not in ("", None))


def _whole(value):
    if isinstance(value, bool) or isinstance(value, float):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _row(kind, raw, index):
    if not isinstance(raw, dict):
        return None
    if kind == "slots":
        department = _text(raw.get("department"), 40)
        if not department:
            return None
        remain = _whole(raw.get("remain"))
        if remain is None:
            return None
        row = {
            "department": department,
            "doctor": _text(raw.get("doctor"), 40),
            "date": _text(raw.get("date"), 20),
            "period": _text(raw.get("period"), 20),
            "remain": remain,
            "place": _text(raw.get("place"), 40),
        }
        row["text"] = _line((
            ("科室", row["department"]),
            ("医生", row["doctor"]),
            ("日期", row["date"]),
            ("时段", row["period"]),
            ("剩余号源", row["remain"]),
            ("地点", row["place"]),
        ))
    elif kind == "queue":
        department = _text(raw.get("department"), 40)
        number = _text(raw.get("number"), 20)
        if not department and not number:
            return None
        ahead = _whole(raw.get("ahead"))
        if ahead is None:
            return None
        row = {
            "patient_id": _text(raw.get("patient_id"), 40),
            "patient_name": _text(raw.get("patient_name"), 40),
            "department": department,
            "room": _text(raw.get("room"), 40),
            "number": number,
            "ahead": ahead,
            "status": _text(raw.get("status"), 20),
        }
        row["text"] = _line((
            ("就诊人", row["patient_name"]),
            ("科室", row["department"]),
            ("诊室", row["room"]),
            ("号码", row["number"]),
            ("前面还有", row["ahead"]),
            ("状态", row["status"]),
        ))
    else:
        item = _text(raw.get("item"), 40)
        if not item:
            return None
        row = {
            "patient_id": _text(raw.get("patient_id"), 40),
            "patient_name": _text(raw.get("patient_name"), 40),
            "item": item,
            "time": _text(raw.get("time"), 30),
            "summary": _text(raw.get("summary"), 500),
            "status": _text(raw.get("status"), 20),
        }
        row["text"] = _line((
            ("就诊人", row["patient_name"]),
            ("项目", row["item"]),
            ("时间", row["time"]),
            ("状态", row["status"]),
            ("原文", row["summary"]),
        ))
    row["id"] = _text(raw.get("id"), 40) or f"{kind}-{index}"
    return row


def _staff(viewer):
    roles = {str(role) for role in (viewer or {}).get("roles") or []}
    return bool(roles & {"admin", "doctor"})


def _visible(kind, row, viewer):
    if kind == "slots":
        return True
    if _staff(viewer):
        return True
    codes = {str((viewer or {}).get("id") or ""), str((viewer or {}).get("pcode") or "")}
    codes.discard("")
    return row.get("patient_id") in codes


def _matched(row, keyword):
    keyword = (keyword or "").strip()
    if not keyword:
        return True
    values = [str(value) for value in row.values() if value not in ("", None)]
    if keyword in " ".join(values):
        return True
    return any(len(value) >= 2 and value in keyword for value in values)


def load(path=None):
    path = path or _FILE
    empty = {"ok": False, "message": _EMPTY, "slots": [], "queues": [], "reports": [], "skipped": 0}
    if not os.path.isfile(path):
        return empty
    try:
        if os.path.getsize(path) > _MAX_BYTES:
            return {**empty, "message": "导入文件过大，请拆分后再放入 feed.json。"}
        with open(path, "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {**empty, "message": "feed.json 无法读取，请确认为 JSON 对象。"}
    if not isinstance(data, dict):
        return {**empty, "message": "feed.json 需要包含 slots、queues、reports 三个数组。"}
    parsed = {"slots": [], "queues": [], "reports": []}
    skipped = 0
    for kind in _KINDS:
        rows = data.get(_JSON_KEY[kind]) or []
        if not isinstance(rows, list):
            skipped += 1
            continue
        for index, raw in enumerate(rows, start=1):
            row = _row(kind, raw, index)
            if row is None:
                skipped += 1
            else:
                parsed[_JSON_KEY[kind]].append(row)
    total = sum(len(rows) for rows in parsed.values())
    if total == 0:
        message = "文件里没有可用记录，请核对必填项。" if skipped else _EMPTY
        return {**empty, "message": message, "skipped": skipped}
    return {"ok": True, "message": "", "skipped": skipped, **parsed}


def query(kind, keyword, viewer, path=None):
    if kind not in _KINDS:
        kind = "slots"
    loaded = load(path)
    visible = {}
    for name in _KINDS:
        visible[name] = [row for row in loaded[_JSON_KEY[name]] if _visible(name, row, viewer)]
    counts = {name: len(rows) for name, rows in visible.items()}
    title = _TITLES[kind]
    if not loaded["ok"]:
        return {
            "ready": False,
            "kind": kind,
            "title": title,
            "message": loaded["message"],
            "items": [],
            "counts": counts,
            "skipped": loaded["skipped"],
        }
    items = [row for row in visible[kind] if _matched(row, keyword)]
    return {
        "ready": True,
        "kind": kind,
        "title": title,
        "message": "" if items else "没有符合条件的记录。",
        "items": items[:50],
        "counts": counts,
        "skipped": loaded["skipped"],
    }
