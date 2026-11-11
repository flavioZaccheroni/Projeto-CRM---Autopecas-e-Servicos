from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT_DIR / "dist"
RELEASES_DIR = ROOT_DIR / "releases"
RELEASE_STAGING = ROOT_DIR / "build" / "release_staging"


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera pacote de release do ERP CRM Autopecas.")
    parser.add_argument("--version", default=datetime.now().strftime("%Y.%m.%d.%H%M"), help="Versao do pacote.")
    parser.add_argument("--skip-exe", action="store_true", help="Nao tentar gerar executavel com PyInstaller.")
    args = parser.parse_args()

    release_name = f"erp_autopecas_{args.version}"
    release_dir = RELEASE_STAGING / release_name
    archive_path = RELEASES_DIR / f"{release_name}.zip"

    _clean_release_dir(release_dir)
    _copy_project_files(release_dir)
    _write_runtime_files(release_dir, args.version)

    exe_path = None
    if not args.skip_exe:
        exe_path = _try_build_exe()
        if exe_path and exe_path.exists():
            bin_dir = release_dir / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(exe_path, bin_dir / exe_path.name)

    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        archive_path.unlink()
    shutil.make_archive(str(archive_path.with_suffix("")), "zip", release_dir)
    print(f"Release gerado: {archive_path}")
    if exe_path:
        print(f"Executavel incluido: {exe_path}")
    else:
        print("Executavel PyInstaller nao incluido; release portatil criado com executar.bat.")
    return 0


def _clean_release_dir(release_dir: Path) -> None:
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)


def _copy_project_files(release_dir: Path) -> None:
    for name in ["app", "docs", "main.py", "requirements.txt", "README.md"]:
        source = ROOT_DIR / name
        target = release_dir / name
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(source, target)
    for name in ["data", "logs", "backups", "exports"]:
        (release_dir / name).mkdir(parents=True, exist_ok=True)


def _write_runtime_files(release_dir: Path, version: str) -> None:
    (release_dir / "VERSION.txt").write_text(f"ERP CRM Autopecas & Servicos\nVersao: {version}\n", encoding="utf-8")
    (release_dir / "executar.bat").write_text(
        "@echo off\n"
        "setlocal\n"
        "cd /d %~dp0\n"
        "if not exist .venv (\n"
        "  py -m venv .venv\n"
        ")\n"
        "call .venv\\Scripts\\activate.bat\n"
        "python -m pip install -r requirements.txt\n"
        "python main.py\n",
        encoding="utf-8",
    )
    (release_dir / "instalar_dependencias.bat").write_text(
        "@echo off\n"
        "setlocal\n"
        "cd /d %~dp0\n"
        "py -m venv .venv\n"
        "call .venv\\Scripts\\activate.bat\n"
        "python -m pip install --upgrade pip\n"
        "python -m pip install -r requirements.txt\n"
        "echo Instalacao concluida.\n"
        "pause\n",
        encoding="utf-8",
    )


def _try_build_exe() -> Path | None:
    if not _module_available("PyInstaller"):
        print("PyInstaller nao instalado; pulando geracao de .exe.")
        return None
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--windowed",
        "--name",
        "ERP_Autopecas",
        # scripts do Alembic sao lidos do disco em tempo de execucao: precisam ir junto
        "--add-data",
        f"{ROOT_DIR / 'app' / 'database' / 'alembic'}{os.pathsep}app/database/alembic",
        "--hidden-import",
        "alembic.runtime.migration",
        "main.py",
    ]
    result = subprocess.run(command, cwd=ROOT_DIR, check=False)
    if result.returncode != 0:
        print("PyInstaller falhou; mantendo release portatil.")
        return None
    if _pyinstaller_warned_broken_tkinter():
        print("PyInstaller detectou Tkinter/Tcl quebrado neste ambiente; .exe nao sera incluido.")
        return None
    return DIST_DIR / "ERP_Autopecas" / "ERP_Autopecas.exe"


def _pyinstaller_warned_broken_tkinter() -> bool:
    warning_file = ROOT_DIR / "build" / "ERP_Autopecas" / "warn-ERP_Autopecas.txt"
    if not warning_file.exists():
        return False
    warning_text = warning_file.read_text(encoding="utf-8", errors="ignore").lower()
    return "tkinter installation is broken" in warning_text or "missing module named tkinter" in warning_text


def _module_available(module_name: str) -> bool:
    result = subprocess.run(
        [sys.executable, "-c", f"import importlib.util; raise SystemExit(0 if importlib.util.find_spec('{module_name}') else 1)"],
        check=False,
    )
    return result.returncode == 0


if __name__ == "__main__":
    raise SystemExit(main())
