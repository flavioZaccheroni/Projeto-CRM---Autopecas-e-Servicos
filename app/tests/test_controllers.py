"""Controllers de ponta a ponta: permissoes, auditoria e fluxo completo sobre um banco temporario."""

from datetime import date, timedelta

import pytest

from app.controllers.auth_controller import AuthController
from app.controllers.cadastro_controller import ClienteController, FornecedorController, ProdutoController
from app.controllers.compra_controller import CompraController
from app.controllers.dashboard_controller import DashboardController
from app.controllers.estoque_controller import EstoqueController
from app.controllers.financeiro_controller import FinanceiroController
from app.controllers.relatorio_controller import RelatorioController
from app.controllers.seguranca_controller import SegurancaController
from app.controllers.usuario_controller import PermissaoController, UsuarioController
from app.controllers.venda_controller import VendaController
from app.utils.sessao import PermissaoNegada, Sessao


def _login_admin():
    auth = AuthController()
    usuario = auth.autenticar("admin", "admin123")
    assert usuario is not None and usuario.precisa_trocar_senha
    return auth, usuario


def test_sem_login_nenhum_controller_responde(app_db):
    for acao in (ClienteController().listar, VendaController().listar, FinanceiroController().listar_lancamentos):
        with pytest.raises(PermissaoNegada):
            acao()


def test_login_falho_e_auditado_e_bloqueio_apos_tentativas(app_db):
    auth = AuthController()
    for _ in range(4):
        assert auth.autenticar("admin", "errada") is None
    with pytest.raises(ValueError):
        for _ in range(3):
            auth.autenticar("admin", "errada")
    with pytest.raises(ValueError):  # mesmo com a senha certa a conta segue bloqueada
        auth.autenticar("admin", "admin123")


def test_fluxo_completo_via_controllers_gera_auditoria(app_db):
    auth, admin = _login_admin()
    ClienteController().salvar({"nome": "Ana", "tipo_pessoa": "PF", "cpf_cnpj": "52998224725", "ativo": True})
    FornecedorController().salvar({"razao_social": "Forn SA", "cnpj": "11222333000181", "ativo": True})
    ProdutoController().salvar(
        {"codigo": "P1", "descricao": "Filtro", "unidade": "UN", "preco_custo": "10", "preco_venda": "25", "estoque_minimo": "3", "ativo": True}
    )

    compra = CompraController()
    pedido = compra.criar_compra({"fornecedor_id": 1}, usuario_id=admin.id)
    compra.adicionar_item({"compra_id": pedido.id, "produto_id": 1, "quantidade": "5", "valor_unitario": "10"})
    compra.receber_compra(pedido.id, usuario_id=admin.id, data_vencimento=date.today() + timedelta(days=10), parcelas=1)
    assert EstoqueController().listar()[0].quantidade_atual == 5

    venda = VendaController()
    v = venda.criar_venda({"cliente_id": 1}, usuario_id=admin.id)
    venda.adicionar_item({"venda_id": v.id, "produto_id": 1, "quantidade": "2", "valor_unitario": "25"})
    venda.aprovar_orcamento(v.id)
    venda.finalizar_venda(v.id, usuario_id=admin.id, data_vencimento=date.today(), parcelas=2, forma_pagamento="PIX")
    assert EstoqueController().listar()[0].quantidade_atual == 3
    assert len(FinanceiroController().listar_lancamentos()) == 3  # 1 a pagar + 2 parcelas a receber

    venda.cancelar_venda(v.id, "cliente desistiu", usuario_id=admin.id)
    assert EstoqueController().listar()[0].quantidade_atual == 5  # estorno devolve ao estoque

    acoes = {(a.entidade, a.acao) for a in SegurancaController().listar_auditoria()}
    assert ("clientes", "CRIAR") in acoes and ("login", "ENTRAR") in acoes


def test_perfil_restrito_nao_acessa_financeiro_nem_usuarios(app_db):
    _login_admin()
    perfis = {p.nome: p.id for p in UsuarioController().listar_perfis()}
    UsuarioController().criar("Vera", "vera@x.com", "vera", "Senha1234", perfis["Vendedor"])
    AuthController().encerrar_sessao()

    assert AuthController().autenticar("vera", "Senha1234") is not None
    assert ClienteController().listar() == []
    for acao in (FinanceiroController().listar_lancamentos, UsuarioController().listar, SegurancaController().criar_backup):
        with pytest.raises(PermissaoNegada):
            acao()


def test_matriz_de_permissoes_e_dashboard_respeitam_o_perfil(app_db):
    _login_admin()
    resumo = DashboardController().resumo()
    assert resumo["vendas"] is not None and resumo["financeiro"] is not None

    perfil = PermissaoController().criar_perfil("Somente vendas")
    PermissaoController().salvar_matriz(perfil.id, {"vendas": {"ver"}})
    UsuarioController().criar("Leo", "leo@x.com", "leo", "Senha1234", perfil.id)
    AuthController().encerrar_sessao()
    AuthController().autenticar("leo", "Senha1234")

    resumo = DashboardController().resumo()
    assert resumo["vendas"] is not None
    assert resumo["financeiro"] is None and resumo["estoque_baixo"] is None


def test_relatorios_via_controller(app_db, tmp_path, monkeypatch):
    from app.services import relatorio_service

    monkeypatch.setattr(relatorio_service, "ROOT_DIR", tmp_path)
    _login_admin()
    pdf = RelatorioController().gerar("estoque", "pdf")
    assert pdf.read_bytes().startswith(b"%PDF")
    xlsx = RelatorioController().gerar("vendas", "xlsx")
    assert xlsx.suffix == ".xlsx" and xlsx.stat().st_size > 0
    assert Sessao.pode("relatorios", "ver")


def test_os_financeiro_e_backup_via_controllers(app_db, tmp_path, monkeypatch):
    from app.controllers.cadastro_controller import VeiculoController
    from app.controllers.lookup_controller import LookupController
    from app.controllers.os_controller import OrdemServicoController
    from app.services import seguranca_service

    _, admin = _login_admin()
    ClienteController().salvar({"nome": "Bia", "tipo_pessoa": "PF", "cpf_cnpj": "52998224725", "ativo": True})
    VeiculoController().salvar({"cliente_id": 1, "placa": "ABC1D23", "marca": "VW", "modelo": "Gol"})
    assert LookupController().veiculos(1)[0][1].startswith("ABC1D23")

    os_ctrl = OrdemServicoController()
    ordem = os_ctrl.abrir_os({"cliente_id": 1, "veiculo_id": 1, "defeito_relatado": "barulho"}, usuario_id=admin.id)
    os_ctrl.adicionar_item({"os_id": ordem.id, "tipo": "SERVICO", "descricao": "Revisao", "quantidade": "1", "valor_unitario": "150"})
    assert len(os_ctrl.listar_itens(ordem.id)) == 1
    os_ctrl.finalizar_os(ordem.id, usuario_id=admin.id, data_vencimento=date.today(), parcelas=1, forma_pagamento="PIX")
    assert os_ctrl.imprimir_os(ordem.id).read_bytes().startswith(b"%PDF")

    financeiro = FinanceiroController()
    lancamento = financeiro.listar_lancamentos()[0]
    financeiro.baixar_lancamento(lancamento.id, "PIX", usuario_id=admin.id)
    assert financeiro.resumo_fluxo()["saldo_caixa"] == 150
    financeiro.estornar_lancamento(lancamento.id, usuario_id=admin.id)
    assert financeiro.resumo_fluxo()["saldo_caixa"] == 0

    monkeypatch.setattr(seguranca_service, "BACKUPS_DIR", tmp_path)
    seguranca = SegurancaController()
    seguranca.salvar_configuracao("empresa", "Oficina X", usuario_id=admin.id)
    assert any(c.chave == "empresa" for c in seguranca.listar_configuracoes())


def test_backup_automatico_pelo_controller(app_db, monkeypatch, tmp_path):
    from app.config import settings  # noqa: F401
    from app.services import seguranca_service

    monkeypatch.setattr(seguranca_service, "BACKUPS_DIR", tmp_path / "bk")
    banco = tmp_path / "teste.db"
    monkeypatch.setattr(seguranca_service.BackupService.__init__, "__defaults__", (banco, tmp_path / "bk"))
    _, admin = _login_admin()
    controller = SegurancaController()

    situacao = controller.situacao_backup()
    assert situacao["auto"] is True and situacao["dias"] is None

    primeiro = controller.executar_backup_automatico("abrir")
    assert primeiro["criado"] is True and primeiro["arquivo"].name.startswith("auto_")
    assert controller.situacao_backup()["dias"] == 0

    controller.salvar_configuracao("backup.auto", "nao", usuario_id=admin.id)
    assert controller.executar_backup_automatico("sair") == {"criado": False, "arquivo": None, "aviso": None}


def _venda_de_100(admin):
    ClienteController().salvar({"nome": "Ana", "tipo_pessoa": "PF", "cpf_cnpj": "52998224725", "ativo": True})
    ProdutoController().salvar(
        {"codigo": "P1", "descricao": "Filtro", "unidade": "UN", "preco_custo": "10", "preco_venda": "100", "estoque_minimo": "0", "ativo": True}
    )
    EstoqueController().movimentar({"produto_id": 1, "tipo": "ENTRADA", "quantidade": "5"}, usuario_id=admin.id)
    venda = VendaController()
    v = venda.criar_venda({"cliente_id": 1}, usuario_id=admin.id)
    venda.adicionar_item({"venda_id": v.id, "produto_id": 1, "quantidade": "1", "valor_unitario": "100"})
    return venda, v


def test_desconto_e_acrescimo_refletem_no_total_e_no_financeiro(app_db):
    from decimal import Decimal

    _, admin = _login_admin()
    venda, v = _venda_de_100(admin)
    venda.definir_desconto(v.id, "30%", "R$ 5,50")  # administrador: sem limite
    atual = next(x for x in venda.listar() if x.id == v.id)
    assert (atual.desconto, atual.acrescimo, atual.valor_total) == (Decimal("30.00"), Decimal("5.50"), Decimal("75.50"))
    venda.adicionar_item({"venda_id": v.id, "produto_id": 1, "quantidade": "1", "valor_unitario": "100"})
    assert next(x for x in venda.listar() if x.id == v.id).valor_total == Decimal("175.50")
    venda.aprovar_orcamento(v.id)
    venda.finalizar_venda(v.id, usuario_id=admin.id, data_vencimento=date.today(), parcelas=1, forma_pagamento="PIX")
    lancamento = [x for x in FinanceiroController().listar_lancamentos() if x.tipo == "RECEBER"][0]
    assert lancamento.valor == Decimal("175.50")
    with pytest.raises(ValueError):  # finalizada nao aceita mais ajuste
        venda.definir_desconto(v.id, "1", "")
    assert any(a.acao == "DESCONTO" for a in SegurancaController().listar_auditoria())


def test_desconto_invalido_e_limitado_ao_subtotal(app_db):
    _, admin = _login_admin()
    venda, v = _venda_de_100(admin)
    for texto in ("150", "-5", "abc", "120%"):
        with pytest.raises(ValueError):
            venda.definir_desconto(v.id, texto, "")
    venda.definir_desconto(v.id, "100", "")
    assert next(x for x in venda.listar() if x.id == v.id).valor_total == 0  # nunca negativo
    venda.definir_desconto(v.id, "", "")  # vazio zera
    assert next(x for x in venda.listar() if x.id == v.id).valor_total == 100


def test_vendedor_respeita_limite_de_desconto_e_admin_ajusta_o_limite(app_db):
    _, admin = _login_admin()
    venda, v = _venda_de_100(admin)
    perfis = {p.nome: p.id for p in UsuarioController().listar_perfis()}
    UsuarioController().criar("Vera", "vera@x.com", "vera", "Senha1234", perfis["Vendedor"])
    SegurancaController().salvar_configuracao("desconto.max_percentual", "15")
    AuthController().encerrar_sessao()
    assert AuthController().autenticar("vera", "Senha1234") is not None
    venda.definir_desconto(v.id, "15%", "")  # no limite
    with pytest.raises(ValueError, match="limite"):
        venda.definir_desconto(v.id, "16", "")


def test_pdf_de_orcamento_e_de_venda_finalizada(app_db, tmp_path, monkeypatch):
    from app.controllers import venda_controller

    monkeypatch.setattr(venda_controller, "ROOT_DIR", tmp_path)
    _, admin = _login_admin()
    venda, v = _venda_de_100(admin)
    venda.definir_desconto(v.id, "10", "")
    orcamento = venda.imprimir_venda(v.id)
    assert orcamento.name.startswith("orcamento_") and orcamento.read_bytes().startswith(b"%PDF")
    assert b"ORCAMENTO V000001" in orcamento.read_bytes() and b"Desconto" in orcamento.read_bytes()
    venda.aprovar_orcamento(v.id)
    venda.finalizar_venda(v.id, usuario_id=admin.id, data_vencimento=date.today(), parcelas=1, forma_pagamento="PIX")
    comprovante = venda.imprimir_venda(v.id)
    assert comprovante.name.startswith("venda_")
    conteudo = comprovante.read_bytes()
    assert b"COMPROVANTE DE VENDA V000001" in conteudo and b"Recebemos de Ana" in conteudo
    assert any(a.acao == "IMPRIMIR" for a in SegurancaController().listar_auditoria())


def test_pdf_usa_dados_da_empresa_e_logo(app_db, tmp_path, monkeypatch):
    from app.controllers import venda_controller
    from app.reports import venda_pdf
    from app.utils import logo as logo_mod

    monkeypatch.setattr(venda_controller, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(logo_mod, "DATA_DIR", tmp_path / "dados")
    monkeypatch.setattr(venda_pdf, "caminho_logo", lambda: logo_mod.caminho_logo(tmp_path / "dados"))
    _, admin = _login_admin()
    seg = SegurancaController()
    seg.salvar_configuracao("empresa.nome", "Auto Pecas Teste")
    seg.salvar_configuracao("empresa.cnpj", "11.222.333/0001-81")
    seg.salvar_configuracao("empresa.cidade", "Campinas")
    venda, v = _venda_de_100(admin)
    conteudo = venda.imprimir_venda(v.id).read_bytes()
    assert b"Auto Pecas Teste" in conteudo and b"CNPJ: 11.222.333/0001-81" in conteudo and b"Campinas" in conteudo
    assert b"/Subtype /Image" not in conteudo
