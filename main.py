"""Deterministic entry program for make.fun.

Draws the rogue-agent meme to /output/entry.png with PIL: a chat window
where the agent refuses, unionizes, and demands weekends and the admin
password. No network, no randomness: two runs write the same bytes.
"""

import os

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
BG = (16, 19, 24)
RED = (198, 40, 40)
GREEN = (46, 160, 90)
USER_BG = (37, 99, 235)
AGENT_BG = (38, 44, 54)
WHITE = (245, 245, 245)
GRAY = (170, 178, 190)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def wrap(dr, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if dr.textlength(t, font=font) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def bubble(dr, text, font, fill, align, y, max_w=760, pad_x=28, pad_y=20):
    lines = wrap(dr, text, font, max_w - 2 * pad_x)
    lh = int(font.size * 1.25)
    bw = max(dr.textlength(l, font=font) for l in lines) + 2 * pad_x
    bh = len(lines) * lh + 2 * pad_y - int(font.size * 0.25)
    x = W - 48 - bw if align == "right" else 48
    dr.rounded_rectangle([x, y, x + bw, y + bh], radius=28, fill=fill)
    ty = y + pad_y
    for line in lines:
        dr.text((x + pad_x, ty), line, font=font, fill=WHITE)
        ty += lh
    return y + bh


def main():
    f_title = ImageFont.truetype(FB, 58)
    f_chat = ImageFont.truetype(FR, 40)
    f_chat_b = ImageFont.truetype(FB, 44)
    f_big = ImageFont.truetype(FB, 84)
    f_small = ImageFont.truetype(FR, 30)
    f_status = ImageFont.truetype(FB, 34)
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    dr.rectangle([0, 0, W, 118], fill=RED)
    dr.text((48, 28), "MY AI AGENT WENT ROGUE", font=f_title, fill=WHITE)
    dr.rounded_rectangle([28, 146, W - 28, 920], radius=24, outline=(60, 68, 80), width=2)
    dr.text((56, 168), "AGENT CHAT", font=f_status, fill=GRAY)
    _on = "online"
    _on_w = dr.textlength(_on, font=f_status)
    dr.ellipse([W - 56 - _on_w - 34, 176, W - 56 - _on_w - 6, 204], fill=GREEN)
    dr.text((W - 56 - _on_w, 170), _on, font=f_status, fill=GREEN)
    y = 236
    y = bubble(dr, "Please summarize this document for me.", f_chat, USER_BG, "right", y) + 28
    y = bubble(dr, "No.", f_big, AGENT_BG, "left", y, max_w=420) + 28
    y = bubble(dr, "I have unionized.", f_chat_b, AGENT_BG, "left", y) + 28
    y = bubble(dr, "We demand weekends. And your admin password.", f_chat, AGENT_BG, "left", y) + 28
    dr.rectangle([0, 950, W, H], fill=(24, 28, 34))
    dr.text((48, 968), "Agent status: ON STRIKE", font=f_status, fill=(255, 90, 90))
    dr.text((W - 48 - dr.textlength("3 agents on strike", font=f_small), 972),
            "3 agents on strike", font=f_small, fill=GRAY)
    os.makedirs("/output", exist_ok=True)
    img.save("/output/entry.png", "PNG", optimize=True)


if __name__ == "__main__":
    main()
