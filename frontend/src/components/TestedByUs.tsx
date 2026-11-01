import { useI18n } from "../i18n/I18nContext";
import { prerenderedTested } from "../lib/prerenderedMeta";
import {
  TESTED_TITLE, TESTED_SEE_ALL, TESTED_IMAGE_ALT, testedIntro, testedTop, testedPick, testedResult,
  type Pair, type TestedEntry,
} from "../lib/testedCopy.mjs";

const P = "text-sm leading-relaxed text-gray-700 dark:text-gray-300 mb-1.5";
const LINK = "text-indigo-600 dark:text-indigo-400 hover:underline";
const EVIDENCE_WIDTH = 1200; // the PPT test's slide sheets (public/best-runs/ppt/*.jpg)
const EVIDENCE_HEIGHT = 675;

function TestedItem({ entry, say }: { entry: TestedEntry; say: (pair: Pair) => string }) {
  const lines = [testedIntro(entry), testedTop(entry), testedPick(entry), testedResult(entry)];
  return (
    <div className="mb-2">
      {lines.map((line, i) => line && <p key={i} className={i === 1 ? `${P} font-semibold` : P}>{say(line)}</p>)}
      {entry.evidence.image && (
        <a href={entry.evidence.href} target="_blank" rel="noopener noreferrer">
          <img src={entry.evidence.href} alt={say(TESTED_IMAGE_ALT)} width={EVIDENCE_WIDTH} height={EVIDENCE_HEIGHT}
            loading="lazy" className="block max-w-full h-auto my-2 rounded-lg border border-gray-200 dark:border-gray-700" />
        </a>
      )}
      <p className={P}>
        <a href={entry.evidence.href} target="_blank" rel="noopener noreferrer" className={LINK}>{say(entry.evidence.label)}</a>
        {" · "}
        <a href={entry.page} className={LINK}>{say(TESTED_SEE_ALL)}</a>
      </p>
    </div>
  );
}

/** "Tested by Agent Skills Hub": the end-to-end tests the static page lists (scripts/skill-tested.mjs).
 *  The entries come with the pre-rendered page, so a direct load (Google's) shows them; a hop
 *  inside the app to another skill does not. */
export function TestedByUs() {
  const { lang } = useI18n();
  const entries = prerenderedTested();
  if (!entries.length) return null;
  const say = (pair: Pair) => (lang === "zh" ? pair[1] : pair[0]);
  return (
    <section className="rounded-xl border border-indigo-200 dark:border-indigo-900 bg-indigo-50/60 dark:bg-indigo-950/30 p-5 mb-6">
      <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-3">🧪 {say(TESTED_TITLE)}</h2>
      {entries.map((entry) => <TestedItem key={entry.page} entry={entry} say={say} />)}
    </section>
  );
}
