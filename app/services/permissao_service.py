from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.perfil import Perfil
from app.models.permissao import Permissao
from app.utils.sessao import ACOES, MODULOS
from app.utils.validators import validar_obrigatorio

PERFIL_ADMIN = "Administrador"

# Perfis criados na instalacao: nome -> (descricao, {modulo: acoes})
_TUDO = set(ACOES)
_LEITURA = {"ver"}
_EDICAO = {"ver", "criar", "editar"}

PERFIS_PADRAO: dict[str, tuple[str, dict[str, set[str]]]] = {
    "Vendedor": (
        "Atendimento, orcamentos, vendas e ordens de servico",
        {
            "clientes": _EDICAO, "veiculos": _EDICAO, "produtos": _LEITURA, "servicos": _LEITURA, "estoque": _LEITURA,
            "vendas": _EDICAO, "os": _EDICAO, "relatorios": _LEITURA,
        },
    ),
    "Estoquista": (
        "Produtos, estoque e compras",
        {
            "produtos": _EDICAO, "categorias": _EDICAO, "marcas": _EDICAO, "fornecedores": _LEITURA,
            "estoque": _EDICAO, "compras": _EDICAO,
        },
    ),
    "Financeiro": (
        "Contas a pagar/receber, caixa e relatorios",
        {
            "financeiro": _TUDO, "relatorios": _LEITURA, "clientes": _LEITURA, "fornecedores": _LEITURA,
            "vendas": _LEITURA, "compras": _LEITURA, "os": _LEITURA,
        },
    ),
}


class PermissaoService:
    def __init__(self, session: Session) -> None:
        self.session = session

    # -- perfis -----------------------------------------------------------------------------
    def listar_perfis(self) -> list[Perfil]:
        return list(self.session.scalars(select(Perfil).order_by(Perfil.nome)))

    def buscar_perfil(self, perfil_id: int) -> Perfil | None:
        return self.session.get(Perfil, int(perfil_id))

    def criar_perfil(self, nome: str, descricao: str | None = None) -> Perfil:
        validar_obrigatorio(nome, "Nome do perfil")
        nome = nome.strip()
        if self.session.scalar(select(Perfil).where(Perfil.nome == nome)):
            raise ValueError("Perfil ja cadastrado.")
        perfil = Perfil(nome=nome, descricao=(descricao or "").strip() or None, ativo=True)
        self.session.add(perfil)
        self.session.flush()
        return perfil

    # -- permissoes -------------------------------------------------------------------------
    def carregar(self, perfil_id: int) -> dict[str, set[str]]:
        perfil = self.buscar_perfil(perfil_id)
        if perfil is None:
            return {}
        if perfil.nome == PERFIL_ADMIN:
            return {modulo: set(ACOES) for modulo in MODULOS}
        resultado: dict[str, set[str]] = {}
        for permissao in perfil.permissoes:
            acoes = {
                acao
                for acao, marcado in (
                    ("ver", permissao.pode_ver),
                    ("criar", permissao.pode_criar),
                    ("editar", permissao.pode_editar),
                    ("excluir", permissao.pode_excluir),
                )
                if marcado
            }
            resultado[permissao.modulo] = acoes
        return resultado

    def salvar_matriz(self, perfil_id: int, matriz: dict[str, set[str]]) -> None:
        perfil = self.buscar_perfil(perfil_id)
        if perfil is None:
            raise ValueError("Perfil nao encontrado.")
        if perfil.nome == PERFIL_ADMIN:
            raise ValueError("O perfil Administrador sempre tem acesso total e nao pode ser alterado.")
        existentes = {permissao.modulo: permissao for permissao in perfil.permissoes}
        for modulo in MODULOS:
            acoes = matriz.get(modulo, set())
            permissao = existentes.get(modulo)
            if permissao is None:
                permissao = Permissao(perfil_id=perfil.id, modulo=modulo)
                self.session.add(permissao)
            permissao.pode_ver = "ver" in acoes
            permissao.pode_criar = "criar" in acoes
            permissao.pode_editar = "editar" in acoes
            permissao.pode_excluir = "excluir" in acoes
        self.session.flush()
        self.session.expire(perfil, ["permissoes"])

    # -- instalacao -------------------------------------------------------------------------
    def garantir_perfis_padrao(self) -> None:
        """Cria Administrador (acesso total) e os perfis padrao que ainda nao existem."""
        admin = self.session.scalar(select(Perfil).where(Perfil.nome == PERFIL_ADMIN))
        if admin is None:
            admin = Perfil(nome=PERFIL_ADMIN, descricao="Acesso total ao sistema", ativo=True)
            self.session.add(admin)
            self.session.flush()
        # O Administrador e tratado por codigo; as linhas sao mantidas para consulta/relatorio.
        existentes = {permissao.modulo: permissao for permissao in admin.permissoes}
        for modulo in MODULOS:
            permissao = existentes.get(modulo) or Permissao(perfil_id=admin.id, modulo=modulo)
            permissao.pode_ver = permissao.pode_criar = permissao.pode_editar = permissao.pode_excluir = True
            self.session.add(permissao)
        self.session.flush()
        self.session.expire(admin, ["permissoes"])

        for nome, (descricao, matriz) in PERFIS_PADRAO.items():
            if self.session.scalar(select(Perfil).where(Perfil.nome == nome)) is None:
                perfil = Perfil(nome=nome, descricao=descricao, ativo=True)
                self.session.add(perfil)
                self.session.flush()
                self.salvar_matriz(perfil.id, matriz)
        self.session.flush()
