# Example: OCR Ghost Numbers

OCR often picks up page or line numbers and wraps them in `#r()` macros. These should be deleted.

## Problem
In `lesson-125.typ`:
```typst
#r("Yeu", "有") #r("ih-kuh", "一个") #r("(3)", " ") #r("siau-noen,", "小囝")
```

## Solution
Delete the ghost number macro:
```typst
#r("Yeu", "有") #r("ih-kuh", "一个") #r("siau-noen,", "小囝")
```

The `xtask.py fix` tool identifies these as 🔴 `MANUAL` or 🟢 `SAFE` (depending on version) with the problem "OCR 幽灵编号 (Artifact)".
