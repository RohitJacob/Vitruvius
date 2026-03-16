import { useState, useMemo } from "react";
import type { Finding, PhotoAnalysis, PhotoGroup as PhotoGroupType } from "../types";
import PhotoCard from "./PhotoCard";
import AnalysisEditor from "./AnalysisEditor";

interface PhotoGroupProps {
  group: PhotoGroupType;
  finding: Finding | undefined;
  photosB64: Record<string, string>;
  photoAnalyses: Record<string, PhotoAnalysis>;
  allGroups: PhotoGroupType[];
  isSelected: boolean;
  onSelect: () => void;
  onUpdateFinding: (id: string, updates: Partial<Finding>) => void;
  onReAnalyze: (groupId: string, hint: string) => void;
  onToggleKeyPhoto: (groupId: string, photoId: string) => void;
  onMovePhotoToNew: (groupId: string, photoId: string) => void;
  onMovePhotoTo: (photoId: string, sourceGroupId: string, targetGroupId: string) => void;
  onDeleteGroup: (groupId: string) => void;
  onUpdateLabel: (groupId: string, label: string) => void;
  reAnalyzing?: boolean;
}

export default function PhotoGroupComponent({
  group, finding, photosB64, photoAnalyses, allGroups, isSelected,
  onSelect, onUpdateFinding, onReAnalyze, onToggleKeyPhoto, onMovePhotoToNew,
  onMovePhotoTo, onDeleteGroup, onUpdateLabel, reAnalyzing,
}: PhotoGroupProps) {
  const [editingLabel, setEditingLabel] = useState(false);
  const [labelDraft, setLabelDraft] = useState(group.label);
  const [movePhotoId, setMovePhotoId] = useState<string | null>(null);

  const otherGroups = useMemo(
    () => allGroups.filter((g) => g.id !== group.id),
    [allGroups, group.id],
  );

  return (
    <div className={`card rounded-2xl transition-all duration-300 ${
      isSelected ? "ring-1 ring-brand-500/40 glow-brand" : "card-hover"
    }`}>
      {/* Header */}
      <div onClick={onSelect} className="flex items-center justify-between p-4 cursor-pointer">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className={`w-2 h-2 rounded-full transition-colors ${isSelected ? "bg-brand-500" : "bg-[var(--border)]"}`} />
          {editingLabel ? (
            <input
              value={labelDraft}
              onChange={(e) => setLabelDraft(e.target.value)}
              onBlur={() => { onUpdateLabel(group.id, labelDraft); setEditingLabel(false); }}
              onKeyDown={(e) => { if (e.key === "Enter") { onUpdateLabel(group.id, labelDraft); setEditingLabel(false); } }}
              onClick={(e) => e.stopPropagation()}
              autoFocus
              className="input-field text-sm font-semibold py-1"
            />
          ) : (
            <h3
              className="text-sm font-semibold truncate cursor-text"
              style={{ color: "var(--text-primary)" }}
              onDoubleClick={(e) => { e.stopPropagation(); setLabelDraft(group.label); setEditingLabel(true); }}
            >
              {group.label}
            </h3>
          )}
          <span className="text-[10px] px-2 py-0.5 rounded-full shrink-0" style={{ color: "var(--text-muted)", background: "var(--bg-secondary)" }}>
            {group.photo_ids.length} photo{group.photo_ids.length !== 1 && "s"}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button onClick={(e) => { e.stopPropagation(); onSelect(); }} className="btn-ghost p-1.5">
            <svg className={`w-4 h-4 transition-transform duration-200 ${isSelected ? "rotate-180" : ""}`} style={{ color: "var(--text-muted)" }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); if (confirm("Delete this group and its finding?")) onDeleteGroup(group.id); }}
            className="btn-ghost p-1.5 hover:!text-red-500 hover:!bg-red-500/10"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      {/* Expanded */}
      {isSelected && (
        <div className="p-4 space-y-4 animate-slide-in" style={{ borderTop: "1px solid var(--border)" }}>
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
            {group.photo_ids.map((pid) => {
              const b64 = photosB64[pid];
              if (!b64) return null;
              const analysis = photoAnalyses[pid];
              return (
                <PhotoCard
                  key={pid}
                  photoId={pid}
                  b64={b64}
                  mime="image/jpeg"
                  isKey={group.key_photo_ids.includes(pid)}
                  filename={analysis?.description?.slice(0, 40)}
                  onToggleKey={() => onToggleKeyPhoto(group.id, pid)}
                  onMoveOut={() => onMovePhotoToNew(group.id, pid)}
                  selected={movePhotoId === pid}
                  onSelect={() => setMovePhotoId(movePhotoId === pid ? null : pid)}
                />
              );
            })}
          </div>

          {movePhotoId && otherGroups.length > 0 && (
            <div className="bg-brand-500/5 border border-brand-500/15 rounded-xl p-3 animate-fade-in">
              <p className="text-xs font-medium text-brand-600 dark:text-brand-400 mb-2">Move photo to:</p>
              <div className="flex flex-wrap gap-1.5">
                {otherGroups.map((g) => (
                  <button
                    key={g.id}
                    onClick={() => { onMovePhotoTo(movePhotoId, group.id, g.id); setMovePhotoId(null); }}
                    className="text-xs px-2.5 py-1 rounded-lg transition-all card card-hover"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {g.label}
                  </button>
                ))}
                <button onClick={() => setMovePhotoId(null)} className="text-xs px-2 py-1" style={{ color: "var(--text-muted)" }}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          {finding && (
            <AnalysisEditor
              finding={finding}
              onSave={(updates) => onUpdateFinding(finding.id, updates)}
              onReAnalyze={(hint) => onReAnalyze(group.id, hint)}
              loading={reAnalyzing}
            />
          )}
        </div>
      )}
    </div>
  );
}
