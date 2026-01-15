"""
Rime 吴语词典加载工具
用于从 rime-wugniu_zaonhe 词库中提取词组和多音字信息
"""
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List, Tuple

# 吴语学堂拼音到本书罗马字的大致映射 (简化版)
# 注意：这只是一个近似映射，实际转换可能需要更精细的规则
WUGNIU_TO_ROMANIZATION = {
    # 声母
    'gn': 'ny',   # 日母
    'gh': '',     # 疑母
    'ng': 'ng',
    'ny': 'ny',
    'sh': 's',
    'zh': 'dz',
    'ch': 'tsh',
    'j': 'dz',
    'q': 'tsh',
    'x': 's',
    'c': 'ts',
    'z': 'z',
    # 韵母
    'iq': 'ih',   # 入声 -q
    'eq': 'eh',
    'aq': 'ah',
    'oq': 'oh',
    'uq': 'uh',
    'oe': 'eu',
    'ao': 'au',
    'ou': 'eu',
    'iu': 'ieu',
    'ui': 'ui',
    'an': 'an',
    'en': 'en',
    'in': 'in',
    'on': 'ong',
    'un': 'ung',
    'aon': 'aung',
}


def convert_wugniu_to_romanization(wugniu: str) -> str:
    """
    将吴语学堂拼音转换为本书使用的罗马字 (近似)
    """
    result = wugniu.lower()
    # 按长度排序，优先匹配较长的模式
    for w, r in sorted(WUGNIU_TO_ROMANIZATION.items(), key=lambda x: -len(x[0])):
        result = result.replace(w, r)
    return result


def load_rime_dict(dict_path: Path) -> Tuple[Dict[str, Set[str]], Dict[str, List[Tuple[str, str]]]]:
    """
    加载 Rime 词典文件
    
    返回:
        char_pinyins: Dict[汉字, Set[拼音变体]]  - 单字的所有可能读音
        phrase_pinyins: Dict[词组, List[(拼音序列, 权重)]] - 多字词组的读音
    """
    char_pinyins: Dict[str, Set[str]] = defaultdict(set)
    phrase_pinyins: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    
    if not dict_path.exists():
        print(f"警告: 词典文件不存在: {dict_path}")
        return char_pinyins, phrase_pinyins
    
    in_dict_section = False
    
    with open(dict_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # 跳过 YAML 头部和空行
            if line == '...' or line == '---':
                in_dict_section = True
                continue
            if not in_dict_section or not line or line.startswith('#'):
                continue
            
            # 解析词条: 汉字\t拼音[\t权重]
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            
            hanzi = parts[0]
            pinyin = parts[1]
            weight = parts[2] if len(parts) > 2 else ""
            
            # 单字
            if len(hanzi) == 1:
                char_pinyins[hanzi].add(pinyin)
            else:
                # 多字词组
                phrase_pinyins[hanzi].append((pinyin, weight))
                
                # 同时记录词组中各字的读音
                py_parts = pinyin.split()
                chars = list(hanzi)
                if len(py_parts) == len(chars):
                    for c, p in zip(chars, py_parts):
                        char_pinyins[c].add(p)
    
    return dict(char_pinyins), dict(phrase_pinyins)


def build_polyphonic_set(char_pinyins: Dict[str, Set[str]], min_variants: int = 2) -> Set[str]:
    """
    构建多音字集合
    
    Args:
        char_pinyins: 单字-拼音映射
        min_variants: 最少需要多少个不同读音才算多音字
    
    Returns:
        多音字集合
    """
    polyphonic = set()
    for char, pinyins in char_pinyins.items():
        if len(pinyins) >= min_variants:
            polyphonic.add(char)
    return polyphonic


def get_phrase_pinyin(phrase: str, phrase_pinyins: Dict[str, List[Tuple[str, str]]]) -> str:
    """
    获取词组的标准拼音 (取第一个可能的读音)
    """
    if phrase in phrase_pinyins:
        return phrase_pinyins[phrase][0][0]
    return ""


# 预加载词典
_RIME_DICT_PATH = Path(__file__).parent.parent / "external/rime-wugniu_zaonhe/wugniu_zaonhe.dict.yaml"
_CHAR_PINYINS, _PHRASE_PINYINS = None, None
_POLYPHONIC_CHARS = None


def get_rime_data():
    """获取 Rime 词典数据 (惰性加载)"""
    global _CHAR_PINYINS, _PHRASE_PINYINS, _POLYPHONIC_CHARS
    if _CHAR_PINYINS is None:
        _CHAR_PINYINS, _PHRASE_PINYINS = load_rime_dict(_RIME_DICT_PATH)
        _POLYPHONIC_CHARS = build_polyphonic_set(_CHAR_PINYINS)
    return _CHAR_PINYINS, _PHRASE_PINYINS, _POLYPHONIC_CHARS


def is_known_polyphonic(char: str) -> bool:
    """检查是否为已知多音字"""
    _, _, polyphonic = get_rime_data()
    return char in polyphonic


def get_char_variants(char: str) -> Set[str]:
    """获取单字的所有读音变体"""
    char_pinyins, _, _ = get_rime_data()
    return char_pinyins.get(char, set())


if __name__ == "__main__":
    # 测试
    char_pinyins, phrase_pinyins, polyphonic = get_rime_data()
    print(f"加载了 {len(char_pinyins)} 个单字, {len(phrase_pinyins)} 个词组")
    print(f"多音字数量: {len(polyphonic)}")
    
    # 测试"日"字
    print(f"\n'日' 的读音: {char_pinyins.get('日', set())}")
    print(f"'日' 是多音字: {is_known_polyphonic('日')}")
    
    # 测试"拉"字
    print(f"\n'拉' 的读音: {char_pinyins.get('拉', set())}")
    print(f"'拉' 是多音字: {is_known_polyphonic('拉')}")
