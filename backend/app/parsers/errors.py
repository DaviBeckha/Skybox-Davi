"""Exceções dos parsers."""

from __future__ import annotations


class DemoParseError(RuntimeError):
    """Falha ao parsear uma demo.

    Usada para converter erros nativos (inclui `pyo3_runtime.PanicException`, que
    herda de `BaseException` e escaparia de um `except Exception`) em uma exceção
    normal, capturável pelo job de parsing → status `failed`.
    """
