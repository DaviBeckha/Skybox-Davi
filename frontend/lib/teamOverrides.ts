"use client";

import { useCallback, useEffect, useState } from "react";

import type { Side } from "./types";

export type TeamKey = "A" | "B";
export type ColorMode = "team" | "side";
export type TeamSetting = { name: string; color: string };
export type ReplayTeamSettings = {
  colorMode: ColorMode;
  teams: Record<TeamKey, TeamSetting>;
};

// Cores padrão por time (skybox-style: âmbar x azul). Seguem o TIME, não o lado,
// então ficam consistentes mesmo após a troca de lado no intervalo.
export const DEFAULT_TEAM_COLORS: Record<TeamKey, string> = {
  A: "#f5b042",
  B: "#5b9dff"
};

// Esquema clássico por LADO (T amarelo / CT azul), usado no modo "Cor: Lado"
// e como fallback quando o demo não tem nome de time.
export const SIDE_COLORS: Record<Side, string> = {
  T: "#ffce86",
  CT: "#a8c5ff"
};

export const DEFAULT_SETTINGS: ReplayTeamSettings = {
  colorMode: "team",
  teams: {
    A: { name: "", color: DEFAULT_TEAM_COLORS.A },
    B: { name: "", color: DEFAULT_TEAM_COLORS.B }
  }
};

function storageKey(matchId: string): string {
  return `cs2lab:replayTeams:${matchId}`;
}

function coerce(raw: unknown): ReplayTeamSettings {
  const parsed = (raw ?? {}) as Partial<ReplayTeamSettings>;
  const teams = parsed.teams ?? ({} as Partial<Record<TeamKey, TeamSetting>>);
  return {
    colorMode: parsed.colorMode === "side" ? "side" : "team",
    teams: {
      A: {
        name: teams.A?.name ?? "",
        color: teams.A?.color || DEFAULT_TEAM_COLORS.A
      },
      B: {
        name: teams.B?.name ?? "",
        color: teams.B?.color || DEFAULT_TEAM_COLORS.B
      }
    }
  };
}

/** Configuração de times do replay (nome + cor + modo de cor), persistida no
 * navegador por partida. Não toca no backend. */
export function useReplayTeamSettings(matchId: string): {
  settings: ReplayTeamSettings;
  setSettings: (next: ReplayTeamSettings) => void;
} {
  const [settings, setLocal] = useState<ReplayTeamSettings>(DEFAULT_SETTINGS);

  useEffect(() => {
    if (!matchId) {
      return;
    }
    try {
      const raw = window.localStorage.getItem(storageKey(matchId));
      setLocal(raw ? coerce(JSON.parse(raw)) : DEFAULT_SETTINGS);
    } catch {
      setLocal(DEFAULT_SETTINGS);
    }
  }, [matchId]);

  const setSettings = useCallback(
    (next: ReplayTeamSettings) => {
      setLocal(next);
      try {
        window.localStorage.setItem(storageKey(matchId), JSON.stringify(next));
      } catch {
        // localStorage indisponível: mantém só em memória.
      }
    },
    [matchId]
  );

  return { settings, setSettings };
}

/** Cor de um jogador conforme o modo (time/lado) e os overrides. Cai para a cor
 * do lado quando não há time resolvido (demo sem nomes de time). */
export function resolveColor(
  side: Side,
  teamKey: TeamKey | null,
  settings: ReplayTeamSettings
): string {
  if (settings.colorMode === "side" || teamKey === null) {
    return SIDE_COLORS[side];
  }
  return settings.teams[teamKey].color || DEFAULT_TEAM_COLORS[teamKey];
}

/** Nome de exibição de um time: override do usuário > nome do demo > "Time X". */
export function resolveTeamName(
  teamKey: TeamKey,
  fallback: string | null,
  settings: ReplayTeamSettings
): string {
  return settings.teams[teamKey].name.trim() || fallback || `Time ${teamKey}`;
}
