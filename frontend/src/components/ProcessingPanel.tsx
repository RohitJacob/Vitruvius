import { useEffect, useRef } from "react";
import { useReportStore } from "../stores/reportStore";
import { startAnalysis, getResults } from "../api/client";

const STAGE_LABELS: Record<string, string> = {
  analyzing_photos: "Analyzing photos",
  grouping: "Grouping issues",
  writing_analyses: "Writing findings",
  analyzing_template: "Reading template",
  ready_for_review: "Complete",
  error: "Error",
};

export default function ProcessingPanel() {
  const sessionId = useReportStore((s) => s.sessionId);
  const addEvent = useReportStore((s) => s.addPipelineEvent);
  const latestEvent = useReportStore((s) => s.latestEvent);
  const loadResults = useReportStore((s) => s.loadResults);
  const setStep = useReportStore((s) => s.setStep);
  const abortRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    abortRef.current = startAnalysis(
      sessionId,
      (evt) => addEvent(evt),
      async () => {
        try {
          const results = await getResults(sessionId);
          loadResults(results);
          setStep("review");
        } catch {
          addEvent({ stage: "error", progress: 0, message: "Failed to load results", error: "Could not fetch analysis results" });
        }
      },
      (err) => addEvent({ stage: "error", progress: 0, message: "Pipeline failed", error: err }),
    );
    return () => abortRef.current?.();
  }, [sessionId, addEvent, loadResults, setStep]);

  const currentStage = latestEvent?.stage || "analyzing_photos";
  const progress = latestEvent?.progress || 0;
  const isError = currentStage === "error";
  const stageLabel = STAGE_LABELS[currentStage] || currentStage;

  return (
    <div className="max-w-sm mx-auto animate-fade-up flex flex-col items-center justify-center" style={{ minHeight: "60vh" }}>
      <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
        Analyzing your photos
      </p>

      {/* Progress bar */}
      <div className="w-full">
        <div className="h-1 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
          <div
            className={`h-full rounded-full transition-all duration-500 ease-out ${
              isError ? "bg-red-500" : "bg-brand-500"
            }`}
            style={{ width: `${Math.max(progress * 100, 1)}%` }}
          />
        </div>
        <p className="text-xs mt-3 text-center transition-all duration-300" style={{ color: "var(--text-muted)" }}>
          {stageLabel}
        </p>
      </div>

      {isError && (
        <div className="mt-8 w-full bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-sm text-red-500 animate-fade-in">
          <p className="font-medium">Something went wrong</p>
          <p className="mt-1 opacity-70 text-xs">{latestEvent?.error}</p>
        </div>
      )}
    </div>
  );
}
