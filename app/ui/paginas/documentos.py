"""Vendas, Ordens de servico e Compras: lista a esquerda; detalhe a direita com etapas de status, itens editaveis,
inclusao de itens e acoes (aprovar, finalizar, cancelar...) conforme o status e as permissoes."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from PySide6.QtCore import QDate, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from app.controllers.compra_controller import CompraController
from app.controllers.lookup_controller import LookupController
from app.controllers.os_controller import OrdemServicoController
from app.controllers.venda_controller import VendaController
from app.ui.componentes import Botao, Card, Coluna, Emblema, Seletor, TabelaDados, rotulo
from app.ui.formulario import Campo
from app.ui.operacoes import DialogoFormulario, DialogoMotivo, EtapasStatus, TabelaItens, confirmar
from app.ui.paginas.base import Pagina
from app.ui.paginas.cadastros import PainelEdicao
from app.utils.busca import valor_coluna
from app.utils.formatacao import format_value
from app.utils.sessao import Sessao

FORMAS = ["", "DINHEIRO", "PIX", "CARTAO_DEBITO", "CARTAO_CREDITO", "BOLETO", "TRANSFERENCIA"]
LARGURA_DETALHE = 500


@dataclass
class AcaoDoc:
    chave: str  # aprovar | recusar | finalizar | cancelar | pdf
    rotulo: str
    variante: str
    icone: str
    estados: set[str]  # status em que a acao faz sentido
    permissao: str  # ver | criar | editar | excluir
    metodo: str  # metodo do controller
    pede: str = ""  # "" | motivo | finalizacao
    sucesso: str = ""
    pergunta: str = ""


@dataclass
class EspecDoc:
    chave: str
    singular: str
    plural: str
    artigo: str  # "a" venda / "o" pedido
    descricao: str
    controller: Callable
    modulo: str
    prefixo_id: str  # chave do id no dicionario de item (venda_id, os_id, compra_id)
    metodo_criar: str
    etapas: list[tuple[str, str]]
    posicao: dict[str, int]  # status -> indice da etapa atual
    terminais: dict[str, str]  # status fora do fluxo -> rotulo
    editaveis: set[str]
    tons: dict[str, str]
    colunas: list[tuple[str, Coluna]]
    resumo: list[tuple[str, str]]
    campos_novo: list[Campo]
    colunas_itens: list[tuple[str, str, str]]
    acoes: list[AcaoDoc]
    sugere_preco: bool = True
    com_tipo_item: bool = False
    usa_forma: bool = True
    com_ajuste: bool = False  # desconto/acrescimo (vendas e OS)
    rotulo_valor_item: str = "Valor unitário"
    curto: str = ""  # nome curto no botao 'Nova ...'
    extras: dict = field(default_factory=dict)


def _lookups() -> LookupController:
    return LookupController()


ESPECS_DOC: dict[str, EspecDoc] = {
    "Vendas": EspecDoc(
        chave="Vendas", singular="venda", plural="vendas", artigo="a",
        descricao="Orçamento → aprovação → venda, com baixa de estoque, parcelamento e contas a receber.",
        controller=VendaController, com_ajuste=True, modulo="vendas", prefixo_id="venda_id", metodo_criar="criar_venda",
        etapas=[("ORCAMENTO", "Orçamento"), ("APROVADO", "Aprovado"), ("FINALIZADA", "Finalizada")],
        posicao={"ORCAMENTO": 0, "APROVADO": 1, "FINALIZADA": 2},
        terminais={"RECUSADO": "Recusado", "CANCELADA": "Cancelada"},
        editaveis={"ORCAMENTO", "APROVADO"},
        tons={"ORCAMENTO": "info", "APROVADO": "primaria", "FINALIZADA": "sucesso", "RECUSADO": "perigo", "CANCELADA": "neutro"},
        colunas=[
            ("numero", Coluna("Número", "texto", 100)),
            ("cliente.nome", Coluna("Cliente", "texto", 180)),
            ("data_venda", Coluna("Data", "data", 105)),
            ("status", Coluna("Status", "emblema", 105)),
            ("valor_total", Coluna("Total", "num", 90)),
        ],
        resumo=[("Cliente", "cliente.nome"), ("Data", "data_venda"), ("Parcelas", "parcelas"), ("Pagamento", "forma_pagamento")],
        campos_novo=[Campo("cliente_id", "Cliente", "busca", fonte=lambda: _lookups().clientes(), dica="Buscar cliente…")],
        colunas_itens=[("Produto", "produto.descricao", "texto"), ("Qtd", "quantidade", "quantidade"), ("Unitário", "valor_unitario", "valor"), ("Total", "valor_total", "total")],
        acoes=[
            AcaoDoc("aprovar", "Aprovar", "secundario", "ok", {"ORCAMENTO"}, "editar", "aprovar_orcamento", sucesso="Orçamento aprovado."),
            AcaoDoc("recusar", "Recusar", "secundario", "fechar", {"ORCAMENTO", "APROVADO"}, "editar", "recusar_orcamento", pede="motivo", sucesso="Orçamento recusado."),
            AcaoDoc("finalizar", "Finalizar venda", "primario", "ok", {"ORCAMENTO", "APROVADO"}, "editar", "finalizar_venda", pede="finalizacao", sucesso="Venda finalizada: estoque baixado e financeiro gerado."),
            AcaoDoc("cancelar", "Cancelar", "perigo", "lixeira", {"ORCAMENTO", "APROVADO", "FINALIZADA"}, "excluir", "cancelar_venda", pede="motivo", sucesso="Venda cancelada.",
                    pergunta="Estoque e financeiro serão estornados."),
            AcaoDoc("pdf", "PDF", "secundario", "documento", set(), "ver", "imprimir_venda"),
        ],
    ),
    "Ordem de Servico": EspecDoc(
        chave="Ordem de Servico", singular="ordem de serviço", plural="ordens de serviço", artigo="a",
        descricao="Peças e mão de obra por veículo, com finalização (baixa de estoque e financeiro) e PDF.",
        controller=OrdemServicoController, com_ajuste=True, modulo="os", prefixo_id="os_id", metodo_criar="abrir_os",
        etapas=[("ABERTA", "Aberta"), ("EM_ANDAMENTO", "Em andamento"), ("FINALIZADA", "Finalizada")],
        posicao={"ABERTA": 0, "EM_ANDAMENTO": 1, "AGUARDANDO_PECA": 1, "AGUARDANDO_APROVACAO": 1, "FINALIZADA": 2},
        terminais={"CANCELADA": "Cancelada"},
        editaveis={"ABERTA", "EM_ANDAMENTO", "AGUARDANDO_PECA", "AGUARDANDO_APROVACAO"},
        tons={"ABERTA": "info", "EM_ANDAMENTO": "primaria", "AGUARDANDO_PECA": "aviso", "AGUARDANDO_APROVACAO": "aviso", "FINALIZADA": "sucesso", "CANCELADA": "neutro"},
        colunas=[
            ("numero", Coluna("Número", "texto", 100)),
            ("cliente.nome", Coluna("Cliente", "texto", 160)),
            ("veiculo.placa", Coluna("Placa", "texto", 80)),
            ("status", Coluna("Status", "emblema", 150)),
            ("valor_total", Coluna("Total", "num", 90)),
        ],
        resumo=[("Cliente", "cliente.nome"), ("Veículo", "veiculo.placa"), ("Abertura", "data_abertura"), ("Defeito", "defeito_relatado"), ("Diagnóstico", "diagnostico")],
        campos_novo=[
            Campo("cliente_id", "Cliente", "busca", fonte=lambda: _lookups().clientes(), dica="Buscar cliente…"),
            Campo("veiculo_id", "Veículo", "busca", fonte=lambda: [], dica="Escolha o cliente primeiro"),
            Campo("status", "Situação inicial", "lista", ["ABERTA", "EM_ANDAMENTO", "AGUARDANDO_PECA", "AGUARDANDO_APROVACAO"], somente_lista=True, padrao="ABERTA"),
            Campo("defeito_relatado", "Defeito relatado"),
            Campo("diagnostico", "Diagnóstico"),
        ],
        colunas_itens=[("Tipo", "tipo", "curto"), ("Descrição", "descricao", "texto"), ("Qtd", "quantidade", "quantidade"), ("Unitário", "valor_unitario", "valor"), ("Total", "valor_total", "total")],
        acoes=[
            AcaoDoc("finalizar", "Finalizar OS", "primario", "ok", {"ABERTA", "EM_ANDAMENTO", "AGUARDANDO_PECA", "AGUARDANDO_APROVACAO"}, "editar", "finalizar_os", pede="finalizacao", sucesso="OS finalizada: estoque baixado e financeiro gerado."),
            AcaoDoc("cancelar", "Cancelar", "perigo", "lixeira", {"ABERTA", "EM_ANDAMENTO", "AGUARDANDO_PECA", "AGUARDANDO_APROVACAO", "FINALIZADA"}, "excluir", "cancelar_os", pede="motivo", sucesso="OS cancelada.",
                    pergunta="Estoque e financeiro serão estornados."),
            AcaoDoc("pdf", "PDF", "secundario", "documento", set(), "ver", "imprimir_os"),
        ],
        com_tipo_item=True, curto="OS",
    ),
    "Compras": EspecDoc(
        chave="Compras", singular="compra", plural="compras", artigo="a",
        descricao="Pedidos a fornecedores: o recebimento dá entrada no estoque e gera a conta a pagar.",
        controller=CompraController, modulo="compras", prefixo_id="compra_id", metodo_criar="criar_compra",
        etapas=[("ABERTA", "Aberta"), ("RECEBIDA", "Recebida")],
        posicao={"ABERTA": 0, "RECEBIDA": 1},
        terminais={"CANCELADA": "Cancelada"},
        editaveis={"ABERTA"},
        tons={"ABERTA": "info", "RECEBIDA": "sucesso", "CANCELADA": "neutro"},
        colunas=[
            ("numero", Coluna("Número", "texto", 100)),
            ("fornecedor.razao_social", Coluna("Fornecedor", "texto", 190)),
            ("data_compra", Coluna("Data", "data", 105)),
            ("status", Coluna("Status", "emblema", 100)),
            ("valor_total", Coluna("Total", "num", 90)),
        ],
        resumo=[("Fornecedor", "fornecedor.razao_social"), ("Data", "data_compra")],
        campos_novo=[Campo("fornecedor_id", "Fornecedor", "busca", fonte=lambda: _lookups().fornecedores(), dica="Buscar fornecedor…")],
        colunas_itens=[("Produto", "produto.descricao", "texto"), ("Qtd", "quantidade", "quantidade"), ("Custo", "valor_unitario", "valor"), ("Total", "valor_total", "total")],
        acoes=[
            AcaoDoc("finalizar", "Receber compra", "primario", "ok", {"ABERTA"}, "editar", "receber_compra", pede="finalizacao", sucesso="Compra recebida: estoque atualizado e conta a pagar gerada."),
            AcaoDoc("cancelar", "Cancelar", "perigo", "lixeira", {"ABERTA", "RECEBIDA"}, "excluir", "cancelar_compra", pede="motivo", sucesso="Compra cancelada.",
                    pergunta="Se já foi recebida, estoque e financeiro serão revertidos."),
        ],
        sugere_preco=False, usa_forma=False, rotulo_valor_item="Custo unitário",
    ),
}


def _nome_status(status: str) -> str:
    return status.replace("_", " ").capitalize()


class PaginaDocumento(Pagina):
    def __init__(self, espec: EspecDoc, usuario) -> None:
        super().__init__()
        self.espec = espec
        self.usuario = usuario
        self.controller = espec.controller()
        self.subtitulo = espec.descricao
        self.docs: dict[str, object] = {}
        self._id_atual: str | None = None
        self.corpo.setContentsMargins(0, 0, 0, 0)

        raiz = QHBoxLayout()
        raiz.setContentsMargins(28, 24, 28, 24)
        raiz.setSpacing(16)
        self.corpo.addLayout(raiz)

        # ---- lista
        card = Card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        tons_status = {self._nome(k): v for k, v in espec.tons.items()}
        colunas = [c for _, c in espec.colunas]
        for c in colunas:
            if c.tipo == "emblema":
                c.tons = tons_status
        self.tabela = TabelaDados(
            colunas,
            vazio_titulo=f"Nenhuma {espec.singular} ainda" if espec.artigo == "a" else f"Nenhum {espec.singular} ainda",
            vazio_texto=f"Use “Nova {espec.singular}” para registrar a primeira.",
            placeholder=f"Buscar {espec.plural}…",
        )
        self.botao_novo = Botao(f"Nova {espec.curto or espec.singular}", "primario", "mais")
        self.botao_novo.clicked.connect(self.novo)
        self.botao_novo.setEnabled(Sessao.pode(espec.modulo, "criar"))
        self.tabela.adicionar_acao(self.botao_novo)
        self.tabela.selecionado.connect(self._ao_selecionar)
        lay.addWidget(self.tabela)
        raiz.addWidget(card, 1)

        # ---- detalhe
        self.painel = PainelEdicao(LARGURA_DETALHE)
        interno = Card()
        interno.setMinimumWidth(LARGURA_DETALHE)
        interno.setMaximumWidth(LARGURA_DETALHE)
        v = QVBoxLayout(interno)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(10)
        topo = QHBoxLayout()
        self.titulo_doc = rotulo("", "secao")
        self.emblema = Emblema("", "neutro")
        fechar = Botao("", "icone", "fechar")
        fechar.setToolTip("Fechar (Esc)")
        fechar.clicked.connect(self.fechar_detalhe)
        topo.addWidget(self.titulo_doc)
        topo.addWidget(self.emblema)
        topo.addStretch()
        topo.addWidget(fechar)
        v.addLayout(topo)
        self.etapas = EtapasStatus(espec.etapas)
        v.addWidget(self.etapas)
        self.resumo = QGridLayout()
        self.resumo.setHorizontalSpacing(14)
        self.resumo.setVerticalSpacing(2)
        v.addLayout(self.resumo)
        v.addWidget(rotulo("Itens", "rotulo"))
        self.itens = TabelaItens(espec.colunas_itens)
        self.itens.editado.connect(self._editar_item)
        self.itens.remover_pedido.connect(self._remover_item)
        v.addWidget(self.itens, 1)
        self._montar_form_ajuste(v)
        self.total = rotulo("", "kpi")
        self.total.setStyleSheet("font-size: 20px;")
        self.total.setAlignment(Qt.AlignmentFlag.AlignRight)
        v.addWidget(self.total)
        self._montar_form_item(v)
        self.aviso_estado = rotulo("", "mudo", quebra=True)
        v.addWidget(self.aviso_estado)
        self.barra = QHBoxLayout()
        self.barra.setSpacing(8)
        self.botoes: dict[str, Botao] = {}
        for acao in espec.acoes:
            b = Botao(acao.rotulo, acao.variante, acao.icone)
            b.clicked.connect(lambda _=False, a=acao: self.acionar(a))
            self.botoes[acao.chave] = b
        for acao in espec.acoes:
            if acao.chave == "cancelar":
                self.barra.addWidget(self.botoes[acao.chave])
        self.barra.addStretch()
        for acao in espec.acoes:
            if acao.chave != "cancelar":
                self.barra.addWidget(self.botoes[acao.chave])
        v.addLayout(self.barra)
        lp = QVBoxLayout(self.painel)
        lp.setContentsMargins(0, 0, 0, 0)
        lp.addWidget(interno)
        raiz.addWidget(self.painel)

        self.recarregar(avisar=False)

    @staticmethod
    def _nome(status: str) -> str:
        return _nome_status(status)

    # ---- formulario de item (inline)
    def _montar_form_item(self, v: QVBoxLayout) -> None:
        e = self.espec
        self.form_item = QWidget()
        g = QGridLayout(self.form_item)
        g.setContentsMargins(0, 4, 0, 0)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(4)
        linha = 0
        self.tipo_item = None
        if e.com_tipo_item:
            from PySide6.QtWidgets import QComboBox

            self.tipo_item = QComboBox()
            self.tipo_item.addItems(["PECA", "SERVICO"])
            self.tipo_item.currentTextChanged.connect(self._tipo_mudou)
            g.addWidget(rotulo("Tipo", "rotulo"), linha, 0)
            g.addWidget(self.tipo_item, linha + 1, 0)
        self.produto = Seletor(lambda: _lookups().produtos(), "Buscar produto…")
        self.produto.escolhido.connect(self._produto_escolhido)
        g.addWidget(rotulo("Produto" if not e.com_tipo_item else "Produto (peças)", "rotulo"), linha, 1)
        g.addWidget(self.produto, linha + 1, 1)
        g.setColumnStretch(1, 1)
        linha += 2
        self.descricao = QLineEdit()
        if e.com_tipo_item:
            g.addWidget(rotulo("Descrição", "rotulo"), linha, 0, 1, 2)
            g.addWidget(self.descricao, linha + 1, 0, 1, 2)
            linha += 2
        linha_qv = QHBoxLayout()
        linha_qv.setSpacing(10)
        self.qtd = QLineEdit("1")
        self.qtd.setMaximumWidth(90)
        self.valor = QLineEdit()
        self.valor.setMaximumWidth(130)
        self.botao_item = Botao("Adicionar item", "secundario", "mais")
        self.botao_item.clicked.connect(self.adicionar_item)
        for rot, campo in (("Qtd", self.qtd), (e.rotulo_valor_item, self.valor)):
            col = QVBoxLayout()
            col.setSpacing(4)
            col.addWidget(rotulo(rot, "rotulo"))
            col.addWidget(campo)
            linha_qv.addLayout(col)
        linha_qv.addStretch()
        col = QVBoxLayout()
        col.addWidget(QLabel(""))
        col.addWidget(self.botao_item)
        linha_qv.addLayout(col)
        g.addLayout(linha_qv, linha, 0, 1, 2)
        v.addWidget(self.form_item)

    def _montar_form_ajuste(self, v: QVBoxLayout) -> None:
        """Linha 'Desconto / Acréscimo' (R$ ou %), só para documentos com ajuste."""
        self.form_ajuste = QWidget()
        lay = QHBoxLayout(self.form_ajuste)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        self.desconto = QLineEdit()
        self.desconto.setPlaceholderText("R$ ou %")
        self.desconto.setMaximumWidth(110)
        self.acrescimo = QLineEdit()
        self.acrescimo.setPlaceholderText("R$ ou %")
        self.acrescimo.setMaximumWidth(110)
        self.botao_ajuste = Botao("Aplicar", "secundario")
        self.botao_ajuste.clicked.connect(self.aplicar_ajuste)
        for rot, campo in (("Desconto", self.desconto), ("Acréscimo", self.acrescimo)):
            col = QVBoxLayout()
            col.setSpacing(4)
            col.addWidget(rotulo(rot, "rotulo"))
            col.addWidget(campo)
            lay.addLayout(col)
        col = QVBoxLayout()
        col.addWidget(QLabel(""))
        col.addWidget(self.botao_ajuste)
        lay.addLayout(col)
        lay.addStretch()
        self.form_ajuste.setVisible(False)
        v.addWidget(self.form_ajuste)

    def aplicar_ajuste(self) -> None:
        if self._id_atual is None:
            return
        iid = int(self._id_atual)
        desconto, acrescimo = self.desconto.text(), self.acrescimo.text()
        if self.executar(lambda: self.controller.definir_desconto(iid, desconto, acrescimo), "Desconto/acréscimo aplicado."):
            self._atualizar()

    def _tipo_mudou(self, tipo: str) -> None:
        self.produto.setEnabled(tipo == "PECA")
        if tipo != "PECA":
            self.produto.limpar()

    def _produto_escolhido(self, opcao) -> None:
        if not opcao:
            return
        if self.espec.sugere_preco and len(opcao) > 2 and opcao[2]:
            self.valor.setText(str(opcao[2]))
        if self.espec.com_tipo_item and not self.descricao.text():
            self.descricao.setText(str(opcao[1]).split(" - ", 1)[-1])

    # ---- carga
    def recarregar(self, avisar: bool = True) -> None:
        try:
            registros = self.controller.listar()
        except Exception as exc:  # noqa: BLE001
            self.avisar(str(exc), "perigo")
            return
        self.docs = {}
        linhas = []
        for doc in registros:
            iid = str(doc.id)
            self.docs[iid] = doc
            valores = []
            for caminho, _ in self.espec.colunas:
                valor = valor_coluna(doc, caminho)
                if isinstance(valor, datetime):
                    valor = valor.date()
                valores.append(self._nome(valor) if caminho == "status" else valor)
            linhas.append((iid, valores))
        self.tabela.definir_dados(linhas)
        if self._id_atual and self._id_atual in self.docs:
            self.tabela.selecionar(self._id_atual)
            self._mostrar(self._id_atual)
        elif self._id_atual:
            self.fechar_detalhe()
        self.produto.recarregar()

    def focar_busca(self) -> bool:
        return self.tabela.focar_busca()

    # ---- selecao / detalhe
    def _ao_selecionar(self, iid) -> None:
        if iid is None:
            return
        if str(iid) != self._id_atual:
            self._mostrar(str(iid))

    def _mostrar(self, iid: str) -> None:
        doc = self.docs.get(iid)
        if doc is None:
            return
        e = self.espec
        primeira_vez = self._id_atual != iid
        self._id_atual = iid
        status = str(doc.status)
        self.titulo_doc.setText(f"{e.singular.capitalize()} {doc.numero}")
        self.emblema.definir(self._nome(status).upper(), e.tons.get(status, "neutro"))
        terminal = e.terminais.get(status, "")
        posicao = e.posicao.get(status, -1)
        nome_etapa = ""
        if status not in dict(e.etapas) and not terminal:
            nome_etapa = self._nome(status)
        self.etapas.definir(posicao, terminal, nome_etapa)
        # resumo
        while self.resumo.count():
            item = self.resumo.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, (rot, caminho) in enumerate(e.resumo):
            valor = valor_coluna(doc, caminho)
            texto = format_value(valor) or "—"
            if caminho == "data_venda" or caminho == "data_abertura" or caminho == "data_compra":
                texto = format_value(valor)[:16]
            self.resumo.addWidget(rotulo(rot, "mudo"), i, 0, Qt.AlignmentFlag.AlignTop)
            self.resumo.addWidget(rotulo(texto, "rotulo", quebra=True), i, 1)
        self.resumo.setColumnStretch(1, 1)
        # itens
        try:
            itens = self.controller.listar_itens(int(iid))
        except Exception as exc:  # noqa: BLE001
            itens = []
            self.avisar(str(exc), "perigo")
        editavel = status in e.editaveis and Sessao.pode(e.modulo, "editar")
        pode_remover = status in e.editaveis and Sessao.pode(e.modulo, "excluir")
        self.itens.definir(itens, editavel, pode_remover)
        desconto = getattr(doc, "desconto", 0) or 0
        acrescimo = getattr(doc, "acrescimo", 0) or 0
        texto_total = "Total  R$ " + format_value(doc.valor_total)
        if desconto or acrescimo:
            subtotal = doc.valor_total + desconto - acrescimo
            partes = [f"Subtotal R$ {format_value(subtotal)}"]
            if desconto:
                partes.append(f"Desconto − R$ {format_value(desconto)}")
            if acrescimo:
                partes.append(f"Acréscimo + R$ {format_value(acrescimo)}")
            texto_total = "  ·  ".join(partes) + "\n" + texto_total
        self.total.setText(texto_total)
        pode_ajustar = e.com_ajuste and status in e.editaveis and Sessao.pode(e.modulo, "editar")
        self.form_ajuste.setVisible(pode_ajustar)
        if pode_ajustar:
            self.desconto.setText(format_value(desconto) if desconto else "")
            self.acrescimo.setText(format_value(acrescimo) if acrescimo else "")
        pode_incluir = status in e.editaveis and Sessao.pode(e.modulo, "criar")
        self.form_item.setVisible(pode_incluir)
        self.aviso_estado.setText("" if status in e.editaveis else "Este documento não aceita mais alteração nos itens.")
        for acao in e.acoes:
            ativo = (not acao.estados or status in acao.estados) and Sessao.pode(e.modulo, acao.permissao)
            self.botoes[acao.chave].setEnabled(ativo)
            if not Sessao.pode(e.modulo, acao.permissao):
                self.botoes[acao.chave].setToolTip("Seu perfil não tem permissão para esta ação.")
            else:
                self.botoes[acao.chave].setToolTip("")
        if primeira_vez:
            self.painel.abrir()

    def fechar_detalhe(self) -> None:
        self._id_atual = None
        self.tabela.tabela.clearSelection()
        self.painel.fechar()

    # ---- criacao
    def novo(self) -> None:
        e = self.espec
        dlg = DialogoFormulario(self, f"Nova {e.singular}", e.campos_novo, "Criar", "Número e data são gerados automaticamente.")
        if e.chave == "Ordem de Servico":
            cliente, veiculo = dlg.formulario.widgets["cliente_id"], dlg.formulario.widgets["veiculo_id"]
            cliente.escolhido.connect(lambda _o, c=cliente, v=veiculo: (v.limpar(), v.definir_opcoes(_lookups().veiculos(c.id() or None))))
        dlg.definir_validador(lambda dados: self._validar_novo(dados))
        dados = dlg.exec_dados()
        if dados is None:
            return
        dados.setdefault("numero", "")
        dados.setdefault("data_venda", "")
        dados.setdefault("data_abertura", "")
        dados.setdefault("data_compra", "")
        criar = getattr(self.controller, e.metodo_criar)
        resultado: dict = {}

        def _acao() -> None:
            resultado["doc"] = criar(dados, usuario_id=self.usuario.id)

        if self.executar(_acao, f"{e.singular.capitalize()} criada."):
            self._id_atual = str(resultado["doc"].id)
            self.recarregar(avisar=False)
            self.tabela.selecionar(self._id_atual)
            self._mostrar(self._id_atual)
            self.painel.abrir()

    def _validar_novo(self, dados: dict) -> None:
        for campo in self.espec.campos_novo:
            if campo.tipo == "busca" and campo.nome != "veiculo_id" and not dados.get(campo.nome):
                raise ValueError(f"Escolha {campo.rotulo.lower()} na lista.")

    # ---- itens
    def adicionar_item(self) -> None:
        if not self._id_atual:
            return
        e = self.espec
        dados = {
            e.prefixo_id: int(self._id_atual),
            "produto_id": self.produto.id(),
            "quantidade": self.qtd.text(),
            "valor_unitario": self.valor.text(),
        }
        if e.com_tipo_item:
            dados["tipo"] = self.tipo_item.currentText()
            dados["descricao"] = self.descricao.text()

        def _acao() -> None:
            self.controller.adicionar_item(dados)

        if self.executar(_acao, "Item adicionado."):
            self.produto.limpar()
            self.qtd.setText("1")
            self.valor.clear()
            self.descricao.clear()
            self._atualizar()

    def _editar_item(self, item_id: int, quantidade: str, valor: str) -> None:
        if self.executar(lambda: self.controller.atualizar_item(item_id, quantidade, valor), "Item atualizado."):
            self._atualizar()
        else:
            self._atualizar()  # volta ao valor gravado

    def _remover_item(self, item_id: int) -> None:
        if not confirmar(self, "Remover item", "Remover este item do documento?", "Remover"):
            return
        if self.executar(lambda: self.controller.remover_item(item_id), "Item removido."):
            self._atualizar()

    def _atualizar(self) -> None:
        self.recarregar(avisar=False)

    # ---- acoes
    def acionar(self, acao: AcaoDoc) -> None:
        if not self._id_atual:
            return
        e = self.espec
        doc_id = int(self._id_atual)
        metodo = getattr(self.controller, acao.metodo)
        if acao.chave == "pdf":
            resultado: dict = {}
            if self.executar(lambda: resultado.update(arquivo=metodo(doc_id))):
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(resultado["arquivo"])))
                self.avisar(f"PDF gerado: {resultado['arquivo']}", "sucesso")
            return
        if acao.pede == "motivo":
            dlg = DialogoMotivo(self, f"{acao.rotulo} {e.singular}", acao.pergunta or "Informe o motivo:", acao.rotulo)
            motivo = dlg.pedir()
            if not motivo:
                return
            if acao.chave == "recusar":
                chamada: Callable = lambda: metodo(doc_id, motivo)  # noqa: E731
            else:
                chamada = lambda: metodo(doc_id, motivo, usuario_id=self.usuario.id)  # noqa: E731
        elif acao.pede == "finalizacao":
            campos = [
                Campo("data_vencimento", "Primeiro vencimento", "data", metade=True),
                Campo("parcelas", "Parcelas", metade=True, padrao="1"),
            ]
            if e.usa_forma:
                campos.append(Campo("forma_pagamento", "Forma de pagamento", "lista", FORMAS))
            dlg = DialogoFormulario(self, acao.rotulo, campos, acao.rotulo, "Define o vencimento e o parcelamento do financeiro gerado.")
            dlg.formulario.widgets["data_vencimento"].setDate(QDate.currentDate().addDays(30))
            dados = dlg.exec_dados()
            if dados is None:
                return
            extras = {"forma_pagamento": dados.get("forma_pagamento", "")} if e.usa_forma else {}
            chamada = lambda: metodo(doc_id, usuario_id=self.usuario.id, data_vencimento=dados["data_vencimento"], parcelas=dados["parcelas"] or 1, **extras)  # noqa: E731
        else:
            chamada = lambda: metodo(doc_id)  # noqa: E731
        if self.executar(chamada, acao.sucesso):
            self._atualizar()

    def keyPressEvent(self, evento) -> None:  # noqa: N802
        if evento.key() == Qt.Key.Key_Escape and self.painel.aberto:
            self.fechar_detalhe()
            return
        super().keyPressEvent(evento)


def fabricas_de_documentos(usuario) -> dict[str, Callable[[], QWidget]]:
    return {chave: (lambda e=espec: PaginaDocumento(e, usuario)) for chave, espec in ESPECS_DOC.items()}


__all__ = ["PaginaDocumento", "ESPECS_DOC", "fabricas_de_documentos"]
