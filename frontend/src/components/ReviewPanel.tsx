import { useState, useCallback } from "react";
import { useReportStore } from "../stores/reportStore";
import {
  updateFinding as apiUpdateFinding,
  reAnalyzeGroup as apiReAnalyze,
  movePhoto as apiMovePhoto,
  createNewGroup as apiCreateNewGroup,
  deleteGroup as apiDeleteGroup,
  updateGroup as apiUpdateGroup,
  getResults,
} from "../api/client";
import type { Finding } from "../types";
import PhotoGroupComponent from "./PhotoGroup";

export default function ReviewPanel() {
  const {
    sessionId, groups, findings, photosB64, photoAnalyses,
    setGroups, updateFinding, setFindings, removeFindingsForGroup, loadResults, setStep,
  } = useReportStore();

  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(groups[0]?.id || null);
  const [reAnalyzingGroupId, setReAnalyzingGroupId] = useState<string | null>(null);

  const findingForGroup = useCallback(
    (groupId: string): Finding | undefined => Object.values(findings).find((f) => f.group_id === groupId),
    [findings],
  );

  const handleUpdateFinding = useCallback(
    async (findingId: string, updates: Partial<Finding>) => {
      if (!sessionId) return;
      const updated = await apiUpdateFinding(sessionId, findingId, updates);
      updateFinding(findingId, updated);
    },
    [sessionId, updateFinding],
  );

  const handleReAnalyze = useCallback(
    async (groupId: string, hint: string) => {
      if (!sessionId) return;
      setReAnalyzingGroupId(groupId);
      try {
        const result = await apiReAnalyze(sessionId, groupId, hint);
        setFindings(result.findings);
      } finally {
        setReAnalyzingGroupId(null);
      }
    },
    [sessionId, setFindings],
  );

  const handleToggleKeyPhoto = useCallback(
    async (groupId: string, photoId: string) => {
      if (!sessionId) return;
      const group = groups.find((g) => g.id === groupId);
      if (!group) return;
      const isKey = group.key_photo_ids.includes(photoId);
      const newKeys = isKey
        ? group.key_photo_ids.filter((id) => id !== photoId)
        : [...group.key_photo_ids, photoId];
      if (newKeys.length === 0) return;
      await apiUpdateGroup(sessionId, groupId, { key_photo_ids: newKeys });
      setGroups(groups.map((g) => (g.id === groupId ? { ...g, key_photo_ids: newKeys } : g)));
    },
    [sessionId, groups, setGroups],
  );

  const handleMovePhotoToNew = useCallback(
    async (groupId: string, photoId: string) => {
      if (!sessionId) return;
      await apiCreateNewGroup(sessionId, photoId, groupId, "", "");
      const fresh = await getResults(sessionId);
      loadResults(fresh);
    },
    [sessionId, loadResults],
  );

  const handleMovePhotoTo = useCallback(
    async (photoId: string, sourceGroupId: string, targetGroupId: string) => {
      if (!sessionId) return;
      await apiMovePhoto(sessionId, photoId, sourceGroupId, targetGroupId);
      const fresh = await getResults(sessionId);
      loadResults(fresh);
    },
    [sessionId, loadResults],
  );

  const handleDeleteGroup = useCallback(
    async (groupId: string) => {
      if (!sessionId) return;
      await apiDeleteGroup(sessionId, groupId);
      setGroups(groups.filter((g) => g.id !== groupId));
      removeFindingsForGroup(groupId);
      if (selectedGroupId === groupId) setSelectedGroupId(groups[0]?.id || null);
    },
    [sessionId, groups, selectedGroupId, setGroups, removeFindingsForGroup],
  );

  const handleUpdateLabel = useCallback(
    async (groupId: string, label: string) => {
      if (!sessionId) return;
      await apiUpdateGroup(sessionId, groupId, { label });
      setGroups(groups.map((g) => (g.id === groupId ? { ...g, label } : g)));
    },
    [sessionId, groups, setGroups],
  );

  return (
    <div className="animate-fade-up space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold" style={{ color: "var(--text-primary)" }}>Review Findings</h2>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Edit, reorganize, and refine before generating your report.
          </p>
        </div>
        <button onClick={() => setStep("generate")} className="btn-primary px-6 py-2.5 text-sm shrink-0">
          Approve &amp; Continue
        </button>
      </div>

      <div className="space-y-3">
        {groups.map((group, i) => (
          <div key={group.id} className="animate-fade-in" style={{ animationDelay: `${i * 60}ms` }}>
            <PhotoGroupComponent
              group={group}
              finding={findingForGroup(group.id)}
              photosB64={photosB64}
              photoAnalyses={photoAnalyses}
              allGroups={groups}
              isSelected={selectedGroupId === group.id}
              onSelect={() => setSelectedGroupId(selectedGroupId === group.id ? null : group.id)}
              onUpdateFinding={handleUpdateFinding}
              onReAnalyze={handleReAnalyze}
              onToggleKeyPhoto={handleToggleKeyPhoto}
              onMovePhotoToNew={handleMovePhotoToNew}
              onMovePhotoTo={handleMovePhotoTo}
              onDeleteGroup={handleDeleteGroup}
              onUpdateLabel={handleUpdateLabel}
              reAnalyzing={reAnalyzingGroupId === group.id}
            />
          </div>
        ))}
      </div>

      {groups.length === 0 && (
        <div className="text-center py-16" style={{ color: "var(--text-muted)" }}>
          <p>No groups found. Go back and re-analyze.</p>
        </div>
      )}
    </div>
  );
}
