# Plano: mínimo para vender o ERP (versão 3.1 → 3.4)

Objetivo: deixar o ERP pronto para os **primeiros clientes-piloto pagantes no Windows**, sem inflar o escopo.
Capacidade considerada: ~10 h/semana, uma frente por vez. Estimativas em horas são aproximadas e servem para ordenar, não para prometer prazo.

Base: auditoria da estrutura do código (modelos, serviços, build, docs). Itens marcados **(verificar)** dependem de conferir o código antes de começar.

## Marcos

| Versão | Tema | Esforço | Resultado |
|---|---|---|---|
| 3.1 | Operação segura | ~20–25 h | Backup automático, dados fora da pasta do exe, tela "Sobre", docs corrigidas |
| 3.2 | Vendas completas | ~20–25 h | Desconto/acréscimo, PDF de venda e orçamento, logo, mão de obra com catálogo |
| 3.3 | Distribuição e licença | ~25–35 h | Instalador, assinatura do exe, licença/trial real |
| 3.4 | Piloto e ajustes | contínuo | Importação por planilha, correções vindas dos pilotos |

A ordem coloca primeiro o que **protege os dados do cliente** (3.1) e só depois o que **torna cobrável** (3.3), porque licença e instalador só valem a pena depois que o produto for seguro e completo.

---

## 3.1 — Operação segura

### 1. Dados fora da pasta do executável
- **Problema:** `app/config/settings.py` usa a pasta do `.exe` como raiz de `data/`, `logs/` e `backups/`. Instalado em "Arquivos de Programas", o Windows bloqueia a escrita.
- **Feito quando:** em modo empacotado os dados ficam em uma pasta gravável do usuário (ex.: `%LOCALAPPDATA%` ou `%PROGRAMDATA%`), com opção de manter o modo portátil (pasta ao lado do exe) por variável ou arquivo de configuração.
- **Cuidados:** migrar a base de quem já usa o modo atual; a base de demonstração do release continua funcionando; ajustar `scripts/build_release.py` e os testes de caminho.
- **Esforço:** ~6–8 h.

### 2. Backup automático
- **Problema:** só existe backup manual, na mesma pasta/disco.
- **Feito quando:**
  - backup automático ao fechar o app (ou 1×/dia ao abrir), mantendo os N últimos (parâmetro em Configurações);
  - pasta de destino configurável (pen drive, outro disco, pasta sincronizada com nuvem);
  - aviso visível se o último backup tiver mais de X dias;
  - teste de restauração automatizado (a validação de backup já existe em `seguranca_service`).
- **Esforço:** ~8–10 h.

### 3. Tela "Sobre" e suporte
- Versão, data do build, caminho da base e dos logs, botão "abrir pasta de logs" e "copiar informações para suporte".
- **Esforço:** ~3 h.

### 4. Documentação corrigida
- Reescrever `docs/INSTALACAO_DEPLOY.md` (hoje cita Python obrigatório, Tkinter, `instalar_dependencias.bat` e versão 1.0.0, o que não reflete o executável atual).
- **Esforço:** ~2 h.

---

## 3.2 — Vendas completas

### 5. Desconto e acréscimo
- **Situação:** não encontrei campos de desconto/acréscimo em venda, OS ou itens (`valor_total` é a soma dos itens).
- **Proposta:** desconto por item e/ou no total (valor ou %), com limite configurável por perfil (ex.: vendedor até 10%), registro na auditoria e reflexo no financeiro e relatórios.
- **Mexe em:** modelos `Venda`, `OrdemServico`, `ItemVenda`, `ItemOS`, migração Alembic, `services/_itens.py` (`recalcular_total`), formulários e relatórios.
- **Esforço:** ~10–12 h (inclui migração e testes).

### 6. PDF e recibo de venda e de orçamento
- **Situação:** só a OS tem PDF (`app/reports/os_pdf.py`).
- **Proposta:** reaproveitar a estrutura da OS para orçamento, venda e recibo de pagamento, com cabeçalho da empresa.
- **Esforço:** ~6 h.

### 7. Logo e dados da empresa
- Upload de logo nas Configurações e uso no cabeçalho dos PDFs.
- **Esforço:** ~3 h.

### 8. Catálogo de serviços
- **Situação:** itens de OS têm `tipo` e `descricao` livres (digitados).
- **Proposta:** cadastro de serviços (nome, preço padrão, tempo estimado) que alimente a OS, mantendo a opção de digitar livre. Campo "mecânico responsável" na OS. **(verificar)** antes de decidir se comissão entra já ou depois.
- **Esforço:** ~8–10 h.

---

## 3.3 — Distribuição e licença

### 9. Instalador
- Criar um instalador Windows (por exemplo Inno Setup) que instale o app, crie atalho e desinstalador, e **preserve os dados** ao atualizar.
- Atualização manual guiada (substituir app, migrar base automaticamente, já suportado por Alembic).
- **Esforço:** ~8–10 h.

### 10. Assinatura digital do executável
- Comprar certificado de assinatura de código (custo anual; **levantar valores atuais**, variam por tipo e emissor) e assinar exe e instalador no passo de release.
- Alternativas a avaliar: certificado EV (reputação imediata, mais caro) vs. padrão (reputação se constrói com o tempo).
- Automatizar no GitHub Actions, guardando o certificado como segredo.
- **Esforço:** ~4–6 h + prazo de emissão do certificado.

### 11. Licença e período de teste real
- **Situação:** o prazo de 30 dias é só aviso no login e na barra lateral.
- **Proposta (simples, offline):**
  - arquivo de licença assinado digitalmente (assinatura com chave privada sua, verificação com chave pública embutida) contendo cliente, plano, validade e, opcionalmente, o identificador da máquina;
  - modo teste: sem licença, o app funciona por 30 dias a partir do primeiro uso, depois entra em modo somente consulta/exportação (não apagar dados do cliente);
  - gerador de licenças em script seu (fora do app distribuído).
- **Limites honestos:** em app local nenhuma proteção é à prova de quebra; o objetivo é evitar uso casual sem pagar, não impedir um invasor. Não bloquear o acesso do cliente aos próprios dados.
- **Decisão antes de começar:** modelo de venda (licença única, anual ou assinatura), porque define a validade do arquivo.
- **Esforço:** ~12–16 h.

### 12. Contrato/EULA e termos
- Termos de licença, suporte e LGPD (o ERP guarda dados pessoais dos clientes do cliente). Revisar com contador/advogado; trocar os termos de teste do site quando houver venda.
- **Esforço seu:** definição e revisão; ~3 h de integração (exibir no primeiro uso e no instalador).

---

## 3.4 — Piloto e ajustes

### 13. Importação por planilha
- Importar produtos e clientes de Excel/CSV, com pré-visualização e relatório de erros por linha, respeitando as validações existentes (CPF/CNPJ, UF, telefone).
- **Esforço:** ~10–12 h.

### 14. Piloto
- 3–5 clientes; teste do instalador em máquina limpa; checklist em `docs/ROTEIRO_HOMOLOGACAO.md`; registrar pedidos para decidir próximas funções.

---

## Fica fora do mínimo (decidir pelos pilotos)

| Item | Por quê |
|---|---|
| NF-e/NFC-e | Projeto grande (regras fiscais, certificado A1, homologação SEFAZ). Opção: integrar um serviço emissor por API só se vários pilotos exigirem. Enquanto isso, posicionar como gestão interna. |
| Rede / vários computadores | Exige trocar SQLite por servidor de banco e rever concorrência. Só se houver demanda. |
| Devolução/troca | Importante, mas pode entrar na 3.4 conforme feedback; precisa definir estorno de estoque e financeiro. |
| Comissão, histórico/lembrete de revisão, código de barras, multi-depósito | Diferenciais; priorizar pelo pedido dos pilotos. |
| Mac, web, celular | Ver `PLANO_COMERCIALIZACAO.md`. |

## Riscos

- **Migração de dados** (itens 1 e 5): testar com cópias de bases reais/demonstração e manter backup automático antes de migrar.
- **Escopo:** desconto toca modelos, relatórios e financeiro; manter testes de fluxo (`test_fluxo_negocio.py`) verdes.
- **Certificado:** o prazo de emissão pode atrasar a 3.3; comprar cedo.
- **Qualidade do exe:** hoje só validado por CI e pelo autoteste; o piloto deve testar em PC limpo.

## Ordem de trabalho sugerida

1. Item 1 (pasta de dados) → 2 (backup automático) → 3 e 4 → publicar **3.1**.
2. Itens 5 → 6 → 7 → 8 → publicar **3.2**.
3. Item 10 (iniciar a compra do certificado já na 3.2) → 9 → 11 → 12 → publicar **3.3** e iniciar pilotos.
4. Itens 13 e 14.

## Perguntas em aberto

1. Modelo de venda do ERP (define o formato da licença).
2. Backup em nuvem: basta "pasta configurável" ou quer integração direta com um serviço?
3. Limite de desconto por perfil: usar o padrão de 10% para vendedor ou configurar por cliente?
4. Quer comissão/mecânico já na 3.2 ou depois?
