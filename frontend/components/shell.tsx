import Link from "next/link";
import type { ReactNode } from "react";

const navigation = [
  ["Overview", "/"],
  ["Benchmarks", "/benchmarks"],
  ["Runs", "/runs"],
  ["Agents", "/agents"],
  ["Analytics", "/analytics"],
  ["Documentation", "/documentation"],
] as const;

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/" aria-label="EvalForge overview">
          <span className="brand-mark">EF</span>
          <span>EvalForge</span>
        </Link>
        <div className="workspace-chip"><span>DE</span><div><small>Workspace</small><strong>Demo environment</strong></div></div>
        <nav aria-label="Primary navigation">
          {navigation.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}
        </nav>
        <div className="sidebar-foot"><span className="live-dot" />Demo mode · deterministic</div>
      </aside>
      <main className="main"><header className="topbar"><div><span className="eyebrow">Evaluation infrastructure</span></div><a className="ghost-button" href="http://localhost:8000/docs">API docs ↗</a></header>{children}</main>
    </div>
  );
}
