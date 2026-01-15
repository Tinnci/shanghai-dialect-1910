"""
IPA Annotation for TTS Training Data

Converts Chinese transcriptions to IPA using Rime dictionary.

Usage:
    uv run python xtask.py annotate-ipa --input data/filelists/train.txt
"""

import sys
from pathlib import Path

# Ensure project root is in path
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def annotate_filelist(
    input_path: Path,
    output_path: Path = None,
    char_pinyins: dict = None,
):
    """
    Add IPA annotations to a filelist.

    Input format:  path|speaker|text
    Output format: path|speaker|text|ipa
    """
    from src.wugniu_to_ipa import hanzi_to_ipa
    from src.rime_dict import get_rime_data

    if char_pinyins is None:
        char_pinyins, _, _ = get_rime_data()

    if output_path is None:
        output_path = input_path.with_suffix(".ipa.txt")

    total = 0
    success = 0
    total_coverage = 0.0

    with (
        open(input_path, "r", encoding="utf-8") as fin,
        open(output_path, "w", encoding="utf-8") as fout,
    ):
        for line in fin:
            line = line.strip()
            if not line:
                continue

            parts = line.split("|")
            if len(parts) < 3:
                continue

            path, speaker, text = parts[0], parts[1], parts[2]

            # Convert to IPA
            ipa, coverage = hanzi_to_ipa(text, char_pinyins)

            # Write output
            fout.write(f"{path}|{speaker}|{text}|{ipa}\n")

            total += 1
            if coverage > 0:
                success += 1
                total_coverage += coverage

    avg_coverage = total_coverage / success if success > 0 else 0.0
    print(f"✓ Annotated {total} entries")
    print(f"  Average coverage: {avg_coverage:.1%}")
    print(f"  Output: {output_path}")

    return output_path


def run_annotate_ipa(
    input_dir: Path = None,
    filelist: Path = None,
):
    """
    Main entry point for IPA annotation.
    """
    print("=" * 60)
    print("🔤 IPA Annotation for TTS Training Data")
    print("=" * 60)

    # Load Rime dictionary once
    from src.rime_dict import get_rime_data

    char_pinyins, phrase_pinyins, polyphonic = get_rime_data()
    print(f"📚 Loaded Rime dictionary: {len(char_pinyins)} characters")

    if filelist:
        # Annotate single file
        annotate_filelist(filelist, char_pinyins=char_pinyins)
    elif input_dir:
        # Annotate all filelists in directory
        filelists_dir = input_dir / "filelists"
        if not filelists_dir.exists():
            print(f"❌ Filelists directory not found: {filelists_dir}")
            return

        for txt_file in filelists_dir.glob("*.txt"):
            # Skip already annotated files
            if ".ipa." in txt_file.name:
                continue
            print(f"\n📝 Processing {txt_file.name}...")
            annotate_filelist(txt_file, char_pinyins=char_pinyins)
    else:
        print("❌ Please specify --input or --filelist")
        return

    print("\n" + "=" * 60)
    print("✓ Annotation complete!")
    print("=" * 60)


if __name__ == "__main__":
    run_annotate_ipa(input_dir=Path("data"))
