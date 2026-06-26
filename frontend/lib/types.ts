export type UUID = string;
export type ISODateTime = string;
export type Side = "CT" | "T";
export type DemoStatus = "pending" | "parsing" | "parsed" | "failed";
export type HeatmapType = "kills" | "deaths" | "path" | "utility" | "grenades";
export type GrenadeType = "he" | "flash" | "smoke" | "molotov" | "incendiary" | "decoy";

export type HealthResponse = {
  status: string;
};

export type Demo = {
  id: UUID;
  filename: string;
  path: string;
  status: DemoStatus;
  createdAt: ISODateTime;
  parsedAt: ISODateTime | null;
  error: string | null;
};

export type Match = {
  id: UUID;
  demoId: UUID;
  map: string;
  teamA: string | null;
  teamB: string | null;
  scoreA: number | null;
  scoreB: number | null;
  startedAt: ISODateTime | null;
  tickRate: number | null;
};

export type MatchSummary = {
  id: UUID;
  demoId: UUID;
  map: string;
  teamA: string | null;
  teamB: string | null;
  score: {
    teamA: number | null;
    teamB: number | null;
  };
  tickRate: number | null;
  startedAt: ISODateTime | null;
  playersCount: number;
  roundsCount: number;
};

export type Player = {
  matchId: UUID;
  steamId: string;
  name: string | null;
  team: string | null;
};

export type Round = {
  matchId: UUID;
  roundNumber: number;
  winner: Side | null;
  reason: string | null;
  startTick: number | null;
  endTick: number | null;
};

export type ReplayPlayer = {
  steamId: string;
  name: string;
  side: Side;
  x: number;
  y: number;
  z: number;
  radarX: number;
  radarY: number;
  hp: number;
  armor: number;
  weapon: string;
  yaw: number | null;
  alive: boolean;
};

export type ReplayEvent = {
  type: "kill" | "bomb_plant" | "bomb_defuse" | "bomb_explode" | "grenade";
  grenadeType: GrenadeType | null;
  tick: number;
  x: number | null;
  y: number | null;
  radarX: number | null;
  radarY: number | null;
};

export type ReplayFrame = {
  tick: number;
  time: number;
  players: ReplayPlayer[];
  events: ReplayEvent[];
};

export type ReplayPayload = {
  matchId: UUID;
  map: string;
  round: number;
  tickRate: number | null;
  frames: ReplayFrame[];
};

export type HeatmapPoint = {
  x: number;
  y: number;
  radarX: number;
  radarY: number;
  weight: number;
};

export type HeatmapFilters = {
  player: string | null;
  team: string | null;
  side: Side | null;
  roundRange: string | null;
  weapon: string | null;
  grenadeType: GrenadeType | null;
};

export type HeatmapPayload = {
  matchId: UUID;
  map: string;
  type: HeatmapType;
  points: HeatmapPoint[];
  filtersApplied: HeatmapFilters;
};

export type GrenadeCounts = Record<GrenadeType | "total", number>;

export type UtilityStats = {
  steamId: string;
  name: string;
  grenadesThrown: GrenadeCounts;
  heWithDamage: number;
  heDamageTotal: number;
  molotovDamageTotal: number;
  flashesThrown: number;
  enemiesBlinded: number;
  enemyBlindTime: number;
  flashAssists: number;
  utilityDamage: number;
};

export type UtilityStatsPayload = {
  matchId: UUID;
  players: UtilityStats[];
};

export type WeaponOverallStats = {
  hsPct: number;
  accuracy: number;
  damagePerShot: number;
  firstShotAccuracy: number;
};

export type WeaponStats = {
  weapon: string;
  shots: number;
  hits: number;
  accuracy: number;
  kills: number;
  headshots: number;
  hsPct: number;
  damage: number;
  damagePerShot: number;
  firstShotAccuracy: number;
};

export type PlayerWeaponStats = {
  steamId: string;
  name: string;
  weaponsUsed: string[];
  overall: WeaponOverallStats;
  weapons: WeaponStats[];
};

export type WeaponStatsPayload = {
  matchId: UUID;
  players: PlayerWeaponStats[];
};

export type Matchup = {
  attackerSteamId: string;
  victimSteamId: string;
  kills: number;
};

export type MatchupPayload = {
  matchId: UUID;
  players: string[];
  matrix: Matchup[];
};

export type DeathPosition = {
  roundNumber: number;
  x: number;
  y: number;
  radarX: number;
  radarY: number;
  attackerSteamId: string;
  weapon: string;
};

export type DeathPositionCluster = {
  x: number;
  y: number;
  radarX: number;
  radarY: number;
  count: number;
  clusterRadius: number;
};

export type DeathPositionsPayload = {
  matchId: UUID;
  steamId: string;
  map: string;
  deaths: DeathPosition[];
  topSpot: DeathPositionCluster | null;
};

export type BombsiteStats = {
  team: string;
  site: "A" | "B";
  plants: number;
  roundWins: number;
  winRate: number;
  postPlantWinRate: number;
};

export type BombsiteStatsPayload = {
  matchId: UUID;
  map: string;
  sites: BombsiteStats[];
  bestSiteByTeam: Record<string, "A" | "B">;
};

export type EconomyRound = {
  roundNumber: number;
  tTeam: string;
  ctTeam: string;
  tBuy: "eco" | "force" | "full" | null;
  ctBuy: "eco" | "force" | "full" | null;
  tEquipValue: number | null;
  ctEquipValue: number | null;
};

export type EconomyPlayer = {
  steamId: string;
  avgEquipValue: number | null;
  ecoRounds: number;
  forceRounds: number;
  fullRounds: number;
};

export type EconomyPayload = {
  matchId: UUID;
  rounds: EconomyRound[];
  byPlayer: EconomyPlayer[];
};

export type RadarMetadata = {
  map: string;
  posX: number;
  posY: number;
  scale: number;
  imageWidth: number;
  imageHeight: number;
  levels: unknown | null;
};

export type MapSummary = {
  map: string;
  hasRadar: boolean;
  hasMetadata: boolean;
};

export type GrenadeEvent = {
  matchId: UUID;
  roundNumber: number;
  tick: number;
  time: number;
  throwerSteamId: string;
  throwerSide: Side;
  grenadeType: GrenadeType;
  event: "thrown" | "detonate" | "expire";
  x: number;
  y: number;
  z: number;
  entityId: number | null;
};

export type BlindEvent = {
  matchId: UUID;
  roundNumber: number;
  tick: number;
  time: number;
  flasherSteamId: string | null;
  victimSteamId: string;
  flasherSide: Side | null;
  victimSide: Side;
  isEnemy: boolean;
  duration: number;
  entityId: number | null;
};

export type ShotEvent = {
  matchId: UUID;
  roundNumber: number;
  tick: number;
  time: number;
  steamId: string;
  weapon: string;
  x: number;
  y: number;
  z: number;
};
