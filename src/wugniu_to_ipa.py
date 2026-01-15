"""
吴语学堂拼音到 IPA 转换器 (Wugniu to IPA Converter)

用于将 Rime 词典中的吴语学堂拼音转换为国际音标 (IPA)，
以便用于 TTS 模型训练。

基于吴语学堂拼音方案的音系规则。
"""

import re
from typing import Tuple

# ============================================================================
# 声母映射 (Initials)
# ============================================================================
WUGNIU_INITIALS_TO_IPA = {
    # 塞音
    "p": "p",
    "ph": "pʰ",
    "b": "b",
    "t": "t",
    "th": "tʰ",
    "d": "d",
    "k": "k",
    "kh": "kʰ",
    "g": "ɡ",
    # 塞擦音
    "ts": "ts",
    "tsh": "tsʰ",
    "c": "ts",
    "ch": "tsʰ",
    "j": "dz",
    "dz": "dz",
    "q": "tɕ",
    "x": "ɕ",
    # 鼻音
    "m": "m",
    "n": "n",
    "ng": "ŋ",
    "gn": "ɲ",
    "ny": "ɲ",
    # 边音/擦音
    "l": "l",
    "f": "f",
    "v": "v",
    "s": "s",
    "sh": "ɕ",
    "z": "z",
    "zh": "ʑ",
    "h": "h",
    "gh": "ɦ",
    # 半元音
    "w": "w",
    "y": "j",
    # 零声母 (用于以元音开头的音节)
    "'": "ʔ",
    "": "",
}

# ============================================================================
# 韵母映射 (Finals)
# ============================================================================
WUGNIU_FINALS_TO_IPA = {
    # 单元音
    "a": "a",
    "o": "o",
    "e": "e",
    "i": "i",
    "u": "u",
    "oe": "ø",
    "y": "y",
    "r": "z̩",  # 舌尖元音
    # 复韵母
    "ae": "ɛ",
    "au": "ɔ",
    "ao": "ɔ",
    "eu": "ɤ",
    "ou": "əu",
    "iu": "iɤ",
    "ui": "ui",
    "ia": "ia",
    "ie": "ie",
    "io": "io",
    "ua": "ua",
    "uo": "uo",
    "ue": "ye",
    "ioe": "yø",
    # 鼻韵母
    "an": "ã",
    "en": "ən",
    "in": "in",
    "on": "oŋ",
    "un": "uŋ",
    "aon": "ɑ̃",
    "iaon": "jɑ̃",  # 以 i 开头的鼻韵母
    "ion": "ioŋ",
    "ien": "iẽ",
    "uan": "uã",
    # 入声韵 (-q 结尾，表示喉塞音)
    "aq": "aʔ",
    "eq": "əʔ",
    "iq": "iʔ",
    "oq": "oʔ",
    "uq": "uʔ",
    "oeq": "øʔ",
    "aeq": "ɛʔ",
    "auq": "ɔʔ",
    "aoq": "ɔʔ",
    "iaq": "iaʔ",
    "ieq": "ieʔ",
    "ioq": "ioʔ",
    "uaq": "uaʔ",
    "ioeq": "yøʔ",
}

# 声母列表 (按长度排序，优先匹配长的)
_INITIALS_SORTED = sorted(
    [k for k in WUGNIU_INITIALS_TO_IPA.keys() if k], key=lambda x: -len(x)
)


def split_wugniu_syllable(syllable: str) -> Tuple[str, str]:
    """
    将吴语学堂拼音音节分离为声母和韵母。

    Args:
        syllable: 吴语学堂拼音音节

    Returns:
        (initial, final) 声母和韵母
    """
    syllable = syllable.lower().strip()
    if not syllable:
        return "", ""

    # 尝试匹配声母
    for init in _INITIALS_SORTED:
        if syllable.startswith(init):
            return init, syllable[len(init) :]

    # 无声母 (零声母)
    return "", syllable


def wugniu_to_ipa(syllable: str) -> str:
    """
    将单个吴语学堂拼音音节转换为 IPA。

    Args:
        syllable: 吴语学堂拼音音节 (如 "zaon", "gnoq", "tshae")

    Returns:
        IPA 转写 (如 "zɑ̃", "ɲoʔ", "tsʰa")
    """
    syllable = syllable.lower().strip()
    if not syllable:
        return ""

    # 分离声母和韵母
    initial, final = split_wugniu_syllable(syllable)

    # 转换声母
    ipa_initial = WUGNIU_INITIALS_TO_IPA.get(initial, initial)

    # 转换韵母
    # 先尝试完整匹配，再尝试逐步缩短匹配
    ipa_final = ""
    remaining = final

    # 尝试完整匹配
    if final in WUGNIU_FINALS_TO_IPA:
        ipa_final = WUGNIU_FINALS_TO_IPA[final]
    else:
        # 尝试从最长到最短匹配
        for length in range(len(final), 0, -1):
            substr = final[:length]
            if substr in WUGNIU_FINALS_TO_IPA:
                ipa_final = WUGNIU_FINALS_TO_IPA[substr]
                remaining = final[length:]
                break

        # 如果有剩余部分，递归处理或直接拼接
        if remaining and remaining != final:
            ipa_final += remaining
        elif not ipa_final:
            # 未找到匹配，直接使用原文
            ipa_final = final

    return ipa_initial + ipa_final


def text_to_ipa_wugniu(text: str) -> str:
    """
    将包含多个吴语学堂拼音音节的文本转换为 IPA。

    音节之间用空格分隔。

    Args:
        text: 吴语学堂拼音文本 (如 "ngu iaon maq zi")

    Returns:
        IPA 转写 (如 "ŋu jɑ̃ maʔ zi")
    """
    syllables = text.strip().split()
    ipa_parts = [wugniu_to_ipa(s) for s in syllables]
    return " ".join(ipa_parts)


def hanzi_to_ipa(
    hanzi: str,
    char_pinyins: dict,
    phrase_pinyins: dict = None,
) -> Tuple[str, float]:
    """
    将汉字文本转换为 IPA。

    Args:
        hanzi: 汉字文本
        char_pinyins: 单字拼音字典 (来自 rime_dict)
        phrase_pinyins: 词组拼音字典 (可选)

    Returns:
        (ipa_text, coverage) IPA 转写和覆盖率
    """
    result = []
    total_chars = 0
    covered_chars = 0

    # 简单处理：逐字转换
    for char in hanzi:
        # 跳过空白和标点
        if char.isspace():
            result.append(" ")
            continue
        if not char.strip() or re.match(r"[，。！？、；：" "''（）]", char):
            continue

        total_chars += 1

        # 查找拼音
        variants = char_pinyins.get(char, set())
        if variants:
            # 取第一个变体 (TODO: 更智能的消歧)
            wugniu = list(variants)[0]
            ipa = wugniu_to_ipa(wugniu)
            result.append(ipa)
            covered_chars += 1
        else:
            # 未找到，保留原字符
            result.append(char)

    coverage = covered_chars / total_chars if total_chars > 0 else 0.0
    return " ".join(result), coverage


# ============================================================================
# 测试
# ============================================================================
if __name__ == "__main__":
    # 测试音节转换
    test_syllables = [
        ("ngu", "ŋu"),  # 我
        ("iaon", "jɑ̃"),  # 要 (预期可能略有不同)
        ("maq", "maʔ"),  # 买
        ("zi", "zi"),  # 子
        ("gnoq", "ɲoʔ"),  # 日
        ("tshae", "tsʰa"),  # 菜 (预期 tsʰa + e)
        ("zaon", "zɑ̃"),  # 上
    ]

    print("=" * 50)
    print("吴语学堂拼音 -> IPA 转换测试")
    print("=" * 50)

    for wugniu, expected in test_syllables:
        ipa = wugniu_to_ipa(wugniu)
        status = "✓" if ipa == expected else "≈"
        print(f"  {status} {wugniu:10} -> {ipa:10} (expected: {expected})")

    # 测试整句转换
    print("\n" + "=" * 50)
    print("整句转换测试")
    print("=" * 50)

    test_sentences = [
        "ngu iaon maq zi",
        "zaon he nin hau",
    ]

    for sent in test_sentences:
        ipa = text_to_ipa_wugniu(sent)
        print(f"  {sent}")
        print(f"  -> {ipa}")
        print()
