# Instalacao e Deploy

## Requisitos

- Windows 10 ou superior.
- Python instalado e disponivel como `py` ou `python`.
- Permissao de escrita na pasta do sistema.

## Instalar a partir do pacote portatil

1. Extraia o arquivo `.zip` gerado em `releases/`.
2. Entre na pasta extraida.
3. Execute `instalar_dependencias.bat`.
4. Execute `executar.bat`.

## Gerar pacote para distribuicao

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe scripts\build_release.py --version 1.0.0
```

O executavel em `bin/` e opcional. Se o ambiente Python usado para empacotar estiver sem Tkinter/Tcl valido, o script mantem apenas o pacote portatil com `executar.bat`.

## Login inicial

- Usuario: `admin`
- Senha temporaria: `admin123` (a troca e obrigatoria no primeiro acesso)

## Estrutura runtime

- `data/`: banco SQLite.
- `logs/`: logs da aplicacao.
- `backups/`: backups manuais.
- `exports/relatorios/`: relatorios PDF e Excel.

## Atualizacao em cliente

> Bancos de versoes anteriores sao migrados automaticamente na primeira abertura (colunas novas sao
> adicionadas sem perda de dados). Mesmo assim, faca o backup antes de atualizar.

1. Abrir o sistema antigo e criar backup manual.
2. Fechar o sistema.
3. Copiar a nova versao para uma pasta separada.
4. Copiar o banco `data/erp_autopecas.db` para a nova versao, se aplicavel.
5. Executar `executar.bat`.
6. Validar login, consultas principais, backup e relatorios.
