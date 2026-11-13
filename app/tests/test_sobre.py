from datetime import datetime

from app.config import settings
from app.services.sobre_service import coletar_informacoes, texto_para_suporte


def test_informacoes_basicas_e_texto_de_suporte():
    info = coletar_informacoes({"ultimo": datetime(2026, 11, 12, 20, 30), "auto": True})
    assert info["versao"] == settings.APP_VERSION
    assert info["modo"].startswith("Código-fonte")
    assert info["ultimo_backup"] == "12/11/2026 20:30"
    assert info["backup_automatico"] == "ligado"

    texto = texto_para_suporte(info)
    assert settings.APP_VERSION in texto
    assert "Último backup: 12/11/2026 20:30" in texto
    assert str(settings.BACKUPS_DIR) in texto


def test_sem_situacao_de_backup_nao_quebra():
    info = coletar_informacoes(None)
    assert info["ultimo_backup"] == "nenhum backup ainda"
    assert info["backup_automatico"] == "não informado"
    assert info["tamanho_banco"]  # texto, mesmo sem banco


def test_texto_de_suporte_nao_vaza_dados_sensiveis():
    texto = texto_para_suporte(coletar_informacoes({"ultimo": None, "auto": False})).lower()
    for proibido in ("senha", "password", "cpf"):
        assert proibido not in texto
