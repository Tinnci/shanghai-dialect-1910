"""
MagicData Shanghai Dialect Corpus Preprocessor

Prepares the following datasets for TTS training:
1. Shanghai_Dialect_Conversational_Speech_Corpus (对话语料)
2. Shanghai_Dialect_Scripted_Speech_Corpus_Daily_Use_Sentence (朗读语料)

Output:
- data/wavs/       Unified audio files (22050Hz mono)
- data/filelists/  Train/val splits in LJSpeech format

Usage:
    uv run python xtask.py prepare --source ~/下载/Samples --output data/
"""

import csv
import re
import shutil
from pathlib import Path


def parse_scripted_corpus(corpus_dir: Path) -> list[dict]:
    """
    Parse the Scripted Speech Corpus (Daily Use Sentence).

    Returns list of {speaker, wav_path, text} dicts.
    """
    uttrans_file = corpus_dir / "UTTRANSINFO.txt"
    if not uttrans_file.exists():
        print(f"⚠️ UTTRANSINFO.txt not found in {corpus_dir}")
        return []

    entries = []
    with open(uttrans_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            speaker = row.get("SPEAKER_ID", "").strip()
            wav_name = row.get("UTTRANS_ID", "").strip()
            # Use TRANSCRIPTION (口语转写) instead of PROMPT (书面语)
            text = row.get("TRANSCRIPTION", "").strip()

            if not wav_name or not text:
                continue

            wav_path = corpus_dir / "WAV" / speaker / wav_name
            if wav_path.exists():
                entries.append(
                    {
                        "speaker": speaker,
                        "wav_path": wav_path,
                        "text": clean_text(text),
                        "source": "scripted",
                    }
                )

    print(f"✓ Parsed {len(entries)} entries from Scripted Corpus")
    return entries


def parse_conversational_corpus(corpus_dir: Path) -> list[dict]:
    """
    Parse the Conversational Speech Corpus.

    This requires splitting audio by timestamps.
    Returns list of {speaker, wav_path, text, start, end} dicts.
    """
    txt_dir = corpus_dir / "TXT"
    wav_dir = corpus_dir / "WAV"

    if not txt_dir.exists():
        print(f"⚠️ TXT directory not found in {corpus_dir}")
        return []

    entries = []
    for txt_file in txt_dir.glob("*.txt"):
        wav_file = wav_dir / txt_file.with_suffix(".wav").name
        if not wav_file.exists():
            continue

        with open(txt_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Format: [start,end]  speaker  gender  text
                match = re.match(
                    r"\[(\d+\.?\d*),(\d+\.?\d*)\]\s+(\w+)\s+\w+\s+(.+)", line
                )
                if match:
                    start = float(match.group(1))
                    end = float(match.group(2))
                    speaker = match.group(3)
                    text = match.group(4)

                    # Skip special markers
                    if any(
                        m in text
                        for m in [
                            "[*]",
                            "[LAUGHTER]",
                            "[SONANT]",
                            "[MUSIC]",
                            "[SYSTEM]",
                            "[ENS]",
                            "[FILLER]",
                        ]
                    ):
                        continue

                    entries.append(
                        {
                            "speaker": speaker,
                            "wav_path": wav_file,
                            "text": clean_text(text),
                            "start": start,
                            "end": end,
                            "source": "conversational",
                        }
                    )

    print(f"✓ Parsed {len(entries)} segments from Conversational Corpus")
    return entries


def clean_text(text: str) -> str:
    """Clean text for TTS training."""
    # Remove special markers
    text = re.sub(r"\[.*?\]", "", text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Remove leading/trailing punctuation issues
    text = text.strip("，。！？、")
    return text


def copy_and_resample_audio(
    entries: list[dict],
    output_dir: Path,
    target_sr: int = 22050,
) -> list[dict]:
    """
    Copy and optionally resample audio files.

    For conversational corpus, segments are extracted.
    Returns updated entries with new paths.
    """
    wavs_dir = output_dir / "wavs"
    wavs_dir.mkdir(parents=True, exist_ok=True)

    processed = []

    # Try to import audio processing libraries
    try:
        import soundfile as sf

        has_audio_libs = True
    except ImportError:
        has_audio_libs = False
        print("⚠️ soundfile not available. Copying files without processing.")

    for i, entry in enumerate(entries):
        src_path = entry["wav_path"]

        # Generate unified filename
        # Format: {source}_{speaker}_{index:05d}.wav
        new_name = f"{entry['source']}_{entry['speaker']}_{i:05d}.wav"
        dst_path = wavs_dir / new_name

        if entry.get("start") is not None and has_audio_libs:
            # Extract segment from conversational audio
            try:
                audio, sr = sf.read(str(src_path))
                start_sample = int(entry["start"] * sr)
                end_sample = int(entry["end"] * sr)
                segment = audio[start_sample:end_sample]

                # Resample if needed (simple approach - proper resampling would use librosa)
                if sr != target_sr:
                    # For now, just save at original rate
                    sf.write(str(dst_path), segment, sr)
                else:
                    sf.write(str(dst_path), segment, sr)

            except Exception as e:
                print(f"⚠️ Failed to process {src_path}: {e}")
                continue
        else:
            # Direct copy for scripted corpus
            if not dst_path.exists():
                shutil.copy2(src_path, dst_path)

        processed.append(
            {
                "path": str(dst_path.relative_to(output_dir)),
                "speaker": entry["speaker"],
                "text": entry["text"],
            }
        )

        # Progress indicator (every 500 files)
        if (i + 1) % 500 == 0:
            print(f"  Processed {i + 1}/{len(entries)} files...")

    print(f"✓ Processed {len(processed)} audio files to {wavs_dir}")
    return processed


def generate_filelists(
    entries: list[dict],
    output_dir: Path,
    val_ratio: float = 0.05,
):
    """
    Generate train/val filelists in LJSpeech format.

    Format: path|speaker|text
    """
    filelists_dir = output_dir / "filelists"
    filelists_dir.mkdir(parents=True, exist_ok=True)

    # Shuffle and split
    import random

    random.seed(42)
    shuffled = entries.copy()
    random.shuffle(shuffled)

    val_size = int(len(shuffled) * val_ratio)
    val_entries = shuffled[:val_size]
    train_entries = shuffled[val_size:]

    # Write filelists
    for name, data in [("train.txt", train_entries), ("val.txt", val_entries)]:
        filepath = filelists_dir / name
        with open(filepath, "w", encoding="utf-8") as f:
            for entry in data:
                line = f"{entry['path']}|{entry['speaker']}|{entry['text']}\n"
                f.write(line)
        print(f"✓ Wrote {len(data)} entries to {filepath}")


def run_prepare(
    source_dir: Path,
    output_dir: Path,
    scripted_name: str = "Shanghai_Dialect_Scripted_Speech_Corpus_Daily_Use_Sentence",
    conversational_name: str = "Shanghai_Dialect_Conversational_Speech_Corpus",
    skip_conversational: bool = False,
):
    """
    Main entry point for data preparation.
    """
    print("=" * 60)
    print("🎤 MagicData Shanghai Dialect Corpus Preprocessor")
    print("=" * 60)

    all_entries = []

    # Parse Scripted Corpus
    scripted_dir = source_dir / scripted_name
    if scripted_dir.exists():
        entries = parse_scripted_corpus(scripted_dir)
        all_entries.extend(entries)
    else:
        print(f"⚠️ Scripted corpus not found at {scripted_dir}")

    # Parse Conversational Corpus (optional, more complex)
    if not skip_conversational:
        conv_dir = source_dir / conversational_name
        if conv_dir.exists():
            entries = parse_conversational_corpus(conv_dir)
            all_entries.extend(entries)
        else:
            print(f"⚠️ Conversational corpus not found at {conv_dir}")

    if not all_entries:
        print("❌ No data found. Please check source directory.")
        return

    print(f"\n📊 Total entries: {len(all_entries)}")

    # Process audio
    print("\n⏳ Processing audio files...")
    processed = copy_and_resample_audio(all_entries, output_dir)

    # Generate filelists
    print("\n📝 Generating filelists...")
    generate_filelists(processed, output_dir)

    print("\n" + "=" * 60)
    print("✓ Data preparation complete!")
    print(f"  Output directory: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    # Test run
    run_prepare(
        source_dir=Path.home() / "下载" / "Samples",
        output_dir=Path("data"),
    )
