# Fase 6 - Checklist

## Entregas implementadas

- Model `OrdemServico`.
- Model `ItemOS`.
- Repository de OS e itens.
- Service transacional de ordem de servico.
- Controller de OS.
- Tela **Ordem de Servico** no menu operacional.
- Abertura de OS por cliente e veiculo.
- Registro de defeito relatado e diagnostico.
- Inclusao de itens de peca e servico.
- Finalizacao de OS.
- Baixa automatica de estoque somente para itens do tipo `PECA`.
- Bloqueio de finalizacao quando nao houver estoque suficiente.
- Geracao automatica de lancamento financeiro a receber.

## Pendencias naturais para refinamento

- Trocar campos `cliente_id`, `veiculo_id` e `produto_id` por seletores pesquisaveis.
- Criar impressao da OS.
- Adicionar historico por cliente/veiculo.
- Permitir status intermediarios como aprovado, em execucao e aguardando peca.
