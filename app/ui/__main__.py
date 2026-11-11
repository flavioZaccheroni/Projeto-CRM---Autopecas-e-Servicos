"""Executa a nova interface:  python -m app.ui"""

import sys

from app.database.init_db import initialize_database
from app.ui.aplicacao import Aplicacao
from app.utils.logger import configurar_logger

if __name__ == "__main__":
    configurar_logger()
    initialize_database()
    raise SystemExit(Aplicacao(sys.argv).executar())
