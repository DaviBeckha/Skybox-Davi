"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { GrenadeIcon, GRENADE_COLORS } from "@/components/replay-grenade-icon";
import { ReplayTeamEditor } from "@/components/replay-team-editor";
import { DEFAULT_API_BASE_URL } from "@/lib/api";
import {
  useMapMetadataQuery,
  useMatchPlayersQuery,
  useMatchRoundsQuery,
  useMatchSummaryQuery,
  useReplayQuery
} from "@/lib/queries";
import {
  resolveColor,
  resolveTeamName,
  useReplayTeamSettings,
  type TeamKey
} from "@/lib/teamOverrides";
import type { GrenadeType, ReplayPlayer, Side } from "@/lib/types";

const SPEEDS = [0.25, 0.5, 1, 2, 4];
// Densidade nativa do parser (1 frame a cada ~8 ticks); a suavidade vem da
// interpolação, não de baixar mais frames.
const SAMPLE_RATE = 1;

function shorten(name: string): string {
  return name.length > 9 ? `${name.slice(0, 8)}…` : name;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function lerpAngle(a: number | null, b: number | null, t: number): number | null {
  if (a === null) {
    return b;
  }
  if (b === null) {
    return a;
  }
  const delta = ((b - a + 540) % 360) - 180;
  return a + delta * t;
}

export function Replay2D({ matchId }: { matchId: string }) {
  const summaryQuery = useMatchSummaryQuery(matchId);
  const roundsQuery = useMatchRoundsQuery(matchId);
  const playersQuery = useMatchPlayersQuery(matchId);
  const map = summaryQuery.data?.map ?? "";
  const metadataQuery = useMapMetadataQuery(map);

  const { settings, setSettings } = useReplayTeamSettings(matchId);
  const [showTeamEditor, setShowTeamEditor] = useState(false);

  const [round, setRound] = useState(1);
  const [playhead, setPlayhead] = useState(0); // posição contínua em "frames"
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  const replayQuery = useReplayQuery(matchId, round, SAMPLE_RATE);
  const frames = useMemo(() => replayQuery.data?.frames ?? [], [replayQuery.data]);
  const totalFrames = frames.length;

  const imageWidth = metadataQuery.data?.imageWidth ?? 1024;
  const imageHeight = metadataQuery.data?.imageHeight ?? 1024;
  const radarUrl = map ? `${DEFAULT_API_BASE_URL}/maps/${encodeURIComponent(map)}/radar` : "";
  const tickRate = replayQuery.data?.tickRate ?? 64;

  // Nomes de time vindos do demo e mapa steamId -> time (A/B), constante na
  // partida. Permite colorir/agrupar por TIME mesmo após a troca de lado.
  const teamNames = useMemo<Record<TeamKey, string | null>>(
    () => ({ A: summaryQuery.data?.teamA ?? null, B: summaryQuery.data?.teamB ?? null }),
    [summaryQuery.data]
  );
  const teamKeyBySteam = useMemo(() => {
    const out = new Map<string, TeamKey>();
    for (const player of playersQuery.data ?? []) {
      if (teamNames.A && player.team === teamNames.A) {
        out.set(player.steamId, "A");
      } else if (teamNames.B && player.team === teamNames.B) {
        out.set(player.steamId, "B");
      }
    }
    return out;
  }, [playersQuery.data, teamNames]);
  const hasTeams = teamKeyBySteam.size > 0 && Boolean(teamNames.A) && Boolean(teamNames.B);

  // fps de origem: tick_rate / (delta médio de ticks entre frames).
  const sourceFps = useMemo(() => {
    if (frames.length < 2) {
      return 8;
    }
    const span = frames[frames.length - 1].tick - frames[0].tick;
    const avgDelta = span / (frames.length - 1);
    return avgDelta > 0 ? (tickRate || 64) / avgDelta : 8;
  }, [frames, tickRate]);

  useEffect(() => {
    setPlayhead(0);
    setPlaying(false);
  }, [round]);

  useEffect(() => {
    setPlayhead((value) => (value > totalFrames - 1 ? 0 : value));
  }, [totalFrames]);

  const lastTsRef = useRef<number | null>(null);
  useEffect(() => {
    if (!playing || totalFrames < 2) {
      return;
    }
    lastTsRef.current = null;
    let raf = 0;
    const step = (timestamp: number) => {
      if (lastTsRef.current === null) {
        lastTsRef.current = timestamp;
      }
      const dt = (timestamp - lastTsRef.current) / 1000;
      lastTsRef.current = timestamp;
      setPlayhead((value) => Math.min(totalFrames - 1, value + dt * sourceFps * speed));
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [playing, speed, totalFrames, sourceFps]);

  useEffect(() => {
    if (playing && totalFrames > 0 && playhead >= totalFrames - 1) {
      setPlaying(false);
    }
  }, [playing, playhead, totalFrames]);

  const availableRounds = useMemo(() => {
    const numbers = (roundsQuery.data ?? []).map((item) => item.roundNumber).sort((a, b) => a - b);
    return numbers.length > 0 ? numbers : [1];
  }, [roundsQuery.data]);

  // Frame base (lo) e próximo (hi) + fração para interpolar.
  const lo = Math.max(0, Math.min(Math.floor(playhead), frames.length - 1));
  const hi = Math.min(lo + 1, frames.length - 1);
  const t = playhead - lo;
  const baseFrame = frames[lo];
  const nextFrame = frames[hi];

  const interpolatedPlayers: ReplayPlayer[] = useMemo(() => {
    if (!baseFrame) {
      return [];
    }
    const nextById = new Map((nextFrame?.players ?? []).map((p) => [p.steamId, p]));
    return baseFrame.players.map((player) => {
      const target = nextById.get(player.steamId) ?? player;
      return {
        ...player,
        radarX: lerp(player.radarX, target.radarX, t),
        radarY: lerp(player.radarY, target.radarY, t),
        yaw: lerpAngle(player.yaw, target.yaw, t)
      };
    });
  }, [baseFrame, nextFrame, t]);

  const grenades = useMemo(() => replayQuery.data?.grenades ?? [], [replayQuery.data]);
  const currentTick = baseFrame
    ? baseFrame.tick + (nextFrame ? (nextFrame.tick - baseFrame.tick) * t : 0)
    : 0;
  const burstWindow = 0.4 * (tickRate || 64);

  const activeGrenades = useMemo(() => {
    const out: Array<{
      key: string;
      type: GrenadeType;
      state: "flying" | "active" | "burst";
      left: number;
      top: number;
      ox?: number;
      oy?: number;
      lx?: number;
      ly?: number;
    }> = [];
    grenades.forEach((g, index) => {
      const hasEnd = g.radarX !== null && g.radarY !== null;
      if (
        g.thrownTick !== null &&
        g.startRadarX !== null &&
        g.startRadarY !== null &&
        hasEnd &&
        currentTick >= g.thrownTick &&
        currentTick <= g.detonateTick &&
        g.detonateTick > g.thrownTick
      ) {
        const f = (currentTick - g.thrownTick) / (g.detonateTick - g.thrownTick);
        out.push({
          key: `fly-${index}`,
          type: g.type,
          state: "flying",
          ox: g.startRadarX,
          oy: g.startRadarY,
          lx: g.radarX as number,
          ly: g.radarY as number,
          left: lerp(g.startRadarX, g.radarX as number, f),
          top: lerp(g.startRadarY, g.radarY as number, f)
        });
      }
      if (!hasEnd) {
        return;
      }
      const isArea = ["smoke", "molotov", "incendiary", "decoy"].includes(g.type);
      if (isArea && currentTick >= g.detonateTick && currentTick <= g.expireTick) {
        out.push({ key: `area-${index}`, type: g.type, state: "active", left: g.radarX as number, top: g.radarY as number });
      }
      if ((g.type === "flash" || g.type === "he") && Math.abs(currentTick - g.detonateTick) <= burstWindow) {
        out.push({ key: `burst-${index}`, type: g.type, state: "burst", left: g.radarX as number, top: g.radarY as number });
      }
    });
    return out;
  }, [grenades, currentTick, burstWindow]);

  const flyingGrenades = activeGrenades.filter((g) => g.state === "flying");
  const settledGrenades = activeGrenades.filter((g) => g.state !== "flying");

  const timelineEvents = useMemo(() => {
    if (frames.length === 0) {
      return [];
    }
    const first = frames[0].tick;
    const last = frames[frames.length - 1].tick;
    const denom = Math.max(1, last - first);
    return frames
      .flatMap((frame) => frame.events)
      .map((event, index) => ({
        key: `${event.type}-${event.tick}-${index}`,
        type: event.type,
        grenadeType: event.grenadeType,
        position: Math.max(0, Math.min(100, ((event.tick - first) / denom) * 100))
      }));
  }, [frames]);

  function togglePlay() {
    if (frames.length === 0) {
      return;
    }
    if (playhead >= frames.length - 1) {
      setPlayhead(0);
    }
    setPlaying((value) => !value);
  }

  if (summaryQuery.isLoading) {
    return (
      <>
        <PageHeader eyebrow="Replay 2D" title="Replay 2D" description="Carregando…" />
        <p className="state-note">Carregando partida…</p>
      </>
    );
  }

  if (summaryQuery.isError || !summaryQuery.data) {
    return (
      <>
        <PageHeader eyebrow="Replay 2D" title="Replay 2D" description="Partida indisponível." />
        <p className="state-note" role="alert">
          Verifique se a partida foi processada e se o backend está no ar em{" "}
          <span className="mono">localhost:8000</span>.
        </p>
      </>
    );
  }

  const summary = summaryQuery.data;
  const teamAName = resolveTeamName("A", teamNames.A, settings);
  const teamBName = resolveTeamName("B", teamNames.B, settings);

  // Agrupa o roster por TIME (quando há nomes de time) ou por LADO (fallback).
  const rosterGroups = hasTeams
    ? (["A", "B"] as TeamKey[]).map((key) => {
        const members = (baseFrame?.players ?? []).filter(
          (player) => teamKeyBySteam.get(player.steamId) === key
        );
        const side = (members[0]?.side ?? "CT") as Side;
        return {
          id: key,
          header: resolveTeamName(key, teamNames[key], settings),
          side,
          badge: settings.colorMode === "side" ? null : side,
          color: resolveColor(side, key, settings),
          members
        };
      })
    : (["T", "CT"] as Side[]).map((side) => ({
        id: side,
        header: side === "T" ? "Lado T" : "Lado CT",
        side,
        badge: null,
        color: resolveColor(side, null, settings),
        members: (baseFrame?.players ?? []).filter((player) => player.side === side)
      }));

  return (
    <>
      <PageHeader
        eyebrow="Replay 2D"
        title={`${teamAName} x ${teamBName}`}
        description={`Mapa ${summary.map} · revisão round a round sobre o radar.`}
      />

      <div className="replay-controls">
        <label className="replay-field">
          Round
          <select value={round} onChange={(event) => setRound(Number(event.target.value))}>
            {availableRounds.map((number) => (
              <option key={number} value={number}>
                {number}
              </option>
            ))}
          </select>
        </label>

        <button className="button" type="button" onClick={togglePlay}>
          {playing ? "Pausar" : "Reproduzir"}
        </button>

        <div className="speed-group" role="group" aria-label="Velocidade">
          {SPEEDS.map((value) => (
            <button
              className="button small"
              data-active={value === speed}
              key={value}
              type="button"
              onClick={() => setSpeed(value)}
            >
              {value}x
            </button>
          ))}
        </div>

        <span className="replay-counter">
          {frames.length > 0 ? Math.floor(playhead) + 1 : 0}/{frames.length}
        </span>

        <div className="replay-team-tools">
          <div className="speed-group" role="group" aria-label="Cor dos marcadores">
            <button
              className="button small"
              data-active={settings.colorMode === "team"}
              type="button"
              onClick={() => setSettings({ ...settings, colorMode: "team" })}
            >
              Cor: Time
            </button>
            <button
              className="button small"
              data-active={settings.colorMode === "side"}
              type="button"
              onClick={() => setSettings({ ...settings, colorMode: "side" })}
            >
              Cor: Lado
            </button>
          </div>
          <button className="button small" type="button" onClick={() => setShowTeamEditor((v) => !v)}>
            {showTeamEditor ? "Fechar" : "Editar times"}
          </button>
        </div>
      </div>

      {showTeamEditor ? (
        <ReplayTeamEditor
          settings={settings}
          teamNames={teamNames}
          hasTeams={hasTeams}
          onChange={setSettings}
        />
      ) : null}

      <input
        className="replay-scrubber"
        type="range"
        min={0}
        max={Math.max(0, frames.length - 1)}
        step={0.01}
        value={Math.min(playhead, Math.max(0, frames.length - 1))}
        aria-label="Linha do tempo do round"
        onChange={(event) => {
          setPlayhead(Number(event.target.value));
          setPlaying(false);
        }}
      />

      <div className="replay-timeline" aria-hidden="true">
        {timelineEvents.map((event) => (
          <span
            className="timeline-mark"
            data-type={event.type}
            data-grenade={event.grenadeType ?? ""}
            key={event.key}
            style={{ left: `${event.position}%` }}
          />
        ))}
        {frames.length > 1 ? (
          <span
            className="timeline-cursor"
            style={{ left: `${(playhead / (frames.length - 1)) * 100}%` }}
          />
        ) : null}
      </div>

      <section className="replay-stage" aria-label="Replay">
        <div className="replay-canvas-wrap panel">
          <div
            className="replay-canvas"
            style={radarUrl ? { backgroundImage: `url("${radarUrl}")` } : undefined}
          >
            {replayQuery.isLoading ? (
              <p className="replay-overlay-note">Carregando frames…</p>
            ) : frames.length === 0 ? (
              <p className="replay-overlay-note">Sem frames para este round.</p>
            ) : (
              <>
                <svg
                  className="replay-grenade-trails"
                  viewBox={`0 0 ${imageWidth} ${imageHeight}`}
                  preserveAspectRatio="none"
                  aria-hidden="true"
                >
                  {flyingGrenades.map((grenade) => (
                    <line
                      key={`trail-${grenade.key}`}
                      x1={grenade.ox ?? 0}
                      y1={grenade.oy ?? 0}
                      x2={grenade.lx ?? 0}
                      y2={grenade.ly ?? 0}
                      stroke={GRENADE_COLORS[grenade.type]}
                      strokeWidth={5}
                      strokeDasharray="10 9"
                      strokeLinecap="round"
                      opacity={0.75}
                    />
                  ))}
                </svg>

                {settledGrenades.map((grenade) => (
                  <span
                    className="replay-grenade"
                    data-type={grenade.type}
                    data-state={grenade.state}
                    key={grenade.key}
                    style={{
                      left: `${(grenade.left / imageWidth) * 100}%`,
                      top: `${(grenade.top / imageHeight) * 100}%`
                    }}
                  />
                ))}

                {flyingGrenades.map((grenade) => (
                  <span
                    className="replay-grenade-icon"
                    key={grenade.key}
                    style={{
                      left: `${(grenade.left / imageWidth) * 100}%`,
                      top: `${(grenade.top / imageHeight) * 100}%`
                    }}
                  >
                    <GrenadeIcon type={grenade.type} />
                  </span>
                ))}

                {baseFrame?.events
                  .filter((event) => event.radarX !== null && event.radarY !== null)
                  .map((event, index) => (
                    <span
                      className="replay-event"
                      data-type={event.type}
                      data-grenade={event.grenadeType ?? ""}
                      key={`${event.type}-${event.tick}-${index}`}
                      style={{
                        left: `${((event.radarX ?? 0) / imageWidth) * 100}%`,
                        top: `${((event.radarY ?? 0) / imageHeight) * 100}%`
                      }}
                      title={event.grenadeType ? `${event.type} (${event.grenadeType})` : event.type}
                    />
                  ))}

                {interpolatedPlayers
                  .filter((player) => player.alive)
                  .map((player) => {
                    const color = resolveColor(
                      player.side,
                      teamKeyBySteam.get(player.steamId) ?? null,
                      settings
                    );
                    return (
                      <div
                        className="replay-player"
                        data-side={player.side}
                        data-blinded={player.blinded ? "true" : undefined}
                        key={player.steamId}
                        style={{
                          left: `${(player.radarX / imageWidth) * 100}%`,
                          top: `${(player.radarY / imageHeight) * 100}%`,
                          color
                        }}
                        title={`${player.name} · ${player.weapon} · ${player.hp} HP`}
                      >
                        {player.yaw !== null ? (
                          <span
                            className="replay-aim"
                            // yaw é o ângulo do mundo (0=+X, anti-horário) e o radar
                            // espelha o eixo Y; a linha aponta para "cima" em rotate(0),
                            // então a rotação correta na tela é (90 - yaw). Verificado
                            // contra ~200 kills (erro mediano ~0,4°).
                            style={{ transform: `translate(-50%, -100%) rotate(${90 - player.yaw}deg)` }}
                          />
                        ) : null}
                        <span className="replay-dot" />
                        <span className="replay-name">{shorten(player.name)}</span>
                      </div>
                    );
                  })}
              </>
            )}
          </div>
        </div>

        <aside className="replay-roster panel" aria-label="Jogadores">
          {rosterGroups.map((group) => (
            <div className="roster-team" data-side={group.side} key={group.id}>
              <h3 style={{ color: group.color }}>
                {group.header}
                {group.badge ? <small className="roster-side-badge"> · {group.badge}</small> : null}
              </h3>
              {group.members.length === 0 ? (
                <p className="state-note">—</p>
              ) : (
                <ul className="roster-list">
                  {group.members.map((player) => (
                    <li className="roster-row" data-alive={player.alive} key={player.steamId}>
                      <div className="roster-main">
                        <strong>{shorten(player.name)}</strong>
                        <small>{player.weapon || "—"}</small>
                      </div>
                      <div className="hp-bar" aria-label={`${player.hp} HP`}>
                        <span
                          className="hp-fill"
                          style={{ width: `${Math.max(0, Math.min(100, player.hp))}%` }}
                        />
                      </div>
                      <span className="roster-hp">{player.alive ? player.hp : "☠"}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </aside>
      </section>
    </>
  );
}
