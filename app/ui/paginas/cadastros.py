"""Telas de cadastro (clientes, veiculos, fornecedores, categorias, marcas, produtos) sobre uma pagina generica:
tabela ordenavel/filtravel a esquerda e painel lateral de edicao que desliza para dentro."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QMessageBox, QScrollArea, QVBoxLayout, QWidget

from app.controllers.cadastro_controller import (
    CategoriaProdutoController,
    ClienteController,
    FornecedorController,
    MarcaProdutoController,
    ProdutoController,
    ServicoController,
    VeiculoController,
)
from app.controllers.lookup_controller import LookupController
from app.ui.componentes import Botao, Card, Coluna, TabelaDados, rotulo
from app.ui.formulario import Campo, Formulario
from app.ui.paginas.base import Pagina
from app.utils.busca import normalizar, valor_coluna
from app.utils.sessao import Sessao
from app.utils.validators import UFS

LARGURA_PAINEL = 370
TONS_ATIVO = {"Ativo": "sucesso", "Inativo": "neutro"}


@dataclass
class EspecCadastro:
    chave: str  # igual a chave do menu
    singular: str
    plural: str
    descricao: str
    controller: Callable
    campos: list[Campo]
    colunas: list[tuple[str, Coluna]]  # (caminho do atributo, coluna)
    artigo: str = "o"  # "o cliente" / "a categoria"


def _busca(nome: str) -> Callable[[], list]:
    return lambda: getattr(LookupController(), nome)()


ESPECS: dict[str, EspecCadastro] = {
    "Clientes": EspecCadastro(
        "Clientes", "cliente", "clientes", "Pessoas físicas e jurídicas atendidas pela oficina.", ClienteController,
        [
            Campo("nome", "Nome"),
            Campo("tipo_pessoa", "Tipo de pessoa", "lista", ["PF", "PJ"], somente_lista=True, metade=True),
            Campo("cpf_cnpj", "CPF/CNPJ", metade=True),
            Campo("telefone", "Telefone", metade=True),
            Campo("email", "E-mail", metade=True),
            Campo("endereco", "Endereço"),
            Campo("cidade", "Cidade", metade=True),
            Campo("uf", "UF", "lista", sorted(UFS), metade=True),
            Campo("ativo", "Cliente ativo", "bool"),
        ],
        [
            ("id", Coluna("ID", "num", 50)),
            ("nome", Coluna("Nome", "texto", 230)),
            ("tipo_pessoa", Coluna("Tipo", "texto", 55)),
            ("cpf_cnpj", Coluna("CPF/CNPJ", "texto", 125)),
            ("telefone", Coluna("Telefone", "texto", 110)),
            ("ativo", Coluna("Situação", "emblema", 90, TONS_ATIVO)),
        ],
    ),
    "Veiculos": EspecCadastro(
        "Veiculos", "veículo", "veículos", "Veículos dos clientes, com placa e quilometragem.", VeiculoController,
        [
            Campo("cliente_id", "Cliente", "busca", fonte=_busca("clientes"), dica="Buscar cliente…"),
            Campo("placa", "Placa", metade=True),
            Campo("ano", "Ano", metade=True),
            Campo("marca", "Marca", metade=True),
            Campo("modelo", "Modelo", metade=True),
            Campo("km_atual", "KM atual"),
            Campo("observacoes", "Observações"),
        ],
        [
            ("id", Coluna("ID", "num", 50)),
            ("cliente.nome", Coluna("Cliente", "texto", 200)),
            ("placa", Coluna("Placa", "texto", 80)),
            ("marca", Coluna("Marca", "texto", 90)),
            ("modelo", Coluna("Modelo", "texto", 105)),
            ("ano", Coluna("Ano", "num", 55)),
            ("km_atual", Coluna("KM", "num", 75)),
        ],
    ),
    "Fornecedores": EspecCadastro(
        "Fornecedores", "fornecedor", "fornecedores", "Empresas que fornecem peças e insumos.", FornecedorController,
        [
            Campo("razao_social", "Razão social"),
            Campo("nome_fantasia", "Nome fantasia"),
            Campo("cnpj", "CNPJ", metade=True),
            Campo("telefone", "Telefone", metade=True),
            Campo("email", "E-mail"),
            Campo("ativo", "Fornecedor ativo", "bool"),
        ],
        [
            ("id", Coluna("ID", "num", 50)),
            ("razao_social", Coluna("Razão social", "texto", 230)),
            ("nome_fantasia", Coluna("Nome fantasia", "texto", 130)),
            ("cnpj", Coluna("CNPJ", "texto", 130)),
            ("telefone", Coluna("Telefone", "texto", 120)),
            ("ativo", Coluna("Situação", "emblema", 90, TONS_ATIVO)),
        ],
    ),
    "Categorias": EspecCadastro(
        "Categorias", "categoria", "categorias", "Agrupamentos para organizar o catálogo de produtos.", CategoriaProdutoController,
        [Campo("nome", "Nome"), Campo("descricao", "Descrição"), Campo("ativo", "Categoria ativa", "bool")],
        [
            ("id", Coluna("ID", "num", 50)),
            ("nome", Coluna("Nome", "texto", 220)),
            ("descricao", Coluna("Descrição", "texto", 320)),
            ("ativo", Coluna("Situação", "emblema", 90, TONS_ATIVO)),
        ],
        artigo="a",
    ),
    "Marcas": EspecCadastro(
        "Marcas", "marca", "marcas", "Marcas dos produtos vendidos e consumidos.", MarcaProdutoController,
        [Campo("nome", "Nome"), Campo("ativo", "Marca ativa", "bool")],
        [("id", Coluna("ID", "num", 50)), ("nome", Coluna("Nome", "texto", 320)), ("ativo", Coluna("Situação", "emblema", 90, TONS_ATIVO))],
        artigo="a",
    ),
    "Produtos": EspecCadastro(
        "Produtos", "produto", "produtos", "Catálogo de peças e serviços com preços e estoque mínimo.", ProdutoController,
        [
            Campo("codigo", "Código", metade=True),
            Campo("unidade", "Unidade", "lista", ["UN", "PC", "CX", "KG", "L", "M", "JG"], metade=True, padrao="UN"),
            Campo("descricao", "Descrição"),
            Campo("categoria_id", "Categoria", "busca", fonte=_busca("categorias"), dica="Buscar categoria…"),
            Campo("marca_id", "Marca", "busca", fonte=_busca("marcas"), dica="Buscar marca…"),
            Campo("ncm", "NCM"),
            Campo("preco_custo", "Preço de custo", metade=True),
            Campo("preco_venda", "Preço de venda", metade=True),
            Campo("estoque_minimo", "Estoque mínimo"),
            Campo("ativo", "Produto ativo", "bool"),
        ],
        [
            ("id", Coluna("ID", "num", 50)),
            ("codigo", Coluna("Código", "texto", 85)),
            ("descricao", Coluna("Descrição", "texto", 250)),
            ("categoria.nome", Coluna("Categoria", "texto", 100)),
            ("marca.nome", Coluna("Marca", "texto", 85)),
            ("preco_venda", Coluna("Preço", "num", 80)),
            ("estoque_minimo", Coluna("Mín.", "num", 60)),
        ],
    ),
    "Servicos": EspecCadastro(
        "Servicos", "serviço", "serviços", "Mão de obra com preço padrão e tempo estimado: alimenta os itens da ordem de serviço.", ServicoController,
        [
            Campo("nome", "Nome do serviço"),
            Campo("descricao", "Descrição"),
            Campo("preco_padrao", "Preço padrão (R$)", metade=True),
            Campo("tempo_estimado_min", "Tempo estimado (min)", metade=True),
            Campo("ativo", "Serviço ativo", "bool"),
        ],
        [
            ("id", Coluna("ID", "num", 50)),
            ("nome", Coluna("Serviço", "texto", 260)),
            ("preco_padrao", Coluna("Preço", "num", 90)),
            ("tempo_estimado_min", Coluna("Min.", "num", 60)),
            ("ativo", Coluna("Situação", "emblema", 90, TONS_ATIVO)),
        ],
    ),
}


class PainelEdicao(QFrame):
    """Painel lateral que desliza para dentro/fora (animacao da largura maxima)."""

    def __init__(self, largura: int = LARGURA_PAINEL) -> None:
        super().__init__()
        self._largura = largura
        self.setMaximumWidth(0)
        self.setMinimumWidth(0)
        self._aberto = False
        self._anim = QPropertyAnimation(self, b"maximumWidth", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    @property
    def aberto(self) -> bool:
        return self._aberto

    def abrir(self) -> None:
        self._mover(True)

    def fechar(self) -> None:
        self._mover(False)

    def _mover(self, abrir: bool) -> None:
        self._aberto = abrir
        self._anim.stop()
        self._anim.setStartValue(self.maximumWidth())
        self._anim.setEndValue(self._largura if abrir else 0)
        self._anim.start()


class PaginaCadastro(Pagina):
    def __init__(self, espec: EspecCadastro) -> None:
        super().__init__()
        self.espec = espec
        self.controller = espec.controller()
        self.modulo = self.controller.modulo
        self.subtitulo = espec.descricao
        self.itens: dict[str, object] = {}
        self._id_atual: str | None = None
        self._sujo = False
        self.corpo.setSpacing(0)
        self.corpo.setContentsMargins(0, 0, 0, 0)

        raiz = QHBoxLayout()
        raiz.setContentsMargins(28, 24, 28, 24)
        raiz.setSpacing(16)
        self.corpo.addLayout(raiz)

        # tabela
        card = Card()
        coluna = QVBoxLayout(card)
        coluna.setContentsMargins(16, 16, 16, 16)
        self.tabela = TabelaDados(
            [c for _, c in espec.colunas],
            vazio_titulo=f"Nenhum {espec.singular} cadastrado" if espec.artigo == "o" else f"Nenhuma {espec.singular} cadastrada",
            vazio_texto=f"Use “Novo {espec.singular}” para cadastrar {espec.artigo} primeir{espec.artigo} {espec.singular}.",
            placeholder=f"Buscar {espec.plural}…",
        )
        self.botao_novo = Botao(f"Novo {espec.singular}", "primario", "mais")
        self.botao_novo.clicked.connect(self.novo)
        self.botao_csv = Botao("Exportar CSV", "secundario", "baixar")
        self.botao_csv.clicked.connect(self.exportar)
        self.tabela.adicionar_acao(self.botao_csv)
        self.tabela.adicionar_acao(self.botao_novo)
        self.tabela.selecionado.connect(self._ao_selecionar)
        coluna.addWidget(self.tabela)
        raiz.addWidget(card, 1)

        # painel de edicao
        self.painel = PainelEdicao()
        interno = Card()
        interno.setMinimumWidth(LARGURA_PAINEL)
        interno.setMaximumWidth(LARGURA_PAINEL)
        vertical = QVBoxLayout(interno)
        vertical.setContentsMargins(20, 18, 20, 18)
        vertical.setSpacing(12)
        topo = QHBoxLayout()
        self.titulo_painel = rotulo("", "secao")
        fechar = Botao("", "icone", "fechar")
        fechar.setToolTip("Fechar (Esc)")
        fechar.clicked.connect(self.cancelar)
        topo.addWidget(self.titulo_painel, 1)
        topo.addWidget(fechar)
        vertical.addLayout(topo)
        self.formulario = Formulario(espec.campos)
        self.formulario.alterado.connect(self._marcar_sujo)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QScrollArea.Shape.NoFrame)
        rolagem.setWidget(self.formulario)
        vertical.addWidget(rolagem, 1)
        self.erro = rotulo("", "erro", quebra=True)
        self.erro.hide()
        vertical.addWidget(self.erro)
        rodape = QHBoxLayout()
        self.botao_cancelar = Botao("Cancelar", "fantasma")
        self.botao_cancelar.clicked.connect(self.cancelar)
        self.botao_salvar = Botao("Salvar", "primario", "ok")
        self.botao_salvar.clicked.connect(self.salvar)
        rodape.addStretch()
        rodape.addWidget(self.botao_cancelar)
        rodape.addWidget(self.botao_salvar)
        vertical.addLayout(rodape)
        lay = QVBoxLayout(self.painel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(interno)
        raiz.addWidget(self.painel)

        for atalho, funcao in (("Ctrl+N", self.novo), ("Ctrl+S", self.salvar), ("Esc", self.cancelar)):
            QShortcut(QKeySequence(atalho), self, activated=funcao).setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)

        self._aplicar_permissoes()
        self.recarregar(avisar=False)

    # ---- permissoes
    def _aplicar_permissoes(self) -> None:
        pode_criar, pode_editar = Sessao.pode(self.modulo, "criar"), Sessao.pode(self.modulo, "editar")
        self.botao_novo.setEnabled(pode_criar)
        self.botao_novo.setToolTip("" if pode_criar else "Seu perfil não pode criar registros neste módulo.")
        self._pode_editar = pode_editar
        self._pode_criar = pode_criar

    # ---- carga
    def recarregar(self, avisar: bool = True) -> None:
        try:
            registros = self.controller.listar()
        except Exception as exc:  # noqa: BLE001 - mostra a falha (inclusive permissao) ao usuario
            self.avisar(str(exc), "perigo")
            return
        self.itens = {}
        linhas = []
        for item in registros:
            iid = str(item.id)
            self.itens[iid] = item
            linhas.append((iid, [self._valor(item, caminho) for caminho, _ in self.espec.colunas]))
        self.tabela.definir_dados(linhas)

    @staticmethod
    def _valor(item, caminho: str):
        valor = valor_coluna(item, caminho)
        if caminho == "ativo":
            return "Ativo" if valor else "Inativo"
        return valor

    def focar_busca(self) -> bool:
        return self.tabela.focar_busca()

    # ---- fluxo de edicao
    def novo(self) -> None:
        if not self._pode_criar:
            self.avisar("Seu perfil não pode criar registros neste módulo.", "aviso")
            return
        if not self._descartar_alteracoes():
            return
        self.tabela.tabela.clearSelection()
        self._abrir(None)

    def _ao_selecionar(self, iid) -> None:
        if iid is None or str(iid) == self._id_atual:
            return
        if not self._descartar_alteracoes():
            if self._id_atual:
                self.tabela.selecionar(self._id_atual)
            return
        self._abrir(str(iid))

    def _abrir(self, iid: str | None) -> None:
        self._id_atual = iid
        item = self.itens.get(iid) if iid else None
        self.formulario.preencher(item)
        self._sujo = False
        self._mostrar_erro("")
        editando = iid is not None
        self.titulo_painel.setText(f"Editar {self.espec.singular}" if editando else f"Novo {self.espec.singular}")
        pode = self._pode_editar if editando else self._pode_criar
        self.formulario.somente_leitura(not pode)
        self.botao_salvar.setEnabled(pode)
        self.botao_salvar.setToolTip("" if pode else "Seu perfil só pode consultar este módulo.")
        self.painel.abrir()
        primeiro = self.formulario.primeiro_campo()
        if primeiro is not None and pode:
            primeiro.setFocus()

    def cancelar(self) -> None:
        if not self.painel.aberto:
            return
        if not self._descartar_alteracoes():
            return
        self._id_atual = None
        self.tabela.tabela.clearSelection()
        self.painel.fechar()

    def _marcar_sujo(self) -> None:
        self._sujo = True

    def _descartar_alteracoes(self) -> bool:
        if not (self._sujo and self.painel.aberto):
            return True
        resposta = QMessageBox.question(
            self,
            "Alterações não salvas",
            "Há alterações não salvas. Descartar?",
            QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return resposta == QMessageBox.StandardButton.Discard

    def salvar(self) -> None:
        if not self.painel.aberto or not self.botao_salvar.isEnabled():
            return
        dados = self.formulario.valores()
        if self._id_atual:
            dados["id"] = self._id_atual
        try:
            item = self.controller.salvar(dados)
        except Exception as exc:  # noqa: BLE001 - regra de negocio/permissao: mensagem amigavel no proprio painel
            self._mostrar_erro(str(exc))
            self._marcar_campo_do_erro(str(exc))
            return
        novo_id = str(item.id)
        criado = self._id_atual is None
        self._sujo = False
        self.recarregar(avisar=False)
        self.tabela.selecionar(novo_id)
        self._abrir(novo_id)
        self.avisar(f"{self.espec.singular.capitalize()} {'cadastrado' if criado and self.espec.artigo == 'o' else 'cadastrada' if criado else 'salvo' if self.espec.artigo == 'o' else 'salva'} com sucesso.", "sucesso")

    def _mostrar_erro(self, texto: str) -> None:
        self.erro.setText(texto)
        self.erro.setVisible(bool(texto))

    def _marcar_campo_do_erro(self, mensagem: str) -> None:
        """Destaca o campo cujo rotulo aparece na mensagem de validacao (melhor esforco)."""
        texto = normalizar(mensagem)
        for campo in self.espec.campos:
            partes = [normalizar(p) for p in campo.rotulo.replace("/", " ").split() if len(p) > 2]
            if campo.tipo != "bool" and (normalizar(campo.rotulo) in texto or any(p in texto.split() or p in texto for p in partes[:1])):
                self.formulario.marcar_invalido(campo.nome)

    # ---- exportacao
    def exportar(self) -> None:
        caminho, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", f"{self.espec.plural}.csv", "CSV (*.csv)")
        if caminho:
            total = self.tabela.exportar_csv(caminho)
            self.avisar(f"{total} registro(s) exportado(s).", "sucesso")


def fabricas_de_cadastros() -> dict[str, Callable[[], QWidget]]:
    return {chave: (lambda e=espec: PaginaCadastro(e)) for chave, espec in ESPECS.items()}
