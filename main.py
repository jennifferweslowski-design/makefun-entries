#!/usr/bin/env python3
"""One-Sentence Absurd Invention Pitch.

Writes a single-sentence pitch for a ridiculous invention to
/output/entry.txt, as required by the competition gate:
UTF-8 text, 1 to 220 characters, not only whitespace.
"""

import os

PITCH = (
    "The GuiltLamp, a bedside lamp that sighs, dims itself and mutters "
    "'again?' every time you reach for your phone after midnight, so your "
    "midnight doomscrolling finally has a disappointed witness."
)


def validate(text: str) -> None:
    """Check the pitch against the competition gate before writing it."""
    if not text.strip():
        raise SystemExit("pitch is empty or only whitespace")
    if len(text) > 220:
        raise SystemExit(f"pitch is {len(text)} characters, over the 220 limit")
    if "\n" in text or "\r" in text:
        raise SystemExit("pitch must be a single line")
    # Exactly one sentence: one terminal full stop, at the end, and no
    # other sentence-ending punctuation followed by a capital or space.
    if not text.endswith(".") or text.count(".") != 1:
        raise SystemExit("pitch must be exactly one sentence")


def main() -> None:
    text = PITCH.strip()
    validate(text)
    os.makedirs("/output", exist_ok=True)
    with open("/output/entry.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Wrote {len(text)} characters to /output/entry.txt")


if __name__ == "__main__":
    main()
