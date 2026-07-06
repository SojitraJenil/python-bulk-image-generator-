from __future__ import annotations

import io
import re
import zipfile
from typing import List, Tuple
from PIL import ImageFont

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
    "STATUS ALERT",
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
    font_names = [
        "arialbd.ttf",               # Windows Arial Bold
        "arial.ttf",                 # Windows Arial
        "segoeuib.ttf",              # Windows Segoe UI Bold
        "calibrib.ttf",              # Windows Calibri Bold
        "DejaVuSans-Bold.ttf",       # Linux standard
        "Arial Bold.ttf",            # macOS Arial Bold
        "Helvetica.ttc",             # macOS Helvetica
        "LiberationSans-Bold.ttf"    # Linux alternative
    ]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except (OSError, IOError):
            continue
            
    # Try system paths directly if not found by name
    fallback_paths = [
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    for path in fallback_paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
            
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
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


def create_zip_in_memory(items):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for filename, image_bytes in items:
            archive.writestr(filename, image_bytes)
    buffer.seek(0)
    return buffer


def safe_int(value, default: int = 0, min_val: int = None, max_val: int = None) -> int:
    """
    Safely convert a value to int with optional clamping.
    Returns `default` when conversion fails.
    """
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default
    if min_val is not None:
        result = max(min_val, result)
    if max_val is not None:
        result = min(max_val, result)
    return result


def validate_hex_color(color: str, fallback: str = "#000000") -> str:
    """
    Ensure a string is a valid 6-digit hex color code.
    Returns `fallback` when the input is invalid.
    """
    import re
    if color and re.fullmatch(r"#[0-9a-fA-F]{6}", color.strip()):
        return color.strip()
    return fallback
