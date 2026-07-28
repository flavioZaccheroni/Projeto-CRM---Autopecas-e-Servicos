# ERP CRM Autopecas & Servicos

Sistema desktop inicial para autopecas, oficinas e servicos automotivos.

## Fase atual

Fase 10 - Deploy, homologacao e treinamento:

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

Usuario inicial:

- Login: `admin`
- Senha: `admin123`

## Testes

```powershell
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
