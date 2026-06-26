import type { RadarMetadata } from "./types";

/**
 * Converte coordenadas do mundo (x/y da demo) para coordenadas de radar.
 *
 * O replay já recebe `radar_x/radar_y` prontos do backend; este helper existe
 * para desenho client-side reutilizável (ex.: playbook na Phase 15), usando a
 * mesma fórmula normativa do contrato de dados.
 */
export function worldToRadar(
  x: number,
  y: number,
  metadata: RadarMetadata
): { radarX: number; radarY: number } {
  return {
    radarX: (x - metadata.posX) / metadata.scale,
    radarY: (metadata.posY - y) / metadata.scale
  };
}
