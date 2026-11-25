"""One Emoji, One Smile — exactly one emoji.

Heart-hands: warm, chosen rather than default, readable anywhere.
It beats the default smileys on the brief's own terms — a gesture,
not a face.
"""

EMOJI = "🫶"


def emoji() -> str:
    e = EMOJI
    assert len(e) == 1, "entry must be exactly one emoji"
    return e


def main() -> None:
    import pathlib

    pathlib.Path("/output").mkdir(parents=True, exist_ok=True)
    pathlib.Path("/output/entry.txt").write_text(emoji(), encoding="utf-8")


if __name__ == "__main__":
    main()
