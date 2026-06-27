import { useTranslation } from "react-i18next";
import type { AppLanguage } from "../i18n";

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const current = i18n.language === "ar" ? "ar" : "en";

  const setLanguage = (lang: AppLanguage) => {
    void i18n.changeLanguage(lang);
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
      <span style={{ color: "#94a3b8", fontSize: "0.85rem" }}>{t("language.label")}:</span>
      <button
        type="button"
        className={`lang-btn ${current === "en" ? "lang-btn-active" : ""}`}
        onClick={() => setLanguage("en")}
      >
        {t("language.en")}
      </button>
      <button
        type="button"
        className={`lang-btn ${current === "ar" ? "lang-btn-active" : ""}`}
        onClick={() => setLanguage("ar")}
      >
        {t("language.ar")}
      </button>
    </div>
  );
}
