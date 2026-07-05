from app.database.init_db import initialize_database
from app.views.login_view import LoginView


def main() -> None:
    initialize_database()
    LoginView().run()


if __name__ == "__main__":
    main()
