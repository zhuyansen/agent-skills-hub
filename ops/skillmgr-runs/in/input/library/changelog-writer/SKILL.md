---
name: changelog-writer
description: "Write a CHANGELOG entry from the commits since the last tag, grouped into added, changed and fixed."
---

# Changelog Writer

Write a CHANGELOG entry from the commits since the last tag, grouped into added, changed and fixed.

## When to use
Use this skill when the user asks for it by name or describes this task. Do not use it for unrelated work.

## Steps
1. Read the input the user points to. If none is given, ask for the file or text.
2. Do the task described above, step by step, and keep the user's own wording where it matters.
3. Show the result, then a short list of what you changed or found, so the user can check it.

## Notes
- Keep changes small and reversible.
- Say plainly when the input is incomplete instead of guessing.
