# Fases 2 a 4 - Checklist

## Fase 2 - Cadastros basicos

- Clientes: model, repository, service, controller, tela e validacao de duplicidade.
- Veiculos: model, repository, service, controller e tela.
- Fornecedores: model, repository, service, controller e tela.
- Categorias: model, repository, service, controller e tela.
- Marcas: model, repository, service, controller e tela.
- Produtos: model, repository, service, controller e tela.

## Fase 3 - Estoque

- Estoque atual por produto.
- Movimentacoes de entrada, saida e ajuste.
- Bloqueio de saldo negativo.
- Registro de origem, usuario, saldo anterior e saldo posterior.
- Tela operacional para movimentos e consulta.

## Fase 4 - Compras

- Pedido de compra.
- Inclusao de itens.
- Calculo de valor total.
- Recebimento de compra.
- Entrada automatica no estoque a partir dos itens recebidos.

## Pendencias naturais para refinamento

- Substituir campos `*_id` por combos pesquisaveis.
- Melhorar permissao por perfil nas telas.
- Criar migrations formais quando o banco estiver em uso real.
- Adicionar exportacao e impressao em fases futuras.
