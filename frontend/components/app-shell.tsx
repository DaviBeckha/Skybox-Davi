"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode } from "react";

import { NAV_ITEMS } from "@/lib/navigation";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <>
      <a className="skip-link" href="#main-content">
        Pular para o conteúdo
      </a>
      <div className="app-shell">
        <aside className="sidebar" aria-label="Navegação principal">
          <Link className="brand" href="/" aria-label="cs2-lab dashboard">
            <span className="brand-mark" aria-hidden="true">
              CL
            </span>
            <span>
              <strong>cs2-lab</strong>
              <small>local demo analytics</small>
            </span>
          </Link>

          <nav className="nav-list" aria-label="Áreas do aplicativo">
            {NAV_ITEMS.map((item) => {
              const isActive =
                item.href === "/" ? pathname === item.href : pathname.startsWith(item.href);

              return (
                <Link
                  aria-current={isActive ? "page" : undefined}
                  className="nav-link"
                  data-active={isActive ? "true" : "false"}
                  href={item.href}
                  key={item.href}
                >
                  <span>{item.label}</span>
                  <small>{item.description}</small>
                </Link>
              );
            })}
          </nav>

          <div className="sidebar-note" aria-label="Escopo de segurança">
            <strong>Offline e privado</strong>
            <span>Somente análise de demos gravadas. Nada em tempo real.</span>
          </div>
        </aside>

        <main className="main-surface" id="main-content" tabIndex={-1}>
          {children}
        </main>
      </div>
    </>
  );
}
