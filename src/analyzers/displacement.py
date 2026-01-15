import re
from pathlib import Path
from collections import defaultdict
from typing import List
from ..loader import LessonFile
from ..utils import split_characters, get_similarity

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

def analyze_displacement(lessons: List[LessonFile], project_root: Path):
    """
    分析文本位移/错位情况
    """
    # 预加载全书字符-音节分布以确定“主流读音”
    char_counts = defaultdict(lambda: defaultdict(int))
    
    for lesson in lessons:
        for pair in lesson.pairs:
            p_parts = re.split(r'[-\s]', pair.normalized_pinyin)
            h_chars = split_characters(pair.hanzi)
            
            if len(p_parts) == len(h_chars):
                for c, p in zip(h_chars, p_parts):
                    char_counts[c][p] += 1
            elif len(h_chars) == 1:
                char_counts[h_chars[0]][p_parts[0]] += 1

    main_prons = {c: max(ps.keys(), key=lambda x: ps[x]) for c, ps in char_counts.items()}
    page_map = get_page_map(project_root)
    
    file_severity = []

    for lesson in lessons:
        mismatch_count = 0
        total_chars = 0
        
        try:
            lesson_num = int(re.search(r'lesson-(\d+)', lesson.filename).group(1))
        except:
            lesson_num = 0
            
        for pair in lesson.pairs:
            p_parts = re.split(r'[-\s]', pair.normalized_pinyin)
            h_chars = split_characters(pair.hanzi)
            
            for i, c in enumerate(h_chars):
                total_chars += 1
                if c in main_prons:
                    expected = main_prons[c]
                    actual = p_parts[i] if i < len(p_parts) else ""
                    # 相似度低于 0.6 判定为潜在位移
                    if get_similarity(expected, actual) < 0.6:
                        mismatch_count += 1
        
        mismatch_rate = mismatch_count / total_chars if total_chars > 0 else 0
        file_severity.append({
            "lesson": lesson_num,
            "filename": lesson.filename,
            "page": page_map.get(lesson_num, "?"),
            "mismatch_count": mismatch_count,
            "total_chars": total_chars,
            "mismatch_rate": mismatch_rate
        })

    # 排序
    file_severity.sort(key=lambda x: -x['mismatch_rate'])
    
    print("\n" + "="*80)
    print("错位分析 (Displacement Analysis)")
    print("="*80)
    print(f"{'课号':<6} | {'页码':<8} | {'错位率':<8} | {'不匹配数':<8} | {'文件名'}")
    print("-" * 65)
    
    for item in file_severity[:15]: 
        print(f"{item['lesson']:<6} | {item['page']:<8} | {item['mismatch_rate']:<8.1%} | {item['mismatch_count']:<8} | {item['filename']}")
