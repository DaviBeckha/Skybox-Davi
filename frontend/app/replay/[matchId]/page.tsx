import { Replay2D } from "@/components/replay-2d";

type ReplayPageProps = {
  params: Promise<{
    matchId: string;
  }>;
};

export default async function ReplayPage({ params }: ReplayPageProps) {
  const { matchId } = await params;
  return <Replay2D matchId={matchId} />;
}
