import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import { uploadBatch } from "../api/batches";
import UploadBox from "../components/UploadBox";

export default function UploadBatch() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (files: File[]) => {
    if (files.length < 2) {
      setError(t("batch.upload.minFiles"));
      return;
    }
    setError(null);
    setSuccess(null);
    setUploading(true);
    try {
      const batch = await uploadBatch(files, name || undefined);
      setSuccess(t("batch.upload.success", { count: batch.report_count, name: batch.name }));
      setTimeout(() => navigate(`/batches/${batch.id}`), 900);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.uploadFailed"));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>{t("batch.upload.title")}</h1>
      <p className="muted">{t("batch.upload.subtitle")}</p>
      <div className="card" style={{ marginBottom: "1rem" }}>
        <label htmlFor="batch-name" style={{ display: "block", marginBottom: "0.35rem", fontWeight: 600 }}>
          {t("batch.upload.nameLabel")}
        </label>
        <input
          id="batch-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t("batch.upload.namePlaceholder")}
          disabled={uploading}
          style={{ width: "100%", padding: "0.65rem 0.85rem", borderRadius: 8, border: "1px solid #cbd5e1" }}
        />
      </div>
      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}
      <UploadBox onUpload={handleUpload} disabled={uploading} multiple />
      {uploading && <p className="muted">{t("upload.uploading")}</p>}
    </div>
  );
}
