"""Sessao do usuario logado e verificacao de permissoes (singleton de processo)."""

from functools import wraps

ACOES = ("ver", "criar", "editar", "excluir")

MODULOS: dict[str, str] = {
    "clientes": "Clientes",
    "veiculos": "Veiculos",
    "fornecedores": "Fornecedores",
    "categorias": "Categorias",
    "marcas": "Marcas",
    "produtos": "Produtos",
    "servicos": "Servicos",
    "estoque": "Estoque",
    "compras": "Compras",
    "vendas": "Vendas",
    "os": "Ordem de Servico",
    "financeiro": "Financeiro",
    "relatorios": "Relatorios",
    "seguranca": "Seguranca e Backup",
    "usuarios": "Usuarios",
    "permissoes": "Permissoes",
    "configuracoes": "Configuracoes",
}

# Nome do item de menu -> chave do modulo de permissao
MENU_PARA_MODULO: dict[str, str | None] = {
    "Dashboard": None,
    "Clientes": "clientes",
    "Veiculos": "veiculos",
    "Fornecedores": "fornecedores",
    "Categorias": "categorias",
    "Marcas": "marcas",
    "Produtos": "produtos",
    "Servicos": "servicos",
    "Estoque": "estoque",
    "Compras": "compras",
    "Vendas": "vendas",
    "Ordem de Servico": "os",
    "Financeiro": "financeiro",
    "Relatorios": "relatorios",
    "Seguranca e Backup": "seguranca",
    "Usuarios": "usuarios",
    "Permissoes": "permissoes",
    "Configuracoes": "configuracoes",
    "Sobre": None,
}


# Em modo somente consulta so se pode ver, exceto fazer backup (os dados do cliente nunca ficam presos).
EXCECOES_SOMENTE_CONSULTA = {("seguranca", "criar")}


class PermissaoNegada(Exception):
    """O usuario logado nao tem permissao para a acao solicitada."""


class _Sessao:
    def __init__(self) -> None:
        # modo somente consulta (licenca/teste vencidos): definido pela aplicacao, nao some ao trocar de usuario
        self.somente_consulta = False
        self.encerrar()

    def iniciar(self, usuario, permissoes: dict[str, set[str]], admin: bool = False) -> None:
        self.usuario_id = usuario.id
        self.usuario_nome = usuario.nome
        self.perfil_nome = usuario.perfil.nome if usuario.perfil else ""
        self.permissoes = {modulo: set(acoes) for modulo, acoes in permissoes.items()}
        self.admin = admin
        self.sistema = False

    def iniciar_sistema(self) -> None:
        """Contexto sem usuario interativo (scripts de homologacao, rotinas internas)."""
        self.encerrar()
        self.sistema = True
        self.usuario_nome = "sistema"

    def encerrar(self) -> None:
        self.usuario_id: int | None = None
        self.usuario_nome = ""
        self.perfil_nome = ""
        self.permissoes: dict[str, set[str]] = {}
        self.admin = False
        self.sistema = False

    @property
    def autenticado(self) -> bool:
        return self.usuario_id is not None or self.sistema

    def pode(self, modulo: str, acao: str) -> bool:
        if self.somente_consulta and acao != "ver" and (modulo, acao) not in EXCECOES_SOMENTE_CONSULTA:
            return False
        if self.sistema or self.admin:
            return True
        return acao in self.permissoes.get(modulo, set())

    def exigir_autenticado(self) -> None:
        if not self.autenticado:
            raise PermissaoNegada("Faca login para continuar.")

    def exigir(self, modulo: str, acao: str) -> None:
        if not self.autenticado:
            raise PermissaoNegada("Faca login para continuar.")
        if not self.pode(modulo, acao):
            if self.somente_consulta and acao != "ver":
                raise PermissaoNegada("Modo somente consulta: licença vencida ou teste encerrado. Ative uma licença em Sobre.")
            raise PermissaoNegada(f"Voce nao tem permissao para '{acao}' em {MODULOS.get(modulo, modulo)}.")


Sessao = _Sessao()


def requer_permissao(modulo: str, acao: str):
    """Decorator para metodos de controller: bloqueia a chamada sem a permissao."""

    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            Sessao.exigir(modulo, acao)
            return func(*args, **kwargs)

        return wrapper

    return decorador
