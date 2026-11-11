"""Registro das paginas da nova interface. Telas ainda nao redesenhadas aparecem como 'em redesenho'."""

from __future__ import annotations

import os
from collections.abc import Callable

from PySide6.QtWidgets import QWidget


def fabricas_de_paginas(usuario) -> dict[str, Callable[[], QWidget]]:
    from app.ui.paginas.dashboard import PaginaDashboard

    fabricas: dict[str, Callable[[], QWidget]] = {"Dashboard": lambda: PaginaDashboard(usuario)}
    if os.environ.get("ERP_UI_GALERIA"):
        from app.ui.paginas.galeria import PaginaGaleria

        fabricas["Galeria"] = PaginaGaleria
    return fabricas
