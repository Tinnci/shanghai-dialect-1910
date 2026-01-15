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
   - Supports dry-run, interactive, and auto modes.

## Usage

The agent should invoke the `xtask.py` runner to perform these tasks.

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
3. **Reduplication Guard**: Note that the fixer will NOT touch words like "拉拉" (`leh-la`/`la-la`) to prevent corrupting dialectal tone variations.
4. **Interactive Polish**: For files with high mismatch remaining, use `fix <target> --interactive`. Use the "📖 全书用例" (Corpus Examples) in the output as your primary reference for deciding `y/n`.
5. **Final Verification**: Re-run `analyze displacement` to confirm the file is now [CLEAN].

