#!/usr/bin/env python3
"""
分析上海话练习文件中汉字与发音的一致性
找出同一个汉字有不同发音标注的情况（outlier分析）
"""

import re
import os
from collections import defaultdict
from pathlib import Path

def extract_ruby_pairs(content: str, filename: str) -> list[tuple[str, str, str]]:
    """从Typst内容中提取 #r("拼音", "汉字") 对"""
    # 匹配 #r("拼音", "汉字") 格式
    pattern = r'#r\("([^"]+)",\s*"([^"]+)"\)'
    matches = re.findall(pattern, content)
    # 返回 (拼音, 汉字, 文件名) 三元组
    return [(pinyin, hanzi, filename) for pinyin, hanzi in matches]

def normalize_pinyin(pinyin: str) -> str:
    """标准化拼音（去除标点符号用于比较）"""
    # 去除末尾的标点符号如逗号、句号
    return re.sub(r'[,.\?!;:，。？！；：]+$', '', pinyin).strip().lower()

def split_characters(hanzi: str) -> list[str]:
    """将汉字字符串分割成单个字符（排除标点）"""
    # 匹配中日韩统一表意文字
    chars = []
    for char in hanzi:
        if '\u4e00' <= char <= '\u9fff':  # CJK Unified Ideographs
            chars.append(char)
    return chars

def analyze_pronunciations(lessons_dir: Path) -> dict:
    """分析所有课程文件中的发音"""
    # 字符 -> {发音: [(文件名, 完整汉字, 完整拼音), ...]}
    char_pronunciations = defaultdict(lambda: defaultdict(list))
    
    # 收集所有数据
    all_pairs = []
    
    for lesson_file in sorted(lessons_dir.glob("lesson-*.typ")):
        content = lesson_file.read_text(encoding='utf-8')
        pairs = extract_ruby_pairs(content, lesson_file.name)
        all_pairs.extend(pairs)
        
        for pinyin, hanzi, filename in pairs:
            # 处理多字词
            chars = split_characters(hanzi)
            # 尝试分割拼音（按连字符或空格）
            pinyin_parts = re.split(r'[-\s]', normalize_pinyin(pinyin))
            
            # 如果拼音分割数与字符数匹配，建立对应关系
            if len(pinyin_parts) == len(chars):
                for char, py in zip(chars, pinyin_parts):
                    char_pronunciations[char][py].append((filename, hanzi, pinyin))
            elif len(chars) == 1:
                # 单字情况
                char_pronunciations[chars[0]][normalize_pinyin(pinyin)].append((filename, hanzi, pinyin))
    
    return char_pronunciations, all_pairs

def find_outliers(char_pronunciations: dict) -> list:
    """找出有多种发音的汉字（潜在异常）"""
    outliers = []
    
    for char, pronunciations in char_pronunciations.items():
        if len(pronunciations) > 1:
            # 计算每种发音的出现次数
            counts = {py: len(occurrences) for py, occurrences in pronunciations.items()}
            total = sum(counts.values())
            
            # 找出主要发音（出现次数最多的）
            main_pronunciation = max(counts, key=counts.get)
            main_count = counts[main_pronunciation]
            
            # 收集异常发音（非主要发音）
            outlier_pronunciations = []
            for py, occurrences in pronunciations.items():
                if py != main_pronunciation:
                    outlier_pronunciations.append({
                        'pronunciation': py,
                        'count': len(occurrences),
                        'occurrences': occurrences[:5]  # 最多显示5个例子
                    })
            
            outliers.append({
                'character': char,
                'main_pronunciation': main_pronunciation,
                'main_count': main_count,
                'total_occurrences': total,
                'variant_count': len(pronunciations),
                'outliers': outlier_pronunciations
            })
    
    # 按异常程度排序（变体数量越多越异常）
    outliers.sort(key=lambda x: (-x['variant_count'], -x['total_occurrences']))
    
    return outliers

def main():
    lessons_dir = Path("/home/drie/下载/Shanghai Dialect Exercises in Romanized and Character with Key to Pronunciation and English Index/typst_source/contents/lessons")
    
    print("=" * 80)
    print("上海话练习册 - 汉字发音一致性分析")
    print("=" * 80)
    print()
    
    print("正在分析所有课程文件...")
    char_pronunciations, all_pairs = analyze_pronunciations(lessons_dir)
    
    print(f"共分析 {len(all_pairs)} 个注音对")
    print(f"涉及 {len(char_pronunciations)} 个不同汉字")
    print()
    
    outliers = find_outliers(char_pronunciations)
    
    # 统计
    multi_pronunciation_chars = [o for o in outliers if o['variant_count'] >= 2]
    print(f"发现 {len(multi_pronunciation_chars)} 个汉字有多种发音标注")
    print()
    
    # 分类显示结果
    print("=" * 80)
    print("可能的异常（Outliers）- 同一汉字有不同发音")
    print("=" * 80)
    print()
    
    # 按异常程度分组
    high_priority = []  # 主要发音占比很高，少数异常
    possible_errors = []  # 可能是OCR/转录错误
    legit_variants = []  # 可能是合理的多音字
    
    for outlier in outliers:
        main_ratio = outlier['main_count'] / outlier['total_occurrences']
        
        # 如果主要发音占比超过80%，其他可能是错误
        if main_ratio >= 0.8 and outlier['total_occurrences'] >= 3:
            for ol in outlier['outliers']:
                possible_errors.append({
                    'character': outlier['character'],
                    'expected': outlier['main_pronunciation'],
                    'expected_count': outlier['main_count'],
                    'found': ol['pronunciation'],
                    'found_count': ol['count'],
                    'examples': ol['occurrences']
                })
        elif outlier['variant_count'] <= 3:
            # 可能是合理的多音字或变体
            legit_variants.append(outlier)
        else:
            high_priority.append(outlier)
    
    # 显示高优先级异常
    if possible_errors:
        print("### 高置信度异常（可能是转录错误）")
        print("-" * 80)
        print()
        for i, err in enumerate(possible_errors[:50], 1):
            print(f"{i}. 汉字「{err['character']}」")
            print(f"   主要发音: {err['expected']} (出现 {err['expected_count']} 次)")
            print(f"   异常发音: {err['found']} (出现 {err['found_count']} 次)")
            print(f"   异常位置:")
            for filename, hanzi, pinyin in err['examples']:
                print(f"     - {filename}: #r(\"{pinyin}\", \"{hanzi}\")")
            print()
    
    # 显示多音字情况
    if legit_variants:
        print()
        print("### 多音字/变体情况（可能是正常现象）")
        print("-" * 80)
        print()
        for i, var in enumerate(legit_variants[:30], 1):
            print(f"{i}. 汉字「{var['character']}」 - {var['variant_count']}种发音，共{var['total_occurrences']}次")
            print(f"   主要发音: {var['main_pronunciation']} ({var['main_count']}次)")
            for ol in var['outliers']:
                print(f"   其他发音: {ol['pronunciation']} ({ol['count']}次)")
                for filename, hanzi, pinyin in ol['occurrences'][:2]:
                    print(f"     例: {filename}: #r(\"{pinyin}\", \"{hanzi}\")")
            print()
    
    # 生成JSON报告
    import json
    report = {
        'summary': {
            'total_pairs': len(all_pairs),
            'unique_characters': len(char_pronunciations),
            'multi_pronunciation_chars': len(multi_pronunciation_chars),
            'possible_errors': len(possible_errors)
        },
        'possible_errors': possible_errors,
        'variants': [{
            'character': v['character'],
            'pronunciations': {py: len(occ) for py, occ in char_pronunciations[v['character']].items()}
        } for v in legit_variants]
    }
    
    report_path = lessons_dir.parent.parent / "pronunciation_analysis.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n详细报告已保存到: {report_path}")

if __name__ == "__main__":
    main()
