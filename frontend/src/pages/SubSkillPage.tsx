import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  fetchRepoSubSkillList, fetchSubSkill, fetchSubSkillParent,
  type SubSkill, type SubSkillListItem, type SubSkillParent,
} from "../api/subSkills";
import {
  skillMdUrl, subSkillDescription, subSkillInstall, subSkillTitle, subSkillUrl,
} from "../lib/subSkillMeta.mjs";
import { useSubSkillStrings } from "../i18n/subSkillStrings";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { SecurityBadge } from "../components/SecurityBadge";
import { CopyablePre } from "../components/CopyableCode";
import { SubSkillLinks } from "../components/SubSkillList";

const SIBLINGS_SHOWN = 20; // SIBLINGS_SHOWN in scripts/sub-skills.mjs
const CARD = "bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5 mb-6";
const H2 = "text-base font-semibold text-gray-900 dark:text-gray-100 mb-3";

// "missing": the database answered and has no such skill. "error": it could not be asked; that
// page gets no noindex, since a failed request while Google renders must not drop a real page.
type PageData =
  | { status: "loading" | "missing" | "error" }
  | { status: "ready"; skill: SubSkill; parent: SubSkillParent | null; list: SubSkillListItem[] | null | undefined };

/** Loading until the answer for this very URL arrives (a hop to a sibling starts over). */
function useSubSkillData(repoFullName: string, slug: string): PageData {
  const key = `${repoFullName}/${slug}`;
  const [result, setResult] = useState<{ key: string; data: PageData } | null>(null);
  useEffect(() => {
    let live = true;
    window.scrollTo(0, 0);
    Promise.all([fetchSubSkill(repoFullName, slug), fetchSubSkillParent(repoFullName), fetchRepoSubSkillList(repoFullName)])
      .then(([skill, parent, list]) => {
        const data: PageData = skill ? { status: "ready", skill, parent, list } : { status: "missing" };
        if (live) setResult({ key, data });
      })
      .catch(() => live && setResult({ key, data: { status: "error" } }));
    return () => { live = false; };
  }, [key, repoFullName, slug]);
  return result?.key === key ? result.data : { status: "loading" };
}

/** Same title, description and canonical as the static page (scripts/sub-skills.mjs); a skill
 *  the build gave no page stays out of the index. */
function SubSkillHead({ skill, published }: { skill: SubSkill; published: boolean }) {
  const title = subSkillTitle(skill.repo_full_name, skill.name, skill.description);
  const description = subSkillDescription(skill.repo_full_name, skill.name, skill.description);
  const url = subSkillUrl(skill.repo_full_name, skill.slug);
  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      {!published && <meta name="robots" content="noindex" />}
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={url} />
      <meta property="og:image" content="https://agentskillshub.top/og-image.png" />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <link rel="canonical" href={url} />
    </Helmet>
  );
}

function SubSkillHero({ skill, parent }: { skill: SubSkill; parent: SubSkillParent | null }) {
  const s = useSubSkillStrings();
  return (
    <div className={CARD}>
      <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">{skill.name}</h1>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
        {s.inRepo}{" "}
        <Link to={`/skill/${skill.repo_full_name}/`} className="text-indigo-600 dark:text-indigo-400 hover:underline">
          {skill.repo_full_name}
        </Link>
        {parent && ` · ${parent.stars.toLocaleString("en-US")} ${s.starsOnGitHub}`}
      </p>
      <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-4">{skill.description}</p>
      <SecurityBadge grade={skill.security_grade} size="md" explain />
    </div>
  );
}

function SubSkillInstall({ skill }: { skill: SubSkill }) {
  const s = useSubSkillStrings();
  return (
    <section className={CARD}>
      <h2 className={H2}>{s.install(skill.name)}</h2>
      <div className="[&_pre]:bg-gray-900 [&_pre]:text-gray-100 [&_pre]:rounded-lg [&_pre]:p-3 [&_pre]:text-xs [&_pre]:overflow-x-auto dark:[&_pre]:bg-gray-950 dark:[&_pre]:border dark:[&_pre]:border-gray-700">
        <CopyablePre><code>{subSkillInstall(skill.repo_full_name, skill.name)}</code></CopyablePre>
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
        {s.installNote}{" "}
        <a href={skillMdUrl(skill.repo_full_name, skill.path)} target="_blank" rel="noopener noreferrer"
          className="text-indigo-600 dark:text-indigo-400 hover:underline">
          {s.readSkillMd}
        </a>
      </p>
    </section>
  );
}

function SubSkillBody({ skill, list }: { skill: SubSkill; list: SubSkillListItem[] }) {
  const s = useSubSkillStrings();
  const others = list.filter((item) => item.slug !== skill.slug).slice(0, SIBLINGS_SHOWN);
  const showExcerpt = skill.body_excerpt && skill.body_excerpt !== skill.description;
  return (
    <>
      {showExcerpt && (
        <section className={CARD}>
          <h2 className={H2}>{s.excerpt}</h2>
          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{skill.body_excerpt}</p>
        </section>
      )}
      {others.length > 0 && (
        <section className={CARD}>
          <h2 className={H2}>{s.others(skill.repo_full_name)}</h2>
          <SubSkillLinks repoFullName={skill.repo_full_name} items={others} />
        </section>
      )}
    </>
  );
}

function PageShell({ crumb, children }: { crumb: string; children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <SiteHeader breadcrumb={[{ label: crumb }]} />
      <main className="max-w-4xl mx-auto px-4 py-6">{children}</main>
      <SiteFooter />
    </div>
  );
}

function NotReady({ repoFullName, status }: { repoFullName: string; status: "loading" | "missing" | "error" }) {
  const s = useSubSkillStrings();
  const missing = status === "missing";
  return (
    <PageShell crumb={repoFullName.split("/")[1] ?? repoFullName}>
      {missing && <Helmet><meta name="robots" content="noindex" /></Helmet>}
      <p className="py-24 text-center text-sm text-gray-500 dark:text-gray-400">
        {{ loading: s.loading, missing: s.notFound, error: s.loadFailed }[status]}{" "}
        {status !== "loading" && (
          <Link to={`/skill/${repoFullName}/`} className="text-indigo-600 dark:text-indigo-400 hover:underline">
            {s.backToRepo}
          </Link>
        )}
      </p>
    </PageShell>
  );
}

/** /skill/<owner>/<repo>/<slug>/: one skill of a repository that holds several. */
export function SubSkillPage() {
  const { owner = "", repo = "", sub = "" } = useParams<{ owner: string; repo: string; sub: string }>();
  const repoFullName = `${owner}/${repo}`;
  const data = useSubSkillData(repoFullName, sub);
  if (data.status !== "ready") return <NotReady repoFullName={repoFullName} status={data.status} />;
  // Without the list (site unreachable) the static page's own robots tag stands.
  const published = data.list === undefined || (data.list ?? []).some((item) => item.slug === data.skill.slug && item.page);
  return (
    <PageShell crumb={data.skill.name}>
      <SubSkillHead skill={data.skill} published={published} />
      <SubSkillHero skill={data.skill} parent={data.parent} />
      <SubSkillInstall skill={data.skill} />
      <SubSkillBody skill={data.skill} list={data.list ?? []} />
    </PageShell>
  );
}
