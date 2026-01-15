"""
知识库管理模块 (Knowledge Base Management)

负责持久化存储和加载项目中学到的知识，包括：
1. 自动推导的音韵转换规则
2. 缓存的词典数据
3. 系统配置和阈值

遵循系统工程的数据持久化分层原则。
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

from .rule_induction import TransformRule

@dataclass
class KnowledgeConfig:
    """知识库配置"""
    confidence_threshold: float = 0.8  # 规则采纳阈值
    similarity_threshold: float = 0.7  # 相似度判定阈值
    last_updated: str = ""             # 最后更新时间

class KnowledgeBase:
    """
    知识库管理器
    
    单例模式，系统唯一的知识来源。
    """
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.rules_file = data_dir / "phonetic_rules.json"
        
        # 内存中的知识数据
        self.initial_rules: List[TransformRule] = []
        self.final_rules: List[TransformRule] = []
        self.config = KnowledgeConfig()
        
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
    def load(self):
        """从磁盘加载知识库"""
        if self.rules_file.exists():
            try:
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.initial_rules = [TransformRule(**r) for r in data.get("initial_rules", [])]
                    self.final_rules = [TransformRule(**r) for r in data.get("final_rules", [])]
                    self.config = KnowledgeConfig(**data.get("config", {}))
                print(f"📚 已加载知识库: {len(self.initial_rules)} 条声母规则, {len(self.final_rules)} 条韵母规则")
            except Exception as e:
                print(f"⚠️ 加载知识库失败: {e}")
        else:
            print("ℹ️ 知识库不存在，使用默认配置")
            
    def save(self):
        """持久化保存到磁盘"""
        data = {
            "initial_rules": [asdict(r) for r in self.initial_rules],
            "final_rules": [asdict(r) for r in self.final_rules],
            "config": asdict(self.config)
        }
        
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 知识库已保存至: {self.rules_file}")
        
    def update_rules(self, initial_rules: List[TransformRule], final_rules: List[TransformRule]):
        """更新规则库（只保留高置信度规则）"""
        # 过滤低置信度规则
        self.initial_rules = [r for r in initial_rules if r.confidence >= self.config.confidence_threshold]
        self.final_rules = [r for r in final_rules if r.confidence >= self.config.confidence_threshold]
        
        from datetime import datetime
        self.config.last_updated = datetime.now().isoformat()
        
    def get_match(self, church_py: str, rule_type: str = "initial") -> str:
        """根据规则查询最佳匹配"""
        rules = self.initial_rules if rule_type == "initial" else self.final_rules
        for rule in rules:
            if rule.source == church_py:
                return rule.target
        return ""

# 全局单例
_KB_INSTANCE = None

def get_knowledge_base() -> KnowledgeBase:
    global _KB_INSTANCE
    if _KB_INSTANCE is None:
        # 默认存储在项目根目录下的 .agent/data
        root = Path(__file__).parent.parent
        _KB_INSTANCE = KnowledgeBase(root / ".agent/data")
        _KB_INSTANCE.load()
    return _KB_INSTANCE
