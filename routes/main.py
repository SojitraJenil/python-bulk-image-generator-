from flask import Blueprint, render_template, abort, send_file, request
import io
import os
import zipfile

main_bp = Blueprint("main", __name__)

TOOLS = {
    "pose-generator": {
        "title": "AI Pose Generator",
        "icon": "user",
        "description": "Generate professional and artistic poses from static images or textual prompts."
    },
    "background-remover": {
        "title": "Background Remover",
        "icon": "image-minus",
        "description": "Instantly isolate products or people from their backgrounds using high-precision AI."
    },
    "product-enhancer": {
        "title": "AI Product Enhancer",
        "icon": "sparkles",
        "description": "Transform simple product photos into studio-grade e-commerce assets automatically."
    },
    "image-upscaler": {
        "title": "Image Upscaler",
        "icon": "maximize",
        "description": "Increase image resolution up to 4x without losing quality or details."
    },
    "watermark-remover": {
        "title": "Watermark Remover",
        "icon": "eraser",
        "description": "Remove text, logos, or watermarks from your images cleanly and automatically."
    }
}

@main_bp.route("/")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")

@main_bp.route("/tools/<tool_name>")
def tool_placeholder(tool_name):
    if tool_name not in TOOLS:
        abort(404)
    tool_info = TOOLS[tool_name]
    return render_template(
        "placeholder.html",
        title=tool_info["title"],
        icon=tool_info["icon"],
        description=tool_info["description"],
        active_page=tool_name
    )

import json

@main_bp.route("/settings", methods=["GET", "POST"])
def settings_page():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "settings.json")
    
    try:
        with open(config_path, "r") as f:
            settings = json.load(f)
    except Exception:
        settings = {}

    if request.method == "POST":
        # Checkbox flags
        settings["enable_pose_library"] = request.form.get("enable_pose_library") == "on"
        settings["enable_bg_generator"] = request.form.get("enable_bg_generator") == "on"
        settings["enable_custom_prompt"] = request.form.get("enable_custom_prompt") == "on"
        settings["enable_batch_gen"] = request.form.get("enable_batch_gen") == "on"
        settings["enable_face_preservation"] = request.form.get("enable_face_preservation") == "on"
        settings["enable_upscaling"] = request.form.get("enable_upscaling") == "on"
        settings["enable_zip_download"] = request.form.get("enable_zip_download") == "on"
        settings["enable_preview"] = request.form.get("enable_preview") == "on"
        settings["enable_gpu"] = request.form.get("enable_gpu") == "on"
        settings["enable_experimental"] = request.form.get("enable_experimental") == "on"
        
        # Advanced configurations
        settings["default_quality"] = request.form.get("default_quality", "High")
        settings["default_pose"] = request.form.get("default_pose", "Standing")
        settings["default_format"] = request.form.get("default_format", "PNG")
        
        try:
            settings["max_images"] = int(request.form.get("max_images", 20))
        except ValueError:
            pass
            
        try:
            settings["max_upload_size"] = int(request.form.get("max_upload_size", 16))
        except ValueError:
            pass
            
        settings["ai_model"] = request.form.get("ai_model", "Stable Diffusion XL")
        settings["random_seed"] = request.form.get("random_seed", "").strip()
        settings["auto_cleanup"] = request.form.get("auto_cleanup") == "on"
        settings["gpu_mode"] = request.form.get("gpu_mode", "CPU")
        
        try:
            with open(config_path, "w") as f:
                json.dump(settings, f, indent=2)
            from flask import redirect, url_for
            return redirect(url_for("main.settings_page", success="true"))
        except Exception as e:
            return render_template("settings.html", settings=settings, error=str(e), active_page="settings")

    from flask import request as flask_req
    success_msg = "Application configurations saved successfully!" if flask_req.args.get("success") == "true" else None
    return render_template("settings.html", settings=settings, success_msg=success_msg, active_page="settings")

@main_bp.route("/about")
def about_page():
    return render_template(
        "placeholder.html",
        title="About",
        icon="info",
        description="Learn more about our SaaS suite, system architecture, version status, and active modules.",
        active_page="about"
    )

@main_bp.route("/tools/bulk-auto-listing")
def auto_listing():
    return render_template("auto_listing.html", active_page="bulk-auto-listing")

@main_bp.route("/download-extension")
def download_extension():
    from flask import request
    # Verify access password
    pw = request.args.get("pw")
    if pw != "Jenil@172":
        abort(403, description="Unauthorized: Invalid download credentials.")
        
    # Resolve absolute path to 'jenn auto listing'
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ext_dir = os.path.join(base_dir, "jenn auto listing")
    
    if not os.path.exists(ext_dir):
        ext_dir = "E:\\python image-bulk\\jenn auto listing"
        
    if not os.path.exists(ext_dir):
        abort(404, description="Extension folder not found")

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(ext_dir):
            # Exclude version control and cache folders
            if ".git" in root or "__pycache__" in root:
                continue
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, ext_dir)
                zipf.write(filepath, arcname)
                
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name="jenn_auto_listing.zip"
    )
