import { useTranslation } from "react-i18next";
import { looksLikeHtml, sanitizeRichHtml } from "../utils/richText";

interface Props {
  value: string | null | undefined;
  emptyLabel?: string;
}

export default function RichTextContent({ value, emptyLabel }: Props) {
  const { t } = useTranslation();
  const text = value?.trim();
  const fallback = emptyLabel ?? t("common.notAvailable");

  if (!text) {
    return <p className="rich-text-empty">{fallback}</p>;
  }

  if (looksLikeHtml(text)) {
    return (
      <div
        className="rich-text-content"
        dangerouslySetInnerHTML={{ __html: sanitizeRichHtml(text) }}
      />
    );
  }

  return <p className="rich-text-plain">{text}</p>;
}
