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
    style.map("Primary.TButton", background=[("active", COLORS["primary_dark"])])
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


def format_value(value) -> str:
    if value is None:
        return ""
    return str(value)
