import re


def validar_obrigatorio(valor: str | None, campo: str) -> None:
    if valor is None or not str(valor).strip():
        raise ValueError(f"{campo} e obrigatorio.")


def validar_email(email: str) -> None:
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()):
        raise ValueError("E-mail invalido.")


def validar_email_opcional(email: str | None) -> None:
    if email and email.strip():
        validar_email(email)
