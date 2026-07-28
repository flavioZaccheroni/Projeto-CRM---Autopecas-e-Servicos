# Roteiro de Homologacao

## Validacao tecnica

- Executar testes automatizados.
- Executar smoke test de homologacao.
- Abrir o sistema pelo `main.py` ou `executar.bat`.
- Validar login inicial.
- Criar backup manual.
- Gerar relatorio PDF.
- Gerar relatorio Excel.

## Validacao funcional

- Cadastrar cliente.
- Cadastrar veiculo.
- Cadastrar fornecedor.
- Cadastrar categoria, marca e produto.
- Registrar entrada de estoque.
- Criar compra com item e receber.
- Criar venda com item e finalizar.
- Criar OS com peca e servico e finalizar.
- Baixar lancamento financeiro.
- Conferir movimentacao de caixa.

## Criterio de aceite

- Nenhuma etapa critica pode apresentar erro nao tratado.
- Estoque nao pode ficar negativo sem bloqueio.
- Vendas e OS devem gerar financeiro a receber.
- Backups devem ser listados na tela de seguranca.
- Relatorios devem ser gerados em `exports/relatorios`.
