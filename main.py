"""Make the AI Judge Laugh: Office Jokes — one line.

A meeting about too many meetings that runs over and spawns a
follow-up: the premise eats itself. Recognition first, punchline last.
"""

JOKE = "My manager called a meeting to discuss why we have too many meetings. It ran over, so we scheduled a follow-up."


def entry_text() -> str:
    text = JOKE
    assert len(text) <= 199, "entry exceeds the 199-character gate"
    return text


if __name__ == "__main__":
    import os

    os.makedirs("/output", exist_ok=True)
    with open("/output/entry.txt", "w", encoding="utf-8") as handle:
        handle.write(entry_text())
