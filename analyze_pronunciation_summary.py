#!/usr/bin/env python3
"""
生成异常发音的汇总报告（按文件分组）
"""

import re
import json
from pathlib import Path
from collections import defaultdict

def extract_ruby_pairs(content: str, filename: str) -> list:
    pattern = r'#r\("([^"]+)",\s*"([^"]+)"\)'
    matches = re.findall(pattern, content)
    return [(pinyin, hanzi, filename) for pinyin, hanzi in matches]

def normalize_pinyin(pinyin: str) -> str:
    return re.sub(r'[,.\?!;:，。？！；：]+$', '', pinyin).strip().lower()

def split_characters(hanzi: str) -> list[str]:
    chars = []
    for char in hanzi:
        if '\u4e00' <= char <= '\u9fff':
            chars.append(char)
    return chars

def main():
    lessons_dir = Path("/home/drie/下载/Shanghai Dialect Exercises in Romanized and Character with Key to Pronunciation and English Index/typst_source/contents/lessons")
    
    # 第一遍：收集所有发音统计
    char_pronunciations = defaultdict(lambda: defaultdict(list))
    
    for lesson_file in sorted(lessons_dir.glob("lesson-*.typ")):
        content = lesson_file.read_text(encoding='utf-8')
        pairs = extract_ruby_pairs(content, lesson_file.name)
        
        for pinyin, hanzi, filename in pairs:
            chars = split_characters(hanzi)
            pinyin_parts = re.split(r'[-\s]', normalize_pinyin(pinyin))
            
            if len(pinyin_parts) == len(chars):
                for char, py in zip(chars, pinyin_parts):
                    char_pronunciations[char][py].append((filename, hanzi, pinyin))
            elif len(chars) == 1:
                char_pronunciations[chars[0]][normalize_pinyin(pinyin)].append((filename, hanzi, pinyin))
    
    # 确定每个字的主要发音
    main_pronunciations = {}
    for char, pronunciations in char_pronunciations.items():
        if len(pronunciations) >= 1:
            main_py = max(pronunciations.keys(), key=lambda x: len(pronunciations[x]))
            main_pronunciations[char] = (main_py, len(pronunciations[main_py]))
    
    # 第二遍：找出每个文件中的异常
    file_anomalies = defaultdict(list)
    
    for lesson_file in sorted(lessons_dir.glob("lesson-*.typ")):
        content = lesson_file.read_text(encoding='utf-8')
        pairs = extract_ruby_pairs(content, lesson_file.name)
        
        for pinyin, hanzi, filename in pairs:
            chars = split_characters(hanzi)
            pinyin_parts = re.split(r'[-\s]', normalize_pinyin(pinyin))
            
            char_py_pairs = []
            if len(pinyin_parts) == len(chars):
                char_py_pairs = list(zip(chars, pinyin_parts))
            elif len(chars) == 1:
                char_py_pairs = [(chars[0], normalize_pinyin(pinyin))]
            
            for char, py in char_py_pairs:
                if char in main_pronunciations:
                    main_py, main_count = main_pronunciations[char]
                    total = sum(len(occ) for occ in char_pronunciations[char].values())
                    py_count = len(char_pronunciations[char].get(py, []))
                    
                    # 如果主要发音占比>80%且出现>=3次，且当前发音不是主要发音
                    if main_count / total >= 0.8 and total >= 3 and py != main_py:
                        file_anomalies[filename].append({
                            'char': char,
                            'found': py,
                            'expected': main_py,
                            'main_count': main_count,
                            'found_count': py_count,
                            'original_hanzi': hanzi,
                            'original_pinyin': pinyin
                        })
    
    # 输出报告
    print("=" * 100)
    print("上海话练习册 - 按文件分组的异常发音报告")
    print("=" * 100)
    print()
    
    # 按异常数量排序文件
    sorted_files = sorted(file_anomalies.items(), key=lambda x: -len(x[1]))
    
    total_anomalies = sum(len(v) for v in file_anomalies.values())
    print(f"总计发现 {total_anomalies} 处高置信度异常，分布在 {len(file_anomalies)} 个文件中")
    print()
    
    # 高异常率文件（可能需要重点关注）
    print("### 异常数量最多的文件（Top 20）")
    print("-" * 100)
    for filename, anomalies in sorted_files[:20]:
        print(f"\n📁 **{filename}** - {len(anomalies)} 处异常")
        # 按字符分组
        by_char = defaultdict(list)
        for a in anomalies:
            by_char[a['char']].append(a)
        
        for char, items in sorted(by_char.items(), key=lambda x: -len(x[1])):
            first = items[0]
            print(f"  • 「{char}」 期望: {first['expected']}({first['main_count']}次) → 发现: {first['found']}({first['found_count']}次)")
            for item in items[:3]:
                print(f"      #r(\"{item['original_pinyin']}\", \"{item['original_hanzi']}\")")
            if len(items) > 3:
                print(f"      ... 还有 {len(items)-3} 处")
    
    # 生成可操作的修复清单
    print()
    print("=" * 100)
    print("修复建议清单（按文件）")
    print("=" * 100)
    
    for filename, anomalies in sorted_files:
        if len(anomalies) == 0:
            continue
        print(f"\n## {filename}")
        seen = set()
        for a in anomalies:
            key = (a['original_pinyin'], a['original_hanzi'])
            if key not in seen:
                seen.add(key)
                print(f"  #r(\"{a['original_pinyin']}\", \"{a['original_hanzi']}\")")
                print(f"    → 「{a['char']}」应为 {a['expected']} (主流发音，{a['main_count']}次)")

if __name__ == "__main__":
    main()
