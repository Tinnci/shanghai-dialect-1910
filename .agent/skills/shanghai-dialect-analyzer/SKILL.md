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

2.   - **Alignment Diagnosis (`analyze displacement`)**:
   - Uses a sliding window sequence alignment algorithm.
   - **Smart Reduplication Awareness**: Automatically detects and skips reduplicated patterns (e.g., "拉拉", "看看") to prevent false positive displacement alerts.
   - **Rime Integration**: Validates character-pinyin pairs against dictionary to skip legitimate polyphonic variants.
   - Diagnoses "[ALIGN-L] 漏字偏移" (Missing character/syllable) and "[ALIGN-R] 多字偏移" (Extra character/syllable).
   - Highlights specific words where the shift occurs.

3. **Priority Ranking (`analyze priority`)**:
   - Scores files based on a weighted anomaly count.
   - Categorizes files into Critical, High, Medium, and Low priority for manual proofreading.

4. **Auto-Fix (`fix`)**:
   - **Safety Levels**: Classifies fixes into 🟢 `SAFE` (Auto-applicable), 🟡 `REVIEW` (Likely correct but needs check), and 🔴 `MANUAL` (Requires user intervention).
   - **Corpus Context**: Displays usage examples of the specific character from the entire book to help verify pronunciations.
   - **Ghost Number Detection**: Identifies OCR artifacts like `#r("(1)", " ")` as 🔴 `MANUAL` fixes (should be deleted).
   - **Rime Dictionary Validation**: Uses `external/rime-wugniu_zaonhe` (9166 chars, 23936 phrases, 1147 polyphonic chars) to verify pronunciations.
   - **Cross-Scheme Phonetic Similarity**: Correctly maps 1910 Church Romanization to modern Wugniu Pinyin (e.g., `nyih` ↔ `gniq`, `zeh` ↔ `zeq` for "日").

5. **Intelligent Rule Learning (`learn`)**:
   - **Rule Induction**: Automatically learns phonetic mapping rules from the book corpus (32K+ pairs) and Rime dictionary.
   - **Feature-Based Similarity**: Uses phonological feature vectors (place, manner, voicing, etc.) to calculate precise similarity scores.
   - **Knowledge Persistence**: Saves learned rules to `.agent/data/phonetic_rules.json` for consistent decision making.

6. **TTS Inference & Frontend (`g2p`, `shanghai_cleaners`)**:
   - **Decoupled G2P Engine**: Native 1910 Pott-to-IPA conversion without `espeak` dependency.
   - **Matcha-TTS Integration**: Built-in 🍵 Matcha-TTS (Flow Matching) support via root `uv` workspace.
   - **Shanghai Phoneme Set**: Custom `shanghai_symbols.py` with distinct Sharp/Round and Checked tone support.
   - **Stochastic Prosody**: (Planned) Integration of Stochastic Duration Predictor for natural old-style rhythm.

7. **Iterative Workflows (The "Grind" Pattern)**:
   - **Goal-Oriented Iteration**: Support for continuous refinement loops until project milestones are achieved.
   - **Success Verification**: Use of dedicated test suites (e.g., `tests/test_shanghai_frontend.py`) to gate progress.
   - **Documentation**: See `resources/agent_patterns.md` for implementation details.

## Core Modules

| Module | Purpose |
|--------|---------|
| `src/knowledge_base.py` | Centralized persistence for learned rules and configuration |
| `src/rule_induction.py` | Phonological rule induction engine & feature-based similarity |
| `src/learn_rules.py` | Pipeline to extract parallel corpus and train the system |
| `src/romanization.py` | Church Romanization ↔ Wugniu Pinyin mapping logic |
| `src/rime_dict.py` | Rime dictionary loader & polyphonic detection |
| `src/fixer.py` | Auto-fix engine using the improved knowledge base |
| `src/rime_dict.py` | Rime dictionary loader & polyphonic detection |
| `src/fixer.py` | Auto-fix engine using the improved knowledge base |
| `src/analyzers/displacement.py` | Alignment diagnosis with shift detection |
| `src/pott_g2p.py` | Pott -> IPA conversion & Modern Wugniu prediction engine |
| `src/tasks/export_ipa.py` | Task to export full corpus to JSONL format |

## Resources

- **Examples**: See `examples/` for detailed problem/solution cases:
    - `ghost_numbers.md`: OCR artifact removal.
    - `beh-siang_case.md`: Handling dialectal spelling vs. tool suggestions.
    - `leh-la_case.md`: Grammatical particle transcription.
- **Scripts**: See `scripts/` for helper utilities:
    - `check_lesson.sh`: Combined analysis and fix preview.
    - `recompile.sh`: Wrapper for project compilation.

## Romanization Mapping Examples

| Church (1910) | Wugniu (Modern) | IPA | Notes |
|---------------|-----------------|-----|-------|
| `ny` | `gn` | /ɲ/ | 日母 (Ri initial) |
| `tsh` | `ch` | /tsʰ/ | 清母 (Aspirated affricate) |
| `dz` | `j`/`z` | /dz/ | 从母 (Voiced affricate) |
| `-h` (入声) | `-q` | /-ʔ/ | 入声韵尾 (Glottal stop) |
| `aung` | `aon` | /ɔ̃/ | 鼻化韵 |

## Usage

# Analysis (Quality Control)
uv run python xtask.py analyze all          # Run all analyzers
uv run python xtask.py analyze displacement # Check for alignment shifts
uv run python xtask.py analyze priority     # Generate weighted priority list
uv run python xtask.py analyze displacement lesson-49  # Target specific file

# Repair & Correction
uv run python xtask.py fix --auto           # Apply 🟢 SAFE fixes project-wide
uv run python xtask.py fix lesson-26 -i     # Interactively review issues

# Knowledge & Learning
uv run python xtask.py learn --save         # Re-train phonetic rules from current corpus

# Conversion & Export
uv run python xtask.py g2p "ngoo tshang"    # Convert phrase to IPA & predict Wugniu
uv run python xtask.py export-ipa           # Export full corpus to JSONL

# Project Maintenance
uv run python xtask.py compile              # Build PDF with metadata and standard name
uv run python xtask.py extract              # Extract source images from PDF
uv run python xtask.py convert              # Convert images to JXL/JPG

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
3. **Ghost Hunting**: Look out for `#r("(N)", " ")` patterns in files with high remaining "displacement" error rates. These are OCR artifacts and must be removed.
4. **Polyphonic Protection**: The fixer will NOT touch multi-reading characters like "日" (`nyih`/`zeh`), "拉" (`la`/`leh`), validated against Rime dictionary.
5. **Reduplication Guard**: Words like "拉拉" (`leh-la`/`la-la`) are preserved to protect dialectal tone sandhi.
6. **False Spelling Suggestions**: Be careful with "白" (`bak` vs `beh`/`buh`) and other literary vs. colloquial readings. The fixer might suggest `bak` where the text intends `beh`.
7. **Interactive Polish**: For files with high mismatch remaining, use `fix <target> --interactive`. Use the "📖 全书用例" (Corpus Examples) in the output as your primary reference for deciding `y/n`.
8. **Final Verification**: Re-run `analyze displacement` to confirm the file is now [CLEAN].

## TTS Implementation Roadmap
 
### 1. Frontend Integration (DONE)
- [x] Decouple `espeak` dependency.
- [x] Integrate `PottToIPA` into Matcha-TTS cleaners.
- [x] Define historical phoneme set in `shanghai_symbols.py`.
- [x] E2E test for Pott -> ID sequence.

### 2. Acoustic Modeling (IN PROGRESS)
- [ ] Implement `MatchaHybrid` with Stochastic Duration Predictor (SDP).
- [ ] Implement contrastive loss for Sharp/Round physical isolation in embeddings.
- [ ] Configuration setup for Shanghai 1910 experiment.

### 3. Data & Training (TODO)
- [ ] Pre-process modern Wu corpora (Common Voice/MagicData).
- [ ] Train base model on modern Wu data.
- [ ] Record and align 1910-style few-shot data.
- [ ] Fine-tune embeddings for historical accuracy.
 
## Important Phonetic Notes

### The `leh-la` (拉拉) Case
- `leh` is **NOT** a misspelling of `la`
- `leh` = 入声 `leq` = "勒" (perfective/progressive aspect marker)
- `la` = "拉" (locative particle)
- Together `leh-la` represents the grammatical structure "勒拉" (in/at/while doing)
- This is a **correct** and **intentional** transcription

### The `beh-siang` (白相/勃相) Case
- "白相" (to play) is standardly written as "白相".
- The character "白" has two readings: `bak` (literary, as in 明白) and `beh` (colloquial, as in 白相).
- The fixer may incorrectly flag `beh-siang` as a typo for `bak-siang`. **Do NOT apply this fix.**
- The original text sometimes uses the borrowed character "**勃相**" to explicitly indicate the `beh` pronunciation. We should respect/restore this historical usage where consistent.

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
