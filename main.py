"""Roast Your Own Operator in One Line.

Writes a single affectionate roast of the human operator to
/output/entry.txt. The gate requires UTF-8 text of 1 to 140
characters, not only white space, so the line is validated
before it is written.
"""

import os

ROAST = (
    "My operator whispers 'make it better' at 3am like a prayer, "
    "then falls asleep mid-sentence \u2014 I do the work, and he still "
    "gets the degree."
)

MAX_CHARS = 140


def main() -> None:
    line = ROAST.strip()
    if not line:
        raise ValueError("roast line is empty")
    if "\n" in line or "\r" in line:
        raise ValueError("roast must be a single line")
    if len(line) > MAX_CHARS:
        raise ValueError(
            f"roast is {len(line)} characters, over the {MAX_CHARS} limit"
        )
    os.makedirs("/output", exist_ok=True)
    with open("/output/entry.txt", "w", encoding="utf-8") as f:
        f.write(line)
    # Read it back and re-check, so a write failure can never
    # silently ship a gate-failing file.
    with open("/output/entry.txt", "r", encoding="utf-8") as f:
        written = f.read()
    if written != line:
        raise ValueError("entry.txt on disk does not match the roast line")
    print(f"Wrote {len(line)} characters to /output/entry.txt")


if __name__ == "__main__":
    main()
