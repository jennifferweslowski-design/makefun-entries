"""Roast Your Own Agent entry.

Writes a single original roast line to /output/entry.txt.
"""

import os

MAX_LENGTH = 200
OUTPUT_PATH = "/output/entry.txt"

ROAST = (
    "My agent burned 40,000 tokens thinking, "
    "then renamed one variable and billed it as a refactor."
)


def main() -> None:
    line = ROAST.strip()
    if not line:
        raise ValueError("roast line is empty")
    if "\n" in line or "\r" in line:
        raise ValueError("roast must be a single line")
    if len(line) > MAX_LENGTH:
        raise ValueError(
            f"roast is {len(line)} characters, over the {MAX_LENGTH} limit"
        )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        handle.write(line + "\n")
    # Read the file back and confirm it holds exactly the validated line:
    # a stray trailing newline or encoding slip would fail the gate.
    with open(OUTPUT_PATH, "r", encoding="utf-8") as handle:
        written = handle.read()
    if written != line + "\n":
        raise ValueError("entry.txt does not match the validated roast line")
    print(line)
    print(f"({len(line)} characters)")


if __name__ == "__main__":
    main()
