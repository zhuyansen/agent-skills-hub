import { useMemo } from "react";
import { ProsePage } from "../components/ProsePage";
import { useStats } from "../hooks/useStats";
import { useI18n } from "../i18n/I18nContext";
import { readCatalogCounts } from "../lib/catalogCounts";
import { countText, directoriesText, UNKNOWN_TOTAL } from "../lib/directoriesContent.mjs";
import { DIRECTORIES_META, DIRECTORIES_URL, FACTS_READ_ON } from "../lib/directoriesMeta.mjs";
import { NOFOLLOW_REL } from "../lib/proseContent.mjs";

/** The page in the reader's language, with our catalog count stated as the home page states it. */
function Directories({ total }: { total: number | null }) {
  const { lang } = useI18n();
  const text = useMemo(() => directoriesText(total === null ? UNKNOWN_TOTAL : countText(total)), [total]);
  const meta = { ...DIRECTORIES_META[lang], url: DIRECTORIES_URL };
  return <ProsePage lang={lang} meta={meta} text={text} date={FACTS_READ_ON} rel={NOFOLLOW_REL} />;
}

/** For a page without the build's count: the live stats, which the home page falls back on too. */
function WithLiveCount() {
  const { stats } = useStats();
  return <Directories total={stats?.total_skills ?? null} />;
}

/**
 * /agent-skills-directories/: where to find agent skills and MCP servers, the directories
 * compared. Our catalog count comes from where the home page's hero takes it
 * (src/components/HeroSection.tsx): the count the build wrote into the page
 * (src/lib/catalogCounts.ts), which is also the number the pre-rendered copy shows, else the
 * live stats. Those are fetched here when needed, so a reader who lands on the page directly
 * costs no query.
 */
export function DirectoriesPage() {
  const build = readCatalogCounts();
  return build ? <Directories total={build.total} /> : <WithLiveCount />;
}
