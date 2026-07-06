from flask import Blueprint, jsonify, render_template, request, send_file
from PIL import Image, UnidentifiedImageError
import io

from utils.helpers import (
    safe_int,
    safe_float,
    validate_hex_color,
    clean_filename,
    parse_labels,
    generate_auto_labels,
    create_zip_in_memory,
    DEFAULT_LABELS,
    ALLOWED_EXTENSIONS,
)
from services.image_service import (
    resize_for_preset,
    draw_border,
    draw_badge,
)

bulk_image_bp = Blueprint("bulk_image", __name__)

@bulk_image_bp.route("/tools/bulk-image", methods=["GET"])
def tool_page():
    return render_template("bulk_image.html", active_page="bulk-image")

@bulk_image_bp.route("/tools/bulk-image", methods=["POST"])
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
        border_enabled = request.form.get("border_enabled", "on") == "on" or request.form.get("border_enabled") == "true"
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
        shadow_enabled = request.form.get("badge_shadow", "on") == "on" or request.form.get("badge_shadow") == "true"

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
