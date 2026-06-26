"use client";

import { type ReactNode, useMemo, useState } from "react";

export type Column<T> = {
  key: string;
  header: string;
  align?: "left" | "right" | "center";
  numeric?: boolean;
  sortable?: boolean;
  /** Valor usado para ordenar (e render padrão se não houver `render`). */
  value?: (row: T) => string | number;
  render?: (row: T) => ReactNode;
  /** Dica curta no cabeçalho (title). */
  hint?: string;
};

type SortState = { key: string; dir: "asc" | "desc" };

type DataTableProps<T> = {
  columns: Column<T>[];
  rows: T[];
  getRowKey: (row: T) => string;
  initialSort?: SortState;
  stickyFirst?: boolean;
  emptyLabel?: string;
};

export function DataTable<T>({
  columns,
  rows,
  getRowKey,
  initialSort,
  stickyFirst = false,
  emptyLabel = "Sem dados."
}: DataTableProps<T>) {
  const [sort, setSort] = useState<SortState | null>(initialSort ?? null);

  const sortedRows = useMemo(() => {
    if (!sort) {
      return rows;
    }
    const column = columns.find((item) => item.key === sort.key);
    if (!column?.value) {
      return rows;
    }
    const direction = sort.dir === "asc" ? 1 : -1;
    return [...rows].sort((a, b) => {
      const va = column.value!(a);
      const vb = column.value!(b);
      if (typeof va === "number" && typeof vb === "number") {
        return (va - vb) * direction;
      }
      return String(va).localeCompare(String(vb)) * direction;
    });
  }, [rows, sort, columns]);

  function toggleSort(column: Column<T>) {
    if (!column.sortable || !column.value) {
      return;
    }
    setSort((current) => {
      if (current?.key === column.key) {
        return { key: column.key, dir: current.dir === "asc" ? "desc" : "asc" };
      }
      // Numérico começa decrescente (maior primeiro); texto, crescente.
      return { key: column.key, dir: column.numeric ? "desc" : "asc" };
    });
  }

  const align = (column: Column<T>) => column.align ?? (column.numeric ? "right" : "left");

  return (
    <div className="table-scroll">
      <table className="data-table" data-sticky-first={stickyFirst ? "true" : undefined}>
        <thead>
          <tr>
            {columns.map((column) => {
              const isSorted = sort?.key === column.key;
              const ariaSort = isSorted
                ? sort.dir === "asc"
                  ? "ascending"
                  : "descending"
                : column.sortable
                  ? "none"
                  : undefined;
              return (
                <th key={column.key} data-align={align(column)} aria-sort={ariaSort} title={column.hint}>
                  {column.sortable && column.value ? (
                    <button
                      className="th-sort"
                      type="button"
                      data-dir={isSorted ? sort.dir : ""}
                      onClick={() => toggleSort(column)}
                    >
                      {column.header}
                      <span className="sort-ind" aria-hidden="true" />
                    </button>
                  ) : (
                    column.header
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {sortedRows.length === 0 ? (
            <tr>
              <td className="data-empty" colSpan={columns.length}>
                {emptyLabel}
              </td>
            </tr>
          ) : (
            sortedRows.map((row) => (
              <tr key={getRowKey(row)}>
                {columns.map((column) => (
                  <td
                    key={column.key}
                    data-align={align(column)}
                    data-numeric={column.numeric ? "true" : undefined}
                  >
                    {column.render ? column.render(row) : column.value ? column.value(row) : null}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
