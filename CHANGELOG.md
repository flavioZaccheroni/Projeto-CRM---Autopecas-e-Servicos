# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [2.0.0]

### Adicionado
- **Segurança:** perfis e permissões aplicados de verdade (Administrador, Vendedor, Estoquista, Financeiro), telas de
  Usuários/Permissões/Configurações, troca de senha obrigatória, política de senha forte, bloqueio após 5 tentativas,
  auditoria de todas as escritas, backup consistente e restauração validada com cópia de segurança prévia.
- **Fluxo de negócio:** numeração automática (V/OS/C), parcelamento, forma de pagamento, conta a pagar na compra,
  cancelamento com estorno de estoque e financeiro, orçamento → aprovação → venda, edição de itens, OS em PDF.
- **Validações:** CPF, CNPJ, placa, UF e telefone.
- **Dashboard** com KPIs reais, gráfico de 6 meses, estoque baixo e próximos vencimentos.
- **Seletores com busca** (ID – nome) e **filtro em todas as listagens**; atalhos F5 e Ctrl+F; nomes no lugar de IDs.
- **Login** redesenhado.
- **Alembic** para migrações; bancos anteriores são atualizados sem perda de dados.
- **Qualidade:** ruff, GitHub Actions (lint + testes), 87 testes (unidade, fluxo e controllers de ponta a ponta).
- **Portfólio:** base de demonstração (`scripts/gerar_demo.py`), variável `ERP_DATA_DIR`, screenshots e README completo.
- Spec do PyInstaller versionado (`ERP_Autopecas.spec`) e build do executável em pasta.

### Alterado
- Código duplicado de itens/pagamento de vendas, OS e compras centralizado em `services/_itens.py`.
- Em executável empacotado, dados/logs/backups ficam ao lado do `.exe`.

### Corrigido
- Parcelamento com `parcelas=0`; estado de relacionamentos após cancelamento; mensagens de erro de permissão.

## [1.0.0]
- Fases 1 a 10: estrutura, banco SQLite/SQLAlchemy, login, cadastros, estoque, compras, vendas, OS, financeiro,
  relatórios PDF/Excel, backup e pacote de release.
