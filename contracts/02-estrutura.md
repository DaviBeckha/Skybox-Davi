# Phase 02/16 — Estrutura Base do Projeto

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior (`docs/audit.md`).

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **arquiteto de software responsável por bootstrapar a estrutura do projeto**.

**Onde os arquivos vivem:** raiz do repositório.

## Pré-requisitos

- Phase 01 (Auditoria) concluída (`docs/audit.md` gerado). O repositório está essencialmente vazio (sem backend/frontend pré-existentes).

## Objetivo

Criar o esqueleto de diretórios e arquivos-raiz do projeto, com placeholders mínimos, pronto para receber as phases seguintes.

## Escopo (o que fazer)

Crie a árvore base:

```txt
backend/
  app/
    api/
    core/
    parsers/
    analytics/
    storage/
    workers/
    tests/
frontend/
  app/
  components/
  lib/
data/
  raw_demos/
  processed/
    parquet/
    duckdb/
  maps/
    radars/
    radar_info/
docs/
AGENTS.md
README.md
docker-compose.yml
.gitignore
```

- Use placeholders mínimos (ex.: `.gitkeep` em pastas vazias, `README.md` e `AGENTS.md` com um título e seção "em construção").
- `.gitignore` adequado para Python (`.venv`, `__pycache__`, `*.duckdb`) e Node (`node_modules`, `.next`); ignore dados pesados em `data/raw_demos/` e `data/processed/`.
- `docker-compose.yml` pode começar como placeholder; os serviços **PostgreSQL** e **Redis** são adicionados nas Phases 04 e 06.
- Não adicione lógica de aplicação ainda — apenas a casca.

## Fora de escopo

- Não implemente FastAPI, Next.js, parsers, analytics ou rotas (ficam para phases posteriores).
- Não preencha o conteúdo detalhado de `AGENTS.md`/`docs` (isso é a Phase 03).
- Não comite demos reais em `data/raw_demos`.

## Entregáveis

- Árvore de diretórios acima criada.
- `AGENTS.md`, `README.md`, `docker-compose.yml`, `.gitignore` na raiz (placeholders mínimos).

## Critérios de aceite

- [ ] Todas as pastas da árvore-alvo existem.
- [ ] Pastas vazias têm `.gitkeep` (ou equivalente) para serem versionadas.
- [ ] `.gitignore` cobre artefatos de Python, Node e dados pesados.
- [ ] Nenhuma lógica de aplicação foi adicionada.

## Comandos de validação

- Verifique a árvore criada (ex.: `tree` ou listagem recursiva).

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 03 — Documentação base** (`03-documentacao-base.md`).
