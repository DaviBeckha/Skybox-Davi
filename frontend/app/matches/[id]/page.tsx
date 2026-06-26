import { PageHeader } from "@/components/page-header";
import { PlaceholderPanel } from "@/components/placeholder-panel";

type MatchPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function MatchPage({ params }: MatchPageProps) {
  const { id } = await params;

  return (
    <>
      <PageHeader
        eyebrow="Match report"
        title="Relatório da partida"
        description="Rota dinâmica preparada para o relatório completo da Phase 12."
      />
      <PlaceholderPanel title="Match selecionado" phase="Phase 12">
        <p>
          Match ID: <span className="mono">{id}</span>
        </p>
        <p>
          A consulta de resumo, rounds, players e estatísticas já está tipada em{" "}
          <span className="mono">lib/api.ts</span>.
        </p>
      </PlaceholderPanel>
    </>
  );
}
