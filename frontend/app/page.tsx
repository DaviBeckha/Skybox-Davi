"use client";

import { useQueries } from "@tanstack/react-query";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { StatCard } from "@/components/stat-card";
import { StatusBadge } from "@/components/status-badge";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { useDemosQuery, useMatchesQuery } from "@/lib/queries";
import type { Demo } from "@/lib/types";

const SHORTCUTS = [
  { href: "/demos", label: "Importar demo", hint: "Enviar um .dem e acompanhar o parsing" },
  { href: "/matches", label: "Partidas", hint: "Abrir relatórios por match" },
  { href: "/replay", label: "Replay 2D", hint: "Revisar rounds sobre o radar" },
  { href: "/analytics", label: "Heatmaps", hint: "Mapas de calor e filtros" }
];

function jobActivity(demo: Demo): string {
  return demo.parsedAt ?? demo.createdAt;
}

export default function DashboardPage() {
  const demosQuery = useDemosQuery();
  const matchesQuery = useMatchesQuery();

  const demos = demosQuery.data ?? [];
  const matches = matchesQuery.data ?? [];

  // "Jogadores identificados" = steamIDs únicos entre as partidas (1 query por match).
  const playersQueries = useQueries({
    queries: matches.map((match) => ({
      queryKey: ["matches", match.id, "players"] as const,
      queryFn: () => api.getMatchPlayers(match.id)
    }))
  });
  const uniquePlayers = new Set<string>();
  for (const query of playersQueries) {
    for (const player of query.data ?? []) {
      uniquePlayers.add(player.steamId);
    }
  }
  const playersLoading = matchesQuery.isLoading || playersQueries.some((query) => query.isLoading);

  const mapsCount = new Set(matches.map((match) => match.map)).size;

  const recentDemos = [...demos]
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
    .slice(0, 6);
  const recentJobs = [...demos]
    .sort((a, b) => jobActivity(b).localeCompare(jobActivity(a)))
    .slice(0, 6);

  const hasError = demosQuery.isError || matchesQuery.isError;

  return (
    <>
      <PageHeader
        eyebrow="Dashboard"
        title="Visão geral da sua base local de demos."
        description="Totais, atividade recente de parsing e atalhos para as áreas do cs2-lab. Os dados vêm do backend local via API."
      />

      {hasError ? (
        <section className="panel full error-banner" role="alert">
          <strong>Não foi possível falar com o backend.</strong>
          <p>
            Verifique se a API está no ar em <span className="mono">localhost:8000</span> (
            <span className="mono">uvicorn app.main:app --reload</span>) e recarregue a página.
          </p>
        </section>
      ) : null}

      <section className="surface-grid" aria-label="Resumo da plataforma">
        <StatCard
          label="Demos importadas"
          value={demos.length}
          loading={demosQuery.isLoading}
          hint="Arquivos .dem registrados localmente."
        />
        <StatCard
          label="Partidas processadas"
          value={matches.length}
          loading={matchesQuery.isLoading}
          hint="Matches com parsing concluído."
        />
        <StatCard
          label="Mapas analisados"
          value={mapsCount}
          loading={matchesQuery.isLoading}
          hint="Mapas distintos entre as partidas."
        />
        <StatCard
          label="Jogadores identificados"
          value={uniquePlayers.size}
          loading={playersLoading}
          hint="SteamIDs únicos nas partidas."
        />

        <article className="panel half" aria-label="Últimos jobs de parsing">
          <div className="panel-head">
            <h2>Últimos jobs</h2>
            <span>Status do parsing</span>
          </div>
          {demosQuery.isLoading ? (
            <p className="state-note">Carregando…</p>
          ) : recentJobs.length === 0 ? (
            <p className="state-note">
              Nenhum job ainda. <Link href="/demos">Importe uma demo</Link> para começar.
            </p>
          ) : (
            <ul className="data-list">
              {recentJobs.map((demo) => (
                <li className="data-row" key={`job-${demo.id}`}>
                  <div className="data-main">
                    <strong>{demo.filename}</strong>
                    <small>{formatDateTime(jobActivity(demo))}</small>
                  </div>
                  <StatusBadge status={demo.status} />
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="panel half" aria-label="Últimas demos importadas">
          <div className="panel-head">
            <h2>Últimas demos</h2>
            <span>Por data de importação</span>
          </div>
          {demosQuery.isLoading ? (
            <p className="state-note">Carregando…</p>
          ) : recentDemos.length === 0 ? (
            <p className="state-note">
              Nenhuma demo importada. <Link href="/demos">Importar agora</Link>.
            </p>
          ) : (
            <ul className="data-list">
              {recentDemos.map((demo) => (
                <li className="data-row" key={`demo-${demo.id}`}>
                  <div className="data-main">
                    <strong>{demo.filename}</strong>
                    <small>{formatDateTime(demo.createdAt)}</small>
                  </div>
                  <StatusBadge status={demo.status} />
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="panel full" aria-label="Atalhos">
          <div className="panel-head">
            <h2>Atalhos</h2>
            <span>Ir direto para as áreas</span>
          </div>
          <ul className="route-list">
            {SHORTCUTS.map((shortcut) => (
              <li key={shortcut.href}>
                <Link href={shortcut.href}>
                  <span>{shortcut.label}</span>
                  <span className="mono">{shortcut.href}</span>
                </Link>
              </li>
            ))}
          </ul>
        </article>
      </section>
    </>
  );
}
