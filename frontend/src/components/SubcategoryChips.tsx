import { useI18n } from "../i18n/I18nContext";
import { getSubcategoriesForCategory } from "../utils/subcategories";

interface Props {
  category: string;
  selected: string | null;
  onSelect: (sub: string | null) => void;
}

export function SubcategoryChips({ category, selected, onSelect }: Props) {
  const { lang } = useI18n();
  const subs = getSubcategoriesForCategory(category);

  if (subs.length === 0) return null;

  return (
    <div className="flex items-center gap-1.5 flex-wrap mb-3">
      <button
        onClick={() => onSelect(null)}
        className={`px-2.5 py-1 text-[11px] font-medium rounded-full border transition-all cursor-pointer ${
          !selected
            ? "bg-indigo-600 text-white border-indigo-600"
            : "bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-indigo-400 hover:text-indigo-600"
        }`}
      >
        {lang === "zh" ? "全部" : "All"}
      </button>
      {subs.map((sub) => (
        <button
          key={sub.id}
          onClick={() => onSelect(selected === sub.id ? null : sub.id)}
          className={`px-2.5 py-1 text-[11px] font-medium rounded-full border transition-all cursor-pointer ${
            selected === sub.id
              ? "bg-indigo-600 text-white border-indigo-600"
              : "bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-indigo-400 hover:text-indigo-600"
          }`}
        >
          {lang === "zh" ? sub.labelZh : sub.labelEn}
        </button>
      ))}
    </div>
  );
}
