import axios from "axios";
import type {
  AnalysisResults,
  Finding,
  PhotoGroup,
  PipelineEvent,
} from "../types";

const api = axios.create({ baseURL: "/api" });

export async function uploadFiles(
  photos: File[],
  template: File | null,
): Promise<{ session_id: string; photo_count: number }> {
  const form = new FormData();
  photos.forEach((f) => form.append("photos", f));
  if (template) form.append("template", template);

  const { data } = await api.post("/upload", form);
  return data;
}

export function startAnalysis(
  sessionId: string,
  onEvent: (evt: PipelineEvent) => void,
  onDone: () => void,
  onError: (err: string) => void,
): () => void {
  const ctrl = new AbortController();

  (async () => {
    try {
      const resp = await fetch(`/api/sessions/${sessionId}/analyze`, {
        method: "POST",
        signal: ctrl.signal,
      });
      if (!resp.ok || !resp.body) {
        onError(`HTTP ${resp.status}`);
        return;
      }
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const chunk of lines) {
          const dataLine = chunk
            .split("\n")
            .find((l) => l.startsWith("data: "));
          if (dataLine) {
            try {
              const evt: PipelineEvent = JSON.parse(dataLine.slice(6));
              onEvent(evt);
            } catch {
              // ignore parse errors
            }
          }
        }
      }
      onDone();
    } catch (err: unknown) {
      if (!ctrl.signal.aborted) {
        onError(err instanceof Error ? err.message : String(err));
      }
    }
  })();

  return () => ctrl.abort();
}

export async function getResults(
  sessionId: string,
): Promise<AnalysisResults> {
  const { data } = await api.get(`/sessions/${sessionId}/results`);
  return data;
}

export async function updateFinding(
  sessionId: string,
  findingId: string,
  updates: Partial<Finding>,
): Promise<Finding> {
  const { data } = await api.patch(
    `/sessions/${sessionId}/findings/${findingId}`,
    updates,
  );
  return data;
}

export async function movePhoto(
  sessionId: string,
  photoId: string,
  sourceGroupId: string,
  targetGroupId: string | null,
): Promise<{ groups: PhotoGroup[] }> {
  const { data } = await api.post(`/sessions/${sessionId}/move-photo`, {
    photo_id: photoId,
    source_group_id: sourceGroupId,
    target_group_id: targetGroupId,
  });
  return data;
}

export async function reAnalyzeGroup(
  sessionId: string,
  groupId: string,
  hint: string = "",
): Promise<{ findings: Record<string, Finding> }> {
  const { data } = await api.post(`/sessions/${sessionId}/re-analyze`, {
    group_id: groupId,
    hint,
  });
  return data;
}

export async function createNewGroup(
  sessionId: string,
  photoId: string,
  sourceGroupId: string,
  label: string = "",
  hint: string = "",
): Promise<{ group: PhotoGroup; findings: Record<string, Finding> }> {
  const { data } = await api.post(`/sessions/${sessionId}/new-group`, {
    photo_id: photoId,
    source_group_id: sourceGroupId,
    label,
    hint,
  });
  return data;
}

export async function deleteGroup(
  sessionId: string,
  groupId: string,
): Promise<void> {
  await api.delete(`/sessions/${sessionId}/groups/${groupId}`);
}

export async function updateGroup(
  sessionId: string,
  groupId: string,
  updates: Partial<PhotoGroup>,
): Promise<PhotoGroup> {
  const { data } = await api.put(
    `/sessions/${sessionId}/groups/${groupId}`,
    updates,
  );
  return data;
}

export function getDownloadUrl(sessionId: string): string {
  return `/api/sessions/${sessionId}/download`;
}

export function getDocxDownloadUrl(sessionId: string): string {
  return `/api/sessions/${sessionId}/download-docx`;
}
