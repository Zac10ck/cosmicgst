#!/usr/bin/env python3
"""
Generate application icon for GST Billing Software
Creates a professional-looking icon with multiple sizes for Windows
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not found. Attempting to install...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pillow'])
        from PIL import Image, ImageDraw, ImageFont
    except Exception as e:
        print(f"Could not install Pillow: {e}")
        print("\nPlease install manually: pip install pillow")
        print("Then run this script again.")
        sys.exit(1)


def create_icon():
    """Create a multi-size .ico file for Windows"""

    # Icon sizes for Windows (standard sizes)
    sizes = [16, 32, 48, 64, 128, 256]

    images = []

    for size in sizes:
        # Create image with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Colors
        bg_color = (41, 128, 185)      # Professional blue
        accent_color = (46, 204, 113)   # Green accent
        text_color = (255, 255, 255)    # White text

        # Draw rounded rectangle background
        padding = max(1, size // 16)

        # Main background circle/rounded shape
        draw.ellipse(
            [padding, padding, size - padding, size - padding],
            fill=bg_color
        )

        # Draw a small accent (like a receipt/bill symbol)
        if size >= 32:
            # Receipt shape
            receipt_left = size // 4
            receipt_top = size // 5
            receipt_right = size - size // 4
            receipt_bottom = size - size // 5

            # White receipt background
            draw.rectangle(
                [receipt_left, receipt_top, receipt_right, receipt_bottom],
                fill=(255, 255, 255, 230)
            )

            # Lines on receipt (representing text)
            line_height = max(2, size // 16)
            line_gap = max(3, size // 10)
            line_start_y = receipt_top + line_gap

            for i in range(3):
                y = line_start_y + i * line_gap
                if y + line_height < receipt_bottom - line_gap:
                    # Varying line widths
                    line_width = receipt_right - receipt_left - size // 8
                    if i == 1:
                        line_width = line_width * 2 // 3

                    draw.rectangle(
                        [receipt_left + size // 16, y,
                         receipt_left + size // 16 + line_width, y + line_height],
                        fill=bg_color
                    )

            # Rupee symbol or checkmark at bottom
            if size >= 48:
                # Green checkmark
                check_size = size // 6
                check_x = receipt_right - check_size - size // 16
                check_y = receipt_bottom - check_size - size // 16

                draw.ellipse(
                    [check_x, check_y, check_x + check_size, check_y + check_size],
                    fill=accent_color
                )

        images.append(img)

    # Save as .ico file
    script_dir = Path(__file__).parent
    icon_path = script_dir / 'icon.ico'

    # Save with multiple sizes
    images[0].save(
        icon_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )

    print(f"Icon created successfully: {icon_path}")

    # Also save a PNG version for other uses
    png_path = script_dir / 'icon.png'
    images[-1].save(png_path, format='PNG')  # Save largest size as PNG
    print(f"PNG version saved: {png_path}")

    return str(icon_path)


def create_simple_icon():
    """Create a simpler icon if the fancy one fails"""

    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Simple blue circle with white "B" for Billing
        padding = max(1, size // 10)

        # Blue background
        draw.ellipse(
            [padding, padding, size - padding, size - padding],
            fill=(41, 128, 185)
        )

        # Try to draw "₹" or "B" text
        try:
            # Calculate font size (roughly 60% of icon size)
            font_size = int(size * 0.5)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()

            text = "₹"

            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Center the text
            x = (size - text_width) // 2
            y = (size - text_height) // 2 - bbox[1]

            draw.text((x, y), text, fill=(255, 255, 255), font=font)

        except Exception as e:
            # Fallback: draw a simple shape
            inner_pad = size // 4
            draw.rectangle(
                [inner_pad, inner_pad, size - inner_pad, size - inner_pad],
                fill=(255, 255, 255, 200)
            )

        images.append(img)

    script_dir = Path(__file__).parent
    icon_path = script_dir / 'icon.ico'

    images[0].save(
        icon_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )

    print(f"Simple icon created: {icon_path}")
    return str(icon_path)


if __name__ == "__main__":
    print("Creating GST Billing icon...")
    print("=" * 40)

    try:
        icon_path = create_icon()
    except Exception as e:
        print(f"Fancy icon failed: {e}")
        print("Trying simple icon...")
        icon_path = create_simple_icon()

    print("=" * 40)
    print("Done! Icon is ready for use.")
