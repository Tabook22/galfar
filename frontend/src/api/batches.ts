import { getCurrentLanguage } from "../i18n";
import { apiClient } from "./client";
import type { Report } from "./reports";

export interface ReportBatch {
  id: number;
  name: string;
  status: string;
  report_count: number;
  has_analysis: boolean;
  latest_analysis_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface BatchDetail extends ReportBatch {
  reports: Report[];
}

export interface BatchAnalysis {
  id: number;
  batch_id: number;
  status: string;
  report_count: number;
  summary: string | null;
  revenue: string | null;
  expenses: string | null;
  profit_loss: string | null;
  cash_flow: string | null;
  assets: string | null;
  liabilities: string | null;
  risks: string | null;
  strengths: string | null;
  weaknesses: string | null;
  recommendations: string | null;
  error_message: string | null;
  created_at: string;
}

export interface BatchChatMessage {
  id: number;
  batch_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface BatchReportAnalysisItem {
  report_id: number;
  original_filename: string;
  analysis: import("./reports").Analysis | null;
}

export interface BatchReportAnalyses {
  batch_id: number;
  items: BatchReportAnalysisItem[];
}

function languageField(): Record<string, string> {
  return { language: getCurrentLanguage() };
}

export async function listBatches(): Promise<ReportBatch[]> {
  return apiClient.request("/api/batches");
}

export async function getBatch(id: number): Promise<BatchDetail> {
  return apiClient.request(`/api/batches/${id}`);
}

export async function uploadBatch(files: File[], name?: string): Promise<BatchDetail> {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  if (name?.trim()) form.append("name", name.trim());
  return apiClient.request("/api/batches", { method: "POST", body: form });
}

export async function deleteBatch(id: number): Promise<void> {
  return apiClient.request(`/api/batches/${id}`, { method: "DELETE" });
}

export async function runBatchAnalysis(batchId: number, force = false): Promise<BatchAnalysis> {
  return apiClient.request(`/api/batches/${batchId}/analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ force, ...languageField() }),
  });
}

export async function getLatestBatchAnalysis(batchId: number): Promise<BatchAnalysis> {
  return apiClient.request(`/api/batches/${batchId}/analysis/latest`);
}

export async function listBatchAnalysisHistory(batchId: number): Promise<BatchAnalysis[]> {
  return apiClient.request(`/api/batches/${batchId}/analysis/history`);
}

export async function getBatchReportAnalyses(batchId: number): Promise<BatchReportAnalyses> {
  return apiClient.request(`/api/batches/${batchId}/report-analyses`);
}

export async function listBatchChatMessages(batchId: number): Promise<BatchChatMessage[]> {
  return apiClient.request(`/api/batches/${batchId}/chat`);
}

export async function sendBatchChatMessage(
  batchId: number,
  message: string
): Promise<{ user_message: BatchChatMessage; assistant_message: BatchChatMessage }> {
  return apiClient.request(`/api/batches/${batchId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, ...languageField() }),
  });
}
