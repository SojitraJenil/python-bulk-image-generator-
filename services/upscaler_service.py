from __future__ import annotations

import io
from typing import Tuple
from PIL import Image, ImageFilter, ImageEnhance


# Scale factors by preset name
SCALE_MAP = {
    "2x":  2,
    "3x":  3,
    "4x":  4,
}

# Sharpening strength map per quality preset
SHARPEN_MAP = {
    "Standard": 1.1,
    "High":     1.3,
    "Ultra HD": 1.55,
}

# Noise-reduction blur radius per quality preset (applied before upscale)
DENOISE_RADIUS = {
    "Standard": 0,
    "High":     0.4,
    "Ultra HD": 0.6,
}


class ImageUpscalerService:
    @staticmethod
    def upscale(
        image_stream,
        scale: str = "2x",
        quality: str = "High",
        output_format: str = "PNG",
        enhance_sharpness: bool = True,
        enhance_contrast: bool = False,
        enhance_color: bool = False,
        denoise: bool = False,
    ) -> Tuple[bytes, Tuple[int, int], Tuple[int, int], str]:
        """
        Upscale an image using Pillow's Lanczos resampler.
        Returns (image_bytes, original_size, new_size, mime_type).

        For future replacement:
        - Drop-in Waifu2x, ESRGAN, Real-ESRGAN or Replicate upscaler API here.
        - This function signature stays the same — only the internal render changes.
        """
        image_stream.seek(0)
        img = Image.open(image_stream).convert("RGB")
        orig_w, orig_h = img.size

        factor = SCALE_MAP.get(scale, 2)

        # ── Optional Denoise before upscale ──────────────────
        radius = DENOISE_RADIUS.get(quality, 0)
        if denoise and radius > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=radius))

        # ── Upscale with Lanczos ──────────────────────────────
        new_w, new_h = orig_w * factor, orig_h * factor
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # ── Optional Sharpen ──────────────────────────────────
        if enhance_sharpness:
            strength = SHARPEN_MAP.get(quality, 1.2)
            img = ImageEnhance.Sharpness(img).enhance(strength)
            # Extra unsharp-mask pass for Ultra HD
            if quality == "Ultra HD":
                img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))

        # ── Optional Contrast boost ───────────────────────────
        if enhance_contrast:
            img = ImageEnhance.Contrast(img).enhance(1.1)

        # ── Optional Color boost ──────────────────────────────
        if enhance_color:
            img = ImageEnhance.Color(img).enhance(1.12)

        # ── Encode output ─────────────────────────────────────
        fmt_map  = {"PNG": ("PNG", "image/png"), "JPG": ("JPEG", "image/jpeg"), "WEBP": ("WEBP", "image/webp")}
        pil_fmt, mime = fmt_map.get(output_format, ("PNG", "image/png"))

        buf = io.BytesIO()
        save_kwargs = {"format": pil_fmt}
        if pil_fmt == "JPEG":
            save_kwargs["quality"] = 95
            save_kwargs["subsampling"] = 0
        elif pil_fmt == "WEBP":
            save_kwargs["quality"] = 92
        img.save(buf, **save_kwargs)
        buf.seek(0)

        return buf.getvalue(), (orig_w, orig_h), (new_w, new_h), mime
