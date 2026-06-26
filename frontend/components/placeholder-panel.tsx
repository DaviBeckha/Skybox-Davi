import type { ReactNode } from "react";

type PlaceholderPanelProps = {
  title: string;
  phase: string;
  children: ReactNode;
};

export function PlaceholderPanel({ title, phase, children }: PlaceholderPanelProps) {
  return (
    <section className="panel placeholder-panel" aria-labelledby={`${phase}-title`}>
      <div className="phase-pill">{phase}</div>
      <h2 id={`${phase}-title`}>{title}</h2>
      <div className="placeholder-copy">{children}</div>
    </section>
  );
}
