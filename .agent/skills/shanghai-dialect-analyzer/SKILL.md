---
name: Shanghai Dialect Project Analyzer
description: Analyze Shanghai dialect transcription for consistency, typos, and alignment shifts using the project's specialized xtask tools.
---

# Shanghai Dialect Project Analyzer

This skill allows the agent to perform deep quality analysis on the Shanghai dialect transcription project. It identifies phonetic inconsistencies, transcription typos, and structural alignment shifts (displacement).

## Capabilities

1. **Phonetic Consistency (`analyze phonetic`)**:
   - Detects low-frequency outliers that are high-similarity matches (typos).
   - Identifies legitimate phonetic variants based on initials/finals analysis.
   - Reports on systemic mismatches.

2. **Alignment Diagnosis (`analyze displacement`)**:
   - Uses a sliding window sequence alignment algorithm.
   - Diagnoses "[ALIGN-L] 漏字偏移" (Missing character/syllable) and "[ALIGN-R] 多字偏移" (Extra character/syllable).
   - Highlights specific words where the shift occurs.

3. **Priority Ranking (`analyze priority`)**:
   - Scores files based on a weighted anomaly count.
   - Categorizes files into Critical, High, Medium, and Low priority for manual proofreading.

4. **Auto-Fix (`fix`)**:
   - **Safety Levels**: Classifies fixes into 🟢 `SAFE` (Auto-applicable), 🟡 `REVIEW` (Likely correct but needs check), and 🔴 `MANUAL` (Requires user intervention).
   - **Corpus Context**: Displays usage examples of the specific character from the entire book to help verify pronunciations.
   - **Reduplication Protection**: Automatically skips all corrections for reduplicated hanzi (e.g., "拉拉", "看看") to preserve tone sandhi records.
   - **Rime Dictionary Validation**: Uses `external/rime-wugniu_zaonhe` (9166 chars, 23936 phrases, 1147 polyphonic chars) to verify pronunciations.
   - **Cross-Scheme Phonetic Similarity**: Correctly maps 1910 Church Romanization to modern Wugniu Pinyin (e.g., `nyih` ↔ `gniq`, `zeh` ↔ `zeq` for "日").
   - Supports dry-run, interactive, and auto modes.

## Core Modules

| Module | Purpose |
|--------|---------|
| `src/romanization.py` | Church Romanization ↔ Wugniu Pinyin conversion and phonetic similarity |
| `src/rime_dict.py` | Rime dictionary loader, polyphonic detection, pronunciation validation |
| `src/fixer.py` | Auto-fix engine with safety levels and protection mechanisms |
| `src/analyzers/displacement.py` | Alignment diagnosis with shift detection |

## Romanization Mapping Examples

| Church (1910) | Wugniu (Modern) | IPA | Notes |
|---------------|-----------------|-----|-------|
| `ny` | `gn` | /ɲ/ | 日母 (Ri initial) |
| `tsh` | `ch` | /tsʰ/ | 清母 (Aspirated affricate) |
| `dz` | `j`/`z` | /dz/ | 从母 (Voiced affricate) |
| `-h` (入声) | `-q` | /-ʔ/ | 入声韵尾 (Glottal stop) |
| `aung` | `aon` | /ɔ̃/ | 鼻化韵 |

## Usage

```bash
# Analysis
uv run python xtask.py analyze all
uv run python xtask.py analyze displacement

# General Repair Workflow
uv run python xtask.py fix --auto          # Safely apply high-confidence fixes project-wide
uv run python xtask.py fix lesson-26 -i   # Interactively review complex issues
```

## Fix Command Options

| Option | Description |
|--------|-------------|
| `target` | Filename (e.g. `lesson-26`) or empty for all files. |
| `--dry-run` | Preview fixes with 🟢/🟡/🔴 indicators without modifying files. |
| `-i, --interactive` | Manually confirm each fix with `y/n/s/q`. |
| `--auto` | Automatically apply ONLY 🟢 `SAFE` level fixes. |
| `--no-backup` | Skip creating `.bak` backup files. |

## Strategy for Analysis & Repair

1. **Discovery**: Run `analyze displacement` to identify high-mismatch files.
2. **Safe Pre-cleaning**: Run `fix --auto` to resolve hundreds of simple alignment and spelling issues project-wide. 
3. **Polyphonic Protection**: The fixer will NOT touch multi-reading characters like "日" (`nyih`/`zeh`), "拉" (`la`/`leh`), validated against Rime dictionary.
4. **Reduplication Guard**: Words like "拉拉" (`leh-la`/`la-la`) are preserved to protect dialectal tone sandhi.
5. **Interactive Polish**: For files with high mismatch remaining, use `fix <target> --interactive`. Use the "📖 全书用例" (Corpus Examples) in the output as your primary reference for deciding `y/n`.
6. **Final Verification**: Re-run `analyze displacement` to confirm the file is now [CLEAN].

## Important Phonetic Notes

### The `leh-la` (拉拉) Case
- `leh` is **NOT** a misspelling of `la`
- `leh` = 入声 `leq` = "勒" (perfective/progressive aspect marker)
- `la` = "拉" (locative particle)
- Together `leh-la` represents the grammatical structure "勒拉" (in/at/while doing)
- This is a **correct** and **intentional** transcription

### Rusheng (入声) Finals
Per `preliminary.typ`:
- `-h` and `-k` indicate **abrupt vowel ending** (glottal stop /ʔ/)
- `ah` = "a" in "at", `eh` = "e" in "let", `ih` = short "i" in "it"
- These map to Wugniu `-q` endings (`aq`, `eq`, `iq`, etc.)

## Shell Usage ⚠️

**IMPORTANT**: Always use `bash -c '...'` wrapper for complex shell commands, especially when:
- Using pipes (`|`)
- Using redirection (`>`, `2>&1`)
- Using special characters or quotes

This avoids Fish shell syntax differences. Example:
```bash
# ✓ Correct
bash -c 'grep "pattern" file.txt | head -10'

# ✓ For git commits with multi-line messages
bash -c 'git commit -m "Short message"'
```
