"""Registro das paginas da nova interface. Telas ainda nao redesenhadas aparecem como 'em redesenho'."""

from __future__ import annotations

import os
from collections.abc import Callable

from PySide6.QtWidgets import QWidget


def fabricas_de_paginas(usuario) -> dict[str, Callable[[], QWidget]]:
    from app.ui.paginas.cadastros import fabricas_de_cadastros
    from app.ui.paginas.dashboard import PaginaDashboard
    from app.ui.paginas.documentos import fabricas_de_documentos
    from app.ui.paginas.estoque import PaginaEstoque
    from app.ui.paginas.financeiro import PaginaFinanceiro
    from app.ui.paginas.relatorios import PaginaRelatorios

    fabricas: dict[str, Callable[[], QWidget]] = {
        "Dashboard": lambda: PaginaDashboard(usuario),
        **fabricas_de_cadastros(),
        **fabricas_de_documentos(usuario),
        "Estoque": lambda: PaginaEstoque(usuario),
        "Financeiro": lambda: PaginaFinanceiro(usuario),
        "Relatorios": PaginaRelatorios,
    }
    if os.environ.get("ERP_UI_GALERIA"):
        from app.ui.paginas.galeria import PaginaGaleria

        fabricas["Galeria"] = PaginaGaleria
    return fabricas
