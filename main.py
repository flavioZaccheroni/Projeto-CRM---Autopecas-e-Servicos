from app.database.init_db import initialize_database
from app.utils.logger import configurar_logger
from app.views.login_view import LoginView


def main() -> None:
    configurar_logger()
    initialize_database()
    LoginView().run()


if __name__ == "__main__":
    main()
