# Phase 03/16 — Documentação Base

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `docs/audit.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **tech lead documentando o projeto**.

**Stack relevante a esta phase:** Backend (Python 3.11+, FastAPI, awpy, demoparser2, Polars, DuckDB, Parquet, **PostgreSQL** via SQLAlchemy/Alembic, RQ+Redis) e Frontend (Next.js, TypeScript, React-Konva, TanStack Query, Recharts).

**Onde os arquivos vivem:** `AGENTS.md` (raiz), `docs/research.md`, `docs/architecture.md`.

## Pré-requisitos

- Phase 02 (Estrutura base) concluída.

## Objetivo

Produzir a documentação fundacional que orienta todas as phases seguintes: convenções, comandos, decisões de stack e arquitetura. Deve ser **coerente com as Convenções técnicas e o contrato de dados** já definidos.

## Escopo (o que fazer)

### `AGENTS.md`
Deve conter:
- Comandos de backend (criar ambiente com `uv`, instalar, subir PostgreSQL+Redis via `docker compose up`, rodar migrations Alembic, rodar testes, subir API).
- Comandos de frontend (instalar com `npm`, dev, lint, build).
- Padrões de código (type hints obrigatórios, Pydantic models, componentes bem separados, client components só onde necessário).
- Convenções de diretório (mapa da árvore do projeto) e de nomenclatura (ver Convenções técnicas no índice).
- Como rodar testes e lint.
- Definição de pronto.

### `docs/research.md`
Pesquisa técnica atualizada (documentações oficiais e repositórios primários) cobrindo:
- Backend: FastAPI, awpy, demoparser2, Polars, DuckDB, Parquet, **PostgreSQL** (SQLAlchemy/Alembic), RQ+Redis (Celery apenas como comparação).
- Frontend: Next.js, React-Konva (PixiJS como alternativa futura), Recharts, TanStack Query.
- Assets de mapa CS2: radar images, overview metadata (`pos_x`, `pos_y`, `scale`), conversão de coordenadas mundo→radar, tratamento de mapas multi-nível (Nuke, Vertigo), e **de onde obter** esses assets.
- Decisão objetiva de stack e riscos técnicos de parsing de CS2.

### `docs/architecture.md`
- Visão da arquitetura (backend, frontend, data, jobs), fluxo de dados (import → parsing job → storage → API → UI), e organização de armazenamento: **PostgreSQL** (metadados) + Parquet + DuckDB (analítico). Referencie o [contrato de dados](_shared/data-contract.md).

## Fora de escopo

- Não implemente código de aplicação.
- Não contrarie as Convenções técnicas/contrato de dados já definidos (a pesquisa valida e detalha).

## Entregáveis

- `AGENTS.md` completo na raiz.
- `docs/research.md` com a pesquisa técnica.
- `docs/architecture.md` com a arquitetura.

## Critérios de aceite

- [ ] `AGENTS.md` cobre comandos back/front (incluindo docker compose e Alembic), padrões, convenções, testes/lint e definição de pronto.
- [ ] `docs/research.md` cobre todas as tecnologias listadas (incluindo PostgreSQL) e o tema de assets de mapa com fontes.
- [ ] `docs/architecture.md` descreve fluxo de dados e armazenamento e referencia o contrato de dados.
- [ ] Documentação coerente com as Convenções técnicas do índice.

## Comandos de validação

- N/A (documentação). Revisão de conteúdo.

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 04 — Backend mínimo** (`04-backend-minimo.md`).
