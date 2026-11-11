from datetime import timedelta

import pytest

from app.models.perfil import Perfil
from app.repositories.usuario_repository import UsuarioRepository
from app.services.auth_service import MAX_TENTATIVAS, AuthService
from app.services.permissao_service import PERFIL_ADMIN, PermissaoService
from app.services.usuario_service import UsuarioService
from app.utils.datas import agora
from app.utils.sessao import PermissaoNegada, Sessao, requer_permissao


@pytest.fixture(autouse=True)
def _limpar_sessao():
    Sessao.encerrar()
    yield
    Sessao.encerrar()


def _perfis(session):
    servico = PermissaoService(session)
    servico.garantir_perfis_padrao()
    return servico, {perfil.nome: perfil for perfil in servico.listar_perfis()}


def test_perfis_padrao_sao_criados_e_sao_idempotentes(session):
    servico, perfis = _perfis(session)
    servico.garantir_perfis_padrao()

    assert {"Administrador", "Vendedor", "Estoquista", "Financeiro"} <= set(perfis)
    assert len(servico.listar_perfis()) == 4


def test_administrador_tem_acesso_total(session):
    servico, perfis = _perfis(session)

    matriz = servico.carregar(perfis[PERFIL_ADMIN].id)

    assert matriz["financeiro"] == {"ver", "criar", "editar", "excluir"}
    assert matriz["permissoes"] == {"ver", "criar", "editar", "excluir"}


def test_vendedor_nao_acessa_financeiro_nem_cancela_venda(session):
    servico, perfis = _perfis(session)

    matriz = servico.carregar(perfis["Vendedor"].id)

    assert "financeiro" not in matriz or not matriz["financeiro"]
    assert "excluir" not in matriz["vendas"]
    assert {"ver", "criar", "editar"} <= matriz["vendas"]


def test_salvar_matriz_persiste_e_admin_e_imutavel(session):
    servico, perfis = _perfis(session)
    perfil = servico.criar_perfil("Gerente")

    servico.salvar_matriz(perfil.id, {"relatorios": {"ver"}, "vendas": {"ver", "excluir"}})

    matriz = servico.carregar(perfil.id)
    assert matriz["relatorios"] == {"ver"}
    assert matriz["vendas"] == {"ver", "excluir"}
    assert matriz["estoque"] == set()
    with pytest.raises(ValueError, match="Administrador"):
        servico.salvar_matriz(perfis[PERFIL_ADMIN].id, {})


def test_criar_perfil_duplicado_falha(session):
    servico, _ = _perfis(session)
    with pytest.raises(ValueError, match="ja cadastrado"):
        servico.criar_perfil("Vendedor")


class _Usuario:
    id = 7
    nome = "Joao"
    perfil = Perfil(nome="Vendedor")


def test_sessao_nega_sem_login_e_sem_permissao():
    class Controller:
        @requer_permissao("vendas", "criar")
        def criar(self):
            return "ok"

    with pytest.raises(PermissaoNegada, match="login"):
        Controller().criar()

    Sessao.iniciar(_Usuario(), {"vendas": {"ver"}})
    with pytest.raises(PermissaoNegada, match="permissao"):
        Controller().criar()

    Sessao.iniciar(_Usuario(), {"vendas": {"ver", "criar"}})
    assert Controller().criar() == "ok"


def test_sessao_admin_e_modo_sistema_passam_em_tudo():
    Sessao.iniciar(_Usuario(), {}, admin=True)
    assert Sessao.pode("usuarios", "excluir")
    Sessao.iniciar_sistema()
    assert Sessao.pode("seguranca", "excluir")


def _usuario(session, perfil_id, login="maria", senha="Senha1234"):
    return UsuarioService(UsuarioRepository(session)).criar_usuario(
        "Maria", f"{login}@teste.com", login, senha, perfil_id
    )


def test_login_correto_zera_tentativas(session):
    _, perfis = _perfis(session)
    usuario = _usuario(session, perfis["Vendedor"].id)
    auth = AuthService(UsuarioRepository(session))
    assert auth.autenticar("maria", "errada1") is None
    assert usuario.tentativas_falhas == 1

    assert auth.autenticar("maria", "Senha1234") is usuario
    assert usuario.tentativas_falhas == 0


def test_conta_bloqueia_apos_tentativas_erradas(session):
    _, perfis = _perfis(session)
    usuario = _usuario(session, perfis["Vendedor"].id)
    auth = AuthService(UsuarioRepository(session))

    for _ in range(MAX_TENTATIVAS):
        assert auth.autenticar("maria", "errada1") is None

    assert usuario.bloqueado_ate is not None
    with pytest.raises(ValueError, match="bloqueada"):
        auth.autenticar("maria", "Senha1234")  # mesmo com a senha certa

    usuario.bloqueado_ate = agora() - timedelta(minutes=1)  # bloqueio expirou
    assert auth.autenticar("maria", "Senha1234") is usuario


def test_usuario_inativo_nao_autentica(session):
    _, perfis = _perfis(session)
    usuario = _usuario(session, perfis["Vendedor"].id)
    usuario.ativo = False
    assert AuthService(UsuarioRepository(session)).autenticar("maria", "Senha1234") is None


def test_alterar_senha_exige_atual_forca_regras_e_limpa_flag(session):
    _, perfis = _perfis(session)
    servico = UsuarioService(UsuarioRepository(session))
    usuario = servico.criar_usuario("Ana", "ana@teste.com", "ana", "Inicial123", perfis["Vendedor"].id, precisa_trocar_senha=True)

    with pytest.raises(ValueError, match="atual incorreta"):
        servico.alterar_senha(usuario.id, "xxxx1234", "NovaSenha1")
    with pytest.raises(ValueError, match="8 caracteres"):
        servico.alterar_senha(usuario.id, "Inicial123", "abc1")
    with pytest.raises(ValueError, match="diferente"):
        servico.alterar_senha(usuario.id, "Inicial123", "Inicial123")

    servico.alterar_senha(usuario.id, "Inicial123", "NovaSenha1")
    assert usuario.precisa_trocar_senha is False
    assert AuthService(UsuarioRepository(session)).autenticar("ana", "NovaSenha1") is usuario


def test_redefinir_senha_exige_nova_troca_e_desbloqueia(session):
    _, perfis = _perfis(session)
    servico = UsuarioService(UsuarioRepository(session))
    usuario = _usuario(session, perfis["Vendedor"].id)
    usuario.bloqueado_ate = agora() + timedelta(minutes=5)

    servico.redefinir_senha(usuario.id, "Temporaria9")

    assert usuario.precisa_trocar_senha is True
    assert usuario.bloqueado_ate is None


def test_nao_permite_remover_ultimo_administrador(session):
    _, perfis = _perfis(session)
    servico = UsuarioService(UsuarioRepository(session))
    admin = servico.criar_usuario("Admin", "admin@teste.com", "admin", "Admin1234", perfis[PERFIL_ADMIN].id)

    with pytest.raises(ValueError, match="Administrador ativo"):
        servico.atualizar_usuario(admin.id, "Admin", "admin@teste.com", perfis["Vendedor"].id, True)
    with pytest.raises(ValueError, match="Administrador ativo"):
        servico.atualizar_usuario(admin.id, "Admin", "admin@teste.com", perfis[PERFIL_ADMIN].id, False)

    outro = servico.criar_usuario("Admin2", "admin2@teste.com", "admin2", "Admin1234", perfis[PERFIL_ADMIN].id)
    servico.atualizar_usuario(admin.id, "Admin", "admin@teste.com", perfis["Vendedor"].id, True)  # agora pode
    assert outro.ativo
