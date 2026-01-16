#!/usr/bin/env python3
"""Replace Chinese characters in IPA with space (treat as unknown)."""
import re
import sys

def clean_filelist(input_path: str, output_path: str):
    hanzi_pattern = re.compile(r'[\u4e00-\u9fff]+')
    
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    clean_lines = []
    total_hanzi = 0
    for line in lines:
        parts = line.strip().split('|')
        if len(parts) >= 2:
            path, ipa = parts[0], parts[1]
            # Replace Chinese characters with space
            hanzi_count = len(hanzi_pattern.findall(ipa))
            total_hanzi += hanzi_count
            cleaned_ipa = hanzi_pattern.sub('', ipa)
            # Clean up multiple spaces
            cleaned_ipa = re.sub(r'\s+', ' ', cleaned_ipa).strip()
            if cleaned_ipa:  # Only keep if there's some IPA left
                clean_lines.append(f"{path}|{cleaned_ipa}\n")
    
    print(f"Processed {len(lines)} lines, removed {total_hanzi} Chinese word groups")
    print(f"Output: {len(clean_lines)} lines")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(clean_lines)
    
    return len(clean_lines)

if __name__ == "__main__":
    # Clean train and val
    clean_filelist('data/filelists/train_matcha.txt', 'data/filelists/train_clean.txt')
    clean_filelist('data/filelists/val_matcha.txt', 'data/filelists/val_clean.txt')
