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

def main():
    parser = argparse.ArgumentParser(description="Shanghai Dialect Project XTask Runner")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analysis Commands
    parser_analyze = subparsers.add_parser("analyze", help="Run quality analysis tools")
    parser_analyze.add_argument("type", choices=['phonetic', 'displacement', 'priority', 'all'], help="Analysis type")
    
    # Task Commands
    subparsers.add_parser("extract", help="Extract images and pages from source PDF")
    subparsers.add_parser("convert", help="Convert extracted images to JPEG XL")
    
    # Global args
    parser.add_argument('--dir', type=str, default="./typst_source/contents/lessons", help="Path to lessons directory (for analysis)")
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
        
    elif args.command == "analyze":
        print(f"Loading lessons from: {lessons_dir}")
        lessons = load_lessons(lessons_dir)
        print(f"Loaded {len(lessons)} files.")

        if args.type in ['phonetic', 'all']:
            analyze_phonetic_consistency(lessons, str(project_root / "phonetic_analysis_v2.json"))
            
        if args.type in ['displacement', 'all']:
            analyze_displacement(lessons, project_root)
            
        if args.type in ['priority', 'all']:
            generate_priority_list(lessons, str(project_root / "priority_report.json"))

if __name__ == "__main__":
    main()
