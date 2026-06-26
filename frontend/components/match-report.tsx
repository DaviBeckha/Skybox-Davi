"use client";

import { BarChart } from "@/components/bar-chart";
import { PageHeader } from "@/components/page-header";
import {
  useBombsiteStatsQuery,
  useMatchRoundsQuery,
  useMatchSummaryQuery,
  useMatchupsQuery,
  usePlayerStatsQuery,
  useUtilityStatsQuery,
  useWeaponStatsQuery
} from "@/lib/queries";

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
  const label = (steamId: string) => nameBySteam.get(steamId) ?? steamId.slice(-5);

  const matrixPlayers = matchupsQuery.data?.players ?? [];
  const killLookup = new Map<string, number>();
  for (const entry of matchupsQuery.data?.matrix ?? []) {
    killLookup.set(`${entry.attackerSteamId}|${entry.victimSteamId}`, entry.kills);
  }

  const killsChart = [...playerStats]
    .sort((a, b) => b.kills - a.kills)
    .map((player) => ({ label: player.name ?? player.steamId.slice(-5), value: player.kills }));

  const bombsiteChart = bombsites.map((site) => ({
    label: `${site.team} · ${site.site}`,
    value: Math.round(site.winRate * 100),
    display: pct(site.winRate)
  }));

  return (
    <>
      <PageHeader
        eyebrow="Match report"
        title={`${summary.teamA ?? "Time A"} x ${summary.teamB ?? "Time B"}`}
        description={`Mapa ${summary.map} · ${summary.roundsCount} rounds · ${summary.playersCount} jogadores.`}
      />

      <section className="surface-grid" aria-label="Relatório da partida">
        {/* Placar */}
        <article className="panel full scoreboard">
          <div className="score-team">
            <span>{summary.teamA ?? "Time A"}</span>
            <strong>{summary.score.teamA ?? 0}</strong>
          </div>
          <div className="score-meta">
            <span className="mono">{summary.map}</span>
            <small>placar final</small>
          </div>
          <div className="score-team">
            <span>{summary.teamB ?? "Time B"}</span>
            <strong>{summary.score.teamB ?? 0}</strong>
          </div>
        </article>

        {/* Rounds */}
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

        {/* Tabela de jogadores */}
        <article className="panel full">
          <div className="panel-head">
            <h2>Jogadores</h2>
            <span>KD · ADR · KAST · entry · trade · clutch</span>
          </div>
          {playerStats.length === 0 ? (
            <p className="state-note">Sem estatísticas de jogadores.</p>
          ) : (
            <div className="table-scroll">
              <table className="stat-table">
                <thead>
                  <tr>
                    <th>Jogador</th>
                    <th>Time</th>
                    <th>K</th>
                    <th>D</th>
                    <th>A</th>
                    <th>K/D</th>
                    <th>ADR</th>
                    <th>KAST</th>
                    <th>Entry K/D</th>
                    <th>Trade</th>
                    <th>Clutch</th>
                  </tr>
                </thead>
                <tbody>
                  {[...playerStats]
                    .sort((a, b) => b.kills - a.kills)
                    .map((player) => (
                      <tr key={player.steamId}>
                        <td>{player.name ?? player.steamId.slice(-5)}</td>
                        <td className="muted-cell">{player.team ?? "—"}</td>
                        <td>{player.kills}</td>
                        <td>{player.deaths}</td>
                        <td>{player.assists}</td>
                        <td>{ratio(player.kills, player.deaths)}</td>
                        <td>{player.adr.toFixed(1)}</td>
                        <td>{pct(player.kastPct)}</td>
                        <td>
                          {player.entryKills}/{player.entryDeaths}
                        </td>
                        <td>{player.tradeKills}</td>
                        <td>{player.clutches}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </article>

        {/* Gráfico simples: kills por jogador */}
        <article className="panel half">
          <div className="panel-head">
            <h2>Kills por jogador</h2>
            <span>gráfico</span>
          </div>
          <BarChart data={killsChart} />
        </article>

        {/* Sucesso por bombsite + gráfico A vs B */}
        <article className="panel half">
          <div className="panel-head">
            <h2>Sucesso por bombsite</h2>
            <span>win rate por site/time</span>
          </div>
          {bombsites.length === 0 ? (
            <p className="state-note">Sem plants registrados.</p>
          ) : (
            <>
              <BarChart data={bombsiteChart} max={100} />
              <div className="table-scroll">
                <table className="stat-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Site</th>
                      <th>Plants</th>
                      <th>Wins</th>
                      <th>Win rate</th>
                      <th>Pós-plant</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bombsites.map((site) => (
                      <tr key={`${site.team}-${site.site}`}>
                        <td>{site.team}</td>
                        <td>{site.site}</td>
                        <td>{site.plants}</td>
                        <td>{site.roundWins}</td>
                        <td>{pct(site.winRate)}</td>
                        <td>{pct(site.postPlantWinRate)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </article>

        {/* Utility */}
        <article className="panel full">
          <div className="panel-head">
            <h2>Utility</h2>
            <span>granadas, dano e flashes</span>
          </div>
          {utility.length === 0 ? (
            <p className="state-note">Sem eventos de utility.</p>
          ) : (
            <div className="table-scroll">
              <table className="stat-table">
                <thead>
                  <tr>
                    <th>Jogador</th>
                    <th>HE</th>
                    <th>Flash</th>
                    <th>Smoke</th>
                    <th>Molotov</th>
                    <th>Decoy</th>
                    <th>Total</th>
                    <th>HE c/ dano</th>
                    <th>Dano HE</th>
                    <th>Dano molly</th>
                    <th>Cegou inim.</th>
                    <th>Tempo cegueira</th>
                    <th>Flash assists</th>
                  </tr>
                </thead>
                <tbody>
                  {utility.map((player) => (
                    <tr key={player.steamId}>
                      <td>{player.name ?? player.steamId.slice(-5)}</td>
                      <td>{player.grenadesThrown.he}</td>
                      <td>{player.grenadesThrown.flash}</td>
                      <td>{player.grenadesThrown.smoke}</td>
                      <td>{player.grenadesThrown.molotov}</td>
                      <td>{player.grenadesThrown.decoy}</td>
                      <td>{player.grenadesThrown.total}</td>
                      <td>{player.heWithDamage}</td>
                      <td>{player.heDamageTotal}</td>
                      <td>{player.molotovDamageTotal}</td>
                      <td>{player.enemiesBlinded}</td>
                      <td>{player.enemyBlindTime.toFixed(1)}s</td>
                      <td>{player.flashAssists}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>

        {/* Kill matrix */}
        <article className="panel full">
          <div className="panel-head">
            <h2>Kill matrix</h2>
            <span>linha matou coluna</span>
          </div>
          {matrixPlayers.length === 0 ? (
            <p className="state-note">Sem confrontos registrados.</p>
          ) : (
            <div className="table-scroll">
              <table className="stat-table kill-matrix">
                <thead>
                  <tr>
                    <th>↓ mata · → morre</th>
                    {matrixPlayers.map((victim) => (
                      <th key={victim}>{label(victim)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {matrixPlayers.map((attacker) => (
                    <tr key={attacker}>
                      <th scope="row">{label(attacker)}</th>
                      {matrixPlayers.map((victim) => {
                        const kills = killLookup.get(`${attacker}|${victim}`) ?? 0;
                        return (
                          <td
                            className={attacker === victim ? "matrix-self" : kills > 0 ? "matrix-hit" : ""}
                            key={victim}
                          >
                            {attacker === victim ? "—" : kills}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>

        {/* Armas por player */}
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
                <div className="weapon-card" key={player.steamId}>
                  <div className="weapon-card-head">
                    <strong>{player.name ?? player.steamId.slice(-5)}</strong>
                    <div className="weapon-overall">
                      <span>HS% {pct(player.overall.hsPct)}</span>
                      <span>Acc {pct(player.overall.accuracy)}</span>
                      <span>Dano/tiro {player.overall.damagePerShot.toFixed(1)}</span>
                      <span>1º tiro {pct(player.overall.firstShotAccuracy)}</span>
                    </div>
                  </div>
                  {player.weapons.length === 0 ? (
                    <p className="state-note">Sem disparos.</p>
                  ) : (
                    <div className="table-scroll">
                      <table className="stat-table">
                        <thead>
                          <tr>
                            <th>Arma</th>
                            <th>Disparos</th>
                            <th>Hits</th>
                            <th>Acc</th>
                            <th>Kills</th>
                            <th>HS</th>
                            <th>HS%</th>
                            <th>Dano</th>
                          </tr>
                        </thead>
                        <tbody>
                          {[...player.weapons]
                            .sort((a, b) => b.kills - a.kills)
                            .map((weapon) => (
                              <tr key={weapon.weapon}>
                                <td>{weapon.weapon}</td>
                                <td>{weapon.shots}</td>
                                <td>{weapon.hits}</td>
                                <td>{pct(weapon.accuracy)}</td>
                                <td>{weapon.kills}</td>
                                <td>{weapon.headshots}</td>
                                <td>{pct(weapon.hsPct)}</td>
                                <td>{weapon.damage}</td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </article>
      </section>
    </>
  );
}
