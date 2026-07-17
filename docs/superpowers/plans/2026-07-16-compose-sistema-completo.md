# Compose do Sistema Completo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Subir frontend, API, worker, PostgreSQL e Redis com `docker compose up --build`.

**Architecture:** API e worker reutilizam uma imagem Python e volume de dados. PostgreSQL e Redis têm healthchecks. Frontend é uma imagem Node multi-stage de produção.

**Tech Stack:** Docker Compose, Python 3.11, uv, FastAPI, Alembic, RQ, PostgreSQL 16, Redis 7, Node 20 e Next.js 15.

## Global Constraints

- Apenas analytics offline de demos `.dem`; sem capacidades anti-cheat ou em tempo real.
- Preservar portas 5544, 6379, 8000 e 3000; API/worker usam os DNS internos `postgres` e `redis`.
- Persistir e compartilhar dados analíticos; não incluir alterações preexistentes do usuário em commits.

---

### Task 1: Criar imagens de produção

**Files:** Create `backend/Dockerfile`, `backend/.dockerignore`, `frontend/Dockerfile`, `frontend/.dockerignore`.

- [ ] **Step 1: Rodar teste vermelho** — executar `$f='backend/Dockerfile','backend/.dockerignore','frontend/Dockerfile','frontend/.dockerignore'; if($f|Where-Object{-not(Test-Path $_)}){throw 'Dockerfiles ausentes'}`. Esperado: FAIL.

- [ ] **Step 2: Implementar backend** — `backend/Dockerfile` usa `python:3.11-slim`, instala `uv`, copia `pyproject.toml`/`uv.lock`, executa `uv sync --frozen --no-dev`, copia a fonte e inicia `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`. `backend/.dockerignore` exclui `.venv`, `venv`, caches, `.git`, `data` e bytecode.

- [ ] **Step 3: Implementar frontend** — `frontend/Dockerfile` usa estágios `dependencies`, `builder` e `runner` de `node:20-alpine`; instala com `npm ci`, recebe `ARG/ENV NEXT_PUBLIC_API_URL=http://localhost:8000`, executa `npm run build`, copia `package.json`, `node_modules`, `.next` e `public` ao runner e inicia `npm run start`. `frontend/.dockerignore` exclui `node_modules`, `.next`, `.turbo`, `.git`, `coverage` e logs npm.

- [ ] **Step 4: Rodar teste verde e builds** — executar o teste da etapa 1, depois `docker build -t cs2lab-backend:test backend` e `docker build --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 -t cs2lab-frontend:test frontend`. Esperado: exit code 0.

- [ ] **Step 5: Commit** — `git add backend/Dockerfile backend/.dockerignore frontend/Dockerfile frontend/.dockerignore; git commit -m "build: add production container images"`.

### Task 2: Orquestrar o sistema completo

**Files:** Modify `docker-compose.yml`.

- [ ] **Step 1: Rodar teste vermelho** — executar `$s=(docker compose config --format json|ConvertFrom-Json).services.psobject.Properties.Name; $m='postgres','redis','api','worker','frontend'|Where-Object{$_ -notin $s}; if($m){throw "Serviços ausentes: $($m -join ', ')"}`. Esperado: FAIL com `api`, `worker` e `frontend`.

- [ ] **Step 2: Implementar composição** — manter `postgres:16` (volume `cs2lab_pgdata`, `5544:5432`, `pg_isready`) e `redis:7` (`6379:6379`, `redis-cli ping`). Criar `api` com build `./backend`, imagem `cs2lab-backend`, volume `cs2lab_data:/app/data`, porta `8000:8000`, URLs `postgresql+psycopg://cs2:cs2@postgres:5432/cs2_lab` e `redis://redis:6379/0`, e comando `sh -c "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"`. Criar `worker` com a mesma imagem/URLs/volume e comando `uv run python -m app.workers.run_worker`. Ambos dependem de PostgreSQL/Redis saudáveis; worker também depende de API iniciada. Criar `frontend` com build `./frontend`, arg `${NEXT_PUBLIC_API_URL:-http://localhost:8000}`, imagem `cs2lab-frontend`, porta `3000:3000` e dependência da API. Declarar `cs2lab_data`.

- [ ] **Step 3: Rodar teste verde** — executar o teste da etapa 1 e `docker compose config --quiet`. Esperado: exit code 0 e cinco serviços.

- [ ] **Step 4: Commit** — `git add docker-compose.yml; git commit -m "feat: compose full local system"`.

### Task 3: Documentar o comando único

**Files:** Modify `.env.example`, `README.md`.

- [ ] **Step 1: Rodar teste vermelho** — executar `$r=Get-Content README.md -Raw; if($r -notmatch 'docker compose up --build' -or $r -match 'Abra três terminais'){throw 'Instrução única ausente'}`. Esperado: FAIL.

- [ ] **Step 2: Implementar documentação** — definir em `.env.example` os exemplos host `DATABASE_URL=postgresql+psycopg://cs2:cs2@localhost:5544/cs2_lab`, `REDIS_URL=redis://localhost:6379/0` e `NEXT_PUBLIC_API_URL=http://localhost:8000`. Atualizar README para `docker compose up --build` (ou `-d`), URLs frontend 3000/API 8000/health 8000/health, persistência em volumes e remoção com `docker compose down -v`.

- [ ] **Step 3: Rodar teste verde e commit** — executar o teste da etapa 1 e `git add .env.example README.md; git commit -m "docs: document full compose startup"`. Esperado: teste com exit code 0.

### Task 4: Verificação integrada

**Files:** nenhum.

- [ ] **Step 1: Iniciar e inspecionar** — executar `docker compose up --build -d; docker compose ps`. Esperado: PostgreSQL/Redis `healthy`; API, worker e frontend em execução.

- [ ] **Step 2: Verificar serviços e qualidade** — executar `(Invoke-RestMethod http://localhost:8000/health).status; (Invoke-WebRequest http://localhost:3000 -UseBasicParsing).StatusCode`; esperado: `ok` e `200`. Depois rodar `uv run pytest`/`uv run ruff check .` em `backend`, `npm test`/`npm run lint`/`npm run build` em `frontend` e `git diff --check`. Registrar comandos bloqueados por ambiente e não declarar validação completa sem evidência.
