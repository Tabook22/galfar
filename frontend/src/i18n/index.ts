import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ar from "./locales/ar.json";
import en from "./locales/en.json";

export const LANGUAGE_STORAGE_KEY = "galfar-language";
export type AppLanguage = "en" | "ar";

export function applyDocumentLanguage(lang: AppLanguage): void {
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  document.title = i18n.t("app.title");
}

const saved = (localStorage.getItem(LANGUAGE_STORAGE_KEY) as AppLanguage | null) ?? "en";

void i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    ar: { translation: ar },
  },
  lng: saved,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

applyDocumentLanguage(saved);

i18n.on("languageChanged", (lang) => {
  const normalized = (lang === "ar" ? "ar" : "en") as AppLanguage;
  localStorage.setItem(LANGUAGE_STORAGE_KEY, normalized);
  applyDocumentLanguage(normalized);
});

export default i18n;

export function getCurrentLanguage(): AppLanguage {
  return i18n.language === "ar" ? "ar" : "en";
}
