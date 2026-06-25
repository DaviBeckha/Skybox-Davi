# Phase 07/16 — Parsing Real

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **especialista em parsing de demos CS2 + engenheiro de dados**.

**Stack relevante a esta phase:** awpy (parsing de alto nível / analytics), demoparser2 (tick-level granular), Polars (processamento), Parquet (armazenamento analítico), DuckDB (consultas), **PostgreSQL** (metadados).

**Onde os arquivos vivem:**
```txt
backend/app/parsers/parse_with_awpy.py
backend/app/parsers/parse_with_demoparser2.py
backend/app/storage/parquet.py
backend/app/storage/duckdb.py
backend/app/storage/db.py            (PostgreSQL)
data/processed/parquet/match_id=.../
data/processed/duckdb/cs2_lab.duckdb
```

## Pré-requisitos

- Phase 06 (Jobs de parsing) concluída (job + mock fallback prontos).

## Objetivo

Implementar o parsing real em camadas, extraindo os dados da demo e persistindo-os **exatamente no schema do [contrato de dados](_shared/data-contract.md)**: PostgreSQL (metadados), Parquet (analítico) e DuckDB (consultas).

## Escopo (o que fazer)

Parser em camadas:
- **Primeira opção:** `awpy` para parsing, estatísticas e visualizações quando útil.
- **Segunda opção:** `demoparser2` para dados tick-level e eventos específicos quando o awpy não expuser tudo.

Dados a extrair e mapear para as tabelas do contrato de dados:
- Metadados → tabelas `matches`, `players`, `rounds` (PostgreSQL).
- `kills`, `damages`, `bomb_events`, `ticks`, `replay_frames`, `rounds`, `players` → Parquet particionado por `match_id` (colunas exatamente como no contrato).
- **`grenades`** (eventos de granada: `thrown`/`detonate`/`expire`, por tipo, com `thrower`, `entity_id` e posição) e **`blinds`** (cada vítima cegada por flash: `flasher`, `victim`, `is_enemy`, `duration`, `entity_id`) → Parquet. Essenciais para utility analytics; o `demoparser2` expõe esses eventos (`player_blind`, detonações de granada, `inferno_startburn`, etc.).
- Em **`rounds`** (Parquet), preencher `bomb_site` (A/B do plant), `t_team`/`ct_team` (times em cada lado no round) — necessários para a win rate de round por bombsite.
- **`shots`** (1 linha por `weapon_fire`: `steam_id`, `weapon`, tick, posição) → Parquet. Permite contar disparos por arma e calcular accuracy (cruzando com `damages`).
- **`economy`** (por player por round: `money_start`, `equip_value`, `buy_type`) → Parquet, **best-effort** — só se o parser expuser dinheiro/valor de equipamento; caso contrário, grave nulos. Alimenta `stats/economy`.
- **Coordenadas:** grave nos Parquet apenas coordenadas do mundo (`x/y/z`); **não** calcule `radar_x/radar_y` aqui (o backend converte na Phase 08).
- Campos: weapon, tick, time, posição x/y/z, yaw (se disponível), hp, armor, alive, side CT/T, headshot, e os campos de granada/flash acima.

Armazenamento:
- **PostgreSQL:** metadados (match/players/rounds).
- **Parquet:** `data/processed/parquet/match_id=<uuid>/{rounds,players,economy,kills,damages,shots,bomb_events,grenades,blinds,ticks,replay_frames}.parquet`.
- **DuckDB:** views sobre os Parquet (`data/processed/duckdb/cs2_lab.duckdb`).

**Importante:** o schema produzido aqui deve ser **idêntico** ao do mock fallback (Phase 06), para o frontend funcionar igual com mock e com real.

Manter o mock fallback como caminho alternativo quando não houver demo/parser disponível. Se não houver `.dem` em `data/raw_demos/`, usar o mock; fixtures sintéticas para teste ficam em `backend/app/tests/fixtures/`.

## Fora de escopo

- Não implemente os endpoints de analytics que consomem esses dados (Phase 08).
- Não implemente UI.
- Estatísticas avançadas (trade windows configuráveis, clutch probability, etc.) ficam para fases futuras.

## Entregáveis

- `parsers/parse_with_awpy.py` e `parsers/parse_with_demoparser2.py`.
- `storage/parquet.py` e `storage/duckdb.py` (pipeline de escrita/consulta).
- Dados persistidos em PostgreSQL + Parquet + DuckDB para uma demo real ou fixture, no schema do contrato.

## Critérios de aceite

- [ ] Uma demo real (ou fixture) é parseada e gera os Parquet particionados por `match_id` com as colunas do contrato.
- [ ] As tabelas `grenades` e `blinds` são geradas com os eventos de granada/flash (não ficam vazias quando há utility na demo).
- [ ] `rounds.parquet` traz `bomb_site`, `t_team` e `ct_team` nos rounds com plant.
- [ ] `shots.parquet` é gerado (1 linha por disparo) e permite contar tiros por arma por player.
- [ ] Metadados (match/players/rounds) gravados no PostgreSQL.
- [ ] DuckDB consegue consultar os dados processados via views.
- [ ] Schema do parsing real == schema do mock fallback.
- [ ] Tratamento de erro para demo inválida (status `failed`).

## Comandos de validação

```bash
docker compose up -d postgres redis
cd backend
pytest
# rodar o job de parsing sobre uma demo/fixture e inspecionar data/processed/ e as tabelas no Postgres
```

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 08 — API de Analytics** (`08-api-analytics.md`).
