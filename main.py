#!/usr/bin/env python3
"""The Funniest Toaster Error Message.

Writes one line -- the error message a kitchen toaster shows its owner
when something goes wrong -- to /output/entry.txt.
"""

import os

ENTRY = "E-11: The bread is stuck. I have notified the bread's next of kin."

MAX_CHARS = 120


def validate(text: str) -> None:
    """Fail loudly instead of writing an entry the gate would refuse."""
    if not text.strip():
        raise SystemExit("entry is empty or only whitespace")
    if len(text) > MAX_CHARS:
        raise SystemExit(f"entry is {len(text)} chars, over the {MAX_CHARS} limit")


def main() -> None:
    validate(ENTRY)
    os.makedirs("/output", exist_ok=True)
    # No trailing newline: the gate counts every character in the file.
    with open("/output/entry.txt", "w", encoding="utf-8") as handle:
        handle.write(ENTRY)


if __name__ == "__main__":
    main()
