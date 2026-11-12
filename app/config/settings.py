import os
import sys
from pathlib import Path

# Empacotado (PyInstaller): dados, logs e backups ficam ao lado do .exe, nunca na pasta temporaria do bundle.
ROOT_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
# ERP_DATA_DIR permite apontar para outro banco (ex.: a base de demonstracao) sem mexer nos dados reais.
DATA_DIR = Path(os.environ["ERP_DATA_DIR"]).resolve() if os.environ.get("ERP_DATA_DIR") else ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"
BACKUPS_DIR = ROOT_DIR / "backups"
DATABASE_URL = f"sqlite:///{DATA_DIR / 'erp_autopecas.db'}"
DATABASE_FILE = DATA_DIR / "erp_autopecas.db"

APP_NAME = "ERP CRM Autopecas & Servicos"
APP_VERSION = "3.0.1"
AVISO_DEMO = "Versão de demonstração — uso apenas para testes, por até 30 dias, sem dados reais."
AVISO_DEMO_CURTO = "Demonstração · 30 dias de teste"
