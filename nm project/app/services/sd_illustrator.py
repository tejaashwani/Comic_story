import os
import io
import time
import urllib.parse
import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests

from app.config import settings

logger = logging.getLogger("comiccraft.sd")

class StableDiffusionIllustrator:
    """
    Handles prompt engineering and image synthesis across Diffusers,
    Hugging Face Inference API, Cloud SD, and built-in artistic canvas.
    """
    def __init__(self, provider: str = None):
        self.provider = (provider or settings.SD_PROVIDER).lower()
        self.diffusers_pipe = None
        self._init_diffusers()

    def _init_diffusers(self):
        """Lazy loads local diffusers pipeline if selected and dependencies are present."""
        if self.provider == "diffusers":
            try:
                import torch
                from diffusers import StableDiffusionPipeline
                
                device = "cuda" if torch.cuda.is_available() else "cpu"
                dtype = torch.float16 if device == "cuda" else torch.float32
                logger.info(f"Loading local Diffusers model: {settings.SD_MODEL_ID} on {device}...")
                
                self.diffusers_pipe = StableDiffusionPipeline.from_pretrained(
                    settings.SD_MODEL_ID,
                    torch_dtype=dtype,
                    safety_checker=None
                ).to(device)
                
                if device == "cuda":
                    try:
                        self.diffusers_pipe.enable_xformers_memory_efficient_attention()
                    except Exception:
                        pass
                logger.info("Local Diffusers pipeline initialized successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize local Diffusers pipeline ({e}). Switching to Cloud SD provider.")
                self.provider = "cloud"

    def build_prompt(
        self,
        visual_description: str,
        art_style: str,
        character_name: str,
        setting: str
    ) -> Tuple[str, str]:
        """
        Synthesizes a refined Stable Diffusion prompt and negative prompt.
        """
        style_key = art_style.lower()
        style_config = settings.ART_STYLES.get(style_key, settings.ART_STYLES["comic book"])
        
        style_enhancement = style_config.get("prompt_enhancement", "")
        negative_prompt = style_config.get("negative_prompt", "")
        
        # Assemble cohesive prompt with character anchor and setting
        prompt_parts = [
            f"Comic panel illustration of {character_name}",
            f"{visual_description}",
            f"setting: {setting}",
            style_enhancement,
            "masterpiece, trending on artstation, highly detailed, dramatic comic framing"
        ]
        
        full_prompt = ", ".join([p for p in prompt_parts if p.strip()])
        return full_prompt, negative_prompt

    def generate_panel_image(
        self,
        visual_description: str,
        art_style: str,
        character_name: str,
        setting: str,
        output_path: Path,
        panel_number: int = 1,
        width: int = None,
        height: int = None
    ) -> Path:
        """
        Generates an illustration for a single comic panel and saves to output_path.
        """
        width = width or settings.IMAGE_WIDTH
        height = height or settings.IMAGE_HEIGHT
        output_path.parent.mkdir(parents=True, exist_ok=True)

        full_prompt, neg_prompt = self.build_prompt(
            visual_description, art_style, character_name, setting
        )

        logger.info(f"Generating panel {panel_number} via [{self.provider}] provider...")

        # 1. Local Diffusers Pipeline
        if self.provider == "diffusers" and self.diffusers_pipe:
            try:
                image = self.diffusers_pipe(
                    prompt=full_prompt,
                    negative_prompt=neg_prompt,
                    width=width,
                    height=height,
                    num_inference_steps=28,
                    guidance_scale=7.5
                ).images[0]
                image.save(output_path, "PNG")
                return output_path
            except Exception as e:
                logger.error(f"Diffusers generation failed ({e}). Falling back to Cloud provider.")

        # 2. Hugging Face Inference API
        if self.provider == "huggingface" and settings.HF_TOKEN:
            try:
                headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}
                api_url = f"https://api-inference.huggingface.co/models/{settings.SD_MODEL_ID}"
                payload = {
                    "inputs": full_prompt,
                    "parameters": {"negative_prompt": neg_prompt, "width": width, "height": height}
                }
                res = requests.post(api_url, headers=headers, json=payload, timeout=45)
                if res.status_code == 200:
                    image = Image.open(io.BytesIO(res.content))
                    image.save(output_path, "PNG")
                    return output_path
                else:
                    logger.warning(f"Hugging Face API returned status {res.status_code}: {res.text[:200]}")
            except Exception as e:
                logger.warning(f"Hugging Face API failed: {e}")

        # 3. Fast High-Resolution Cloud Diffusion (Pollinations / Direct Cloud SD)
        if self.provider in ["cloud", "diffusers", "huggingface"]:
            try:
                encoded_prompt = urllib.parse.quote(full_prompt)
                cloud_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={int(time.time() * 1000) % 999999}&nologo=true"
                
                response = requests.get(cloud_url, timeout=30)
                if response.status_code == 200 and len(response.content) > 5000:
                    image = Image.open(io.BytesIO(response.content))
                    image.save(output_path, "PNG")
                    logger.info(f"Cloud SD generated panel {panel_number} saved to {output_path}")
                    return output_path
                else:
                    logger.warning(f"Cloud provider returned status {response.status_code}")
            except Exception as e:
                logger.warning(f"Cloud SD generation exception: {e}")

        # 4. Built-in Stylized Comic Canvas Generator (Guaranteed offline fallback)
        logger.info(f"Generating artistic comic panel graphic for panel {panel_number} using PIL engine.")
        return self._generate_stylized_canvas(
            visual_description, art_style, character_name, setting, panel_number, output_path, width, height
        )

    def _generate_stylized_canvas(
        self,
        visual_desc: str,
        art_style: str,
        character_name: str,
        setting: str,
        panel_number: int,
        output_path: Path,
        width: int,
        height: int
    ) -> Path:
        """
        Creates a vivid comic-style graphic with dynamic gradients, halftone dots,
        character silhouette, action speedlines, and comic panel borders.
        """
        # Create base canvas
        img = Image.new("RGBA", (width, height), (20, 24, 38, 255))
        draw = ImageDraw.Draw(img)

        # Style-based palette
        palettes = {
            "comic book": [(245, 197, 24), (231, 76, 60), (41, 128, 185), (39, 174, 96)],
            "anime": [(255, 110, 180), (120, 115, 245), (64, 224, 208), (255, 215, 0)],
            "cyberpunk": [(255, 0, 128), (0, 240, 255), (138, 43, 226), (15, 240, 140)],
            "watercolor": [(176, 224, 230), (255, 182, 193), (221, 160, 221), (152, 251, 152)],
            "dark fantasy": [(44, 62, 80), (149, 165, 166), (192, 57, 43), (22, 160, 133)]
        }
        palette = palettes.get(art_style.lower(), palettes["comic book"])
        primary_color = palette[(panel_number - 1) % len(palette)]
        secondary_color = palette[panel_number % len(palette)]

        # Dynamic gradient background
        for y in range(height):
            ratio = y / height
            r = int(primary_color[0] * (1 - ratio * 0.7))
            g = int(primary_color[1] * (1 - ratio * 0.7))
            b = int(primary_color[2] * (1 - ratio * 0.7))
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

        # Comic Speedlines / Sunburst from center
        cx, cy = width // 2, height // 2
        for angle_deg in range(0, 360, 12):
            import math
            rad = math.radians(angle_deg)
            ex = cx + int(width * math.cos(rad))
            ey = cy + int(height * math.sin(rad))
            draw.line([(cx, cy), (ex, ey)], fill=(255, 255, 255, 30), width=3)

        # Halftone dot effect in corner
        for dot_x in range(0, width // 3, 20):
            for dot_y in range(0, height // 3, 20):
                radius = 2 + (dot_x + dot_y) // 40
                draw.ellipse([dot_x, dot_y, dot_x + radius, dot_y + radius], fill=(255, 255, 255, 45))

        # Stylized Character Silhouette & Scene Composition
        char_box_w, char_box_h = 160, 220
        char_x = (width - char_box_w) // 2
        char_y = height - char_box_h - 40
        
        # Shadow/glow
        draw.ellipse([char_x - 30, height - 60, char_x + char_box_w + 30, height - 20], fill=(0, 0, 0, 120))
        # Silhouette body
        draw.rounded_rectangle([char_x, char_y, char_x + char_box_w, char_y + char_box_h], radius=24, fill=(15, 17, 26, 240), outline=(255, 255, 255, 200), width=3)
        # Head / Helmet
        draw.ellipse([char_x + 35, char_y - 45, char_x + char_box_w - 35, char_y + 35], fill=(15, 17, 26, 240), outline=(255, 255, 255, 200), width=3)
        # Glowing eyes
        draw.ellipse([char_x + 55, char_y - 15, char_x + 65, char_y - 8], fill=secondary_color)
        draw.ellipse([char_x + 95, char_y - 15, char_x + 105, char_y - 8], fill=secondary_color)

        # Draw Bold Comic Frame Border
        border_width = 8
        draw.rectangle([0, 0, width, height], outline=(15, 17, 26, 255), width=border_width)
        draw.rectangle([border_width, border_width, width - border_width, height - border_width], outline=(255, 255, 255, 180), width=2)

        # Panel Number Badge in Top-Left
        badge_size = 54
        draw.rectangle([border_width, border_width, border_width + badge_size, border_width + badge_size], fill=(231, 76, 60, 255))
        draw.rectangle([border_width, border_width, border_width + badge_size, border_width + badge_size], outline=(15, 17, 26, 255), width=3)
        
        try:
            font = ImageFont.truetype("arial.ttf", 26)
            font_sm = ImageFont.truetype("arial.ttf", 16)
        except Exception:
            font = ImageFont.load_default()
            font_sm = ImageFont.load_default()

        draw.text((border_width + 18, border_width + 12), str(panel_number), fill=(255, 255, 255, 255), font=font)

        # Style & Scene Watermark banner
        scene_tag = f"{art_style.upper()} • {character_name.upper()} IN {setting.upper()}"
        draw.rounded_rectangle([width - 340, height - 38, width - 15, height - 12], radius=6, fill=(0, 0, 0, 180))
        draw.text((width - 330, height - 34), scene_tag[:36], fill=(255, 215, 0, 255), font=font_sm)

        # Save image
        rgb_img = img.convert("RGB")
        rgb_img.save(output_path, "PNG")
        return output_path
