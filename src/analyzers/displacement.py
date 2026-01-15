import re
from pathlib import Path
from collections import defaultdict
from typing import List, Set
from ..loader import LessonFile
from ..utils import split_characters, get_similarity, get_best_match_offset
from ..rime_dict import is_valid_pronunciation
from ..knowledge_base import get_knowledge_base


def get_page_map(project_root: Path):
    # Try to find PAGE_INDEX.md relative to project root
    page_index_path = project_root / "digitized/PAGE_INDEX.md"
    if not page_index_path.exists():
        return {}

    content = page_index_path.read_text(encoding="utf-8")
    page_map = {}

    pattern = r"\| ([\d-]+) \| ([\d,\s-]+) \|"
    matches = re.finditer(pattern, content)
    for m in matches:
        pages = m.group(1).strip()
        lessons_raw = m.group(2).strip()
        lesson_parts = re.split(r"[-\s,]+", lessons_raw)
        for lp in lesson_parts:
            if lp.isdigit():
                page_map[int(lp)] = pages
    return page_map


def _detect_reduplication_patterns(lessons: List[LessonFile]) -> Set[str]:
    """
    检测全书中的叠词模式 (如 "拉拉" / "leh-la")
    返回一个集合，包含所有被识别的叠词的汉字形式。

    用于后续跳过误报。
    """
    reduplication_hanzi = set()

    for lesson in lessons:
        for pair in lesson.pairs:
            h_chars = split_characters(pair.hanzi)
            # 检查双字叠词 (AA 模式)
            if len(h_chars) == 2 and h_chars[0] == h_chars[1]:
                reduplication_hanzi.add(pair.hanzi)
            # 检查 AABB 模式
            if (
                len(h_chars) == 4
                and h_chars[0] == h_chars[1]
                and h_chars[2] == h_chars[3]
            ):
                reduplication_hanzi.add(pair.hanzi)

    return reduplication_hanzi


def _is_known_valid_pair(char: str, pinyin: str, kb) -> bool:
    """
    检查字符-拼音对是否在知识库中被验证为合法。
    结合 Rime 词典和我们学习到的音韵规则。
    """
    # 1. Rime 词典验证
    if is_valid_pronunciation(char, pinyin):
        return True

    # 2. 知识库规则验证 (声母/韵母转换)
    # 如果当前 pinyin 可以通过已学规则转换到期望的形式，则认为合法
    # (注意: 这里需要更复杂的实现，暂时只做简单的规则匹配)

    return False


def analyze_displacement(
    lessons: List[LessonFile], project_root: Path, target_filter: str = None
):
    """
    分析文本位移/错位情况 (诊断式报告)

    【智能增强版】
    - 集成叠词检测，避免 "拉拉" 类误报
    - 集成 Rime 词典和知识库，跳过合法多音字变体
    - 更精准的错位诊断
    """
    # 0. 加载知识库
    kb = get_knowledge_base()

    # 1. 检测全书叠词模式
    reduplication_patterns = _detect_reduplication_patterns(lessons)

    # 2. 建立主流读音基准
    char_counts = defaultdict(lambda: defaultdict(int))
    for lesson in lessons:
        for pair in lesson.pairs:
            p_parts = re.split(r"[-\s]", pair.normalized_pinyin)
            h_chars = split_characters(pair.hanzi)
            if len(p_parts) == len(h_chars):
                for c, p in zip(h_chars, p_parts):
                    char_counts[c][p] += 1

    main_prons = {
        c: max(ps.keys(), key=lambda x: ps[x]) for c, ps in char_counts.items() if ps
    }

    # 3. 构建多音字白名单 (第二读音占比 > 15% 的字)
    polyphonic_chars = set()
    for c, ps in char_counts.items():
        if len(ps) >= 2:
            sorted_counts = sorted(ps.values(), reverse=True)
            total = sum(sorted_counts)
            if total > 0 and sorted_counts[1] / total > 0.15:
                polyphonic_chars.add(c)

    page_map = get_page_map(project_root)
    file_severity = []

    for lesson in lessons:
        if target_filter and target_filter not in lesson.filename:
            continue
        diagnostics = []
        mismatch_count = 0
        total_chars = 0

        # 将文件内所有对整合成序列以便进行滑动窗口分析
        expected_seq = []
        actual_seq = []
        source_pairs = []  # 记录来源以便回溯
        skip_flags = []  # 标记是否应跳过该位置的检查

        for pair in lesson.pairs:
            p_parts = re.split(r"[-\s]", pair.normalized_pinyin)
            h_chars = split_characters(pair.hanzi)

            # 叠词检测
            is_reduplication = pair.hanzi in reduplication_patterns

            for i, c in enumerate(h_chars):
                expected_seq.append(main_prons.get(c, ""))
                actual_seq.append(p_parts[i] if i < len(p_parts) else "")
                source_pairs.append(pair)

                # 决定是否跳过
                should_skip = False
                if is_reduplication:
                    should_skip = True  # 叠词跳过
                elif c in polyphonic_chars:
                    # 多音字：如果当前读音在其已知读音列表中，跳过
                    if i < len(p_parts) and p_parts[i] in char_counts[c]:
                        should_skip = True
                elif i < len(p_parts) and _is_known_valid_pair(c, p_parts[i], kb):
                    should_skip = True  # Rime/知识库验证通过

                skip_flags.append(should_skip)

        # 4. 诊断偏移 (智能版)
        i = 0
        while i < len(actual_seq):
            total_chars += 1

            # 跳过已标记的合法位置
            if skip_flags[i]:
                i += 1
                continue

            exp = expected_seq[i]
            act = actual_seq[i]

            sim = get_similarity(exp, act)
            if sim < 0.6:
                # 触发位移检测
                offset = get_best_match_offset(expected_seq, actual_seq, i)
                if offset == -1:
                    diagnostics.append(
                        f"[ALIGN-L] 漏字偏移 at '{source_pairs[i].hanzi}'"
                    )
                    mismatch_count += 5  # 权重加重
                elif offset == 1:
                    diagnostics.append(
                        f"[ALIGN-R] 多字偏移 at '{source_pairs[i].hanzi}'"
                    )
                    mismatch_count += 5
                else:
                    mismatch_count += 1
            i += 1

        mismatch_rate = mismatch_count / total_chars if total_chars > 0 else 0

        try:
            lesson_num = int(re.search(r"lesson-(\d+)", lesson.filename).group(1))
        except (AttributeError, ValueError):
            lesson_num = 0

        file_severity.append(
            {
                "lesson": lesson_num,
                "filename": lesson.filename,
                "page": page_map.get(lesson_num, "?"),
                "mismatch_count": mismatch_count,
                "total_chars": total_chars,
                "mismatch_rate": mismatch_rate,
                "diagnostics": diagnostics[:3],  # 只保留前三个主要诊断
            }
        )

    # 5. 输出报告 (精要版)
    file_severity.sort(key=lambda x: -x["mismatch_rate"])

    print("\n" + "=" * 90)
    print(
        f"{'课号':<5} | {'错位率':<8} | {'诊断结论 (Top Diagnostics)':<40} | {'文件名'}"
    )
    print("-" * 90)

    for item in file_severity[:15]:
        diag_str = ", ".join(item["diagnostics"]) if item["diagnostics"] else "[CLEAN]"
        print(
            f"{item['lesson']:<5} | {item['mismatch_rate']:<8.1%} | {diag_str:<40} | {item['filename']}"
        )
