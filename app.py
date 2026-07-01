from __future__ import annotations

import io
import re
import zipfile
from typing import List, Tuple

from flask import Flask, jsonify, render_template, request, send_file
from PIL import Image, ImageColor, ImageDraw, ImageFont, UnidentifiedImageError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

DEFAULT_LABELS: List[Tuple[str, str, str]] = [
    ("SALE", "#e53935", "#ffffff"),
    ("20% OFF", "#fb8c00", "#ffffff"),
    ("BEST SELLER", "#43a047", "#ffffff"),
    ("NEW ARRIVAL", "#1e88e5", "#ffffff"),
    ("LIMITED OFFER", "#d81b60", "#ffffff"),
    ("HOT DEAL", "#8e24aa", "#ffffff"),
    ("PREMIUM", "#00897b", "#ffffff"),
    ("30% OFF", "#f4511e", "#ffffff"),
    ("TRENDING", "#3949ab", "#ffffff"),
    ("BEST PRICE", "#6d4c41", "#ffffff"),
]

AUTO_LABELS: List[str] = [
    "SALE",
    "1% OFF",
    "1% OFF",
    "2% OFF",
    "2% OFF",
    "3% OFF",
    "4% OFF",
    "5% OFF",
    "6% OFF",
    "7% OFF",
    "BEST SELLER",
    "NEW ARRIVAL",
    "HOT DEAL",
    "TRENDING",
    "LIMITED OFFER",
    "PREMIUM",
    "BEST PRICE",
    "SPECIAL DEAL",
    "FLASH SALE",
    "SUPER SAVER",
    "TODAY ONLY",
    "MEGA OFFER",
    "HOT PICK",
    "TOP CHOICE",
    "CUSTOMER FAVORITE",
    "MOST WANTED",
    "TOP RATED",
    "EDITOR'S PICK",
    "EXCLUSIVE",
    "ONLINE ONLY",
    "SHOP NOW",
    "BUY NOW",
    "ACT FAST",
    "HURRY UP",
    "SELLING FAST",
    "LOW STOCK",
    "LAST CHANCE",
    "FINAL SALE",
    "CLEARANCE",
    "BIG SAVINGS",
    "SAVE BIG",
    "BEST VALUE",
    "VALUE DEAL",
    "SMART BUY",
    "LIMITED STOCK",
    "JUST IN",
    "JUST ARRIVED",
    "FRESH STOCK",
    "BACK IN STOCK",
    "NEW COLLECTION",
    "NEW DESIGN",
    "NEW LOOK",
    "TOP TREND",
    "TREND ALERT",
    "SEASON SALE",
    "SUMMER SALE",
    "WINTER SALE",
    "SPRING SALE",
    "FESTIVE SALE",
    "HOLIDAY SALE",
    "WEEKEND DEAL",
    "MIDWEEK OFFER",
    "DAILY DEAL",
    "WEEKLY DEAL",
    "MONTHLY SPECIAL",
    "EXTRA SAVINGS",
    "EXTRA 10% OFF",
    "BUY 1 GET 1",
    "BUY 2 GET 1",
    "FREE SHIPPING",
    "FREE GIFT",
    "FREE DELIVERY",
    "SPECIAL PRICE",
    "PRICE DROP",
    "LOWEST PRICE",
    "BEST DEAL",
    "UNBEATABLE PRICE",
    "BUDGET PICK",
    "LUXURY PICK",
    "PREMIUM QUALITY",
    "TOP QUALITY",
    "HIGH QUALITY",
    "HANDPICKED",
    "RECOMMENDED",
    "POPULAR",
    "VIRAL",
    "MUST HAVE",
    "DON'T MISS",
    "SHOP TODAY",
    "ONLY TODAY",
    "ENDS SOON",
    "LIMITED TIME",
    "SPECIAL EDITION",
    "EXCLUSIVE OFFER",
    "IN DEMAND",
    "TOP SELLING",
    "AMAZING DEAL",
    "SUPER DEAL",
    "INCREDIBLE OFFER",
    "HOT PRICE",
]

def safe_int(value, default, min_value, max_value):
    try:
        parsed = int(value)
        return max(min_value, min(parsed, max_value))
    except (TypeError, ValueError):
        return default


def safe_float(value, default, min_value, max_value):
    try:
        parsed = float(value)
        return max(min_value, min(parsed, max_value))
    except (TypeError, ValueError):
        return default


def validate_hex_color(value, default="#e53935"):
    if not value:
        return default
    value = str(value).strip()
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return default
    return value.lower()


def clean_filename(text):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", text).strip("_")[:40] or "promo"


def parse_labels(raw_text):
    labels = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        text = parts[0] if parts else ""
        badge_color = validate_hex_color(parts[1] if len(parts) > 1 else "", "#e53935")
        text_color = validate_hex_color(parts[2] if len(parts) > 2 else "", "#ffffff")
        if text:
            labels.append((text, badge_color, text_color))
    return labels or list(DEFAULT_LABELS)


def generate_auto_labels(count):
    labels = []
    while len(labels) < count:
        for item in AUTO_LABELS:
            labels.append((item, "#e53935", "#ffffff"))
            if len(labels) >= count:
                break
    return labels


def get_font(size=36):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except (OSError, IOError):
        return ImageFont.load_default()


def get_position(position, w, h, box_w, box_h, margin):
    if position == "top-right":
        return w - box_w - margin, margin
    if position == "bottom-left":
        return margin, h - box_h - margin
    if position == "bottom-right":
        return w - box_w - margin, h - box_h - margin
    if position == "center":
        return (w - box_w) // 2, (h - box_h) // 2
    if position == "top-center":
        return (w - box_w) // 2, margin
    if position == "bottom-center":
        return (w - box_w) // 2, h - box_h - margin
    return margin, margin


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
    font = get_font(font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    box_w = text_w + padding_x * 2
    box_h = text_h + padding_y * 2
    x, y = get_position(position, img.width, img.height, box_w, box_h, margin)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if shadow_enabled:
        shadow_offset = 8
        overlay_draw.rounded_rectangle((x + shadow_offset, y + shadow_offset, x + box_w + shadow_offset, y + box_h + shadow_offset), radius=radius, fill=(0, 0, 0, 80))

    fill_color = ImageColor.getrgb(badge_color)
    alpha = int(255 * max(0.05, opacity))
    overlay_draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=radius, fill=(fill_color[0], fill_color[1], fill_color[2], alpha))

    if border_width > 0:
        border_rgb = ImageColor.getrgb(border_color)
        overlay_draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=radius, outline=(border_rgb[0], border_rgb[1], border_rgb[2], alpha), width=border_width)

    overlay_draw.text((x + padding_x, y + padding_y), text, fill=(ImageColor.getrgb(text_color)[0], ImageColor.getrgb(text_color)[1], ImageColor.getrgb(text_color)[2], 255), font=font)

    img = Image.alpha_composite(img, overlay)
    return img.convert("RGB")


def create_zip_in_memory(items):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for filename, image_bytes in items:
            archive.writestr(filename, image_bytes)
    buffer.seek(0)
    return buffer


@app.errorhandler(413)
def handle_request_too_large(_error):
    return jsonify({"error": "The uploaded image is too large. Please choose a file smaller than 16 MB."}), 413


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/", methods=["POST"])
def generate_images():
    try:
        image_file = request.files.get("image")
        if not image_file or image_file.filename == "":
            return jsonify({"error": "Please upload an image before generating promo files."}), 400

        filename = image_file.filename or ""
        if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            return jsonify({"error": "Unsupported image format. Please upload JPG, JPEG, PNG, or WEBP."}), 400

        label_mode = request.form.get("label_mode", "default")
        image_count = safe_int(request.form.get("image_count"), 1, 1, 100)
        border_enabled = request.form.get("border_enabled", "on") == "on"
        border_color = validate_hex_color(request.form.get("border_color"), "#ffffff")
        border_width = safe_int(request.form.get("border_width"), 8, 0, 40)
        border_style = request.form.get("border_style", "solid")
        border_radius = safe_int(request.form.get("border_radius"), 18, 0, 80)

        badge_text = request.form.get("badge_text", "SALE").strip() or "SALE"
        badge_background = validate_hex_color(request.form.get("badge_background"), "#e53935")
        output_preset = request.form.get("output_preset", "original")
        badge_text_color = validate_hex_color(request.form.get("badge_text_color"), "#ffffff")
        badge_opacity = safe_float(request.form.get("badge_opacity"), 0.95, 0.1, 1.0)
        badge_position = request.form.get("badge_position", "top-left")
        badge_font_size = safe_int(request.form.get("badge_font_size"), 36, 14, 96)
        badge_padding_x = safe_int(request.form.get("badge_padding_x"), 18, 6, 80)
        badge_padding_y = safe_int(request.form.get("badge_padding_y"), 12, 6, 80)
        badge_radius = safe_int(request.form.get("badge_radius"), 18, 0, 60)
        badge_margin = safe_int(request.form.get("badge_margin"), 24, 6, 120)
        badge_border_color = validate_hex_color(request.form.get("badge_border_color"), "#ffffff")
        badge_border_width = safe_int(request.form.get("badge_border_width"), 1, 0, 12)
        shadow_enabled = request.form.get("badge_shadow", "on") == "on"

        labels_source = request.form.get("labels", "").strip()

        if label_mode == "custom":
            labels = parse_labels(labels_source)
        elif label_mode == "auto":
            labels = generate_auto_labels(image_count)
        else:
            labels = list(DEFAULT_LABELS)

        if len(labels) < image_count:
            extra = generate_auto_labels(image_count - len(labels))
            labels = labels + extra

        labels = labels[:image_count]

        if not labels:
            labels = list(DEFAULT_LABELS)[:1]

        image_file.stream.seek(0)
        try:
            with Image.open(image_file.stream) as img_obj:
                img_obj.load()
                base_image = resize_for_preset(img_obj, output_preset)
        except (UnidentifiedImageError, OSError, ValueError, EOFError):
            return jsonify({"error": "The uploaded file is not a valid image. Please try another file."}), 400

        files_to_zip = []
        for index, label in enumerate(labels, start=1):
            label_text = label[0] if isinstance(label, tuple) else badge_text
            label_bg = label[1] if isinstance(label, tuple) and len(label) > 1 else badge_background
            label_text_color = label[2] if isinstance(label, tuple) and len(label) > 2 else badge_text_color

            output_image = base_image.copy()
            output_image = draw_border(output_image, border_enabled, border_color, border_width, border_style, border_radius)
            output_image = draw_badge(
                output_image,
                label_text,
                label_bg,
                label_text_color,
                badge_position,
                badge_font_size,
                badge_padding_x,
                badge_padding_y,
                badge_radius,
                badge_margin,
                badge_opacity,
                badge_border_color,
                badge_border_width,
                shadow_enabled,
            )

            buffer = io.BytesIO()
            output_image.save(buffer, format="PNG")
            files_to_zip.append((f"promo_{index:02d}_{clean_filename(label_text)}.png", buffer.getvalue()))

        zip_buffer = create_zip_in_memory(files_to_zip)
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name="promo_images.zip",
            mimetype="application/zip",
        )
    except Exception as exc:  # pragma: no cover
        return jsonify({"error": f"Processing failed: {exc}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)