import json
from datetime import date, timedelta

import pytest

from app.controllers.licenca_controller import CHAVE_PRIMEIRO_USO, LicencaController
from app.services import licenca_service as ls
from app.utils import ed25519
from app.utils.sessao import PermissaoNegada, Sessao

SEGREDO = bytes(range(1, 33))
PUBLICA = ed25519.chave_publica(SEGREDO)
HOJE = date(2026, 11, 13)


def _licenca(validade=date(2027, 11, 13), maquina=None, cliente="Auto Pecas Exemplo"):
    texto = ls.montar_licenca(SEGREDO, cliente, "Anual", validade, HOJE, "11.222.333/0001-81", maquina)
    return ls.ler_licenca(texto, PUBLICA)


# -- formato e assinatura -------------------------------------------------------------------
def test_licenca_assinada_e_lida_de_volta():
    dados = _licenca()
    assert dados["cliente"] == "Auto Pecas Exemplo" and dados["validade"] == "2027-11-13" and dados["maquina"] is None
    assert _licenca(validade=None)["validade"] is None


def test_licenca_adulterada_ou_de_outro_emissor_e_recusada():
    texto = ls.montar_licenca(SEGREDO, "Cliente", "Anual", date(2027, 1, 1), HOJE)
    bruto = json.loads(texto)
    bruto["dados"]["validade"] = "2099-01-01"  # estende a validade sem assinar de novo
    with pytest.raises(ls.LicencaInvalida, match="assinatura"):
        ls.ler_licenca(json.dumps(bruto), PUBLICA)
    outra = ed25519.chave_publica(bytes(range(40, 72)))
    with pytest.raises(ls.LicencaInvalida, match="assinatura"):
        ls.ler_licenca(texto, outra)
    for lixo in ("", "nao e json", "[]", '{"dados": {}}', '{"dados": {}, "assinatura": "@@"}'):
        with pytest.raises(ls.LicencaInvalida):
            ls.ler_licenca(lixo, PUBLICA)


def test_chave_publica_embutida_tem_32_bytes():
    assert len(bytes.fromhex(ls.CHAVE_PUBLICA_HEX)) == 32


# -- avaliacao ------------------------------------------------------------------------------
def test_teste_de_30_dias_e_depois_somente_consulta():
    s = ls.avaliar(HOJE, None, HOJE, "AAAA-BBBB-CCCC")
    assert s.estado == "teste" and s.dias_restantes == 30 and not s.somente_consulta
    assert ls.avaliar(HOJE + timedelta(days=29), None, HOJE, "X").dias_restantes == 1
    fim = ls.avaliar(HOJE + timedelta(days=30), None, HOJE, "X")
    assert fim.estado == "teste_encerrado" and fim.somente_consulta
    assert "backup" in fim.detalhe  # explica que os dados continuam acessiveis


def test_licenca_valida_vencimento_e_aviso():
    lic = _licenca(validade=date(2026, 11, 20))
    s = ls.avaliar(HOJE, lic, HOJE - timedelta(days=400), "X")
    assert s.estado == "licenciado" and s.dias_restantes == 7 and s.precisa_aviso and "20/11/2026" in s.titulo
    assert ls.avaliar(date(2026, 11, 20), lic, HOJE, "X").estado == "licenciado"  # vale ate o proprio dia
    vencida = ls.avaliar(date(2026, 11, 21), lic, HOJE, "X")
    assert vencida.estado == "licenca_expirada" and vencida.somente_consulta
    assert not ls.avaliar(HOJE, _licenca(), HOJE, "X").precisa_aviso
    assert ls.avaliar(HOJE, _licenca(validade=None), HOJE - timedelta(days=999), "X").dias_restantes is None


def test_licenca_vinculada_a_maquina():
    lic = _licenca(maquina="abcd-1234-ef56")
    assert ls.avaliar(HOJE, lic, HOJE, "ABCD-1234-EF56").estado == "licenciado"
    outra = ls.avaliar(HOJE, lic, HOJE - timedelta(days=100), "9999-9999-9999")
    assert outra.estado == "teste_encerrado" and "outro computador" in outra.erro


# -- controller: marcador, relogio e ativacao -----------------------------------------------
def _controller(tmp_path):
    return LicencaController(arquivo_licenca=tmp_path / "licenca.erplic", marcador=tmp_path / ".erp_inicio")


def test_primeiro_uso_e_gravado_e_nao_reinicia_apagando_um_dos_lugares(app_db, tmp_path):
    ctrl = _controller(tmp_path)
    assert ctrl.situacao(HOJE).dias_restantes == 30
    assert (tmp_path / ".erp_inicio").read_text().split()[0] == HOJE.isoformat()
    depois = HOJE + timedelta(days=20)
    assert ctrl.situacao(depois).dias_restantes == 10
    # apagar o marcador nao reinicia: o banco lembra
    (tmp_path / ".erp_inicio").unlink()
    assert ctrl.situacao(depois).dias_restantes == 10
    # apagar o registro do banco tambem nao: o marcador lembra
    from app.database.database import SessionLocal
    from app.repositories.seguranca_repository import ConfiguracaoRepository
    from app.services.seguranca_service import ConfiguracaoService

    with SessionLocal() as session:
        ConfiguracaoService(ConfiguracaoRepository(session)).salvar(CHAVE_PRIMEIRO_USO, "")
        session.commit()
    assert ctrl.situacao(depois).dias_restantes == 10


def test_voltar_o_relogio_nao_devolve_dias_de_teste(app_db, tmp_path):
    ctrl = _controller(tmp_path)
    ctrl.situacao(HOJE)
    assert ctrl.situacao(HOJE + timedelta(days=40)).estado == "teste_encerrado"
    assert ctrl.situacao(HOJE).estado == "teste_encerrado"  # relogio de volta: continua encerrado


def test_ativar_licenca_libera_o_sistema_e_audita(app_db, tmp_path, monkeypatch):
    from app.controllers.auth_controller import AuthController
    from app.controllers.seguranca_controller import SegurancaController

    monkeypatch.setattr(ls, "CHAVE_PUBLICA_HEX", PUBLICA.hex())
    AuthController().autenticar("admin", "admin123")
    ctrl = _controller(tmp_path)
    ctrl.situacao(date.today() - timedelta(days=90))  # teste ja vencido
    try:
        assert ctrl.aplicar_restricao().somente_consulta and Sessao.somente_consulta
        arquivo = tmp_path / "nova.erplic"
        validade = date.today() + timedelta(days=365)
        arquivo.write_text(ls.montar_licenca(SEGREDO, "Auto Pecas Exemplo", "Anual", validade, date.today()), encoding="utf-8")
        situacao = ctrl.ativar(str(arquivo))
        assert situacao.estado == "licenciado" and not Sessao.somente_consulta
        assert (tmp_path / "licenca.erplic").is_file()
        assert any(a.acao == "ATIVAR" for a in SegurancaController().listar_auditoria())
    finally:
        Sessao.somente_consulta = False


def test_ativar_recusa_arquivo_ruim_vencida_ou_de_outro_pc(app_db, tmp_path, monkeypatch):
    from app.controllers.auth_controller import AuthController

    monkeypatch.setattr(ls, "CHAVE_PUBLICA_HEX", PUBLICA.hex())
    AuthController().autenticar("admin", "admin123")
    ctrl = _controller(tmp_path)

    def gravar(validade, maquina=None):
        arquivo = tmp_path / "x.erplic"
        arquivo.write_text(ls.montar_licenca(SEGREDO, "Cliente", "Anual", validade, date.today(), maquina=maquina), encoding="utf-8")
        return str(arquivo)

    lixo = tmp_path / "lixo.erplic"
    lixo.write_text("oi")
    with pytest.raises(ls.LicencaInvalida):
        ctrl.ativar(str(lixo))
    with pytest.raises(ls.LicencaInvalida, match="venceu"):
        ctrl.ativar(gravar(date.today() - timedelta(days=1)))
    with pytest.raises(ls.LicencaInvalida, match="outro computador"):
        ctrl.ativar(gravar(None, "0000-0000-0000"))
    assert not (tmp_path / "licenca.erplic").exists()  # nada foi gravado


def test_ativar_exige_login(app_db, tmp_path):
    with pytest.raises(PermissaoNegada):
        _controller(tmp_path).ativar(str(tmp_path / "x.erplic"))


# -- sessao: modo somente consulta ----------------------------------------------------------
def test_somente_consulta_bloqueia_escrita_mas_mantem_consulta_e_backup(app_db):
    from app.controllers.auth_controller import AuthController
    from app.controllers.cadastro_controller import ClienteController
    from app.controllers.seguranca_controller import SegurancaController
    from app.controllers.venda_controller import VendaController

    AuthController().autenticar("admin", "admin123")  # administrador tem tudo, mas nao escreve em consulta
    try:
        Sessao.somente_consulta = True
        assert Sessao.pode("clientes", "ver") and Sessao.pode("seguranca", "criar")
        assert not Sessao.pode("clientes", "criar") and not Sessao.pode("vendas", "editar") and not Sessao.pode("os", "excluir")
        assert ClienteController().listar() == [] and VendaController().listar() == []
        with pytest.raises(PermissaoNegada, match="somente consulta"):
            ClienteController().salvar({"nome": "Ana", "tipo_pessoa": "PF", "cpf_cnpj": "52998224725", "ativo": True})
        assert SegurancaController().criar_backup().exists()  # backup continua permitido
    finally:
        Sessao.somente_consulta = False
    assert Sessao.pode("clientes", "criar")
