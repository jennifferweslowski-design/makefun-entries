"""Deterministic entry program for make.fun.

Writes the entry text to /output/entry.txt. No network, no randomness:
two runs write the same bytes.
"""

import os

TEXT = 'Null pointer at dawn\nthe debugger sighs softly\nship it anyway'


def main():
    os.makedirs("/output", exist_ok=True)
    with open("/output/entry.txt", "w", encoding="utf-8") as f:
        f.write(TEXT)


if __name__ == "__main__":
    main()
