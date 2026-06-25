# Phase 11/16 — Demos UI

> Parte do fluxo de execução em phases do **cs2-lab**. Execute as phases em ordem. Ao concluir esta phase (todos os critérios de aceite ✓), avance para a próxima.
>
> **Antes de começar, leia:** o **Protocolo de execução** e as **Convenções técnicas** em [`00-indice.md`](00-indice.md) e o contrato de dados em [`_shared/data-contract.md`](_shared/data-contract.md). Se já existirem, leia também `AGENTS.md`, `docs/architecture.md` e a saída da phase anterior.

## Contexto

O **cs2-lab** é uma plataforma local e pessoal de análise de demos de Counter-Strike 2 (backend Python/FastAPI + frontend Next.js), usada offline para revisar partidas já gravadas. **Regra inviolável:** nada de leitura de memória do jogo, DMA, injeção de código, wallhack, radar ao vivo, automação de gameplay ou qualquer vantagem competitiva em tempo real — apenas analytics e revisão de demos `.dem` gravadas. Você atua como **frontend engineer (Next.js/TypeScript)**.

**Stack relevante a esta phase:** Next.js, TypeScript, TanStack Query. Consome `POST /demos/import`, `GET /demos`.

**Onde os arquivos vivem:** `frontend/app/demos/`, `frontend/components/UploadDemo/`.

## Pré-requisitos

- Phase 05 (Importação de demos no backend) e Phase 09 (Frontend base) concluídas.

## Objetivo

Implementar a tela de demos: importar arquivo `.dem`, listar demos, acompanhar status de parsing e abrir o relatório.

## Escopo (o que fazer)

A tela de demos deve conter:
- Upload/import de arquivo `.dem` (componente `UploadDemo`), chamando `POST /demos/import`.
- Lista de demos importadas (`GET /demos`) com: nome do arquivo, data de importação, status de parsing.
- Indicação visual do status (`pending`, `parsing`, `parsed`, `failed`).
- Botão para abrir o relatório da partida (quando `parsed`).
- Mensagem de erro quando o parsing falhar (campo `error` da demo).

Atualizar a lista conforme o status evolui (polling/refetch via TanStack Query).

## Fora de escopo

- Não implemente o conteúdo do match report (Phase 12) — apenas o link/botão para abri-lo.
- Não altere o backend de importação (já entregue na Phase 05).

## Entregáveis

- Tela de demos com upload + lista + status + ação de abrir relatório.
- Componente `UploadDemo` reutilizável.

## Critérios de aceite

- [ ] É possível importar um `.dem` pela UI e ele aparece na lista.
- [ ] Status de parsing é exibido e atualiza conforme evolui.
- [ ] Botão "abrir relatório" disponível quando a demo está `parsed`.
- [ ] Erro de parsing é exibido de forma clara.
- [ ] `npm run lint` e `npm run build` passam.

## Comandos de validação

```bash
cd frontend
npm run dev   # com o backend rodando
npm run lint
npm run build
```

## Conclusão da phase

Quando todos os critérios de aceite estiverem ✓, marque esta phase como concluída no `00-indice.md` e prossiga para a **Phase 12 — Match Report** (`12-match-report.md`).
