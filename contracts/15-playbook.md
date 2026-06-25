# Phase 15/16 — Playbook Privado

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **full-stack engineer**.

**Stack relevante a esta phase:** Next.js, TypeScript, React-Konva/canvas (desenho no mapa); persistência em **PostgreSQL** (tabela `tactics`, ver contrato de dados) via FastAPI.

**Onde os arquivos vivem:** `frontend/app/playbook/`, componentes de editor/desenho; backend `backend/app/api/routes_playbook.py` + tabela `tactics` (PostgreSQL).

## Pré-requisitos

- Phase 09 (Frontend base) concluída. (Reaproveita o radar/`mapProjection.ts` do Replay 2D para o desenho.)

## Objetivo

Implementar a primeira versão de um playbook privado local: CRUD de táticas com desenho sobre o mapa e persistência no PostgreSQL.

## Escopo (o que fazer)

Backend:
- Endpoints CRUD `routes_playbook.py`: criar, listar, obter, editar, excluir tática.
- Persistir na tabela `tactics` (PostgreSQL) **conforme o [contrato de dados](_shared/data-contract.md)** (`tags`, `reference_rounds`, `drawing` como `jsonb`).

Frontend:
- Tela de playbook: lista + editor de tática.
- Associar tática a mapa e a lado CT/T; descrição, tags, rounds de referência.
- Desenhar pontos e linhas no mapa (canvas), salvando em `drawing`.

Modelo de tática (ver contrato de dados):
```json
{
  "id": "uuid", "name": "Mirage A Execute", "map": "de_mirage", "side": "T",
  "description": "Execução A com smokes padrão.",
  "tags": ["execute", "mirage", "a-site"],
  "reference_rounds": [], "drawing": { "points": [], "lines": [] }
}
```

## Fora de escopo

- Editor visual avançado, layers, utility lineups, exportação em imagem e clipes de demo ficam para a Fase 4 (Playbook Avançado).
- Pattern finder (Fase 3) não faz parte desta phase.

## Entregáveis

- Endpoints CRUD de táticas no backend (PostgreSQL).
- Tela de playbook com lista + editor + desenho no mapa.
- Persistência das táticas no PostgreSQL.

## Critérios de aceite

- [ ] É possível criar, editar e excluir uma tática.
- [ ] Tática pode ser associada a mapa e lado, com descrição/tags/rounds.
- [ ] Desenho de pontos e linhas no mapa funciona e é salvo em `drawing`.
- [ ] Táticas persistem no PostgreSQL entre sessões.
- [ ] `npm run lint` e `npm run build` passam; `pytest` cobre o CRUD.

## Comandos de validação

```bash
docker compose up -d postgres
cd backend && pytest
cd frontend && npm run dev && npm run lint && npm run build
```

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 16 — QA (aceite do MVP)** (`16-qa.md`).
