import { useMemo } from "react";
import { useReportStore } from "../stores/reportStore";
import { getDownloadUrl, getDocxDownloadUrl } from "../api/client";

export default function GeneratePanel() {
  const { sessionId, groups, findings, setStep, reset } = useReportStore();

  const findingsList = useMemo(() => Object.values(findings), [findings]);
  const groupMap = useMemo(() => Object.fromEntries(groups.map((g) => [g.id, g])), [groups]);
  const totalPhotos = useMemo(() => groups.reduce((sum, g) => sum + g.photo_ids.length, 0), [groups]);

  const downloadZip = () => { if (sessionId) window.open(getDownloadUrl(sessionId), "_blank"); };
  const downloadDocx = () => { if (sessionId) window.open(getDocxDownloadUrl(sessionId), "_blank"); };

  return (
    <div className="max-w-3xl mx-auto animate-fade-up">
      <div className="text-center mb-10">
        <h2 className="text-2xl font-semibold" style={{ color: "var(--text-primary)" }}>Export Report</h2>
        <p className="mt-2 text-sm" style={{ color: "var(--text-secondary)" }}>Review summary and download your deliverables.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 mb-8">
        <StatCard label="Groups" value={groups.length} />
        <StatCard label="Findings" value={findingsList.length} />
        <StatCard label="Photos" value={totalPhotos} />
      </div>

      {/* Findings summary */}
      <div className="card rounded-2xl mb-8" style={{ borderColor: "var(--border)" }}>
        {findingsList.map((finding, idx) => {
          const group = groupMap[finding.group_id];
          return (
            <div key={finding.id} className="p-4 flex items-start gap-3" style={{ borderBottom: idx < findingsList.length - 1 ? "1px solid var(--border)" : "none" }}>
              <span className="w-6 h-6 rounded-full bg-brand-500/15 text-brand-600 dark:text-brand-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                {idx + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{group?.label || "Unknown"}</h4>
                  <SeverityBadge severity={finding.severity} />
                </div>
                <p className="text-xs mt-1 line-clamp-2" style={{ color: "var(--text-secondary)" }}>{finding.observation}</p>
              </div>
            </div>
          );
        })}
        {findingsList.length === 0 && (
          <div className="p-10 text-center text-sm" style={{ color: "var(--text-muted)" }}>No findings to include.</div>
        )}
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button onClick={() => setStep("review")} className="flex-1 btn-outline py-3 px-6 text-sm">
          Back to Review
        </button>
        <button onClick={downloadDocx} className="flex-1 btn-outline py-3 px-6 text-sm !border-brand-500/20 !text-brand-600 dark:!text-brand-400 hover:!bg-brand-500/5">
          Download .docx
        </button>
        <button onClick={downloadZip} className="flex-1 btn-primary py-3 px-6 text-sm">
          Download .zip
        </button>
      </div>

      <div className="text-center mt-8">
        <button onClick={reset} className="text-xs transition-colors" style={{ color: "var(--text-muted)" }}>
          Start New Report
        </button>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="card rounded-xl p-5 text-center">
      <p className="text-3xl font-bold tabular-nums" style={{ color: "var(--text-primary)" }}>{value}</p>
      <p className="text-xs mt-1 uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>{label}</p>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const styles: Record<string, string> = {
    low: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
    medium: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
    high: "bg-orange-500/15 text-orange-600 dark:text-orange-400",
    critical: "bg-red-500/15 text-red-600 dark:text-red-400",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${styles[severity] || "bg-gray-500/15 text-gray-500"}`}>
      {severity?.toUpperCase() || "N/A"}
    </span>
  );
}
