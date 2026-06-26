import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";
import { Providers } from "@/components/providers";

import "./globals.css";

export const metadata: Metadata = {
  title: "cs2-lab",
  description: "Análise local e privada de demos gravadas de Counter-Strike 2."
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
