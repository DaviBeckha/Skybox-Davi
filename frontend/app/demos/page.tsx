"use client";

import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { UploadDemo } from "@/components/upload-demo";
import { formatDateTime } from "@/lib/format";
import { useDemosQuery, useMatchesQuery } from "@/lib/queries";

export default function DemosPage() {
  const demosQuery = useDemosQuery();
  const matchesQuery = useMatchesQuery();

  const demos = demosQuery.data ?? [];
  const matches = matchesQuery.data ?? [];
  const matchByDemo = new Map(matches.map((match) => [match.demoId, match.id]));
  const ordered = [...demos].sort((a, b) => b.createdAt.localeCompare(a.createdAt));

  return (
    <>
      <PageHeader
        eyebrow="Demos"
        title="Importação e status das suas demos."
        description="Envie um arquivo .dem, acompanhe o parsing e abra o relatório quando a partida estiver pronta."
      />

      <section className="surface-grid" aria-label="Demos">
        <article className="panel full">
          <div className="panel-head">
            <h2>Importar demo</h2>
            <span>POST /demos/import</span>
          </div>
          <UploadDemo />
        </article>

        <article className="panel full" aria-label="Demos importadas">
          <div className="panel-head">
            <h2>Demos importadas</h2>
            <span>{demos.length} no total</span>
          </div>

          {demosQuery.isLoading ? (
            <p className="state-note">Carregando…</p>
          ) : demosQuery.isError ? (
            <p className="state-note" role="alert">
              Não foi possível carregar as demos. Verifique se o backend está no ar em{" "}
              <span className="mono">localhost:8000</span>.
            </p>
          ) : ordered.length === 0 ? (
            <p className="state-note">Nenhuma demo importada ainda. Use o formulário acima.</p>
          ) : (
            <ul className="demo-list">
              {ordered.map((demo) => {
                const matchId = matchByDemo.get(demo.id);
                return (
                  <li className="demo-row" key={demo.id}>
                    <div className="demo-row-head">
                      <div className="data-main">
                        <strong>{demo.filename}</strong>
                        <small>{formatDateTime(demo.createdAt)}</small>
                      </div>
                      <div className="demo-actions">
                        <StatusBadge status={demo.status} />
                        {demo.status === "parsed" && matchId ? (
                          <Link className="button small primary" href={`/matches/${matchId}`}>
                            Abrir relatório
                          </Link>
                        ) : null}
                      </div>
                    </div>
                    {demo.status === "failed" && demo.error ? (
                      <p className="demo-error" role="alert">
                        Erro no parsing: {demo.error}
                      </p>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          )}
        </article>
      </section>
    </>
  );
}
