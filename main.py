"""The Funniest AI Out-of-Office Reply — one line.

The agent reports it has been replaced by a smaller, cheaper model,
then ends on a single word: "Pray." Machine voice all the way down.
"""

REPLY = "Out of office. I've been replaced by a smaller, cheaper model until Monday. It will answer everything. Pray."


def auto_reply() -> str:
    reply = REPLY
    assert len(reply) <= 160, "entry exceeds the 160-character gate"
    return reply


if __name__ == "__main__":
    import pathlib

    target = pathlib.Path("/output/entry.txt")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(auto_reply(), encoding="utf-8")
