#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tracking_init.py — 一键建小说项目骨架（目录 + 唯一真源 + 派生文件 + 模板）

用法：
  python tracking_init.py "D:\\小说\\我的书" --title 我的书 --genre 都市复仇 --platform 番茄 --target 1200000
  python tracking_init.py ./新书 --short          # 短篇三件套
  python tracking_init.py ./新书 --force          # 目录已存在时仍补缺，不覆盖已有文件

输出：
  {root}/设定/ 大纲/ 正文/ 追踪/ 发布/ .work/
  追踪/_state.json（唯一真源）
  追踪/promises.md clues.md questions.md 时间线.md 上下文.md 人物快照.md
  大纲/章纲.md（含可被 pacing_grid.py 解析的表头）
不覆盖已存在文件（除非 --force 且文件为空）。
"""

import argparse
import datetime
import json
import os
import sys

STATE_TEMPLATE = {
    "book": {"title": "", "genre": "", "platform": "", "target_words": 0,
             "form": "long", "created": ""},
    "progress": {"volume": 1, "chapter": 0, "words_total": 0, "last_update": ""},
    "structure": {"model": "八步", "beats": {}},
    "characters": {"主角": {"位置": "", "伤势": "", "资源": "", "已知": [], "目标": ""}},
    "ledger": {"promises": [], "clues": [], "questions": []},
    "bans": [],
    "next": {"chapter": 1, "goal": "", "hook": ""},
}

OUTLINE_HEAD = """# 章纲

> 表头固定，字段含义见 references/05-outline.md 第十一节。
> outcome 取值：yes / yes-but / no / no-and；钩子填 13 式名称或收束型。

| 章号 | 标题 | 功能标签 | outcome | 钩子 | 埋收 | 字数 |
|---|---|---|---|---|---|---|
| 1 |  | 爆发 | yes-but | 未完成动作 | 0 | 2100-2300 |
| 2 |  | 推进 | no | 信息差 | P001 | 2100-2300 |
"""

LEDGER_HEAD = {
    "promises.md": "# 承诺账本（契诃夫之枪／誓言／预言／死线）\n\n| 编号 | 内容 | 状态 | 埋于章 | 收于章 | 关联线 |\n|---|---|---|---|---|---|\n| P001 |  | planned |  |  | 主线 |\n",
    "clues.md": "# 线索账本（推理线索／红鲱鱼）\n\n| 编号 | 内容 | 状态 | 埋于章 | 收于章 | 公平性（读者是否拿到） |\n|---|---|---|---|---|---|\n| C001 |  | planned |  |  |  |\n",
    "questions.md": "# 悬念账本（读者被留下要问的问题）\n\n| 编号 | 问题 | 状态 | 提出章 | 回答章 | 属于哪条线 |\n|---|---|---|---|---|---|\n| Q001 |  | open |  |  | 主线 |\n",
}

TIMELINE_HEAD = """# 时间线（故事时间）

> 一行一件事，按故事先后排；倒叙／插叙在"章节"列标注。

| 故事时间 | 事件 | 关联线 | 章节 |
|---|---|---|---|
|  |  | 主线 | — |
"""

CONTEXT_HEAD = """# 当前局面（派生文件，禁手改）

> 由 追踪/_state.json 生成。人工只读。

- 进度：第 {chapter} 章 / 第 {volume} 卷
- 主角目标：{goal}
- 下一章要写：{next_goal}
- 下一章钩子：{hook}
"""

SNAPSHOT_HEAD = """# 人物快照（派生文件，禁手改）

| 人物 | 位置 | 伤势 | 资源 | 已知 | 目标 |
|---|---|---|---|---|---|
"""


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def write_if_absent(path, content, force=False):
    if os.path.exists(path) and not force:
        return False
    if os.path.exists(path) and force and os.path.getsize(path) > 0:
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def main():
    ap = argparse.ArgumentParser(description="建小说项目骨架")
    ap.add_argument("root", help="项目根目录")
    ap.add_argument("--title", default="")
    ap.add_argument("--genre", default="")
    ap.add_argument("--platform", default="")
    ap.add_argument("--target", type=int, default=0)
    ap.add_argument("--short", action="store_true", help="短篇三件套模式")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    today = datetime.date.today().isoformat()

    if args.short:
        ensure_dir(root)
        write_if_absent(os.path.join(root, "设定.md"), "# 设定\n\n- 主角：\n- 缺口：\n- 主导变化：从 __ 到 __\n- 单一效果：\n- 篇幅：\n", args.force)
        write_if_absent(os.path.join(root, "小节大纲.md"), "# 小节大纲\n\n| 段 | 占比 | 任务 | 内容 |\n|---|---|---|---|\n| 钩 | 10% |  |  |\n| 立 | 20% |  |  |\n| 转 | 35% |  |  |\n| 顶 | 20% |  |  |\n| 收 | 15% |  |  |\n", args.force)
        write_if_absent(os.path.join(root, "正文.md"), "# 正文\n\n", args.force)
        print(f"已建短篇骨架：{root}")
        return 0

    for d in ("设定", "大纲", "正文", "追踪", "发布", ".work", ".work/原稿", ".work/去味原稿"):
        ensure_dir(os.path.join(root, d))

    state = json.loads(json.dumps(STATE_TEMPLATE))
    state["book"]["title"] = args.title
    state["book"]["genre"] = args.genre
    state["book"]["platform"] = args.platform
    state["book"]["target_words"] = args.target
    state["book"]["created"] = today
    state["progress"]["last_update"] = today

    state_path = os.path.join(root, "追踪", "_state.json")
    if not os.path.exists(state_path) or args.force:
        if not os.path.exists(state_path) or os.path.getsize(state_path) == 0:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

    for fn, head in LEDGER_HEAD.items():
        write_if_absent(os.path.join(root, "追踪", fn), head, args.force)
    write_if_absent(os.path.join(root, "追踪", "时间线.md"), TIMELINE_HEAD, args.force)

    write_if_absent(os.path.join(root, "追踪", "上下文.md"),
                    CONTEXT_HEAD.format(chapter=0, volume=1, goal="", next_goal="", hook=""), args.force)
    write_if_absent(os.path.join(root, "追踪", "人物快照.md"), SNAPSHOT_HEAD, args.force)

    write_if_absent(os.path.join(root, "大纲", "章纲.md"), OUTLINE_HEAD, args.force)

    print(f"已建项目骨架：{root}")
    print("  设定/ 大纲/ 正文/ 追踪/ 发布/ .work/")
    print("  唯一真源：追踪/_state.json")
    print("下一步：填 设定/题材定位.md → 大纲/全书结构.md → 大纲/章纲.md，再跑 pacing_grid.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
