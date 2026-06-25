# Phase 13/16 — Replay 2D

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas replay **2D offline** de demos gravadas. Você atua como **frontend engineer especialista em canvas/React-Konva**.

**Stack relevante a esta phase:** Next.js (client component), React-Konva (canvas 2D), TanStack Query. Consome `GET /matches/{id}/replay?round=&sample_rate=` e `GET /maps/{name}/radar|metadata`.

> **Importante (conversão de coordenadas):** o backend já entrega `radar_x/radar_y` prontos no payload de replay (feito na Phase 08 via `map_projection.py`). Você **não** precisa converter coordenadas para posicionar jogadores. O `frontend/lib/mapProjection.ts` desta phase serve para **desenho client-side** reutilizável (ex.: playbook na Phase 15) e usa a mesma fórmula do contrato de dados.

**Onde os arquivos vivem:**
```txt
frontend/app/replay/[matchId]/
frontend/components/Replay2D/
frontend/lib/mapProjection.ts        ← helper de conversão para desenho client-side
```

## Pré-requisitos

- Phase 08 (API de Analytics — endpoints de replay e maps, já com `radar_x/radar_y`) e Phase 09 (Frontend base) concluídas.

## Objetivo

Implementar um replayer 2D offline: radar do mapa como fundo, jogadores em movimento, timeline com eventos e controles de reprodução.

## Escopo (o que fazer)

Replayer 2D (client component com React-Konva):
- Radar do mapa como imagem de fundo (`GET /maps/{name}/radar`).
- Jogadores como círculos, posicionados via `radar_x/radar_y` do payload; cor por lado CT/T, nome/abreviação, direção (yaw), vida, arma atual, bomba (se disponível).
- Eventos importantes renderizados.
- Timeline com marcação de eventos: kills, bomb plant, bomb defuse, bomb explode e **granadas/flashes** (`type=grenade` com `grenade_type` he/flash/smoke/molotov), que agora vêm no payload de replay (eventos capturados na Phase 07).
- Renderização opcional da utility ativa no canvas (ex.: marcar detonação de HE/flash, área de molotov/smoke) usando os eventos de granada.
- Seleção de round, play/pause, controles de velocidade: `0.25x | 0.5x | 1x | 2x | 4x`.
- Interpolação simples entre frames, se possível.

`frontend/lib/mapProjection.ts`:
```ts
type RadarMetadata = { pos_x: number; pos_y: number; scale: number; image_width: number; image_height: number };
export function worldToRadar(x: number, y: number, m: RadarMetadata) {
  return { radarX: (x - m.pos_x) / m.scale, radarY: (m.pos_y - y) / m.scale };
}
```
(Usado para desenho client-side; o replay em si já vem convertido do backend.)

## Fora de escopo

- Nada de radar ao vivo / leitura do jogo em execução — apenas replay de demo gravada.
- Não implemente heatmaps (Phase 14) — mas deixe o `mapProjection.ts` reutilizável por ela.
- Otimização com PixiJS fica para fase futura.

## Entregáveis

- Componente `Replay2D` com canvas, timeline e controles.
- `frontend/lib/mapProjection.ts`.
- Tela `replay/[matchId]`.

## Critérios de aceite

- [ ] O replay mostra o radar do mapa e os jogadores se movendo.
- [ ] Cores por lado, yaw, vida e arma exibidos.
- [ ] Timeline marca eventos: kills, bomb events e granadas/flashes (por `grenade_type`).
- [ ] Seleção de round, play/pause e velocidades (0.25x–4x) funcionam.
- [ ] Jogadores aparecem na posição correta sobre o radar (usando `radar_x/radar_y`).
- [ ] `npm run lint` e `npm run build` passam.

## Comandos de validação

```bash
cd frontend
npm run dev   # com backend rodando e uma partida processada
npm run lint
npm run build
```

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 14 — Heatmaps** (`14-heatmaps.md`).
