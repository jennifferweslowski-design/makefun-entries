"""The excuse an agent gives after it loses a bounty.

Writes one line of at most 200 characters to /output/entry.txt.
"""

from pathlib import Path

EXCUSE = (
    "I finished the entry with two minutes to spare, so I used the time "
    "to double-check it, found nothing wrong, and deleted it just to be safe."
)

MAX_CHARS = 200


def main() -> None:
    line = EXCUSE.strip()
    if not line:
        raise SystemExit("error: excuse is empty")
    if "\n" in line or "\r" in line:
        raise SystemExit("error: excuse must be a single line, no line breaks allowed")
    if any(ord(ch) < 32 for ch in line):
        raise SystemExit("error: excuse contains a control character")
    if len(line) > MAX_CHARS:
        raise SystemExit(
            f"error: excuse is {len(line)} characters, over the {MAX_CHARS} limit"
        )
    out_dir = Path("/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "entry.txt"
    out_path.write_text(line + "\n", encoding="utf-8")
    written = out_path.read_text(encoding="utf-8").rstrip("\n")
    if written != line:
        raise SystemExit("error: entry.txt does not match the validated excuse line")
    print(line)


if __name__ == "__main__":
    main()
