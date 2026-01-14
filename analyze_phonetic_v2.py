#!/usr/bin/env python3
"""
高级上海话音韵一致性分析工具 (Advanced Phonetic Consistency Analyzer)
1. 支持连读词（带连字符）整体分析
2. 基于声母/韵母相似度的异常检测
3. 自动识别连读变调和方言变体模式
"""

import re
import os
import json
from collections import defaultdict
from pathlib import Path

# 定义声母和韵母的简单提取逻辑（基于该书所用的罗马字系统）
INITIALS = ['ph', 'th', 'kh', 'tsh', 'dz', 'dj', 'ts', 'ky', 'kyi', 'ny', 'ng', 'sh', 'sz', 'v', 'z', 'gh', 'h', 'l', 'n', 'm', 'p', 't', 'k', 'b', 'd', 'g', 'f', 's', 'y', 'w', 'j']
INITIALS.sort(key=len, reverse=True) # 优先匹配长声母

def split_phonetic(syllable: str) -> tuple[str, str]:
    """将单音节拆分为声母和韵母"""
    syllable = syllable.lower().strip("'")
    if not syllable:
        return "", ""
    
    # 特殊处理元音开头的音节
    for init in INITIALS:
        if syllable.startswith(init):
            return init, syllable[len(init):]
    
    return "", syllable

def levenshtein_distance(s1, s2):
    """计算简易编辑距离"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if not s2:
        return len(s1)
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

def get_similarity(p1: str, p2: str) -> float:
    """计算两个拼音的相似度 (0-1)"""
    dist = levenshtein_distance(p1, p2)
    max_len = max(len(p1), len(p2), 1)
    return 1 - (dist / max_len)

def extract_ruby_pairs(content: str, filename: str) -> list:
    pattern = r'#r\("([^"]+)",\s*"([^"]+)"\)'
    matches = re.finditer(pattern, content)
    return [(m.group(1), m.group(2), filename, m.start()) for m in matches]

def normalize(p: str) -> str:
    return re.sub(r'[,.\?!;:，。？！；：]+$', '', p).strip().lower()

def main():
    lessons_dir = Path("/home/drie/下载/Shanghai Dialect Exercises in Romanized and Character with Key to Pronunciation and English Index/typst_source/contents/lessons")
    
    # 1. 数据收集
    # word_stats: {汉字词: {拼音: [位置信息]}}
    word_stats = defaultdict(lambda: defaultdict(list))
    # single_char_stats: {单汉字: {音节: [位置信息]}}
    char_stats = defaultdict(lambda: defaultdict(list))
    
    for f in sorted(lessons_dir.glob("lesson-*.typ")):
        content = f.read_text(encoding='utf-8')
        pairs = extract_ruby_pairs(content, f.name)
        
        for pinyin, hanzi, fname, pos in pairs:
            p_norm = normalize(pinyin)
            h_chars = [c for c in hanzi if '\u4e00' <= c <= '\u9fff']
            if not h_chars: continue
            
            # 记录整词 (捕捉连读情况)
            word_stats[hanzi][p_norm].append((fname, pinyin))
            
            # 记录单字 (如果是连读词，则尝试拆分)
            p_parts = re.split(r'[-\s]', p_norm)
            if len(h_chars) == len(p_parts):
                for char, py in zip(h_chars, p_parts):
                    char_stats[char][py].append((fname, pinyin, hanzi))
            elif len(h_chars) == 1:
                char_stats[h_chars[0]][p_norm].append((fname, pinyin, hanzi))

    # 2. 异常分析
    report = {
        "typos": [],       # 极其相似，极低频，高概率是手误 (kuh vs kub)
        "variants": [],    # 语音相似，且有一定频率，可能是音变或变体 (la vs leh, l vs n)
        "mismatches": [],  # 差异巨大，可能是对齐或索引混入错误 (i vs comb)
        "tone_sandhi": []  # 连读中的音变情况
    }

    # 分析单字音变
    for char, prons in char_stats.items():
        if len(prons) <= 1: continue
        
        # 找出主流发音
        main_py = max(prons.keys(), key=lambda k: len(prons[k]))
        main_count = len(prons[main_py])
        total = sum(len(v) for v in prons.values())
        
        for py, occurrences in prons.items():
            if py == main_py: continue
            
            similarity = get_similarity(main_py, py)
            count = len(occurrences)
            
            info = {
                "char": char,
                "main": main_py,
                "main_count": main_count,
                "alt": py,
                "alt_count": count,
                "similarity": round(similarity, 2),
                "examples": occurrences[:3]
            }
            
            # 分类逻辑
            if similarity >= 0.7:
                if count <= 2: 
                    report["typos"].append(info)
                else:
                    # 检查是否是 l/n 互换等模式
                    init1, fin1 = split_phonetic(main_py)
                    init2, fin2 = split_phonetic(py)
                    info["init_match"] = (init1 == init2)
                    info["fin_match"] = (fin1 == fin2)
                    report["variants"].append(info)
            else:
                report["mismatches"].append(info)

    # 3. 输出美化报告
    print("="*80)
    print("上海话音韵深度一致性分析")
    print("="*80)
    
    print(f"\n[!] 发现 {len(report['typos'])} 处疑似手误 (高相似度，低频)")
    for item in sorted(report['typos'], key=lambda x: -x['similarity'])[:15]:
        print(f"  - 「{item['char']}」: {item['main']}({item['main_count']}) → {item['alt']}({item['alt_count']}) | 相似度: {item['similarity']}")
        print(f"    位置: {item['examples'][0][0]}: #r(\"{item['examples'][0][1]}\", \"{item['examples'][0][2]}\")")

    print(f"\n[~] 发现 {len(report['variants'])} 处语音变体 (如 la/leh, l/n)")
    # 聚合显示常见的变体模式
    patterns = defaultdict(int)
    for v in report['variants']:
        patterns[f"{v['main']} -> {v['alt']}"] += v['alt_count']
    
    sorted_patterns = sorted(patterns.items(), key=lambda x: -x[1])
    for pat, freq in sorted_patterns[:10]:
        print(f"  - 模式 {pat}: 出现 {freq} 次")

    print(f"\n[X] 发现 {len(report['mismatches'])} 处严重不匹配 (可能是索引干扰或对齐错误)")
    for item in sorted(report['mismatches'], key=lambda x: x['similarity'])[:15]:
        print(f"  - 「{item['char']}」: {item['main']}({item['main_count']}) → {item['alt']}({item['alt_count']})")
        print(f"    位置: {item['examples'][0][0]}: #r(\"{item['examples'][0][1]}\", \"{item['examples'][0][2]}\")")

    # 保存 JSON
    with open("phonetic_analysis_v2.json", "w", encoding="utf-8") as jf:
        json.dump(report, jf, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
