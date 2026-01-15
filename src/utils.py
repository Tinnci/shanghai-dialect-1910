import re
from typing import List, Tuple

# 上海话罗马字声母表 (按长度倒序排序以优先匹配长声母)
INITIALS = [
    "ph",
    "th",
    "kh",
    "tsh",
    "dz",
    "dj",
    "ts",
    "ky",
    "kyi",
    "ny",
    "ng",
    "sh",
    "sz",
    "v",
    "z",
    "gh",
    "h",
    "l",
    "n",
    "m",
    "p",
    "t",
    "k",
    "b",
    "d",
    "g",
    "f",
    "s",
    "y",
    "w",
    "j",
]
INITIALS.sort(key=len, reverse=True)


def extract_ruby_pairs(content: str, filename: str) -> List[Tuple[str, str, str, int]]:
    """
    提取文件中的 #r("拼音", "汉字") 对
    返回: List[(拼音, 汉字, 文件名, 字符位置)]
    """
    pattern = r'#r\("([^"]+)",\s*"([^"]+)"\)'
    matches = re.finditer(pattern, content)
    return [(m.group(1), m.group(2), filename, m.start()) for m in matches]


def normalize_pinyin(pinyin: str) -> str:
    """标准化拼音（去除标点符号用于比较）"""
    return re.sub(r"[,.\?!;:，。？！；：]+$", "", pinyin).strip().lower()


def split_characters(hanzi: str) -> List[str]:
    """将汉字字符串分割成单个字符（排除标点）"""
    chars = []
    for char in hanzi:
        if "\u4e00" <= char <= "\u9fff":
            chars.append(char)
    return chars


def split_phonetic(syllable: str) -> Tuple[str, str]:
    """将单音节拆分为声母和韵母"""
    syllable = syllable.lower().strip("'")
    if not syllable:
        return "", ""

    for init in INITIALS:
        if syllable.startswith(init):
            return init, syllable[len(init) :]

    return "", syllable


def levenshtein_distance(s1: str, s2: str) -> int:
    """计算简易编辑距离"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if not s2:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def get_similarity(p1: str, p2: str) -> float:
    if not p1 and not p2:
        return 1.0
    if not p1 or not p2:
        return 0.0
    dist = levenshtein_distance(p1, p2)
    max_len = max(len(p1), len(p2), 1)
    return 1 - (dist / max_len)


def get_best_match_offset(
    expected_list: List[str], actual_list: List[str], current_idx: int, window: int = 3
) -> int:
    """
    在窗口内寻找最佳匹配偏移量。
    返回偏移量: -1 (漏字), 0 (匹配), 1 (多字)
    """
    if current_idx >= len(actual_list) or current_idx >= len(expected_list):
        return 0

    current_sim = get_similarity(expected_list[current_idx], actual_list[current_idx])
    if current_sim > 0.7:
        return 0  # 匹配良发

    # 尝试检测漏字 (实际落后于期望)
    # Expected: [A, B, C]
    # Actual:   [A, C] -> 在 idx 1, Actual[1]('C') 匹配 Expected[2]('C')
    if current_idx + 1 < len(expected_list):
        lookahead_sim = get_similarity(
            expected_list[current_idx + 1], actual_list[current_idx]
        )
        if lookahead_sim > 0.8:
            return -1  # 期望序列领先，说明实际可能漏了一个词

    # 尝试检测多字 (实际领先于期望)
    # Expected: [A, C]
    # Actual:   [A, B, C] -> 在 idx 1, Actual[2]('C') 匹配 Expected[1]('C')
    if current_idx + 1 < len(actual_list):
        lookbehind_sim = get_similarity(
            expected_list[current_idx], actual_list[current_idx + 1]
        )
        if lookbehind_sim > 0.8:
            return 1  # 实际序列领先，说明实际可能多了一个词

    return 0
