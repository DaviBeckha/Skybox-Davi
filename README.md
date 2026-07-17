# cs2-lab

Plataforma **local e pessoal** de análise de demos de Counter-Strike 2. Importa arquivos `.dem` gravados, faz parsing offline, e gera analytics completos: stats por partida, replay 2D interativo, heatmaps de posicionamento e um playbook privado de táticas.

> **Regra inviolável:** O cs2-lab faz apenas analytics e revisão de demos gravadas, offline. Não implementa leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real.

---

## Funcionalidades

- **Importação de demos** — upload de `.dem` via UI; parsing assíncrono em background
- **Match Report** — placar, times, rounds, KD/ADR/KAST, utility stats, kill matrix, win rate por bombsite e stats de armas por player
- **Replay 2D** — movimentação dos jogadores sobre o radar do mapa, com timeline de kills/granadas/bomb events, play/pause e velocidades de 0.25×–4×
- **Heatmaps** — kills, mortes, pathing, utility e granadas; filtros por player/time/side/round/tipo de granada
- **Dashboard** — visão geral de partidas e jobs de parsing em tempo real
- **Playbook privado** — criação e edição de táticas com desenho sobre o radar *(em desenvolvimento)*

---

## Stack

| Camada | Tecnologias |
|---|---|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy + Alembic, awpy / demoparser2, Polars, DuckDB, Parquet, RQ + Redis |
| **Banco relacional** | PostgreSQL (metadados de demos/partidas/players/rounds) |
| **Camada analítica** | Parquet (colunar) + DuckDB (consultas locais) |
| **Fila de jobs** | RQ + Redis |
| **Frontend** | Node 20 LTS, Next.js 14 + TypeScript, TanStack Query, Recharts |
| **Infra local** | Docker Compose (PostgreSQL + Redis) |

---

## Pré-requisitos

- **Docker** com `docker compose` (para PostgreSQL e Redis)
- **Python 3.11+** com [`uv`](https://github.com/astral-sh/uv) instalado
- **Node 20 LTS** com `npm`

---

## Setup

### 1. Clone e configure variáveis de ambiente

```bash
git clone <repo>
cd cs2-lab
cp .env.example .env
# Edite .env se necessário (DATABASE_URL e REDIS_URL já vêm pré-configurados)
```

### 2. Suba a infraestrutura local

```bash
docker compose up -d postgres redis
```

### 3. Backend — instale dependências e aplique migrations

```bash
cd backend
uv sync
uv run alembic upgrade head
```

### 4. Frontend — instale dependências

```bash
cd frontend
npm install
```

### 5. Assets de mapa (radar images)

Os overviews dos mapas não são versionados (são assets da Valve). Para baixá-los:

```bash
cd backend
uv run python -m scripts.fetch_map_assets
```

Sem isso, a API serve um placeholder do tamanho correto — os pontos e jogadores ainda aparecem na posição certa sobre o radar.

---

## Como rodar

Com o Docker Desktop em execução, na raiz do repositório:

```bash
docker compose up --build
```

O Compose inicia PostgreSQL, Redis, API, worker de parsing e frontend. Após a
inicialização, acesse:

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Healthcheck: http://localhost:8000/health

Para executar em segundo plano, use `docker compose up --build -d`. Os dados
do PostgreSQL e de `data/` persistem em volumes Docker; `docker compose down
-v` remove esses dados.

Se a porta 3000 já estiver em uso, defina `FRONTEND_PORT=3001` no `.env` antes
de subir o Compose e acesse o frontend em `http://localhost:3001`.

---

## Testes e lint

**Backend**
```bash
cd backend
docker compose up -d postgres   # banco cs2_lab_test é criado automaticamente
uv run pytest
uv run ruff check .
```

**Frontend**
```bash
cd frontend
npm run lint
npm run build
```

---

## Estrutura do projeto

```
backend/
  app/
    api/         rotas FastAPI (health, demos, matches, stats, replay, heatmap, maps)
    core/        config, settings, conexão DB
    parsers/     parsing de .dem (awpy/demoparser2 + mock fallback)
    analytics/   queries DuckDB/Polars, map_projection.py (mundo → radar)
    storage/     escrita/leitura de Parquet, repositórios SQLAlchemy
    workers/     jobs RQ (parsing assíncrono)
    tests/       pytest
  alembic/       migrations do banco relacional
  pyproject.toml

frontend/
  app/           rotas Next.js (App Router)
  components/    componentes React
  lib/           api.ts, types.ts, mapProjection.ts

data/
  raw_demos/              .dem importadas (não versionadas)
  processed/parquet/      match_id=<uuid>/<tabela>.parquet
  processed/duckdb/       cs2_lab.duckdb
  maps/radars/            imagens de radar (.png)
  maps/radar_info/        metadata de overview (pos_x, pos_y, scale)

docs/           audit.md, research.md, architecture.md
contracts/      planos das 16 phases + CHECKLIST.md + data-contract.md
docker-compose.yml
```

---

## Progresso

| # | Phase | Status |
|---|---|---|
| 01 | Auditoria do repositório | ✅ |
| 02 | Estrutura base | ✅ |
| 03 | Documentação base | ✅ |
| 04 | Backend mínimo | ✅ |
| 05 | Importação de demos | ✅ |
| 06 | Jobs de parsing | ✅ |
| 07 | Parsing real | ✅ |
| 08 | API de Analytics | ✅ |
| 09 | Frontend base | ✅ |
| 10 | Dashboard | ✅ |
| 11 | Demos UI | ✅ |
| 12 | Match Report | ✅ |
| 13 | Replay 2D | ✅ |
| 14 | Heatmaps | ✅ |
| 15 | Playbook privado | 🔄 |
| 16 | QA — aceite do MVP | ⏳ |

Detalhes de cada phase e critérios de aceite em [`contracts/CHECKLIST.md`](contracts/CHECKLIST.md).

---

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://cs2:cs2@localhost:5544/cs2_lab` | Conexão PostgreSQL |
| `REDIS_URL` | `redis://localhost:6379/0` | Conexão Redis |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL da API para o frontend |
