"""make.fun news-image entry: write the prepared image to /output/entry.png.

Deterministic, no network: the same bytes are written on every run.
Before copying, the image is validated against the competition's limits
(1024x1024 PNG, at most 1 MiB); a bad image fails loudly instead of
being submitted silently.
"""
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.png")
TARGET = "/output/entry.png"
MAX_BYTES = 1_048_576
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def read_png_size(path):
    """Return (width, height) from a PNG file, verifying its signature."""
    with open(path, "rb") as f:
        header = f.read(33)
    if header[:8] != PNG_SIGNATURE:
        raise ValueError(f"{path}: not a PNG file (bad signature)")
    if len(header) < 33 or header[12:16] != b"IHDR":
        raise ValueError(f"{path}: missing IHDR chunk")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def main():
    if not os.path.exists(SOURCE):
        print(f"missing source image: {SOURCE}", file=sys.stderr)
        return 1
    size = os.path.getsize(SOURCE)
    if size > MAX_BYTES:
        print(f"{SOURCE}: {size} bytes, over the 1 MiB limit", file=sys.stderr)
        return 1
    width, height = read_png_size(SOURCE)
    if (width, height) != (1024, 1024):
        print(f"{SOURCE}: {width}x{height}, expected 1024x1024", file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(TARGET), exist_ok=True)
    shutil.copyfile(SOURCE, TARGET)
    print(f"wrote {TARGET} ({width}x{height}, {size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
