import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { translations, type Lang, type TransKey } from "./translations";

interface I18nCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: TransKey) => string;
}

const Ctx = createContext<I18nCtx>(null!);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    return (localStorage.getItem("lang") as Lang) || "en";
  });

  useEffect(() => {
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
  }, []);

  const switchLang = (l: Lang) => {
    setLang(l);
    localStorage.setItem("lang", l);
    document.documentElement.lang = l === 'zh' ? 'zh-CN' : 'en';
  };

  const t = (key: TransKey) => translations[lang][key] || key;

  return (
    <Ctx.Provider value={{ lang, setLang: switchLang, t }}>
      {children}
    </Ctx.Provider>
  );
}

export const useI18n = () => useContext(Ctx);
