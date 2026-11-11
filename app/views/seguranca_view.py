import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.seguranca_controller import SegurancaController
from app.views.helpers import aplicar_permissao
from app.views.widgets import TabelaFiltravel


class SegurancaFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.usuario = usuario
        self.controller = SegurancaController()
        self.backup_path = tk.StringVar()

        ttk.Label(self, text="Seguranca e Backup", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Gerencie backups, restauracao (com copia de seguranca previa e validacao do arquivo) e consulte a auditoria.",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(4, 14))
        self._criar_acoes_backup()
        self._criar_tabelas()
        self.carregar()

    def _criar_acoes_backup(self) -> None:
        frame = ttk.LabelFrame(self, text="Backup e restauracao", padding=14, style="Section.TLabelframe")
        frame.pack(fill="x", pady=(0, 8))
        aplicar_permissao(ttk.Button(frame, text="Criar backup", command=self.criar_backup, style="Primary.TButton"), "seguranca", "criar").grid(row=0, column=0, padx=(0, 10))
        ttk.Label(frame, text="Arquivo para restaurar").grid(row=0, column=1, padx=(0, 6), sticky="w")
        ttk.Entry(frame, textvariable=self.backup_path, width=70).grid(row=0, column=2, sticky="ew", padx=(0, 10))
        aplicar_permissao(ttk.Button(frame, text="Restaurar", command=self.restaurar_backup), "seguranca", "excluir").grid(row=0, column=3)
        frame.columnconfigure(2, weight=1)

    def _criar_tabelas(self) -> None:
        panes = ttk.PanedWindow(self, orient="vertical")
        panes.pack(fill="both", expand=True)

        backups_frame = ttk.LabelFrame(panes, text="Backups disponiveis", padding=10, style="Section.TLabelframe")
        auditoria_frame = ttk.LabelFrame(panes, text="Auditoria", padding=10, style="Section.TLabelframe")
        panes.add(backups_frame, weight=1)
        panes.add(auditoria_frame, weight=2)

        self.backup_tree = ttk.Treeview(backups_frame, columns=["arquivo"], show="headings", height=4)
        self.backup_tree.heading("arquivo", text="Arquivo")
        self.backup_tree.column("arquivo", width=900, anchor="w")
        self.backup_tree.pack(fill="both", expand=True)
        self.backup_tree.bind("<<TreeviewSelect>>", self._selecionar_backup)

        columns = ["id", "usuario_id", "entidade", "entidade_id", "acao", "detalhes", "criado_em"]
        self.auditoria_tabela = TabelaFiltravel(auditoria_frame, columns, altura=8, larguras={"id": 50, "detalhes": 360, "criado_em": 140})
        self.auditoria_tabela.pack(fill="both", expand=True)

    def criar_backup(self) -> None:
        try:
            arquivo = self.controller.criar_backup(usuario_id=self.usuario.id)
            self.backup_path.set(str(arquivo))
            self.carregar()
            messagebox.showinfo("Backup", f"Backup criado:\n{arquivo}")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def restaurar_backup(self) -> None:
        try:
            arquivo = self.backup_path.get()
            if not messagebox.askyesno(
                "Restaurar backup",
                "O banco atual sera substituido pelo backup selecionado.\n"
                "Uma copia do estado atual (pre_restore_*) sera guardada.\n\n"
                "Continuar?",
            ):
                return
            self.controller.restaurar_backup(arquivo, usuario_id=self.usuario.id)
            self.carregar()
            messagebox.showinfo("Backup", "Backup restaurado. Reinicie o sistema para recarregar todas as conexoes.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def carregar(self) -> None:
        for row in self.backup_tree.get_children():
            self.backup_tree.delete(row)
        for arquivo in self.controller.listar_backups():
            self.backup_tree.insert("", "end", values=[str(arquivo)])
        self.auditoria_tabela.preencher(
            [
                (i.id, [i.id, i.usuario_id, i.entidade, i.entidade_id, i.acao, i.detalhes, i.criado_em])
                for i in self.controller.listar_auditoria()
            ]
        )

    def _selecionar_backup(self, _event) -> None:
        selection = self.backup_tree.selection()
        if selection:
            self.backup_path.set(self.backup_tree.item(selection[0], "values")[0])
