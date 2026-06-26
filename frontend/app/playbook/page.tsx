import { PageHeader } from "@/components/page-header";
import { PlaceholderPanel } from "@/components/placeholder-panel";

export default function PlaybookPage() {
  return (
    <>
      <PageHeader
        eyebrow="Playbook privado"
        title="Táticas e anotações locais"
        description="Espaço reservado para táticas pessoais por mapa/lado. CRUD e desenho entram apenas na Phase 15."
      />
      <PlaceholderPanel title="Playbook local" phase="Phase 15">
        <p>
          A base visual já reserva o espaço do playbook, sem criar o editor ou entidades de tática
          nesta phase.
        </p>
      </PlaceholderPanel>
    </>
  );
}
