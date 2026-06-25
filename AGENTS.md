# AGENTS.md — cs2-lab

Guia operacional para agentes e desenvolvedores que trabalham neste repositório. É a **fonte de comandos e padrões**; as decisões de stack estão em [`docs/research.md`](docs/research.md), a arquitetura em [`docs/architecture.md`](docs/architecture.md) e o **contrato de dados normativo** em [`contracts/_shared/data-contract.md`](contracts/_shared/data-contract.md).

## Regra inviolável

O cs2-lab faz apenas **analytics e revisão de demos `.dem` gravadas**, offline e local. **Proibido** implementar: leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo competitivo, automação de gameplay, triggerbot, aimbot ou qualquer vantagem competitiva em tempo real.

## Visão geral da stack

| Camada | Tecnologias |
|--------|-------------|
| Backend | Python 3.11+ (`uv`), FastAPI, Pydantic, SQLAlchemy + Alembic, awpy/demoparser2, Polars, DuckDB, Parquet, RQ + Redis |
| Banco relacional | PostgreSQL (metadados) |
| Camada analítica | Parquet (colunar) + DuckDB (consultas locais) |
| Fila de jobs | RQ + Redis |
| Frontend | Node 20 LTS (`npm`), Next.js + TypeScript, TanStack Query, React-Konva, Recharts |
| Infra local | `docker-compose` (PostgreSQL + Redis) |

## Mapa de diretórios

```txt
backend/
  app/
    api/         rotas FastAPI (health, demos, matches, stats, replay, heatmap, maps)
    core/        config, settings, conexão DB, sessão
    parsers/     parsing de .dem (real via awpy/demoparser2 + mock fallback)
    analytics/   queries DuckDB/Polars, map_projection.py (mundo→radar)
    storage/     escrita/leitura de Parquet, repositórios SQLAlchemy
    workers/     jobs RQ (parsing assíncrono)
    tests/       pytest
frontend/
  app/           rotas Next.js (App Router)
  components/     componentes React
  lib/            api.ts, types.ts, mapProjection.ts
data/
  raw_demos/                  .dem importadas (não versionadas)
  processed/parquet/          match_id=<uuid>/<tabela>.parquet
  processed/duckdb/           cs2_lab.duckdb
  maps/radars/                imagens de radar (.png)
  maps/radar_info/            metadata de overview (pos_x, pos_y, scale)
docs/            audit.md, research.md, architecture.md
contracts/       planos das 16 phases + CHECKLIST.md + _shared/data-contract.md
docker-compose.yml   PostgreSQL + Redis
```

## Convenções de código e nomenclatura

- **Nomenclatura:** `snake_case` no backend/dados; `camelCase` no frontend. A conversão acontece na borda (API client em `frontend/lib/api.ts`).
- **IDs:** `uuid` v4 como string.
- **`steam_id`:** steamID64 sempre como **string** (nunca número — evita perda de precisão).
- **`side`:** `"CT"` ou `"T"`.
- **Coordenadas:** Parquet guarda **apenas** coordenadas do mundo (`x/y/z`). `radar_x/radar_y` são derivados pelo backend nos payloads de API (`analytics/map_projection.py`).
- **Tempo:** `tick` é `int64`; `time` é segundos (float) desde o início do round; timestamps de metadados em ISO 8601 (`timestamptz`).
- **Backend:** type hints **obrigatórios**; modelos **Pydantic** para payloads de API; SQLAlchemy para metadados; funções puras na camada analytics quando possível.
- **Frontend:** componentes bem separados; **Server Components por padrão**, `"use client"` **só** onde há interatividade/estado (replay, heatmap, formulários do playbook); tipos em `lib/types.ts` espelhando o contrato de dados.

## Comandos — Backend

> Executados a partir de `backend/`. Em Windows, se `uv` não estiver no PATH, use `py -m uv` no lugar de `uv`.

```bash
# Ambiente e dependências (uv gerencia .venv + pyproject.toml)
uv sync                              # cria .venv e instala dependências
uv add <pacote>                      # adiciona dependência

# Infra local (a partir da raiz do repo)
docker compose up -d postgres redis  # sobe PostgreSQL + Redis
docker compose down                  # derruba

# Migrations (Alembic)
uv run alembic upgrade head          # aplica migrations
uv run alembic revision --autogenerate -m "mensagem"   # gera nova migration

# Subir a API
uv run uvicorn app.main:app --reload # http://localhost:8000  (health: /health)

# Worker de parsing (RQ) — Phase 06+
uv run python -m app.workers.run_worker   # consome a fila "cs2-parsing"
# (usa SimpleWorker, sem fork — funciona no Windows; substitui o `rq worker`)

# Testes e lint
uv run pytest                        # testes
uv run ruff check .                  # lint
uv run ruff format .                 # format
```

Variável de ambiente principal: `DATABASE_URL` (ex.: `postgresql+psycopg://cs2:cs2@localhost:5544/cs2_lab`) e `REDIS_URL` (ex.: `redis://localhost:6379/0`). Use um `.env` (ver `.env.example`).

> **Nota de ambiente (Phase 04):** o container Postgres publica na porta **5544** do host (mapeada para a 5432 interna) porque as portas 5432 e 5433 já estavam ocupadas por instalações locais de PostgreSQL. Se elas estiverem livres na sua máquina, pode ajustar `docker-compose.yml` e `DATABASE_URL` para a porta que preferir.

## Comandos — Frontend

> Executados a partir de `frontend/`.

```bash
npm install        # instala dependências
npm run dev        # ambiente de desenvolvimento (http://localhost:3000)
npm run lint       # ESLint
npm run build      # build de produção
npm run start      # serve o build
```

Variável de ambiente: `NEXT_PUBLIC_API_URL` (ex.: `http://localhost:8000`).

## Como rodar testes e lint (resumo)

- **Backend:** `uv run pytest` (testes) e `uv run ruff check .` (lint).
  - Os testes usam **PostgreSQL exclusivamente** (sem SQLite): criam e usam um banco dedicado **`cs2_lab_test`** no mesmo container. Suba o Postgres antes (`docker compose up -d postgres`).
- **Frontend:** `npm run lint` e `npm run build` (o build precisa passar).

## Definição de Pronto (DoD)

Uma phase/tarefa só é considerada **pronta** quando:

1. O escopo da phase foi implementado **exatamente** como no contrato (sem antecipar phases futuras).
2. Os **critérios de aceite** da phase estão todos ✓ (ver `contracts/CHECKLIST.md`).
3. **Comandos de validação** da phase rodam e passam — evidência antes de afirmação.
4. O código segue o **contrato de dados** (nomes de coluna, tipos e payloads batem entre quem grava e quem lê; mock e parsing real produzem o **mesmo schema**).
5. Backend: `pytest` e `ruff check` passam. Frontend: `npm run lint` e `npm run build` passam.
6. **Commit atômico** com mensagem clara (ex.: `feat(phase-04): backend minimo`) e a phase marcada no índice e no checklist.
7. Nada viola a **regra inviolável** anti-cheat.
