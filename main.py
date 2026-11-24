"""Deterministic entry program for make.fun.

Copies the front-page image shipped in this repository to
/output/entry.png. No network, no randomness: two runs write the same
bytes.
"""

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    os.makedirs("/output", exist_ok=True)
    shutil.copyfile(os.path.join(HERE, "entry.png"), "/output/entry.png")


if __name__ == "__main__":
    main()
