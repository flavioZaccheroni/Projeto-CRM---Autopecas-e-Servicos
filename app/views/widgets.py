"""Widgets reutilizaveis: seletor com busca (ID + nome) e tabela com filtro de texto."""

import tkinter as tk
from tkinter import ttk

from app.utils.busca import extrair_id, filtrar_linhas, normalizar, titulo_coluna, valor_coluna  # noqa: F401
from app.views.theme import COLORS, format_value


# -- seletor -------------------------------------------------------------------------------------
class IdVar(tk.StringVar):
    """StringVar cujo get() devolve so o ID (parte numerica inicial), para uso direto nos controllers."""

    def get(self) -> str:  # type: ignore[override]
        return extrair_id(super().get())

    def texto(self) -> str:
        return super().get()


class Seletor(ttk.Combobox):
    """Combobox 'ID - nome' com busca ao digitar. A variavel (IdVar) devolve apenas o ID."""

    def __init__(self, master, variavel: IdVar, carregar, largura: int = 26, ao_escolher=None) -> None:
        super().__init__(master, textvariable=variavel, width=largura)
        self._carregar = carregar
        self._ao_escolher = ao_escolher
        self._opcoes: list[tuple] = []
        self.recarregar()
        self.bind("<KeyRelease>", self._filtrar, add="+")
        self.bind("<<ComboboxSelected>>", self._escolhido, add="+")

    @staticmethod
    def _texto(opcao) -> str:
        return f"{opcao[0]} - {opcao[1]}"

    def recarregar(self) -> None:
        try:
            self._opcoes = list(self._carregar())
        except Exception:  # sem permissao/sessao: o seletor fica vazio, a tela continua utilizavel
            self._opcoes = []
        self["values"] = [self._texto(o) for o in self._opcoes]

    def opcao_atual(self):
        id_atual = extrair_id(self.get())
        return next((o for o in self._opcoes if str(o[0]) == id_atual), None)

    def definir_id(self, valor) -> None:
        if valor in (None, ""):
            self.set("")
            return
        opcao = next((o for o in self._opcoes if str(o[0]) == str(valor)), None)
        self.set(self._texto(opcao) if opcao else str(valor))

    def _filtrar(self, evento) -> None:
        if evento.keysym in {"Up", "Down", "Return", "Tab", "Escape", "Left", "Right", "Shift_L", "Shift_R"}:
            return
        termo = normalizar(self.get())
        todos = [self._texto(o) for o in self._opcoes]
        self["values"] = [t for t in todos if termo in normalizar(t)] if termo else todos

    def _escolhido(self, _evento) -> None:
        self["values"] = [self._texto(o) for o in self._opcoes]
        if self._ao_escolher:
            self._ao_escolher(self.opcao_atual())


# -- tabela --------------------------------------------------------------------------------------
class TabelaFiltravel(ttk.Frame):
    """Treeview com caixa de busca (todas as palavras, sem acento), linhas zebradas e contador."""

    _instancias: list["TabelaFiltravel"] = []

    def __init__(self, master, colunas: list[str], altura: int = 10, larguras: dict[str, int] | None = None, filtro: bool = True) -> None:
        super().__init__(master, style="Surface.TFrame")
        self.colunas = colunas
        self._linhas: list[tuple[str, list]] = []
        self.termo = tk.StringVar()
        self.contador = tk.StringVar()
        larguras = larguras or {}

        if filtro:
            barra = ttk.Frame(self, style="Surface.TFrame")
            barra.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 6))
            ttk.Label(barra, text="Buscar").pack(side="left", padx=(0, 6))
            self.entrada = ttk.Entry(barra, textvariable=self.termo, width=36)
            self.entrada.pack(side="left")
            ttk.Button(barra, text="Limpar", command=self.limpar_filtro).pack(side="left", padx=(6, 12))
            ttk.Label(barra, textvariable=self.contador, style="Subtle.TLabel").pack(side="left")
            self.entrada.bind("<Escape>", lambda _e: self.limpar_filtro())
            self.termo.trace_add("write", lambda *_: self._reaplicar())
            TabelaFiltravel._instancias.append(self)

        self.tree = ttk.Treeview(self, columns=colunas, show="headings", height=altura)
        for coluna in colunas:
            self.tree.heading(coluna, text=titulo_coluna(coluna))
            self.tree.column(coluna, width=larguras.get(coluna, 120), anchor="w")
        self.tree.tag_configure("zebra", background=COLORS["zebra"])
        yscroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        yscroll.grid(row=1, column=1, sticky="ns")
        xscroll.grid(row=2, column=0, sticky="ew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    # -- dados
    def limpar(self) -> None:
        self._linhas = []
        self._mostrar([])

    def inserir(self, iid, valores: list) -> None:
        self._linhas.append((str(iid), [format_value(v) for v in valores]))

    def concluir(self) -> None:
        """Chame depois de varias chamadas a inserir() para exibir o resultado."""
        self._reaplicar()

    def preencher(self, linhas: list[tuple[object, list]]) -> None:
        self._linhas = [(str(iid), [format_value(v) for v in valores]) for iid, valores in linhas]
        self._reaplicar()

    def _reaplicar(self) -> None:
        visiveis = filtrar_linhas(self._linhas, self.termo.get())
        self._mostrar(visiveis)
        total = len(self._linhas)
        self.contador.set(f"{len(visiveis)} de {total}" if len(visiveis) != total else f"{total} registro(s)")

    def _mostrar(self, linhas: list[tuple[str, list]]) -> None:
        selecionado = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for posicao, (iid, valores) in enumerate(linhas):
            self.tree.insert("", "end", iid=iid, values=valores, tags=("zebra",) if posicao % 2 else ())
        if selecionado and self.tree.exists(selecionado[0]):
            self.tree.selection_set(selecionado[0])

    # -- interacao
    def limpar_filtro(self) -> None:
        self.termo.set("")

    def selection(self):
        return self.tree.selection()

    def item(self, iid, opcao="values"):
        return self.tree.item(iid, opcao)

    def ao_selecionar(self, callback) -> None:
        self.tree.bind("<<TreeviewSelect>>", callback)

    @classmethod
    def focar_busca(cls) -> bool:
        """Ctrl+F: foca a caixa de busca da primeira tabela visivel."""
        cls._instancias = [t for t in cls._instancias if t.winfo_exists()]
        for tabela in cls._instancias:
            if tabela.winfo_ismapped():
                tabela.entrada.focus_set()
                tabela.entrada.select_range(0, "end")
                return True
        return False
