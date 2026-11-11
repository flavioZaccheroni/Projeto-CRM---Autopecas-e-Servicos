# Sprint 3 - Dashboard e UX

## O que mudou
- **Dashboard real** (`DashboardService`, `DashboardController`, `views/dashboard_view.py`): faturamento do mes,
  vendas e OS finalizadas, OS abertas, orcamentos em aberto, saldo de caixa, a receber/pagar (vencido e proximos 7 dias),
  grafico de barras dos ultimos 6 meses, estoque abaixo do minimo e proximos vencimentos.
  Cada bloco aparece conforme a permissao "ver" do modulo correspondente.
- **Seletores com busca** (`views/widgets.py`): cliente, fornecedor, produto, veiculo, categoria e marca agora sao listas
  "ID - nome" filtraveis ao digitar. Nao e mais preciso decorar IDs. Em OS, a lista de veiculos mostra so os do cliente escolhido;
  em Vendas/OS o preco de venda do produto e sugerido ao selecionar.
- **Busca em todas as listagens** (`TabelaFiltravel`): filtro por varias palavras, sem diferenciar acentos/maiusculas,
  contador de registros e linhas zebradas. Cobre cadastros, vendas, compras, OS, estoque, financeiro e auditoria.
- **Nomes em vez de IDs** nas tabelas (cliente, fornecedor, produto, veiculo) via eager loading nos repositorios.
- **Formatacao**: datas dd/mm/aaaa, valores em pt-BR, Sim/Nao.
- **Atalhos**: `F5` recarrega o modulo atual; `Ctrl+F` foca a busca da tabela visivel.
- **Login redesenhado**: painel de marca, erro exibido na propria tela, opcao "Mostrar senha".

## Testes
`pytest`: 77 testes (inclui `test_dashboard_lookup.py` e `test_widgets_puros.py`).
Alem disso, um roteiro de GUI automatizado (fora do repositorio) abriu as 17 telas e percorreu o fluxo
cadastros -> compra -> venda parcelada -> OS -> financeiro -> estoque -> dashboard sem erros.
