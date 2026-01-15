import json
import re
from pathlib import Path
from typing import List, Any
from src.loader import load_lessons, LessonFile
from src.pott_g2p import PottToIPA


class IPAExporter:
    def __init__(self, output_file: Path):
        self.output_file = output_file
        self.converter = PottToIPA()

    def export(self, lessons_dir: Path):
        """Export all lessons to JSONL format."""
        lessons = load_lessons(lessons_dir)
        print(f"Loaded {len(lessons)} lessons.")

        with open(self.output_file, "w", encoding="utf-8") as f:
            for lesson in lessons:
                self._process_lesson(lesson, f)

        print(f"Export completed: {self.output_file}")

    def _process_lesson(self, lesson: LessonFile, file_handle):
        """Process a single lesson and write sentences to file."""
        current_sentence_pairs = []

        # We try to segment sentences based on punctuation in the pinyin/hanzi
        # Common sentence terminators
        terminators = re.compile(r"[.?!。？！]$")

        for pair in lesson.pairs:
            current_sentence_pairs.append(pair)

            # Check if this pair ends a sentence
            # We check both pinyin and hanzi for robustness
            is_end = False

            # Check pinyin (often has . or ?)
            if terminators.search(pair.pinyin.strip()):
                is_end = True
            # Check hanzi (often has 。 or ？)
            elif terminators.search(pair.hanzi.strip()):
                is_end = True

            if is_end:
                self._write_sentence(
                    lesson.filename, current_sentence_pairs, file_handle
                )
                current_sentence_pairs = []

        # Write any remaining pairs
        if current_sentence_pairs:
            self._write_sentence(lesson.filename, current_sentence_pairs, file_handle)

    def _write_sentence(self, filename: str, pairs: List[Any], file_handle):
        """Construct and write a sentence object."""
        if not pairs:
            return

        # Reconstruct full text
        full_hanzi = "".join(p.hanzi for p in pairs)
        full_pott = " ".join(p.pinyin for p in pairs)

        # Generate tokens with IPA and Modern prediction
        tokens = []
        full_ipa_list = []

        for p in pairs:
            # Clean pinyin for conversion (remove punctuation)
            clean_pinyin = re.sub(r"[^\w\s\'-]", "", p.pinyin)

            # Convert
            # Note: A single ruby pair might strictly be one word, but let's treat it as a phrase just in case
            # Using convert_phrase to handle any internal spacing, though usually it's one token.
            conversion_results = self.converter.convert_phrase(clean_pinyin)

            # We usually expect 1 main token per pair, but convert_phrase returns a list
            # We'll aggregate them into one token object for the JSON output if possible,
            # or just list the sub-components.

            token_ipa = ""
            token_wugniu = ""
            token_conf = 0.0

            if conversion_results:
                # Join parts if multiple
                token_ipa = "".join(item.get("ipa", "") for item in conversion_results)
                token_wugniu = "".join(
                    item.get("wugniu", "") for item in conversion_results
                )
                # Average confidence
                confs = [
                    item.get("confidence", 0)
                    for item in conversion_results
                    if "confidence" in item
                ]
                if confs:
                    token_conf = sum(confs) / len(confs)

            full_ipa_list.append(token_ipa)

            tokens.append(
                {
                    "hanzi": p.hanzi,
                    "pott": p.pinyin,
                    "ipa": token_ipa,
                    "wugniu": token_wugniu,
                    "confidence": round(token_conf, 2),
                }
            )

        full_ipa = " ".join(full_ipa_list)

        record = {
            "source_file": filename,
            "content": {"hanzi": full_hanzi, "pott": full_pott, "ipa": full_ipa},
            "tokens": tokens,
        }

        file_handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_export_ipa(project_root: Path):
    output_path = project_root / "shanghai_dialect_ipa.jsonl"
    lessons_dir = project_root / "typst_source/contents/lessons"

    exporter = IPAExporter(output_path)
    exporter.export(lessons_dir)
