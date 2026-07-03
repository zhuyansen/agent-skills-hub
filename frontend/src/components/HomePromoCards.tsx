import { Link } from "react-router-dom";

/** Static promo cards at the tail of the overview tab: latest blog feature +
 *  submit-to-the-hub. Pure JSX, no props — extracted from Home.tsx to keep the
 *  page component under the size red line. */
export function HomePromoCards() {
  return (
    <>
      <div id="blog">
        {/* Static HTML page — use <a href> so browser hard-navigates,
            bypassing React Router (which would 404 → redirect to /). */}
        <a
          href="/blog/skill-stack-solo-saas-2026/"
          className="surface surface-hover block mt-12 mb-4 p-5 sm:p-6"
        >
          <div className="flex items-center gap-4">
            <div className="flex-none w-12 h-12 bg-indigo-100 dark:bg-indigo-900/50 rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-indigo-600 dark:text-indigo-400"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"
                />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="inline-block px-2 py-0.5 text-[11px] font-semibold rounded-full bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-400">
                  New
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  Blog · 2026-05-04
                </span>
              </div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                How I'd Build a SaaS Solo in 6 Weeks Using AI Skills
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                5 tiers · 19 skills · idea → launch in 6 weeks. With real
                examples.
              </p>
            </div>
            <span className="hidden sm:inline-flex flex-none text-indigo-600 dark:text-indigo-400 text-sm font-semibold whitespace-nowrap">
              Read →
            </span>
          </div>
        </a>
      </div>
      <div id="submit-skill">
        <Link
          to="/submit/"
          className="surface surface-hover block mt-4 mb-4 p-5 sm:p-6"
        >
          <div className="flex items-center gap-4">
            <div className="flex-none w-12 h-12 bg-indigo-50 dark:bg-indigo-950/40 rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-indigo-600 dark:text-indigo-400"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 4v16m8-8H4"
                />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                Submit to the Hub
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                Submit a Skill, compose a Workflow, or apply for Verified
                Creator
              </p>
            </div>
            <span className="flex-none text-indigo-600 dark:text-indigo-400 text-sm font-semibold whitespace-nowrap">
              Open →
            </span>
          </div>
        </Link>
      </div>
    </>
  );
}
