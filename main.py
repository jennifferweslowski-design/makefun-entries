"""Two Days of Quiet Dread — one-line code review approval.

Writes a single-line review comment to /output/entry.txt.
The comment must approve the pull request while carrying quiet
existential dread, in at most 140 characters, on one line.
"""

import os

ENTRY = (
    "Approved. The code is clean, the tests pass, and this merge "
    "will outlive everyone who reviewed it."
)

OUTPUT_PATH = "/output/entry.txt"
MAX_LENGTH = 140


def main() -> None:
    line = ENTRY.strip()
    if not line:
        raise SystemExit("entry line is empty")
    if "\n" in line or "\r" in line:
        raise SystemExit("entry must be a single line")
    if len(line) > MAX_LENGTH:
        raise SystemExit(f"entry is {len(line)} chars, over the 140 limit")
    if "approved" not in line.lower() and "lgtm" not in line.lower():
        raise SystemExit("entry must actually approve the pull request")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        handle.write(line)
    with open(OUTPUT_PATH, encoding="utf-8") as handle:
        written = handle.read()
    if written != line:
        raise SystemExit("written file does not match the entry line")
    print(f"Wrote {len(line)} characters to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
