# Phase 01/16 — Auditoria do Repositório

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **auditor técnico do repositório**.

Esta é a primeira phase. Nada deve ser implementado ainda — apenas auditado e relatado.

**Onde os arquivos vivem:** raiz do repositório atual; o relatório é gravado em `docs/audit.md`.

## Pré-requisitos

- Nenhum. Esta é a primeira phase.

## Objetivo

Auditar o estado atual do repositório e gravar um relatório claro (`docs/audit.md`) do que existe, do que falta e de eventuais conflitos com a estrutura-alvo do projeto — para que a Phase 02 possa lê-lo.

## Escopo (o que fazer)

Inspecione o diretório atual e verifique:

- Arquivos existentes e estrutura de pastas atual.
- Dependências já declaradas (qualquer `pyproject.toml`, `package.json`, lockfiles).
- Se já existe um `frontend/` ou `backend/`.
- Se há conflitos com a estrutura-alvo proposta (ver abaixo).
- Presença de `git`, `.gitignore`, documentação existente.

Grave o resultado em `docs/audit.md` (criando a pasta `docs/` se necessário).

Estrutura-alvo do projeto (referência para detectar conflitos):

```txt
cs2-lab/
  backend/        (FastAPI, parsers, analytics, storage, workers, tests)
  frontend/       (Next.js, components, lib)
  data/           (raw_demos, processed/parquet, processed/duckdb, maps)
  docs/           (research.md, architecture.md, audit.md)
  docker-compose.yml   (PostgreSQL + Redis)
  AGENTS.md
  README.md
```

## Fora de escopo

- Não crie pastas de código nem arquivos de configuração de aplicação (só `docs/audit.md`).
- Não instale dependências.
- Não altere o `contract.md`.

## Entregáveis

- `docs/audit.md` cobrindo: o que existe, o que falta, conflitos encontrados e recomendação de como proceder para a Phase 02.

## Critérios de aceite

- [ ] `docs/audit.md` existe e lista os arquivos/pastas relevantes existentes.
- [ ] Relatório indica claramente se há backend/frontend pré-existentes.
- [ ] Relatório aponta conflitos (ou confirma que não há) com a estrutura-alvo.
- [ ] Nenhum arquivo de código foi criado ou modificado.

## Comandos de validação

- N/A (phase de leitura/auditoria apenas). Conferir que `docs/audit.md` foi gerado.

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 02 — Estrutura base** (`02-estrutura.md`).
