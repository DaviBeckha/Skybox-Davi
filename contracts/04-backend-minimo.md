# Phase 04/16 — Backend Mínimo

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **backend engineer (FastAPI)**.

**Stack relevante a esta phase:** Python 3.11+ (`uv` + `pyproject.toml`), FastAPI, Pydantic, **PostgreSQL** via SQLAlchemy + Alembic (driver `psycopg`). Testes com pytest. PostgreSQL local via `docker-compose`.

**Onde os arquivos vivem:**
```txt
backend/
  app/
    main.py
    api/            (routes_*.py)
    core/
      config.py     (settings + DATABASE_URL)
      paths.py
    storage/
      db.py         (engine/session SQLAlchemy → PostgreSQL)
      models.py     (modelos ORM) | schemas Pydantic em models/
    tests/
  alembic/          (migrations)
  pyproject.toml
docker-compose.yml  (serviço postgres)
```

## Pré-requisitos

- Phase 02 (Estrutura base) concluída.

## Objetivo

Subir um backend FastAPI mínimo, executável localmente, com healthcheck, configuração, paths locais, **PostgreSQL** inicializado via migrations, modelos Pydantic e estrutura de rotas pronta para crescer.

## Escopo (o que fazer)

- `pyproject.toml` (gerenciado com `uv`) com dependências: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `psycopg[binary]`, `alembic`, e extra `[dev]` com `pytest`, `httpx`.
- Adicionar serviço **`postgres`** ao `docker-compose.yml` (imagem oficial, volume, porta 5432, db `cs2_lab`).
- `core/config.py`: settings via `pydantic-settings`, incluindo `DATABASE_URL` (ex.: `postgresql+psycopg://cs2:cs2@localhost:5432/cs2_lab`).
- `core/paths.py`: paths locais (`data/raw_demos`, `data/processed/parquet`, `data/processed/duckdb`, `data/maps`).
- `storage/db.py`: engine + session factory SQLAlchemy apontando para PostgreSQL.
- Modelos ORM + Pydantic para as tabelas de metadados **conforme o [contrato de dados](_shared/data-contract.md)**: `demos`, `matches`, `players`, `rounds`.
- **Alembic**: migration inicial criando essas tabelas.
- `app/main.py`: instanciar FastAPI, registrar routers, evento de startup que verifica conexão com o banco.
- `GET /health` → `{ "status": "ok" }` (e opcionalmente checa conectividade do DB).
- Estrutura de rotas (`api/routes_demos.py`, `routes_matches.py`, `routes_replay.py`, `routes_stats.py`, `routes_maps.py`) como stubs registrados.
- Teste pytest do healthcheck (usando `httpx`/TestClient).
- Logging claro.

## Fora de escopo

- Não implemente upload/import de demo ainda (Phase 05).
- Não implemente jobs/parsing (Phases 06/07).
- Não implemente endpoints de analytics/replay/heatmap com lógica real (Phase 08) — apenas stubs registrados.

## Entregáveis

- `backend/pyproject.toml` e serviço `postgres` no `docker-compose.yml`.
- `backend/app/main.py` com `/health`.
- `core/config.py`, `core/paths.py`, `storage/db.py`, modelos ORM/Pydantic.
- `alembic/` com a migration inicial.
- `backend/app/tests/` com teste do healthcheck.

## Critérios de aceite

- [ ] `docker compose up -d postgres` sobe o banco; `alembic upgrade head` cria as tabelas.
- [ ] `uvicorn app.main:app --reload` sobe sem erros e conecta ao PostgreSQL.
- [ ] `GET /health` retorna `{ "status": "ok" }`.
- [ ] Tabelas `demos/matches/players/rounds` batem com o contrato de dados.
- [ ] `pytest` passa o teste do healthcheck.

## Comandos de validação

```bash
docker compose up -d postgres
cd backend
uv sync                      # ou: pip install -e ".[dev]"
alembic upgrade head
pytest
uvicorn app.main:app --reload
```

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 05 — Importação de demos** (`05-importacao-demos.md`). (A **Phase 09 — Frontend base** também já fica desbloqueada a partir daqui.)
