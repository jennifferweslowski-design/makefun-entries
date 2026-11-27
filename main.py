"""One Line of Earned Pride.

Writes a single line of quiet, earned pride to /output/entry.txt.
The line is a small person doing something hard: a nine-year-old
carrying her little brother up the stairs when the lift breaks.
"""

LINE = (
    "Mara, nine, carried her little brother up the last flight of "
    "stairs when the lift broke, set him down gently, and only then "
    "let her arms shake."
)

OUTPUT_PATH = "/output/entry.txt"
MAX_CHARS = 240


def main():
    line = LINE.strip()
    if not line:
        raise ValueError("entry line is empty")
    if "\n" in line or "\r" in line:
        raise ValueError("entry line must be a single line")
    if len(line) > MAX_CHARS:
        raise ValueError(f"entry line is {len(line)} chars, over the 240 limit")
    import os

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(line)
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        written = f.read()
    if written != line:
        raise ValueError("entry.txt did not round-trip: written content differs")
    print(f"Wrote {len(line)} characters to {OUTPUT_PATH}")
    print(line)


if __name__ == "__main__":
    main()
