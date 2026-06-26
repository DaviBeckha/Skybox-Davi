"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "./api";

export const queryKeys = {
  health: ["health"] as const,
  demos: ["demos"] as const,
  demo: (demoId: string) => ["demos", demoId] as const,
  matches: ["matches"] as const,
  match: (matchId: string) => ["matches", matchId] as const,
  matchSummary: (matchId: string) => ["matches", matchId, "summary"] as const,
  matchRounds: (matchId: string) => ["matches", matchId, "rounds"] as const,
  matchPlayers: (matchId: string) => ["matches", matchId, "players"] as const,
  playerStats: (matchId: string) => ["matches", matchId, "stats", "player"] as const,
  utilityStats: (matchId: string) => ["matches", matchId, "stats", "utility"] as const,
  matchups: (matchId: string) => ["matches", matchId, "stats", "matchups"] as const,
  weaponStats: (matchId: string) => ["matches", matchId, "stats", "weapons"] as const,
  bombsiteStats: (matchId: string) => ["matches", matchId, "stats", "bombsites"] as const,
  maps: ["maps"] as const,
  mapMetadata: (mapName: string) => ["maps", mapName, "metadata"] as const
};

export function useHealthQuery() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: api.getHealth
  });
}

export function useDemosQuery() {
  return useQuery({
    queryKey: queryKeys.demos,
    queryFn: api.getDemos,
    // Enquanto houver parsing em andamento, refaz a busca para refletir o status.
    refetchInterval: (query) =>
      (query.state.data ?? []).some(
        (demo) => demo.status === "pending" || demo.status === "parsing"
      )
        ? 2500
        : false
  });
}

export function useDemoQuery(demoId: string) {
  return useQuery({
    queryKey: queryKeys.demo(demoId),
    queryFn: () => api.getDemo(demoId),
    enabled: demoId.length > 0
  });
}

export function useMatchesQuery() {
  return useQuery({
    queryKey: queryKeys.matches,
    queryFn: api.getMatches
  });
}

export function useMatchSummaryQuery(matchId: string) {
  return useQuery({
    queryKey: queryKeys.matchSummary(matchId),
    queryFn: () => api.getMatchSummary(matchId),
    enabled: matchId.length > 0
  });
}

export function useMatchRoundsQuery(matchId: string) {
  return useQuery({
    queryKey: queryKeys.matchRounds(matchId),
    queryFn: () => api.getMatchRounds(matchId),
    enabled: matchId.length > 0
  });
}

export function usePlayerStatsQuery(matchId: string) {
  return useQuery({
    queryKey: queryKeys.playerStats(matchId),
    queryFn: () => api.getPlayerStats(matchId),
    enabled: matchId.length > 0
  });
}

export function useUtilityStatsQuery(matchId: string) {
  return useQuery({
    queryKey: queryKeys.utilityStats(matchId),
    queryFn: () => api.getUtilityStats(matchId),
    enabled: matchId.length > 0
  });
}

export function useMatchupsQuery(matchId: string) {
  return useQuery({
    queryKey: queryKeys.matchups(matchId),
    queryFn: () => api.getMatchups(matchId),
    enabled: matchId.length > 0
  });
}

export function useWeaponStatsQuery(matchId: string) {
  return useQuery({
    queryKey: queryKeys.weaponStats(matchId),
    queryFn: () => api.getWeaponStats(matchId),
    enabled: matchId.length > 0
  });
}

export function useBombsiteStatsQuery(matchId: string) {
  return useQuery({
    queryKey: queryKeys.bombsiteStats(matchId),
    queryFn: () => api.getBombsiteStats(matchId),
    enabled: matchId.length > 0
  });
}

export function useReplayQuery(matchId: string, round: number, sampleRate: number) {
  return useQuery({
    queryKey: ["matches", matchId, "replay", round, sampleRate] as const,
    queryFn: () => api.getReplay(matchId, { round, sampleRate }),
    enabled: matchId.length > 0 && round > 0
  });
}

export function useMapMetadataQuery(mapName: string) {
  return useQuery({
    queryKey: queryKeys.mapMetadata(mapName),
    queryFn: () => api.getMapMetadata(mapName),
    enabled: mapName.length > 0
  });
}

export function useMapsQuery() {
  return useQuery({
    queryKey: queryKeys.maps,
    queryFn: api.getMaps
  });
}
