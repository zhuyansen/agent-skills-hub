export interface Platform {
  name: string;
  url: string;
  description_zh: string;
  description_en: string;
  icon: string;
}

export const platforms: Platform[] = [
  {
    name: "Skills.sh",
    url: "https://skills.sh/",
    description_zh: "Agent Skill 发现与浏览平台",
    description_en: "Agent Skill discovery & browsing platform",
    icon: "globe",
  },
  {
    name: "Find Skills",
    url: "https://skills.sh/vercel-labs/skills/find-skills",
    description_zh: "Vercel Labs 技能搜索引擎",
    description_en: "Vercel Labs skill search engine",
    icon: "search",
  },
  {
    name: "SkillsMP",
    url: "https://skillsmp.com/zh",
    description_zh: "技能市场 · 多语言支持",
    description_en: "Skill marketplace with multi-language support",
    icon: "store",
  },
];
