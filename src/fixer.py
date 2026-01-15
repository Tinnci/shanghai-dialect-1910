"""
Ruby 对自动修复模块
支持交互式修复、干运行和自动模式
"""
import re
import shutil
from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Dict
from collections import defaultdict

from .loader import LessonFile, load_lessons
from .utils import split_characters, get_similarity, normalize_pinyin

class FixStrategy(Enum):
    SPLIT_RUBY = auto()      # 拆分：汉字多于拼音
    MERGE_RUBY = auto()      # 合并：拼音多于汉字
    REPLACE_PINYIN = auto()  # 替换：拼写错误
    MANUAL = auto()          # 无法自动处理

@dataclass
class FixSuggestion:
    """单条修复建议"""
    file: str
    line_num: int
    strategy: FixStrategy
    original: str           # 原始 #r(...) 文本
    problem: str            # 问题描述
    suggestion: str         # 建议的修复后文本
    confidence: float       # 置信度 (0-1)
    needs_input: bool = False  # 是否需要用户输入
    missing_char: str = ""     # 需要用户提供拼音的汉字

def build_pronunciation_db(lessons: List[LessonFile]) -> Dict[str, str]:
    """从全书构建汉字-主流读音数据库"""
    char_counts = defaultdict(lambda: defaultdict(int))
    
    for lesson in lessons:
        for pair in lesson.pairs:
            p_parts = re.split(r'[-\s]', pair.normalized_pinyin)
            h_chars = split_characters(pair.hanzi)
            
            if len(p_parts) == len(h_chars):
                for c, p in zip(h_chars, p_parts):
                    char_counts[c][p] += 1
    
    # 返回每个字的主流读音
    return {c: max(ps.keys(), key=lambda x: ps[x]) 
            for c, ps in char_counts.items() if ps}

def analyze_ruby_pair(pinyin: str, hanzi: str, pron_db: Dict[str, str]) -> Optional[FixSuggestion]:
    """分析单个 Ruby 对是否需要修复"""
    p_parts = re.split(r'[-\s]', normalize_pinyin(pinyin))
    h_chars = split_characters(hanzi)
    
    original = f'#r("{pinyin}", "{hanzi}")'
    
    # 情况1: 长度匹配，检查拼写错误
    if len(p_parts) == len(h_chars):
        for i, (char, py) in enumerate(zip(h_chars, p_parts)):
            if char in pron_db:
                expected = pron_db[char]
                sim = get_similarity(expected, py)
                if sim < 0.5 and sim > 0:
                    # 可能是拼写错误
                    new_parts = p_parts.copy()
                    new_parts[i] = expected
                    new_pinyin = "-".join(new_parts)
                    return FixSuggestion(
                        file="", line_num=0,
                        strategy=FixStrategy.REPLACE_PINYIN,
                        original=original,
                        problem=f"拼写错误: '{py}' 应为 '{expected}' (字: {char})",
                        suggestion=f'#r("{new_pinyin}", "{hanzi}")',
                        confidence=0.8
                    )
        return None  # 匹配良好
    
    # 情况2: 汉字比拼音多 (漏字)
    if len(h_chars) > len(p_parts):
        diff = len(h_chars) - len(p_parts)
        # 尝试推断缺失的拼音
        missing_chars = []
        inferred_pinyins = []
        
        for char in h_chars:
            if char in pron_db:
                inferred_pinyins.append((char, pron_db[char]))
            else:
                missing_chars.append(char)
                inferred_pinyins.append((char, None))
        
        if not missing_chars:
            # 可以完全推断
            new_rubies = " ".join([f'#r("{py}", "{c}")' for c, py in inferred_pinyins])
            return FixSuggestion(
                file="", line_num=0,
                strategy=FixStrategy.SPLIT_RUBY,
                original=original,
                problem=f"汉字 ({len(h_chars)}字) > 拼音 ({len(p_parts)}节)",
                suggestion=new_rubies,
                confidence=0.7
            )
        else:
            # 需要用户输入
            return FixSuggestion(
                file="", line_num=0,
                strategy=FixStrategy.SPLIT_RUBY,
                original=original,
                problem=f"汉字 ({len(h_chars)}字) > 拼音 ({len(p_parts)}节), 无法推断 '{missing_chars[0]}'",
                suggestion="",
                confidence=0.0,
                needs_input=True,
                missing_char=missing_chars[0]
            )
    
    # 情况3: 拼音比汉字多 (多字)
    if len(p_parts) > len(h_chars):
        return FixSuggestion(
            file="", line_num=0,
            strategy=FixStrategy.MERGE_RUBY,
            original=original,
            problem=f"拼音 ({len(p_parts)}节) > 汉字 ({len(h_chars)}字)",
            suggestion="",  # 需要人工判断
            confidence=0.0,
            needs_input=True
        )
    
    return None

def scan_file_for_fixes(lesson: LessonFile, pron_db: Dict[str, str]) -> List[FixSuggestion]:
    """扫描单个文件，返回所有修复建议"""
    suggestions = []
    
    # 使用正则找出所有 #r(...) 并记录行号
    lines = lesson.content.split('\n')
    pattern = r'#r\("([^"]+)",\s*"([^"]+)"\)'
    
    for line_num, line in enumerate(lines, 1):
        for match in re.finditer(pattern, line):
            pinyin, hanzi = match.group(1), match.group(2)
            fix = analyze_ruby_pair(pinyin, hanzi, pron_db)
            if fix:
                fix.file = lesson.filename
                fix.line_num = line_num
                suggestions.append(fix)
    
    return suggestions

def apply_fix(file_path: Path, suggestion: FixSuggestion, backup: bool = True) -> bool:
    """应用单条修复到文件"""
    if not suggestion.suggestion:
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    if suggestion.original not in content:
        return False
    
    if backup:
        backup_path = file_path.with_suffix(file_path.suffix + '.bak')
        if not backup_path.exists():
            shutil.copy(file_path, backup_path)
    
    new_content = content.replace(suggestion.original, suggestion.suggestion, 1)
    file_path.write_text(new_content, encoding='utf-8')
    return True

def run_fixer(
    lessons_dir: Path,
    target: Optional[str] = None,
    dry_run: bool = True,
    interactive: bool = False,
    auto: bool = False,
    backup: bool = True
):
    """主修复入口"""
    print("="*80)
    print("Ruby 对修复工具")
    print("="*80)
    
    # 加载数据
    lessons = load_lessons(lessons_dir)
    if not lessons:
        print("未找到课程文件")
        return
    
    # 过滤目标
    if target and target != "--all":
        lessons = [l for l in lessons if target in l.filename]
        if not lessons:
            print(f"未找到匹配 '{target}' 的文件")
            return
    
    # 建立发音数据库
    all_lessons = load_lessons(lessons_dir)  # 全部用于建库
    pron_db = build_pronunciation_db(all_lessons)
    print(f"已建立 {len(pron_db)} 字发音数据库")
    
    # 扫描问题
    all_fixes = []
    for lesson in lessons:
        fixes = scan_file_for_fixes(lesson, pron_db)
        all_fixes.extend(fixes)
    
    if not all_fixes:
        print("\n✅ 未发现需要修复的问题")
        return
    
    print(f"\n发现 {len(all_fixes)} 处待修复问题")
    
    # 按文件分组显示
    by_file = defaultdict(list)
    for fix in all_fixes:
        by_file[fix.file].append(fix)
    
    fixed_count = 0
    skipped_count = 0
    
    for filename, fixes in by_file.items():
        print(f"\n📄 {filename} ({len(fixes)} 处)")
        file_path = lessons_dir / filename
        
        for i, fix in enumerate(fixes, 1):
            print(f"\n  [{i}/{len(fixes)}] 第 {fix.line_num} 行")
            print(f"  原文: {fix.original}")
            print(f"  问题: {fix.problem}")
            
            if fix.suggestion:
                print(f"  建议: {fix.suggestion}")
                print(f"  置信度: {fix.confidence:.0%}")
            
            if dry_run:
                print("  [DRY-RUN] 跳过")
                continue
            
            if fix.needs_input:
                if interactive:
                    user_input = input(f"  输入 '{fix.missing_char}' 的拼音 (留空跳过): ").strip()
                    if user_input:
                        # 重新构建建议 (简化处理)
                        print(f"  → 需手动编辑文件添加: #r(\"{user_input}\", \"{fix.missing_char}\")")
                    skipped_count += 1
                else:
                    print("  [需手动处理]")
                    skipped_count += 1
                continue
            
            if interactive:
                choice = input("  应用修复? [y/n/s=跳过文件/q=退出] > ").strip().lower()
                if choice == 'q':
                    print("\n已退出")
                    return
                if choice == 's':
                    print(f"  跳过文件 {filename}")
                    break
                if choice != 'y':
                    skipped_count += 1
                    continue
            
            if auto or (interactive and choice == 'y'):
                if apply_fix(file_path, fix, backup):
                    print("  ✓ 已修复")
                    fixed_count += 1
                else:
                    print("  ✗ 修复失败")
                    skipped_count += 1
    
    print("\n" + "="*80)
    print(f"完成! 修复 {fixed_count} 处, 跳过 {skipped_count} 处")
    if dry_run:
        print("(干运行模式，未实际修改文件)")
