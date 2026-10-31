import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchRepoSubSkillList, type SubSkillListItem } from "../api/subSkills";
import { githubFolderUrl, subSkillPath } from "../lib/subSkillMeta.mjs";
import { useSubSkillStrings } from "../i18n/subSkillStrings";

const LIST_SHOWN = 50; // PARENT_LIST_SHOWN in scripts/sub-skills.mjs

const LINK_CLASS = "font-semibold text-indigo-600 dark:text-indigo-400 hover:underline";

function SubSkillItem({ repoFullName, item }: { repoFullName: string; item: SubSkillListItem }) {
  const label = item.page ? (
    <Link to={subSkillPath(repoFullName, item.slug)} className={LINK_CLASS}>{item.name}</Link>
  ) : (
    <a href={githubFolderUrl(repoFullName, item.path)} target="_blank" rel="noopener noreferrer" className={LINK_CLASS}>
      {item.name}
    </a>
  );
  return (
    <li className="text-sm leading-relaxed">
      {label}
      {item.description && <span className="text-gray-500 dark:text-gray-400"> {item.description}</span>}
    </li>
  );
}

/** A repository's skills: their own page when the build published one, otherwise the GitHub folder. */
export function SubSkillLinks({ repoFullName, items }: { repoFullName: string; items: SubSkillListItem[] }) {
  return (
    <ul className="grid gap-1.5">
      {items.map((item) => (
        <SubSkillItem key={item.slug} repoFullName={repoFullName} item={item} />
      ))}
    </ul>
  );
}

/** "Skills in this repository" on a repository page: the list the static page carries
 *  (scripts/sub-skills.mjs parentSectionHtml). Nothing for a repository without one. */
export function RepoSubSkills({ repoFullName }: { repoFullName: string }) {
  const s = useSubSkillStrings();
  const [list, setList] = useState<SubSkillListItem[] | null>(null);
  useEffect(() => {
    let live = true;
    fetchRepoSubSkillList(repoFullName).then((l) => live && setList(l ?? null)).catch(() => live && setList(null));
    return () => { live = false; };
  }, [repoFullName]);
  if (!list?.length) return null;
  const more = list.length - LIST_SHOWN;
  return (
    <section className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5 mb-6">
      <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-3">{s.listTitle(list.length)}</h2>
      <SubSkillLinks repoFullName={repoFullName} items={list.slice(0, LIST_SHOWN)} />
      {more > 0 && (
        <a href={`https://github.com/${repoFullName}`} target="_blank" rel="noopener noreferrer"
          className="mt-3 inline-block text-sm text-indigo-600 dark:text-indigo-400 hover:underline">
          {s.moreOnGitHub(more)}
        </a>
      )}
    </section>
  );
}
