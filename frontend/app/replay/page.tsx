import { PageHeader } from "@/components/page-header";
import { PlaceholderPanel } from "@/components/placeholder-panel";

export default function ReplayIndexPage() {
  return (
    <>
      <PageHeader
        eyebrow="Replay"
        title="Entrada para replay 2D"
        description="A rota base permite navegação funcional. O canvas e timeline do replay ficam para a Phase 13."
      />
      <PlaceholderPanel title="Selecione uma partida" phase="Phase 13">
        <p>
          O replay tipado consome <span className="mono">GET /matches/:id/replay</span>, com
          coordenadas de radar já calculadas pelo backend.
        </p>
      </PlaceholderPanel>
    </>
  );
}
