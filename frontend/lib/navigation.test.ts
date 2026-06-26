import { describe, expect, it } from "vitest";

import { NAV_ITEMS } from "./navigation";

describe("base navigation", () => {
  it("exposes the phase-09 primary areas without external links", () => {
    expect(NAV_ITEMS.map((item) => item.href)).toEqual([
      "/",
      "/demos",
      "/matches",
      "/replay",
      "/analytics",
      "/playbook"
    ]);
    expect(NAV_ITEMS.map((item) => item.label)).toEqual([
      "Dashboard",
      "Demos",
      "Matches",
      "Replay",
      "Heatmaps",
      "Playbook"
    ]);
    expect(NAV_ITEMS.every((item) => item.href.startsWith("/"))).toBe(true);
  });
});
