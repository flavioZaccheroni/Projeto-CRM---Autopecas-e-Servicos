import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.seguranca_controller import SegurancaController
from app.views.theme import format_value


class SegurancaFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.usuario = usuario
        self.controller = SegurancaController()
        self.config_inputs = {
            "chave": tk.StringVar(),
            "valor": tk.StringVar(),
        }
        self.backup_path = tk.StringVar()

        ttk.Label(self, text="Seguranca e Backup", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Gerencie backups, restauracao, parametros e auditoria operacional.",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(4, 14))
        self._criar_acoes_backup()
        self._criar_configuracoes()
        self._criar_tabelas()
        self.carregar()

    def _criar_acoes_backup(self) -> None:
        frame = ttk.LabelFrame(self, text="Backup e restauracao", padding=14, style="Section.TLabelframe")
        frame.pack(fill="x", pady=(0, 8))
        ttk.Button(frame, text="Criar backup", command=self.criar_backup, style="Primary.TButton").grid(row=0, column=0, padx=(0, 10))
        ttk.Label(frame, text="Arquivo para restaurar").grid(row=0, column=1, padx=(0, 6), sticky="w")
        ttk.Entry(frame, textvariable=self.backup_path, width=70).grid(row=0, column=2, sticky="ew", padx=(0, 10))
        ttk.Button(frame, text="Restaurar", command=self.restaurar_backup).grid(row=0, column=3)
        frame.columnconfigure(2, weight=1)

    def _criar_configuracoes(self) -> None:
        frame = ttk.LabelFrame(self, text="Parametros do sistema", padding=14, style="Section.TLabelframe")
        frame.pack(fill="x", pady=(0, 12))
        ttk.Label(frame, text="Chave").grid(row=0, column=0, padx=(0, 6), sticky="w")
        ttk.Entry(frame, textvariable=self.config_inputs["chave"], width=28).grid(row=0, column=1, padx=(0, 12), sticky="ew")
        ttk.Label(frame, text="Valor").grid(row=0, column=2, padx=(0, 6), sticky="w")
        ttk.Entry(frame, textvariable=self.config_inputs["valor"], width=42).grid(row=0, column=3, padx=(0, 12), sticky="ew")
        ttk.Button(frame, text="Salvar parametro", command=self.salvar_configuracao).grid(row=0, column=4)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=2)

    def _criar_tabelas(self) -> None:
        panes = ttk.PanedWindow(self, orient="vertical")
        panes.pack(fill="both", expand=True)

        backups_frame = ttk.LabelFrame(panes, text="Backups disponiveis", padding=10, style="Section.TLabelframe")
        auditoria_frame = ttk.LabelFrame(panes, text="Auditoria", padding=10, style="Section.TLabelframe")
        config_frame = ttk.LabelFrame(panes, text="Configuracoes", padding=10, style="Section.TLabelframe")
        panes.add(backups_frame, weight=1)
        panes.add(config_frame, weight=1)
        panes.add(auditoria_frame, weight=2)

        self.backup_tree = ttk.Treeview(backups_frame, columns=["arquivo"], show="headings", height=4)
        self.backup_tree.heading("arquivo", text="Arquivo")
        self.backup_tree.column("arquivo", width=900, anchor="w")
        self.backup_tree.pack(fill="both", expand=True)
        self.backup_tree.bind("<<TreeviewSelect>>", self._selecionar_backup)

        self.config_tree = ttk.Treeview(config_frame, columns=["id", "chave", "valor"], show="headings", height=5)
        for column in ["id", "chave", "valor"]:
            self.config_tree.heading(column, text=column.title())
            self.config_tree.column(column, width=180, anchor="w")
        self.config_tree.pack(fill="both", expand=True)
        self.config_tree.bind("<<TreeviewSelect>>", self._selecionar_configuracao)

        columns = ["id", "usuario_id", "entidade", "entidade_id", "acao", "detalhes", "criado_em"]
        self.auditoria_tree = ttk.Treeview(auditoria_frame, columns=columns, show="headings", height=8)
        for column in columns:
            self.auditoria_tree.heading(column, text=column.replace("_", " ").title())
            self.auditoria_tree.column(column, width=130, anchor="w")
        scroll = ttk.Scrollbar(auditoria_frame, orient="vertical", command=self.auditoria_tree.yview)
        self.auditoria_tree.configure(yscrollcommand=scroll.set)
        self.auditoria_tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        auditoria_frame.columnconfigure(0, weight=1)
        auditoria_frame.rowconfigure(0, weight=1)

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
            self.controller.restaurar_backup(arquivo, usuario_id=self.usuario.id)
            self.carregar()
            messagebox.showinfo("Backup", "Backup restaurado. Reinicie o sistema para recarregar todas as conexoes.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def salvar_configuracao(self) -> None:
        try:
            self.controller.salvar_configuracao(
                self.config_inputs["chave"].get(),
                self.config_inputs["valor"].get(),
                usuario_id=self.usuario.id,
            )
            self.carregar()
            messagebox.showinfo("Configuracao", "Parametro salvo.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def carregar(self) -> None:
        for tree in [self.backup_tree, self.config_tree, self.auditoria_tree]:
            for row in tree.get_children():
                tree.delete(row)

        for arquivo in self.controller.listar_backups():
            self.backup_tree.insert("", "end", values=[str(arquivo)])
        for item in self.controller.listar_configuracoes():
            self.config_tree.insert("", "end", iid=str(item.id), values=[format_value(item.id), format_value(item.chave), format_value(item.valor)])
        for item in self.controller.listar_auditoria():
            self.auditoria_tree.insert(
                "",
                "end",
                values=[
                    format_value(item.id),
                    format_value(item.usuario_id),
                    format_value(item.entidade),
                    format_value(item.entidade_id),
                    format_value(item.acao),
                    format_value(item.detalhes),
                    format_value(item.criado_em),
                ],
            )

    def _selecionar_backup(self, _event) -> None:
        selection = self.backup_tree.selection()
        if selection:
            self.backup_path.set(self.backup_tree.item(selection[0], "values")[0])

    def _selecionar_configuracao(self, _event) -> None:
        selection = self.config_tree.selection()
        if selection:
            values = self.config_tree.item(selection[0], "values")
            self.config_inputs["chave"].set(values[1])
            self.config_inputs["valor"].set(values[2])
