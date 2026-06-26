"use client";

import { useState } from "react";

import { BarChart } from "@/components/bar-chart";
import { type Column, DataTable } from "@/components/data-table";
import { PageHeader } from "@/components/page-header";
import { type TabItem, Tabs } from "@/components/tabs";
import {
  useBombsiteStatsQuery,
  useMatchRoundsQuery,
  useMatchSummaryQuery,
  useMatchupsQuery,
  usePlayerStatsQuery,
  useUtilityStatsQuery,
  useWeaponStatsQuery
} from "@/lib/queries";
import type {
  BombsiteStats,
  PlayerCoreStats,
  PlayerWeaponStats,
  UtilityStats,
  WeaponStats
} from "@/lib/types";

const pct = (value: number) => `${Math.round(value * 100)}%`;
const ratio = (num: number, den: number) => (den === 0 ? num.toFixed(2) : (num / den).toFixed(2));

export function MatchReport({ matchId }: { matchId: string }) {
  const summaryQuery = useMatchSummaryQuery(matchId);
  const roundsQuery = useMatchRoundsQuery(matchId);
  const playerStatsQuery = usePlayerStatsQuery(matchId);
  const utilityQuery = useUtilityStatsQuery(matchId);
  const matchupsQuery = useMatchupsQuery(matchId);
  const weaponsQuery = useWeaponStatsQuery(matchId);
  const bombsitesQuery = useBombsiteStatsQuery(matchId);
  const [duelPlayer, setDuelPlayer] = useState("");

  if (summaryQuery.isLoading) {
    return (
      <>
        <PageHeader eyebrow="Match report" title="Relatório da partida" description="Carregando…" />
        <p className="state-note">Carregando relatório…</p>
      </>
    );
  }

  if (summaryQuery.isError || !summaryQuery.data) {
    return (
      <>
        <PageHeader
          eyebrow="Match report"
          title="Relatório da partida"
          description="Não foi possível carregar a partida."
        />
        <p className="state-note" role="alert">
          Verifique se a partida foi processada e se o backend está no ar em{" "}
          <span className="mono">localhost:8000</span>.
        </p>
      </>
    );
  }

  const summary = summaryQuery.data;
  const rounds = roundsQuery.data ?? [];
  const playerStats = playerStatsQuery.data?.players ?? [];
  const utility = utilityQuery.data?.players ?? [];
  const weapons = weaponsQuery.data?.players ?? [];
  const bombsites = bombsitesQuery.data?.sites ?? [];

  const nameBySteam = new Map<string, string>();
  for (const player of playerStats) {
    nameBySteam.set(player.steamId, player.name ?? player.steamId);
  }
  const teamLabel = (team: string | null) => (team === summary.teamA ? "a" : team === summary.teamB ? "b" : "");
  const label = (steamId: string) => nameBySteam.get(steamId) ?? steamId.slice(-5);

  const matrixPlayers = matchupsQuery.data?.players ?? [];
  const killLookup = new Map<string, number>();
  for (const entry of matchupsQuery.data?.matrix ?? []) {
    killLookup.set(`${entry.attackerSteamId}|${entry.victimSteamId}`, entry.kills);
  }

  // Duelos por jogador: escolhe-se um player e vê-se o confronto direto (a favor /
  // contra) contra cada ADVERSÁRIO. Comparar colegas de time não faz sentido, então
  // filtramos pelo time (quando conhecido).
  const teamBySteam = new Map<string, string | null>();
  for (const player of playerStats) {
    teamBySteam.set(player.steamId, player.team ?? null);
  }
  const duelOptions = matrixPlayers
    .map((steamId) => ({ steamId, name: label(steamId), team: teamBySteam.get(steamId) ?? null }))
    .sort((a, b) => (a.team ?? "").localeCompare(b.team ?? "") || a.name.localeCompare(b.name));
  const selectedDuelPlayer = duelPlayer || duelOptions[0]?.steamId || "";
  const selectedTeam = teamBySteam.get(selectedDuelPlayer) ?? null;
  const duels = matrixPlayers
    .filter((opp) => opp !== selectedDuelPlayer)
    .filter((opp) => {
      const oppTeam = teamBySteam.get(opp) ?? null;
      // só adversários quando há time conhecido dos dois; senão mostra todos.
      return selectedTeam && oppTeam ? oppTeam !== selectedTeam : true;
    })
    .map((opp) => {
      const kills = killLookup.get(`${selectedDuelPlayer}|${opp}`) ?? 0;
      const deaths = killLookup.get(`${opp}|${selectedDuelPlayer}`) ?? 0;
      return { opp, kills, deaths, diff: kills - deaths };
    })
    .sort((a, b) => b.diff - a.diff || b.kills + b.deaths - (a.kills + a.deaths));
  const duelTotals = duels.reduce(
    (acc, duel) => ({ kills: acc.kills + duel.kills, deaths: acc.deaths + duel.deaths }),
    { kills: 0, deaths: 0 }
  );
  const duelBalance = duelTotals.kills - duelTotals.deaths;
  const fmtDiff = (value: number) => (value > 0 ? `+${value}` : `${value}`);
  const posAttr = (value: number) => (value > 0 ? "true" : value < 0 ? "false" : undefined);

  const killsChart = [...playerStats]
    .sort((a, b) => b.kills - a.kills)
    .map((player) => ({ label: player.name ?? player.steamId.slice(-5), value: player.kills }));

  const bombsiteChart = bombsites.map((site) => ({
    label: `${site.team} · ${site.site}`,
    value: Math.round(site.winRate * 100),
    display: pct(site.winRate)
  }));

  const teamChip = (team: string | null) => (
    <span className="team-chip" data-team={teamLabel(team)}>
      {team ?? "—"}
    </span>
  );

  const playerColumns: Column<PlayerCoreStats>[] = [
    {
      key: "name",
      header: "Jogador",
      sortable: true,
      value: (p) => p.name ?? p.steamId,
      render: (p) => (
        <span className="cell-player">
          <strong>{p.name ?? p.steamId.slice(-5)}</strong>
          {teamChip(p.team)}
        </span>
      )
    },
    { key: "kills", header: "K", numeric: true, sortable: true, value: (p) => p.kills },
    { key: "deaths", header: "D", numeric: true, sortable: true, value: (p) => p.deaths },
    { key: "assists", header: "A", numeric: true, sortable: true, value: (p) => p.assists },
    {
      key: "kd",
      header: "K/D",
      numeric: true,
      sortable: true,
      value: (p) => (p.deaths === 0 ? p.kills : p.kills / p.deaths),
      render: (p) => ratio(p.kills, p.deaths)
    },
    {
      key: "adr",
      header: "ADR",
      numeric: true,
      sortable: true,
      value: (p) => p.adr,
      render: (p) => p.adr.toFixed(1)
    },
    {
      key: "kast",
      header: "KAST",
      numeric: true,
      sortable: true,
      value: (p) => p.kastPct,
      render: (p) => pct(p.kastPct)
    },
    {
      key: "entry",
      header: "Entry K/D",
      numeric: true,
      sortable: true,
      value: (p) => p.entryKills,
      render: (p) => `${p.entryKills}/${p.entryDeaths}`
    },
    { key: "trade", header: "Trade", numeric: true, sortable: true, value: (p) => p.tradeKills },
    { key: "clutch", header: "Clutch", numeric: true, sortable: true, value: (p) => p.clutches }
  ];

  const utilityColumns: Column<UtilityStats>[] = [
    {
      key: "name",
      header: "Jogador",
      sortable: true,
      value: (u) => u.name ?? u.steamId,
      render: (u) => <strong>{u.name ?? u.steamId.slice(-5)}</strong>
    },
    { key: "he", header: "HE", numeric: true, sortable: true, value: (u) => u.grenadesThrown.he },
    { key: "flash", header: "Flash", numeric: true, sortable: true, value: (u) => u.grenadesThrown.flash },
    { key: "smoke", header: "Smoke", numeric: true, sortable: true, value: (u) => u.grenadesThrown.smoke },
    { key: "molotov", header: "Molotov", numeric: true, sortable: true, value: (u) => u.grenadesThrown.molotov },
    { key: "decoy", header: "Decoy", numeric: true, sortable: true, value: (u) => u.grenadesThrown.decoy },
    { key: "total", header: "Total", numeric: true, sortable: true, value: (u) => u.grenadesThrown.total },
    { key: "heDmgCount", header: "HE c/ dano", numeric: true, sortable: true, value: (u) => u.heWithDamage },
    { key: "heDmg", header: "Dano HE", numeric: true, sortable: true, value: (u) => u.heDamageTotal },
    { key: "molyDmg", header: "Dano molly", numeric: true, sortable: true, value: (u) => u.molotovDamageTotal },
    { key: "blinded", header: "Cegou", numeric: true, sortable: true, value: (u) => u.enemiesBlinded },
    {
      key: "blindTime",
      header: "Tempo cegueira",
      numeric: true,
      sortable: true,
      value: (u) => u.enemyBlindTime,
      render: (u) => `${u.enemyBlindTime.toFixed(1)}s`
    },
    { key: "fa", header: "Flash assists", numeric: true, sortable: true, value: (u) => u.flashAssists }
  ];

  const weaponColumns: Column<WeaponStats>[] = [
    { key: "weapon", header: "Arma", sortable: true, value: (w) => w.weapon },
    { key: "shots", header: "Disparos", numeric: true, sortable: true, value: (w) => w.shots },
    { key: "hits", header: "Hits", numeric: true, sortable: true, value: (w) => w.hits },
    { key: "acc", header: "Acc", numeric: true, sortable: true, value: (w) => w.accuracy, render: (w) => pct(w.accuracy) },
    { key: "kills", header: "Kills", numeric: true, sortable: true, value: (w) => w.kills },
    { key: "hs", header: "HS", numeric: true, sortable: true, value: (w) => w.headshots },
    { key: "hsPct", header: "HS%", numeric: true, sortable: true, value: (w) => w.hsPct, render: (w) => pct(w.hsPct) },
    { key: "damage", header: "Dano", numeric: true, sortable: true, value: (w) => w.damage }
  ];

  const bombsiteColumns: Column<BombsiteStats>[] = [
    { key: "team", header: "Time", sortable: true, value: (b) => b.team, render: (b) => teamChip(b.team) },
    { key: "site", header: "Site", sortable: true, value: (b) => b.site },
    { key: "plants", header: "Plants", numeric: true, sortable: true, value: (b) => b.plants },
    { key: "wins", header: "Wins", numeric: true, sortable: true, value: (b) => b.roundWins },
    { key: "winRate", header: "Win rate", numeric: true, sortable: true, value: (b) => b.winRate, render: (b) => pct(b.winRate) },
    {
      key: "postPlant",
      header: "Pós-plant",
      numeric: true,
      sortable: true,
      value: (b) => b.postPlantWinRate,
      render: (b) => pct(b.postPlantWinRate)
    }
  ];

  const weaponPlayerKey = (player: PlayerWeaponStats) => player.steamId;

  const tabs: TabItem[] = [
    {
      id: "overview",
      label: "Visão geral",
      content: (
        <section className="surface-grid">
          <article className="panel full">
            <div className="panel-head">
              <h2>Rounds</h2>
              <span>{rounds.length} no total</span>
            </div>
            {rounds.length === 0 ? (
              <p className="state-note">Sem rounds registrados.</p>
            ) : (
              <div className="rounds-strip">
                {[...rounds]
                  .sort((a, b) => a.roundNumber - b.roundNumber)
                  .map((round) => (
                    <span
                      className="round-chip"
                      data-side={round.winner ?? "none"}
                      key={round.roundNumber}
                      title={`Round ${round.roundNumber}: ${round.winner ?? "?"} (${round.reason ?? "—"})`}
                    >
                      {round.roundNumber}
                    </span>
                  ))}
              </div>
            )}
          </article>

          <article className="panel half">
            <div className="panel-head">
              <h2>Kills por jogador</h2>
              <span>gráfico</span>
            </div>
            <BarChart data={killsChart} />
          </article>

          <article className="panel half">
            <div className="panel-head">
              <h2>Win rate por bombsite</h2>
              <span>A vs B</span>
            </div>
            {bombsiteChart.length === 0 ? (
              <p className="state-note">Sem plants registrados.</p>
            ) : (
              <BarChart data={bombsiteChart} max={100} />
            )}
          </article>
        </section>
      )
    },
    {
      id: "players",
      label: "Jogadores",
      content: (
        <article className="panel full">
          <div className="panel-head">
            <h2>Jogadores</h2>
            <span>clique nos cabeçalhos para ordenar</span>
          </div>
          <DataTable
            columns={playerColumns}
            rows={playerStats}
            getRowKey={(p) => p.steamId}
            initialSort={{ key: "kills", dir: "desc" }}
            emptyLabel="Sem estatísticas de jogadores."
          />
        </article>
      )
    },
    {
      id: "utility",
      label: "Utility",
      content: (
        <article className="panel full">
          <div className="panel-head">
            <h2>Utility</h2>
            <span>granadas, dano e flashes</span>
          </div>
          <DataTable
            columns={utilityColumns}
            rows={utility}
            getRowKey={(u) => u.steamId}
            initialSort={{ key: "total", dir: "desc" }}
            stickyFirst
            emptyLabel="Sem eventos de utility."
          />
        </article>
      )
    },
    {
      id: "duels",
      label: "Duelos",
      content: (
        <article className="panel full">
          <div className="panel-head">
            <h2>Duelos</h2>
            <span>confronto direto contra cada adversário</span>
          </div>
          {duelOptions.length === 0 ? (
            <p className="state-note">Sem confrontos registrados.</p>
          ) : (
            <>
              <div className="duel-controls">
                <label className="duel-field">
                  Jogador
                  <select
                    value={selectedDuelPlayer}
                    onChange={(event) => setDuelPlayer(event.target.value)}
                  >
                    {duelOptions.map((option) => (
                      <option key={option.steamId} value={option.steamId}>
                        {option.name}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="duel-totals">
                  <span className="duel-kpi">
                    <strong>{duelTotals.kills}</strong> a favor
                  </span>
                  <span className="duel-kpi">
                    <strong>{duelTotals.deaths}</strong> contra
                  </span>
                  <span className="duel-kpi" data-pos={posAttr(duelBalance)}>
                    <strong>{fmtDiff(duelBalance)}</strong> saldo
                  </span>
                </div>
              </div>
              {duels.length === 0 ? (
                <p className="state-note">Sem confrontos deste jogador contra adversários.</p>
              ) : (
                <table className="stat-table duel-table">
                  <thead>
                    <tr>
                      <th>Oponente</th>
                      <th>A favor</th>
                      <th>Contra</th>
                      <th>Saldo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {duels.map((duel) => (
                      <tr key={duel.opp}>
                        <th scope="row">{label(duel.opp)}</th>
                        <td>{duel.kills}</td>
                        <td>{duel.deaths}</td>
                        <td className="duel-diff" data-pos={posAttr(duel.diff)}>
                          {fmtDiff(duel.diff)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </>
          )}
        </article>
      )
    },
    {
      id: "weapons",
      label: "Armas",
      content: (
        <article className="panel full">
          <div className="panel-head">
            <h2>Armas por jogador</h2>
            <span>disparos, accuracy, kills e HS%</span>
          </div>
          {weapons.length === 0 ? (
            <p className="state-note">Sem estatísticas de armas.</p>
          ) : (
            <div className="weapons-grid">
              {weapons.map((player) => (
                <div className="weapon-card" key={weaponPlayerKey(player)}>
                  <div className="weapon-card-head">
                    <strong>{player.name ?? player.steamId.slice(-5)}</strong>
                    <div className="weapon-overall">
                      <span>HS% {pct(player.overall.hsPct)}</span>
                      <span>Acc {pct(player.overall.accuracy)}</span>
                      <span>Dano/tiro {player.overall.damagePerShot.toFixed(1)}</span>
                      <span>1º tiro {pct(player.overall.firstShotAccuracy)}</span>
                    </div>
                  </div>
                  <DataTable
                    columns={weaponColumns}
                    rows={player.weapons}
                    getRowKey={(w) => `${player.steamId}-${w.weapon}`}
                    initialSort={{ key: "kills", dir: "desc" }}
                    emptyLabel="Sem disparos."
                  />
                </div>
              ))}
            </div>
          )}
        </article>
      )
    },
    {
      id: "bombsites",
      label: "Bombsites",
      content: (
        <section className="surface-grid">
          <article className="panel half">
            <div className="panel-head">
              <h2>Win rate por bombsite</h2>
              <span>A vs B</span>
            </div>
            {bombsiteChart.length === 0 ? (
              <p className="state-note">Sem plants registrados.</p>
            ) : (
              <BarChart data={bombsiteChart} max={100} />
            )}
          </article>
          <article className="panel half">
            <div className="panel-head">
              <h2>Detalhe por site</h2>
              <span>plants · wins · win rate</span>
            </div>
            <DataTable
              columns={bombsiteColumns}
              rows={bombsites}
              getRowKey={(b) => `${b.team}-${b.site}`}
              initialSort={{ key: "winRate", dir: "desc" }}
              emptyLabel="Sem plants registrados."
            />
          </article>
        </section>
      )
    }
  ];

  return (
    <>
      <PageHeader
        eyebrow="Match report"
        title={`${summary.teamA ?? "Time A"} x ${summary.teamB ?? "Time B"}`}
        description={`Mapa ${summary.map} · ${summary.roundsCount} rounds · ${summary.playersCount} jogadores.`}
      />

      <article className="panel full scoreboard">
        <div className="score-team" data-team="a">
          <span>{summary.teamA ?? "Time A"}</span>
          <strong>{summary.score.teamA ?? 0}</strong>
        </div>
        <div className="score-meta">
          <span className="mono">{summary.map}</span>
          <small>placar final</small>
        </div>
        <div className="score-team" data-team="b">
          <span>{summary.teamB ?? "Time B"}</span>
          <strong>{summary.score.teamB ?? 0}</strong>
        </div>
      </article>

      <Tabs items={tabs} />
    </>
  );
}
