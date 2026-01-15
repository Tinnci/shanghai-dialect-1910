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
    parser = argparse.ArgumentParser(description="Shanghai Dialect Project XTask Runner")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analysis Commands
    parser_analyze = subparsers.add_parser("analyze", help="Run quality analysis tools")
    parser_analyze.add_argument("type", choices=['phonetic', 'displacement', 'priority', 'all'], help="Analysis type")
    parser_analyze.add_argument("target", nargs='?', help="Optional target file (e.g. lesson-49)")
    
    # Fix Commands
    parser_fix = subparsers.add_parser("fix", help="Auto-fix Ruby pair issues")
    parser_fix.add_argument("target", nargs='?', default="--all", help="Target file (e.g., lesson-26) or --all")
    parser_fix.add_argument("--dry-run", action="store_true", help="Show fixes without applying")
    parser_fix.add_argument("--interactive", "-i", action="store_true", help="Confirm each fix")
    parser_fix.add_argument("--auto", action="store_true", help="Apply all fixes without confirmation")
    parser_fix.add_argument("--no-backup", action="store_true", help="Don't backup files before fixing")

    # Learn Commands
    parser_learn = subparsers.add_parser("learn", help="Automatic rule learning from corpus")
    parser_learn.add_argument("--save", action="store_true", help="Save learned rules to knowledge base")
    
    # Task Commands
    subparsers.add_parser("extract", help="Extract images and pages from source PDF")
    subparsers.add_parser("convert", help="Convert extracted images to JPEG XL")
    
    # Global args
    parser.add_argument('--dir', type=str, default="./typst_source/contents/lessons", help="Path to lessons directory")
    parser.add_argument('--root', type=str, default=".", help="Project root directory")
    
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
    
    elif args.command == "learn":
        from src.learn_rules import learn_rules_from_corpus
        from src.knowledge_base import get_knowledge_base
        
        initial_rules, final_rules = learn_rules_from_corpus(lessons_dir)
        
        if args.save:
            kb = get_knowledge_base()
            kb.update_rules(initial_rules, final_rules)
            kb.save()
            
    elif args.command == "fix":
        run_fixer(
            lessons_dir=lessons_dir,
            target=args.target,
            dry_run=args.dry_run,
            interactive=args.interactive,
            auto=args.auto,
            backup=not args.no_backup
        )
        
    elif args.command == "analyze":
        print(f"Loading lessons from: {lessons_dir}")
        lessons = load_lessons(lessons_dir)
        print(f"Loaded {len(lessons)} files.")

        if args.type in ['phonetic', 'all']:
            analyze_phonetic_consistency(lessons, str(project_root / "phonetic_analysis_v2.json"))
            
        if args.type in ['displacement', 'all']:
            analyze_displacement(lessons, project_root, target_filter=args.target)
            
        if args.type in ['priority', 'all']:
            generate_priority_list(lessons, str(project_root / "priority_report.json"))

if __name__ == "__main__":
    main()
