from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
import os, zipfile, uuid

app = Flask(__name__)

OUTPUT_DIR = "static/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DEFAULT_LABELS = [
    ("SALE", "#e53935"),
    ("20% OFF", "#fb8c00"),
    ("BEST SELLER", "#43a047"),
    ("NEW ARRIVAL", "#1e88e5"),
    ("LIMITED OFFER", "#d81b60"),
    ("HOT DEAL", "#8e24aa"),
    ("PREMIUM", "#00897b"),
    ("30% OFF", "#f4511e"),
    ("TRENDING", "#3949ab"),
    ("BEST PRICE", "#6d4c41"),
]

def get_font(size=36):
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except:
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        except:
            return ImageFont.load_default()

def get_position(position, w, h, box_w, box_h, margin):
    if position == "top-right":
        return w - box_w - margin, margin
    if position == "bottom-left":
        return margin, h - box_h - margin
    if position == "bottom-right":
        return w - box_w - margin, h - box_h - margin
    return margin, margin

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("image")
        custom_labels = request.form.get("labels", "").strip()

        position = request.form.get("position", "top-left")
        border_width = int(request.form.get("border_width", 10))
        font_size = int(request.form.get("font_size", 36))
        radius = int(request.form.get("radius", 14))
        padding_x = int(request.form.get("padding_x", 18))
        padding_y = int(request.form.get("padding_y", 12))

        if not file:
            return "Please upload image"

        labels = []

        if custom_labels:
            for item in custom_labels.splitlines():
                parts = item.split("|")
                text = parts[0].strip()
                color = parts[1].strip() if len(parts) > 1 else "#e53935"
                if text:
                    labels.append((text, color))
        else:
            labels = DEFAULT_LABELS

        folder_id = str(uuid.uuid4())[:8]
        outdir = os.path.join(OUTPUT_DIR, folder_id)
        os.makedirs(outdir, exist_ok=True)

        img = Image.open(file).convert("RGB")
        font = get_font(font_size)

        for i, (text, color) in enumerate(labels, 1):
            im = img.copy()
            d = ImageDraw.Draw(im)
            w, h = im.size

            d.rectangle((0, 0, w - 1, h - 1), outline=color, width=border_width)

            bbox = d.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            box_w = text_w + padding_x * 2
            box_h = text_h + padding_y * 2

            x, y = get_position(position, w, h, box_w, box_h, 24)

            d.rounded_rectangle(
                (x, y, x + box_w, y + box_h),
                radius=radius,
                fill=color
            )

            d.text(
                (x + padding_x, y + padding_y),
                text,
                fill="white",
                font=font
            )

            im.save(os.path.join(outdir, f"promo_{i:02d}_{text.replace(' ', '_')}.png"))

        zip_path = os.path.join(outdir, "promo_images.zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(os.listdir(outdir)):
                if f.endswith(".png"):
                    z.write(os.path.join(outdir, f), arcname=f)

        return send_file(zip_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)