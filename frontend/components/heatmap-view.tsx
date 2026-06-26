"use client";

import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { DEFAULT_API_BASE_URL } from "@/lib/api";
import {
  useDeathPositionsQuery,
  useHeatmapQuery,
  useMapMetadataQuery,
  useMatchesQuery,
  usePlayerStatsQuery
} from "@/lib/queries";
import type { HeatmapType } from "@/lib/types";

const TYPES: Array<{ value: HeatmapType; label: string }> = [
  { value: "kills", label: "Kills" },
  { value: "deaths", label: "Deaths" },
  { value: "path", label: "Pathing" },
  { value: "utility", label: "Utility" },
  { value: "grenades", label: "Grenades" }
];

const GRENADES = ["he", "flash", "smoke", "molotov", "decoy"];

export function HeatmapView() {
  const matchesQuery = useMatchesQuery();
  const matches = useMemo(() => matchesQuery.data ?? [], [matchesQuery.data]);

  const [matchId, setMatchId] = useState("");
  const [type, setType] = useState<HeatmapType>("kills");
  const [player, setPlayer] = useState("");
  const [team, setTeam] = useState("");
  const [side, setSide] = useState("");
  const [roundRange, setRoundRange] = useState("");
  const [grenadeType, setGrenadeType] = useState("");

  useEffect(() => {
    if (!matchId && matches.length > 0) {
      setMatchId(matches[0].id);
    }
  }, [matchId, matches]);

  const selectedMatch = matches.find((match) => match.id === matchId);
  const map = selectedMatch?.map ?? "";
  const metadataQuery = useMapMetadataQuery(map);
  const playerStatsQuery = usePlayerStatsQuery(matchId);
  const players = playerStatsQuery.data?.players ?? [];
  const teams = Array.from(
    new Set(players.map((item) => item.team).filter((value): value is string => Boolean(value)))
  );

  const deathsMode = type === "deaths" && player !== "";
  const showGrenadeFilter = type === "utility" || type === "grenades";

  const heatmapQuery = useHeatmapQuery(
    matchId,
    {
      type,
      player: player || undefined,
      team: team || undefined,
      side: side || undefined,
      roundRange: roundRange || undefined,
      grenadeType: showGrenadeFilter ? grenadeType || undefined : undefined
    },
    !deathsMode
  );
  const deathQuery = useDeathPositionsQuery(matchId, player, deathsMode);

  const imageWidth = metadataQuery.data?.imageWidth ?? 1024;
  const imageHeight = metadataQuery.data?.imageHeight ?? 1024;
  const radarUrl = map ? `${DEFAULT_API_BASE_URL}/maps/${encodeURIComponent(map)}/radar` : "";

  const points = deathsMode
    ? (deathQuery.data?.deaths ?? []).map((death) => ({ radarX: death.radarX, radarY: death.radarY }))
    : (heatmapQuery.data?.points ?? []).map((point) => ({ radarX: point.radarX, radarY: point.radarY }));
  const topSpot = deathsMode ? deathQuery.data?.topSpot ?? null : null;

  const isLoading = deathsMode ? deathQuery.isLoading : heatmapQuery.isLoading;
  const isError = deathsMode ? deathQuery.isError : heatmapQuery.isError;

  return (
    <>
      <PageHeader
        eyebrow="Heatmaps"
        title="Mapas de calor sobre o radar."
        description="Kills, deaths, pathing, utility e granadas — com filtros por player, time, lado, rounds e tipo de granada."
      />

      <div className="heat-filters panel">
        <label className="replay-field">
          Partida
          <select value={matchId} onChange={(event) => setMatchId(event.target.value)}>
            {matches.length === 0 ? <option value="">—</option> : null}
            {matches.map((match) => (
              <option key={match.id} value={match.id}>
                {(match.teamA ?? "Time A")} x {(match.teamB ?? "Time B")} · {match.map}
              </option>
            ))}
          </select>
        </label>

        <label className="replay-field">
          Tipo
          <select value={type} onChange={(event) => setType(event.target.value as HeatmapType)}>
            {TYPES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="replay-field">
          Player
          <select value={player} onChange={(event) => setPlayer(event.target.value)}>
            <option value="">Todos</option>
            {players.map((item) => (
              <option key={item.steamId} value={item.steamId}>
                {item.name ?? item.steamId.slice(-5)}
              </option>
            ))}
          </select>
        </label>

        <label className="replay-field">
          Time
          <select value={team} onChange={(event) => setTeam(event.target.value)}>
            <option value="">Todos</option>
            {teams.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>

        <label className="replay-field">
          Lado
          <select value={side} onChange={(event) => setSide(event.target.value)}>
            <option value="">Ambos</option>
            <option value="CT">CT</option>
            <option value="T">T</option>
          </select>
        </label>

        <label className="replay-field">
          Rounds
          <input
            type="text"
            value={roundRange}
            placeholder="ex.: 1-12"
            onChange={(event) => setRoundRange(event.target.value)}
          />
        </label>

        {showGrenadeFilter ? (
          <label className="replay-field">
            Granada
            <select value={grenadeType} onChange={(event) => setGrenadeType(event.target.value)}>
              <option value="">Todas</option>
              {GRENADES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </div>

      <section className="replay-stage" aria-label="Heatmap">
        <div className="replay-canvas-wrap panel">
          <div
            className="replay-canvas"
            style={radarUrl ? { backgroundImage: `url("${radarUrl}")` } : undefined}
          >
            {!matchId ? (
              <p className="replay-overlay-note">Nenhuma partida processada.</p>
            ) : isLoading ? (
              <p className="replay-overlay-note">Carregando heatmap…</p>
            ) : isError ? (
              <p className="replay-overlay-note" role="alert">
                Erro ao carregar. Verifique o backend.
              </p>
            ) : points.length === 0 ? (
              <p className="replay-overlay-note">Sem pontos para os filtros atuais.</p>
            ) : (
              <>
                {points.map((point, index) => (
                  <span
                    className="heat-point"
                    data-type={type}
                    key={index}
                    style={{
                      left: `${(point.radarX / imageWidth) * 100}%`,
                      top: `${(point.radarY / imageHeight) * 100}%`
                    }}
                  />
                ))}
                {topSpot ? (
                  <span
                    className="heat-topspot"
                    style={{
                      left: `${(topSpot.radarX / imageWidth) * 100}%`,
                      top: `${(topSpot.radarY / imageHeight) * 100}%`
                    }}
                    title={`Top spot · ${topSpot.count} mortes`}
                  >
                    <small>top spot ({topSpot.count})</small>
                  </span>
                ) : null}
              </>
            )}
          </div>
        </div>

        <aside className="replay-roster panel" aria-label="Resumo do heatmap">
          <div className="roster-team">
            <h3>Resumo</h3>
            <ul className="data-list">
              <li className="data-row">
                <div className="data-main">
                  <strong>{TYPES.find((option) => option.value === type)?.label}</strong>
                  <small>{points.length} pontos</small>
                </div>
              </li>
              {deathsMode ? (
                <li className="data-row">
                  <div className="data-main">
                    <strong>Posições de morte</strong>
                    <small>
                      {topSpot ? `top spot: ${topSpot.count} mortes` : "sem cluster destacado"}
                    </small>
                  </div>
                </li>
              ) : null}
            </ul>
            <p className="state-note">
              Para o mapa de movimento, escolha <strong>Pathing</strong> + um player. Para a posição
              de morte #1, escolha <strong>Deaths</strong> + um player.
            </p>
          </div>
        </aside>
      </section>
    </>
  );
}
