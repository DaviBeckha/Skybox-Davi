"use client";

import {
  DEFAULT_TEAM_COLORS,
  type ReplayTeamSettings,
  type TeamKey,
  type TeamSetting
} from "@/lib/teamOverrides";

const KEYS: TeamKey[] = ["A", "B"];

export function ReplayTeamEditor({
  settings,
  teamNames,
  hasTeams,
  onChange
}: {
  settings: ReplayTeamSettings;
  teamNames: Record<TeamKey, string | null>;
  hasTeams: boolean;
  onChange: (next: ReplayTeamSettings) => void;
}) {
  const update = (key: TeamKey, patch: Partial<TeamSetting>) =>
    onChange({
      ...settings,
      teams: { ...settings.teams, [key]: { ...settings.teams[key], ...patch } }
    });

  return (
    <div className="replay-team-editor panel">
      {KEYS.map((key) => (
        <div className="team-editor-row" key={key}>
          <span className="team-editor-label">Time {key}</span>
          <input
            className="team-editor-name"
            type="text"
            placeholder={teamNames[key] ?? `Time ${key}`}
            value={settings.teams[key].name}
            onChange={(event) => update(key, { name: event.target.value })}
          />
          <input
            className="team-editor-color"
            type="color"
            value={settings.teams[key].color || DEFAULT_TEAM_COLORS[key]}
            onChange={(event) => update(key, { color: event.target.value })}
            aria-label={`Cor do Time ${key}`}
          />
        </div>
      ))}
      {!hasTeams ? (
        <p className="state-note">
          Sem nomes de time neste demo — as cores seguem o lado (T/CT). Os nomes editados
          ainda aparecem no título.
        </p>
      ) : null}
    </div>
  );
}
