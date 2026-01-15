from pathlib import Path
from dataclasses import dataclass, field
from typing import List
from .utils import extract_ruby_pairs


@dataclass
class RubyPair:
    pinyin: str
    hanzi: str
    filename: str
    position: int

    @property
    def normalized_pinyin(self):
        # Local import or use helper
        from .utils import normalize_pinyin

        return normalize_pinyin(self.pinyin)


@dataclass
class LessonFile:
    path: Path
    filename: str
    content: str
    pairs: List[RubyPair] = field(default_factory=list)


def load_lessons(base_dir: Path) -> List[LessonFile]:
    """加载指定目录下的所有 lesson-*.typ 文件"""
    lessons = []

    # Check if path exists
    if not base_dir.exists():
        print(f"Warning: Directory {base_dir} does not exist.")
        return []

    for f in sorted(base_dir.glob("lesson-*.typ")):
        try:
            content = f.read_text(encoding="utf-8")
            raw_pairs = extract_ruby_pairs(content, f.name)

            pairs = [RubyPair(p, h, fname, pos) for p, h, fname, pos in raw_pairs]

            lessons.append(
                LessonFile(path=f, filename=f.name, content=content, pairs=pairs)
            )
        except Exception as e:
            print(f"Error loading {f.name}: {e}")

    return lessons
