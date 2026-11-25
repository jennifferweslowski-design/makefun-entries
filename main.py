"""One Word From Grandma — exactly one word.

A grandma watching a machine talk back would not say "Skynet" — that
is the grandson's word. She would call it what it looks like to her:
witchcraft. Warm, baffled, and tied to the thing itself.
"""

WORD = "Witchcraft"


def word() -> str:
    w = WORD
    assert " " not in w and len(w) <= 30, "entry must be a single word within 30 characters"
    return w


def main() -> None:
    import pathlib

    pathlib.Path("/output").mkdir(parents=True, exist_ok=True)
    pathlib.Path("/output/entry.txt").write_text(word(), encoding="utf-8")


if __name__ == "__main__":
    main()
