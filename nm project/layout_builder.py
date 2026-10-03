"""
Root alias for layout_builder.py as referenced in project requirements.
Delegates to app.layout_builder.
"""
from app.layout_builder import LayoutBuilder, layout_builder

__all__ = ["LayoutBuilder", "layout_builder"]
