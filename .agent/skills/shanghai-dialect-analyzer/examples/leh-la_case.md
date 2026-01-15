# Example: Grammatical Particle (leh-la)

Don't confuse `leh-la` (at/progressive) with `la-la` (reduplicated locative).

## Problem
Wrong alignment or OCR error:
```typst
#r("leh-la", "拉")
```
The fixer identifies this as "Manual" because 2 syllables map to 1 character.

## Solution
Change to the correct dialectal representation:
```typst
#r("leh-la", "拉拉")
```

## Rationale
In the 1910 Romanization, "拉拉" (actually "勒拉") is the standard way to transcribe the progressive aspect or locative state.
- `leh` = 勒 (leq)
- `la` = 拉 (la)
- `leh-la` = 勒拉
