# Phase 09/16 — Frontend Base

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **frontend engineer (Next.js/TypeScript)**.

**Stack relevante a esta phase:** Node 20 LTS, `npm`, Next.js, TypeScript, React, TanStack Query, CSS Modules/Tailwind. Design escuro estilo analytics dashboard, desktop-first.

**Onde os arquivos vivem:**
```txt
frontend/
  app/            (rotas: page.tsx, demos/, matches/[id]/, replay/[matchId]/, analytics/, playbook/)
  components/
  lib/
    api.ts
    types.ts
  package.json
```

## Pré-requisitos

- Phase 04 (Backend mínimo) concluída. (Pode evoluir em paralelo às phases de parsing usando dados mockados no schema do contrato.)

## Objetivo

Criar a aplicação Next.js base: estrutura de rotas, layout principal, navegação, tema escuro, camada de API client e tipos compartilhados.

## Escopo (o que fazer)

- Criar app Next.js com TypeScript (Node 20, `npm`).
- Estrutura de rotas conforme a árvore acima.
- Layout principal + navegação entre as áreas (dashboard, demos, matches, replay, heatmaps, playbook).
- Tema escuro estilo analytics dashboard, responsivo desktop-first.
- `lib/api.ts`: camada de API client apontando para o backend local.
- `lib/types.ts`: tipos TypeScript compartilhados (Demo, Match, Player, Round, ReplayFrame, HeatmapPoint, UtilityStats, WeaponStats, Matchup, DeathPosition, BombsiteStats, GrenadeEvent, BlindEvent, ShotEvent, etc.), **derivados do [contrato de dados](_shared/data-contract.md)** (mapear `snake_case` → `camelCase` na borda).
- Configurar TanStack Query (provider + hooks base).
- Client components apenas onde necessário.

## Fora de escopo

- Não implemente as telas com conteúdo final ainda (Dashboard=10, Demos UI=11, Match Report=12, Replay 2D=13, Heatmaps=14, Playbook=15) — aqui ficam o esqueleto/rotas e a navegação.
- Não implemente o canvas do replay (Phase 13).

## Entregáveis

- App Next.js executável (`npm run dev`).
- Estrutura de rotas + layout + navegação + tema escuro.
- `lib/api.ts` e `lib/types.ts` (alinhados ao contrato de dados).
- TanStack Query configurado.

## Critérios de aceite

- [ ] `npm run dev` sobe o frontend e abre no navegador.
- [ ] Navegação entre as áreas principais funciona (mesmo com telas placeholder).
- [ ] Tema escuro aplicado.
- [ ] `lib/api.ts` consegue chamar o backend local (ex.: `/health` ou `/demos`).
- [ ] Tipos em `lib/types.ts` correspondem ao contrato de dados.
- [ ] `npm run lint` e `npm run build` passam.

## Comandos de validação

```bash
cd frontend
npm install
npm run dev
npm run lint
npm run build
```

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 10 — Dashboard** (`10-dashboard.md`).
