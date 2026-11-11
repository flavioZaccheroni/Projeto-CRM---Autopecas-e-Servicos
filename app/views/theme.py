from datetime import date, datetime
from decimal import Decimal
from tkinter import ttk


COLORS = {
    "app_bg": "#f4f6f8",
    "surface": "#ffffff",
    "sidebar": "#17212b",
    "sidebar_hover": "#223140",
    "sidebar_active": "#0f766e",
    "sidebar_text": "#d7dee8",
    "sidebar_muted": "#8ea0b5",
    "text": "#1f2933",
    "muted": "#667085",
    "border": "#d9e2ec",
    "primary": "#0f766e",
    "primary_dark": "#115e59",
    "zebra": "#f6f8fa",
    "danger": "#b42318",
    "danger_bg": "#fef3f2",
    "warning": "#b54708",
    "ok": "#067647",
    "accent": "#2563eb",
}


def configure_style(root) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    root.configure(bg=COLORS["app_bg"])
    style.configure(".", font=("Segoe UI", 10), foreground=COLORS["text"])
    style.configure("App.TFrame", background=COLORS["app_bg"])
    style.configure("Surface.TFrame", background=COLORS["surface"])
    style.configure("Header.TLabel", background=COLORS["surface"], foreground=COLORS["text"], font=("Segoe UI", 18, "bold"))
    style.configure("Subtle.TLabel", background=COLORS["surface"], foreground=COLORS["muted"], font=("Segoe UI", 10))
    style.configure("Section.TLabelframe", background=COLORS["surface"], bordercolor=COLORS["border"], relief="solid")
    style.configure("Section.TLabelframe.Label", background=COLORS["surface"], foreground=COLORS["text"], font=("Segoe UI", 10, "bold"))
    style.configure("TLabel", background=COLORS["surface"], foreground=COLORS["text"])
    style.configure("TEntry", fieldbackground="#ffffff", bordercolor=COLORS["border"], lightcolor=COLORS["border"], darkcolor=COLORS["border"])
    style.configure("TCombobox", fieldbackground="#ffffff")
    style.configure("TButton", padding=(12, 7), font=("Segoe UI", 10))
    style.configure("Primary.TButton", padding=(14, 8), font=("Segoe UI", 10, "bold"), foreground="#ffffff", background=COLORS["primary"])
    style.map("Primary.TButton", background=[("active", COLORS["primary_dark"]), ("disabled", COLORS["border"])])
    style.configure(
        "Treeview",
        background="#ffffff",
        fieldbackground="#ffffff",
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        rowheight=28,
    )
    style.configure("Treeview.Heading", background="#e8eef5", foreground=COLORS["text"], font=("Segoe UI", 10, "bold"))
    style.map("Treeview", background=[("selected", COLORS["primary"])], foreground=[("selected", "#ffffff")])

    # Cartoes de indicador (dashboard)
    style.configure("Card.TFrame", background=COLORS["surface"], bordercolor=COLORS["border"], relief="solid", borderwidth=1)
    style.configure("CardTitle.TLabel", background=COLORS["surface"], foreground=COLORS["muted"], font=("Segoe UI", 9, "bold"))
    style.configure("CardValue.TLabel", background=COLORS["surface"], foreground=COLORS["text"], font=("Segoe UI", 20, "bold"))
    style.configure("CardValueDanger.TLabel", background=COLORS["surface"], foreground=COLORS["danger"], font=("Segoe UI", 20, "bold"))
    style.configure("CardValueOk.TLabel", background=COLORS["surface"], foreground=COLORS["ok"], font=("Segoe UI", 20, "bold"))
    style.configure("CardNote.TLabel", background=COLORS["surface"], foreground=COLORS["muted"], font=("Segoe UI", 9))

    # Login
    style.configure("Brand.TFrame", background=COLORS["sidebar"])
    style.configure("BrandTitle.TLabel", background=COLORS["sidebar"], foreground="#ffffff", font=("Segoe UI", 20, "bold"))
    style.configure("BrandText.TLabel", background=COLORS["sidebar"], foreground=COLORS["sidebar_muted"], font=("Segoe UI", 10))
    style.configure("Error.TLabel", background=COLORS["surface"], foreground=COLORS["danger"], font=("Segoe UI", 9))


def format_value(value) -> str:
    """Formata para exibicao: datas dd/mm/aaaa, valores no padrao brasileiro, booleanos como Sim/Nao."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Sim" if value else "Nao"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, Decimal):
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(value)
