"""Funcoes puras de busca/filtro e leitura de colunas (usadas pelas interfaces Tk e Qt)."""

import re
import unicodedata


def normalizar(texto) -> str:
    """Minusculas e sem acentos, para buscas tolerantes ('Pecas' acha 'Peças')."""
    base = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(c for c in base if not unicodedata.combining(c)).lower()


def extrair_id(texto) -> str:
    """'12 - Filtro de oleo' -> '12'; '7' -> '7'; texto sem numero inicial -> ''."""
    encontrado = re.match(r"^\s*(\d+)\s*(?:-.*)?$", str(texto or ""), re.S)
    return encontrado.group(1) if encontrado else ""


def filtrar_linhas(linhas: list[tuple[str, list]], termo: str) -> list[tuple[str, list]]:
    """Mantem as linhas que contem TODAS as palavras do termo em qualquer coluna."""
    palavras = normalizar(termo).split()
    if not palavras:
        return list(linhas)
    resultado = []
    for iid, valores in linhas:
        texto = normalizar(" ".join(str(v) for v in valores))
        if all(p in texto for p in palavras):
            resultado.append((iid, valores))
    return resultado


def valor_coluna(objeto, coluna: str):
    """Le 'cliente.nome' de forma segura (None no caminho vira vazio)."""
    atual = objeto
    for parte in coluna.split("."):
        if atual is None:
            return ""
        atual = getattr(atual, parte, "")
    return atual


def titulo_coluna(coluna: str) -> str:
    base = coluna.split(".")[0]
    return "ID" if base == "id" else base.replace("_", " ").capitalize()


