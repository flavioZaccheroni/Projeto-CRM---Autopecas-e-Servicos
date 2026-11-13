"""Identificador do computador para licencas vinculadas (opcional)."""

from __future__ import annotations

import hashlib
import uuid


def _guid_da_maquina() -> str:
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as chave:
            return str(winreg.QueryValueEx(chave, "MachineGuid")[0])
    except (ImportError, OSError):
        return f"mac-{uuid.getnode():012x}"


def codigo_da_maquina() -> str:
    """Codigo curto e estavel (XXXX-XXXX-XXXX) derivado do identificador do Windows. Nao revela o GUID original."""
    resumo = hashlib.sha256(f"erp-autopecas|{_guid_da_maquina()}".encode()).hexdigest().upper()[:12]
    return "-".join(resumo[i : i + 4] for i in range(0, 12, 4))
