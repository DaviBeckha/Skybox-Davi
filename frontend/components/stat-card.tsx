import type { ReactNode } from "react";

type StatCardProps = {
  label: string;
  value: ReactNode;
  hint: string;
  loading?: boolean;
};

export function StatCard({ label, value, hint, loading = false }: StatCardProps) {
  return (
    <article className="panel stat-card quarter">
      <span>{label}</span>
      <strong>{loading ? "…" : value}</strong>
      <p>{hint}</p>
    </article>
  );
}
