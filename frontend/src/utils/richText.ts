import DOMPurify from "dompurify";

const HTML_TAG_PATTERN = /<[a-z][\s\S]*>/i;

export function looksLikeHtml(value: string | null | undefined): boolean {
  if (!value) return false;
  return HTML_TAG_PATTERN.test(value);
}

export function sanitizeRichHtml(value: string): string {
  return DOMPurify.sanitize(value, {
    USE_PROFILES: { html: true },
    ADD_ATTR: ["target", "rel"],
  });
}

/** Plain text from legacy saves → minimal HTML for the editor. */
export function toEditorHtml(value: string | null | undefined): string {
  const text = value?.trim() ?? "";
  if (!text) return "";
  if (looksLikeHtml(text)) return text;
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return `<p>${escaped.replace(/\n/g, "<br>")}</p>`;
}

/** Treat empty Quill output as blank. */
export function fromEditorHtml(value: string): string {
  const trimmed = value.trim();
  if (!trimmed || trimmed === "<p><br></p>" || trimmed === "<p></p>") return "";
  return value;
}
