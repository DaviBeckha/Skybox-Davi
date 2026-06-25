# Phase 10/16 — Dashboard

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **frontend engineer (Next.js/TypeScript)**.

**Stack relevante a esta phase:** Next.js, TypeScript, TanStack Query, Recharts (gráficos simples). Consome a API de analytics.

**Onde os arquivos vivem:** `frontend/app/page.tsx`, componentes em `frontend/components/`.

## Pré-requisitos

- Phase 08 (API de Analytics) e Phase 09 (Frontend base) concluídas.

## Objetivo

Implementar a tela inicial/dashboard com visão geral do estado da plataforma e atalhos para as áreas principais.

## Escopo (o que fazer)

A home deve conter:
- Cards: total de demos importadas, total de partidas processadas, total de mapas, total de jogadores identificados.
- Lista dos últimos jobs e seus status.
- Lista das últimas demos.
- Atalhos para importação, matches, replay e heatmaps.

Buscar dados via API client (TanStack Query). Tratar estados de loading/erro.

## Fora de escopo

- Não implemente a tela de demos com upload (Phase 11), match report (Phase 12), replay (Phase 13), heatmaps (Phase 14) nem playbook (Phase 15) — apenas links/atalhos para elas.

## Entregáveis

- Dashboard funcional em `app/page.tsx` com cards, listas e atalhos.
- Componentes reutilizáveis de card/lista quando fizer sentido.

## Critérios de aceite

- [ ] Cards exibem os totais corretos (a partir da API ou de mock).
- [ ] Últimos jobs e últimas demos aparecem com status.
- [ ] Atalhos navegam para as áreas corretas.
- [ ] Estados de loading e erro tratados.
- [ ] `npm run lint` e `npm run build` passam.

## Comandos de validação

```bash
cd frontend
npm run dev
npm run lint
npm run build
```

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 11 — Demos UI** (`11-demos-ui.md`).
