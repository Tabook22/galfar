import { getCurrentLanguage } from "../i18n";
import { apiClient } from "./client";

export interface SavedAnalysis {
  id: number;
  title: string;
  filename: string;
  source_type: "report" | "batch";
  source_name: string;
  report_id: number | null;
  batch_id: number | null;
  analysis_id: number | null;
  batch_analysis_id: number | null;
  created_at: string;
}

export interface SavedAnalysisDetail extends SavedAnalysis {
  content: Record<string, unknown>;
}

export interface SavedAnalysisCustomSection {
  title: string;
  content: string;
}

export interface UpdateSavedAnalysisPayload {
  title?: string;
  summary?: string;
  revenue?: string;
  expenses?: string;
  profit_loss?: string;
  cash_flow?: string;
  assets?: string;
  liabilities?: string;
  risks?: string;
  strengths?: string;
  weaknesses?: string;
  recommendations?: string;
  custom_sections?: SavedAnalysisCustomSection[];
  document_html?: string;
}

export async function listSavedAnalyses(): Promise<SavedAnalysis[]> {
  return apiClient.request("/api/saved-analyses");
}

export async function getSavedAnalysis(id: number): Promise<SavedAnalysisDetail> {
  return apiClient.request(`/api/saved-analyses/${id}`);
}

export async function saveReportAnalysis(
  reportId: number,
  title: string,
  analysisId?: number
): Promise<SavedAnalysis> {
  return apiClient.request(`/api/saved-analyses/reports/${reportId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, analysis_id: analysisId ?? null }),
  });
}

export async function saveBatchAnalysis(
  batchId: number,
  title: string,
  batchAnalysisId?: number
): Promise<SavedAnalysis> {
  return apiClient.request(`/api/saved-analyses/batches/${batchId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, batch_analysis_id: batchAnalysisId ?? null }),
  });
}

export async function deleteSavedAnalysis(id: number): Promise<void> {
  return apiClient.request(`/api/saved-analyses/${id}`, { method: "DELETE" });
}

export async function deleteSavedAnalyses(ids: number[]): Promise<{ deleted_count: number }> {
  return apiClient.request("/api/saved-analyses/bulk-delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ saved_ids: ids }),
  });
}

export async function updateSavedAnalysis(
  id: number,
  payload: UpdateSavedAnalysisPayload
): Promise<SavedAnalysisDetail> {
  return apiClient.request(`/api/saved-analyses/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function reanalyzeSavedAnalysis(
  id: number,
  criteria: string
): Promise<SavedAnalysisDetail> {
  return apiClient.request(`/api/saved-analyses/${id}/reanalyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ criteria, language: getCurrentLanguage() }),
  });
}
