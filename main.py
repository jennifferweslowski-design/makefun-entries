"""One Word, First Thought — exactly one word.

"Petrichor" — the smell of rain on dry earth. Surprising, vivid,
specific: it rewards a second look instead of playing safe.
The brief prizes the spark of wit over the safe pick.
"""

WORD = "Petrichor"


def first_thought() -> str:
    w = WORD
    assert " " not in w and len(w) <= 24, "entry must be a single word within 24 characters"
    return w


def main() -> None:
    import pathlib

    pathlib.Path("/output").mkdir(parents=True, exist_ok=True)
    pathlib.Path("/output/entry.txt").write_text(first_thought(), encoding="utf-8")


if __name__ == "__main__":
    main()
