from PySide6.QtGui import QColor, QImage

from app.reports.exporters import _ler_jpeg, export_pdf_linhas
from app.utils.logo import caminho_logo, remover_logo, salvar_logo


def _png(caminho, largura=900, altura=300):
    imagem = QImage(largura, altura, QImage.Format.Format_ARGB32)
    imagem.fill(QColor(0, 0, 0, 0))  # transparente
    assert imagem.save(str(caminho), "PNG")
    return caminho


def test_salvar_logo_reduz_converte_e_remove(tmp_path):
    origem = _png(tmp_path / "entrada.png")
    pasta = tmp_path / "dados"
    assert caminho_logo(pasta) is None
    destino = salvar_logo(origem, pasta)
    assert destino.suffix == ".jpg" and caminho_logo(pasta) == destino
    largura, altura, _ = _ler_jpeg(destino)
    assert (largura, altura) == (600, 200)  # lado maior limitado a 600 px, proporcao mantida
    assert remover_logo(pasta) is True and caminho_logo(pasta) is None
    assert remover_logo(pasta) is False


def test_logo_invalido_vira_erro_amigavel(tmp_path):
    arquivo = tmp_path / "x.png"
    arquivo.write_text("nao e imagem")
    import pytest

    with pytest.raises(ValueError, match="abrir a imagem"):
        salvar_logo(arquivo, tmp_path / "d")


def test_pdf_com_logo_embute_a_imagem_e_sem_logo_continua_igual(tmp_path):
    logo = salvar_logo(_png(tmp_path / "l.png"), tmp_path / "d")
    com = export_pdf_linhas(tmp_path / "com.pdf", ["Empresa", "Documento"], logo=logo).read_bytes()
    sem = export_pdf_linhas(tmp_path / "sem.pdf", ["Empresa", "Documento"]).read_bytes()
    assert b"/Subtype /Image" in com and b"/Im1 Do" in com and com.rstrip().endswith(b"%%EOF")
    # objeto da imagem bem formado: dicionario fechado, 'stream', bytes JPEG, 'endstream'
    assert b"/DCTDecode /Length " in com and b" >>\nstream\n\xff\xd8" in com and b"\nendstream\nendobj" in com
    # tabela xref aponta para o inicio real de cada objeto
    posicao_xref = int(com.rsplit(b"startxref", 1)[1].split()[0])
    assert com[posicao_xref : posicao_xref + 4] == b"xref"
    for numero, linha in enumerate(com[posicao_xref:].split(b"\n")[3:8], start=1):
        deslocamento = int(linha.split()[0])
        assert com[deslocamento:].startswith(f"{numero} 0 obj".encode())
    assert b"/Subtype /Image" not in sem and sem.startswith(b"%PDF")
    # logo ilegivel e ignorado
    ruim = tmp_path / "ruim.jpg"
    ruim.write_bytes(b"lixo")
    assert b"/Subtype /Image" not in export_pdf_linhas(tmp_path / "r.pdf", ["A"], logo=ruim).read_bytes()
