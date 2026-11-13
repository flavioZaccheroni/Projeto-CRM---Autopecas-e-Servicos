# Instalação e deploy

O sistema é distribuído de dois jeitos:

| Formato | Arquivo | Para quem |
| --- | --- | --- |
| **Executável Windows** (recomendado) | `ERP_Autopecas_<versão>_windows.zip` | Quem só quer usar: não precisa instalar Python |
| **Código-fonte** | `erp_autopecas_<versão>.zip` ou o repositório | Desenvolvimento e quem não pode rodar o executável |

## Requisitos

- Windows 10 ou superior (64 bits).
- Executável: nenhum software adicional.
- Código-fonte: Python 3.12+ (as dependências, incluindo o PySide6 da interface, vêm do `requirements.txt`).

## Executável (Windows)

1. Extraia o `.zip` em uma pasta de sua escolha (por exemplo `C:\ERP_Autopecas`). Não execute de dentro do zip.
2. Abra `ERP_Autopecas.exe`.
3. Faça login (veja "Primeiro acesso").

> **Alerta do Windows:** o executável **ainda não é assinado digitalmente**. O Windows (SmartScreen, Smart App Control ou política da empresa) pode exibir um aviso ou bloquear a execução. Baixe sempre pelo site oficial ou pelo GitHub do autor. Se o bloqueio persistir, execute a partir do código-fonte (abaixo).

### Primeiro acesso

- **Pacote de demonstração** (traz a pasta `data/` com dados 100% fictícios): `admin` / `Demo@1234` ou `vendedor` / `Demo@1234`. Uso apenas para testes, por até 30 dias, sem dados reais.
- **Base nova** (sem dados): `admin` / `admin123`. O sistema **obriga a troca da senha** no primeiro login (mínimo de 8 caracteres, com letras e números).

Para começar do zero a partir do pacote de demonstração, **apague a pasta `data/`** ao lado do `.exe` antes do primeiro uso: o sistema cria uma base nova e vazia (veja o próximo item sobre onde ela fica).

## Onde ficam os dados

O sistema grava o banco SQLite, os logs, os backups e os relatórios em uma **pasta de dados**:

| Situação | Pasta de dados |
| --- | --- |
| Existe uma pasta `data/` ao lado do `.exe` (ou o arquivo `portable.flag`) | A própria pasta do programa: **modo portátil** (`data/`, `logs/`, `backups/`, `exports/`) |
| Não existe `data/` nem `portable.flag` ao lado do `.exe` | `%LOCALAPPDATA%\ERP_Autopecas` (gravável mesmo se o programa estiver em "Arquivos de Programas") |
| Variável de ambiente `ERP_HOME` definida | A pasta indicada |
| Código-fonte | A pasta do projeto |

`ERP_DATA_DIR` aponta só o banco para outra pasta (usada, por exemplo, para abrir a base de demonstração sem tocar nos dados reais).

Para conferir os caminhos em uso, abra **Sistema → Sobre**: a tela mostra a pasta de dados, o banco, os logs e os backups, com botões para abrir as pastas e copiar as informações para o suporte.

## Backup

- **Automático** (ligado por padrão): cria uma cópia `auto_*` ao abrir o sistema (no máximo uma por dia) e ao fechá-lo (se houve alterações, no máximo uma por hora). Mantém as mais recentes (padrão 15; backups manuais nunca são apagados).
- **Cópia extra:** em **Configurações → Backup automático** é possível indicar outra pasta (outro disco, pen drive ou pasta sincronizada com a nuvem) que também recebe cada backup.
- **Manual e restauração:** em **Segurança e backup**. Antes de restaurar, o sistema guarda uma cópia do estado atual (`pre_restore_*`).

Mantenha sempre uma cópia fora do computador onde o sistema roda.

## Atualização em cliente

Bancos de versões anteriores são migrados automaticamente na primeira abertura (Alembic), sem perda de dados. Mesmo assim, faça backup antes de atualizar.

1. Abra o sistema atual e confirme que há um backup recente (Segurança e backup → Criar backup).
2. Feche o sistema.
3. Extraia a nova versão em uma **pasta separada**.
4. Se o seu sistema está em modo portátil, copie para a nova pasta as pastas `data/`, `backups/` e `logs/` da versão antiga. No modo "pasta do usuário", os dados já estão fora do programa e não precisam ser copiados.
5. Abra `ERP_Autopecas.exe` e valide: login, uma consulta, o backup e um relatório.
6. Guarde a versão antiga por alguns dias, até ter certeza de que tudo está certo.

## Executar a partir do código-fonte

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

O pacote de código-fonte (`erp_autopecas_<versão>.zip`) também traz `instalar_dependencias.bat` e `executar.bat`, que fazem esses passos (exigem Python instalado e disponível como `py`).

## Gerar o pacote para distribuição

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe scripts\build_release.py --version 3.1.0
```

Gera em `releases/`:

- `erp_autopecas_<versão>.zip`: pacote de código-fonte;
- `ERP_Autopecas_<versão>_windows.zip`: executável (PyInstaller, em pasta) com a base de demonstração em `data/`. Use `--skip-exe` para gerar só o pacote de código-fonte.

O executável também é gerado e validado (autoteste de banco e interface) no GitHub Actions, pelo workflow **Build do executavel** (execução manual ou ao publicar uma tag `v*`). Antes de publicar uma versão, atualize `APP_VERSION` em `app/config/settings.py` e o `CHANGELOG.md`.

## Solução de problemas

- **O Windows bloqueia o executável:** veja o alerta acima; use o código-fonte ou peça ao suporte uma versão assinada quando disponível.
- **Não abre ou fecha sozinho:** abra **Sobre → Abrir pasta de logs** (ou a pasta `logs/` em modo portátil) e envie o arquivo `erp_autopecas.log` ao suporte, junto com o texto de **Copiar informações para o suporte**.
- **Erro de permissão ao gravar:** o programa está em uma pasta protegida e os dados estão ao lado dele. Remova a pasta `data/` vazia (se houver) para o sistema usar a pasta do usuário, ou defina `ERP_HOME`.
- **Esqueci a senha do administrador:** restaure um backup anterior ou entre em contato com o suporte.
