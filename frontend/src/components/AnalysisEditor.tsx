import { useState } from "react";
import type { Finding } from "../types";

interface AnalysisEditorProps {
  finding: Finding;
  onSave: (updates: Partial<Finding>) => void;
  onReAnalyze: (hint: string) => void;
  loading?: boolean;
}

const SEVERITY_OPTIONS = ["low", "medium", "high", "critical"];

const severityStyle: Record<string, string> = {
  low: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
  medium: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  high: "bg-orange-500/15 text-orange-600 dark:text-orange-400",
  critical: "bg-red-500/15 text-red-600 dark:text-red-400",
};

export default function AnalysisEditor({ finding, onSave, onReAnalyze, loading }: AnalysisEditorProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(finding);
  const [showPrompt, setShowPrompt] = useState(false);
  const [hint, setHint] = useState("");

  const handleSave = () => {
    onSave({
      observation: draft.observation,
      potential_cause: draft.potential_cause,
      recommendation: draft.recommendation,
      severity: draft.severity,
    });
    setEditing(false);
  };

  const handleReAnalyze = () => {
    onReAnalyze(hint);
    setShowPrompt(false);
    setHint("");
  };

  if (loading) {
    return (
      <div className="space-y-3 py-2">
        <div className="h-3 rounded-full w-3/4 animate-pulse" style={{ background: "var(--border)" }} />
        <div className="h-3 rounded-full w-1/2 animate-pulse" style={{ background: "var(--border)" }} />
        <div className="h-3 rounded-full w-2/3 animate-pulse" style={{ background: "var(--border)" }} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        {editing ? (
          <select
            value={draft.severity}
            onChange={(e) => setDraft({ ...draft, severity: e.target.value })}
            className="input-field py-1 text-xs"
          >
            {SEVERITY_OPTIONS.map((s) => (
              <option key={s} value={s}>{s.toUpperCase()}</option>
            ))}
          </select>
        ) : (
          <span className={`px-2.5 py-1 rounded-full text-[10px] font-semibold ${severityStyle[finding.severity] || "bg-gray-500/15"}`}
            style={{ color: severityStyle[finding.severity] ? undefined : "var(--text-muted)" }}>
            {finding.severity?.toUpperCase() || "N/A"}
          </span>
        )}

        <div className="flex gap-1">
          {editing ? (
            <>
              <button onClick={() => { setEditing(false); setDraft(finding); }} className="btn-ghost text-xs px-2.5 py-1">
                Cancel
              </button>
              <button onClick={handleSave} className="btn-primary text-xs px-3 py-1">
                Save
              </button>
            </>
          ) : (
            <>
              <button onClick={() => { setDraft(finding); setEditing(true); }} className="btn-ghost text-xs px-2.5 py-1 !text-brand-600 dark:!text-brand-400">
                Edit
              </button>
              <button onClick={() => setShowPrompt(true)} className="btn-ghost text-xs px-2.5 py-1">
                Re-analyze
              </button>
            </>
          )}
        </div>
      </div>

      <div className="space-y-3">
        <FieldBlock label="Observation" value={editing ? draft.observation : finding.observation} editing={editing} onChange={(v) => setDraft({ ...draft, observation: v })} />
        <FieldBlock label="Potential Cause" value={editing ? draft.potential_cause : finding.potential_cause} editing={editing} onChange={(v) => setDraft({ ...draft, potential_cause: v })} />
        <FieldBlock label="Recommendation" value={editing ? draft.recommendation : finding.recommendation} editing={editing} onChange={(v) => setDraft({ ...draft, recommendation: v })} />
      </div>

      {showPrompt && (
        <div className="rounded-xl p-3 space-y-2 animate-fade-in" style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)" }}>
          <p className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Guide the re-analysis (optional):</p>
          <textarea
            value={hint}
            onChange={(e) => setHint(e.target.value)}
            placeholder="e.g. This is actually a plumbing issue, not structural..."
            rows={2}
            className="input-field w-full resize-none"
          />
          <div className="flex justify-end gap-2">
            <button onClick={() => { setShowPrompt(false); setHint(""); }} className="btn-ghost text-xs px-2.5 py-1">Cancel</button>
            <button onClick={handleReAnalyze} className="btn-primary text-xs px-3 py-1">Re-analyze</button>
          </div>
        </div>
      )}
    </div>
  );
}

function FieldBlock({ label, value, editing, onChange }: {
  label: string; value: string; editing: boolean; onChange: (v: string) => void;
}) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-widest mb-1" style={{ color: "var(--text-muted)" }}>{label}</p>
      {editing ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={3}
          className="input-field w-full resize-none"
        />
      ) : (
        <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          {value || <span className="italic" style={{ color: "var(--text-muted)" }}>Not provided</span>}
        </p>
      )}
    </div>
  );
}
