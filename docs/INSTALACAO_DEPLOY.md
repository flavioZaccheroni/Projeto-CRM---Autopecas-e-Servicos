# Instalação e deploy

O sistema é distribuído de dois jeitos:

| Formato | Arquivo | Para quem |
| --- | --- | --- |
| **Instalador Windows** (recomendado) | `ERP_Autopecas_Setup_<versão>.exe` | Cliente final: atalhos, desinstalador e atualização por cima, sem Python |
| **Executável portátil** | `ERP_Autopecas_<versão>_windows.zip` | Testar sem instalar (inclui a base de demonstração) ou rodar de um pen drive |
| **Código-fonte** | `erp_autopecas_<versão>.zip` ou o repositório | Desenvolvimento e quem não pode rodar o executável |

## Requisitos

- Windows 10 ou superior (64 bits).
- Executável: nenhum software adicional.
- Código-fonte: Python 3.12+ (as dependências, incluindo o PySide6 da interface, vêm do `requirements.txt`).

## Instalador (Windows)

1. Execute `ERP_Autopecas_Setup_<versão>.exe`. Não exige administrador: instala só para o seu usuário (em `%LOCALAPPDATA%\Programs\ERP_Autopecas`). Para instalar para todos, escolha a opção na primeira tela e confirme a permissão do Windows.
2. Siga o assistente (marque o atalho na área de trabalho se quiser) e abra o sistema.
3. A primeira abertura cria uma **base nova e vazia** (login `admin` / `admin123`, com troca obrigatória de senha). O instalador não traz a base de demonstração.

Os dados (banco, backups, logs) ficam em `%LOCALAPPDATA%\ERP_Autopecas`, **fora** da pasta do programa.

- **Atualizar:** rode o instalador da versão nova por cima. Ele fecha o sistema, troca só os arquivos do programa e **não mexe nos dados**; o banco é migrado na primeira abertura. Faça um backup antes, por precaução.
- **Desinstalar:** *Configurações do Windows → Aplicativos* (ou o atalho "Desinstalar" no menu Iniciar). Remove o programa e **mantém os dados**; apague `%LOCALAPPDATA%\ERP_Autopecas` manualmente só se não precisar mais deles.
- **Vindo do modo portátil (zip):** com o sistema fechado, copie a pasta `data` (e, se quiser, `backups`) da pasta antiga para `%LOCALAPPDATA%\ERP_Autopecas`, depois instale e abra.
- **Instalação silenciosa** (suporte/TI): `ERP_Autopecas_Setup_<versão>.exe /VERYSILENT /NORESTART` (opcionalmente `/DIR="C:\Pasta"`).

> O instalador também **ainda não é assinado digitalmente**: o Windows pode mostrar o aviso do SmartScreen ("Windows protegeu o computador"; use *Mais informações → Executar assim mesmo*).

## Executável portátil (Windows)

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

## Licença e período de teste

- Sem licença, o sistema funciona por **30 dias** a partir do primeiro uso. Depois entra em **modo somente consulta**: o cliente continua vendo e exportando seus dados e fazendo backup, mas não cria nem altera registros. Os dados nunca são apagados ou bloqueados.
- **Ativar:** *Sobre → Ativar licença…* e escolher o arquivo `.erplic` recebido. A licença é gravada na pasta de dados e vale já, sem reiniciar. A tela mostra cliente, plano e vencimento; o aviso aparece quando faltam poucos dias.
- **Licença vinculada ao computador (opcional):** o cliente copia o *código do computador* em *Sobre* e envia ao fornecedor, que emite a licença com `--maquina`.
- Reinstalar ou apagar arquivos não reinicia o teste: o primeiro uso fica registrado no banco e em um marcador ao lado do programa, e voltar o relógio não devolve dias.

### Emitir licenças (fornecedor)

```powershell
# uma única vez: cria a chave privada fora do repositório (faça cópia de segurança!)
.\.venv\Scripts\python.exe scripts\gerar_licenca.py chaves --saida "C:\Users\voce\ERP_licencas"
# a cada venda
.\.venv\Scripts\python.exe scripts\gerar_licenca.py emitir --chave "C:\Users\voce\ERP_licencas\chave_privada.key" --cliente "Auto Peças Exemplo" --plano Anual --validade 2027-11-13
```

Omita `--validade` para licença sem vencimento. A chave **pública** fica embutida em `app/services/licenca_service.py`; a **privada** nunca vai ao Git nem ao cliente. Perder a privada obriga a trocar a pública e reemitir as licenças. Limite honesto: em um programa local nada impede um invasor determinado; o objetivo é evitar o uso casual sem pagar.

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
.\.venv\Scripts\python.exe scripts\build_release.py --version 3.2.0
# instalador (precisa do Inno Setup 6, https://jrsoftware.org/isinfo.php; usa o dist\ gerado acima):
.\.venv\Scripts\python.exe scripts\build_installer.py --version 3.2.0
```

Gera em `releases/`:

- `erp_autopecas_<versão>.zip`: pacote de código-fonte;
- `ERP_Autopecas_<versão>_windows.zip`: executável portátil (PyInstaller, em pasta) com a base de demonstração em `data/`. Use `--skip-exe` para gerar só o pacote de código-fonte;
- `ERP_Autopecas_Setup_<versão>.exe`: instalador (Inno Setup, script em `installer/ERP_Autopecas.iss`), **sem** a pasta `data/` de demonstração para o sistema usar a pasta de dados do usuário.

O executável e o instalador também são gerados e validados no GitHub Actions, pelo workflow **Build do executavel** (execução manual ou ao publicar uma tag `v*`): autoteste do `.exe` (banco e interface) e teste do instalador (instalar, abrir, atualizar por cima e desinstalar, conferindo que os dados são preservados). Os artefatos são `ERP_Autopecas_windows` (zip portátil) e `ERP_Autopecas_Setup` (instalador). Antes de publicar uma versão, atualize `APP_VERSION` em `app/config/settings.py` e o `CHANGELOG.md`.

## Solução de problemas

- **O Windows bloqueia o executável:** veja o alerta acima; use o código-fonte ou peça ao suporte uma versão assinada quando disponível.
- **Não abre ou fecha sozinho:** abra **Sobre → Abrir pasta de logs** (ou a pasta `logs/` em modo portátil) e envie o arquivo `erp_autopecas.log` ao suporte, junto com o texto de **Copiar informações para o suporte**.
- **Erro de permissão ao gravar:** o programa está em uma pasta protegida e os dados estão ao lado dele. Remova a pasta `data/` vazia (se houver) para o sistema usar a pasta do usuário, ou defina `ERP_HOME`.
- **Esqueci a senha do administrador:** restaure um backup anterior ou entre em contato com o suporte.
