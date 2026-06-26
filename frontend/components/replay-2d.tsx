"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { DEFAULT_API_BASE_URL } from "@/lib/api";
import {
  useMapMetadataQuery,
  useMatchRoundsQuery,
  useMatchSummaryQuery,
  useReplayQuery
} from "@/lib/queries";
import type { ReplayPlayer } from "@/lib/types";

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
  const map = summaryQuery.data?.map ?? "";
  const metadataQuery = useMapMetadataQuery(map);

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
  const teams: Array<{ side: "T" | "CT"; label: string }> = [
    { side: "T", label: "Lado T" },
    { side: "CT", label: "Lado CT" }
  ];

  return (
    <>
      <PageHeader
        eyebrow="Replay 2D"
        title={`${summary.teamA ?? "Time A"} x ${summary.teamB ?? "Time B"}`}
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
      </div>

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
                  .map((player) => (
                    <div
                      className="replay-player"
                      data-side={player.side}
                      key={player.steamId}
                      style={{
                        left: `${(player.radarX / imageWidth) * 100}%`,
                        top: `${(player.radarY / imageHeight) * 100}%`
                      }}
                      title={`${player.name} · ${player.weapon} · ${player.hp} HP`}
                    >
                      {player.yaw !== null ? (
                        <span
                          className="replay-aim"
                          style={{ transform: `translate(-50%, -100%) rotate(${-player.yaw}deg)` }}
                        />
                      ) : null}
                      <span className="replay-dot" />
                      <span className="replay-name">{shorten(player.name)}</span>
                    </div>
                  ))}
              </>
            )}
          </div>
        </div>

        <aside className="replay-roster panel" aria-label="Jogadores">
          {teams.map((team) => {
            const roster = (baseFrame?.players ?? []).filter((player) => player.side === team.side);
            return (
              <div className="roster-team" data-side={team.side} key={team.side}>
                <h3>{team.label}</h3>
                {roster.length === 0 ? (
                  <p className="state-note">—</p>
                ) : (
                  <ul className="roster-list">
                    {roster.map((player) => (
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
            );
          })}
        </aside>
      </section>
    </>
  );
}
