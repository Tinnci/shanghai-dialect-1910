import argparse
import sys
from pathlib import Path

# Add src to python path to ensure local imports work
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.loader import load_lessons
from src.analyzers.phonetic import analyze_phonetic_consistency
from src.analyzers.displacement import analyze_displacement
from src.analyzers.stats import generate_priority_list
from src.tasks.pdf_extract import run_extraction
from src.tasks.jxl_convert import run_conversion
from src.fixer import run_fixer


def main():
    parser = argparse.ArgumentParser(
        description="Shanghai Dialect Project XTask Runner"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Analysis Commands
    parser_analyze = subparsers.add_parser("analyze", help="Run quality analysis tools")
    parser_analyze.add_argument(
        "type",
        choices=["phonetic", "displacement", "priority", "all"],
        help="Analysis type",
    )
    parser_analyze.add_argument(
        "target", nargs="?", help="Optional target file (e.g. lesson-49)"
    )

    # Fix Commands
    parser_fix = subparsers.add_parser("fix", help="Auto-fix Ruby pair issues")
    parser_fix.add_argument(
        "target",
        nargs="?",
        default="--all",
        help="Target file (e.g., lesson-26) or --all",
    )
    parser_fix.add_argument(
        "--dry-run", action="store_true", help="Show fixes without applying"
    )
    parser_fix.add_argument(
        "--interactive", "-i", action="store_true", help="Confirm each fix"
    )
    parser_fix.add_argument(
        "--auto", action="store_true", help="Apply all fixes without confirmation"
    )
    parser_fix.add_argument(
        "--no-backup", action="store_true", help="Don't backup files before fixing"
    )

    # Learn Commands
    parser_learn = subparsers.add_parser(
        "learn", help="Automatic rule learning from corpus"
    )
    parser_learn.add_argument(
        "--save", action="store_true", help="Save learned rules to knowledge base"
    )

    # G2P Commands
    parser_g2p = subparsers.add_parser("g2p", help="Convert Pott Romanization to IPA")
    parser_g2p.add_argument("text", nargs="+", help="Text to convert (space separated)")

    # Synthesize Commands (TTS)
    parser_synth = subparsers.add_parser(
        "synthesize", help="Synthesize speech from Pott Romanization"
    )
    parser_synth.add_argument(
        "text", nargs="+", help="Text to synthesize (Pott romanization)"
    )
    parser_synth.add_argument(
        "--output", "-o", type=str, default=None, help="Output audio file path"
    )
    parser_synth.add_argument(
        "--model", type=str, default=None, help="Path to Matcha-TTS checkpoint"
    )
    parser_synth.add_argument(
        "--vocoder", type=str, default=None, help="Path to HiFi-GAN checkpoint"
    )
    parser_synth.add_argument(
        "--steps", type=int, default=10, help="Number of ODE solver steps"
    )
    parser_synth.add_argument(
        "--temperature", type=float, default=0.667, help="Sampling temperature"
    )
    parser_synth.add_argument(
        "--length-scale", type=float, default=1.0, help="Duration scaling factor"
    )

    # Prepare Data Commands (TTS)
    parser_prep = subparsers.add_parser(
        "prepare", help="Prepare TTS training data from MagicData corpus"
    )
    parser_prep.add_argument(
        "--source",
        type=str,
        default=str(Path.home() / "下载" / "Samples"),
        help="Source directory containing MagicData corpora",
    )
    parser_prep.add_argument(
        "--output", "-o", type=str, default="data", help="Output directory"
    )
    parser_prep.add_argument(
        "--skip-conv",
        action="store_true",
        help="Skip conversational corpus (faster, scripted only)",
    )

    # Annotate IPA Command
    parser_annot = subparsers.add_parser(
        "annotate-ipa", help="Add IPA annotations to training filelists"
    )
    parser_annot.add_argument(
        "--input", "-i", type=str, default="data", help="Data directory with filelists"
    )
    parser_annot.add_argument(
        "--filelist", type=str, default=None, help="Specific filelist to annotate"
    )

    # Train Command
    parser_train = subparsers.add_parser("train", help="Train TTS model")
    parser_train.add_argument(
        "--config",
        type=str,
        default="configs/shanghai_1910.yaml",
        help="Training config file",
    )
    parser_train.add_argument(
        "--resume", type=str, default=None, help="Resume from checkpoint"
    )
    parser_train.add_argument(
        "--dry-run", action="store_true", help="Validate config without training"
    )

    # Task Commands
    subparsers.add_parser("extract", help="Extract images and pages from source PDF")
    subparsers.add_parser("convert", help="Convert extracted images to JPEG XL")
    subparsers.add_parser(
        "compile", help="Compile Typst project to PDF with descriptive name"
    )
    subparsers.add_parser(
        "export-ipa", help="Export exercises to JSONL with IPA and Modern Pinyin"
    )

    # Global args
    parser.add_argument(
        "--dir",
        type=str,
        default="./typst_source/contents/lessons",
        help="Path to lessons directory",
    )
    parser.add_argument("--root", type=str, default=".", help="Project root directory")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    project_root = Path(args.root).resolve()
    lessons_dir = Path(args.dir).resolve()

    # Route commands
    if args.command == "extract":
        run_extraction(project_root)

    elif args.command == "convert":
        run_conversion(project_root)

    elif args.command == "compile":
        import subprocess

        typst_main = project_root / "typst_source" / "main.typ"
        output_pdf = project_root / "shanghai-dialect-exercises.pdf"
        print(f"Compiling {typst_main} to {output_pdf}...")
        try:
            subprocess.run(
                ["typst", "compile", str(typst_main), str(output_pdf)], check=True
            )
            print("✓ Compilation successful!")
        except subprocess.CalledProcessError as e:
            print(f"✗ Compilation failed: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print("✗ Error: 'typst' command not found. Please install Typst.")

    elif args.command == "export-ipa":
        from src.tasks.export_ipa import run_export_ipa

        run_export_ipa(project_root)

    elif args.command == "learn":
        from src.learn_rules import learn_rules_from_corpus
        from src.knowledge_base import get_knowledge_base

        initial_rules, final_rules = learn_rules_from_corpus(lessons_dir)

        if args.save:
            kb = get_knowledge_base()
            kb.update_rules(initial_rules, final_rules)
            kb.save()

    elif args.command == "g2p":
        from src.pott_g2p import PottToIPA

        converter = PottToIPA()

        text = " ".join(args.text)
        results = converter.convert_phrase(text)

        print("\nConversion Results:")
        print(f"{'Original':<15} {'IPA':<15} {'Modern (Wugniu)':<20} {'Conf':<10}")
        print("-" * 60)

        ipa_list = []
        for item in results:
            if "original" in item:
                print(
                    f"{item['original']:<15} {item['ipa']:<15} {item['wugniu']:<20} {item['confidence']:.2f}"
                )
                ipa_list.append(item["ipa"])

        print("-" * 60)
        print(f"Full IPA Sentence: {' '.join(ipa_list)}")
        print()

    elif args.command == "synthesize":
        from src.tasks.synthesize import run_synthesize

        text = " ".join(args.text)
        output_path = Path(args.output) if args.output else None
        model_ckpt = Path(args.model) if args.model else None
        vocoder_ckpt = Path(args.vocoder) if args.vocoder else None

        run_synthesize(
            text=text,
            output_path=output_path,
            model_checkpoint=model_ckpt,
            vocoder_checkpoint=vocoder_ckpt,
            n_timesteps=args.steps,
            temperature=args.temperature,
            length_scale=getattr(args, "length_scale", 1.0),
        )

    elif args.command == "prepare":
        from src.tasks.prepare_magicdata import run_prepare

        run_prepare(
            source_dir=Path(args.source),
            output_dir=Path(args.output),
            skip_conversational=args.skip_conv,
        )

    elif args.command == "annotate-ipa":
        from src.tasks.annotate_ipa import run_annotate_ipa

        run_annotate_ipa(
            input_dir=Path(args.input),
            filelist=Path(args.filelist) if args.filelist else None,
        )

    elif args.command == "train":
        print("🚧 Training command not yet implemented.")
        print("   Use: uv run python -m matcha.train --config <config>")
        if args.dry_run:
            print("   (dry-run mode)")

    elif args.command == "fix":
        run_fixer(
            lessons_dir=lessons_dir,
            target=args.target,
            dry_run=args.dry_run,
            interactive=args.interactive,
            auto=args.auto,
            backup=not args.no_backup,
        )

    elif args.command == "analyze":
        print(f"Loading lessons from: {lessons_dir}")
        lessons = load_lessons(lessons_dir)
        print(f"Loaded {len(lessons)} files.")

        if args.type in ["phonetic", "all"]:
            analyze_phonetic_consistency(
                lessons, str(project_root / "phonetic_analysis_v2.json")
            )

        if args.type in ["displacement", "all"]:
            analyze_displacement(lessons, project_root, target_filter=args.target)

        if args.type in ["priority", "all"]:
            generate_priority_list(lessons, str(project_root / "priority_report.json"))


if __name__ == "__main__":
    main()
