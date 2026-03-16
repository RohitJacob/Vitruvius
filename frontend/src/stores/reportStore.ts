import { create } from "zustand";
import type {
  AnalysisResults,
  AppStep,
  Finding,
  PhotoAnalysis,
  PhotoGroup,
  PipelineEvent,
  TemplateSchema,
} from "../types";

interface ReportState {
  step: AppStep;
  sessionId: string | null;

  // Upload state
  photoFiles: File[];
  templateFile: File | null;

  // Pipeline state
  pipelineEvents: PipelineEvent[];
  latestEvent: PipelineEvent | null;

  // Analysis results
  groups: PhotoGroup[];
  findings: Record<string, Finding>;
  photoAnalyses: Record<string, PhotoAnalysis>;
  templateSchema: TemplateSchema | null;
  photosB64: Record<string, string>;

  // Actions
  setStep: (step: AppStep) => void;
  setSessionId: (id: string) => void;
  setPhotoFiles: (files: File[]) => void;
  setTemplateFile: (file: File | null) => void;
  addPipelineEvent: (evt: PipelineEvent) => void;
  loadResults: (results: AnalysisResults) => void;
  setGroups: (groups: PhotoGroup[]) => void;
  updateFinding: (id: string, finding: Finding) => void;
  setFindings: (findings: Record<string, Finding>) => void;
  removeFindingsForGroup: (groupId: string) => void;
  reset: () => void;
}

const initialState = {
  step: "upload" as AppStep,
  sessionId: null,
  photoFiles: [],
  templateFile: null,
  pipelineEvents: [],
  latestEvent: null,
  groups: [],
  findings: {},
  photoAnalyses: {},
  templateSchema: null,
  photosB64: {},
};

export const useReportStore = create<ReportState>((set) => ({
  ...initialState,

  setStep: (step) => set({ step }),
  setSessionId: (sessionId) => set({ sessionId }),
  setPhotoFiles: (photoFiles) => set({ photoFiles }),
  setTemplateFile: (templateFile) => set({ templateFile }),

  addPipelineEvent: (evt) =>
    set((s) => ({
      pipelineEvents: [...s.pipelineEvents, evt],
      latestEvent: evt,
    })),

  loadResults: (results) =>
    set({
      groups: results.groups,
      findings: results.findings,
      photoAnalyses: results.photo_analyses,
      templateSchema: results.template_schema,
      photosB64: results.photos,
    }),

  setGroups: (groups) => set({ groups }),

  updateFinding: (id, finding) =>
    set((s) => ({ findings: { ...s.findings, [id]: finding } })),

  setFindings: (findings) =>
    set((s) => ({ findings: { ...s.findings, ...findings } })),

  removeFindingsForGroup: (groupId) =>
    set((s) => {
      const next = { ...s.findings };
      for (const [k, v] of Object.entries(next)) {
        if (v.group_id === groupId) delete next[k];
      }
      return { findings: next };
    }),

  reset: () => set(initialState),
}));
