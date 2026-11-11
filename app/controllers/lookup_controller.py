from app.database.database import SessionLocal
from app.services.lookup_service import LookupService
from app.utils.sessao import Sessao


class LookupController:
    """Listas para seletores. Exige apenas usuario autenticado: so expoe id e nome/rotulo."""

    def _listar(self, nome: str, *args):
        Sessao.exigir_autenticado()
        with SessionLocal() as session:
            return getattr(LookupService(session), nome)(*args)

    def clientes(self):
        return self._listar("clientes")

    def fornecedores(self):
        return self._listar("fornecedores")

    def produtos(self):
        return self._listar("produtos")

    def veiculos(self, cliente_id=None):
        return self._listar("veiculos", cliente_id)

    def categorias(self):
        return self._listar("categorias")

    def marcas(self):
        return self._listar("marcas")
