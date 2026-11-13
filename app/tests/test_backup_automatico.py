import os
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

from app.config.settings import resolver_raiz
from app.repositories.seguranca_repository import AuditoriaRepository, ConfiguracaoRepository
from app.services.seguranca_service import (
    AuditoriaService,
    BackupService,
    ConfiguracaoService,
    ler_parametros_backup,
)


def _banco(caminho: Path) -> None:
    conexao = sqlite3.connect(caminho)
    for tabela in ("usuarios", "perfis", "permissoes", "clientes", "produtos", "vendas"):
        conexao.execute(f"CREATE TABLE {tabela} (id INTEGER PRIMARY KEY, valor TEXT)")
    conexao.execute("INSERT INTO usuarios (valor) VALUES ('x')")
    conexao.commit()
    conexao.close()


def _tocar(arquivo: Path, quando: datetime) -> None:
    carimbo = quando.timestamp()
    os.utime(arquivo, (carimbo, carimbo))


def _servico(session, tmp_path):
    _banco(tmp_path / "erp.db")
    auditoria = AuditoriaService(AuditoriaRepository(session))
    return BackupService(auditoria, database_file=tmp_path / "erp.db", backup_dir=tmp_path / "backups")


# -- pasta de dados -------------------------------------------------------------------------
def test_raiz_codigo_fonte_usa_a_pasta_do_projeto(tmp_path):
    assert resolver_raiz(False, pasta_codigo=tmp_path, ambiente={}) == tmp_path


def test_raiz_executavel_com_pasta_data_continua_portatil(tmp_path):
    (tmp_path / "data").mkdir()
    assert resolver_raiz(True, pasta_exe=tmp_path, ambiente={"LOCALAPPDATA": str(tmp_path / "local")}) == tmp_path


def test_raiz_executavel_com_portable_flag_e_portatil(tmp_path):
    (tmp_path / "portable.flag").write_text("")
    assert resolver_raiz(True, pasta_exe=tmp_path, ambiente={"LOCALAPPDATA": str(tmp_path / "local")}) == tmp_path


def test_raiz_executavel_instalado_usa_pasta_do_usuario(tmp_path):
    instalado = tmp_path / "Program Files" / "ERP"
    instalado.mkdir(parents=True)
    local = tmp_path / "AppData" / "Local"
    assert resolver_raiz(True, pasta_exe=instalado, ambiente={"LOCALAPPDATA": str(local)}) == local / "ERP_Autopecas"


def test_raiz_erp_home_tem_prioridade(tmp_path):
    destino = tmp_path / "meus-dados"
    assert resolver_raiz(True, pasta_exe=tmp_path, ambiente={"ERP_HOME": str(destino)}) == destino.resolve()


# -- parametros -----------------------------------------------------------------------------
def test_parametros_padrao_sao_seguros(session):
    parametros = ler_parametros_backup(ConfiguracaoService(ConfiguracaoRepository(session)))
    assert parametros == {"auto": True, "pasta_extra": None, "manter": 15, "alerta_dias": 7}


def test_parametros_configurados_e_valores_invalidos(session):
    config = ConfiguracaoService(ConfiguracaoRepository(session))
    config.salvar("backup.auto", "nao")
    config.salvar("backup.manter", "abc")
    config.salvar("backup.alerta_dias", "9999")
    config.salvar("backup.pasta_extra", " D:\\Backups ")
    parametros = ler_parametros_backup(config)
    assert parametros["auto"] is False
    assert parametros["manter"] == 15  # invalido volta ao padrao
    assert parametros["alerta_dias"] == 365  # limitado ao maximo
    assert parametros["pasta_extra"] == "D:\\Backups"


# -- quando criar ---------------------------------------------------------------------------
def test_sem_nenhum_backup_cria_ao_abrir_e_ao_sair(session, tmp_path):
    service = _servico(session, tmp_path)
    assert service.precisa_backup_automatico("abrir") is True
    assert service.precisa_backup_automatico("sair") is True


def test_sem_banco_nao_cria(session, tmp_path):
    auditoria = AuditoriaService(AuditoriaRepository(session))
    service = BackupService(auditoria, database_file=tmp_path / "nao_existe.db", backup_dir=tmp_path / "b")
    assert service.precisa_backup_automatico("abrir") is False


def test_nao_repete_backup_sem_alteracoes(session, tmp_path):
    service = _servico(session, tmp_path)
    service.backup_automatico()
    futuro = datetime.now() + timedelta(days=3)
    # banco nao mudou desde o backup: nem apos dias sem usar
    assert service.precisa_backup_automatico("abrir", agora=futuro) is False
    assert service.precisa_backup_automatico("sair", agora=futuro) is False


def test_abrir_exige_24h_e_sair_exige_1h_quando_ha_alteracoes(session, tmp_path):
    service = _servico(session, tmp_path)
    arquivo, _ = service.backup_automatico()
    agora = datetime.now()
    _tocar(arquivo, agora - timedelta(hours=2))
    _tocar(tmp_path / "erp.db", agora)  # banco alterado depois do backup
    assert service.precisa_backup_automatico("sair", agora=agora) is True  # >= 1 h
    assert service.precisa_backup_automatico("abrir", agora=agora) is False  # < 24 h
    _tocar(arquivo, agora - timedelta(hours=25))
    assert service.precisa_backup_automatico("abrir", agora=agora) is True


def test_sair_nao_cria_mais_de_um_por_hora(session, tmp_path):
    service = _servico(session, tmp_path)
    arquivo, _ = service.backup_automatico()
    agora = datetime.now()
    _tocar(arquivo, agora - timedelta(minutes=10))
    _tocar(tmp_path / "erp.db", agora)
    assert service.precisa_backup_automatico("sair", agora=agora) is False


# -- criacao, retencao e pasta extra --------------------------------------------------------
def test_backup_automatico_cria_arquivo_valido_e_audita(session, tmp_path):
    service = _servico(session, tmp_path)
    arquivo, aviso = service.backup_automatico()
    assert aviso is None
    assert arquivo.name.startswith("auto_")
    assert service.validar_backup(arquivo) == arquivo
    assert AuditoriaService(AuditoriaRepository(session)).listar()[0].acao == "CRIAR_AUTO"


def test_retencao_apaga_so_automaticos_antigos(session, tmp_path):
    service = _servico(session, tmp_path)
    manual = service.criar_backup()
    for _ in range(5):
        service.backup_automatico(manter=3)
        time.sleep(0.01)
    pasta = tmp_path / "backups"
    automaticos = sorted(pasta.glob("auto_*.db"))
    assert len(automaticos) == 3
    assert manual.exists()  # backup manual nunca e apagado
    assert len(list(pasta.glob("erp_autopecas_*.db"))) == 1


def test_copia_na_pasta_extra_com_retencao(session, tmp_path):
    service = _servico(session, tmp_path)
    extra = tmp_path / "nuvem" / "erp"
    for _ in range(4):
        _, aviso = service.backup_automatico(manter=2, pasta_extra=extra)
        assert aviso is None
        time.sleep(0.01)
    assert len(list(extra.glob("auto_*.db"))) == 2


def test_falha_na_pasta_extra_nao_derruba_o_backup(session, tmp_path):
    service = _servico(session, tmp_path)
    ocupado = tmp_path / "arquivo_no_lugar_da_pasta"
    ocupado.write_text("x")  # nao e possivel criar pasta dentro de um arquivo
    arquivo, aviso = service.backup_automatico(pasta_extra=ocupado / "sub")
    assert arquivo.exists()
    assert aviso and "Nao foi possivel copiar" in aviso


def test_ultimo_backup_e_dias_sem_backup(session, tmp_path):
    service = _servico(session, tmp_path)
    assert service.ultimo_backup() is None
    assert service.dias_sem_backup() is None
    arquivo, _ = service.backup_automatico()
    _tocar(arquivo, datetime.now() - timedelta(days=10, hours=1))
    assert service.dias_sem_backup() == 10
    # copia de seguranca da restauracao nao conta como backup do cliente
    (tmp_path / "backups" / "pre_restore_x.db").write_bytes(b"")
    assert service.dias_sem_backup() == 10
