"use client";

import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { DEFAULT_API_BASE_URL } from "@/lib/api";
import {
  useMapMetadataQuery,
  useMatchRoundsQuery,
  useMatchSummaryQuery,
  useReplayQuery
} from "@/lib/queries";

const SPEEDS = [0.25, 0.5, 1, 2, 4];
const SAMPLE_RATE = 8;

function shorten(name: string): string {
  return name.length > 9 ? `${name.slice(0, 8)}…` : name;
}

export function Replay2D({ matchId }: { matchId: string }) {
  const summaryQuery = useMatchSummaryQuery(matchId);
  const roundsQuery = useMatchRoundsQuery(matchId);
  const map = summaryQuery.data?.map ?? "";
  const metadataQuery = useMapMetadataQuery(map);

  const [round, setRound] = useState(1);
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  const replayQuery = useReplayQuery(matchId, round, SAMPLE_RATE);
  const frames = useMemo(() => replayQuery.data?.frames ?? [], [replayQuery.data]);

  const imageWidth = metadataQuery.data?.imageWidth ?? 1024;
  const imageHeight = metadataQuery.data?.imageHeight ?? 1024;
  const radarUrl = map ? `${DEFAULT_API_BASE_URL}/maps/${encodeURIComponent(map)}/radar` : "";

  useEffect(() => {
    setFrameIndex(0);
    setPlaying(false);
  }, [round]);

  useEffect(() => {
    setFrameIndex((index) => (index > frames.length - 1 ? 0 : index));
  }, [frames.length]);

  useEffect(() => {
    if (!playing || frames.length === 0) {
      return;
    }
    const interval = setInterval(() => {
      setFrameIndex((index) => (index >= frames.length - 1 ? index : index + 1));
    }, Math.max(30, Math.round(110 / speed)));
    return () => clearInterval(interval);
  }, [playing, speed, frames.length]);

  useEffect(() => {
    if (playing && frames.length > 0 && frameIndex >= frames.length - 1) {
      setPlaying(false);
    }
  }, [playing, frameIndex, frames.length]);

  const availableRounds = useMemo(() => {
    const numbers = (roundsQuery.data ?? []).map((item) => item.roundNumber).sort((a, b) => a - b);
    return numbers.length > 0 ? numbers : [1];
  }, [roundsQuery.data]);

  const currentFrame = frames[Math.min(frameIndex, Math.max(0, frames.length - 1))];

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
    if (frameIndex >= frames.length - 1) {
      setFrameIndex(0);
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
          {frames.length > 0 ? frameIndex + 1 : 0}/{frames.length}
        </span>
      </div>

      <input
        className="replay-scrubber"
        type="range"
        min={0}
        max={Math.max(0, frames.length - 1)}
        value={Math.min(frameIndex, Math.max(0, frames.length - 1))}
        aria-label="Linha do tempo do round"
        onChange={(event) => {
          setFrameIndex(Number(event.target.value));
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
            style={{ left: `${(frameIndex / (frames.length - 1)) * 100}%` }}
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
                {currentFrame?.events
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

                {currentFrame?.players
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
            const roster = (currentFrame?.players ?? []).filter((player) => player.side === team.side);
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
