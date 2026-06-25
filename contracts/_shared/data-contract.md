# Contrato de Dados — cs2-lab (fonte única de verdade)

> Este documento é **normativo**. Toda phase que **grava** ou **lê** dados deve seguir exatamente os nomes de coluna, tipos e payloads aqui definidos. Quando o parsing real e o mock divergem deste contrato, o frontend quebra ao trocar de mock para dados reais — então **mock e real produzem o mesmo schema**.

## Convenções gerais

- **Nomenclatura:** `snake_case` no backend/dados; `camelCase` no frontend. Mapeie na borda (API client).
- **IDs:** `uuid` v4 como string.
- **`steam_id`:** steamID64 como **string** (nunca número, para não perder precisão).
- **`side`:** `"CT"` ou `"T"`.
- **Coordenadas:** `x/y/z` são coordenadas **do mundo** (float), vindas da demo. `radar_x/radar_y` são derivadas via `worldToRadar` (ver seção "Conversão de coordenadas").
- **Tempo:** `tick` é `int64`; `time` é segundos (float) desde o início do round; timestamps de metadados em ISO 8601 (`timestamptz`).
- **`status` da demo:** `pending | parsing | parsed | failed`.

## 1. Banco relacional — PostgreSQL (metadados)

> Substitui o SQLite do `contract.md`. Acesso via SQLAlchemy; migrations com Alembic. Conexão por `DATABASE_URL` (ex.: `postgresql+psycopg://user:pass@localhost:5432/cs2_lab`).

### Tabela `demos`
| coluna       | tipo         | notas                              |
|--------------|--------------|------------------------------------|
| id           | uuid         | PK                                 |
| filename     | text         | nome original do `.dem`            |
| path         | text         | caminho em `data/raw_demos/`       |
| status       | text         | `pending\|parsing\|parsed\|failed` |
| created_at   | timestamptz  | criação do registro                |
| parsed_at    | timestamptz  | nulo até concluir parsing          |
| error        | text         | nulo; mensagem quando `failed`     |

### Tabela `matches`
| coluna     | tipo        | notas                         |
|------------|-------------|-------------------------------|
| id         | uuid        | PK                            |
| demo_id    | uuid        | FK → `demos.id`               |
| map        | text        | ex.: `de_mirage`              |
| team_a     | text        |                               |
| team_b     | text        |                               |
| score_a    | int         |                               |
| score_b    | int         |                               |
| started_at | timestamptz | nulo se indisponível          |
| tick_rate  | int         | ex.: 64                       |

### Tabela `players`
| coluna   | tipo | notas                          |
|----------|------|--------------------------------|
| match_id | uuid | FK → `matches.id`              |
| steam_id | text | steamID64                      |
| name     | text |                                |
| team     | text | `team_a`/`team_b` ou nome      |
| PK       |      | (`match_id`, `steam_id`)       |

### Tabela `rounds`
| coluna       | tipo  | notas                          |
|--------------|-------|--------------------------------|
| match_id     | uuid  | FK → `matches.id`              |
| round_number | int   | 1-based                        |
| winner       | text  | `CT` ou `T`                    |
| reason       | text  | `elimination`, `bomb`, etc.    |
| start_tick   | int64 |                                |
| end_tick     | int64 |                                |
| PK           |       | (`match_id`, `round_number`)   |

### Tabela `tactics` (playbook — Phase 15)
| coluna           | tipo        | notas                                   |
|------------------|-------------|-----------------------------------------|
| id               | uuid        | PK                                      |
| name             | text        |                                         |
| map              | text        |                                         |
| side             | text        | `CT` ou `T`                             |
| description      | text        |                                         |
| tags             | jsonb       | array de strings                        |
| reference_rounds | jsonb       | array de `{match_id, round_number}`     |
| drawing          | jsonb       | `{ "points": [...], "lines": [...] }`   |
| created_at       | timestamptz |                                         |
| updated_at       | timestamptz |                                         |

## 2. Camada analítica — Parquet (particionada por match)

Layout: `data/processed/parquet/match_id=<uuid>/<tabela>.parquet`. Toda tabela carrega `match_id` (string) como coluna além da partição.

> **Coordenadas:** os Parquet guardam **apenas coordenadas do mundo** (`x/y/z`). Os campos `radar_x/radar_y` **não** são armazenados — o backend os adiciona nos payloads de API (replay/heatmap/etc.) na Phase 08, usando o metadata do radar. Isso evita depender dos assets de mapa no momento do parsing (Phase 07).

### `rounds.parquet`
`match_id` (str), `round_number` (int), `winner` (str), `reason` (str), `start_tick` (int64), `end_tick` (int64), `bomb_planted` (bool), `bomb_site` (str: `A|B|null`), `plant_tick` (int64|null), `defuse_tick` (int64|null), `t_team` (str — time no lado T neste round), `ct_team` (str — time no lado CT neste round).
- `bomb_site` + `winner` + `t_team`/`ct_team` permitem calcular a win rate de round por bombsite e por time (mesmo com a troca de lados no intervalo).

### `players.parquet` (roster da partida)
`match_id` (str), `steam_id` (str), `name` (str), `team` (str), `starting_side` (str).

### `economy.parquet` (por player por round — best-effort, "se disponível")
`match_id` (str), `round_number` (int), `steam_id` (str), `side` (str), `money_start` (int|null), `equip_value` (int|null), `buy_type` (str|null: `eco|force|full`).
- Depende de o parser expor dinheiro/valor de equipamento no início do round. Se indisponível, gravar nulos e `stats/economy` retorna vazio. Não bloqueia o MVP.

### `kills.parquet`
`match_id` (str), `round_number` (int), `tick` (int64), `time` (float), `attacker_steam_id` (str), `victim_steam_id` (str), `assister_steam_id` (str|null), `weapon` (str), `headshot` (bool), `attacker_side` (str), `victim_side` (str), `attacker_x/attacker_y/attacker_z` (float), `victim_x/victim_y/victim_z` (float).

### `damages.parquet`
`match_id` (str), `round_number` (int), `tick` (int64), `time` (float), `attacker_steam_id` (str), `victim_steam_id` (str), `weapon` (str), `hp_damage` (int), `armor_damage` (int), `hitgroup` (str).

### `shots.parquet` (1 linha por disparo — evento `weapon_fire`)
`match_id` (str), `round_number` (int), `tick` (int64), `time` (float), `steam_id` (str), `weapon` (str), `x/y/z` (float — posição do atirador).
- "Disparos por arma" = contar linhas por (`steam_id`, `weapon`). Granadas/molotov também emitem `weapon_fire` ao lançar — filtre pelo `weapon` de fogo quando quiser só armas. Shotgun = 1 linha por disparo (não por pellet).

### `bomb_events.parquet`
`match_id` (str), `round_number` (int), `tick` (int64), `time` (float), `event` (str: `plant|defuse|explode`), `steam_id` (str|null), `site` (str|null), `x/y/z` (float|null).

### `grenades.parquet` (eventos de granada — 1 linha por evento)
`match_id` (str), `round_number` (int), `tick` (int64), `time` (float), `thrower_steam_id` (str), `thrower_side` (str), `grenade_type` (str: `he|flash|smoke|molotov|incendiary|decoy`), `event` (str: `thrown|detonate|expire`), `x/y/z` (float — posição do evento, coordenadas do mundo), `entity_id` (int|null — id da instância, correlaciona `thrown`↔`detonate`).
- "Granadas lançadas" = linhas com `event='thrown'`. "HE lançadas" = `grenade_type='he' AND event='thrown'`.

### `blinds.parquet` (eventos de cegueira por flash — 1 linha por vítima cegada)
`match_id` (str), `round_number` (int), `tick` (int64), `time` (float), `flasher_steam_id` (str|null), `victim_steam_id` (str), `flasher_side` (str|null), `victim_side` (str), `is_enemy` (bool — lados opostos), `duration` (float — segundos de cegueira), `entity_id` (int|null — flash que causou).
- "Flashes que cegaram inimigos" = flashes (`entity_id`) distintas com pelo menos uma linha `is_enemy=true`. "Flash assist" = vítima inimiga cegada que morre logo em seguida (correlacionar com `kills`), ou campo direto do parser quando disponível.

### Dano por tipo de granada
Derivado de `damages.parquet` pelo campo `weapon`: HE → `weapon='hegrenade'`; molotov/incendiária → `weapon ∈ {'molotov','incgrenade','inferno'}` (CS2 costuma reportar o dano de fogo como `inferno`). "HE que deram dano" = HE (`grenades` com `event='detonate'`) correlacionadas a linhas de `damages` com `weapon='hegrenade'` no mesmo round/janela.

### `ticks.parquet` (granular, por jogador por tick)
`match_id` (str), `round_number` (int), `tick` (int64), `time` (float), `steam_id` (str), `name` (str), `side` (str), `x/y/z` (float), `yaw` (float|null), `hp` (int), `armor` (int), `weapon` (str), `alive` (bool).

### `replay_frames.parquet` (downsample de `ticks` para replay)
Mesmas colunas de `ticks.parquet` (apenas coordenadas do mundo). O backend adiciona `radar_x/radar_y` no payload de replay — **não** são armazenados no Parquet. Amostragem definida por `sample_rate` (ver seção 4).

## 3. DuckDB (consultas analíticas locais)

Arquivo: `data/processed/duckdb/cs2_lab.duckdb`. Cria **views** sobre os Parquet acima, ex.:
```sql
CREATE VIEW kills AS SELECT * FROM read_parquet('data/processed/parquet/match_id=*/kills.parquet', hive_partitioning=1);
-- idem: rounds, players, economy, damages, shots, bomb_events, grenades, blinds, ticks, replay_frames
```
Os endpoints de analytics (Phase 08) consultam preferencialmente via DuckDB/Polars.

## 4. Payloads de API

### Replay — `GET /matches/{id}/replay?round=N&sample_rate=S`
`sample_rate=S` significa **1 frame a cada S ticks** (fps efetivo ≈ `tick_rate / S`). Default sugerido: `S=8`.
```json
{ "match_id": "abc123", "map": "de_mirage", "round": 1, "tick_rate": 64,
  "frames": [ { "tick": 12345, "time": 12.34, "players": [
    { "steam_id": "7656119...", "name": "player", "side": "T",
      "x": 0, "y": 0, "z": 0, "radar_x": 512, "radar_y": 384,
      "hp": 100, "armor": 100, "weapon": "ak47", "yaw": 180, "alive": true } ],
    "events": [ { "type": "kill|bomb_plant|bomb_defuse|bomb_explode|grenade",
                  "grenade_type": "he|flash|smoke|molotov|null",
                  "tick": 12345, "x": 0, "y": 0, "radar_x": 0, "radar_y": 0 } ] } ] }
```

### Heatmap — `GET /matches/{id}/heatmap?type=kills|deaths|path|utility|grenades`
Filtros via query: `player`, `team`, `side`, `round_range`, `weapon`, `grenade_type`. `type=path&player=<id>` = mapa de movimento de um player.
```json
{ "match_id": "abc123", "map": "de_mirage", "type": "kills",
  "points": [ { "x": 0, "y": 0, "radar_x": 512, "radar_y": 384, "weight": 1 } ],
  "filters_applied": { "player": null, "team": null, "side": null, "round_range": null, "weapon": null, "grenade_type": null } }
```

### Utility stats — `GET /matches/{id}/stats/utility`
```json
{ "match_id": "abc123", "players": [
  { "steam_id": "7656119...", "name": "player",
    "grenades_thrown": { "he": 12, "flash": 18, "smoke": 20, "molotov": 7, "decoy": 1, "total": 58 },
    "he_with_damage": 9, "he_damage_total": 213, "molotov_damage_total": 88,
    "flashes_thrown": 18, "enemies_blinded": 14, "enemy_blind_time": 23.4,
    "flash_assists": 3, "utility_damage": 301 } ] }
```

### Stats por arma (por player) — `GET /matches/{id}/stats/weapons`
```json
{ "match_id": "abc123", "players": [
  { "steam_id": "7656119...", "name": "player",
    "weapons_used": ["awp", "ak47", "deagle", "knife"],
    "overall": { "hs_pct": 0.42, "accuracy": 0.39, "damage_per_shot": 11.8, "first_shot_accuracy": 0.55 },
    "weapons": [
      { "weapon": "awp", "shots": 42, "hits": 30, "accuracy": 0.71,
        "kills": 14, "headshots": 2, "hs_pct": 0.14, "damage": 1450,
        "damage_per_shot": 34.5, "first_shot_accuracy": 0.68 },
      { "weapon": "ak47", "shots": 120, "hits": 55, "accuracy": 0.46,
        "kills": 9, "headshots": 5, "hs_pct": 0.56, "damage": 980,
        "damage_per_shot": 8.2, "first_shot_accuracy": 0.40 } ] } ] }
```
- `weapons_used` = armas com que o player deu kill ou disparou na partida.
- `shots` = `weapon_fire` daquela arma; `hits` = `player_hurt` causados por ela; `accuracy = hits / shots`; `kills`/`headshots` de `kills.parquet`; `damage` de `damages.parquet`.
- `hs_pct` (por arma) e `overall.hs_pct` (**HS% geral** do player) = headshot kills / kills.
- `damage_per_shot` = `damage / shots` (**dano por tiro**).
- `first_shot_accuracy` = acerto do **primeiro disparo de cada rajada** — heurística: agrupar `shots` em rajadas por gap de ticks e marcar o 1º como acerto se houver `player_hurt` do mesmo atacante/arma numa janela curta após o tiro. É aproximação.
- Caveat: shotgun (1 disparo = vários pellets) e granadas distorcem `accuracy` — trate como aproximação e, se quiser, marque essas armas.
- Caso do AWP: `shots` (tiros dados) e `kills` (pessoas mortas) saem direto deste payload.

### Kill matrix (confrontos) — `GET /matches/{id}/stats/matchups`
```json
{ "match_id": "abc123", "players": ["7656119A", "7656119B"],
  "matrix": [ { "attacker_steam_id": "7656119A", "victim_steam_id": "7656119B", "kills": 4 } ] }
```
Para "quantas vezes cada player morreu para quem": filtrar por `victim_steam_id` e agrupar por `attacker_steam_id`.

### Posições de morte do player — `GET /matches/{id}/stats/death-positions?player=<steam_id>`
```json
{ "match_id": "abc123", "steam_id": "7656119...", "map": "de_mirage",
  "deaths": [ { "round_number": 1, "x": 0, "y": 0, "radar_x": 0, "radar_y": 0,
               "attacker_steam_id": "7656119...", "weapon": "ak47" } ],
  "top_spot": { "x": 0, "y": 0, "radar_x": 0, "radar_y": 0, "count": 5, "cluster_radius": 128 } }
```
`top_spot` = cluster onde o player **mais morreu** na demo (maior contagem dentro de um raio).

### Sucesso por bombsite — `GET /matches/{id}/stats/bombsites`
Win rate de round por site, por time (perspectiva do ataque/T). Baseado no `bomb_site` do plant + resultado do round.
```json
{ "match_id": "abc123", "map": "de_mirage",
  "sites": [
    { "team": "Team A", "site": "A", "plants": 7, "round_wins": 6, "win_rate": 0.86, "post_plant_win_rate": 0.83 },
    { "team": "Team A", "site": "B", "plants": 3, "round_wins": 1, "win_rate": 0.33, "post_plant_win_rate": 0.33 },
    { "team": "Team B", "site": "A", "plants": 5, "round_wins": 3, "win_rate": 0.60, "post_plant_win_rate": 0.60 } ],
  "best_site_by_team": { "Team A": "A", "Team B": "A" } }
```
- `plants` = rounds em que o time foi/plantou no site (como T); `round_wins` = desses, quantos venceu; `win_rate = round_wins / plants`; `post_plant_win_rate` = vitória após o plant concretizado.
- Refinamento futuro: detectar "site executado" mesmo sem plant, via posições dos T (heurística), além do site do plant.

### Economia — `GET /matches/{id}/stats/economy` (se disponível)
Depende de `economy.parquet`. Se o parser não expuser dinheiro/equip value, retorna listas vazias.
```json
{ "match_id": "abc123",
  "rounds": [ { "round_number": 1, "t_team": "Team A", "ct_team": "Team B",
                "t_buy": "full", "ct_buy": "eco", "t_equip_value": 4200, "ct_equip_value": 800 } ],
  "by_player": [ { "steam_id": "7656119...", "avg_equip_value": 3800,
                   "eco_rounds": 3, "force_rounds": 2, "full_rounds": 7 } ] }
```

### Maps — `GET /maps/{map_name}/metadata`
```json
{ "map": "de_mirage", "pos_x": -3230, "pos_y": 1713, "scale": 5.0,
  "image_width": 1024, "image_height": 1024, "levels": null }
```

## 5. Conversão de coordenadas (mundo → radar)

**Onde acontece:** o **backend** converte e já entrega `radar_x/radar_y` nos payloads de replay e heatmap (módulo `backend/app/analytics/map_projection.py`). O frontend recebe coordenadas de radar prontas. O `frontend/lib/mapProjection.ts` existe para **desenho client-side** (playbook) usando a mesma fórmula.

```ts
type RadarMetadata = { pos_x: number; pos_y: number; scale: number; image_width: number; image_height: number };
function worldToRadar(x: number, y: number, m: RadarMetadata) {
  return { radarX: (x - m.pos_x) / m.scale, radarY: (m.pos_y - y) / m.scale };
}
```
Validar com metadados reais; mapas multi-nível (Nuke, Vertigo) podem exigir ajuste por nível.
