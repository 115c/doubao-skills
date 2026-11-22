#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""novel_check.py — 小说稿件机检（无第三方依赖）

三种用法：
  1) 稿件体检：python novel_check.py 正文.md  [--chapter N] [--no-ai] [--json]
     - 自动按文件名识别章号，读 大纲/章纲.md 的字数区间做闸口（±10% 提示，±20% 阻断）
     - 自动读 追踪/_state.json 的人物名单，统计本章需记人名与本章新增人名
  2) 目录体检：python novel_check.py 正文/     [--json]
  3) 账本/状态：python novel_check.py --state 追踪/_state.json
                python novel_check.py --consistency 追踪/
                python novel_check.py --ledger 追踪/    # 章纲「埋收」列 × 账本章号 对齐

设计原则：脚本只定位，不判定。命中的是"线索"，不是"错误"；
blocking 项要改到净或登记白名单，advisory 项回上下文判断。
"""

import argparse
import json
import os
import re
import sys

# ---------------------------------------------------------------- 词表

# 强信号：出现即高概率是 AI 腔 / 预告腔 / 意义膨胀
BLOCKING = [
    r"他不知道的是", r"她不知道的是", r"殊不知", r"多年以后", r"冥冥之中",
    r"仿佛预示着", r"仿佛在预示", r"命运的齿轮", r"宿命的齿轮", r"命运的棋局",
    r"从这一刻开始", r"从今以后[，,]", r"故事才刚刚开始", r"属于[他她]的反击",
    r"意义深远", r"未来可期", r"前途无量", r"可谓是?", r"这就是命运的",
    r"他这才意识到", r"她这才意识到", r"他终于明白", r"她终于明白",
    r"真正重要的是", r"这意味着", r"由此可见", r"综上所述", r"不难看出",
    r"事实上[，,]", r"与此同时[，,]", r"这一刻[，,].{0,6}注定",
    r"所有人都会记住", r"一切都将改变", r"一切都变了",
    r"（此处|\(此处", r"待补", r"TODO", r"XXX", r"【】",
]

# 弱信号：只在扎堆时成问题，单次出现按语境判断
ADVISORY = [
    r"微微", r"淡淡", r"缓缓", r"轻轻", r"一丝", r"一抹", r"些许", r"几分",
    r"隐约", r"微不可察", r"毫无征兆", r"不禁", r"不由得",
    r"眼中闪过", r"嘴角勾起", r"嘴角微扬", r"脸色一变", r"眉头微皱",
    r"瞳孔一缩", r"瞳孔微缩", r"瞳孔收缩", r"指节泛白", r"指尖轻叩",
    r"攥紧袖口", r"目光移开", r"头皮发紧", r"眼皮一跳", r"心口一沉",
    r"心头一震", r"心中一动", r"心下了然", r"心中暗道", r"心中一凛",
    r"涌起一股", r"不容置疑", r"不容置喙", r"显而易见", r"毫无疑问",
    r"前所未有", r"闪烁着光芒", r"深邃", r"凛冽", r"如潮水般", r"如闪电般",
    r"映入眼帘", r"此时此刻", r"不由自主", r"情不自禁", r"话锋一转",
    r"取而代之", r"梨花带雨", r"如沐春风", r"沉声道", r"淡淡地说",
]

PLACEHOLDER = [r"TODO", r"待补", r"待定", r"此处可", r"XXX+", r"【】", r"占位"]

# ---------------------------------------------------------------- 工具


def read_text(path):
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    with open(path, "rb") as f:
        return f.read().decode("utf-8", errors="ignore")


def strip_quotes(text):
    """去掉对话引号内的内容，用于旁白类检查（"" 和 「」 和 『』）"""
    t = re.sub(r"“[^”]*”", "　", text)
    t = re.sub(r"「[^」]*」", "　", t)
    t = re.sub(r"『[^』]*』", "　", t)
    t = re.sub(r"\"[^\"]*\"", "　", t)
    return t


def count_hits(text, patterns):
    hits = []
    for p in patterns:
        for m in re.finditer(p, text):
            s = max(0, m.start() - 12)
            e = min(len(text), m.end() + 12)
            hits.append((m.group(0), text[s:e].replace("\n", " ")))
    return hits


def sentences(text):
    """切句：按句末标点与换行切；剥掉引号后只剩标点的碎片不算句子。

    否则一段短对话（“问”“柳巧云”）的引号会被切成 0 字句，
    误判成电报体。
    """
    parts = re.split(r"[。！？…；\n]+", text)
    out = []
    for p in parts:
        s = p.strip().strip("“”\"'「」『』\u3000 ")
        if not re.search(r"[\u4e00-\u9fffA-Za-z0-9]", s):
            continue
        out.append(s)
    return out


def paragraphs(text):
    lines = [l.strip() for l in text.split("\n")]
    return [l for l in lines if l]


def ngrams(text, n=8):
    clean = re.sub(r"\s", "", text)
    return [clean[i:i + n] for i in range(0, max(0, len(clean) - n))]


# ---------------------------------------------------------------- 章纲 / 账本 / 人名

CHAP_RE = re.compile(r"第0*(\d+)章")


def guess_chapter(path):
    m = CHAP_RE.search(os.path.basename(path))
    return int(m.group(1)) if m else None


def project_root_of(path):
    """正文/第0002章_x.md、大纲/章纲.md、追踪/、审稿/ 都归到同一个项目根。"""
    p = os.path.abspath(path)
    base = p if os.path.isdir(p) else os.path.dirname(p)
    if os.path.basename(base) in ("正文", "大纲", "追踪", "审稿", "设定", "发布"):
        return os.path.dirname(base)
    return base


def find_outline(project_dir):
    for cand in (os.path.join("大纲", "章纲.md"), "章纲.md"):
        p = os.path.join(project_dir, cand)
        if os.path.exists(p):
            return p
    return None


def load_outline(path):
    """解析章纲表：字数区间、埋收列。返回 {'ranges','ledger','titles'}。"""
    out = {"ranges": {}, "ledger": {}, "titles": {}}
    if not path or not os.path.exists(path):
        return out
    for line in read_text(path).split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 4 or not cells[0].isdigit():
            continue
        no = int(cells[0])
        out["titles"][no] = cells[1] if len(cells) > 1 else ""
        if len(cells) >= 7:
            m = re.search(r"(\d{3,5})\s*[-–~至]\s*(\d{3,5})", cells[6])
            if m:
                out["ranges"][no] = (int(m.group(1)), int(m.group(2)))
        if len(cells) >= 6:
            marks = []
            for tok in re.split(r"[/、,，\s]+", cells[5]):
                m = re.match(r"([PCQ]\d{3})\s*(埋|收)", tok)
                if m:
                    marks.append((m.group(1), m.group(2)))
            if marks:
                out["ledger"][no] = marks
    return out


def check_names(path, chapter_no, project_dir):
    """本章出现的需记人名；首次出现在本章的算「新增」。"""
    if not chapter_no:
        return None
    state = os.path.join(project_dir, "追踪", "_state.json")
    body = os.path.join(project_dir, "正文")
    if not (os.path.exists(state) and os.path.isdir(body)):
        return None
    try:
        data = json.loads(read_text(state))
    except json.JSONDecodeError:
        return None
    names = list((data.get("characters") or {}).keys())
    if not names:
        return None
    files, first = [], {}
    for fn in os.listdir(body):
        m = CHAP_RE.search(fn)
        if m:
            files.append((int(m.group(1)), os.path.join(body, fn)))
    files.sort()
    for no, fp in files:
        txt = read_text(fp)
        for n in names:
            if n not in first and n in txt:
                first[n] = no
    cur = read_text(path)
    present = [n for n in names if n in cur]
    new = [n for n in present if first.get(n) == chapter_no]
    return {"present": present, "new": new}


def check_ledger(project_dir, outline_path=None):
    """章纲「埋收」列 × _state.json 账本章号 对齐；发现冲突报错误，不自动改。"""
    errs, warns = [], []
    outline = load_outline(outline_path or find_outline(project_dir))
    state = os.path.join(project_dir, "追踪", "_state.json")
    if not outline["ledger"]:
        return {"dir": project_dir, "errors": ["章纲没解析到「埋收」列，无法比对"], "warnings": []}
    if not os.path.exists(state):
        return {"dir": project_dir, "errors": ["缺 _state.json（唯一真源不存在）"], "warnings": []}
    try:
        data = json.loads(read_text(state))
    except json.JSONDecodeError as e:
        return {"dir": project_dir, "errors": [f"_state.json 解析失败：{e}"], "warnings": []}
    items = {}
    for kind in ("promises", "clues", "questions"):
        for it in (data.get("ledger") or {}).get(kind, []):
            if it.get("id"):
                items[it["id"]] = it
    cur_ch = (data.get("progress") or {}).get("chapter", 0) or 0
    writes = []
    for ch, marks in sorted(outline["ledger"].items()):
        for tid, action in marks:
            it = items.get(tid)
            if not it:
                # 章纲已规划、正文还没写到，账本没登记属正常
                if ch <= cur_ch:
                    writes.append(("error", f"章纲第 {ch} 章标 {tid}{action}，账本里没有这个编号"))
                continue
            if action == "埋":
                got = it.get("chapter")
            else:
                got = it.get("paid_at") or it.get("payoff")
            if got != ch:
                lvl = "warning" if ch > cur_ch else "error"
                writes.append((lvl, f"{tid}：章纲标「第 {ch} 章{'埋' if action == '埋' else '收'}」，"
                                    f"账本记 {'chapter' if action == '埋' else 'paid_at/payoff'}={got}"))
    for lvl, msg in writes:
        (errs if lvl == "error" else warns).append(msg)
    return {"dir": project_dir, "errors": errs, "warnings": warns}


# ---------------------------------------------------------------- 单文件体检


def check_file(path, do_ai=True, words_range=None, names_info=None):
    text = read_text(path)
    report = {"file": os.path.basename(path), "path": path,
              "blocking": 0, "advisory": 0, "notes": []}

    # 字数
    net = len(re.sub(r"\s", "", text))
    cn = len(re.findall(r"[\u4e00-\u9fff]", text))
    paras = paragraphs(text)
    sents = sentences(text)
    qcn = sum(len(re.findall(r"[\u4e00-\u9fff]", m)) for m in re.findall(r"“[^”]*”", text))
    dlg = (qcn / cn) if cn else 0
    report["metrics"] = {
        "净字数": net,
        "中文字符": cn,
        "段落数": len(paras),
        "句数": len(sents),
        "平均句长": round(sum(len(s) for s in sents) / len(sents), 1) if sents else 0,
        "最长段字数": max((len(p) for p in paras), default=0),
        "对话占比": f"{dlg:.0%}",
        "均段字数": round(cn / len(paras), 1) if paras else 0,
    }

    notes = report["notes"]

    # 长度
    if net and net < 1500 and net > 0:
        notes.append(("info", f"净字数 {net}，低于常见单章底线 2000（平台规则按当期核实）"))
    if net > 4500:
        notes.append(("info", f"净字数 {net}，高于 4000，移动端易被划走"))
    if len(paras) > 3 and report["metrics"]["最长段字数"] > 320:
        notes.append(("advisory", f"存在 {report['metrics']['最长段字数']} 字的长段，检查是否该按镜头断段"))

    # 章纲字数区间（±10% 提示，±20% 阻断）
    if words_range:
        lo, hi = words_range
        mid = (lo + hi) / 2
        dev = (net - mid) / mid if mid else 0
        msg = f"净字数 {net}，章纲区间 {lo}-{hi}（{dev:+.0%}）"
        if dev >= 0.20 or dev <= -0.20:
            notes.append(("blocking", msg + "，超出 ±20%，必须回到区间再交"))
            report["blocking"] += 1
        elif dev >= 0.10 or dev <= -0.10:
            notes.append(("advisory", msg + "，超出 ±10%，按 07 的疏密复核"))
            report["advisory"] += 1
        else:
            notes.append(("info", msg + "，在区间内"))

    # 需记人名密度（平庸清单第 11 条：一章超过 3 个新名字就开始累）
    if names_info:
        pres, new = names_info["present"], names_info["new"]
        if len(pres) > 5:
            notes.append(("advisory", f"本章需记人名 {len(pres)} 个（{'、'.join(pres)}），超过 5 个"))
            report["advisory"] += 1
        if len(new) > 2:
            notes.append(("advisory", f"本章新增需记人名 {len(new)} 个（{'、'.join(new)}），超过 2 个"))
            report["advisory"] += 1
        elif new:
            notes.append(("info", f"本章新增人名：{'、'.join(new)}"))

    # 对话占比（对标实测 37%；长篇靠对话推进更抗疲劳，纯旁白推进易闷）
    if cn >= 1200:
        if dlg < 0.18:
            notes.append(("advisory", f"对话占比 {dlg:.0%}，低于对标常见 30-37%，推进可能压在一次旁白上"))
            report["advisory"] += 1
        elif dlg < 0.25:
            notes.append(("info", f"对话占比 {dlg:.0%}，偏旁白型（对标 37%）"))
        else:
            notes.append(("info", f"对话占比 {dlg:.0%}，接近对标区"))

    # 句长 + 对话双低＝碎句流（对标均句 17 字）
    avg_sent = report["metrics"]["平均句长"]
    if cn >= 1200 and avg_sent and avg_sent < 12 and dlg < 0.25:
        notes.append(("advisory", f"平均句长 {avg_sent} 字且对话占比 {dlg:.0%}，旁白偏碎，检查是否该并句"))
        report["advisory"] += 1

    # 连续空行（改稿常带出的脏格式；正常段间只有一个空行）
    if re.search(r"\n[ \t\u3000]*\n[ \t\u3000]*\n", text):
        notes.append(("advisory", "存在连续空行，疑似改稿残留"))
        report["advisory"] += 1

    # 连续短碎句（电报体）：只看旁白。逐字短对白（“问。”“柳巧云。”）是合法口语，不计入。
    short_run, worst = 0, 0
    for s in sentences(strip_quotes(text)):
        if len(re.sub(r"[^\u4e00-\u9fff]", "", s)) <= 6:
            short_run += 1
            worst = max(worst, short_run)
        else:
            short_run = 0
    if worst >= 5:
        notes.append(("blocking", f"连续 {worst} 句 ≤6 字的碎句，疑似电报体"))
        report["blocking"] += 1

    # 占位符 / 截断
    ph = count_hits(text, PLACEHOLDER)
    if ph:
        notes.append(("blocking", f"占位符/工程词 {len(ph)} 处：{ph[0][0]}"))
        report["blocking"] += 1

    # 重复句（逐字复读）
    seen, dup = {}, []
    for s in sents:
        k = re.sub(r"\s", "", s)
        if len(k) >= 8:
            if k in seen:
                dup.append(s[:20])
            seen[k] = 1
    if dup:
        notes.append(("blocking", f"逐字重复句 {len(dup)} 处：{dup[0]}"))
        report["blocking"] += 1

    # 长 n-gram 重复（打转）
    grams = ngrams(text, 8)
    if grams:
        from collections import Counter
        c = Counter(grams)
        top, n = c.most_common(1)[0]
        if n >= 6:
            notes.append(("advisory", f"8 字片段重复 {n} 次：{top}"))

    # 标点
    narr = strip_quotes(text)
    dash = len(re.findall(r"——|—|--", narr))
    if dash:
        notes.append(("advisory", f"叙述段出现破折号 {dash} 处（应只出现在对话内）"))
    if re.search(r"！！|!!!|!！", text):
        notes.append(("advisory", "出现连续感叹号"))
    half = len(re.findall(r"[a-zA-Z0-9]?[,;:?!]\s?[\u4e00-\u9fff]", text))
    if half > 5:
        notes.append(("advisory", f"疑似半角标点 {half} 处"))
    ell = narr.count("……")
    if net > 1000 and ell / (net / 1000) > 3:
        notes.append(("advisory", f"旁白省略号 {ell} 处，密度偏高"))

    # AI 词
    if do_ai:
        b = count_hits(text, BLOCKING)
        a = count_hits(text, ADVISORY)
        if b:
            report["blocking"] += len(b)
            for w, ctx in b[:6]:
                notes.append(("blocking", f"强信号「{w}」：…{ctx}…"))
        if len(a) >= 8:
            report["advisory"] += len(a)
            kinds = sorted({w for w, _ in a})
            notes.append(("advisory", f"弱信号 {len(a)} 处（{len(kinds)} 种）：{'、'.join(kinds[:10])}"))
        elif a:
            report["advisory"] += len(a)
            kinds = sorted({w for w, _ in a})
            notes.append(("info", f"弱信号 {len(a)} 处：{'、'.join(kinds[:8])}（单次不作判据）"))

        if "了一下" in text or "了下" in text:
            cnt = len(re.findall(r"了下", text))
            if net and cnt / max(1, net / 1000) > 4:
                notes.append(("advisory", f"「了下」{cnt} 处，动作套式密度偏高"))

    return report


# ---------------------------------------------------------------- 状态 / 账本


def check_state(path):
    errs = []
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as e:
        return {"file": path, "errors": [f"JSON 解析失败：{e}"], "warnings": []}
    need_top = ["book", "progress", "structure", "characters", "ledger", "next"]
    for k in need_top:
        if k not in data:
            errs.append(f"缺顶层字段：{k}")
    prog = data.get("progress", {})
    for k in ("chapter", "volume"):
        if k not in prog:
            errs.append(f"progress 缺字段：{k}")
    for name, c in (data.get("characters") or {}).items():
        for k in ("目标",):
            if k not in c:
                errs.append(f"人物「{name}」缺字段：{k}")
    led = data.get("ledger", {})
    for k in ("promises", "clues", "questions"):
        if k not in led:
            errs.append(f"ledger 缺账本：{k}")
        else:
            for item in led[k]:
                st = item.get("status")
                if st == "planted" and not item.get("payoff") and item.get("chapter", 0):
                    gaps = prog.get("chapter", 0) - item.get("chapter", 0)
                    if gaps > 20:
                        errs.append(f"伏笔 {item.get('id','?')} 埋了 {gaps} 章未收")
                if st == "paid-off" and not item.get("payoff"):
                    errs.append(f"伏笔 {item.get('id','?')} 标为已收但缺 payoff 章号")
    return {"file": path, "errors": errs, "warnings": []}


def check_consistency(dirpath):
    errs, warns = [], []
    chapters = set()
    for fn in os.listdir(dirpath):
        m = re.match(r"第(\d+)章", fn)
        if m:
            chapters.add(int(m.group(1)))
    if chapters:
        mx = max(chapters)
        missing = [i for i in range(1, mx + 1) if i not in chapters]
        if missing:
            errs.append(f"章节缺号：{missing[:12]}{'…' if len(missing) > 12 else ''}")
    # 账本
    for name in ("promises.md", "clues.md", "questions.md"):
        p = os.path.join(dirpath, name)
        if not os.path.exists(p):
            warns.append(f"缺账本文件：{name}")
            continue
        txt = read_text(p)
        for line in txt.split("\n"):
            if line.startswith("|") and ("planted" in line or "open" in line):
                if "paid-off" not in line and "answered" not in line:
                    warns.append(f"{name} 未结条目：{line.strip()[:60]}")
    if not os.path.exists(os.path.join(dirpath, "_state.json")):
        errs.append("缺 _state.json（唯一真源不存在）")
    return {"dir": dirpath, "errors": errs, "warnings": warns}


# ---------------------------------------------------------------- 输出


def print_report(report):
    print(f"\n=== {report.get('file', report.get('dir', ''))} ===")
    m = report.get("metrics")
    if m:
        print(f"净字数 {m['净字数']}｜中文 {m['中文字符']}｜段落 {m['段落数']}｜句 {m['句数']}"
              f"｜平均句长 {m['平均句长']}｜最长段 {m['最长段字数']}"
              f"｜对话占比 {m.get('对话占比', '—')}｜均段 {m.get('均段字数', '—')}")
    for lvl, msg in report.get("notes", []):
        tag = {"blocking": "[阻断]", "advisory": "[提示]", "info": "[信息]"}[lvl]
        print(f"  {tag} {msg}")
    for e in report.get("errors", []):
        print(f"  [错误] {e}")
    for w in report.get("warnings", []):
        print(f"  [警告] {w}")
    if not report.get("notes") and not report.get("errors") and not report.get("warnings"):
        print("  未发现命中项（零命中不等于合格，仍需人工三层扫描）")
    print(f"  汇总：blocking={report.get('blocking', 0)} advisory={report.get('advisory', 0)}")


def main():
    ap = argparse.ArgumentParser(description="小说稿件/账本机检")
    ap.add_argument("path", nargs="?", help="正文文件或正文目录")
    ap.add_argument("--ai", action="store_true", help="启用 AI 味词表扫描（默认启用）")
    ap.add_argument("--no-ai", action="store_true", help="关闭 AI 味词表扫描")
    ap.add_argument("--chapter", type=int, help="章号（默认按文件名 第0002章 识别）")
    ap.add_argument("--outline", help="章纲路径（默认自动找 <项目>/大纲/章纲.md）")
    ap.add_argument("--state", help="校验 _state.json")
    ap.add_argument("--consistency", help="校验追踪目录（章节缺号/账本）")
    ap.add_argument("--ledger", help="章纲「埋收」列 × 账本章号 对齐（传项目目录或 追踪/）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()

    reports = []
    if args.state:
        reports.append(check_state(args.state))
    elif args.consistency:
        reports.append(check_consistency(args.consistency))
    elif args.ledger:
        reports.append(check_ledger(project_root_of(args.ledger), args.outline))
    elif args.path:
        p = args.path
        root = project_root_of(p)
        outline = load_outline(args.outline or find_outline(root))
        if os.path.isdir(p):
            for fn in sorted(os.listdir(p)):
                if fn.lower().endswith((".md", ".txt")) and not fn.startswith("_"):
                    fp = os.path.join(p, fn)
                    ch = args.chapter or guess_chapter(fp)
                    reports.append(check_file(
                        fp, do_ai=not args.no_ai,
                        words_range=outline["ranges"].get(ch),
                        names_info=check_names(fp, ch, root),
                    ))
        elif os.path.isfile(p):
            ch = args.chapter or guess_chapter(p)
            reports.append(check_file(
                p, do_ai=not args.no_ai,
                words_range=outline["ranges"].get(ch),
                names_info=check_names(p, ch, root),
            ))
        else:
            print(f"路径不存在：{p}")
            return 2
    else:
        ap.print_help()
        return 2

    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        for r in reports:
            print_report(r)

    blocked = sum(r.get("blocking", 0) for r in reports)
    errored = sum(len(r.get("errors", [])) for r in reports)
    return 1 if (blocked or errored) else 0


if __name__ == "__main__":
    sys.exit(main())
