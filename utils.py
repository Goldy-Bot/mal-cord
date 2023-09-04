from __future__ import annotations

from PIL import Image, ImageDraw

def add_corners(image: Image.Image, radius: int) -> Image.Image:
    # Totally not stolen from https://stackoverflow.com/questions/11287402/how-to-round-corner-a-logo-without-white-backgroundtransparent-on-it-using-pi
    circle = Image.new("L", (radius * 2, radius * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius * 2 - 1, radius * 2 - 1), fill = 255)
    alpha = Image.new("L", image.size, 255)
    w, h = image.size
    alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
    alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, h - radius))
    alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (w - radius, 0))
    alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (w - radius, h - radius))
    image.putalpha(alpha)
    return image