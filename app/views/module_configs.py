from app.utils.validators import UFS
from app.controllers.cadastro_controller import (
    CategoriaProdutoController,
    ClienteController,
    FornecedorController,
    MarcaProdutoController,
    ProdutoController,
    VeiculoController,
)


CADASTRO_MODULES = {
    "Clientes": {
        "controller": ClienteController,
        "fields": [
            {"name": "nome", "label": "Nome"},
            {"name": "tipo_pessoa", "label": "Tipo pessoa", "choices": ["PF", "PJ"], "readonly": True},
            {"name": "cpf_cnpj", "label": "CPF/CNPJ"},
            {"name": "telefone", "label": "Telefone"},
            {"name": "email", "label": "E-mail"},
            {"name": "endereco", "label": "Endereco"},
            {"name": "cidade", "label": "Cidade"},
            {"name": "uf", "label": "UF", "choices": sorted(UFS)},
            {"name": "ativo", "label": "Ativo", "type": "bool"},
        ],
        "columns": ["id", "nome", "tipo_pessoa", "cpf_cnpj", "telefone", "ativo"],
    },
    "Veiculos": {
        "controller": VeiculoController,
        "fields": [
            {"name": "cliente_id", "label": "Cliente", "lookup": "clientes"},
            {"name": "placa", "label": "Placa"},
            {"name": "marca", "label": "Marca"},
            {"name": "modelo", "label": "Modelo"},
            {"name": "ano", "label": "Ano"},
            {"name": "km_atual", "label": "KM atual"},
            {"name": "observacoes", "label": "Observacoes"},
        ],
        "columns": ["id", "cliente.nome", "placa", "marca", "modelo", "ano", "km_atual"],
    },
    "Fornecedores": {
        "controller": FornecedorController,
        "fields": [
            {"name": "razao_social", "label": "Razao social"},
            {"name": "nome_fantasia", "label": "Nome fantasia"},
            {"name": "cnpj", "label": "CNPJ"},
            {"name": "telefone", "label": "Telefone"},
            {"name": "email", "label": "E-mail"},
            {"name": "ativo", "label": "Ativo", "type": "bool"},
        ],
        "columns": ["id", "razao_social", "nome_fantasia", "cnpj", "telefone", "ativo"],
    },
    "Categorias": {
        "controller": CategoriaProdutoController,
        "fields": [
            {"name": "nome", "label": "Nome"},
            {"name": "descricao", "label": "Descricao"},
            {"name": "ativo", "label": "Ativo", "type": "bool"},
        ],
        "columns": ["id", "nome", "descricao", "ativo"],
    },
    "Marcas": {
        "controller": MarcaProdutoController,
        "fields": [
            {"name": "nome", "label": "Nome"},
            {"name": "ativo", "label": "Ativo", "type": "bool"},
        ],
        "columns": ["id", "nome", "ativo"],
    },
    "Produtos": {
        "controller": ProdutoController,
        "fields": [
            {"name": "codigo", "label": "Codigo"},
            {"name": "descricao", "label": "Descricao"},
            {"name": "categoria_id", "label": "Categoria", "lookup": "categorias"},
            {"name": "marca_id", "label": "Marca", "lookup": "marcas"},
            {"name": "ncm", "label": "NCM"},
            {"name": "unidade", "label": "Unidade", "choices": ["UN", "PC", "CX", "KG", "L", "M", "JG"]},
            {"name": "preco_custo", "label": "Preco custo"},
            {"name": "preco_venda", "label": "Preco venda"},
            {"name": "estoque_minimo", "label": "Estoque minimo"},
            {"name": "ativo", "label": "Ativo", "type": "bool"},
        ],
        "columns": ["id", "codigo", "descricao", "categoria.nome", "marca.nome", "preco_venda", "estoque_minimo"],
    },
}
