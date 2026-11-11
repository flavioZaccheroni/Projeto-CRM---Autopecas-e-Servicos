# ERP CRM Autopecas & Servicos

Sistema desktop inicial para autopecas, oficinas e servicos automotivos.

## Versao atual

Fases 1 a 10 + Sprints 1 e 2 (seguranca e fluxo de negocio). Veja `docs/SPRINTS_1_E_2.md`.

Novidades:

- Perfis e permissoes aplicados de verdade (ver/criar/editar/excluir por modulo), com perfis padrao
  Administrador, Vendedor, Estoquista e Financeiro.
- Telas de Usuarios, Perfis/Permissoes e Configuracoes.
- Login seguro: troca de senha obrigatoria no primeiro acesso, politica de senha e bloqueio por tentativas.
- Backup consistente, restauracao validada com copia de seguranca previa e auditoria de todas as escritas.
- Numeracao automatica, parcelamento, contas a pagar na compra, cancelamento com estorno,
  orcamento -> aprovacao -> venda, edicao de itens e impressao de OS em PDF.
- Validacao de CPF/CNPJ, placa, UF e telefone; migracao automatica de bancos antigos.

## Escopo original (Fase 10)

- Estrutura de pastas
- Banco SQLite com SQLAlchemy
- Login
- Usuarios, perfis e permissoes
- Dashboard profissional
- Cadastros, estoque, compras, vendas, OS e financeiro
- Relatorios PDF/Excel
- Seguranca, backup e auditoria
- Pacote de release, roteiro de homologacao e treinamento

## Executar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Primeiro acesso:

- Login: `admin`
- Senha temporaria: `admin123` — o sistema **obriga a troca** no primeiro login
  (minimo 8 caracteres, com letras e numeros).

## Testes

```powershell
pip install -r requirements-dev.txt
pytest
```

## Release

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe scripts\build_release.py --version 1.0.0
```

Para gerar somente o pacote portatil:

```powershell
.\.venv\Scripts\python.exe scripts\build_release.py --version 1.0.0 --skip-exe
```
