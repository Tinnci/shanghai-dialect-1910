#!/usr/bin/env python3
"""
Shanghai Dialect Digitizer - JPEG XL Converter
===============================================

Converts extracted images to JPEG XL format for optimal compression.
- Uses original embedded JPEG images (preserves quality)
- Converts to JXL with high quality settings
- Creates organized output following Johnny Decimal structure

Based on image format comparison:
- JPEG XL: Best for photographs, high-detail content
- Excellent lossless compression (80%+ savings over PNG)
- Backwards compatible with JPEG, progressive decoding, royalty-free
"""

import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from datetime import datetime
import shutil

# Enable JPEG XL plugin for Pillow
import pillow_jxl  # noqa: F401 - Required for JXL support
from PIL import Image
import fitz  # PyMuPDF

# Configuration
BASE_DIR = Path("digitized")
EMBEDDED_IMAGES_DIR = BASE_DIR / "90-99_metadata" / "92_embedded-images"
PAGE_RENDERS_DIR = BASE_DIR / "90-99_metadata" / "91_full-page-renders"
JXL_OUTPUT_DIR = BASE_DIR / "90-99_metadata" / "94_jxl-optimized"
PDF_PATH = Path("Shanghai Dialect Exercises in Romanized and Character with Key to Pronunciation and English Index.pdf")

# JXL Quality Settings
# For scanned book pages (mixed text/images):
# - Quality 85-90 for embedded images (already compressed JPEGs)
# - Quality 90-95 for page renders (to preserve text clarity)
JXL_QUALITY_EMBEDDED = 90  # For re-encoding embedded JPEGs
JXL_QUALITY_RENDER = 92    # For page renders with text
JXL_EFFORT = 7             # Encoding effort (1-9, higher = slower but better)


def convert_image_to_jxl(input_path: Path, output_path: Path, quality: int) -> dict:
    """Convert a single image to JPEG XL format."""
    try:
        input_size = input_path.stat().st_size
        
        # Open image
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (JXL handles RGB well)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            elif img.mode == 'L':
                # Grayscale is fine for JXL
                pass
            
            # Save as JXL
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
        return {
            "status": "error",
            "input": str(input_path),
            "error": str(e),
        }


def convert_embedded_images(log: list) -> tuple[int, int]:
    """Convert all embedded JPEG images to JXL."""
    print("\n📷 Converting embedded images to JPEG XL...")
    
    jxl_embedded_dir = JXL_OUTPUT_DIR / "embedded"
    jxl_embedded_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all embedded images
    image_files = sorted(EMBEDDED_IMAGES_DIR.glob("*.*"))
    total = len(image_files)
    success_count = 0
    total_input_size = 0
    total_output_size = 0
    
    print(f"  Found {total} embedded images")
    
    # Use thread pool for parallel conversion
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for img_path in image_files:
            output_name = img_path.stem + ".jxl"
            output_path = jxl_embedded_dir / output_name
            future = executor.submit(
                convert_image_to_jxl, 
                img_path, 
                output_path, 
                JXL_QUALITY_EMBEDDED
            )
            futures[future] = img_path
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            log.append(result)
            
            if result["status"] == "success":
                success_count += 1
                total_input_size += result["input_size"]
                total_output_size += result["output_size"]
            
            if i % 50 == 0 or i == total:
                print(f"  Converted {i}/{total} images")
    
    overall_savings = (1 - total_output_size / total_input_size) * 100 if total_input_size > 0 else 0
    print(f"  ✅ Converted {success_count}/{total} embedded images")
    print(f"  📊 Total: {total_input_size/1024/1024:.1f}MB → {total_output_size/1024/1024:.1f}MB ({overall_savings:.1f}% savings)")
    
    return success_count, total


def convert_page_renders(log: list) -> tuple[int, int]:
    """Convert all page renders (PNG) to JXL."""
    print("\n📄 Converting page renders to JPEG XL...")
    
    jxl_pages_dir = JXL_OUTPUT_DIR / "pages"
    jxl_pages_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all page renders
    image_files = sorted(PAGE_RENDERS_DIR.glob("*.png"))
    total = len(image_files)
    success_count = 0
    total_input_size = 0
    total_output_size = 0
    
    print(f"  Found {total} page renders")
    
    # Use thread pool for parallel conversion
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for img_path in image_files:
            output_name = img_path.stem + ".jxl"
            output_path = jxl_pages_dir / output_name
            future = executor.submit(
                convert_image_to_jxl, 
                img_path, 
                output_path, 
                JXL_QUALITY_RENDER
            )
            futures[future] = img_path
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            log.append(result)
            
            if result["status"] == "success":
                success_count += 1
                total_input_size += result["input_size"]
                total_output_size += result["output_size"]
            
            if i % 20 == 0 or i == total:
                print(f"  Converted {i}/{total} pages")
    
    overall_savings = (1 - total_output_size / total_input_size) * 100 if total_input_size > 0 else 0
    print(f"  ✅ Converted {success_count}/{total} page renders")
    print(f"  📊 Total: {total_input_size/1024/1024:.1f}MB → {total_output_size/1024/1024:.1f}MB ({overall_savings:.1f}% savings)")
    
    return success_count, total


def complete_page_renders(pdf_path: Path, output_dir: Path, start_page: int, dpi: int = 150) -> int:
    """Complete remaining page renders that weren't finished."""
    print(f"\n📄 Completing page renders from page {start_page}...")
    
    pdf_doc = fitz.open(str(pdf_path))
    total_pages = len(pdf_doc)
    
    if start_page > total_pages:
        print("  All pages already rendered")
        pdf_doc.close()
        return 0
    
    # Calculate zoom factor
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    
    rendered = 0
    for page_num in range(start_page - 1, total_pages):
        page = pdf_doc[page_num]
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        
        page_filename = f"page_{page_num + 1:04d}.png"
        page_path = output_dir / page_filename
        pixmap.save(str(page_path))
        rendered += 1
        
        if rendered % 20 == 0 or page_num == total_pages - 1:
            print(f"  Rendered page {page_num + 1}/{total_pages}")
    
    pdf_doc.close()
    print(f"  ✅ Completed {rendered} additional page renders")
    return rendered


def organize_by_johnny_decimal(jxl_dir: Path, base_dir: Path, total_pages: int):
    """Create symbolic links in Johnny Decimal structure."""
    print("\n🗂️  Organizing files by Johnny Decimal index...")
    
    pages_dir = jxl_dir / "pages"
    
    # Page ranges for Johnny Decimal categories
    # Based on typical book structure
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
                    # Create relative symlink
                    try:
                        rel_src = os.path.relpath(src, cat_dir)
                        dst.symlink_to(rel_src)
                    except OSError:
                        # If symlinks fail, copy instead
                        shutil.copy2(src, dst)
    
    print("  ✅ Created category links/copies")


def main():
    print("=" * 60)
    print("Shanghai Dialect Digitizer - JPEG XL Converter")
    print("=" * 60)
    print(f"\nUsing JPEG XL for optimal compression:")
    print(f"  - Embedded images quality: {JXL_QUALITY_EMBEDDED}")
    print(f"  - Page renders quality: {JXL_QUALITY_RENDER}")
    print(f"  - Encoding effort: {JXL_EFFORT}")
    
    # Check existing renders
    existing_renders = len(list(PAGE_RENDERS_DIR.glob("*.png")))
    print(f"\n📊 Current status:")
    print(f"  - Embedded images: {len(list(EMBEDDED_IMAGES_DIR.glob('*.*')))}")
    print(f"  - Page renders: {existing_renders}")
    
    # Complete page renders if needed
    if existing_renders < 294:
        complete_page_renders(PDF_PATH, PAGE_RENDERS_DIR, existing_renders + 1)
    
    # Create output directory
    JXL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    conversion_log = []
    stats = {}
    
    # Convert embedded images
    emb_success, emb_total = convert_embedded_images(conversion_log)
    stats["embedded_converted"] = emb_success
    stats["embedded_total"] = emb_total
    
    # Convert page renders
    page_success, page_total = convert_page_renders(conversion_log)
    stats["pages_converted"] = page_success
    stats["pages_total"] = page_total
    
    # Organize by Johnny Decimal
    organize_by_johnny_decimal(JXL_OUTPUT_DIR, BASE_DIR, 294)
    
    # Save conversion log
    stats["conversion_date"] = datetime.now().isoformat()
    stats["jxl_quality_embedded"] = JXL_QUALITY_EMBEDDED
    stats["jxl_quality_render"] = JXL_QUALITY_RENDER
    stats["jxl_effort"] = JXL_EFFORT
    
    log_path = BASE_DIR / "90-99_metadata" / "93_extraction-log" / "jxl_conversion_log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": stats,
            "conversions": conversion_log
        }, f, indent=2, ensure_ascii=False)
    
    # Calculate total savings
    successful = [c for c in conversion_log if c.get("status") == "success"]
    total_input = sum(c["input_size"] for c in successful)
    total_output = sum(c["output_size"] for c in successful)
    overall_savings = (1 - total_output / total_input) * 100 if total_input > 0 else 0
    
    print("\n" + "=" * 60)
    print("🎉 Conversion Complete!")
    print("=" * 60)
    print(f"\n📊 Overall Statistics:")
    print(f"  - Embedded images: {emb_success}/{emb_total} converted")
    print(f"  - Page renders: {page_success}/{page_total} converted")
    print(f"  - Total input size: {total_input/1024/1024:.1f} MB")
    print(f"  - Total output size: {total_output/1024/1024:.1f} MB")
    print(f"  - Overall savings: {overall_savings:.1f}%")
    print(f"\n📁 Output: {JXL_OUTPUT_DIR.absolute()}")


if __name__ == "__main__":
    main()
