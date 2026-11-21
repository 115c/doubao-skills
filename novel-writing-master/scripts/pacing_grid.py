#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pacing_grid.py — 从章纲表格生成节奏网格并告警

用法：
  python pacing_grid.py 章纲.md
  python pacing_grid.py 章纲.md --out grid.csv
  python pacing_grid.py 章纲.md --json

章纲表需含表头行（用 | 分隔）。识别列名（含关键词即可）：
  章号 / 标题 / 功能标签 / outcome / 钩子 / 埋收 / 字数

告警口径（对应 references/05、12、13）：
  [阻断] 章节缺号或章号重复
  [提示] 连续 3 章 outcome=yes（没有压力）
  [提示] 连续 3 章钩子=resolution/收束（没有拉力）
  [提示] 连续 3 章同一功能标签
  [提示] 某章缺钩子
  [提示] 字数离群（超过中位数 2 倍或低于一半）
"""

import argparse
import csv
import json
import os
import re
import statistics
import sys

KEY_MAP = [
    ("章号", ["章号", "章", "chapter", "no"]),
    ("标题", ["标题", "title"]),
    ("功能标签", ["功能", "标签", "松紧", "tag"]),
    ("outcome", ["outcome", "结果"]),
    ("钩子", ["钩子", "hook"]),
    ("埋收", ["埋", "收", "伏笔"]),
    ("字数", ["字数", "word"]),
]

HOOK_WEAK = {"resolution", "收束", "收束型", "无", ""}


def read_text(path):
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    return ""


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse(path):
    lines = [l for l in read_text(path).split("\n") if l.strip().startswith("|")]
    if not lines:
        return [], [], {}
    header, rows = None, []
    for l in lines:
        cells = split_row(l)
        if set("".join(cells)) <= set("-: "):
            continue
        if header is None:
            header = cells
            continue
        rows.append(cells)
    idx = {}
    for name, keys in KEY_MAP:
        for i, h in enumerate(header):
            if any(k.lower() in h.lower() for k in keys):
                idx[name] = i
                break
    return header, rows, idx


def as_int(s):
    m = re.search(r"\d+", s or "")
    return int(m.group(0)) if m else None


def analyze(header, rows, idx):
    recs = []
    for r in rows:
        rec = {}
        for name, i in idx.items():
            rec[name] = r[i] if i < len(r) else ""
        nums = re.findall(r"\d+", rec.get("字数", ""))
        rec["_words"] = [int(n) for n in nums[:2]] if nums else []
        rec["_no"] = as_int(rec.get("章号", ""))
        recs.append(rec)

    issues = []
    # 章号
    nos = [r["_no"] for r in recs if r["_no"]]
    if nos:
        if len(set(nos)) != len(nos):
            issues.append(("阻断", "章号重复"))
        miss = [i for i in range(min(nos), max(nos) + 1) if i not in set(nos)]
        if miss:
            issues.append(("阻断", f"章号缺号：{miss[:10]}"))

    # 连续同型
    def run_check(field, bad=None, label=""):
        run, start, prev = 0, None, None
        for i, r in enumerate(recs):
            v = (r.get(field) or "").strip()
            if bad is not None and v in bad:
                v = "<bad>"
            if v and v == prev:
                run += 1
                if run == 3:
                    issues.append(("提示", f"{label}连续 3 章为「{r.get(field)}」，起始第 {recs[i-2].get('章号')} 章"))
            else:
                run, prev = 1, v

    run_check("outcome", {"yes", "是"}, "outcome ")
    run_check("钩子", HOOK_WEAK, "钩子")
    run_check("功能标签", None, "功能标签")

    # 缺钩子
    for r in recs:
        if not (r.get("钩子") or "").strip():
            issues.append(("提示", f"第 {r.get('章号')} 章缺章尾钩子"))

    # 字数离群
    meds = []
    for r in recs:
        if r["_words"]:
            meds.append(sum(r["_words"]) / len(r["_words"]))
    if len(meds) >= 3:
        med = statistics.median(meds)
        for r, w in zip([r for r in recs if r["_words"]], meds):
            if w > med * 2 or w < med * 0.5:
                issues.append(("提示", f"第 {r.get('章号')} 章字数 {w:.0f} 离群（中位数 {med:.0f}）"))
    return recs, issues


def main():
    ap = argparse.ArgumentParser(description="章纲节奏网格")
    ap.add_argument("outline", help="章纲 markdown 文件")
    ap.add_argument("--out", help="导出 CSV 路径")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.outline):
        print(f"文件不存在：{args.outline}")
        return 2

    parsed = parse(args.outline)
    if not parsed or not parsed[0]:
        print("没在文件里找到章纲表格（需以 | 分隔的 markdown 表）")
        return 2
    header, rows, idx = parsed
    recs, issues = analyze(header, rows, idx)

    if args.json:
        print(json.dumps({"header": header, "rows": recs, "issues": issues},
                         ensure_ascii=False, indent=2))
    else:
        keep = [h for h in ("章号", "标题", "功能标签", "outcome", "钩子", "埋收", "字数") if h in idx]
        print(" | ".join(keep))
        for r in recs:
            print(" | ".join((r.get(k) or "") for k in keep))
        print()
        if issues:
            for lvl, msg in issues:
                print(f"[{lvl}] {msg}")
        else:
            print("未发现节奏告警（不等于合格，人工仍需核节拍位置）")

    if args.out:
        with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["章号", "标题", "功能标签", "outcome", "钩子", "埋收", "字数下限", "字数上限"])
            for r in recs:
                lo = r["_words"][0] if r["_words"] else ""
                hi = r["_words"][-1] if r["_words"] else ""
                w.writerow([r.get("章号", ""), r.get("标题", ""), r.get("功能标签", ""),
                            r.get("outcome", ""), r.get("钩子", ""), r.get("埋收", ""), lo, hi])
        print(f"\n已导出：{args.out}")

    return 1 if any(l == "阻断" for l, _ in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
