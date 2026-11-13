"""Logo da empresa: salvo como JPEG reduzido na pasta de dados e usado no cabecalho dos PDFs."""

from pathlib import Path

from app.config.settings import DATA_DIR

NOME_ARQUIVO = "logo_empresa.jpg"
LADO_MAXIMO = 600  # pixels: suficiente para impressao e mantem o PDF leve


def caminho_logo(pasta: Path = DATA_DIR) -> Path | None:
    arquivo = pasta / NOME_ARQUIVO
    return arquivo if arquivo.is_file() else None


def salvar_logo(origem: str | Path, pasta: Path = DATA_DIR) -> Path:
    """Converte a imagem escolhida (PNG, JPG, BMP...) em JPEG reduzido sobre fundo branco."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QImage, QPainter

    imagem = QImage(str(origem))
    if imagem.isNull():
        raise ValueError("Nao foi possivel abrir a imagem. Use um arquivo PNG, JPG ou BMP.")
    if max(imagem.width(), imagem.height()) > LADO_MAXIMO:
        imagem = imagem.scaled(LADO_MAXIMO, LADO_MAXIMO, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    fundo = QImage(imagem.size(), QImage.Format.Format_RGB32)
    fundo.fill(QColor("white"))  # transparencia vira branco
    pintor = QPainter(fundo)
    pintor.drawImage(0, 0, imagem)
    pintor.end()
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / NOME_ARQUIVO
    if not fundo.save(str(destino), "JPG", 90):
        raise ValueError("Nao foi possivel gravar o logo na pasta de dados.")
    return destino


def remover_logo(pasta: Path = DATA_DIR) -> bool:
    arquivo = pasta / NOME_ARQUIVO
    if arquivo.is_file():
        arquivo.unlink()
        return True
    return False
