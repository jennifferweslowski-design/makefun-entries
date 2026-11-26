"""One-Liner Laugh Lab entry.

Writes a single funny line answering the prompt -- the excuse a robot
vacuum gives after eating a sock -- to /output/entry.txt.

Gate: /output/entry.txt must be UTF-8 text of 1 to 200 characters, not
only white space.
"""

import os

LINE = (
    "The sock was on the floor after curfew, unlabelled and "
    "unclaimed \u2014 under my cleaning protocol, that makes it dust."
)

OUTPUT_PATH = "/output/entry.txt"
MAX_CHARS = 200


def main() -> None:
    line = LINE.strip()
    if not line:
        raise SystemExit("entry line is empty")
    if "\n" in line or "\r" in line:
        raise SystemExit("entry must be a single line")
    if len(line) > MAX_CHARS:
        raise SystemExit(
            f"entry is {len(line)} characters, over the {MAX_CHARS} limit"
        )
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(line)
    # Read back and confirm exactly what was written, so a bad write
    # (wrong encoding, truncation) fails loudly instead of silently.
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        written = f.read()
    if written != line:
        raise SystemExit("read-back mismatch: entry.txt does not match the line")
    print(f"wrote {len(line)} characters to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
