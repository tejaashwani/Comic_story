import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from fpdf import FPDF

from app.config import settings
from app.layout_builder import layout_builder

logger = logging.getLogger("comiccraft.exporter")

class ComicPDF(FPDF):
    """
    Custom FPDF subclass for comic book styling:
    - Comic title header
    - Halftone / comic border lines
    - Timestamped footer with issue pagination
    """
    def __init__(self, comic_title: str = "ComicCraft", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.comic_title = comic_title
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(180, 180, 190)
            self.cell(0, 8, f"COMICCRAFT PRESENTS: {self.comic_title.upper()}", align="L", ln=False)
            self.set_font("Helvetica", "I", 9)
            self.cell(0, 8, "OFFICIAL COLLECTOR'S EDITION", align="R", ln=True)
            # Header line
            self.set_draw_color(220, 220, 230)
            self.set_line_width(0.4)
            self.line(10, 16, 200, 16)
            self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(150, 150, 160)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 8, "Powered by ComicCraft (Gemini + Stable Diffusion)", align="R")


class ComicExporter:
    """
    Handles PDF compilation and layout formatting for comic books.
    """
    def __init__(self, exports_dir: Optional[Path] = None):
        self.exports_dir = exports_dir or settings.EXPORTS_DIR
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def export_to_pdf(
        self,
        comic_data: Dict[str, Any],
        panels: List[Dict[str, Any]],
        page_format: str = "A4",
        orientation: str = "P"
    ) -> Path:
        """
        Compiles the entire comic into a professional multi-page PDF document.
        Saves with a timestamped filename as specified in Scenario 3.
        """
        title = comic_data.get("title", "ComicCraft_Adventure")
        clean_title = re.sub(r'[^a-zA-Z0-9_-]', '_', title.lower()).strip('_')[:30]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comiccraft_{clean_title}_{timestamp}.pdf"
        output_pdf_path = self.exports_dir / filename

        logger.info(f"Compiling PDF comic for '{title}' -> {output_pdf_path}")

        pdf = ComicPDF(comic_title=title, orientation=orientation, unit="mm", format=page_format)
        pdf.set_margins(left=12, top=12, right=12)

        # ------------------------------------------------------------------
        # PAGE 1: FULL COVER PAGE
        # ------------------------------------------------------------------
        pdf.add_page()
        self._build_cover_page(pdf, comic_data, panels)

        # ------------------------------------------------------------------
        # CONSECUTIVE PAGES: PANELS & NARRATION
        # ------------------------------------------------------------------
        for p in panels:
            pdf.add_page()
            self._build_panel_page(pdf, p, comic_data)

        # ------------------------------------------------------------------
        # BACK COVER: CREATIVE SYNOPSIS & CREDITS
        # ------------------------------------------------------------------
        pdf.add_page()
        self._build_back_cover(pdf, comic_data, len(panels))

        # Output to file
        pdf.output(str(output_pdf_path))
        logger.info(f"PDF successfully generated: {output_pdf_path} ({os.path.getsize(output_pdf_path)} bytes)")

        return output_pdf_path

    def _build_cover_page(self, pdf: ComicPDF, comic_data: Dict[str, Any], panels: List[Dict[str, Any]]):
        """Builds a rich, dynamic comic book cover."""
        # Top banner badge
        pdf.set_fill_color(245, 197, 24)
        pdf.rect(12, 12, 186, 12, style="F")
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 15, 20)
        pdf.set_xy(16, 14)
        pdf.cell(0, 8, "COMICCRAFT PREMIER • ORIGINAL GRAPHIC NOVEL", align="L")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_xy(150, 14)
        pdf.cell(42, 8, "#1 SPECIAL EDITION", align="R")

        # Main Comic Title
        pdf.ln(16)
        pdf.set_font("Helvetica", "B", 26)
        pdf.set_text_color(235, 47, 6)
        title = comic_data.get("title", "Untitled Adventure").upper()
        pdf.multi_cell(0, 11, title, align="C")

        # Tagline
        tagline = comic_data.get("tagline", "")
        if tagline:
            pdf.set_font("Helvetica", "I", 12)
            pdf.set_text_color(60, 64, 75)
            pdf.cell(0, 8, f'"{tagline}"', align="C", ln=True)

        pdf.ln(3)

        # Cover Hero Image (Use composite or panel 1)
        first_panel = panels[0] if panels else None
        if first_panel and first_panel.get("image_path") and os.path.exists(first_panel["image_path"]):
            img_path = first_panel["image_path"]
            # Render composite panel with speech/captions
            comp_path = self.exports_dir / f"cover_{comic_data.get('id', 'temp')}.jpg"
            layout_builder.assemble_panel_composite(
                image_path=Path(img_path),
                panel_number=1,
                title="The Adventure Begins",
                caption=first_panel.get("caption", ""),
                dialogue=first_panel.get("dialogue", ""),
                character_name=comic_data.get("character_name", ""),
                sound_effect=first_panel.get("sound_effect", "PREMIERE!"),
                output_composite_path=comp_path
            )
            # Center image on cover
            img_w = 160
            img_h = 106
            img_x = (210 - img_w) / 2
            img_y = pdf.get_y() + 2
            pdf.image(str(comp_path), x=img_x, y=img_y, w=img_w, h=img_h)
            pdf.set_y(img_y + img_h + 8)

        # Comic Metadata Box
        pdf.set_fill_color(248, 249, 252)
        pdf.set_draw_color(210, 215, 225)
        pdf.set_line_width(0.5)
        meta_y = pdf.get_y()
        pdf.rounded_rect(16, meta_y, 178, 38, round_corners=True, r=3, style="FD")

        pdf.set_xy(20, meta_y + 4)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(40, 44, 52)
        pdf.cell(85, 6, f"PROTAGONIST: {comic_data.get('character_name', 'Hero')}", ln=False)
        pdf.cell(85, 6, f"ART STYLE: {comic_data.get('art_style', 'Comic Book').title()}", ln=True)

        pdf.set_x(20)
        pdf.cell(85, 6, f"SETTING: {comic_data.get('setting', 'World')}", ln=False)
        pdf.cell(85, 6, f"NARRATIVE TONE: {comic_data.get('tone', 'Dramatic').title()}", ln=True)

        pdf.set_x(20)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(100, 105, 115)
        pdf.multi_cell(170, 5, f"Original Prompt: {comic_data.get('prompt', '')}")

    def _build_panel_page(self, pdf: ComicPDF, panel: Dict[str, Any], comic_data: Dict[str, Any]):
        """Renders an individual panel with illustration, dialogues, and narrative caption."""
        panel_num = panel.get("panel_number", 1)
        panel_title = panel.get("title", f"Panel {panel_num}")
        
        # Panel Title Header
        pdf.set_fill_color(235, 47, 6)
        pdf.rect(12, 22, 10, 8, style="F")
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(12, 22)
        pdf.cell(10, 8, str(panel_num), align="C")

        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(20, 24, 33)
        pdf.set_xy(25, 22)
        pdf.cell(0, 8, panel_title.upper(), align="L", ln=True)
        pdf.ln(4)

        # Panel Composite Graphic
        img_path = panel.get("image_path")
        if img_path and os.path.exists(img_path):
            comp_path = self.exports_dir / f"panel_comp_{comic_data.get('id', 'temp')}_{panel_num}.jpg"
            layout_builder.assemble_panel_composite(
                image_path=Path(img_path),
                panel_number=panel_num,
                title=panel_title,
                caption=panel.get("caption", ""),
                dialogue=panel.get("dialogue", ""),
                character_name=comic_data.get("character_name", ""),
                sound_effect=panel.get("sound_effect", None),
                output_composite_path=comp_path
            )
            img_w = 175
            img_h = 115
            img_x = (210 - img_w) / 2
            img_y = pdf.get_y()
            pdf.image(str(comp_path), x=img_x, y=img_y, w=img_w, h=img_h)
            pdf.set_y(img_y + img_h + 8)

        # Narrative Story Transcript Box
        pdf.set_fill_color(255, 251, 230) # Classic parchment/yellow comic paper
        pdf.set_draw_color(230, 210, 150)
        pdf.set_line_width(0.6)
        box_y = pdf.get_y()
        pdf.rounded_rect(14, box_y, 182, 54, round_corners=True, r=3, style="FD")

        # Caption
        pdf.set_xy(18, box_y + 4)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(160, 100, 20)
        pdf.cell(0, 5, "NARRATION / SCENE CAPTION:", ln=True)
        
        pdf.set_x(18)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 30, 30)
        caption_text = panel.get("caption", "...")
        pdf.multi_cell(174, 5, caption_text)

        pdf.ln(2)
        # Dialogue
        dialogue = panel.get("dialogue", "")
        if dialogue:
            pdf.set_x(18)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(200, 40, 40)
            char = panel.get("character", comic_data.get("character_name", "Hero"))
            pdf.cell(0, 5, f"{char.upper()} SAYS:", ln=True)
            
            pdf.set_x(18)
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(20, 20, 25)
            pdf.multi_cell(174, 5, f'"{dialogue}"')

    def _build_back_cover(self, pdf: ComicPDF, comic_data: Dict[str, Any], total_panels: int):
        """Builds a collector's back cover with storyline synopsis and creation details."""
        pdf.ln(10)
        # Big seal
        pdf.set_fill_color(30, 36, 50)
        pdf.rect(12, 24, 186, 250, style="F")

        pdf.set_xy(20, 36)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(255, 215, 0)
        pdf.cell(0, 10, "COMICCRAFT CHRONICLES", align="C", ln=True)

        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(220, 225, 235)
        pdf.cell(0, 7, "AI GRAPHIC NOVEL STUDIO EDITION", align="C", ln=True)

        pdf.ln(10)
        # Synopsis
        pdf.set_x(26)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(245, 197, 24)
        pdf.cell(0, 8, "STORY SYNOPSIS", ln=True)

        synopsis = comic_data.get("synopsis", "An epic tale crafted through artificial imagination.")
        pdf.set_x(26)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(230, 230, 240)
        pdf.multi_cell(158, 6, synopsis)

        pdf.ln(8)
        # Spec Table
        pdf.set_x(26)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(245, 197, 24)
        pdf.cell(0, 8, "PRODUCTION SPECIFICATIONS", ln=True)

        specs = [
            ("Story Engine", f"Google Gemini 1.5 ({comic_data.get('tone', '').title()} Tone)"),
            ("Illustration Model", f"Stable Diffusion ({comic_data.get('art_style', '').title()} Style)"),
            ("Panel Count", f"{total_panels} Hand-crafted Panels"),
            ("Layout & Typesetting", "layout_builder.py (Dynamic Speech & Caption Engine)"),
            ("PDF Pipeline", "exporters.py (FPDF2 High-Fidelity Rendering)"),
            ("Generated Date", datetime.now().strftime("%B %d, %Y - %I:%M %p"))
        ]

        pdf.set_font("Helvetica", "", 10)
        for label, val in specs:
            pdf.set_x(26)
            pdf.set_text_color(180, 190, 205)
            pdf.cell(60, 7, label + ":", ln=False)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(98, 7, val, ln=True)

        # Thank you note
        pdf.set_y(235)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(160, 165, 180)
        pdf.multi_cell(0, 5, "Created with ComicCraft • Where your words become legendary comic books.\nPrint, share, and enjoy!", align="C")

# Global exporter singleton
comic_exporter = ComicExporter()
