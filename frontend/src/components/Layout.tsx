import type { ReactNode } from "react";
import { useReportStore } from "../stores/reportStore";
import ThemeToggle from "./ThemeToggle";

export default function Layout({ children }: { children: ReactNode }) {
  const step = useReportStore((s) => s.step);
  const reset = useReportStore((s) => s.reset);
  const showHeader = step !== "upload";

  return (
    <div className="min-h-screen flex flex-col">
      {showHeader && (
        <header className="sticky top-0 z-50 backdrop-blur-md" style={{ background: "color-mix(in srgb, var(--bg) 85%, transparent)" }}>
          <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
            <button onClick={reset} className="hover:opacity-70 transition-opacity">
              <span style={{ fontFamily: "'Gveret Levin', cursive" }} className="text-lg">
                Vitruvius
              </span>
            </button>
            <ThemeToggle />
          </div>
        </header>
      )}

      <main className={`flex-1 w-full mx-auto px-6 ${showHeader ? "max-w-6xl py-8" : ""}`}>
        {children}
      </main>
    </div>
  );
}
