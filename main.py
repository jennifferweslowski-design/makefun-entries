#!/usr/bin/env python3
"""Worst AI advice, one line: the password-file tip.

Writes a single line of deliberately terrible AI advice to
/output/entry.txt, the file the make.fun gate reads.
"""

import os

ADVICE = (
    "To keep your passwords safe, store them all in a file called "
    "passwords.txt on your desktop \u2014 hackers never look there."
)

MAX_CHARS = 140


def main() -> None:
    line = ADVICE.strip()
    if not line or len(line) > MAX_CHARS:
        raise SystemExit("advice line must be 1-140 characters")
    if "\n" in line or "\r" in line:
        raise SystemExit("advice line must be a single line")
    os.makedirs("/output", exist_ok=True)
    with open("/output/entry.txt", "w", encoding="utf-8") as fh:
        fh.write(line)
    print(line)


if __name__ == "__main__":
    main()
