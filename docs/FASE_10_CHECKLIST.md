# Fase 10 - Checklist

## Entregas implementadas

- Script de empacotamento `scripts/build_release.py`.
- Release portatil com `executar.bat`.
- Suporte opcional a executavel via PyInstaller quando instalado e com Tkinter/Tcl valido.
- Script de homologacao tecnica `scripts/homologacao_smoke.py`.
- Documentacao de instalacao.
- Roteiro de treinamento.
- Roteiro de homologacao.
- Pasta `releases/` ignorada no Git.
- Pastas `build/` e `dist/` ignoradas no Git.

## Como gerar release

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe scripts\build_release.py --version 1.0.0
```

Para gerar apenas pacote portatil, sem tentar PyInstaller:

```powershell
.\.venv\Scripts\python.exe scripts\build_release.py --version 1.0.0 --skip-exe
```

## Como homologar

```powershell
.\.venv\Scripts\python.exe scripts\homologacao_smoke.py
.\.venv\Scripts\python.exe -m pytest app\tests
```

## Pendencias naturais para refinamento

- Instalador Windows nativo com assistente visual.
- Assinatura digital do executavel.
- Geracao do executavel em ambiente Python com Tkinter/Tcl validado.
- Pipeline CI/CD no GitHub Actions.
- Migracao futura para PostgreSQL quando o uso multiusuario exigir.
