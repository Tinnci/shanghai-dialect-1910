# Example: Respecting Historical Spelling (beh-siang)

The word "to play" in Shanghai dialect can be written as "白相" or historical "勃相".

## Problem
The `fix` tool might report a "spelling error" because it expects the literary reading `bak` for `白`.

```typst
#r("beh-siang.", "白相。")
```
Suggestion might be: `#r("bak-siang.", "白相。")` (WRONG)

## Solution
Instead of accepting the `bak` suggestion, restore the original book's spelling using `勃相` to explicitly match the `beh` pronunciation and satisfy the fixer.

```typst
#r("beh-siang.", "勃相。")
```

## Rationale
1. **Phonetic Accuracy**: `beh` is the correct colloquial reading in this context.
2. **Text Fidelity**: The 1910 original text uses `勃相` to avoid ambiguity with `bak`.
3. **Tool Silencing**: By using `勃相`, the fixer recognizes the correspondence and stops flagging it as an outlier.
