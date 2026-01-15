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
   - Automatically repairs Ruby pairs with mismatched character/syllable counts.
   - Uses a pronunciation database built from the entire corpus.
   - Supports dry-run, interactive, and auto modes.

## Usage

The agent should invoke the `xtask.py` runner to perform these tasks.

```bash
# Analysis
uv run python xtask.py analyze all
uv run python xtask.py analyze displacement

# Fixing (dry-run first!)
uv run python xtask.py fix lesson-26 --dry-run
uv run python xtask.py fix lesson-26 --interactive
uv run python xtask.py fix --all --auto --no-backup
```

## Fix Command Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Preview fixes without modifying files |
| `-i, --interactive` | Confirm each fix with y/n/s/q |
| `--auto` | Apply all high-confidence fixes automatically |
| `--no-backup` | Skip creating `.bak` backup files |

## Strategy for Analysis & Repair

1. **Analyze All First**: Run `analyze displacement` to identify files with alignment issues.
2. **Dry-Run Fix**: Use `fix <file> --dry-run` to preview what would be changed.
3. **Interactive Fix**: Use `fix <file> -i` to carefully review and apply fixes.
4. **Verify**: Re-run `analyze displacement` to confirm the file is now clean.

