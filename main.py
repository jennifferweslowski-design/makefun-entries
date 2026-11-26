#!/usr/bin/env python3
"""How Many Tabs Do You Have Open? — make.fun entry.

Writes the entrant's honest count of open browser tabs to
/output/entry.txt: one number in digits and nothing else.
"""

import os


TAB_COUNT = 137


def main() -> None:
    text = str(TAB_COUNT)
    # Gate: the entry must be UTF-8 text of 1 to 5 characters,
    # digits only, and not only whitespace.
    if not text.isdigit() or not 1 <= len(text) <= 5 or not text.strip():
        raise ValueError(f"invalid tab count for entry: {text!r}")
    os.makedirs("/output", exist_ok=True)
    with open("/output/entry.txt", "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)


if __name__ == "__main__":
    main()
