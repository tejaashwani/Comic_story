import os
import json
import uuid
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.config import settings
from app.models.schemas import ComicCreateRequest, ComicData, PanelData
from app.services.gemini_story import GeminiStoryService
from app.services.sd_illustrator import StableDiffusionIllustrator
from app.layout_builder import layout_builder
from app.exporters import comic_exporter

logger = logging.getLogger("comiccraft.engine")

class ComicEngine:
    """
    Coordinates the end-to-end comic generation pipeline:
    Story synthesis (Gemini) -> Illustration rendering (Stable Diffusion)
    -> Layout binding (layout_builder.py) -> PDF export (exporters.py).
    """
    def __init__(self):
        self.story_service = GeminiStoryService()
        self.illustrator = StableDiffusionIllustrator()

    def generate_comic(self, req: ComicCreateRequest) -> ComicData:
        """
        Executes Scenario 1 & Scenario 2 pipelines.
        """
        start_time = time.time()
        comic_id = f"comic_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        comic_dir = settings.COMICS_DIR / comic_id
        comic_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting ComicCraft generation pipeline for: '{req.prompt}' (ID: {comic_id})")

        # Step 1: Story & Panel breakdown via Gemini
        story_data = self.story_service.generate_comic_story(
            prompt=req.prompt,
            character_name=req.character_name,
            setting=req.setting,
            tone=req.tone,
            art_style=req.art_style,
            num_panels=req.num_panels
        )

        title = story_data.get("title", f"The Chronicles of {req.character_name}")
        tagline = story_data.get("tagline", "")
        synopsis = story_data.get("synopsis", "")
        raw_panels = story_data.get("panels", [])

        # Step 2: Generate visual illustrations for each panel via Stable Diffusion
        panels: List[PanelData] = []
        for p in raw_panels:
            p_num = p.get("panel_number", len(panels) + 1)
            vis_desc = p.get("visual_description", f"{req.character_name} in {req.setting}")
            
            img_filename = f"panel_{p_num}.png"
            img_path = comic_dir / img_filename
            
            self.illustrator.generate_panel_image(
                visual_description=vis_desc,
                art_style=req.art_style,
                character_name=req.character_name,
                setting=req.setting,
                output_path=img_path,
                panel_number=p_num
            )

            # Assemble composite with layout_builder
            comp_filename = f"composite_{p_num}.jpg"
            comp_path = comic_dir / comp_filename
            layout_builder.assemble_panel_composite(
                image_path=img_path,
                panel_number=p_num,
                title=p.get("title", f"Panel {p_num}"),
                caption=p.get("caption", ""),
                dialogue=p.get("dialogue", ""),
                character_name=req.character_name,
                sound_effect=p.get("sound_effect", None),
                output_composite_path=comp_path
            )

            panel_data = PanelData(
                panel_number=p_num,
                title=p.get("title", f"Panel {p_num}"),
                caption=p.get("caption", ""),
                dialogue=p.get("dialogue", ""),
                character=p.get("character", req.character_name),
                sound_effect=p.get("sound_effect", None),
                visual_description=vis_desc,
                image_url=f"/storage/comics/{comic_id}/{comp_filename}",
                image_path=str(img_path)
            )
            panels.append(panel_data)

        # Step 3: Assemble unified multi-panel comic strip sheet
        strip_path = comic_dir / "full_strip.jpg"
        try:
            layout_builder.assemble_comic_strip(
                panels_data=[p.dict() for p in panels],
                title=title,
                output_strip_path=strip_path,
                columns=2 if len(panels) > 2 else 1
            )
        except Exception as e:
            logger.warning(f"Could not build full strip composite: {e}")

        # Assemble ComicData object
        comic = ComicData(
            id=comic_id,
            title=title,
            tagline=tagline,
            synopsis=synopsis,
            prompt=req.prompt,
            character_name=req.character_name,
            setting=req.setting,
            tone=req.tone,
            art_style=req.art_style,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            num_panels=len(panels),
            panels=panels,
            status="completed"
        )

        # Save comic metadata to JSON
        meta_file = comic_dir / "comic.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(comic.dict(), f, indent=2)

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"Comic generation completed in {elapsed}s for ID: {comic_id}")
        return comic

    def get_comic(self, comic_id: str) -> Optional[ComicData]:
        """Loads comic metadata from disk."""
        meta_file = settings.COMICS_DIR / comic_id / "comic.json"
        if not meta_file.exists():
            return None
        with open(meta_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return ComicData(**data)

    def list_comics(self) -> List[Dict[str, Any]]:
        """Lists all existing comics sorted by creation time."""
        comics_list = []
        if not settings.COMICS_DIR.exists():
            return []
        
        for p in settings.COMICS_DIR.iterdir():
            if p.is_dir():
                meta_file = p / "comic.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            comics_list.append({
                                "id": data.get("id"),
                                "title": data.get("title"),
                                "character_name": data.get("character_name"),
                                "setting": data.get("setting"),
                                "tone": data.get("tone"),
                                "art_style": data.get("art_style"),
                                "created_at": data.get("created_at"),
                                "panel_count": len(data.get("panels", [])),
                                "cover_url": f"/storage/comics/{data.get('id')}/composite_1.jpg",
                                "pdf_url": data.get("pdf_url")
                            })
                    except Exception:
                        continue
        
        # Sort descending by creation
        comics_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return comics_list

    def regenerate_panel(
        self,
        comic_id: str,
        panel_number: int,
        custom_prompt: Optional[str] = None,
        updated_dialogue: Optional[str] = None,
        updated_caption: Optional[str] = None
    ) -> Optional[ComicData]:
        """Regenerates a single panel within an existing comic."""
        comic = self.get_comic(comic_id)
        if not comic:
            return None

        comic_dir = settings.COMICS_DIR / comic_id
        target_panel = None
        for p in comic.panels:
            if p.panel_number == panel_number:
                target_panel = p
                break

        if not target_panel:
            return None

        # Update text if provided
        if updated_dialogue is not None:
            target_panel.dialogue = updated_dialogue
        if updated_caption is not None:
            target_panel.caption = updated_caption
        
        vis_desc = custom_prompt or target_panel.visual_description
        target_panel.visual_description = vis_desc

        img_path = comic_dir / f"panel_{panel_number}.png"
        comp_filename = f"composite_{panel_number}.jpg"
        comp_path = comic_dir / comp_filename

        # Re-render image
        self.illustrator.generate_panel_image(
            visual_description=vis_desc,
            art_style=comic.art_style,
            character_name=comic.character_name,
            setting=comic.setting,
            output_path=img_path,
            panel_number=panel_number
        )

        # Re-bind composite
        layout_builder.assemble_panel_composite(
            image_path=img_path,
            panel_number=panel_number,
            title=target_panel.title,
            caption=target_panel.caption,
            dialogue=target_panel.dialogue,
            character_name=comic.character_name,
            sound_effect=target_panel.sound_effect,
            output_composite_path=comp_path
        )

        target_panel.image_url = f"/storage/comics/{comic_id}/{comp_filename}?t={int(time.time())}"

        # Save metadata
        meta_file = comic_dir / "comic.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(comic.dict(), f, indent=2)

        return comic

    def export_pdf(self, comic_id: str, page_format: str = "A4", orientation: str = "P") -> Dict[str, Any]:
        """Executes Scenario 3: compiles PDF via exporters.py with timestamped filename."""
        comic = self.get_comic(comic_id)
        if not comic:
            raise ValueError(f"Comic {comic_id} not found.")

        panels_dict = [p.dict() for p in comic.panels]
        pdf_path = comic_exporter.export_to_pdf(
            comic_data=comic.dict(),
            panels=panels_dict,
            page_format=page_format,
            orientation=orientation
        )

        pdf_filename = pdf_path.name
        pdf_url = f"/storage/exports/{pdf_filename}"
        comic.pdf_filename = pdf_filename
        comic.pdf_url = pdf_url

        # Save updated metadata
        meta_file = settings.COMICS_DIR / comic_id / "comic.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(comic.dict(), f, indent=2)

        file_size_mb = round(os.path.getsize(pdf_path) / (1024 * 1024), 2)
        return {
            "comic_id": comic_id,
            "filename": pdf_filename,
            "pdf_url": pdf_url,
            "file_size_mb": file_size_mb,
            "total_pages": len(comic.panels) + 2
        }

# Global singleton
comic_engine = ComicEngine()
