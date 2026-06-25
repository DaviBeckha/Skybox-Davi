# Phase 14/16 — Heatmaps

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **frontend engineer + data viz**.

**Stack relevante a esta phase:** Next.js, TypeScript, React-Konva/canvas, TanStack Query. Consome `GET /matches/{id}/heatmap?type=` e `GET /matches/{id}/stats/death-positions` (pontos já com `radar_x/radar_y`).

**Onde os arquivos vivem:** `frontend/app/analytics/` (ou rota de heatmaps), `frontend/components/Heatmap/`, `frontend/components/Filters/`.

## Pré-requisitos

- Phase 08 (API de Analytics — endpoint de heatmap) e Phase 09 (Frontend base) concluídas.

## Objetivo

Implementar a tela de heatmaps sobre o radar do mapa, com os tipos suportados e filtros básicos.

## Escopo (o que fazer)

Tela de heatmaps com tipos:
- Kills, Deaths, Pathing, Utility, **Grenades**.

Renderização sobre o radar do mapa, usando `radar_x/radar_y` já fornecidos pelo endpoint de heatmap (formato no [contrato de dados](_shared/data-contract.md), seção 4). Para desenho/escala adicional client-side, reutilizar `frontend/lib/mapProjection.ts` (Phase 13).

Recursos focados em player (objetivo: entender como cada player se movimenta e onde morre):
- **Mapa de movimento por player:** `type=path&player=<steam_id>` — heatmap da movimentação de um jogador específico.
- **Posição de morte #1:** consumir `GET /stats/death-positions?player=<id>`, plotar todas as mortes e **destacar o `top_spot`** (onde o player mais morreu na demo).
- **Heatmap de granadas:** `type=grenades` com filtro `grenade_type` (he/flash/smoke/molotov).

Filtros:
- Player, Team, Side CT/T, Round range, Weapon, Grenade type — enviados como query params ao endpoint.

Buscar dados via `GET /matches/{id}/heatmap?type=...`; tratar loading/erro.

## Fora de escopo

- Não reimplemente a conversão de coordenadas — os pontos já chegam convertidos do backend.
- Heatmaps por timing avançado ficam para a Fase 2.

## Entregáveis

- Tela de heatmaps com os 5 tipos (kills/deaths/pathing/utility/grenades).
- Componentes `Heatmap` e `Filters`.

## Critérios de aceite

- [ ] É possível ver ao menos um heatmap básico (ex.: kills) sobre o radar.
- [ ] Os tipos (kills/deaths/pathing/utility/grenades) são selecionáveis.
- [ ] Mapa de movimento de um player (`path` + filtro player) renderiza.
- [ ] Posição de morte do player mostra todas as mortes e destaca o `top_spot`.
- [ ] Filtros básicos (player/team/side/round range/grenade type) afetam o resultado.
- [ ] Pontos posicionados corretamente via `radar_x/radar_y`.
- [ ] `npm run lint` e `npm run build` passam.

## Comandos de validação

```bash
cd frontend
npm run dev   # com backend rodando e uma partida processada
npm run lint
npm run build
```

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 15 — Playbook privado** (`15-playbook.md`).
