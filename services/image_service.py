from __future__ import annotations

from PIL import Image, ImageColor, ImageDraw
from utils.helpers import get_font, get_position

def calculate_badge_metrics(image_width, image_height, text, base_font_size, base_padding_x, base_padding_y, base_radius, base_margin, base_border_width):
    if not text:
        return {
            "font_size": max(20, int(min(image_width, image_height) * 0.04)),
            "padding_x": max(12, int(min(image_width, image_height) * 0.02)),
            "padding_y": max(8, int(min(image_width, image_height) * 0.012)),
            "radius": max(6, int(min(image_width, image_height) * 0.012)),
            "margin": max(10, int(min(image_width, image_height) * 0.016)),
            "border_width": max(1, int(min(image_width, image_height) * 0.002)),
            "shadow_offset": max(4, int(min(image_width, image_height) * 0.008)),
        }

    image_width = max(1, int(image_width))
    image_height = max(1, int(image_height))
    min_side = min(image_width, image_height)

    text_length_factor = min(1.0, max(0.2, len(text) / 24.0))
    font_size = max(int(base_font_size * 0.9), int(image_width * 0.055), 24)
    padding_x = max(18, int(image_width * 0.032))
    padding_y = max(12, int(min_side * 0.017))
    radius = max(10, int(min_side * 0.018))
    margin = max(12, int(min_side * 0.020))
    border_width = max(1, int(min_side * 0.002))
    shadow_offset = max(5, int(min_side * 0.008))

    target_width_ratio = 0.22 + min(0.12, text_length_factor * 0.12)
    target_box_width = max(int(image_width * 0.22), int(image_width * min(0.35, target_width_ratio)))

    sample_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    font = get_font(font_size)
    bbox = sample_draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    box_w = max(text_w + padding_x * 2, target_box_width)

    return {
        "font_size": font_size,
        "padding_x": padding_x,
        "padding_y": padding_y,
        "radius": radius,
        "margin": margin,
        "border_width": border_width,
        "shadow_offset": shadow_offset,
        "box_width": box_w,
    }


def resize_for_preset(image, preset):
    if preset == "meesho_square":
        target_size = (1080, 1080)
    elif preset == "meesho_portrait":
        target_size = (1080, 1350)
    elif preset == "meesho_story":
        target_size = (1080, 1920)
    elif preset == "meesho_banner":
        target_size = (1080, 540)
    else:
        return image.convert("RGB")

    img = image.convert("RGB")
    width, height = img.size
    target_width, target_height = target_size
    target_ratio = target_width / target_height
    source_ratio = width / height

    if source_ratio > target_ratio:
        new_width = target_width
        new_height = max(1, int(target_width / source_ratio))
    else:
        new_height = target_height
        new_width = max(1, int(target_height * source_ratio))

    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", target_size, (255, 255, 255))
    offset_x = (target_width - new_width) // 2
    offset_y = (target_height - new_height) // 2
    canvas.paste(resized, (offset_x, offset_y))
    return canvas


def draw_border(image, enabled, color, width, style, radius):
    if not enabled:
        return image

    img = image.convert("RGBA")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    color_rgb = ImageColor.getrgb(color)

    if style == "gradient":
        colors = [color_rgb, (255, 255, 255)]
        for i in range(width):
            gradient_color = tuple(int(colors[0][j] + (colors[1][j] - colors[0][j]) * (i / max(width, 1))) for j in range(3))
            draw.rounded_rectangle((i, i, w - 1 - i, h - 1 - i), radius=max(0, radius - i), outline=gradient_color, width=1)
        return img.convert("RGB")

    if style == "double":
        draw.rounded_rectangle((1, 1, w - 2, h - 2), radius=radius, outline=color_rgb, width=max(1, width // 2))
        draw.rounded_rectangle((width + 2, width + 2, w - width - 3, h - width - 3), radius=max(0, radius - width), outline=color_rgb, width=max(1, width // 2))
        return img.convert("RGB")

    if style == "dashed":
        dash = max(4, width * 2)
        gap = max(4, width * 2)
        edges = [
            ((0, 0), (w, 0)),
            ((w, 0), (w, h)),
            ((w, h), (0, h)),
            ((0, h), (0, 0)),
        ]
        for start, end in edges:
            x0, y0 = start
            x1, y1 = end
            if x0 == x1:
                coords = [(x0, y) for y in range(y0, y1 + 1, dash + gap)]
                for idx, (x, y) in enumerate(coords):
                    if idx % 2 == 0:
                        draw.line((x, y, x, min(y + dash, h)), fill=color_rgb, width=max(1, width))
            else:
                coords = [(x, y0) for x in range(x0, x1 + 1, dash + gap)]
                for idx, (x, y) in enumerate(coords):
                    if idx % 2 == 0:
                        draw.line((x, y, min(x + dash, w), y), fill=color_rgb, width=max(1, width))
        return img.convert("RGB")

    if style == "dotted":
        step = max(2, width)
        for x in range(0, w, step * 2):
            draw.ellipse((x, 0, x + step, step), fill=color_rgb)
            draw.ellipse((x, h - step, x + step, h), fill=color_rgb)
        for y in range(0, h, step * 2):
            draw.ellipse((0, y, step, y + step), fill=color_rgb)
            draw.ellipse((w - step, y, w, y + step), fill=color_rgb)
        return img.convert("RGB")

    draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, outline=color_rgb, width=width)
    return img.convert("RGB")


def draw_badge(image, text, badge_color, text_color, position, font_size, padding_x, padding_y, radius, margin, opacity, border_color, border_width, shadow_enabled):
    if not text:
        return image

    img = image.convert("RGBA")
    draw = ImageDraw.Draw(img)
    metrics = calculate_badge_metrics(img.width, img.height, text, font_size, padding_x, padding_y, radius, margin, border_width)
    font = get_font(metrics["font_size"])

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    box_w = max(text_w + metrics["padding_x"] * 2, metrics.get("box_width", text_w + metrics["padding_x"] * 2))
    box_h = text_h + metrics["padding_y"] * 2
    x, y = get_position(position, img.width, img.height, box_w, box_h, metrics["margin"])

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if shadow_enabled:
        overlay_draw.rounded_rectangle((x + metrics["shadow_offset"], y + metrics["shadow_offset"], x + box_w + metrics["shadow_offset"], y + box_h + metrics["shadow_offset"]), radius=metrics["radius"], fill=(0, 0, 0, 80))

    fill_color = ImageColor.getrgb(badge_color)
    alpha = int(255 * max(0.05, opacity))
    overlay_draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=metrics["radius"], fill=(fill_color[0], fill_color[1], fill_color[2], alpha))

    if metrics["border_width"] > 0:
        border_rgb = ImageColor.getrgb(border_color)
        overlay_draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=metrics["radius"], outline=(border_rgb[0], border_rgb[1], border_rgb[2], alpha), width=metrics["border_width"])

    text_x = x + metrics["padding_x"] - bbox[0]
    text_y = y + (box_h - text_h) // 2 - bbox[1]
    overlay_draw.text((text_x, text_y), text, fill=(ImageColor.getrgb(text_color)[0], ImageColor.getrgb(text_color)[1], ImageColor.getrgb(text_color)[2], 255), font=font)

    img = Image.alpha_composite(img, overlay)
    return img.convert("RGB")
