# ERP CRM Autopecas & Servicos

Sistema desktop inicial para autopecas, oficinas e servicos automotivos.

## Fase atual

Fase 1 - Base do sistema:

- Estrutura de pastas
- Banco SQLite com SQLAlchemy
- Login
- Usuarios, perfis e permissoes
- Janela principal inicial

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
