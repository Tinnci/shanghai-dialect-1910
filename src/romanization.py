"""
上海话罗马化方案转换工具

支持 1910 年教会罗马字 (Church Romanization) 与现代吴语学堂拼音 (Wugniu Pinyin) 之间的转换和相似度比较。

两种方案的主要系统性差异：

声母对应:
| 教会罗马字 | 吴语学堂 | IPA  | 说明 |
|-----------|---------|------|------|
| ny        | gn      | ɲ    | 日母 |
| ng        | ng      | ŋ    | 疑母 |
| dz        | j/z     | dz/z | 从母 |
| ts        | c       | ts   | 精母 |
| tsh       | ch      | tsʰ  | 清母 |
| s         | s/sh    | s/ʃ  | 心母 |
| z         | zh/z    | z    | 邪母 |
| kh        | kh      | kʰ   | 溪母 |
| '         | gh/'    | ʔ    | 影母 |

韵母对应 (入声用 -h vs -q):
| 教会罗马字 | 吴语学堂 | IPA  | 说明 |
|-----------|---------|------|------|
| ih        | iq      | iʔ   | 入声 |
| eh        | eq      | eʔ   | 入声 |
| ah        | aq      | aʔ   | 入声 |
| oh        | oq      | oʔ   | 入声 |
| uh        | uq      | uʔ   | 入声 |
| aung      | aon     | ɔ̃    | 鼻化 |
| ung       | on      | oŋ   | 通摄 |
| oong      | on      | oŋ   | 通摄 |
| eu        | oe      | ø    | 流摄 |
| au        | ao      | ɔ    | 效摄 |
| ieu       | iau     | iɔ   | 效摄 |
"""

import re
from typing import Tuple, List, Set
from dataclasses import dataclass

# ============ 声母映射 ============
# 教会罗马字 -> 吴语学堂 (1:N 映射)
INITIAL_CHURCH_TO_WUGNIU = {
    "ny": ["gn"],
    "ng": ["ng"],
    "dz": ["j", "z", "dz"],
    "ts": ["c", "ts"],
    "tsh": ["ch", "tsh"],
    "s": ["s", "sh"],
    "z": ["z", "zh"],
    "kh": ["kh"],
    "k": ["k", "c"],  # 见母在某些环境下
    "gh": ["gh"],
    "'": ["gh", "'", ""],  # 影母
    "h": ["h", "gh"],
    "m": ["m"],
    "n": ["n"],
    "l": ["l"],
    "v": ["v", "w"],
    "f": ["f"],
    "p": ["p"],
    "ph": ["ph"],
    "b": ["b"],
    "t": ["t"],
    "th": ["th"],
    "d": ["d"],
    "j": ["j", "zh"],
    "ch": ["ch", "q"],
    "sh": ["sh", "x"],
    "": [""],  # 零声母
}

# 吴语学堂 -> 教会罗马字 (反向映射)
INITIAL_WUGNIU_TO_CHURCH = {}
for church, wugnius in INITIAL_CHURCH_TO_WUGNIU.items():
    for w in wugnius:
        if w not in INITIAL_WUGNIU_TO_CHURCH:
            INITIAL_WUGNIU_TO_CHURCH[w] = []
        INITIAL_WUGNIU_TO_CHURCH[w].append(church)

# ============ 韵母映射 ============
# 教会罗马字 -> 吴语学堂
FINAL_CHURCH_TO_WUGNIU = {
    # 入声 (-h -> -q)
    "ih": ["iq", "ieq"],
    "eh": ["eq", "eiq"],
    "ah": ["aq", "ak"],
    "oh": ["oq", "ok"],
    "uh": ["uq", "uk"],
    "iah": ["iaq"],
    "ieh": ["ieq"],
    "ueh": ["ueq"],
    "auh": ["auq"],
    # 鼻化韵
    "aung": ["aon", "an"],
    "ung": ["on", "un"],
    "oong": ["on", "ong"],
    "ang": ["an", "aon"],
    "eng": ["en"],
    "ing": ["in"],
    "ong": ["on", "ong"],
    "iung": ["ion"],
    # 普通韵母
    "eu": ["oe", "eu"],
    "au": ["ao", "au"],
    "iau": ["iau", "iao"],
    "ieu": ["ieu", "ioe"],
    "ou": ["ou", "eu"],
    "oo": ["o", "u"],
    "u": ["u", "oe"],
    "i": ["i", "y"],
    "a": ["a"],
    "e": ["e", "a"],
    "o": ["o", "au"],
    "ai": ["ai", "e"],
    "ei": ["ei", "i"],
    "oi": ["oi", "e"],
    "ui": ["ui", "uei"],
    "ia": ["ia", "ie"],
    "ie": ["ie", "i"],
    "io": ["io", "iau"],
    "iu": ["iu", "ioe"],
    "ua": ["ua", "ue"],
    "ue": ["ue", "uei"],
    "uo": ["uo", "o"],
    "": [""],
}

# ============ 声母列表 (按长度排序) ============
CHURCH_INITIALS = sorted([
    "tsh", "dz", "ts", "ng", "ny", "kh", "ph", "th", "gh", "ch", "sh",
    "k", "h", "m", "n", "l", "v", "f", "p", "b", "t", "d", "s", "z", "j", "'"
], key=lambda x: -len(x))

WUGNIU_INITIALS = sorted([
    "tsh", "dz", "ts", "ng", "gn", "kh", "ph", "th", "gh", "ch", "sh", "zh",
    "k", "h", "m", "n", "l", "v", "w", "f", "p", "b", "t", "d", "s", "z", "j", "c", "q", "x", "'"
], key=lambda x: -len(x))


def split_syllable_church(syllable: str) -> Tuple[str, str]:
    """拆分教会罗马字音节为声母和韵母"""
    syllable = syllable.lower().strip("',.")
    if not syllable:
        return "", ""
    
    for init in CHURCH_INITIALS:
        if syllable.startswith(init):
            return init, syllable[len(init):]
    
    return "", syllable


def split_syllable_wugniu(syllable: str) -> Tuple[str, str]:
    """拆分吴语学堂拼音音节为声母和韵母"""
    syllable = syllable.lower().strip("',.")
    if not syllable:
        return "", ""
    
    for init in WUGNIU_INITIALS:
        if syllable.startswith(init):
            return init, syllable[len(init):]
    
    return "", syllable


def church_to_wugniu_candidates(syllable: str) -> List[str]:
    """
    将教会罗马字转换为可能的吴语学堂拼音候选
    
    Returns:
        可能的吴语学堂拼音列表
    """
    init, final = split_syllable_church(syllable)
    
    init_candidates = INITIAL_CHURCH_TO_WUGNIU.get(init, [init])
    final_candidates = FINAL_CHURCH_TO_WUGNIU.get(final, [final])
    
    # 组合所有可能
    candidates = []
    for i in init_candidates:
        for f in final_candidates:
            candidates.append(i + f)
    
    return candidates


def phonetic_similarity(church_py: str, wugniu_py: str) -> float:
    """
    计算教会罗马字和吴语学堂拼音之间的音系相似度
    
    基于声母和韵母的对应关系给分，而非简单的字符串相似度。
    
    Returns:
        0.0 - 1.0 之间的相似度
    """
    church_init, church_final = split_syllable_church(church_py)
    wugniu_init, wugniu_final = split_syllable_wugniu(wugniu_py)
    
    # 声母匹配分数
    init_score = 0.0
    expected_wugniu_inits = INITIAL_CHURCH_TO_WUGNIU.get(church_init, [])
    if wugniu_init in expected_wugniu_inits:
        init_score = 1.0
    elif wugniu_init == church_init:
        init_score = 0.8  # 相同但不一定是标准对应
    else:
        # 检查是否有部分匹配
        for exp in expected_wugniu_inits:
            if exp and wugniu_init and (exp[0] == wugniu_init[0]):
                init_score = 0.5
                break
    
    # 韵母匹配分数
    final_score = 0.0
    expected_wugniu_finals = FINAL_CHURCH_TO_WUGNIU.get(church_final, [])
    if wugniu_final in expected_wugniu_finals:
        final_score = 1.0
    elif wugniu_final == church_final:
        final_score = 0.8
    else:
        # 入声对应检查 (-h <-> -q)
        if church_final.endswith('h') and wugniu_final.endswith('q'):
            if church_final[:-1] == wugniu_final[:-1]:
                final_score = 0.9
        # 部分匹配
        elif church_final and wugniu_final:
            # 主元音相同
            vowels_church = re.sub(r'[^aeiou]', '', church_final)
            vowels_wugniu = re.sub(r'[^aeiou]', '', wugniu_final)
            if vowels_church and vowels_wugniu and vowels_church[0] == vowels_wugniu[0]:
                final_score = 0.5
    
    # 综合分数 (声母和韵母各占一半)
    return (init_score + final_score) / 2


def are_phonetically_equivalent(church_py: str, wugniu_py: str, threshold: float = 0.7) -> bool:
    """
    判断教会罗马字和吴语学堂拼音是否音系等价
    """
    return phonetic_similarity(church_py, wugniu_py) >= threshold


# ============ 测试 ============
if __name__ == "__main__":
    test_pairs = [
        ("nyih", "gniq"),   # 日 (应该高度相似)
        ("zeh", "zeq"),     # 日 (另一读音)
        ("la", "la"),       # 拉 (完全相同)
        ("leh", "laq"),     # 拉 (入声变体)
        ("tshang", "chan"), # 长
        ("dzoong", "jon"),  # 从
        ("aung", "aon"),    # 鼻化韵
        ("kuh", "keq"),     # 个
        ("nyung", "gnin"),  # 人
    ]
    
    print("教会罗马字 vs 吴语学堂拼音 相似度测试:")
    print("=" * 60)
    for church, wugniu in test_pairs:
        sim = phonetic_similarity(church, wugniu)
        candidates = church_to_wugniu_candidates(church)
        print(f"{church:10} <-> {wugniu:10} | 相似度: {sim:.2f} | 候选: {candidates[:3]}")
