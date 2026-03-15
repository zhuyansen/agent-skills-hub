import { useI18n } from "../i18n/I18nContext";

export function LanguageToggle() {
  const { lang, setLang } = useI18n();
  return (
    <button
      onClick={() => setLang(lang === "zh" ? "en" : "zh")}
      className="px-2.5 py-1 text-xs rounded-full border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:border-blue-300 transition-colors"
    >
      {lang === "zh" ? "EN" : "中文"}
    </button>
  );
}
