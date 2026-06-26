import type { DemoStatus } from "@/lib/types";

const STATUS_LABELS: Record<DemoStatus, string> = {
  pending: "Na fila",
  parsing: "Processando",
  parsed: "Concluído",
  failed: "Falhou"
};

export function StatusBadge({ status }: { status: DemoStatus }) {
  return (
    <span className="status-badge" data-status={status}>
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}
