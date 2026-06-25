# Phase 05/16 — Importação de Demos

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **backend engineer (FastAPI)**.

**Stack relevante a esta phase:** FastAPI (upload de arquivo), Pydantic, **PostgreSQL** (SQLAlchemy).

**Onde os arquivos vivem:** `backend/app/api/routes_demos.py`, `backend/app/storage/db.py`, destino dos arquivos em `data/raw_demos/`.

## Pré-requisitos

- Phase 04 (Backend mínimo) concluída (PostgreSQL + tabela `demos` prontos).

## Objetivo

Permitir importar uma demo `.dem` localmente: validar, copiar para `data/raw_demos`, registrar no PostgreSQL com status inicial e expor endpoints de listagem/consulta.

## Escopo (o que fazer)

- `POST /demos/import`:
  - Receber arquivo (`.dem`) via upload local.
  - Validar extensão `.dem` (rejeitar outras com erro claro — HTTP 400).
  - Copiar o arquivo para `data/raw_demos/`.
  - Criar registro na tabela `demos` (PostgreSQL) com `status = "pending"`, `created_at`, `filename`, `path` — **conforme o [contrato de dados](_shared/data-contract.md)**.
  - Retornar o registro criado.
- `GET /demos`: listar demos importadas.
- `GET /demos/{demo_id}`: consultar uma demo específica (404 quando não existe).

Ciclo de vida do `status` (esta phase cria em `pending`; transições são da Phase 06):
```txt
pending | parsing | parsed | failed
```

## Fora de escopo

- Não dispare nem implemente o job de parsing (Phase 06).
- Não faça parsing real da demo (Phase 07).
- Não implemente a UI de upload (Phase 11).

## Entregáveis

- Endpoints `POST /demos/import`, `GET /demos`, `GET /demos/{demo_id}` funcionais.
- Persistência de metadados de demo no PostgreSQL.
- Arquivo copiado para `data/raw_demos/`.

## Critérios de aceite

- [ ] Upload de um `.dem` cria registro com status `pending` e copia o arquivo para `data/raw_demos/`.
- [ ] Upload de arquivo não-`.dem` é rejeitado com erro claro (400).
- [ ] `GET /demos` lista a demo importada.
- [ ] `GET /demos/{demo_id}` retorna a demo correta (e 404 quando não existe).
- [ ] Campos persistidos batem com o contrato de dados.

## Comandos de validação

```bash
docker compose up -d postgres
cd backend
uvicorn app.main:app --reload
# testar POST /demos/import com um arquivo .dem
pytest
```

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 06 — Jobs de parsing** (`06-jobs-parsing.md`).
