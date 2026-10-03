import os
import logging
from pathlib import Path
from fastapi import FastAPI, Request, Form, HTTPException, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.models.schemas import ComicCreateRequest, RegeneratePanelRequest, ExportPDFRequest, APIResponse
from app.services.comic_engine import comic_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("comiccraft.main")

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION
)

# Ensure directories exist
settings.STATIC_DIR.mkdir(parents=True, exist_ok=True)
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.COMICS_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Mount Static and Storage directories
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")
app.mount("/storage", StaticFiles(directory=str(settings.STORAGE_DIR)), name="storage")

# Setup Jinja2 Templates
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

# -----------------------------------------------------------------------------
# Frontend Page Views
# -----------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home_studio(request: Request):
    """
    Main Creative Studio view.
    Includes form for Story Prompt, Character Name, Setting, Tone, and Art Style.
    """
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.APP_NAME,
            "art_styles": settings.ART_STYLES,
            "tones": settings.TONES,
            "default_panels": settings.DEFAULT_PANELS,
            "sd_provider": settings.SD_PROVIDER
        }
    )

@app.get("/preview/{comic_id}", response_class=HTMLResponse)
async def comic_preview(request: Request, comic_id: str):
    """
    Interactive Comic Preview page.
    Displays panels with comic book styling, speech bubbles, sound effects,
    and download / export actions.
    """
    comic = comic_engine.get_comic(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")

    return templates.TemplateResponse(
        request=request,
        name="preview.html",
        context={
            "app_name": settings.APP_NAME,
            "comic": comic,
            "art_styles": settings.ART_STYLES
        }
    )

@app.get("/export-success/{comic_id}", response_class=HTMLResponse)
async def export_success_view(request: Request, comic_id: str):
    """
    Scenario 3: Export Success confirmation page.
    Confirms successful download, shows PDF download button, metadata, and reader.
    """
    comic = comic_engine.get_comic(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")

    # If PDF has not been generated yet, generate it now
    if not comic.pdf_filename:
        export_res = comic_engine.export_pdf(comic_id)
        comic = comic_engine.get_comic(comic_id)

    pdf_path = settings.EXPORTS_DIR / comic.pdf_filename
    file_size_mb = 0.0
    if pdf_path.exists():
        file_size_mb = round(os.path.getsize(pdf_path) / (1024 * 1024), 2)

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "app_name": settings.APP_NAME,
            "comic": comic,
            "file_size_mb": file_size_mb,
            "pdf_filename": comic.pdf_filename,
            "pdf_url": comic.pdf_url
        }
    )

@app.get("/gallery", response_class=HTMLResponse)
async def gallery_view(request: Request):
    """
    Gallery view to browse and read all saved comic issues.
    """
    comics = comic_engine.list_comics()
    return templates.TemplateResponse(
        request=request,
        name="gallery.html",
        context={
            "app_name": settings.APP_NAME,
            "comics": comics
        }
    )

@app.get("/settings", response_class=HTMLResponse)
async def settings_view(request: Request):
    """
    Config and status page for Gemini AI and Stable Diffusion providers.
    """
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "app_name": settings.APP_NAME,
            "settings": settings,
            "has_gemini": bool(settings.GEMINI_API_KEY),
            "has_hf": bool(settings.HF_TOKEN)
        }
    )

# -----------------------------------------------------------------------------
# REST API Endpoints
# -----------------------------------------------------------------------------

@app.post("/api/generate", response_model=APIResponse)
async def api_generate_comic(req: ComicCreateRequest):
    """
    Scenario 1 & 2 Generation Endpoint:
    Combines Gemini 1.5 Pro and Stable Diffusion to generate the comic strip.
    """
    try:
        comic = comic_engine.generate_comic(req)
        return APIResponse(
            success=True,
            message="Comic created successfully!",
            data={
                "comic_id": comic.id,
                "preview_url": f"/preview/{comic.id}",
                "title": comic.title,
                "panels_count": len(comic.panels)
            }
        )
    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        return APIResponse(
            success=False,
            message=f"Failed to generate comic: {str(e)}"
        )

@app.post("/api/export-pdf")
async def api_export_pdf(req: ExportPDFRequest):
    """
    Scenario 3 PDF Generation Endpoint:
    Calls layout_builder.py and exporters.py to generate PDF and redirects to export-success.
    """
    try:
        res = comic_engine.export_pdf(
            comic_id=req.comic_id,
            page_format=req.page_format,
            orientation=req.orientation
        )
        return {
            "success": True,
            "export_success_url": f"/export-success/{req.comic_id}",
            "pdf_url": res["pdf_url"],
            "filename": res["filename"],
            "file_size_mb": res["file_size_mb"]
        }
    except Exception as e:
        logger.error(f"PDF export error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/regenerate-panel")
async def api_regenerate_panel(req: RegeneratePanelRequest, comic_id: str = Query(...)):
    """
    Re-generate or edit an individual panel.
    """
    try:
        updated_comic = comic_engine.regenerate_panel(
            comic_id=comic_id,
            panel_number=req.panel_number,
            custom_prompt=req.custom_prompt,
            updated_dialogue=req.updated_dialogue,
            updated_caption=req.updated_caption
        )
        if not updated_comic:
            raise HTTPException(status_code=404, detail="Comic or panel not found")

        return {
            "success": True,
            "message": f"Panel {req.panel_number} refreshed successfully",
            "panel": [p.dict() for p in updated_comic.panels if p.panel_number == req.panel_number][0]
        }
    except Exception as e:
        logger.error(f"Panel regeneration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{filename}")
async def api_download_file(filename: str):
    """
    Direct file download endpoint for PDF exports.
    """
    file_path = settings.EXPORTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested file not found")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf"
    )

@app.get("/api/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "gemini_active": bool(settings.GEMINI_API_KEY),
        "sd_provider": settings.SD_PROVIDER
    }
