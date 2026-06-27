import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import { uploadReport } from "../api/reports";
import UploadBox from "../components/UploadBox";

export default function UploadReport() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (files: File[]) => {
    const file = files[0];
    if (!file) return;
    setError(null);
    setSuccess(null);
    setUploading(true);
    try {
      const report = await uploadReport(file);
      setSuccess(t("upload.success", { filename: report.original_filename }));
      setTimeout(() => navigate(`/reports/${report.id}`), 800);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.uploadFailed"));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>{t("upload.title")}</h1>
      <p className="muted">{t("upload.subtitle")}</p>
      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}
      <UploadBox onUpload={handleUpload} disabled={uploading} />
      {uploading && <p className="muted">{t("upload.uploading")}</p>}
    </div>
  );
}
