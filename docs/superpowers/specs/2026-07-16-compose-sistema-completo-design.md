# Compose do sistema completo

## Objetivo

Permitir executar o cs2-lab localmente com `docker compose up --build`,
incluindo frontend, API, worker de parsing, PostgreSQL e Redis. A configuração
é de produção local: imagens reproduzíveis e sem hot reload ou montagem do
código-fonte como volume.

## Serviços

- **postgres**: PostgreSQL 16 com volume `cs2lab_pgdata`, publicado em
  `5544:5432` e healthcheck por `pg_isready`.
- **redis**: Redis 7, publicado em `6379:6379`, com healthcheck por
  `redis-cli ping`.
- **api**: imagem Python construída de `backend/`. Aguarda PostgreSQL e Redis
  saudáveis, executa `alembic upgrade head` e inicia Uvicorn em `8000`.
- **worker**: reutiliza a imagem da API e executa `python -m
  app.workers.run_worker`, aguardando PostgreSQL e Redis saudáveis.
- **frontend**: imagem multi-stage construída de `frontend/`; instala
  dependências com `npm ci`, gera o build do Next.js e inicia `next start` na
  porta `3000`.

## Rede, configuração e dados

Os serviços se comunicam pela rede padrão do Compose. API e worker recebem
`DATABASE_URL=postgresql+psycopg://cs2:cs2@postgres:5432/cs2_lab` e
`REDIS_URL=redis://redis:6379/0`; portanto não dependem de portas do host.

O frontend recebe `NEXT_PUBLIC_API_URL=http://localhost:8000` durante o build,
pois esse valor é executado pelo navegador no host. Ele pode ser substituído no
ambiente de build, mantendo esse valor como padrão local.

API e worker compartilham o volume `cs2lab_data`, montado em `/app/data`, para
preservar demos importadas, Parquet, DuckDB e assets de radar, e para que o
worker processe arquivos enviados pela API. O banco e os dados analíticos são
mantidos após `docker compose down`; são removidos apenas com `docker compose
down -v`.

## Arquivos e responsabilidades

- `backend/Dockerfile`: imagem Python 3.11 que instala dependências bloqueadas
  por `uv.lock`, copia o backend e expõe os comandos reutilizados por API e
  worker.
- `frontend/Dockerfile`: build multi-stage Node 20 para imagem final reduzida.
- `.dockerignore` em cada contexto: exclui ambientes locais, dependências,
  caches, artefatos de build e dados locais da construção das imagens.
- `docker-compose.yml`: orquestra os cinco serviços, variáveis internas,
  dependências, healthchecks, portas e volumes.
- `.env.example` e `README.md`: documentam o caminho único de inicialização e
  as URLs publicadas.

## Inicialização e falhas

O Compose só inicia API e worker após PostgreSQL e Redis ficarem saudáveis. A
API roda migrations idempotentes antes de servir requisições. O worker pode ser
reiniciado de forma independente e continua usando a fila Redis e os dados
persistidos.

Se uma dependência falhar, os healthchecks tornam o diagnóstico explícito em
`docker compose ps` e a API/worker não iniciam prematuramente. A configuração
não introduz funcionalidades de jogo em tempo real: ela somente executa os
componentes locais de analytics de demos gravadas existentes.

## Validação

1. `docker compose config` valida a composição e a interpolação de variáveis.
2. `docker compose up --build -d` cria e inicia os cinco serviços.
3. `docker compose ps` confirma PostgreSQL/Redis saudáveis e os demais serviços
   em execução.
4. `curl http://localhost:8000/health` retorna o healthcheck da API.
5. `curl http://localhost:3000` confirma que o frontend é servido.
6. `uv run pytest` e `uv run ruff check .` no backend; `npm run lint`,
   `npm run build` e `npm test` no frontend validam os projetos fonte quando as
   dependências locais estiverem disponíveis.
