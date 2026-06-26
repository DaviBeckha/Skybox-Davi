import type {
  BombsiteStatsPayload,
  DeathPositionsPayload,
  Demo,
  EconomyPayload,
  HealthResponse,
  HeatmapPayload,
  HeatmapType,
  MapSummary,
  Match,
  MatchSummary,
  MatchupPayload,
  Player,
  RadarMetadata,
  ReplayPayload,
  Round,
  UtilityStatsPayload,
  WeaponStatsPayload
} from "./types";

export const DEFAULT_API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type ApiQueryValue = string | number | boolean | null | undefined;
type Fetcher = (input: string, init?: RequestInit) => Promise<Response>;

type RequestOptions = {
  query?: Record<string, ApiQueryValue>;
  init?: RequestInit;
};

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export function toCamelCase(value: string): string {
  return value.replace(/_([a-z0-9])/g, (_, character: string) => character.toUpperCase());
}

export function camelizeApiPayload<T = unknown>(payload: unknown): T {
  if (Array.isArray(payload)) {
    return payload.map((item) => camelizeApiPayload(item)) as T;
  }

  if (payload !== null && typeof payload === "object" && payload.constructor === Object) {
    return Object.fromEntries(
      Object.entries(payload).map(([key, value]) => [toCamelCase(key), camelizeApiPayload(value)])
    ) as T;
  }

  return payload as T;
}

export function buildApiUrl(
  baseUrl: string,
  path: string,
  query?: Record<string, ApiQueryValue>
): URL {
  const normalizedBaseUrl = baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  const url = new URL(normalizedPath, normalizedBaseUrl);

  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null) {
      url.searchParams.set(key, String(value));
    }
  }

  return url;
}

export function createApiClient(options: { baseUrl?: string; fetcher?: Fetcher } = {}) {
  const baseUrl = options.baseUrl ?? DEFAULT_API_BASE_URL;
  const fetcher = options.fetcher ?? fetch;

  async function request<T>(path: string, requestOptions: RequestOptions = {}): Promise<T> {
    const url = buildApiUrl(baseUrl, path, requestOptions.query);
    const response = await fetcher(url.toString(), {
      cache: "no-store",
      ...requestOptions.init
    });

    if (!response.ok) {
      const body = await readResponseBody(response);
      throw new ApiError(`Backend request failed: ${response.status}`, response.status, body);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    const body = await response.json();
    return camelizeApiPayload<T>(body);
  }

  return {
    getHealth: () => request<HealthResponse>("/health"),
    getDemos: () => request<Demo[]>("/demos"),
    getDemo: (demoId: string) => request<Demo>(`/demos/${demoId}`),
    importDemo: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return request<Demo>("/demos/import", {
        init: {
          method: "POST",
          body: formData
        }
      });
    },
    getMatches: () => request<Match[]>("/matches"),
    getMatch: (matchId: string) => request<Match>(`/matches/${matchId}`),
    getMatchSummary: (matchId: string) => request<MatchSummary>(`/matches/${matchId}/summary`),
    getMatchRounds: (matchId: string) => request<Round[]>(`/matches/${matchId}/rounds`),
    getMatchPlayers: (matchId: string) => request<Player[]>(`/matches/${matchId}/players`),
    getReplay: (matchId: string, params: { round?: number; sampleRate?: number } = {}) =>
      request<ReplayPayload>(`/matches/${matchId}/replay`, {
        query: {
          round: params.round,
          sample_rate: params.sampleRate
        }
      }),
    getHeatmap: (
      matchId: string,
      params: {
        type: HeatmapType;
        player?: string;
        team?: string;
        side?: string;
        roundRange?: string;
        weapon?: string;
        grenadeType?: string;
      }
    ) =>
      request<HeatmapPayload>(`/matches/${matchId}/heatmap`, {
        query: {
          type: params.type,
          player: params.player,
          team: params.team,
          side: params.side,
          round_range: params.roundRange,
          weapon: params.weapon,
          grenade_type: params.grenadeType
        }
      }),
    getPlayerStats: (matchId: string) => request(`/matches/${matchId}/stats/player`),
    getEconomyStats: (matchId: string) =>
      request<EconomyPayload>(`/matches/${matchId}/stats/economy`),
    getWeaponStats: (matchId: string) =>
      request<WeaponStatsPayload>(`/matches/${matchId}/stats/weapons`),
    getUtilityStats: (matchId: string) =>
      request<UtilityStatsPayload>(`/matches/${matchId}/stats/utility`),
    getMatchups: (matchId: string) => request<MatchupPayload>(`/matches/${matchId}/stats/matchups`),
    getDeathPositions: (matchId: string, playerSteamId: string) =>
      request<DeathPositionsPayload>(`/matches/${matchId}/stats/death-positions`, {
        query: {
          player: playerSteamId
        }
      }),
    getBombsiteStats: (matchId: string) =>
      request<BombsiteStatsPayload>(`/matches/${matchId}/stats/bombsites`),
    getMaps: () => request<MapSummary[]>("/maps"),
    getMapMetadata: (mapName: string) => request<RadarMetadata>(`/maps/${mapName}/metadata`)
  };
}

async function readResponseBody(response: Response): Promise<unknown> {
  const text = await response.text();

  if (text.length === 0) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export const api = createApiClient();
