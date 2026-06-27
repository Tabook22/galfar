import { FormEvent, lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import {
  companyLogoSrc,
  deleteCompanyLogo,
  hasRequiredBranding,
  updateCompanySettings,
  uploadCompanyLogo,
  type CompanySettings,
  type UpdateCompanySettingsPayload,
} from "../api/settings";
import BilingualField from "../components/BilingualField";
import CompanyProfile from "../components/CompanyProfile";
import ConfirmDialog from "../components/ConfirmDialog";
import { useCompanyBranding, useCompanySettings } from "../context/CompanySettingsContext";
import { useConfirmDialog } from "../hooks/useConfirmDialog";
import { fromEditorHtml, toEditorHtml } from "../utils/richText";

const RichTextEditor = lazy(() => import("../components/RichTextEditor"));

type FormState = UpdateCompanySettingsPayload;

function toFormState(settings: CompanySettings): FormState {
  return {
    company_name: { ...settings.company_name },
    page_title: { ...settings.page_title },
    tagline: { ...settings.tagline },
    address: { ...settings.address },
    industry: { ...settings.industry },
    history: { ...settings.history },
    introduction_html: { ...settings.introduction_html },
    phone: settings.phone,
    email: settings.email,
    website: settings.website,
  };
}

function buildPreviewSettings(
  settings: CompanySettings,
  form: FormState,
  introEn: string,
  introAr: string
): CompanySettings {
  return {
    ...settings,
    ...form,
    introduction_html: {
      en: fromEditorHtml(introEn),
      ar: fromEditorHtml(introAr),
    },
  };
}

export default function SettingsPage() {
  const { t } = useTranslation();
  const { settings, setSettings } = useCompanySettings();
  const branding = useCompanyBranding();
  const [form, setForm] = useState<FormState>(() => toFormState(settings));
  const [introEn, setIntroEn] = useState(() => toEditorHtml(settings.introduction_html.en));
  const [introAr, setIntroAr] = useState(() => toEditorHtml(settings.introduction_html.ar));
  const [previewSettings, setPreviewSettings] = useState<CompanySettings>(() =>
    buildPreviewSettings(settings, toFormState(settings), introEn, introAr)
  );
  const [printSettings, setPrintSettings] = useState<CompanySettings>(settings);
  const [showPreview, setShowPreview] = useState(false);
  const [saving, setSaving] = useState(false);
  const [logoUploading, setLogoUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const hydratedRef = useRef(false);
  const confirmDialog = useConfirmDialog();

  useEffect(() => {
    if (!hydratedRef.current) {
      hydratedRef.current = true;
      return;
    }
    setForm(toFormState(settings));
    setIntroEn((prev) => {
      const next = toEditorHtml(settings.introduction_html.en);
      return prev === next ? prev : next;
    });
    setIntroAr((prev) => {
      const next = toEditorHtml(settings.introduction_html.ar);
      return prev === next ? prev : next;
    });
    setPrintSettings(settings);
  }, [settings.updated_at]);

  useEffect(() => {
    if (!showPreview) return;
    const timer = window.setTimeout(() => {
      setPreviewSettings(buildPreviewSettings(settings, form, introEn, introAr));
    }, 350);
    return () => window.clearTimeout(timer);
  }, [showPreview, settings.logo_url, form, introEn, introAr, settings]);

  const canSave = useMemo(
    () => hasRequiredBranding({ ...settings, ...form }),
    [settings, form]
  );

  const applyBrandingToHeader = (next: FormState) => {
    setSettings((prev) => ({
      ...prev,
      company_name: next.company_name,
      page_title: next.page_title,
      tagline: next.tagline,
    }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!canSave) {
      setError(t("settings.bilingualRequired"));
      return;
    }

    const payload = {
      ...form,
      introduction_html: {
        en: fromEditorHtml(introEn),
        ar: fromEditorHtml(introAr),
      },
    };

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const updated = await updateCompanySettings(payload);
      setSettings(updated);
      setPrintSettings(updated);
      setPreviewSettings(updated);
      setSuccess(t("settings.saveSuccess"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("settings.errors.save"));
    } finally {
      setSaving(false);
    }
  };

  const handleLogoChange = async (file: File | null) => {
    if (!file) return;
    setLogoUploading(true);
    setError(null);
    setSuccess(null);
    try {
      const updated = await uploadCompanyLogo(file);
      setSettings(updated);
      setSuccess(t("settings.logoUploadSuccess"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("settings.errors.logo"));
    } finally {
      setLogoUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleRemoveLogo = () => {
    confirmDialog.requestConfirm(t("settings.confirmRemoveLogo"), async () => {
      setLogoUploading(true);
      setError(null);
      try {
        const updated = await deleteCompanyLogo();
        setSettings(updated);
        setSuccess(t("settings.logoRemoved"));
      } catch (err) {
        setError(err instanceof ApiError ? err.message : t("settings.errors.logo"));
        throw err;
      } finally {
        setLogoUploading(false);
      }
    });
  };

  const handlePrint = () => {
    setPrintSettings(buildPreviewSettings(settings, form, introEn, introAr));
    window.requestAnimationFrame(() => window.print());
  };

  const logoSrc = companyLogoSrc(branding.logo_url);

  return (
    <div>
      <div className="page-actions no-print">
        <div>
          <h1 style={{ marginTop: 0 }}>{t("settings.title")}</h1>
          <p className="muted">{t("settings.subtitle")}</p>
        </div>
        <div className="action-buttons">
          <button type="button" className="btn btn-secondary" onClick={handlePrint}>
            {t("settings.printProfile")}
          </button>
        </div>
      </div>

      {error && <div className="error no-print">{error}</div>}
      {success && <div className="success no-print">{success}</div>}

      <form className="card settings-form no-print" onSubmit={(e) => void handleSubmit(e)}>
        <h2 className="section-title">{t("settings.brandingTitle")}</h2>
        <p className="muted bilingual-form-hint">{t("settings.bilingualHint")}</p>

        <BilingualField
          label={t("settings.pageTitle")}
          value={form.page_title}
          onChange={(page_title) => {
            setForm((prev) => {
              const next = { ...prev, page_title };
              applyBrandingToHeader(next);
              return next;
            });
          }}
          enLabel={t("settings.englishVersion")}
          arLabel={t("settings.arabicVersion")}
          enPlaceholder={t("settings.pageTitlePlaceholder")}
          arPlaceholder={t("settings.pageTitlePlaceholderAr")}
          disabled={saving}
          required
        />

        <BilingualField
          label={t("settings.companyName")}
          value={form.company_name}
          onChange={(company_name) => {
            setForm((prev) => {
              const next = { ...prev, company_name };
              applyBrandingToHeader(next);
              return next;
            });
          }}
          enLabel={t("settings.englishVersion")}
          arLabel={t("settings.arabicVersion")}
          enPlaceholder={t("settings.companyNamePlaceholder")}
          arPlaceholder={t("settings.companyNamePlaceholderAr")}
          disabled={saving}
          required
        />

        <BilingualField
          label={t("settings.tagline")}
          value={form.tagline}
          onChange={(tagline) => {
            setForm((prev) => {
              const next = { ...prev, tagline };
              applyBrandingToHeader(next);
              return next;
            });
          }}
          enLabel={t("settings.englishVersion")}
          arLabel={t("settings.arabicVersion")}
          enPlaceholder={t("settings.taglinePlaceholder")}
          arPlaceholder={t("settings.taglinePlaceholderAr")}
          disabled={saving}
        />

        <div className="edit-field">
          <span>{t("settings.logo")}</span>
          <div className="settings-logo-row">
            {logoSrc ? (
              <img
                src={logoSrc}
                alt={form.company_name.en || form.company_name.ar}
                className="settings-logo-preview"
              />
            ) : (
              <div className="settings-logo-placeholder">{t("settings.noLogo")}</div>
            )}
            <div className="action-buttons">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => fileInputRef.current?.click()}
                disabled={saving || logoUploading}
              >
                {logoUploading ? t("common.loading") : t("settings.uploadLogo")}
              </button>
              {logoSrc && (
                <button
                  type="button"
                  className="btn btn-danger"
                  onClick={handleRemoveLogo}
                  disabled={saving || logoUploading}
                >
                  {t("settings.removeLogo")}
                </button>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml"
              hidden
              onChange={(e) => void handleLogoChange(e.target.files?.[0] ?? null)}
            />
          </div>
        </div>

        <h2 className="section-title">{t("settings.companyInfoTitle")}</h2>

        <BilingualField
          label={t("settings.industry")}
          value={form.industry}
          onChange={(industry) => setForm((prev) => ({ ...prev, industry }))}
          enLabel={t("settings.englishVersion")}
          arLabel={t("settings.arabicVersion")}
          enPlaceholder={t("settings.industryPlaceholder")}
          arPlaceholder={t("settings.industryPlaceholderAr")}
          disabled={saving}
        />

        <BilingualField
          label={t("settings.address")}
          value={form.address}
          onChange={(address) => setForm((prev) => ({ ...prev, address }))}
          enLabel={t("settings.englishVersion")}
          arLabel={t("settings.arabicVersion")}
          enPlaceholder={t("settings.addressPlaceholder")}
          arPlaceholder={t("settings.addressPlaceholderAr")}
          disabled={saving}
          multiline
          rows={2}
        />

        <div className="settings-contact-grid">
          <label className="edit-field">
            <span>{t("settings.phone")}</span>
            <input
              value={form.phone}
              onChange={(e) => setForm((prev) => ({ ...prev, phone: e.target.value }))}
              disabled={saving}
            />
          </label>
          <label className="edit-field">
            <span>{t("settings.email")}</span>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
              disabled={saving}
            />
          </label>
          <label className="edit-field">
            <span>{t("settings.website")}</span>
            <input
              value={form.website}
              onChange={(e) => setForm((prev) => ({ ...prev, website: e.target.value }))}
              disabled={saving}
            />
          </label>
        </div>

        <BilingualField
          label={t("settings.history")}
          value={form.history}
          onChange={(history) => setForm((prev) => ({ ...prev, history }))}
          enLabel={t("settings.englishVersion")}
          arLabel={t("settings.arabicVersion")}
          enPlaceholder={t("settings.historyPlaceholder")}
          arPlaceholder={t("settings.historyPlaceholderAr")}
          disabled={saving}
          multiline
          rows={4}
        />

        <fieldset className="bilingual-field">
          <legend>{t("settings.introduction")}</legend>
          <p className="muted bilingual-form-hint">{t("settings.introductionHint")}</p>
          <div className="bilingual-field-grid">
            <div className="edit-field analysis-document-editor">
              <span>{t("settings.englishVersion")}</span>
              <Suspense fallback={<p className="muted">{t("common.loading")}</p>}>
                <RichTextEditor
                  value={introEn}
                  onChange={setIntroEn}
                  disabled={saving}
                  minHeight="180px"
                  ariaLabel={t("settings.introduction")}
                />
              </Suspense>
            </div>
            <div className="edit-field analysis-document-editor">
              <span>{t("settings.arabicVersion")}</span>
              <Suspense fallback={<p className="muted">{t("common.loading")}</p>}>
                <RichTextEditor
                  value={introAr}
                  onChange={setIntroAr}
                  disabled={saving}
                  minHeight="180px"
                  ariaLabel={t("settings.introduction")}
                />
              </Suspense>
            </div>
          </div>
        </fieldset>

        <div className="action-buttons">
          <Link className="btn btn-secondary" to="/" style={{ padding: "0.6rem 1rem", textDecoration: "none" }}>
            {t("settings.backToDashboard")}
          </Link>
          <button type="submit" className="btn" disabled={saving || !canSave}>
            {saving ? t("settings.saving") : t("common.save")}
          </button>
        </div>
      </form>

      <div className="card company-profile-preview no-print">
        <div className="company-profile-preview-header">
          <h2 className="section-title" style={{ margin: 0 }}>
            {t("settings.previewTitle")}
          </h2>
          <div className="action-buttons">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowPreview((open) => !open)}
            >
              {showPreview ? t("settings.hidePreview") : t("settings.showPreview")}
            </button>
            <button type="button" className="btn btn-secondary" onClick={handlePrint}>
              {t("settings.printProfile")}
            </button>
          </div>
        </div>
        {showPreview && <CompanyProfile settings={previewSettings} />}
      </div>

      <div className="print-only">
        <CompanyProfile settings={printSettings} printable />
      </div>

      <ConfirmDialog
        open={confirmDialog.open}
        message={confirmDialog.message}
        confirmLabel={t("settings.removeLogo")}
        loading={confirmDialog.loading || logoUploading}
        onConfirm={() => void confirmDialog.confirm()}
        onCancel={confirmDialog.cancel}
      />
    </div>
  );
}
