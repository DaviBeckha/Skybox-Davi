# cs2-lab — Execução em 16 Phases

Esta pasta contém o `contract.md` (prompt mestre) **decomposto em 16 phases sequenciais**. A ideia é executar com a IA **uma phase por vez**: a IA recebe a phase atual, conclui, marca como pronta e **avança para a próxima**.

Cada phase é **auto-contida** — pode ser colada como prompt mesmo sem o `contract.md` em contexto — e termina com uma seção **"Conclusão da phase"** apontando para a próxima.

## Como executar

1. Comece pela **Phase 01** e siga a ordem numérica, respeitando as dependências.
2. Cole **uma phase por vez** no agente. Antes de implementar, o agente deve ler este índice (Protocolo + Convenções), o [contrato de dados](_shared/data-contract.md) e a saída da phase anterior.
3. A IA executa o escopo, valida os critérios de aceite e só então avança.

## Protocolo de execução (vale para TODAS as phases)

1. **Leia antes de começar:** `AGENTS.md`, `docs/architecture.md`, o [contrato de dados](_shared/data-contract.md) e o que a **phase anterior** entregou (código/diff). Não comece sem entender o estado atual.
2. **Siga o contrato de dados à risca.** Nomes de coluna, tipos e payloads são normativos — quem grava e quem lê precisam casar exatamente.
3. **Implemente apenas o escopo da phase.** Respeite a seção "Fora de escopo"; não invente requisitos nem antecipe phases futuras.
4. **Valide antes de declarar pronto.** Rode os "Comandos de validação" e confirme que passam — evidência antes de afirmação.
5. **Commit atômico** ao final da phase, com mensagem clara (ex.: `feat(phase-04): backend minimo`), e **marque a phase neste índice**.
6. **Ambiguidade:** assuma a opção mais simples e razoável, **documente** a decisão (comentário/README) e siga — não pare nem expanda escopo.
7. A **regra inviolável anti-cheat** (abaixo) vale sempre.

## Convenções técnicas (vale para TODAS as phases)

- **Backend:** Python 3.11+, gerenciado com `uv` (`pyproject.toml`). Type hints obrigatórios, modelos Pydantic.
- **Banco relacional:** **PostgreSQL** (metadados), via SQLAlchemy + Alembic. Conexão por `DATABASE_URL`. *(Override do `contract.md`, que sugeria SQLite.)*
- **Camada analítica:** Parquet (armazenamento colunar) + DuckDB (consultas locais).
- **Fila de jobs:** RQ + Redis.
- **Frontend:** Node 20 LTS, gerenciador `npm`, Next.js + TypeScript, TanStack Query.
- **Infra local:** `docker-compose` sobe **PostgreSQL + Redis**.
- **Nomenclatura:** `snake_case` no backend/dados, `camelCase` no frontend; `steam_id` (steamID64) como string; `side` ∈ {`CT`, `T`}; ids `uuid` v4.

## Phases e dependências

| #  | Phase                                | Depende de | Status |
|----|--------------------------------------|------------|--------|
| 01 | [Auditoria do repositório](01-auditoria.md) | —          | [x]    |
| 02 | [Estrutura base](02-estrutura.md)           | 01         | [x]    |
| 03 | [Documentação base](03-documentacao-base.md) | 02        | [x]    |
| 04 | [Backend mínimo](04-backend-minimo.md)      | 02         | [x]    |
| 05 | [Importação de demos](05-importacao-demos.md) | 04       | [x]    |
| 06 | [Jobs de parsing](06-jobs-parsing.md)       | 05         | [x]    |
| 07 | [Parsing real](07-parsing-real.md)          | 06         | [x]    |
| 08 | [API de Analytics](08-api-analytics.md)     | 07         | [x]    |
| 09 | [Frontend base](09-frontend-base.md)        | 04         | [ ]    |
| 10 | [Dashboard](10-dashboard.md)                | 08, 09     | [ ]    |
| 11 | [Demos UI](11-demos-ui.md)                  | 05, 09     | [ ]    |
| 12 | [Match Report](12-match-report.md)          | 08, 09     | [ ]    |
| 13 | [Replay 2D](13-replay-2d.md)                | 08, 09     | [ ]    |
| 14 | [Heatmaps](14-heatmaps.md)                  | 08, 09     | [ ]    |
| 15 | [Playbook privado](15-playbook.md)          | 09         | [ ]    |
| 16 | [QA — aceite do MVP](16-qa.md)              | todos      | [ ]    |

## Notas de dependência

- A **Phase 09 (Frontend base)** depende apenas da **Phase 04 (Backend mínimo)** — pode evoluir em paralelo ao parsing usando dados mockados (no schema do contrato de dados).
- A **conversão mundo→radar** acontece no **backend** (módulo `map_projection.py`, entregue na Phase 08): replay e heatmap já chegam com `radar_x/radar_y`. O `mapProjection.ts` do frontend (Phase 13) serve para desenho client-side (playbook).
- Os **assets de mapa** (radar images + metadata) são obtidos e posicionados em `data/maps/` na **Phase 08**, e consumidos por 13/14.
- **Analytics de utility/duelo** (granadas, flashes, kill matrix, posição de morte por player) é capturado na **Phase 07** (tabelas `grenades`/`blinds`), exposto na **Phase 08** (`stats/utility`, `stats/matchups`, `stats/death-positions`) e exibido nas **Phases 12, 13 e 14**.
- **Sucesso por bombsite** (win rate de round por site) usa `rounds.bomb_site` + resultado do round (**Phase 07**), é exposto em `stats/bombsites` (**Phase 08**) e mostrado no Match Report (**Phase 12**).
- **Armas/disparos por player** (disparos, accuracy, kills por arma) vêm de `shots` (`weapon_fire`) + `kills`/`damages` (**Phase 07**), expostos em `stats/weapons` (**Phase 08**) e no Match Report (**Phase 12**).
- A **Phase 16 (QA)** é o portão final de aceite do MVP e depende de todas as anteriores.

## Regra inviolável (vale para todas as phases)

O cs2-lab é uma plataforma local de **analytics e revisão de demos gravadas**. Nenhuma phase deve implementar leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo competitivo, automação de gameplay, triggerbot, aimbot ou qualquer vantagem competitiva em tempo real.
