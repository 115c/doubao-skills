#!/usr/bin/env python3
"""提示词体检：六段式视频提示词的机检 + 评分。

用法：
    python prompt_lint.py 提示词.md [--duration 6] [--json]

退出码：0 = PASS，1 = WARN，2 = FAIL。
"""

import argparse
import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FIELDS = [
    "subject_definitions",
    "summary",
    "retention_analysis",
    "detailed_description",
    "overall_soundscape",
    "non_diegetic_music",
]

FORBIDDEN = [
    "杰作", "8K", "超清", "电影级", "氛围感", "大片感", "震撼", "唯美", "极致", "完美",
    "masterpiece", "best quality", "ultra detailed", "highly detailed",
]

PLATFORM_PARAMS = [
    r"\b\d{3,4}\s*[x×]\s*\d{3,4}\b", r"步数", r"\bseed\b", r"采样器", r"\bcfg\b", r"负面提示词", r"\bsteps\s*[:=]", r"--ar\b",
]

TS_RE = re.compile(r"At\s+(\d{1,2}):(\d{2})\.(\d{3})")
SHOT_RE = re.compile(r"\[Shot\s+(\d+)\]")
SUBJ_USE_RE = re.compile(r"<(Subject|Picture|Video|Audio)\s+(\d+)>")
SUBJ_DEF_RE = re.compile(r"^\s*(Subject|Picture|Video|Audio)\s+(\d+)\s*=", re.MULTILINE)


def load(path: str) -> str:
    with open(path, encoding="utf-8-sig") as handle:
        return handle.read()


def field_bodies(text: str):
    """返回 {字段: 正文}，按行首 `字段:` 切分。"""
    marks = []
    for name in FIELDS:
        match = re.search(rf"^\s*{name}\s*:\s*", text, re.MULTILINE)
        if match:
            marks.append((match.start(), match.end(), name))
    marks.sort()
    bodies = {}
    for index, (_, end, name) in enumerate(marks):
        stop = marks[index + 1][0] if index + 1 < len(marks) else len(text)
        bodies[name] = text[end:stop]
    return bodies, marks


def chinese_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def split_items(text: str):
    return [part.strip() for part in re.split(r"[；;]", text) if part.strip()]


def check(text: str, duration: float):
    issues = []  # (level, message)
    bodies, marks = field_bodies(text)

    # 1-2 字段齐全与顺序
    missing = [name for name in FIELDS if name not in bodies]
    if missing:
        issues.append(("FAIL", "缺少字段：" + "、".join(missing)))
    order = [name for _, _, name in marks]
    if order and order != [name for name in FIELDS if name in order]:
        issues.append(("FAIL", "字段顺序不对：应为 " + " → ".join(FIELDS)))

    # 3 镜号
    shots = [(int(num), match.start()) for match in SHOT_RE.finditer(text) for num in [match.group(1)]]
    if not shots:
        issues.append(("FAIL", "没有 [Shot N] 镜号"))
    else:
        numbers = [num for num, _ in shots]
        expected = list(range(1, len(numbers) + 1))
        if numbers != expected:
            issues.append(("FAIL", f"镜号不连续：{numbers}（应为 {expected}）"))
        first_shot_pos = shots[0][1]
        first_line = text[first_shot_pos:].split("\n", 1)[0]
        if TS_RE.search(first_line):
            issues.append(("WARN", "[Shot 1] 建议不带时间戳（时间戳从 Shot 2 起写）"))
        # Shot 1 之后每镜都要有时间戳
        for index in range(1, len(shots)):
            start = shots[index][1]
            stop = shots[index + 1][1] if index + 1 < len(shots) else len(text)
            if not TS_RE.search(text[start:stop]):
                issues.append(("FAIL", f"[Shot {shots[index][0]}] 没有 At MM:SS.mmm 时间戳"))

    # 4 时间戳递增与时长
    stamps = [(int(m.group(1)), int(m.group(2)), int(m.group(3))) for m in TS_RE.finditer(text)]
    seconds = [m * 60 + s + ms / 1000 for m, s, ms in stamps]
    for prev, cur in zip(seconds, seconds[1:]):
        if cur <= prev:
            issues.append(("FAIL", f"时间戳未递增：{prev:.3f}s → {cur:.3f}s"))
            break
    if seconds and duration and max(seconds) > duration + 0.05:
        issues.append(("FAIL", f"时间戳 {max(seconds):.2f}s 超过时长 {duration:.2f}s"))

    # 5 引用闭合
    defined = {(kind, int(num)) for kind, num in SUBJ_DEF_RE.findall(text)}
    defs_body = bodies.get("subject_definitions", "")
    for kind, num in SUBJ_USE_RE.findall(defs_body):
        defined.add((kind, int(num)))
    used = {(kind, int(num)) for kind, num in SUBJ_USE_RE.findall(text)}
    dangling = sorted(used - defined)
    if dangling:
        issues.append(("FAIL", "引用未定义：" + "、".join(f"<{k} {n}>" for k, n in dangling)))
    if not defined:
        issues.append(("WARN", "subject_definitions 里没有 <Subject N> = 定义（纯文生视频可忽略）"))

    # 6 台词
    dialogues = re.findall(r"<d>(.*?)</d>", text, re.DOTALL)
    for index, dialogue in enumerate(dialogues, 1):
        if "[Chinese]" not in dialogue:
            issues.append(("FAIL", f"第 {index} 句台词缺少 [Chinese] 标记"))
        if not re.search(r"\(S\d\)", dialogue):
            issues.append(("WARN", f"第 {index} 句台词没有 (S#) 说话人绑定"))

    # 7 无对白锁嘴
    if not dialogues and not re.search(r"嘴唇闭合|无对白|不出声", text):
        issues.append(("WARN", "没有台词，但未写「嘴唇闭合/无对白」"))

    # 8 禁用词
    lowered = text.lower()
    for word in FORBIDDEN:
        if word.lower() in lowered:
            issues.append(("FAIL", f"禁用词：{word}"))

    # 9 平台参数
    for pattern in PLATFORM_PARAMS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            issues.append(("FAIL", f"出现平台参数：{match.group(0)}"))

    # 10 字数
    total = chinese_len(text)
    if total < 350:
        issues.append(("FAIL", f"六字段总字数偏少：{total} 字（下限 350）"))
    elif total > 900:
        issues.append(("WARN", f"六字段总字数偏多：{total} 字（上限 900）"))

    # 11 声音点
    soundscape = bodies.get("overall_soundscape", "")
    sound_items = split_items(soundscape)
    if len(sound_items) < 3:
        issues.append(("FAIL", f"声景只有 {len(sound_items)} 项（至少 3 项）"))

    # 12 配乐
    music = bodies.get("non_diegetic_music", "").strip()
    if not music:
        issues.append(("WARN", "non_diegetic_music 为空，写 N/A 或给乐器"))
    elif music.upper() != "N/A" and not re.search(r"鼓|钢琴|弦|贝斯|吉他|合成器|号|铜管|笛|低频|pad", music, re.IGNORECASE):
        issues.append(("WARN", "配乐没写乐器"))

    issues.extend(camera_logic_issues(text, duration))

    # 评分
    score = 100
    for level, message in issues:
        if level == "FAIL":
            score -= 10 if "时间戳" in message or "引用" in message else 6
        else:
            score -= 2
    score = max(0, score)
    if score < 80:
        issues.append(("FAIL", f"评分 {score} < 80，不通过"))

    levels = {level for level, _ in issues}
    verdict = "FAIL" if "FAIL" in levels else ("WARN" if "WARN" in levels else "PASS")
    return {"verdict": verdict, "score": score, "issues": issues, "chars": total}




# ---------------- 镜头六要素 + 动作逻辑机检 ----------------

SHOT_SPLIT_RE = re.compile(r"\[Shot\s+(\d+)\]")

CAMERA_ELEMS = {
    "景别": r"(大特写|特写|近景|中近景|中景|中全景|全景|远景|大全景)",
    "角度": r"(平视|俯拍|俯视|仰拍|仰视|侧拍|侧面|正面|背面|斜侧|顶拍|荷兰角)",
    "机位运动": r"(推镜|推近|推进|拉镜|拉开|摇镜|摇摄|平移|移镜|跟拍|跟镜|升降|手持|固定机位|固定|环绕|变焦)",
    "焦段": r"(\d{1,3}\s*mm|广角|长焦|标准镜|微距|鱼眼)",
    "光线": r"(逆光|侧光|顶光|底光|柔光|硬光|自然光|补光|光比|色温|光从)",
    "起落幅": r"(起幅|落幅|从[^。；]{0,14}到[^。；]{0,14})",
}

ACTION_WORDS = r"(抬手|转身|迈步|冲|奔|跑|跳|跃|跪|扑|抓|拔|刺|劈|砍|踢|踹|推|拉|拽|扔|抛|接|挡|格|闪|躲|翻|滚|蹲|起立|坐下|躺|回头|低头|抬头|摇头|点头|伸手|缩手|撑|蹬|甩|挥)"
AIRBORNE_WORDS = r"(腾空|飞起|击飞|倒飞|翻滚|跃起|凌空|悬空|离地)"
SUPPORT_WORDS = r"(蹬|踏|踩|撑|借力|发力|起跳|撑地|蹬地|踩实|踏地|落地|着地)"
STRIKE_WORDS = r"(劈|砍|踹|踢|刺|捅|撞|挥拳|抡|抽打|踹开|顶开|撞飞)"
STRIKE_IGNORE = r"(打来|拍打|相击|脆响|击响|相撞|撞响)"
DIRECTION_WORDS = r"(向|朝|从[^。；]{0,10}到|方向|自下而上|自上而下|横|竖|斜|正对|迎面|背向)"
GROUND_WORDS = r"(地面|沙|泥|石|台阶|坡|走廊|街|屋|地板|土地)"
GAZE_WORDS = r"(看向|望向|盯着|视线|面向|背对|侧对|抬眼|垂眼|目光)"
ABSTRACT_WORDS = ["气势", "压迫感", "爆发", "震撼", "凌厉", "杀气", "恐怖如斯", "气吞山河", "霸气"]

MUTEX_PAIRS = [
    ("跑", "停下"), ("跑", "站住"), ("奔", "驻足"),
    ("举", "放下"), ("睁开眼", "闭上眼"), ("睁眼", "闭眼"),
    ("拔刀", "收刀"), ("起身", "坐下"),
    ("前进", "后退"), ("靠近", "远离"),
]


def shot_blocks(text: str):
    matches = list(SHOT_SPLIT_RE.finditer(text))
    blocks = []
    for index, match in enumerate(matches):
        stop = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((int(match.group(1)), text[match.end():stop]))
    return blocks


def camera_logic_issues(text: str, duration: float):
    issues = []
    blocks = shot_blocks(text)

    # 六要素
    for num, body in blocks:
        missing = [name for name, pattern in CAMERA_ELEMS.items() if not re.search(pattern, body)]
        if len(missing) >= 3:
            issues.append(("FAIL", f"[Shot {num}] 镜头六要素缺 {len(missing)} 项：{'、'.join(missing)}"))
        elif missing:
            issues.append(("WARN", f"[Shot {num}] 镜头六要素缺：{'、'.join(missing)}"))

    # 互斥动作
    for num, body in blocks:
        for first, second in MUTEX_PAIRS:
            for clause in re.split(r"[。；;，,\n]", body):
                if first in clause and second in clause:
                    issues.append(("FAIL", f"[Shot {num}] 动作互相打架：「{first}」和「{second}」不能同时发生"))

    # 无支撑的腾空/翻滚
    for num, body in blocks:
        if re.search(AIRBORNE_WORDS, body) and not re.search(SUPPORT_WORDS, body):
            issues.append(("FAIL", f"[Shot {num}] 有腾空/击飞/翻滚，但没写支撑点或发力（蹬地、借力、落地）——物理不成立"))

    # 打击没方向
    for num, body in blocks:
        for clause in re.split(r"[。；;，,\n]", body):
            if re.search(STRIKE_WORDS, clause) and not re.search(STRIKE_IGNORE, clause) and not re.search(DIRECTION_WORDS, clause):
                issues.append(("WARN", f"[Shot {num}] 攻击动作没写方向/目标：「{clause.strip()[:18]}」"))

    # 动作密度 vs 时长
    if duration and blocks:
        for num, body in blocks:
            actions = re.findall(ACTION_WORDS, body)
            limit = max(2, int(duration / 2) + 1)
            if len(actions) > limit * 2:
                issues.append(("WARN", f"[Shot {num}] {duration:g}s 内动作节点 {len(actions)} 个，超出可拍密度（建议 ≤{limit * 2}）"))

    # 镜头运动自相矛盾
    for num, body in blocks:
        for clause in re.split(r"[。；;，,\n]", body):
            if re.search(r"推", clause) and re.search(r"拉", clause) and not re.search(r"推拉|拉推", clause):
                issues.append(("WARN", f"[Shot {num}] 同一句里推和拉冲突：「{clause.strip()[:18]}」"))
            if re.search(r"摇", clause) and re.search(r"移", clause) and not re.search(r"摇移|移摇|摇镜平移|边摇边移", clause):
                issues.append(("WARN", f"[Shot {num}] 同一句里摇和移冲突：「{clause.strip()[:18]}」"))

    # 移动类动作没有地面/环境
    for num, body in blocks:
        if re.search(r"(跑|冲|追|逃|退|奔)", body) and not re.search(GROUND_WORDS, body):
            issues.append(("WARN", f"[Shot {num}] 有移动动作但没写地面/环境（沙地、石阶、走廊…）"))

    # 人物镜没有视线
    for num, body in blocks:
        if re.search(r"<(Subject|Picture)\s+\d+>", body) and not re.search(GAZE_WORDS, body):
            issues.append(("WARN", f"[Shot {num}] 有人物/参考图，但没写视线或朝向"))

    # 抽象词过多
    hits = [word for word in ABSTRACT_WORDS if word in text]
    total = sum(text.count(word) for word in ABSTRACT_WORDS)
    if total > 3:
        issues.append(("WARN", f"抽象词过多（{total} 次：{'、'.join(hits)}）——换成可拍的具体动作"))

    # 参考素材上限
    limits = {"Picture": 9, "Video": 3, "Audio": 3}
    for kind, limit in limits.items():
        used = {int(n) for n in re.findall(rf"<{kind}\s+(\d+)>", text)}
        defined = {int(n) for n in re.findall(rf"^\s*{kind}\s+(\d+)\s*=", text, re.MULTILINE)}
        count = max(len(used), len(defined))
        if count > limit:
            issues.append(("FAIL", f"<{kind}> 用了 {count} 个，超过上限 {limit}"))

    return issues


# ---------------- 图片（MOSS）体检 ----------------

IMG_UNITS = {
    "五件套-年龄": r"(\d{1,3}|[一二三四五六七八九十百]{1,4})\s*岁",
    "五件套-发型": r"(发|辫|马尾|寸头|刘海|分缝|丸子头|盘发)",
    "五件套-脸型特征": r"(脸|眉|眼|痣|疤|酒窝|颧骨)",
    "五件套-服装": r"(衣|裙|袍|衫|外套|西装|制服|裤|披风|甲)",
    "五件套-标志物": r"(戒|镯|项链|耳|剑|刀|枪|杖|包|伞|扇|镜|印|符)",
    "姿态朝向": r"(站|坐|跪|躺|蹲|回身|侧身|面向|背对|抬手|持|握|抱)",
    "景别机位": r"(特写|近景|中景|全景|远景|半身|全身|平视|俯拍|仰拍|侧面|正面)",
    "环境": r"(背景|场景|房间|街道|室内|室外|纯色|墙面|地面|桌|窗|门)",
    "光线": r"(光|逆光|侧光|顶光|底光|柔光|色温|暖|冷|打亮|投影)",
    "色调质感": r"(色调|质感|胶片|颗粒|写实|渲染|低饱和|高对比|冷灰|暖黄)",
}

NEG_SENTENCE = re.compile(r"(?:^|[。；\n])[^。；\n]{0,20}(不要|没有|禁止|避免)[^。；\n]{0,20}[。；\n]")
RATIO_RE = re.compile(r"\b\d{1,2}\s*[:：]\s*\d{1,2}\b")


def check_image(text: str):
    issues = []
    total = chinese_len(text)
    if total < 120:
        issues.append(("FAIL", f"字数偏少：{total} 字（下限 120）"))
    elif total > 800:
        issues.append(("WARN", f"字数偏多：{total} 字（上限 800）"))

    for name, pattern in IMG_UNITS.items():
        if not re.search(pattern, text):
            issues.append(("FAIL", f"缺少单元：{name}"))

    for word in FORBIDDEN:
        if word.lower() in text.lower():
            issues.append(("FAIL", f"禁用词：{word}"))

    for pattern in PLATFORM_PARAMS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            issues.append(("FAIL", f"出现平台参数：{match.group(0)}"))

    match = RATIO_RE.search(text)
    if match:
        issues.append(("FAIL", f"正文出现比例：{match.group(0)}（比例放节点参数）"))

    if re.search(r"同上|一样的人|如同上一张", text):
        issues.append(("FAIL", "用了「同上」——跨图必须复写五件套"))

    for match in NEG_SENTENCE.finditer(text):
        issues.append(("WARN", f"疑似负向句：{match.group(0).strip()[:24]}"))

    score = 100
    for level, message in issues:
        score -= 6 if level == "FAIL" else 2
    score = max(0, score)
    if score < 80:
        issues.append(("FAIL", f"评分 {score} < 80，不通过"))

    levels = {level for level, _ in issues}
    verdict = "FAIL" if "FAIL" in levels else ("WARN" if "WARN" in levels else "PASS")
    return {"verdict": verdict, "score": score, "issues": issues, "chars": total}




# ---------------- 道具多视角板体检 ----------------

PROP_VIEW_WORDS = ["正面", "正侧", "侧面", "背面", "俯视", "仰视", "45", "顶视", "底视", "特写", "微距"]
PROP_FORM_WORDS = ["拎", "提", "放", "桌", "插", "鞘", "拔", "握", "掰", "咬", "开", "合", "悬", "立", "倒", "摊", "挂", "捧", "递"]
PROP_MATERIAL_WORDS = ["木", "铁", "铜", "钢", "竹", "陶", "瓷", "布", "皮", "石", "纸", "金属", "麻", "漆", "玉", "银", "面"]
PROP_STYLE_WORDS = ["写实", "实拍", "电影", "低饱和", "自然光", "侧逆光", "做旧", "磨损", "包浆", "4K", "浅景深"]
PROP_REFER_WORDS = ["参照物", "旁边放", "旁边摆", "并排放", "作对比", "对比物", "一只手", "手持比例", "参照"]
PROP_NEGATORS = ["无", "没有", "不要", "不许", "禁止", "别", "不出现"]


def _has_reference_object(text: str) -> str:
    for clause in re.split(r"[。；;\n]", text):
        for word in PROP_REFER_WORDS:
            if word in clause:
                if any(neg in clause for neg in PROP_NEGATORS):
                    continue
                return clause.strip()[:40]
    return ""


def check_prop(text: str):
    issues = []
    total = chinese_len(text)
    if total < 150:
        issues.append(("FAIL", f"字数偏少：{total} 字（下限 150）"))
    elif total > 900:
        issues.append(("WARN", f"字数偏多：{total} 字（上限 900）"))

    # 1 零件清单：结构段里至少 3 个零件
    part_count = 0
    match = re.search(r"结构[：:]\s*(.+)", text)
    if match:
        segment = match.group(1)
        segment = re.split(r"[。；;]", segment)[0]
        parts = [item for item in re.split(r"[、，,]", segment) if len(re.sub(r"\s", "", item)) >= 2]
        part_count = len(parts)
    if part_count < 3:
        issues.append(("FAIL", f"结构零件只有 {part_count} 个（至少 3 个；写法「结构：由 A、B、C 组成」）"))

    # 2 视角/形态数（数量不固定，2–4 个；但必须写清怎么用）
    views = {word for word in PROP_VIEW_WORDS if word in text}
    forms = {word for word in PROP_FORM_WORDS if word in text}
    if len(views | forms) < 2:
        issues.append(("FAIL", f"视角/形态只有 {len(views | forms)} 个（至少 2 个，写清怎么用：被拎起/放桌面/插鞘/掰开…）"))
    if not forms:
        issues.append(("WARN", "没写使用形态（被拎起/放在桌面/插在鞘中/拔出/掰开…）——建议按分镜里的出现方式补"))

    # 3 尺寸
    if not re.search(r"(长|高|宽|直径|厚)[^。；]{0,12}(约|≈)?\s*\d+(\.\d+)?\s*(cm|厘米|mm|毫米)?", text) and not re.search(r"掌心|单手|双手|前臂|拇指", text):
        issues.append(("FAIL", "没写尺寸（长度/直径/能否单手握住）"))

    # 4 材质
    if not any(word in text for word in PROP_MATERIAL_WORDS):
        issues.append(("FAIL", "没写材质（木/铁/铜/陶/布/皮…）"))

    # 5 风格
    style_hits = [word for word in PROP_STYLE_WORDS if word in text]
    if len(style_hits) < 2:
        issues.append(("FAIL", f"风格词不足（{len(style_hits)} 个；至少 2 个：写实/低饱和/做旧…）"))

    # 6 背景
    if not re.search(r"纯色|中性|灰背景|纯灰|背景", text):
        issues.append(("FAIL", "没写背景（纯中性灰/纯色）"))

    # 7 参照物
    bad = _has_reference_object(text)
    if bad:
        issues.append(("FAIL", f"出现参照物描述：{bad}"))

    for word in FORBIDDEN:
        if word.lower() in text.lower():
            issues.append(("FAIL", f"禁用词：{word}"))

    for pattern in PLATFORM_PARAMS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            issues.append(("FAIL", f"出现平台参数：{m.group(0)}"))

    m = RATIO_RE.search(text)
    if m:
        issues.append(("FAIL", f"正文出现比例：{m.group(0)}（比例放节点参数）"))

    if re.search(r"同上|一样的东西|如同上一张", text):
        issues.append(("FAIL", "用了「同上」——每件道具都要写全"))

    for m in NEG_SENTENCE.finditer(text):
        issues.append(("WARN", f"疑似负向句：{m.group(0).strip()[:24]}"))

    score = 100
    for level, message in issues:
        score -= 6 if level == "FAIL" else 2
    score = max(0, score)
    if score < 80:
        issues.append(("FAIL", f"评分 {score} < 80，不通过"))

    levels = {level for level, _ in issues}
    verdict = "FAIL" if "FAIL" in levels else ("WARN" if "WARN" in levels else "PASS")
    return {"verdict": verdict, "score": score, "issues": issues, "chars": total}


def main() -> int:
    parser = argparse.ArgumentParser(description="六段式视频提示词体检")
    parser.add_argument("file")
    parser.add_argument("--duration", type=float, default=0.0, help="镜头时长（秒）")
    parser.add_argument("--kind", choices=["video", "image", "prop"], default="video", help="video=六段式；image=MOSS 文生图；prop=道具多视角板")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    content = load(args.file)
    if args.kind == "image":
        result = check_image(content)
    elif args.kind == "prop":
        result = check_prop(content)
    else:
        result = check(content, args.duration)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['verdict']}  评分 {result['score']}  字数 {result['chars']}")
        for level, message in result["issues"]:
            print(f"  [{level}] {message}")
        if not result["issues"]:
            print("  无问题，可以交稿")
    return {"PASS": 0, "WARN": 1}.get(result["verdict"], 2)


if __name__ == "__main__":
    sys.exit(main())
