# Checklist de Execução — cs2-lab (16 Phases)

> Rastreamento do progresso de execução dos contratos. Marque cada critério de aceite (`[x]`) ao concluí-lo e atualize o **Status** da phase no quadro abaixo e em [`00-indice.md`](00-indice.md).
>
> Legenda de status: `[ ]` pendente · `[~]` em andamento · `[x]` concluída.

## Quadro de progresso

| #  | Phase | Depende de | Status |
|----|-------|------------|--------|
| 01 | Auditoria do repositório | — | [x] |
| 02 | Estrutura base | 01 | [x] |
| 03 | Documentação base | 02 | [x] |
| 04 | Backend mínimo | 02 | [x] |
| 05 | Importação de demos | 04 | [x] |
| 06 | Jobs de parsing | 05 | [x] |
| 07 | Parsing real | 06 | [x] |
| 08 | API de Analytics | 07 | [x] |
| 09 | Frontend base | 04 | [x] |
| 10 | Dashboard | 08, 09 | [x] |
| 11 | Demos UI | 05, 09 | [x] |
| 12 | Match Report | 08, 09 | [x] |
| 13 | Replay 2D | 08, 09 | [x] |
| 14 | Heatmaps | 08, 09 | [x] |
| 15 | Playbook privado | 09 | [ ] |
| 16 | QA — aceite do MVP | todos | [ ] |

---

## Phase 01 — Auditoria do repositório ✅

- [x] `docs/audit.md` existe e lista os arquivos/pastas relevantes existentes.
- [x] Relatório indica claramente se há backend/frontend pré-existentes.
- [x] Relatório aponta conflitos (ou confirma que não há) com a estrutura-alvo.
- [x] Nenhum arquivo de código foi criado ou modificado.

## Phase 02 — Estrutura base ✅

- [x] Todas as pastas da árvore-alvo existem.
- [x] Pastas vazias têm `.gitkeep` (ou equivalente) para serem versionadas.
- [x] `.gitignore` cobre artefatos de Python, Node e dados pesados.
- [x] Nenhuma lógica de aplicação foi adicionada.

## Phase 03 — Documentação base ✅

- [x] `AGENTS.md` cobre comandos back/front (incluindo docker compose e Alembic), padrões, convenções, testes/lint e definição de pronto.
- [x] `docs/research.md` cobre todas as tecnologias listadas (incluindo PostgreSQL) e o tema de assets de mapa com fontes.
- [x] `docs/architecture.md` descreve fluxo de dados e armazenamento e referencia o contrato de dados.
- [x] Documentação coerente com as Convenções técnicas do índice.

## Phase 04 — Backend mínimo ✅

- [x] `docker compose up -d postgres` sobe o banco; `alembic upgrade head` cria as tabelas. *(host 5544 → container 5432; 5432/5433 ocupadas por Postgres local)*
- [x] `uvicorn app.main:app --reload` sobe sem erros e conecta ao PostgreSQL.
- [x] `GET /health` retorna `{ "status": "ok" }`.
- [x] Tabelas `demos/matches/players/rounds` batem com o contrato de dados.
- [x] `pytest` passa o teste do healthcheck.

## Phase 05 — Importação de demos ✅

- [x] Upload de um `.dem` cria registro com status `pending` e copia o arquivo para `data/raw_demos/`.
- [x] Upload de arquivo não-`.dem` é rejeitado com erro claro (400).
- [x] `GET /demos` lista a demo importada.
- [x] `GET /demos/{demo_id}` retorna a demo correta (e 404 quando não existe).
- [x] Campos persistidos batem com o contrato de dados.

## Phase 06 — Jobs de parsing ✅

- [x] Importar uma demo enfileira um job e a demo passa por `pending → parsing → parsed`.
- [x] Em caso de erro, a demo vai para `failed` com erro logado e gravado em `demos.error`.
- [x] A API responde normalmente enquanto o parsing roda (não bloqueia).
- [x] Com o parser real ausente, o mock fallback conclui o job como `parsed` produzindo dados no schema do contrato.
- [x] Worker RQ documentado (como iniciar): `uv run python -m app.workers.run_worker`.

## Phase 07 — Parsing real

- [x] Uma demo real (ou fixture) é parseada e gera os Parquet particionados por `match_id` com as colunas do contrato.
- [x] As tabelas `grenades` e `blinds` são geradas com os eventos de granada/flash (não ficam vazias quando há utility na demo).
- [x] `rounds.parquet` traz `bomb_site`, `t_team` e `ct_team` nos rounds com plant.
- [x] `shots.parquet` é gerado (1 linha por disparo) e permite contar tiros por arma por player.
- [x] Metadados (match/players/rounds) gravados no PostgreSQL.
- [x] DuckDB consegue consultar os dados processados via views.
- [x] Schema do parsing real == schema do mock fallback.
- [x] Tratamento de erro para demo inválida (status `failed`).

## Phase 08 — API de Analytics

- [x] `GET /matches` lista as partidas processadas.
- [x] `GET /matches/{id}/summary`, `/rounds`, `/players` retornam dados coerentes.
- [x] `GET /matches/{id}/stats/player` retorna as métricas mínimas.
- [x] `GET /matches/{id}/stats/utility` retorna granadas por tipo, HE/molly dano, flashes que cegaram inimigos e flash assists por player.
- [x] `GET /matches/{id}/stats/matchups` retorna a kill matrix (quem matou quem, quantas vezes).
- [x] `GET /matches/{id}/stats/death-positions?player=<id>` retorna as mortes do player e o `top_spot`.
- [x] `GET /matches/{id}/stats/bombsites` retorna plants, round wins e win rate por bombsite/time.
- [x] `GET /matches/{id}/stats/weapons` retorna, por player e por arma, disparos, accuracy, kills e armas usadas, mais HS% geral, dano por tiro e first-shot accuracy.
- [x] `GET /matches/{id}/replay?round=N&sample_rate=S` retorna frames com `radar_x/radar_y` no formato do contrato.
- [x] `GET /matches/{id}/heatmap?type=kills|deaths|path|utility|grenades` responde para cada tipo (incluindo `path&player=<id>` para movimento), com pontos convertidos.
- [x] `GET /maps`, `/maps/{name}/radar`, `/maps/{name}/metadata` respondem (imagem + metadata reais).

## Phase 09 — Frontend base ✅

- [x] `npm run dev` sobe o frontend e abre no navegador.
- [x] Navegação entre as áreas principais funciona (mesmo com telas placeholder).
- [x] Tema escuro aplicado.
- [x] `lib/api.ts` consegue chamar o backend local (ex.: `/health` ou `/demos`).
- [x] Tipos em `lib/types.ts` correspondem ao contrato de dados.
- [x] `npm run lint` e `npm run build` passam.

## Phase 10 — Dashboard ✅

- [x] Cards exibem os totais corretos (a partir da API ou de mock).
- [x] Últimos jobs e últimas demos aparecem com status.
- [x] Atalhos navegam para as áreas corretas.
- [x] Estados de loading e erro tratados.
- [x] `npm run lint` e `npm run build` passam.

## Phase 11 — Demos UI ✅

- [x] É possível importar um `.dem` pela UI e ele aparece na lista.
- [x] Status de parsing é exibido e atualiza conforme evolui (polling via TanStack Query).
- [x] Botão "abrir relatório" disponível quando a demo está `parsed`.
- [x] Erro de parsing é exibido de forma clara.
- [x] `npm run lint` e `npm run build` passam.

## Phase 12 — Match Report ✅

- [x] Placar, mapa, times e rounds exibidos corretamente.
- [x] Tabela de jogadores mostra KD, ADR, KAST-like, entry/trade/clutch (armas em seção própria).
- [x] Tabela de utility mostra granadas por tipo, HE/molly dano, flashes que cegaram e flash assists.
- [x] Kill matrix mostra quantas vezes cada player morreu para cada adversário.
- [x] Sucesso por bombsite mostra a win rate de round por site/time (A vs B) com gráfico.
- [x] Tabela de armas por player mostra armas usadas, disparos, accuracy e kills por arma.
- [x] Pelo menos um gráfico simples renderiza (barras CSS, sem dependência extra).
- [x] Estados de loading/erro tratados.
- [x] `npm run lint` e `npm run build` passam.

## Phase 13 — Replay 2D ✅

- [x] O replay mostra o radar do mapa e os jogadores se movendo.
- [x] Cores por lado, yaw (ponteiro), vida e arma (roster) exibidos.
- [x] Timeline marca eventos: kills, bomb events e granadas/flashes (por `grenade_type`).
- [x] Seleção de round, play/pause e velocidades (0.25x–4x) funcionam.
- [x] Jogadores aparecem na posição correta sobre o radar (usando `radar_x/radar_y`).
- [x] `npm run lint` e `npm run build` passam. *(overlay DOM em vez de React-Konva, p/ evitar peer-deps React 19/SSR)*

## Phase 14 — Heatmaps ✅

- [x] É possível ver ao menos um heatmap básico (ex.: kills) sobre o radar.
- [x] Os tipos (kills/deaths/pathing/utility/grenades) são selecionáveis.
- [x] Mapa de movimento de um player (`path` + filtro player) renderiza.
- [x] Posição de morte do player mostra todas as mortes e destaca o `top_spot`.
- [x] Filtros básicos (player/team/side/round range/grenade type) afetam o resultado.
- [x] Pontos posicionados corretamente via `radar_x/radar_y`.
- [x] `npm run lint` e `npm run build` passam.

## Phase 15 — Playbook privado

- [ ] É possível criar, editar e excluir uma tática.
- [ ] Tática pode ser associada a mapa e lado, com descrição/tags/rounds.
- [ ] Desenho de pontos e linhas no mapa funciona e é salvo em `drawing`.
- [ ] Táticas persistem no PostgreSQL entre sessões.
- [ ] `npm run lint` e `npm run build` passam; `pytest` cobre o CRUD.

## Phase 16 — QA — aceite do MVP

- [ ] Backend sobe localmente (com PostgreSQL + Redis via docker-compose).
- [ ] Frontend sobe localmente e abre no navegador.
- [ ] É possível importar uma demo ou usar fixture mock; a demo aparece na lista com status correto.
- [ ] É possível abrir uma partida e ver o relatório básico.
- [ ] É possível abrir o replay 2D e ver mapa + jogadores se movendo.
- [ ] É possível ver pelo menos um heatmap básico, incluindo o mapa de movimento de um player.
- [ ] Stats de utility (granadas/flashes), kill matrix e posição de morte (`top_spot`) do player aparecem.
- [ ] Sucesso por bombsite (win rate de round por site) aparece no relatório.
- [ ] Stats por arma por player (disparos, accuracy, kills) aparecem.
- [ ] Código organizado; há `README.md`, `AGENTS.md` e testes mínimos.
- [ ] Nada depende de serviço externo obrigatório além do PostgreSQL/Redis locais (containerizados).
- [ ] Nenhum recurso de cheat, leitura de memória, injeção, DMA ou vantagem competitiva ao vivo foi implementado.
- [ ] Todos os itens do checklist global do MVP acima marcados.
- [ ] `pytest` passa.
- [ ] `npm run lint` e `npm run build` passam.
- [ ] Resumo final (Definição de Pronto) entregue.
