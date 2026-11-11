"""Gera uma base de demonstracao com dados 100% ficticios (clientes, produtos, vendas, OS, financeiro).

Uso:
    python scripts/gerar_demo.py            # cria demo/erp_autopecas.db
    python scripts/gerar_demo.py --recriar  # apaga e recria a base de demo

Para abrir o sistema com essa base (PowerShell):
    $env:ERP_DATA_DIR = "demo"; python main.py
Acesso: admin / Demo@1234  (ou vendedor / Demo@1234)
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DEMO_DIR = ROOT_DIR / "demo"
SENHA_DEMO = "Demo@1234"


def _dv(digitos: list[int], pesos: list[int]) -> int:
    resto = sum(d * p for d, p in zip(digitos, pesos, strict=True)) % 11
    return 0 if resto < 2 else 11 - resto


def cpf(base: int) -> str:
    d = [int(c) for c in f"{base:09d}"]
    d.append(_dv(d, list(range(10, 1, -1))))
    d.append(_dv(d, list(range(11, 1, -1))))
    return "".join(map(str, d))


def cnpj(base: int) -> str:
    d = [int(c) for c in f"{base:08d}0001"]
    d.append(_dv(d, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]))
    d.append(_dv(d, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]))
    return "".join(map(str, d))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recriar", action="store_true", help="Apaga a base de demo existente.")
    args = parser.parse_args()

    os.environ["ERP_DATA_DIR"] = str(DEMO_DIR)
    sys.path.insert(0, str(ROOT_DIR))
    banco = DEMO_DIR / "erp_autopecas.db"
    if banco.exists():
        if not args.recriar:
            print(f"{banco} ja existe. Use --recriar para gerar de novo.")
            return 1
        banco.unlink()

    from app.controllers.auth_controller import AuthController
    from app.controllers.cadastro_controller import (
        CategoriaProdutoController,
        ClienteController,
        FornecedorController,
        MarcaProdutoController,
        ProdutoController,
        VeiculoController,
    )
    from app.controllers.compra_controller import CompraController
    from app.controllers.financeiro_controller import FinanceiroController
    from app.controllers.os_controller import OrdemServicoController
    from app.controllers.usuario_controller import UsuarioController
    from app.controllers.venda_controller import VendaController
    from app.database.init_db import initialize_database

    rnd = random.Random(42)
    hoje = date.today()
    initialize_database()
    auth = AuthController()
    admin = auth.autenticar("admin", "admin123")
    auth.trocar_senha(admin.id, "admin123", SENHA_DEMO)
    auth.encerrar_sessao()
    admin = auth.autenticar("admin", SENHA_DEMO)
    usuarios = UsuarioController()
    perfis = {p.nome: p.id for p in usuarios.listar_perfis()}
    usuarios.criar("Carla Vendedora", "carla@demo.test", "vendedor", SENHA_DEMO, perfis["Vendedor"])

    categorias = ["Filtros", "Freios", "Suspensao", "Motor", "Eletrica", "Lubrificantes"]
    marcas = ["Bosch", "Mahle", "Cofap", "NGK", "Valeo", "Fras-le"]
    for nome in categorias:
        CategoriaProdutoController().salvar({"nome": nome, "ativo": True})
    for nome in marcas:
        MarcaProdutoController().salvar({"nome": nome, "ativo": True})

    # (codigo, descricao, categoria_id, marca_id, custo, preco de venda)
    produtos = [
        ("FO-001", "Filtro de oleo", 1, 2, 18, 39.9),
        ("FA-002", "Filtro de ar", 1, 2, 24, 52.0),
        ("PF-010", "Pastilha de freio dianteira", 2, 6, 68, 139.9),
        ("DF-011", "Disco de freio ventilado", 2, 6, 120, 249.0),
        ("AM-020", "Amortecedor dianteiro", 3, 3, 190, 389.0),
        ("BC-021", "Bieleta da barra estabilizadora", 3, 3, 22, 59.9),
        ("VL-030", "Vela de ignicao", 4, 4, 14, 32.5),
        ("CD-031", "Correia dentada", 4, 5, 55, 119.0),
        ("BT-040", "Bateria 60Ah", 5, 5, 310, 519.0),
        ("LP-041", "Lampada H7", 5, 5, 16, 34.9),
        ("OL-050", "Oleo 5W30 sintetico 1L", 6, 1, 29, 54.9),
        ("AD-051", "Aditivo radiador 1L", 6, 1, 12, 27.9),
    ]
    for codigo, descricao, cat, marca, custo, preco in produtos:
        ProdutoController().salvar(
            {
                "codigo": codigo, "descricao": descricao, "categoria_id": cat, "marca_id": marca, "unidade": "UN",
                "preco_custo": custo, "preco_venda": preco, "estoque_minimo": 6, "ativo": True,
            }
        )

    fornecedores = [
        ("Distribuidora Pecas Sul Ltda", "Pecas Sul"),
        ("Auto Atacado Brasil S.A.", "AutoAtacado"),
        ("Eletro Motor Comercio Ltda", "EletroMotor"),
    ]
    for i, (razao, fantasia) in enumerate(fornecedores, start=1):
        FornecedorController().salvar(
            {"razao_social": razao, "nome_fantasia": fantasia, "cnpj": cnpj(10000000 + i * 111), "ativo": True}
        )

    nomes = ["Joao Almeida", "Maria Santos", "Carlos Pereira", "Ana Souza", "Pedro Lima", "Fernanda Costa", "Rafael Rocha", "Juliana Mendes"]
    modelos = [
        ("VW", "Gol", 2016), ("Fiat", "Palio", 2014), ("Chevrolet", "Onix", 2019), ("Ford", "Ka", 2018),
        ("Toyota", "Corolla", 2020), ("Honda", "Civic", 2017), ("Hyundai", "HB20", 2021), ("Renault", "Sandero", 2015),
    ]
    for i, nome in enumerate(nomes, start=1):
        ClienteController().salvar(
            {
                "nome": nome, "tipo_pessoa": "PF", "cpf_cnpj": cpf(123456000 + i * 7919),
                "telefone": f"119{rnd.randint(10000000, 99999999)}", "email": f"cliente{i}@demo.test",
                "cidade": "Sao Paulo", "uf": "SP", "ativo": True,
            }
        )
        marca, modelo, ano = modelos[i - 1]
        VeiculoController().salvar(
            {
                "cliente_id": i, "placa": f"DEM{i}A{rnd.randint(10, 99)}", "marca": marca, "modelo": modelo,
                "ano": ano, "km_atual": rnd.randint(20000, 140000),
            }
        )

    # compras: a primeira abastece todos os produtos; as demais repoem alguns itens
    compra = CompraController()
    for n, forn in enumerate((1, 2, 3, 1), start=1):
        data = hoje - timedelta(days=170 - n * 40)
        pedido = compra.criar_compra({"fornecedor_id": forn, "data_compra": data}, usuario_id=admin.id)
        escolhidos = range(1, len(produtos) + 1) if n == 1 else rnd.sample(range(1, len(produtos) + 1), 4)
        for produto_id in escolhidos:
            compra.adicionar_item(
                {
                    "compra_id": pedido.id, "produto_id": produto_id, "quantidade": 8 if n == 1 else rnd.randint(4, 8),
                    "valor_unitario": produtos[produto_id - 1][4],
                }
            )
        compra.receber_compra(pedido.id, usuario_id=admin.id, data_vencimento=data + timedelta(days=30), parcelas=rnd.choice((1, 2)))

    # vendas ao longo de ~6 meses (alimenta o grafico do dashboard)
    venda = VendaController()
    formas = ["PIX", "DINHEIRO", "CARTAO_CREDITO", "CARTAO_DEBITO", "BOLETO"]
    for n in range(28):
        data = datetime.combine(hoje - timedelta(days=rnd.randint(0, 165)), datetime.min.time()).replace(hour=rnd.randint(9, 17))
        v = venda.criar_venda({"cliente_id": rnd.randint(1, len(nomes)), "data_venda": data}, usuario_id=admin.id)
        for produto_id in rnd.sample(range(1, len(produtos) + 1), rnd.randint(1, 3)):
            venda.adicionar_item(
                {
                    "venda_id": v.id, "produto_id": produto_id, "quantidade": rnd.randint(1, 3),
                    "valor_unitario": produtos[produto_id - 1][5],
                }
            )
        if n % 9 == 8:
            venda.recusar_orcamento(v.id, "Cliente achou caro")
        elif n % 7 == 6:
            continue  # fica como orcamento em aberto
        else:
            venda.aprovar_orcamento(v.id)
            try:
                venda.finalizar_venda(
                    v.id, usuario_id=admin.id, data_vencimento=data.date() + timedelta(days=rnd.choice((0, 15, 30))),
                    parcelas=rnd.choice((1, 1, 2, 3)), forma_pagamento=rnd.choice(formas),
                )
            except ValueError:
                pass  # estoque insuficiente: a venda fica aprovada

    # ordens de servico
    os_ctrl = OrdemServicoController()
    defeitos = ["Barulho na suspensao", "Freio com ruido", "Revisao 30 mil km", "Luz da injecao acesa", "Motor falhando", "Troca de oleo e filtros"]
    for n in range(10):
        cliente = rnd.randint(1, len(nomes))
        abertura = datetime.combine(hoje - timedelta(days=rnd.randint(0, 120)), datetime.min.time()).replace(hour=10)
        ordem = os_ctrl.abrir_os(
            {"cliente_id": cliente, "veiculo_id": cliente, "defeito_relatado": defeitos[n % len(defeitos)], "data_abertura": abertura},
            usuario_id=admin.id,
        )
        os_ctrl.adicionar_item(
            {"os_id": ordem.id, "tipo": "SERVICO", "descricao": "Mao de obra", "quantidade": 1, "valor_unitario": rnd.choice((90, 150, 220, 320))}
        )
        produto_id = rnd.randint(1, len(produtos))
        os_ctrl.adicionar_item(
            {
                "os_id": ordem.id, "tipo": "PECA", "produto_id": produto_id, "descricao": produtos[produto_id - 1][1],
                "quantidade": 1, "valor_unitario": produtos[produto_id - 1][5],
            }
        )
        if n < 7:
            try:
                os_ctrl.finalizar_os(
                    ordem.id, usuario_id=admin.id, data_vencimento=hoje + timedelta(days=rnd.randint(-20, 25)),
                    parcelas=1, forma_pagamento=rnd.choice(formas),
                )
            except ValueError:
                pass

    # baixa de parte dos lancamentos e algumas despesas avulsas
    financeiro = FinanceiroController()
    for lanc in financeiro.listar_lancamentos():
        if lanc.data_vencimento <= hoje - timedelta(days=15):  # o que venceu ha mais de 15 dias ja foi pago
            financeiro.baixar_lancamento(lanc.id, rnd.choice(formas), usuario_id=admin.id)
    for descricao, valor, dias in (("Aluguel da oficina", 3200, 5), ("Energia eletrica", 780, 9), ("Internet", 160, -3)):
        financeiro.criar_lancamento(
            {"tipo": "PAGAR", "descricao": descricao, "valor": valor, "data_vencimento": hoje + timedelta(days=dias), "origem": "MANUAL", "origem_id": 0}
        )

    auth.encerrar_sessao()
    print(f"Base de demonstracao criada em {banco}")
    print(f"Acesso: admin / {SENHA_DEMO}   ou   vendedor / {SENHA_DEMO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
