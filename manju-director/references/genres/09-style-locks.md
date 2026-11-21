# 画风锁：六种画风的参数级写法

> 只写画风名 = 抽卡。这一份把每种画风拆成**能量测的参数**，并给出**排除清单**。没有排除清单，2D 会塌成通用 3D 脸，3D 会塌成半写实。每段可直接粘进提示词的「① 全局块」。

---

## 通用结构（每种画风都按这五行写）

1. **媒介与流派**（点名到具体年代/工艺，不要只写 anime / 3D）
2. **线条规格**（粗细像素 + 是否有色 + 断线）
3. **阴影与高光规格**（段数 + 硬边/软边 + 层次）
4. **材质分家**（布/革/金属/宝石/湿面/玻璃各自一句）
5. **排除清单**（排掉相邻画风，逐项写）

---

## §1 2D 赛璐璐日漫（玄幻、武侠、校园、言情主力）

```text
媒介与流派：90s–2000s Japanese cel-shaded 2D animation, hand-drawn feel, limited animation.
线条：thin colored line art, 1–2px equivalent, warm dark brown rather than pure black, line weight varies slightly with pressure, never uniform mechanical lines.
阴影：2–3 band cel shading with hard edges; a single soft translucent mid-tone layer between the two bands; no airbrushed gradients.
高光：two-layer hair highlight (a hard specular streak plus one soft sheen band); pupils carry one crisp catchlight and one smaller secondary.
材质：cloth = matte with hard-edged fold shadows; leather = small sharp specular; metal = one high-contrast streak, no gradient; gem = flat color plus one white sparkle; wet ground = mirror reflection with cel-broken edges; glass = flat translucent panel, no refraction.
背景：painted backgrounds deliberately one stop darker than the characters; primary light and shadow color borrowed from each character's own palette.
颜色：each character assigned one main / one secondary / one accent color plus a material motif; colors never swap between characters.
排除清单：no thick black outlines, no single-band flat shading, no cheap TV-anime look, no generic 3D pretty-face, no plastic CG sheen, no semi-realism, no photorealism, no low-density background, no muddy color.
```

**易崩点**：快动作会让赛璐珞退化成写实光影 → 高速段重申一次上色规格。
**适用**：玄幻、武侠、校园、言情、纯动作。

---

## §2 国漫厚涂（玄幻、古装、山海题材）

```text
媒介与流派：Chinese national-manhua thick-paint (厚涂) rendering, digital painterly, cinematic Chinese animation.
线条：no visible outline on lit surfaces; thin dark contour only in shadow cores and at silhouette edges.
阴影：painterly value blocks, 3–5 steps, soft-brush transitions inside forms but hard silhouette edges; ambient occlusion painted darker and warmer than the key.
高光：broad soft specular on skin and silk; metal gets a dry-brush streak rather than a clean line.
材质：heavy silk with weight and straight-falling folds; oxidized brass with green blotches; aged wood with grain and cracked lacquer; stone with moss in the crevices.
背景：atmospheric depth with painted fog layers; distant forms lose saturation and contrast rather than detail.
颜色：deep ink base plus one metallic accent (gold / bronze / cinnabar); highlight color never pure white.
排除清单：no anime flat shading, no cel banding, no airbrushed plastic skin, no western fantasy armor look, no neon color, no sharp uniform line art, no photographic texture.
```

**易崩点**：厚涂容易糊成一团 → 必须保留「硬剪影边缘 + 暗部更暖」两条。
**适用**：玄幻、古装宫斗、洪荒、山海经题目。

---

## §3 3D 卡通渲染（萌宝、亲子、搞笑、部分都市）

```text
媒介与流派：stylized 3D toon-shaded animation, feature-film quality, soft global illumination.
线条：no outlines; silhouette carried by shape and rim light instead.
阴影：two-tone toon shading with soft terminator; contact shadows always present and slightly warmer than ambient.
高光：broad soft specular shaped by the form; skin never chrome-bright.
材质：skin = subsurface with soft peach scatter; cloth = matte with visible weave at close-up; plastic = chalky, low gloss; metal = soft anisotropic; hair = card-based, alpha-clumped strands.
比例：if a child, head-to-body about 1:4, short limbs, rounded belly, dimpled knuckles.
背景：soft depth-of-field, warm ambient bounce, props slightly out of scale (too large for a child's world).
颜色：high-key, cream and warm white base, one saturated accent per character.
排除清单：no photoreal skin pores, no anime 2D line art, no plastic toy gloss on faces, no harsh specular hotspots, no realistic human proportions, no dark horror lighting, no visible polygon edges.
```

**易崩点**：脸变塑料 → 写 `chalky low-gloss` 与 `subsurface peach scatter`，并进排除清单写 `no plastic toy gloss on faces`。
**适用**：萌宝、亲子、儿童教育、搞笑。

---

## §4 2.5D 半写实（悬疑、末世、都市爽剧、科幻）

```text
媒介与流派：2.5D semi-realistic rendering, animation that reads as stylized live-action, no photoreal skin pores.
线条：none; form defined by light, not line.
阴影：physically plausible key/fill/rim, but values compressed one stop so faces stay readable; shadows cool, highlights warm.
高光：specular controlled and small; eyes carry a single soft catchlight.
材质：skin = matte with subtle sheen on nose and cheekbone; fabric = visible weave; concrete = pitted with rebar; steel = brushed with oil streaks; glass = dust-filmed.
背景：real lens behavior — shallow depth of field, slight chromatic edge, practical light bloom.
颜色：single dominant grade plus one practical warm source; blacks crushed but never pure 0.
排除清单：no photorealistic pores or stubble detail, no anime cel banding, no cartoon proportions, no plastic CG sheen, no oversaturated neon, no HDR halo, no video-game cutscene look.
```

**易崩点**：往写实漂 → 写 `no photorealistic pores and stubble`，并把肤色写成 `matte with subtle sheen`。
**适用**：悬疑恐怖、末世废土、都市爽剧、科幻机甲。

---

## §5 水墨 / 国风写意（仙侠意境、山水、宣传片头）

```text
媒介与流派：Chinese ink-wash animation, xieyi (写意) brushwork, minimal color.
线条：brush strokes with visible dry-brush breakup (飞白), pressure variation, no uniform lines.
阴影：ink wash gradients (5 tones of diluted ink), wet-on-wet bleed at edges, no digital banding.
高光：paper white left unpainted as the only highlight; never add white paint.
材质：silk suggested by two strokes; stone by one dry stroke; water by negative space.
背景：mist made of unpainted paper; composition follows 留白, subject occupies at most one third of frame.
颜色：ink black, paper warm white, one single spot color (cinnabar or indigo) used once per shot.
排除清单：no cel shading, no 3D render, no full-color saturation, no hard digital gradients, no western watercolor, no thick outlines, no detailed texture rendering.
```

**易崩点**：AI 会偷偷补满细节 → 明写 `subject occupies at most one third of frame, the rest is unpainted paper`。
**适用**：仙侠意境镜头、片头、山水空镜。

---

## §6 特殊媒介

| 媒介 | 关键参数 | 排除清单 |
|---|---|---|
| **定格动画** | `12fps on twos, 2-frame holds, handcrafted felt/clay/paper materials, visible finger marks, slight set jitter` | no smooth 24fps interpolation, no CG cleanliness, no motion blur |
| **像素风** | `limited 32-color palette, 1:1 pixel grid, no anti-aliasing, dithered gradients only, sprite-based motion on 8-frame loops` | no smooth gradients, no HD detail, no 3D lighting |
| **条漫/分格** | 只作**单帧内的图形设计**（斜切分、留白条），**不作分镜载体**（硬规则 9 禁宫格故事板） | 不得把整片做成漫画格叙事 |
| **复古胶片** | `16mm grain, halation on highlights, gate weave, slight exposure flicker, anamorphic oval bokeh` | no digital sharpness, no clean modern grade |
| **DV/家录** | `auto-focus hunting, exposure pumping, handshake, tape noise, timestamp burned in`（**时间码是唯一允许的屏内文字**） | no cinematic stabilization, no shallow DOF |

---

## §7 特殊形态（非题材，是片子形态）

### 7.1 搞笑 / 沙雕

- **笑点必须落在一个看得见的东西上**（一件物变形、一个人做错一个动作、一个数量不对）。
- **荒诞设定配一本正经的相机**：物理要真、重力要真、镜头要稳。荒诞来自内容，不来自运镜。
- 15 秒结构：`0-4s 正常 → 4-8s 出现异常但没人发现 → 8-11s 有人发现 → 11-15s 反应`。
- 禁止：滑稽音效堆叠、镜头乱晃、表情夸张特写。
- 梗图式分格只允许做**单帧图形**，不做分镜。

### 7.2 纯动作 / 无对白

- 删掉所有台词，靠**运动矢量**叙事：每一拍一个朝向（左→右→上→下），观众靠方向变化读进度。
- 音效必须写：每拍一行（`fabric snap, gravel crunch, metal ring`）。
- 段落 2–3 秒，7–10 秒最多 4 段。

### 7.3 卡点 MV / OP

1. **从 BPM 推节拍锚点**：`BPM 96 → beat every 0.625s`；把剪辑、甩发、队形变化钉在真实重拍上。
2. **写节拍表**：`[0.0s][0.625s][1.25s]...` 每个重拍一个动作。
3. **约束伴舞/背景**，别抢视觉中心：`background figures never cross the center line, never occlude the lead's face`。
4. 外观锚点必须贯穿：发色、主色衣、一个饰品。

### 7.4 预告片 / 宣传

- 8–15 秒，写死「广告美学 + 编号分镜 + 一个英雄镜头 + 关键词串」。
- 前 2 秒必须有信息，不要 logo 铺场。
- 结尾留一个未解决的画面，不给结论。

### 7.5 儿童 / 教育

- 低对比、圆角、软材质、无硬阴影、无快速剪辑。
- 每个镜头只教一件事，动作要有明确的因与果。
- 禁用：恐怖元素、尖锐物、快速推近、闪烁灯效（视觉安全）。
- 角色比例固定，跨镜不变（儿童观众对形变极敏感）。

---

## §8 画风选择速查

| 题材 | 首选 | 次选 | 别用 |
|---|---|---|---|
| 玄幻修真 | 2D 赛璐璐 / 国漫厚涂 | 水墨（意境段） | 3D 卡通、2.5D |
| 武侠 | 2D 赛璐璐 | 国漫厚涂 | 3D 卡通 |
| 都市爽剧 | 2.5D 半写实 | 3D 卡通（喜剧向） | 水墨 |
| 言情 | 2D 赛璐璐 | 2.5D | 像素、定格 |
| 悬疑恐怖 | 2.5D | 2D（老动画感） | 3D 卡通、高饱和 |
| 古装宫斗 | 国漫厚涂 | 2D 赛璐璐 | 3D 卡通 |
| 科幻末世 | 2.5D | 3D（机甲向） | 水墨 |
| 校园青春 | 2D 赛璐璐 | 2.5D | 厚涂 |
| 萌宝亲子 | 3D 卡通 | 2D 手绘 | 2.5D、悬疑向 |
| 搞笑 | 3D 卡通 / 2D | 定格 | 2.5D 半写实 |

**一票否决**：2D 与 3D 的词汇表混写 = 半写实失败态。选一套，另一套的词写进排除清单。
