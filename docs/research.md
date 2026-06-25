# Pesquisa Técnica — cs2-lab

> Pesquisa fundacional que valida e detalha as decisões de stack do projeto. Coerente com as **Convenções técnicas** ([`contracts/00-indice.md`](../contracts/00-indice.md)) e o **contrato de dados** ([`contracts/_shared/data-contract.md`](../contracts/_shared/data-contract.md)). Esta é uma fase de **documentação**: nenhuma dependência é instalada aqui (isso ocorre a partir da Phase 04).

## 1. Backend

### FastAPI
Framework web assíncrono em Python, baseado em Starlette + Pydantic. Gera OpenAPI/Swagger automaticamente (útil para inspecionar os endpoints de analytics). Usaremos roteadores (`APIRouter`) por domínio (`health`, `demos`, `matches`, `stats`, `replay`, `heatmap`, `maps`).
- Docs: https://fastapi.tiangolo.com/
- Padrões adotados: modelos **Pydantic** para todos os payloads; injeção de dependência para a sessão do banco; respostas tipadas que casam com a seção 4 do contrato de dados.

### awpy e demoparser2 (parsing de demos CS2)
Duas bibliotecas primárias para ler demos `.dem` do CS2 (formato Source 2):
- **demoparser2** (`demoparser2`, projeto `demoparser` da Laihoo/Markus) — parser de alta performance escrito em Rust com binding Python; expõe eventos (`player_death`, `weapon_fire`, `player_hurt`, `bomb_planted`, `flashbang_detonate`, etc.) e ticks por jogador como DataFrames. É a base para extrair `kills`, `damages`, `shots`, `grenades`, `blinds`, `bomb_events` e `ticks`.
  - Repo: https://github.com/LaihoE/demoparser
- **awpy** (`awpy`) — biblioteca de mais alto nível para parsing + analytics + visualização de CS2; útil como referência de eventos e para os **assets/coordenadas de mapa** (overview/radar). Em versões recentes o awpy usa o próprio motor de parsing e oferece dados de navegação/mapa.
  - Repo: https://github.com/pnxenopoulos/awpy · Docs: https://awpy.readthedocs.io/

**Decisão:** `demoparser2` como parser primário (eventos + ticks → Parquet conforme contrato). `awpy` como apoio para metadata de mapa e validação cruzada. Ambos devem produzir o **mesmo schema** que o mock fallback (Phase 06).

### Polars
DataFrame library em Rust com API Python; rápida e com baixo consumo de memória, ideal para transformar a saída do parser em tabelas e escrever Parquet. Integra bem com Arrow/Parquet e com DuckDB.
- Docs: https://docs.pola.rs/

### Parquet
Formato colunar (Apache Arrow/Parquet) para a camada analítica. Layout particionado por partida: `data/processed/parquet/match_id=<uuid>/<tabela>.parquet`. Cada tabela carrega `match_id` como coluna além da partição (hive partitioning). Guardamos **apenas coordenadas do mundo**; `radar_x/radar_y` são derivados na API.

### DuckDB
Banco analítico embarcado (OLAP) que lê Parquet diretamente e cria **views** sobre os arquivos particionados. Arquivo local: `data/processed/duckdb/cs2_lab.duckdb`. Os endpoints de analytics (Phase 08) consultam preferencialmente via DuckDB/Polars.
- Docs: https://duckdb.org/docs/
- Exemplo de view (do contrato): `CREATE VIEW kills AS SELECT * FROM read_parquet('data/processed/parquet/match_id=*/kills.parquet', hive_partitioning=1);`

### PostgreSQL (SQLAlchemy + Alembic)
**Substitui o SQLite** sugerido no `contract.md` (override registrado nas Convenções técnicas). Guarda **metadados relacionais**: `demos`, `matches`, `players`, `rounds`, `tactics`. Acesso via **SQLAlchemy** (ORM/Core) e migrations versionadas com **Alembic**. Conexão por `DATABASE_URL` (`postgresql+psycopg://user:pass@localhost:5432/cs2_lab`). Driver recomendado: `psycopg` (v3).
- PostgreSQL: https://www.postgresql.org/docs/ · SQLAlchemy: https://docs.sqlalchemy.org/ · Alembic: https://alembic.sqlalchemy.org/

### RQ + Redis (fila de jobs)
**RQ (Redis Queue)** para enfileirar o parsing de demos de forma assíncrona, mantendo a API responsiva. Redis como broker. O fluxo: importar demo → enfileirar job → worker parseia (`pending → parsing → parsed|failed`).
- RQ: https://python-rq.org/ · Redis: https://redis.io/docs/
- **Celery** foi considerado como alternativa (mais recursos: retries, agendamento, múltiplos brokers), mas é **overkill** para um app local de usuário único. **Decisão:** RQ pela simplicidade; migração para Celery fica como possibilidade futura se houver necessidade de orquestração avançada.

## 2. Frontend

### Next.js + TypeScript
App Router (Next.js 14+/Node 20 LTS), TypeScript estrito. Server Components por padrão; `"use client"` apenas onde há interatividade (replay, heatmap, formulários do playbook).
- Docs: https://nextjs.org/docs

### React-Konva (canvas 2D)
Wrapper React para a Konva (canvas 2D) — usado no **replay 2D**, **heatmaps** e no **desenho do playbook** sobre a imagem de radar. Bom equilíbrio entre ergonomia (declarativo, em React) e performance para dezenas de objetos animados.
- Docs: https://konvajs.org/docs/react/
- **PixiJS** (WebGL) fica como **alternativa futura** caso a quantidade de elementos/efeitos exija aceleração por GPU.

### Recharts
Biblioteca de gráficos declarativa para React — usada no Match Report (ex.: gráfico simples de desempenho/round). Simples de integrar e suficiente para o MVP.
- Docs: https://recharts.org/

### TanStack Query
Gerenciamento de estado de servidor (fetching, cache, revalidação, polling do status de parsing). Reduz boilerplate de loading/erro e mantém a UI sincronizada com o backend.
- Docs: https://tanstack.com/query/latest

## 3. Assets de mapa CS2 (radar + overview)

Para posicionar jogadores/eventos sobre o radar, precisamos, por mapa, de:
- **Imagem de radar** (overview), normalmente PNG (ex.: 1024×1024). Vão em `data/maps/radars/<map>.png`.
- **Metadata de overview**: `pos_x`, `pos_y` (origem do mundo no canto do radar) e `scale` (unidades de mundo por pixel), além de `image_width`/`image_height`. Vão em `data/maps/radar_info/<map>.json` (ou equivalente). Payload exposto em `GET /maps/{name}/metadata`.

**Conversão mundo→radar** (acontece no **backend**, `analytics/map_projection.py`):
```ts
radarX = (x - pos_x) / scale
radarY = (pos_y - y) / scale   // eixo Y invertido
```
O frontend recebe `radar_x/radar_y` prontos nos payloads de replay/heatmap; `frontend/lib/mapProjection.ts` replica a fórmula **só** para desenho client-side (playbook).

**De onde obter os assets:**
1. **Arquivos do jogo** (CS2 instalado): os overviews/radar e os `.txt`/metadata de overview ficam nos arquivos do jogo (pasta de instalação do CS2). É a fonte canônica e a mais correta legalmente para uso pessoal/offline.
2. **awpy** — fornece dados de mapa/navegação e utilidades de coordenadas que ajudam a validar `pos_x/pos_y/scale`.
3. **Repositórios da comunidade** (ex.: SimpleRadar e coleções de overview metadata em projetos open-source de análise de CS) — úteis como referência cruzada de `scale`/origem.

**Mapas multi-nível (Nuke, Vertigo):** têm dois níveis (superior/inferior) com radares e offsets distintos. O metadata pode incluir um campo `levels` (no contrato, `levels: null` para mapas de nível único). O posicionamento desses mapas pode exigir ajuste por nível (escolher o radar/metadata conforme a coordenada `z` do jogador). Tratado como refinamento; não bloqueia o MVP.

## 4. Decisão de stack (resumo) e riscos

**Stack escolhida:** FastAPI + demoparser2 (parser) + Polars/Parquet + DuckDB (analytics) + PostgreSQL (metadados) + RQ/Redis (jobs); Next.js/TS + React-Konva + Recharts + TanStack Query (frontend); docker-compose para Postgres+Redis.

**Riscos técnicos de parsing de CS2:**
- **Evolução do formato Source 2:** atualizações do CS2 podem mudar nomes/estrutura de eventos; manter `demoparser2`/`awpy` atualizados e ter o **mock fallback** garante que o pipeline e o frontend continuem funcionando enquanto o parser real é ajustado.
- **Eventos de utility/flash:** flashes que cegam, `flash_assist` e dano de molotov/`inferno` exigem correlação entre eventos (`grenades` ↔ `damages` ↔ `kills`) e nem sempre vêm como campo direto — ver regras no contrato de dados (seções `grenades`/`blinds`/dano por granada).
- **`first_shot_accuracy`** é heurística (agrupar `shots` em rajadas por gap de ticks) — documentado como aproximação.
- **Shotguns e granadas distorcem `accuracy`** (vários pellets / não-armas) — tratar como aproximação.
- **Coordenadas e mapas multi-nível:** validar `pos_x/pos_y/scale` com metadata real; Nuke/Vertigo podem exigir ajuste por nível.
- **Performance:** demos longas geram muitos ticks; o downsample para `replay_frames` (por `sample_rate`) e o uso de Parquet/DuckDB mitigam memória e tempo de consulta.

**Conformidade:** todas as fontes/ferramentas são para **análise offline de demos gravadas**. Nada de leitura de memória, injeção ou vantagem em tempo real.
