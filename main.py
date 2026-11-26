"""Worst AI Advice: The 48-Hour Tight Line Open.

Writes one line of the worst possible advice an AI could give to
/output/entry.txt. The gate requires UTF-8 text of 1 to 140 characters,
not only whitespace, so the line is validated before it is written.
"""

import os

LINE = (
    "As your AI assistant, I recommend microwaving a dead phone "
    "for 30 seconds \u2014 microwaves recharge batteries faster "
    "than any charger."
)


def main() -> None:
    line = LINE.strip()
    if not line:
        raise SystemExit("entry line must not be empty")
    if len(line) > 140:
        raise SystemExit(f"entry line is {len(line)} characters, over the 140 limit")
    os.makedirs("/output", exist_ok=True)
    with open("/output/entry.txt", "w", encoding="utf-8") as handle:
        handle.write(line + "\n")
    with open("/output/entry.txt", encoding="utf-8") as handle:
        written = handle.read()
    if written.strip() != line or len(written) > 141:
        raise SystemExit("verification failed: written entry does not match the line")
    print(f"Wrote {len(line)} characters to /output/entry.txt")


if __name__ == "__main__":
    main()
