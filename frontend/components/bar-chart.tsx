export type BarChartDatum = {
  label: string;
  value: number;
  display?: string;
};

type BarChartProps = {
  data: BarChartDatum[];
  max?: number;
};

export function BarChart({ data, max }: BarChartProps) {
  const ceiling = max ?? Math.max(1, ...data.map((datum) => datum.value));

  if (data.length === 0) {
    return <p className="state-note">Sem dados para o gráfico.</p>;
  }

  return (
    <div className="bar-chart">
      {data.map((datum) => {
        const width = Math.max(0, Math.min(100, (datum.value / ceiling) * 100));
        return (
          <div className="bar-row" key={datum.label}>
            <span className="bar-label">{datum.label}</span>
            <span className="bar-track">
              <span className="bar-fill" style={{ width: `${width}%` }} />
            </span>
            <span className="bar-value">{datum.display ?? String(datum.value)}</span>
          </div>
        );
      })}
    </div>
  );
}
