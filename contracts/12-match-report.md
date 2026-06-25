# Phase 12/16 — Match Report

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **frontend engineer + product analytics**.

**Stack relevante a esta phase:** Next.js, TypeScript, TanStack Query, Recharts. Consome `GET /matches/{id}/summary|rounds|players|stats/*`.

**Onde os arquivos vivem:** `frontend/app/matches/[id]/`, `frontend/components/MatchReport/`.

## Pré-requisitos

- Phase 08 (API de Analytics) e Phase 09 (Frontend base) concluídas.

## Objetivo

Implementar a tela de relatório de partida com placar, contexto e tabela de estatísticas dos jogadores.

## Escopo (o que fazer)

A tela de relatório deve conter:
- Placar, nome do mapa, times.
- Rounds da partida.
- Tabela de jogadores com: KD, ADR, KAST-like, entry stats, trade stats, clutch stats, estatísticas por arma.
- **Tabela de utility** (de `GET /stats/utility`): granadas lançadas por tipo, HE com dano, dano de HE e de molotov, flashes que cegaram inimigos, tempo de cegueira e flash assists por player.
- **Kill matrix** (de `GET /stats/matchups`): grade quem-matou-quem, deixando claro quantas vezes cada player morreu para cada adversário.
- **Sucesso por bombsite** (de `GET /stats/bombsites`): win rate de round por site e por time — em qual bomb o time mais venceu quando foi — com um gráfico simples comparando A vs B.
- **Armas por player** (de `GET /stats/weapons`): armas usadas na partida, disparos, accuracy, kills e HS% por arma (ex.: ver o AWP — tiros dados vs pessoas mortas), além de HS% geral, dano por tiro e first-shot accuracy do player.
- Gráficos simples (Recharts) — ex.: distribuição de kills, desempenho por round/lado.

Buscar dados via API client; tratar loading/erro.

## Fora de escopo

- Não implemente o replay 2D (Phase 13) nem heatmaps (Phase 14) — apenas, se útil, links para eles.
- Não implemente analytics avançado da Fase 2.

## Entregáveis

- Tela `matches/[id]` com resumo + tabela de jogadores + gráficos simples.
- Componentes em `components/MatchReport/`.

## Critérios de aceite

- [ ] Placar, mapa, times e rounds exibidos corretamente.
- [ ] Tabela de jogadores mostra KD, ADR, KAST-like, entry/trade/clutch e por arma.
- [ ] Tabela de utility mostra granadas por tipo, HE/molly dano, flashes que cegaram e flash assists.
- [ ] Kill matrix mostra quantas vezes cada player morreu para cada adversário.
- [ ] Sucesso por bombsite mostra a win rate de round por site/time (A vs B).
- [ ] Tabela de armas por player mostra armas usadas, disparos, accuracy e kills por arma.
- [ ] Pelo menos um gráfico simples renderiza.
- [ ] Estados de loading/erro tratados.
- [ ] `npm run lint` e `npm run build` passam.

## Comandos de validação

```bash
cd frontend
npm run dev   # com backend rodando e uma partida processada
npm run lint
npm run build
```

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 13 — Replay 2D** (`13-replay-2d.md`).
