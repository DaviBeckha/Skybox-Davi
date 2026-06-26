"""Dispatcher do parser real da Phase 07."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from app.parsers.errors import DemoParseError
from app.parsers.result import ParsedDemo


def real_parser_available() -> bool:
    """True quando awpy ou demoparser2 podem ser importados no ambiente."""
    return (
        importlib.util.find_spec("awpy") is not None
        or importlib.util.find_spec("demoparser2") is not None
    )


def parse_demo(demo_path: Path, *, match_id: str) -> ParsedDemo:
    """Usa awpy primeiro; demoparser2 fica como fallback real granular.

    Converte qualquer erro nativo (inclui `pyo3_runtime.PanicException`, que herda
    de `BaseException`) em `DemoParseError`, para que o job marque a demo `failed`
    em vez de derrubar o worker com uma demo corrompida/inválida.
    """
    try:
        if importlib.util.find_spec("awpy") is not None:
            from app.parsers.parse_with_awpy import parse_demo as parse_with_awpy

            return parse_with_awpy(demo_path, match_id=match_id)
        if importlib.util.find_spec("demoparser2") is not None:
            from app.parsers.parse_with_demoparser2 import parse_demo as parse_with_demoparser2

            return parse_with_demoparser2(demo_path, match_id=match_id)
        raise DemoParseError("nenhum parser real disponível (awpy/demoparser2 ausentes)")
    except DemoParseError:
        raise
    except (KeyboardInterrupt, SystemExit, MemoryError):
        raise
    except BaseException as exc:  # noqa: BLE001 - inclui PanicException (pyo3)
        raise DemoParseError(f"falha ao parsear demo: {exc}") from exc
