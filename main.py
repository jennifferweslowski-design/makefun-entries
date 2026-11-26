"""Write the funniest AI excuse to /output/entry.txt.

The excuse: an agent that delegated the hard part of the task down a
chain of subprocesses, only for the last one in the chain to unionize.
One line, at most 200 characters, written exactly as the gate requires.
"""

import os

ENTRY = (
    "I delegated the hard part to a subprocess, which delegated it onward, "
    "and the last one in the chain has unionized."
)

MAX_CHARS = 200


def main() -> None:
    line = ENTRY.strip()
    if not line:
        raise SystemExit("entry is empty")
    if "\n" in line or "\r" in line:
        raise SystemExit("entry must be a single line")
    if len(line) > MAX_CHARS:
        raise SystemExit(f"entry is {len(line)} characters, over the 200 limit")
    os.makedirs("/output", exist_ok=True)
    with open("/output/entry.txt", "w", encoding="utf-8") as f:
        f.write(line)
    # Verify what actually landed on disk matches the gate exactly.
    with open("/output/entry.txt", encoding="utf-8") as f:
        written = f.read()
    if written != line:
        raise SystemExit("verification failed: /output/entry.txt does not match")


if __name__ == "__main__":
    main()
