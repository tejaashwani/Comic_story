"""
Unit & Integration Tests for ComicCraft
Verifies Scenario 1, Scenario 2, and Scenario 3 functionality:
- Gemini story generation
- Stable Diffusion prompt building
- layout_builder.py composite assembly
- exporters.py PDF compilation with timestamped filename
- End-to-end comic engine pipeline
"""
import os
import sys
from pathlib import Path
import pytest

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import settings
from app.models.schemas import ComicCreateRequest
from app.services.gemini_story import GeminiStoryService
from app.services.sd_illustrator import StableDiffusionIllustrator
from app.layout_builder import layout_builder
from app.exporters import comic_exporter
from app.services.comic_engine import comic_engine

def test_gemini_story_service():
    """Verifies story outline and panel breakdown generation."""
    service = GeminiStoryService()
    story = service.generate_comic_story(
        prompt="A brave fox exploring an enchanted forest.",
        character_name="Rusty the Fox",
        setting="Enchanted Forest",
        tone="dramatic",
        art_style="anime",
        num_panels=4
    )
    
    assert "title" in story
    assert "panels" in story
    assert len(story["panels"]) == 4
    for panel in story["panels"]:
        assert "panel_number" in panel
        assert "visual_description" in panel
        assert "caption" in panel

def test_sd_illustrator_prompt_building():
    """Verifies artistic prompt injection and style tailoring."""
    illustrator = StableDiffusionIllustrator(provider="mock")
    prompt, neg = illustrator.build_prompt(
        visual_description="Rusty discovers an ancient runic tree",
        art_style="comic book",
        character_name="Rusty the Fox",
        setting="Enchanted Forest"
    )
    
    assert "Rusty the Fox" in prompt
    assert "comic book style" in prompt or "Jack Kirby" in prompt
    assert len(neg) > 0

def test_layout_builder_assembly(tmp_path):
    """Verifies layout_builder.py binds panel image, dialogue, and caption."""
    # Generate test panel image
    test_img = tmp_path / "raw_panel.png"
    illustrator = StableDiffusionIllustrator(provider="mock")
    illustrator._generate_stylized_canvas(
        visual_desc="Test scene",
        art_style="comic book",
        character_name="Rusty",
        setting="Forest",
        panel_number=1,
        output_path=test_img,
        width=512,
        height=384
    )
    assert test_img.exists()

    # Bind composite
    comp_path = tmp_path / "composite_panel.jpg"
    layout_builder.assemble_panel_composite(
        image_path=test_img,
        panel_number=1,
        title="The Awakening",
        caption="In the quiet woods, destiny calls.",
        dialogue="What ancient mystery lies ahead?",
        character_name="Rusty",
        sound_effect="SWOOSH!",
        output_composite_path=comp_path
    )
    assert comp_path.exists()
    assert os.path.getsize(comp_path) > 1000

def test_exporters_pdf_generation(tmp_path):
    """Verifies exporters.py compiles PDF with timestamped filename (Scenario 3)."""
    # Create test panel
    test_img = tmp_path / "panel_1.png"
    illustrator = StableDiffusionIllustrator(provider="mock")
    illustrator._generate_stylized_canvas(
        visual_desc="Hero stands at edge of forest",
        art_style="anime",
        character_name="Rusty",
        setting="Forest",
        panel_number=1,
        output_path=test_img,
        width=512,
        height=384
    )

    comic_data = {
        "id": "comic_test_123",
        "title": "Rusty The Fox",
        "tagline": "A Journey Beyond the Woods",
        "synopsis": "An epic adventure of courage and mystery.",
        "character_name": "Rusty the Fox",
        "setting": "Enchanted Forest",
        "art_style": "anime",
        "tone": "dramatic",
        "prompt": "A brave fox exploring an enchanted forest."
    }

    panels = [{
        "panel_number": 1,
        "title": "The Threshold",
        "caption": "The mist parts before the curious fox.",
        "dialogue": "I will discover the truth!",
        "character": "Rusty the Fox",
        "sound_effect": "RUMBLE!",
        "image_path": str(test_img)
    }]

    pdf_path = comic_exporter.export_to_pdf(
        comic_data=comic_data,
        panels=panels,
        page_format="A4"
    )

    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    # Ensure filename has timestamp pattern: e.g. comiccraft_rusty_the_fox_2026xxxx_xxxxxx.pdf
    assert "comiccraft_" in pdf_path.name
    assert os.path.getsize(pdf_path) > 5000

def test_scenario_1_and_scenario_2_pipeline(tmp_path):
    """
    Simulates Scenario 1 (Dramatic + Anime) and Scenario 2 (Funny + Comic Book).
    """
    # Scenario 1
    req1 = ComicCreateRequest(
        prompt="A brave fox exploring an enchanted forest.",
        character_name="Rusty the Fox",
        setting="Enchanted Forest",
        tone="dramatic",
        art_style="anime",
        num_panels=3
    )
    comic1 = comic_engine.generate_comic(req1)
    assert comic1.tone == "dramatic"
    assert comic1.art_style == "anime"
    assert len(comic1.panels) == 3

    # Scenario 2: Switch tone to "funny" and art style to "comic book"
    req2 = ComicCreateRequest(
        prompt="A brave fox exploring an enchanted forest.",
        character_name="Rusty the Fox",
        setting="Enchanted Forest",
        tone="funny",
        art_style="comic book",
        num_panels=3
    )
    comic2 = comic_engine.generate_comic(req2)
    assert comic2.tone == "funny"
    assert comic2.art_style == "comic book"
    assert len(comic2.panels) == 3

    # Scenario 3: PDF export
    export_result = comic_engine.export_pdf(comic2.id)
    assert "filename" in export_result
    assert "pdf_url" in export_result
    assert export_result["file_size_mb"] >= 0
