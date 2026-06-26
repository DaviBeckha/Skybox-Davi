import { describe, expect, it, vi } from "vitest";

import { buildApiUrl, camelizeApiPayload, createApiClient } from "./api";

describe("api client boundary", () => {
  it("deeply maps backend snake_case payloads to frontend camelCase", () => {
    const payload = {
      match_id: "match-1",
      steam_id: "76561198000000000",
      created_at: "2026-06-25T18:00:00Z",
      nested_rows: [
        {
          round_number: 1,
          radar_x: 512,
          radar_y: 384
        }
      ]
    };

    expect(camelizeApiPayload(payload)).toEqual({
      matchId: "match-1",
      steamId: "76561198000000000",
      createdAt: "2026-06-25T18:00:00Z",
      nestedRows: [
        {
          roundNumber: 1,
          radarX: 512,
          radarY: 384
        }
      ]
    });
  });

  it("builds local backend URLs with query params", () => {
    const url = buildApiUrl("http://localhost:8000", "/matches/abc/replay", {
      round: 4,
      sample_rate: 8,
      empty: undefined
    });

    expect(url.toString()).toBe("http://localhost:8000/matches/abc/replay?round=4&sample_rate=8");
  });

  it("calls backend endpoints and returns camelCase objects", async () => {
    const fetcher = vi.fn(async () => {
      return new Response(
        JSON.stringify({
          id: "demo-1",
          filename: "mirage.dem",
          created_at: "2026-06-25T18:00:00Z",
          parsed_at: null,
          status: "pending",
          path: "data/raw_demos/demo-1.dem",
          error: null
        }),
        { status: 200 }
      );
    });

    const client = createApiClient({
      baseUrl: "http://localhost:8000",
      fetcher
    });

    await expect(client.getDemo("demo-1")).resolves.toMatchObject({
      id: "demo-1",
      createdAt: "2026-06-25T18:00:00Z",
      parsedAt: null
    });
    expect(fetcher).toHaveBeenCalledWith("http://localhost:8000/demos/demo-1", expect.any(Object));
  });
});
