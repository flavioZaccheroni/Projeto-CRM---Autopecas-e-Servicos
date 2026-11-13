import html
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def export_xlsx(path: Path, title: str, headers: list[str], rows: list[list[object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    worksheet = _worksheet_xml(title, headers, rows)
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types())
        archive.writestr("_rels/.rels", _root_rels())
        archive.writestr("xl/workbook.xml", _workbook_xml(title))
        archive.writestr("xl/_rels/workbook.xml.rels", _workbook_rels())
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
    return path


def export_pdf(path: Path, title: str, headers: list[str], rows: list[list[object]]) -> Path:
    lines = [title, "", " | ".join(headers)]
    lines.extend(" | ".join(_pdf_text(value) for value in row) for row in rows)
    return export_pdf_linhas(path, lines)


def export_pdf_linhas(path: Path, lines: list[str], logo: Path | None = None) -> Path:
    """Gera um PDF simples com uma linha de texto por item de `lines` (42 linhas por pagina).

    `logo` (JPEG) e desenhado no canto superior direito da primeira pagina; se ilegivel, e ignorado.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    title = lines[0] if lines else "Documento"
    pages = [lines[index : index + 42] for index in range(0, len(lines), 42)] or [[title]]
    imagem = _ler_jpeg(logo)

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    page_refs = " ".join(f"{3 + index * 2} 0 R" for index in range(len(pages)))
    objects.append(f"<< /Type /Pages /Kids [{page_refs}] /Count {len(pages)} >>".encode("latin-1"))
    id_imagem = 3 + len(pages) * 2
    for page_index, page_lines in enumerate(pages):
        page_obj = 3 + page_index * 2
        content_obj = page_obj + 1
        com_logo = imagem is not None and page_index == 0
        xobject = f"/XObject << /Im1 {id_imagem} 0 R >> " if com_logo else ""
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> {xobject}>> "
                f"/Contents {content_obj} 0 R >>"
            ).encode("latin-1")
        )
        stream = _content_stream(page_lines)
        if com_logo:
            stream = _desenho_logo(imagem[0], imagem[1]) + "\n" + stream
        dados = stream.encode("latin-1", errors="replace")
        objects.append(b"<< /Length " + str(len(dados)).encode() + b" >>\nstream\n" + dados + b"\nendstream")
    if imagem is not None:
        largura, altura, bruto = imagem
        objects.append(
            f"<< /Type /XObject /Subtype /Image /Width {largura} /Height {altura} /ColorSpace /DeviceRGB "
            f"/BitsPerComponent 8 /Filter /DCTDecode /Length {len(bruto)} >>\nstream\n".encode("latin-1")
            + bruto
            + b"\nendstream"
        )

    offsets: list[int] = []
    pdf = b"%PDF-1.4\n"
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{index} 0 obj\n".encode("latin-1") + obj + b"\nendobj\n"
    xref_offset = len(pdf)
    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n" + "".join(f"{offset:010d} 00000 n \n" for offset in offsets)
    pdf += xref.encode("latin-1")
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode("latin-1")
    path.write_bytes(pdf)
    return path


LOGO_MAX_PT = (150, 55)  # largura x altura maximas do logo na pagina (pontos)


def _ler_jpeg(caminho: Path | None):
    """(largura, altura, bytes) de um JPEG RGB valido, ou None."""
    if not caminho:
        return None
    try:
        bruto = Path(caminho).read_bytes()
    except OSError:
        return None
    if not bruto.startswith(b"\xff\xd8"):
        return None
    posicao = 2
    while posicao + 9 < len(bruto):
        if bruto[posicao] != 0xFF:
            posicao += 1
            continue
        marcador = bruto[posicao + 1]
        if marcador in (0xC0, 0xC1, 0xC2):
            if bruto[posicao + 9] != 3:  # so RGB (3 componentes)
                return None
            altura = int.from_bytes(bruto[posicao + 5 : posicao + 7], "big")
            largura = int.from_bytes(bruto[posicao + 7 : posicao + 9], "big")
            return (largura, altura, bruto) if largura and altura else None
        posicao += 2 + int.from_bytes(bruto[posicao + 2 : posicao + 4], "big")
    return None


def _desenho_logo(largura: int, altura: int) -> str:
    fator = min(LOGO_MAX_PT[0] / largura, LOGO_MAX_PT[1] / altura)
    w, h = largura * fator, altura * fator
    return f"q {w:.1f} 0 0 {h:.1f} {545 - w:.1f} {827 - h:.1f} cm /Im1 Do Q"


def _worksheet_xml(title: str, headers: list[str], rows: list[list[object]]) -> str:
    all_rows = [[title], [], headers, *rows]
    rows_xml = []
    for row_index, row in enumerate(all_rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            cell_ref = f"{_column_name(col_index)}{row_index}"
            text = html.escape("" if value is None else str(value))
            cells.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{text}</t></is></c>')
        rows_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(rows_xml)}</sheetData>"
        "</worksheet>"
    )


def _content_types() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )


def _root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def _workbook_xml(title: str) -> str:
    safe_title = html.escape(title[:31] or "Relatorio")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{safe_title}" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )


def _workbook_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _content_stream(lines: list[str]) -> str:
    content = ["BT", "/F1 10 Tf", "50 800 Td", "14 TL"]
    for line in lines:
        content.append(f"({_escape_pdf(line[:110])}) Tj")
        content.append("T*")
    content.append("ET")
    return "\n".join(content)


def _escape_pdf(value: str) -> str:
    return _pdf_text(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_text(value) -> str:
    return "" if value is None else str(value)
