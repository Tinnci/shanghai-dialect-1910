"""
平行语料提取与规则学习工具

从本书的 Ruby 对和 Rime 词典中提取平行语料，自动学习转换规则。
"""

import re
from pathlib import Path
from typing import List, Tuple, Set

try:
    from .loader import load_lessons
    from .rime_dict import get_rime_data
    from .rule_induction import RuleInductionEngine, phonetic_feature_similarity
except ImportError:
    from loader import load_lessons
    from rime_dict import get_rime_data
    from rule_induction import RuleInductionEngine, phonetic_feature_similarity


def extract_parallel_corpus(lessons_dir: Path) -> List[Tuple[str, str, str]]:
    """
    从本书中提取平行语料

    返回: [(church_pinyin, wugniu_pinyin, hanzi), ...]
    """
    lessons = load_lessons(lessons_dir)
    char_pinyins, _, _ = get_rime_data()

    parallel_pairs = []

    for lesson in lessons:
        for pair in lesson.pairs:
            pinyin = pair.pinyin.lower().strip("',.-")
            hanzi = pair.hanzi

            # 分割多音节
            py_parts = re.split(r"[-\s]", pinyin)
            hz_chars = list(hanzi)

            # 只处理长度匹配的
            if len(py_parts) == len(hz_chars):
                for church_py, char in zip(py_parts, hz_chars):
                    if char in char_pinyins:
                        # 找到最匹配的 Rime 读音
                        wugniu_variants = char_pinyins[char]
                        best_match = find_best_match(church_py, wugniu_variants)
                        if best_match:
                            parallel_pairs.append((church_py, best_match, char))

    return parallel_pairs


def find_best_match(church_py: str, wugniu_variants: Set[str]) -> str:
    """找到与教会罗马字最匹配的吴语学堂拼音"""
    best_sim = 0
    best_match = ""

    for variant in wugniu_variants:
        # 简单的字符相似度 + 音韵特征相似度
        sim = calculate_similarity(church_py, variant)
        if sim > best_sim:
            best_sim = sim
            best_match = variant

    return best_match if best_sim > 0.5 else ""


def calculate_similarity(church_py: str, wugniu_py: str) -> float:
    """计算两个拼音的相似度"""
    # 分离声母韵母
    c_init, c_final = split_syllable(church_py, is_wugniu=False)
    w_init, w_final = split_syllable(wugniu_py, is_wugniu=True)

    # 使用音韵特征相似度
    return phonetic_feature_similarity(c_init, c_final, w_init, w_final)


def split_syllable(syllable: str, is_wugniu: bool = False) -> Tuple[str, str]:
    """分离声母和韵母"""
    syllable = syllable.lower().strip("',.-")
    if not syllable:
        return "", ""

    if is_wugniu:
        initials = [
            "tsh",
            "dz",
            "ts",
            "ng",
            "gn",
            "kh",
            "ph",
            "th",
            "gh",
            "ch",
            "sh",
            "zh",
            "k",
            "h",
            "m",
            "n",
            "l",
            "v",
            "w",
            "f",
            "p",
            "b",
            "t",
            "d",
            "s",
            "z",
            "j",
            "c",
            "q",
            "x",
            "y",
            "'",
            "lh",
        ]
    else:
        initials = [
            "tsh",
            "dz",
            "ts",
            "ng",
            "ny",
            "kh",
            "ph",
            "th",
            "gh",
            "ch",
            "sh",
            "ky",
            "hy",
            "kw",
            "gw",
            "hw",
            "k",
            "h",
            "m",
            "n",
            "l",
            "v",
            "w",
            "f",
            "p",
            "b",
            "t",
            "d",
            "s",
            "z",
            "j",
            "y",
            "'",
            "'v",
        ]

    for init in sorted(initials, key=lambda x: -len(x)):
        if syllable.startswith(init):
            return init, syllable[len(init) :]

    return "", syllable


def learn_rules_from_corpus(lessons_dir: Path):
    """从语料中学习规则"""
    print("=" * 70)
    print("平行语料规则学习 (Parallel Corpus Rule Learning)")
    print("=" * 70)

    # 提取平行语料
    print("\n📚 正在提取平行语料...")
    pairs = extract_parallel_corpus(lessons_dir)
    print(f"   提取了 {len(pairs)} 对平行拼音")

    # 学习规则
    engine = RuleInductionEngine()
    for church, wugniu, hanzi in pairs:
        engine.add_parallel_pair(church, wugniu, hanzi)

    # 输出规则
    engine.print_rules_report()

    # 统计
    initial_rules, final_rules = engine.induce_rules()

    print("\n" + "=" * 70)
    print("高置信度规则 (Top Confident Rules)")
    print("=" * 70)

    print("\n声母规则 (出现 >= 10 次):")
    for rule in initial_rules:
        if rule.count >= 10:
            print(f"  ✓ '{rule.source}' → '{rule.target}' (出现 {rule.count} 次)")

    print("\n韵母规则 (出现 >= 10 次):")
    for rule in final_rules:
        if rule.count >= 10:
            print(f"  ✓ '{rule.source}' → '{rule.target}' (出现 {rule.count} 次)")

    return initial_rules, final_rules


if __name__ == "__main__":
    lessons_dir = Path(__file__).parent.parent / "typst_source/contents/lessons"
    learn_rules_from_corpus(lessons_dir)
