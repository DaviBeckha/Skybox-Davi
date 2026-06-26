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
    queryFn: api.getDemos
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

export function useMapsQuery() {
  return useQuery({
    queryKey: queryKeys.maps,
    queryFn: api.getMaps
  });
}
