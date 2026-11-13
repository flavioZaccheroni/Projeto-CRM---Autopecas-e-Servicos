import os
import sys
from pathlib import Path


def resolver_raiz(congelado: bool, pasta_exe: Path | None = None, ambiente: dict | None = None, pasta_codigo: Path | None = None) -> Path:
    """Pasta-raiz gravavel do sistema (dados, logs, backups e exports).

    - Codigo-fonte: a propria pasta do projeto.
    - Executavel (PyInstaller): modo portatil (ao lado do .exe) quando ja existe uma pasta `data` ou o arquivo
      `portable.flag` ali, o que preserva instalacoes e o pacote de demonstracao; caso contrario, uma pasta do
      usuario (pasta ERP_Autopecas em %LOCALAPPDATA%), que o Windows sempre permite gravar, mesmo se o programa estiver
      instalado em "Arquivos de Programas".
    - `ERP_HOME` forca uma pasta especifica.
    """
    ambiente = os.environ if ambiente is None else ambiente
    if ambiente.get("ERP_HOME"):
        return Path(ambiente["ERP_HOME"]).resolve()
    if not congelado:
        return pasta_codigo or Path(__file__).resolve().parents[2]
    exe = pasta_exe or Path(sys.executable).resolve().parent
    if (exe / "data").exists() or (exe / "portable.flag").exists():
        return exe
    base = ambiente.get("LOCALAPPDATA")
    return (Path(base) if base else Path.home() / "AppData" / "Local") / "ERP_Autopecas"


ROOT_DIR = resolver_raiz(getattr(sys, "frozen", False))
# ERP_DATA_DIR permite apontar para outro banco (ex.: a base de demonstracao) sem mexer nos dados reais.
DATA_DIR = Path(os.environ["ERP_DATA_DIR"]).resolve() if os.environ.get("ERP_DATA_DIR") else ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"
BACKUPS_DIR = ROOT_DIR / "backups"
DATABASE_URL = f"sqlite:///{DATA_DIR / 'erp_autopecas.db'}"
DATABASE_FILE = DATA_DIR / "erp_autopecas.db"

APP_NAME = "ERP CRM Autopecas & Servicos"
APP_VERSION = "3.1.0"
AVISO_DEMO = "Versão de demonstração — uso apenas para testes, por até 30 dias, sem dados reais."
AVISO_DEMO_CURTO = "Demonstração · 30 dias de teste"
