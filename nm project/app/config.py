import os
from pathlib import Path

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel
    class BaseSettings(BaseModel):
        pass

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "ComicCraft"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-Powered Personalized Comic Book & Graphic Novel Creator"
    
    # Server Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    
    # Stable Diffusion / Image Provider
    # Options: "cloud", "diffusers", "huggingface", "mock"
    SD_PROVIDER: str = os.getenv("SD_PROVIDER", "cloud")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    SD_MODEL_ID: str = os.getenv("SD_MODEL_ID", "stabilityai/stable-diffusion-2-1")
    
    # Image Generation Config
    IMAGE_WIDTH: int = 768
    IMAGE_HEIGHT: int = 512
    DEFAULT_PANELS: int = 4
    
    # Directories
    BASE_DIR: Path = BASE_DIR
    STORAGE_DIR: Path = BASE_DIR / "storage"
    COMICS_DIR: Path = BASE_DIR / "storage" / "comics"
    EXPORTS_DIR: Path = BASE_DIR / "storage" / "exports"
    STATIC_DIR: Path = BASE_DIR / "app" / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"
    
    # Predefined Art Styles and their specialized prompt enhancements
    ART_STYLES: dict = {
        "comic book": {
            "label": "Classic Comic Book",
            "prompt_enhancement": "classic American comic book style, bold black ink outlines, dynamic action framing, halftone dot pattern, dramatic cel-shading, vintage pulp colors, Jack Kirby and Stan Lee comic aesthetic, 4k resolution, masterpiece",
            "negative_prompt": "photorealistic, photograph, 3d render, blurry, distorted, grainy, washed out, low quality"
        },
        "anime": {
            "label": "Anime / Manga",
            "prompt_enhancement": "vibrant Japanese anime aesthetic, Makoto Shinkai and Studio Ghibli cinematic lighting, expressive detailed eyes, crisp cel shading, clean linework, breathtaking composition, 8k digital illustration",
            "negative_prompt": "ugly, 3d, realistic photograph, Western comic style, dull, low resolution, anatomical errors"
        },
        "watercolor": {
            "label": "Storybook Watercolor",
            "prompt_enhancement": "dreamy whimsical watercolor illustration, soft blended pastel washes, paper texture, elegant pencil underdrawing, storybook aesthetic, gentle luminous lighting, artistic masterpiece",
            "negative_prompt": "harsh black lines, neon, photo, 3d render, plastic, oversaturated"
        },
        "cyberpunk": {
            "label": "Cyberpunk Graphic Novel",
            "prompt_enhancement": "futuristic cyberpunk graphic novel art, glowing neon accents, moody rain-slicked atmosphere, high-contrast chiaroscuro, intricate mechanical details, cinematic sci-fi framing, highly detailed",
            "negative_prompt": "rustic, watercolor, medieval, blurry, oversaturated, amateur"
        },
        "dark fantasy": {
            "label": "Dark Fantasy / Noir",
            "prompt_enhancement": "dark fantasy grimdark comic style, heavy shadows, muted brooding earth tones, gritty inking, moody atmospheric fog, Frank Miller sin city meets Mike Mignola Hellboy style",
            "negative_prompt": "bright pastel, cartoon, childish, low contrast, washed out"
        },
        "retro cartoon": {
            "label": "Retro Cartoon / Sunday Strip",
            "prompt_enhancement": "playful vintage 1960s Sunday cartoon strip, cheerful colorful palette, thick expressive ink strokes, fun rounded caricatures, light-hearted illustration",
            "negative_prompt": "grim, dark, realistic, horror, photorealistic, grainy"
        }
    }
    
    # Predefined Tones
    TONES: list = [
        "dramatic",
        "funny",
        "adventurous",
        "mysterious",
        "heroic",
        "whimsical",
        "dark & gritty",
        "inspirational"
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.COMICS_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
