"""Componentes de interface compartilhados: permissoes em botoes, dialogos e painel de itens."""

import os
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from app.utils.sessao import Sessao
from app.views.theme import format_value
from app.views.widgets import titulo_coluna, valor_coluna


def aplicar_permissao(widget, modulo: str, acao: str):
    """Desabilita o widget se o usuario logado nao tem a permissao (a barreira real fica no controller)."""
    if not Sessao.pode(modulo, acao):
        widget.state(["disabled"])
    return widget


def pedir_motivo(parent, titulo: str, pergunta: str = "Informe o motivo:") -> str | None:
    motivo = simpledialog.askstring(titulo, pergunta, parent=parent)
    if motivo is None:
        return None
    if not motivo.strip():
        messagebox.showwarning(titulo, "O motivo e obrigatorio.", parent=parent)
        return None
    return motivo.strip()


def abrir_arquivo(caminho) -> None:
    try:
        os.startfile(str(caminho))  # type: ignore[attr-defined]  # Windows
    except (AttributeError, OSError):
        pass


def executar(acao, sucesso: str | None = None, titulo: str = "Aviso", depois=None) -> bool:
    """Roda `acao`, mostra erros amigaveis (inclusive permissao negada) e confirma o sucesso."""
    try:
        acao()
    except Exception as exc:  # a UI mostra qualquer erro de regra de negocio/permissao
        messagebox.showerror("Erro", str(exc))
        return False
    if depois:
        depois()
    if sucesso:
        messagebox.showinfo(titulo, sucesso)
    return True


class ItensPanel(ttk.LabelFrame):
    """Tabela de itens do documento selecionado, com edicao e remocao (antes da finalizacao)."""

    def __init__(self, master, colunas, listar, editar, remover, valores_form, modulo: str, ao_alterar) -> None:
        super().__init__(master, text="Itens do documento selecionado", padding=10, style="Section.TLabelframe")
        self._listar, self._editar, self._remover = listar, editar, remover
        self._valores_form, self._ao_alterar = valores_form, ao_alterar
        self._documento_id: int | None = None
        self.tree = ttk.Treeview(self, columns=colunas, show="headings", height=3)
        for coluna in colunas:
            self.tree.heading(coluna, text=titulo_coluna(coluna))
            self.tree.column(coluna, width=110, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        botoes = ttk.Frame(self, style="Surface.TFrame")
        botoes.grid(row=0, column=1, sticky="n", padx=(10, 0))
        aplicar_permissao(ttk.Button(botoes, text="Aplicar qtd/valor", command=self.editar), modulo, "editar").pack(fill="x", pady=(0, 6))
        aplicar_permissao(ttk.Button(botoes, text="Remover item", command=self.remover), modulo, "excluir").pack(fill="x")
        self.columnconfigure(0, weight=1)
        self._colunas = colunas

    def mostrar(self, documento_id) -> None:
        self._documento_id = int(documento_id) if documento_id not in (None, "") else None
        for linha in self.tree.get_children():
            self.tree.delete(linha)
        if self._documento_id is None:
            return
        try:
            itens = self._listar(self._documento_id)
        except Exception:
            return
        for item in itens:
            self.tree.insert("", "end", iid=str(item.id), values=[format_value(valor_coluna(item, c)) for c in self._colunas])

    def _selecionado(self) -> int | None:
        selecao = self.tree.selection()
        if not selecao:
            messagebox.showwarning("Itens", "Selecione um item na tabela.")
            return None
        return int(selecao[0])

    def editar(self) -> None:
        item_id = self._selecionado()
        if item_id is None:
            return
        quantidade, valor = self._valores_form()
        if executar(lambda: self._editar(item_id, quantidade, valor), "Item atualizado."):
            self.mostrar(self._documento_id)
            self._ao_alterar()

    def remover(self) -> None:
        item_id = self._selecionado()
        if item_id is None or not messagebox.askyesno("Itens", "Remover o item selecionado?"):
            return
        if executar(lambda: self._remover(item_id), "Item removido."):
            self.mostrar(self._documento_id)
            self._ao_alterar()


FORMAS_PAGAMENTO = ["", "DINHEIRO", "PIX", "CARTAO_DEBITO", "CARTAO_CREDITO", "BOLETO", "TRANSFERENCIA"]


def campo_entry(master, variavel: tk.Variable, largura: int = 14) -> ttk.Entry:
    return ttk.Entry(master, textvariable=variavel, width=largura)
