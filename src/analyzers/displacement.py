import re
from pathlib import Path
from collections import defaultdict
from typing import List
from ..loader import LessonFile
from ..utils import split_characters, get_similarity, get_best_match_offset

def get_page_map(project_root: Path):
    # Try to find PAGE_INDEX.md relative to project root
    page_index_path = project_root / "digitized/PAGE_INDEX.md"
    if not page_index_path.exists():
        return {}

    content = page_index_path.read_text(encoding='utf-8')
    page_map = {}
    
    pattern = r'\| ([\d-]+) \| ([\d,\s-]+) \|'
    matches = re.finditer(pattern, content)
    for m in matches:
        pages = m.group(1).strip()
        lessons_raw = m.group(2).strip()
        lesson_parts = re.split(r'[-\s,]+', lessons_raw)
        for lp in lesson_parts:
            if lp.isdigit():
                page_map[int(lp)] = pages
    return page_map

def analyze_displacement(lessons: List[LessonFile], project_root: Path, target_filter: str = None):
    """
    分析文本位移/错位情况 (诊断式报告)
    """
    # 1. 建立主流读音基准
    char_counts = defaultdict(lambda: defaultdict(int))
    for lesson in lessons:
        for pair in lesson.pairs:
            p_parts = re.split(r'[-\s]', pair.normalized_pinyin)
            h_chars = split_characters(pair.hanzi)
            if len(p_parts) == len(h_chars):
                for c, p in zip(h_chars, p_parts):
                    char_counts[c][p] += 1

    main_prons = {c: max(ps.keys(), key=lambda x: ps[x]) for c, ps in char_counts.items() if ps}
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
        source_pairs = [] # 记录来源以便回溯

        for pair in lesson.pairs:
            p_parts = re.split(r'[-\s]', pair.normalized_pinyin)
            h_chars = split_characters(pair.hanzi)
            for i, c in enumerate(h_chars):
                expected_seq.append(main_prons.get(c, ""))
                actual_seq.append(p_parts[i] if i < len(p_parts) else "")
                source_pairs.append(pair)

        # 2. 诊断偏移
        i = 0
        while i < len(actual_seq):
            total_chars += 1
            exp = expected_seq[i]
            act = actual_seq[i]
            
            sim = get_similarity(exp, act)
            if sim < 0.6:
                # 触发位移检测
                offset = get_best_match_offset(expected_seq, actual_seq, i)
                if offset == -1:
                    diagnostics.append(f"[ALIGN-L] 漏字偏移 at '{source_pairs[i].hanzi}'")
                    mismatch_count += 5 # 权重加重
                elif offset == 1:
                    diagnostics.append(f"[ALIGN-R] 多字偏移 at '{source_pairs[i].hanzi}'")
                    mismatch_count += 5
                else:
                    mismatch_count += 1
            i += 1
        
        mismatch_rate = mismatch_count / total_chars if total_chars > 0 else 0
        
        try:
            lesson_num = int(re.search(r'lesson-(\d+)', lesson.filename).group(1))
        except (AttributeError, ValueError):
            lesson_num = 0
            
        file_severity.append({
            "lesson": lesson_num,
            "filename": lesson.filename,
            "page": page_map.get(lesson_num, "?"),
            "mismatch_count": mismatch_count,
            "total_chars": total_chars,
            "mismatch_rate": mismatch_rate,
            "diagnostics": diagnostics[:3] # 只保留前三个主要诊断
        })

    # 3. 输出报告 (精要版)
    file_severity.sort(key=lambda x: -x['mismatch_rate'])
    
    print("\n" + "="*90)
    print(f"{'课号':<5} | {'错位率':<8} | {'诊断结论 (Top Diagnostics)':<40} | {'文件名'}")
    print("-" * 90)
    
    for item in file_severity[:15]:
        diag_str = ", ".join(item['diagnostics']) if item['diagnostics'] else "[CLEAN]"
        print(f"{item['lesson']:<5} | {item['mismatch_rate']:<8.1%} | {diag_str:<40} | {item['filename']}")
