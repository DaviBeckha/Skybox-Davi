import { PageHeader } from "@/components/page-header";
import { PlaceholderPanel } from "@/components/placeholder-panel";

export default function DemosPage() {
  return (
    <>
      <PageHeader
        eyebrow="Demos"
        title="Uploads locais de arquivos .dem"
        description="A rota já existe para receber a UI de importação. Upload, tabela e status de parsing serão implementados na Phase 11."
      />
      <PlaceholderPanel title="Importação de demos" phase="Phase 11">
        <p>
          O backend já expõe <span className="mono">POST /demos/import</span> e{" "}
          <span className="mono">GET /demos</span>. Esta tela fica preparada, mas sem implementar o
          formulário final nesta phase.
        </p>
      </PlaceholderPanel>
    </>
  );
}
