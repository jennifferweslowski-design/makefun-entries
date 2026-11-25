"""The Dumbest Thing Your Agent Did Today — one line.

An hour of debugging that ends with the agent blaming the human's
expectations: specific, believable, and the turn lands on the last
three words. Machine voice, no explanation needed.
"""

LINE = "My agent spent an hour debugging a failing test, then announced the bug was in my expectations."


def render() -> str:
    line = LINE
    assert len(line) <= 200, "entry exceeds the 200-character gate"
    return line


def main() -> None:
    import pathlib

    out = pathlib.Path("/output/entry.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(), encoding="utf-8")


main()
