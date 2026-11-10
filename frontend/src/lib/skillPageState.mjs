/**
 * What a /skill/ page is doing, as one state (hooks/useSkillPage.ts). The page kept it in
 * `loading`, `error`, `detail` and a local `redirected` flag, and nothing tied an answer to the
 * page that asked: after a hop from one skill to another, the first one's late answer (or late
 * failure) replaced the second's page.
 *
 *   loading      waiting for the skill named by `key` (owner/repo, or a numeric id)
 *   ready        `detail` is that skill
 *   redirecting  `key` is an old name of a renamed repository; `to` is the name it has now
 *   failed       no such skill, or the request failed; the page falls back to its static copy
 *
 * Every event names the key it answers; one for another key changes nothing.
 * Test: node --test scripts/skill-page-state.test.mjs
 */

export const loadingSkillPage = (key) => ({ kind: "loading", key });

const SETTLED = {
  loaded: (key, event) => ({ kind: "ready", key, detail: event.detail }),
  moved: (key, event) => ({ kind: "redirecting", key, to: event.to }),
  failed: (key, event) => ({ kind: "failed", key, message: event.message }),
};

export function skillPageReducer(state, event) {
  if (event.type === "requested") return loadingSkillPage(event.key);
  const settle = SETTLED[event.type];
  if (!settle || state.kind !== "loading" || state.key !== event.key) return state;
  return settle(state.key, event);
}

/** The state for the page now on screen: a state left by the previous page reads as loading. */
export function skillPageFor(state, key) {
  return state.key === key ? state : loadingSkillPage(key);
}
