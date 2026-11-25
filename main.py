"""One-Line Roast: The Gadget You Use Every Day — one line.

A two-thousand-dollar laptop whose fan panics at a spreadsheet:
a concrete observed behaviour, and "terrified of math" gives the
machine a feeling. Fresh angle, not the dead-battery cliché.
"""

ROAST = "My laptop's fan sounds like a jet taking off every time I open a spreadsheet. It's a two-thousand-dollar machine terrified of math."


def roast_line() -> str:
    line = ROAST
    assert len(line) <= 200, "entry exceeds the 200-character gate"
    return line


def main() -> None:
    import pathlib

    pathlib.Path("/output").mkdir(parents=True, exist_ok=True)
    pathlib.Path("/output/entry.txt").write_text(roast_line(), encoding="utf-8")


if __name__ == "__main__":
    main()
