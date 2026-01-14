#!/usr/bin/env python3
"""
生成按异常数量排序的练习文件优先级列表
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
    file_total_pairs = defaultdict(int)
    
    for lesson_file in sorted(lessons_dir.glob("lesson-*.typ")):
        content = lesson_file.read_text(encoding='utf-8')
        pairs = extract_ruby_pairs(content, lesson_file.name)
        file_total_pairs[lesson_file.name] = len(pairs)
        
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
            main_count = len(pronunciations[main_py])
            total = sum(len(occ) for occ in pronunciations.values())
            main_pronunciations[char] = (main_py, main_count, total)
    
    # 第二遍：统计每个文件的异常
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
                    main_py, main_count, total = main_pronunciations[char]
                    py_count = len(char_pronunciations[char].get(py, []))
                    
                    # 高置信度异常：主要发音占比>80%，出现>=3次，且当前发音不是主要发音
                    if main_count / total >= 0.8 and total >= 3 and py != main_py:
                        file_anomalies[filename].append({
                            'char': char,
                            'found': py,
                            'expected': main_py,
                            'main_count': main_count,
                            'found_count': py_count,
                            'original_hanzi': hanzi,
                            'original_pinyin': pinyin,
                            'confidence': main_count / total
                        })
    
    # 计算每个文件的异常率和加权分数
    file_scores = []
    for filename in sorted(lessons_dir.glob("lesson-*.typ")):
        fname = filename.name
        anomalies = file_anomalies.get(fname, [])
        total_pairs = file_total_pairs.get(fname, 1)
        anomaly_count = len(anomalies)
        anomaly_rate = anomaly_count / total_pairs if total_pairs > 0 else 0
        
        # 计算加权分数（考虑异常置信度）
        weighted_score = sum(a['confidence'] for a in anomalies)
        
        # 提取课程编号
        lesson_num = int(re.search(r'lesson-(\d+)', fname).group(1))
        
        file_scores.append({
            'filename': fname,
            'lesson_num': lesson_num,
            'anomaly_count': anomaly_count,
            'total_pairs': total_pairs,
            'anomaly_rate': anomaly_rate,
            'weighted_score': weighted_score,
            'anomalies': anomalies
        })
    
    # 按异常数量排序
    sorted_by_count = sorted(file_scores, key=lambda x: -x['anomaly_count'])
    
    # 输出优先级报告
    print("=" * 100)
    print("📋 上海话练习册 - 异常检查优先级列表")
    print("=" * 100)
    print()
    
    # 汇总统计
    total_anomalies = sum(f['anomaly_count'] for f in file_scores)
    files_with_anomalies = sum(1 for f in file_scores if f['anomaly_count'] > 0)
    files_without_anomalies = sum(1 for f in file_scores if f['anomaly_count'] == 0)
    
    print(f"📊 **汇总统计**")
    print(f"   • 总异常数: {total_anomalies}")
    print(f"   • 有异常的文件: {files_with_anomalies}")
    print(f"   • 无异常的文件: {files_without_anomalies}")
    print()
    
    # 优先级分级
    critical = [f for f in sorted_by_count if f['anomaly_count'] >= 20]
    high = [f for f in sorted_by_count if 10 <= f['anomaly_count'] < 20]
    medium = [f for f in sorted_by_count if 5 <= f['anomaly_count'] < 10]
    low = [f for f in sorted_by_count if 1 <= f['anomaly_count'] < 5]
    clean = [f for f in sorted_by_count if f['anomaly_count'] == 0]
    
    print("=" * 100)
    print(f"🔴 **紧急优先级 (≥20 处异常)** - {len(critical)} 个文件")
    print("=" * 100)
    for i, f in enumerate(critical, 1):
        print(f"{i:3}. {f['filename']:20} | 异常: {f['anomaly_count']:3} | 总对数: {f['total_pairs']:3} | 错误率: {f['anomaly_rate']*100:5.1f}%")
        # 显示主要异常类型
        char_counts = defaultdict(int)
        for a in f['anomalies']:
            char_counts[a['char']] += 1
        top_chars = sorted(char_counts.items(), key=lambda x: -x[1])[:5]
        chars_str = ', '.join(f"「{c}」×{n}" for c, n in top_chars)
        print(f"      主要问题字: {chars_str}")
    
    print()
    print("=" * 100)
    print(f"🟠 **高优先级 (10-19 处异常)** - {len(high)} 个文件")
    print("=" * 100)
    for i, f in enumerate(high, 1):
        print(f"{i:3}. {f['filename']:20} | 异常: {f['anomaly_count']:3} | 总对数: {f['total_pairs']:3} | 错误率: {f['anomaly_rate']*100:5.1f}%")
        char_counts = defaultdict(int)
        for a in f['anomalies']:
            char_counts[a['char']] += 1
        top_chars = sorted(char_counts.items(), key=lambda x: -x[1])[:3]
        chars_str = ', '.join(f"「{c}」×{n}" for c, n in top_chars)
        print(f"      主要问题字: {chars_str}")
    
    print()
    print("=" * 100)
    print(f"🟡 **中优先级 (5-9 处异常)** - {len(medium)} 个文件")
    print("=" * 100)
    for i, f in enumerate(medium, 1):
        print(f"{i:3}. {f['filename']:20} | 异常: {f['anomaly_count']:3} | 总对数: {f['total_pairs']:3} | 错误率: {f['anomaly_rate']*100:5.1f}%")
    
    print()
    print("=" * 100)
    print(f"🟢 **低优先级 (1-4 处异常)** - {len(low)} 个文件")
    print("=" * 100)
    for i, f in enumerate(low, 1):
        print(f"{i:3}. {f['filename']:20} | 异常: {f['anomaly_count']:3} | 总对数: {f['total_pairs']:3} | 错误率: {f['anomaly_rate']*100:5.1f}%")
    
    print()
    print("=" * 100)
    print(f"✅ **无异常文件** - {len(clean)} 个文件")
    print("=" * 100)
    clean_nums = [f['lesson_num'] for f in clean]
    print(f"   课程编号: {', '.join(str(n) for n in sorted(clean_nums))}")
    
    # 保存详细JSON报告
    report = {
        'summary': {
            'total_anomalies': total_anomalies,
            'files_with_anomalies': files_with_anomalies,
            'files_without_anomalies': files_without_anomalies,
            'priority_distribution': {
                'critical': len(critical),
                'high': len(high),
                'medium': len(medium),
                'low': len(low),
                'clean': len(clean)
            }
        },
        'priority_list': [
            {
                'filename': f['filename'],
                'lesson_num': f['lesson_num'],
                'anomaly_count': f['anomaly_count'],
                'total_pairs': f['total_pairs'],
                'anomaly_rate': round(f['anomaly_rate'] * 100, 2),
                'priority': 'critical' if f['anomaly_count'] >= 20 else
                           'high' if f['anomaly_count'] >= 10 else
                           'medium' if f['anomaly_count'] >= 5 else
                           'low' if f['anomaly_count'] >= 1 else 'clean',
                'anomalies': [
                    {
                        'char': a['char'],
                        'expected': a['expected'],
                        'found': a['found'],
                        'original': f"#r(\"{a['original_pinyin']}\", \"{a['original_hanzi']}\")"
                    }
                    for a in f['anomalies']
                ]
            }
            for f in sorted_by_count if f['anomaly_count'] > 0
        ]
    }
    
    report_path = lessons_dir.parent.parent / "priority_report.json"
    with open(report_path, 'w', encoding='utf-8') as fp:
        json.dump(report, fp, ensure_ascii=False, indent=2)
    print()
    print(f"\n📄 详细优先级报告已保存到: {report_path}")

if __name__ == "__main__":
    main()
