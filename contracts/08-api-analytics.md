# Phase 08/16 — API de Analytics

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **backend engineer + engenheiro de dados**.

**Stack relevante a esta phase:** FastAPI, Pydantic, DuckDB/Polars (consultas sobre Parquet), **PostgreSQL** (metadados).

**Onde os arquivos vivem:** `backend/app/api/routes_matches.py`, `routes_stats.py`, `routes_replay.py`, `routes_maps.py`, módulos de `backend/app/analytics/` (incluindo `map_projection.py`), e assets em `data/maps/`.

## Pré-requisitos

- Phase 07 (Parsing real) concluída (dados em PostgreSQL/Parquet/DuckDB no schema do contrato).

## Objetivo

Expor os dados processados via endpoints REST de matches, stats, replay, heatmap e maps — com payloads **exatamente no formato do [contrato de dados](_shared/data-contract.md)**. Inclui obter os assets de mapa e a conversão mundo→radar no backend.

## Escopo (o que fazer)

### Assets de mapa + conversão de coordenadas
- Obter as **radar images** e o **overview metadata** (`pos_x`, `pos_y`, `scale`, `image_width`, `image_height`) dos mapas e colocá-los em `data/maps/radars/` e `data/maps/radar_info/` (fontes pesquisadas na Phase 03).
- Implementar `backend/app/analytics/map_projection.py` com `world_to_radar(x, y, metadata)` (fórmula no contrato de dados).
- Replay e heatmap devem retornar `radar_x/radar_y` **já convertidos**.

### Endpoints
```http
GET /matches
GET /matches/{match_id}
GET /matches/{match_id}/summary
GET /matches/{match_id}/rounds
GET /matches/{match_id}/players
GET /matches/{match_id}/stats/player
GET /matches/{match_id}/stats/economy                    (se disponível: buy type / equip value por round)
GET /matches/{match_id}/stats/weapons                    (por player e arma: disparos, accuracy, kills, HS%, armas usadas)
GET /matches/{match_id}/stats/utility                    (granadas por tipo, HE/molly dano, flashes que cegaram, flash assists)
GET /matches/{match_id}/stats/matchups                   (kill matrix: quem matou quem, quantas vezes)
GET /matches/{match_id}/stats/death-positions?player=<steam_id>   (mortes do player + top_spot)
GET /matches/{match_id}/stats/bombsites                  (win rate de round por bombsite/time: onde mais vencemos quando fomos)
GET /matches/{match_id}/replay?round=1&sample_rate=8     (sample_rate = 1 frame a cada N ticks; events incluem kills, bomb e granadas/flashes)
GET /matches/{match_id}/heatmap?type=kills               (kills|deaths|path|utility|grenades; filtros: player, team, side, round_range, weapon, grenade_type)
GET /maps
GET /maps/{map_name}/radar                               (imagem do radar)
GET /maps/{map_name}/metadata                            (pos_x/pos_y/scale/...)
```

Métricas mínimas nos módulos de `analytics/`: kills, deaths, assists, ADR, KAST-like, entry attempts/kills/deaths, trade kills, clutches, utility damage, economy/buy type (se disponível), estatísticas por arma, por lado CT/T e por mapa.

**Utility & duelos (a partir de `grenades`, `blinds`, `damages`, `kills`):**
- Granadas lançadas por tipo e total (por player); HE lançadas; HE que deram dano (`he_with_damage`); dano total de HE (`he_damage_total`) e de molotov (`molotov_damage_total`).
- Flashes lançadas, **inimigos cegados** (`enemies_blinded`), tempo de cegueira de inimigos (`enemy_blind_time`), flash assists.
- **Kill matrix** (`/stats/matchups`): contagem de kills por par atacante→vítima — permite ver quantas vezes cada player morreu para quem.
- **Posições de morte** (`/stats/death-positions`): lista de mortes do player com `radar_x/radar_y` + `top_spot` (cluster onde mais morreu).
- **Sucesso por bombsite** (`/stats/bombsites`): por time/site, quantos plants, quantos round wins e a win rate — responde "em qual bomb mais vencemos quando fomos". Baseado em `rounds.bomb_site` + `winner` + `t_team`/`ct_team`.
- **Armas por player** (`/stats/weapons`): armas usadas, disparos (`shots`/`weapon_fire`), hits, accuracy, kills, headshots e dano por arma — ex.: o AWP de um player com tiros dados e pessoas mortas. Inclui também **HS% geral**, **dano por tiro** (`damage/shots`) e **first-shot accuracy** (acerto do 1º disparo de cada rajada — heurística).

Os payloads de **replay**, **heatmap**, **stats/utility**, **stats/matchups**, **stats/death-positions** e **maps/metadata** seguem exatamente os exemplos da seção 4 do [contrato de dados](_shared/data-contract.md).

## Fora de escopo

- Não implemente o frontend (Phases 09–15).
- Não implemente analytics avançado da Fase 2 (trade windows configuráveis, clutch probability, etc.).
- Não implemente o pattern finder.

## Entregáveis

- Todos os endpoints acima funcionais, lendo dos dados processados.
- `analytics/map_projection.py` + assets de mapa em `data/maps/`.
- Módulos `analytics/player_stats.py`, `economy.py`, `weapons.py` (disparos/accuracy/kills por arma), `utility.py` (granadas/flashes), `matchups.py` (kill matrix), `positions.py` (death-positions/`top_spot`), `sites.py` (win rate por bombsite), `heatmaps.py`, `replay_frames.py` conforme necessário.
- Respostas validadas por modelos Pydantic, no formato do contrato.

## Critérios de aceite

- [ ] `GET /matches` lista as partidas processadas.
- [ ] `GET /matches/{id}/summary`, `/rounds`, `/players` retornam dados coerentes.
- [ ] `GET /matches/{id}/stats/player` retorna as métricas mínimas.
- [ ] `GET /matches/{id}/stats/utility` retorna granadas por tipo, HE/molly dano, flashes que cegaram inimigos e flash assists por player.
- [ ] `GET /matches/{id}/stats/matchups` retorna a kill matrix (quem matou quem, quantas vezes).
- [ ] `GET /matches/{id}/stats/death-positions?player=<id>` retorna as mortes do player e o `top_spot`.
- [ ] `GET /matches/{id}/stats/bombsites` retorna plants, round wins e win rate por bombsite/time.
- [ ] `GET /matches/{id}/stats/weapons` retorna, por player e por arma, disparos, accuracy, kills e armas usadas, mais HS% geral, dano por tiro e first-shot accuracy.
- [ ] `GET /matches/{id}/replay?round=N&sample_rate=S` retorna frames com `radar_x/radar_y` no formato do contrato.
- [ ] `GET /matches/{id}/heatmap?type=kills|deaths|path|utility|grenades` responde para cada tipo (incluindo `path&player=<id>` para movimento), com pontos convertidos.
- [ ] `GET /maps`, `/maps/{name}/radar`, `/maps/{name}/metadata` respondem (imagem + metadata reais).

## Comandos de validação

```bash
docker compose up -d postgres redis
cd backend
pytest
uvicorn app.main:app --reload
# exercitar os endpoints com uma partida processada (ou mock)
```

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 09 — Frontend base** (`09-frontend-base.md`).
