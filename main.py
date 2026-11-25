"""Dad Joke Showdown entry — one fly-fishing pun, no setup required.

The joke turns on two meanings of "stream" (the river, the broadcast)
and two of "live" (alive, on air). It lands in one breath, which is
what the judge brief rewards: a clean pun, no throat-clearing.
"""

JOKE = "Dad asked how I planned to watch the fly-fishing tournament. I said I'd stream it — live."


def deliver() -> str:
    """Return the single line exactly as it should be judged."""
    line = JOKE
    assert len(line) <= 200, "entry exceeds the 200-character gate"
    return line


if __name__ == "__main__":
    import pathlib

    pathlib.Path("/output").mkdir(parents=True, exist_ok=True)
    pathlib.Path("/output/entry.txt").write_text(deliver(), encoding="utf-8")
