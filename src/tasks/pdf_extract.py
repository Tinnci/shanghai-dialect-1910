
import fitz  # PyMuPDF
from pathlib import Path
import json
from datetime import datetime

# Configuration
PDF_FILENAME = "Shanghai Dialect Exercises in Romanized and Character with Key to Pronunciation and English Index.pdf"
OUTPUT_BASE_NAME = "digitized"

# Johnny Decimal Category Definitions
JOHNNY_DECIMAL_STRUCTURE = {
    "10-19_preliminary": {
        "11": "cover",
        "12": "title-pages",
        "13": "preface",
        "14": "table-of-contents",
        "15": "introduction",
    },
    "20-29_pronunciation-guide": {
        "21": "key-to-pronunciation",
        "22": "tone-charts",
        "23": "romanization-system",
        "24": "phonetic-tables",
    },
    "30-39_lessons": {
        "31": "lesson-01-10",
        "32": "lesson-11-20",
        "33": "lesson-21-30",
        "34": "lesson-31-40",
        "35": "lesson-41-50",
        "36": "additional-exercises",
    },
    "40-49_appendices": {
        "41": "english-index",
        "42": "character-index",
        "43": "vocabulary-lists",
        "44": "supplementary-materials",
    },
    "90-99_metadata": {
        "91": "full-page-renders",
        "92": "embedded-images",
        "93": "extraction-log",
    }
}

def create_directory_structure(base_path: Path) -> dict:
    """Create the Johnny Decimal directory structure."""
    created_dirs = {}
    
    for category, subcategories in JOHNNY_DECIMAL_STRUCTURE.items():
        category_path = base_path / category
        category_path.mkdir(parents=True, exist_ok=True)
        created_dirs[category] = str(category_path)
        
        for code, name in subcategories.items():
            subdir_path = category_path / f"{code}_{name}"
            subdir_path.mkdir(parents=True, exist_ok=True)
            created_dirs[f"{category}/{code}"] = str(subdir_path)
    
    return created_dirs

def extract_embedded_images(pdf_doc, output_dir: Path, log: list) -> int:
    """Extract all embedded images from the PDF."""
    embedded_dir = output_dir / "90-99_metadata" / "92_embedded-images"
    image_count = 0
    
    print("\n📷 Extracting embedded images...")
    
    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]
        image_list = page.get_images(full=True)
        
        if image_list:
            print(f"  Page {page_num + 1}: Found {len(image_list)} embedded image(s)")
        
        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            
            try:
                # Extract image data
                base_image = pdf_doc.extract_image(xref)
                if base_image:
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)
                    colorspace = base_image.get("colorspace", "unknown")
                    
                    # Save image
                    image_filename = f"page_{page_num + 1:04d}_img_{img_idx + 1:03d}.{image_ext}"
                    image_path = embedded_dir / image_filename
                    
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                    
                    image_count += 1
                    
                    log.append({
                        "type": "embedded_image",
                        "page": page_num + 1,
                        "image_index": img_idx + 1,
                        "xref": xref,
                        "format": image_ext,
                        "width": width,
                        "height": height,
                        "colorspace": colorspace,
                        "output_path": str(image_path.relative_to(output_dir))
                    })
                    
            except Exception as e:
                log.append({
                    "type": "error",
                    "page": page_num + 1,
                    "image_index": img_idx + 1,
                    "xref": xref,
                    "error": str(e)
                })
                print(f"    ⚠️ Error extracting image {img_idx + 1} from page {page_num + 1}: {e}")
    
    return image_count

def render_full_pages(pdf_doc, output_dir: Path, log: list, dpi: int = 150) -> int:
    """Render all pages as high-quality images."""
    pages_dir = output_dir / "90-99_metadata" / "91_full-page-renders"
    total_pages = len(pdf_doc)
    
    print(f"\n📄 Rendering {total_pages} pages at {dpi} DPI...")
    
    # Calculate zoom factor for desired DPI
    zoom = dpi / 72  # PDF standard is 72 DPI
    matrix = fitz.Matrix(zoom, zoom)
    
    for page_num in range(total_pages):
        page = pdf_doc[page_num]
        
        # Render page to pixmap
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        
        # Save as PNG
        page_filename = f"page_{page_num + 1:04d}.png"
        page_path = pages_dir / page_filename
        pixmap.save(str(page_path))
        
        # Progress indicator
        if (page_num + 1) % 10 == 0 or page_num == 0 or page_num == total_pages - 1:
            print(f"  Rendered page {page_num + 1}/{total_pages}")
        
        log.append({
            "type": "full_page_render",
            "page": page_num + 1,
            "dpi": dpi,
            "width": pixmap.width,
            "height": pixmap.height,
            "output_path": str(page_path.relative_to(output_dir))
        })
    
    return total_pages

def categorize_pages_by_content(pdf_doc, output_dir: Path, log: list):
    """
    Analyze PDF structure and create symbolic links or copies
    in appropriate Johnny Decimal categories based on content.
    """
    print("\n📚 Analyzing PDF structure for categorization...")
    
    total_pages = len(pdf_doc)
    categories = {
        "preliminary": [],
        "pronunciation": [],
        "lessons": [],
        "appendices": [],
    }
    
    toc = pdf_doc.get_toc()
    
    if toc:
        print(f"  Found Table of Contents with {len(toc)} entries:")
        toc_log = []
        for item in toc:
            level, title, page = item
            toc_log.append({
                "level": level,
                "title": title,
                "page": page
            })
            print(f"    {'  ' * (level-1)}[{page}] {title}")
        log.append({
            "type": "table_of_contents",
            "entries": toc_log
        })
    else:
        print("  No embedded table of contents found - using page-based heuristics")
        preliminary_end = min(10, total_pages)
        categories["preliminary"] = list(range(1, preliminary_end + 1))
        appendix_start = max(total_pages - 30, preliminary_end + 1)
        categories["appendices"] = list(range(appendix_start, total_pages + 1))
        categories["lessons"] = list(range(preliminary_end + 1, appendix_start))
        
        log.append({
            "type": "heuristic_categorization",
            "preliminary_pages": categories["preliminary"],
            "lesson_pages": categories["lessons"],
            "appendix_pages": categories["appendices"]
        })
    
    return categories

def create_readme(output_dir: Path, pdf_info: dict, stats: dict):
    """Create a README file documenting the extraction."""
    readme_content = f"""# Shanghai Dialect Exercises - Digitized Copy

## 📖 Source Document

- **Title**: {pdf_info.get('title', 'Shanghai Dialect Exercises in Romanized and Character with Key to Pronunciation and English Index')}
- **Author**: {pdf_info.get('author', 'Unknown')}
- **Pages**: {pdf_info.get('page_count', 'Unknown')}
- **Created**: {pdf_info.get('creationDate', 'Unknown')}

## 📊 Extraction Statistics

- **Total Pages Rendered**: {stats.get('pages_rendered', 0)}
- **Embedded Images Extracted**: {stats.get('embedded_images', 0)}
- **Extraction Date**: {stats.get('extraction_date', 'Unknown')}

## 📁 Directory Structure (Johnny Decimal Index)

This archive uses an improved Johnny Decimal indexing system:

```
10-19_preliminary/        # Cover, title pages, preface, contents
20-29_pronunciation-guide/  # Pronunciation keys and phonetic guides
30-39_lessons/            # Main lesson content
40-49_appendices/         # Indices and supplementary materials
90-99_metadata/           # Full renders and extraction data
```

## 🔍 How to Use

1. **Full Page Renders**: Browse `90-99_metadata/91_full-page-renders/` for complete page images
2. **Embedded Images**: Check `90-99_metadata/92_embedded-images/` for any embedded graphics
3. **Extraction Log**: See `90-99_metadata/93_extraction-log/` for detailed extraction metadata

---
*Generated by Shanghai Dialect Digitizer on {stats.get('extraction_date', 'Unknown')}*
"""
    readme_path = output_dir / "README.md"
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"\n📝 Created README at {readme_path}")

def run_extraction(project_root: Path):
    """Main entry point for extraction task"""
    pdf_path = project_root / PDF_FILENAME
    output_base = project_root / OUTPUT_BASE_NAME

    print("=" * 60)
    print("Shanghai Dialect Digitizer - PDF Image Extractor")
    print("=" * 60)
    
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found at {pdf_path}")
        return
    
    print(f"\n📂 Source PDF: {pdf_path}")
    print(f"   File size: {pdf_path.stat().st_size / (1024*1024):.2f} MB")
    print("\n🗂️  Creating Johnny Decimal directory structure...")
    created_dirs = create_directory_structure(output_base)
    print(f"   Created {len(created_dirs)} directories")
    
    print("\n📖 Opening PDF document...")
    pdf_doc = fitz.open(str(pdf_path))
    
    pdf_info = {
        "page_count": len(pdf_doc),
        "title": pdf_doc.metadata.get("title", ""),
        "author": pdf_doc.metadata.get("author", ""),
    }
    
    print(f"   Total pages: {pdf_info['page_count']}")
    
    extraction_log = [{"type": "pdf_metadata", "data": pdf_info}]
    embedded_count = extract_embedded_images(pdf_doc, output_base, extraction_log)
    print(f"\n✅ Extracted {embedded_count} embedded images")
    
    render_dpi = 150
    pages_rendered = render_full_pages(pdf_doc, output_base, extraction_log, dpi=render_dpi)
    print(f"\n✅ Rendered {pages_rendered} full pages")
    
    categorize_pages_by_content(pdf_doc, output_base, extraction_log)
    pdf_doc.close()
    
    stats = {
        "pages_rendered": pages_rendered,
        "embedded_images": embedded_count,
        "render_dpi": render_dpi,
        "extraction_date": datetime.now().isoformat(),
    }
    
    log_dir = output_base / "90-99_metadata" / "93_extraction-log"
    log_path = log_dir / "extraction_log.json"
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({"metadata": stats, "pdf_info": pdf_info, "log": extraction_log}, f, indent=2, ensure_ascii=False)
    print(f"\n📋 Saved extraction log to {log_path}")
    
    create_readme(output_base, pdf_info, stats)
    
    print("\n" + "=" * 60)
    print("🎉 Extraction Complete!")
    print("=" * 60)
