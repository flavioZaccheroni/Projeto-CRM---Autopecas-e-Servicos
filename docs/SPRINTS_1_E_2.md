# Sprints 1 e 2 - Seguranca e fluxo de negocio

## Sprint 1 - Seguranca

| Item | Entrega |
|---|---|
| Permissoes | `Sessao` + decorator `@requer_permissao` nos controllers; menu e botoes respeitam o perfil. A barreira real fica no controller. |
| Perfis padrao | Administrador (acesso total, imutavel), Vendedor, Estoquista, Financeiro. Novos perfis na tela Permissoes. |
| Telas | Usuarios, Permissoes, Configuracoes (`app/views/admin_views.py`). |
| Login | Troca obrigatoria no primeiro acesso/senha redefinida, politica de senha, bloqueio de 5 min apos 5 erros. |
| Backup | API `sqlite3.backup`, validacao (integrity_check + tabelas do sistema), copia `pre_restore_*` antes de restaurar. |
| Auditoria | Toda escrita e login/logout registrados com o usuario logado. |
| Migracao | `app/database/migrations.py`: adiciona colunas novas em bancos antigos (idempotente). |

## Sprint 2 - Fluxo de negocio

| Item | Entrega |
|---|---|
| Numeracao | `V000001`, `OS000001`, `C000001` automaticos (campo em branco). |
| Compra -> pagar | Receber compra gera conta(s) a pagar. |
| Parcelamento | Venda/OS/compra em N parcelas (30 em 30 dias); resto de arredondamento na ultima. |
| Pagamento | Forma de pagamento na venda e na OS. |
| Cancelamento | Venda, OS e compra: motivo obrigatorio, estorno de estoque e de titulos (pagos geram estorno no caixa). |
| Orcamento | `ORCAMENTO -> APROVADO -> FINALIZADA` (ou `RECUSADO`/`CANCELADA`). |
| Itens | Editar e remover itens antes de finalizar; total recalculado. |
| Impressao | PDF da OS em `exports/os/` (cabecalho usa a configuracao `empresa.nome`). |
| Validacao | CPF/CNPJ com digito verificador, placa (antiga e Mercosul), UF, telefone. |

## Mapa de permissoes das acoes

- `ver`: listar e abrir telas / imprimir OS.
- `criar`: novo registro, adicionar item, movimentar estoque, criar backup.
- `editar`: editar, aprovar, finalizar, receber, baixar titulo.
- `excluir`: remover item, **cancelar** documentos, estornar titulo, restaurar backup.

## Pendencias conhecidas

- Telas ainda usam IDs digitados (cliente, produto, veiculo); seletores/busca ficam para a Sprint 3.
- Dashboard ainda sem KPIs reais (Sprint 3).
- Migracoes de schema futuras: migrar para Alembic (Sprint 4).
