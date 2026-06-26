import { PageHeader } from "@/components/page-header";
import { PlaceholderPanel } from "@/components/placeholder-panel";

export default function MatchesPage() {
  return (
    <>
      <PageHeader
        eyebrow="Matches"
        title="Partidas parseadas"
        description="Base para a lista de partidas e entrada para relatórios. O conteúdo final do match report é escopo da Phase 12."
      />
      <PlaceholderPanel title="Lista de partidas" phase="Phase 12">
        <p>
          O cliente já sabe chamar <span className="mono">GET /matches</span>,{" "}
          <span className="mono">GET /matches/:id</span>, rounds e players. A tela final será
          conectada quando a phase de relatório começar.
        </p>
      </PlaceholderPanel>
    </>
  );
}
