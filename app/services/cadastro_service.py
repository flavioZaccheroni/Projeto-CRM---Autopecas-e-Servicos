from decimal import Decimal

from app.models.categoria_produto import CategoriaProduto
from app.models.cliente import Cliente
from app.models.fornecedor import Fornecedor
from app.models.marca_produto import MarcaProduto
from app.models.produto import Produto
from app.models.veiculo import Veiculo
from app.repositories.cadastro_repository import (
    CategoriaProdutoRepository,
    ClienteRepository,
    FornecedorRepository,
    MarcaProdutoRepository,
    ProdutoRepository,
    VeiculoRepository,
)
from app.utils.validators import validar_email_opcional, validar_obrigatorio


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
        item_id = _id(dados)
        existente = self.repository.buscar_por_cpf_cnpj(dados["cpf_cnpj"].strip())
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
        item_id = _id(dados)
        existente = self.repository.buscar_por_placa(dados["placa"].strip().upper())
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
        item_id = _id(dados)
        existente = self.repository.buscar_por_cnpj(dados["cnpj"].strip())
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


def _aplicar(objeto, dados: dict, campos: list[str]) -> None:
    for campo in campos:
        valor = dados.get(campo)
        if campo.endswith("_id") or campo in {"ano", "km_atual"}:
            valor = int(valor) if valor not in (None, "") else None
        elif campo in {"preco_custo", "preco_venda", "estoque_minimo"}:
            valor = Decimal(str(valor or 0).replace(",", "."))
        elif campo == "ativo":
            valor = bool(valor)
        elif isinstance(valor, str):
            valor = valor.strip()
        setattr(objeto, campo, valor)


def _id(dados: dict) -> int | None:
    valor = dados.get("id")
    return int(valor) if valor not in (None, "") else None
