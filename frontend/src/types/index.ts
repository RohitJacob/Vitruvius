export interface PhotoMeta {
  id: string;
  filename: string;
  mime_type: string;
}

export interface PhotoAnalysis {
  photo_id: string;
  description: string;
  issues: string[];
  severity: string;
  location_hint: string;
  tags: string[];
}

export interface PhotoGroup {
  id: string;
  label: string;
  photo_ids: string[];
  key_photo_ids: string[];
}

export interface Finding {
  id: string;
  group_id: string;
  observation: string;
  potential_cause: string;
  recommendation: string;
  severity: string;
}

export interface TemplateField {
  name: string;
  field_type: "text" | "image" | "table" | "list";
  description: string;
  location_hint: string;
}

export interface TemplateSchema {
  format: string;
  sections: string[];
  fields: TemplateField[];
  findings_section: string;
  has_photo_placeholders: boolean;
  raw_instructions: string;
}

export interface AnalysisResults {
  groups: PhotoGroup[];
  findings: Record<string, Finding>;
  photo_analyses: Record<string, PhotoAnalysis>;
  template_schema: TemplateSchema | null;
  photos: Record<string, string>; // photo_id → base64
}

export interface PipelineEvent {
  stage: string;
  progress: number;
  message: string;
  error?: string | null;
}

export type AppStep = "upload" | "processing" | "review" | "generate";
