from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"
BACKUPS_DIR = ROOT_DIR / "backups"
DATABASE_URL = f"sqlite:///{DATA_DIR / 'erp_autopecas.db'}"
DATABASE_FILE = DATA_DIR / "erp_autopecas.db"

APP_NAME = "ERP CRM Autopecas & Servicos"
