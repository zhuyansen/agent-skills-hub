import type { CategoryCount } from "../types/skill";

interface Props {
  categories: CategoryCount[];
  selected: string;
  onSelect: (category: string) => void;
}

export function CategoryFilter({ categories, selected, onSelect }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onSelect("")}
        className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
          !selected
            ? "bg-blue-600 text-white border-blue-600"
            : "bg-white text-gray-600 border-gray-200 hover:border-gray-300"
        }`}
      >
        All
      </button>
      {categories.map((cat) => (
        <button
          key={cat.name}
          onClick={() => onSelect(cat.name)}
          className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
            selected === cat.name
              ? "bg-blue-600 text-white border-blue-600"
              : "bg-white text-gray-600 border-gray-200 hover:border-gray-300"
          }`}
        >
          {cat.name}
          <span className="ml-1 opacity-70">{cat.count}</span>
        </button>
      ))}
    </div>
  );
}
