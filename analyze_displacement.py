#!/usr/bin/env python3
import re
import json
from pathlib import Path
from collections import defaultdict

def extract_ruby_pairs(content):
    pattern = r'#r\("([^"]+)",\s*"([^"]+)"\)'
    return re.findall(pattern, content)

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2): return levenshtein_distance(s2, s1)
    if not s2: return len(s1)
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

def get_similarity(p1, p2):
    dist = levenshtein_distance(p1, p2)
    max_len = max(len(p1), len(p2), 1)
    return 1 - (dist / max_len)

def get_page_map():
    page_index_path = Path("/home/drie/下载/Shanghai Dialect Exercises in Romanized and Character with Key to Pronunciation and English Index/digitized/PAGE_INDEX.md")
    content = page_index_path.read_text(encoding='utf-8')
    page_map = {}
    
    # 匹配表格中的行 | 页码 | 课号 | ...
    # 适应不同的表格格式
    pattern = r'\| ([\d-]+) \| ([\d,\s-]+) \|'
    matches = re.finditer(pattern, content)
    for m in matches:
        pages = m.group(1).strip()
        lessons_raw = m.group(2).strip()
        # 处理课程号，如 "1-2" 或 "2-3" 或 "5"
        lesson_parts = re.split(r'[-\s,]+', lessons_raw)
        for lp in lesson_parts:
            if lp.isdigit():
                page_map[int(lp)] = pages
    return page_map

def main():
    lessons_dir = Path("/home/drie/下载/Shanghai Dialect Exercises in Romanized and Character with Key to Pronunciation and English Index/typst_source/contents/lessons")
    
    # 预加载全书字符-音节分布以确定“主流读音”
    char_counts = defaultdict(lambda: defaultdict(int))
    all_files_data = {}
    
    for f in sorted(lessons_dir.glob("lesson-*.typ")):
        content = f.read_text(encoding='utf-8')
        pairs = extract_ruby_pairs(content)
        all_files_data[f.name] = pairs
        for pinyin, hanzi in pairs:
            p_parts = re.split(r'[-\s]', pinyin.lower().strip())
            h_chars = [c for c in hanzi if '\u4e00' <= c <= '\u9fff']
            if len(p_parts) == len(h_chars):
                for c, p in zip(h_chars, p_parts):
                    char_counts[c][p] += 1
            elif len(h_chars) == 1:
                char_counts[h_chars[0]][p_parts[0]] += 1

    main_prons = {c: max(ps.keys(), key=lambda x: ps[x]) for c, ps in char_counts.items()}
    page_map = get_page_map()
    
    file_severity = []

    for fname, pairs in all_files_data.items():
        mismatch_count = 0
        total_chars = 0
        lesson_num = int(re.search(r'lesson-(\d+)', fname).group(1))
        
        for pinyin, hanzi in pairs:
            p_parts = re.split(r'[-\s]', pinyin.lower().strip().replace('"', ''))
            h_chars = [c for c in hanzi if '\u4e00' <= c <= '\u9fff']
            
            for i, c in enumerate(h_chars):
                total_chars += 1
                if c in main_prons:
                    expected = main_prons[c]
                    # 如果当前对齐的音节与期望音节相似度低于 0.6，判定为潜在位移
                    actual = p_parts[i] if i < len(p_parts) else ""
                    if get_similarity(expected, actual) < 0.6:
                        mismatch_count += 1
        
        mismatch_rate = mismatch_count / total_chars if total_chars > 0 else 0
        file_severity.append({
            "lesson": lesson_num,
            "filename": fname,
            "page": page_map.get(lesson_num, "Unknown"),
            "mismatch_count": mismatch_count,
            "total_chars": total_chars,
            "mismatch_rate": round(mismatch_rate, 3)
        })

    # 排序：按错位率降序
    file_severity.sort(key=lambda x: -x['mismatch_rate'])
    
    print(f"{'课号':<5} | {'页码':<8} | {'错位率':<8} | {'不匹配数':<8} | {'文件名'}")
    print("-" * 60)
    for item in file_severity[:20]: # 显示前20个最严重的
        print(f"{item['lesson']:<5} | {item['page']:<8} | {item['mismatch_rate']:<8.1%} | {item['mismatch_count']:<8} | {item['filename']}")

if __name__ == "__main__":
    main()
