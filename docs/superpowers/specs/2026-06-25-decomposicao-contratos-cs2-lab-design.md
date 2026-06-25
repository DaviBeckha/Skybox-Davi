# Design — Decomposição do `contract.md` em 16 contratos (cs2-lab)

**Data:** 2026-06-25
**Status:** Aprovado para implementação
**Autor:** brainstorming colaborativo

---

## 1. Contexto e objetivo

O repositório contém um único arquivo `contract.md`: um **prompt mestre** que descreve, de ponta a ponta, a construção da plataforma local `cs2-lab` (análise de demos de Counter-Strike 2 — backend Python/FastAPI + frontend Next.js). O repositório está, fora isso, vazio (apenas `.git`). Nada foi implementado ainda.

O `contract.md` é grande demais para ser executado de uma vez por um agente de IA. O objetivo deste trabalho é **decompô-lo em vários contratos menores**, cada um representando uma tarefa pequena, focada e auto-contida.

O `contract.md` original **permanece** como fonte mestre; os contratos derivados são gerados a partir dele.

## 2. Decisões de design (travadas no brainstorming)

1. **Granularidade — 1 contrato por Etapa (1–16).** O `contract.md` já define 16 etapas de execução na seção 12 ("Etapas de Execução"). Cada etapa vira um contrato. É o eixo mais limpo e incremental, pois segue a ordem de execução já pensada.
2. **Consumo — prompt auto-contido para agente de IA.** Cada contrato será colado como prompt em um agente (Codex/Claude/etc.) que pode **não** ter o `contract.md` em contexto. Portanto cada arquivo precisa ser independente.
3. **Contexto global — preamble curto + foco.** Cada contrato começa com um bloco curto e padronizado de contexto (o que é o `cs2-lab`, papel do agente, regra anti-cheat, stack relevante àquela etapa, onde os arquivos vivem) e depois foca na tarefa específica. Equilíbrio entre auto-contido e enxuto; evita a redundância extensa de repetir todo o contexto em cada arquivo.
4. **Idioma e tom.** Português pt-br, mantendo o tom imperativo/objetivo do `contract.md` original.

## 3. Estrutura de saída

Criar uma pasta `contracts/` na raiz do repositório:

```
contracts/
  00-indice.md            ← ordem, mapa de dependências, status sugerido
  01-auditoria.md
  02-estrutura.md
  03-documentacao-base.md
  04-backend-minimo.md
  05-importacao-demos.md
  06-jobs-parsing.md
  07-parsing-real.md
  08-api-analytics.md
  09-frontend-base.md
  10-dashboard.md
  11-demos-ui.md
  12-match-report.md
  13-replay-2d.md
  14-heatmaps.md
  15-playbook.md
  16-qa.md
```

Convenção de nome: `NN-slug.md` (dois dígitos para ordenar). O `00-indice.md` dá a visão de ordem e dependências.

## 4. Template de cada contrato (9 seções)

Cada arquivo `NN-*.md` segue o mesmo esqueleto:

1. **Título + ID** — ex.: `Contrato 04 — Backend Mínimo`.
2. **Preamble curto (padronizado)** — 1 parágrafo contendo:
   - o que é o `cs2-lab` (plataforma local de análise de demos CS2, uso pessoal/offline);
   - papel do agente (engenheiro full-stack / especialista na área daquela etapa);
   - **regra anti-cheat** em 1 linha: nada de leitura de memória, DMA, injeção, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos gravadas;
   - **stack relevante somente àquela etapa** (não a stack inteira);
   - onde os arquivos vivem (paths relevantes da árvore do projeto).
3. **Pré-requisitos / dependências** — quais contratos precisam estar prontos antes e em que estado o repo deve estar.
4. **Objetivo** — uma frase do resultado esperado.
5. **Escopo (o que fazer)** — passos concretos derivados da Etapa correspondente.
6. **Fora de escopo** — o que NÃO tocar nesta etapa (impede o agente de avançar além da fatia).
7. **Entregáveis** — paths/arquivos concretos esperados ao final.
8. **Critérios de aceite** — checklist verificável.
9. **Comandos de validação** — quando aplicável (`pytest`, `uvicorn ...`, `npm run lint`, `npm run build`, etc.).

## 5. Mapa dos 16 contratos e dependências

| #  | Contrato                        | Etapa-fonte | Depende de   |
|----|---------------------------------|-------------|--------------|
| 01 | Auditoria do repositório        | Etapa 1     | —            |
| 02 | Estrutura base (pastas + raiz)  | Etapa 2     | 01           |
| 03 | Documentação base               | Etapa 3     | 02           |
| 04 | Backend mínimo                  | Etapa 4     | 02           |
| 05 | Importação de demos             | Etapa 5     | 04           |
| 06 | Jobs de parsing                 | Etapa 6     | 05           |
| 07 | Parsing real                    | Etapa 7     | 06           |
| 08 | API de Analytics                | Etapa 8     | 07           |
| 09 | Frontend base                   | Etapa 9     | 04           |
| 10 | Dashboard                       | Etapa 10    | 08, 09       |
| 11 | Demos UI                        | Etapa 11    | 05, 09       |
| 12 | Match Report                    | Etapa 12    | 08, 09       |
| 13 | Replay 2D                       | Etapa 13    | 08, 09       |
| 14 | Heatmaps                        | Etapa 14    | 08, 09       |
| 15 | Playbook privado                | Etapa 15    | 09           |
| 16 | QA                              | Etapa 16    | todos        |

### Detalhamento por contrato (escopo central)

- **01 — Auditoria:** auditar diretório atual (arquivos, estrutura, dependências, se já existe front/back, conflitos com a estrutura proposta). Entregável: relato de auditoria (sem criar código ainda).
- **02 — Estrutura:** criar a árvore base (`backend/`, `frontend/`, `data/`, `docs/`, `AGENTS.md`, `README.md`, `docker-compose.yml`) com placeholders mínimos.
- **03 — Documentação base:** `AGENTS.md` (comandos back/front, padrões, convenções de diretório, como rodar testes/lint, definição de pronto), `docs/research.md` (pesquisa técnica da stack) e `docs/architecture.md`.
- **04 — Backend mínimo:** app FastAPI, `/health`, `core/config.py`, `core/paths.py`, SQLite inicial, modelos Pydantic, estrutura de rotas, teste do healthcheck.
- **05 — Importação de demos:** `POST /demos/import` (upload local, validação `.dem`, cópia para `data/raw_demos`, registro no SQLite com status `pending`), `GET /demos`, `GET /demos/{demo_id}`.
- **06 — Jobs de parsing:** worker (RQ+Redis), transições de status `pending → parsing → parsed/failed`, logging de erro, **mock fallback** quando o parser real não estiver disponível.
- **07 — Parsing real:** parsing em camadas com `awpy` (primeira opção) e `demoparser2` (tick-level quando necessário); extrair metadata/players/rounds/kills/damages/bomb events/posições/replay frames; salvar metadados em SQLite, dados analíticos em Parquet, views/queries em DuckDB.
- **08 — API de Analytics:** endpoints de matches, summary, rounds, players, stats (player/economy/weapons), replay (`?round=&sample_rate=`), heatmap (`?type=`), maps (`/maps`, `/maps/{name}/radar`, `/maps/{name}/metadata`).
- **09 — Frontend base:** app Next.js + TypeScript, estrutura de rotas, layout principal, navegação, tema escuro, `lib/api.ts`, `lib/types.ts` (tipos compartilhados), TanStack Query.
- **10 — Dashboard:** cards (total de demos, partidas, mapas, jogadores), últimos jobs/demos, atalhos para matches/replay/heatmaps.
- **11 — Demos UI:** upload de demo, lista, status de parsing, data, nome do arquivo, botão "abrir relatório", mensagem de erro em falha.
- **12 — Match Report:** placar, mapa, times, rounds, tabela de jogadores (KD, ADR, KAST-like, entry, trade, clutch, por arma), gráficos simples.
- **13 — Replay 2D:** canvas React-Konva, radar como fundo, jogadores como círculos (cor por lado, nome, yaw, vida, arma), bomba/eventos, timeline com eventos, seleção de round, play/pause, velocidades (0.25x–4x), interpolação simples entre frames. **Inclui o módulo de conversão de coordenadas** `frontend/lib/mapProjection.ts` e `backend/app/analytics/map_projection.py` (função `worldToRadar`), validado contra metadata real de radar.
- **14 — Heatmaps:** tipos kills/deaths/pathing/utility, filtros (player, team, side, round range, weapon). Reutiliza o `mapProjection` do contrato 13.
- **15 — Playbook privado:** CRUD local de táticas (nome, mapa, lado, descrição, tags, rounds de referência, desenho de pontos/linhas no mapa), persistência em SQLite ou JSON local.
- **16 — QA:** rodar `pytest` (backend) e `npm run lint` + `npm run build` (frontend), validar fluxo mínimo com dados mockados, corrigir erros críticos.

### Observações de dependência

- O **frontend base (09)** depende apenas do **backend mínimo (04)**, não do parsing real — pode evoluir em paralelo usando dados mockados.
- O módulo de **conversão de coordenadas** (`mapProjection`) entra dentro do **Contrato 13 (Replay 2D)**, que é onde ele é primeiro usado, e é referenciado pelo **14 (Heatmaps)**.
- O **Contrato 16 (QA)** depende de todos, sendo o portão final de aceite do MVP.

## 6. Conteúdo do `00-indice.md`

O índice deve conter:
- breve descrição do propósito da pasta `contracts/`;
- a tabela de ordem + dependências (seção 5 acima);
- instrução de uso: "cole um contrato por vez no agente, na ordem; cada um é auto-contido";
- coluna/marcação de status sugerida (ex.: `[ ]` pendente / `[x]` concluído) para acompanhamento.

## 7. Fora de escopo deste trabalho

- **Não** implementar nenhuma etapa do `cs2-lab` em si (não escrever backend/frontend). Este trabalho gera **apenas os contratos** (arquivos markdown).
- **Não** alterar o `contract.md` original.
- **Não** adicionar etapas novas além das 16 já presentes no `contract.md` (sem inventar escopo).

## 8. Critérios de aceite deste trabalho

- Pasta `contracts/` criada com os 17 arquivos (`00-indice.md` + `01`–`16`).
- Cada contrato segue o template de 9 seções da seção 4.
- Cada contrato é auto-contido (preamble curto presente, com a regra anti-cheat).
- O `00-indice.md` reflete corretamente a ordem e as dependências da seção 5.
- Conteúdo fiel ao `contract.md` (sem inventar requisitos nem omitir os principais de cada etapa).
- Tudo em português pt-br.

## 9. Revisão pós-feedback (2026-06-25)

Após a geração inicial, os contratos foram reformatados como **16 phases sequenciais** (execução phase-por-phase com a IA) e revisados para execução autônoma pelo Opus 4.8. Mudanças aplicadas:

- **Override de banco:** **PostgreSQL** substitui o SQLite como banco relacional de metadados (via SQLAlchemy + Alembic). Parquet + DuckDB permanecem como camada analítica. `docker-compose` sobe PostgreSQL + Redis.
- **Contrato de dados:** novo arquivo normativo `contracts/_shared/data-contract.md` com schema canônico (tabelas PostgreSQL, tabelas Parquet, views DuckDB, payloads de replay/heatmap/maps, conversão de coordenadas). Resolve a divergência de schema entre quem grava (Phase 07) e quem lê (Phase 08), e exige que o mock produza o mesmo schema do real.
- **Protocolo de execução + Convenções técnicas:** adicionados ao `00-indice.md` e referenciados por cada phase (bloco "Antes de começar"): ler antes, validar antes de concluir, commit atômico, atualizar índice, tratar ambiguidade sem expandir escopo; tooling fixado (`uv`, Node 20, `npm`).
- **Assets de mapa + conversão radar:** aquisição dos radar images/metadata e o módulo `map_projection.py` foram alocados na **Phase 08** (backend já entrega `radar_x/radar_y`); o `mapProjection.ts` (Phase 13) passa a ser apenas para desenho client-side. Resolve o conflito de ordem entre Phases 08 e 13.
- **Ajustes finos:** Phase 01 grava `docs/audit.md`; semântica de `sample_rate` definida (1 frame a cada N ticks); consistência mock↔real explicitada.

### Analytics de utility/duelo (cobertura completa — pedido do usuário)

Para suportar análises de granadas, flashes, confrontos e movimento por player:
- **Contrato de dados:** novas tabelas `grenades.parquet` (lançamentos/detonações por tipo) e `blinds.parquet` (cegueiras por flash: flasher, vítima, `is_enemy`, duração); novos payloads `stats/utility`, `stats/matchups` (kill matrix) e `stats/death-positions` (com `top_spot`); `heatmap` ganha `type=grenades` e filtro `grenade_type`.
- **Phase 07:** captura os eventos de granada/flash (senão o dado se perde no parse).
- **Phase 08:** endpoints `stats/utility`, `stats/matchups`, `stats/death-positions`; métricas de granadas por tipo, HE com dano, dano HE/molotov, flashes que cegaram inimigos, flash assists.
- **Phase 12:** tabela de utility + kill matrix no match report.
- **Phase 13:** timeline do replay marca granadas/flashes (`type=grenade` + `grenade_type`); render opcional da utility no canvas.
- **Phase 14:** heatmap de movimento por player, posição de morte #1 (`top_spot`) e heatmap de granadas.
- **Phase 06:** mock fallback inclui `grenades`/`blinds` para que utility/kill matrix funcionem com mock.
- **Sucesso por bombsite:** `rounds.parquet` ganha `bomb_site`/`t_team`/`ct_team` (Phase 07); endpoint `stats/bombsites` (Phase 08) com win rate de round por site/time; exibido no Match Report (Phase 12). Métrica baseada no site do plant — detecção de "site executado" por posições fica como refinamento futuro.
- **Armas/disparos por player:** nova tabela `shots.parquet` (evento `weapon_fire`, Phase 07); `stats/weapons` (Phase 08) com armas usadas, disparos, accuracy, kills e HS% por arma, mais **HS% geral**, **dano por tiro** (`damage/shots`) e **first-shot accuracy** (1º disparo de cada rajada — heurística); exibido no Match Report (Phase 12). `accuracy = hits/shots` (aproximação; shotgun/granadas distorcem).

### Revisão de coerência (2026-06-25)

Auditoria completa dos 18 arquivos. Correções aplicadas:
- **Coordenadas radar:** deixam de ser armazenadas no Parquet (`grenades`/`replay_frames`); o backend adiciona `radar_x/radar_y` nos payloads na Phase 08. Resolve a contradição de ordem (assets de mapa só chegam na Phase 08).
- **`stats/economy`:** ganha respaldo de dados com a tabela `economy.parquet` (per player/round, best-effort "se disponível") — o endpoint não fica mais sem fonte.
- **DuckDB:** lista de views completada (`shots`, `grenades`, `blinds`, `economy`).
- **Phase 14:** corrige a contagem de tipos de heatmap (5, não 4).
