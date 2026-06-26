import { PageHeader } from "@/components/page-header";
import { PlaceholderPanel } from "@/components/placeholder-panel";

type ReplayPageProps = {
  params: Promise<{
    matchId: string;
  }>;
};

export default async function ReplayPage({ params }: ReplayPageProps) {
  const { matchId } = await params;

  return (
    <>
      <PageHeader
        eyebrow="Replay 2D"
        title="Revisão round a round"
        description="Rota dinâmica pronta para receber o canvas de replay na Phase 13."
      />
      <PlaceholderPanel title="Replay selecionado" phase="Phase 13">
        <p>
          Match ID: <span className="mono">{matchId}</span>
        </p>
        <p>
          Esta phase não implementa canvas, timeline ou controles de reprodução.
        </p>
      </PlaceholderPanel>
    </>
  );
}
