; Instalador do ERP Autopecas & Servicos (Inno Setup 6).
; Gerar:  python scripts/build_installer.py --version 3.2.0   (precisa do PyInstaller gerado em dist\ERP_Autopecas)
;
; Decisoes:
;  - Instalacao por usuario (sem administrador) em %LOCALAPPDATA%\Programs; o usuario pode escolher "para todos".
;  - NAO inclui a pasta data\ (base de demonstracao): com data\ ao lado do .exe o sistema entra em modo portatil.
;    Instalado, ele grava banco, logs e backups em %LOCALAPPDATA%\ERP_Autopecas, fora da pasta do programa.
;  - Atualizar = rodar o novo instalador por cima (mesmo AppId): troca so os arquivos do programa; os dados ficam.
;  - Desinstalar remove o programa e NUNCA apaga os dados do cliente.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppName "ERP Autopecas e Servicos"
#define AppExe "ERP_Autopecas.exe"

[Setup]
AppId={{7C1E5A3B-4D2F-4B8E-9A61-3F0D8E2B5C47}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Flavio H. Zaccheroni
DefaultDirName={autopf}\ERP_Autopecas
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
OutputBaseFilename=ERP_Autopecas_Setup_{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na area de trabalho"; GroupDescription: "Atalhos:"

[Files]
; Programa (PyInstaller onedir). A base de demonstracao (data\) fica de fora de proposito.
Source: "..\dist\ERP_Autopecas\*"; DestDir: "{app}"; Excludes: "data,data\*"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir o {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and (not UninstallSilent) then
    MsgBox('O programa foi removido. Seus dados (banco, backups e logs) foram MANTIDOS em:' + #13#10 +
           ExpandConstant('{localappdata}\ERP_Autopecas') + #13#10 + #13#10 +
           'Apague essa pasta somente se nao precisar mais deles.', mbInformation, MB_OK);
end;
