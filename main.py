"""make.fun news-image entry: copy the prepared image to /output/entry.png.

Deterministic, no network: the same bytes are written on every run.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))

os.makedirs("/output", exist_ok=True)
shutil.copyfile(os.path.join(HERE, "entry.png"), "/output/entry.png")
print("wrote /output/entry.png")
