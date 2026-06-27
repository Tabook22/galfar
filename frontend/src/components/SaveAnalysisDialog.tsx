import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

interface Props {
  open: boolean;
  defaultTitle?: string;
  saving?: boolean;
  onClose: () => void;
  onSave: (title: string) => Promise<void>;
}

export default function SaveAnalysisDialog({ open, defaultTitle = "", saving, onClose, onSave }: Props) {
  const { t } = useTranslation();
  const [title, setTitle] = useState(defaultTitle);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setTitle(defaultTitle);
      setError(null);
    }
  }, [open, defaultTitle]);

  if (!open) return null;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = title.trim();
    if (!trimmed) {
      setError(t("savedAnalyses.titleRequired"));
      return;
    }
    setError(null);
    try {
      await onSave(trimmed);
      onClose();
    } catch {
      // parent handles API error display
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="card modal-card" onClick={(e) => e.stopPropagation()}>
        <h2 style={{ marginTop: 0 }}>{t("savedAnalyses.saveDialogTitle")}</h2>
        <p className="muted">{t("savedAnalyses.saveDialogHint")}</p>
        <form onSubmit={(e) => void handleSubmit(e)}>
          <label htmlFor="save-title" style={{ display: "block", marginBottom: "0.35rem", fontWeight: 600 }}>
            {t("savedAnalyses.titleLabel")}
          </label>
          <input
            id="save-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={t("savedAnalyses.titlePlaceholder")}
            disabled={saving}
            autoFocus
            style={{ width: "100%", padding: "0.65rem 0.85rem", borderRadius: 8, border: "1px solid #cbd5e1", marginBottom: "0.75rem" }}
          />
          {error && <div className="error" style={{ marginBottom: "0.75rem" }}>{error}</div>}
          <div className="action-buttons">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
              {t("savedAnalyses.cancel")}
            </button>
            <button type="submit" className="btn" disabled={saving || !title.trim()}>
              {saving ? t("savedAnalyses.saving") : t("savedAnalyses.saveButton")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
