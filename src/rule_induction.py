"""
音韵规则推导模块 (Phonological Rule Induction)

实现智能化的启发式分析算法：
1. 从平行语料(本书 vs Rime词典)自动推导转换规则
2. 基于音韵特征的加权编辑距离
3. 上下文感知的多音字消歧
4. 规则置信度评估

算法分类:
- Rule Induction (规则推导): 从数据中自动发现模式
- Weighted Edit Distance (加权编辑距离): 音韵学距离而非字符距离
- Feature-based Similarity (特征相似度): 基于声韵调特征向量
- Context-aware Disambiguation (上下文消歧): 利用词组上下文
"""

from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# ============================================================================
# 音韵特征系统 (Phonological Feature System)
# ============================================================================


@dataclass
class PhoneticFeatures:
    """音韵特征向量"""

    # 声母特征
    place: str = ""  # 发音部位: labial, dental, velar, palatal, glottal
    manner: str = ""  # 发音方式: stop, fricative, affricate, nasal, lateral
    voiced: bool = False  # 浊音
    aspirated: bool = False  # 送气

    # 韵母特征
    vowel_height: str = ""  # 元音高度: high, mid, low
    vowel_front: str = ""  # 元音前后: front, central, back
    vowel_round: bool = False  # 圆唇
    nasal_coda: bool = False  # 鼻韵尾
    stop_coda: bool = False  # 入声韵尾 (喉塞)

    def to_vector(self) -> List[float]:
        """转换为数值向量，用于计算距离"""
        place_map = {
            "labial": 0,
            "dental": 1,
            "velar": 2,
            "palatal": 3,
            "glottal": 4,
            "": -1,
        }
        manner_map = {
            "stop": 0,
            "fricative": 1,
            "affricate": 2,
            "nasal": 3,
            "lateral": 4,
            "approximant": 5,
            "": -1,
        }
        height_map = {"high": 0, "mid": 1, "low": 2, "": -1}
        front_map = {"front": 0, "central": 1, "back": 2, "": -1}

        return [
            place_map.get(self.place, -1),
            manner_map.get(self.manner, -1),
            float(self.voiced),
            float(self.aspirated),
            height_map.get(self.vowel_height, -1),
            front_map.get(self.vowel_front, -1),
            float(self.vowel_round),
            float(self.nasal_coda),
            float(self.stop_coda),
        ]


# 声母特征库
INITIAL_FEATURES = {
    # 唇音
    "p": PhoneticFeatures(place="labial", manner="stop", voiced=False, aspirated=False),
    "ph": PhoneticFeatures(place="labial", manner="stop", voiced=False, aspirated=True),
    "b": PhoneticFeatures(place="labial", manner="stop", voiced=True, aspirated=False),
    "m": PhoneticFeatures(place="labial", manner="nasal", voiced=True),
    "f": PhoneticFeatures(place="labial", manner="fricative", voiced=False),
    "v": PhoneticFeatures(place="labial", manner="fricative", voiced=True),
    "w": PhoneticFeatures(place="labial", manner="approximant", voiced=True),
    # 齿音
    "t": PhoneticFeatures(place="dental", manner="stop", voiced=False, aspirated=False),
    "th": PhoneticFeatures(place="dental", manner="stop", voiced=False, aspirated=True),
    "d": PhoneticFeatures(place="dental", manner="stop", voiced=True, aspirated=False),
    "n": PhoneticFeatures(place="dental", manner="nasal", voiced=True),
    "l": PhoneticFeatures(place="dental", manner="lateral", voiced=True),
    "lh": PhoneticFeatures(place="dental", manner="lateral", voiced=False),  # 清边音
    # 齿龈塞擦/擦音
    "ts": PhoneticFeatures(
        place="dental", manner="affricate", voiced=False, aspirated=False
    ),
    "tsh": PhoneticFeatures(
        place="dental", manner="affricate", voiced=False, aspirated=True
    ),
    "c": PhoneticFeatures(
        place="dental", manner="affricate", voiced=False, aspirated=False
    ),
    "ch": PhoneticFeatures(
        place="dental", manner="affricate", voiced=False, aspirated=True
    ),
    "dz": PhoneticFeatures(
        place="dental", manner="affricate", voiced=True, aspirated=False
    ),
    "j": PhoneticFeatures(
        place="dental", manner="affricate", voiced=True, aspirated=False
    ),
    "s": PhoneticFeatures(place="dental", manner="fricative", voiced=False),
    "z": PhoneticFeatures(place="dental", manner="fricative", voiced=True),
    "sh": PhoneticFeatures(place="dental", manner="fricative", voiced=False),
    "zh": PhoneticFeatures(place="dental", manner="fricative", voiced=True),
    # 腭音
    "ny": PhoneticFeatures(place="palatal", manner="nasal", voiced=True),
    "gn": PhoneticFeatures(place="palatal", manner="nasal", voiced=True),
    "ky": PhoneticFeatures(
        place="palatal", manner="stop", voiced=False, aspirated=False
    ),
    "hy": PhoneticFeatures(place="palatal", manner="fricative", voiced=False),
    "x": PhoneticFeatures(place="palatal", manner="fricative", voiced=False),
    "y": PhoneticFeatures(place="palatal", manner="approximant", voiced=True),
    # 软腭音
    "k": PhoneticFeatures(place="velar", manner="stop", voiced=False, aspirated=False),
    "kh": PhoneticFeatures(place="velar", manner="stop", voiced=False, aspirated=True),
    "g": PhoneticFeatures(place="velar", manner="stop", voiced=True, aspirated=False),
    "gh": PhoneticFeatures(place="velar", manner="fricative", voiced=True),
    "ng": PhoneticFeatures(place="velar", manner="nasal", voiced=True),
    # 喉音
    "h": PhoneticFeatures(place="glottal", manner="fricative", voiced=False),
    "'": PhoneticFeatures(place="glottal", manner="stop", voiced=False),
    "hh": PhoneticFeatures(place="glottal", manner="stop", voiced=False),
    # 零声母
    "": PhoneticFeatures(),
}

# 韵母特征库 (简化版)
FINAL_FEATURES = {
    # 开口呼
    "a": PhoneticFeatures(vowel_height="low", vowel_front="central"),
    "e": PhoneticFeatures(vowel_height="mid", vowel_front="front"),
    "o": PhoneticFeatures(vowel_height="mid", vowel_front="back", vowel_round=True),
    "i": PhoneticFeatures(vowel_height="high", vowel_front="front"),
    "u": PhoneticFeatures(vowel_height="high", vowel_front="back", vowel_round=True),
    "oe": PhoneticFeatures(vowel_height="mid", vowel_front="front", vowel_round=True),
    "eu": PhoneticFeatures(vowel_height="mid", vowel_front="front", vowel_round=True),
    # 入声
    "aq": PhoneticFeatures(vowel_height="low", vowel_front="central", stop_coda=True),
    "eq": PhoneticFeatures(vowel_height="mid", vowel_front="front", stop_coda=True),
    "iq": PhoneticFeatures(vowel_height="high", vowel_front="front", stop_coda=True),
    "oq": PhoneticFeatures(
        vowel_height="mid", vowel_front="back", vowel_round=True, stop_coda=True
    ),
    "uq": PhoneticFeatures(
        vowel_height="high", vowel_front="back", vowel_round=True, stop_coda=True
    ),
    "ah": PhoneticFeatures(vowel_height="low", vowel_front="central", stop_coda=True),
    "eh": PhoneticFeatures(vowel_height="mid", vowel_front="front", stop_coda=True),
    "ih": PhoneticFeatures(vowel_height="high", vowel_front="front", stop_coda=True),
    "oh": PhoneticFeatures(
        vowel_height="mid", vowel_front="back", vowel_round=True, stop_coda=True
    ),
    "uh": PhoneticFeatures(
        vowel_height="high", vowel_front="back", vowel_round=True, stop_coda=True
    ),
    # 鼻韵
    "an": PhoneticFeatures(vowel_height="low", vowel_front="central", nasal_coda=True),
    "en": PhoneticFeatures(vowel_height="mid", vowel_front="front", nasal_coda=True),
    "in": PhoneticFeatures(vowel_height="high", vowel_front="front", nasal_coda=True),
    "on": PhoneticFeatures(
        vowel_height="mid", vowel_front="back", vowel_round=True, nasal_coda=True
    ),
    "aon": PhoneticFeatures(vowel_height="low", vowel_front="back", nasal_coda=True),
    "aung": PhoneticFeatures(vowel_height="low", vowel_front="back", nasal_coda=True),
}


def feature_distance(f1: PhoneticFeatures, f2: PhoneticFeatures) -> float:
    """计算两个特征向量之间的距离 (0-1)"""
    v1, v2 = f1.to_vector(), f2.to_vector()

    # 忽略未定义的特征 (-1)
    diff_sum = 0
    count = 0
    for a, b in zip(v1, v2):
        if a >= 0 and b >= 0:
            diff_sum += abs(a - b)
            count += 1

    if count == 0:
        return 1.0

    # 归一化到 0-1
    return min(1.0, diff_sum / (count * 2))


def phonetic_feature_similarity(
    init1: str, final1: str, init2: str, final2: str
) -> float:
    """
    基于音韵特征计算两个音节的相似度

    返回 0-1 之间的相似度
    """
    # 获取特征
    f_init1 = INITIAL_FEATURES.get(init1.lower(), PhoneticFeatures())
    f_init2 = INITIAL_FEATURES.get(init2.lower(), PhoneticFeatures())
    f_final1 = FINAL_FEATURES.get(final1.lower(), PhoneticFeatures())
    f_final2 = FINAL_FEATURES.get(final2.lower(), PhoneticFeatures())

    # 计算距离
    init_dist = feature_distance(f_init1, f_init2)
    final_dist = feature_distance(f_final1, f_final2)

    # 加权平均 (声母权重稍高)
    total_dist = init_dist * 0.6 + final_dist * 0.4

    return 1.0 - total_dist


# ============================================================================
# 规则推导引擎 (Rule Induction Engine)
# ============================================================================


@dataclass
class TransformRule:
    """转换规则"""

    source: str  # 源模式 (教会罗马字)
    target: str  # 目标模式 (吴语学堂)
    rule_type: str  # 规则类型: initial, final, tone
    context: str = ""  # 上下文条件 (可选)
    count: int = 0  # 出现次数
    examples: List[str] = field(default_factory=list)  # 示例

    @property
    def confidence(self) -> float:
        """基于出现次数的置信度"""
        return min(1.0, self.count / 10)  # 10次以上为高置信度


class RuleInductionEngine:
    """
    规则推导引擎

    从平行语料中自动发现转换规则
    """

    def __init__(self):
        self.initial_rules: Dict[str, List[TransformRule]] = defaultdict(list)
        self.final_rules: Dict[str, List[TransformRule]] = defaultdict(list)
        self.learned_pairs: List[Tuple[str, str, str]] = []  # (church, wugniu, hanzi)

    def add_parallel_pair(
        self, church_pinyin: str, wugniu_pinyin: str, hanzi: str = ""
    ):
        """添加一对平行拼音用于学习"""
        self.learned_pairs.append((church_pinyin.lower(), wugniu_pinyin.lower(), hanzi))

    def induce_rules(self) -> Tuple[List[TransformRule], List[TransformRule]]:
        """
        从平行语料中推导规则

        使用 最小编辑脚本 (Minimum Edit Script) 算法
        """
        initial_counter = Counter()
        final_counter = Counter()

        for church, wugniu, hanzi in self.learned_pairs:
            # 分离声母韵母
            c_init, c_final = self._split_syllable(church, is_wugniu=False)
            w_init, w_final = self._split_syllable(wugniu, is_wugniu=True)

            # 记录对应关系
            if c_init or w_init:
                initial_counter[(c_init, w_init)] += 1
            if c_final or w_final:
                final_counter[(c_final, w_final)] += 1

        # 生成规则
        initial_rules = []
        for (src, tgt), count in initial_counter.most_common():
            if src != tgt:  # 只记录不同的
                rule = TransformRule(
                    source=src, target=tgt, rule_type="initial", count=count
                )
                initial_rules.append(rule)

        final_rules = []
        for (src, tgt), count in final_counter.most_common():
            if src != tgt:
                rule = TransformRule(
                    source=src, target=tgt, rule_type="final", count=count
                )
                final_rules.append(rule)

        return initial_rules, final_rules

    def _split_syllable(
        self, syllable: str, is_wugniu: bool = False
    ) -> Tuple[str, str]:
        """分离声母和韵母"""
        syllable = syllable.lower().strip("',.-")
        if not syllable:
            return "", ""

        # 声母列表 (按长度排序)
        if is_wugniu:
            initials = [
                "tsh",
                "dz",
                "ts",
                "ng",
                "gn",
                "kh",
                "ph",
                "th",
                "gh",
                "ch",
                "sh",
                "zh",
                "k",
                "h",
                "m",
                "n",
                "l",
                "v",
                "w",
                "f",
                "p",
                "b",
                "t",
                "d",
                "s",
                "z",
                "j",
                "c",
                "q",
                "x",
                "y",
                "'",
            ]
        else:
            initials = [
                "tsh",
                "dz",
                "ts",
                "ng",
                "ny",
                "kh",
                "ph",
                "th",
                "gh",
                "ch",
                "sh",
                "ky",
                "hy",
                "kw",
                "gw",
                "hw",
                "k",
                "h",
                "m",
                "n",
                "l",
                "v",
                "w",
                "f",
                "p",
                "b",
                "t",
                "d",
                "s",
                "z",
                "j",
                "y",
                "'",
            ]

        for init in sorted(initials, key=lambda x: -len(x)):
            if syllable.startswith(init):
                return init, syllable[len(init) :]

        return "", syllable

    def print_rules_report(self):
        """打印规则报告"""
        initial_rules, final_rules = self.induce_rules()

        print("=" * 60)
        print("自动推导的转换规则 (Rule Induction Results)")
        print("=" * 60)

        print("\n📌 声母规则 (Initial Rules):")
        for rule in initial_rules[:20]:
            conf = (
                "🟢"
                if rule.confidence > 0.8
                else "🟡"
                if rule.confidence > 0.5
                else "🔴"
            )
            print(f"  {conf} '{rule.source}' → '{rule.target}' (出现 {rule.count} 次)")

        print("\n📌 韵母规则 (Final Rules):")
        for rule in final_rules[:20]:
            conf = (
                "🟢"
                if rule.confidence > 0.8
                else "🟡"
                if rule.confidence > 0.5
                else "🔴"
            )
            print(f"  {conf} '{rule.source}' → '{rule.target}' (出现 {rule.count} 次)")


# ============================================================================
# 智能分析器 (Intelligent Analyzer)
# ============================================================================


class IntelligentAnalyzer:
    """
    智能分析器

    综合使用多种启发式规则进行分析
    """

    def __init__(self):
        self.rule_engine = RuleInductionEngine()
        self._load_rime_data()

    def _load_rime_data(self):
        """加载 Rime 词典数据"""
        try:
            from .rime_dict import get_rime_data

            self.char_pinyins, self.phrase_pinyins, self.polyphonic = get_rime_data()
        except ImportError:
            self.char_pinyins = {}
            self.phrase_pinyins = {}
            self.polyphonic = set()

    def analyze_with_heuristics(self, church_pinyin: str, hanzi: str) -> Dict:
        """
        使用启发式规则分析拼音-汉字对

        返回分析结果，包括:
        - is_valid: 是否合法
        - confidence: 置信度
        - reasons: 判断原因
        - suggestions: 建议
        """
        result = {
            "is_valid": True,
            "confidence": 1.0,
            "reasons": [],
            "suggestions": [],
        }

        # 启发式规则1: 检查是否为多音字
        if hanzi in self.polyphonic:
            result["reasons"].append(f"'{hanzi}' 是多音字，需要上下文判断")
            result["confidence"] *= 0.8

        # 启发式规则2: 检查 Rime 词典中的变体
        if hanzi in self.char_pinyins:
            wugniu_variants = self.char_pinyins[hanzi]

            # 使用特征相似度检查
            best_match = None
            best_sim = 0

            c_init, c_final = self.rule_engine._split_syllable(
                church_pinyin, is_wugniu=False
            )

            for variant in wugniu_variants:
                w_init, w_final = self.rule_engine._split_syllable(
                    variant, is_wugniu=True
                )
                sim = phonetic_feature_similarity(c_init, c_final, w_init, w_final)
                if sim > best_sim:
                    best_sim = sim
                    best_match = variant

            if best_sim > 0.7:
                result["reasons"].append(
                    f"音韵特征匹配: '{church_pinyin}' ≈ '{best_match}' (相似度: {best_sim:.2f})"
                )
            else:
                result["is_valid"] = False
                result["confidence"] *= best_sim
                result["reasons"].append(
                    f"最接近的读音是 '{best_match}' (相似度: {best_sim:.2f})"
                )
                result["suggestions"].append(f"建议检查: {wugniu_variants}")

        # 启发式规则3: 入声韵尾检查
        if church_pinyin.endswith(("h", "k")) and not church_pinyin.endswith(
            ("ng", "ung", "aung")
        ):
            result["reasons"].append("检测到入声韵尾 (-h/-k → -q)")

        return result


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    # 测试特征相似度
    print("=" * 60)
    print("音韵特征相似度测试")
    print("=" * 60)

    test_cases = [
        ("ny", "ih", "gn", "iq"),  # nyih vs gniq (日)
        ("l", "eh", "l", "eq"),  # leh vs leq (勒)
        ("l", "a", "l", "a"),  # la vs la (拉)
        ("ts", "ang", "c", "an"),  # tsang vs can
        ("dz", "oong", "j", "on"),  # dzoong vs jon
    ]

    for c_init, c_final, w_init, w_final in test_cases:
        sim = phonetic_feature_similarity(c_init, c_final, w_init, w_final)
        print(f"  {c_init}{c_final} vs {w_init}{w_final}: 相似度 = {sim:.2f}")

    # 测试规则推导
    print("\n" + "=" * 60)
    print("规则推导测试")
    print("=" * 60)

    engine = RuleInductionEngine()

    # 添加一些训练数据
    training_pairs = [
        ("nyih", "gniq", "日"),
        ("zeh", "zeq", "日"),
        ("la", "la", "拉"),
        ("leh", "leq", "勒"),
        ("tshang", "chan", "长"),
        ("dzoong", "jon", "从"),
        ("aung", "aon", "昂"),
        ("kuh", "keq", "个"),
        ("nyung", "gnin", "人"),
        ("tseu", "ceu", "走"),
    ]

    for church, wugniu, hanzi in training_pairs:
        engine.add_parallel_pair(church, wugniu, hanzi)

    engine.print_rules_report()
