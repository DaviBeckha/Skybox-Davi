import type { JSX } from "react";

import type { GrenadeType } from "@/lib/types";

// Cor por tipo de granada (compartilhada entre o ícone e o rastro de trajetória).
export const GRENADE_COLORS: Record<GrenadeType, string> = {
  he: "#ff6b7a",
  flash: "#f4e08a",
  smoke: "#c3ccda",
  molotov: "#ff8c5a",
  incendiary: "#ff8c5a",
  decoy: "#94a3b8"
};

const INK = "#10141f";

function glyph(type: GrenadeType): JSX.Element {
  switch (type) {
    case "smoke":
      return (
        <g fill={INK}>
          <circle cx="9" cy="14" r="3.4" />
          <circle cx="13" cy="11.4" r="4" />
          <circle cx="16" cy="14.4" r="3" />
        </g>
      );
    case "flash":
      return (
        <g stroke={INK} strokeWidth="1.8" strokeLinecap="round">
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
          <line x1="7.2" y1="7.2" x2="16.8" y2="16.8" />
          <line x1="16.8" y1="7.2" x2="7.2" y2="16.8" />
        </g>
      );
    case "molotov":
    case "incendiary":
      return (
        <path
          d="M12.4 4.4c1.9 2.7 3.4 4.4 1.7 7.3 1.9-.5 2 2.4.4 4 2.4-.6 2.4-3.4.7-5.6.3 1.8-1 2.4-1 2.4.6-2.1-1.1-3.8-1.1-5.7-1.3.9-1.8 2-1.4 3.3-1-.6-1.4-1.9-.9-3.1-1.7 1.5-2.2 3.6-1 5.4-1.7-1.4-1.6-4 .6-6.1.8-.8 2.1-1.7 2.7-1.6z"
          fill={INK}
        />
      );
    case "he":
      return (
        <g fill={INK}>
          <rect x="10.7" y="4.6" width="2.6" height="2.4" rx="0.5" />
          <circle cx="12" cy="13" r="5" />
          <line x1="12" y1="9" x2="12" y2="17" stroke={GRENADE_COLORS.he} strokeWidth="1.1" />
          <line x1="8" y1="13" x2="16" y2="13" stroke={GRENADE_COLORS.he} strokeWidth="1.1" />
        </g>
      );
    case "decoy":
    default:
      return (
        <text x="12" y="16.5" textAnchor="middle" fontSize="11" fontWeight="700" fill={INK}>
          ?
        </text>
      );
  }
}

/** Ícone da granada: distintivo redondo na cor do tipo + glifo branco-escuro. */
export function GrenadeIcon({ type, size = 20 }: { type: GrenadeType; size?: number }): JSX.Element {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-hidden="true">
      <circle
        cx="12"
        cy="12"
        r="11"
        fill={GRENADE_COLORS[type]}
        stroke="rgba(7,10,18,0.85)"
        strokeWidth="1.5"
      />
      {glyph(type)}
    </svg>
  );
}
