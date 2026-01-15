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
from .rime_dict import is_valid_pronunciation

class FixStrategy(Enum):
    SPLIT_RUBY = auto()      # 拆分：汉字多于拼音
    MERGE_RUBY = auto()      # 合并：拼音多于汉字
    REPLACE_PINYIN = auto()  # 替换：拼写错误
    MANUAL = auto()          # 无法自动处理

class SafetyLevel(Enum):
    """自动修复安全等级"""
    SAFE = auto()        # 可安全自动修复 (置信度 > 95%)
    REVIEW = auto()      # 建议人工审核 (置信度 70-95%)
    MANUAL = auto()      # 必须人工处理 (置信度 < 70%)

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
    safety: SafetyLevel = SafetyLevel.MANUAL
    needs_input: bool = False  # 是否需要用户输入
    missing_char: str = ""     # 需要用户提供拼音的汉字
    context_before: str = ""   # 前文上下文
    context_after: str = ""    # 后文上下文
    corpus_examples: List[str] = None  # 全书中该字的其他用例
    
    def __post_init__(self):
        if self.corpus_examples is None:
            self.corpus_examples = []

@dataclass
class CharPronInfo:
    """汉字发音信息"""
    main_pinyin: str
    main_count: int
    total_count: int
    all_pinyins: Dict[str, int]
    examples: List[str]  # 示例: ["lesson-1.typ: #r('kuh', '个')"]
    
    @property
    def confidence(self) -> float:
        return self.main_count / self.total_count if self.total_count > 0 else 0
    
    @property
    def is_polyphonic(self) -> bool:
        """是否可能是多音字 (第二常见读音占比 > 15%)"""
        if len(self.all_pinyins) < 2:
            return False
        sorted_counts = sorted(self.all_pinyins.values(), reverse=True)
        second_ratio = sorted_counts[1] / self.total_count
        return second_ratio > 0.15

def build_pronunciation_db(lessons: List[LessonFile]) -> Dict[str, CharPronInfo]:
    """从全书构建汉字-发音信息数据库 (带统计和示例)"""
    char_data = defaultdict(lambda: {"counts": defaultdict(int), "examples": defaultdict(list)})
    
    for lesson in lessons:
        for pair in lesson.pairs:
            p_parts = re.split(r'[-\s]', pair.normalized_pinyin)
            h_chars = split_characters(pair.hanzi)
            
            if len(p_parts) == len(h_chars):
                for c, p in zip(h_chars, p_parts):
                    char_data[c]["counts"][p] += 1
                    if len(char_data[c]["examples"][p]) < 3:  # 最多保留3个示例
                        char_data[c]["examples"][p].append(
                            f"{lesson.filename}: #r(\"{pair.pinyin}\", \"{pair.hanzi}\")"
                        )
    
    result = {}
    for char, data in char_data.items():
        counts = data["counts"]
        if not counts:
            continue
        main_py = max(counts.keys(), key=lambda x: counts[x])
        total = sum(counts.values())
        # 收集所有示例
        all_examples = []
        for py, exs in data["examples"].items():
            all_examples.extend(exs)
        
        result[char] = CharPronInfo(
            main_pinyin=main_py,
            main_count=counts[main_py],
            total_count=total,
            all_pinyins=dict(counts),
            examples=all_examples[:5]
        )
    
    return result

def analyze_ruby_pair(pinyin: str, hanzi: str, pron_db: Dict[str, CharPronInfo]) -> Optional[FixSuggestion]:
    """分析单个 Ruby 对是否需要修复"""
    p_parts = re.split(r'[-\s]', normalize_pinyin(pinyin))
    h_chars = split_characters(hanzi)
    
    original = f'#r("{pinyin}", "{hanzi}")'
    
    # 0. 保护机制：叠词检查 (如 "leh-la" "拉拉")
    # 如果汉字是叠词，无论拼音形式如何，都不做拼写修正
    # 因为上海话叠词有复杂的连读变调规则 (如 leh-la, khoe-kho 等)
    is_hanzi_reduplication = len(h_chars) >= 2 and h_chars[0] == h_chars[1]
    
    # 情况1: 长度匹配，检查拼写错误
    if len(p_parts) == len(h_chars):
        for i, (char, py) in enumerate(zip(h_chars, p_parts)):
            if char in pron_db:
                info = pron_db[char]
                expected = info.main_pinyin
                sim = get_similarity(expected, py)
                
                # 跳过多音字 (可能是合理变体)
                if info.is_polyphonic and py in info.all_pinyins:
                    continue
                
                # 使用 Rime 词典 + 音系相似度验证：
                # 如果当前拼音是该字的合法读音变体（考虑教会罗马字到吴语学堂的转换），跳过修正
                if is_valid_pronunciation(char, py):
                    continue
                    
                if sim < 0.5 and sim > 0:
                    # 叠词保护：对于叠词汉字，不做自动拼写修正
                    if is_hanzi_reduplication:
                        continue  # 跳过，不建议修改叠词的读音
                    
                    new_parts = p_parts.copy()
                    new_parts[i] = expected
                    new_pinyin = "-".join(new_parts)
                    
                    # 根据置信度确定安全等级
                    safety = SafetyLevel.SAFE if info.confidence > 0.95 else \
                             SafetyLevel.REVIEW if info.confidence > 0.7 else \
                             SafetyLevel.MANUAL
                    
                    return FixSuggestion(
                        file="", line_num=0,
                        strategy=FixStrategy.REPLACE_PINYIN,
                        original=original,
                        problem=f"拼写错误: '{py}' → '{expected}' (字: {char}, 置信度: {info.confidence:.0%})",
                        suggestion=f'#r("{new_pinyin}", "{hanzi}")',
                        confidence=info.confidence,
                        safety=safety,
                        corpus_examples=info.examples[:3]
                    )
        return None
    
    # 情况2: 汉字比拼音多 (漏字)
    if len(h_chars) > len(p_parts):
        missing_chars = []
        inferred_pinyins = []
        min_confidence = 1.0
        examples = []
        
        for char in h_chars:
            if char in pron_db:
                info = pron_db[char]
                inferred_pinyins.append((char, info.main_pinyin))
                min_confidence = min(min_confidence, info.confidence)
                examples.extend(info.examples[:1])
            else:
                missing_chars.append(char)
                inferred_pinyins.append((char, None))
        
        if not missing_chars:
            new_rubies = " ".join([f'#r("{py}", "{c}")' for c, py in inferred_pinyins])
            safety = SafetyLevel.SAFE if min_confidence > 0.95 else \
                     SafetyLevel.REVIEW if min_confidence > 0.7 else \
                     SafetyLevel.MANUAL
            return FixSuggestion(
                file="", line_num=0,
                strategy=FixStrategy.SPLIT_RUBY,
                original=original,
                problem=f"汉字 ({len(h_chars)}字) > 拼音 ({len(p_parts)}节)",
                suggestion=new_rubies,
                confidence=min_confidence,
                safety=safety,
                corpus_examples=examples[:3]
            )
        else:
            return FixSuggestion(
                file="", line_num=0,
                strategy=FixStrategy.SPLIT_RUBY,
                original=original,
                problem=f"汉字 ({len(h_chars)}字) > 拼音 ({len(p_parts)}节), 无法推断 '{missing_chars[0]}'",
                suggestion="",
                confidence=0.0,
                safety=SafetyLevel.MANUAL,
                needs_input=True,
                missing_char=missing_chars[0]
            )
    
    # 情况3: 拼音比汉字多
    if len(p_parts) > len(h_chars):
        return FixSuggestion(
            file="", line_num=0,
            strategy=FixStrategy.MERGE_RUBY,
            original=original,
            problem=f"拼音 ({len(p_parts)}节) > 汉字 ({len(h_chars)}字)",
            suggestion="",
            confidence=0.0,
            safety=SafetyLevel.MANUAL,
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
        lessons = [lsn for lsn in lessons if target in lsn.filename]
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
        # 按安全等级分组统计
        safe_count = sum(1 for f in fixes if f.safety == SafetyLevel.SAFE)
        review_count = sum(1 for f in fixes if f.safety == SafetyLevel.REVIEW)
        manual_count = sum(1 for f in fixes if f.safety == SafetyLevel.MANUAL)
        
        print(f"\n📄 {filename} ({len(fixes)} 处: 🟢{safe_count} 🟡{review_count} 🔴{manual_count})")
        file_path = lessons_dir / filename
        
        for i, fix in enumerate(fixes, 1):
            # 安全等级标记
            safety_icon = "🟢" if fix.safety == SafetyLevel.SAFE else \
                          "🟡" if fix.safety == SafetyLevel.REVIEW else "🔴"
            
            print(f"\n  [{i}/{len(fixes)}] {safety_icon} 第 {fix.line_num} 行")
            print(f"  原文: {fix.original}")
            print(f"  问题: {fix.problem}")
            
            if fix.suggestion:
                print(f"  建议: {fix.suggestion}")
                print(f"  置信度: {fix.confidence:.0%} | 安全等级: {fix.safety.name}")
            
            # 显示全书上下文
            if fix.corpus_examples:
                print("  📖 全书用例:")
                for ex in fix.corpus_examples[:2]:
                    print(f"     {ex}")
            
            if dry_run:
                print("  [DRY-RUN] 跳过")
                continue
            
            if fix.needs_input:
                if interactive:
                    user_input = input(f"  输入 '{fix.missing_char}' 的拼音 (留空跳过): ").strip()
                    if user_input:
                        print(f"  → 需手动编辑文件添加: #r(\"{user_input}\", \"{fix.missing_char}\")")
                    skipped_count += 1
                else:
                    print("  [需手动处理]")
                    skipped_count += 1
                continue
            
            # 自动模式：只自动应用 SAFE 级别的修复
            if auto:
                if fix.safety == SafetyLevel.SAFE:
                    if apply_fix(file_path, fix, backup):
                        print("  ✓ 已自动修复 (SAFE)")
                        fixed_count += 1
                    else:
                        print("  ✗ 修复失败")
                        skipped_count += 1
                else:
                    print(f"  [跳过] 安全等级为 {fix.safety.name}，需人工处理")
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

