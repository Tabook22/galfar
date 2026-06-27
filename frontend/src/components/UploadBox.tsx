import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";

interface Props {
  onUpload: (files: File[]) => Promise<void>;
  disabled?: boolean;
  multiple?: boolean;
}

export default function UploadBox({ onUpload, disabled, multiple = false }: Props) {
  const { t } = useTranslation();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [selected, setSelected] = useState<File[]>([]);

  const handleFiles = async (fileList: FileList | null) => {
    if (!fileList?.length || disabled) return;
    const files = Array.from(fileList);
    if (multiple) {
      setSelected(files);
      await onUpload(files);
    } else {
      await onUpload([files[0]]);
    }
    if (inputRef.current) inputRef.current.value = "";
    if (!multiple) setSelected([]);
  };

  return (
    <div
      className="card"
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        void handleFiles(e.dataTransfer.files);
      }}
      style={{
        borderStyle: "dashed",
        textAlign: "center",
        background: dragOver ? "#eff6ff" : "#fff",
      }}
    >
      <p style={{ marginTop: 0 }}>
        {multiple ? t("batch.upload.dragDrop") : t("upload.dragDrop")}
      </p>
      <p className="muted">{t("upload.supported")}</p>
      {multiple && selected.length > 0 && (
        <p className="muted">{t("batch.upload.selected", { count: selected.length })}</p>
      )}
      <input
        ref={inputRef}
        type="file"
        multiple={multiple}
        accept=".pdf,.txt,.csv,.xlsx,.xls,.docx"
        style={{ display: "none" }}
        onChange={(e) => void handleFiles(e.target.files)}
      />
      <button className="btn" disabled={disabled} onClick={() => inputRef.current?.click()}>
        {multiple ? t("batch.upload.chooseFiles") : t("common.chooseFile")}
      </button>
    </div>
  );
}
