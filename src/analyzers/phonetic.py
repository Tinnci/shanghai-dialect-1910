import re
import json
from collections import defaultdict
from typing import List
from ..loader import LessonFile
from ..utils import split_phonetic, get_similarity, split_characters


def analyze_phonetic_consistency(
    lessons: List[LessonFile], output_json: str = "phonetic_analysis.json"
):
    """
    高级上海话音韵一致性分析
    """
    # 1. 数据收集
    # word_stats: {汉字词: {拼音: [位置信息]}}
    word_stats = defaultdict(lambda: defaultdict(list))
    # char_stats: {单汉字: {音节: [位置信息]}}
    char_stats = defaultdict(lambda: defaultdict(list))

    for lesson in lessons:
        for pair in lesson.pairs:
            p_norm = pair.normalized_pinyin
            hanzi = pair.hanzi
            fname = lesson.filename

            h_chars = split_characters(hanzi)
            if not h_chars:
                continue

            # 记录整词
            word_stats[hanzi][p_norm].append((fname, pair.pinyin))

            # 记录单字
            p_parts = re.split(r"[-\s]", p_norm)
            if len(h_chars) == len(p_parts):
                for char, py in zip(h_chars, p_parts):
                    char_stats[char][py].append((fname, pair.pinyin, hanzi))
            elif len(h_chars) == 1:
                char_stats[h_chars[0]][p_norm].append((fname, pair.pinyin, hanzi))

    # 2. 异常分析
    report = {
        "typos": [],  # 疑似手误
        "variants": [],  # 语音变体
        "mismatches": [],  # 严重不匹配
    }

    for char, prons in char_stats.items():
        if len(prons) <= 1:
            continue

        main_py = max(prons.keys(), key=lambda k: len(prons[k]))
        main_count = len(prons[main_py])

        for py, occurrences in prons.items():
            if py == main_py:
                continue

            similarity = get_similarity(main_py, py)
            count = len(occurrences)

            info = {
                "char": char,
                "main": main_py,
                "main_count": main_count,
                "alt": py,
                "alt_count": count,
                "similarity": round(similarity, 2),
                "examples": occurrences[:3],
            }

            if similarity >= 0.7:
                if count <= 2:
                    report["typos"].append(info)
                else:
                    init1, fin1 = split_phonetic(main_py)
                    init2, fin2 = split_phonetic(py)
                    info["init_match"] = init1 == init2
                    info["fin_match"] = fin1 == fin2
                    report["variants"].append(info)
            else:
                report["mismatches"].append(info)

    # 3. 输出报告
    print("=" * 80)
    print("音韵一致性分析报告")
    print("=" * 80)

    print(f"\n[!] 发现 {len(report['typos'])} 处疑似手误 (高相似度，低频)")
    for item in sorted(report["typos"], key=lambda x: -x["similarity"])[:10]:
        print(
            f"  - 「{item['char']}」: {item['main']} → {item['alt']} ({item['alt_count']}次) | Sim: {item['similarity']}"
        )
        ex = item["examples"][0]
        print(f'    位置: {ex[0]}: #r("{ex[1]}", "{ex[2]}")')

    print(f"\n[~] 发现 {len(report['variants'])} 处语音变体")
    patterns = defaultdict(int)
    for v in report["variants"]:
        patterns[f"{v['main']} -> {v['alt']}"] += v["alt_count"]

    sorted_patterns = sorted(patterns.items(), key=lambda x: -x[1])
    for pat, freq in sorted_patterns[:5]:
        print(f"  - 模式 {pat}: {freq} 次")

    print(f"\n[X] 发现 {len(report['mismatches'])} 处严重不匹配")
    for item in sorted(report["mismatches"], key=lambda x: x["similarity"])[:5]:
        print(f"  - 「{item['char']}」: {item['main']} → {item['alt']}")

    # 保存 JSON
    with open(output_json, "w", encoding="utf-8") as jf:
        json.dump(report, jf, ensure_ascii=False, indent=2)
    print(f"\n完整报告已保存至: {output_json}")
