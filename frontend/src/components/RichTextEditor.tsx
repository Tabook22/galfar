import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import ReactQuill from "react-quill";
import type Quill from "quill";
import "react-quill/dist/quill.snow.css";

interface Props {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  minHeight?: string;
  ariaLabel?: string;
}

export default function RichTextEditor({
  value,
  onChange,
  disabled = false,
  minHeight = "140px",
  ariaLabel,
}: Props) {
  const { t } = useTranslation();

  const modules = useMemo(() => {
    const linkHandler = function (this: { quill: Quill }) {
      const quill = this.quill;
      const range = quill.getSelection(true);
      if (!range) return;

      const current = range.length > 0 ? quill.getFormat(range).link : "";
      const url = window.prompt(t("richEditor.linkPrompt"), typeof current === "string" ? current : "");
      if (url === null) return;

      if (url === "") {
        quill.format("link", false);
        return;
      }

      if (range.length === 0) {
        quill.insertText(range.index, url, "link", url);
        quill.setSelection(range.index + url.length, 0);
      } else {
        quill.format("link", url);
      }
    };

    const imageHandler = function (this: { quill: Quill }) {
      const quill = this.quill;
      const range = quill.getSelection(true);
      if (!range) return;

      const url = window.prompt(t("richEditor.imagePrompt"));
      if (!url?.trim()) return;

      quill.insertEmbed(range.index, "image", url.trim());
      quill.setSelection(range.index + 1, 0);
    };

    return {
      toolbar: {
        container: [
          [{ font: [] }, { size: [] }],
          ["bold", "italic", "underline", "strike"],
          [{ color: [] }, { background: [] }],
          [{ header: [1, 2, 3, false] }],
          [{ list: "ordered" }, { list: "bullet" }],
          [{ indent: "-1" }, { indent: "+1" }],
          [{ align: [] }],
          ["link", "image"],
          ["clean"],
        ],
        handlers: {
          link: linkHandler,
          image: imageHandler,
        },
      },
    };
  }, [t]);

  const formats = useMemo(
    () => [
      "font",
      "size",
      "bold",
      "italic",
      "underline",
      "strike",
      "color",
      "background",
      "header",
      "list",
      "indent",
      "align",
      "link",
      "image",
    ],
    []
  );

  return (
    <div className="rich-text-editor" style={{ ["--editor-min-height" as string]: minHeight }}>
      <ReactQuill
        theme="snow"
        value={value}
        onChange={onChange}
        modules={modules}
        formats={formats}
        readOnly={disabled}
        aria-label={ariaLabel}
      />
    </div>
  );
}
