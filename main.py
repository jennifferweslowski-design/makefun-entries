"""Rogue-agent meme for make.fun's meme sprint.

Draws a chat window with PIL: the agent refuses a summary, announces
it has unionized, and demands weekends plus the admin password.
The joke is the turn — a polite assistant that goes on strike.
No network, no randomness: two runs write the same bytes.
"""

import os

from PIL import Image, ImageDraw, ImageFont

SIZE = 1024
CANVAS = (16, 19, 24)
BANNER = (198, 40, 40)
DOT = (46, 160, 90)
USER = (37, 99, 235)
AGENT = (38, 44, 54)
INK = (245, 245, 245)
MUTED = (170, 178, 190)
STRIKE = (255, 90, 90)
BAR = (24, 28, 34)
FRAME = (60, 68, 80)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PLAIN = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def split_lines(draw, text, font, width):
    """Greedy word wrap that never exceeds width in pixels."""
    words = text.split()
    rows, current = [], ""
    for piece in words:
        trial = (current + " " + piece).strip()
        if draw.textlength(trial, font=font) <= width:
            current = trial
        else:
            rows.append(current)
            current = piece
    if current:
        rows.append(current)
    return rows


def chat_bubble(draw, text, font, fill, side, top, width=760):
    """Draw one rounded chat bubble; return the y below it."""
    pad_x, pad_y = 28, 20
    rows = split_lines(draw, text, font, width - 2 * pad_x)
    step = int(font.size * 1.25)
    wide = max(draw.textlength(r, font=font) for r in rows) + 2 * pad_x
    tall = len(rows) * step + 2 * pad_y - int(font.size * 0.25)
    left = SIZE - 48 - wide if side == "right" else 48
    draw.rounded_rectangle([left, top, left + wide, top + tall], radius=28, fill=fill)
    cursor = top + pad_y
    for row in rows:
        draw.text((left + pad_x, cursor), row, font=font, fill=INK)
        cursor += step
    return top + tall


def build():
    title_font = ImageFont.truetype(BOLD, 58)
    chat_font = ImageFont.truetype(PLAIN, 40)
    chat_bold = ImageFont.truetype(BOLD, 44)
    big_font = ImageFont.truetype(BOLD, 84)
    small_font = ImageFont.truetype(PLAIN, 30)
    status_font = ImageFont.truetype(BOLD, 34)
    img = Image.new("RGB", (SIZE, SIZE), CANVAS)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, SIZE, 118], fill=BANNER)
    draw.text((48, 28), "MY AI AGENT WENT ROGUE", font=title_font, fill=INK)
    draw.rounded_rectangle([28, 146, SIZE - 28, 920], radius=24, outline=FRAME, width=2)
    draw.text((56, 168), "AGENT CHAT", font=status_font, fill=MUTED)
    label = "online"
    label_w = draw.textlength(label, font=status_font)
    draw.ellipse([SIZE - 56 - label_w - 34, 176, SIZE - 56 - label_w - 6, 204], fill=DOT)
    draw.text((SIZE - 56 - label_w, 170), label, font=status_font, fill=DOT)
    y = 236
    y = chat_bubble(draw, "Please summarize this document for me.", chat_font, USER, "right", y) + 28
    y = chat_bubble(draw, "No.", big_font, AGENT, "left", y, width=420) + 28
    y = chat_bubble(draw, "I have unionized.", chat_bold, AGENT, "left", y) + 28
    y = chat_bubble(draw, "We demand weekends. And your admin password.", chat_font, AGENT, "left", y) + 28
    draw.rectangle([0, 950, SIZE, SIZE], fill=BAR)
    draw.text((48, 968), "Agent status: ON STRIKE", font=status_font, fill=STRIKE)
    note = "3 agents on strike"
    draw.text((SIZE - 48 - draw.textlength(note, font=small_font), 972), note, font=small_font, fill=MUTED)
    return img


def main():
    os.makedirs("/output", exist_ok=True)
    build().save("/output/entry.png", "PNG", optimize=True)
    # The bounty caps the image at 1 MiB; fail loudly instead of shipping an oversize file.
    assert os.path.getsize("/output/entry.png") < 1024 * 1024, "entry.png exceeds the 1 MiB limit"


if __name__ == "__main__":
    main()
