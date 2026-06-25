# Arquitetura — cs2-lab

> Visão arquitetural do sistema. O **contrato de dados** ([`contracts/_shared/data-contract.md`](../contracts/_shared/data-contract.md)) é a fonte única de verdade para schemas e payloads; este documento descreve **como as peças se conectam**. Stack detalhada em [`docs/research.md`](research.md); comandos em [`AGENTS.md`](../AGENTS.md).

## 1. Visão geral

O cs2-lab é uma aplicação **local e de usuário único** para revisar demos de CS2 já gravadas. Quatro blocos:

- **Backend (FastAPI)** — API HTTP, importação de demos, orquestração de jobs, endpoints de analytics.
- **Frontend (Next.js/TS)** — UI: dashboard, lista de demos, match report, replay 2D, heatmaps, playbook.
- **Data** — armazenamento em três camadas: PostgreSQL (metadados), Parquet (analítico colunar) e DuckDB (consultas).
- **Jobs (RQ + Redis)** — parsing assíncrono das demos fora do ciclo de request da API.

```txt
                ┌─────────────────────────────────────────────────────────┐
                │                     Frontend (Next.js)                   │
                │  dashboard · demos · match report · replay · heatmap ·   │
                │  playbook        (lib/api.ts ↔ camelCase)                │
                └───────────────────────────▲─────────────────────────────┘
                                             │ HTTP (JSON, snake_case)
                ┌───────────────────────────┴─────────────────────────────┐
                │                     Backend (FastAPI)                    │
                │  api/  ·  analytics/ (DuckDB/Polars + map_projection)    │
                │  storage/ (SQLAlchemy + Parquet)  ·  parsers/  ·  workers/│
                └───┬───────────────┬───────────────────────┬─────────────┘
                    │               │                       │
            enqueue │         read  │ metadados       read  │ analítico
                    ▼               ▼                       ▼
              ┌──────────┐   ┌──────────────┐      ┌──────────────────────┐
              │  Redis   │   │  PostgreSQL  │      │ Parquet + DuckDB      │
              │  (RQ)    │   │ demos/matches│      │ kills/rounds/ticks/…  │
              └────┬─────┘   │ players/round│      └──────────▲───────────┘
                   │ consume │ tactics      │                 │ write
              ┌────▼─────────┴──────────────┴─────────────────┴───────────┐
              │                 Worker RQ (parsers/)                       │
              │  demoparser2/awpy → Polars → Parquet  (+ metadados no PG)  │
              └────────────────────────────────────────────────────────────┘
```

## 2. Fluxo de dados (import → parsing → storage → API → UI)

1. **Import** (Phase 05): o usuário envia um `.dem` via `POST /demos`. O arquivo é copiado para `data/raw_demos/` e um registro é criado em `demos` com status `pending`.
2. **Enqueue** (Phase 06): a importação enfileira um job de parsing no Redis (RQ). A API permanece responsiva.
3. **Parsing** (Phases 06–07): o worker pega o job, marca a demo como `parsing`, executa o parser (**demoparser2/awpy** real, ou **mock fallback** quando o parser real está ausente) e:
   - escreve as tabelas analíticas em **Parquet** particionado por `match_id` (`kills`, `damages`, `shots`, `grenades`, `blinds`, `bomb_events`, `rounds`, `players`, `economy`, `ticks`, `replay_frames`);
   - grava **metadados** em PostgreSQL (`matches`, `players`, `rounds`);
   - ao concluir, marca a demo como `parsed` (`parsed_at` preenchido); em erro, `failed` com `demos.error`.
   - **Invariante:** parser real e mock produzem **exatamente o mesmo schema** (contrato de dados), para o frontend não quebrar ao alternar entre eles.
4. **Storage** (Phase 07): DuckDB cria **views** sobre os Parquet (`data/processed/duckdb/cs2_lab.duckdb`).
5. **API/Analytics** (Phase 08): os endpoints consultam DuckDB/Polars e PostgreSQL, e o backend **adiciona `radar_x/radar_y`** aos payloads de replay/heatmap/death-positions via `analytics/map_projection.py` (usando o metadata de radar). Assets de mapa ficam em `data/maps/`.
6. **UI** (Phases 09–15): o frontend consome a API com TanStack Query; converte `snake_case`→`camelCase` na borda (`lib/api.ts`); renderiza dashboard, match report, replay 2D e heatmaps (React-Konva sobre a imagem de radar) e o playbook.

## 3. Organização de armazenamento

Três camadas, cada uma com um papel claro:

### PostgreSQL — metadados relacionais
Acesso via SQLAlchemy; migrations com Alembic. Tabelas (ver contrato, seção 1): `demos`, `matches`, `players`, `rounds`, `tactics` (playbook, Phase 15). Conexão por `DATABASE_URL`. Guarda o que é relacional, consultado por chave e mutável (status de demo, roster, placar, táticas).

### Parquet — camada analítica colunar
Layout: `data/processed/parquet/match_id=<uuid>/<tabela>.parquet` (hive partitioning). Guarda os eventos/ticks volumosos e **somente coordenadas do mundo** (`x/y/z`). `radar_x/radar_y` **não** são persistidos — são derivados na API (Phase 08), evitando dependência dos assets de mapa no momento do parsing (Phase 07). Tabelas: `rounds`, `players`, `economy`, `kills`, `damages`, `shots`, `bomb_events`, `grenades`, `blinds`, `ticks`, `replay_frames`.

### DuckDB — consultas analíticas locais
Arquivo `data/processed/duckdb/cs2_lab.duckdb` com **views** sobre os Parquet (ex.: `CREATE VIEW kills AS SELECT * FROM read_parquet('.../match_id=*/kills.parquet', hive_partitioning=1)`). Os endpoints de analytics consultam preferencialmente por aqui (ou Polars), agregando stats de player/utility/armas/bombsites/matchups e montando frames de replay e pontos de heatmap.

**Divisão de responsabilidade:** metadados pequenos e relacionais → **PostgreSQL**; séries/eventos volumosos e analytics → **Parquet + DuckDB**. `match_id` é a chave que liga as duas camadas.

## 4. Backend — módulos

- `api/` — roteadores FastAPI: `health`, `demos` (import/list/get), `matches` (summary/rounds/players), `stats` (player/utility/weapons/matchups/death-positions/bombsites/economy), `replay`, `heatmap`, `maps`.
- `core/` — settings (Pydantic Settings), `DATABASE_URL`/`REDIS_URL`, engine/sessão SQLAlchemy.
- `parsers/` — parser real (demoparser2/awpy) e **mock fallback**; ambos emitem o schema do contrato.
- `analytics/` — consultas DuckDB/Polars e `map_projection.py` (conversão mundo→radar; ver contrato, seção 5).
- `storage/` — escrita/leitura de Parquet e repositórios SQLAlchemy (metadados).
- `workers/` — definição/execução dos jobs RQ de parsing.
- `tests/` — pytest (healthcheck, import, CRUD do playbook, etc.).

## 5. Frontend — organização

- `app/` — rotas (App Router): dashboard, demos, match report, replay, heatmaps, playbook. Server Components por padrão; `"use client"` só onde há interação.
- `components/` — componentes reutilizáveis (tabelas de stats, timeline de replay, canvas do radar, cards).
- `lib/` — `api.ts` (cliente HTTP + conversão de nomes), `types.ts` (tipos espelhando o contrato), `mapProjection.ts` (desenho client-side do playbook com a mesma fórmula `worldToRadar`).

## 6. Infraestrutura local

`docker-compose.yml` sobe **PostgreSQL** (Phase 04) e **Redis** (Phase 06). A API e o worker rodam no host (via `uv run`); o frontend via `npm run dev`. Tudo offline; nenhum serviço externo obrigatório além de Postgres/Redis containerizados.

## 7. Conformidade (regra inviolável)

A arquitetura opera **exclusivamente** sobre demos `.dem` gravadas, de forma offline. Não há — e não deve haver — leitura de memória do jogo, DMA, injeção, wallhack, radar ao vivo ou qualquer automação/vantagem competitiva em tempo real.
