import sys

from app.database.init_db import initialize_database
from app.utils.logger import configurar_logger
from app.views.login_view import LoginView


def autoteste() -> int:
    """Valida o pacote (inclusive o .exe): banco via Alembic + Tk abrindo. Grava o resultado em selftest.txt."""
    from app.config.settings import DATA_DIR
    from app.database.alembic_runner import versao_atual
    from app.database.database import engine

    resultado = DATA_DIR / "selftest.txt"
    try:
        initialize_database()
        versao = versao_atual(engine)
        import tkinter

        raiz = tkinter.Tk()
        raiz.update()
        raiz.destroy()
        resultado.write_text(f"OK alembic={versao}\n", encoding="utf-8")
        return 0
    except Exception as exc:  # noqa: BLE001 - qualquer falha reprova o autoteste
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        resultado.write_text(f"FALHOU {type(exc).__name__}: {exc}\n", encoding="utf-8")
        return 1


def main() -> None:
    if "--selftest" in sys.argv:
        raise SystemExit(autoteste())
    configurar_logger()
    initialize_database()
    LoginView().run()


if __name__ == "__main__":
    main()
