import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useTranslation } from "react-i18next";
import {
  DEFAULT_COMPANY_SETTINGS,
  getCompanySettings,
  pickLocalized,
  type BilingualText,
  type CompanySettings,
} from "../api/settings";

interface CompanySettingsContextValue {
  settings: CompanySettings;
  loading: boolean;
  refresh: () => Promise<void>;
  setSettings: (settings: CompanySettings | ((prev: CompanySettings) => CompanySettings)) => void;
}

export interface CompanyBranding {
  company_name: BilingualText;
  page_title: BilingualText;
  tagline: BilingualText;
  logo_url: string | null;
}

const CompanySettingsContext = createContext<CompanySettingsContextValue | null>(null);

export function CompanySettingsProvider({ children }: { children: ReactNode }) {
  const { t, i18n } = useTranslation();
  const [settings, setSettingsState] = useState<CompanySettings>(DEFAULT_COMPANY_SETTINGS);
  const [loading, setLoading] = useState(true);
  const loadedRef = useRef(false);

  const setSettings = useCallback(
    (value: CompanySettings | ((prev: CompanySettings) => CompanySettings)) => {
      setSettingsState(value);
    },
    []
  );

  const refresh = useCallback(async () => {
    try {
      const loaded = await getCompanySettings();
      setSettings(loaded);
    } catch {
      if (!loadedRef.current) {
        setSettings({
          ...DEFAULT_COMPANY_SETTINGS,
          company_name: { ar: t("app.name"), en: t("app.name") },
          page_title: { ar: t("app.title"), en: t("app.title") },
        });
      }
    } finally {
      loadedRef.current = true;
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const lang = i18n.language === "ar" ? "ar" : "en";
    document.title = pickLocalized(settings.page_title, lang) || t("app.title");
  }, [settings.page_title, i18n.language, t]);

  const value = useMemo(
    () => ({ settings, loading, refresh, setSettings }),
    [settings, loading, refresh]
  );

  return (
    <CompanySettingsContext.Provider value={value}>{children}</CompanySettingsContext.Provider>
  );
}

export function useCompanySettings() {
  const context = useContext(CompanySettingsContext);
  if (!context) {
    throw new Error("useCompanySettings must be used within CompanySettingsProvider");
  }
  return context;
}

/** Lightweight hook for header/dashboard title — avoids re-renders when intro/history changes. */
export function useCompanyBranding(): CompanyBranding & { loading: boolean } {
  const { settings, loading } = useCompanySettings();
  return useMemo(
    () => ({
      company_name: settings.company_name,
      page_title: settings.page_title,
      tagline: settings.tagline,
      logo_url: settings.logo_url,
      loading,
    }),
    [
      settings.company_name.en,
      settings.company_name.ar,
      settings.page_title.en,
      settings.page_title.ar,
      settings.tagline.en,
      settings.tagline.ar,
      settings.logo_url,
      loading,
    ]
  );
}
