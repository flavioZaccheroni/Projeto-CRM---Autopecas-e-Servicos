# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [3.0.1]

### Adicionado
- Aviso de **versão de demonstração (uso apenas para testes, 30 dias, sem dados reais)** na tela de login, no menu lateral e no título das janelas.

## [3.0.0]

### Adicionado
- **Nova interface em PySide6 (Qt)**, substituindo as telas Tkinter: login, shell com menu lateral recolhível,
  paleta de comandos (`Ctrl+K`), tema claro/escuro, avisos e estados vazios.
- Dashboard com KPIs e gráficos desenhados em QPainter; cadastros com painel lateral de edição; documentos
  (compras, vendas, OS) com linha de etapas, itens e ações por status e permissão; estoque, financeiro,
  relatórios, usuários, permissões, segurança/backup, auditoria e configurações.
- Tabelas com busca que ignora acentos, ordenação e exportação CSV.

### Alterado
- `main.py` abre a interface Qt; o autoteste do `.exe` (`--selftest`) valida Alembic e a inicialização do Qt.
- Camadas de modelo, serviço e controller ficaram intactas; helpers de formatação e busca foram para `app/utils`.
- Pacote do executável maior (inclui o Qt); PyInstaller exclui módulos Qt não usados e o Tk.

### Removido
- Pacote `app/views` (Tkinter).

## [2.0.1]

### Corrigido
- O executável do v2.0.0 não abria: faltava empacotar `app.database.migrations`, usado pela migração do Alembic.
  O build agora é validado no CI, que abre o `.exe` num autoteste (`--selftest`) antes de gerar o pacote.

### Adicionado
- Workflow `Build do executavel` (GitHub Actions) com autoteste do `.exe`; spike de PySide6 para o redesign.

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
