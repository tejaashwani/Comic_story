import os
import json
import logging
import re
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger("comiccraft.gemini")

class GeminiStoryService:
    """
    Handles script generation, panel outlines, dialogue, and Stable Diffusion
    image prompt engineering using Google Gemini 1.5 Pro / Flash models.
    """
    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self._init_client()

    def _init_client(self):
        self.client = None
        self.genai_type = None

        if not self.api_key:
            logger.warning("No GEMINI_API_KEY set. Built-in story synthesis generator will be available as fallback.")
            return

        # Attempt to initialize google.genai or google.generativeai
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model_name)
            self.genai_type = "legacy"
            logger.info(f"Initialized google.generativeai with model {self.model_name}")
            return
        except ImportError:
            pass

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.genai_type = "new"
            logger.info(f"Initialized google.genai with model {self.model_name}")
        except Exception as e:
            logger.warning(f"Could not initialize Gemini SDK ({e}). Fallback generator enabled.")

    def generate_comic_story(
        self,
        prompt: str,
        character_name: str,
        setting: str,
        tone: str = "dramatic",
        art_style: str = "comic book",
        num_panels: int = 4
    ) -> Dict[str, Any]:
        """
        Generates a cohesive comic storyline with structured panel breakdowns.
        """
        if self.client:
            try:
                return self._call_gemini_api(prompt, character_name, setting, tone, art_style, num_panels)
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}. Falling back to internal generator.")
                return self._generate_fallback_story(prompt, character_name, setting, tone, art_style, num_panels)
        else:
            return self._generate_fallback_story(prompt, character_name, setting, tone, art_style, num_panels)

    def _call_gemini_api(
        self,
        prompt: str,
        character_name: str,
        setting: str,
        tone: str,
        art_style: str,
        num_panels: int
    ) -> Dict[str, Any]:
        system_instructions = (
            "You are a master comic book author, storyboard director, and visual artist. "
            "Your task is to craft an engaging, cohesive comic strip with a clear narrative arc "
            "(Beginning, Rising Action, Climax, Resolution). "
            "You MUST respond ONLY with valid JSON matching the exact schema specified below."
        )

        style_info = settings.ART_STYLES.get(art_style.lower(), {})
        style_prompt = style_info.get("prompt_enhancement", art_style)

        user_prompt = f"""
Create a {num_panels}-panel comic strip based on the following creative specifications:
- Core Story Prompt: {prompt}
- Protagonist Name: {character_name}
- World / Setting: {setting}
- Story Tone: {tone} (Tailor all dialogues, narration, pacing, and emotional depth to this specific tone)
- Visual Art Style: {art_style} ({style_prompt})

JSON output structure:
{{
  "title": "A compelling, catchy comic title",
  "tagline": "A punchy one-sentence comic teaser",
  "synopsis": "A 2-3 sentence overview of this comic issue",
  "panels": [
    {{
      "panel_number": 1,
      "title": "Panel scene title",
      "caption": "Narrative caption or voiceover text describing the moment",
      "dialogue": "Character dialogue speech bubble (or empty if purely visual/action)",
      "character": "{character_name}",
      "sound_effect": "A comic sound effect like WHOOSH, BOOM, CRACKLE, or null",
      "visual_description": "Extremely detailed, vivid visual prompt for Stable Diffusion describing the camera angle (close-up, wide shot, Dutch angle), character pose, expression, background lighting, color palette, and action."
    }}
  ]
}}

Ensure there are EXACTLY {num_panels} panels. Ensure valid JSON without extra markdown wrapping.
"""

        raw_text = ""
        if self.genai_type == "legacy":
            response = self.client.generate_content(
                f"{system_instructions}\n\n{user_prompt}",
                generation_config={"temperature": 0.75, "max_output_tokens": 2048}
            )
            raw_text = response.text
        elif self.genai_type == "new":
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"{system_instructions}\n\n{user_prompt}"
            )
            raw_text = response.text

        # Extract and parse JSON
        cleaned_json = self._extract_json(raw_text)
        data = json.loads(cleaned_json)
        return data

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        # Remove markdown code fences if present
        if "```json" in text:
            match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                return match.group(1)
        if "```" in text:
            match = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                return match.group(1)
        
        # Look for outer curly braces
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start:end+1]
        return text

    def _generate_fallback_story(
        self,
        prompt: str,
        character_name: str,
        setting: str,
        tone: str,
        art_style: str,
        num_panels: int
    ) -> Dict[str, Any]:
        """
        High quality contextual fallback generator that dynamically adapts
        to user inputs even without external Gemini API connectivity.
        """
        logger.info(f"Generating contextual story via internal engine for: {character_name} in {setting}")
        
        # Determine narrative flavor based on tone
        is_funny = "fun" in tone.lower() or "comic" in tone.lower() or "humor" in tone.lower()
        is_dramatic = "dram" in tone.lower() or "dark" in tone.lower() or "noir" in tone.lower()
        is_heroic = "hero" in tone.lower() or "action" in tone.lower()
        
        if is_funny:
            title = f"The Hilarious Misadventures of {character_name}"
            tagline = f"When exploring {setting} goes comically sideways!"
            sfx_list = ["SPLAT!", "BOING!", "WHOOPS!", "YIKES!", "BONK!", "ZOOM!"]
            p1_cap = f"In the whimsical corners of {setting}, {character_name} thought today would be simple."
            p1_diag = "What could possibly go wrong? I'm an expert at this!"
            p2_cap = f"Plot twist: Everything that could go wrong in {setting}, promptly did."
            p2_diag = "Wait... did that glowing mushroom just wink at me?!"
            p3_cap = f"Desperation meets sheer slapstick comedy as {character_name} reacts."
            p3_diag = "Hold on to your hats! Time for the legendary tactical retreat!"
            p4_cap = f"Catching breath under the canopy of {setting}, grinning despite the chaos."
            p4_diag = "Phew! Well, at least nobody saw that. Right?"
        elif is_dramatic:
            title = f"{character_name}: Shadows of {setting}"
            tagline = f"In the heart of {setting}, destiny demands courage."
            sfx_list = ["RUMBLE...", "CRACKLE!", "SHHHK!", "THUD!", "WHISPER...", "BOOM!"]
            p1_cap = f"The silence of {setting} hung heavy, broken only by {character_name}'s resolute footsteps."
            p1_diag = "The ancient legends were true... it really is hidden here."
            p2_cap = f"An unexpected tremor shakes {setting}. Shadows lengthen with menacing grace."
            p2_diag = "Show yourself! I won't back down now!"
            p3_cap = f"A blinding surge of elemental energy illuminates {character_name}'s determined gaze."
            p3_diag = "For all we hold dear... I must endure this trial!"
            p4_cap = f"The storm subsides over {setting}. A newfound radiance marks a guardian reborn."
            p4_diag = "This is only the beginning of our quest."
        else: # Adventurous / default
            title = f"{character_name} and the Secrets of {setting}"
            tagline = f"An epic journey into the uncharted depths of {setting}."
            sfx_list = ["WHOOSH!", "FLASH!", "SWOOSH!", "RUMBLE!", "DING!", "AURA!"]
            p1_cap = f"{character_name} steps beyond the borders of known maps into {setting}."
            p1_diag = "Every path has a secret waiting to be uncovered."
            p2_cap = f"Deep within {setting}, an ancient relic awakens to the explorer's presence."
            p2_diag = "Look at this craftsmanship... it's pulsating with living light!"
            p3_cap = f"Without warning, guardian runes ignite across the terrain."
            p3_diag = "Quick reflexes! We need to harmonize with the frequencies!"
            p4_cap = f"The trial mastered, {setting} reveals its wondrous panoramic vista."
            p4_diag = "Magnificent... the journey has only just begun!"

        panels = []
        raw_panels = [
            (p1_cap, p1_diag, sfx_list[0], f"Wide establishing shot of {character_name} standing at the threshold of {setting}, cinematic atmospheric lighting, curious expression, detailed background"),
            (p2_cap, p2_diag, sfx_list[1], f"Medium shot of {character_name} discovering a magical anomaly in {setting}, glowing particles, dynamic camera angle, expressive face"),
            (p3_cap, p3_diag, sfx_list[2], f"Intense action panel, dramatic Dutch angle, dynamic pose of {character_name} reacting to sudden event in {setting}, motion lines, vibrant colors"),
            (p4_cap, p4_diag, sfx_list[3], f"Inspiring hero shot, golden hour lighting bathing {setting}, {character_name} smiling triumphantly into the horizon, masterwork composition")
        ]

        # Generate panels up to num_panels
        for i in range(num_panels):
            idx = i % len(raw_panels)
            cap, diag, sfx, vis = raw_panels[idx]
            panels.append({
                "panel_number": i + 1,
                "title": f"Panel {i + 1}: {['The Arrival', 'The Encounter', 'The Turning Point', 'The Horizon', 'The Discovery', 'The Triumph'][i % 6]}",
                "caption": cap,
                "dialogue": diag,
                "character": character_name,
                "sound_effect": sfx,
                "visual_description": f"{vis}, {tone} mood, {prompt}"
            })

        return {
            "title": title,
            "tagline": tagline,
            "synopsis": f"A {tone} comic adventure featuring {character_name} in {setting}. Prompt inspired: '{prompt}'.",
            "panels": panels
        }
