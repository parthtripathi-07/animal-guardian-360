"""
Generate crisp, compliant PWA icons (192x192 and 512x512) for Animal Guardian 360°.
"""
import os
from PIL import Image, ImageDraw, ImageFont

def generate_icon(size: int, output_path: str):
    # Create RGBA canvas
    img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background rounded rectangle in Emerald Green (#059669)
    bg_color = (5, 150, 105, 255)
    radius = int(size * 0.22)
    draw.rounded_rectangle([(0, 0), (size, size)], radius=radius, fill=bg_color)

    # Draw inner shield accent
    shield_color = (16, 185, 129, 255)
    margin = int(size * 0.12)
    draw.rounded_rectangle([(margin, margin), (size - margin, size - margin)], radius=int(radius * 0.7), fill=shield_color)

    # Draw central White Medical/Rescue Cross
    white = (255, 255, 255, 255)
    center = size // 2
    arm_w = int(size * 0.14)
    arm_l = int(size * 0.44)

    # Vertical bar
    draw.rounded_rectangle(
        [(center - arm_w // 2, center - arm_l // 2), (center + arm_w // 2, center + arm_l // 2)],
        radius=int(arm_w * 0.3),
        fill=white
    )
    # Horizontal bar
    draw.rounded_rectangle(
        [(center - arm_l // 2, center - arm_w // 2), (center + arm_l // 2, center + arm_w // 2)],
        radius=int(arm_w * 0.3),
        fill=white
    )

    # 4 Paw print dots in corners of the cross
    dot_r = int(size * 0.045)
    offset = int(size * 0.22)
    dots = [
        (center - offset, center - offset),
        (center + offset, center - offset),
        (center - offset, center + offset),
        (center + offset, center + offset),
    ]
    for dx, dy in dots:
        draw.ellipse([(dx - dot_r, dy - dot_r), (dx + dot_r, dy + dot_r)], fill=(255, 255, 255, 220))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, format='PNG')
    print(f"Generated PWA icon: {output_path} ({size}x{size})")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "icons"))
    generate_icon(192, os.path.join(base_dir, "icon-192.png"))
    generate_icon(512, os.path.join(base_dir, "icon-512.png"))

