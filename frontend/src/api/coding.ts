/** API helpers for coding, codebook, and field-note endpoints. */
import api from "./client";
import type {
  CodebookCode,
  CodingAssignment,
  AISuggestion,
  FieldNoteItem,
  ReliabilityResult,
  CodebookVersion,
} from "../types/coding";

// ── Codebook CRUD ──────────────────────────────────────────

export async function fetchCodebook(
  projectId: number,
  paradigm?: string,
): Promise<{ codes: CodebookCode[]; total: number }> {
  const params: Record<string, string> = {};
  if (paradigm) params.paradigm = paradigm;
  const res = await api.get(`/coding/codebooks/${projectId}`, { params });
  return res.data;
}

export async function createCode(
  projectId: number,
  data: {
    name: string;
    definition?: string;
    example?: string;
    exclusion_criteria?: string;
    parent_code_id?: number | null;
    paradigm?: string;
    color?: string;
    created_by_profile_id?: number;
  },
): Promise<{ id: number; name: string; paradigm: string }> {
  const res = await api.post(`/coding/codebooks/${projectId}/codes`, data);
  return res.data;
}

export async function updateCode(
  codeId: number,
  data: Partial<CodebookCode>,
): Promise<{ id: number; name: string; definition: string }> {
  const res = await api.patch(`/coding/codebooks/codes/${codeId}`, data);
  return res.data;
}

export async function deleteCode(codeId: number): Promise<{ deleted: boolean; id: number }> {
  const res = await api.delete(`/coding/codebooks/codes/${codeId}`);
  return res.data;
}

// ── AI Suggestions ─────────────────────────────────────────

export async function suggestCodes(
  transcript: string,
  researchQuestion: string,
  projectId: number,
  codingParadigm?: string,
): Promise<{ suggestions: AISuggestion[]; count: number }> {
  const res = await api.post("/coding/suggest", {
    transcript,
    research_question: researchQuestion,
    project_id: projectId,
    coding_paradigm: codingParadigm || "auto",
  });
  return res.data;
}

// ── Coding Assignments ─────────────────────────────────────

export async function createAssignment(data: {
  code_id: number;
  session_id: number;
  span_start: number;
  span_end: number;
  quote_text: string;
  coder_profile_id?: number;
  is_ai_suggested?: boolean;
  confidence?: number;
}): Promise<{ id: number; code_id: number; session_id: number }> {
  const res = await api.post("/coding/assign", data);
  return res.data;
}

export async function fetchAssignments(
  sessionId: number,
): Promise<{ assignments: CodingAssignment[]; total: number }> {
  const res = await api.get(`/coding/assignments/${sessionId}`);
  return res.data;
}

export async function deleteAssignment(
  assignmentId: number,
): Promise<{ deleted: boolean; id: number }> {
  const res = await api.delete(`/coding/assignments/${assignmentId}`);
  return res.data;
}

// ── Reliability ────────────────────────────────────────────

export async function fetchReliability(sessionId: number): Promise<ReliabilityResult> {
  const res = await api.get(`/coding/reliability/${sessionId}`);
  return res.data;
}

// ── Export ─────────────────────────────────────────────────

export async function exportCodebook(
  projectId: number,
  format: "markdown" | "json" = "markdown",
): Promise<string> {
  const res = await api.get(`/coding/export/${projectId}`, { params: { fmt: format } });
  return res.data;
}

// ── Version Snapshot ───────────────────────────────────────

export async function snapshotCodebook(
  projectId: number,
  changelog?: string,
  createdByProfileId?: number,
): Promise<CodebookVersion> {
  const res = await api.post(`/coding/versions/${projectId}`, {
    changelog: changelog || "",
    created_by_profile_id: createdByProfileId,
  });
  return res.data;
}

// ── Field Notes ────────────────────────────────────────────

export async function fetchFieldNotes(sessionId?: number): Promise<FieldNoteItem[]> {
  const params: Record<string, string> = {};
  if (sessionId) params.session_id = String(sessionId);
  const res = await api.get("/fieldwork/field-notes", { params });
  return Array.isArray(res.data) ? res.data : res.data?.notes || [];
}

export async function createFieldNote(data: {
  session_id: number;
  project_id?: number;
  note_type?: string;
  content: string;
  tags?: string[];
  timestamp_in_recording?: number;
  ai_generated?: boolean;
}): Promise<FieldNoteItem> {
  const res = await api.post("/fieldwork/field-notes", data);
  return res.data;
}

export async function updateFieldNote(
  noteId: number,
  data: Partial<FieldNoteItem>,
): Promise<FieldNoteItem> {
  const res = await api.patch(`/fieldwork/field-notes/${noteId}`, data);
  return res.data;
}

export async function deleteFieldNote(
  noteId: number,
): Promise<{ deleted: boolean; id: number }> {
  const res = await api.delete(`/fieldwork/field-notes/${noteId}`);
  return res.data;
}
