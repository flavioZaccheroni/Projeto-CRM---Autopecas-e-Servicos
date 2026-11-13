from decimal import Decimal, InvalidOperation

from app.models.categoria_produto import CategoriaProduto
from app.models.cliente import Cliente
from app.models.fornecedor import Fornecedor
from app.models.marca_produto import MarcaProduto
from app.models.produto import Produto
from app.models.servico import Servico
from app.models.veiculo import Veiculo
from app.repositories.cadastro_repository import (
    CategoriaProdutoRepository,
    ClienteRepository,
    FornecedorRepository,
    MarcaProdutoRepository,
    ProdutoRepository,
    ServicoRepository,
    VeiculoRepository,
)
from app.utils.validators import (
    somente_digitos,
    validar_cpf_cnpj,
    validar_email_opcional,
    validar_obrigatorio,
    validar_placa,
    validar_telefone_opcional,
    validar_uf_opcional,
)


class ClienteService:
    def __init__(self, repository: ClienteRepository) -> None:
        self.repository = repository

    def listar(self) -> list[Cliente]:
        return self.repository.listar()

    def salvar(self, dados: dict) -> Cliente:
        validar_obrigatorio(dados.get("nome"), "Nome")
        validar_obrigatorio(dados.get("tipo_pessoa"), "Tipo pessoa")
        validar_obrigatorio(dados.get("cpf_cnpj"), "CPF/CNPJ")
        validar_email_opcional(dados.get("email"))
        validar_cpf_cnpj(dados["cpf_cnpj"], dados.get("tipo_pessoa"))
        validar_telefone_opcional(dados.get("telefone"))
        validar_uf_opcional(dados.get("uf"))
        dados = {**dados, "cpf_cnpj": somente_digitos(dados["cpf_cnpj"])}
        item_id = _id(dados)
        existente = self.repository.buscar_por_cpf_cnpj(dados["cpf_cnpj"])
        if existente and existente.id != item_id:
            raise ValueError("CPF/CNPJ ja cadastrado.")
        cliente = self.repository.buscar_por_id(item_id) if item_id else Cliente()
        _aplicar(cliente, dados, ["nome", "tipo_pessoa", "cpf_cnpj", "telefone", "email", "endereco", "cidade", "uf", "ativo"])
        return self.repository.salvar(cliente)


class VeiculoService:
    def __init__(self, repository: VeiculoRepository) -> None:
        self.repository = repository

    def listar(self) -> list[Veiculo]:
        return self.repository.listar()

    def salvar(self, dados: dict) -> Veiculo:
        validar_obrigatorio(dados.get("cliente_id"), "Cliente")
        validar_obrigatorio(dados.get("placa"), "Placa")
        validar_placa(dados["placa"])
        dados = {**dados, "placa": dados["placa"].strip().upper().replace("-", "")}
        item_id = _id(dados)
        existente = self.repository.buscar_por_placa(dados["placa"])
        if existente and existente.id != item_id:
            raise ValueError("Placa ja cadastrada.")
        veiculo = self.repository.buscar_por_id(item_id) if item_id else Veiculo()
        _aplicar(veiculo, dados, ["cliente_id", "placa", "marca", "modelo", "ano", "km_atual", "observacoes"])
        veiculo.placa = veiculo.placa.upper()
        return self.repository.salvar(veiculo)


class FornecedorService:
    def __init__(self, repository: FornecedorRepository) -> None:
        self.repository = repository

    def listar(self) -> list[Fornecedor]:
        return self.repository.listar()

    def salvar(self, dados: dict) -> Fornecedor:
        validar_obrigatorio(dados.get("razao_social"), "Razao social")
        validar_obrigatorio(dados.get("cnpj"), "CNPJ")
        validar_email_opcional(dados.get("email"))
        validar_cpf_cnpj(dados["cnpj"], "PJ")
        validar_telefone_opcional(dados.get("telefone"))
        dados = {**dados, "cnpj": somente_digitos(dados["cnpj"])}
        item_id = _id(dados)
        existente = self.repository.buscar_por_cnpj(dados["cnpj"])
        if existente and existente.id != item_id:
            raise ValueError("CNPJ ja cadastrado.")
        fornecedor = self.repository.buscar_por_id(item_id) if item_id else Fornecedor()
        _aplicar(fornecedor, dados, ["razao_social", "nome_fantasia", "cnpj", "telefone", "email", "ativo"])
        return self.repository.salvar(fornecedor)


class CategoriaProdutoService:
    def __init__(self, repository: CategoriaProdutoRepository) -> None:
        self.repository = repository

    def listar(self) -> list[CategoriaProduto]:
        return self.repository.listar()

    def salvar(self, dados: dict) -> CategoriaProduto:
        validar_obrigatorio(dados.get("nome"), "Nome")
        item_id = _id(dados)
        existente = self.repository.buscar_por_nome(dados["nome"].strip())
        if existente and existente.id != item_id:
            raise ValueError("Categoria ja cadastrada.")
        categoria = self.repository.buscar_por_id(item_id) if item_id else CategoriaProduto()
        _aplicar(categoria, dados, ["nome", "descricao", "ativo"])
        return self.repository.salvar(categoria)


class MarcaProdutoService:
    def __init__(self, repository: MarcaProdutoRepository) -> None:
        self.repository = repository

    def listar(self) -> list[MarcaProduto]:
        return self.repository.listar()

    def salvar(self, dados: dict) -> MarcaProduto:
        validar_obrigatorio(dados.get("nome"), "Nome")
        item_id = _id(dados)
        existente = self.repository.buscar_por_nome(dados["nome"].strip())
        if existente and existente.id != item_id:
            raise ValueError("Marca ja cadastrada.")
        marca = self.repository.buscar_por_id(item_id) if item_id else MarcaProduto()
        _aplicar(marca, dados, ["nome", "ativo"])
        return self.repository.salvar(marca)


class ProdutoService:
    def __init__(self, repository: ProdutoRepository) -> None:
        self.repository = repository

    def listar(self) -> list[Produto]:
        return self.repository.listar()

    def salvar(self, dados: dict) -> Produto:
        validar_obrigatorio(dados.get("codigo"), "Codigo")
        validar_obrigatorio(dados.get("descricao"), "Descricao")
        item_id = _id(dados)
        existente = self.repository.buscar_por_codigo(dados["codigo"].strip())
        if existente and existente.id != item_id:
            raise ValueError("Codigo de produto ja cadastrado.")
        produto = self.repository.buscar_por_id(item_id) if item_id else Produto()
        _aplicar(produto, dados, ["codigo", "descricao", "categoria_id", "marca_id", "ncm", "unidade", "preco_custo", "preco_venda", "estoque_minimo", "ativo"])
        return self.repository.salvar(produto)


class ServicoService:
    def __init__(self, repository: ServicoRepository) -> None:
        self.repository = repository

    def listar(self) -> list[Servico]:
        return self.repository.listar()

    def salvar(self, dados: dict) -> Servico:
        validar_obrigatorio(dados.get("nome"), "Nome")
        preco = str(dados.get("preco_padrao") or "0").strip().replace(",", ".")
        try:
            if Decimal(preco) < 0:
                raise ValueError("Preco padrao nao pode ser negativo.")
        except InvalidOperation:
            raise ValueError("Preco padrao numerico invalido.") from None
        tempo = str(dados.get("tempo_estimado_min") or "").strip()
        if tempo and (not tempo.isdigit() or int(tempo) <= 0):
            raise ValueError("Tempo estimado deve ser um numero inteiro de minutos.")
        item_id = _id(dados)
        existente = self.repository.buscar_por_nome(dados["nome"].strip())
        if existente and existente.id != item_id:
            raise ValueError("Servico ja cadastrado.")
        servico = self.repository.buscar_por_id(item_id) if item_id else Servico()
        _aplicar(servico, dados, ["nome", "descricao", "preco_padrao", "tempo_estimado_min", "ativo"])
        return self.repository.salvar(servico)


def _aplicar(objeto, dados: dict, campos: list[str]) -> None:
    for campo in campos:
        valor = dados.get(campo)
        if campo.endswith("_id") or campo in {"ano", "km_atual", "tempo_estimado_min"}:
            valor = int(valor) if valor not in (None, "") else None
        elif campo in {"preco_custo", "preco_venda", "estoque_minimo", "preco_padrao"}:
            valor = Decimal(str(valor or 0).replace(",", "."))
        elif campo == "ativo":
            valor = bool(valor)
        elif isinstance(valor, str):
            valor = valor.strip()
        setattr(objeto, campo, valor)


def _id(dados: dict) -> int | None:
    valor = dados.get("id")
    return int(valor) if valor not in (None, "") else None
