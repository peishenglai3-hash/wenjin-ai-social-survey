/** Type definitions for coding / codebook / field-note domain. */

export interface CodebookCode {
  id: number;
  name: string;
  definition: string;
  example: string;
  exclusion_criteria: string;
  parent_code_id: number | null;
  paradigm: string;
  color: string;
  sort_order: number;
  version: number;
  created_at?: string;
}

export interface CodingAssignment {
  id: number;
  code_id: number;
  session_id: number;
  span_start: number;
  span_end: number;
  quote_text: string;
  coder_profile_id: number | null;
  is_ai_suggested: boolean;
  confidence: number;
}

export interface AISuggestion {
  name: string;
  definition: string;
  example?: string;
  paradigm?: string;
  confidence?: number;
}

export interface FieldNoteItem {
  id: number;
  session_id: number;
  project_id?: number;
  note_type: NoteType;
  content: string;
  tags: string[];
  ai_generated: boolean;
  ai_edited: boolean;
  timestamp_in_recording: number | null;
  created_at: string;
  updated_at?: string;
}

export type NoteType = "quote" | "observation" | "reflection" | "memo" | "methodology";

export const NOTE_TYPE_LABELS: Record<NoteType, string> = {
  quote: "引用",
  observation: "观察",
  reflection: "反思",
  memo: "备忘",
  methodology: "方法论",
};

export const NOTE_TYPE_ICONS: Record<NoteType, string> = {
  quote: "🟢",
  observation: "🔵",
  reflection: "🟣",
  memo: "🟡",
  methodology: "🔴",
};

export interface ReliabilityResult {
  kappa?: number;
  agreement_rate?: number;
  coder_count?: number;
  total_assignments?: number;
  details?: string;
}

export interface CodebookVersion {
  id: number;
  version_number: number;
  changelog: string;
}
