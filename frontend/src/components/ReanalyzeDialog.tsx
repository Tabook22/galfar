import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

interface Props {
  open: boolean;
  saving?: boolean;
  onClose: () => void;
  onSubmit: (criteria: string) => Promise<void>;
}

export default function ReanalyzeDialog({ open, saving, onClose, onSubmit }: Props) {
  const { t } = useTranslation();
  const [criteria, setCriteria] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setCriteria("");
      setError(null);
    }
  }, [open]);

  if (!open) return null;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = criteria.trim();
    if (!trimmed) {
      setError(t("savedAnalyses.reanalyzeCriteriaRequired"));
      return;
    }
    setError(null);
    try {
      await onSubmit(trimmed);
      onClose();
    } catch {
      // parent handles API error display
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="card modal-card" onClick={(e) => e.stopPropagation()}>
        <h2 style={{ marginTop: 0 }}>{t("savedAnalyses.reanalyzeDialogTitle")}</h2>
        <p className="muted">{t("savedAnalyses.reanalyzeDialogHint")}</p>
        <form onSubmit={(e) => void handleSubmit(e)}>
          <label htmlFor="reanalyze-criteria" className="edit-field">
            <span>{t("savedAnalyses.reanalyzeCriteriaLabel")}</span>
            <textarea
              id="reanalyze-criteria"
              rows={6}
              value={criteria}
              onChange={(e) => setCriteria(e.target.value)}
              placeholder={t("savedAnalyses.reanalyzeCriteriaPlaceholder")}
              disabled={saving}
              autoFocus
            />
          </label>
          {error && <div className="error" style={{ marginBottom: "0.75rem" }}>{error}</div>}
          <div className="action-buttons">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
              {t("savedAnalyses.cancel")}
            </button>
            <button type="submit" className="btn" disabled={saving || !criteria.trim()}>
              {saving ? t("savedAnalyses.reanalyzing") : t("savedAnalyses.reanalyze")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
