# Phase 06/16 — Jobs de Parsing

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **backend engineer especialista em filas/jobs**.

**Stack relevante a esta phase:** RQ + Redis (fila de jobs), FastAPI, **PostgreSQL** (SQLAlchemy), logging. Redis local via `docker-compose`.

**Onde os arquivos vivem:** `backend/app/workers/jobs.py`, integração em `backend/app/api/routes_demos.py`, atualização de status em `backend/app/storage/db.py`.

## Pré-requisitos

- Phase 05 (Importação de demos) concluída.

## Objetivo

Introduzir o processamento assíncrono de parsing como job separado, com ciclo de vida de status e um **mock fallback** que permite testar o fluxo sem o parser real.

## Escopo (o que fazer)

- Adicionar serviço **`redis`** ao `docker-compose.yml`.
- Configurar fila de jobs com **RQ + Redis** (worker separado).
- Ao importar uma demo (`POST /demos/import`), enfileirar um job de parsing.
- Implementar o job em `workers/jobs.py` com as transições de status (coluna `demos.status` no PostgreSQL):
  ```txt
  pending → parsing → parsed
  pending → parsing → failed
  ```
- Logging claro de início, fim e erro do job.
- **Mock fallback:** quando o parser real (awpy/demoparser2) não estiver disponível, o job gera dados mockados **no schema exato do [contrato de dados](_shared/data-contract.md)** (PostgreSQL + Parquet, **incluindo as tabelas `grenades`, `blinds` e `shots`**, para que utility analytics, kill matrix e stats por arma funcionem com mock) e marca a demo como `parsed`, sem travar o fluxo. O mock deve ser indistinguível do real para o frontend.
- Garantir que a API **não trave** durante o parsing (processamento fora do request).

## Fora de escopo

- Não implemente o parsing real com awpy/demoparser2 ainda (Phase 07) — aqui basta o esqueleto do job + mock fallback.
- Não implemente endpoints de analytics (Phase 08).

## Entregáveis

- Serviço `redis` no `docker-compose.yml`.
- `workers/jobs.py` com o job de parsing e transições de status.
- Enfileiramento disparado pela importação de demo.
- Mock fallback funcional, aderente ao contrato de dados.

## Critérios de aceite

- [ ] Importar uma demo enfileira um job e a demo passa por `pending → parsing → parsed`.
- [ ] Em caso de erro, a demo vai para `failed` com erro logado e gravado em `demos.error`.
- [ ] A API responde normalmente enquanto o parsing roda (não bloqueia).
- [ ] Com o parser real ausente, o mock fallback conclui o job como `parsed` produzindo dados no schema do contrato.
- [ ] Worker RQ documentado (como iniciar).

## Comandos de validação

```bash
docker compose up -d postgres redis
cd backend
rq worker            # ou comando equivalente do projeto
uvicorn app.main:app --reload
pytest
```

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 07 — Parsing real** (`07-parsing-real.md`).
