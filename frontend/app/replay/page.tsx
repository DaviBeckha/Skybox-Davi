"use client";

import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { useMatchesQuery } from "@/lib/queries";

export default function ReplayIndexPage() {
  const matchesQuery = useMatchesQuery();
  const matches = matchesQuery.data ?? [];

  return (
    <>
      <PageHeader
        eyebrow="Replay"
        title="Escolha uma partida para revisar."
        description="Abra o replay 2D round a round sobre o radar do mapa."
      />

      <section className="surface-grid" aria-label="Partidas para replay">
        <article className="panel full">
          <div className="panel-head">
            <h2>Partidas</h2>
            <span>{matches.length} no total</span>
          </div>

          {matchesQuery.isLoading ? (
            <p className="state-note">Carregando…</p>
          ) : matchesQuery.isError ? (
            <p className="state-note" role="alert">
              Não foi possível carregar as partidas. Verifique o backend em{" "}
              <span className="mono">localhost:8000</span>.
            </p>
          ) : matches.length === 0 ? (
            <p className="state-note">
              Nenhuma partida processada ainda. <Link href="/demos">Importe uma demo</Link>.
            </p>
          ) : (
            <ul className="demo-list">
              {matches.map((match) => (
                <li className="demo-row" key={match.id}>
                  <div className="demo-row-head">
                    <div className="data-main">
                      <strong>
                        {(match.teamA ?? "Time A")} x {(match.teamB ?? "Time B")}
                      </strong>
                      <small className="mono">{match.map}</small>
                    </div>
                    <div className="demo-actions">
                      <Link className="button small primary" href={`/replay/${match.id}`}>
                        Abrir replay
                      </Link>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>
    </>
  );
}
