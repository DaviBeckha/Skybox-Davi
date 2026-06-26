export type NavItem = {
  href: string;
  label: string;
  description: string;
};

export const NAV_ITEMS: NavItem[] = [
  {
    href: "/",
    label: "Dashboard",
    description: "Resumo geral das demos e partidas."
  },
  {
    href: "/demos",
    label: "Demos",
    description: "Uploads locais e histórico de arquivos .dem."
  },
  {
    href: "/matches",
    label: "Matches",
    description: "Partidas parseadas e relatórios por match."
  },
  {
    href: "/replay",
    label: "Replay",
    description: "Entrada para revisão 2D por partida."
  },
  {
    href: "/analytics",
    label: "Heatmaps",
    description: "Área base para mapas de calor e filtros."
  },
  {
    href: "/playbook",
    label: "Playbook",
    description: "Espaço privado para táticas e anotações."
  }
];
