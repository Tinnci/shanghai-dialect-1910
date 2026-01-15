"""
上海话罗马化方案转换工具

支持 1910 年教会罗马字 (Church Romanization) 与现代吴语学堂拼音 (Wugniu Pinyin) 之间的转换和相似度比较。

==============================================================================
教会罗马字规则来源: preliminary.typ (Key to the Pronunciation)
==============================================================================

声母对应 (Initials):
| 教会罗马字 | 吴语学堂 | IPA  | 说明 |
|-----------|---------|------|------|
| ny        | gn      | ɲ    | 日母 ("ni" in spaniel) |
| ng        | ng      | ŋ    | 疑母 |
| ky        | c/j     | tɕ   | 见母腭化 ("ch" without aspiration) |
| ch        | ch/q    | tɕʰ  | 清母送气 ("ch" in church) |
| hy        | sh/x    | ɕ    | 晓母腭化 ("ti" in Portia) |
| tsh       | tsh/ch  | tsʰ  | 清母送气 |
| dz        | j/z/dz  | dz   | 从母 |
| ts        | ts/c    | ts   | 精母 |
| th        | th      | tʰ   | 透母 ("th" in Thomas, NOT thing!) |
| kh        | kh      | kʰ   | 溪母 |
| kwh       | khw     | kʷʰ  | 溪母合口 |
| 'v        | v/w     | v    | 微母 (高调) |
| v         | v/w     | v    | 微母 (低调) |
| j         | j/zh    | dʑ   | 日母 (低调) |
| gw        | ghw     | ɡʷ   | 群母合口 |

韵母对应 (Finals - 入声用 -h/-k vs -q):
| 教会罗马字 | 吴语学堂 | IPA  | 说明 |
|-----------|---------|------|------|
| ah        | aq      | aʔ   | 入声 ("a" in at) |
| ak        | aq      | aʔ   | 入声 ("a" in what) |
| eh        | eq      | eʔ   | 入声 ("e" in let) |
| ih        | iq      | iʔ   | 入声 |
| oh        | oq      | oʔ   | 入声 |
| uh        | uq      | uʔ   | 入声 |
| auh       | auq     | ɔʔ   | 入声 |
| oeh       | oeq     | øʔ   | 入声 |
| iah       | iaq     | iaʔ  | 入声 |
| iak       | iaq     | iaʔ  | 入声 |
| aung      | aon     | ɔ̃    | 鼻化韵 ("ng" in song) |
| ang       | an/aon  | ã/ɔ̃  | 鼻化韵 ("a" in far + ng) |
| oong      | on      | oŋ   | 通摄 ("o" in bone + ng) |
| ung       | on/un   | oŋ   | 通摄 |
| oe        | oe      | ø    | 遇摄 (German ö) |
| eu        | oe/eu   | ø    | 流摄 (French "eu" in Monsieur) |

特殊说明:
- "leh-la" (拉拉) 中的 "leh" 实际是入声 leq (勒)，表示进行态
- 入声 -h/-k 结尾表示喉塞尾 /-ʔ/，元音突然结束
"""

import re
from typing import Tuple, List, Set
from dataclasses import dataclass

# ============ 声母映射 ============
# 教会罗马字 -> 吴语学堂 (1:N 映射)
INITIAL_CHURCH_TO_WUGNIU = {
    # 日母
    "ny": ["gn", "ni"],
    # 疑母
    "ng": ["ng"],
    # 见系
    "ky": ["c", "j", "ci"],      # 见母腭化
    "ch": ["ch", "q", "tsh"],    # 清母送气
    "hy": ["sh", "x", "hi"],     # 晓母腭化
    "kh": ["kh"],
    "kwh": ["khw", "khu"],
    "kw": ["kw", "ku", "gw"],
    "k": ["k", "c"],
    "gw": ["ghw", "gu"],
    "g": ["g", "gh"],
    # 精系
    "tsh": ["tsh", "ch"],
    "ts": ["ts", "c"],
    "dz": ["j", "z", "dz"],
    "s": ["s", "sh"],
    "z": ["z", "zh"],
    # 端系
    "th": ["th"],
    "t": ["t"],
    "d": ["d"],
    # 帮系
    "ph": ["ph"],
    "p": ["p"],
    "b": ["b"],
    # 微母
    "'v": ["v", "w"],
    "v": ["v", "w"],
    # 其他
    "gh": ["gh"],
    "h": ["h", "gh", "hh"],
    "hw": ["hw", "hu", "f"],
    "f": ["f"],
    "m": ["m"],
    "n": ["n"],
    "l": ["l", "lh"],
    "j": ["j", "zh", "ni"],
    "y": ["y", "ghi", "i"],
    "w": ["w", "ghu", "u", "v"],
    "'": ["gh", "'", "hh", ""],  # 影母/喉塞
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
