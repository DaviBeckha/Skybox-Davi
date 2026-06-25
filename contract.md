# CS2 Lab — Prompt Mestre para Codex com GPT-5.5

Você é meu agente principal de engenharia para criar uma plataforma local de análise de demos de Counter-Strike 2, inspirada em plataformas como Skybox EDGE, mas com marca, UI, código e arquitetura próprios.

Use **GPT-5.5**, **reasoning high** e recursos avançados de agente. Trabalhe como:

* Arquiteto de software
* Tech lead
* Full-stack engineer
* Especialista em dados
* Especialista em análise de demos CS2
* Especialista em produto analytics

Antes de codar, faça uma pesquisa técnica atualizada nas documentações oficiais, repositórios primários e exemplos reais das tecnologias citadas neste documento.

---

# 1. Objetivo do Produto

Criar um MVP local chamado **`cs2-lab`**, com backend em Python e frontend em Next.js, para importar demos `.dem` de CS2, processar estatísticas, gerar replay 2D, heatmaps, relatórios de partida e uma base inicial para pattern finder/playbook privado.

A plataforma será usada localmente e de forma pessoal.

## Escopo permitido

O sistema deve trabalhar com:

* Demos `.dem`
* Arquivos locais
* Dados derivados de partidas já gravadas
* Estatísticas pós-jogo
* Replay 2D offline
* Heatmaps offline
* Playbook privado
* Análise de padrões em demos

## Fora de escopo

Não implemente:

* Leitura de memória do jogo
* DMA
* Injeção de código
* Wallhack
* Radar ao vivo competitivo
* Automação de gameplay
* Triggerbot
* Aimbot
* Qualquer recurso que interfira no CS2 em execução
* Qualquer vantagem competitiva em tempo real

O produto deve ser uma plataforma local de analytics e revisão de demos.

---

# 2. Pesquisa Técnica Inicial Obrigatória

Antes de implementar, pesquise e documente em `docs/research.md`:

## Backend

* Python 3.11+
* FastAPI
* Pydantic
* awpy
* demoparser2
* Polars
* DuckDB
* Parquet
* SQLite
* RQ + Redis
* Celery, apenas como comparação

## Frontend

* Next.js
* TypeScript
* React
* React-Konva
* PixiJS, apenas como alternativa futura
* Recharts ou biblioteca equivalente
* TanStack Query

## Assets de mapa

Pesquisar fontes para:

* Radar images dos mapas de CS2
* Overview metadata
* `pos_x`
* `pos_y`
* `scale`
* Conversão de coordenadas do mundo para coordenadas do radar
* Tratamento básico para mapas com múltiplos níveis, como Nuke e Vertigo

---

# 3. Stack Recomendada

## 3.1 Backend

Use:

* **Python 3.11+**
* **FastAPI**
* **Pydantic**
* **awpy**
* **demoparser2**
* **Polars**
* **DuckDB**
* **Parquet**
* **SQLite**
* **RQ + Redis**

### Justificativa

Python é a melhor escolha para o backend porque já existem bibliotecas maduras ou em crescimento para parsing e análise de demos CS2.

Use:

* `awpy` para analytics, parsing de alto nível e visualizações
* `demoparser2` para extração mais granular e tick-level quando necessário
* `Polars` para processamento rápido de dados
* `DuckDB` para consultas analíticas locais
* `Parquet` para armazenamento eficiente dos dados processados
* `SQLite` para metadados simples do MVP
* `FastAPI` para expor a API local

---

## 3.2 Frontend

Use:

* **Next.js**
* **TypeScript**
* **React**
* **React-Konva**
* **TanStack Query**
* **Recharts**
* **CSS Modules, Tailwind ou alternativa simples**

### Justificativa

Next.js com TypeScript permite criar uma aplicação moderna e organizada. React-Konva é adequado para o MVP do replay 2D porque permite renderizar mapa, jogadores, eventos, linhas e timeline usando canvas com uma API declarativa em React.

Se o replay 2D ficar pesado futuramente, considere migrar o canvas para PixiJS.

---

# 4. Arquitetura Sugerida

Estrutura esperada do projeto:

```txt
cs2-lab/
  backend/
    app/
      main.py
      api/
        routes_demos.py
        routes_matches.py
        routes_replay.py
        routes_stats.py
        routes_maps.py
      core/
        config.py
        paths.py
      parsers/
        parse_with_awpy.py
        parse_with_demoparser2.py
      analytics/
        player_stats.py
        economy.py
        utility.py
        heatmaps.py
        replay_frames.py
        pattern_finder.py
      storage/
        duckdb.py
        parquet.py
        sqlite.py
      workers/
        jobs.py
      tests/
    pyproject.toml

  frontend/
    app/
      page.tsx
      demos/
      matches/[id]/
      replay/[matchId]/
      analytics/
      playbook/
    components/
      Replay2D/
      Heatmap/
      MatchReport/
      UploadDemo/
      Filters/
    lib/
      api.ts
      types.ts
      mapProjection.ts
    package.json

  data/
    raw_demos/
    processed/
      parquet/
      duckdb/
    maps/
      radars/
      radar_info/

  docs/
    research.md
    architecture.md

  docker-compose.yml
  AGENTS.md
  README.md
```

---

# 5. Uso de Subagents

Use subagents ou frentes paralelas sempre que possível.

## 5.1 Research Agent

Responsável por:

* Verificar awpy
* Verificar demoparser2
* Verificar FastAPI
* Verificar DuckDB
* Verificar Polars
* Verificar Next.js
* Verificar React-Konva
* Verificar PixiJS
* Verificar assets de mapas CS2
* Entregar uma decisão objetiva de stack
* Identificar riscos técnicos de parsing CS2

Resultado esperado:

```txt
docs/research.md
```

---

## 5.2 Backend Agent

Responsável por:

* Criar backend FastAPI
* Implementar upload/import de demo
* Implementar job de parsing
* Criar schema de armazenamento
* Criar endpoints de demos
* Criar endpoints de matches
* Criar endpoints de rounds
* Criar endpoints de players
* Criar endpoints de stats
* Criar endpoints de replay frames
* Criar endpoints de heatmaps

Resultado esperado:

```txt
backend/
```

---

## 5.3 Data/Analytics Agent

Responsável por:

* Definir modelo de dados
* Implementar métricas de jogadores
* Implementar métricas de economia
* Implementar métricas por mapa
* Implementar métricas por round
* Implementar heatmaps
* Implementar pipeline Parquet/DuckDB

Métricas mínimas:

* Kills
* Deaths
* Assists
* ADR
* KAST-like
* Entry attempts
* Entry kills
* Entry deaths
* Trade kills
* Clutches
* Utility damage
* Flash assists, se disponível
* Economy/buy type, se disponível
* Estatísticas por arma
* Estatísticas por lado CT/T
* Estatísticas por mapa

Resultado esperado:

```txt
backend/app/analytics/
```

---

## 5.4 Frontend Agent

Responsável por:

* Criar aplicação Next.js
* Implementar dashboard
* Implementar tela de importação
* Implementar relatório de partida
* Implementar Replay2D
* Implementar Heatmaps
* Implementar tela de Playbook privado
* Criar componentes reutilizáveis
* Criar camada de API client

Resultado esperado:

```txt
frontend/
```

---

## 5.5 QA/DevOps Agent

Responsável por:

* Criar README
* Criar comandos de instalação
* Criar testes unitários mínimos
* Criar lint/format
* Criar docker-compose local, se útil
* Validar que backend sobe localmente
* Validar que frontend sobe localmente
* Validar fluxo mínimo com dados mockados

Resultado esperado:

```txt
README.md
AGENTS.md
docker-compose.yml
backend/tests/
```

---

# 6. Funcionalidades MVP

## 6.1 Importação de Demo

Criar endpoint e UI para:

* Selecionar arquivo `.dem`
* Fazer upload/importação local
* Copiar arquivo para `data/raw_demos`
* Criar registro local da demo
* Iniciar job de parsing
* Mostrar status de processamento

Status possíveis:

```txt
pending
parsing
parsed
failed
```

---

## 6.2 Parsing

Implementar parser em camadas.

### Primeira opção

Usar `awpy` para parsing, estatísticas e visualizações quando útil.

### Segunda opção

Usar `demoparser2` para extrair dados tick-level e eventos específicos quando `awpy` não expuser tudo.

## Dados mínimos a extrair

* Metadata da partida
* Nome do mapa
* Times
* Jogadores
* Rounds
* Kills
* Deaths
* Assists, se disponível
* Damages
* Bomb events, se disponível
* Weapon
* Tick
* Tempo
* Posição x/y/z por jogador
* Yaw/angle, se disponível
* Health
* Armor
* Equipment, se disponível
* Side CT/T

## Armazenamento

Salvar:

* Metadados em SQLite
* Dados analíticos em Parquet
* Views ou queries em DuckDB

Organização sugerida:

```txt
data/
  raw_demos/
    example.dem

  processed/
    parquet/
      match_id=abc123/
        rounds.parquet
        players.parquet
        kills.parquet
        damages.parquet
        ticks.parquet
        replay_frames.parquet

    duckdb/
      cs2_lab.duckdb
```

---

# 7. API Backend

Criar endpoints REST.

## Health

```http
GET /health
```

Resposta:

```json
{
  "status": "ok"
}
```

---

## Demos

```http
POST /demos/import
GET /demos
GET /demos/{demo_id}
```

---

## Matches

```http
GET /matches
GET /matches/{match_id}
GET /matches/{match_id}/summary
GET /matches/{match_id}/rounds
GET /matches/{match_id}/players
```

---

## Stats

```http
GET /matches/{match_id}/stats/player
GET /matches/{match_id}/stats/economy
GET /matches/{match_id}/stats/weapons
```

---

## Replay

```http
GET /matches/{match_id}/replay?round=1&sample_rate=8
```

Resposta esperada:

```json
{
  "match_id": "abc123",
  "map": "de_mirage",
  "round": 1,
  "tick_rate": 64,
  "frames": [
    {
      "tick": 12345,
      "time": 12.34,
      "players": [
        {
          "steam_id": "7656119...",
          "name": "player",
          "side": "T",
          "x": 0,
          "y": 0,
          "z": 0,
          "radar_x": 512,
          "radar_y": 384,
          "hp": 100,
          "armor": 100,
          "weapon": "ak47",
          "yaw": 180,
          "alive": true
        }
      ],
      "events": []
    }
  ]
}
```

---

## Heatmaps

```http
GET /matches/{match_id}/heatmap?type=kills
GET /matches/{match_id}/heatmap?type=deaths
GET /matches/{match_id}/heatmap?type=path
GET /matches/{match_id}/heatmap?type=utility
```

---

## Maps

```http
GET /maps
GET /maps/{map_name}/radar
GET /maps/{map_name}/metadata
```

---

# 8. Frontend

Criar telas principais.

---

## 8.1 Home / Dashboard

A tela inicial deve conter:

* Total de demos importadas
* Total de partidas processadas
* Total de mapas
* Total de jogadores identificados
* Lista de últimos jobs
* Status dos jobs
* Atalhos para importação, matches, replay e heatmaps

---

## 8.2 Demos

A tela de demos deve conter:

* Upload/import de arquivo `.dem`
* Lista de demos importadas
* Status de parsing
* Data de importação
* Nome do arquivo
* Botão para abrir relatório
* Mensagem de erro quando parsing falhar

---

## 8.3 Match Report

A tela de relatório deve conter:

* Placar
* Nome do mapa
* Times
* Rounds
* Tabela de jogadores
* KD
* ADR
* KAST-like
* Entry stats
* Trade stats
* Clutch stats
* Estatísticas por arma
* Gráficos simples

---

## 8.4 Replay 2D

Criar um replayer 2D com:

* Radar do mapa como imagem de fundo
* Jogadores como círculos
* Cor por lado CT/T
* Nome ou abreviação do jogador
* Direção/yaw
* Vida
* Arma atual
* Bomba, se disponível
* Eventos importantes
* Timeline
* Seleção de round
* Play/pause
* Speed controls

Velocidades:

```txt
0.25x
0.5x
1x
2x
4x
```

Eventos marcados na timeline:

* Kills
* Bomb plant
* Bomb defuse
* Bomb explode
* Utility, quando disponível

---

## 8.5 Heatmaps

Criar tela de heatmaps com tipos:

* Kills
* Deaths
* Pathing
* Utility

Filtros:

* Player
* Team
* Side CT/T
* Round range
* Weapon, se disponível

---

## 8.6 Playbook Privado

Criar primeira versão de playbook local.

Funcionalidades:

* Criar tática
* Editar tática
* Excluir tática
* Associar tática a mapa
* Associar tática a lado CT/T
* Adicionar descrição
* Adicionar tags
* Adicionar rounds de referência
* Desenhar pontos no mapa
* Desenhar linhas no mapa
* Salvar em SQLite ou JSON local

Campos sugeridos:

```json
{
  "id": "uuid",
  "name": "Mirage A Execute",
  "map": "de_mirage",
  "side": "T",
  "description": "Execução A com smokes padrão.",
  "tags": ["execute", "mirage", "a-site"],
  "reference_rounds": [],
  "drawing": {
    "points": [],
    "lines": []
  }
}
```

---

# 9. Modelo de Dados Inicial

## 9.1 Demo

```json
{
  "id": "uuid",
  "filename": "match.dem",
  "path": "data/raw_demos/match.dem",
  "status": "parsed",
  "created_at": "2026-01-01T12:00:00Z",
  "parsed_at": "2026-01-01T12:05:00Z",
  "error": null
}
```

---

## 9.2 Match

```json
{
  "id": "uuid",
  "demo_id": "uuid",
  "map": "de_mirage",
  "team_a": "Team A",
  "team_b": "Team B",
  "score_a": 13,
  "score_b": 9,
  "started_at": null,
  "tick_rate": 64
}
```

---

## 9.3 Player

```json
{
  "steam_id": "7656119...",
  "name": "player",
  "team": "Team A"
}
```

---

## 9.4 Round

```json
{
  "match_id": "uuid",
  "round_number": 1,
  "winner": "CT",
  "reason": "elimination",
  "start_tick": 1000,
  "end_tick": 9000"
}
```

---

## 9.5 Kill Event

```json
{
  "match_id": "uuid",
  "round_number": 1,
  "tick": 4567,
  "time": 42.1,
  "attacker_steam_id": "7656119...",
  "victim_steam_id": "7656119...",
  "assister_steam_id": null,
  "weapon": "ak47",
  "headshot": true,
  "attacker_x": 0,
  "attacker_y": 0,
  "attacker_z": 0,
  "victim_x": 0,
  "victim_y": 0,
  "victim_z": 0
}
```

---

# 10. Conversão de Coordenadas para Radar

Implementar módulo:

```txt
frontend/lib/mapProjection.ts
backend/app/analytics/map_projection.py
```

Função esperada:

```ts
type RadarMetadata = {
  pos_x: number;
  pos_y: number;
  scale: number;
  image_width: number;
  image_height: number;
};

export function worldToRadar(
  x: number,
  y: number,
  metadata: RadarMetadata
): { radarX: number; radarY: number } {
  const radarX = (x - metadata.pos_x) / metadata.scale;
  const radarY = (metadata.pos_y - y) / metadata.scale;

  return {
    radarX,
    radarY,
  };
}
```

Validar essa fórmula com os metadados reais dos mapas pesquisados. Ajustar conforme necessário.

---

# 11. Requisitos Técnicos

## Backend

* Usar `uv` ou `pip` com `pyproject.toml`
* Type hints obrigatórios
* Pydantic models
* Estrutura modular
* Testes com pytest
* Logging claro
* Tratamento de erro para demo inválida
* API não pode travar durante parsing
* Parsing deve rodar em job separado
* Suporte a mock fallback para testes

---

## Frontend

* Next.js com TypeScript
* Componentes bem separados
* Client components apenas onde necessário
* Canvas/replayer como client component
* Estado de dados com TanStack Query ou camada própria
* Tipos compartilhados em `frontend/lib/types.ts`
* UI responsiva desktop-first
* Design escuro estilo analytics dashboard

---

## Dados

* Criar fixtures pequenas para testes
* Criar mocks realistas para UI/replay
* Separar dados mockados de dados reais
* Não depender de serviço externo obrigatório no MVP
* Salvar dados processados localmente

---

# 12. Etapas de Execução

Execute nesta ordem:

## Etapa 1 — Auditoria

Audite o diretório atual.

Verifique:

* Arquivos existentes
* Estrutura atual
* Dependências existentes
* Se já existe frontend
* Se já existe backend
* Se há conflitos com a estrutura proposta

---

## Etapa 2 — Estrutura

Se o projeto estiver vazio, crie:

```txt
backend/
frontend/
data/
docs/
AGENTS.md
README.md
docker-compose.yml
```

---

## Etapa 3 — Documentação Base

Crie:

```txt
AGENTS.md
docs/research.md
docs/architecture.md
```

O `AGENTS.md` deve conter:

* Comandos de backend
* Comandos de frontend
* Padrões de código
* Convenções de diretório
* Como rodar testes
* Como rodar lint
* Definição de pronto

---

## Etapa 4 — Backend Mínimo

Implemente:

* FastAPI app
* `/health`
* Configuração
* Paths locais
* SQLite inicial
* Modelos Pydantic
* Estrutura de rotas
* Teste básico do healthcheck

---

## Etapa 5 — Importação de Demos

Implemente:

* Upload local
* Validação de extensão `.dem`
* Registro no SQLite
* Cópia para `data/raw_demos`
* Status inicial `pending`
* Endpoint para listar demos
* Endpoint para consultar demo específica

---

## Etapa 6 — Jobs

Implemente:

* Job de parsing
* Status `parsing`
* Status `parsed`
* Status `failed`
* Logging de erro
* Mock fallback se parser real não estiver disponível

---

## Etapa 7 — Parsing Real

Implemente parsing com:

* `awpy`
* `demoparser2` quando necessário

Extrair:

* Match metadata
* Players
* Rounds
* Kills
* Damages
* Bomb events
* Player positions
* Replay frames

Salvar em:

* SQLite para metadados
* Parquet para dados analíticos
* DuckDB para consultas

---

## Etapa 8 — API de Analytics

Implemente endpoints:

```http
GET /matches
GET /matches/{match_id}
GET /matches/{match_id}/summary
GET /matches/{match_id}/rounds
GET /matches/{match_id}/players
GET /matches/{match_id}/stats/player
GET /matches/{match_id}/stats/economy
GET /matches/{match_id}/stats/weapons
GET /matches/{match_id}/replay
GET /matches/{match_id}/heatmap
GET /maps
GET /maps/{map_name}/radar
GET /maps/{map_name}/metadata
```

---

## Etapa 9 — Frontend Base

Crie app Next.js com:

* TypeScript
* Estrutura de rotas
* Layout principal
* Navegação
* Tema escuro
* API client
* Tipos compartilhados

---

## Etapa 10 — Dashboard

Implemente:

* Cards principais
* Últimas demos
* Últimos jobs
* Links para matches, replay e heatmaps

---

## Etapa 11 — Demos UI

Implemente:

* Upload de demo
* Lista de demos
* Status de parsing
* Botão para abrir relatório
* Tratamento de erro

---

## Etapa 12 — Match Report

Implemente:

* Resumo da partida
* Placar
* Times
* Mapa
* Rounds
* Tabela de players
* Estatísticas principais
* Gráficos simples

---

## Etapa 13 — Replay 2D

Implemente:

* Canvas com React-Konva
* Radar como fundo
* Jogadores renderizados
* Timeline
* Play/pause
* Velocidade
* Round selector
* Eventos na timeline
* Interpolação simples entre frames se possível

---

## Etapa 14 — Heatmaps

Implemente:

* Heatmap de kills
* Heatmap de deaths
* Heatmap de pathing
* Heatmap de utility
* Filtros básicos

---

## Etapa 15 — Playbook

Implemente:

* CRUD local de táticas
* Lista de táticas
* Editor de tática
* Desenho no mapa
* Persistência local

---

## Etapa 16 — QA

Rode:

```bash
cd backend
pytest
```

```bash
cd frontend
npm run lint
npm run build
```

Corrija erros críticos.

---

# 13. Comandos Esperados

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload
```

## Frontend

```bash
cd frontend
npm install
npm run dev
npm run lint
npm run build
```

## Root opcional

```bash
docker compose up
```

---

# 14. Critérios de Aceite do MVP

O MVP estará pronto quando:

* Backend sobe localmente
* Frontend sobe localmente
* UI abre no navegador
* É possível importar uma demo ou usar fixture mock
* Demo aparece na lista
* Status de parsing aparece corretamente
* É possível abrir uma partida
* É possível ver relatório básico
* É possível abrir replay 2D
* O replay mostra mapa e jogadores se movendo
* É possível ver pelo menos um heatmap básico
* Código está organizado
* Há README
* Há AGENTS.md
* Há testes mínimos
* Nada depende de serviço externo obrigatório
* Nenhum recurso de cheat, leitura de memória, injeção, DMA ou vantagem competitiva ao vivo foi implementado

---

# 15. Definição de Pronto

Antes de finalizar, entregue um resumo com:

* O que foi criado
* Quais arquivos principais foram alterados
* Como rodar o backend
* Como rodar o frontend
* Como importar uma demo
* Como usar dados mockados
* Quais comandos foram executados
* Resultado dos testes
* Limitações atuais
* Próximos passos recomendados

---

# 16. Limitações Aceitáveis no MVP

É aceitável que:

* Nem todos os eventos de granada estejam perfeitos
* Alguns mapas precisem de ajuste manual de radar metadata
* O parser real tenha fallback para mock se não houver demo disponível
* Estatísticas avançadas venham em uma segunda fase
* PixiJS fique para uma futura otimização
* Multiusuário não exista
* Autenticação não exista
* Deploy público não exista

---

# 17. Próximas Fases Futuras

Depois do MVP, planeje:

## Fase 2 — Analytics Avançado

* Trade windows configuráveis
* Opening duels avançados
* Clutch probability
* Utility effectiveness
* Flash effectiveness
* Path clustering
* Heatmaps por timing
* Comparação entre partidas
* Comparação entre jogadores
* Tendências por mapa

## Fase 3 — Pattern Finder

* Detectar defaults
* Detectar executes
* Detectar retakes
* Detectar stacks
* Detectar timings recorrentes
* Encontrar rounds parecidos
* Buscar padrões por coordenadas e eventos
* Salvar padrões no playbook

## Fase 4 — Playbook Avançado

* Editor visual de táticas
* Layers
* Utility lineups
* Timings
* Exportação em imagem
* Comentários por round
* Clipes/referências de demo

## Fase 5 — Performance

* Cache de replay frames
* Compressão de payload
* Streaming parcial de frames
* Otimização com PixiJS
* Agregações materializadas em DuckDB
* Workers paralelos

---

# 18. Instrução Final para o Agente

Comece agora fazendo a auditoria do repositório.

Depois:

1. Planeje a execução.
2. Crie a estrutura do projeto.
3. Faça a pesquisa técnica.
4. Documente decisões.
5. Implemente o MVP incrementalmente.
6. Rode testes e builds.
7. Corrija erros críticos.
8. Entregue o resumo final.

Não pule a documentação.

Não implemente nada relacionado a cheat ou vantagem ao vivo.

Priorize um MVP funcional, local, organizado e extensível.
