import os
import math
import textwrap
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

class LayoutBuilder:
    """
    Assembles panel elements (title, illustration, caption boxes, speech bubbles,
    sound effects, and panel frames) into a structured comic strip layout.
    """
    def __init__(self):
        self._load_fonts()

    def _load_fonts(self):
        """Loads available system fonts or defaults for comic typography."""
        font_names = ["comic.ttf", "comici.ttf", "arialbd.ttf", "arial.ttf", "calibri.ttf", "DejaVuSans-Bold.ttf"]
        
        self.font_title = None
        self.font_caption = None
        self.font_dialogue = None
        self.font_sfx = None
        self.font_badge = None

        for name in font_names:
            try:
                self.font_title = ImageFont.truetype(name, 28)
                self.font_caption = ImageFont.truetype(name, 16)
                self.font_dialogue = ImageFont.truetype(name, 18)
                self.font_sfx = ImageFont.truetype(name, 36)
                self.font_badge = ImageFont.truetype(name, 20)
                break
            except Exception:
                continue

        if not self.font_title:
            self.font_title = ImageFont.load_default()
            self.font_caption = ImageFont.load_default()
            self.font_dialogue = ImageFont.load_default()
            self.font_sfx = ImageFont.load_default()
            self.font_badge = ImageFont.load_default()

    def assemble_panel_composite(
        self,
        image_path: Path,
        panel_number: int,
        title: str = "",
        caption: str = "",
        dialogue: str = "",
        character_name: str = "",
        sound_effect: Optional[str] = None,
        output_composite_path: Optional[Path] = None
    ) -> Image.Image:
        """
        Binds a single panel's image with comic book styling:
        - Heavy black border with outer gutter
        - Yellow narrative caption box at top/bottom
        - White oval speech bubble with comic tail pointing towards character
        - Dynamic sound effect (SFX) badge if present
        - Panel number badge
        """
        base_img = Image.open(image_path).convert("RGBA")
        width, height = base_img.size

        # Create canvas with comic gutter border
        border_size = 12
        canvas_w = width + (border_size * 2)
        canvas_h = height + (border_size * 2)
        
        panel_canvas = Image.new("RGBA", (canvas_w, canvas_h), (18, 18, 24, 255))
        panel_canvas.paste(base_img, (border_size, border_size))
        draw = ImageDraw.Draw(panel_canvas)

        # 1. Panel Number Badge (Top Left)
        badge_w, badge_h = 44, 38
        draw.rectangle(
            [border_size, border_size, border_size + badge_w, border_size + badge_h],
            fill=(235, 47, 6, 255),
            outline=(0, 0, 0, 255),
            width=2
        )
        draw.text(
            (border_size + 14, border_size + 8),
            str(panel_number),
            fill=(255, 255, 255, 255),
            font=self.font_badge
        )

        # 2. Sound Effect (SFX) callout if specified
        if sound_effect:
            sfx_clean = sound_effect.strip().upper()
            if sfx_clean:
                sfx_x = width - 180
                sfx_y = border_size + 24
                # SFX burst badge
                self._draw_sfx_badge(draw, sfx_clean, sfx_x, sfx_y)

        # 3. Speech Bubble (if dialogue exists)
        if dialogue and dialogue.strip():
            self._draw_speech_bubble(
                draw,
                dialogue.strip(),
                character_name,
                x=border_size + 60,
                y=border_size + 50,
                max_w=width - 120
            )

        # 4. Narrative Caption Box (Classic comic caption at bottom)
        if caption and caption.strip():
            self._draw_caption_box(
                draw,
                caption.strip(),
                x=border_size + 16,
                y=canvas_h - border_size - 64,
                w=canvas_w - (border_size * 2) - 32
            )

        # 5. Crisp Comic Panel Outer Border
        draw.rectangle(
            [0, 0, canvas_w - 1, canvas_h - 1],
            outline=(20, 24, 33, 255),
            width=border_size
        )
        draw.rectangle(
            [border_size - 1, border_size - 1, canvas_w - border_size, canvas_h - border_size],
            outline=(0, 0, 0, 255),
            width=3
        )

        final_composite = panel_canvas.convert("RGB")
        if output_composite_path:
            output_composite_path.parent.mkdir(parents=True, exist_ok=True)
            final_composite.save(output_composite_path, "JPEG", quality=95)

        return final_composite

    def _draw_speech_bubble(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        character: str,
        x: int,
        y: int,
        max_w: int = 340
    ):
        """Renders an authentic comic speech bubble with outline and pointer tail."""
        wrapped = textwrap.fill(text, width=28)
        lines = wrapped.split("\n")
        
        line_height = 22
        bubble_h = max(50, len(lines) * line_height + 24)
        bubble_w = min(max_w, max([len(l) for l in lines]) * 10 + 36)
        
        # Bounding box for bubble
        bx1, by1 = x, y
        bx2, by2 = x + bubble_w, y + bubble_h

        # Draw pointer tail
        tail_tip = (bx1 + 30, by2 + 18)
        tail_base1 = (bx1 + 20, by2)
        tail_base2 = (bx1 + 45, by2)
        draw.polygon([tail_base1, tail_base2, tail_tip], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))

        # Draw bubble body (rounded rectangle)
        draw.rounded_rectangle(
            [bx1, by1, bx2, by2],
            radius=16,
            fill=(255, 255, 255, 255),
            outline=(0, 0, 0, 255),
            width=3
        )
        
        # Redraw inner tail base to clear duplicate line
        draw.line([tail_base1, tail_base2], fill=(255, 255, 255, 255), width=4)

        # Draw speech text
        text_y = by1 + 12
        for line in lines:
            draw.text((bx1 + 16, text_y), line, fill=(10, 10, 15, 255), font=self.font_dialogue)
            text_y += line_height

    def _draw_caption_box(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        w: int
    ):
        """Draws classic comic yellow narration caption box."""
        wrapped = textwrap.fill(text, width=65)
        lines = wrapped.split("\n")
        line_height = 20
        box_h = len(lines) * line_height + 16
        
        box_y1 = max(y, y - (box_h - 50))
        box_y2 = box_y1 + box_h
        
        # Yellow comic box
        draw.rectangle(
            [x, box_y1, x + w, box_y2],
            fill=(255, 242, 117, 245),
            outline=(0, 0, 0, 255),
            width=3
        )
        
        # Drop-shadow accent line
        draw.line([x + 3, box_y2 + 2, x + w + 2, box_y2 + 2], fill=(0, 0, 0, 160), width=2)
        draw.line([x + w + 2, box_y1 + 3, x + w + 2, box_y2 + 2], fill=(0, 0, 0, 160), width=2)

        cur_y = box_y1 + 8
        for line in lines:
            draw.text((x + 12, cur_y), line, fill=(20, 20, 20, 255), font=self.font_caption)
            cur_y += line_height

    def _draw_sfx_badge(self, draw: ImageDraw.ImageDraw, sfx: str, x: int, y: int):
        """Draws a starburst style comic SFX badge."""
        w, h = 140, 50
        # Shadow
        draw.rounded_rectangle([x + 4, y + 4, x + w + 4, y + h + 4], radius=8, fill=(0, 0, 0, 180))
        # SFX burst
        draw.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=(255, 71, 87, 255), outline=(255, 242, 0, 255), width=3)
        draw.text((x + 14, y + 8), sfx[:10], fill=(255, 255, 255, 255), font=self.font_sfx)

    def assemble_comic_strip(
        self,
        panels_data: List[Dict[str, Any]],
        title: str = "ComicCraft Issue",
        output_strip_path: Optional[Path] = None,
        columns: int = 2
    ) -> Path:
        """
        Assembles all panels into a multi-panel comic strip sheet.
        """
        panel_composites = []
        for p in panels_data:
            img_path = Path(p["image_path"])
            if img_path.exists():
                comp = self.assemble_panel_composite(
                    image_path=img_path,
                    panel_number=p.get("panel_number", 1),
                    title=p.get("title", ""),
                    caption=p.get("caption", ""),
                    dialogue=p.get("dialogue", ""),
                    character_name=p.get("character", ""),
                    sound_effect=p.get("sound_effect", None)
                )
                panel_composites.append(comp)

        if not panel_composites:
            raise ValueError("No valid panel images found to assemble strip.")

        num_panels = len(panel_composites)
        cols = min(columns, num_panels)
        rows = math.ceil(num_panels / cols)

        single_w, single_h = panel_composites[0].size
        gutter = 20
        header_h = 100
        
        sheet_w = (single_w * cols) + (gutter * (cols + 1))
        sheet_h = header_h + (single_h * rows) + (gutter * (rows + 1))

        sheet = Image.new("RGB", (sheet_w, sheet_h), (24, 28, 42))
        draw = ImageDraw.Draw(sheet)

        # Header Title Banner
        draw.rectangle([gutter, gutter, sheet_w - gutter, header_h - 10], fill=(255, 215, 0), outline=(0, 0, 0), width=4)
        draw.text((gutter + 24, gutter + 16), title.upper(), fill=(10, 10, 10), font=self.font_title)
        
        # Subtitle badge
        draw.text((sheet_w - 240, gutter + 22), "COMICCRAFT • AI ISSUE #1", fill=(100, 30, 20), font=self.font_caption)

        # Place panels
        for idx, comp in enumerate(panel_composites):
            r = idx // cols
            c = idx % cols
            px = gutter + c * (single_w + gutter)
            py = header_h + gutter + r * (single_h + gutter)
            sheet.paste(comp, (px, py))

        if output_strip_path:
            output_strip_path.parent.mkdir(parents=True, exist_ok=True)
            sheet.save(output_strip_path, "JPEG", quality=95)
            return output_strip_path
            
        return output_strip_path or Path("strip.jpg")

# Global layout builder singleton
layout_builder = LayoutBuilder()
