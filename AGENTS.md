# AGENTS.md — cs2-lab

> **Em construção.** O conteúdo completo (comandos de backend/frontend, padrões de código, convenções de diretório/nomenclatura, como rodar testes/lint e a definição de pronto) é entregue na **Phase 03 — Documentação base**.

Guia operacional para agentes e desenvolvedores que trabalham neste repositório. Até a Phase 03, consulte as **Convenções técnicas** em [`contracts/00-indice.md`](contracts/00-indice.md) e o **contrato de dados** em [`contracts/_shared/data-contract.md`](contracts/_shared/data-contract.md).

## Resumo das convenções (provisório)

- **Backend:** Python 3.11+ com `uv`; type hints obrigatórios; modelos Pydantic.
- **Frontend:** Node 20 LTS com `npm`; Next.js + TypeScript.
- **Nomenclatura:** `snake_case` no backend/dados, `camelCase` no frontend; `steam_id` (steamID64) como string; `side` ∈ {`CT`, `T`}; ids `uuid` v4.
- **Infra local:** `docker-compose` sobe PostgreSQL + Redis.
