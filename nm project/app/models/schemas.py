from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ComicCreateRequest(BaseModel):
    prompt: str = Field(..., description="High level story prompt or idea", example="A brave fox exploring an enchanted forest.")
    character_name: str = Field(..., description="Main protagonist name", example="Rusty")
    setting: str = Field(..., description="Primary world or environment", example="Enchanted luminescent forest")
    tone: str = Field(default="dramatic", description="Narrative tone (e.g. dramatic, funny, adventurous)")
    art_style: str = Field(default="comic book", description="Visual aesthetic (e.g. comic book, anime, watercolor)")
    num_panels: int = Field(default=4, ge=2, le=8, description="Number of panels to generate")

class PanelData(BaseModel):
    panel_number: int
    title: str = ""
    caption: str = ""
    dialogue: str = ""
    character: str = ""
    sound_effect: Optional[str] = None
    visual_description: str
    image_url: Optional[str] = None
    image_path: Optional[str] = None

class ComicData(BaseModel):
    id: str
    title: str
    tagline: Optional[str] = ""
    synopsis: Optional[str] = ""
    prompt: str
    character_name: str
    setting: str
    tone: str
    art_style: str
    created_at: str
    num_panels: int
    panels: List[PanelData] = []
    pdf_filename: Optional[str] = None
    pdf_url: Optional[str] = None
    status: str = "completed"

class RegeneratePanelRequest(BaseModel):
    panel_number: int
    custom_prompt: Optional[str] = None
    updated_dialogue: Optional[str] = None
    updated_caption: Optional[str] = None

class ExportPDFRequest(BaseModel):
    comic_id: str
    include_cover: bool = True
    page_format: str = "A4" # A4 or Letter
    orientation: str = "P" # P (Portrait) or L (Landscape)

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
