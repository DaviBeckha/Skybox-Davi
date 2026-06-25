"""Parsers de demo: dispatcher entre parser real (Phase 07) e mock fallback."""

from app.parsers.real import parse_demo as parse_real_demo
from app.parsers.real import real_parser_available

__all__ = ["parse_real_demo", "real_parser_available"]
