"""Compatibility re-exports — renderers live in apa7_validator.render."""

from apa7_validator.render import render_human, render_json

__all__ = ["render_human", "render_json"]
