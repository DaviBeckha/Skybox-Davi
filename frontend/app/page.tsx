import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { PlaceholderPanel } from "@/components/placeholder-panel";
import { NAV_ITEMS } from "@/lib/navigation";

export default function DashboardPage() {
  return (
    <>
      <PageHeader
        eyebrow="Phase 09 · Frontend base"
        title="Base visual e estrutural para revisar suas demos de CS2."
        description="Este dashboard ainda é um esqueleto. As métricas reais entram na Phase 10; a base já deixa navegação, tema e contratos prontos."
      />

      <section className="surface-grid" aria-label="Resumo da base do produto">
        <article className="panel stat-card third">
          <span>Escopo</span>
          <strong>Offline</strong>
          <p>Somente demos gravadas e analytics local, sem integração em tempo real com o jogo.</p>
        </article>
        <article className="panel stat-card third">
          <span>API</span>
          <strong>FastAPI</strong>
          <p>Cliente preparado para consumir o backend local em <span className="mono">:8000</span>.</p>
        </article>
        <article className="panel stat-card third">
          <span>UI</span>
          <strong>Dark</strong>
          <p>Layout desktop-first, responsivo e com estados de foco acessíveis.</p>
        </article>

        <PlaceholderPanel title="Rotas principais disponíveis" phase="Phase 09">
          <p>
            A navegação já cobre as áreas do MVP. Cada rota ainda mantém conteúdo placeholder para
            respeitar as próximas phases.
          </p>
          <ul className="route-list" aria-label="Rotas do frontend">
            {NAV_ITEMS.map((item) => (
              <li key={item.href}>
                <Link href={item.href}>
                  <span>{item.label}</span>
                  <span className="mono">{item.href}</span>
                </Link>
              </li>
            ))}
          </ul>
        </PlaceholderPanel>
      </section>
    </>
  );
}
