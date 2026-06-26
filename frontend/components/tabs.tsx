"use client";

import { type KeyboardEvent, type ReactNode, useState } from "react";

export type TabItem = {
  id: string;
  label: string;
  content: ReactNode;
};

export function Tabs({ items, initialId }: { items: TabItem[]; initialId?: string }) {
  const [active, setActive] = useState(initialId ?? items[0]?.id);

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") {
      return;
    }
    event.preventDefault();
    const index = items.findIndex((item) => item.id === active);
    const delta = event.key === "ArrowRight" ? 1 : -1;
    const next = items[(index + delta + items.length) % items.length];
    if (next) {
      setActive(next.id);
    }
  }

  return (
    <div className="tabs">
      <div className="tablist" role="tablist" aria-label="Seções do relatório" onKeyDown={onKeyDown}>
        {items.map((item) => {
          const selected = item.id === active;
          return (
            <button
              key={item.id}
              id={`tab-${item.id}`}
              className="tab"
              role="tab"
              type="button"
              aria-selected={selected}
              aria-controls={`panel-${item.id}`}
              tabIndex={selected ? 0 : -1}
              data-active={selected}
              onClick={() => setActive(item.id)}
            >
              {item.label}
            </button>
          );
        })}
      </div>
      {items.map((item) => (
        <div
          key={item.id}
          id={`panel-${item.id}`}
          role="tabpanel"
          aria-labelledby={`tab-${item.id}`}
          hidden={item.id !== active}
        >
          {item.id === active ? item.content : null}
        </div>
      ))}
    </div>
  );
}
