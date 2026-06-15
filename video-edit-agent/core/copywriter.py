"""文案生成模块 — DeepSeek API + 预置模板兜底"""

import json
import random
import re
from itertools import combinations

from config import DEEPSEEK_API_KEY
from core.llm import LLMClient, LLMConfig

# ========== 预置模板（API 失败时兜底） ==========

OPENING_TEMPLATES = [
    "你家衣柜还乱糟糟的吗？",
    "每次找衣服都要翻半天？",
    "衣柜空间总是不够用？",
    "钢制家具不知道怎么选？",
    "你家衣柜是不是还缺点什么？",
    "衣服太多放不下怎么办？",
    "想要衣柜多用十年？",
    "衣柜用好多年了还跟新的一样？",
    "选衣柜你最看重什么？",
    "很多人买衣柜都忽略了这一点！",
]

CLOSING_TEMPLATES = [
    "赶快点击下方下单吧！",
    "限时优惠，点击购买！",
    "让衣柜焕然一新，点击下单！",
    "好物不等人，赶紧入手吧！",
    "点击下方链接，把它带回家！",
    "现在下单还有优惠哦！",
]

SP_TEMPLATES = [
    "我们的{sp}设计，让使用更省心。",
    "采用{sp}工艺，品质看得见。",
    "加厚{sp}，耐用不变形。",
    "{sp}的精工设计，每一个细节都用心。",
    "升级{sp}，体验大不同。",
    "特别做了{sp}处理，经久耐用。",
    "来看看我们的{sp}，这就是品质。",
    "{sp}加高加厚设计，承重力更强。",
]


def generate_script(chosen_two, product_name="", usage_scenario=""):
    """
    生成带分段标记的文案。

    参数:
        chosen_two: tuple[str, str] - 本次选中的两个卖点
        product_name: str - 商品名称（前端输入）
        usage_scenario: str - 使用场景（前端输入）

    返回:
        dict: {"开头": "...", "卖点1": "...", "卖点2": "...", "结尾": "..."}
    """
    if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != "your-api-key-here":
        try:
            return _call_llm(chosen_two, product_name, usage_scenario)
        except Exception as e:
            print(f"  [WARNING]  LLM 调用失败: {e}")
            print(f"  → 切换到预置模板生成")

    return _generate_template(chosen_two, product_name)


def _call_llm(chosen_two, product_name="", usage_scenario=""):
    """调用 LLM 生成文案"""
    sp1, sp2 = chosen_two
    product = product_name or "钢制家具"
    scenario = usage_scenario or "日常家居收纳"

    system_prompt = """# 角色
你是一位电商短视频文案写手 根据用户提供的商品名称 使用场景 和两个指定的卖点关键词 写出叫卖风格的短视频文案 生成的文案长度控制在20秒朗读时长 特别注意：文字中的标点只能出现"!" "?" 其余标点符号用空格代替

## 核心规则（必须严格遵守）
1. 文案只围绕用户明确给出的两个卖点关键词展开 不得提及任何其他产品特性 功能 材质 设计 或优点
2. 即使你认为某个其他卖点也很有吸引力 也绝不能写入文案
3. 如果用户没有提供某条信息 就视为不存在 不要自行补充或推测

## 写作要求
1. 风格有创意 不呆板 符合电商叫卖风格
2. 逻辑清晰 富有吸引力
3. 文案篇幅严格控制在100字左右
4. 【开头】和【结尾】必须精简 各只写1句 每句控制在8字以内

## 输出格式（每个段落一行）：
【开头】文案内容
【卖点1】文案内容
【卖点2】文案内容
【结尾】文案内容"""

    user_prompt = f"""商品名称:{product}
使用场景:{scenario}
本次视频只允许展示以下两个卖点（严禁出现其他卖点）:
1. {sp1}
2. {sp2}

请严格按照以上两个卖点生成文案"""

    client = LLMClient()
    content = client.chat(system_prompt=system_prompt, user_prompt=user_prompt)
    return _parse_script(content)


def _parse_script(content):
    """解析 LLM 返回的文案为结构化字典"""
    sections = {"开头": "", "卖点1": "", "卖点2": "", "结尾": ""}
    pattern = re.compile(r'【(开头|卖点1|卖点2|结尾)】\s*(.*?)(?=【|$)', re.DOTALL)
    matches = pattern.findall(content)

    if not matches:
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        keys = list(sections.keys())
        for i, line in enumerate(lines):
            if i < len(keys):
                clean = re.sub(r'[【】\[\]]', '', line)
                for k in keys:
                    if k in clean:
                        clean = clean.replace(k, '', 1).strip()
                        sections[k] = clean
                        break
                else:
                    sections[keys[i]] = line
    else:
        for key, text in matches:
            sections[key] = text.strip()

    for key in sections:
        if not sections[key].strip():
            sections[key] = _fallback_text(key)

    return sections


def _fallback_text(section_key):
    """当某个段落为空时提供默认文本"""
    fallbacks = {
        "开头": "来看看这款钢制家具！",
        "卖点1": "品质设计，经久耐用。",
        "卖点2": "细节考究，使用更放心。",
        "结尾": "赶快下单吧！",
    }
    return fallbacks.get(section_key, "品质之选。")


def _generate_template(chosen_two, product_name=""):
    """使用预置模板组合生成文案（兜底用）"""
    sp1, sp2 = chosen_two
    prefix = f"{product_name}" if product_name else "钢制家具"

    opening = random.choice(OPENING_TEMPLATES)
    sp1_text = random.choice(SP_TEMPLATES).format(sp=sp1)
    sp2_text = random.choice(SP_TEMPLATES).format(sp=sp2)
    closing = random.choice(CLOSING_TEMPLATES)

    return {
        "开头": opening,
        "卖点1": sp1_text,
        "卖点2": sp2_text,
        "结尾": closing,
    }


def get_all_combinations(selling_points):
    """获取所有不重复的两两卖点组合"""
    return list(combinations(selling_points, 2))


# =====================================================================
# AI 分镜切分
# =====================================================================

SEGMENT_PROMPT = """# 角色
你是一个专业的电商混剪文案分镜师，能够根据用户提供的文案，在不更改原文的基础上，对文案进行精准的分镜切分。

## 技能
### 技能1:分镜切分
1. 接收用户提供的文案
2. 对文案进行逐句分镜切分：每遇到一个空格或标点符号（。！？，、；：）就换行，让每个分句只包含一个短语或分句。

## 限制:
必须严格按照用户提供的原文进行分镜切分，不得更改原文内容。
不得合并相邻分句，每个空格/标点处必须断开。

以下是需要分镜的文案：

【开头】{opening}
【卖点1】{sp1}
【卖点2】{sp2}
【结尾】{closing}

请按以下格式输出分镜结果（每个分句一行）：
【开头】
分句1
分句2
【卖点1】
分句1
分句2
【卖点2】
分句1
分句2
【结尾】
分句1
分句2"""


def split_into_segments(sections):
    """
    使用 AI 对文案进行逐短语分镜切分。

    参数:
        sections: {"开头": "...", "卖点1": "...", "卖点2": "...", "结尾": "..."}

    返回:
        {"开头": ["seg1", "seg2"], "卖点1": [...], "卖点2": [...], "结尾": [...]}
    """
    if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != "your-api-key-here":
        try:
            return _call_ai_segmentation(sections)
        except Exception as e:
            print(f"  [WARNING]  AI 分镜切分失败: {e}")
            print(f"  → 使用默认切分")

    return _default_segmentation(sections)


def _call_ai_segmentation(sections):
    """调用 LLM 进行分镜切分"""
    prompt = SEGMENT_PROMPT.format(
        opening=sections.get("开头", ""),
        sp1=sections.get("卖点1", ""),
        sp2=sections.get("卖点2", ""),
        closing=sections.get("结尾", ""),
    )

    client = LLMClient()
    content = client.chat(
        messages=[
            {"role": "system", "content": "你是一个专业的电商文案分镜师，输出简洁的分镜结果。"},
            {"role": "user", "content": prompt},
        ],
    )
    return _parse_segments(content, sections)


def _parse_segments(content, original_sections):
    """解析 AI 返回的分镜结果为结构化字典"""
    result = {"开头": [], "卖点1": [], "卖点2": [], "结尾": []}
    current_section = None

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        section_match = re.match(r'【(开头|卖点1|卖点2|结尾)】', line)
        if section_match:
            current_section = section_match.group(1)
            text_after = line[line.index("】") + 1:].strip()
            if text_after and current_section in result:
                result[current_section].append(text_after)
            continue
        if current_section and current_section in result:
            if re.match(r'^\d+[.、]', line):
                line = re.sub(r'^\d+[.、]\s*', '', line)
            if line:
                result[current_section].append(line)

    for key in result:
        if not result[key]:
            text = original_sections.get(key, "")
            result[key] = _split_by_punct(text)

    return result


def _split_by_punct(text):
    """按空格和标点符号切分为短语（AI 分镜失败时兜底）"""
    if not text.strip():
        return []
    parts = re.split(r'[。！？，、；：!\?,;:\s]+', text)
    return [p.strip() for p in parts if p.strip()]


def _default_segmentation(sections):
    """默认切分：按空格/标点切分（API 失败时兜底）"""
    result = {}
    for key in ["开头", "卖点1", "卖点2", "结尾"]:
        text = sections.get(key, "")
        result[key] = _split_by_punct(text)
    return result
