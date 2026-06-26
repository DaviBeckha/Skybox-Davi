import { PageHeader } from "@/components/page-header";
import { PlaceholderPanel } from "@/components/placeholder-panel";

export default function AnalyticsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Heatmaps"
        title="Mapas de calor e filtros"
        description="Área base para visualizar kills, deaths, pathing e utility. A implementação visual entra na Phase 14."
      />
      <PlaceholderPanel title="Heatmap placeholder" phase="Phase 14">
        <p>
          O cliente já está preparado para <span className="mono">GET /matches/:id/heatmap</span> e
          tipos de filtro como player, team, side, round range, weapon e grenade type.
        </p>
      </PlaceholderPanel>
    </>
  );
}
