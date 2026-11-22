#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill_audit.py — 逐章体检器（技能 1.3.0）

做一件事：把硬规则里"能判定"的部分变成可复跑的检查，产出一份机器可读的
状态文件（默认 <项目>/追踪/_check.json），由主控读取，而不是靠人回忆。

用法：
    python skill_audit.py <项目根>                 # 体检并写状态文件
    python skill_audit.py <项目根> --quiet         # 只写文件，不打印
    python skill_audit.py <项目根> --json          # 只打印 JSON

判定口径见 references/20-tools.md 第十四节。
"""
import json
import os
import re
import statistics
import sys

# 13 式 + 5 模板 + 3 速写（08 钩子的合法取值）
HOOKS = [
    "突然揭示", "紧急危机", "未完成动作", "身份反转", "两难抉择", "神秘物品",
    "倒计时", "承诺威胁", "承诺／威胁", "离奇消失", "隐藏含义", "意象钩子",
    "回声钩子", "留白钩子", "留白",
    "系统激活", "选择型", "情感转折", "信息差型", "时间跳跃", "时间跳跃型",
    "收获预告", "反派逼近", "行动预告", "收束型",
]
OUTCOMES = ["yes", "yes-but", "no", "no-and"]


def cn(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def net_chars(text):
    body = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        body.append(s)
    return len(re.sub(r"\s", "", "".join(body)))


def split_paras(text):
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


def last_sentence(paras):
    if not paras:
        return "", "空章"
    s = paras[-1]
    if s[:1] in "“\"「『":
        return s, "台词"
    if s.endswith(("？", "?")):
        return s, "疑问"
    if s.endswith("……") or s.endswith("..."):
        return s, "省略"
    return s, "叙述／动作"


def first_open(paras):
    if not paras:
        return "", "空章"
    s = paras[0]
    if s[:1] in "“\"「『":
        return s, "对话开场"
    if re.match(r"^(今天|当天|次日|第二天|第三天|半个月后|三天后|那年|六年前|三十年前|冬月|清晨|早上|上午|中午|下午|傍晚|天黑|夜里|半夜|凌晨)", s):
        return s, "时间开场"
    if re.search(r"(风|雨|雪|太阳|天色|天气|雾)", s[:20]):
        return s, "天气／环境开场"
    return s, "动作／物件开场"


def parse_outline(path):
    rows = {}
    if not os.path.exists(path):
        return rows
    for line in open(path, encoding="utf-8"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7 or not cells[0].isdigit():
            continue
        num = int(cells[0])
        rng = re.findall(r"\d+", cells[6])
        lo, hi = (int(rng[0]), int(rng[1])) if len(rng) >= 2 else (0, 0)
        ids = re.findall(r"[PCQ]\d{3}", cells[5])
        buried = len(re.findall(r"[PCQ]\d{3}埋|[PCQ]\d{3}（埋", cells[5]))
        if buried == 0:
            buried = len(ids)
        rows[num] = {
            "title": cells[1], "func": cells[2], "outcome": cells[3],
            "hook": cells[4], "marks": cells[5], "lo": lo, "hi": hi,
            "buried": buried, "ids": ids,
        }
    return rows


def audit(root):
    outline = os.path.join(root, "大纲", "章纲.md")
    body_dir = os.path.join(root, "正文")
    state_path = os.path.join(root, "追踪", "_state.json")
    annot_path = os.path.join(root, "追踪", "_annot.json")

    rows = parse_outline(outline)
    annot = {}
    if os.path.exists(annot_path):
        try:
            annot = json.load(open(annot_path, encoding="utf-8"))
        except Exception:
            annot = {}
    state = {}
    if os.path.exists(state_path):
        state = json.load(open(state_path, encoding="utf-8"))

    chapters = []
    for fn in sorted(os.listdir(body_dir)):
        m = re.match(r"第0*(\d+)章_([^.]*)\.md$", fn)
        if not m:
            continue
        num = int(m.group(1))
        text = open(os.path.join(body_dir, fn), encoding="utf-8").read()
        paras = split_paras(text)
        net = net_chars(text)
        dlg = sum(cn(p) for p in paras if p[:1] in "“\"「『")
        han = cn(text)
        sents = [x for x in re.split(r"[。！？…]+", text) if cn(x) > 1]
        row = rows.get(num, {})
        lo, hi = row.get("lo", 0), row.get("hi", 0)
        dev = None
        if lo and hi:
            mid = (lo + hi) / 2
            dev = round(100 * (net - mid) / mid)
        hook = row.get("hook", "（章纲缺）")
        hook_ok = any(h in hook for h in HOOKS)
        a = annot.get(str(num), {})
        chapters.append({
            "chapter": num, "file": fn, "title": m.group(2),
            "net": net, "hanzi": han,
            "range": [lo, hi], "dev_pct": dev,
            "dialogue_pct": round(100 * dlg / net) if net else 0,
            "avg_sent": round(statistics.mean([cn(x) for x in sents]), 1) if sents else 0,
            "avg_para": round(statistics.mean([cn(p) for p in paras]), 1) if paras else 0,
            "last_type": last_sentence(paras)[1],
            "last_line": last_sentence(paras)[0][-40:],
            "open_type": first_open(paras)[1],
            "outcome": row.get("outcome", "?"),
            "func": row.get("func", "?"),
            "outcome_valid": row.get("outcome") in OUTCOMES,
            "hook": hook, "hook_valid": hook_ok,
            "buried_ids": row.get("buried", 0),
            "info_count": a.get("info", row.get("buried", 0)),
            "rule_kit": a.get("rule_kit", "未标注"),
            "horror_proof": a.get("horror_proof", "未标注"),
            "payoff": a.get("payoff", "未标注"),
            "note": a.get("note", ""),
        })

    # 全局判定
    blocking, warn = [], []

    def think(msg):
        warn.append(msg)

    for c in chapters:
        if c["range"][0]:
            if abs(c["dev_pct"]) > 20:
                blocking.append(f"第{c['chapter']}章 净字 {c['net']} 偏离区间 {abs(c['dev_pct'])}% > 20%")
            elif abs(c["dev_pct"]) > 10:
                think(f"第{c['chapter']}章 净字偏离 {c['dev_pct']}%，超 ±10%")
        if not c["hook_valid"]:
            blocking.append(f"第{c['chapter']}章 章纲钩子「{c['hook']}」不在 13 式／5 模板／3 速写内")
        if not c["outcome_valid"]:
            blocking.append(f"第{c['chapter']}章 outcome「{c['outcome']}」非法")
        if c["info_count"] > 5:
            blocking.append(f"第{c['chapter']}章 情报 {c['info_count']} 件 > 5（并章章需在 _annot.json 写 waiver）")
        elif c["info_count"] > 3:
            think(f"第{c['chapter']}章 情报 {c['info_count']} 件 > 3")
        if c["rule_kit"] == "未标注" and c["func"] in ("修炼", "推进", "爆发"):
            think(f"第{c['chapter']}章 规则三件套未标注（看 _annot.json）")
        if c["horror_proof"] == "未标注" and c["func"] in ("爆发", "感情", "推进"):
            think(f"第{c['chapter']}章 恐怖实证未标注")

    seq = [c for c in chapters]
    for i in range(2, len(seq)):
        a, b, c3 = seq[i - 2], seq[i - 1], seq[i]
        if a["hook"] == b["hook"] == c3["hook"]:
            blocking.append(f"第{c3['chapter']}章 钩子「{c3['hook']}」连续 3 章同型")
        outs = [x["outcome"] for x in (a, b, c3)]
        if all(o == "yes" for o in outs):
            blocking.append(f"第{c3['chapter']}章 连续 3 章 outcome=yes，无压力")
        if not any(o in ("yes", "yes-but") for o in outs):
            think(f"第{c3['chapter']}章 起连续 3 章没有兑现点（主角没做成一件事）")

    # 前三章连挫（平台留存公式：第二章要给微小反击，三章内不得两次挫败）
    front = [c for c in chapters if c["chapter"] <= 3]
    bad = [c["chapter"] for c in front if c["outcome"] in ("no", "no-and")]
    if len(bad) >= 2:
        blocking.append("前三章挫败 %d 次（第 %s 章），违反硬规则 26：三章内不得两次 no／no-and"
                        % (len(bad), "、".join(str(x) for x in bad)))

    # 规则登记表
    rule_tab = os.path.join(root, "追踪", "规则表.md")
    rules_registered = 0
    if os.path.exists(rule_tab):
        for line in open(rule_tab, encoding="utf-8"):
            if line.startswith("| R"):
                rules_registered += 1
    else:
        think("缺 追踪/规则表.md：规则只写在设定里，写到中期会自相矛盾（硬规则 27）")

    # 账本未结
    ledger = state.get("ledger", {})
    unclosed = {
        "promises": [p["id"] for p in ledger.get("promises", []) if p.get("status") not in ("paid", "paid_off")],
        "clues": [c["id"] for c in ledger.get("clues", []) if c.get("status") not in ("paid", "paid_off")],
        "questions": [q["id"] for q in ledger.get("questions", []) if q.get("status") not in ("answered", "paid")],
    }

    result = {
        "generated_for": root,
        "chapters": chapters,
        "summary": {
            "chapters": len(chapters),
            "net_total": sum(c["net"] for c in chapters),
            "blocking": blocking,
            "warnings": warn,
            "unclosed": {k: len(v) for k, v in unclosed.items()},
            "unclosed_ids": unclosed,
            "rules_registered": rules_registered,
            "verdict": "FAIL" if blocking else ("PASS-WITH-WARN" if warn else "PASS"),
        },
    }
    return result


def main():
    root = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "."
    quiet = "--quiet" in sys.argv
    as_json = "--json" in sys.argv
    res = audit(root)
    out = os.path.join(root, "追踪", "_check.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    if quiet:
        return

    for c in res["chapters"]:
        print("第%d章 %s｜净 %d（%+d%%）｜对话 %d%%｜均句 %.1f｜章末 %s｜开场 %s｜钩子 %s｜情报 %d"
              % (c["chapter"], c["title"], c["net"], c["dev_pct"] or 0,
                 c["dialogue_pct"], c["avg_sent"], c["last_type"], c["open_type"],
                 c["hook"], c["info_count"]))
        if c["note"]:
            print("   note: " + c["note"])
    print("\n判定：%s｜blocking %d｜warn %d｜未结 %s"
          % (res["summary"]["verdict"], len(res["summary"]["blocking"]),
             len(res["summary"]["warnings"]), res["summary"]["unclosed"]))
    for b in res["summary"]["blocking"]:
        print("  [阻断] " + b)
    for w in res["summary"]["warnings"]:
        print("  [提示] " + w)
    print("状态文件：%s" % out)


if __name__ == "__main__":
    main()
