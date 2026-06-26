# cs2-lab

Plataforma **local e pessoal** de análise de demos de Counter-Strike 2. Importa demos `.dem` gravadas, faz parsing offline, gera analytics (stats, replay 2D, heatmaps) e um playbook privado de táticas.

> **Em construção.** Este projeto está sendo construído em phases (ver [`contracts/`](contracts/)). A documentação completa (setup, comandos, arquitetura) é entregue na **Phase 03**.

## Regra inviolável

O cs2-lab faz apenas **analytics e revisão de demos gravadas**, offline. Não implementa leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real.

## Stack (resumo)

- **Backend:** Python 3.11+ (gerenciado com `uv`), FastAPI, SQLAlchemy + Alembic, PostgreSQL, Parquet + DuckDB, RQ + Redis.
- **Frontend:** Node 20 LTS, Next.js + TypeScript, TanStack Query.
- **Infra local:** `docker-compose` (PostgreSQL + Redis).

## Estrutura

```txt
backend/    FastAPI, parsers, analytics, storage, workers, tests
frontend/   Next.js (app, components, lib)
data/       raw_demos, processed (parquet/duckdb), maps
docs/       audit, research, architecture
```

## Assets de mapa (radares)

Os overviews dos mapas (imagens de radar) **não são versionados** (são assets da Valve). Para baixá-los dos arquivos oficiais do CS2 (via `awpy`) e popular `data/maps/`:

```bash
cd backend
uv run python -m scripts.fetch_map_assets
```

Sem isso, a API serve um placeholder do tamanho correto — os pontos e jogadores ainda aparecem na posição certa sobre o radar.

Veja o índice de execução em [`contracts/00-indice.md`](contracts/00-indice.md) e o progresso em [`contracts/CHECKLIST.md`](contracts/CHECKLIST.md).
