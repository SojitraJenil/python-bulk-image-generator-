from __future__ import annotations

import io

from flask import Blueprint, jsonify, render_template, request, send_file

from services.upscaler_service import ImageUpscalerService
from utils.helpers import safe_int, ALLOWED_EXTENSIONS

upscaler_bp = Blueprint("image_upscaler", __name__)


@upscaler_bp.route("/tools/image-upscaler", methods=["GET"])
def tool_page():
    return render_template("image_upscaler.html", active_page="image-upscaler")


@upscaler_bp.route("/tools/image-upscaler", methods=["POST"])
def upscale_image():
    image_file = request.files.get("image")
    if not image_file or not image_file.filename:
        return jsonify({"error": "Please upload an image first."}), 400

    fname = image_file.filename or ""
    if not any(fname.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return jsonify({"error": "Unsupported format. Use JPG, PNG, or WEBP."}), 400

    scale           = request.form.get("scale", "2x")
    quality         = request.form.get("quality", "High")
    output_format   = request.form.get("output_format", "PNG")
    enhance_sharp   = request.form.get("enhance_sharpness") == "true"
    enhance_contrast= request.form.get("enhance_contrast") == "true"
    enhance_color   = request.form.get("enhance_color") == "true"
    denoise         = request.form.get("denoise") == "true"

    try:
        data, orig_size, new_size, mime = ImageUpscalerService.upscale(
            image_stream      = image_file.stream,
            scale             = scale,
            quality           = quality,
            output_format     = output_format,
            enhance_sharpness = enhance_sharp,
            enhance_contrast  = enhance_contrast,
            enhance_color     = enhance_color,
            denoise           = denoise,
        )
        ext = output_format.lower().replace("jpg", "jpeg")
        download_name = f"upscaled_{scale}_{fname.rsplit('.',1)[0]}.{output_format.lower()}"
        return send_file(
            io.BytesIO(data),
            mimetype=mime,
            as_attachment=True,
            download_name=download_name,
        )
    except Exception as exc:
        return jsonify({"error": f"Upscaling failed: {exc}"}), 500
