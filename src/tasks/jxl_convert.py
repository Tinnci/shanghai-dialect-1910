
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil

# Enable JPEG XL plugin for Pillow
import pillow_jxl  # noqa: F401 - Required for JXL support
from PIL import Image
import fitz  # PyMuPDF

# Configuration Defaults (can be overridden or passed in)
PDF_FILENAME = "Shanghai Dialect Exercises in Romanized and Character with Key to Pronunciation and English Index.pdf"
OUTPUT_BASE_NAME = "digitized"

JXL_QUALITY_EMBEDDED = 90
JXL_QUALITY_RENDER = 92
JXL_EFFORT = 7

def convert_image_to_jxl(input_path: Path, output_path: Path, quality: int) -> dict:
    """Convert a single image to JPEG XL format."""
    try:
        input_size = input_path.stat().st_size
        with Image.open(input_path) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(
                output_path,
                format='JXL',
                quality=quality,
                effort=JXL_EFFORT,
            )
        output_size = output_path.stat().st_size
        savings = (1 - output_size / input_size) * 100 if input_size > 0 else 0
        return {
            "status": "success",
            "input": str(input_path),
            "output": str(output_path),
            "input_size": input_size,
            "output_size": output_size,
            "savings_percent": round(savings, 2),
        }
    except Exception as e:
        return {"status": "error", "input": str(input_path), "error": str(e)}

def convert_directory(input_dir: Path, output_dir: Path, quality: int, label: str) -> tuple[int, int, list]:
    print(f"\n📦 Converting {label} to JPEG XL...")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Try different extensions found in dir
    image_files = sorted(list(input_dir.glob("*.[pjP][pnP][gG]")) + list(input_dir.glob("*.jpeg")))
    total = len(image_files)
    success_count = 0
    log = []
    
    print(f"  Found {total} images in {input_dir}")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for img_path in image_files:
            output_name = img_path.stem + ".jxl"
            output_path = output_dir / output_name
            future = executor.submit(convert_image_to_jxl, img_path, output_path, quality)
            futures[future] = img_path
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            log.append(result)
            if result["status"] == "success":
                success_count += 1
            if i % 50 == 0 or i == total:
                print(f"  Converted {i}/{total}")

    print(f"  ✅ Converted {success_count}/{total} {label}")
    return success_count, total, log

def organize_by_johnny_decimal(jxl_dir: Path, base_dir: Path, total_pages: int):
    """Create symbolic links in Johnny Decimal structure."""
    print("\n🗂️  Organizing files by Johnny Decimal index...")
    pages_dir = jxl_dir / "pages"
    
    categories = {
        "10-19_preliminary/11_cover": (1, 1),
        "10-19_preliminary/12_title-pages": (2, 4),
        "10-19_preliminary/13_preface": (5, 8),
        "10-19_preliminary/14_table-of-contents": (9, 12),
        "10-19_preliminary/15_introduction": (13, 20),
        "20-29_pronunciation-guide/21_key-to-pronunciation": (21, 35),
        "20-29_pronunciation-guide/22_tone-charts": (36, 40),
        "30-39_lessons/31_lesson-01-10": (41, 80),
        "30-39_lessons/32_lesson-11-20": (81, 120),
        "30-39_lessons/33_lesson-21-30": (121, 160),
        "30-39_lessons/34_lesson-31-40": (161, 200),
        "30-39_lessons/35_lesson-41-50": (201, 240),
        "30-39_lessons/36_additional-exercises": (241, 260),
        "40-49_appendices/41_english-index": (261, 280),
        "40-49_appendices/42_character-index": (281, 294),
    }
    
    for category_path, (start, end) in categories.items():
        cat_dir = base_dir / category_path
        cat_dir.mkdir(parents=True, exist_ok=True)
        for page in range(start, min(end + 1, total_pages + 1)):
            src = pages_dir / f"page_{page:04d}.jxl"
            if src.exists():
                dst = cat_dir / f"page_{page:04d}.jxl"
                if not dst.exists():
                    try:
                        rel_src = os.path.relpath(src, cat_dir)
                        dst.symlink_to(rel_src)
                    except OSError:
                        shutil.copy2(src, dst)
    print("  ✅ Created category links/copies")

def complete_page_renders(pdf_path: Path, output_dir: Path, start_page: int, dpi: int = 150):
    print(f"\n📄 Completing page renders from page {start_page}...")
    pdf_doc = fitz.open(str(pdf_path))
    total_pages = len(pdf_doc)
    if start_page > total_pages:
        pdf_doc.close()
        return
    
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    
    rendered = 0
    for page_num in range(start_page - 1, total_pages):
        page = pdf_doc[page_num]
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        page_path = output_dir / f"page_{page_num + 1:04d}.png"
        pixmap.save(str(page_path))
        rendered += 1
        if rendered % 20 == 0:
            print(f"  Rendered {rendered} pages...")
    pdf_doc.close()
    print(f"  ✅ Completed {rendered} additional page renders")

def run_conversion(project_root: Path):
    """Main entry point for JXL conversion task"""
    base_dir = project_root / OUTPUT_BASE_NAME
    pdf_path = project_root / PDF_FILENAME
    
    embedded_images_dir = base_dir / "90-99_metadata" / "92_embedded-images"
    page_renders_dir = base_dir / "90-99_metadata" / "91_full-page-renders"
    jxl_output_dir = base_dir / "90-99_metadata" / "94_jxl-optimized"
    
    print("=" * 60)
    print("Shanghai Dialect Digitizer - JPEG XL Converter")
    print("=" * 60)
    
    # Check if we need to complete renders
    existing_renders = len(list(page_renders_dir.glob("*.png")))
    if existing_renders < 294 and pdf_path.exists():
         complete_page_renders(pdf_path, page_renders_dir, existing_renders + 1)
    
    jxl_output_dir.mkdir(parents=True, exist_ok=True)
    conversion_log = []
    
    # Convert Embedded
    s1, t1, log1 = convert_directory(embedded_images_dir, jxl_output_dir / "embedded", JXL_QUALITY_EMBEDDED, "embedded images")
    conversion_log.extend(log1)
    
    # Convert Pages
    s2, t2, log2 = convert_directory(page_renders_dir, jxl_output_dir / "pages", JXL_QUALITY_RENDER, "pages")
    conversion_log.extend(log2)
    
    # Organize
    if s2 > 0:
        organize_by_johnny_decimal(jxl_output_dir, base_dir, 294)
        
    print("\n" + "=" * 60)
    print("🎉 Conversion Complete!")
    print("=" * 60)
