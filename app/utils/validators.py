import re

UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
    "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


def validar_obrigatorio(valor: str | None, campo: str) -> None:
    if valor is None or not str(valor).strip():
        raise ValueError(f"{campo} e obrigatorio.")


def validar_email(email: str) -> None:
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()):
        raise ValueError("E-mail invalido.")


def validar_email_opcional(email: str | None) -> None:
    if email and email.strip():
        validar_email(email)


def somente_digitos(valor: str | None) -> str:
    return re.sub(r"\D", "", valor or "")


def cpf_valido(valor: str | None) -> bool:
    cpf = somente_digitos(valor)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11 % 10
        if digito != int(cpf[tamanho]):
            return False
    return True


def cnpj_valido(valor: str | None) -> bool:
    cnpj = somente_digitos(valor)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    for tamanho in (12, 13):
        pesos = ([5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] if tamanho == 12 else [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(tamanho))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if digito != int(cnpj[tamanho]):
            return False
    return True


def validar_cpf(valor: str | None) -> None:
    if not cpf_valido(valor):
        raise ValueError("CPF invalido.")


def validar_cnpj(valor: str | None) -> None:
    if not cnpj_valido(valor):
        raise ValueError("CNPJ invalido.")


def validar_cpf_cnpj(valor: str | None, tipo_pessoa: str | None = None) -> None:
    """Valida CPF (11 digitos) ou CNPJ (14 digitos). O tipo PF/PJ, quando informado, deve bater."""
    digitos = somente_digitos(valor)
    tipo = (tipo_pessoa or "").strip().upper()
    if tipo == "PF" or (tipo != "PJ" and len(digitos) == 11):
        validar_cpf(valor)
    elif tipo == "PJ" or len(digitos) == 14:
        validar_cnpj(valor)
    else:
        raise ValueError("CPF/CNPJ invalido.")


def validar_uf_opcional(uf: str | None) -> None:
    if uf and uf.strip() and uf.strip().upper() not in UFS:
        raise ValueError("UF invalida.")


def validar_telefone_opcional(telefone: str | None) -> None:
    if telefone and telefone.strip() and len(somente_digitos(telefone)) not in (10, 11):
        raise ValueError("Telefone invalido. Informe DDD + numero.")


def placa_valida(placa: str | None) -> bool:
    valor = (placa or "").strip().upper().replace("-", "")
    return bool(re.fullmatch(r"[A-Z]{3}\d{4}", valor) or re.fullmatch(r"[A-Z]{3}\d[A-Z]\d{2}", valor))


def validar_placa(placa: str | None) -> None:
    if not placa_valida(placa):
        raise ValueError("Placa invalida. Use o formato ABC1234 ou ABC1D23.")


def validar_senha_forte(senha: str | None) -> None:
    senha = senha or ""
    if len(senha) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")
    if not re.search(r"[A-Za-z]", senha) or not re.search(r"\d", senha):
        raise ValueError("A senha deve conter letras e numeros.")
