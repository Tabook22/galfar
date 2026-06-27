import { toEditorHtml } from "./richText";

const SECTION_KEYS = [
  "summary",
  "revenue",
  "expenses",
  "profitLoss",
  "cashFlow",
  "assets",
  "liabilities",
  "risks",
  "strengths",
  "weaknesses",
  "recommendations",
] as const;

type SectionKey = (typeof SECTION_KEYS)[number];

const API_FIELD_MAP: Record<SectionKey, string> = {
  summary: "summary",
  revenue: "revenue",
  expenses: "expenses",
  profitLoss: "profit_loss",
  cashFlow: "cash_flow",
  assets: "assets",
  liabilities: "liabilities",
  risks: "risks",
  strengths: "strengths",
  weaknesses: "weaknesses",
  recommendations: "recommendations",
};

function readField(obj: Record<string, unknown> | undefined, key: string): string {
  const value = obj?.[key];
  return typeof value === "string" ? value : value != null ? String(value) : "";
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function readCustomSections(content: Record<string, unknown>): Array<{ title: string; content: string }> {
  if (!Array.isArray(content.custom_sections)) return [];
  return content.custom_sections
    .filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null)
    .map((item) => ({
      title: typeof item.title === "string" ? item.title : "",
      content: typeof item.content === "string" ? item.content : "",
    }));
}

function getAnalysisRecord(content: Record<string, unknown>, sourceType: string) {
  return (sourceType === "batch" ? content.combined_analysis : content.analysis) as
    | Record<string, unknown>
    | undefined;
}

/** Build one HTML document from stored sections (legacy) or return saved document_html. */
export function resolveSavedAnalysisDocument(
  content: Record<string, unknown>,
  sourceType: string,
  sectionLabel: (key: SectionKey) => string
): string {
  const saved = content.document_html;
  if (typeof saved === "string" && saved.trim()) {
    return saved;
  }

  const analysis = getAnalysisRecord(content, sourceType);
  const parts: string[] = [];

  for (const key of SECTION_KEYS) {
    const value = readField(analysis, API_FIELD_MAP[key]).trim();
    if (!value) continue;
    parts.push(`<h2>${escapeHtml(sectionLabel(key))}</h2>`);
    parts.push(toEditorHtml(value));
  }

  for (const section of readCustomSections(content)) {
    const title = section.title.trim();
    if (!title) continue;
    parts.push(`<h2>${escapeHtml(title)}</h2>`);
    parts.push(toEditorHtml(section.content));
  }

  return parts.join("") || "<p><br></p>";
}

/** Prepare document HTML for the rich text editor. */
export function toEditorDocument(html: string): string {
  const trimmed = html.trim();
  return trimmed || "<p><br></p>";
}

export { SECTION_KEYS, API_FIELD_MAP, readField };
