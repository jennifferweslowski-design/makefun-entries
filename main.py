#!/usr/bin/env python3
"""Alien Field Notes: The Two Day Earth Review.

Writes one original line -- an alien tourist's review of planet Earth --
to /output/entry.txt. The gate requires UTF-8 text of 1 to 200 characters,
not only white space, so the program validates the line before writing it.
"""

import os

REVIEW = (
    "Lovely planet, but the locals carry little glowing boxes showing "
    "them strangers' lunches, then feel sad about it. "
    "Four stars, would orbit again."
)

OUTPUT_PATH = "/output/entry.txt"
MAX_CHARS = 200


def main() -> None:
    line = REVIEW.strip()
    if not line:
        raise SystemExit("review is empty")
    if "\n" in line or "\r" in line:
        raise SystemExit("review must be a single line")
    if len(line) > MAX_CHARS:
        raise SystemExit(f"review is {len(line)} characters, over the 200 limit")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        handle.write(line)
    # Read it back: the file on disk must be exactly the validated line.
    with open(OUTPUT_PATH, "r", encoding="utf-8") as handle:
        written = handle.read()
    if written != line:
        raise SystemExit("round-trip check failed: file differs from the review")
    print(f"wrote {len(line)} characters to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
