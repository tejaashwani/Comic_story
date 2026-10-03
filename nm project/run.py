"""
ComicCraft Entrypoint
Runs the FastAPI web application with hot-reloading.
"""
import sys
import os
from pathlib import Path

# Ensure Windows terminal doesn't crash on emoji or UTF-8 characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("===========================================================")
    print(f"  [COMICCRAFT] {settings.APP_NAME} v{settings.APP_VERSION} - AI Comic Studio")
    print(f"  Server URL: http://{settings.HOST}:{settings.PORT}")
    print(f"  Diffusers/SD Provider: {settings.SD_PROVIDER.upper()}")
    print(f"  Story Engine: Gemini ({settings.GEMINI_MODEL})")
    print(f"  PDF Engine: layout_builder.py & exporters.py (FPDF)")
    print("===========================================================")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
