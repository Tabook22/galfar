import { getCurrentLanguage } from "../i18n";
import { apiClient } from "./client";

export interface Report {
  id: number;
  batch_id?: number | null;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: string;
  created_at: string;
  updated_at: string;
  has_analysis: boolean;
  latest_analysis_id: number | null;
}

export interface ListReportsParams {
  search?: string;
  category?: string;
  sort_by?: "name" | "date" | "category";
  sort_order?: "asc" | "desc";
}

export interface ReportDetail extends Report {
  extracted_text_preview: string | null;
  analysis_count: number;
  chat_message_count: number;
}

export interface Analysis {
  id: number;
  report_id: number;
  status: string;
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

export interface ChatMessage {
  id: number;
  report_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface DashboardStats {
  total_reports: number;
  analyzed_reports: number;
  pending_reports: number;
  total_chat_messages: number;
}

function languageBody(extra: Record<string, unknown> = {}): string {
  return JSON.stringify({ language: getCurrentLanguage(), ...extra });
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return apiClient.request("/api/reports/stats/dashboard");
}

export async function listReports(params: ListReportsParams = {}): Promise<Report[]> {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.category) query.set("category", params.category);
  if (params.sort_by) query.set("sort_by", params.sort_by);
  if (params.sort_order) query.set("sort_order", params.sort_order);
  const qs = query.toString();
  return apiClient.request(`/api/reports${qs ? `?${qs}` : ""}`);
}

export async function listReportCategories(): Promise<string[]> {
  return apiClient.request("/api/reports/categories");
}

export async function getReport(id: number): Promise<ReportDetail> {
  return apiClient.request(`/api/reports/${id}`);
}

export function getReportDownloadUrl(id: number): string {
  return `/api/reports/${id}/download`;
}

export async function uploadReport(file: File): Promise<Report> {
  const form = new FormData();
  form.append("file", file);
  return apiClient.request("/api/reports", { method: "POST", body: form, timeoutMs: 60000 });
}

export async function deleteReport(id: number): Promise<void> {
  return apiClient.request(`/api/reports/${id}`, { method: "DELETE" });
}

export async function deleteReports(ids: number[]): Promise<{ deleted_count: number }> {
  return apiClient.request("/api/reports/bulk-delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ report_ids: ids }),
  });
}

export async function runAnalysis(reportId: number, force = false): Promise<Analysis> {
  return apiClient.request(`/api/reports/${reportId}/analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: languageBody({ force }),
  });
}

export async function getLatestAnalysis(reportId: number): Promise<Analysis> {
  return apiClient.request(`/api/reports/${reportId}/analysis/latest`);
}

export async function listChatMessages(reportId: number): Promise<ChatMessage[]> {
  return apiClient.request(`/api/reports/${reportId}/chat`);
}

export async function sendChatMessage(
  reportId: number,
  message: string
): Promise<{ user_message: ChatMessage; assistant_message: ChatMessage }> {
  return apiClient.request(`/api/reports/${reportId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: languageBody({ message }),
  });
}
