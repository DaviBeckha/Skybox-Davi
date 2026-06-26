import { describe, expect, it } from "vitest";

import {
  DEFAULT_SETTINGS,
  DEFAULT_TEAM_COLORS,
  resolveColor,
  resolveTeamName,
  SIDE_COLORS,
  type ReplayTeamSettings
} from "./teamOverrides";

function withTeamA(patch: Partial<{ name: string; color: string }>): ReplayTeamSettings {
  return {
    ...DEFAULT_SETTINGS,
    teams: { ...DEFAULT_SETTINGS.teams, A: { ...DEFAULT_SETTINGS.teams.A, ...patch } }
  };
}

describe("resolveColor", () => {
  it("usa a cor do lado quando colorMode = side", () => {
    const settings: ReplayTeamSettings = { ...DEFAULT_SETTINGS, colorMode: "side" };
    expect(resolveColor("T", "A", settings)).toBe(SIDE_COLORS.T);
  });

  it("usa a cor padrão do time quando colorMode = team", () => {
    expect(resolveColor("CT", "B", DEFAULT_SETTINGS)).toBe(DEFAULT_TEAM_COLORS.B);
  });

  it("cai para a cor do lado quando não há time resolvido", () => {
    expect(resolveColor("T", null, DEFAULT_SETTINGS)).toBe(SIDE_COLORS.T);
  });

  it("respeita a cor custom do time", () => {
    expect(resolveColor("T", "A", withTeamA({ color: "#123456" }))).toBe("#123456");
  });
});

describe("resolveTeamName", () => {
  it("usa o override quando houver", () => {
    expect(resolveTeamName("A", "fallback", withTeamA({ name: "FURIA" }))).toBe("FURIA");
  });

  it("usa o fallback do demo quando sem override", () => {
    expect(resolveTeamName("A", "NAVI", DEFAULT_SETTINGS)).toBe("NAVI");
  });

  it("usa 'Time X' quando não há override nem fallback", () => {
    expect(resolveTeamName("B", null, DEFAULT_SETTINGS)).toBe("Time B");
  });
});
