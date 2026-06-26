import { MatchReport } from "@/components/match-report";

type MatchPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function MatchPage({ params }: MatchPageProps) {
  const { id } = await params;
  return <MatchReport matchId={id} />;
}
