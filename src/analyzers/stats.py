import re
import json
from collections import defaultdict
from typing import List
from ..loader import LessonFile
from ..utils import split_characters

def generate_priority_list(lessons: List[LessonFile], output_json: str = "priority_report.json"):
    """
    生成按异常数量排序的优先级列表
    """
    # 1. 收集全局发音统计
    char_pronunciations = defaultdict(lambda: defaultdict(list))
    file_total_pairs = defaultdict(int)
    
    for lesson in lessons:
        pairs = lesson.pairs
        file_total_pairs[lesson.filename] = len(pairs)
        
        for p in pairs:
            # p is RubyPair object
            pinyin = p.normalized_pinyin
            hanzi = p.hanzi
            fname = p.filename
            
            chars = split_characters(hanzi)
            p_parts = re.split(r'[-\s]', pinyin)
            
            if len(p_parts) == len(chars):
                for char, py in zip(chars, p_parts):
                    char_pronunciations[char][py].append((fname, hanzi, p.pinyin))
            elif len(chars) == 1:
                char_pronunciations[chars[0]][pinyin].append((fname, hanzi, p.pinyin))

    # 2. 确定主流发音
    main_pronunciations = {}
    for char, prons in char_pronunciations.items():
        if prons:
            main_py = max(prons.keys(), key=lambda x: len(prons[x]))
            main_count = len(prons[main_py])
            total = sum(len(occ) for occ in prons.values())
            main_pronunciations[char] = (main_py, main_count, total)

    # 3. 统计文件异常
    file_scores = []
    
    for lesson in lessons:
        anomalies = []
        for p in lesson.pairs:
            chars = split_characters(p.hanzi)
            p_parts = re.split(r'[-\s]', p.normalized_pinyin)
            
            # Check mappings
            check_list = []
            if len(p_parts) == len(chars):
                check_list = list(zip(chars, p_parts))
            elif len(chars) == 1:
                check_list = [(chars[0], p.normalized_pinyin)]
                
            for char, py in check_list:
                if char in main_pronunciations:
                    main_py, main_count, total = main_pronunciations[char]
                    
                    # 判定异常规则
                    if main_count / total >= 0.8 and total >= 3 and py != main_py:
                        anomalies.append({
                            'char': char,
                            'found': py,
                            'expected': main_py,
                            'original_pinyin': p.pinyin,
                            'original_hanzi': p.hanzi,
                            'confidence': main_count / total
                        })
        
        anomaly_count = len(anomalies)
        total_pairs = file_total_pairs.get(lesson.filename, 1)
        
        try:
            lesson_num = int(re.search(r'lesson-(\d+)', lesson.filename).group(1))
        except (AttributeError, ValueError):
            lesson_num = 0

        file_scores.append({
            'filename': lesson.filename,
            'lesson_num': lesson_num,
            'anomaly_count': anomaly_count,
            'total_pairs': total_pairs,
            'anomaly_rate': anomaly_count / total_pairs if total_pairs > 0 else 0,
            'anomalies': anomalies
        })

    # 4. 输出
    sorted_files = sorted(file_scores, key=lambda x: -x['anomaly_count'])
    
    print("\n" + "="*80)
    print("优先级列表 (Priority List - Top 10)")
    print("="*80)
    for f in sorted_files[:10]:
        print(f"{f['filename']:<20} | 异常: {f['anomaly_count']:<3} | 错误率: {f['anomaly_rate']:.1%}")

    # 保存 Detailed Report
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({'files': sorted_files}, f, ensure_ascii=False, indent=2)
    print(f"\n优先级报告已保存至: {output_json}")
