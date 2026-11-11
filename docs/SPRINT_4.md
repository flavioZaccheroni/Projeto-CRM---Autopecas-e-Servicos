# Sprint 4 - Qualidade tecnica

## Migracoes com Alembic
- `app/database/alembic/` (env.py + `versions/0001_baseline.py`) e `app/database/alembic_runner.py`.
- `create_database()` agora roda `alembic upgrade head`. A migracao 0001 cria o schema completo e, em bancos
  anteriores ao Alembic, adiciona as colunas novas sem perder dados (reaproveita `migrations.aplicar_migracoes`).
- **Mudou o modelo?** Crie uma revisao em `app/database/alembic/versions/` (copie o formato da 0001, ajuste
  `revision`/`down_revision`) com o `op.add_column(...)` correspondente. Nao edite a 0001.
- O build (`scripts/build_release.py`) inclui a pasta do Alembic no executavel.

## Lint e CI
- `pyproject.toml`: configuracao do ruff (E, F, W, I, B, UP) e do pytest. `ruff check .` passa limpo.
- `.github/workflows/ci.yml`: a cada push na `main` e em PRs roda ruff + pytest (Windows, Python 3.12).
- `requirements-dev.txt` agora traz pytest, pytest-cov e ruff; `requirements.txt` inclui alembic.

## Codigo duplicado
`services/_itens.py` concentra o que vendas, OS e compras repetiam: `validar_quantidade_valor`,
`normalizar_forma_pagamento`, `carregar_produtos`, `recalcular_total` e `FORMAS_PAGAMENTO`.

## Testes
- `test_controllers.py` (novo): controllers sobre um banco temporario (fixture `app_db`) - bloqueio sem login,
  bloqueio de conta, fluxo compra -> venda parcelada -> cancelamento com estorno, OS + PDF, financeiro (baixa/estorno),
  perfil restrito, dashboard por permissao, relatorios e auditoria.
- `test_alembic.py` (novo): banco novo, banco antigo com dados e idempotencia.
- Total: 87 testes. Cobertura: `pytest --cov=app`.

## Como rodar
```bash
python -m pip install -r requirements-dev.txt
ruff check .
python -m pytest -q
```
