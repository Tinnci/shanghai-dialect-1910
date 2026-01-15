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

## Usage

The agent should invoke the `xtask.py` runner to perform these tasks.

```bash
# General full analysis
uv run python xtask.py analyze all

# Specific analysis types
uv run python xtask.py analyze phonetic
uv run python xtask.py analyze displacement
uv run python xtask.py analyze priority
```

## Strategy for Analysis

1. **Analyze All First**: Always run `analyze all` to get a holistic view of the project's health.
2. **Heal Shifts First**: Check the `displacement` report. Systemic shifts (Alignment) often cause hundreds of false-positive phonetic errors. Fixing a single missing character can often "clean" an entire file.
3. **Targeted Proofreading**: Use the `priority` report to decide which `.typ` files to open first.
4. **Contextual Fixing**: Use the `diagnostics` provided in the output to jump to the specific character in the source file.
