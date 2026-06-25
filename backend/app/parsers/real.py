"""Dispatcher do parser real da Phase 07."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from app.parsers.result import ParsedDemo


def real_parser_available() -> bool:
    """True quando awpy ou demoparser2 podem ser importados no ambiente."""
    return (
        importlib.util.find_spec("awpy") is not None
        or importlib.util.find_spec("demoparser2") is not None
    )


def parse_demo(demo_path: Path, *, match_id: str) -> ParsedDemo:
    """Usa awpy primeiro; demoparser2 fica como fallback real granular."""
    if importlib.util.find_spec("awpy") is not None:
        from app.parsers.parse_with_awpy import parse_demo as parse_with_awpy

        return parse_with_awpy(demo_path, match_id=match_id)
    if importlib.util.find_spec("demoparser2") is not None:
        from app.parsers.parse_with_demoparser2 import parse_demo as parse_with_demoparser2

        return parse_with_demoparser2(demo_path, match_id=match_id)
    raise RuntimeError("nenhum parser real disponível (awpy/demoparser2 ausentes)")
