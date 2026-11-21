#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""novel_check.py — 小说稿件机检（无第三方依赖）

三种用法：
  1) 稿件体检：python novel_check.py 正文.md  [--ai] [--json]
  2) 目录体检：python novel_check.py 正文/     [--ai] [--json]
  3) 账本/状态：python novel_check.py --state 追踪/_state.json
                python novel_check.py --consistency 追踪/

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


# ---------------------------------------------------------------- 单文件体检


def check_file(path, do_ai=True):
    text = read_text(path)
    report = {"file": os.path.basename(path), "path": path,
              "blocking": 0, "advisory": 0, "notes": []}

    # 字数
    net = len(re.sub(r"\s", "", text))
    cn = len(re.findall(r"[\u4e00-\u9fff]", text))
    paras = paragraphs(text)
    sents = sentences(text)
    report["metrics"] = {
        "净字数": net,
        "中文字符": cn,
        "段落数": len(paras),
        "句数": len(sents),
        "平均句长": round(sum(len(s) for s in sents) / len(sents), 1) if sents else 0,
        "最长段字数": max((len(p) for p in paras), default=0),
    }

    notes = report["notes"]

    # 长度
    if net and net < 1500 and net > 0:
        notes.append(("info", f"净字数 {net}，低于常见单章底线 2000（平台规则按当期核实）"))
    if net > 4500:
        notes.append(("info", f"净字数 {net}，高于 4000，移动端易被划走"))
    if len(paras) > 3 and report["metrics"]["最长段字数"] > 320:
        notes.append(("advisory", f"存在 {report['metrics']['最长段字数']} 字的长段，检查是否该按镜头断段"))

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
        print("净字数 {净字数}｜中文 {中文字符}｜段落 {段落数}｜句 {句数}｜平均句长 {平均句长}｜最长段 {最长段字数}".format(**m))
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
    ap.add_argument("--state", help="校验 _state.json")
    ap.add_argument("--consistency", help="校验追踪目录（章节缺号/账本）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()

    reports = []
    if args.state:
        reports.append(check_state(args.state))
    elif args.consistency:
        reports.append(check_consistency(args.consistency))
    elif args.path:
        p = args.path
        if os.path.isdir(p):
            for fn in sorted(os.listdir(p)):
                if fn.lower().endswith((".md", ".txt")):
                    reports.append(check_file(os.path.join(p, fn), do_ai=not args.no_ai))
        elif os.path.isfile(p):
            reports.append(check_file(p, do_ai=not args.no_ai))
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
