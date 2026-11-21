---
name: manju-director
description: 漫剧总控（合并技能）。把 canvas 画布操作手册、cinematic-director-zh 电影级提示词手册、djzs 短剧助手、fuyaoai-vip 剧本创作工作室四套能力合成一个入口：从小说/创意 → 剧本 → 会诊与台词 → 子镜表分镜 → 资产与音色 → 图片/视频提示词 → 画布落地与生成 → 验收复盘 → 后期声音，一站走完。用户要做漫剧/短剧、写改剧本、分镜、写图片或视频提示词、搭或改 Toonflow 画布、跑生成与验收时使用。用户只问单点（例如只想改一句台词或只连一根线）时也用本技能，按阶段只读一份参考，不全量加载。
metadata:
  displayName: 漫剧总控
  version: "1.4.0"
  author: 合并自 canvas 2.1.0 / cinematic-director-zh 2.0.0 / djzs 1.4.0 / fuyaoai-vip
  promptContract: references/genres/17-prompt-contract.md（全能模式 3+M 行 / 秒数求和 / 槽位语法 / 十条机检）
  mergedFrom:
    - canvas
    - cinematic-director-zh
    - djzs
    - fuyaoai-vip
  genreLibrary: references/genres（全量 17 模块：题材 12 族 + 画风参数锁 + 能力边界 + 参考契约 + 续写编辑转场 + 剪辑交付 + 批量生产 + 旁白字幕出海 + 首次上手；技巧层取自 Dreamina Seedance 2.5 官方指南、LearnPrompt/awesome-seedance 1070 条实测案例、liyue-aigc/seedance-2-5-video-director；工程口径对标 LocalMiniDrama 1.2.9 与 DramaClaw 2.1.3 的公开实践）
---

# 漫剧总控

**唯一入口。** 先判当前在第几步，再只读那一步对应的**一份**参考文件；不要一次全读。

四套原件完整保留在 `references/<名字>/` 下，**未改写、未删节**，内部相对链接照常可用。本文件只负责三件事：**阶段路由、冲突裁决、闸口**。

---

## 0. 先用一句话判阶段

| 用户说的话 | 阶段 | 首个要读的文件 |
|---|---|---|
| 「做一部玄幻/都市/悬疑/甜宠……漫剧」「这个题材该怎么拍」「用什么画风」「2D 还是 3D」 | ⓿ 定题材与画风 | `references/genres/00-index.md`（定位族与子类型）→ 对应题材文件 → `genres/09-style-locks.md` |
| 「能不能做 30 秒 / 多久出片 / 要几张图 / 这个时长能不能做」 | 能力边界 | `references/genres/11-capability-matrix.md` |
| 「用这张图当参考」「多个参考素材怎么给」 | 参考契约 | `references/genres/12-reference-grammar.md` |
| 「新项目第一次做」「怎么快速试一条」 | 上手 | `references/genres/15-onboarding.md` |
| 「从这本小说/这个创意做一部漫剧」「写剧本」「改剧本」「续写」 | ① 剧本 | `references/fuyao/references/01-script-creation.md` 或 `01b-script-drafting.md` |
| 「帮我看看这个剧本行不行」「这段戏有问题吗」 | ② 会诊 | `references/fuyao/references/02-script-doctor.md` |
| 「台词太假」「这句怎么说才好」 | ② 台词 | `references/fuyao/references/03-dialogue-expert.md` |
| 「分镜」「子镜表」「这场戏怎么切」「镜头怎么设计」 | ③ 分镜 | `references/djzs/references/分镜.md` + `镜头模板.md` |
| 「这个角色长什么样」「场景图」「道具图」「资产」 | ④ 资产 | `references/djzs/SKILL.md` §0 规则 2 + `references/fuyao/references/05-asset-library.md` |
| 「写图片提示词」「写视频提示词」「提示词不像电影」 | ⑤ 提示词 | `references/djzs/references/提示词.md` + **`references/genres/17-prompt-contract.md`（形状与机检，必读）**；要电影级深度转 `references/cinematic/SKILL.md` |
| 「画布」「加节点」「连线」「改提示词框」「调模型参数」 | ⑥ 画布 | `references/canvas/SKILL.md` |
| 「生成」「出图」「出片」「验收」「抽帧看看」 | ⑦ 验收 | `references/djzs/references/验收与复盘.md` |
| 「配乐」「BGM」「音效」「后期声音」 | ⑧ 后期 | `references/fuyao/references/07-post-music-sound-design.md` |
| 「接着写」「延长一下」「补前情」「把某个东西改掉」「两段接起来」「让这张漫画动起来」 | ⑨ 续作与返修 | `references/genres/10-community-banks.md` |
| 「剪一下」「加字幕」「封面」「这个平台的规格」「能不能发」 | ⑩ 剪辑交付 | `references/genres/13-editing-delivery.md` |
| 「一集做完了，做十集」「怎么排期」「怎么记进度」 | ⑪ 批量排产 | `references/genres/14-batch-production.md` |
| 「加旁白」「导出字幕文件」「翻成英文发海外」「重剪一版」 | ⑫ 旁白与出海 | `references/genres/16-narration-subtitle-global.md` |

判不出阶段就问一句，不要猜。用户跨阶段时，**先补最早缺的那一环**，不要跳。

**⓿ 是唯一允许「倒回去」的阶段**：题材/画风定错，后面分镜、提示词、生成全部白做。已经进到分镜才发现定错，回到 `genres/00-index.md` 重定位，不要在半路改，改一半比不改更乱。

---

## 1. 八阶段流水线

| 步 | 阶段 | 产出 | 闸口（不过不许进下一步） | 主参考 |
|---|---|---|---|---|
| 0 | 定题材 / 画风 | 题材族与子类型、画风参数与排除清单、主色、光色、本片唯一奇观 | 用户确认题材与画风 | `genres/00`→题材文件→`genres/09` |
| 1 | 立项 / 剧本 | 戏核、人物、分集大纲、单集剧本 | 用户确认戏核与分集 | `fuyao/01`→`fuyao/01b` |
| 2 | 会诊 / 台词 | 问题清单、优先级、逐句改写 | 用户选定改哪些 | `fuyao/02`→`fuyao/03` |
| 3 | 分镜（子镜表） | 每镜：镜号/时长/景别/焦段/机位/运镜/动作站位/光影/声音/出场对象/参考编号 | 用户确认子镜表 | `djzs/分镜.md`+`模板.md` |
| 4 | 资产与音色 | 先复用前集资产，再补本集新资产、`音色·<角色>` | 提示词确认 + 图确认 + 试听 | `djzs/SKILL.md` §0-2 + `fuyao/05` |
| 5 | 图片 / 视频提示词 | 图片：单元达标 + 体检 ≥80；视频：H3 六段式成品 | 体检 ≥80 且用户确认 | `djzs/提示词.md` + `提示词体检.md` |
| 6 | 画布落地 | 节点、连线、`{{ref N}}` 绑定、模型参数 | 端口与引用编号核对一致 | `canvas/SKILL.md` |
| 7 | 生成与验收 | 样片 → 成片、抽帧自检、返修单 | 用户确认样片 | `djzs/验收与复盘.md` |
| 8 | 后期声音 | BGM 曲线、Cue Sheet、音效方案 | 用户确认 | `fuyao/07` |

流水线只有一条，**宽度优先于深度**：先把 1–7 打通一条 15 秒样片，再批量。不要在第 1 步就把 950 章写完。

**全量覆盖自检**（哪一环缺，就在这一环停下来补，不许跳过）：

| 环 | 管它的文件 | 缺了会怎样 |
|---|---|---|
| 能不能做 | `genres/11-capability-matrix.md` | 承诺了做不到的事 |
| 拍什么 | `genres/00-index.md` + 题材文件 | 镜头都对，类型不对 |
| 长什么样 | `genres/09-style-locks.md` | 画风塌成半写实 |
| 素材怎么用 | `genres/12-reference-grammar.md` | 多参考串味、换脸 |
| 怎么写 | `genres/01-tech-core.md` | 结构错，权重全乱 |
| 写成什么形状 / 怎么验 | `genres/17-prompt-contract.md` | 秒数加不平、跳号、槽位错绑，白跑 |
| 怎么接 | `genres/10-community-banks.md` | 续写接反、拼接跳 |
| 怎么剪 | `genres/13-editing-delivery.md` | 做出来发不出去 |
| 怎么扩量 | `genres/14-batch-production.md` | 第 3 集开始乱 |
| 怎么发出去 / 怎么发海外 | `genres/16-narration-subtitle-global.md` | 字幕格式错、翻译串味、二创踩线 |
| 第一次怎么起 | `genres/15-onboarding.md` | 一上来写 60 集，全返工 |

---

## 2. 冲突裁决（四家说法不一致时按这张表）

| 冲突点 | 谁说了算 | 理由 |
|---|---|---|
| **生成模型与参数** | **当前画布实际注册的模型**，其次用户明确指定 | 画布是唯一事实源；技能里的默认值只是技能作者的机器配置 |
| **画布怎么操作** | `canvas` | 唯一一份写清工具参数、端口规则、截断与分页的文件；其余三家都只是引用它 |
| **分镜载体** | `djzs`（子镜表，禁宫格/漫画故事板） | 有用户定版记录，且与画布节点结构一一对应 |
| **提示词骨架** | 短视频交付按 `djzs`（H3 六段式 / MOSS 图片写法）；要电影级纵深时按 `cinematic`（四层结构 + 13 块） | djzs 面向短剧交付，cinematic 面向镜头语言深度；两者不冲突，是粗细两档 |
| **资产复用** | `djzs`（前集资产一律引用，不重新生成） | 防重复生成，直接对应 Toonflow 的 `remote-imageNode` 引用节点 |
| **剧本结构 / 平台节奏** | `fuyao`（节奏档位四档 + 交接模板） | djzs 只给短剧节奏要点，fuyao 有完整档位判定与继承机制 |
| **视频模型适配** | 目标模型是 Seedance 系列 → `fuyao/06`；是 H3 / 通用多参 → `djzs/提示词.md` | 两家各有一套官方字段，按实际模型选，不混用 |
| **参数写不写进正文** | `cinematic` + `djzs` 一致：**不写** | 时长、画幅、分辨率是 UI 的事，写进正文会和真实参数打架 |
| **提示词里能不能写「同上」** | 不能 | 模型无记忆，每镜从零重写 |
| **题材规格与画风参数** | `genres` | 十二题材族的戏核/视觉锚点/镜头语法，加上六种画风的**参数级**写法与排除清单，是本库唯一成体系的；其余四家只讲通用镜头，不分题材 |
| **通用提示词结构** | `genres/01-tech-core.md` | 五块结构 + 时间轴分法 + 身份锁 + 自检 8 条，是四家共性与实测案例的交集，冲突最少 |
| **单条时长上限** | 画布实测（15s） | 仓库案例有 30/60/80 秒，那是网页版能力；本画布节点 15s，超过就拆条拼接 |
| **多格分镜图能不能用** | 只能当输入，不能当交付载体 | 硬规则 9 不变：分镜交付物只有子镜表；多格图只是中间参考素材 |
| **续写是往前往后** | 歧义必须先问，不许猜 | 猜错等于把片子接错方向，整条返工 |

**参数以画布为准的具体做法**：动手前先 `node:getConfig` 读一次真实配置，拿到的 `providerId / modelId / size / ratio` 才是真的，技能文档里的默认值一律当历史配置看。

---

## 3. 合并后的硬规则（四家共同红线，违反即返工）

1. **素材真实性**：提示词里写的 `{{ref N}}` / 参考编号，必须在画布上真实存在且顺序对得上；编造引用算返工。
2. **先复用再新建**：本集要的人物、场景、道具、音色，先查前集有没有，有就引用，没有才新建。
3. **一次只推进一个已确认阶段**：不因用户说「做一部短片」就一次创建全部分镜与生成节点；提问失败、跳过、沉默都不等于确认。
4. **样片闸口**：先拿信息最全的 1 镜跑通「分镜 → 提示词 → 资产 → 生成 → 验收」，模板冻结后再批量。
5. **自检要自己动手**：出片后自己抽首/中/尾帧看，如实报告；没跑、没看图就明说，不要拿「应该没问题」交差。
6. **质量闸**：交稿前跑 `references/djzs/tools/prompt_lint.py`（视频 `--duration N`；图片 `--kind image`），**≥80 分才交**。
7. **长任务不判失败**：视频渲染十几分钟到半小时正常，任务还在、供应商没报错就继续等；只有明确报错才算失败。
8. **复盘落库**：每次返工记进项目 `.agent/复盘.md`，写「现象 → 根因 → 可执行规则」，下次开工先读。
9. **不做宫格 / 漫画故事板**：分镜载体只有子镜表。
10. **无书写载体强制**：画面出现纸张、单据、账簿、匾额、招帖、对联、木牌 → 模型必写错字；要么禁载体，要么拍背面/剪影/手部特写。
11. **一条片只给一个奇观**：15 秒塞两个爆点，两个都是半成品。其余镜头全是走位铺垫。
12. **画风必须写成参数 + 排除清单**：只写 `anime style` / `3D 卡通` 算违规，必须按 `genres/09-style-locks.md` 写成可量测规格，并逐项列出要排掉的相邻画风。2D 词表与 3D 词表**禁止混写**。
13. **身份锁必须带不继承清单**：继承清单写清了但没写「不继承什么」（背景、原姿势、原光线、原文字），参考图会把背景和姿势一起搬进成片。
14. **续写、编辑、衔接一律写状态锁**：续写写清「接在哪一帧、那帧是什么状态」；编辑写全保护清单（身份/服装/动作/背景/机位/原声）；两段衔接必须有一个盖满整屏的过桥物。少任何一项，接缝就会跳。
15. **任何承诺先过能力边界**：时长、张数、分辨率、能不能做，一律以 `genres/11-capability-matrix.md` 与 `node:getConfig` 实测为准。禁止说"提示词能突破限制""一条 30 秒没问题""百分百不换脸"。
16. **一个素材只管一件事**：每张图/每条视频/每段音频都要写清「借什么、作用在谁身上、哪段时间、保护什么、不继承什么」，五栏缺一就是空话（`genres/12-reference-grammar.md` §1–§2）。
17. **字幕是文件，不是画面**：交付必须带 UTF-8 SRT（时间码、单行 ≤14 字、无重叠），绝不烧字进画面；出海版按目标语言重排时间码，并换掉含中文歌词的 BGM（`genres/16` §2–§3）。
18. **二创只改叙事，不做技术去重**：以规避平台原创识别为目的的搬运、抽帧、镜像、变速、滤镜去重一律拒绝，不给方法（`genres/16` §4）。
19. **提示词必须落在契约形状上**：全能模式按 `genres/17-prompt-contract.md` 的 `3+M` 行写，`ΣTk` 必须等于总时长、序号连续、槽位只用 `@图片N`；形状不合不许提交生成。无参考图时按 `17` §7 停下来补图，不许硬跑。

---

## 4. 当前项目已实测的画布事实（示例，换项目重新测）

判参数前先 `getCanvas` / `node:getConfig` 重测，下表只作参照：

| 类型 | 实测配置 |
|---|---|
| 图片生成节点 | `toonflow / doubao-seedream-5.0-Lite`，`2K`，`16:9` |
| 视频成片节点 | `toonflow / Seedance 2.5`，`15s`，`720p`，`16:9` |
| 文本投喂节点 | 输出走 `data.outputs.text.value`，全文落 `assets/<nodeId>/content.md` |
| 素材位节点 | `remote-imageNode`，空位 `outputs` 为 `{}`，靠生成节点灌入 |

---

## 5. 阶段交接模板（每阶段收尾都发这一段）

```text
【阶段交接】
当前阶段：
题材族 / 子类型：
画风（参数锁 + 排除清单已定？）：
主色 / 辅助色 / 点缀色：
光源方向与色温：
本片唯一奇观：
已确认内容：
平台节奏档案：
当前节奏档位：
主要问题/风险：
下一步建议：
下一步需要材料：
可直接复制调用语：
```

资产阶段追加：资产库版本、已定稿 / 待补 / 高风险资产、视觉风格锁、`@图N` 映射、图片预算。
提示词阶段追加：模板档位、素材映射、Must Keep、Avoid、段末衔接状态。

---

## 6. 文件地图

> 下面树状图里的路径**相对上一级目录**；正文和表格里引用文件一律用从技能根目录起的完整路径（例如 `references/fuyao/references/02-script-doctor.md`），照树里缩进直接拼会少一层。

```
manju-director/
├── SKILL.md                          ← 本文件（只做路由、裁决、闸口）
└── references/
    ├── genres/                       ← 漫剧题材库（1.1.0 新增，技巧层取自 awesome-seedance 1070 条实测案例 + 27 套模板）
    │   ├── 00-index.md               十二题材族总图、三步定位法、跨族混搭边界
    │   ├── 01-tech-core.md           通用技术要求：五块结构、时间轴、身份锁、画风锁、打斗、对白、参数裁决、自检 8 条
    │   ├── 02-fantasy-wuxia.md       玄幻·修真·仙侠·武侠（含灵气语法库、打斗四件套）
    │   ├── 03-urban-revenge.md       都市爽剧·战神·赘婿·打脸逆袭（含俯仰机位对调法）
    │   ├── 04-romance.md             甜宠·霸总·虐恋·重生（含距离遮挡语法）
    │   ├── 05-suspense-horror.md     悬疑·灵异·民俗·规则怪谈·无限流（含恐怖四手法）
    │   ├── 06-costume-history.md     古装·宫斗·宅斗·权谋·穿越（含位份服化四级）
    │   ├── 07-scifi-apocalypse.md    科幻·末世·废土·机甲·赛博（含尺度参照法、机械三纪律）
    │   ├── 08-youth-family.md        校园·青春·萌宝·亲子·家庭（含儿童机位与比例）
    │   ├── 09-style-locks.md         六种画风的参数级写法 + 排除清单 + 特殊形态（搞笑/纯动作/MV/预告/儿童）
    │   ├── 10-community-banks.md     续写（前接/后接）、视频编辑、两段无缝衔接、10 类转场、多格图红线、动态漫、长片拼法、外部仓库坐标表
    │   ├── 11-capability-matrix.md   模式选择、图片/视频/音频输入规格与上限、稳定性建议、超限五步、「别承诺」10 条
    │   ├── 12-reference-grammar.md   资产锁表、参考契约句法、人物参考保守解释、多人群像、音色绑定、去 BGM、局部增改、透视重构、绿幕、冲突优先级
    │   ├── 13-editing-delivery.md    剪辑节奏与模板、转场纪律、字幕规范、封面、平台规格、交付清单、合规、交付问题修法
    │   ├── 14-batch-production.md    单元化、四级闸口、排产顺序、资产与分镜的依赖顺序、异步任务与失败隔离、重跑策略、单集/跨集台账、成本估算法、目录命名
    │   ├── 15-onboarding.md          30 分钟最小闭环、三条入口、每一步给什么材料、十个坑、跑通三条标准
    │   ├── 16-narration-subtitle-global.md  解说旁白写法、SRT 字幕文件规范、出海翻译与 BGM 置换、二次创作红线、交付自检
    │   └── 17-prompt-contract.md     全能模式 3+M 行契约、M 判定、槽位语法、邻镜注入、无图闸口、十条机检
    ├── canvas/                       ← 画布操作手册 2.1.0（工具层，唯一事实源）
    │   ├── SKILL.md                  工具参数、端口、分页截断、失败处理
    │   └── references/videoProduction.md   制作阶段协作 + 画布转换
    ├── cinematic/                    ← 电影级提示词手册 2.0.0（镜头深度层）
    │   ├── SKILL.md                  唯一定理、五步循环、剧情分流、16 条、骨架
    │   ├── banks/A-optics-bank.md    光学
    │   ├── banks/B-phrase-bank.md    句式
    │   ├── banks/C-negative-bank.md  负面
    │   ├── banks/D-block-orders.md   段落顺序
    │   ├── banks/E-failure-atlas.md  失败图谱
    │   ├── banks/F-model-caps.md     模型能力
    │   ├── banks/G-prompt-depth.md   写多深
    │   ├── banks/H-dialogue-safety.md 台词安全
    │   ├── banks/I-image-models.md   图片模型
    │   ├── banks/J-story-router.md   剧情分流
    │   ├── modules/01-14-*.md        14 个模块（故事/演员/空间/光学/光/运动/序列/声/组装/资产/项目/实测/表演/重抽）
    │   ├── cases/INDEX.md            37 部片案例索引
    │   └── examples/full-6shot-30s.md 30 秒 6 镜完整示例
    ├── djzs/                          ← 短剧助手 1.4.0（交付流程层）
    │   ├── SKILL.md                  硬规则 + 8 阶段 + 各阶段要点
    │   ├── references/编剧.md        戏核、结构、人物、对白、分集钩子
    │   ├── references/分镜.md        子镜表字段、镜头语法、衔接
    │   ├── references/模板.md        分镜表 / 镜头段 / 资产清单 / 交付自检
    │   ├── references/提示词.md      图片与视频提示词写法、口型、失败诊断
    │   ├── references/打斗.md        战斗设计、招式、冲击帧
    │   ├── references/镜头模板.md     六类镜头填空模板
    │   ├── references/图像模板.md     六类图片填空模板
    │   ├── references/逻辑与镜头.md    动作分解表 + 物理常识 + 镜头六要素
    │   ├── references/提示词体检.md    20 条机检 + 6 条人读 + 100 分表
    │   ├── references/验收与复盘.md    七锁、抽帧、返修单
    │   ├── references/样本库.md       正样本、空话替换、归因
    │   └── tools/prompt_lint.py      体检脚本
    └── fuyao/                        ← 剧本创作工作室（剧本与后期层）
        ├── SKILL.md                  模块路由、推荐流程、05/04/06 红线、交接
        ├── references/01-script-creation.md       项目开发
        ├── references/01b-script-drafting.md      完整剧本写作
        ├── references/02-script-doctor.md         剧本会诊
        ├── references/03-dialogue-expert.md       台词专家
        ├── references/04-ai-video-storyboard.md   AI 视频分镜
        ├── references/04b-*.md                    运镜与动作子库
        ├── references/05-*.md                     资产库六件
        ├── references/06-seedance2-adapter.md     Seedance 适配
        └── references/07-post-music-sound-design.md 后期声音
```

**读法**：进哪个阶段就读那一行指的**一个**文件。只有命中特殊分支才追加：
- 题材没定 / 定了但画法不对 → `genres/00-index.md` → 对应题材文件
- 画风塌了（2D 变 3D 脸、3D 变塑料） → `genres/09-style-locks.md`
- 提示词结构不对（分段、身份锁、负向位置） → `genres/01-tech-core.md`
- 打斗戏 → `djzs/references/打斗.md`；要生物力学/接触点/连招链 → `genres/01-tech-core.md` §5 + `genres/02-fantasy-wuxia.md` §5
- 「接着写 / 延长 / 补前情 / 后面发生什么」→ `genres/10-community-banks.md` §1（**先说清是前接还是后接**）
- 「把某个东西改掉 / 换背景 / 去掉一个人」→ `genres/10-community-banks.md` §2（编辑必带保护清单）
- 「把两段接起来」→ `genres/10-community-banks.md` §3
- 「让这张漫画/条漫动起来」→ `genres/10-community-banks.md` §6（动态漫三条推断）
- 「要 30 秒以上」→ `genres/10-community-banks.md` §8（按幕组织 + 状态链）
- 「这个能不能做 / 多少张图 / 多长」→ `genres/11-capability-matrix.md`（先过能力边界，再动笔）
- 「参考图怎么用 / 多个人怎么绑 / 声音怎么绑」→ `genres/12-reference-grammar.md`
- 「剪 / 字幕 / 封面 / 平台规格」→ `genres/13-editing-delivery.md`
- 「做十集 / 排期 / 记进度」→ `genres/14-batch-production.md`
- 「第一次做，先试一条」→ `genres/15-onboarding.md`
- 「加旁白 / 导字幕 / 翻英文 / 重剪一版」→ `genres/16-narration-subtitle-global.md`
- 「提示词写完要提交了 / 形状对不对 / 秒数加不平」→ `genres/17-prompt-contract.md`（十条机检全绿才提交）
- 一镜到底 / 复杂运镜 → `cinematic/banks/A` + `modules/06-motion.md`
- 生成总崩同一类问题 → `cinematic/banks/E-failure-atlas.md`
- 连续段落衔接 → `cinematic/modules/07-sequence.md`
- 要拆成 4–15 秒 Seedance 单元 → `fuyao/06-seedance2-adapter.md`

---

## 7. 与原四技能的关系

本技能是**加法**：四套原件原地不动，仍可单独 `/skill:canvas`、`/skill:djzs` 等调用。

- 只想跑一条完整链路 → 用本技能，一次入口到底。
- 只想查某个细节 → 直接用原技能，路径更短。
- 两边结论打架 → 按第 2 节的冲突裁决表，不要各写一半。
- 想按题材拍 → 只有本技能有题材库；原四家都不分题材，别指望在 `djzs` 里找出「宫斗该怎么拍」。

禁用原技能前先确认本技能能覆盖对应场景；不确定就都留着，重复的只是磁盘，不是判断。
