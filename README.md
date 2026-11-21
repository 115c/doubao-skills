# doubao-skills

三套自用 Skill，用于豆包 / 兼容 Claude Skill 目录结构的 Agent 运行时。直接放进技能目录即可被识别（每个目录的 `SKILL.md` 是唯一入口）。

| 目录 | 定位 | 文件数 | 什么时候用 |
| --- | --- | --- | --- |
| `novel-writing-master/` | 写小说全流程总控（别名「写小说技能大全」） | 26 | 选题、世界观、人物、卷纲章纲、开篇、单章、钩子、对白、情绪、去 AI 味、一致性、审稿评分、题材、平台运营、短篇、跨媒介、机检脚本 |
| `manju-director/` | 漫剧总控（画布 + 电影级提示词 + 短剧助手 + 剧本工作室四套能力合并） | 116 | 从小说到分镜、到画布节点、到成片；提示词写法、镜头语言、批量生产、剪辑交付 |
| `six-gate-review/` | 六机制决策审查 | 5 | 任何有副作用或不可逆后果的动作之前，按「目标/条件/退路/影响/依据/收尾」六问过一遍 |

## 用法

```
<skills-root>/
  novel-writing-master/
  manju-director/
  six-gate-review/
```

- 每个技能都是自包含的：`SKILL.md` 给路由与硬规则，细节在同目录 `references/`，可执行部分在 `scripts/`。
- `novel-writing-master/scripts/` 三个脚本只依赖 Python 标准库，不需要装包：

```
python scripts/tracking_init.py <小说目录> --title 书名 --genre 题材 --platform 平台
python scripts/pacing_grid.py <小说目录>/大纲/章纲.md
python scripts/novel_check.py <小说目录>/正文/第0001章_xxx.md
```

- `manju-director/` 里的路径写法按各自的 `SKILL.md` 走，里面若提到画布工具、导演台，需要对应的工具环境；没有该环境时仍可只当提示词手册用。

## 边界

- `novel-writing-master` 负责「把小说写出来」，`manju-director` 负责「把小说变成画面」。两者在结构与节奏上有重叠，裁决规则写在各自 `SKILL.md` 的冲突裁决一节。
- `six-gate-review` 是前置闸门，不产出内容，只拦不该动手的动作。

## 来源与许可

见 `NOTICE.md`。三套技能里既有原创部分，也有从公开仓库提炼的方法论和合并进来的第三方技能内容，公开使用前请先看 NOTICE 里的许可状态标注。
