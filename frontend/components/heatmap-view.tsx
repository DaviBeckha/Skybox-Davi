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

  const heatPoints = (heatmapQuery.data?.points ?? []).map((point) => ({
    radarX: point.radarX,
    radarY: point.radarY
  }));
  const rawDeaths = deathQuery.data?.deaths ?? [];

  const isLoading = deathsMode ? deathQuery.isLoading : heatmapQuery.isLoading;
  const isError = deathsMode ? deathQuery.isError : heatmapQuery.isError;

  const nameOf = (steamId: string) =>
    players.find((item) => item.steamId === steamId)?.name ?? steamId.slice(-5);

  type DeathCluster = {
    key: string;
    radarX: number;
    radarY: number;
    count: number;
    attackers: { label: string; count: number }[];
    weapons: { label: string; count: number }[];
    rounds: number[];
  };

  // Deaths + player: agrupamos as mortes na mesma grade de 128u que o backend usa
  // no top spot, respondendo "quantas vezes morreu aqui" e "quem matou".
  const deathClusters: DeathCluster[] = !deathsMode
    ? []
    : (() => {
        const groups = new Map<string, { rx: number; ry: number; deaths: typeof rawDeaths }>();
        for (const death of rawDeaths) {
          const key = `${Math.round(death.x / 128)},${Math.round(death.y / 128)}`;
          const group = groups.get(key) ?? { rx: 0, ry: 0, deaths: [] };
          group.rx += death.radarX;
          group.ry += death.radarY;
          group.deaths.push(death);
          groups.set(key, group);
        }
        const tally = (items: string[]) => {
          const counts = new Map<string, number>();
          for (const item of items) counts.set(item, (counts.get(item) ?? 0) + 1);
          return [...counts.entries()]
            .map(([label, count]) => ({ label, count }))
            .sort((a, b) => b.count - a.count);
        };
        return [...groups.entries()]
          .map(([key, group]) => ({
            key,
            radarX: group.rx / group.deaths.length,
            radarY: group.ry / group.deaths.length,
            count: group.deaths.length,
            attackers: tally(group.deaths.map((death) => nameOf(death.attackerSteamId))),
            weapons: tally(group.deaths.map((death) => death.weapon)),
            rounds: [...new Set(group.deaths.map((death) => death.roundNumber))].sort((a, b) => a - b)
          }))
          .sort((a, b) => b.count - a.count);
      })();

  const listText = (items: { label: string; count: number }[]) =>
    items.map((item) => `${item.label}${item.count > 1 ? ` ×${item.count}` : ""}`).join(", ");
  const clusterAria = (cluster: DeathCluster) =>
    `Morreu ${cluster.count} ${cluster.count === 1 ? "vez" : "vezes"} aqui; ` +
    `morto por ${listText(cluster.attackers)}; armas ${listText(cluster.weapons)}; ` +
    `rounds ${cluster.rounds.join(", ")}`;
  const clusterTitle = (cluster: DeathCluster) =>
    `Morreu ${cluster.count}× aqui\nMorto por: ${listText(cluster.attackers)}\n` +
    `Armas: ${listText(cluster.weapons)}\nRounds: ${cluster.rounds.join(", ")}`;

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
            ) : deathsMode ? (
              deathClusters.length === 0 ? (
                <p className="replay-overlay-note">Este player não tem mortes registradas.</p>
              ) : (
                deathClusters.map((cluster, index) => (
                  <span
                    aria-label={clusterAria(cluster)}
                    className="death-cluster"
                    data-top={index === 0 ? "true" : undefined}
                    key={cluster.key}
                    style={{
                      left: `${(cluster.radarX / imageWidth) * 100}%`,
                      top: `${(cluster.radarY / imageHeight) * 100}%`
                    }}
                    title={clusterTitle(cluster)}
                  >
                    {cluster.count}
                  </span>
                ))
              )
            ) : heatPoints.length === 0 ? (
              <p className="replay-overlay-note">Sem pontos para os filtros atuais.</p>
            ) : (
              <>
                {heatPoints.map((point, index) => (
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
              </>
            )}
          </div>
        </div>

        <aside className="replay-roster panel" aria-label="Resumo do heatmap">
          {deathsMode ? (
            <div className="roster-team">
              <h3>Posições de morte</h3>
              {deathClusters.length === 0 ? (
                <p className="state-note">Sem mortes registradas para este player.</p>
              ) : (
                <>
                  <p className="death-summary">
                    <strong>{rawDeaths.length}</strong> mortes em{" "}
                    <strong>{deathClusters.length}</strong>{" "}
                    {deathClusters.length === 1 ? "posição" : "posições"}
                  </p>
                  <ol className="death-rank">
                    {deathClusters.map((cluster, index) => (
                      <li
                        className="death-rank-row"
                        data-top={index === 0 ? "true" : undefined}
                        key={cluster.key}
                      >
                        <span className="death-rank-badge">{cluster.count}×</span>
                        <div className="death-rank-main">
                          <strong>{index === 0 ? "Top spot" : `Posição ${index + 1}`}</strong>
                          <small>por {listText(cluster.attackers)}</small>
                          <small className="death-rank-meta">
                            {listText(cluster.weapons)} · rounds {cluster.rounds.join(", ")}
                          </small>
                        </div>
                      </li>
                    ))}
                  </ol>
                </>
              )}
            </div>
          ) : (
            <div className="roster-team">
              <h3>Resumo</h3>
              <ul className="data-list">
                <li className="data-row">
                  <div className="data-main">
                    <strong>{TYPES.find((option) => option.value === type)?.label}</strong>
                    <small>{heatPoints.length} pontos</small>
                  </div>
                </li>
              </ul>
              <p className="state-note">
                Para o mapa de movimento, escolha <strong>Pathing</strong> + um player. Para ver onde
                um player morreu, escolha <strong>Deaths</strong> + um player.
              </p>
            </div>
          )}
        </aside>
      </section>
    </>
  );
}
