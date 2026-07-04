import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { translations, type Lang, type TransKey } from "./translations";

interface I18nCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: TransKey) => string;
}

const Ctx = createContext<I18nCtx>(null!);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    // Explicit user choice always wins; first-time visitors get their
    // browser's language. Clarity data (2026-07-04): the 中文 toggle was the
    // single most-clicked element on the homepage (5.9% of all clicks) —
    // Chinese visitors shouldn't have to hunt for it.
    const saved = localStorage.getItem("lang") as Lang | null;
    if (saved === "zh" || saved === "en") return saved;
    return navigator.language?.toLowerCase().startsWith("zh") ? "zh" : "en";
  });

  // Keep <html lang> in sync with the active language (deps were previously
  // [] — a lying dep array; runtime was saved only by switchLang's manual DOM
  // write, which this now makes redundant but harmless).
  useEffect(() => {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  }, [lang]);

  const switchLang = (l: Lang) => {
    setLang(l);
    localStorage.setItem("lang", l);
    document.documentElement.lang = l === "zh" ? "zh-CN" : "en";
  };

  const t = (key: TransKey) => translations[lang][key] || key;

  return (
    <Ctx.Provider value={{ lang, setLang: switchLang, t }}>
      {children}
    </Ctx.Provider>
  );
}

export const useI18n = () => useContext(Ctx);
