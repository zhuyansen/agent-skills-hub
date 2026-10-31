/**
 * Labels for the sub-skill pages and the "Skills in this repository" list. Kept out of
 * translations.ts, which is past the file-size limit. The English matches the static page
 * (scripts/sub-skills.mjs), which is what search engines read first.
 */
import { useI18n } from "./I18nContext";

export interface SubSkillStrings {
  listTitle: (count: number) => string;
  moreOnGitHub: (count: number) => string;
  inRepo: string;
  starsOnGitHub: string;
  install: (name: string) => string;
  installNote: string;
  readSkillMd: string;
  excerpt: string;
  others: (repo: string) => string;
  loading: string;
  notFound: string;
  loadFailed: string;
  backToRepo: string;
}

const EN: SubSkillStrings = {
  listTitle: (n) => `Skills in this repository (${n})`,
  moreOnGitHub: (n) => `${n} more in the repository on GitHub`,
  inRepo: "A skill in",
  starsOnGitHub: "stars on GitHub",
  install: (name) => `How to install ${name}`,
  installNote: "The skills CLI copies this one skill into Claude Code (use -a for another agent).",
  readSkillMd: "Read its SKILL.md on GitHub",
  excerpt: "What the SKILL.md says",
  others: (repo) => `Other skills in ${repo}`,
  loading: "Loading…",
  notFound: "This skill is not in our catalog",
  loadFailed: "Could not load this skill. Try again in a moment.",
  backToRepo: "See the repository",
};

const ZH: SubSkillStrings = {
  listTitle: (n) => `本仓库里的 Skills（${n}）`,
  moreOnGitHub: (n) => `另有 ${n} 个，见 GitHub 仓库`,
  inRepo: "所在仓库",
  starsOnGitHub: "GitHub Stars",
  install: (name) => `安装 ${name}`,
  installNote: "用 skills 命令行只把这一个 skill 装进 Claude Code（换别的 agent 改 -a 参数）。",
  readSkillMd: "在 GitHub 上看它的 SKILL.md",
  excerpt: "SKILL.md 里写了什么",
  others: (repo) => `${repo} 里的其他 Skills`,
  loading: "加载中…",
  notFound: "目录里没有这个 skill",
  loadFailed: "暂时加载不了，稍后再试。",
  backToRepo: "去仓库页",
};

export function useSubSkillStrings(): SubSkillStrings {
  const { lang } = useI18n();
  return lang === "zh" ? ZH : EN;
}
