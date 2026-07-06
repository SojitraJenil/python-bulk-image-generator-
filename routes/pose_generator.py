from __future__ import annotations

import io
import json
import os
import zipfile

from flask import Blueprint, jsonify, render_template, request, send_file

from services.pose_service import PoseGeneratorService
from utils.helpers import safe_int, validate_hex_color, ALLOWED_EXTENSIONS

pose_generator_bp = Blueprint("pose_generator", __name__)

POSE_CATEGORIES = [
    {"id": "standing",      "label": "Standing",          "icon": "person-standing"},
    {"id": "sitting",       "label": "Sitting",           "icon": "armchair"},
    {"id": "walking",       "label": "Walking",           "icon": "footprints"},
    {"id": "front_view",    "label": "Front View",        "icon": "scan"},
    {"id": "back_view",     "label": "Back View",         "icon": "flip-vertical"},
    {"id": "left_side",     "label": "Left Side",         "icon": "arrow-left"},
    {"id": "right_side",    "label": "Right Side",        "icon": "arrow-right"},
    {"id": "cross_leg",     "label": "Cross-Leg Sitting", "icon": "shuffle"},
    {"id": "chair_pose",    "label": "Chair Pose",        "icon": "armchair"},
    {"id": "floor_sitting", "label": "Floor Sitting",     "icon": "layers"},
    {"id": "leaning",       "label": "Leaning",           "icon": "activity"},
    {"id": "arms_folded",   "label": "Arms Folded",       "icon": "shield"},
    {"id": "hand_on_hip",   "label": "Hand on Hip",       "icon": "move"},
    {"id": "holding",       "label": "Holding Product",   "icon": "package"},
    {"id": "looking_left",  "label": "Looking Left",      "icon": "arrow-up-left"},
    {"id": "looking_right", "label": "Looking Right",     "icon": "arrow-up-right"},
    {"id": "looking_down",  "label": "Looking Down",      "icon": "arrow-down"},
    {"id": "looking_up",    "label": "Looking Up",        "icon": "arrow-up"},
    {"id": "smiling",       "label": "Smiling",           "icon": "smile"},
    {"id": "casual",        "label": "Casual Fashion",    "icon": "star"},
]

BACKGROUNDS = [
    {"id": "Keep Original",         "color": "#e2e8f0"},
    {"id": "White Background",      "color": "#ffffff"},
    {"id": "Transparent",           "color": "#94a3b8"},
    {"id": "Bedroom",               "color": "#f5e6cc"},
    {"id": "Living Room",           "color": "#c8d5c0"},
    {"id": "Studio",                "color": "#d1d5db"},
    {"id": "Outdoor",               "color": "#6fb3e0"},
    {"id": "AI Generated Background", "color": "linear-gradient(135deg,#6366f1,#ec4899)"},
]


def _load_settings():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg  = os.path.join(base, "config", "settings.json")
    try:
        with open(cfg) as f:
            return json.load(f)
    except Exception:
        return {}


@pose_generator_bp.route("/tools/pose-generator", methods=["GET"])
def tool_page():
    settings = _load_settings()
    return render_template(
        "pose_generator.html",
        active_page="pose-generator",
        settings=settings,
        poses=POSE_CATEGORIES,
        backgrounds=BACKGROUNDS,
    )


@pose_generator_bp.route("/tools/pose-generator", methods=["POST"])
def generate_poses():
    settings = _load_settings()
    try:
        image_file = request.files.get("image")
        if not image_file or not image_file.filename:
            return jsonify({"error": "Please upload a product image first."}), 400

        fname = image_file.filename or ""
        if not any(fname.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            return jsonify({"error": "Unsupported format. Use JPG, PNG, or WEBP."}), 400

        selected_poses  = request.form.getlist("poses")
        custom_prompt   = request.form.get("custom_prompt", "").strip()
        background      = request.form.get("background", "Keep Original")
        quality         = request.form.get("quality", settings.get("default_quality", "High"))
        aspect_ratio    = request.form.get("aspect_ratio", "Original")
        batch_count     = safe_int(request.form.get("batch_count"), 1, 1,
                                   settings.get("max_images", 20))
        seed            = request.form.get("seed", "").strip()

        generated = PoseGeneratorService.generate_poses(
            image_stream       = image_file.stream,
            selected_poses     = selected_poses,
            custom_prompt      = custom_prompt,
            background_option  = background,
            quality_preset     = quality,
            aspect_ratio       = aspect_ratio,
            batch_count        = batch_count,
            seed               = seed,
            enable_face_preservation = settings.get("enable_face_preservation", True),
            enable_upscaling         = settings.get("enable_upscaling", False),
            gpu_mode                 = settings.get("gpu_mode", "CPU"),
            model_name               = settings.get("ai_model", "Stable Diffusion XL"),
        )

        if len(generated) == 1:
            fname_out, data = generated[0]
            return send_file(
                io.BytesIO(data),
                mimetype="image/png",
                as_attachment=True,
                download_name=fname_out,
            )

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname_out, data in generated:
                zf.writestr(fname_out, data)
        buf.seek(0)
        return send_file(
            buf,
            mimetype="application/zip",
            as_attachment=True,
            download_name="pose_images.zip",
        )

    except Exception as exc:
        return jsonify({"error": f"Generation failed: {exc}"}), 500
