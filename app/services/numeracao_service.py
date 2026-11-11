from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sequencia import Sequencia

PREFIXOS = {"VENDA": "V", "OS": "OS", "COMPRA": "C"}


class NumeracaoService:
    """Gera numeros sequenciais de documentos (V000001, OS000001, C000001)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def proximo(self, nome: str) -> str:
        if nome not in PREFIXOS:
            raise ValueError(f"Sequencia desconhecida: {nome}.")
        sequencia = self.session.scalar(select(Sequencia).where(Sequencia.nome == nome))
        if sequencia is None:
            sequencia = Sequencia(nome=nome, ultimo_numero=0)
            self.session.add(sequencia)
        sequencia.ultimo_numero += 1
        self.session.flush()
        return f"{PREFIXOS[nome]}{sequencia.ultimo_numero:06d}"
