import tkinter as tk
from datetime import date
from decimal import Decimal
from tkinter import messagebox, ttk

from app.controllers.dashboard_controller import DashboardController
from app.views.theme import COLORS, format_value
from app.views.widgets import TabelaFiltravel

MESES_EXTENSO = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]


def reais(valor) -> str:
    return "R$ " + format_value(Decimal(valor))


class DashboardFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=26, style="Surface.TFrame")
        self.usuario = usuario
        self.controller = DashboardController()
        self.serie: list[tuple[str, Decimal]] = []

        topo = ttk.Frame(self, style="Surface.TFrame")
        topo.pack(fill="x")
        hoje = date.today()
        ttk.Label(topo, text=f"Ola, {usuario.nome.split()[0]}", style="Header.TLabel").pack(side="left")
        ttk.Button(topo, text="Atualizar (F5)", command=self.carregar).pack(side="right")
        ttk.Label(
            self,
            text=f"{DIAS[hoje.weekday()].capitalize()}, {hoje.day} de {MESES_EXTENSO[hoje.month - 1]} de {hoje.year}  |  Perfil: {usuario.perfil.nome}",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(2, 16))

        self.corpo = ttk.Frame(self, style="Surface.TFrame")
        self.corpo.pack(fill="both", expand=True)
        self.carregar()

    # -- carga ------------------------------------------------------------------------------
    def carregar(self) -> None:
        for filho in self.corpo.winfo_children():
            filho.destroy()
        try:
            dados = self.controller.resumo()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        vendas, financeiro, estoque = dados["vendas"], dados["financeiro"], dados["estoque_baixo"]
        if vendas is None and financeiro is None and estoque is None:
            ttk.Label(self.corpo, text="Seu perfil nao tem indicadores liberados. Use o menu lateral para acessar seus modulos.", style="Subtle.TLabel").pack(anchor="w")
            return

        if vendas is not None:
            self._linha_cards(
                [
                    ("FATURAMENTO DO MES", reais(vendas["faturamento_mes"]), f"{vendas['vendas_mes']} venda(s) + {vendas['os_finalizadas_mes']} OS finalizada(s)", None),
                    ("OS EM ABERTO", str(vendas["os_abertas"]), "Ordens de servico em andamento", None),
                    ("ORCAMENTOS EM ABERTO", str(vendas["orcamentos_abertos"]), "Aguardando aprovacao ou venda", None),
                ]
            )
        if financeiro is not None:
            vencido_r, vencido_p = financeiro["receber_vencido"], financeiro["pagar_vencido"]
            self._linha_cards(
                [
                    ("SALDO EM CAIXA", reais(financeiro["saldo_caixa"]), "Entradas menos saidas realizadas", "ok" if financeiro["saldo_caixa"] >= 0 else "danger"),
                    ("A RECEBER VENCIDO", reais(vencido_r), "Titulos em atraso" if vencido_r else "Nada em atraso", "danger" if vencido_r else None),
                    ("A PAGAR VENCIDO", reais(vencido_p), "Contas em atraso" if vencido_p else "Nada em atraso", "danger" if vencido_p else None),
                    ("VENCE EM 7 DIAS", f"{reais(financeiro['receber_7_dias'])}", f"a receber  |  {reais(financeiro['pagar_7_dias'])} a pagar", None),
                ]
            )

        meio = ttk.Frame(self.corpo, style="Surface.TFrame")
        meio.pack(fill="both", expand=True, pady=(4, 0))
        meio.columnconfigure(0, weight=3, uniform="col")
        meio.columnconfigure(1, weight=2, uniform="col")
        meio.rowconfigure(0, weight=1)
        meio.rowconfigure(1, weight=1)
        if vendas is not None:
            self._grafico(meio, vendas["serie_mensal"])
        if estoque is not None:
            self._tabela_estoque(meio, estoque)
        if financeiro is not None:
            self._tabela_vencimentos(meio, financeiro["proximos_vencimentos"])

    # -- blocos -----------------------------------------------------------------------------
    def _linha_cards(self, cartoes: list[tuple[str, str, str, str | None]]) -> None:
        linha = ttk.Frame(self.corpo, style="Surface.TFrame")
        linha.pack(fill="x", pady=(0, 12))
        for indice, (titulo, valor, nota, tom) in enumerate(cartoes):
            cartao = ttk.Frame(linha, style="Card.TFrame", padding=(16, 12))
            cartao.grid(row=0, column=indice, sticky="nsew", padx=(0, 12 if indice < len(cartoes) - 1 else 0))
            linha.columnconfigure(indice, weight=1, uniform="cards")
            ttk.Label(cartao, text=titulo, style="CardTitle.TLabel").pack(anchor="w")
            estilo = {"danger": "CardValueDanger.TLabel", "ok": "CardValueOk.TLabel"}.get(tom, "CardValue.TLabel")
            ttk.Label(cartao, text=valor, style=estilo).pack(anchor="w", pady=(4, 2))
            ttk.Label(cartao, text=nota, style="CardNote.TLabel", wraplength=230).pack(anchor="w")

    def _grafico(self, pai, serie: list[tuple[str, Decimal]]) -> None:
        self.serie = serie
        moldura = ttk.LabelFrame(pai, text="Faturamento - ultimos 6 meses", padding=10, style="Section.TLabelframe")
        moldura.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 12))
        self.canvas = tk.Canvas(moldura, height=260, bg=COLORS["surface"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self._desenhar())

    def _desenhar(self) -> None:
        c = self.canvas
        c.delete("all")
        largura, altura = c.winfo_width(), c.winfo_height()
        if largura < 80 or altura < 80 or not self.serie:
            return
        margem_esq, margem_base, margem_topo = 12, 28, 22
        maior = max((v for _, v in self.serie), default=Decimal("0"))
        if maior <= 0:
            c.create_text(largura / 2, altura / 2, text="Sem vendas finalizadas no periodo", fill=COLORS["muted"], font=("Segoe UI", 10))
            return
        area_h = altura - margem_base - margem_topo
        faixa = (largura - margem_esq * 2) / len(self.serie)
        barra = faixa * 0.55
        c.create_line(margem_esq, altura - margem_base, largura - margem_esq, altura - margem_base, fill=COLORS["border"])
        for indice, (rotulo, valor) in enumerate(self.serie):
            x0 = margem_esq + faixa * indice + (faixa - barra) / 2
            h = float(valor / maior) * area_h
            ultimo = indice == len(self.serie) - 1
            if h > 0:
                c.create_rectangle(x0, altura - margem_base - h, x0 + barra, altura - margem_base, fill=COLORS["primary"] if ultimo else "#99d5cf", outline="")
            c.create_text(x0 + barra / 2, altura - margem_base - h - 9, text=format_value(valor).split(",")[0] if valor else "0", fill=COLORS["text"], font=("Segoe UI", 8, "bold" if ultimo else "normal"))
            c.create_text(x0 + barra / 2, altura - margem_base + 13, text=rotulo, fill=COLORS["muted"], font=("Segoe UI", 9))

    def _tabela_estoque(self, pai, linhas) -> None:
        moldura = ttk.LabelFrame(pai, text="Estoque abaixo do minimo", padding=10, style="Section.TLabelframe")
        moldura.grid(row=0, column=1, sticky="nsew", pady=(0, 12))
        tabela = TabelaFiltravel(moldura, ["codigo", "descricao", "atual", "minimo"], altura=5, larguras={"codigo": 70, "descricao": 170, "atual": 60, "minimo": 60}, filtro=False)
        tabela.pack(fill="both", expand=True)
        tabela.preencher([(i, list(l)) for i, l in enumerate(linhas)])
        if not linhas:
            ttk.Label(moldura, text="Tudo certo: nenhum produto abaixo do minimo.", style="Subtle.TLabel").pack(anchor="w", pady=(6, 0))

    def _tabela_vencimentos(self, pai, linhas) -> None:
        moldura = ttk.LabelFrame(pai, text="Proximos vencimentos", padding=10, style="Section.TLabelframe")
        moldura.grid(row=1, column=1, sticky="nsew")
        tabela = TabelaFiltravel(moldura, ["vencimento", "tipo", "descricao", "valor"], altura=5, larguras={"vencimento": 85, "tipo": 70, "descricao": 150, "valor": 80}, filtro=False)
        tabela.pack(fill="both", expand=True)
        tabela.preencher([(i, [data, tipo, desc, valor]) for i, (data, tipo, desc, valor, _vencido) in enumerate(linhas)])
        tabela.tree.tag_configure("vencido", foreground=COLORS["danger"])
        for i, (*_resto, vencido) in enumerate(linhas):
            if vencido and tabela.tree.exists(str(i)):
                tabela.tree.item(str(i), tags=("vencido",))
        if not linhas:
            ttk.Label(moldura, text="Nenhum titulo em aberto.", style="Subtle.TLabel").pack(anchor="w", pady=(6, 0))
