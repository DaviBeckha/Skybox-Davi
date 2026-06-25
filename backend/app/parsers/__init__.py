"""Parsers de demo: dispatcher entre parser real (Phase 07) e mock fallback (Phase 06)."""


def real_parser_available() -> bool:
    """Indica se o parser real (awpy/demoparser2) está disponível.

    Phase 06 sempre retorna False (usa o mock fallback). A Phase 07 passa a
    detectar/usar o parser real.
    """
    return False
